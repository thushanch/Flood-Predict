"""Combine reservoir series and draw the Knuckles downstream figures.

Outputs in results/knuckles/:
  reservoir_series.csv, reservoir_summary.csv
  fig_k1_subwatersheds.(png|pdf)   provisional units, river sediment, reservoirs, stations
  fig_k2_reservoirs.(png|pdf)      water spread and turbidity 2019-2025 per reservoir
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from sedrs import trends  # noqa: E402
from sedrs.config import DATA_DIR, OUT_DIR, ROOT  # noqa: E402
from sedrs.seasons import SEASONS, season_of  # noqa: E402

K = DATA_DIR / "knuckles"
RES = ROOT / "results" / "knuckles"
EVENT = ("2025-11-26", "2025-12-12")
plt.rcParams.update({"font.family": "Inter", "font.size": 8, "axes.titlesize": 8.5, "axes.titleweight": "semibold",
                     "savefig.dpi": 300, "axes.edgecolor": "#8a8f8c", "axes.linewidth": 0.6})
INK, MUTED = "#1f2523", "#5c625f"

# ------------------------------------------------------------------ reservoir series
files = [f for f in (K / "reservoirs").glob("*.csv") if f.stat().st_size > 5]
s = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
s["date"] = pd.to_datetime(s["date"])
s = (s.sort_values("clear_frac", ascending=False).drop_duplicates(["reservoir", "date"])
     .sort_values(["reservoir", "date"]))
s["season"] = season_of(s["date"]).values


def flag_dropouts(g, k=3):
    """A reservoir cannot empty and refill within days: a view whose water spread is < 50 % of the
    median of its k neighbours on each side is an artefact (haze or shadow missed by the SCL)."""
    w = g["water_ha"].to_numpy()
    bad = np.zeros(len(w), bool)
    for i in range(len(w)):
        nb = np.r_[w[max(0, i - k):i], w[i + 1:i + 1 + k]]
        if len(nb) >= 2 and w[i] < 0.5 * np.median(nb):
            bad[i] = True
    return g.assign(dropout=bad)


s = pd.concat([flag_dropouts(g) for _, g in s.groupby("reservoir")], ignore_index=True)
print("dropout views removed:", int(s["dropout"].sum()), "of", len(s))
s = s[~s["dropout"]].drop(columns="dropout")
s.to_csv(RES / "reservoir_series.csv", index=False)

rows = []
for name, g in s.groupby("reservoir"):
    sp = g.dropna(subset=["spm_red"])
    cap = g["water_ha"].quantile(0.95)
    ev = sp[sp["date"].between(*EVENT)]["spm_red"]
    base = sp[~sp["date"].between(*EVENT)]["spm_red"]
    seas = sp.groupby("season")["spm_red"].median().reindex(SEASONS)
    m = sp.set_index(sp["date"].dt.to_period("M"))["spm_red"].groupby(level=0).median()
    m = m.reindex(pd.period_range(m.index.min(), m.index.max(), freq="M"))
    sk = trends.seasonal_kendall(m)
    y = g.groupby(g["date"].dt.year)["water_ha"].median()
    rows.append({"reservoir": name, "clear_views": len(g), "turbidity_views": len(sp),
                 "water_ha_p95": round(cap, 0), "water_ha_p05": round(g["water_ha"].quantile(0.05), 0),
                 "drawdown_pct": round(100 * (1 - g["water_ha"].quantile(0.05) / cap), 0),
                 "water_ha_median_2019": round(y.get(2019, np.nan), 0),
                 "water_ha_median_2025": round(y.get(2025, np.nan), 0),
                 "spm_median": round(sp["spm_red"].median(), 1),
                 **{f"spm_{k}": round(v, 1) for k, v in seas.items()},
                 "peak_season": seas.idxmax() if seas.notna().any() else None,
                 "ditwah_spm": round(ev.median(), 1) if len(ev) else None,
                 "ditwah_ratio": round(ev.median() / base.median(), 1) if len(ev) else None,
                 "trend_pct_per_yr": round(sk.get("pct_per_yr"), 1) if sk.get("pct_per_yr") is not None else None,
                 "trend_p": round(sk.get("p"), 3) if sk.get("p") is not None else None})
summ = pd.DataFrame(rows)
summ["trend_q"] = trends.bh_fdr(summ["trend_p"].astype(float))
summ = summ.sort_values("water_ha_p95", ascending=False)
summ.to_csv(RES / "reservoir_summary.csv", index=False)
pd.set_option("display.width", 250)
print(summ.to_string(index=False))

# ------------------------------------------------------------------ figure K1: map
lab_ds = rasterio.open(K / "subwatersheds.tif")
lab, tr = lab_ds.read(1), lab_ds.transform
units = pd.read_csv(RES / "unit_summary.csv").set_index("unit")
hs = np.load(OUT_DIR / "cog" / "hillshade.npz")
cells = pd.read_csv(ROOT / "results" / "sentinel2_2019-2025" / "river_cells_metrics.csv")
wb = pd.read_csv(RES / "waterbodies.csv")
st = pd.read_csv(DATA_DIR / "cog" / "stations.csv")
st = st[st["id"].str.startswith("mahaweli")]
ext = (tr.c, tr.c + tr.a * lab.shape[1], tr.f + tr.e * lab.shape[0], tr.f)
KX = np.cos(np.radians(7.6))

fig, ax = plt.subplots(figsize=(6.4, 8.6))
e = hs["extent"]
ax.imshow(hs["hillshade"].astype("float32"), extent=(e[0], e[1], e[2], e[3]), cmap="Greys_r", vmin=-0.2, vmax=1.15,
          alpha=0.45, interpolation="bilinear", zorder=0)
kn_units = units.index[units["knuckles_share_pct"] >= 30]
shade = np.where(np.isin(lab, kn_units), 2, np.where(lab > 0, 1, 0)).astype(float)
ax.imshow(np.ma.masked_equal(shade, 0), extent=ext, cmap=matplotlib.colors.ListedColormap(["#e9eef0", "#cfe3d4"]),
          alpha=0.55, interpolation="none", zorder=1)
ax.contour(lab, levels=np.arange(0.5, lab.max() + 1), colors="#53605c", linewidths=0.5, extent=ext, origin="upper",
           zorder=2)
from scipy import ndimage as ndi  # noqa: E402

for k in units.index:
    dist = ndi.distance_transform_edt(lab == k)             # label at the unit's most interior point
    rr, cc = np.unravel_index(np.argmax(dist), dist.shape)
    x, y = tr * (cc + 0.5, rr + 0.5)
    ax.text(x, y, str(k), fontsize=7, fontweight="semibold", color="#2d3a36", ha="center", va="center", zorder=6,
            bbox=dict(boxstyle="circle,pad=0.15", fc="white", ec="none", alpha=0.75))
inside = (cells["lon"].between(ext[0], ext[1])) & (cells["lat"].between(ext[2], ext[3]))
sc = ax.scatter(cells.loc[inside, "lon"], cells.loc[inside, "lat"], c=cells.loc[inside, "spm_all"], cmap="YlOrBr",
                norm=LogNorm(5, 150), s=7, marker="s", lw=0, zorder=4)
summ_i = summ.set_index("reservoir")
LABEL_OFFS = {"Bowatenna": (-7, -2, "right"), "Moragahakanda": (7, 4, "left"), "Parakrama Samudra": (-8, -8, "right"),
              "Giritale": (7, -5, "left"), "Minneriya": (-8, 3, "right"), "Ulhitiya-Ratkinda": (8, -7, "left")}
for r in wb[wb["name"].fillna("") != ""].itertuples():
    v = summ_i["spm_median"].get(r.name, np.nan)
    ax.scatter(r.lon, r.lat, s=18 + r.area_max_ha / 25, c=[v], cmap="YlOrBr", norm=LogNorm(5, 150), marker="o",
               edgecolor=INK, lw=0.7, zorder=5)
    dx, dy, ha = LABEL_OFFS.get(r.name, (6, -2, "left"))
    ax.annotate(r.name, (r.lon, r.lat), xytext=(dx, dy), textcoords="offset points", fontsize=6.2, color=INK,
                style="italic", ha=ha, zorder=7)
ax.scatter(st["lon"], st["lat"], marker="^", s=26, facecolor="white", edgecolor=INK, lw=0.8, zorder=7)
ax.plot([80.70, 80.90, 80.90, 80.70, 80.70], [7.33, 7.33, 7.58, 7.58, 7.33], color="#b23b2a", lw=1.0, ls="--",
        zorder=6)
ax.text(80.705, 7.585, "Knuckles range (approx.)", fontsize=6.5, color="#b23b2a", zorder=7)
ax.set_xlim(80.42, 81.32)
ax.set_ylim(6.78, 8.28)
ax.set_aspect(1 / KX)
ax.set_xticks([])
ax.set_yticks([])
cax = fig.add_axes([0.14, 0.075, 0.32, 0.012])
cb = fig.colorbar(sc, cax=cax, orientation="horizontal", ticks=[5, 10, 20, 50, 150])
cb.ax.set_xticklabels(["5", "10", "20", "50", "150"])
cb.set_label("Median SPM 2024–25, river cells and reservoirs (g m$^{-3}$, estimated)", fontsize=6.5)
cb.ax.tick_params(labelsize=6, length=2)
fig.legend(handles=[Patch(fc="#cfe3d4", ec="#53605c", lw=0.5, label="Unit draining the Knuckles (≥ 30 % in range)"),
                    Patch(fc="#e9eef0", ec="#53605c", lw=0.5, label="Other unit of the Mahaweli catchment"),
                    Line2D([], [], marker="^", ls="", mfc="white", mec=INK, label="Mahaweli station"),
                    Line2D([], [], marker="o", ls="", mfc="#d9a066", mec=INK, label="Named reservoir (size ~ area)")],
           loc="lower left", bbox_to_anchor=(0.52, 0.045), frameon=False, fontsize=6.5)
fig.text(0.05, 0.965, "Knuckles downstream: provisional sub-watersheds, river sediment and reservoirs",
         fontsize=10.5, fontweight="semibold", color=INK)
fig.text(0.05, 0.948, f"Mahaweli catchment to below the Amban Ganga confluence ({int(units['area_km2'].sum()):,} km²), "
         "15 units from the Copernicus GLO-90 DEM with Sentinel-2/JRC channels burned in", fontsize=7, color=MUTED)
fig.text(0.05, 0.02, "Units are provisional until IWMI's sub-watershed boundaries are available. "
         "Reservoir and river SPM: red-band Nechad, uncalibrated.", fontsize=6, color=MUTED)
for ext_ in ("png", "pdf"):
    fig.savefig(RES / f"fig_k1_subwatersheds.{ext_}", bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------------ figure K2: reservoir series
names = list(summ["reservoir"])
n = len(names)
fig, axes = plt.subplots(n, 2, figsize=(7.2, 1.05 * n + 0.8), sharex=True,
                         gridspec_kw={"hspace": 0.35, "wspace": 0.25})
axes = np.atleast_2d(axes)
for i, name in enumerate(names):
    g = s[s["reservoir"] == name]
    cap = summ_i.loc[name, "water_ha_p95"]
    a1, a2 = axes[i]
    a1.plot(g["date"], 100 * g["water_ha"] / cap, color="#2a78d6", lw=0.8, marker="o", ms=1.6)
    a1.set_ylim(0, 115)
    a1.set_ylabel(name, rotation=0, ha="right", va="center", fontsize=7, labelpad=4)
    a2.plot(g["date"], g["spm_red"], color="#a8461f", lw=0, marker="o", ms=1.8)
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
fig.text(0.01, 0.005, "Clear views only (≥ 90 % of the reservoir cloud-free). Shaded: Cyclone Ditwah floods, "
         "26 Nov–12 Dec 2025.", fontsize=6, color=MUTED)
for ext_ in ("png", "pdf"):
    fig.savefig(RES / f"fig_k2_reservoirs.{ext_}", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("figures written to", RES)
