"""Seasonal median composites over every reach (Sentinel-2), for the atlas and hotspots.

Starts one Drive export per year (4 seasons each) plus one lentic-flag table.
Put the CSVs in data/reaches/.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ee  # noqa: E402

from sedrs import gee  # noqa: E402
from sedrs.config import DATA_DIR, load_settings  # noqa: E402
from sedrs.seasons import SEASONS  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
ap.add_argument("--sensor", default="S2")
args = ap.parse_args()

cfg = load_settings()
gee.init(cfg["gee_project"])
rc = cfg["reaches"]

gj = json.loads((DATA_DIR / "reaches.geojson").read_text())
feats = [ee.Feature(ee.Geometry.LineString(f["geometry"]["coordinates"]).buffer(rc["buffer_m"]),
                    f["properties"]) for f in gj["features"]]
reaches = ee.FeatureCollection(feats)
region = ee.Geometry.Rectangle(rc["bbox"])

wf = gee.water_fraction(reaches, cfg).map(
    lambda f: ee.Feature(None, {"reach_id": f.get("reach_id"), "water_fraction": f.get("mean")}))
gee.export_table(wf, "reaches_water_fraction", cfg["drive_folder"])

for y in args.years:
    tables = [gee.reduce_reaches(gee.season_composite(args.sensor, region, s, y, cfg), reaches, args.sensor)
              for s in SEASONS]
    fc = ee.FeatureCollection(tables).flatten()
    t = gee.export_table(fc, f"reaches_{args.sensor}_{y}", cfg["drive_folder"])
    print("started export", y, t.id)
