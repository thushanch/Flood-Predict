# Sri Lankan flood and flash-flood studies: susceptibility mapping, hydrological/hydraulic modelling, and flood frequency analysis (inventory to 2026, Cyclone Ditwah excluded)

> **Method note for the report writer.** WebFetch could not open any publisher page in this session: Wiley, MDPI, Springer, SLJOL, ResearchGate, Semantic Scholar, ADS and PWRI all failed with DNS errors or a proxy 403. Every detail below therefore comes from search-engine-indexed abstracts, repository records (dl.lib.uom.lk, ir.lib.pdn.ac.lk, DOAJ, IEEE Xplore listing, SLJOL listing) and search snippets. Details such as catchment size, rainfall time step, DEM and inventory source were often missing from abstracts. Those are marked **[unverified]** or listed under Gaps. Nothing here is invented. Where a field was not in the indexed text it says "not stated in abstract". Cyclone Ditwah (Nov 2025) material is excluded, including the 2026 *Hydrology* IDF paper on Ditwah rainfall.
>
> **Flash-flood flag used below.**
> - **FF-true:** sub-daily inputs, small (<~500 km²) steep catchment, event peak/timing simulated.
> - **FF-partial:** some sub-daily or event elements but basin-scale.
> - **FF-loose:** "flash flood" used loosely, or riverine/basin-scale daily work.

## 1. Flood/flash-flood susceptibility and hazard mapping: methods, basins, validation, inventories

### Takeaway
Data-driven flood susceptibility mapping (FSM) in Sri Lanka is thin. The verifiable peer-reviewed work found is:
- one boosting-ML study in Ratnapura (upper Kalu), the only ML-based FSM found;
- one logistic regression (LR) study in the Nilwala basin;
- an LR study in Kalutara that could not be verified;
- several AHP/MCDA hazard or vulnerability studies (Neluwa/Gin, Thudawa/Nilwala, Lower Nilwala, Colombo).

No Sri Lankan flood (as opposed to landslide) susceptibility study using frequency ratio, weights of evidence, Shannon entropy, SVM, ANN or CNN/deep learning was found. All studies found are riverine/basin-scale with inventories drawn from DMC inundation maps, satellite images and surveys. None is a true flash-flood susceptibility study of small steep upland catchments (Kegalle, Badulla, Nuwara Eliya: none found).

### Cited Findings

