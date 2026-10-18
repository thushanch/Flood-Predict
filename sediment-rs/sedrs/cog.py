"""No-account backend: read public Cloud-Optimized GeoTIFFs directly over HTTP.

* Sentinel-2 L2A (Sen2Cor) COGs, AWS Open Data bucket `sentinel-cogs`
  (Element 84 Earth Search layout). Reflectance = DN * 1e-4. Items from
  processing baseline >= 04.00 carry `raster:bands` offset -0.1 together with
  `earthsearch:boa_offset_applied: true`: the offset is ALREADY applied to the
  pixel values. Verified on tile 44NLN: land DN levels match between 2021
  (baseline 02.14, no offset) and 2024-25 (baseline 05.1), and applying the
  metadata offset again drives water SWIR to about -0.08.
* JRC Global Surface Water v1.4 occurrence tiles (Pekel et al. 2016) on GCS.

This mirrors `gee.py` for users without Earth Engine. Differences: the SCL
scene classification replaces Cloud Score+ for cloud masking, and the river
corridor is derived from JRC occurrence (see `river_mask`).
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np

S2_BUCKET = "https://sentinel-cogs.s3.us-west-2.amazonaws.com"
S2_PREFIX = "sentinel-s2-l2a-cogs"
JRC_URL = ("https://storage.googleapis.com/global-surface-water/downloads2021/"
           "occurrence/occurrence_{tile}v1_4_2021.tif")

# Sentinel-2 MGRS tiles (UTM 44N) intersecting Sri Lanka
SL_TILES = ["44NLM", "44NLN", "44NLP", "44PLQ", "44PLR", "44NML", "44NMM", "44NMN", "44NMP",
            "44PMQ", "44PMR", "44NNL", "44NNM", "44NNN", "44NNP", "44PNQ", "44PNR"]

# SCL classes treated as invalid: no data, saturated, cloud shadow, cloud (med/high), cirrus, snow
SCL_BAD = (0, 1, 3, 8, 9, 10, 11)

GDAL_ENV = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
    "GDAL_HTTP_MULTIRANGE": "YES",
    "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
    "GDAL_HTTP_MAX_RETRY": "5",
    "GDAL_HTTP_RETRY_DELAY": "2",
    "VSI_CACHE": "TRUE",
}


def set_gdal_env():
    for k, v in GDAL_ENV.items():
        os.environ.setdefault(k, v)
    # GDAL's curl needs the proxy CA bundle in this environment
    for ca in ("/root/.ccr/ca-bundle.crt",):
        if os.path.exists(ca):
            os.environ.setdefault("CURL_CA_BUNDLE", ca)


def _get(url, timeout=60, retries=6):
    import time
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return r.read()
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(2 ** i)


# --------------------------------------------------------------------------
# JRC occurrence + river corridor
# --------------------------------------------------------------------------
def read_jrc(bbox, tiles=("70E_10N", "80E_10N")):
    """Mosaic JRC occurrence over bbox (lon0, lat0, lon1, lat1). Returns (array, transform)."""
    import rasterio
    from rasterio.transform import from_origin
    from rasterio.windows import from_bounds

    set_gdal_env()
    res = 0.00025
    lon0, lat0, lon1, lat1 = bbox
    width, height = round((lon1 - lon0) / res), round((lat1 - lat0) / res)
    out = np.zeros((height, width), np.uint8)
    tr = from_origin(lon0, lat1, res, res)
    for t in tiles:
        with rasterio.open("/vsicurl/" + JRC_URL.format(tile=t)) as d:
            b = d.bounds
            ix0, ix1 = max(lon0, b.left), min(lon1, b.right)
            if ix0 >= ix1:
                continue
            win = from_bounds(ix0, lat0, ix1, lat1, d.transform).round_offsets().round_lengths()
            arr = d.read(1, window=win)
            c0 = round((ix0 - lon0) / res)
            out[:, c0:c0 + arr.shape[1]] = arr[:height]
    return out, tr


def river_mask(occ, occ_min=25, wide_radius_px=5, join_radius_px=3, min_len_km=1.5,
               min_elong=4.0, px_km=0.0277, wide_halo_px=2):
    """Separate river channels from tanks, reservoirs, lagoons and sea.

    1. water = occurrence >= occ_min (narrow channels are mixed pixels in the
       30 m JRC data, so the threshold is lower than for a stable-water mask)
    2. remove 'wide' water: anything surviving a morphological opening with a
       disk of `wide_radius_px` (~140 m, i.e. wider than ~280 m) plus a 2-px halo
       -> drops sea, lagoons, reservoirs and large tanks
    3. bridge small gaps (bridges, rapids, cloud-affected JRC pixels) by
       dilating `join_radius_px` before labelling
    4. keep joined components that are long (skeleton >= min_len_km) and
       elongated (skeleton length / sqrt(area) >= min_elong); small compact
       tanks fail the elongation test
    Returns (mask on the original, undilated water pixels; stats dict).
    """
    from scipy import ndimage as ndi
    from skimage.morphology import disk, skeletonize

    water = occ >= occ_min
    wide = ndi.binary_opening(water, structure=disk(wide_radius_px))
    wide = ndi.binary_dilation(wide, structure=disk(wide_halo_px))
    cand = water & ~wide
    joined = ndi.binary_dilation(cand, structure=disk(join_radius_px)) & ~wide
    lab, n = ndi.label(joined, structure=np.ones((3, 3)))
    area = np.bincount(lab.ravel(), minlength=n + 1)
    skel = skeletonize(joined)
    slen = np.bincount(lab[skel], minlength=n + 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        elong = slen / np.sqrt(area)
    keep = (slen * px_km >= min_len_km) & (elong >= min_elong)
    keep[0] = False
    mask = keep[lab] & cand
    stats = {"water_px": int(water.sum()), "candidate_components": int(n),
             "kept_components": int(keep.sum()), "river_px": int(mask.sum()),
             "river_skeleton_km": float(slen[keep].sum() * px_km)}
    return mask, stats, skel & keep[lab]


# --------------------------------------------------------------------------
# Sentinel-2 scene listing (S3 ListObjectsV2, no STAC API needed)
# --------------------------------------------------------------------------
def _list_prefixes(prefix):
    out, token = [], None
    while True:
        url = f"{S2_BUCKET}/?list-type=2&prefix={prefix}&delimiter=/"
        if token:
            url += "&continuation-token=" + urllib.request.quote(token)
        xml = _get(url).decode()
        out += re.findall(r"<CommonPrefixes><Prefix>([^<]*)</Prefix></CommonPrefixes>", xml)
        m = re.search(r"<NextContinuationToken>([^<]*)</NextContinuationToken>", xml)
        if not m:
            return out
        token = m.group(1)


def tile_path(tile):
    return f"{tile[:2]}/{tile[2]}/{tile[3:]}"


def list_items(tile, year, month):
    pre = f"{S2_PREFIX}/{tile_path(tile)}/{year}/{month}/"
    return [p for p in _list_prefixes(pre) if p.endswith("_L2A/")]


def item_meta(prefix):
    name = prefix.rstrip("/").split("/")[-1]
    d = json.loads(_get(f"{S2_BUCKET}/{prefix}{name}.json"))
    p = d["properties"]
    off_meta = (d["assets"].get("red", {}).get("raster:bands") or [{}])[0].get("offset", 0.0)
    applied = bool(p.get("earthsearch:boa_offset_applied", False))
    off = 0.0 if applied else off_meta
    return {"id": name, "prefix": prefix, "tile": name.split("_")[1], "date": p["datetime"][:10],
            "platform": p.get("platform"), "cloud": p.get("eo:cloud_cover"),
            "nodata_pct": p.get("s2:nodata_pixel_percentage"),
            "baseline": p.get("s2:processing_baseline"), "offset": off, "offset_meta": off_meta,
            "boa_offset_applied": applied}


def list_scenes(tiles, years, workers=8):
    jobs = [(t, y, m) for t in tiles for y in years for m in range(1, 13)]
    with ThreadPoolExecutor(workers) as ex:
        prefixes = [p for ps in ex.map(lambda a: list_items(*a), jobs) for p in ps]
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(item_meta, prefixes))


def band_url(prefix, band):
    return f"/vsicurl/{S2_BUCKET}/{prefix}{band}.tif"
