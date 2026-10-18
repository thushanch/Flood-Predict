"""Pass 2: per-scene sediment retrieval over river pixels.

    python scripts/cog/14_extract.py --national-from 2024-01-01 --national-to 2025-12-31 \
        --stations-from 2019-01-01 --max-cloud 70

* National period: every 1024x1024 block that contains river pixels is read,
  and per-scene medians are written for 1 km x 1 km river cells.
* Station period: only blocks containing station areas are read (cheap), for
  the long station time series.
Per-scene outputs go to data/cog/cells/<id>.csv and data/cog/stations/<id>.csv
so the run can be interrupted and resumed.
"""
import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from rasterio.windows import Window  # noqa: E402

from sedrs import cog, s2grid  # noqa: E402
from sedrs.config import DATA_DIR, load_settings  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--national-from", default="2024-01-01")
ap.add_argument("--national-to", default="2025-12-31")
ap.add_argument("--stations-from", default="2019-01-01")
ap.add_argument("--max-cloud", type=float, default=70)
ap.add_argument("--workers", type=int, default=6)
ap.add_argument("--limit", type=int)
ap.add_argument("--shard", default="0/1", help="i/n: process every n-th scene starting at i (run n processes)")
args = ap.parse_args()

cog.set_gdal_env()
out = DATA_DIR / "cog"
(out / "cells").mkdir(exist_ok=True)
(out / "stations").mkdir(exist_ok=True)
cfg = load_settings()
CELL = 50                                     # 50 px x 20 m = 1 km cells
NCOL_CELLS = s2grid.W // CELL + 1
BLOCK = 1024
VARS = ["SPM_blend", "T_dog", "ndti", "red", "green", "nir", "SPM_red", "SPM_nir"]

rivers = rasterio.open(out / "rivers_20m.tif").read(1).astype(bool)
water_any = rasterio.open(out / "water_any_20m.tif").read(1).astype(bool)
st = pd.read_csv(out / "stations.csv")
st = st[st["snapped"]].astype({"row": int, "col": int}).reset_index(drop=True)
station_label = np.zeros(rivers.shape, np.int16)          # 0 = none, i+1 = station i
station_px = np.zeros(rivers.shape, bool)                 # station AOI pixels (any source)
for i, s in enumerate(st.itertuples()):
    buf = int(s.aoi_radius_m / s2grid.RES)
    yy, xx = np.ogrid[-buf:buf + 1, -buf:buf + 1]
    layer = rivers if s.aoi_source == "river" else water_any
    sl = (slice(s.row - buf, s.row + buf + 1), slice(s.col - buf, s.col + buf + 1))
    m = (yy ** 2 + xx ** 2 <= buf ** 2) & layer[sl]
    station_label[sl][m] = i + 1
    station_px[sl] |= m
station_ids = list(st["id"])

sc = pd.read_csv(out / "scenes.csv")
sc = sc[(sc["cloud"] <= args.max_cloud) & (sc["date"] >= args.stations_from)
        & (sc["nodata_pct"] < 95)].sort_values("date", ascending=False)
if args.limit:
    sc = sc.head(args.limit)
shard_i, shard_n = (int(v) for v in args.shard.split("/"))
todo = [r for k, r in enumerate(sc.itertuples())
        if k % shard_n == shard_i and not (out / "stations" / f"{r.id}.csv").exists()]
print(f"{len(sc)} scenes selected, {len(todo)} to do")


TILE_GEO = {}          # tile -> (r0, c0, h, w); identical for every scene of a tile


def tile_has_stations(tile):
    r0, c0, h, w = TILE_GEO[tile]
    R0, C0 = max(r0, 0), max(c0, 0)
    return (station_label[R0:max(R0, r0 + h), C0:max(C0, c0 + w)] > 0).any()


