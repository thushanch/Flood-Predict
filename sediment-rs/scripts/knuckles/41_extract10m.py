"""Per-scene 10 m turbidity for every tank and river cell in the project area, plus sub-watershed NDVI.

Inputs from 40_water10m.py (data/project_layers/s2_10m/). For each Sentinel-2 scene (2017-2025, scene cloud
<= 90 %): SCL is read first for every block; the 10 m bands (B03, B04, B08) are read only for blocks holding a
water object that is at least 30 % cloud-free in this scene.

Valid water pixel (10 m): SCL clear and >= 50 m from cloud or cloud shadow, NDVI < 0.05, NIR < 0.15, and
  tanks:  NDWI > 0.05, >= 30 m inside this scene's shoreline, and SWIR (B11, 20 m) < 0.04. A first run that kept
          everything 10 m inside the shoreline and had no SWIR test read the dry-season tanks 3-7 x higher than
          the 20 m analysis: shallow margins where the bottom or wet mud shows through. This rule removes them.
  rivers: NDWI > 0.15 (purer water; channels are too narrow for a shoreline buffer or the 20 m SWIR test)
Per object and scene (>= 10 valid pixels): medians of green, red, NIR reflectance, NDTI = (R-G)/(R+G)
(Lacaux et al. 2007), SPM from red (Nechad et al. 2010/2016, S2 B4) and turbidity from red (Dogliotti et al.
2015). Water spread (tanks) only when >= 90 % of the tank's maximum extent is clear.
Per sub-watershed and scene: mean NDVI and share of land with NDVI < 0.3, over clear land in the blocks read.
Per 10 m water pixel: seasonal sums of NDTI and log10 SPM, for the 10 m maps.

    python scripts/knuckles/41_extract10m.py --shard 0/4
Resumable (per-scene CSVs + per-shard checkpoint). 43_relate10m.py combines the outputs.
"""
import argparse
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
from scipy import ndimage as ndi  # noqa: E402

from sedrs import algorithms as alg  # noqa: E402
from sedrs import cog  # noqa: E402
from sedrs import s2_10m as g10  # noqa: E402
from sedrs.config import DATA_DIR  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--shard", default="0/1")
ap.add_argument("--max-cloud", type=float, default=90)
ap.add_argument("--workers", type=int, default=10)
args = ap.parse_args()
cog.set_gdal_env()
si, sn = (int(v) for v in args.shard.split("/"))

D = DATA_DIR / "project_layers" / "s2_10m"
OBJ_DIR, VEG_DIR = D / "obj", D / "veg"
OBJ_DIR.mkdir(exist_ok=True)
VEG_DIR.mkdir(exist_ok=True)
grid, tile_ul = g10.load_meta(D / "grid.json")
blocks = json.loads((D / "blocks.json").read_text())
owner = np.load(D / "owner.npy")
with rasterio.open(D / "objects.tif") as d:
    objects = d.read(1)
with rasterio.open(D / "subws.tif") as d:
    subws = d.read(1)
n_sw = int(subws.max())
CLOUDY = (3, 8, 9, 10)                                             # shadow, cloud (medium, high), cirrus
SEAS = {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 10: 3, 11: 3}   # NEM FIM SWM SIM

# ---------------------------------------------------------------- per-block static arrays
off = 0
for b in blocks:
    sl = (slice(b["gr0"], b["gr0"] + b["gh"]), slice(b["gc0"], b["gc0"] + b["gw"]))
    own = owner[sl] == b["k"]
    ob = np.where(own, objects[sl], 0)
    b["own"] = own
    b["obj"] = ob
    b["sw"] = np.where(own, subws[sl], 0)
    b["pos"] = np.flatnonzero(ob > 0)
    b["off"] = off
    off += len(b["pos"])
    b["ids"] = np.unique(ob[ob > 0])
N_WPX = off
del owner, objects, subws
obj_px = {}                                                        # object id -> total owned pixels (per tile)
for b in blocks:
    ids, cnt = np.unique(b["obj"][b["obj"] > 0], return_counts=True)
    for i, c in zip(ids, cnt):
        obj_px[(b["tile"], int(i))] = obj_px.get((b["tile"], int(i)), 0) + int(c)
sw_px = {}
for b in blocks:
    c = np.bincount(b["sw"].ravel(), minlength=n_sw + 1)
    sw_px[b["tile"]] = sw_px.get(b["tile"], 0) + c
