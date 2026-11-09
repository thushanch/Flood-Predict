"""National 10 m river channels, one Sentinel-2 tile at a time.

For each MGRS tile (in its own 10 m pixel grid, UTM 44N):
  1. Ownership: a pixel belongs to the covering tile whose centre is nearest, so overlaps are mapped once.
  2. Search corridor: within 400 m of DEM streams draining >= 25 km2 (20_streams_dem.py), or within 100 m of the
     20 m satellite river mask; on land and >= 600 m from the coast (Natural Earth).
  3. Water frequency at 10 m from low-cloud scenes (2019-2025, <= 15 % cloud, up to 6 per calendar month):
     SCL clear and NDWI (B03, B08) > 0.
  4. River channel: water in >= 25 % of clear views, extended along connected pixels with >= 8 % (hysteresis),
     minus lakes, reservoirs and tanks. A water body counts as a lake when its core is >= 70 m wide (opening with
     a disk of radius 3), unless >= 30 % of it lies on the 20 m river mask or its centre line is >= 3 km long
     with a mean width < 250 m. River pieces must have >= 300 m of centre line.

    python scripts/cog/21_rivers10m.py 44NMP 44NLN ...      (no tiles = all)
Writes data/cog/r10m/<tile>/: river.tif (water frequency %, 0 = not river), blocks.json, meta.json
"""
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from rasterio.features import rasterize  # noqa: E402
from rasterio.transform import Affine  # noqa: E402
from rasterio.warp import Resampling, reproject, transform_geom  # noqa: E402
from rasterio.windows import Window  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402
from skimage.filters import apply_hysteresis_threshold  # noqa: E402
from skimage.morphology import disk, skeletonize  # noqa: E402

from sedrs import cog  # noqa: E402
from sedrs.config import DATA_DIR  # noqa: E402

cog.set_gdal_env()
R = DATA_DIR / "cog" / "r10m"
TPX, BLK = 10980, 1024
tiles = sys.argv[1:] or cog.SL_TILES
scenes = pd.read_csv(DATA_DIR / "cog" / "scenes.csv").drop_duplicates("id")


def tile_ul(t):
    pre = scenes[scenes["tile"] == t]["prefix"].iloc[0]
    with rasterio.open(cog.band_url(pre, "B04")) as d:
        return d.transform.c, d.transform.f


UL_PATH = R / "tile_ul.json"
if UL_PATH.exists():
    UL = {k: tuple(v) for k, v in json.loads(UL_PATH.read_text()).items()}
else:
    UL = {t: tile_ul(t) for t in cog.SL_TILES}
    UL_PATH.write_text(json.dumps(UL))

with open(DATA_DIR / "cog" / "ne" / "ne_10m_admin_0_countries.geojson") as f:
    sl_geom = next(ft["geometry"] for ft in json.load(f)["features"]
                   if ft["properties"].get("ADMIN") == "Sri Lanka" or ft["properties"].get("NAME") == "Sri Lanka")
sl_utm = transform_geom("EPSG:4326", "EPSG:32644", sl_geom)


def coarse_inputs(t, step=5):
    """Ownership, corridor and inland mask on a 50 m grid of tile t, then repeated to 10 m."""
    x0, y1 = UL[t]
    n = TPX // step + 1
    tr50 = Affine(10 * step, 0, x0, 0, -10 * step, y1)
    yy = y1 - (np.arange(n) + 0.5) * 10 * step
    xx = x0 + (np.arange(n) + 0.5) * 10 * step
    X, Y = np.meshgrid(xx, yy)
    half = TPX * 10 / 2
    me = np.hypot(X - (x0 + half), Y - (y1 - half))
    own = np.ones_like(me, bool)
    for u, (ux, uy) in UL.items():
        if u == t:
            continue
        inside = (X >= ux) & (X < ux + 2 * half) & (Y <= uy) & (Y > uy - 2 * half)
        own &= ~(inside & (np.hypot(X - (ux + half), Y - (uy - half)) < me))
    land = rasterize([(sl_utm, 1)], out_shape=(n, n), transform=tr50, dtype="uint8").astype(bool)
    inland = ndi.binary_erosion(land, iterations=12)                 # >= 600 m from the coast
    st = np.zeros((n, n), np.uint8)
    with rasterio.open(R / "streams90.tif") as d:
        reproject(d.read(1), st, src_transform=d.transform, src_crs=d.crs, dst_transform=tr50,
                  dst_crs="EPSG:32644", resampling=Resampling.max)
    corr = ndi.binary_dilation(st > 0, structure=disk(8))               # 400 m
    r20 = np.zeros((n, n), np.uint8)
    with rasterio.open(DATA_DIR / "cog" / "rivers_20m.tif") as d:
        reproject(d.read(1), r20, src_transform=d.transform, src_crs=d.crs, dst_transform=tr50,
                  dst_crs="EPSG:32644", resampling=Resampling.max)
    corr |= ndi.binary_dilation(r20 > 0, iterations=2)                  # 100 m
    m = own & inland & corr
    return np.repeat(np.repeat(m, step, 0), step, 1)[:TPX, :TPX], int(own.sum()), int((own & inland).sum())