def process(row):
    national = args.national_from <= row.date <= args.national_to
    if not national and row.tile in TILE_GEO and not tile_has_stations(row.tile):
        pd.DataFrame().to_csv(out / "stations" / f"{row.id}.csv", index=False)
        return row.id, 0, 0, 0
    ds = s2grid.open_scene(row.prefix)
    try:
        return _process(row, national, ds)
    finally:
        for d in ds.values():
            d.close()


def _process(row, national, ds):
    r0, c0 = s2grid.offset(ds["SCL"].transform)
    h, w = ds["SCL"].height, ds["SCL"].width
    TILE_GEO[row.tile] = (r0, c0, h, w)
    cell_rows, st_rows, nbytes_blocks = [], [], 0
    for br in range(0, h, BLOCK):
        for bc in range(0, w, BLOCK):
            bh, bw = min(BLOCK, h - br), min(BLOCK, w - bc)
            R0, C0 = r0 + br, c0 + bc
            if R0 < 0 or C0 < 0 or R0 + bh > s2grid.H or C0 + bw > s2grid.W:
                continue
            rv = rivers[R0:R0 + bh, C0:C0 + bw]
            lab = station_label[R0:R0 + bh, C0:C0 + bw]
            need = rv.any() if national else (lab > 0).any()
            if not need:
                continue
            nbytes_blocks += 1
            b = s2grid.read_window(ds, Window(bc, br, bw, bh))
            p = s2grid.products(b, row.offset)
            ok = p["valid"] & rv
            ok_st = p["valid"] & station_px[R0:R0 + bh, C0:C0 + bw]
            # stations: report potential (river px in AOI with data) and valid
            for i in np.unique(lab[lab > 0]):
                a = lab == i
                have = a & (b["SCL"] > 0)
                if not have.any():
                    continue
                v = a & ok_st
                rec = {"station": station_ids[i - 1], "date": row.date, "sensor": "S2",
                       "platform": row.platform, "scene": row.id,
                       "red_count": int(v.sum()), "SPM_blend_count": int((v & np.isfinite(p["SPM_blend"])).sum()),
                       "potential": int(have.sum())}
                for var in VARS:
                    x = p[var][v]
                    x = x[np.isfinite(x)]
                    q = np.percentile(x, [25, 50, 75]) if len(x) else [np.nan] * 3
                    rec.update({f"{var}_p25": q[0], f"{var}_p50": q[1], f"{var}_p75": q[2]})
                st_rows.append(rec)
            if national and ok.any():
                rr, cc = np.nonzero(ok)
                cid = ((R0 + rr) // CELL) * NCOL_CELLS + (C0 + cc) // CELL
                df = pd.DataFrame({"cell": cid, **{v: p[v][rr, cc] for v in VARS}})
                g = df.groupby("cell")
                agg = g.median()
                agg["n"] = g.size()
                cell_rows.append(agg.reset_index())
    if cell_rows:
        c = pd.concat(cell_rows)
        c = c.groupby("cell").apply(lambda g: g.loc[g["n"].idxmax()], include_groups=False).reset_index()
        c.insert(1, "date", row.date)
        c.insert(2, "scene", row.id)
        c.to_csv(out / "cells" / f"{row.id}.csv", index=False, float_format="%.5g")
    pd.DataFrame(st_rows).to_csv(out / "stations" / f"{row.id}.csv", index=False, float_format="%.5g")
    return row.id, nbytes_blocks, len(st_rows), sum(len(c) for c in cell_rows)


t0 = time.time()
done = 0
with ThreadPoolExecutor(args.workers) as ex:
    futs = {ex.submit(process, r): r.id for r in todo}
    for f in as_completed(futs):
        done += 1
        try:
            sid, nb, ns, nc = f.result()
        except Exception as e:
            print("FAILED", futs[f], repr(e)[:200], flush=True)
            continue
        if done % 25 == 0 or done == len(todo):
            el = time.time() - t0
            print(f"{done}/{len(todo)}  {el / 60:.1f} min  eta {el / done * (len(todo) - done) / 60:.0f} min",
                  flush=True)
print("finished")
