"""Pass 1: national 20 m water-frequency map from the clearest Sentinel-2 scenes.

For each MGRS tile, the N least-cloudy scenes (spread over years and seasons)
are read in full (B03 overview, B11, SCL). Water = MNDWI > 0 and NDVI < 0 and
NIR < 0.12 on clear pixels. Writes data/cog/water_count.tif and clear_count.tif.
"""
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402

from sedrs import cog, s2grid  # noqa: E402
from sedrs.config import DATA_DIR  # noqa: E402

N_PER_TILE = int(sys.argv[1]) if len(sys.argv) > 1 else 10
cog.set_gdal_env()
out = DATA_DIR / "cog"
sc = pd.read_csv(out / "scenes.csv")
sc = sc[(sc["cloud"] < 20) & (sc["nodata_pct"] < 60) & (sc["date"] >= "2022-01-01")]
sc["q"] = pd.to_datetime(sc["date"]).dt.month % 12 // 3          # spread over seasons
picks = (sc.sort_values("cloud").groupby(["tile", "q"]).head(max(1, N_PER_TILE // 4))
           .groupby("tile").head(N_PER_TILE))
print(f"{len(picks)} scenes over {picks['tile'].nunique()} tiles")

water = np.zeros((s2grid.H, s2grid.W), np.uint8)
clear = np.zeros((s2grid.H, s2grid.W), np.uint8)
lock = threading.Lock()


def do(row):
    b = s2grid.read_bands(row.prefix, None, ("B03", "B04", "B8A", "B11", "SCL"))
    with s2grid._open(row.prefix, "SCL") as d:
        r0, c0 = s2grid.offset(d.transform)
    g = b["B03"].astype(np.float32) * 1e-4 + row.offset
    s = b["B11"].astype(np.float32) * 1e-4 + row.offset
    r = b["B04"].astype(np.float32) * 1e-4 + row.offset
    n = b["B8A"].astype(np.float32) * 1e-4 + row.offset
    ok = ~np.isin(b["SCL"], cog.SCL_BAD) & (b["B03"] > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        # strict open-water rule: MNDWI > 0 (Xu 2006) AND NDVI < 0 AND low NIR;
        # terrain shadow, dark forest and wet soil fail at least one test
        wat = ok & ((g - s) / (g + s) > 0) & ((n - r) / (n + r) < 0) & (n < 0.12)
    del r, n
    h, w = ok.shape
    # clip to national grid
    rr0, cc0 = max(r0, 0), max(c0, 0)
    rr1, cc1 = min(r0 + h, s2grid.H), min(c0 + w, s2grid.W)
    if rr1 <= rr0 or cc1 <= cc0:
        return row.id
    sl_t = (slice(rr0 - r0, rr1 - r0), slice(cc0 - c0, cc1 - c0))
    with lock:
        clear[rr0:rr1, cc0:cc1] += ok[sl_t].astype(np.uint8)
        water[rr0:rr1, cc0:cc1] += wat[sl_t].astype(np.uint8)
    return row.id


t0 = time.time()
with ThreadPoolExecutor(4) as ex:
    futs = [ex.submit(do, r) for r in picks.itertuples()]
    for i, f in enumerate(as_completed(futs), 1):
        try:
            f.result()
        except Exception as e:  # keep going; one bad scene must not kill the run
            print("failed:", e)
        if i % 10 == 0:
            print(f"{i}/{len(futs)}  {time.time() - t0:.0f}s", flush=True)

prof = dict(driver="GTiff", width=s2grid.W, height=s2grid.H, count=1, dtype="uint8",
            crs=s2grid.CRS, transform=s2grid.transform(), compress="deflate", tiled=True)
for name, arr in (("water_count", water), ("clear_count", clear)):
    with rasterio.open(out / f"{name}.tif", "w", **prof) as d:
        d.write(arr, 1)
print(f"done in {time.time() - t0:.0f}s")
