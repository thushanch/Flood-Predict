"""Daily satellite rainfall per project sub-watershed from PERSIANN-CDR (0.25 deg, NOAA CDR on AWS Open Data).

PERSIANN-CDR (Ashouri et al. 2015) is infrared-based and bias-adjusted to GPCP monthly totals; it stands in
for the project's gauge rainfall until that is shared. Each daily global file is read in memory, cut to the
project window, and averaged over each sub-watershed with area weights.

    python scripts/knuckles/42_rain_persiann.py 2017 2025
Writes data/project_layers/rain_persiann_subws.csv (date x SubWS_ID, mm/day)
"""
import io
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import geopandas as gpd  # noqa: E402
import h5py  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from rasterio.features import rasterize  # noqa: E402
from rasterio.transform import from_origin  # noqa: E402

from sedrs.config import DATA_DIR  # noqa: E402

BUCKET = "https://noaa-cdr-precip-persiann-pds.s3.amazonaws.com"
y0, y1 = (int(a) for a in sys.argv[1:3]) if len(sys.argv) > 2 else (2017, 2025)
P = DATA_DIR / "project_layers"
sw = gpd.read_file(P / "project_layers_clean.gpkg", layer="sub_watersheds").to_crs(4326).sort_values("SubWS_ID")

# 0.25 deg cells over the project window; area weights from a 0.0025 deg rasterization
LON0, LAT1, NC, NR = 79.75, 8.75, 6, 7                         # cells 79.75-81.25 E, 7.0-8.75 N
FINE = 100
ftr = from_origin(LON0, LAT1, 0.25 / FINE, 0.25 / FINE)
lab = rasterize([(g, i + 1) for i, g in enumerate(sw.geometry)], out_shape=(NR * FINE, NC * FINE),
                transform=ftr, dtype="int16")
W = np.zeros((len(sw), NR, NC))
for i in range(len(sw)):
    m = (lab == i + 1).reshape(NR, FINE, NC, FINE).sum(axis=(1, 3))
    W[i] = m / m.sum()


def keys(year):
    out, token = [], None
    while True:
        url = f"{BUCKET}/?list-type=2&prefix=data/{year}/&max-keys=1000"
        if token:
            url += "&continuation-token=" + urllib.parse.quote(token)
        txt = urllib.request.urlopen(url, timeout=60).read().decode()
        out += re.findall(r"<Key>([^<]+\.nc)</Key>", txt)
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", txt)
        if not m:
            return out
        token = m.group(1)


def one(key):
    for i in range(5):
        try:
            raw = urllib.request.urlopen(f"{BUCKET}/{key}", timeout=120).read()
            break
        except Exception:
            if i == 4:
                raise
            time.sleep(2 ** i)
    with h5py.File(io.BytesIO(raw), "r") as f:
        lat, lon = f["lat"][:], f["lon"][:]
        pr = f["precipitation"][0]                           # (lon, lat)
    ilon = np.searchsorted(lon, LON0 + 0.125 + 0.25 * np.arange(NC) - 1e-3)
    ilat = [int(np.argmin(np.abs(lat - (LAT1 - 0.125 - 0.25 * k)))) for k in range(NR)]
    cell = pr[np.ix_(ilon, ilat)].T.astype(float)            # (lat rows N->S, lon cols)
    cell[cell < 0] = np.nan
    vals = [np.nansum(W[i] * cell) / np.nansum(W[i] * np.isfinite(cell)) for i in range(len(sw))]
    date = re.search(r"_(\d{8})_c", key).group(1)
    return pd.Timestamp(date), vals


all_keys = [k for y in range(y0, y1 + 1) for k in keys(y)]
print(len(all_keys), "daily files")
t0 = time.time()
with ThreadPoolExecutor(16) as ex:
    res = list(ex.map(one, all_keys))
df = pd.DataFrame([v for _, v in res], index=[d for d, _ in res], columns=list(sw["SubWS_ID"])).sort_index()
df.index.name = "date"
df.round(2).to_csv(P / "rain_persiann_subws.csv")
print(f"done in {(time.time() - t0) / 60:.1f} min; annual mean (mm):")
print(df.groupby(df.index.year).sum().mean(axis=1).round(0).to_string())