**Boosting ML (XGBoost, LightGBM, CatBoost, GBM, LogitBoost)**
- **Kurugama, Kazama, Hiraga & Samarasuriya (2024).** "A comparative spatial analysis of flood susceptibility mapping using boosting machine learning algorithms in Rathnapura, Sri Lanka", *J. Flood Risk Management* 17(2) e12980 (Tohoku University group). Peer-reviewed. — [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1111/jfr3.12980); [Tohoku Pure](https://tohoku.elsevierpure.com/en/publications/a-comparative-spatial-analysis-of-flood-susceptibility-mapping-us)
  - **Data and models:** a spatial database of 595 flood-inventory points and 13 flood predictors, used to run five boosting algorithms (GBM, XGBoost, CatBoost, LogitBoost, LightGBM). — [Wiley search snippet](https://onlinelibrary.wiley.com/doi/full/10.1111/jfr3.12980)
  - **Inventory source:** "445 flood locations from 2003 to 2017" drawn from Disaster Management Center (DMC) inundation maps, satellite images and field surveys. The 445 vs 595 difference may be flood vs flood+non-flood points **[unverified; conflicting snippets]**. — [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1111/jfr3.12980)
  - **Study area:** upper Kalu catchment, separated into five Divisional Secretariat divisions. — [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1111/jfr3.12980)
  - **Validation:** best was LightGBM (F1 = 0.907, Kappa = 0.813, AUC = 0.970); worst was GBM (F1 = 0.649, Kappa = 0.313, AUC = 0.737). — [Wiley PDF listing](https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/jfr3.12980)
  - **Transferability:** LightGBM tested beyond the training region gave "moderate" performance (F1 = 0.745, Kappa = 0.460, AUC = 0.800). One snippet names the transfer area as Kalutara district **[region name unverified]**. — [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1111/jfr3.12980); [arXiv 2604.16265 bibliography mention](https://arxiv.org/pdf/2604.16265)
  - **Gap statement:** the authors say "in the context of FSM in Sri Lanka, the application of ML models is limited." — [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1111/jfr3.12980)
  - **Not stated in abstract:** XGBoost AUC, DEM source, rainfall layer resolution.
  - **Flag:** FF-loose. Riverine Kalu flooding at Ratnapura; static predictors; no sub-daily rainfall.

**Logistic regression**
- **Abeysiriwardana & Wijesekera (2022).** "Application of GIS and Logistic Regression for Flood Susceptibility Mapping in Nilwala River Basin, Sri Lanka", *Engineer* (IESL) 55(2): 1–9, DOI 10.4038/engineer.v55i2.7503. Peer-reviewed national journal. — [SLJOL](https://engineer.sljol.info/articles/10.4038/engineer.v55i2.7503); [ResearchGate](https://www.researchgate.net/publication/363924406_Application_of_GIS_and_Logistic_Regression_for_Flood_Susceptibility_Mapping_in_Nilwala_River_Basin_Sri_Lanka)
  - **Factors:** four conditioning factors (elevation, slope, distance from river, land use).
  - **Inventory:** 205 flood and 199 non-flood locations, split 70/30.
  - **Validation:** AUC success rate 86%, prediction rate 87%.
  - **Not stated in abstract:** inventory source, DEM.
  - **Flag:** FF-loose.
- **Kalutara district LR study in QGIS (JournalsPub, ~2025).** Reports AUC = 0.89 and very high susceptibility around Kalu Ganga and Kuda Ganga. — [JournalsPub PDF](https://journalspub.com/wp-content/uploads/2025/06/1-11-FLOOD-SUSCEPTIBILITY-MODELLING-USING-LOGISTIC-REGRESSION-IN-QGIS-ENVIRONMENT-1.pdf)
  - **[Authors, venue quality and Sri Lankan setting only partially verified.]** A follow-up search did not re-locate it.
  - Treat as low-tier / unverified.

**AHP / GIS-MCDA (hazard and vulnerability, mostly not validated against an inventory)**
- **Wijesinghe, Mishra, Tripathi, Abdelrahman, Tiwari & Fnais (2023).** "Integrated Flood Hazard Vulnerability Modeling of Neluwa (Sri Lanka) Using AHP and Geospatial Techniques", *Water* 15: 1212, DOI 10.3390/w15061212. Upper Gin basin, Galle district. — [MDPI/DOI](https://doi.org/10.3390/w15061212); [MDPI](https://www.mdpi.com/2073-4441/15/6/1212)
  - **Criteria:** nine sub-criteria under built-environment, physical and socio-economic groups.
  - **Result:** 14.24% of the area at very high risk and 30.24% at high risk.
  - **Validation:** not stated in abstract.
  - **Flag:** FF-loose. Neluwa is a hilly upper-Gin area, so it is a potential flash-flood setting, but there is no hydrological analysis.
- **Nuwanka & Withanage (2024).** "A GIS-based framework for flood hazard vulnerability evaluation in Thudawa area, Sri Lanka", *Int. J. Information and Decision Sciences* 16(1): 90–108. — [IDEAS/RePEc](https://ideas.repec.org/a/ids/ijidsc/v16y2024i1p90-108.html); [ResearchGate](https://researchgate.net/publication/377755040_A_GIS-based_framework_for_flood_hazard_vulnerability_evaluation_in_Thudawa_area_Sri_Lanka)
  - **Method:** AHP criterion weighting.
  - **Validation:** one snippet reports 72.2% overall accuracy by ROC **[unverified; second search could not confirm ROC]**.
  - **Flash-flood claim:** describes "high flash-flood risk" near the Nilwala river mouth. This is a lowland/coastal setting. — [ResearchGate](https://www.researchgate.net/publication/356855239_A_GIS-Based_Framework_For_Flood_Hazard_Vulnerability_Evaluation_In_Thudawa_Area_Sri_Lanka)
  - **Flag:** FF-loose. Mislabelled "flash".
- **Lower Nilwala floodplain GIS-MCDA (2026).** Springer article s44177-026-00114-5. — [Springer](https://link.springer.com/article/10.1007/s44177-026-00114-5)
  - **Method:** AHP + weighted linear combination, 22 sub-criteria.
  - **Result:** 7.9% of area (32.7 km²) at high/very-high risk; 48.7% (200.6 km²) at moderate risk.
  - **Authors:** not captured.
- **Nilwala sub-basin prioritisation for flood exposure using MCDA/TOPSIS (2022).** *Engineer* 55(1), DOI 10.4038/engineer.v55i1.7483. — [SLJOL](https://engineer.sljol.info/article/10.4038/engineer.v55i1.7483/)
  - **Result:** 20% / 54% / 26% of basin area at high / moderate / low exposure.
  - **Data:** SRTM DEM, soil and land use.
- **Colombo vs Auckland vs Valencia, GIS hybrid/fuzzy-AHP (2026).** *Environmental Earth Sciences*, s12665-026-12888-3. — [Springer](https://link.springer.com/article/10.1007/s12665-026-12888-3)
  - **Factors:** seven (elevation, slope, LULC, drainage density, proximity to river, soil, rainfall).
  - **Weights:** slope had the highest weight for Colombo (0.3401).
- **Colombo multi-method framework (2025).** AHP hazard mapping + hydrodynamic modelling + economic impact. — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2772741625000390)
- **Ja-Ela DS Division geospatial flood hazard model.** Uses distance to water, buildings, soils and past flood records. **[Venue/year unverified.]** — [ResearchGate](https://www.researchgate.net/publication/324690169_A_Geo-spatial_Model_for_Flood_Hazard_Mitigation_With_Reference_to_Ja-Ela_Divisional_Secretariat_Division_-_Sri_Lanka)
- **Remote sensing and GIS flood risk analysis, Kalu Ganga.** Says the lower reaches of Kalu, Kelani and Gin are frequently flooded. **[Method details unverified.]** — [ResearchGate](https://www.researchgate.net/publication/289840047_Application_of_remote_sensing_and_gis_for_flood_risk_analysis_A_case_study_at_Kalu-Ganga_River_Sri_Lanka)
- **Other low-tier items found but not verified.** Possibly relevant, but abstracts were garbled or inaccessible:
  - "Climate Change Effect on the Urbanization: Intensified Rainfall and Flood Susceptibility in Sri Lanka" — [ResearchGate](https://www.researchgate.net/publication/368475972_Climate_Change_Effect_on_the_Urbanization_Intensified_Rainfall_and_Flood_Susceptibility_in_Sri_Lanka)
  - Perera, *Athens Journal of Sciences* 2024 — [PDF](https://www.athensjournals.gr/sciences/2023-5584-AJS-Perera-07.pdf)
  - KDU 12th IRC 2019 paper — [KDU IR](http://ir.kdu.ac.lk/bitstream/handle/345/2286/com035.pdf?sequence=3&isAllowed=y)
  - "Flood prediction using ML ... Kalu Ganga" preprint. Its indexed abstract reads like energy-load forecasting (CNN/LSTM/CNN-LSTM), so it is possibly mis-indexed. — [ResearchGate](https://www.researchgate.net/publication/378682897_FLOOD_PREDICTION_USING_MACHINE_LEARNING_BASED_ON_METROLOGICAL_AND_TOPOGRAPHICAL_FEATURES_OF_KALU_GANGA_RIVER_BASIN_SRI_LANKA)

**Methods with no Sri Lankan flood application found**
- **Shannon entropy:** the only Sri Lankan entropy application found is landslide vulnerability in Kegalle district (14 indicators), not floods. — [Springer, MESE](https://link.springer.com/article/10.1007/s40808-019-00615-w)
- **Weights of evidence, frequency ratio, SVM, RF-only, ANN, CNN/deep-learning FSM:** none found for Sri Lankan floods. — searches summarised in [WebSearch results incl. FL-MHSM arXiv](https://arxiv.org/abs/2604.16265)
- **FL-MHSM (Mundayatt & Sreevalsan-Nair, 2026, arXiv 2604.16265):** a flood–landslide multi-hazard ML paper that covers Kerala and Nepal, not Sri Lanka. Do not count it. — [arXiv](https://arxiv.org/abs/2604.16265)
- **Flood inventories:** the stated sources are DMC inundation maps, satellite images and field surveys (Kurugama et al.). DesInventar Sri Lanka (DMC) is the national disaster-loss database usable for inventories. — [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1111/jfr3.12980); [DesInventar.lk](https://www.desinventar.lk/)

### Inferences
- **No susceptibility work in the upland districts.** None was found for Kegalle, Badulla, Nuwara Eliya or the steep upper Kelani (Kitulgala) sub-catchments, nor any flash-flood-specific susceptibility map. This is a clear gap for a flash-flood study.
- **ML is close to untouched.** Only one ML-FSM study was found (Kurugama et al. 2024). Frequency ratio, WoE, entropy, RF, SVM, ANN, CNN and explainable ML (SHAP) are effectively open for Sri Lankan floods. For novelty, combine these with a flash-flood-specific inventory (event dates, sub-daily triggers).
- **Validation is weak.** AHP studies are rarely validated against an independent inventory, and inventories are dominated by large monsoon riverine events (2003, 2016, 2017).

### Gaps
- Not obtained from full texts: the XGBoost AUC and DEM resolution in Kurugama et al.; the inventory source and DEM in Abeysiriwardana & Wijesekera; whether the Thudawa ROC figure is genuine.
- Not exhaustively searched (Google Scholar was not accessible): Sri Lanka Journal of Geography, JNSF, iPURSE, Ruhuna and SAITM proceedings. More AHP/FR undergraduate- and conference-level studies probably exist there.

## 2. Hydrological and hydraulic modelling in Sri Lankan basins: which models, which basins, sub-daily inputs and small steep catchments

### Takeaway
The most-used tools are HEC-HMS (Kelani, Kalu, Deduru Oya, Nilwala, Attanagalu), HEC-RAS 1D/2D (lower Kelani, lower Kalu, Attanagalu), and the ICHARM RRI model (Kalu, Gin, Nilwala, Attanagalu, Mundeni; plus WEB-RRI). Other tools appear occasionally: MIKE 11/NAM/MIKE FLOOD (Gin, lower Kelani, Colombo), LISFLOOD-FP (Mundeni Aru), FLO-2D and iRIC (Kelani, Nilwala), SWAT (Nilwala, Mahaweli, Kelani), the Tank model (Nilwala) and ML/LSTM (Kelani, Kalu/Ratnapura, Deduru Oya, Mahaweli).

Almost all are basin-scale (hundreds to thousands of km²), mostly at daily resolution. Exceptions are a few event models with hourly data (Dhanapala et al. 2022 Nilwala/Pitabeddara, De Silva et al. 2014 Kelani events). No study was found that simulates event peaks with hourly data in a small (<~100–500 km²) steep upland catchment explicitly framed as flash flooding. No GR4J or TOPMODEL application to Sri Lanka was found.

### Cited Findings

#### HEC-HMS
- **De Silva, Weerakoon & Herath (2014).** "Modeling of Event and Continuous Flow Hydrographs with HEC-HMS: Case Study in the Kelani River Basin", *J. Hydrologic Engineering* 19(4): 800–806, DOI 10.1061/(ASCE)HE.1943-5584.0000846. — [Semantic Scholar](https://www.semanticscholar.org/paper/Modeling-of-Event-and-Continuous-Flow-Hydrographs-Silva-Weerakoon/5ae00035f0dfcb5b402a2167010c7270fb74f49b); [UNU](https://collections.unu.edu/view/UNU:1614)
  - **Events:** calibration on Nov 2005; validation on Apr–May 2008, May–Jun 2008 and May 2010.
  - **Methods:** Green-Ampt loss, Clark UH, recession baseflow; five-layer SMA for the continuous model.
  - **Validation:** average NSE 0.91 (event).
  - **Flag:** FF-partial. Event peaks, but large basin; time step not stated in abstract.
- **Kelani HEC-HMS long-term streamflow.** Daily rainfall from six stations; "fairly well" performance. **[Authors/venue unverified.]** — [ResearchGate](https://www.researchgate.net/publication/341479842_Application_of_HEC-HMS_model_to_simulate_long_term_streamflow_in_the_Kelani_River_Basin_Sri_Lanka)
  - **Flag:** FF-loose.
- **"River flow modeling in the Kelani River catchment".** HEC-HMS with initial/constant loss, Snyder UH and constant monthly baseflow; R² 0.7991 (calibration) / 0.8359 (validation). **[Authors/venue unverified.]** — [ResearchGate](https://www.researchgate.net/publication/376856813_RIVER_FLOW_MODELING_IN_THE_KELANI_RIVER_CATCHMENT_SRI_LANKA)
- **Kamburugamuwa, Netthikumara & Nandalal (2024).** "Application of HEC-HMS Model on Event-Based Simulation in Kalu Ganga (for Flood Prediction)". 2nd Int. Conf. on Engineering, Univ. of Jaffna; also listed in the Univ. of Sri Jayewardenepura FESympo. Conference paper. — [Jaffna PDF](https://www.eng.jfn.ac.lk/ice/wp-content/uploads/2024/11/Paper1.pdf); [SJP journals](https://journals.sjp.ac.lk/index.php/fesympo/article/view/8098)
  - **Catchment:** upper Kalu to Ellagawa.
  - **Data:** four rain gauges in Ratnapura district; Ellagawa discharge 2018–2021.
  - **Methods:** six method combinations tested; best was Initial-Constant + Clark UH + Recession + Muskingum.
  - **Validation:** NSE 0.98, RMSE 0.1.
  - **Flag:** FF-partial. Time step not stated.
- **Peradeniya repository: "Assessing flood prediction models for the Kalu Ganga Basin using HEC-HMS".** Likely a thesis or report **[details unverified]**. — [UoP IR](https://ir.lib.pdn.ac.lk/handle/20.500.14444/5912)
- **"Event Based Modeling of a Watershed Using HEC-HMS" (Engineer, ~2010).** Kalu Ganga; 4 and 10 sub-basin models; three gauging stations; four historical flood events; evaluated on peak flow, time to peak and NSE. — [SLJOL](https://engineer.sljol.info/articles/6979); [ResearchGate](https://www.researchgate.net/publication/303978597_Event_Based_Modeling_of_a_Watershed_Using_HEC-HMS)
  - **Flag:** FF-partial.
- **"A Diagnostic Application of HEC-HMS ... Ratnapura Watershed of Kalu Ganga".** Acceptable calibration, weaker verification. **[Authors/year unverified.]** — [ResearchGate](https://www.researchgate.net/publication/338365003_A_Diagnostic_Application_of_HEC-_HMS_Model_to_Evaluate_the_Potential_for_Water_Management_in_the_Ratnapura_Watershed_of_Kalu_Ganga_Sri_Lanka)
- **Sampath, Weerakoon & Herath (2014/2015).** HEC-HMS in Deduru Oya (2,620 km²) with intra-basin diversions; 19th IAHR-APD Congress (Hanoi 2014), plus an *Engineer* version. Average NSE 0.80. — [ResearchGate](https://www.researchgate.net/publication/273652903_HEC-HMS_Model_for_Runoff_Simulation_in_a_Tropical_Catchment_with_Intra-Basin_Diversions_Case_Study_of_the_Deduru_Oya_River_Basin_Sri_Lanka); [IAHR](https://iahr.org/library/info?pid=9863)
  - **Flag:** FF-loose.
- **Dhanapala, Gunarathna, Kumari, Ranagalage, Sakai & Meegastenna (2022).** "Towards Coupling of 1D and 2D Models for Flood Simulation — Nilwala River Basin", *Hydrology* 9(2): 17, DOI 10.3390/hydrology9020017. — [DOAJ](https://doaj.org/article/412e5ead5eff4c0ead3ead794c7fa3e4); [MDPI](https://www.mdpi.com/2306-5338/9/2/17)
  - **Methods:** HEC-HMS calibrated/validated with **hourly rainfall and streamflow** for three flood events, upper basin to Pitabeddara (reliable data lacking downstream); coupled with the iRIC 2D model.
  - **Validation:** May 2017 extent overall accuracy 81.5%; depth NSE 0.94 at the Tudawa gauge.
  - **Sensitivity:** loss parameters control the peak; transform/routing controls peak timing.
  - **Flag:** FF-partial. Hourly data and event peaks; the Pitabeddara sub-catchment is ~291–306 km², so near the small-catchment threshold, but it is framed as riverine flooding. Possibly the closest existing analogue to a flash-flood event model.
- **Wickramarachchi, W.C.P. (2019).** "A Study of Flood Forecasting and Mapping for the Attanagalu Oya". Conference paper; HEC-HMS + HEC-RAS; NSE 0.836 (calibration) / 0.825 (validation). — [ResearchGate](https://www.researchgate.net/publication/356839152_A_Study_of_Flood_Forecasting_and_Mapping_for_the_Attanagalu_Oya_Sri_Lanka)
- **Manjitha, H.H.U. & Perera, D.M.C.A. (2025, Univ. of Moratuwa).** HEC-HMS vs ANN/LSTM/RF/XGBoost in Kelani and Malwathu Oya. — [UoM DL](https://dl.lib.uom.lk/items/cd12cdb6-8061-4350-9f39-c28a99955c65); [UoM handle 123/24504](https://dl.lib.uom.lk/handle/123/24504)
  - **Kelani:** LSTM best (NSE 0.89, KGE 0.90).
  - **Malwathu Oya:** HEC-HMS NSE 0.49, PBIAS 15.82.
  - **Conflict:** the two repository versions give Kelani HEC-HMS NSE as 0.81 or 0.74.

#### HEC-RAS / FLO-2D / iRIC / other 2D (hydraulic)
- **Samarasinghe, Basnayaka, Gunathilake, Azamathulla & Rathnayake (2022).** "Comparing Combined 1D/2D and 2D Hydraulic Simulations Using High-Resolution Topographic Data: Lower Kelani", *Hydrology* 9: 39, DOI 10.3390/hydrology9020039. — [DOI](https://doi.org/10.3390/hydrology9020039); [SLIIT repo](https://rda.sliit.lk/handle/123456789/2619)
  - **Events:** HEC-RAS on the 2016 and 2018 floods, checked against observed and satellite inundation.
  - **Result:** the combined 1D/2D setup performed best.
- **Gunasekara, I.P.A.** "Flood Hazard Mapping in Lower Reach of Kelani River" (AIT Geoinformatics Center / Engineer). — [ResearchGate](https://www.researchgate.net/publication/311971739_Flood_Hazard_Mapping_in_Lower_Reach_of_Kelani_River); [AIT](https://geoinfo.ait.ac.th/flood-hazard-mapping-in-the-lower-reach-of-the-kelani-river-sri-lanka/)
  - **Method:** HEC-RAS 1D steady.
  - **Result:** extents of 60, 77 and 94 km² for 10-, 20- and 50-year floods.
- **"Flood inundations and risk mapping in a tidal river: Kelani".** HEC-HMS inflows + HEC-RAS combined 1D/2D. — [ResearchGate](https://www.researchgate.net/publication/352668374_Flood_inundations_and_risk_mapping_in_a_tidal_river_a_case_study_for_the_Kelani_River_basin_Sri_Lanka)
- **"Evaluation of topographic data sources for 2D flood modelling: Kelani basin".** Merges SRTM DEM and ASTER GDEM2 where reference data are lacking. **[Authors unverified.]** — [ResearchGate](https://www.researchgate.net/publication/347548103_Evaluation_of_topographic_data_sources_for_2D_flood_modelling_case_study_of_Kelani_basin_Sri_Lanka)
- **Lower Kelani event-based inundation under climate change.** HEC-HMS inflow at Hanwella feeding FLO-2D below Hanwella. — [Hilaris PDF](https://www.hilarispublisher.com/open-access/event-based-flood-inundation-mapping-under-the-impact-of-climatechange-a-case-study-in-lower-kelani-river-basin-sri-lanka-2157-7587-1000228.pdf)
- **"Floodplain Zoning and Mapping for Lower Kelani River" (Engineer).** NAM + MIKE 11 HD; NSE 0.766 (NAM) and 0.917 (coupled); time-to-peak critical in calibration. — [SLJOL PDF](https://engineer.sljol.info/articles/7594/files/66cd52bce3a03.pdf)
- **Lower Kalu: "Flood Inundation Modeling in the Lower Reach of the Kalu River".** HEC-HMS + HEC-RAS + satellite extents; hazard maps for 10, 20, 50 and 100-year floods. **[Authors/year unverified.]** — [Academia](https://www.academia.edu/31162376/Flood_Inundation_Modeling_in_the_Lower_Reach_of_the_Kalu_River_Sri_Lanka)

#### RRI (ICHARM) and WEB-RRI
- **Rasmy, Sayama & Koike (2019).** "Development of water and energy Budget-based Rainfall-Runoff-Inundation model (WEB-RRI) and its verification in the Kalu and Mundeni River Basins", *J. Hydrology* 579: 124163. Nash > 0.9 in calibration and validation; suited to real-time forecasting. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0022169419308984)
- **Herath, R.D. et al. (2024; online Oct 2023).** "Rainfall-runoff-inundation (RRI) model for Kalu River", *Modeling Earth Systems and Environment* 10: 1825, DOI 10.1007/s40808-023-01877-1. R² = 0.89, NSE = 0.86; IMERG underestimated peak discharge relative to gauges. **[Full author list unverified.]** — [ADS](https://ui.adsabs.harvard.edu/abs/2024MESE...10.1825H/abstract); [ResearchGate](https://www.researchgate.net/publication/374419844_Rainfall-runoff-inundation_RRI_model_for_Kalu_River_Sri_Lanka)
- **Herath, Pawar, Attanayaka & Rathnayake.** "Investigations of Multi-Platform Data for Developing an Integrated Flood Information System in the Kalu River Basin" (separate paper). — [ResearchGate](https://www.researchgate.net/publication/369396165_Investigations_of_Multi-Platform_Data_for_Developing_an_Integrated_Flood_Information_System_in_the_Kalu_River_Basin_Sri_Lanka)
- **Univ. of Moratuwa thesis: "Development of a rainfall-runoff-inundation model and flood monitoring system based on satellite imagery for Kalu Ganga basin".** Thesis. RRI vs Sentinel-1 SAR: modelled area 35.5% above the SAR area in 2016 and 22.1% above in 2017. — [UoM DL](https://dl.lib.uom.lk/items/ba1a558a-0629-4525-9cc4-39168c82935b)
- **ICHARM/GRIPS master's synopsis (2022, "Aruna").** Climate change impacts on extreme rainfall and floods in the Kalu basin using RRI; annual rainfall change 13–26%. Thesis. **[Full details unverified; PWRI host blocked.]** — [PWRI synopsis PDF](https://www.pwri.go.jp/icharm/training/master/img/2022/synopses/12_Aruna_synopsis.pdf)
- **ICHARM course synopses list.** Includes Sri Lankan theses on Metro Colombo inundation, climate change impacts on the Kelani basin, and Malwathu Oya water use. — [PWRI synopses](https://www.pwri.go.jp/icharm/training/master/img/synopses.pdf)
- **RRI for Attanagalu Oya.** Downstream extent matched satellite maps about 74%; under-predicts upstream and tributaries. **[Year (2016?) and authors unverified.]** — [ResearchGate](https://www.researchgate.net/publication/345156544_Rainfall-Runoff-Inundation_RRI_model_for_flood_analysis_in_Attanagalu_Oya_basin_Sri_Lanka)
- **Jayapadma, Souma, Magome, Wickramaarachchi & Ishidaira (2024).** "Integrated assessment of the impacts of climate and land-use changes on future flooding ... Gin River Basin", *J. Hydrology: Regional Studies* 55: 101919. — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2214581824002684); [DOAJ](https://doaj.org/article/7677f17eeedb47fdafb5153eafa9f315)
  - **Methods:** RRI driven by RCP4.5 bias-corrected GCMs.
  - **Projections:** high flows +16% upstream and +4% downstream; maximum inundation +3.5%.
  - **Related:** IAHS Proc. 386 (2024) Gin climate projection. — [PIAHS](https://piahs.copernicus.org/articles/386/33/2024/)
- **"The Effect of Incorporation of Embankment Information for Flood Simulation of the Gin River".** RRI. — [ResearchGate](https://www.researchgate.net/publication/359665274_The_Effect_of_Incorporation_of_Embankment_Information_for_Flood_Simulation_of_the_Gin_River_Sri_Lanka)
- **Nilwala RRI hazard-to-exposure with 30 m vs ~300 m settlement data (2025).** *J. Hydrology: Regional Studies*. Reasonable discharge and inundation accuracy, especially in the flat downstream sub-catchment. **[Authors unverified.]** — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2214581825007785)
- **Jayapadma, Souma, Wickramaarachchi, Magome & Ishidaira (2025).** ISHC2025 conference presentation on future flood exposure in the Gin and Nilwala using RRI. — [Confit](https://pub.confit.atlas.jp/en/event/ishc2025/presentation/33-19)
- **IWMI: RRI on Mundeni Aru** for flood depth/extent and reservoir design. — [PreventionWeb](https://www.preventionweb.net/news/sri-lanka-getting-ahead-disaster-risks)

#### MIKE / LISFLOOD-FP
- **Gin catchment (932 km²), MIKE 11 + MIKE 21 coupled in MIKE FLOOD.** Land-use-change flood impact; *Environmental Monitoring and Assessment* (2022). — [Springer](https://link.springer.com/article/10.1007/s10661-022-09986-7)
- **"Flood inundation modeling using MIKE FLOOD and remote sensing data".** 90 m SRTM bathymetry; validated against a 2001 satellite extent. Older paper. **[Basin and authors unverified in snippet.]** — [ResearchGate](https://www.researchgate.net/publication/236856278_Flood_inundation_modeling_using_MIKE_FLOOD_and_remote_sensing_data)
- **SLLDC (Colombo) operational model is MIKE 11.** Used as the benchmark in a 2025 Madiwela South Diversion study. — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2772741625000390) **[attribution approximate]**
- **LISFLOOD-FP, Mundeni Aru (2015).** *Proc. IAHS* 370: 131 (IWMI); basin-scale inundation checked against SAR. — [PIAHS](https://piahs.copernicus.org/articles/370/131/2015/); [IWMI](https://archive.iwmi.org/wle/modelling-flood-risk-extent-using-lisflood-fp-complex-watershed-case-study-mundeni-aru-river-basin/)

#### SWAT, Tank model and conceptual models
- **SWAT, upper Nilwala to Pitabeddara.** SWAT-CUP; NSE 0.72 (calibration) / 0.67 (validation), PBIAS −2.7% / 6.8%; best in mid flows. A related daily/monthly Pitabeddara study (306 km²) also exists. — [IJESD PDF](https://www.ijesd.org/vol16/IJESD-V16N2-1515.pdf) **[attribution to that PDF approximate]**
- **SWAT, selected Mahaweli catchments.** — [ResearchGate](https://www.researchgate.net/publication/355143647_Evaluation_of_the_Streamflow_Simulation_by_SWAT_Model_for_Selected_Catchments_in_Mahaweli_River_Basin_Sri_Lanka)
- **SWAT land-use/land-cover study** in a Sri Lankan tropical catchment. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S2352801X24001747)
- **Kelani, "Bridging data-driven and process-based approaches" (2025).** — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S259012302502047X)
  - **SWAT:** NSE 0.71 but PBIAS −23.67%.
  - **LSTM variants (monthly):** Bi-LSTM best in calibration, Stacked LSTM best in validation.
  - **Gap claim:** says no prior systematic LSTM vs physics-based comparison exists for the region.
- **Tank model (Sugawara, four-tank), Nilwala at Pitabeddara (291.4 km²).** *Engineer*. Daily 2008/09–2017/18; MRAE 0.31 (calibration) / 0.43 (validation). GR4J is mentioned only as an alternative. — [SLJOL PDF](https://engineer.sljol.info/articles/7489/files/submission/proof/7489-1-25727-1-10-20220607.pdf)
  - **Flag:** FF-loose. Daily.
- **GR4J and TOPMODEL:** no Sri Lankan application found.

#### ML / ANN / LSTM streamflow and flood forecasting
- **Saubhagya, Tilakaratne, Lakraj & Mammadov (2025).** "A Fusion of Deep Learning and Time Series Regression for Flood Forecasting: Ratnapura (Kalu)", *Forecasting* 7(2): 29. — [MDPI](https://www.mdpi.com/2571-9394/7/2/29); [UoC archive](https://archive.cmb.ac.lk/handle/70130/8585)
  - **Method:** Bi-LSTM + time-series regression.
  - **Data:** **daily** 2014–2020.
  - **Result:** 1–3-day-ahead actionable-flood accuracy of 80%, 80% and 100%.
  - **Operational context:** notes that the current real-time water level app gives only a few hours' warning.
  - **Flag:** FF-loose.
- **Gamage & Ilmini.** "Flood Forecasting Using ANN for Kalu Ganga", Springer book chapter (~2019). — [Springer](https://link.springer.com/chapter/10.1007/978-981-13-9129-3_7); [ResearchGate](https://www.researchgate.net/publication/331521514_Flood_forecasting_using_Artificial_Neural_Network_for_Kalu_Ganga)
- **Madhushanka, Jayasinghe & Rajapakse.** "Transformer & LSTM Based Models for Multi Day Ahead Flood Prediction in Tropical Climates". SSRN preprint; lower Mahaweli at Manampitiya; 1–3 day lead times. — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4746297)
- **"LSTM Modelling Approach for Flood Prediction: Deduru Oya" (~2020).** Conference paper. — [ResearchGate](https://www.researchgate.net/publication/363465237_Long_Short_Term_Memory_Modelling_Approach_for_Flood_Prediction_An_Application_in_Deduru_Oya_Basin_of_Sri_Lanka)
- **LSTM–XGBoost ensemble with IoT deployment** in a Sri Lankan basin. *Frontiers in AI* 2026. **[Basin and metrics unverified.]** — [Frontiers](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1903150/abstract)
- **Excluded:** Ikeuchi et al. (2025), "Development of Flash Flood Forecasting System for Small and Medium-Sized Rivers", *JFRM* 18(1): e70026. RRI + H–Q, MLIT/Japan-funded. Its study area could not be confirmed and it appears to be Japan, **not Sri Lanka**. — [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/jfr3.70026)

### Inferences
- **Hourly event modelling of steep upland catchments is unclaimed.** No Sri Lankan study was found that couples hourly or sub-hourly rainfall (gauge or IMERG/GSMaP half-hourly) with RRI or HEC-HMS in a <~300 km² steep upland catchment (e.g. Kalu tributaries above Ratnapura, Kelani upper tributaries at Kitulgala/Deraniyagala, Gin above Neluwa), with evaluation of peak magnitude/timing and lag time. Dhanapala et al. (2022) at Pitabeddara (~300 km², hourly) is the closest precedent and should be cited as the baseline.
- **RRI is well established in Sri Lanka** (Kalu, Gin, Nilwala, Attanagalu, Mundeni). RRI has been used for flash-flood reproduction in Japan (e.g. Kobayashi 2025 JFRM, Myohoujigawa — [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/jfr3.70076)), so a Sri Lankan flash-flood RRI study at fine grid and hourly step is a defensible, novel extension.
- **Satellite rainfall underestimates peaks.** IMERG underestimating peaks (Herath 2024) is relevant: any sub-daily satellite-forced flash-flood model needs bias correction.

### Gaps
- Not confirmed for most studies: DEM resolution, the exact model time step, and whether rainfall was hourly. Abstracts did not state these.
- Not checked: GRIPS/ICHARM thesis lists could not be fetched (PWRI host blocked). There are likely more Sri Lankan RRI theses (Kelani, Mahaweli, Deduru Oya).
- Not retrieved: JICA flood management planning reports for Kelani/Kalu/Gin/Nilwala (e.g. [JICA Part II](https://openjicareport.jica.go.jp/pdf/11931946_02.pdf)), which likely contain hydrological models and design floods.
- No Sri Lankan TOPMODEL, GR4J or HEC-RAS 2D rain-on-grid flash-flood study was found. This may be real absence or a search limitation.

## 3. Flood frequency analysis, design-flood guidance, rational method, and regional formulae

### Takeaway
At-site FFA in Sri Lanka exists only as a handful of conference or low-tier papers:
- Ratnapura/Kalu (L-moments, GEV best);
- Kelani six stations (PWM/L-moments) and Kelani bunds (Gumbel);
- one 2026 peer-reviewed FFA for ungauged Akuressa (Nilwala) using SWAT-simulated flows, AM and POT, and L-moments.

No regional FFA (index-flood, L-moment homogeneity tests, regional growth curves) for Sri Lankan discharge was found. No non-stationary FFA of discharge was found. Design practice for small catchments still rests on Ponrajah (1984) IDF curves and the Rational/SCS methods. The Irrigation Department reports an internal IDF update (2020/21), and academic regional IDF updates exist.

### Cited Findings

**At-site FFA**
- **Weerabangsa, Himanujahn, Iresh & Athapattu (2023).** "Flood Frequency Analysis for the Upper Kalu River Basin at Ratnapura", MERCon 2023 (IEEE). Conference paper. — [IEEE Xplore](https://ieeexplore.ieee.org/document/10355531/); [UoM DL](https://dl.lib.uom.lk/items/fc97237a-7880-4da2-8370-360ff61854c0)
  - **Data:** 44-year annual peak series.
  - **Method:** five distributions; L-moments parameter estimation; GEV best (L-moment ratio diagram).
  - **Trend tests:** no trend (Mann-Kendall, Levene).
  - **Result:** a "major flood" roughly once every three years.
  - **Claims:** no previous return-period estimates existed at Ratnapura, and GEV is proposed as a candidate for regional FFA in Sri Lanka.
- **"Flood Frequency Analysis for Kelani River Basin: Case Study in Sri Lanka".** PWM/L-moments at six gauges; 10/25/50/100-year floods; lag tests show Hanwella, Glencourse and Kithulgala as random series. **[Authors/venue unverified.]** — [Academia](https://www.academia.edu/40804290/Flood_Frequency_Analysis_for_Kelani_River_Basin_Case_Study_in_Sri_Lanka); [ResearchGate](https://www.researchgate.net/publication/365360047_Flood_Frequency_Analysis_for_Kelani_River_Basin_CaseStudy_in_Sri_Lanka)
- **"Flood Frequency Analysis for the Kelani River and the Design Flood for Kelani Flood Bunds".** Water levels 1960–2015; Gumbel best; gauges Glencourse, Hanwella and Nagalagam Street. **[Authors unverified.]** — [ResearchGate](https://www.researchgate.net/publication/327745195_Flood_Frequency_Analysis_for_the_Kelani_River_and_the_Design_Flood_for_Kelani_Flood_Bunds)
  - A snippet also reports falling trends at Glencourse and Kithulgala **[source attribution unclear]**.
- **Dissanayake, D.M.K.P. & Wickramaarachchi, T.N. (2026).** "Flood frequency assessment in the ungauged, flood-prone Akuressa city ... using SWAT-simulated streamflow", *Modeling Earth Systems and Environment* (published 28 July 2026). Peer-reviewed. — [Springer](https://link.springer.com/article/10.1007/s40808-026-02856-y)
  - **Context:** only two flow gauges in the Nilwala, leaving about 70% of the downstream area ungauged.
  - **Data:** regionalised SWAT flows for 2000–2020.
  - **Method:** AM and POT; L-moments; GEV, GL, GP, Log-logistic and Log-normal fitted; three-parameter distributions best (K-S test).
  - **Result:** 2003 peak (1114 m³/s) ≈ 250-year and 2017 peak (1253 m³/s) ≈ 333-year return periods (GEV-POT).
- **Return-period hazard mapping that embeds FFA:** lower Kalu (10–100-year) and lower Kelani (10/20/50-year, Gunasekara). — [Academia](https://www.academia.edu/31162376/Flood_Inundation_Modeling_in_the_Lower_Reach_of_the_Kalu_River_Sri_Lanka); [ResearchGate](https://www.researchgate.net/publication/311971739_Flood_Hazard_Mapping_in_Lower_Reach_of_Kelani_River)
- **Kelani POT flood characteristics:** Samarasinghe, Makumbura, Wickramarachchi, Sirisena, Gunathilake, Muttil, Teo & Rathnayake (2022), *Hydrology* 9(10): 177. Uses POT flood characteristics with LULC for 1988–2017 and finds rising flood intensity and frequency. — [DOI](https://doi.org/10.3390/hydrology9100177); [VU repository](https://vuir.vu.edu.au/46825/)

**Non-stationary analysis**
- No Sri Lankan non-stationary GEV or other FFA of discharge was found.
- The nearest work is rainfall-trend work. A national 1975–2025 analysis reports annual maximum 1-day rainfall rising 12.2 mm/decade (Mann-Kendall, Pettitt). — [Springer, Discover Geoscience](https://link.springer.com/article/10.1007/s44288-026-00545-y)
- The Ratnapura AMS showed no trend. — [IEEE](https://ieeexplore.ieee.org/document/10355531/)

**Design-flood guidance, rational method and IDF**
- **Ponrajah, A.J.P. (1984).** *Design of Irrigation Headworks for Small Catchments*, Irrigation Department. — [UoM library catalogue](https://opac.lib.uom.lk/cgi-bin/koha/opac-detail.pl?biblionumber=139215&shelfbrowse_itemnumber=126320); [Scribd copy](https://www.scribd.com/document/453676436/Design-of-Irrigation-Headworks-for-Small-Catchments); [ResearchGate (Colombo IDF paper)](https://www.researchgate.net/publication/328381427_Development_of_Rainfall_Intensity-Duration-Frequency_IDF_Curves_for_Colombo_Sri_Lanka)
  - **Content:** island-wide IDF curves in six climatic zones; recommends slope-based velocity for time of concentration.
  - **Scope:** the Ponrajah method and the Rational Method are intended for catchments under about 25 km².
- **Wijesinghe, W.M.D. & Wijesekera, N.T.S. (2011).** "Comparison of Rational Formula Alternatives for Streamflow Generation for Small Ungauged Catchments", *Engineer* 44(4): 29–36, DOI 10.4038/engineer.v44i4.6955. — [SLJOL](https://engineer.sljol.info/articles/10.4038/engineer.v44i4.6955); [Semantic Scholar PDF](https://pdfs.semanticscholar.org/835f/583295af0060f218583004d51b379d235c2f.pdf)
  - **Basin:** Welipenna (Kalu sub-basin).
  - **Result:** lumped Qp 0.49 m³/s vs distributed 0.51 m³/s.
  - **Finding:** the choice of runoff-coefficient guideline causes large variation; Kirpich and Bransby-Williams Tc gave higher design floods.
- **Irrigation Department paper: "Estimation of Direct Runoff and Flow Hydrographs in Small Un-gauged Catchments".** SCS-CN + unit hydrograph worked example; requires IDF curves. — [ResearchGate](https://www.researchgate.net/publication/328578090_Estimation_of_Direct_Runoff_and_Flow_Hydrographs_in_Small_Un-gauged_Catchments)
- **Irrigation Department Hydrological Annual 2020/21.** Reports updating IDF curves, iso-yield curves, probability rainfalls and "Cp, Ct values for 15 Hydrometric Stations" (Snyder UH parameters) as part of a design-guideline revision. **Formal adoption is unconfirmed.** — [Irrigation Dept PDF](https://www.irrigation.gov.lk/web/images/Publications/Hydrologyical_Annual_2020-21.pdf)
- **Academic IDF updates:**
  - Regional IDF from cluster analysis + regional frequency analysis: 11 homogeneous regions (ASCE *J. Hydrologic Engineering*). — [ASCE](https://ascelibrary.org/doi/10.1061/JHYEFF.HEENG-6167)
  - Satellite-based IDF: 50 station curves from gauges plus three satellite products, 1990–2019, using **daily** data. — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2666016424001075)
  - Colombo IDF: 15-min to 24-h, 30-year record, intensities increasing. — [ResearchGate](https://www.researchgate.net/publication/328381427_Development_of_Rainfall_Intensity-Duration-Frequency_IDF_Curves_for_Colombo_Sri_Lanka)
  - Future regional IDF. — [LIDSEN AEER](https://www.lidsen.com/journals/aeer/aeer-07-03-031)
  - Early rainfall depth-duration-frequency study for Sri Lanka, *J. Hydrology* 1978. **[Authors unverified; likely Baghirathan & Shaw.]** — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/0022169478900185)
- **Regional discharge formulae for ungauged small catchments:** no published Sri Lanka-specific regional peak-discharge regression or index-flood growth curve was found. — search summary (see [IWA review, general](https://iwaponline.com/jwcc/article/doi/10.2166/wcc.2025.153/110076/Peak-discharge-estimation-for-ungauged-basins-a))

### Inferences
- **Regional and non-stationary FFA are open.** A regional L-moment FFA (Hosking-Wallis discordancy/heterogeneity, index-flood with catchment-descriptor regression) for Sri Lankan wet-zone gauges is apparently unpublished. Non-stationary FFA conditioned on rainfall or land use is also open, as is a test of Ponrajah 1984 / Rational / SCS against observed peaks in small steep catchments.
- **Sub-daily design rainfall is missing.** Most IDF updates use daily data. Sub-daily design rainfall for small upland catchments (Tc under a few hours) remains weakly supported, so a flash-flood design storm or IDF study would fill a design need.

### Gaps
- Not verified: authors and venues of the two Kelani FFA papers. The JICA design flood estimates for the Kelani, Kalu, Gin and Nilwala could not be retrieved.
- No access to: the Irrigation Department's updated (post-2020) guideline document, and whether it supersedes Ponrajah 1984.

## 4. Studies explicitly defining or characterising flash floods in Sri Lanka (2003 Ratnapura, May 2016, Aranayake 2016, May 2017; Ditwah excluded)

### Takeaway
No peer-reviewed study was found that formally defines Sri Lankan flash floods or characterises them hydrologically (rainfall intensity–duration thresholds, lag times, unit peak discharge, catchment flashiness). "Flash flood" appears loosely:
- in the May 2017 PDNA;
- in the Thudawa AHP paper;
- in 2024 media/OCHA reports.

Aranayake 2016 is studied as a rain-triggered landslide, not a flood. The May 2003 Ratnapura/Kalu event is described mainly through return-period rainfall and stage data.

### Cited Findings
- **May 2003 (Kalu/Ratnapura):** observed rainfall at Ratnapura was 446 mm/3 days and 345 mm/day, about a 40-year return period (JICA). — [JICA DRR data collection survey](https://openjicareport.jica.go.jp/pdf/12291944.pdf)
  - **Ratnapura stage classes:** normal 18.3 m, minor 20.1 m, major 21.3 m, critical 24.4 m MSL.
  - **Impact:** the 2003 flood caused 122 deaths and Rs 11.4 bn damage.
  - **[Stage/impact source attribution uncertain: from a ResearchGate table on Ratnapura/Putupaula flood levels.]** — [ResearchGate](https://www.researchgate.net/figure/Flood-levels-at-Putupaula-for-different-floods-observed-at-Ratnapura_tbl1_230540578)
- **Zubair (2004)**, *Natural Hazards* 33(3): 303–318. Links a major flood to a stalled cyclone and orographic rainfall and argues for local NWP-based warnings. **[Exact title unverified.]** — [IDEAS/RePEc](https://ideas.repec.org/a/spr/nathaz/v33y2004i3p303-318.html)
- **May 2016 (Kelani):** 350 mm fell in two days (15–16 May); the extent peaked 18 May, driven by runoff from upland areas covering two-thirds of the catchment (rapid emergency mapping). — [ResearchGate](https://www.researchgate.net/publication/311303566_RAPID_EMERGENCY_RESPONSE_MAPPING_FOR_THE_2016_FLOODS_IN_KELANI_RIVER_BASIN_SRI_LANKA)
  - Sentinel Asia/IWMI RISAT-1 mapping gave about 2,343 km² maximum inundation (18 May 2016). — [Sentinel Asia PDF](https://sentinel-asia.org/EO/2016/article20160515LK/15May2016_Sri_Lanka_Flood_after_Product-IWMI(PDF)_19May2016_004.pdf)
- **Aranayake, 17 May 2016 (Kegalle):** treated as a rapid long-runout landslide, not a flash flood.
  - Dang et al. (2019), *Landslides*: ring-shear tests; 127 killed. — [Springer](https://link.springer.com/article/10.1007/s10346-018-1089-7)
  - Tan et al. (2020): LS-RAPID hazard. — [Springer](https://link.springer.com/article/10.1007/s10346-020-01419-1)
  - **Rainfall:** reported as about 435 mm over 72 h or 446.5 mm over 3 days (sources differ).
  - **Socio-economic impacts** study. — [Springer](https://link.springer.com/article/10.1186/s40677-018-0104-6)
- **May 2017 PDNA (GoSL/GFDRR):** up to 600 mm in two days (25–26 May) caused "flash floods and landslides" in 15 of 25 districts; in places water stood up to 6 m for 4–10 days. That duration is riverine, not flash. — [GFDRR PDNA](https://www.gfdrr.org/sites/default/files/publication/sri%20lanka%20v11%20LOW.pdf)
  - **Nilwala May 2017 studies:**
    - Sentinel-2 mapping: 46 of 109 km² inundated. — [Springer, SWRM 2024](https://link.springer.com/article/10.1007/s40899-024-01133-z)
    - Dhanapala et al. 2022 (HEC-HMS/iRIC validation on May 2017). — [MDPI](https://www.mdpi.com/2306-5338/9/2/17)
    - Extreme rainfall and flood events analysis, Nilwala (TARE). — [SLJOL TARE](https://tare.sljol.info/articles/10.4038/tare.v29i2.5829)
  - Coastal flood disaster May 2017. *J. Coastal Research* SI85. — [BioOne](https://bioone.org/journals/journal-of-coastal-research/volume-85/issue-sp1/SI85-296.1/Coastal-Flood-Disaster-in-Sri-Lanka-May-2017--Exploring/10.2112/SI85-296.1.pdf)
- **Tillekaratne, Jayawardena, Basnayaka, Rathnayake, Werellagama, Herath, Nianthi, Madduma-Bandara & Bandara (2023).** "Hydro-Meteorological Disaster Incidents and Associated Weather Systems in Sri Lanka". Catalogue for 1907–2019; most disasters occur in the SW monsoon; Bay of Bengal depressions Oct–Jan. Journal ISEIS-linked **[journal name unverified]**. — [UTwente](https://research.utwente.nl/en/publications/hydro-meteorological-disaster-incidents-and-associated-weather-sy/); [ResearchGate](https://www.researchgate.net/publication/374536269_Hydro-meteorological_disaster_incidents_and_associated_weather_systems_in_Sri_Lanka)
- **Local pluvial/short-burst flooding, Mavadippalli (Eastern Province):** "Causes and impacts of flood inundation". Not a hydrological analysis. — [ResearchGate](https://www.researchgate.net/publication/377701429_Causes_and_impacts_of_flood_inundation_a_case_study_based_on_Mavadippalli_Sri_Lanka)

### Inferences
- **The definitional gap looks real.** Defining and characterising Sri Lankan flash floods is genuinely open. A study could combine sub-daily gauge and IMERG data, small-catchment response times, unit peak discharge and event dating from DesInventar. Cite the May 2003, 2016 and 2017 events as precedents, but note that published analyses treat them as monsoon riverine and landslide events.

### Gaps
- Not checked: Department of Meteorology technical reports (e.g. the "Synoptic and Mesoscale Background" PDF at meteo.gov.lk), and NBRO landslide/flash-flood early-warning thresholds, which may contain rainfall thresholds relevant to flash floods.

## 5. Review papers summarising Sri Lankan flood research

### Takeaway
There are only a few broad reviews. They cover hazard and risk management or disaster statistics rather than a systematic review of flood mapping and modelling methods. A systematic methods review (susceptibility + modelling + FFA) for Sri Lanka appears absent.

### Cited Findings
- **"A Review of Flood Hazard and Risk Management Strategies, Past, Present, and Future Challenges in the South Asian Region, Particularly in Sri Lanka".** **[Authors/venue/year unverified; ~2022.]** — [ResearchGate](https://www.researchgate.net/publication/364087147_A_Review_of_Flood_Hazard_and_Risk_Management_Strategies_Past_Present_and_Future_Challenges_in_the_South_Asian_Region_Particularly_in_Sri_Lanka)
- **"Analysis and risk evolution of floods and cyclones in Sri Lanka from 1975 to 2025 towards resilient strategies"** (Springer *Discover Geoscience*, 2026). Mann-Kendall/Pettitt trends; names Mahaweli, Kelani, Kalu, Gin, Deduru Oya and Nilwala as priority basins; discusses a "last-mile" governance gap. Its 2025 window may include Ditwah, so use it only for pre-Ditwah trends. — [Springer](https://link.springer.com/article/10.1007/s44288-026-00545-y)
- **"Natural hazards and population impact in Sri Lanka, 2010–2025"** (PMC). — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13465857/)
- **Tillekaratne et al. (2023):** hydro-meteorological disaster catalogue 1907–2019. — [UTwente](https://research.utwente.nl/en/publications/hydro-meteorological-disaster-incidents-and-associated-weather-sy/)
- **Gap statements inside primary papers:**
  - Kurugama et al. 2024 on scarce ML-FSM. — [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1111/jfr3.12980)
  - The Kelani "Bridging" paper on the lack of LSTM vs physics-based comparisons. — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S259012302502047X)
  - Weerabangsa et al. 2023 on no prior FFA at Ratnapura. — [IEEE](https://ieeexplore.ieee.org/document/10355531/)

### Inferences
- **A methods review would itself be a contribution.** A structured review (PRISMA-style) of Sri Lankan flood susceptibility, modelling and FFA, with the flash-flood flag used here, would be a publishable contribution and a useful companion to a flash-flood study.

### Gaps
- Not identified: authors and venue of the South Asia/Sri Lanka review.
- Unknown: whether reviews exist in *Sri Lanka Journal of Geography*, *JNSF* or *Engineer*. Those venues could not be searched directly.
