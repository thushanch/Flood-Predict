# Methods — satellite sediment signals for Sri Lankan rivers without in-situ data

Every processing choice below names the paper (or reference implementation) it
follows. Coefficients were checked on 2026-10-16 against the ACOLITE source
code (`github.com/acolite/acolite`), which is maintained by the algorithm
authors' group at RBINS.

## 1. Framing

No suspended-sediment concentration (SSC) gauge network exists that could
calibrate a local algorithm. The study therefore:

1. retrieves **uncalibrated** SSC (as SPM, g m⁻³) and turbidity (FNU) with
   published, transferable semi-analytical algorithms plus a relative index;
2. replaces point validation with **four independent consistency checks** (§6);
3. draws conclusions mainly from **relative** quantities — seasonal contrasts,
   trends in % per year, longitudinal ratios — which are much less sensitive to
   calibration error than absolute concentrations.

Absolute values are reported as "estimated SPM" with uncertainty ranges and
must not be read as measured concentrations.

## 2. Data

| Data | Product (GEE ID) | Use | Reference |
|---|---|---|---|
| Sentinel-2 MSI L2A | `COPERNICUS/S2_SR_HARMONIZED` | main sensor (10–20 m) | — |
| Landsat-8/9 OLI C2 L2 | `LANDSAT/LC08|LC09/C02/T1_L2` | cross-sensor check, longer record | — |
| Cloud Score+ | `GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED` | S2 cloud/shadow mask | Pasquarella et al. 2023 |
| JRC Global Surface Water v1.4 | `JRC/GSW1_4/GlobalSurfaceWater` | stable-channel mask | Pekel et al. 2016 |
| HydroSHEDS Free-Flowing Rivers | `WWF/HydroSHEDS/v1/FreeFlowingRivers` | reach network | Grill et al. 2019 |
| HydroBASINS level 8 | `WWF/HydroSHEDS/v1/Basins/hybas_8` | upstream catchments | Lehner & Grill 2013 |
| CHIRPS daily | `UCSB-CHG/CHIRPS/DAILY` | catchment rainfall | Funk et al. 2015 |

Sentinel-2 L2A is systematic globally only from about December 2018, so the
Sentinel-2 record over Sri Lanka effectively starts in 2019. Landsat-8 extends
the record to 2013.

## 3. Pre-processing and masking

* **Atmospheric correction.** The GEE surface-reflectance products (Sen2Cor for
  S2, LaSRC for Landsat) are designed for land. The ACIX-Aqua intercomparison
  (Pahlevan et al. 2021) shows that the choice of atmospheric correction
  dominates the error budget over inland water. We use the GEE products at
  national scale and quantify their effect on a subset of scenes reprocessed
  with ACOLITE/DSF (Vanhellemont & Ruddick 2018), a processor built for aquatic
  applications (§6.5).
* **Clouds.** Sentinel-2: Cloud Score+ `cs_cdf ≥ 0.60`. The GEE catalogue
  recommends 0.50–0.65; higher values remove thin cloud and haze. Landsat:
  `QA_PIXEL` bits 1–4 (dilated cloud, cirrus, cloud, shadow) and `QA_RADSAT = 0`.
* **Water pixels.** A pixel must satisfy all of:
  1. JRC water occurrence ≥ 50 % (a stable channel, which excludes seasonally
     flooded paddy);
  2. lie at least 30 m (one JRC pixel) inside the bank, after erosion. This
     removes mixed land–water pixels and reduces the adjacency effect, which
     ACIX-Aqua names as a key error source for small water bodies;
  3. MNDWI > 0 on that date (Xu 2006), which removes exposed sand bars;
  4. ρ(SWIR-1, ~1610 nm) < 0.0215, the ACOLITE default non-water threshold;
  5. ρ(red) > 0 and ρ(green) > 0.
* **Station areas.** 500 m radius around each station after snapping it to the
  nearest stable-water pixel. An image is used only if it has ≥ 10 valid water
  pixels **and** ≥ 50 % of the station's potential water pixels are clear. A
  partially clouded area biases the median toward its clear part. Where tiles
  or paths overlap on the same date, the observation with the most pixels is
  kept.
