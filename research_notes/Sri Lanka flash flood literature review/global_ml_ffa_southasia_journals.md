# Global context for Sri Lankan flash flood studies: ML/DL, regional and non-stationary flood frequency analysis (FFA), South Asian and tropical-island analogues, and target journals

Method note: 15 web searches, run on 2026-10-18. Items marked **[PK]** come from prior knowledge. Their DOIs or bibliographic details were not re-checked in this session, so verify them before citing. Everything else links to a page the searches returned. Search snippets were sometimes summaries of abstracts, not full text. Where that matters, it is flagged.

## Q1. ML/DL: state of the art in flash flood susceptibility and forecasting, published critiques, and whether susceptibility mapping is saturated

### Takeaway
ML flood and flash-flood susceptibility mapping is a very crowded field. Many case studies compare algorithms (RF/XGBoost/SVM/ANN/hybrids, now often with SHAP) and report AUCs of 0.9 or more. A growing critical literature shows these scores are often inflated by random (non-spatial) splits and by how pseudo-absence points are sampled. The maps are also rarely checked against hydrology. Forecasting is different. Data-driven LSTM rainfall-runoff modelling for ungauged basins is now established through Kratzert et al. 2019, Caravan 2023 and Nearing et al. 2024 (Nature). It is open for small, flashy tropical catchments, because the training data are dominated by larger, temperate, daily-resolution basins.

