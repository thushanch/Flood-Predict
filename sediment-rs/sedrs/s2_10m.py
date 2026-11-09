"""10 m Sentinel-2 grid over the Knuckles downstream project area, and block readers.

The grid is UTM 44N (EPSG:32644) at 10 m, snapped to multiples of 20 m so every Sentinel-2 tile in zone 44N
(corners on multiples of 20 m) maps onto it by an integer offset. Each project pixel is "owned" by one tile
(the covering tile whose centre is nearest), so overlapping tiles are read only once per date. Reads go block by
block (the COGs' internal 1024 x 1024 tiles), and only blocks that hold owned project pixels are read.

10 m bands: B03 (green), B04 (red), B08 (NIR). SCL is 20 m and is repeated 2 x 2 onto the 10 m grid.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import cog

CRS = "EPSG:32644"
RES = 10.0
TILES = ("44NLP", "44PLQ", "44NMN", "44NMP", "44PMQ")
BLOCK = 1024
TILE_PX = 10980


@dataclass
class Grid:
    x0: float
    y1: float
    width: int
    height: int

    @property
    def transform(self):
        from rasterio.transform import from_origin
        return from_origin(self.x0, self.y1, RES, RES)


def make_grid(geoms_utm, pad_m=1000.0) -> Grid:
    x0, y0, x1, y1 = geoms_utm.total_bounds
    x0 = np.floor((x0 - pad_m) / 20) * 20
    y0 = np.floor((y0 - pad_m) / 20) * 20
    x1 = np.ceil((x1 + pad_m) / 20) * 20
    y1 = np.ceil((y1 + pad_m) / 20) * 20
    return Grid(float(x0), float(y1), int((x1 - x0) / RES), int((y1 - y0) / RES))


def blocks_for(grid: Grid, tile_ul: dict, owner: np.ndarray, inarea: np.ndarray):
    """Blocks to read per tile. tile_ul: tile -> (x, y) of its upper-left corner (10 m grid).

    Returns a list of dicts: tile, tile window (full block: col, row, w, h) and the clipped part on the grid
    (gr0, gc0, h, w and the matching offsets inside the block, br0, bc0).
    """
    out = []
    for k, t in enumerate(TILES):
        tx, ty = tile_ul[t]
        roff = int(round((grid.y1 - ty) / RES))         # grid row of tile row 0
        coff = int(round((tx - grid.x0) / RES))
        for bi in range(0, TILE_PX, BLOCK):
            for bj in range(0, TILE_PX, BLOCK):
                bh, bw = min(BLOCK, TILE_PX - bi), min(BLOCK, TILE_PX - bj)
                r0, c0 = roff + bi, coff + bj
                gr0, gc0 = max(r0, 0), max(c0, 0)
                gr1, gc1 = min(r0 + bh, grid.height), min(c0 + bw, grid.width)
                if gr0 >= gr1 or gc0 >= gc1:
                    continue
                own = (owner[gr0:gr1, gc0:gc1] == k) & inarea[gr0:gr1, gc0:gc1]
                if not own.any():
                    continue
                out.append({"tile": t, "k": k, "col": bj, "row": bi, "w": bw, "h": bh,
                            "gr0": gr0, "gc0": gc0, "gh": gr1 - gr0, "gw": gc1 - gc0,
                            "br0": gr0 - r0, "bc0": gc0 - c0})
    return out


def ownership(grid: Grid, tile_ul: dict, step: int = 10) -> np.ndarray:
    """Tile index owning each grid pixel (nearest covering tile centre); 255 where no tile covers it."""
    rows = np.arange(0, grid.height, step)
    cols = np.arange(0, grid.width, step)
    yy = grid.y1 - (rows[:, None] + 0.5) * RES
    xx = grid.x0 + (cols[None, :] + 0.5) * RES
    best = np.full((len(rows), len(cols)), np.inf)
    own = np.full((len(rows), len(cols)), 255, np.uint8)
    half = TILE_PX * RES / 2
    for k, t in enumerate(TILES):
        tx, ty = tile_ul[t]
        cx, cy = tx + half, ty - half
        inside = (xx >= tx) & (xx < tx + 2 * half) & (yy <= ty) & (yy > ty - 2 * half)
        d = np.hypot(xx - cx, yy - cy)
        upd = inside & (d < best)
        best[upd] = d[upd]
        own[upd] = k
    own = np.repeat(np.repeat(own, step, 0), step, 1)[:grid.height, :grid.width]
    return own


def tile_ul_from_scenes(scenes) -> dict:
    """Upper-left corner of each tile, read from one scene's B04 header."""
    import rasterio
    out = {}
    for t in TILES:
        pre = scenes[scenes["tile"] == t]["prefix"].iloc[0]
        with rasterio.open(cog.band_url(pre, "B04")) as d:
            assert abs(d.transform.a - RES) < 1e-6
            out[t] = (d.transform.c, d.transform.f)
    return out


def open_bands(prefix, bands=("B03", "B04", "B08", "SCL")):
    import rasterio
    return {b: rasterio.open(cog.band_url(prefix, b)) for b in bands}


def read_block(ds: dict, blk: dict, bands=("B03", "B04", "B08")):
    """Read one block; returns arrays cropped to the grid part (gh x gw). Reflectance as float32 (NaN = no data).

    SCL (20 m) is read for the full block and repeated 2 x 2 before cropping.
    """
    from rasterio.windows import Window
    sl = (slice(blk["br0"], blk["br0"] + blk["gh"]), slice(blk["bc0"], blk["bc0"] + blk["gw"]))
    out = {}
    if "SCL" in ds:
        s = ds["SCL"].read(1, window=Window(blk["col"] // 2, blk["row"] // 2, (blk["w"] + 1) // 2,
                                            (blk["h"] + 1) // 2))
        s = np.repeat(np.repeat(s, 2, 0), 2, 1)
        out["SCL"] = s[sl]
    for b in bands:
        a = ds[b].read(1, window=Window(blk["col"], blk["row"], blk["w"], blk["h"]))[sl]
        r = a.astype(np.float32) * 1e-4
        r[a == 0] = np.nan
        out[b] = r
    return out


def save_meta(path: Path, grid: Grid, tile_ul: dict):
    path.write_text(json.dumps({"x0": grid.x0, "y1": grid.y1, "width": grid.width, "height": grid.height,
                                "tile_ul": tile_ul, "crs": CRS, "res": RES}, indent=1))


def load_meta(path: Path):
    m = json.loads(path.read_text())
    return Grid(m["x0"], m["y1"], m["width"], m["height"]), {k: tuple(v) for k, v in m["tile_ul"].items()}
