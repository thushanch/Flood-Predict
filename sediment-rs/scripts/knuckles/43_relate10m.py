"""Combine the 10 m extraction and relate turbidity to rainfall, vegetation, tank water level and land use.

Inputs: data/project_layers/s2_10m/ (40_water10m.py, 41_extract10m.py), rain_persiann_subws.csv
(42_rain_persiann.py), subws_summary.csv (31_project_summary.py).

Turbidity measures (all from 10 m Sentinel-2 B03/B04/B08):
  NDTI  = (red - green) / (red + green)          Lacaux et al. 2007; a band ratio, so it does not depend on
                                                  the absolute reflectance calibration
  SPM   = Nechad red-band SPM (g m-3)             Nechad et al. 2010, S2 coefficients 2016
  T     = Dogliotti red-band turbidity (FNU)      Dogliotti et al. 2015
SPM and T are both monotonic in red reflectance, so they rank observations identically; NDTI is the
independent check.

Relations (observation level, within-object anomalies so that each tank or river cell is its own control):
  anomaly = NDTI minus that object's median NDTI
  rain    = PERSIANN-CDR rainfall over the object's sub-watershed, 1, 3, 7, 14 and 30 days before the overpass
  NDVI    = sub-watershed mean NDVI of clear land on the same date (+-8 days), as anomaly from its monthly mean
  fill    = tank water spread / its 95th-percentile spread (same date, +-10 days)
Regression: anomaly ~ z(log1p R7) + z(log1p R30) + z(NDVI anomaly) [+ z(fill)], OLS with standard errors
clustered by object. Cross-section: per sub-watershed median tank NDTI vs land cover, slope, rainfall, NDVI.

    python scripts/knuckles/43_relate10m.py
Writes data/project_layers/s2_10m/report/: object_summary.csv, subws_turbidity.csv, relations.json,
regression.csv, ndti_mean_10m.tif, spm_gmean_10m.tif, figures fig_t1..fig_t4 (png, pdf)
"""
import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import geopandas as gpd  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
import statsmodels.formula.api as smf  # noqa: E402
from scipy import stats  # noqa: E402

from sedrs import s2_10m as g10  # noqa: E402
from sedrs import trends  # noqa: E402
from sedrs.config import DATA_DIR  # noqa: E402
from sedrs.seasons import SEASONS, season_of  # noqa: E402

warnings.filterwarnings("ignore")
P = DATA_DIR / "project_layers"
D = P / "s2_10m"
R = D / "report"
R.mkdir(exist_ok=True)
EVENT = ("2025-11-26", "2025-12-12")
plt.rcParams.update({"font.family": "Inter", "font.size": 8, "axes.titlesize": 8.5, "axes.titleweight": "semibold",
                     "savefig.dpi": 300, "axes.edgecolor": "#8a8f8c", "axes.linewidth": 0.6})
INK, MUTED = "#1f2523", "#5c625f"
C_TANK, C_RIV, C_RAIN, C_VEG = "#2a78d6", "#c2571a", "#6b8fb3", "#3f8f4e"

objs = pd.read_csv(D / "objects.csv")
objs = objs[objs["SubWS_ID"].fillna("") != ""].set_index("obj_id")
ids_sw = json.loads((D / "subws_ids.json").read_text())

def rho(x, y):
    r = stats.spearmanr(x, y, nan_policy="omit")
    return round(float(r[0]), 3), round(float(r[1]), 4)


# ------------------------------------------------------------------ observations
files = [f for f in (D / "obj").glob("*.csv") if f.stat().st_size > 5]
obs = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
obs = obs[obs["obj"].isin(objs.index)]
obs["date"] = pd.to_datetime(obs["date"])
spread = obs.dropna(subset=["water_ha"])[["obj", "date", "water_ha", "clear_frac"]]
spread = spread.sort_values("clear_frac", ascending=False).drop_duplicates(["obj", "date"])
tur = obs.dropna(subset=["ndti"])
tur = tur[(tur["n_px"] >= 10) & tur["red"].between(0.005, 0.25) & tur["ndti"].between(-0.5, 0.5)]
tur = tur.sort_values("n_px", ascending=False).drop_duplicates(["obj", "date"]).sort_values(["obj", "date"])
tur["kind"] = objs.loc[tur["obj"], "kind"].values
tur["SubWS_ID"] = objs.loc[tur["obj"], "SubWS_ID"].values
tur["season"] = season_of(tur["date"]).values
tur["lspm"] = np.log10(tur["spm"].clip(lower=0.1))
print(f"{len(files)} scene files; {len(tur):,} turbidity observations of {tur['obj'].nunique()} objects "
      f"({tur['date'].dt.year.min()}-{tur['date'].dt.year.max()}); {len(spread):,} water-spread views")


