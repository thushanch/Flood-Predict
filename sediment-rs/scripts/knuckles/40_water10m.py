"""10 m water frequency and water objects (tanks, river channels) for the project area.

1. Project grid (10 m, UTM 44N) over the cleaned project sub-watersheds; tile ownership; blocks to read.
2. Water frequency from low-cloud Sentinel-2 scenes (2017-2025, up to N per tile and calendar month):
   water = SCL clear and NDWI (B03, B08) > 0, counted over clear views.
3. Water objects:
   - tanks/reservoirs: water seen in >= 15 % of clear views, with a core at least 50 m wide (opening with a
     5 x 5 disk), >= 2 ha, and water in >= 50 % of views somewhere in it (excludes paddy flooded for a few weeks);
     long, narrow wide-water bodies (the Mahaweli) are classed as river, not tank;
   - river channels: remaining water (>= 15 % of views) within 300 m of the project river lines, in elongated
     pieces (>= 300 m long, mean width <= 60 m), plus the wide rivers; grouped into 1 km river cells.

    python scripts/knuckles/40_water10m.py [--max-per-month 6]
Writes data/project_layers/s2_10m/: grid.json, blocks.json, subws.tif, water_valid.tif, water_count.tif,
water_freq.tif, objects.tif (tank ids 1..N; river-cell ids 100001..), objects.csv
"""
import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from rasterio.features import rasterize  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402

from sedrs import cog  # noqa: E402
from sedrs import s2_10m as g10  # noqa: E402
from sedrs.config import DATA_DIR  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--max-per-month", type=int, default=6)
ap.add_argument("--max-cloud", type=float, default=15)
ap.add_argument("--workers", type=int, default=24)
ap.add_argument("--objects-only", action="store_true", help="skip the frequency pass (reuse saved counts)")
args = ap.parse_args()
cog.set_gdal_env()

P = DATA_DIR / "project_layers"
OUT = P / "s2_10m"
OUT.mkdir(parents=True, exist_ok=True)
gpkg = P / "project_layers_clean.gpkg"
sw = gpd.read_file(gpkg, layer="sub_watersheds").to_crs(g10.CRS).sort_values("SubWS_ID").reset_index(drop=True)


def project_scenes():
    a = pd.read_csv(DATA_DIR / "cog" / "scenes.csv")
    b = DATA_DIR / "cog" / "scenes_2017_2018_project.csv"
    if b.exists():
        a = pd.concat([a, pd.read_csv(b)])
    a = a[a["tile"].isin(g10.TILES)].drop_duplicates("id")
    return a.sort_values(["date", "tile", "id"]).reset_index(drop=True)


scenes = project_scenes()
grid = g10.make_grid(sw.geometry)
meta_path = OUT / "grid.json"
if meta_path.exists():
    grid, tile_ul = g10.load_meta(meta_path)
else:
    tile_ul = g10.tile_ul_from_scenes(scenes)
    g10.save_meta(meta_path, grid, tile_ul)
TR = grid.transform
prof = {"driver": "GTiff", "width": grid.width, "height": grid.height, "count": 1, "crs": g10.CRS,
        "transform": TR, "compress": "deflate", "tiled": True, "blockxsize": 512, "blockysize": 512}
print(f"grid {grid.width} x {grid.height} px (10 m)")

subws = rasterize([(geom, i + 1) for i, geom in enumerate(sw.geometry)], out_shape=(grid.height, grid.width),
                  transform=TR, dtype="uint8")
with rasterio.open(OUT / "subws.tif", "w", dtype="uint8", **prof) as d:
    d.write(subws, 1)
(OUT / "subws_ids.json").write_text(json.dumps(list(sw["SubWS_ID"])))
inarea = ndi.binary_dilation(subws > 0, iterations=30)          # 300 m around the project area
owner = g10.ownership(grid, tile_ul)
blocks = g10.blocks_for(grid, tile_ul, owner, inarea)
for b in blocks:                                                 # pixels this block is responsible for
    b["npx"] = int(((owner[b["gr0"]:b["gr0"] + b["gh"], b["gc0"]:b["gc0"] + b["gw"]] == b["k"])
                    & inarea[b["gr0"]:b["gr0"] + b["gh"], b["gc0"]:b["gc0"] + b["gw"]]).sum())
(OUT / "blocks.json").write_text(json.dumps(blocks))
np.save(OUT / "owner.npy", owner)
print(len(blocks), "blocks:", pd.Series([b["tile"] for b in blocks]).value_counts().to_dict())

