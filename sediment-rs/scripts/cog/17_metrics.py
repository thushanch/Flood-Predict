"""Derived river-cell metrics, longitudinal profiles and a hillshade base map.

Outputs (outputs/cog/):
  river_cells_metrics.csv     per cell: peak season, seasonal swing, flood-pulse ratio
  profiles.csv                Kalu, Kelani and Mahaweli cells ordered from the mouth
  hillshade.npz               Copernicus GLO-90 hillshade for the map figures

Flood pulse = median red-band SPM in the Cyclone Ditwah window (26 Nov - 12 Dec 2025)
divided by the cell's median over the rest of 2024-2025. SPM is capped at 500 g m-3
before the ratio because the red-band algorithm saturates above that.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from sedrs import cog  # noqa: E402
from sedrs.config import DATA_DIR, OUT_DIR  # noqa: E402
from sedrs.reaches import haversine_km  # noqa: E402
from sedrs.seasons import SEASONS, season_of  # noqa: E402

out = OUT_DIR / "cog"
EVENT = ("2025-11-26", "2025-12-12")
CAP = 500.0
MIN_SEASON_SCENES = 3

# ---------------------------------------------------------------- reach labels
# Rough reach labels for the profiles and summaries: cells within 3 km of the Natural Earth
# Mahaweli centreline, and boxes around the lower Kelani, lower Kalu, south-west and west-coast
# rivers (>= 2 km from the coast). Built from the current river_cells.csv every run, so the
# values always match the primary product.
import json  # noqa: E402

cells = pd.read_csv(out / "river_cells.csv")
_ne = json.load(open(DATA_DIR / "cog" / "ne" / "ne_10m_rivers_lake_centerlines.geojson"))
_mpts = np.array([pt for f in _ne["features"] if f["properties"].get("name") == "Mahaweli"
                  for line in (f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiLineString"
                               else [f["geometry"]["coordinates"]]) for pt in line])
BOXES = {"Kelani (lower)": (79.86, 80.25, 6.85, 7.02), "Kalu (lower)": (79.95, 80.45, 6.52, 6.75),
         "Gin/Nilwala (south)": (80.1, 80.6, 5.93, 6.3), "Deduru/Maha Oya (west)": (79.8, 80.2, 7.2, 7.7)}


def _reach(lon, lat, coast_km):
    d = np.sqrt(((_mpts[:, 0] - lon) * np.cos(np.radians(lat))) ** 2 + (_mpts[:, 1] - lat) ** 2) * 111
    if d.min() < 3:
        return "Mahaweli"
    for k, (a, b, c, e) in BOXES.items():
        if a <= lon <= b and c <= lat <= e and coast_km >= 2:
            return k
    return "other"


cells["reach"] = [_reach(r.lon, r.lat, r.coast_km) for r in cells.itertuples()]
cells.to_csv(out / "river_cells_labelled.csv", index=False, float_format="%.4g")
obs = pd.concat([pd.read_csv(f) for f in sorted((DATA_DIR / "cog" / "cells").glob("*.csv"))], ignore_index=True)
obs = obs[obs["n"] >= 3].sort_values("n", ascending=False).drop_duplicates(["cell", "date"])
obs["season"] = season_of(obs["date"]).values
obs["spm"] = obs["SPM_red"].clip(upper=CAP)

# ---------------------------------------------------------------- peak season and swing
sm = obs.groupby(["cell", "season"])["spm"].agg(["median", "count"]).reset_index()
sm = sm[sm["count"] >= MIN_SEASON_SCENES].pivot(index="cell", columns="season", values="median")
sm = sm.reindex(columns=SEASONS)
enough = sm.notna().sum(axis=1) >= 3
peak = sm[enough].idxmax(axis=1).rename("peak_season")
swing = (sm[enough].max(axis=1) / sm[enough].min(axis=1)).rename("seasonal_swing")

# ---------------------------------------------------------------- flood pulse
in_event = obs["date"].between(*EVENT)
ev = obs[in_event].groupby("cell")["spm"].agg(event_spm="median", event_scenes="count")
base = obs[~in_event].groupby("cell")["spm"].agg(base_spm="median", base_scenes="count")
flood = ev.join(base, how="inner")
flood = flood[flood["base_scenes"] >= 5]
flood["flood_ratio"] = flood["event_spm"] / flood["base_spm"]

m = cells.set_index("cell").join(peak).join(swing).join(flood)
m.to_csv(out / "river_cells_metrics.csv", float_format="%.4g")
print(f"cells {len(m)}: peak season for {m['peak_season'].notna().sum()}, "
      f"flood ratio for {m['flood_ratio'].notna().sum()}")
print("peak season counts:", m["peak_season"].value_counts().to_dict())
print("flood ratio quartiles:", m["flood_ratio"].quantile([.25, .5, .75]).round(2).to_dict())

# ---------------------------------------------------------------- longitudinal profiles
# Kelani and Kalu start at their mouths. Mahaweli cells stop ~25 km short of Koddiyar Bay
# (coast exclusion, estuary distributaries), so its profile starts at the lowest main-stem
# cell near Somawathiya and may jump the 20-40 km gaps where the river runs through
# reservoirs; distances across those gaps are straight-line and therefore approximate.
MOUTH = {"Kelani (lower)": (79.870, 6.980), "Kalu (lower)": (79.958, 6.575), "Mahaweli": (81.180, 8.110)}
MAX_JUMP_KM = {"Kelani (lower)": 3.0, "Kalu (lower)": 3.0, "Mahaweli": 45.0}


def chain(sub, mouth, max_jump):
    """Greedy nearest-neighbour walk upstream from the cell closest to the mouth."""
    pts = sub[["lon", "lat"]].to_numpy()
    left = set(range(len(pts)))
    cur = min(left, key=lambda i: haversine_km(pts[i], mouth))
    order, dist, km = [cur], [haversine_km(pts[cur], mouth)], haversine_km(pts[cur], mouth)
    left.remove(cur)
    while left:
        nxt = min(left, key=lambda i: haversine_km(pts[i], pts[cur]))
        d = haversine_km(pts[nxt], pts[cur])
        if d > max_jump:
            break
        km += d
        order.append(nxt)
        dist.append(km)
        left.remove(nxt)
        cur = nxt
    return sub.iloc[order].assign(km_from_mouth=np.round(dist, 2))


prof = []
for reach, mouth in MOUTH.items():
    sub = m.reset_index()
    sub = sub[sub["reach"] == reach]
    c = chain(sub, mouth, MAX_JUMP_KM[reach])
    print(f"{reach}: {len(c)} of {len(sub)} cells chained, {c['km_from_mouth'].max():.0f} km")
    prof.append(c)
prof = pd.concat(prof)
prof.to_csv(out / "profiles.csv", index=False, float_format="%.4g")

# ---------------------------------------------------------------- hillshade (Copernicus GLO-90)
hs_path = out / "hillshade.npz"
if not hs_path.exists():
    import rasterio
    from matplotlib.colors import LightSource
    from rasterio.merge import merge

    cog.set_gdal_env()
    srcs = []
    for lat in range(5, 10):
        for lon in range(79, 82):
            name = f"Copernicus_DSM_COG_30_N{lat:02d}_00_E{lon:03d}_00_DEM"
            url = f"/vsicurl/https://copernicus-dem-90m.s3.amazonaws.com/{name}/{name}.tif"
            try:
                srcs.append(rasterio.open(url))
            except Exception:
                pass                                   # ocean tiles do not exist
    dem, tr = merge(srcs, bounds=(79.5, 5.85, 82.0, 9.9))
    dem = dem[0].astype("float32")
    dy = abs(tr.e) * 111320.0
    dx = tr.a * 111320.0 * np.cos(np.radians(7.8))
    hs = LightSource(azdeg=315, altdeg=40).hillshade(dem, vert_exag=2.0, dx=dx, dy=dy)
    np.savez_compressed(hs_path, hillshade=hs.astype("float16"), dem=dem.astype("float16"),
                        extent=np.array([tr.c, tr.c + tr.a * dem.shape[1], tr.f + tr.e * dem.shape[0], tr.f]))
    print("hillshade", hs.shape, f"{len(srcs)} DEM tiles")