def flag_dropouts(g, k=3):
    w = g["water_ha"].to_numpy()
    bad = np.zeros(len(w), bool)
    for i in range(len(w)):
        nb = np.r_[w[max(0, i - k):i], w[i + 1:i + 1 + k]]
        bad[i] = len(nb) >= 2 and w[i] < 0.5 * np.median(nb)
    return g[~bad]


spread = pd.concat([flag_dropouts(g.sort_values("date")) for _, g in spread.groupby("obj")], ignore_index=True)
cap = spread.groupby("obj")["water_ha"].quantile(0.95)
spread["fill"] = spread["water_ha"] / spread["obj"].map(cap)

# ------------------------------------------------------------------ per-object summary
rows = []
for oid, g in tur.groupby("obj"):
    if len(g) < 10:
        continue
    o = objs.loc[oid]
    seas = g.groupby("season")["spm"].median().reindex(SEASONS)
    seas_nd = g.groupby("season")["ndti"].median().reindex(SEASONS)
    ev = g[g["date"].between(*EVENT)]
    base = g[~g["date"].between(*EVENT)]
    m = g.set_index(g["date"].dt.to_period("M"))["spm"].groupby(level=0).median()
    m = m.reindex(pd.period_range(m.index.min(), m.index.max(), freq="M"))
    sk = trends.seasonal_kendall(m) if m.notna().sum() >= 24 else {}
    sp = spread[spread["obj"] == oid]
    rows.append({"obj_id": oid, "kind": o["kind"], "name": o["name"] if isinstance(o["name"], str) else "",
                 "SubWS_ID": o["SubWS_ID"], "area_ha": o["area_ha"], "lon": o["lon"], "lat": o["lat"],
                 "n_obs": len(g), "n_months": g["date"].dt.to_period("M").nunique(),
                 "ndti_median": round(g["ndti"].median(), 3), "spm_median": round(g["spm"].median(), 1),
                 "T_median": round(g["T"].median(), 1),
                 **{f"spm_{k}": round(v, 1) for k, v in seas.items()},
                 **{f"ndti_{k}": round(v, 3) for k, v in seas_nd.items()},
                 "peak_season": seas.idxmax() if seas.notna().any() else None,
                 "ditwah_ratio": round(ev["spm"].median() / base["spm"].median(), 1) if len(ev) else None,
                 "ditwah_ndti_rise": round(ev["ndti"].median() - base["ndti"].median(), 3) if len(ev) else None,
                 "drawdown_pct": round(100 * (1 - sp["water_ha"].quantile(0.05) / cap[oid]), 0)
                 if len(sp) >= 10 and cap.get(oid, 0) > 0 else None,
                 "trend_pct_per_yr": round(sk["pct_per_yr"], 1) if sk.get("pct_per_yr") is not None else None,
                 "trend_p": sk.get("p")})
osum = pd.DataFrame(rows)
# a reservoir name belongs to the largest object it matched; small tanks nearby lose it
osum["name"] = osum["name"].fillna("").str.replace(r" \(\d\)$", "", regex=True)
keep_name = osum[osum["name"] != ""].sort_values("area_ha").drop_duplicates("name", keep="last")["obj_id"]
osum.loc[~osum["obj_id"].isin(keep_name), "name"] = ""
osum["trend_q"] = trends.bh_fdr(osum["trend_p"].astype(float))
osum.to_csv(R / "object_summary.csv", index=False)
print(osum.groupby("kind").agg(n=("obj_id", "size"), obs=("n_obs", "median"), ndti=("ndti_median", "median"),
                               spm=("spm_median", "median"), ditwah=("ditwah_ratio", "median"),
                               rising=("trend_q", lambda q: int((q < 0.05).sum()))).to_string())

