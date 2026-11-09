"""Web-map tiles for the national 10 m river sediment map, packed into a few files.

Rivers: XYZ tiles (Web Mercator, 256 px) at zoom 7-14 wherever river pixels exist. Zoom 14 is ~9.5 m per pixel,
i.e. the native 10 m. Lower zooms average log10(SPM) over the source pixels (a 10/40/160 m pyramid) and widen
the lines slightly so narrow rivers stay visible. Hillshade tiles (zoom 6-10) give the relief underneath.
Tiles are packed per zoom into one binary file plus a JSON index, so the page fetches a handful of files.

    python scripts/cog/24_webtiles.py
Writes data/cog/r10m/web/: rivers_z{z}.bin, hill_z{z}.bin, index.json, cells.json
"""
import io
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from PIL import Image  # noqa: E402
from rasterio.transform import Affine  # noqa: E402
from rasterio.warp import Resampling, reproject, transform  # noqa: E402
from rasterio.windows import Window  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402

from sedrs.config import DATA_DIR, OUT_DIR  # noqa: E402

M = DATA_DIR / "cog" / "r10m" / "maps"
WEB = DATA_DIR / "cog" / "r10m" / "web"
WEB.mkdir(exist_ok=True)
X0, Y1 = 320000.0, 1100000.0
ORIGIN = 20037508.342789244
LO, HI = math.log10(5), math.log10(200)
cmap = plt.get_cmap("YlOrBr")
LUT = (cmap(np.linspace(0, 1, 256))[:, :3] * 255).astype(np.uint8)


def tile_bounds(z, x, y):
    size = 2 * ORIGIN / 2 ** z
    return -ORIGIN + x * size, ORIGIN - (y + 1) * size, -ORIGIN + (x + 1) * size, ORIGIN - y * size


def lonlat_to_tile(lon, lat, z):
    n = 2 ** z
    x = ((np.asarray(lon) + 180) / 360 * n).astype(int)
    lr = np.radians(lat)
    y = ((1 - np.log(np.tan(lr) + 1 / np.cos(lr)) / math.pi) / 2 * n).astype(int)
    return x, y


