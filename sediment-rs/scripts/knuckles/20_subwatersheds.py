"""Provisional sub-watersheds for the Knuckles downstream study area (until IWMI's boundaries arrive).

Copernicus GLO-90 DEM -> pit/depression fill -> D8 flow -> catchment of the Mahaweli at
Somawathiya (below the Amban Ganga confluence). The catchment is split at tributary
junctions: every point where a stream draining >= MIN_TRIB_KM2 enters a channel draining
at least 2x more becomes an outlet. Units are carved from largest to smallest so nested
tributaries get their own unit; whatever remains drains straight to the main stem.
Units that include part of the Knuckles range (Knuckles Conservation Forest, approx.
7.33-7.58 N, 80.70-80.90 E) are flagged.

Writes data/knuckles/: dem90.tif, flowdir/acc rasters, subwatersheds.tif + .geojson,
streams.geojson.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np  # noqa: E402
import rasterio  # noqa: E402
from rasterio.features import shapes  # noqa: E402
from rasterio.merge import merge  # noqa: E402

from sedrs import cog  # noqa: E402
from sedrs.config import DATA_DIR  # noqa: E402

OUT = DATA_DIR / "knuckles"
OUT.mkdir(parents=True, exist_ok=True)
BOUNDS = (80.30, 6.75, 81.45, 8.45)
BURN_M = 15.0          # metres cut along satellite-mapped channels and stable water
MIN_TRIB_KM2 = float(sys.argv[1]) if len(sys.argv) > 1 else 250.0
# smaller tributaries (100-250 km2) get their own unit only if >= 30 % of them lies in the Knuckles range
MIN_KNUCKLES_TRIB_KM2, MIN_KNUCKLES_SHARE = 100.0, 0.30
# Mahaweli below the Amban Ganga confluence. On the flat floodplain the 90 m DEM keeps the
# Amban Ganga in its own channel beside the Mahaweli until ~8.19 N, so the outlet sits there.
OUTLET = (81.190, 8.200)
KNUCKLES = (80.70, 7.33, 80.90, 7.58)        # lon0, lat0, lon1, lat1 (approximate range extent)
NAMED_POINTS = {                             # approximate, for naming units only
    "Amban Ganga": (80.80, 7.80), "Kalu Ganga (Laggala)": (80.83, 7.58), "Heen Ganga": (80.95, 7.40),
    "Hasalaka Oya": (80.98, 7.33), "Hulu Ganga": (80.75, 7.33), "Upper Mahaweli (above Victoria)": (80.60, 7.15),
    "Uma Oya / Badulu Oya": (81.05, 7.05), "Mahaweli main stem": (81.05, 7.75),
    "Amban Ganga (lower) / Elahera": (80.90, 7.85), "Kalu Ganga / Moragahakanda": (80.72, 7.68),
}

# ------------------------------------------------------------------ DEM
cog.set_gdal_env()
dem_path = OUT / "dem90.tif"
if not dem_path.exists():
    srcs = []
    for lat in (6, 7, 8):
        for lon in (80, 81):
            n = f"Copernicus_DSM_COG_30_N{lat:02d}_00_E{lon:03d}_00_DEM"
            srcs.append(rasterio.open(f"/vsicurl/https://copernicus-dem-90m.s3.amazonaws.com/{n}/{n}.tif"))
    arr, tr = merge(srcs, bounds=BOUNDS)
    prof = dict(driver="GTiff", width=arr.shape[2], height=arr.shape[1], count=1, dtype="float32",
                crs="EPSG:4326", transform=tr, nodata=-9999, compress="deflate")
    with rasterio.open(dem_path, "w", **prof) as d:
        d.write(arr[0].astype("float32"), 1)

if not hasattr(np, "in1d"):          # pysheds still calls np.in1d, removed in numpy 2.x
    np.in1d = lambda a, b, **kw: np.isin(np.ravel(a), b, **kw)
from pysheds.grid import Grid  # noqa: E402

# Stream burning: in the flat dry zone, tank bunds and floodplain flats in a 90 m DEM send
# flow the wrong way (the Amban Ganga was routed away from the Mahaweli without this).
# Lowering the DEM along channels and stable water mapped from Sentinel-2/JRC
# (data/cog/rivers_20m.tif, data/cog/jrc_occurrence.tif) enforces the observed network.
from rasterio.warp import Resampling, reproject  # noqa: E402

burn_path = OUT / "dem90_burned.tif"
with rasterio.open(dem_path) as d:
    demv, prof_b = d.read(1), d.profile
    burn = np.zeros(demv.shape, np.uint8)
    for src_path, thr in ((DATA_DIR / "cog" / "rivers_20m.tif", 1), (DATA_DIR / "cog" / "jrc_occurrence.tif", 50)):
        with rasterio.open(src_path) as s_:
            tmp = np.zeros(demv.shape, np.uint8)
            reproject((s_.read(1) >= thr).astype(np.uint8), tmp, src_transform=s_.transform, src_crs=s_.crs,
                      dst_transform=d.transform, dst_crs=d.crs, resampling=Resampling.max)
            burn |= tmp
    demb = np.where((burn > 0) & (demv > 0), demv - BURN_M, demv).astype("float32")
with rasterio.open(burn_path, "w", **prof_b) as d:
    d.write(demb, 1)
print(f"burned {int((burn > 0).sum())} DEM cells")

grid = Grid.from_raster(str(burn_path))
dem = grid.read_raster(str(burn_path))
inflated = grid.resolve_flats(grid.fill_depressions(grid.fill_pits(dem)))
fdir = grid.flowdir(inflated)
acc = grid.accumulation(fdir)
with rasterio.open(dem_path) as d:
    tr, crs = d.transform, d.crs
    shape = (d.height, d.width)
lat_c = np.linspace(BOUNDS[3], BOUNDS[1], shape[0])[:, None]
cell_km2 = (abs(tr.a) * 111.32 * np.cos(np.radians(lat_c))) * (abs(tr.e) * 110.57)
acc_km2 = np.asarray(acc) * float(np.median(cell_km2))

# ------------------------------------------------------------------ upstream traversal
moves = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
fd = np.asarray(fdir)
H_, W_ = shape
down = np.full(H_ * W_, -1, np.int64)                # flat index of the downstream cell
for code, (dr, dc) in moves.items():
    r_, c_ = np.nonzero(fd == code)
    r2, c2 = r_ + dr, c_ + dc
    ok = (r2 >= 0) & (r2 < H_) & (c2 >= 0) & (c2 < W_)
    down[r_[ok] * W_ + c_[ok]] = r2[ok] * W_ + c2[ok]
src = np.nonzero(down >= 0)[0]
order = np.argsort(down[src], kind="stable")
up_src, up_dst = src[order], down[src][order]       # edges grouped by downstream cell
starts = np.searchsorted(up_dst, np.arange(H_ * W_))
ends = np.searchsorted(up_dst, np.arange(H_ * W_), side="right")


def catchment(r, c):
    """Boolean mask of every cell that drains to (r, c)."""
    m = np.zeros(H_ * W_, bool)
    stack = [r * W_ + c]
    m[stack[0]] = True
    while stack:
        i = stack.pop()
        for j in up_src[starts[i]:ends[i]]:
            if not m[j]:
                m[j] = True
                stack.append(j)
    return m.reshape(shape)


# ------------------------------------------------------------------ main catchment
c_f, r_f = ~tr * OUTLET
rr, cc = np.nonzero(acc_km2 > 8500)
k = int(np.argmin((rr - r_f) ** 2 + (cc - c_f) ** 2))
r_out, c_out = int(rr[k]), int(cc[k])
x, y = tr * (c_out + 0.5, r_out + 0.5)
basin = catchment(r_out, c_out)
print(f"Mahaweli catchment at ({x:.3f}, {y:.3f}): {basin.sum() * np.median(cell_km2):.0f} km2")

# ------------------------------------------------------------------ tributary outlets
kn = np.zeros(shape, bool)
_c0, _r0 = ~tr * (KNUCKLES[0], KNUCKLES[3])
_c1, _r1 = ~tr * (KNUCKLES[2], KNUCKLES[1])
kn[int(_r0):int(_r1), int(_c0):int(_c1)] = True
rows, cols = np.nonzero(basin & (acc_km2 >= MIN_KNUCKLES_TRIB_KM2))
outlets = []
for r, c in zip(rows, cols):
    mv = moves.get(int(fd[r, c]))
    if mv is None:
        continue
    r2, c2 = r + mv[0], c + mv[1]
    if 0 <= r2 < shape[0] and 0 <= c2 < shape[1] and acc_km2[r2, c2] >= 2 * acc_km2[r, c] + 50:
        if acc_km2[r, c] < MIN_TRIB_KM2:
            cm = catchment(r, c)
            if (cm & kn).sum() < MIN_KNUCKLES_SHARE * cm.sum():
                continue
        outlets.append((r, c, acc_km2[r, c]))
outlets.append((r_out, c_out, float(acc_km2[r_out, c_out])))   # main outlet
outlets.sort(key=lambda o: -o[2])
labels = np.zeros(shape, np.int16)
for k, (r, c, _a) in enumerate(outlets, start=1):
    labels[catchment(r, c) & basin] = k
print(f"{len(outlets)} units: tributaries >= {MIN_TRIB_KM2:.0f} km2, or >= {MIN_KNUCKLES_TRIB_KM2:.0f} km2 "
      f"with >= {MIN_KNUCKLES_SHARE:.0%} in the Knuckles range")

# ------------------------------------------------------------------ describe units
area = {k: float(cell_km2[np.nonzero(labels == k)[0], 0].sum()) for k in range(1, len(outlets) + 1)}
units = []
for k, (r, c, a) in enumerate(outlets, start=1):
    m = labels == k
    if not m.any():
        continue
    lon, lat = tr * (c + 0.5, r + 0.5)
    cy, cx = [v.mean() for v in np.nonzero(m)]
    clon, clat = tr * (cx + 0.5, cy + 0.5)
    name = min(NAMED_POINTS, key=lambda n: (NAMED_POINTS[n][0] - clon) ** 2 + (NAMED_POINTS[n][1] - clat) ** 2)
    units.append({"unit": k, "area_km2": round(area[k], 1), "outlet_lon": round(lon, 4), "outlet_lat": round(lat, 4),
                  "upstream_km2_at_outlet": round(float(a), 0), "centroid_lon": round(clon, 3),
                  "centroid_lat": round(clat, 3), "near_name": name,
                  "knuckles_share_pct": round(100 * (m & kn).sum() / m.sum(), 1),
                  "drains_knuckles": bool((m & kn).sum() > 0.02 * kn.sum())})
units.sort(key=lambda u: -u["area_km2"])

prof = dict(driver="GTiff", width=shape[1], height=shape[0], count=1, dtype="int16", crs=crs, transform=tr,
            nodata=0, compress="deflate")
with rasterio.open(OUT / "subwatersheds.tif", "w", **prof) as d:
    d.write(labels, 1)
with rasterio.open(OUT / "acc_km2.tif", "w", **{**prof, "dtype": "float32", "nodata": None}) as d:
    d.write(acc_km2.astype("float32"), 1)
info = {u["unit"]: u for u in units}
feats = [{"type": "Feature", "geometry": g, "properties": info[int(v)]}
         for g, v in shapes(labels, mask=labels > 0, transform=tr) if int(v) in info]
(OUT / "subwatersheds.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
(OUT / "subwatersheds.json").write_text(json.dumps(units, indent=1))
streams = (acc_km2 >= 50) & basin
sfeats = [{"type": "Feature", "geometry": g, "properties": {}} for g, v in shapes(streams.astype("uint8"),
                                                                               mask=streams, transform=tr)]
(OUT / "streams_mask.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": sfeats}))
for u in units:
    print(f"unit {u['unit']:2d} {u['area_km2']:7.0f} km2  near {u['near_name']:32s} "
          f"Knuckles {u['knuckles_share_pct']:5.1f}%  {'*' if u['drains_knuckles'] else ''}")
kn_area = sum(u["area_km2"] for u in units if u["drains_knuckles"])
print(f"units draining the Knuckles: {sum(u['drains_knuckles'] for u in units)}, {kn_area:.0f} km2")