* **Minimum river width.** After erosion, a channel needs to be about 60 m
  wide for Sentinel-2's 20 m bands (and wider for Landsat) to keep clean
  pixels. Narrower reaches drop out automatically. This is reported as a
  limitation, not hidden.

## 4. Retrieval algorithms

All algorithms take water-leaving reflectance ρw (= π·Rrs) and share the
single-band form of Nechad et al. (2010):

  X = A·ρw / (1 − ρw / C)

| Product | Band | A | C | Source |
|---|---|---|---|---|
| Turbidity T (FNU), red | ~645 nm (S2 B4, OLI B4) | 228.1 | 0.1641 | Dogliotti et al. 2015 |
| Turbidity T (FNU), NIR | ~859 nm (S2 B8A, OLI B5) | 3078.9 | 0.2112 | Dogliotti et al. 2015 |
| SPM (g m⁻³), S2 red | B4 665 nm | 342.10 | 0.19563 | Nechad 2016 calibration (ACOLITE table, Sept 2016) |
| SPM (g m⁻³), S2 NIR | B8A 865 nm | 2932.21 | 0.21151 | idem |
| SPM (g m⁻³), OLI red | B4 654 nm | 346.32 | 0.19905 | idem |
| SPM (g m⁻³), OLI NIR | B5 864 nm | 2929.49 | 0.21135 | idem |

* **Red/NIR switching** (Dogliotti et al. 2015). The red band is used when
  ρw(red) < 0.05, the NIR band when ρw(red) > 0.07, and a linear blend in
  between. The red band saturates in very turbid water, and the NIR band is
  noisy in clear water. We apply the same switching to the Nechad SPM pair
  (`SPM_blend`). Novoa et al. (2017) motivate multi-band switching for SPM.
* **NDTI** = (ρred − ρgreen)/(ρred + ρgreen) (Lacaux et al. 2007). This
  calibration-free relative index is used as a robustness check on every
  SPM-based result.
