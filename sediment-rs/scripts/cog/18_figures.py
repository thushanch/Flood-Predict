"""Publication figures for the Sentinel-2 river sediment run.

  fig1_sediment_map.(png|pdf)      headline map: median red-band SPM per 1 km river cell
  fig2_four_panel.(png|pdf)        (a) median SPM (b) peak season (c) Cyclone Ditwah flood pulse
                                   (d) station trends 2019-2025
  fig3_profiles.(png|pdf)          downstream profiles of Kelani, Kalu and Mahaweli by season

Colour: SPM uses a single sequential ramp; flood ratio and trends use a two-hue
diverging scale with a grey midpoint at "no change"; peak season uses three
validated hues plus a neutral grey, with marker shapes as a second cue
(dataviz validator: CVD dE 9.2, normal-vision dE 21.8, all pairs).
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
from matplotlib.colors import LinearSegmentedColormap, LogNorm, TwoSlopeNorm  # noqa: E402
from matplotlib.patches import PathPatch, Rectangle  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402

from sedrs.config import DATA_DIR, OUT_DIR, ROOT  # noqa: E402

RES = ROOT / "results" / "sentinel2_2019-2025"
FIG = RES / "figures"
FIG.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "cog"

plt.rcParams.update({
    "font.family": "Inter", "font.size": 8, "axes.titlesize": 9, "axes.titleweight": "semibold",
    "axes.edgecolor": "#8a8f8c", "axes.linewidth": 0.6, "savefig.dpi": 300,
    "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.labelcolor": "#2b2b29",
})
INK, MUTED, OCEAN, COAST = "#1f2523", "#5c625f", "#eef2f3", "#7f8a86"
SEASON_COL = {"NEM": "#2a78d6", "FIM": "#1baf7a", "SWM": "#52514e", "SIM": "#eb6834"}
SEASON_MARK = {"NEM": "o", "FIM": "s", "SWM": "^", "SIM": "D"}
SEASON_NAME = {"NEM": "NE monsoon (Dec–Feb)", "FIM": "1st inter-monsoon (Mar–Apr)",
               "SWM": "SW monsoon (May–Sep)", "SIM": "2nd inter-monsoon (Oct–Nov)"}
SPM_CMAP = plt.get_cmap("YlOrBr")
DIV_CMAP = LinearSegmentedColormap.from_list("div", ["#2a78d6", "#9ab9de", "#d8d8d4", "#d9a066", "#8c3b0c"])
KX = np.cos(np.radians(7.8))
EXTENT = (79.6, 81.95, 5.88, 9.88)

cells = pd.read_csv(out / "river_cells_metrics.csv")
prof = pd.read_csv(out / "profiles.csv")
stations = pd.read_csv(DATA_DIR / "cog" / "stations.csv")
trends = pd.read_csv(RES / "trends.csv")
clean = pd.read_csv(RES / "stations_clean.csv")
stations = stations[stations["id"].isin(clean["station"].unique())]
hs = np.load(out / "hillshade.npz")
ne = json.load(open(DATA_DIR / "cog" / "ne" / "ne_10m_admin_0_countries.geojson"))


def polys(code):
    g = next(f for f in ne["features"] if f["properties"].get("ADM0_A3") == code)["geometry"]
    return [np.asarray(p[0]) for p in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]])]


LKA = polys("LKA")
LABEL = {"kelani_hanwella": "Hanwella", "kelani_colombo": "Colombo", "kalu_putupaula": "Putupaula",
         "kalu_ellagawa": "Ellagawa", "gin_gintota": "Gintota", "mahaweli_peradeniya": "Peradeniya",
         "mahaweli_mahiyangana": "Mahiyangana", "mahaweli_manampitiya": "Manampitiya",
         "mahaweli_somawathiya": "Somawathiya", "walawe_embilipitiya": "Embilipitiya",
         "walawe_ambalantota": "Ambalantota", "deduru_chilaw": "Chilaw", "mahaoya_badalgama": "Badalgama",
         "nilwala_matara": "Matara"}
# label offsets (points) chosen to avoid collisions
OFFS = {"Colombo": (-6, 5, "right"), "Hanwella": (6, -9, "left"), "Putupaula": (-6, -9, "right"),
        "Ellagawa": (6, 2, "left"), "Peradeniya": (-6, -2, "right"), "Mahiyangana": (6, 0, "left"),
        "Manampitiya": (6, -2, "left"), "Somawathiya": (6, 2, "left"), "Badalgama": (-6, 2, "right"),
        "Chilaw": (-6, 0, "right"), "Gintota": (-6, 4, "right"), "Ambalantota": (6, -4, "left"),
        "Embilipitiya": (6, 2, "left")}
RIVERS = [("Mahaweli", 81.12, 7.62, 72), ("Kelani", 80.10, 7.04, -8), ("Kalu", 80.22, 6.53, 22),
          ("Deduru Oya", 79.93, 7.73, 0), ("Maha Oya", 79.99, 7.36, 0)]


def basemap(ax, hill=True, extent=EXTENT):
    ax.set_facecolor(OCEAN)
    clip = None
    for p in LKA:
        patch = PathPatch(MPath(p), facecolor="#f4f3ee", edgecolor=COAST, lw=0.5, zorder=1)
        ax.add_patch(patch)
        if clip is None or len(p) > len(clip.get_path().vertices):
            clip = patch
    if hill:
        e = hs["extent"]
        im = ax.imshow(hs["hillshade"].astype("float32"), extent=(e[0], e[1], e[2], e[3]), cmap="Greys_r",
                       vmin=-0.2, vmax=1.15, alpha=0.32, zorder=2, interpolation="bilinear")
        im.set_clip_path(clip)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_aspect(1 / KX)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)


def scalebar(ax, lon, lat, km=50):
    dlon = km / (111.32 * KX)
    ax.add_patch(Rectangle((lon, lat), dlon / 2, 0.025, fc=INK, ec=INK, lw=0.5, zorder=6))
    ax.add_patch(Rectangle((lon + dlon / 2, lat), dlon / 2, 0.025, fc="white", ec=INK, lw=0.5, zorder=6))
    for f, t in ((0, "0"), (1, f"{km} km")):
        ax.text(lon + f * dlon, lat + 0.05, t, ha="center", va="bottom", fontsize=6.5, color=INK, zorder=6)


def north(ax, lon, lat):
    ax.annotate("", xy=(lon, lat + 0.16), xytext=(lon, lat), zorder=6,
                arrowprops=dict(arrowstyle="-|>,head_width=0.25,head_length=0.5", color=INK, lw=0.9))
    ax.text(lon, lat + 0.19, "N", ha="center", va="bottom", fontsize=7.5, fontweight="semibold", color=INK)


def stations_layer(ax, labels=True, size=16):
    ax.scatter(stations["lon"], stations["lat"], s=size, facecolor="white", edgecolor=INK, lw=0.8, zorder=7)
    if labels:
        for s in stations.itertuples():
            name = LABEL.get(s.id)
            if not name:
                continue
            dx, dy, ha = OFFS.get(name, (6, 0, "left"))
            ax.annotate(name, (s.lon, s.lat), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                        fontsize=6.3, color=INK, zorder=8)


def river_names(ax, size=7):
    for name, lon, lat, rot in RIVERS:
        ax.text(lon, lat, name, rotation=rot, fontsize=size, style="italic", color="#245a73",
                ha="center", va="center", zorder=8)


def cells_layer(ax, values, cmap, norm, size=5):
    ok = values.notna()
    order = values[ok].sort_values().index
    return ax.scatter(cells.loc[order, "lon"], cells.loc[order, "lat"], c=values[order], cmap=cmap, norm=norm,
                      s=size, marker="s", lw=0, zorder=5)


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"{name}.{ext}", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", FIG / f"{name}.png")


SPM_NORM = LogNorm(vmin=5, vmax=150)
CREDIT = ("Copernicus Sentinel-2 L2A (Sen2Cor), 2,179 scenes 2024–2025 · JRC Global Surface Water · "
          "Copernicus GLO-90 DEM · Natural Earth. SPM: red-band Nechad algorithm, uncalibrated.")

# ======================================================================= figure 1
fig = plt.figure(figsize=(6.6, 9.6))
ax = fig.add_axes([0.02, 0.135, 0.96, 0.79])
basemap(ax)
sc = cells_layer(ax, cells["spm_all"], SPM_CMAP, SPM_NORM, size=7)
river_names(ax, 7.5)
stations_layer(ax)
scalebar(ax, 81.42, 5.93)
north(ax, 81.8, 8.62)
# locator inset
ins = fig.add_axes([0.70, 0.74, 0.25, 0.17])
for code in ("IND", "LKA"):
    for p in polys(code):
        ins.fill(p[:, 0], p[:, 1], color="#dcdcd6" if code == "IND" else INK, lw=0)
ins.add_patch(Rectangle((79.5, 5.85), 2.5, 4.05, fill=False, ec="#eb6834", lw=1))
ins.set_xlim(72, 88)
ins.set_ylim(5, 16)
ins.set_aspect(1 / np.cos(np.radians(10)))
ins.set_xticks([])
ins.set_yticks([])
ins.set_facecolor(OCEAN)
for spn in ins.spines.values():
    spn.set_color(COAST)
cax = fig.add_axes([0.06, 0.098, 0.46, 0.013])
cb = fig.colorbar(sc, cax=cax, orientation="horizontal", ticks=[5, 10, 20, 50, 100, 150])
cb.ax.set_xticklabels(["5", "10", "20", "50", "100", "150"])
cb.set_label("Median suspended sediment, 2024–2025 (g m$^{-3}$, estimated)", fontsize=7)
cb.outline.set_linewidth(0.4)
cb.ax.tick_params(labelsize=6.5, length=2)
ax.scatter([], [], s=16, facecolor="white", edgecolor=INK, lw=0.8, label="Station (2019–2025 record)")
ax.scatter([], [], s=12, marker="s", c="#d9a066", lw=0, label="1 km river cell")
fig.legend(*ax.get_legend_handles_labels(), loc="lower left", bbox_to_anchor=(0.60, 0.072), frameon=False,
           fontsize=6.8, handletextpad=0.4)
fig.text(0.04, 0.968, "Suspended sediment in Sri Lanka's rivers, seen by Sentinel-2", fontsize=12,
         fontweight="semibold", color=INK)
fig.text(0.04, 0.95, f"{cells['spm_all'].notna().sum()} river cells (1 km) on channels wider than ~60 m · "
         "median of all clear scenes", fontsize=7.5, color=MUTED)
fig.text(0.04, 0.025, CREDIT, fontsize=5.6, color=MUTED, wrap=True)
save(fig, "fig1_sediment_map")

# ======================================================================= figure 2
fig, axes = plt.subplots(2, 2, figsize=(7.2, 11.0), gridspec_kw={"hspace": 0.30, "wspace": 0.04})
axes = axes.ravel()

# (a) median SPM
ax = axes[0]
basemap(ax)
sc = cells_layer(ax, cells["spm_all"], SPM_CMAP, SPM_NORM)
river_names(ax, 6)
ax.set_title("(a) Median suspended sediment, 2024–25", loc="left", pad=13)
cax = ax.inset_axes([0.03, -0.045, 0.55, 0.022])
cb = fig.colorbar(sc, cax=cax, orientation="horizontal", ticks=[5, 10, 20, 50, 150])
cb.ax.set_xticklabels(["5", "10", "20", "50", "150"])
cb.set_label("g m$^{-3}$ (estimated)", fontsize=6.5)
cb.ax.tick_params(labelsize=6, length=2)
cb.outline.set_linewidth(0.4)
scalebar(ax, 81.3, 6.0)
north(ax, 81.8, 9.4)

# (b) peak season
ax = axes[1]
basemap(ax)
for s in ["SWM", "NEM", "FIM", "SIM"]:
    sub = cells[cells["peak_season"] == s]
    ax.scatter(sub["lon"], sub["lat"], s=6, marker=SEASON_MARK[s], c=SEASON_COL[s], lw=0, zorder=5,
               label=f"{SEASON_NAME[s]}  ({len(sub)})")
ax.set_title("(b) Season with the highest median", loc="left", pad=13)
handles, labels = ax.get_legend_handles_labels()
order = [1, 2, 0, 3]                                   # calendar order: NEM, FIM, SWM, SIM
ax.legend([handles[i] for i in order], [labels[i] for i in order], loc="upper left", bbox_to_anchor=(0.0, 0.0),
          frameon=False, fontsize=6, markerscale=1.8, handletextpad=0.3, labelspacing=0.35, ncol=1)

# (c) flood pulse
ax = axes[2]
basemap(ax)
fr = np.log10(cells["flood_ratio"].clip(0.25, 40))
fnorm = TwoSlopeNorm(vmin=np.log10(0.25), vcenter=0.0, vmax=np.log10(40))
sc = cells_layer(ax, fr, DIV_CMAP, fnorm, size=6)
ax.set_title("(c) Cyclone Ditwah flood pulse", loc="left", pad=13)
cax = ax.inset_axes([0.03, -0.045, 0.55, 0.022])
ticks = [0.25, 0.5, 1, 3, 10, 40]
cb = fig.colorbar(sc, cax=cax, orientation="horizontal", ticks=np.log10(ticks))
cb.ax.set_xticklabels(["¼", "½", "1", "3", "10", "40"])
cb.set_label("× the cell's normal level", fontsize=6.5)
cb.ax.tick_params(labelsize=6, length=2)
cb.outline.set_linewidth(0.4)
n_fr = cells["flood_ratio"].notna().sum()
ax.text(0.0, 1.008, f"26 Nov–12 Dec 2025 vs normal · {n_fr} cells · median {cells['flood_ratio'].median():.1f}×",
        transform=ax.transAxes, fontsize=6, color=MUTED, va="bottom")

# (d) station trends
TOFFS = {"Putupaula": (8, -7, "left"), "Colombo": (-7, 4, "right"), "Peradeniya": (-8, -4, "right")}
ax = axes[3]
basemap(ax)
ax.scatter(cells["lon"], cells["lat"], s=3, marker="s", c="#c9c7bd", lw=0, zorder=4)
t = stations.merge(trends, left_on="id", right_on="station", how="left")
tnorm = TwoSlopeNorm(vmin=-20, vcenter=0, vmax=20)
has = t["sk_pct_per_yr"].notna()
sig = has & t["sk_significant"].fillna(False).astype(bool)
ax.scatter(t.loc[~has, "lon"], t.loc[~has, "lat"], s=22, marker="x", c=MUTED, lw=0.9, zorder=6,
           label="< 3 years of monthly data")
ax.scatter(t.loc[has & ~sig, "lon"], t.loc[has & ~sig, "lat"], s=46, facecolor="white",
           edgecolor=DIV_CMAP(tnorm(t.loc[has & ~sig, "sk_pct_per_yr"].clip(-20, 20))), lw=1.8, zorder=6,
           label="trend not significant")
sc = ax.scatter(t.loc[sig, "lon"], t.loc[sig, "lat"], s=60, c=t.loc[sig, "sk_pct_per_yr"].clip(-20, 20),
                cmap=DIV_CMAP, norm=tnorm, edgecolor=INK, lw=0.8, zorder=7, label="significant (FDR q < 0.05)")
for r in t[has].itertuples():
    name = LABEL.get(r.id, r.id)
    pct = r.sk_pct_per_yr
    txt = f"{name} {'0' if abs(pct) < 0.5 else f'{pct:+.0f}'}%"
    dx, dy, ha = TOFFS.get(name, OFFS.get(name, (6, 0, "left")))
    ax.annotate(txt, (r.lon, r.lat), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=6,
                color=INK, fontweight="semibold" if r.sk_significant else "normal", zorder=8)
ax.set_title("(d) Station trends, 2019–2025", loc="left", pad=13)
ax.text(0.0, 1.008, "seasonal Kendall slope, % per year", transform=ax.transAxes, fontsize=6, color=MUTED, va="bottom")
ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.0), frameon=False, fontsize=6, handletextpad=0.3,
          labelspacing=0.5)
fig.text(0.02, 0.035, CREDIT + " Trends: seasonal Kendall test with Benjamini–Hochberg correction.",
         fontsize=5.6, color=MUTED, wrap=True)
save(fig, "fig2_four_panel")

# ======================================================================= figure 3
STN = {"Kelani (lower)": ["kelani_colombo", "kelani_hanwella"], "Kalu (lower)": ["kalu_putupaula", "kalu_ellagawa"],
       "Mahaweli": ["mahaweli_somawathiya", "mahaweli_manampitiya", "mahaweli_mahiyangana", "mahaweli_peradeniya"]}
TITLE = {"Kelani (lower)": "Kelani: km upstream of the mouth", "Kalu (lower)": "Kalu: km upstream of the mouth",
         "Mahaweli": "Mahaweli: km upstream of Somawathiya (approximate across reservoirs)"}
fig, axes = plt.subplots(3, 1, figsize=(7.0, 8.4), gridspec_kw={"hspace": 0.45, "height_ratios": [1, 1, 1.3]})
for ax, (reach, sts) in zip(axes, STN.items()):
    p = prof[prof["reach"] == reach].sort_values("km_from_mouth")
    k = 5 if reach != "Mahaweli" else 9
    for s in ["NEM", "FIM", "SWM", "SIM"]:
        y = p[f"spm_{s}"].rolling(k, center=True, min_periods=3).median()
        ax.plot(p["km_from_mouth"], y, color=SEASON_COL[s], lw=2 if s == "SIM" else 1.4, label=SEASON_NAME[s],
                solid_capstyle="round")
        last = y.last_valid_index()
        if last is not None:
            ax.annotate(s, (p.loc[last, "km_from_mouth"], y[last]), xytext=(4, 0), textcoords="offset points",
                        fontsize=6.5, color=MUTED, va="center")
    ax.set_yscale("log")
    ax.set_ylim(5, 250)
    ax.set_yticks([5, 10, 20, 50, 100, 200])
    ax.set_yticklabels(["5", "10", "20", "50", "100", "200"])
    ax.grid(axis="y", color="#e4e4df", lw=0.6)
    ax.set_axisbelow(True)
    for spn in ("top", "right"):
        ax.spines[spn].set_visible(False)
    ax.set_title(TITLE[reach], loc="left")
    ax.set_ylabel("SPM (g m$^{-3}$)")
    # station positions: nearest profile cell to each station
    for sid in sts:
        srow = stations[stations["id"] == sid]
        if srow.empty:
            continue
        d = np.hypot((p["lon"] - srow["lon"].iloc[0]) * KX, p["lat"] - srow["lat"].iloc[0])
        if d.min() * 111 > 5:
            continue
        km = p.loc[d.idxmin(), "km_from_mouth"]
        ax.axvline(km, color="#b9b8b0", lw=0.8, ls=(0, (2, 2)), zorder=0)
        ax.text(km, 230, LABEL.get(sid, sid), rotation=90, fontsize=6.3, color=MUTED, ha="right", va="top")
axes[-1].set_xlabel("Distance along the river (km)")
axes[0].legend(ncol=2, fontsize=6.5, frameon=False, loc="upper left", bbox_to_anchor=(0, 1.38))
fig.text(0.01, 0.01, "Lines: running median of 1 km cell medians (5 cells; 9 on the Mahaweli) per season, 2024–2025, "
         "red-band SPM (uncalibrated). Gaps: reaches without resolved channel pixels.", fontsize=5.8, color=MUTED)
save(fig, "fig3_profiles")