### Cited Findings
**Susceptibility mapping: methods and how crowded the field is**
- A 2024 bibliometric and meta-data review in *Water* (Web of Science corpus) found that GIS, machine learning, statistical models and AHP dominate flood susceptibility modelling. Hybrid models were the most frequently used prediction models. The abstract says only that interest is "growing" and gives no growth curve. — [DOAJ: Water, Jan 2024](https://doaj.org/article/db1f5a68e6a342f68587314b0e66a91b)
- Typical recent case studies report very high AUCs for tree ensembles:
  - Storm Daniel, Greece: RF AUC 96.9%, XGBoost 96.8%. — [Water 17, 02678 (PDF)](https://www.itia.ntua.gr/el/getfile/2562/1/documents/water-17-02678-v2.pdf)
  - An Amazon basin study found XGBoost slightly better than RF. SHAP ranked LULC, elevation, rainfall, drainage density, slope, CN and soil as the top predictors. — [preprints.org 202505.1740](https://www.preprints.org/manuscript/202505.1740/v1)
  - A coastal study used SHAP, with XGBoost beating ANN and LightGBM. — [Applied AI Letters (DOAJ)](https://doaj.org/article/4e8d55ab62c943158bbcbd0ef209dc45)
- South Asian flash-flood susceptibility papers already exist:
  - NE Bangladesh: four ML models trained on 400 flood/non-flood points, with ANN best. — [Advances in Space Research, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0273117724010792)
  - Hybrid and ensemble tree-based flash-flood susceptibility. — [Remote Sensing 12(21):3568](https://doi.org/10.3390/RS12213568)
  - Kaljani basin, West Bengal. — [Springer s44288-026-00410-y](https://link.springer.com/article/10.1007/s44288-026-00410-y)
  - National-scale Nigeria study. — [Remote Sensing 18:3264](https://doi.org/10.3390/rs18193264)
  - Sedrata, Algeria (hybrid ML + optimisation). — [Sci Rep s41598-026-43262-9](https://www.nature.com/articles/s41598-026-43262-9)
  - Joint flood-landslide multi-hazard ensembles are a newer variant. — [arXiv 2604.16265](https://arxiv.org/pdf/2604.16265)

**Published critiques and pitfalls**
- **Random splits inflate AUC.** A 2026 study of the Feni (Bangladesh) flash flood found random splits inflate AUC by about 0.06–0.09 compared with spatially blocked cross-validation. — [Springer s44288-026-00759-0](https://link.springer.com/article/10.1007/s44288-026-00759-0)
- **Learned responses can be physically implausible.** In the same paper, an unconstrained learner was monotone in the physically expected direction on only 54.5% of its response surface. Its outputs were neither calibrated nor given valid uncertainty. The authors propose monotonicity constraints plus spatial conformal prediction. They also note that a single-event inventory gives an "event-conditioned diagnosis rather than a return-period product". — [Springer s44288-026-00759-0](https://link.springer.com/article/10.1007/s44288-026-00759-0)
- **Spatial validation as a fix.** One urban flood study used spatial 4-fold CV with a 5-km buffer to remove optimism caused by autocorrelation. — [Water 18(17):2141](https://doi.org/10.3390/w18172141)
- **Pseudo-absence sampling.** Non-flood points chosen outside buffer zones have very different predictor values, which makes classification artificially easy. — summarised in search results from [ResearchGate: Comparative assessment of ML models for FSM](https://www.researchgate.net/publication/400102315_Comparative_assessment_of_machine_learning_models_for_flood_susceptibility_mapping) (study not opened, so attribution is approximate)
- **Sampling matters more than the algorithm.** A Nepal preprint reports AUCs ranging from below 0.80 to above 0.95 depending on validation design. It says pseudo-absence sampling strategy has more influence on performance than algorithm choice. — [Research Square rs-10471428](https://www.researchsquare.com/article/rs-10471428)
- **Feature importance can be reversed.** Default Gini importance (ArcGIS Pro RF) completely reversed the true importance ranking when high-cardinality land cover was present. The authors recommend permutation importance. — [Remote Sensing 18:3264](https://doi.org/10.3390/rs18193264)
- **Historical inventory bias.** Models trained on past flood events may underestimate risk where no flood has occurred recently. — [ScienceDirect S2590197424000302](https://www.sciencedirect.com/science/article/pii/S2590197424000302)
- **Reporting standards.** A review asks ML flood-mapping studies to report validation strategy (random, k-fold, spatial or temporal CV) and class balance explicitly. — [MDPI 2673-4834/7/2/44](https://www.mdpi.com/2673-4834/7/2/44)
- **Hydrodynamic checks.** Some studies now combine susceptibility ML with hydrodynamic modelling to deal with the lack of hydrological validation. — [Natural Hazards s11069-025-07109-2](https://link.springer.com/article/10.1007/s11069-025-07109-2)
- **Data-sparse validation.** A national Nigeria study validated against satellite flood maps because inventories were sparse. — [Remote Sensing 18:3264](https://doi.org/10.3390/rs18193264)

**Reviews**
- **Bentivoglio et al. (2022).** "Deep learning methods for flood mapping: a review of existing applications and future research directions", *HESS* 26:4345–4378, doi:10.5194/hess-26-4345-2022. It reviews 58 publications and is CC BY. — [HESS](https://hess.copernicus.org/articles/26/4345/2022/)
- **Mosavi, Ozturk & Chau (2018).** "Flood prediction using machine learning models: literature review", *Water* 10(11):1536, doi:10.3390/w10111536. **[PK]** Bentivoglio et al. cite it, but the search did not return the paper itself. — [Bentivoglio et al. 2022 (citing)](https://hess.copernicus.org/articles/26/4345/2022/hess-26-4345-2022.pdf)
- **Rainfall-threshold methods.** A systematic review splits threshold methods for flash-flood early warning into empirical, hydrological and ML approaches. — [IWA Water Practice & Technology 19(11):4486](https://iwaponline.com/wpt/article/19/11/4486/105548/A-literature-review-rainfall-thresholds-as-flash)

**Forecasting (LSTM, global models, ungauged basins)**
- **Kratzert et al. (2019).** "Toward improved predictions in ungauged basins: Exploiting the power of machine learning", *Water Resources Research*, doi:10.1029/2019WR026065. LSTMs trained on 531 CAMELS basins and tested on basins left out of training reached median NSE 0.69. Calibrated SAC-SMA reached 0.64 and the NWM reanalysis 0.58. — [JKU research portal](https://research.jku.at/en/publications/toward-improved-predictions-in-ungauged-basins-exploiting-the-pow/)
- **Caravan (Kratzert et al. 2023, *Scientific Data*).** A standardised merger of 7 large-sample hydrology datasets covering 6,830 catchments, with ERA5-Land forcing. It is extendable through cloud-based extraction code. A GRDC extension adds 5,356 catchments in 25 countries (1950–2023). — [Google Research](https://research.google/pubs/caravan-a-global-community-dataset-for-large-sample-hydrology/); [DOAJ](https://doaj.org/article/5b1436c4feef4818b712c766b37627f2); [Zenodo GRDC extension](https://zenodo.org/records/15349031)
- **Nearing et al. (2024).** "Global prediction of extreme floods in ungauged watersheds", *Nature* 627:559–563, doi:10.1038/s41586-024-07145-1. An LSTM trained on 5,680 gauges gives reliability for extreme riverine events in ungauged basins at up to 5-day lead time. That is similar to or better than GloFAS same-day nowcasts. Its skill on 5-year events is similar to or better than current skill on 1-year events. It runs operationally in Google Flood Hub, covering more than 80 countries. — [IDEAS/RePEc](https://ideas.repec.org/a/nat/nature/v627y2024i8004d10.1038_s41586-024-07145-1.html); [Google Research blog](https://research.google/blog/using-ai-to-expand-global-access-to-reliable-flood-forecasts/). Volume and page numbers come from the RePEc record ID (v627, i8004).
- **Benchmarks on extremes.** In a related study, LSTMs, including a mass-conserving variant, stayed relatively accurate on extremes compared with Sacramento and the US NWM, even when extremes were not in the training data. Adding mass-balance constraints lowered skill on extremes. — summary in search results from [Google Research pubs](https://research.google/pubs/ai-increases-global-access-to-reliable-flood-forecasts/) (attribution to a specific paper not checked; this is probably Frame et al. 2022 HESS **[PK]**)
- **Deep-learning flash-flood warning in mountains.** A probabilistic deep-learning flash-flood warning study for mountainous catchments appeared in *J. Hydrology* (2025). — [ScienceDirect S0022169425000150](https://www.sciencedirect.com/science/article/abs/pii/S0022169425000150)
- **Earlier LSTM benchmark.** Kratzert et al. (2018), *HESS* 22:6005, doi:10.5194/hess-22-6005-2018, was the first large-sample LSTM rainfall-runoff benchmark. **[PK]**

### Inferences
- Another "compare RF/XGBoost/SVM + SHAP" flash-flood susceptibility map for a Sri Lankan district would most likely be judged incremental. The field looks saturated for algorithm comparisons. A study could still be novel if it uses spatial CV, controlled pseudo-absence sampling and monotonic or physics constraints, validates against hydrology (gauged flood records, hydrodynamic runs, independent events), or quantifies uncertainty with conformal methods.
- There is no published "saturation" statement in a formal review in what I found. The saturation judgement comes from the volume of near-identical case studies plus the critique papers.
- Google's global LSTM gives daily-scale riverine skill. Flash floods in catchments of roughly 10–500 km² with hourly response times sit outside its demonstrated scope. Testing Flood Hub or Caravan-style LSTMs on Sri Lankan wet-zone catchments, or fine-tuning them on local data, is a feasible and likely novel direction, if streamflow from the Irrigation Department can be obtained.

### Gaps
- No formal bibliometric count of the annual growth in flood-susceptibility ML papers was found.
- The search did not confirm whether Sri Lankan basins are included in Caravan or covered by Flood Hub.
- No transformer-based flash-flood forecasting paper was retrieved. Transformer vs LSTM claims need a separate search.
- Mosavi 2018 bibliographic details are **[PK]**.

## Q2. Regional and non-stationary FFA for small and ungauged catchments, plus sub-daily IDF links to design floods

### Takeaway
L-moment regional frequency analysis (Hosking & Wallis index-flood) and regression on catchment descriptors are still standard for ungauged sites. The main national guidelines (ARR 2019 RFFE, UK FEH/ReFH2, USGS StreamStats) cover small catchments poorly, and tropical-monsoon applications are few and recent (Bangladesh 2025, Krishna basin 2025). Non-stationary GEV with ENSO/IOD/urbanisation covariates is well developed for India. In those studies, short-duration rainfall extremes respond more to local drivers and long-duration extremes to ENSO/IOD. No Sri Lanka-specific non-stationary FFA was found.

### Cited Findings
**Regional FFA and index-flood methods**
- **Hosking & Wallis (1997).** *Regional Frequency Analysis: An Approach Based on L-Moments*, Cambridge University Press, doi:10.1017/CBO9780511529443. **[PK]** It is cited as the index-flood L-moment basis in, for example, the NZ RFFA paper, which used it for clusters of 10 or fewer sites. — [Australasian J Water Resources 2025 (T&F)](https://www.tandfonline.com/doi/full/10.1080/13241583.2025.2530280)
- **NE Bangladesh (2025, tropical-monsoon analogue).** L-moment RFFA on 26 gauges gave 4 homogeneous regions: 2 stable, 2 with high extreme variability. Regression for ungauged peaks reached R² 0.61–0.87, with higher uncertainty for extremes. — [Water 17(12):1771](https://doi.org/10.3390/w17121771)
- **Krishna basin, India.** An LH-moment RFFA framework for design floods. — [J. Hydrol. Regional Studies, S2214581825001065](https://www.sciencedirect.com/science/article/pii/S2214581825001065)
- **Mid-Norway.** L-moment RFFA with bootstrap uncertainty and regression for prediction in ungauged basins. — [JH:RS S2214581816301768](https://www.sciencedirect.com/science/article/pii/S2214581816301768)
- **Ungauged sites from regionalised streamflows.** FFA at ungauged sites can use regionally estimated streamflow series. — [J. Hydrometeorology 18(9), 2017](https://journals.ametsoc.org/view/journals/hydr/18/9/jhm-d-16-0143_1.xml)

**National guidelines and small catchments**
- **ARR RFFE.** It takes latitude, longitude and catchment area as inputs and interpolates quantiles from up to 15 gauged sites within 300 km (natural-neighbour interpolation; 2015 model, carried into ARR 2019). — [Rahman et al., MODSIM 2015](https://www.mssanz.org.au/modsim2015/L6/rahman2.pdf)
- **Pilbara (small catchments).** Most RFFE equations were built for larger catchments. A Pilbara study tested RFFE methods on new ungauged catchments under 10 km², using ARR2019 rainfall. — [Hydrology 9(10):165](https://doi.org/10.3390/hydrology9100165)
- **ARR 2019.** Ball et al. (eds) 2019, *Australian Rainfall and Runoff: A Guide to Flood Estimation*, Geoscience Australia, Book 3 (RFFE). **[PK]**
- **UK FEH (1999) and ReFH2.** ReFH2 is the event-based rainfall-runoff method of Kjeldsen 2007 (FEH Supplementary Report No. 1) and is updated for small and plot-scale catchments. It is the recommended UK approach for small catchments together with the FEH statistical method. **[PK]** The search returned no ReFH2 documentation.
- **USGS StreamStats.** A web application applying state regional regression equations for peak flows (Ries et al., USGS). **[PK]** Not returned by the search.
- **Other regional work.** Bayesian RFFA for large catchments. — [arXiv 1802.09278](https://arxiv.org/pdf/1802.09278). Regional flood methods (Western Sydney University). — [WSU](https://researchers.westernsydney.edu.au/en/publications/regional-flood-methods/)

**Non-stationary GEV with covariates**
- **Peninsular India.** Non-stationary GEV for 54 peninsular Indian catchments with ENSO, IOD and AMO as covariates found that all extreme indices showed non-stationarity. — [Sci Rep s41598-023-38771-w](https://www.nature.com/articles/s41598-023-38771-w)
- **Hyderabad IDF.** 62 GEV covariate combinations were tested (urbanisation, local and global temperature, ENSO, IOD). Local processes best explained short-duration rainfall; ENSO and IOD best explained long-duration rainfall. — [ResearchGate: Time-varying IDF through climate-informed covariates](https://www.researchgate.net/publication/356299497_Time-varying_Intensity-Duration-Frequency_relationship_through_climate-informed_covariates); work by Agilan & Umamahesh and by Vinnarasi & Dhanya is cited in the same sources
- **Climate drivers as covariates (China and elsewhere).** ENSO, IOD, NAO, PDO and SAM were used as time-varying GEV/GP covariates. — [J. Hydrol. 2024, S0022169424007042](https://www.sciencedirect.com/science/article/pii/S0022169424007042). Pearl River covariates. — [Atmos. Res. S0169809518316685](https://www.sciencedirect.com/science/article/abs/pii/S0169809518316685). Three Gorges non-stationary FFA. — [HSJ 10.1080/02626667.2019.1596274](https://www.tandfonline.com/doi/full/10.1080/02626667.2019.1596274). Asian monsoon regional non-stationary extremes. — [Atmos. Res. S0169809522005786](https://www.sciencedirect.com/science/article/abs/pii/S0169809522005786)
- **Background.** Milly et al. (2008) "Stationarity is dead", *Science* 319:573, doi:10.1126/science.1151915. **[PK]** Serinaldi & Kilsby (2015) critique of non-stationary FFA, *Adv. Water Resour.* 77:17–36, doi:10.1016/j.advwatres.2014.12.013. **[PK]** Their warning that trend-in-time covariates over-fit short records and should not be extrapolated matters for Sri Lankan records of about 30–60 years.

**Sub-daily IDF and design floods**
- **Fowler et al. (2021).** *Nature Reviews Earth & Environment* 2:107–122, doi:10.1038/s43017-020-00128-6. Short- and long-duration extremes intensify at about 7%/K (Clausius-Clapeyron). Some regions show super-CC increases in short-duration intensities, linked to convective feedbacks. These have "likely increased the incidence of flash flooding at local scales". — [CentAUR Reading](https://centaur.reading.ac.uk/95124/)
- **IDF curves built only from past data** can lead to over- or under-design. Disaggregation methods turn daily projections into sub-daily IDFs. CONUS thermodynamic simulations show amplified 1–24 h extremes. — [Princeton collaborate](https://collaborate.princeton.edu/en/publications/regional-variability-in-the-projected-changes-in-sub-daily-precip-2/)
- **TENAX (Peleg & Marra).** Builds sub-hourly design storms from daily climate-model output without downscaling. This is at conference-abstract stage. — [EGU24-3239](https://presentations.copernicus.org/EGU24/EGU24-3239_presentation.pdf)
- **Hanoi (tropical analogue).** Sub-daily IDF from regional model output using simple scaling projected AMS increases of 34–48% for 10–200-year return periods (Vu et al. 2017). — [MDPI Water 11(2):313 (intro citing)](https://0-www-mdpi-com.brum.beds.ac.uk/2073-4441/11/2/313)

### Inferences
- A Sri Lankan study offering any of the following would fill a visible gap:
  - an L-moment RFFA or index-flood for small wet-zone catchments;
  - a check of whether ARR/FEH-style small-catchment methods transfer;
  - a non-stationary GEV of annual maximum rainfall or floods with ENSO/IOD (and monsoon-season) covariates.
- The Indian evidence points to separate covariate structures for sub-daily and multi-day extremes. That fits a storm-shape and sub-daily study well.
- Short gauge records and few streamflow gauges will limit the work. Regional pooling plus covariate models that keep parameters to a minimum (Serinaldi & Kilsby) are advisable.

### Gaps
- ReFH2/FEH and StreamStats were not checked in this session (**[PK]** only).
- No Sri Lanka-specific RFFA or non-stationary FFA paper was found by the searches. A targeted search (Kelani, Kalu, Gin, Nilwala; Irrigation Department) is still needed. Absence of results does not prove absence of the work.
- No ARR 2019 tropical (Queensland/NT) small-catchment performance evaluation was retrieved.

## Q3. South Asian and tropical-island analogues: methods and data constraints

### Takeaway
Methods across South Asia fall into four groups:
- operational regional FFGS (WMO/HRC, SAsiaFFGS since 2020, covering Sri Lanka);
- post-event remote sensing (Sentinel-1 SAR / GEE inundation mapping, especially in Bangladesh);
- event attribution and return-period analysis (Kerala 2018, Pakistan 2022);
- ML susceptibility maps.

Calibrated, peer-reviewed rainfall-threshold studies are scarce. So are hydrological validations of FFGS for South Asia, and studies of flashiness or storm shape. Sparse sub-daily gauges and streamflow, trans-boundary data limits, and reliance on satellite rainfall are recurring constraints.

### Cited Findings
**Regional systems**
- **SAsiaFFGS.** The WMO-HRC-NOAA-USAID system covers Bangladesh, Bhutan, India (Regional Centre), Nepal and Sri Lanka. IMD dedicated it on 23 Oct 2020 for impact-based flash-flood guidance about 6–12 h ahead at 4 km × 4 km, after pre-operational testing. — [WMO SAsiaFFGS](https://wmo.int/south-asia-flash-flood-guidance-system-sasiaffgs); [AffairsCloud](https://affairscloud.com/india-meteorological-department-dedicated-1st-flash-flood-guidance-services-for-south-asia/)
- **Radar training.** 2021 radar-hydrology training for FFGS forecasters from all five countries. — [WMO news](https://wmo.int/media/news/south-asia-flash-flood-guidance-system-radar-hydrology-training)
- **Shutdown claim (weak source).** An uncorroborated claim says an earlier HRC South Asia system was shut down after about 1.5 years for lack of regional collaboration. — [BYJU'S (weak source)](https://byjus.com/free-ias-prep/south-asian-flash-flood-guidance-system-sasiaffg/); not confirmed by WMO
- **FFG overestimates observed thresholds.** In Mediterranean catchments, uniform FFG thresholds always overestimated observed rainfall thresholds, by 8–30%, and rainfall spatial variability mattered. — [arXiv 1904.07213](https://arxiv.org/pdf/1904.07213)
- **Ungauged basins and soil moisture.** A threshold method combining rainfall thresholds and soil moisture has been assessed for gauged and ungauged basins. — [ResearchGate 222568503](https://www.researchgate.net/publication/222568503_Flash_flood_warning_based_on_rainfall_thresholds_and_soil_moisture_conditions_An_assessment_for_gauged_and_ungauged_basins)

**India**
- **Kerala 2018 (Mishra et al.).** Basin 1-, 2- and 3-day rainfall had return periods of about 75, 200 and 100 years. Over 1–15-day durations above the Idukki, Kakki and Periyar reservoirs, return periods exceeded 500 years. Six of seven major reservoirs were above 90% full on 8 Aug 2018, which compounded the flooding. This was submitted as an HESS-Discussions preprint; final publication status was not confirmed in this session. — [HESSD hess-2018-480](https://hess.copernicus.org/preprints/hess-2018-480/)
- **Kerala damage survey.** Several river flood levels were at about 100-year return periods. — [AIR Worldwide white paper](https://www.air-worldwide.com/siteassets/Publications/White-Papers/documents/air_2018_kerala_flood_damage_survey_whitepaper.pdf)
- **Kerala modelling.** WRF sensitivity studies of the Kerala 2018 rainfall exist. — [arXiv 2609.09709](https://arxiv.org/pdf/2609.09709)
- **Drivers of flash floods across Indian sub-continental basins.** *npj Natural Hazards* (2025). — [Nature s44304-025-00121-3](https://www.nature.com/articles/s44304-025-00121-3). Title only seen; contents not checked.
- **Uttarakhand 2013 (Kedarnath).** Not retrieved in this session.

**Bangladesh**
- **Sylhet 2022 (SAR mapping).** Sentinel-1 + Otsu mapping estimated more than 1,600 km² inundated and more than 0.5 M people directly affected, with Habiganj worst hit. — [Geomatics, Natural Hazards and Risk 2026](https://www.tandfonline.com/doi/full/10.1080/19475705.2026.2614729)
- **Sylhet/Sunamganj 2022 (GEE).** About 152,253 ha and 210,670 ha flooded. — [ScienceDirect chapter](https://www.sciencedirect.com/science/article/abs/pii/B9780443238901000037)
- **Sylhet multi-year monitoring.** Sentinel-1/2 for 2017–2022. — [Springer chapter](https://link.springer.com/chapter/10.1007/978-3-032-11300-9_26)
- **Upstream rainfall drives haor flash floods.** Rainfall in Assam and Meghalaya, across the border, drives Sylhet haor flash-flood probability. — [J. Water & Climate Change 14(11):3985](https://iwaponline.com/jwcc/article/14/11/3985/98170/Spatiotemporal-rainfall-variability-and-its)
- **Feni 2024.** Constrained ML susceptibility with spatial conformal prediction (see Q1). — [Springer s44288-026-00759-0](https://link.springer.com/article/10.1007/s44288-026-00759-0)

**Pakistan 2022**
- **WWA rapid attribution.** 5-day maximum rainfall over Sindh and Balochistan increased by about 50–75%, with large model uncertainty. The CRS notes it was rapid and not peer-reviewed. — [WWA](https://www.worldweatherattribution.org/climate-change-likely-increased-extreme-monsoon-rainfall-flooding-highly-vulnerable-communities-in-pakistan/); [CRS IF12211](https://www.congress.gov/crs-product/IF12211)
- **Nanditha et al. (2023).** "The Pakistan Flood of August 2022: Causes and Implications", *Earth's Future*, doi:10.1029/2022EF003230. — [AGU/Wiley](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2022EF003230)
- **npj Natural Hazards (2025).** Pre-monsoon rainfall was 111% above the 1951–2021 average. It raised soil moisture before the monsoon, which made the flood worse. — [Nature s44304-025-00109-z](https://www.nature.com/articles/s44304-025-00109-z)

**Nepal**
- **Melamchi 2021 (ICIMOD).** A cascading flash flood on 15 June 2021 with multiple causes. Informal upstream-to-downstream risk communication reduced loss of life. ICIMOD recommends community-involved EWS. — [ICIMOD](https://www.icimod.org/article/the-melamchi-flood-disaster/); [HimalDoc report PDF](https://dpnet.org.np/public/uploads/files/HimalDoc2021_MelamchiFloods_Report%202022-03-07%2010-29-32.pdf)
- **Melamchi hazard mapping.** — [ADB](https://www.adb.org/sites/default/files/publication/927371/mapping-hazards-nepal-melamchi-river.pdf)
- **Melamchi drone damage and risk.** — [World Bank](https://documents1.worldbank.org/curated/en/099600006212237293/pdf/P16057809e269a0cf096ab044bc77400259.pdf)

**Thresholds and flashiness (transferable to steep islands)**
- **Thresholds depend on antecedent moisture and rainfall pattern.** In small mountainous catchments, thresholds ranged from 93 to 334 mm at one site and fell sharply with wetter antecedent soil. Antecedent moisture and rainfall temporal pattern both changed thresholds significantly. This directly supports a storm-shape × threshold study. — [ResearchGate 326330474](https://www.researchgate.net/publication/326330474_Rainfall_threshold_determination_for_flash_flood_warning_in_mountainous_catchments_with_consideration_of_antecedent_soil_moisture_and_rainfall_pattern)
- **US flash-flood severity (Saharia et al., J. Hydrometeorology).** Event flashiness was defined, with a 75th-percentile cut-off (0.0279 m³ s⁻² non-standardised). Flashiness depends on heavy rain occurring. — [NOAA repository](https://repository.library.noaa.gov/view/noaa/48334/noaa_48334_DS1.pdf). Author attribution is **[PK]**.
- **National flash flood potential index.** — [De Gruyter geo-2025-0891](https://www.degruyterbrill.com/document/doi/10.1515/geo-2025-0891/html)
- **European flash-flood database.** Gaume et al. (2009) *J. Hydrol.* 367:70–78, doi:10.1016/j.jhydrol.2008.12.028. **[PK]**

### Inferences
- **Sri Lanka is inside SAsiaFFGS.** Yet no peer-reviewed evaluation of FFGS skill for Sri Lanka (or for most member countries) turned up. Verifying FFGS guidance against observed flash floods and gauge thresholds in Sri Lanka's wet zone is likely novel and of practical use.
- **Thresholds that account for storm shape are underexplored in South Asia.** The mountainous-catchment evidence that rainfall temporal pattern changes thresholds supports a Sri Lankan "storm shape → threshold" paper.
- **South Asian analogue studies are mostly event-specific.** They are post-event SAR or GEE mapping, attribution, or one-off ML maps. Multi-event, multi-catchment threshold and flashiness climatologies are the open niche.

### Gaps
- None of Taiwan, Philippines, Malaysia, Indonesia, the Caribbean or Hawaii came up in a flash-flood threshold or flashiness study in the one search run. Their absence reflects search budget, not literature absence. Follow-ups: Taiwan WRA/NCDR threshold studies, PAGASA/Project NOAH, Malaysia (Cameron Highlands), Hawaii USGS flashiness, and the Caribbean FFGS (CARFFG).
- Bhutan, Myanmar, Chittagong Hill Tracts, Western Ghats beyond Kerala, and Uttarakhand were not searched.
- No country-level SAsiaFFGS verification document was found.

## Q4. Target journals for a Sri Lankan flash-flood study on thresholds, storm shape and flashiness

### Takeaway
The best scope fits for a regional, data-driven threshold, storm-shape and flashiness study are *Journal of Hydrology: Regional Studies* (fully OA, explicitly regional), *NHESS* (OA, per-page APC with waivers), and *Journal of Flood Risk Management* (fully OA, more applied and risk-focused). *J. Hydrometeorology* suits a rainfall-process or IMERG-focused version. *Hydrological Sciences Journal*, *Hydrology Research* and *J. Hydrology* suit methods-heavy versions. *Natural Hazards* and *IJDRR* suit warning, impact and DRR framing. *Water* (MDPI) is the fastest outlet but carries less prestige. APC figures below are mostly from third-party directories; confirm on publisher sites.

### Cited Findings
| Journal | Model / APC (as found) | Scope-fit note | Comparable recent papers seen in this search |
|---|---|---|---|
| J. Hydrology: Regional Studies (Elsevier) | Fully OA. APC about USD 2,460 (third-party). CC BY or CC BY-NC-ND. — [researcher.life](https://www.researcher.life/journal/journal-of-hydrology-regional-studies/16099) | Built for regional case studies with transferable insight. Strong fit for Sri Lankan thresholds/RFFA. | Krishna LH-moment RFFA (2025) [link](https://www.sciencedirect.com/science/article/pii/S2214581825001065); mid-Norway RFFA [link](https://www.sciencedirect.com/science/article/pii/S2214581816301768) |
| NHESS (Copernicus/EGU) | OA. Per-page APC: €77 (LaTeX) / €93 (Word) net. Copy-editing included. Limited waivers. — [NHESS APC page](https://www.natural-hazards-and-earth-system-sciences.net/about/article_processing_charges.html) | Hazard-focused. Public open discussion. Suits threshold/EWS framing. | Kerala 2018 study (HESS-D, same publisher) [link](https://hess.copernicus.org/preprints/hess-2018-480/) |
| J. Flood Risk Management (Wiley/CIWEM) | Fully OA. APC figures conflict: USD 2,090 [editage](https://www.editage.com/journal/journal-of-flood-risk-management/), up to USD 3,120 [DOAJ](https://doaj.org/toc/1753-318X), or USD 2,970 [OA finder](https://finder.open-access.network/journal/117024d1-e5c2-11ee-8238-dca48e8aad27) | Applied flood-risk and warning. Good for operational threshold/FFGS evaluation. | — |
| Hydrological Sciences Journal (T&F/IAHS) | Hybrid **[PK]** | Methods and hydrology; non-stationary FFA papers fit. | Three Gorges non-stationary FFA [link](https://www.tandfonline.com/doi/full/10.1080/02626667.2019.1596274) |
| J. Hydrometeorology (AMS) | Hybrid **[PK]** | Rainfall structure, IMERG, flashiness. | Ungauged FFA [link](https://journals.ametsoc.org/view/journals/hydr/18/9/jhm-d-16-0143_1.xml); US flash-flood severity/flashiness (NOAA copy) [link](https://repository.library.noaa.gov/view/noaa/48334/noaa_48334_DS1.pdf) |
| Natural Hazards (Springer) | Hybrid **[PK]** | Broad hazard scope. Many susceptibility papers. | Hydrodynamic + ensemble ML susceptibility [link](https://link.springer.com/article/10.1007/s11069-025-07109-2) |
| IJDRR (Elsevier) | Hybrid **[PK]** | DRR, EWS, community-warning angle. | — |
| Water (MDPI) | Fully OA, APC in CHF **[PK]**, amount not checked | Fast. Many susceptibility and RFFA papers. | NE Bangladesh L-moment RFFA 2025 [link](https://doi.org/10.3390/w17121771); urban ML flood risk [link](https://doi.org/10.3390/w18172141) |
| Hydrology Research (IWA) | Possibly fully OA since about 2021 **[PK, unverified]** | Regional hydrology and methods. | Sister IWA journal (JWCC) has a Sylhet rainfall–flash flood paper [link](https://iwaponline.com/jwcc/article/14/11/3985/98170/Spatiotemporal-rainfall-variability-and-its) |
| J. Hydrology (Elsevier) | Hybrid **[PK]** | Highest bar. Needs methodological novelty. | DL probabilistic flash-flood warning (2025) [link](https://www.sciencedirect.com/science/article/abs/pii/S0022169425000150); ENSO/IOD non-stationary GEV (2024) [link](https://www.sciencedirect.com/science/article/pii/S0022169424007042) |

- **Other outlets with relevant recent South Asian papers:** *Geomatics, Natural Hazards and Risk* (OA, T&F) [Sylhet 2022](https://www.tandfonline.com/doi/full/10.1080/19475705.2026.2614729); *npj Natural Hazards* [Pakistan 2022](https://www.nature.com/articles/s44304-025-00109-z) and [Indian flash flood drivers](https://www.nature.com/articles/s44304-025-00121-3); *Earth's Future* [Pakistan 2022](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2022EF003230); *Scientific Reports* [peninsular India non-stationarity](https://www.nature.com/articles/s41598-023-38771-w).

### Inferences
- **Threshold + storm-shape + flashiness paper.** First choice JH:RS or NHESS. If the work is reframed around warning operations, JFRM. For a sub-daily/IMERG-focused version, J. Hydrometeorology.
- **Algorithm-comparison susceptibility papers** mostly end up in Natural Hazards, GNHR, Water and Scientific Reports. Leading hydrology journals increasingly expect spatial CV and physical constraints (Q1).

### Gaps
- APCs for HSJ, J. Hydrometeorology, Natural Hazards, IJDRR, Water, Hydrology Research and J. Hydrology were not checked from publisher pages.
- JH:RS and JFRM APCs come from third-party aggregators, and the JFRM figures conflict.
- Recent Sri Lanka-specific papers in these journals were not systematically checked.