# ------------------------------------------------------------------ water frequency
if not args.objects_only:
    sel = scenes[scenes["cloud"] <= args.max_cloud].copy()
    sel["month"] = sel["date"].str[5:7]
    # spread over years: within each tile-month take evenly spaced scenes
    pick = []
    for _, gsel in sel.groupby(["tile", "month"]):
        idx = np.linspace(0, len(gsel) - 1, min(args.max_per_month, len(gsel))).round().astype(int)
        pick.append(gsel.iloc[np.unique(idx)])
    sel = pd.concat(pick)
    print(len(sel), "scenes for water frequency:", sel["tile"].value_counts().to_dict())
    valid_n = np.zeros((grid.height, grid.width), np.uint16)
    water_n = np.zeros((grid.height, grid.width), np.uint16)
    lock = threading.Lock()
    by_tile = {t: [b for b in blocks if b["tile"] == t] for t in g10.TILES}

    def run(row):
        ds = g10.open_bands(row.prefix, ("B03", "B08", "SCL"))
        try:
            for b in by_tile[row.tile]:
                x = g10.read_block(ds, b, ("B03", "B08"))
                sl = (slice(b["gr0"], b["gr0"] + b["gh"]), slice(b["gc0"], b["gc0"] + b["gw"]))
                mine = (owner[sl] == b["k"]) & inarea[sl]
                clear = mine & ~np.isin(x["SCL"], cog.SCL_BAD) & np.isfinite(x["B03"]) & np.isfinite(x["B08"])
                if not clear.any():
                    continue
                with np.errstate(divide="ignore", invalid="ignore"):
                    ndwi = (x["B03"] - x["B08"]) / (x["B03"] + x["B08"])
                wat = clear & (ndwi > 0)
                with lock:
                    valid_n[sl] += clear
                    water_n[sl] += wat
        finally:
            for d in ds.values():
                d.close()

    t0 = time.time()
    with ThreadPoolExecutor(args.workers) as ex:
        futs = {ex.submit(run, r): r.id for r in sel.itertuples()}
        for k, f in enumerate(as_completed(futs), 1):
            try:
                f.result()
            except Exception as e:
                print("FAILED", futs[f], repr(e)[:120], flush=True)
            if k % 25 == 0 or k == len(futs):
                el = time.time() - t0
                print(f"{k}/{len(futs)} {el / 60:.1f} min, eta {el / k * (len(futs) - k) / 60:.0f} min", flush=True)
    for name, arr in (("water_valid", valid_n), ("water_count", water_n)):
        with rasterio.open(OUT / f"{name}.tif", "w", dtype="uint16", **prof) as d:
            d.write(arr, 1)

# ------------------------------------------------------------------ water objects (memory-light)
owner = None                                                      # free memory
with rasterio.open(OUT / "water_valid.tif") as d:
    valid_n = d.read(1)
with rasterio.open(OUT / "water_count.tif") as d:
    pct = np.where(valid_n >= 8, np.round(100.0 * d.read(1) / np.maximum(valid_n, 1)), 255).astype(np.uint8)
valid_n = None
with rasterio.open(OUT / "water_freq.tif", "w", dtype="uint8", nodata=255, **prof) as d:
    d.write(pct, 1)
pct[pct == 255] = 0
pct[~inarea] = 0
inarea = None

from skimage.measure import regionprops  # noqa: E402
from skimage.morphology import disk, skeletonize  # noqa: E402

# tanks
wmax = ndi.binary_closing(pct >= 15, structure=np.ones((3, 3)))
core = ndi.binary_opening(wmax, structure=disk(2))               # >= ~50 m wide
core_lab, n_core = ndi.label(core, structure=np.ones((3, 3)))
del core
wide_river = np.zeros(n_core + 1, bool)
for p in regionprops(core_lab):                                   # long, narrow wide water = river (Mahaweli)
    length = max(p.axis_major_length, 1) * 10
    width = p.area * 100 / length
    if length >= 3000 and width < 300 and length / width > 15:
        wide_river[p.label] = True
wide = wide_river[core_lab]
tank_core = (core_lab > 0) & ~wide
del core_lab
tank_zone = ndi.binary_dilation(tank_core, structure=disk(3)) & wmax
del tank_core
tank_lab, n_tank = ndi.label(tank_zone, structure=np.ones((3, 3)))
del tank_zone
ids = np.arange(1, n_tank + 1)
area_px = ndi.sum(tank_lab > 0, tank_lab, ids)
fmax = ndi.maximum(pct, tank_lab, ids)
keep = (area_px >= 200) & (fmax >= 50)
remap = np.zeros(n_tank + 1, np.int32)
remap[ids[keep]] = np.arange(1, keep.sum() + 1)
objects = remap[tank_lab]
del tank_lab
print(f"tanks: {keep.sum()} kept of {n_tank} candidates (>= 2 ha and water in >= 50 % of views somewhere)", flush=True)

