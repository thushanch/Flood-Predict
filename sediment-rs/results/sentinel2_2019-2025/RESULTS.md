# Sentinel-2 river sediment signals, Sri Lanka — first national run

Interactive version: `river_sediment_atlas.html` (open in a browser).
Produced with the no-account pathway, `scripts/cog/10–18`; methods are in `docs/METHODS.md` §7.

## Data processed

| Item | Value |
|---|---|
| Sentinel-2 L2A scenes listed (2019–2025, 17 MGRS tiles) | 18,903 |
| Scenes read (≤ 70 % cloud) | 10,599 (7 missing from the archive) |
| National map period | 2024–2025: 2,179 scenes, 32,099 cell-observations |
| River cells (1 km), ≥ 3 clear scenes | 879 (≈ 880 km of channel wider than ~60 m) |
| Stations with data | 13 of 17; 948 QC'd station-days, 2019–2025 |
| Primary product | Red-band Nechad SPM (g m⁻³), uncalibrated |

## Findings

1. **October–November (second inter-monsoon) is the muddiest season.** It has
   the highest median at 10 of 13 stations, unchanged when the Nov–Dec 2025
   flood is removed. River cells seen in all four seasons (n = 575): NEM 30,
   FIM 30, SWM 24, SIM 34 g m⁻³.
2. **The dry-zone Mahaweli follows its own monsoon.** The lower Mahaweli is
   clearest in the SW monsoon (its dry season, 28 g m⁻³) and most turbid in
   FIM and NEM (45–53 g m⁻³).
3. **The Kalu carries more sediment than the Kelani.** Lower-Kalu cells have a
   median of 62 g m⁻³ against 23 for the lower Kelani (2.7×). Putupaula reads
   higher than Colombo on 77 % of shared clear days (median paired ratio 1.3).
4. **The lower Kalu is getting muddier.** Putupaula medians: 32 (2020–21),
   41 (2022–23), 66 g m⁻³ (2024–25). The seasonal Kendall trend is +18 %/yr
   (BH-FDR q = 0.004) and Pettitt finds a change after Nov 2021 (q = 0.005).
   Two checks argue against a processing artefact:
   - within the same years, reprocessed (baseline ≥ 04.00) and original
     scenes give similar values;
   - the Kelani, Walawe and Mahaweli show no comparable rise.

   Candidate causes to check: sand mining and land-use change.
5. **The late-November 2025 floods (Cyclone Ditwah) appear as a sediment
   pulse.**
   - Kelani at Colombo: 210 g m⁻³ on 30 Nov, about 10× normal.
   - Hanwella: 185 g m⁻³.
   - Lower Mahaweli: 25–42× normal on 2 Dec.

   Values above about 500 g m⁻³ are beyond the red band's reliable range.
6. **On the Kalu the sediment comes from upstream.** Along the lower 54 km
   (Fig. 3), red-band SPM goes from about 45 g m⁻³ near the mouth to 55–75
   around Putupaula, then steps up to 100–200 beyond about 35 km toward
   Ellagawa, in every season. The lower Kelani stays near 20 along its whole
   length. That points to sources in the Ellagawa–Ratnapura reaches, where gem
   dredging is documented. Narrower channels there may add some bank
   contamination.
7. **Flood pulse map (Fig. 2c).** 490 river cells were seen during
   26 Nov–12 Dec 2025, at a median of 5.4× their normal level. The
   interquartile range is 1.5–13×.
8. **Peak-season map (Fig. 2b).** Of the 750 cells with at least three
   seasons observed, the peak falls in SIM in 250, FIM in 223, NEM in 171 and
   SWM in 106. The lower Mahaweli peaks in FIM and NEM; western rivers
   mostly peak in SIM.
9. **Cloud hides the wet-zone SW monsoon.** Wet-zone stations had 0–7 clear SW
   monsoon looks over seven years, against 44–47 at the dry-zone Mahaweli
   stations.
10. **Method findings.**
   - *NIR contamination:* red- and NIR-band SPM differ by 100–140 % at every
     station. Bank-vegetation adjacency contaminates NIR in 20 m pixels of
     these channels, so red-band SPM is used.
   - *Reservoir trapping:* the check across the Mahaweli reservoirs
     (Peradeniya → Mahiyangana) is inconclusive (ratio 1.06, 95 % CI
     0.77–1.70), because tributaries join between the stations.

## Not yet done

- **Rainfall response and rating curves** (needs your gauge and discharge
  data). No rainfall API was reachable from the processing environment.
- **Cross-sensor check against Landsat:** Landsat on AWS is requester-pays.
  Use the GEE pathway.
- **ACOLITE reprocessing** of a scene subset: needed to quantify the
  atmospheric-correction and adjacency effects.
- **Ground truth:** none. All concentrations are uncalibrated estimates.

## Files

| File | Contents |
|---|---|
| `river_cells.csv` / `.geojson` | per 1 km cell: lon/lat, all-season and seasonal median SPM, turbidity, NDTI, scene counts, distance to coast, blended upper bound |
| `river_cells_labelled.csv` | same, with rough reach labels used for the reach summaries |
| `stations_clean.csv` | QC'd station-days. Columns `SPM_blend_*` hold red-band SPM in this run; see `summary.md` |
| `seasonal_median_spm.csv`, `trends.csv`, `observation_counts.csv`, `algorithm_spread.csv`, `reservoir_trapping.csv` | station analysis outputs |
| `stations_snapped.csv` | station locations snapped to the channel mask, with AOI source and size |
| `river_cells_metrics.csv` | per cell: peak season, seasonal swing, Cyclone Ditwah flood ratio, reach label |
| `profiles.csv` | Kelani, Kalu and Mahaweli cells ordered downstream-to-upstream, with seasonal SPM |
| `figures/fig1_sediment_map.(png,pdf)` | headline map: median SPM per river cell over hillshade, with stations, scale, north arrow and locator |
| `figures/fig2_four_panel.(png,pdf)` | (a) median SPM, (b) peak season, (c) Ditwah flood pulse, (d) station trends |
| `figures/fig3_profiles.(png,pdf)` | downstream profiles by season for the Kelani, Kalu and Mahaweli |
| `figures/` (other) | national seasonal maps, overview, station climatologies and time series |
