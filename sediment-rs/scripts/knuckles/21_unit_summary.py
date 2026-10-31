"""Per-sub-watershed summary and tank/reservoir inventory for the Knuckles downstream area.

Inputs: data/knuckles/subwatersheds.tif (20_subwatersheds.py), data/cog/jrc_occurrence.tif,
results/.../river_cells_metrics.csv, ESA WorldCover 2021 (10 m, AWS Open Data), Copernicus GLO-90.

Outputs (data/knuckles/ and results/knuckles/):
  waterbodies.csv / .geojson   every JRC water body >= 1 ha (max extent = occurrence >= 10 %)
  unit_summary.csv             area, relief, slope, land cover, tanks, river-sediment statistics
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from rasterio.features import shapes  # noqa: E402
from rasterio.warp import Resampling, reproject  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402

from sedrs import cog  # noqa: E402
from sedrs.config import DATA_DIR, ROOT  # noqa: E402

K = DATA_DIR / "knuckles"
RES = ROOT / "results" / "knuckles"
RES.mkdir(parents=True, exist_ok=True)
cog.set_gdal_env()

UNIT_NAMES = {   # descriptive; river names to be confirmed against IWMI / Survey Department maps
    1: "Mahaweli main stem + upper catchment (incl. Victoria)", 2: "Amban Ganga (Matale to Elahera and Polonnaruwa)",
    3: "Lower Amban Ganga, northern tributary A", 9: "Lower Amban Ganga, northern tributary B",
    4: "Uva tributary (Uma Oya side)", 7: "Uva tributary (Badulu Oya side) A", 8: "Uva tributary B",
    5: "Right-bank tributary (east) A", 6: "Right-bank tributary near Manampitiya",
    10: "North Knuckles -> Kalu Ganga (Laggala)", 14: "North Knuckles tributary A", 15: "North Knuckles tributary B",
    11: "South Knuckles -> Hulu Ganga (to Victoria)", 12: "East Knuckles -> Mahaweli A (Heen Ganga side)",
    13: "East Knuckles -> Mahaweli B",
}
RESERVOIRS = {   # approximate centres, used only to name the largest water bodies (nearest within 5 km)
    "Victoria": (80.75, 7.27), "Randenigala": (80.89, 7.19), "Rantembe": (80.99, 7.21),
    "Kotmale": (80.60, 7.05), "Moragahakanda": (80.75, 7.68), "Kalu Ganga reservoir": (80.83, 7.55),
    "Bowatenna": (80.68, 7.66), "Minneriya": (80.88, 8.03), "Giritale": (80.92, 7.99), "Kaudulla": (80.92, 8.15),
    "Parakrama Samudra": (80.98, 7.91),
    "Ulhitiya-Ratkinda": (81.06, 7.45), "Polgolla": (80.64, 7.33),
}

units = {u["unit"]: u for u in json.load(open(K / "subwatersheds.json"))}
lab_ds = rasterio.open(K / "subwatersheds.tif")
lab = lab_ds.read(1)
tr, crs, shape = lab_ds.transform, lab_ds.crs, lab.shape
lat_c = tr.f + (np.arange(shape[0]) + 0.5) * tr.e
cell_km2 = np.broadcast_to((abs(tr.a) * 111.32 * np.cos(np.radians(lat_c)))[:, None] * (abs(tr.e) * 110.57), shape)

# ------------------------------------------------------------------ relief and slope (GLO-90)
dem = rasterio.open(K / "dem90.tif").read(1).astype("float64")
dy = abs(tr.e) * 110570.0
dx = (abs(tr.a) * 111320.0 * np.cos(np.radians(lat_c)))[:, None]
gy, gx = np.gradient(dem)
slope_deg = np.degrees(np.arctan(np.hypot(gx / dx, gy / dy)))

# ------------------------------------------------------------------ WorldCover 2021 -> class fractions on the DEM grid
WC = {10: "tree", 20: "shrub", 30: "grass", 40: "crop", 50: "built", 60: "bare", 80: "water", 90: "wetland"}
wc_frac = {k: np.zeros(shape, "float32") for k in WC}
for tile in ("N06E078", "N06E081"):
    url = f"/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
    with rasterio.open(url) as d:
        b = d.bounds
        lon0, lon1 = max(b.left, tr.c), min(b.right, tr.c + tr.a * shape[1])
        if lon0 >= lon1:
            continue
        win = rasterio.windows.from_bounds(lon0, tr.f + tr.e * shape[0], lon1, tr.f, d.transform).round_offsets()
        win = win.round_lengths()
        arr = d.read(1, window=win, out_shape=(int(win.height // 3), int(win.width // 3)))   # ~30 m
        wtr = d.window_transform(win) * rasterio.Affine.scale(win.width / arr.shape[1], win.height / arr.shape[0])
        for k in WC:
            tmp = np.zeros(shape, "float32")
            reproject((arr == k).astype("float32"), tmp, src_transform=wtr, src_crs=d.crs, dst_transform=tr,
                      dst_crs=crs, resampling=Resampling.average)
            wc_frac[k] += tmp

# ------------------------------------------------------------------ water bodies from JRC
with rasterio.open(DATA_DIR / "cog" / "jrc_occurrence.tif") as d:
    win = rasterio.windows.from_bounds(tr.c, tr.f + tr.e * shape[0], tr.c + tr.a * shape[1], tr.f, d.transform)
    win = win.round_offsets().round_lengths()
    occ = d.read(1, window=win)
    jtr = d.window_transform(win)
wmax = occ >= 10
wl, n = ndi.label(wmax, structure=np.ones((3, 3)))
px_ha = (abs(jtr.a) * 111320 * np.cos(np.radians(7.7))) * (abs(jtr.e) * 110570) / 1e4
idx = np.arange(1, n + 1)
area_max = ndi.sum(wmax, wl, idx) * px_ha
area_perm = ndi.sum(occ >= 75, wl, idx) * px_ha
mean_occ = ndi.mean(occ, wl, idx)
cy, cx = np.array(ndi.center_of_mass(wmax, wl, idx)).T
clon, clat = jtr * (cx + 0.5, cy + 0.5)
wb = pd.DataFrame({"wb_id": idx, "lon": np.round(clon, 5), "lat": np.round(clat, 5), "area_max_ha": area_max.round(2),
                   "area_permanent_ha": area_perm.round(2), "mean_occurrence_pct": mean_occ.round(1)})
wb = wb[wb["area_max_ha"] >= 1.0]
r_, c_ = rasterio.transform.rowcol(tr, wb["lon"], wb["lat"])
r_, c_ = np.clip(r_, 0, shape[0] - 1), np.clip(c_, 0, shape[1] - 1)
wb["unit"] = lab[r_, c_]
wb = wb[wb["unit"] > 0].copy()


def name_of(row):
    if row.area_max_ha < 100:
        return ""
    best = min(RESERVOIRS, key=lambda k: (RESERVOIRS[k][0] - row.lon) ** 2 + (RESERVOIRS[k][1] - row.lat) ** 2)
    d_km = np.hypot((RESERVOIRS[best][0] - row.lon) * 110.3, (RESERVOIRS[best][1] - row.lat) * 110.6)
    return best if d_km < 4 else ""


wb["name"] = [name_of(r) for r in wb.itertuples()]
wb["class"] = np.where(wb["area_max_ha"] >= 100, "reservoir / large tank (>= 1 km2)",
                       np.where(wb["area_max_ha"] >= 10, "tank 10-100 ha", "small tank / pond 1-10 ha"))
wb = wb.sort_values("area_max_ha", ascending=False)
wb.to_csv(RES / "waterbodies.csv", index=False)
keep = set(wb["wb_id"])
feats = [{"type": "Feature", "geometry": g, "properties": {"wb_id": int(v)}}
         for g, v in shapes(wl.astype("int32"), mask=np.isin(wl, list(keep)) & (wl > 0), transform=jtr)
         if int(v) in keep and wb.set_index("wb_id").loc[int(v), "area_max_ha"] >= 10]
(K / "waterbodies_ge10ha.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))

# ------------------------------------------------------------------ river cells per unit
cells = pd.read_csv(ROOT / "results" / "sentinel2_2019-2025" / "river_cells_metrics.csv")
r_, c_ = rasterio.transform.rowcol(tr, cells["lon"], cells["lat"])
ok = (np.array(r_) >= 0) & (np.array(r_) < shape[0]) & (np.array(c_) >= 0) & (np.array(c_) < shape[1])
cells = cells[ok].copy()
cells["unit"] = lab[np.array(r_)[ok], np.array(c_)[ok]]
cells = cells[cells["unit"] > 0]

# ------------------------------------------------------------------ assemble
rows = []
for k, u in units.items():
    m = lab == k
    a = float(cell_km2[m].sum())
    rec = {"unit": k, "name": UNIT_NAMES.get(k, f"unit {k}"), "area_km2": round(a, 0),
           "knuckles_share_pct": u["knuckles_share_pct"], "drains_knuckles": u["drains_knuckles"],
           "elev_mean_m": round(float(dem[m].mean()), 0), "elev_max_m": round(float(dem[m].max()), 0),
           "slope_mean_deg": round(float(slope_deg[m].mean()), 1),
           "steep_gt20deg_pct": round(100 * float((slope_deg[m] > 20).mean()), 1)}
    for kk, nm in WC.items():
        rec[f"{nm}_pct"] = round(100 * float(wc_frac[kk][m].mean()), 1)
    # cropland or bare ground on slopes > 15 deg: a simple erosion-exposure indicator (not RUSLE)
    rec["crop_bare_on_steep_pct"] = round(100 * float(((wc_frac[40] + wc_frac[60])[m] * (slope_deg[m] > 15)).mean()), 1)
    w = wb[wb["unit"] == k]
    rec.update({"tanks_n": int((w["area_max_ha"] < 100).sum()), "reservoirs_n": int((w["area_max_ha"] >= 100).sum()),
                "water_max_km2": round(float(w["area_max_ha"].sum()) / 100, 1),
                "tank_density_per_100km2": round(100 * int((w["area_max_ha"] < 100).sum()) / a, 1),
                "named_reservoirs": ", ".join(n for n in w["name"] if n)})
    c = cells[cells["unit"] == k]
    rec.update({"river_cells": len(c), "spm_median": round(float(c["spm_all"].median()), 1) if len(c) else None,
                "spm_SIM": round(float(c["spm_SIM"].median()), 1) if c["spm_SIM"].notna().any() else None,
                "spm_SWM": round(float(c["spm_SWM"].median()), 1) if c["spm_SWM"].notna().any() else None,
                "flood_ratio_median": round(float(c["flood_ratio"].median()), 1) if c["flood_ratio"].notna().any()
                else None})
    rows.append(rec)
summary = pd.DataFrame(rows).sort_values("unit")
summary.to_csv(RES / "unit_summary.csv", index=False)
pd.set_option("display.width", 250)
print(summary[["unit", "name", "area_km2", "knuckles_share_pct", "slope_mean_deg", "tree_pct", "crop_pct",
               "crop_bare_on_steep_pct", "tanks_n", "reservoirs_n", "river_cells", "spm_median",
               "flood_ratio_median"]].to_string(index=False))
print("\nwater bodies >= 1 ha in catchment:", len(wb), "| reservoirs >= 1 km2:", (wb["area_max_ha"] >= 100).sum())
print(wb[wb["area_max_ha"] >= 100][["name", "unit", "area_max_ha", "area_permanent_ha", "mean_occurrence_pct",
                                    "lon", "lat"]].head(20).to_string(index=False))