by_tile = {t: [b for b in blocks if b["tile"] == t] for t in g10.TILES}
print(f"{N_WPX:,} water-object pixels owned; blocks per tile:", {t: len(v) for t, v in by_tile.items()})

# ---------------------------------------------------------------- per-pixel seasonal accumulators (checkpointed)
ck = D / f"accum_shard{si}of{sn}.npz"
if ck.exists():
    z = np.load(ck, allow_pickle=True)
    acc_ndti, acc_lspm, acc_n = z["ndti"], z["lspm"], z["n"]
    done_acc = set(z["done"].tolist())
else:
    acc_ndti = np.zeros((4, N_WPX), np.float32)
    acc_lspm = np.zeros((4, N_WPX), np.float32)
    acc_n = np.zeros((4, N_WPX), np.uint16)
    done_acc = set()
lock = threading.Lock()


def save_ck():
    with lock:
        np.savez(ck, ndti=acc_ndti, lspm=acc_lspm, n=acc_n, done=np.array(sorted(done_acc), dtype=object))


A_SPM, C_SPM = alg.NECHAD_SPM["S2"]["red"]
A_T, C_T = alg.DOGLIOTTI["A_red"], alg.DOGLIOTTI["C_red"]


def process(row):
    tb = by_tile.get(row.tile, [])
    if not tb:
        return "none"
    ds = g10.open_bands(row.prefix)
    try:
        # phase 1: SCL for all blocks -> clear fraction per object
        scl = {}
        clear_cnt = {}
        for b in tb:
            s = g10.read_block({"SCL": ds["SCL"]}, b, bands=())["SCL"]
            cloudy = ndi.binary_dilation(np.isin(s, CLOUDY), iterations=5)       # 50 m buffer
            ok = b["own"] & ~np.isin(s, cog.SCL_BAD) & ~cloudy
            scl[id(b)] = ok
            if len(b["ids"]):
                ids, cnt = np.unique(b["obj"][ok & (b["obj"] > 0)], return_counts=True)
                for i, c in zip(ids, cnt):
                    clear_cnt[int(i)] = clear_cnt.get(int(i), 0) + int(c)
        cfrac = {i: c / obj_px[(row.tile, i)] for i, c in clear_cnt.items()}
        good = {i for i, f in cfrac.items() if f >= 0.3}
        recs, veg = [], np.zeros((3, n_sw + 1))
        season = SEAS[int(row.date[5:7])]
        pix_upd = []
        for b in tb:
            if not any(int(i) in good for i in b["ids"]):
                continue
            x = g10.read_block(ds, b, ("B03", "B04", "B08", "B11"))
            g, r, n, sw_ = x["B03"], x["B04"], x["B08"], x["B11"]
            clear = scl[id(b)] & np.isfinite(g) & np.isfinite(r) & np.isfinite(n)
            with np.errstate(divide="ignore", invalid="ignore"):
                ndwi = (g - n) / (g + n)
                ndvi = (n - r) / (n + r)
            wat = clear & (ndwi > 0)
            # vegetation over clear land
            land = clear & (b["obj"] == 0) & (b["sw"] > 0) & (ndwi < 0)
            swl = b["sw"][land]
            veg[0] += np.bincount(swl, weights=ndvi[land], minlength=n_sw + 1)
            veg[1] += np.bincount(swl, minlength=n_sw + 1)
            veg[2] += np.bincount(swl, weights=(ndvi[land] < 0.3), minlength=n_sw + 1)
            # water pixels
            ob = b["obj"]
            interior = ndi.binary_erosion(wat, structure=np.ones((3, 3)), iterations=3, border_value=1)
            base = clear & (ndvi < 0.05) & (n < 0.15)
            tank_ok = interior & (ndwi > 0.05) & (np.nan_to_num(sw_, nan=1.0) < alg.SWIR_WATER_THRESHOLD)
            v = base & np.where(ob > 100000, ndwi > 0.15, tank_ok) & (ob > 0)
            sel = ob[v]
            keep = np.isin(sel, list(good))
            if keep.any():
                gg, rr, nn = g[v][keep], r[v][keep], n[v][keep]
                recs.append(pd.DataFrame({"obj": sel[keep], "g": gg, "r": rr, "n": nn}))
            # tank water spread inside the maximum extent
            tk = (ob > 0) & (ob <= 100000)
            if tk.any():
                ids_w, cnt_w = np.unique(ob[tk & wat], return_counts=True)
                recs.append(pd.DataFrame({"obj": ids_w, "wpx": cnt_w}))
            # per-pixel accumulators
            vpos = np.flatnonzero(v.ravel()[b["pos"]])
            if len(vpos):
                rv = r.ravel()[b["pos"][vpos]]
                gv = g.ravel()[b["pos"][vpos]]
                pix_upd.append((b["off"] + vpos, alg.ndti(rv, gv).astype(np.float32),
                                np.log10(np.clip(alg.nechad(rv, A_SPM, C_SPM), 0.1, None)).astype(np.float32)))
        out = []
        if recs:
            allr = pd.concat(recs, ignore_index=True)
            px = allr.dropna(subset=["r"]) if "r" in allr else allr.iloc[0:0]
            if len(px):
                px = px.assign(ndti=alg.ndti(px["r"].values, px["g"].values),
                               spm=alg.nechad(px["r"].values, A_SPM, C_SPM),
                               T=alg.nechad(px["r"].values, A_T, C_T))
                med = px.groupby("obj")[["g", "r", "n", "ndti", "spm", "T"]].median()
                med["n_px"] = px.groupby("obj").size()
                med = med[med["n_px"] >= 10]
            else:
                med = pd.DataFrame()
            wpx = (allr.dropna(subset=["wpx"]).groupby("obj")["wpx"].sum() if "wpx" in allr
                   else pd.Series(dtype=float))
            for i in sorted(good):
                rec = {"obj": i, "date": row.date, "scene": row.id, "tile": row.tile, "clear_frac": round(cfrac[i], 3)}
                if i in med.index:
                    m = med.loc[i]
                    rec.update({"n_px": int(m["n_px"]), "green": round(m["g"], 4), "red": round(m["r"], 4),
                                "nir": round(m["n"], 4), "ndti": round(m["ndti"], 4), "spm": round(m["spm"], 2),
                                "T": round(m["T"], 2)})
                if i <= 100000 and cfrac[i] >= 0.9:
                    rec["water_ha"] = round(float(wpx.get(i, 0)) * 0.01, 2)
                out.append(rec)
        pd.DataFrame(out).to_csv(OBJ_DIR / f"{row.id}.csv", index=False)
        tot = sw_px[row.tile]
        vrow = [{"scene": row.id, "date": row.date, "tile": row.tile, "sw_idx": k, "land_px": int(veg[1][k]),
                 "owned_px": int(tot[k]), "ndvi_mean": round(veg[0][k] / veg[1][k], 4) if veg[1][k] else None,
                 "low_ndvi_share": round(veg[2][k] / veg[1][k], 4) if veg[1][k] else None}
                for k in range(1, n_sw + 1) if tot[k] > 0]
        pd.DataFrame(vrow).to_csv(VEG_DIR / f"{row.id}.csv", index=False)
        if row.id not in done_acc:
            with lock:
                for idx, nd, ls in pix_upd:
                    acc_ndti[season, idx] += nd
                    acc_lspm[season, idx] += ls
                    acc_n[season, idx] += 1
                done_acc.add(row.id)
        return len(out)
    finally:
        for d in ds.values():
            d.close()


