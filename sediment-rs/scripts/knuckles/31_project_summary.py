"""Per-sub-watershed summary for the project's own downstream boundaries.

Input: data/project_layers/project_layers_clean.gpkg (from 30_clean_project_layers.py).
Adds: relief and slope (Copernicus GLO-90), ESA WorldCover 2021 classes, JRC water bodies (tanks), Sentinel-2
river cells (national run) per sub-watershed. Output: data/project_layers/subws_summary.csv
"""
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from rasterio.features import rasterize  # noqa: E402
from rasterio.merge import merge  # noqa: E402
from rasterio.warp import Resampling, reproject  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402

from sedrs import cog  # noqa: E402
from sedrs.config import DATA_DIR, ROOT  # noqa: E402

warnings.filterwarnings("ignore")
cog.set_gdal_env()
P = DATA_DIR / "project_layers"
gpkg = P / "project_layers_clean.gpkg"
sw = gpd.read_file(gpkg, layer="sub_watersheds").to_crs(4326)
lon0, lat0, lon1, lat1 = sw.total_bounds + np.array([-0.05, -0.05, 0.05, 0.05])

# ---------------------------------------------------------------- DEM (GLO-90) for the project area
dem_path = P / "dem90_project.tif"
if not dem_path.exists():
    srcs = []
    for la in range(int(np.floor(lat0)), int(np.floor(lat1)) + 1):
        for lo in range(int(np.floor(lon0)), int(np.floor(lon1)) + 1):
            n = f"Copernicus_DSM_COG_30_N{la:02d}_00_E{lo:03d}_00_DEM"
            try:
                srcs.append(rasterio.open(f"/vsicurl/https://copernicus-dem-90m.s3.amazonaws.com/{n}/{n}.tif"))
            except Exception:
                pass
    arr, tr_ = merge(srcs, bounds=(lon0, lat0, lon1, lat1))
    with rasterio.open(dem_path, "w", driver="GTiff", width=arr.shape[2], height=arr.shape[1], count=1,
                       dtype="float32", crs="EPSG:4326", transform=tr_, compress="deflate") as d:
        d.write(arr[0].astype("float32"), 1)
with rasterio.open(dem_path) as d:
    dem, tr, crs = d.read(1).astype("float64"), d.transform, d.crs
shape = dem.shape
lat_c = tr.f + (np.arange(shape[0]) + 0.5) * tr.e
dx = (abs(tr.a) * 111320.0 * np.cos(np.radians(lat_c)))[:, None]
dy = abs(tr.e) * 110570.0
gy, gx = np.gradient(dem)
slope = np.degrees(np.arctan(np.hypot(gx / dx, gy / dy)))
lab = rasterize([(g, i + 1) for i, g in enumerate(sw.geometry)], out_shape=shape, transform=tr, dtype="int16")

