"""National 10 m river turbidity: per-pixel seasonal sums and per-scene 1 km summaries, one tile at a time.

Uses the river pixels from 21_rivers10m.py. For every Sentinel-2 scene of the tile (2019-2025, scene cloud
<= 80 %), blocks holding river pixels are read (B03, B04, B08 at 10 m; SCL at 20 m). A river pixel is valid
when SCL is clear and >= 50 m from cloud or shadow, NDWI > 0.15, NDVI < 0.05 and NIR < 0.15 (as for the project
rivers; channels are too narrow for a shoreline buffer or the 20 m SWIR test).

Per valid pixel: NDTI = (red - green) / (red + green) and red-band Nechad SPM, summed by season (NEM, FIM, SWM,
SIM) for the 10 m maps. Per scene and 1 km UTM cell (>= 5 valid pixels): median NDTI, SPM and red.

    python scripts/cog/22_extract_river10m.py 44NMP 44NLN ...   (no tiles = all with river pixels)
Writes data/cog/r10m/<tile>/accum.npz (checkpointed, resumable) and cells/<scene>.csv
"""
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from rasterio.windows import Window  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402

from sedrs import algorithms as alg  # noqa: E402
from sedrs import cog  # noqa: E402
from sedrs.config import DATA_DIR  # noqa: E402

cog.set_gdal_env()
R = DATA_DIR / "cog" / "r10m"
CLOUDY = (3, 8, 9, 10)
SEAS = {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 10: 3, 11: 3}
A_SPM, C_SPM = alg.NECHAD_SPM["S2"]["red"]
scenes = pd.read_csv(DATA_DIR / "cog" / "scenes.csv").drop_duplicates("id")
scenes = scenes[scenes["cloud"] <= 80].sort_values(["date", "id"])
tiles = sys.argv[1:] or [p.name for p in sorted(R.iterdir()) if (p / "blocks.json").exists()]
WORKERS = 8


def run_tile(t):
    D = R / t
    blocks = json.loads((D / "blocks.json").read_text())
    if not blocks:
        return
    with rasterio.open(D / "river.tif") as d:
        river = d.read(1) > 0
        x0, y1 = d.transform.c, d.transform.f
    off = 0
    for b in blocks:
        sub = river[b["row"]:b["row"] + b["h"], b["col"]:b["col"] + b["w"]]
        b["mask"] = sub
        b["pos"] = np.flatnonzero(sub)
        b["off"] = off
        rr, cc = np.divmod(b["pos"], b["w"])
        xs = x0 + (b["col"] + cc + 0.5) * 10
        ys = y1 - (b["row"] + rr + 0.5) * 10
        b["cell"] = (np.floor(xs / 1000).astype(np.int64) * 10000 + np.floor(ys / 1000).astype(np.int64))
        off += len(b["pos"])
    npx = off
    del river
    ck = D / "accum.npz"
    if ck.exists():
        z = np.load(ck, allow_pickle=True)
        acc_nd, acc_ls, acc_n = z["ndti"], z["lspm"], z["n"]
        done = set(z["done"].tolist())
    else:
        acc_nd = np.zeros((4, npx), np.float32)
        acc_ls = np.zeros((4, npx), np.float32)
        acc_n = np.zeros((4, npx), np.uint16)
        done = set()
    cdir = D / "cells"
    cdir.mkdir(exist_ok=True)
    lock = threading.Lock()

    def save():
        with lock:
            np.savez(ck, ndti=acc_nd, lspm=acc_ls, n=acc_n, done=np.array(sorted(done), dtype=object))

    def process(row):
        ds = {b_: rasterio.open(cog.band_url(row.prefix, b_)) for b_ in ("B03", "B04", "B08", "SCL")}
        try:
            season = SEAS[int(row.date[5:7])]
            upd, cells = [], []
            for b in blocks:
                s = ds["SCL"].read(1, window=Window(b["col"] // 2, b["row"] // 2, (b["w"] + 1) // 2,
                                                    (b["h"] + 1) // 2))
                s = np.repeat(np.repeat(s, 2, 0), 2, 1)[:b["h"], :b["w"]]
                ok = ~np.isin(s, cog.SCL_BAD) & ~ndi.binary_dilation(np.isin(s, CLOUDY), iterations=5)
                if not (ok & b["mask"]).any():
                    continue
                win = Window(b["col"], b["row"], b["w"], b["h"])
                g, r, n = (ds[k].read(1, window=win).astype(np.float32).ravel()[b["pos"]] * 1e-4
                           for k in ("B03", "B04", "B08"))
                okp = ok.ravel()[b["pos"]] & (g > 0) & (r > 0) & (n > 0)
                with np.errstate(divide="ignore", invalid="ignore"):
                    v = okp & ((g - n) / (g + n) > 0.15) & ((n - r) / (n + r) < 0.05) & (n < 0.15)
                if not v.any():
                    continue
                idx = np.flatnonzero(v)
                nd = alg.ndti(r[idx], g[idx]).astype(np.float32)
                spm = alg.nechad(r[idx], A_SPM, C_SPM)
                ls = np.log10(np.clip(np.nan_to_num(spm, nan=5000.0), 0.1, 5000)).astype(np.float32)
                upd.append((b["off"] + idx, nd, ls))
                cells.append(pd.DataFrame({"cell": b["cell"][idx], "ndti": nd, "spm": spm, "red": r[idx]}))
            if cells:
                c = pd.concat(cells)
                agg = c.groupby("cell").agg(n_px=("ndti", "size"), ndti=("ndti", "median"), spm=("spm", "median"),
                                            red=("red", "median"))
                agg = agg[agg["n_px"] >= 5].round({"ndti": 4, "spm": 2, "red": 4}).reset_index()
                agg.insert(0, "date", row.date)
                agg.to_csv(cdir / f"{row.id}.csv", index=False)
            else:
                pd.DataFrame().to_csv(cdir / f"{row.id}.csv", index=False)
            with lock:
                if row.id not in done:
                    for idx, nd, ls in upd:
                        acc_nd[season, idx] += nd
                        acc_ls[season, idx] += ls
                        acc_n[season, idx] += 1
                    done.add(row.id)
        finally:
            for d in ds.values():
                d.close()

    todo = [r for r in scenes[scenes["tile"] == t].itertuples() if r.id not in done]
    print(f"{t}: {npx:,} river pixels, {len(blocks)} blocks, {len(todo)} scenes to do", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(WORKERS) as ex:
        futs = {ex.submit(process, r): r.id for r in todo}
        for k, f in enumerate(as_completed(futs), 1):
            try:
                f.result()
            except Exception as e:
                print(t, "FAILED", futs[f], repr(e)[:120], flush=True)
            if k % 100 == 0 or k == len(todo):
                el = time.time() - t0
                print(f"{t} {k}/{len(todo)} {el / 60:.1f} min, eta {el / k * (len(todo) - k) / 60:.0f} min",
                      flush=True)
            if k % 150 == 0:
                save()
    save()
    print(t, "finished", flush=True)


for t in tiles:
    run_tile(t)