sc = pd.read_csv(DATA_DIR / "cog" / "scenes.csv")
extra = DATA_DIR / "cog" / "scenes_2017_2018_project.csv"
if extra.exists():
    sc = pd.concat([sc, pd.read_csv(extra)])
sc = sc[sc["tile"].isin([t for t, v in by_tile.items() if v]) & (sc["cloud"] <= args.max_cloud)]
sc = sc.drop_duplicates("id").sort_values(["date", "id"]).reset_index(drop=True)
todo = [r for k, r in enumerate(sc.itertuples()) if k % sn == si
        and not ((OBJ_DIR / f"{r.id}.csv").exists() and r.id in done_acc)]
print(f"shard {si}/{sn}: {len(todo)} scenes to do (of {len(sc)} in total)", flush=True)
t0 = time.time()
with ThreadPoolExecutor(args.workers) as ex:
    futs = {ex.submit(process, r): r.id for r in todo}
    for k, f in enumerate(as_completed(futs), 1):
        try:
            f.result()
        except Exception as e:
            print("FAILED", futs[f], repr(e)[:150], flush=True)
        if k % 50 == 0 or k == len(todo):
            el = time.time() - t0
            print(f"{k}/{len(todo)} {el / 60:.1f} min, eta {el / k * (len(todo) - k) / 60:.0f} min", flush=True)
        if k % 200 == 0:
            save_ck()
save_ck()
print("finished", flush=True)
