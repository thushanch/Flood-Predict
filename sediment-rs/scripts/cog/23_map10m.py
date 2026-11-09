"""National 10 m river sediment map from the per-tile sums (22_extract_river10m.py).

Per river pixel with >= 5 valid views (2019-2025): geometric-mean red-band SPM (g m-3, Nechad), mean NDTI and the
number of views; seasonal geometric-mean SPM where a season has >= 3 views.

    python scripts/cog/23_map10m.py
Writes data/cog/r10m/maps/: river_sediment_10m.tif (bands: SPM, NDTI, views; national 10 m grid, UTM 44N),
river_spm_seasons_10m.tif (NEM, FIM, SWM, SIM), river_cells_1km.csv, stats.json, and the figure
fig_national_10m.(png|pdf)
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
import rasterio  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402
from matplotlib.ticker import FixedFormatter, FixedLocator, NullFormatter  # noqa: E402
from rasterio.transform import Affine  # noqa: E402
from rasterio.warp import Resampling, reproject, transform, transform_geom  # noqa: E402
from rasterio.windows import Window  # noqa: E402

from sedrs.config import DATA_DIR, OUT_DIR  # noqa: E402

R = DATA_DIR / "cog" / "r10m"
M = R / "maps"
M.mkdir(exist_ok=True)
X0, Y1, X1, Y0 = 320000.0, 1100000.0, 620000.0, 640000.0      # national grid (as sedrs.s2grid), 10 m
W, H = int((X1 - X0) / 10), int((Y1 - Y0) / 10)
NTR = Affine(10, 0, X0, 0, -10, Y1)
plt.rcParams.update({"font.family": "Inter", "font.size": 8, "axes.titlesize": 8.5, "axes.titleweight": "semibold",
                     "savefig.dpi": 300, "axes.edgecolor": "#8a8f8c", "axes.linewidth": 0.6})
INK, MUTED = "#1f2523", "#5c625f"

# ------------------------------------------------------------------ per-tile maps
tiles = [p.name for p in sorted(R.iterdir()) if (p / "accum.npz").exists()]
tile_files, stats = [], {"tiles": {}}
cells = []
for t in tiles:
    D = R / t
    blocks = json.loads((D / "blocks.json").read_text())
    with rasterio.open(D / "river.tif") as d:
        river = d.read(1) > 0
        prof = d.profile
    rows, cols = [], []
    for b in blocks:
        sub = river[b["row"]:b["row"] + b["h"], b["col"]:b["col"] + b["w"]]
        p = np.flatnonzero(sub)
        rows.append(b["row"] + p // b["w"])
        cols.append(b["col"] + p % b["w"])
    rows, cols = np.concatenate(rows), np.concatenate(cols)
    z = np.load(D / "accum.npz", allow_pickle=True)
    nd, ls, n = z["ndti"].astype(np.float64), z["lspm"].astype(np.float64), z["n"].astype(np.float64)
    nall = n.sum(0)
    ok = nall >= 5
    bands = [10 ** (ls.sum(0) / np.maximum(nall, 1)), nd.sum(0) / np.maximum(nall, 1), nall]
    masks = [ok, ok, ok]
    for s in range(4):
        bands.append(10 ** (ls[s] / np.maximum(n[s], 1)))
        masks.append(n[s] >= 3)
    prof.update(dtype="float32", count=len(bands), nodata=np.nan, compress="deflate", predictor=3)
    with rasterio.open(D / "map10m.tif", "w", **prof) as d:
        for k, (v, m) in enumerate(zip(bands, masks), 1):
            a = np.full(river.shape, np.nan, np.float32)
            a[rows[m], cols[m]] = v[m]
            d.write(a, k)
    tile_files.append(D / "map10m.tif")
    stats["tiles"][t] = {"river_px": int(len(rows)), "mapped_px": int(ok.sum()),
                         "median_views": float(np.median(nall[ok])) if ok.any() else 0}
    # 1 km summaries of the map (for tables and the web page)
    xs = prof["transform"].c + (cols[ok] + 0.5) * 10
    ys = prof["transform"].f - (rows[ok] + 0.5) * 10
    cells.append(pd.DataFrame({"cx": np.floor(xs / 1000).astype(int), "cy": np.floor(ys / 1000).astype(int),
                               "lspm": ls.sum(0)[ok] / nall[ok], "ndti": nd.sum(0)[ok] / nall[ok],
                               **{f"l{s}": np.where(n[s][ok] >= 3, ls[s][ok] / np.maximum(n[s][ok], 1), np.nan)
                                  for s in range(4)}}))
    print(t, stats["tiles"][t], flush=True)

c = pd.concat(cells)
g = c.groupby(["cx", "cy"])
cell = g.agg(px=("lspm", "size"), lspm=("lspm", "median"), ndti=("ndti", "median"),
             l0=("l0", "median"), l1=("l1", "median"), l2=("l2", "median"), l3=("l3", "median")).reset_index()
cell = cell[cell["px"] >= 10]
lon, lat = transform("EPSG:32644", "EPSG:4326", (cell["cx"] * 1000 + 500).tolist(), (cell["cy"] * 1000 + 500).tolist())
cell["lon"], cell["lat"] = np.round(lon, 5), np.round(lat, 5)
cell["spm"] = (10 ** cell["lspm"]).round(1)
for s, nm in enumerate(("NEM", "FIM", "SWM", "SIM")):
    cell[f"spm_{nm}"] = (10 ** cell[f"l{s}"]).round(1)
cell["peak"] = cell[[f"spm_{s}" for s in ("NEM", "FIM", "SWM", "SIM")]].idxmax(axis=1).str[4:]
cell["ndti"] = cell["ndti"].round(3)
cell = cell.drop(columns=["lspm", "l0", "l1", "l2", "l3"])
cell.to_csv(M / "river_cells_1km.csv", index=False)

# ------------------------------------------------------------------ national mosaics (strip by strip)
def mosaic(name, band_ids, descs):
    p = {"driver": "GTiff", "width": W, "height": H, "count": len(band_ids), "dtype": "float32", "nodata": np.nan,
         "crs": "EPSG:32644", "transform": NTR, "compress": "deflate", "predictor": 3, "tiled": True,
         "blockxsize": 512, "blockysize": 512, "BIGTIFF": "IF_SAFER"}
    srcs = [rasterio.open(f) for f in tile_files]
    with rasterio.open(M / name, "w", **p) as dst:
        for r0 in range(0, H, 2048):
            h = min(2048, H - r0)
            out = np.full((len(band_ids), h, W), np.nan, np.float32)
            ys1 = Y1 - r0 * 10
            for s in srcs:
                tr = s.transform
                tr0 = int(round((tr.f - ys1) / 10))                     # tile row at strip top
                tc0 = int(round((X0 - tr.c) / 10))                      # tile col at grid col 0
                rr0, rr1 = max(tr0, 0), min(tr0 + h, s.height)
                cc0, cc1 = max(tc0, 0), min(tc0 + W, s.width)
                if rr0 >= rr1 or cc0 >= cc1:
                    continue
                a = s.read(band_ids, window=Window(cc0, rr0, cc1 - cc0, rr1 - rr0))
                o = out[:, rr0 - tr0:rr1 - tr0, cc0 - tc0:cc1 - tc0]
                m = np.isfinite(a)
                o[m] = a[m]
            dst.write(out, window=Window(0, r0, W, h))
        dst.descriptions = tuple(descs)
    for s in srcs:
        s.close()


mosaic("river_sediment_10m.tif", [1, 2, 3], ["SPM g m-3 (geometric mean)", "NDTI (mean)", "valid views"])
mosaic("river_spm_seasons_10m.tif", [4, 5, 6, 7], ["SPM NEM", "SPM FIM", "SPM SWM", "SPM SIM"])
tot_px = sum(v["mapped_px"] for v in stats["tiles"].values())
stats.update({"mapped_px": tot_px, "mapped_km2": round(tot_px * 1e-4, 1), "cells_1km": int(len(cell)),
              "median_spm_cells": float(cell["spm"].median()),
              "peak_counts": cell["peak"].value_counts().to_dict()})
(M / "stats.json").write_text(json.dumps(stats, indent=1))
print(json.dumps({k: v for k, v in stats.items() if k != "tiles"}, indent=1))

# ------------------------------------------------------------------ national figure
INSETS = json.loads((M / "insets.json").read_text()) if (M / "insets.json").exists() else []
COARSE = 20                                                     # 200 m display cells for the overview
ov = np.full((H // COARSE, W // COARSE), np.nan, np.float32)
with rasterio.open(M / "river_sediment_10m.tif") as d, np.errstate(all="ignore"):
    import warnings
    warnings.simplefilter("ignore", RuntimeWarning)
    step = COARSE * 100
    for r0 in range(0, (H // COARSE) * COARSE, step):
        h = min(step, (H // COARSE) * COARSE - r0)
        a = d.read(1, window=Window(0, r0, (W // COARSE) * COARSE, h))
        ov[r0 // COARSE:(r0 + h) // COARSE] = np.nanmax(
            a.reshape(h // COARSE, COARSE, W // COARSE, COARSE), axis=(1, 3))
hs = np.load(OUT_DIR / "cog" / "hillshade.npz")
e = hs["extent"]
hs_tr = Affine((e[1] - e[0]) / hs["hillshade"].shape[1], 0, e[0], 0, -(e[3] - e[2]) / hs["hillshade"].shape[0], e[3])
hsu = np.full(ov.shape, np.nan, np.float32)
reproject(hs["hillshade"].astype(np.float32), hsu, src_transform=hs_tr, src_crs="EPSG:4326",
          dst_transform=Affine(10 * COARSE, 0, X0, 0, -10 * COARSE, Y1), dst_crs="EPSG:32644",
          resampling=Resampling.bilinear, src_nodata=np.nan, dst_nodata=np.nan)
with open(DATA_DIR / "cog" / "ne" / "ne_10m_admin_0_countries.geojson") as f:
    slg = next(ft["geometry"] for ft in json.load(f)["features"] if ft["properties"].get("ADMIN") == "Sri Lanka")
slu = transform_geom("EPSG:4326", "EPSG:32644", slg)
from rasterio.features import rasterize  # noqa: E402

land = rasterize([(slu, 1)], out_shape=ov.shape, transform=Affine(10 * COARSE, 0, X0, 0, -10 * COARSE, Y1),
                 dtype="uint8")
from scipy import ndimage as ndi  # noqa: E402

vis = np.where(np.isfinite(ov), ov, -1)
vis = ndi.grey_dilation(vis, size=(2, 2))                       # widen 200 m lines a little for visibility
vis = np.where(vis > 0, vis, np.nan)
norm = LogNorm(5, 200)
cmap = plt.get_cmap("YlOrBr").copy()
fig = plt.figure(figsize=(7.4, 9.6))
ax = fig.add_axes([0.0, 0.08, 0.56, 0.84])
ext = (X0, X1, Y0, Y1)
ax.imshow(np.where(land > 0, 1.0, np.nan), extent=ext, cmap="Greys", vmin=0, vmax=8, zorder=0)
ax.imshow(np.where(land > 0, hsu, np.nan), extent=ext, cmap="Greys_r", vmin=-0.3, vmax=1.2, alpha=0.35, zorder=1)
im = ax.imshow(vis, extent=ext, cmap=cmap, norm=norm, interpolation="nearest", zorder=2)
ax.set_xlim(335000, 600000)
ax.set_ylim(650000, 1090000)
ax.set_aspect("equal")
ax.set_axis_off()
for k, ins in enumerate(INSETS):
    x, y = transform("EPSG:4326", "EPSG:32644", [ins["lon"]], [ins["lat"]])
    hw = ins["km"] * 500
    ax.add_patch(plt.Rectangle((x[0] - hw, y[0] - hw), 2 * hw, 2 * hw, fill=False, ec=INK, lw=0.7, zorder=3))
    ax.text(x[0] + hw + 1500, y[0] + hw, "ABCDEF"[k], fontsize=7, fontweight="bold", va="top", zorder=3)
    axz = fig.add_axes([0.58, 0.72 - k * 0.205, 0.40, 0.19])
    c0, r0 = int((x[0] - hw - X0) / 10), int((Y1 - (y[0] + hw)) / 10)
    nn = int(2 * hw / 10)
    with rasterio.open(M / "river_sediment_10m.tif") as d:
        a = d.read(1, window=Window(c0, r0, nn, nn))
    axz.set_facecolor("#eceee9")
    axz.imshow(a, cmap=cmap, norm=norm, interpolation="nearest", extent=(0, 2 * hw, 0, 2 * hw))
    axz.set_xticks([])
    axz.set_yticks([])
    axz.set_title(f"{'ABCDEF'[k]}  {ins['name']}", loc="left", fontsize=7)
    axz.plot([2 * hw - 1200, 2 * hw - 200], [250, 250], color=INK, lw=1.4)
    axz.text(2 * hw - 700, 380, "1 km", ha="center", fontsize=6)
cax = fig.add_axes([0.05, 0.075, 0.45, 0.012])
cb = fig.colorbar(im, cax=cax, orientation="horizontal")
cb.ax.xaxis.set_major_locator(FixedLocator([5, 10, 20, 50, 100, 200]))
cb.ax.xaxis.set_major_formatter(FixedFormatter(["5", "10", "20", "50", "100", "200"]))
cb.ax.xaxis.set_minor_formatter(NullFormatter())
cb.ax.tick_params(labelsize=6)
cb.set_label("Surface SPM, geometric mean 2019–2025 (g m⁻³, red band, uncalibrated)", fontsize=6.5)
fig.text(0.02, 0.965, "Sri Lankan rivers at 10 m: suspended sediment from Sentinel-2", fontsize=11,
         fontweight="semibold", color=INK)
fig.text(0.02, 0.947, f"{stats['mapped_km2']:,.0f} km² of river channel mapped at 10 m · "
         f"{stats['cells_1km']:,} one-km river cells · 2019–2025", fontsize=7, color=MUTED)
fig.text(0.02, 0.035, "Overview: 200 m cells showing the highest 10 m value, widened for visibility. Insets: true 10 m "
         "pixels with ≥ 5 clear water views.\nRivers narrower than about 20 m, or hidden under trees, are not "
         "mapped; lakes, reservoirs, tanks and lagoons are excluded.", fontsize=6, color=MUTED, va="top")
for ext_ in ("png", "pdf"):
    fig.savefig(M / f"fig_national_10m.{ext_}", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("written to", M)
