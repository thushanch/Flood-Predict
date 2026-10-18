"""National 20 m UTM-44N grid and Sentinel-2 block readers.

Sentinel-2 MGRS tiles in zone 44N have corners on multiples of 20 m, so every
tile maps onto the national grid by an integer offset with no resampling.
"""
from __future__ import annotations

import numpy as np

from . import algorithms as alg
from . import cog

CRS = "EPSG:32644"
RES = 20.0
# Sri Lanka in UTM 44N, snapped outward to 20 m
X0, Y1 = 320000.0, 1100000.0          # upper-left corner  (~79.37 E, 9.95 N)
X1, Y0 = 620000.0, 640000.0           # lower-right corner (~82.09 E, 5.79 N)
W, H = int((X1 - X0) / RES), int((Y1 - Y0) / RES)


def transform():
    from rasterio.transform import from_origin
    return from_origin(X0, Y1, RES, RES)


def offset(tile_transform):
    """(row, col) of a tile's upper-left pixel in the national grid."""
    col = round((tile_transform.c - X0) / RES)
    row = round((Y1 - tile_transform.f) / RES)
    return row, col


def _open(prefix, band):
    import rasterio
    url = cog.band_url(prefix, band)
    if band in ("B03", "B04", "B02", "B08"):          # 10 m bands -> first overview = 20 m
        return rasterio.open(url, overview_level=0)
    return rasterio.open(url)


BANDS = ("B03", "B04", "B8A", "B11", "SCL")


def open_scene(prefix, bands=BANDS):
    return {b: _open(prefix, b) for b in bands}


def read_window(ds: dict, window):
    return {b: d.read(1, window=window) for b, d in ds.items()}


def read_bands(prefix, window, bands=BANDS):
    ds = open_scene(prefix, bands)
    try:
        return read_window(ds, window)
    finally:
        for d in ds.values():
            d.close()


def tile_geo(prefix):
    with _open(prefix, "SCL") as d:
        return d.transform, d.width, d.height


def reflectance(dn, offset_):
    r = dn.astype(np.float32) * 1e-4 + offset_
    r[dn == 0] = np.nan
    return r


def products(b, offset_, swir_max=alg.SWIR_WATER_THRESHOLD):
    """Per-pixel water products and validity for one block (all 20 m arrays)."""
    g, r = reflectance(b["B03"], offset_), reflectance(b["B04"], offset_)
    n, s = reflectance(b["B8A"], offset_), reflectance(b["B11"], offset_)
    scl = b["SCL"]
    with np.errstate(divide="ignore", invalid="ignore"):
        mndwi = (g - s) / (g + s)
        ndvi = (n - r) / (n + r)
    clear = ~np.isin(scl, cog.SCL_BAD)
    valid = (clear & (mndwi > 0.1) & (s < swir_max) & (r > 0) & (g > 0)
             & (ndvi < 0.1) & np.isfinite(n))
    spm_red, spm_nir, spm = alg.nechad_spm(r, n, "S2")
    return {
        "valid": valid, "green": g, "red": r, "nir": n,
        "ndti": alg.ndti(r, g), "T_dog": alg.dogliotti_turbidity(r, n),
        "SPM_red": spm_red, "SPM_nir": spm_nir, "SPM_blend": spm,
        "clear": clear, "water": clear & (mndwi > 0),
    }
