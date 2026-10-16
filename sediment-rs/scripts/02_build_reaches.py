"""Build ~1 km reaches along all Sri Lankan rivers above a drainage-area threshold.

Source: WWF HydroSHEDS Free-Flowing Rivers network (Grill et al. 2019) in GEE.
Writes data/reaches.geojson (LineStrings, chainage from the mouth).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ee  # noqa: E402

from sedrs import gee, reaches  # noqa: E402
from sedrs.config import DATA_DIR, load_settings  # noqa: E402

cfg = load_settings()
rc = cfg["reaches"]
gee.init(cfg["gee_project"])

fc = ee.FeatureCollection(rc["river_network"]).filterBounds(ee.Geometry.Rectangle(rc["bbox"]))
props = fc.first().propertyNames().getInfo()
need = {"BB_ID", "BB_NAME", "UPLAND_SKM"}
if not need <= set(props):
    sys.exit(f"Expected fields {need} not in dataset; available: {sorted(props)}")

fc = fc.filter(ee.Filter.gte("UPLAND_SKM", rc["min_upland_km2"])).select(sorted(need))
n = fc.size().getInfo()
print("river lines above threshold:", n)
feats = fc.toList(n).getInfo() if n <= 5000 else sys.exit("too many lines; raise min_upland_km2")

segs = reaches.build_reaches(feats, seg_km=rc["segment_km"])
DATA_DIR.mkdir(exist_ok=True)
path = DATA_DIR / "reaches.geojson"
path.write_text(json.dumps({"type": "FeatureCollection", "features": segs}))
rivers = sorted({s["properties"]["river"] for s in segs})
print(f"wrote {len(segs)} reaches on {len(rivers)} rivers -> {path}")
print("Note: BB_NAME is often empty in HydroSHEDS; rename rivers in the GeoJSON if needed.")
