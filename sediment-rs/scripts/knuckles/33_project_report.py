"""Combine the project-area water-body series and summarise by water body and sub-watershed.

Outputs (data/project_layers/report/ -- project data, not committed):
  waterbody_series.csv, waterbody_summary.csv, subws_sediment_summary.csv
  fig_p1_project_map.(png|pdf), fig_p2_named_reservoirs.(png|pdf)
"""
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
from matplotlib.colors import LogNorm  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FixedFormatter, FixedLocator, NullFormatter  # noqa: E402

from sedrs import trends  # noqa: E402
from sedrs.config import DATA_DIR, OUT_DIR, ROOT  # noqa: E402
from sedrs.seasons import SEASONS, season_of  # noqa: E402

warnings.filterwarnings("ignore")
P = DATA_DIR / "project_layers"
R = P / "report"
R.mkdir(exist_ok=True)
EVENT = ("2025-11-26", "2025-12-12")
plt.rcParams.update({"font.family": "Inter", "font.size": 8, "axes.titlesize": 8.5, "axes.titleweight": "semibold",
                     "savefig.dpi": 300, "axes.edgecolor": "#8a8f8c", "axes.linewidth": 0.6})
INK, MUTED = "#1f2523", "#5c625f"

# ------------------------------------------------------------------ series + dropout filter
files = [f for f in (P / "waterbodies_s2").glob("*.csv") if f.stat().st_size > 5]
s = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
s["date"] = pd.to_datetime(s["date"])
s = (s.sort_values("clear_frac", ascending=False).drop_duplicates(["reservoir", "date"])
     .sort_values(["reservoir", "date"]))


def flag_dropouts(g, k=3):
    """Water-spread dropouts only (views with water_ha); turbidity-only views are kept."""
    g = g.copy()
    g["dropout"] = False
    h = g[g["water_ha"].notna()]
    w = h["water_ha"].to_numpy()
    for i in range(len(w)):
        nb = np.r_[w[max(0, i - k):i], w[i + 1:i + 1 + k]]
        if len(nb) >= 2 and w[i] < 0.5 * np.median(nb):
            g.loc[h.index[i], "dropout"] = True
    return g


s = pd.concat([flag_dropouts(g) for _, g in s.groupby("reservoir")], ignore_index=True)
print("water-spread dropouts removed:", int(s["dropout"].sum()), "of", int(s["water_ha"].notna().sum()),
      "| total views", len(s))
s = s[~s["dropout"]].drop(columns="dropout")
s["season"] = season_of(s["date"]).values
s.to_csv(R / "waterbody_series.csv", index=False)

tracked = pd.read_csv(P / "waterbodies_tracked.csv").set_index("label")
rows = []
for name, g in s.groupby("reservoir"):
    sp = g.dropna(subset=["spm_red"])
    if len(sp) < 10:
        continue
    cap = g["water_ha"].quantile(0.95)
    ev = sp[sp["date"].between(*EVENT)]["spm_red"]
    base = sp[~sp["date"].between(*EVENT)]["spm_red"]
    seas = sp.groupby("season")["spm_red"].median().reindex(SEASONS)
    m = sp.set_index(sp["date"].dt.to_period("M"))["spm_red"].groupby(level=0).median()
    m = m.reindex(pd.period_range(m.index.min(), m.index.max(), freq="M"))
    sk = trends.seasonal_kendall(m)
    dry = g[g["date"].dt.month.isin([8, 9])]["water_ha"].dropna()
    nm = str(tracked.loc[name, "name"])
    rows.append({"water_body": name, "SubWS_ID": tracked.loc[name, "SubWS_ID"], "named": nm not in ("", "nan"),
                 "spm_views": len(sp), "spm_months": int(sp["date"].dt.to_period("M").nunique()),
                 "lon": tracked.loc[name, "lon"], "lat": tracked.loc[name, "lat"],
                 "jrc_max_ha": tracked.loc[name, "area_max_ha"], "spread_views": int(g["water_ha"].notna().sum()),
                 "water_ha_p95": round(cap, 0), "water_ha_p05": round(g["water_ha"].quantile(0.05), 0),
                 "drawdown_pct": round(100 * (1 - g["water_ha"].quantile(0.05) / cap), 0) if cap > 0 else None,
                 "aug_sep_fill_pct": round(100 * dry.median() / cap, 0) if len(dry) and cap > 0 else None,
                 "spm_median": round(sp["spm_red"].median(), 1),
                 **{f"spm_{k}": round(v, 1) for k, v in seas.items()},
                 "peak_season": seas.idxmax() if seas.notna().any() else None,
                 "ditwah_ratio": round(ev.median() / base.median(), 1) if len(ev) else None,
                 "trend_pct_per_yr": round(sk["pct_per_yr"], 1) if sk.get("pct_per_yr") is not None else None,
                 "trend_p": round(sk["p"], 3) if sk.get("p") is not None else None})
