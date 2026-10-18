"""Pass 3: aggregate per-scene river cells and stations into the national picture.

Outputs
  outputs/cog/river_cells.csv        1 km river cells: seasonal medians, observation counts
  outputs/cog/river_cells.geojson    same, as points (for web maps / GIS)
  outputs/cog/figures/*.png          national maps
  data/cog_analysis/stations/*.csv   station table in the format of scripts/05_analyse.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402
from rasterio.warp import transform  # noqa: E402

from sedrs import s2grid  # noqa: E402
from sedrs.config import DATA_DIR, OUT_DIR, load_settings  # noqa: E402
from sedrs.seasons import SEASONS, season_of  # noqa: E402

CELL = 50
NCOL = s2grid.W // CELL + 1
# Primary product: red-band Nechad SPM. In these narrow channels the NIR band
# carries strong bank-vegetation adjacency signal (Kelani: rho_nir ~0.038 where
# red-band SPM is ~20 g m-3), so NIR-based and red/NIR-blended estimates are
# biased high. The blend is kept as an upper bound (spm_blend_all).
PRIMARY = "SPM_red"
MIN_PX = 3            # valid 20 m pixels per cell-scene
MIN_SCENES = 3        # scenes per cell-season to report a median

src = DATA_DIR / "cog"
out = OUT_DIR / "cog"
fig_dir = out / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)
cfg = load_settings()

# ------------------------------------------------------------------ cells
files = sorted((src / "cells").glob("*.csv"))
cells = pd.concat([pd.read_csv(f) for f in files if f.stat().st_size > 0], ignore_index=True)
cells = (cells[cells["n"] >= MIN_PX].sort_values("n", ascending=False)
         .drop_duplicates(["cell", "date"]))
cells["season"] = season_of(cells["date"]).values
print(f"{len(files)} scenes, {len(cells)} cell-observations, {cells['cell'].nunique()} river cells")

from sedrs import algorithms as alg  # noqa: E402

D = alg.DOGLIOTTI
cells["T_red"] = alg.nechad(cells["red"], D["A_red"], D["C_red"])     # Dogliotti red-band turbidity
g = cells.groupby(["cell", "season"])
tab = g[PRIMARY].median().unstack().reindex(columns=SEASONS)
cnt = g.size().unstack().reindex(columns=SEASONS).fillna(0).astype(int)
tab = tab.where(cnt >= MIN_SCENES)
allm = cells.groupby("cell").agg(spm_all=(PRIMARY, "median"), turb_all=("T_red", "median"),
                                 ndti_all=("ndti", "median"), n_scenes=("date", "nunique"),
                                 spm_blend_all=("SPM_blend", "median"), red_all=("red", "median"),
                                 nir_all=("nir", "median"), px_median=("n", "median"))
res = allm.join(tab.add_prefix("spm_")).join(cnt.add_prefix("n_"))
row, col = res.index // NCOL, res.index % NCOL
x = s2grid.X0 + (col + 0.5) * CELL * s2grid.RES
y = s2grid.Y1 - (row + 0.5) * CELL * s2grid.RES
lon, lat = transform(s2grid.CRS, "EPSG:4326", list(x), list(y))
res.insert(0, "lon", np.round(lon, 5))
res.insert(1, "lat", np.round(lat, 5))
# distance to the coast (km) on the 1 km cell grid; cells < 3 km are often lagoon / estuary reaches
from rasterio.features import rasterize  # noqa: E402
from rasterio.transform import from_origin  # noqa: E402
from rasterio.warp import transform_geom  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402

_ne = json.load(open(src / "ne" / "ne_10m_admin_0_countries.geojson"))
_lka = next(f for f in _ne["features"] if f["properties"].get("ADM0_A3") == "LKA")["geometry"]
_land = rasterize([(transform_geom("EPSG:4326", s2grid.CRS, _lka), 1)],
                  out_shape=(s2grid.H // CELL + 1, NCOL), dtype="uint8",
                  transform=from_origin(s2grid.X0, s2grid.Y1, CELL * s2grid.RES, CELL * s2grid.RES))
_dist = ndi.distance_transform_edt(_land)
res["coast_km"] = _dist[row, col].round(1)
res["wet_dry_ratio"] = res[["spm_SWM", "spm_SIM"]].max(axis=1) / res[["spm_NEM", "spm_FIM"]].min(axis=1)
res = res[res["n_scenes"] >= MIN_SCENES]
res.to_csv(out / "river_cells.csv", float_format="%.4g")

feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [r.lon, r.lat]},
          "properties": {k: (None if pd.isna(v) else round(float(v), 3))
                         for k, v in r.drop(["lon", "lat"]).items()} | {"cell": int(i)}}
         for i, r in res.iterrows()]
(out / "river_cells.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
print(f"{len(res)} cells with >= {MIN_SCENES} scenes")

# ------------------------------------------------------------------ maps
ne = json.load(open(src / "ne" / "ne_10m_admin_0_countries.geojson"))
lka = next(f for f in ne["features"] if f["properties"].get("ADM0_A3") == "LKA")["geometry"]
polys = lka["coordinates"] if lka["type"] == "MultiPolygon" else [lka["coordinates"]]


def basemap(ax):
    for p in polys:
        xy = np.asarray(p[0])
        ax.fill(xy[:, 0], xy[:, 1], color="#f2efe9", ec="#9a9a9a", lw=0.6, zorder=0)
    ax.set_xlim(79.5, 82.0)
    ax.set_ylim(5.85, 9.9)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


norm = LogNorm(vmin=2, vmax=200)
fig, axes = plt.subplots(1, 4, figsize=(15, 5.6), layout="constrained")
for ax, s in zip(axes, SEASONS):
    basemap(ax)
    v = res[f"spm_{s}"]
    ok = v.notna()
    sc = ax.scatter(res.loc[ok, "lon"], res.loc[ok, "lat"], c=v[ok], s=4, cmap="YlOrBr", norm=norm, lw=0)
    ax.set_title(f"{s}  ({ok.sum()} cells)", fontsize=10)
fig.colorbar(sc, ax=axes, shrink=0.6, label="Estimated SPM, red band (g m$^{-3}$), median of scenes")
fig.suptitle("Sentinel-2 river sediment signal by monsoon season, 2024–2025 (1 km river cells)", fontsize=12)
fig.savefig(fig_dir / "map_spm_by_season.png", dpi=180, bbox_inches="tight")
plt.close(fig)

fig, axes = plt.subplots(1, 3, figsize=(13, 5.8), layout="constrained")
for ax, (var, lab, nrm, cmap) in zip(axes, [
        ("spm_all", "Estimated SPM (red band), all seasons (g m$^{-3}$)", norm, "YlOrBr"),
        ("ndti_all", "NDTI (calibration-free)", plt.Normalize(-0.25, 0.25), "RdYlBu_r"),
        ("n_scenes", "Clear-sky scenes per cell", plt.Normalize(0, res["n_scenes"].quantile(0.95)), "viridis")]):
    basemap(ax)
    sc = ax.scatter(res["lon"], res["lat"], c=res[var], s=4, cmap=cmap, norm=nrm, lw=0)
    fig.colorbar(sc, ax=ax, shrink=0.55, label=lab)
fig.savefig(fig_dir / "map_overview.png", dpi=180, bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------------------------ stations
sfiles = sorted((src / "stations").glob("*.csv"))
sdf = pd.concat([pd.read_csv(f) for f in sfiles if f.stat().st_size > 1], ignore_index=True)
sdf["valid_fraction"] = sdf["red_count"] / sdf["potential"]
keep = (sdf["red_count"] >= cfg["masking"]["min_pixels"]) & (sdf["valid_fraction"] >= 0.5)
st_dir = DATA_DIR / "cog_analysis" / "stations"
st_dir.mkdir(parents=True, exist_ok=True)
sdf[keep].drop(columns=["potential", "valid_fraction"]).to_csv(st_dir / "stations_S2.csv", index=False)
print(f"stations: {len(sdf)} station-scene rows, {keep.sum()} pass QC")
print(sdf[keep].groupby("station").size().to_string())
