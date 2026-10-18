"""Pass 1b: river-channel mask on the national 20 m grid + station snapping.

Water = Sentinel-2 strict water frequency >= 0.5 (>= 3 clear looks) within
60 m of JRC water (occurrence >= 5 %), OR JRC occurrence >= 50 (narrow
channels whose 20 m pixels are too mixed to pass the strict S2 rule).
Rivers are separated from tanks, reservoirs, lagoons and sea by width and
elongation (cog.river_mask). Pixels outside the Natural Earth land polygon
(buffered 1 km) are dropped, and so is everything within 600 m of the coast
(surf-zone slivers otherwise pass as rivers).

Writes data/cog/rivers_20m.tif and data/cog/stations.csv.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from rasterio.features import rasterize  # noqa: E402
from rasterio.warp import Resampling, reproject, transform, transform_geom  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402

from sedrs import cog, s2grid  # noqa: E402
from sedrs.config import DATA_DIR, load_settings  # noqa: E402

out = DATA_DIR / "cog"
cfg = load_settings()
tr = s2grid.transform()
shape = (s2grid.H, s2grid.W)

wc = rasterio.open(out / "water_count.tif").read(1)
cc = rasterio.open(out / "clear_count.tif").read(1)
with np.errstate(divide="ignore", invalid="ignore"):
    freq = np.where(cc >= 3, wc / cc, np.nan)

jrc = np.zeros(shape, np.uint8)
with rasterio.open(out / "jrc_occurrence.tif") as d:
    reproject(d.read(1), jrc, src_transform=d.transform, src_crs=d.crs,
              dst_transform=tr, dst_crs=s2grid.CRS, resampling=Resampling.nearest)

# S2 water must sit on or within 60 m of water JRC has seen at least occasionally
# (1984-2021); this removes speckle that no long record supports.
jrc_near = ndi.binary_dilation(jrc >= 5, iterations=3)
water_s2 = (freq >= 0.5) & jrc_near
# JRC >= 50 % keeps channels whose 20 m pixels are too mixed for the strict S2 rule
water_jrc = jrc >= 50

# land polygon (Natural Earth 1:10m) buffered ~1 km to keep river mouths
ne = json.load(open(out / "ne" / "ne_10m_admin_0_countries.geojson"))
lka = next(f for f in ne["features"] if f["properties"].get("ADM0_A3") == "LKA")
geom = transform_geom("EPSG:4326", s2grid.CRS, lka["geometry"])
land_raw = rasterize([(geom, 1)], out_shape=shape, transform=tr, dtype="uint8").astype(bool)
land = ndi.binary_dilation(land_raw, iterations=50)
# surf-zone and sea-edge slivers look like long thin "rivers" along the coast:
# keep only channels at least 600 m inside the coastline
land_core = ndi.binary_erosion(land_raw, iterations=30)

# 20 m pixels: wide = >280 m (radius 7), join gaps of ~160 m, 10-px halo removes coastal slivers.
# The filter runs on each water source separately: merging them first links channels
# to lagoons and tanks, and the merged blobs then fail the elongation test.
kw = dict(occ_min=50, wide_radius_px=7, join_radius_px=4, min_len_km=2.0, min_elong=4.0,
          px_km=0.02, wide_halo_px=10)
mask, skel = np.zeros(shape, bool), np.zeros(shape, bool)
for name, w in (("sentinel-2", water_s2 & land), ("jrc", water_jrc & land)):
    m, stats, sk = cog.river_mask(w.astype(np.uint8) * 100, **kw)
    print(name, json.dumps(stats))
    mask |= m & land_core
    skel |= sk & land_core
print("combined river px:", int(mask.sum()), " skeleton km ~", round(skel.sum() * 0.02))

prof = dict(driver="GTiff", width=s2grid.W, height=s2grid.H, count=1, dtype="uint8",
            crs=s2grid.CRS, transform=tr, compress="deflate", tiled=True)
with rasterio.open(out / "rivers_20m.tif", "w", **prof) as d:
    d.write(mask.astype("uint8"), 1)
with rasterio.open(out / "river_skeleton_20m.tif", "w", **prof) as d:
    d.write(skel.astype("uint8"), 1)
water_any = ((water_s2 | water_jrc) & land_core)
with rasterio.open(out / "water_any_20m.tif", "w", **prof) as d:
    d.write(water_any.astype("uint8"), 1)
with rasterio.open(out / "water_freq_20m.tif", "w", **{**prof, "dtype": "float32"}) as d:
    d.write(freq.astype("float32"), 1)

# ---- snap stations to the nearest river pixel within snap_search_m --------
# Stations are hand-picked river locations, so a station off the filtered
# network falls back to any confirmed water (S2 or JRC) within 1 km, using a
# 300 m AOI to stay on the channel.
search = int(cfg["snap_search_m"] / s2grid.RES)
rows = []
for s in cfg["stations"]:
    xs, ys = transform("EPSG:4326", s2grid.CRS, [s["lon"]], [s["lat"]])
    c, r = (~tr) * (xs[0], ys[0])
    r, c = int(r), int(c)
    rec = {**s, "snapped": False}
    rr = cc_ = np.array([], int)
    for cand in (("river", mask, search, cfg["station_buffer_m"]),
                 ("water", water_any, int(1000 / s2grid.RES), 300)):
        win = cand[1][r - cand[2]:r + cand[2] + 1, c - cand[2]:c + cand[2] + 1]
        rr, cc_ = np.nonzero(win)
        if len(rr):
            break
    if len(rr):
        src_name, mask_src, search, buf_m = cand
        buf = int(buf_m / s2grid.RES)
        d2 = (rr - search) ** 2 + (cc_ - search) ** 2
        k = int(np.argmin(d2))
        R, C = r - search + rr[k], c - search + cc_[k]
        x, y = tr * (C + 0.5, R + 0.5)
        lon, lat = transform(s2grid.CRS, "EPSG:4326", [x], [y])
        yy, xx = np.ogrid[-buf:buf + 1, -buf:buf + 1]
        aoi = mask_src[R - buf:R + buf + 1, C - buf:C + buf + 1] & (yy ** 2 + xx ** 2 <= buf ** 2)
        rec.update(snapped=True, aoi_source=src_name, aoi_radius_m=buf_m,
                   row=int(R), col=int(C), lon=round(lon[0], 6), lat=round(lat[0], 6),
                   moved_m=round(float(np.sqrt(d2[k])) * s2grid.RES), aoi_river_px=int(aoi.sum()))
    search = int(cfg["snap_search_m"] / s2grid.RES)
    rows.append(rec)
st = pd.DataFrame(rows)
st.to_csv(out / "stations.csv", index=False)
print(st[["id", "snapped", "aoi_source", "moved_m", "aoi_river_px"]].to_string(index=False))