wbs = pd.DataFrame(rows)
wbs["trend_q"] = trends.bh_fdr(wbs["trend_p"].astype(float))
wbs = wbs.sort_values(["SubWS_ID", "jrc_max_ha"], ascending=[True, False])
wbs.to_csv(R / "waterbody_summary.csv", index=False)

# ------------------------------------------------------------------ per sub-watershed
sws = pd.read_csv(P / "subws_summary.csv")
agg = (wbs.groupby("SubWS_ID").agg(tracked_water_bodies=("water_body", "size"),
                                   tank_spm_median=("spm_median", "median"),
                                   tank_spm_max=("spm_median", "max"),
                                   tank_drawdown_median=("drawdown_pct", "median"),
                                   tank_ditwah_ratio=("ditwah_ratio", "median"),
                                   rising_tanks=("trend_q", lambda q: int((q < 0.05).sum())))
       .round(1).reset_index())
peak = wbs.groupby("SubWS_ID")["peak_season"].agg(lambda x: x.mode().iloc[0] if len(x.dropna()) else None)
agg["tank_peak_season"] = agg["SubWS_ID"].map(peak)
out = sws.merge(agg, on="SubWS_ID", how="left")
out.to_csv(R / "subws_sediment_summary.csv", index=False)
pd.set_option("display.width", 260)
print(out[["SubWS_ID", "SubWS_Name", "area_km2", "crop_pct", "tanks_lt1km2", "tracked_water_bodies",
           "tank_spm_median", "tank_spm_max", "tank_peak_season", "tank_drawdown_median", "tank_ditwah_ratio",
           "rising_tanks", "river_cells", "river_spm_median"]].to_string(index=False))
print("\nnamed reservoirs:")
print(wbs[wbs["named"]][["water_body", "SubWS_ID", "water_ha_p95", "drawdown_pct", "aug_sep_fill_pct", "spm_median",
                         "peak_season", "ditwah_ratio", "trend_pct_per_yr", "trend_q"]].to_string(index=False))

# ------------------------------------------------------------------ figure P1: project map
gpkg = P / "project_layers_clean.gpkg"
sw = gpd.read_file(gpkg, layer="sub_watersheds").to_crs(4326)
basins = gpd.read_file(gpkg, layer="basins").to_crs(4326)
riv = gpd.read_file(gpkg, layer="rivers").to_crs(4326)
riv = riv[riv["in_project_area"] & (riv["strahler"] >= 3)]
hs = np.load(OUT_DIR / "cog" / "hillshade.npz")
cells = pd.read_csv(ROOT / "results" / "sentinel2_2019-2025" / "river_cells_metrics.csv")
x0, y0, x1, y1 = sw.total_bounds + np.array([-0.04, -0.04, 0.04, 0.04])
fig = plt.figure(figsize=(6.8, 8.0))
ax = fig.add_axes([0.03, 0.14, 0.94, 0.76])
e = hs["extent"]
ax.imshow(hs["hillshade"].astype("float32"), extent=(e[0], e[1], e[2], e[3]), cmap="Greys_r", vmin=-0.2, vmax=1.15,
          alpha=0.4, interpolation="bilinear", zorder=0)
sw.plot(ax=ax, facecolor="#eef3f0", edgecolor="#6b7772", lw=0.4, zorder=1)
basins.boundary.plot(ax=ax, color="#2d3a36", lw=1.1, zorder=2)
riv.plot(ax=ax, color="#6f9fc0", lw=0.5, zorder=3)
norm = LogNorm(3, 60)
cmap = plt.get_cmap("YlOrBr")
near = sw.union_all().buffer(0.03)                  # river cells inside or within ~3 km of the project area
inside = cells[cells.lon.between(x0, x1) & cells.lat.between(y0, y1)]
inside = inside[gpd.points_from_xy(inside.lon, inside.lat).within(near)]
ax.scatter(inside.lon, inside.lat, c=inside.spm_all, cmap=cmap, norm=norm, s=6, marker="s", lw=0, zorder=4)
sc = ax.scatter(wbs.lon, wbs.lat, c=wbs.spm_median, cmap=cmap, norm=norm, s=10 + wbs.jrc_max_ha / 12,
                edgecolor=INK, lw=0.5, zorder=5)
# label offsets (points) chosen so neighbouring names do not collide
OFFS = {"Tissa Wewa (2)": (-5, 5, "right"), "Usgala Siyambalangamu Wewa": (7, -2, "left"),
        "Dambulu Oya Reservoir": (-6, -8, "right"), "Kandalama Tank": (6, 3, "left")}
for r in wbs[wbs["named"]].itertuples():
    dx_, dy_, ha_ = OFFS.get(r.water_body, (5, 3, "left"))
    ax.annotate(r.water_body.replace(" Wewa", " W.").replace(" Tank", " T.").replace(" Reservoir", " Res."),
                (r.lon, r.lat), xytext=(dx_, dy_), textcoords="offset points", fontsize=5.8, style="italic",
                color=INK, ha=ha_, zorder=6)