# ---------------------------------------------------------------- WorldCover fractions on the DEM grid
WC = {10: "tree", 20: "shrub", 30: "grass", 40: "crop", 50: "built", 60: "bare", 80: "water", 90: "wetland"}
frac = {k: np.zeros(shape, "float32") for k in WC}
for tile in ("N06E078", "N06E081"):
    url = ("/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
           f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif")
    with rasterio.open(url) as d:
        b = d.bounds
        a0, a1 = max(b.left, lon0), min(b.right, lon1)
        if a0 >= a1:
            continue
        win = rasterio.windows.from_bounds(a0, lat0, a1, lat1, d.transform).round_offsets().round_lengths()
        arr = d.read(1, window=win, out_shape=(int(win.height // 3), int(win.width // 3)))
        wtr = d.window_transform(win) * rasterio.Affine.scale(win.width / arr.shape[1], win.height / arr.shape[0])
        for k in WC:
            tmp = np.zeros(shape, "float32")
            reproject((arr == k).astype("float32"), tmp, src_transform=wtr, src_crs=d.crs, dst_transform=tr,
                      dst_crs=crs, resampling=Resampling.average)
            frac[k] += tmp

# ---------------------------------------------------------------- JRC water bodies (tanks)
with rasterio.open(DATA_DIR / "cog" / "jrc_occurrence.tif") as d:
    win = rasterio.windows.from_bounds(lon0, lat0, lon1, lat1, d.transform).round_offsets().round_lengths()
    occ, jtr = d.read(1, window=win), d.window_transform(win)
wl, n = ndi.label(occ >= 10, structure=np.ones((3, 3)))
idx = np.arange(1, n + 1)
px_ha = (abs(jtr.a) * 111320 * np.cos(np.radians(8.0))) * (abs(jtr.e) * 110570) / 1e4
area_ha = ndi.sum(occ >= 10, wl, idx) * px_ha
perm_ha = ndi.sum(occ >= 75, wl, idx) * px_ha
cy, cx = np.array(ndi.center_of_mass(occ >= 10, wl, idx)).T
clon, clat = jtr * (cx + 0.5, cy + 0.5)
wb = gpd.GeoDataFrame({"area_max_ha": area_ha, "area_perm_ha": perm_ha},
                      geometry=gpd.points_from_xy(clon, clat), crs=4326)
wb = wb[wb.area_max_ha >= 1]
wb = gpd.sjoin(wb, sw[["SubWS_ID", "geometry"]], predicate="within")

# ---------------------------------------------------------------- Sentinel-2 river cells
cells = pd.read_csv(ROOT / "results" / "sentinel2_2019-2025" / "river_cells_metrics.csv")
cells = gpd.GeoDataFrame(cells, geometry=gpd.points_from_xy(cells.lon, cells.lat), crs=4326)
cells = gpd.sjoin(cells, sw[["SubWS_ID", "geometry"]], predicate="within")

# ---------------------------------------------------------------- per sub-watershed
cell_km2 = (dx / 1000) * (dy / 1000) * np.ones(shape)
rows = []
for i, r in enumerate(sw.itertuples(), start=1):
    m = lab == i
    w = wb[wb.SubWS_ID == r.SubWS_ID]
    c = cells[cells.SubWS_ID == r.SubWS_ID]
    rec = {"SubWS_ID": r.SubWS_ID, "SubWS_Name": r.SubWS_Name, "Basin": r.Basin_Name,
           "area_km2": round(float(cell_km2[m].sum()), 1), "n_MWS": r.n_MWS,
           "elev_mean_m": round(float(dem[m].mean()), 0), "slope_mean_deg": round(float(slope[m].mean()), 1),
           "steep_gt15deg_pct": round(100 * float((slope[m] > 15).mean()), 1)}
    for k, nm in WC.items():
        rec[f"{nm}_pct"] = round(100 * float(frac[k][m].mean()), 1)
    crop_bare = (frac[40] + frac[60])[m]
    rec["crop_bare_on_slopes_gt8deg_pct"] = round(100 * float((crop_bare * (slope[m] > 8)).mean()), 1)
    n_tanks = int((w.area_max_ha < 100).sum())
    wmax, wperm = float(w.area_max_ha.sum()), float(w.area_perm_ha.sum())
    rec.update({"water_bodies_ge1ha": len(w), "tanks_lt1km2": n_tanks,
                "tank_density_per_100km2": round(100 * n_tanks / max(rec["area_km2"], 1), 1),
                "water_max_km2": round(wmax / 100, 2),
                "seasonal_water_share_pct": round(100 * (1 - wperm / max(wmax, 1e-6)), 0),
                "river_cells": len(c),
                "river_spm_median": round(float(c.spm_all.median()), 1) if len(c) else None,
                "river_flood_ratio": round(float(c.flood_ratio.median()), 1) if c.flood_ratio.notna().any() else None})
    rows.append(rec)
out = pd.DataFrame(rows).sort_values("SubWS_ID")
out.to_csv(P / "subws_summary.csv", index=False)
pd.set_option("display.width", 250)
print(out[["SubWS_ID", "SubWS_Name", "Basin", "area_km2", "slope_mean_deg", "tree_pct", "crop_pct", "built_pct",
           "crop_bare_on_slopes_gt8deg_pct", "tanks_lt1km2", "tank_density_per_100km2", "seasonal_water_share_pct",
           "river_cells", "river_spm_median"]].to_string(index=False))
print("totals: area", round(out.area_km2.sum()), "km2 | tanks", out.tanks_lt1km2.sum(),
      "| river cells", out.river_cells.sum())
