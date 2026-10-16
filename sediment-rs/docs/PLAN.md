# Work plan

**Working title:** *Satellite-derived suspended-sediment signals across Sri Lankan
rivers: seasonal regimes, trends and hotspots under data scarcity*

**Gap addressed:** no multi-river, multi-year, satellite-derived SSC record
exists for Sri Lanka. Existing remote-sensing work covers reservoir clarity
(Somasundaram et al. 2021), coastal turbidity (ACRS 2024) or channel planform
(Lower Mahaweli, Deduru Oya). The only river-level use of reflectance was a
model check in the Kelani basin (Dissanayaka Mudiyanselage et al. 2025).

## Research questions

1. **RQ1 Regimes.** How does the satellite sediment signal vary by season
   (NEM/FIM/SWM/SIM) and between wet-zone and dry-zone rivers?
2. **RQ2 Change.** Which rivers show significant trends or step changes over
   2013/2019–2026?
3. **RQ3 Hotspots.** Where along the rivers do recurring downstream jumps
   occur (candidate sand or gem mining, bank erosion)?
4. **RQ4 Reliability.** How far can these signals be trusted without in-situ
   data? Answered through cross-sensor, algorithm, rainfall, reservoir and
   atmospheric-correction checks.

## Phases

| # | Step | Script | Output | Done when |
|---|---|---|---|---|
| 0 | GEE account + Cloud project; `pip install -r requirements.txt` | — | — | `earthengine authenticate` works |
| 1 | Snap stations, inspect in Code Editor | `00_snap_stations.py`, `gee_js/explore.js` | `config/stations_snapped.yaml` | every station sits on open channel, not on a reservoir, lagoon or bridge |
| 2 | Station extraction S2 + L8/9 | `01_extract_stations.py` | `data/stations/*.csv` | all exports finished |
| 3 | Catchment rainfall | `04_rainfall.py` | `data/rainfall/*.csv` | — |
| 4 | Station analysis + checks 1–4 | `05_analyse.py` | `outputs/summary.md`, figures | checks reviewed; implausible stations listed |
| 5 | ACOLITE subset (check 5) | ACOLITE GUI/CLI on ~20 scenes | AC-sensitivity table | bias / MAPD known |
| 6 | National reaches + seasonal composites | `02_build_reaches.py`, `03_extract_reaches.py` | `data/reaches/*.csv` | — |
| 7 | Atlas + hotspots | `05_analyse.py` | `outputs/hotspots.csv` | each hotspot checked in Google Earth history |
| 8 | Writing | — | manuscript | — |

Start small: run phases 1–4 for **Kelani, Kalu and Mahaweli** first. Scale to
all rivers only after the checks look sensible.

## Paper figures (planned)

1. Study area: rivers, stations, wet/dry zones, reservoirs.
2. Observation availability per season (shows the SW-monsoon cloud gap).
3. Monthly climatology per station (SPM and NDTI).
4. Validation-substitute panel: cross-sensor scatter, rainfall-response bars,
   reservoir ratio, ACOLITE vs GEE.
5. Trend map (% per year, FDR-significant markers).
6. National reach atlas: seasonal median SPM.
7. Longitudinal profiles with hotspot clusters, plus high-resolution image
   inserts.

## Candidate journals

*Remote Sensing Applications: Society and Environment*; *Journal of Hydrology:
Regional Studies*; *Remote Sensing* (MDPI); *Environmental Monitoring and
Assessment*. Local option: *Engineer* (IESL).
