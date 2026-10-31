"""Sentinel-2 water spread and turbidity for every water body >= 25 ha in the PROJECT area.

Same method as 22_reservoirs.py, but the water bodies are all JRC components >= 25 ha whose centre lies in the
project's own sub-watersheds (data/project_layers/project_layers_clean.gpkg), named from the project's cleaned
reservoir layer where they overlap. Output: data/project_layers/waterbodies_s2/<scene>.csv

Analysis mask per water body: its JRC maximum extent (occurrence >= 10 %) united with the connected 2022-25
Sentinel-2 water extent (water frequency >= 0.2), dilated by 40 m.

Per scene (scenes with <= 70 % cloud, five tiles over the project area):
  water_ha     clear pixels with MNDWI > 0 inside the mask, only when >= 90 % of the mask is cloud-free
  spm_red      median red-band Nechad SPM of interior water (2 pixels in from the shore), when >= 50 % is clear

    python scripts/knuckles/32_project_waterbodies.py --shard 0/4
Resumable; 33_project_report.py combines the per-scene files.
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
from rasterio.warp import Resampling, reproject, transform_bounds  # noqa: E402
from rasterio.windows import Window  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402

from sedrs import algorithms as alg  # noqa: E402
from sedrs import cog, s2grid  # noqa: E402
from sedrs.config import DATA_DIR  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--shard", default="0/1")
ap.add_argument("--max-cloud", type=float, default=70)
ap.add_argument("--from-date", default="2019-01-01")
ap.add_argument("--workers", type=int, default=4)
args = ap.parse_args()
cog.set_gdal_env()

import geopandas as gpd  # noqa: E402

P = DATA_DIR / "project_layers"
OUT = P / "waterbodies_s2"
OUT.mkdir(parents=True, exist_ok=True)
sw = gpd.read_file(P / "project_layers_clean.gpkg", layer="sub_watersheds").to_crs(4326)
named = gpd.read_file(P / "project_layers_clean.gpkg", layer="reservoirs").to_crs(4326)
with rasterio.open(DATA_DIR / "cog" / "jrc_occurrence.tif") as d_:
    _occ, _jtr = d_.read(1), d_.transform
_wl, _n = ndi.label(_occ >= 10, structure=np.ones((3, 3)))
_ids = np.arange(1, _n + 1)
_ha = ndi.sum(_occ >= 10, _wl, _ids) * 0.0757
_big = _ids[(_ha >= 25) & (_ha < 10000)]        # excludes the sea component
_cy, _cx = np.array(ndi.center_of_mass(_occ >= 10, _wl, _big)).T
_lon, _lat = _jtr * (_cx + 0.5, _cy + 0.5)
cand = gpd.GeoDataFrame({"wb_id": _big, "area_max_ha": _ha[_big - 1].round(1)},
                        geometry=gpd.points_from_xy(_lon, _lat), crs=4326)
cand = gpd.sjoin(cand, sw[["SubWS_ID", "SubWS_Name", "geometry"]], predicate="within").drop(columns="index_right")
cand["name"] = ""
for i, r in cand.iterrows():
    m = named[named.distance(r.geometry) < 0.01]               # ~1 km
    if len(m):
        cand.loc[i, "name"] = m.iloc[0]["name"]
cand["label"] = np.where(cand["name"] != "", cand["name"], "Tank " + cand["wb_id"].astype(str))
res = cand.reset_index(drop=True)
res.drop(columns="geometry").assign(lon=res.geometry.x.round(5), lat=res.geometry.y.round(5)).to_csv(
    P / "waterbodies_tracked.csv", index=False)

# ---------------------------------------------------------------- masks on the national 20 m grid
jtr, jcrs, wl = _jtr, "EPSG:4326", _wl          # same JRC labelling as the candidate list above
del _occ
freq = rasterio.open(DATA_DIR / "cog" / "water_freq_20m.tif")
ntr = s2grid.transform()
masks = []
for r in res.itertuples():
    comp = wl == r.wb_id
    ys, xs = np.nonzero(comp)
    lon0, lat1 = jtr * (xs.min() - 40, ys.min() - 40)
    lon1, lat0 = jtr * (xs.max() + 40, ys.max() + 40)
    x0, y0, x1, y1 = transform_bounds("EPSG:4326", s2grid.CRS, lon0, lat0, lon1, lat1)
    c0, r0 = int((x0 - s2grid.X0) // 20), int((s2grid.Y1 - y1) // 20)
    c1, r1 = int((x1 - s2grid.X0) // 20) + 1, int((s2grid.Y1 - y0) // 20) + 1
    sub_tr = rasterio.Affine(20, 0, s2grid.X0 + c0 * 20, 0, -20, s2grid.Y1 - r0 * 20)
    m = np.zeros((r1 - r0, c1 - c0), np.uint8)
    reproject(comp.astype(np.uint8), m, src_transform=jtr, src_crs=jcrs, dst_transform=sub_tr,
              dst_crs=s2grid.CRS, resampling=Resampling.nearest)
    f = freq.read(1, window=Window(c0, r0, c1 - c0, r1 - r0))
    jrc_body = m > 0
    union = jrc_body | (np.nan_to_num(f) >= 0.2)
    lab_u, _ = ndi.label(union, structure=np.ones((3, 3)))
    keep = np.unique(lab_u[jrc_body])               # only water connected to this reservoir, not nearby tanks
    m = np.isin(lab_u, keep[keep > 0])
    m = ndi.binary_dilation(m, iterations=2)
    masks.append({"name": r.label, "subws": r.SubWS_ID, "r0": r0, "c0": c0, "mask": m})

# ---------------------------------------------------------------- scenes
sc = pd.read_csv(DATA_DIR / "cog" / "scenes.csv")
sc = sc[(sc["cloud"] <= args.max_cloud) & (sc["date"] >= args.from_date)
        & sc["tile"].isin(["44NLP", "44PLQ", "44NMN", "44NMP", "44PMQ"])].sort_values("date")
i, n = (int(v) for v in args.shard.split("/"))
todo = [r for k, r in enumerate(sc.itertuples()) if k % n == i and not (OUT / f"{r.id}.csv").exists()]
print(f"{len(todo)} scenes to do")
TILE_GEO = {}


def process(row):
    if row.tile in TILE_GEO:
        r_t, c_t, h, w = TILE_GEO[row.tile]
        if not any(r_t <= m["r0"] and m["r0"] + m["mask"].shape[0] <= r_t + h and c_t <= m["c0"]
                   and m["c0"] + m["mask"].shape[1] <= c_t + w for m in masks):
            pd.DataFrame().to_csv(OUT / f"{row.id}.csv", index=False)
            return 0
    ds = s2grid.open_scene(row.prefix, ("B03", "B04", "B11", "SCL"))
    try:
        r_t, c_t = s2grid.offset(ds["SCL"].transform)
        h, w = ds["SCL"].height, ds["SCL"].width
        TILE_GEO[row.tile] = (r_t, c_t, h, w)
        recs = []
        for m in masks:
            rr, cc = m["r0"] - r_t, m["c0"] - c_t
            mh, mw = m["mask"].shape
            if rr < 0 or cc < 0 or rr + mh > h or cc + mw > w:
                continue
            b = s2grid.read_window(ds, Window(cc, rr, mw, mh))
            if (b["SCL"][m["mask"]] == 0).mean() > 0.01:          # outside the swath
                continue
            clear = ~np.isin(b["SCL"], cog.SCL_BAD) & m["mask"]
            frac = clear.sum() / m["mask"].sum()
            if frac < 0.5:            # turbidity needs only part of the water body clear
                continue
            g, r_, s = (b[k].astype("float32") * 1e-4 for k in ("B03", "B04", "B11"))
            with np.errstate(divide="ignore", invalid="ignore"):
                water = clear & ((g - s) / (g + s) > 0)
            interior = ndi.binary_erosion(water, iterations=2) & (s < alg.SWIR_WATER_THRESHOLD)
            spm = alg.nechad(r_[interior], *alg.NECHAD_SPM["S2"]["red"])
            recs.append({"reservoir": m["name"], "subws": m["subws"], "date": row.date, "scene": row.id,
                         "clear_frac": round(frac, 3),
                         # water spread only when >= 90 % of the water body is clear (else NaN)
                         "water_ha": round(water.sum() * 0.04, 1) if frac >= 0.9 else None,
                         "interior_px": int(interior.sum()),
                         "spm_red": round(float(np.nanmedian(spm)), 2) if interior.sum() >= 20 else None,
                         "red": round(float(np.nanmedian(r_[interior])), 4) if interior.sum() >= 20 else None})
        pd.DataFrame(recs).to_csv(OUT / f"{row.id}.csv", index=False)
        return len(recs)
    finally:
        for d in ds.values():
            d.close()


t0 = time.time()
with ThreadPoolExecutor(args.workers) as ex:
    futs = {ex.submit(process, r): r.id for r in todo}
    for k, f in enumerate(as_completed(futs), 1):
        try:
            f.result()
        except Exception as e:
            print("FAILED", futs[f], repr(e)[:150], flush=True)
        if k % 100 == 0 or k == len(todo):
            el = time.time() - t0
            print(f"{k}/{len(todo)} {el / 60:.1f} min eta {el / k * (len(todo) - k) / 60:.0f} min", flush=True)
print("finished")
