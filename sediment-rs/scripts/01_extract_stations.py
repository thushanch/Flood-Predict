"""Per-image station extractions for Sentinel-2 and Landsat-8/9.

Usage:
    python scripts/01_extract_stations.py              # Drive exports (robust, default)
    python scripts/01_extract_stations.py --download   # direct CSV download (small runs)
    python scripts/01_extract_stations.py --sensors S2 --years 2023 2024

Exports go to Google Drive/<drive_folder>; put the CSVs in data/stations/.
Also writes data/potential_pixels.json (static water pixels per station).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ee  # noqa: E402

from sedrs import gee  # noqa: E402
from sedrs.config import DATA_DIR, load_settings  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--sensors", nargs="+")
ap.add_argument("--years", nargs="+", type=int)
ap.add_argument("--download", action="store_true")
args = ap.parse_args()

cfg = load_settings()
if not cfg["_stations_snapped"]:
    sys.exit("Run scripts/00_snap_stations.py first (stations are approximate).")
gee.init(cfg["gee_project"])

stations = gee.stations_fc(cfg["stations"], cfg["station_buffer_m"])
region = stations.geometry().bounds()
m = cfg["masking"]
out_dir = DATA_DIR / "stations"
out_dir.mkdir(parents=True, exist_ok=True)

pot = {"S2": gee.potential_pixels(stations, cfg, 20), "L": gee.potential_pixels(stations, cfg, 30)}
(DATA_DIR / "potential_pixels.json").write_text(json.dumps(pot, indent=1))

y0, y1 = int(cfg["period"]["start"][:4]), int(cfg["period"]["end"][:4])
years = args.years or range(y0, y1 + 1)
for sensor in args.sensors or cfg["sensors"]:
    for y in years:
        if sensor == "S2" and y < 2017 or sensor == "L9" and y < 2021:
            continue
        start = max(f"{y}-01-01", cfg["period"]["start"])
        end = min(f"{y + 1}-01-01", cfg["period"]["end"])
        col = gee.collection(sensor, region, start, end, cfg)
        fc = gee.reduce_images(col, stations, sensor, m["min_pixels"])
        name = f"stations_{sensor}_{y}"
        if args.download:
            path = out_dir / f"{name}.csv"
            try:
                gee.download_table(fc, str(path), gee.STATION_COLUMNS)
                print("downloaded", path)
            except ee.EEException as e:
                print(f"{name}: {e} -- rerun without --download")
        else:
            t = gee.export_table(fc, name, cfg["drive_folder"], gee.STATION_COLUMNS)
            print("started export", name, t.id)