# ------------------------------------------------------------------ index agreement
rel = {}
for kind, g in tur.groupby("kind"):
    rel[f"{kind}_rho_ndti_lspm_pooled"] = round(stats.spearmanr(g["ndti"], g["lspm"], nan_policy="omit")[0], 3)
    an = g.assign(a=g["ndti"] - g.groupby("obj")["ndti"].transform("median"),
                  b=g["lspm"] - g.groupby("obj")["lspm"].transform("median"))
    rel[f"{kind}_rho_ndti_lspm_within"] = round(stats.spearmanr(an["a"], an["b"], nan_policy="omit")[0], 3)
med = osum.set_index("obj_id")
rel["objects_rho_ndti_spm_medians"] = rho(med["ndti_median"], med["spm_median"])[0]
rel["objects_rho_T_spm_medians"] = rho(med["T_median"], med["spm_median"])[0]

# ------------------------------------------------------------------ drivers: rainfall, NDVI, fill
rain = pd.read_csv(P / "rain_persiann_subws.csv", parse_dates=["date"]).set_index("date").asfreq("D")
WIN = (1, 3, 7, 14, 30)
acc = {k: rain.shift(1).rolling(k, min_periods=k).sum() for k in WIN}       # days d-k .. d-1
for k in WIN:
    a = acc[k].stack().rename(f"R{k}").reset_index().rename(columns={"level_1": "SubWS_ID"})
    tur = tur.merge(a, on=["date", "SubWS_ID"], how="left")
rain_ann = rain.groupby(rain.index.year).sum().mean()

veg = pd.concat([pd.read_csv(f) for f in (D / "veg").glob("*.csv") if f.stat().st_size > 5], ignore_index=True)
veg["date"] = pd.to_datetime(veg["date"])
veg = veg.dropna(subset=["ndvi_mean"])
veg["s_ndvi"] = veg["ndvi_mean"] * veg["land_px"]
veg["s_low"] = veg["low_ndvi_share"] * veg["land_px"]
vg = veg.groupby(["sw_idx", "date"])[["s_ndvi", "s_low", "land_px", "owned_px"]].sum()
vg = vg[vg["land_px"] >= 0.3 * vg["owned_px"]]
vg["ndvi"] = vg["s_ndvi"] / vg["land_px"]
vg["low"] = vg["s_low"] / vg["land_px"]
vg = vg.reset_index()
vg["SubWS_ID"] = [ids_sw[i - 1] for i in vg["sw_idx"]]
vg["month"] = vg["date"].dt.month
vg["ndvi_anom"] = vg["ndvi"] - vg.groupby(["SubWS_ID", "month"])["ndvi"].transform("mean")
vg = vg.sort_values("date")
tur = tur.sort_values("date")
tur = pd.merge_asof(tur, vg[["date", "SubWS_ID", "ndvi", "ndvi_anom", "low"]], on="date", by="SubWS_ID",
                    direction="nearest", tolerance=pd.Timedelta(days=8))
sp_ = spread.sort_values("date")[["date", "obj", "fill"]]
tur = pd.merge_asof(tur, sp_, on="date", by="obj", direction="nearest", tolerance=pd.Timedelta(days=10))
tur["a_ndti"] = tur["ndti"] - tur.groupby("obj")["ndti"].transform("median")
tur["a_lspm"] = tur["lspm"] - tur.groupby("obj")["lspm"].transform("median")
tur.to_csv(R / "observations.csv.gz", index=False)

for kind, g in tur.groupby("kind"):
    for k in WIN:
        h = g.dropna(subset=[f"R{k}"])
        rel[f"{kind}_rho_anom_R{k}"] = round(stats.spearmanr(h["a_ndti"], h[f"R{k}"], nan_policy="omit")[0], 3)
    h = g.dropna(subset=["ndvi_anom"])
    rel[f"{kind}_rho_anom_ndvi_anom"] = round(stats.spearmanr(h["a_ndti"], h["ndvi_anom"], nan_policy="omit")[0], 3)
    if kind == "tank":
        h = g.dropna(subset=["fill"])
        rel["tank_rho_anom_fill"] = round(stats.spearmanr(h["a_ndti"], h["fill"], nan_policy="omit")[0], 3)

