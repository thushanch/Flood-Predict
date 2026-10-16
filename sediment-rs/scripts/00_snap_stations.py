"""Snap approximate station coordinates onto the stable river channel.

Writes config/stations_snapped.yaml, which every later script uses
automatically. Review the printout: large moves or high water fractions
(reservoir / lagoon) mean the station needs a manual coordinate.
"""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sedrs import gee  # noqa: E402
from sedrs.config import CONFIG_DIR, load_settings  # noqa: E402

cfg = load_settings()
if cfg["_stations_snapped"]:
    # always snap from the original approximate coordinates
    with open(CONFIG_DIR / "settings.yaml", encoding="utf-8") as f:
        cfg["stations"] = yaml.safe_load(f)["stations"]
gee.init(cfg["gee_project"])

out = []
print(f"{'station':24s} {'moved_m':>8s} {'water_frac':>10s}  note")
for s in cfg["stations"]:
    r = gee.snap_station(s["lon"], s["lat"], cfg)
    s2 = dict(s)
    note = ""
    if not r["ok"]:
        note = "NO stable water within search radius -- fix coordinates manually"
    else:
        s2.update(lon=r["lon"], lat=r["lat"], snap_moved_m=r["moved_m"],
                  water_fraction=r["water_fraction"])
        if r["moved_m"] > 1000:
            note = "moved > 1 km: check"
        if r["water_fraction"] > 0.5:
            note += " AOI mostly water: reservoir/lagoon?"
    print(f"{s['id']:24s} {r.get('moved_m', float('nan')):8.0f} "
          f"{r.get('water_fraction', float('nan')):10.2f}  {note}")
    out.append(s2)

with open(CONFIG_DIR / "stations_snapped.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump({"stations": out}, f, sort_keys=False)
print("wrote config/stations_snapped.yaml -- now check every station in gee_js/explore.js")