def process_tile(t):
    out = R / t
    out.mkdir(exist_ok=True)
    if (out / "river.tif").exists():
        print(t, "done already")
        return
    t0 = time.time()
    corr, _, _ = coarse_inputs(t)
    blocks = []
    for bi in range(0, TPX, BLK):
        for bj in range(0, TPX, BLK):
            h, w = min(BLK, TPX - bi), min(BLK, TPX - bj)
            if corr[bi:bi + h, bj:bj + w].any():
                blocks.append({"row": bi, "col": bj, "h": h, "w": w})
    if not blocks:
        (out / "meta.json").write_text(json.dumps({"tile": t, "blocks": 0}))
        print(t, "no corridor")
        return
    sel = scenes[(scenes["tile"] == t) & (scenes["cloud"] <= 15)].copy()
    sel["month"] = sel["date"].str[5:7]
    pick = []
    for _, g in sel.sort_values("date").groupby("month"):
        idx = np.linspace(0, len(g) - 1, min(6, len(g))).round().astype(int)
        pick.append(g.iloc[np.unique(idx)])
    sel = pd.concat(pick) if pick else sel
    fpath = out / "freq.tif"
    nf = 0
    tile_prof = {"driver": "GTiff", "width": TPX, "height": TPX, "count": 1, "dtype": "uint8", "crs": "EPSG:32644",
                 "transform": Affine(10, 0, UL[t][0], 0, -10, UL[t][1]), "compress": "deflate", "tiled": True,
                 "blockxsize": 512, "blockysize": 512}
    if fpath.exists():                                   # reuse a saved frequency pass
        with rasterio.open(fpath) as d:
            fr = d.read(1)
        freq = np.where(fr == 255, 0, fr / 100.0).astype(np.float32)
    else:
        valid = np.zeros((TPX, TPX), np.uint16)
        water = np.zeros((TPX, TPX), np.uint16)
        lock = threading.Lock()

        def run(row):
            ds = {b: rasterio.open(cog.band_url(row.prefix, b)) for b in ("B03", "B08", "SCL")}
            try:
                for b in blocks:
                    sl = (slice(b["row"], b["row"] + b["h"]), slice(b["col"], b["col"] + b["w"]))
                    s = ds["SCL"].read(1, window=Window(b["col"] // 2, b["row"] // 2, (b["w"] + 1) // 2,
                                                        (b["h"] + 1) // 2))
                    s = np.repeat(np.repeat(s, 2, 0), 2, 1)[:b["h"], :b["w"]]
                    ok = ~np.isin(s, cog.SCL_BAD) & corr[sl]
                    if not ok.any():
                        continue
                    g = ds["B03"].read(1, window=Window(b["col"], b["row"], b["w"], b["h"])).astype(np.float32)
                    n = ds["B08"].read(1, window=Window(b["col"], b["row"], b["w"], b["h"])).astype(np.float32)
                    ok &= (g > 0) & (n > 0)
                    wat = ok & ((g - n) > 0)                                     # NDWI > 0
                    with lock:
                        valid[sl] += ok
                        water[sl] += wat
            finally:
                for d in ds.values():
                    d.close()

        with ThreadPoolExecutor(12) as ex:
            futs = [ex.submit(run, r) for r in sel.itertuples()]
            for f in as_completed(futs):
                try:
                    f.result()
                except Exception as e:
                    nf += 1
                    print(t, "scene failed:", repr(e)[:100], flush=True)
        freq = np.where(valid >= 8, water.astype(np.float32) / np.maximum(valid, 1), 0)
        water = None
        with rasterio.open(fpath, "w", nodata=255, **tile_prof) as d:
            d.write(np.where(valid >= 8, np.round(freq * 100), 255).astype(np.uint8), 1)
        valid = None
    # hysteresis: water in >= 8 % of views is kept where it connects to water seen in >= 25 % of views
    wmax = apply_hysteresis_threshold(np.where(corr, freq, 0), 0.08, 0.25)
    wmax = ndi.binary_closing(wmax, structure=np.ones((3, 3))) & corr
    core = ndi.binary_opening(wmax, structure=disk(3))
    lab, nc = ndi.label(core, structure=np.ones((3, 3)))
    # a wide water body is river, not lake, when >= 30 % of it lies on the 20 m river mask (which already
    # separates rivers from lakes), or when its centre line is >= 3 km long and its mean width < 250 m
    r20 = np.zeros((TPX, TPX), np.uint8)
    with rasterio.open(DATA_DIR / "cog" / "rivers_20m.tif") as d:
        reproject(d.read(1), r20, src_transform=d.transform, src_crs=d.crs,
                  dst_transform=Affine(10, 0, UL[t][0], 0, -10, UL[t][1]), dst_crs="EPSG:32644",
                  resampling=Resampling.nearest)
    r20 = ndi.binary_dilation(r20 > 0, iterations=4)
    cid = np.arange(1, nc + 1)
    c_area = ndi.sum(core, lab, cid)
    on20 = ndi.sum(r20, lab, cid) / np.maximum(c_area, 1)
    c_len = ndi.sum(skeletonize(core), lab, cid) * 10.0
    c_width = c_area * 100 / np.maximum(c_len, 10)
    riverlike = (on20 >= 0.3) | ((c_len >= 3000) & (c_width < 250))
    lake = np.r_[False, ~riverlike]
    del core, r20
    lake_zone = ndi.binary_dilation(lake[lab] & (lab > 0), structure=disk(4)) & wmax
    del lab
    river = wmax & ~ndi.binary_dilation(lake_zone, iterations=3)
    del lake_zone
    rl, nr = ndi.label(river, structure=np.ones((3, 3)))
    ids = np.arange(1, nr + 1)
    slen = ndi.sum(skeletonize(river), rl, ids) * 10.0
    keep = np.zeros(nr + 1, bool)
    keep[ids[slen >= 300]] = True
    river = keep[rl]
    del rl
    out_arr = np.where(river, np.clip(np.round(freq * 100), 1, 100), 0).astype(np.uint8)
    prof = {"driver": "GTiff", "width": TPX, "height": TPX, "count": 1, "dtype": "uint8", "nodata": 0,
            "crs": "EPSG:32644", "transform": Affine(10, 0, UL[t][0], 0, -10, UL[t][1]), "compress": "deflate",
            "tiled": True, "blockxsize": 512, "blockysize": 512}
    with rasterio.open(out / "river.tif", "w", **prof) as d:
        d.write(out_arr, 1)
    rblocks = [b for b in blocks if river[b["row"]:b["row"] + b["h"], b["col"]:b["col"] + b["w"]].any()]
    (out / "blocks.json").write_text(json.dumps(rblocks))
    meta = {"tile": t, "corridor_km2": round(corr.sum() * 1e-4, 1), "river_km2": round(river.sum() * 1e-4, 2),
            "river_skeleton_km": round(float(slen[slen >= 300].sum()) / 1000, 1), "freq_scenes": len(sel),
            "failed_scenes": nf, "blocks": len(rblocks), "minutes": round((time.time() - t0) / 60, 1)}
    (out / "meta.json").write_text(json.dumps(meta))
    print(json.dumps(meta), flush=True)


for t in tiles:
    process_tile(t)