reg_rows = []
for kind, g in tur.groupby("kind"):
    cols = ["a_ndti", "R7", "R30", "ndvi_anom"] + (["fill"] if kind == "tank" else [])
    h = g.dropna(subset=cols).copy()
    h["lR7"], h["lR30"] = np.log1p(h["R7"]), np.log1p(h["R30"])
    preds = ["lR7", "lR30", "ndvi_anom"] + (["fill"] if kind == "tank" else [])
    for c in preds:
        h[c] = (h[c] - h[c].mean()) / h[c].std()
    h["y"] = h["a_ndti"] / h["a_ndti"].std()
    fit = smf.ols("y ~ " + " + ".join(preds), data=h).fit(cov_type="cluster", cov_kwds={"groups": h["obj"]})
    for c in preds:
        reg_rows.append({"kind": kind, "predictor": c, "beta_std": round(fit.params[c], 3),
                         "ci_lo": round(fit.conf_int().loc[c, 0], 3), "ci_hi": round(fit.conf_int().loc[c, 1], 3),
                         "p": float(fit.pvalues[c]), "n_obs": int(fit.nobs), "n_objects": h["obj"].nunique(),
                         "r2": round(fit.rsquared, 3)})
reg = pd.DataFrame(reg_rows)
reg.to_csv(R / "regression.csv", index=False)
print(reg.to_string(index=False))

# ------------------------------------------------------------------ cross-section by sub-watershed
sws = pd.read_csv(P / "subws_summary.csv")
tk = osum[osum["kind"] == "tank"]
rv = osum[osum["kind"] == "river"]
agg = (tk.groupby("SubWS_ID").agg(tanks_10m=("obj_id", "size"), tank_ndti=("ndti_median", "median"),
                                  tank_spm=("spm_median", "median"), tank_peak=("peak_season",
                                                                               lambda x: x.mode().iloc[0]),
                                  tank_ditwah=("ditwah_ratio", "median"), tank_drawdown=("drawdown_pct", "median"))
       .join(rv.groupby("SubWS_ID").agg(river_cells_10m=("obj_id", "size"), river_ndti=("ndti_median", "median"),
                                        river_spm=("spm_median", "median"))
             , how="outer").reset_index())
vmean = vg.groupby("SubWS_ID").agg(ndvi_mean=("ndvi", "mean"), low_ndvi_share=("low", "mean"))
vamp = vg.groupby(["SubWS_ID", "month"])["ndvi"].mean().groupby(level=0).agg(lambda x: x.max() - x.min())
out = (sws[["SubWS_ID", "SubWS_Name", "Basin", "area_km2", "slope_mean_deg", "tree_pct", "crop_pct", "built_pct",
            "bare_pct", "tank_density_per_100km2"]]
       .merge(agg, on="SubWS_ID", how="left").merge(vmean, on="SubWS_ID", how="left"))
out["ndvi_seasonal_range"] = out["SubWS_ID"].map(vamp)
out["rain_mm_yr"] = out["SubWS_ID"].map(rain_ann).round(0)
out.round(3).to_csv(R / "subws_turbidity.csv", index=False)
cs = {}
for x in ("crop_pct", "tree_pct", "slope_mean_deg", "rain_mm_yr", "ndvi_mean", "low_ndvi_share",
          "ndvi_seasonal_range", "tank_density_per_100km2"):
    h = out.dropna(subset=[x, "tank_ndti"])
    r, p = stats.spearmanr(h[x], h["tank_ndti"], nan_policy="omit")
    cs[x] = {"rho": round(r, 3), "p": round(p, 3), "n": len(h)}
h = tk.dropna(subset=["area_ha", "ndti_median"])
cs["tank_size_vs_ndti"] = dict(zip(("rho", "p"), rho(np.log(h["area_ha"]), h["ndti_median"])), n=len(h))
h = tk.dropna(subset=["drawdown_pct", "ndti_median"])
cs["tank_drawdown_vs_ndti"] = dict(zip(("rho", "p"), rho(h["drawdown_pct"], h["ndti_median"])), n=len(h))
rel["cross_section_tank_ndti"] = cs
rel["counts"] = {"observations": int(len(tur)), "objects_with_10plus": int(len(osum)),
                 "tanks": int((osum["kind"] == "tank").sum()), "river_cells": int((osum["kind"] == "river").sum()),
                 "scene_files": len(files), "first": str(tur["date"].min().date()),
                 "last": str(tur["date"].max().date())}
