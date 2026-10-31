# Knuckles downstream: sub-watersheds, tanks and reservoirs (provisional)

Supports the GCF Knuckles Project (UOM proposal sections 1, 4, 5, 6; deliverables D1-A03, D2, D3, D4, D6).
All products come from open data. Units are provisional until IWMI's sub-watershed boundaries are shared.

| File | Contents |
|---|---|
| `subwatersheds.geojson` | 15 provisional units of the Mahaweli catchment to below the Amban Ganga confluence (9,060 km²), WGS84 |
| `subwatershed_outlets.json` | outlet coordinates, upstream area and share inside the Knuckles range per unit |
| `unit_summary.csv` | per unit: area, elevation, slope, WorldCover 2021 classes, tanks, reservoirs, river-cell SPM |
| `waterbodies.csv`, `waterbodies_ge10ha.geojson` | 351 JRC water bodies ≥ 1 ha (max extent, permanent extent, mean occurrence, unit, name if known) |
| `reservoir_series.csv` | Sentinel-2 water spread and surface SPM per clear view, 11 reservoirs, 2019–2025 |
| `reservoir_summary.csv` | per reservoir: drawdown, seasonal SPM, Cyclone Ditwah ratio, trend (seasonal Kendall, BH-FDR) |
| `fig_k1_subwatersheds.(png,pdf)` | map of units, river sediment, reservoirs, stations |
| `fig_k2_reservoirs.(png,pdf)` | reservoir water spread and turbidity, 2019–2025 |

Method: `scripts/knuckles/20–23`. Units are delineated from the Copernicus GLO-90 DEM, with Sentinel-2/JRC
channels burned in by 15 m, using D8 routing (pysheds) and a custom upstream traversal. The catchment is
split at tributaries ≥ 250 km², plus tributaries ≥ 100 km² lying ≥ 30 % inside the Knuckles range
(7.33–7.58 N, 80.70–80.90 E, approximate).

Reservoir masks are the JRC maximum extent united with the connected 2022–25 Sentinel-2 water extent. Views
count only when ≥ 90 % of the reservoir is clear. Single-view water-spread drops below 50 % of the neighbouring
median are removed as artefacts (35 of 1,382). SPM is red-band Nechad and uncalibrated; values above
~500 g m⁻³ are saturated.