# river channels: water in >= 5 % of clear views within 100 m of project rivers of Strahler order >= 3,
# outside tanks, in elongated pieces; plus the wide rivers
riv = gpd.read_file(gpkg, layer="rivers").to_crs(g10.CRS)
riv = riv[riv["strahler"] >= 3]
near_riv = rasterize([(geom.buffer(100), 1) for geom in riv.geometry], out_shape=(grid.height, grid.width),
                     transform=TR, dtype="uint8").astype(bool)
wide_zone = ndi.binary_dilation(wide, iterations=3)
del wide
cand = (pct >= 5) & (near_riv | wide_zone) & ~ndi.binary_dilation(objects > 0, iterations=3)
cand = ndi.binary_closing(cand, structure=np.ones((3, 3))) & ~(objects > 0)
del near_riv, wmax
rl, nr = ndi.label(cand, structure=np.ones((3, 3)))
rid = np.arange(1, nr + 1)
r_area = ndi.sum(cand, rl, rid)
r_len = ndi.sum(skeletonize(cand), rl, rid) * 10.0
r_width = r_area * 100 / np.maximum(r_len, 10)
touches_wide = ndi.maximum(wide_zone, rl, rid) > 0
del wide_zone, cand
keep_r = ((r_len >= 200) & (r_width <= 60)) | touches_wide
rows, cols = np.nonzero(np.isin(rl, rid[keep_r]))
del rl
print(f"river channels: {keep_r.sum()} pieces, {len(rows) * 0.01:.0f} ha, {r_len[keep_r].sum() / 1000:.0f} km "
      "of channel skeleton", flush=True)

# 1 km river cells on the UTM km grid
cx = np.floor((grid.x0 + (cols + 0.5) * 10) / 1000).astype(np.int64)
cy = np.floor((grid.y1 - (rows + 0.5) * 10) / 1000).astype(np.int64)
uk, inv, cnt = np.unique(cx * 10000 + cy, return_inverse=True, return_counts=True)
ok = cnt >= 10                                                    # >= 0.1 ha of channel water in the cell
cell_id = np.where(ok, 100001 + np.cumsum(ok) - 1, 0)
objects[rows, cols] = cell_id[inv]
with rasterio.open(OUT / "objects.tif", "w", dtype="int32", nodata=0, **prof) as d:
    d.write(objects, 1)

# ------------------------------------------------------------------ object table (from object pixels only)
orr, occ = np.nonzero(objects)
lab = objects[orr, occ]
fr = pct[orr, occ].astype(float)
swv = subws[orr, occ]
del objects, pct
uid, inv = np.unique(lab, return_inverse=True)
n = np.bincount(inv)
xs = grid.x0 + (np.bincount(inv, occ) / n + 0.5) * 10
ys = grid.y1 - (np.bincount(inv, orr) / n + 0.5) * 10
fmean = np.bincount(inv, fr) / n
sw_major = np.array([np.bincount(swv[inv == k], minlength=len(sw) + 1)[1:].argmax() + 1
                     if (swv[inv == k] > 0).any() else 0 for k in range(len(uid))])
tab = gpd.GeoDataFrame({"obj_id": uid, "kind": np.where(uid > 100000, "river", "tank"),
                        "area_ha": np.round(n * 0.01, 2), "mean_water_pct": np.round(fmean, 1)},
                       geometry=gpd.points_from_xy(xs, ys), crs=g10.CRS)
ids_sw = [""] + list(sw["SubWS_ID"])
tab["SubWS_ID"] = [ids_sw[i] for i in sw_major]
named = gpd.read_file(gpkg, layer="reservoirs").to_crs(g10.CRS)
added = gpd.read_file(gpkg, layer="reservoirs_added_from_satellite").to_crs(g10.CRS)
named = pd.concat([named[["name", "geometry"]], added[["name", "geometry"]]])
tab["name"] = ""
tk = tab["kind"] == "tank"
j = gpd.sjoin_nearest(tab[tk][["obj_id", "geometry"]], named, max_distance=500, distance_col="d")
j = j.sort_values("d").drop_duplicates("obj_id")
tab.loc[tk, "name"] = tab.loc[tk, "obj_id"].map(dict(zip(j["obj_id"], j["name"]))).fillna("")
ll = tab.to_crs(4326)
tab["lon"], tab["lat"] = ll.geometry.x.round(5), ll.geometry.y.round(5)
tab.drop(columns=["geometry"]).to_csv(OUT / "objects.csv", index=False)
inside = tab[tab["SubWS_ID"] != ""]
print(inside.groupby("kind").agg(n=("obj_id", "size"), ha=("area_ha", "sum")).round(0).to_string())
print("named tanks:", (inside["name"] != "").sum(), "| river cells per basin prefix:",
      inside[inside["kind"] == "river"]["SubWS_ID"].str[:2].value_counts().to_dict())
