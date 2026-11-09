"""National stream network from the Copernicus GLO-90 DEM, to bound the 10 m river mapping.

The 20 m Sentinel-2 river mask (rivers_20m.tif) only holds channels wider than about 60 m. To look for
narrower rivers at 10 m, the search is limited to a corridor around DEM-derived streams. The satellite
channels are burned 15 m into the DEM first, so the flow lines follow the real rivers on the floodplains.

    python scripts/cog/20_streams_dem.py
Writes data/cog/r10m/dem90.tif, acc90.tif (upstream area, km2) and streams90.tif (1 where >= 25 km2)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np  # noqa: E402
import rasterio  # noqa: E402
from rasterio.merge import merge  # noqa: E402
from rasterio.warp import Resampling, reproject  # noqa: E402

from sedrs import cog  # noqa: E402
from sedrs.config import DATA_DIR  # noqa: E402

if not hasattr(np, "in1d"):          # pysheds still calls np.in1d, removed in numpy 2.x
    np.in1d = lambda a, b, **kw: np.isin(np.ravel(a), b, **kw)
from pysheds.grid import Grid  # noqa: E402

cog.set_gdal_env()
OUT = DATA_DIR / "cog" / "r10m"
OUT.mkdir(parents=True, exist_ok=True)
MIN_KM2 = 25.0
BURN_M = 15.0

dem_path = OUT / "dem90.tif"
if not dem_path.exists():
    srcs = []
    for la in range(5, 10):
        for lo in range(79, 82):
            n = f"Copernicus_DSM_COG_30_N{la:02d}_00_E{lo:03d}_00_DEM"
            try:
                srcs.append(rasterio.open(f"/vsicurl/https://copernicus-dem-90m.s3.amazonaws.com/{n}/{n}.tif"))
            except Exception:
                pass
    arr, tr = merge(srcs, bounds=(79.4, 5.85, 82.0, 9.9), nodata=-9999)
    with rasterio.open(dem_path, "w", driver="GTiff", width=arr.shape[2], height=arr.shape[1], count=1,
                       dtype="float32", crs="EPSG:4326", transform=tr, nodata=-9999, compress="deflate") as d:
        d.write(arr[0].astype("float32"), 1)
with rasterio.open(dem_path) as d:
    dem, prof = d.read(1), d.profile

# burn the 20 m satellite river channels (and any S2 water seen in >= 50 % of views) into the DEM
burn = np.zeros(dem.shape, np.uint8)
for f in ("rivers_20m.tif",):
    with rasterio.open(DATA_DIR / "cog" / f) as d:
        tmp = np.zeros(dem.shape, np.uint8)
        reproject((d.read(1) > 0).astype(np.uint8), tmp, src_transform=d.transform, src_crs=d.crs,
                  dst_transform=prof["transform"], dst_crs=prof["crs"], resampling=Resampling.max)
        burn |= tmp
land = dem > -100
sea_level = (dem <= 0) | ~land
demb = np.where(burn > 0, dem - BURN_M, dem)
demb = np.where(land, demb, -9999).astype("float32")
bp = OUT / "dem90_burned.tif"
with rasterio.open(bp, "w", **prof) as d:
    d.write(demb, 1)

grid = Grid.from_raster(str(bp))
dm = grid.read_raster(str(bp))
inflated = grid.resolve_flats(grid.fill_depressions(grid.fill_pits(dm)))
fdir = grid.flowdir(inflated)
acc = np.asarray(grid.accumulation(fdir), dtype=np.float64)
lat = prof["transform"].f + (np.arange(dem.shape[0]) + 0.5) * prof["transform"].e
cell_km2 = (abs(prof["transform"].a) * 111.32 * np.cos(np.radians(lat)))[:, None] * abs(prof["transform"].e) * 110.57
area = (acc * cell_km2).astype("float32")
area[~land] = 0
p2 = prof.copy()
p2.update(nodata=None)
with rasterio.open(OUT / "acc90.tif", "w", **p2) as d:
    d.write(area, 1)
streams = ((area >= MIN_KM2) & land & ~sea_level).astype("uint8")
p2.update(dtype="uint8")
with rasterio.open(OUT / "streams90.tif", "w", **p2) as d:
    d.write(streams, 1)
km = streams.sum() * 0.09
print(f"streams >= {MIN_KM2:.0f} km2: {int(streams.sum()):,} cells (~{km:,.0f} km of channel); "
      f"burned {int(burn.sum()):,} cells; DEM {dem.shape}")
