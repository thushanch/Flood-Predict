"""Derive the Sri Lankan river-channel mask from JRC Global Surface Water occurrence.

Writes data/cog/river_mask.tif (EPSG:4326, 0.00025 deg) and prints network stats.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np  # noqa: E402
import rasterio  # noqa: E402

from sedrs import cog  # noqa: E402
from sedrs.config import DATA_DIR, load_settings  # noqa: E402

cfg = load_settings()
bbox = cfg["reaches"]["bbox"]
out = DATA_DIR / "cog"
out.mkdir(parents=True, exist_ok=True)

t0 = time.time()
occ, tr = cog.read_jrc(bbox)
print(f"JRC read {occ.shape} in {time.time() - t0:.0f}s; values: {np.unique(occ)[:5]} ... max {occ.max()}")
occ = np.where(occ > 100, 0, occ)          # 255 = no data (ocean / outside coverage)
mask, stats, skel = cog.river_mask(occ)
print(json.dumps(stats, indent=1), f"{time.time() - t0:.0f}s")

prof = dict(driver="GTiff", width=mask.shape[1], height=mask.shape[0], count=1, dtype="uint8",
            crs="EPSG:4326", transform=tr, compress="deflate", tiled=True, nbits=1)
with rasterio.open(out / "river_mask.tif", "w", **prof) as d:
    d.write(mask.astype("uint8"), 1)
with rasterio.open(out / "jrc_occurrence.tif", "w", **{**prof, "nbits": 8}) as d:
    d.write(occ, 1)
with rasterio.open(out / "river_skeleton.tif", "w", **prof) as d:
    d.write(skel.astype("uint8"), 1)
(out / "river_mask_stats.json").write_text(json.dumps(stats, indent=1))
print("wrote", out / "river_mask.tif")