* Values are invalid where ρw ≤ 0 or ρw ≥ C (the formula's pole).
* Per station and image we keep the median and interquartile range of each
  product over the valid water pixels.

## 5. Analyses

| Question | Method | Reference |
|---|---|---|
| Seasonal regime | Monthly and seasonal medians by Department of Meteorology season (NEM Dec–Feb, FIM Mar–Apr, SWM May–Sep, SIM Oct–Nov); wet- vs dry-zone contrast | Dept. of Meteorology, Sri Lanka |
| Trend | Seasonal Kendall test and seasonal Sen slope on log₁₀ monthly medians | Hirsch et al. 1982; Sen 1968 |
| Trend, autocorrelation-robust | Hamed–Rao modified Mann-Kendall test on annual medians | Hamed & Rao 1998 |
| Step change (e.g. start of mining) | Pettitt test on deseasonalised log anomalies | Pettitt 1979 |
| Multiple stations | Benjamini–Hochberg false-discovery-rate correction across stations | Benjamini & Hochberg 1995 |
| Hotspots | Seasonal reach composites; a reach is flagged when its value is ≥ 2× the median of the 3 upstream reaches in ≥ 2 years; adjacent flags are merged into one hotspot | doubling threshold after Dethier et al. 2023 |
| Atlas | 1 km reaches along all rivers draining > 300 km²; seasonal median SPM, turbidity and NDTI per reach-year | — |

Trend tests use `pymannkendall` (Hussain & Mahmud 2019). Logs are used because
concentrations are right-skewed and changes are multiplicative.

## 6. Checks that replace in-situ validation

1. **Cross-sensor consistency.** Same-day Sentinel-2 vs Landsat-8/9 retrievals
   at the same station: bias, MAPD and Pearson r in log space, reduced major
   axis slope (Pahlevan et al. 2019; metrics after Seegers et al. 2018).
   Agreement shows the retrieval is repeatable across independent sensors and
   corrections. It does **not** prove accuracy.
2. **Algorithm spread.** Relative difference between the red- and NIR-band SPM
   estimates where both bands carry signal (ρred 0.03–0.09). This gives a
   per-station algorithm uncertainty.
3. **Physical plausibility: rainfall.** Spearman correlation between the
   signal and antecedent catchment rainfall (1, 3, 7 and 14 days, CHIRPS),
   tested with a Bonferroni-adjusted significance level. A station without a
   positive response is flagged: its signal may be dominated by bottom
   reflectance, algae or adjacency.
4. **Physical plausibility: reservoirs.** The downstream/upstream ratio across
   the Mahaweli cascade (Victoria–Randenigala–Rantembe) should be below 1
   (sediment trapping). Bootstrap 95 % CI.
5. **Atmospheric-correction sensitivity.** Reprocess about 20 cloud-free
   scenes covering wet and dry seasons with ACOLITE/DSF, and compare SPM with
   the GEE-based values using the same metrics as check 1.
6. **Order-of-magnitude check against literature.** Compare with published
   Sri Lankan point data: turbidity–TSS at the Gin River at Baddegama; Kelani
   turbidity at the Ambatale intake (Dissanayaka Mudiyanselage et al. 2025); Kotmale Oya
   sediment rating.
7. **Optional, very cheap ground truth.** National Water Supply and Drainage
   Board intake turbidity (by request), or about 15 handheld turbidity-meter
   readings on Sentinel-2 overpass days. Even a few points turn check 6 into a
   real error estimate.

## 7. Known limitations (state them in the paper)

* **Mineralogy.** Mineral absorption varies with iron-oxide content (Babin &
  Stramski 2004). Sri Lanka's lateritic soils may shift the red-band SPM
  relationship away from the North Sea and Río de la Plata calibrations, so
  absolute SPM could be off by a factor of about 2. Relative results are
  largely immune because the bias is roughly multiplicative.
* **Cloud bias.** The SW monsoon, when sediment peaks in the wet zone, has the
  fewest clear observations. Report observation counts per season and expect
  peaks to be under-sampled.
* **Narrow channels and the adjacency effect** (§3).
* **Atmospheric correction over water** (§3, check 5).
* **Optical depth.** In shallow, clear reaches, bottom reflectance can
  masquerade as sediment. Such reaches fail check 3.
* **Hotspot candidates** are not attributions: confluences, bridges and
  ferries produce the same signature. Verify each one on high-resolution
  imagery.
* **Catchment rainfall** includes the whole HydroBASINS unit that contains
  the station, which slightly over-estimates the catchment.

## References

* Babin, M., Stramski, D. (2004). Variations in the mass-specific absorption coefficient of mineral particles suspended in water. *Limnol. Oceanogr.* 49, 756–767.
* Benjamini, Y., Hochberg, Y. (1995). Controlling the false discovery rate. *J. R. Stat. Soc. B* 57, 289–300.
* Dethier, E.N., Renshaw, C.E., Magilligan, F.J. (2022). Rapid changes to global river suspended sediment flux by humans. *Science* 376, 1447–1452. doi:10.1126/science.abn7980
* Dethier, E.N., et al. (2023). A global rise in alluvial mining increases sediment load in tropical rivers. *Nature* 620, 787–793. doi:10.1038/s41586-023-06309-9
* Dogliotti, A.I., Ruddick, K.G., Nechad, B., Doxaran, D., Knaeps, E. (2015). A single algorithm to retrieve turbidity from remotely-sensed data in all coastal and estuarine waters. *Remote Sens. Environ.* 156, 157–168. doi:10.1016/j.rse.2014.09.020
* Funk, C., et al. (2015). The climate hazards infrared precipitation with stations (CHIRPS). *Sci. Data* 2, 150066.
* Grill, G., et al. (2019). Mapping the world's free-flowing rivers. *Nature* 569, 215–221.
* Hamed, K.H., Rao, A.R. (1998). A modified Mann-Kendall trend test for autocorrelated data. *J. Hydrol.* 204, 182–196.
* Hirsch, R.M., Slack, J.R., Smith, R.A. (1982). Techniques of trend analysis for monthly water quality data. *Water Resour. Res.* 18, 107–121.
* Hussain, M.M., Mahmud, I. (2019). pyMannKendall: a python package for non parametric Mann Kendall family of trend tests. *J. Open Source Softw.* 4(39), 1556. doi:10.21105/joss.01556
* Lacaux, J.P., Tourre, Y.M., Vignolle, C., Ndione, J.A., Lafaye, M. (2007). Classification of ponds from high-spatial resolution remote sensing: application to Rift Valley Fever epidemics in Senegal. *Remote Sens. Environ.* 106, 66–74.
* Lehner, B., Grill, G. (2013). Global river hydrography and network routing: baseline data and new approaches to study the world's large river systems. *Hydrol. Process.* 27, 2171–2186.
* Nechad, B., Ruddick, K.G., Park, Y. (2010). Calibration and validation of a generic multisensor algorithm for mapping of total suspended matter in turbid waters. *Remote Sens. Environ.* 114, 854–866.
* Nechad, B., et al. (2016). Calibration coefficients for Sentinel-2 MSI and Landsat-8 OLI (ESA Living Planet Symposium; values as updated Sept 2016 and distributed with ACOLITE, `Nechad_calibration_201609.txt`).
* Novoa, S., et al. (2017). Atmospheric corrections and multi-conditional algorithm for multi-sensor remote sensing of suspended particulate matter in low-to-high turbidity levels coastal waters. *Remote Sens.* 9(1), 61. doi:10.3390/rs9010061
* Pahlevan, N., Chittimalli, S.K., Balasubramanian, S.V., Vellucci, V. (2019). Sentinel-2/Landsat-8 product consistency and implications for monitoring aquatic systems. *Remote Sens. Environ.* 220, 19–29.
* Pahlevan, N., et al. (2021). ACIX-Aqua: a global assessment of atmospheric correction methods for Landsat-8 and Sentinel-2 over lakes, rivers, and coastal waters. *Remote Sens. Environ.* 258, 112366. doi:10.1016/j.rse.2021.112366
* Pasquarella, V.J., Brown, C.F., Czerwinski, W., Rucklidge, W.J. (2023). Comprehensive quality assessment of optical satellite imagery using weakly supervised video learning. *CVPR Workshops*. doi:10.1109/CVPRW59228.2023.00206
* Pekel, J.-F., Cottam, A., Gorelick, N., Belward, A.S. (2016). High-resolution mapping of global surface water and its long-term changes. *Nature* 540, 418–422.
* Pettitt, A.N. (1979). A non-parametric approach to the change-point problem. *J. R. Stat. Soc. C* 28, 126–135.
* Ross, M.R.V., et al. (2019). AquaSat: a data set to enable remote sensing of water quality for inland waters. *Water Resour. Res.* 55. doi:10.1029/2019WR024883
* Seegers, B.N., et al. (2018). Performance metrics for the assessment of satellite data products: an ocean color case study. *Opt. Express* 26, 7404–7422.
* Sen, P.K. (1968). Estimates of the regression coefficient based on Kendall's tau. *J. Am. Stat. Assoc.* 63, 1379–1389.
* Somasundaram, D., et al. (2021). [Secchi-depth transparency of 550 Sri Lankan reservoirs from Landsat-8 in GEE, 2013–2020]. *Remote Sens.* 13(11), 2193. (title paraphrased — check)
* Dissanayaka Mudiyanselage, P.S. (Sudeshika), et al. (2025). Study of sediment transport processes in the Kelani River Basin, Sri Lanka. *J. JSCE* 13(2), 24-16129.
* Vanhellemont, Q., Ruddick, K. (2018). Atmospheric correction of metre-scale optical satellite data for inland and coastal water applications. *Remote Sens. Environ.* 216, 586–597.
* Xu, H. (2006). Modification of normalised difference water index (NDWI) to enhance open water features in remotely sensed imagery. *Int. J. Remote Sens.* 27, 3025–3033.

*Verify page numbers and author lists against the publisher's version before
submission. Entries without a DOI above were cited from memory or from
abstract pages and have not been checked against the full text.*