for r in sw.itertuples():
    pt = r.geometry.representative_point()
    ax.text(pt.x, pt.y, r.SubWS_ID, fontsize=4.8, color="#7d8884", ha="center", va="center", zorder=4.5)
BASIN_LBL = {"Kala Oya": (80.18, 7.99), "Malwathu Oya": (80.52, 8.44), "Yan Oya": (80.78, 8.46),
             "Mahaweli Ganga": (80.80, 7.52)}
for r in basins.itertuples():
    lx, ly = BASIN_LBL.get(r.Basin_Name, (r.geometry.representative_point().x, r.geometry.representative_point().y))
    ax.text(lx, ly, r.Basin_Name.upper(), fontsize=7, fontweight="semibold", color="#2d3a36",
            ha="center", zorder=6, alpha=0.85)
ax.set_xlim(x0, x1)
ax.set_ylim(y0, y1)
ax.set_aspect(1 / np.cos(np.radians(7.8)))
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel("")
ax.set_ylabel("")
cax = fig.add_axes([0.06, 0.085, 0.36, 0.012])
cb = fig.colorbar(sc, cax=cax, orientation="horizontal")
cb.ax.xaxis.set_major_locator(FixedLocator([3, 5, 10, 20, 50]))
cb.ax.xaxis.set_major_formatter(FixedFormatter(["3", "5", "10", "20", "50"]))
cb.ax.xaxis.set_minor_formatter(NullFormatter())
cb.set_label("Median surface SPM 2019–25, tanks and river cells (g m$^{-3}$, estimated)", fontsize=6.5)
cb.ax.tick_params(labelsize=6, length=2)
fig.legend(handles=[Line2D([], [], marker="o", ls="", mfc="#e6a85c", mec=INK,
                           label="Tank / reservoir ≥ 25 ha (size ~ area)"),
                    Line2D([], [], color="#6f9fc0", lw=1, label="River, Strahler order ≥ 3 (project layer)"),
                    Line2D([], [], color="#2d3a36", lw=1.2, label="Basin boundary")],
           loc="lower left", bbox_to_anchor=(0.50, 0.045), frameon=False, fontsize=6.5)
fig.text(0.03, 0.955, "Knuckles downstream project area: satellite sediment signal in tanks and rivers",
         fontsize=10.5, fontweight="semibold", color=INK)
fig.text(0.03, 0.935, f"{len(sw)} sub-watersheds, {sw.to_crs(5235).area.sum() / 1e6:,.0f} km² (project boundaries, "
         f"cleaned) · {len(wbs)} water bodies tracked with Sentinel-2, 2019–2025", fontsize=7, color=MUTED)
fig.text(0.03, 0.02, "SPM: red-band Nechad, uncalibrated. Tank turbidity in the dry zone also reflects shallow-water "
         "resuspension, not only inflowing sediment.", fontsize=6, color=MUTED)
for ext_ in ("png", "pdf"):
    fig.savefig(R / f"fig_p1_project_map.{ext_}", bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------------ figure P2: named reservoirs
names = list(wbs[wbs["named"]].sort_values("water_ha_p95", ascending=False)["water_body"])
fig, axes = plt.subplots(len(names), 2, figsize=(7.2, 1.0 * len(names) + 0.8), sharex=True,
                         gridspec_kw={"hspace": 0.35, "wspace": 0.25})
axes = np.atleast_2d(axes)
for i, name in enumerate(names):
    g = s[s["reservoir"] == name]
    cap = g["water_ha"].quantile(0.95)
    a1, a2 = axes[i]
    gw = g.dropna(subset=["water_ha"])
    a1.plot(gw["date"], 100 * gw["water_ha"] / cap, color="#2a78d6", lw=0.8, marker="o", ms=1.5)
    a1.set_ylim(0, 115)
    a1.set_ylabel(name, rotation=0, ha="right", va="center", fontsize=7, labelpad=4)
    a2.plot(g["date"], g["spm_red"], color="#a8461f", lw=0, marker="o", ms=1.7)
    a2.set_yscale("log")
    a2.set_ylim(1, 300)
    for a in (a1, a2):
        a.axvspan(pd.Timestamp(EVENT[0]), pd.Timestamp(EVENT[1]), color="#eb6834", alpha=0.15, lw=0)
        a.grid(axis="y", color="#e6e6e1", lw=0.5)
        for sp_ in ("top", "right"):
            a.spines[sp_].set_visible(False)
        a.tick_params(labelsize=6)
axes[0, 0].set_title("Water spread (% of the 95th-percentile area)", loc="left")
axes[0, 1].set_title("Surface SPM (g m$^{-3}$, estimated, log scale)", loc="left")
fig.text(0.01, 0.005, "Water spread: views with ≥ 90 % of the water body cloud-free; SPM: ≥ 50 %. "
         "Shaded: Cyclone Ditwah floods, 26 Nov–12 Dec 2025.",
         fontsize=6, color=MUTED)
for ext_ in ("png", "pdf"):
    fig.savefig(R / f"fig_p2_named_reservoirs.{ext_}", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("written to", R)