(R / "relations.json").write_text(json.dumps(rel, indent=1))
print(json.dumps(rel, indent=1))

# ------------------------------------------------------------------ 10 m maps from the per-pixel accumulators
grid, tile_ul = g10.load_meta(D / "grid.json")
blocks = json.loads((D / "blocks.json").read_text())
owner = np.load(D / "owner.npy")
with rasterio.open(D / "objects.tif") as d:
    objects, prof = d.read(1), d.profile
pos_r, pos_c = [], []
for b in blocks:
    sl = (slice(b["gr0"], b["gr0"] + b["gh"]), slice(b["gc0"], b["gc0"] + b["gw"]))
    ob = np.where(owner[sl] == b["k"], objects[sl], 0)
    p = np.flatnonzero(ob > 0)
    pos_r.append(b["gr0"] + p // b["gw"])
    pos_c.append(b["gc0"] + p % b["gw"])
pos_r, pos_c = np.concatenate(pos_r), np.concatenate(pos_c)
del owner
sums = None
for f in sorted(D.glob("accum_shard*of4.npz")):
    z = np.load(f, allow_pickle=True)
    if sums is None:
        sums = [z["ndti"].astype(np.float64), z["lspm"].astype(np.float64), z["n"].astype(np.float64)]
    else:
        sums[0] += z["ndti"]
        sums[1] += z["lspm"]
        sums[2] += z["n"]
nd_all = sums[0].sum(0) / np.maximum(sums[2].sum(0), 1)
ls_all = sums[1].sum(0) / np.maximum(sums[2].sum(0), 1)
nobs = sums[2].sum(0)
ok = nobs >= 5
prof.update(dtype="float32", nodata=np.nan, count=5)
for name, allv, seasv in (("ndti_mean_10m", nd_all, sums[0] / np.maximum(sums[2], 1)),
                          ("spm_gmean_10m", 10 ** ls_all, 10 ** (sums[1] / np.maximum(sums[2], 1)))):
    with rasterio.open(R / f"{name}.tif", "w", **prof) as d:
        for band, (vals, mask) in enumerate([(allv, ok)] + [(seasv[s], sums[2][s] >= 3) for s in range(4)], 1):
            a = np.full(objects.shape, np.nan, np.float32)
            a[pos_r[mask], pos_c[mask]] = vals[mask]
            d.write(a, band)
        d.descriptions = ("all seasons", "NEM", "FIM", "SWM", "SIM")
print("10 m maps written; pixels with >= 5 valid views:", int(ok.sum()))

# ------------------------------------------------------------------ figures
sw = gpd.read_file(P / "project_layers_clean.gpkg", layer="sub_watersheds").to_crs(g10.CRS)
basins = gpd.read_file(P / "project_layers_clean.gpkg", layer="basins").to_crs(g10.CRS)
NDTI_CMAP, NDTI_LIM = "RdYlBu_r", (-0.25, 0.15)

# fig t1: overview (per-object median NDTI) + two 10 m zooms
fig = plt.figure(figsize=(7.2, 8.6))
ax = fig.add_axes([0.02, 0.30, 0.62, 0.62])
sw.boundary.plot(ax=ax, color="#9aa39f", lw=0.3)
basins.boundary.plot(ax=ax, color="#2d3a36", lw=0.9)
om = osum.copy()
xy = gpd.GeoSeries(gpd.points_from_xy(om["lon"], om["lat"]), crs=4326).to_crs(g10.CRS)
for kind, mk, s0 in (("tank", "o", 6), ("river", "s", 5)):
    k = (om["kind"] == kind).values
    ax.scatter(xy.x[k], xy.y[k], c=om.loc[k, "ndti_median"], cmap=NDTI_CMAP, vmin=NDTI_LIM[0], vmax=NDTI_LIM[1],
               s=s0 + (np.sqrt(om.loc[k, "area_ha"]) * 1.2 if kind == "tank" else 0), marker=mk,
               edgecolor=INK if kind == "tank" else "none", lw=0.25, zorder=3)
ax.set_aspect("equal")
ax.set_axis_off()
ax.set_title("Median NDTI per tank (circles) and 1 km river cell (squares)", loc="left")
zooms = [("Kala Wewa and Balalu Wewa (93-04)", 80.555, 8.005, 4000),
         ("Mahaweli at Minipe (60-10, 60-11)", 81.02, 7.30, 3500)]
for i, (title, lo, la, half) in enumerate(zooms):
    zx = gpd.GeoSeries(gpd.points_from_xy([lo], [la]), crs=4326).to_crs(g10.CRS)
    cx, cy = zx.x[0], zx.y[0]
    c0, r0 = int((cx - half - grid.x0) / 10), int((grid.y1 - (cy + half)) / 10)
    n_ = int(2 * half / 10)
    with rasterio.open(R / "ndti_mean_10m.tif") as d:
        a = d.read(1, window=rasterio.windows.Window(c0, r0, n_, n_))
    axz = fig.add_axes([0.66, 0.62 - i * 0.31, 0.32, 0.29])
    im = axz.imshow(a, cmap=NDTI_CMAP, vmin=NDTI_LIM[0], vmax=NDTI_LIM[1], interpolation="nearest",
                    extent=(cx - half, cx + half, cy - half, cy + half))
    axz.set_facecolor("#f1f2ef")
    axz.set_xticks([])
    axz.set_yticks([])
    axz.set_title(title, loc="left", fontsize=7)
    axz.plot([cx + half - 1200, cx + half - 200], [cy - half + 300] * 2, color=INK, lw=1.5)
    axz.text(cx + half - 700, cy - half + 450, "1 km", ha="center", fontsize=6)
    ax.add_patch(plt.Rectangle((cx - half, cy - half), 2 * half, 2 * half, fill=False, ec=INK, lw=0.7, zorder=4))
    ax.text(cx + half, cy + half, "AB"[i], fontsize=7, fontweight="bold", va="bottom")
    axz.text(0.02, 0.96, "AB"[i], transform=axz.transAxes, fontsize=8, fontweight="bold", va="top")
cax = fig.add_axes([0.06, 0.25, 0.5, 0.012])
cb = fig.colorbar(im, cax=cax, orientation="horizontal")
cb.set_label("NDTI = (red − green) / (red + green), mean 2017–2025 (higher = more turbid)", fontsize=6.5)
cb.ax.tick_params(labelsize=6)
fig.text(0.02, 0.965, "Turbidity of project tanks and rivers at 10 m (Sentinel-2, 2017–2025)", fontsize=10.5,
         fontweight="semibold", color=INK)
fig.text(0.02, 0.945, f"{rel['counts']['tanks']} tanks ≥ 2 ha and {rel['counts']['river_cells']} river cells · "
         f"{rel['counts']['observations']:,} object-date observations from {rel['counts']['scene_files']:,} scenes",
         fontsize=7, color=MUTED)
fig.text(0.02, 0.20, "Zooms show per-pixel means at 10 m (pixels with ≥ 5 clear water views). NDTI is a band ratio; "
         "it does not depend on the absolute\nreflectance calibration, so it ranks water bodies reliably without "
         "field data. Tank pixels within 30 m of the day's shoreline are excluded.", fontsize=6, color=MUTED, va="top")
for ext in ("png", "pdf"):
    fig.savefig(R / f"fig_t1_map10m.{ext}", bbox_inches="tight", facecolor="white")
plt.close(fig)

# fig t2: relations
fig, axs = plt.subplots(2, 2, figsize=(7.2, 6.0), gridspec_kw={"hspace": 0.45, "wspace": 0.3})
a = axs[0, 0]
h = tur.sample(min(len(tur), 60000), random_state=1)
a.hexbin(h["ndti"], h["spm"], gridsize=60, bins="log", yscale="log", cmap="Greys", mincnt=1)
a.set_xlabel("NDTI")
a.set_ylabel("SPM, red band (g m⁻³)")
a.set_title("A  NDTI against red-band SPM", loc="left")
a.text(0.03, 0.95, f"Spearman ρ = {rel['tank_rho_ndti_lspm_pooled']:.2f} (tanks), "
       f"{rel['river_rho_ndti_lspm_pooled']:.2f} (rivers)", transform=a.transAxes, fontsize=6.5, va="top")
a = axs[0, 1]
bins = [-0.1, 0.5, 10, 25, 50, 100, 1e4]
labels = ["0", "0.5–10", "10–25", "25–50", "50–100", "> 100"]
for j, (kind, col) in enumerate((("tank", C_TANK), ("river", C_RIV))):
    g = tur[tur["kind"] == kind].dropna(subset=["R7"])
    cl = pd.cut(g["R7"], bins, labels=labels)
    q = g.groupby(cl, observed=False)["a_ndti"].quantile([0.25, 0.5, 0.75]).unstack()
    n_ = g.groupby(cl, observed=False).size()
    x = np.arange(len(labels)) + (j - 0.5) * 0.25
    a.errorbar(x, q[0.5], yerr=[q[0.5] - q[0.25], q[0.75] - q[0.5]], fmt="o", color=col, ms=3, lw=0.8, capsize=0,
               label=f"{kind}s (ρ = {rel[f'{kind}_rho_anom_R7']:.2f})")
a.axhline(0, color="#aaa", lw=0.5)
a.set_xticks(range(len(labels)), labels, fontsize=6.5)
a.set_xlabel("Rain in the 7 days before the image (mm, PERSIANN-CDR)")
a.set_ylabel("NDTI minus the object's median")
a.set_title("B  Turbidity anomaly against recent rain", loc="left")
a.legend(frameon=False, fontsize=6.5, loc="upper left")
a = axs[1, 0]
g = tur[(tur["kind"] == "tank")].dropna(subset=["fill"])
cl = pd.cut(g["fill"].clip(upper=1.1), np.arange(0, 1.21, 0.1))
q = g.groupby(cl, observed=False)["a_ndti"].quantile([0.25, 0.5, 0.75]).unstack()
xm = np.arange(0.05, 1.2, 0.1)[:len(q)]
a.fill_between(xm, q[0.25], q[0.75], color=C_TANK, alpha=0.18, lw=0)
a.plot(xm, q[0.5], color=C_TANK, marker="o", ms=3, lw=1)
a.axhline(0, color="#aaa", lw=0.5)
a.set_xlabel("Tank water spread / full extent (95th percentile)")
a.set_ylabel("NDTI minus the tank's median")
a.set_title("C  Tank turbidity against water level", loc="left")
a.text(0.97, 0.95, f"ρ = {rel['tank_rho_anom_fill']:.2f}", transform=a.transAxes, ha="right", va="top", fontsize=6.5)
a = axs[1, 1]
rg = reg.copy()
lab_map = {"lR7": "Rain, 7 days", "lR30": "Rain, 30 days", "ndvi_anom": "NDVI anomaly", "fill": "Tank fill"}
yy = 0
ticks, tl = [], []
for pred in ("lR7", "lR30", "ndvi_anom", "fill"):
    for kind, col in (("tank", C_TANK), ("river", C_RIV)):
        r_ = rg[(rg["kind"] == kind) & (rg["predictor"] == pred)]
        if len(r_):
            r_ = r_.iloc[0]
            a.plot([r_["ci_lo"], r_["ci_hi"]], [yy, yy], color=col, lw=1.2)
            a.plot(r_["beta_std"], yy, "o", color=col, ms=3.5)
        yy -= 1
    ticks.append(yy + 1.5)
    tl.append(lab_map[pred])
    yy -= 0.6
a.axvline(0, color="#aaa", lw=0.5)
a.set_yticks(ticks, tl, fontsize=7)
a.set_xlabel("Standardized effect on NDTI anomaly (95 % CI)")
a.set_title("D  All drivers together (regression)", loc="left")
for a in axs.ravel():
    for sp in ("top", "right"):
        a.spines[sp].set_visible(False)
    a.tick_params(labelsize=6.5)
fig.text(0.01, 0.005, "Anomalies are within each tank or river cell, so every object is its own control. "
         "Regression: OLS with errors clustered by object; blue = tanks, orange = river cells.",
         fontsize=6, color=MUTED)
for ext in ("png", "pdf"):
    fig.savefig(R / f"fig_t2_relations.{ext}", bbox_inches="tight", facecolor="white")
plt.close(fig)

# fig t3: monthly climatology per basin
bmap = sws.set_index("SubWS_ID")["Basin"]
tur["Basin"] = tur["SubWS_ID"].map(bmap)
tur["month"] = tur["date"].dt.month
vg["Basin"] = vg["SubWS_ID"].map(bmap)
vg["ndvi_dev"] = vg["ndvi"] - vg.groupby("SubWS_ID")["ndvi"].transform("mean")
rain_m = rain.copy()
rain_m.columns = [bmap[c] for c in rain_m.columns]
rain_m = rain_m.T.groupby(level=0).mean().T
rain_clim = rain_m.groupby(rain_m.index.month).mean() * 30.4
order = ["Kala Oya", "Malwathu Oya", "Yan Oya", "Mahaweli Ganga"]
fig, axs = plt.subplots(1, 4, figsize=(7.4, 2.5), sharey=True, gridspec_kw={"wspace": 0.12})
for a, bname in zip(axs, order):
    a2 = a.twinx()
    a2.bar(range(1, 13), rain_clim[bname], color=C_RAIN, alpha=0.25, width=0.8)
    a2.set_ylim(0, 500)
    a2.tick_params(labelsize=6)
    if bname != order[-1]:
        a2.set_yticklabels([])
    else:
        a2.set_ylabel("Rain (mm/month)", fontsize=6.5, color=C_RAIN)
    for kind, col in (("tank", C_TANK), ("river", C_RIV)):
        g = tur[(tur["Basin"] == bname) & (tur["kind"] == kind)]
        if g["obj"].nunique() >= 3:
            m_ = g.groupby("month")["a_ndti"].median()
            a.plot(m_.index, m_.values, color=col, marker="o", ms=2.5, lw=1, label=f"{kind}s", zorder=3)
    v = vg[vg["Basin"] == bname].groupby("month")["ndvi_dev"].mean()
    a.plot(v.index, v.values, color=C_VEG, lw=1, ls="--", label="NDVI (minus its mean)")
    a.axhline(0, color="#bbb", lw=0.5)
    a.set_zorder(a2.get_zorder() + 1)
    a.patch.set_visible(False)
    a.set_xticks([1, 4, 7, 10], ["Jan", "Apr", "Jul", "Oct"], fontsize=6)
    a.set_title(bname, loc="left")
    a.tick_params(labelsize=6)
axs[0].set_ylabel("Anomaly (NDTI or NDVI)", fontsize=6.5)
axs[0].legend(frameon=False, fontsize=6, loc="lower left")
fig.suptitle("Seasonal cycle by basin: rain (bars), turbidity anomaly (NDTI) and vegetation (NDVI)", x=0.06,
             ha="left", fontsize=9, fontweight="semibold", y=1.04)
for ext in ("png", "pdf"):
    fig.savefig(R / f"fig_t3_seasonal.{ext}", bbox_inches="tight", facecolor="white")
plt.close(fig)

# fig t4: cross-section
fig, axs = plt.subplots(1, 4, figsize=(7.4, 2.2), gridspec_kw={"wspace": 0.35})
for a, (x, xl) in zip(axs, (("crop_pct", "Cropland (%)"), ("ndvi_mean", "Mean NDVI"),
                            ("rain_mm_yr", "Rain (mm/yr)"), ("tank_density_per_100km2", "Tanks per 100 km²"))):
    h = out.dropna(subset=[x, "tank_ndti"])
    a.scatter(h[x], h["tank_ndti"], s=12, color=C_TANK, edgecolor="white", lw=0.4)
    a.set_xlabel(xl, fontsize=6.5)
    c_ = cs[x]
    a.set_title(f"ρ = {c_['rho']:.2f}, p = {c_['p']:.2f}", loc="left", fontsize=6.5, fontweight="normal")
    for sp in ("top", "right"):
        a.spines[sp].set_visible(False)
    a.tick_params(labelsize=6)
axs[0].set_ylabel("Median tank NDTI", fontsize=6.5)
fig.suptitle("Sub-watershed differences (n = 18–23 sub-watersheds)", x=0.06, ha="left", fontsize=9,
             fontweight="semibold", y=1.06)
for ext in ("png", "pdf"):
    fig.savefig(R / f"fig_t4_crosssection.{ext}", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("written to", R)