# ------------------------------------------------------------------ log10 SPM pyramid (10, 40, 160 m)
src = rasterio.open(M / "river_sediment_10m.tif")
H, W = src.height, src.width
lev = {}
for f in (4, 16):
    h, w = H // f, W // f
    s_sum = np.zeros((h, w), np.float32)
    s_n = np.zeros((h, w), np.float32)
    for r0 in range(0, h * f, 4096 // f * f):
        hh = min(4096 // f * f, h * f - r0)
        a = src.read(1, window=Window(0, r0, w * f, hh))
        la = np.log10(a)
        ok = np.isfinite(la)
        s_sum[r0 // f:(r0 + hh) // f] = np.where(ok, la, 0).reshape(hh // f, f, w, f).sum(axis=(1, 3))
        s_n[r0 // f:(r0 + hh) // f] = ok.reshape(hh // f, f, w, f).sum(axis=(1, 3))
    lev[f] = (np.where(s_n > 0, s_sum / np.maximum(s_n, 1), np.nan).astype(np.float32),
              Affine(10 * f, 0, X0, 0, -10 * f, Y1))
    print("pyramid level", f * 10, "m:", int((s_n > 0).sum()), "cells", flush=True)

# river tile set from the 160 m level (any river cell -> its tiles, with a one-tile margin at high zoom)
rr, cc = np.nonzero(np.isfinite(lev[16][0]))
xs, ys = X0 + (cc + 0.5) * 160, Y1 - (rr + 0.5) * 160
lon, lat = transform("EPSG:32644", "EPSG:4326", xs.tolist(), ys.tolist())
lon, lat = np.array(lon), np.array(lat)


def source_for(z):
    res = 2 * ORIGIN / 2 ** z / 256 * math.cos(math.radians(7.8))       # ground metres per pixel
    if res < 30:
        return None
    return lev[4] if res < 120 else lev[16]


def render(z, x, y):
    b = tile_bounds(z, x, y)
    dst_tr = Affine((b[2] - b[0]) / 256, 0, b[0], 0, -(b[3] - b[1]) / 256, b[3])
    out = np.full((256, 256), np.nan, np.float32)
    s = source_for(z)
    if s is None:                                                  # read the 10 m source window
        ux, uy = transform("EPSG:3857", "EPSG:32644", [b[0], b[2], b[0], b[2]], [b[1], b[1], b[3], b[3]])
        c0 = int((min(ux) - X0) / 10) - 4
        r0 = int((Y1 - max(uy)) / 10) - 4
        c1 = int((max(ux) - X0) / 10) + 4
        r1 = int((Y1 - min(uy)) / 10) + 4
        c0, r0 = max(c0, 0), max(r0, 0)
        c1, r1 = min(c1, W), min(r1, H)
        if c0 >= c1 or r0 >= r1:
            return None
        a = src.read(1, window=Window(c0, r0, c1 - c0, r1 - r0))
        if not np.isfinite(a).any():
            return None
        data, tr = np.log10(a), Affine(10, 0, X0 + c0 * 10, 0, -10, Y1 - r0 * 10)
        rs = Resampling.average if z <= 13 else Resampling.nearest
    else:
        data, tr = s
        rs = Resampling.average
    reproject(data, out, src_transform=tr, src_crs="EPSG:32644", dst_transform=dst_tr, dst_crs="EPSG:3857",
              resampling=rs, src_nodata=np.nan, dst_nodata=np.nan)
    ok = np.isfinite(out)
    if not ok.any():
        return None
    if z <= 11:                                                   # widen thin lines at small scales
        grow = ndi.grey_dilation(np.where(ok, out, -9), size=(2, 2) if z >= 10 else (3, 3))
        out = np.where(ok, out, np.where(grow > -9, grow, np.nan))
        ok = np.isfinite(out)
    idx = np.clip(((out - LO) / (HI - LO) * 255), 0, 255)
    idx = np.where(ok, idx, 0).astype(np.uint8)
    rgba = np.zeros((256, 256, 4), np.uint8)
    rgba[..., :3] = LUT[idx]
    rgba[..., 3] = np.where(ok, 255, 0)
    im = Image.fromarray(rgba, "RGBA").quantize(colors=64, method=Image.Quantize.FASTOCTREE)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


index = {"rivers": {}, "hill": {}}
for z in range(7, 15):
    tx, ty = lonlat_to_tile(lon, lat, z)
    tiles = set(zip(tx.tolist(), ty.tolist()))
    blob, idx_z = bytearray(), {}
    for x, y in sorted(tiles):
        png = render(z, x, y)
        if png is None:
            continue
        idx_z[f"{x}/{y}"] = [len(blob), len(png)]
        blob += png
    (WEB / f"rivers_z{z}.bin").write_bytes(bytes(blob))
    index["rivers"][str(z)] = idx_z
    print(f"z{z}: {len(idx_z)} river tiles, {len(blob) / 1e6:.1f} MB", flush=True)

# ------------------------------------------------------------------ hillshade tiles (zoom 6-10)
hs = np.load(OUT_DIR / "cog" / "hillshade.npz")
e = hs["extent"]
hsv = hs["hillshade"].astype(np.float32)
hs_tr = Affine((e[1] - e[0]) / hsv.shape[1], 0, e[0], 0, -(e[3] - e[2]) / hsv.shape[0], e[3])
land = hs["dem"].astype(np.float32) > 0
hsv = np.where(land, hsv, np.nan)
for z in range(6, 11):
    x0t, y0t = lonlat_to_tile(np.array([79.5]), np.array([9.9]), z)
    x1t, y1t = lonlat_to_tile(np.array([82.0]), np.array([5.85]), z)
    blob, idx_z = bytearray(), {}
    for x in range(int(x0t[0]), int(x1t[0]) + 1):
        for y in range(int(y0t[0]), int(y1t[0]) + 1):
            b = tile_bounds(z, x, y)
            dst_tr = Affine((b[2] - b[0]) / 256, 0, b[0], 0, -(b[3] - b[1]) / 256, b[3])
            out = np.full((256, 256), np.nan, np.float32)
            reproject(hsv, out, src_transform=hs_tr, src_crs="EPSG:4326", dst_transform=dst_tr, dst_crs="EPSG:3857",
                      resampling=Resampling.bilinear, src_nodata=np.nan, dst_nodata=np.nan)
            ok = np.isfinite(out)
            if not ok.any():
                continue
            # grey shading as alpha over the page's own land colour: shadows dark, lit slopes light
            v = np.clip(np.nan_to_num(out, nan=0.75), 0, 1)
            shade = np.clip((0.78 - v) * 1.6, 0, 1)                 # 0 on flat ground, 1 in deep shadow
            light = np.clip((v - 0.85) * 2.0, 0, 1)
            rgba = np.zeros((256, 256, 4), np.uint8)
            rgba[..., :3] = np.where(shade[..., None] > light[..., None], 20, 255)
            rgba[..., 3] = np.where(ok, (np.maximum(shade * 150, light * 90)).astype(np.uint8), 0)
            buf = io.BytesIO()
            Image.fromarray(rgba, "RGBA").quantize(colors=32, method=Image.Quantize.FASTOCTREE).save(
                buf, "PNG", optimize=True)
            png = buf.getvalue()
            idx_z[f"{x}/{y}"] = [len(blob), len(png)]
            blob += png
    (WEB / f"hill_z{z}.bin").write_bytes(bytes(blob))
    index["hill"][str(z)] = idx_z
    print(f"hill z{z}: {len(idx_z)} tiles, {len(blob) / 1e6:.1f} MB", flush=True)
(WEB / "index.json").write_text(json.dumps(index, separators=(",", ":")))

# ------------------------------------------------------------------ 1 km cells for the click-through layer
cells = pd.read_csv(M / "river_cells_1km.csv")
cols = ["lon", "lat", "spm", "spm_NEM", "spm_FIM", "spm_SWM", "spm_SIM", "ndti", "px", "peak"]
rows = cells[cols].replace({np.nan: None}).values.tolist()
(WEB / "cells.json").write_text(json.dumps({"cols": cols, "rows": rows}, separators=(",", ":")))
print("cells:", len(rows))
