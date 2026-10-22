# sediment-rs — satellite sediment signals for Sri Lankan rivers

This pipeline maps suspended sediment (SPM / SSC), turbidity and NDTI along
Sri Lankan rivers from Sentinel-2 and Landsat-8/9 imagery in Google Earth
Engine, then analyses the results offline. It is built for the **no in-situ
data** situation: published algorithms with literature-verified coefficients,
plus four independent consistency checks in place of point validation.

* Methods and references: [`docs/METHODS.md`](docs/METHODS.md)
* Research questions, phases and planned figures: [`docs/PLAN.md`](docs/PLAN.md)

## Quick start

```bash
cd sediment-rs
pip install -r requirements.txt
earthengine authenticate             # once
# set gee_project in config/settings.yaml

python scripts/00_snap_stations.py   # snap approximate stations onto the channel
#   -> check every station in gee_js/explore.js (GEE Code Editor)
python scripts/01_extract_stations.py   # S2 + L8/9 per-image station stats -> Drive
python scripts/04_rainfall.py           # CHIRPS catchment rainfall -> Drive
#   download the CSVs into data/stations/ and data/rainfall/
python scripts/05_analyse.py            # QC, checks, climatology, trends -> outputs/

# national atlas + hotspots (heavier)
python scripts/02_build_reaches.py      # HydroSHEDS -> data/reaches.geojson
python scripts/03_extract_reaches.py    # seasonal composites -> Drive -> data/reaches/
python scripts/05_analyse.py
```

### No Earth Engine account? Public-archive pathway (`scripts/cog/`)

Reads Sentinel-2 Cloud-Optimized GeoTIFFs straight from AWS Open Data and
JRC water from Google Cloud Storage. This is how the first national map was
made.

```bash
python scripts/cog/10_river_mask.py          # JRC occurrence for Sri Lanka
python scripts/cog/11_list_scenes.py 2019 2025   # ~19k scenes, ~15 min
python scripts/cog/12_water_frequency.py 12  # clearest 12 scenes/tile -> 20 m water frequency
python scripts/cog/13_river_network.py       # channel mask + station snapping
# per-scene retrieval; run 4 shards in parallel (resumable)
for i in 0 1 2 3; do python scripts/cog/14_extract.py --shard $i/4 --workers 4 & done; wait
python scripts/cog/15_aggregate.py           # 1 km river cells, maps, station table
python scripts/05_analyse.py --data data/cog_analysis --out outputs/cog_stations
python scripts/cog/17_metrics.py             # peak season, flood pulse, profiles, hillshade
python scripts/cog/16_build_map.py           # interactive atlas HTML
python scripts/cog/18_figures.py             # publication figures (PNG + PDF)
```

### Offline demo (no GEE needed)

```bash
python scripts/make_demo_data.py
python scripts/05_analyse.py --data demo_data --out demo_outputs
python -m pytest -q
```

The demo uses **synthetic** data with planted signals: a +6 %/yr trend, a
step change, reservoir trapping, a Landsat–Sentinel bias and a mining-type
jump. Use it to confirm the analysis recovers them. Its numbers say nothing
about real rivers.

## Layout

```
config/settings.yaml   stations (APPROXIMATE coords), masks, thresholds
sedrs/algorithms.py    Nechad / Dogliotti / NDTI -- coefficients from ACOLITE tables
sedrs/gee.py           Earth Engine collections, masks, reductions, exports
sedrs/qc.py            filtering, de-duplication, monthly series
sedrs/consistency.py   cross-sensor, algorithm spread, reservoir trapping
sedrs/drivers.py       rainfall response
sedrs/trends.py        seasonal Kendall, Hamed-Rao MK, Pettitt, BH-FDR
sedrs/reaches.py       HydroSHEDS lines -> ordered 1 km reaches
sedrs/hotspots.py      recurring downstream jumps + clustering
gee_js/explore.js      Code Editor map for visual QA
scripts/00..05         pipeline steps
tests/                 unit tests (formulas checked against hand calculations)
```

## Status / caveats

* The offline analysis is unit-tested and runs end to end on synthetic data.
* The Earth Engine code (`sedrs/gee.py`, `gee_js/explore.js`) has **not yet
  been run against live GEE**: it was written without an authenticated
  session. Expect to fix small API issues on the first run. Start with one
  river and one year (`--sensors S2 --years 2024`).
* Station coordinates are approximate until `00_snap_stations.py` has been
  run and each station checked visually.
* Reported SPM values are *uncalibrated estimates*. Interpret seasonal
  contrasts, trends (% per year) and longitudinal ratios, and be cautious
  with absolute mg/L.
