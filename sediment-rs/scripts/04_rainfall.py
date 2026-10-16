"""Daily catchment-mean rainfall (CHIRPS) above each station.

Catchment = the HydroBASINS level-8 basin containing the station plus every
basin upstream of it (NEXT_DOWN topology). This slightly over-estimates the
true catchment because the whole containing basin is included.
Put the exported CSV in data/rainfall/.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sedrs import gee  # noqa: E402
from sedrs.config import load_settings  # noqa: E402

cfg = load_settings()
if not cfg["_stations_snapped"]:
    sys.exit("Run scripts/00_snap_stations.py first.")
gee.init(cfg["gee_project"])

catch = gee.catchment_fc(cfg["stations"], cfg)
areas = catch.map(lambda f: f.set("area_km2", f.geometry().area(100).divide(1e6)))
for f in areas.select(["station", "n_basins", "area_km2"]).getInfo()["features"]:
    p = f["properties"]
    print(f"{p['station']:24s} {p['n_basins']:4d} basins  {p['area_km2']:9.0f} km2")

r = cfg["rainfall"]
y0, y1 = int(cfg["period"]["start"][:4]), int(cfg["period"]["end"][:4])
for y in range(y0, y1 + 1):
    fc = gee.rainfall_series(catch, f"{y}-01-01", f"{y + 1}-01-01", r["dataset"])
    t = gee.export_table(fc, f"rainfall_{y}", cfg["drive_folder"], ["station", "date", "rain_mm"])
    print("started export", y, t.id)
