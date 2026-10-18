# Sri Lanka: Flood Early Warning, Rainfall Thresholds, Satellite Rainfall, Sub-daily/IDF, Catchment Response and Data Availability (FLASH flood relevance)

Research notes compiled 2026-10-18. Scope: Sri Lanka only (South Asia programmes only where SL is a member). Cyclone Ditwah (Nov 2025) excluded entirely. Method note: direct page fetches (MDPI, Springer, Wiley, HRC, PWRI) were blocked by the network proxy in this session, so most findings rest on search-engine extractions of abstracts/snippets of the cited pages. Numeric values should be checked against full texts before being quoted in a final manuscript; items flagged "[unverified]" especially so.

## 1. Early warning: institutions, systems, projects and verification

### Takeaway
Operational flood warning in Sri Lanka is river-stage based (Irrigation Department, gauge thresholds "Alert / Minor flood / Major flood", disseminated with DMC), rainfall warnings are colour-coded quantitative advisories from the Department of Meteorology (DoM), and landslide warnings come from NBRO's rain-gauge thresholds. There is no Sri Lanka-specific, operational, verified flash-flood warning product: SAsiaFFGS (WMO/HRC, regional centre IMD) includes Sri Lanka, but the only Sri Lankan evaluation found is a qualitative 2018 newsletter case study; JAXA/ICHARM Kalu Ganga GSMaP-RRI work is a prototype/research system with published (not operationally verified) skill.

### Cited Findings
**Irrigation Department (ID) – Hydrology & Disaster Management Division**
- The Division's listed functions include monitoring, flood forecasting and early warning for major river basins, and developing/updating rating curves for permanent and peripheral gauging stations; the ID site states there are 42 permanent gauging stations recording river water level and rainfall hourly — [ID Hydrology & Disaster Management page](https://www.irrigation.gov.lk/web/index.php?option=com_content&view=article&id=27&Itemid=128&lang=en)
- ID warnings are station-threshold based with three tiers (Alert, Minor Flood, Major Flood); a third-party real-time monitor republishing ID data lists e.g. Thalgahagoda 1.4/1.7/2.8 m and Ellagawa 10.0/10.7/12.2 m (Alert/Minor/Major) [third-party; verify against ID] — [Realtime Water Level Monitor](https://rivermonitorsl.homerelieflk.org/); also [RISE Sri Lanka gauges](https://risesrilanka.org/gauges)
- Warning issuance logic as reported in recent bulletins: based on rainfall in upper/middle catchment and water levels at basin gauges; lead time framed as "next 24/48 hours" (e.g. Kelani minor-flood warning "may develop over the next 48 hours"; major-flood warning for next 24 h on 3 Aug 2026) — [NewsFirst, 3 Aug 2026](https://www.newsfirst.lk/2026/08/03/major-flood-warning-issued-for-kelani-river-areas); [Ada Derana](https://adaderana.lk/news/cms9qz9a40003356q906rv48p)
- Example: ID minor flood warning for Nilwala basin issued 15 Oct 2026 18:00, extended 48 h to 18 Oct 2026, covering Akuressa, Athuraliya, Malimbada, Kamburupitiya, Thihagoda, Matara divisions — [Ada Derana](https://adaderana.lk/news/250034); [Ada Derana extension](https://adaderana.lk/news/250077); [Newswire 15 Oct 2026](https://www.newswire.lk/2026/10/15/irrigation-department-issues-amber-flood-warning-for-nilwala-river-basin/)
- DMC republishes numbered ID flood warnings and periodic river water-level/rainfall bulletins (e.g. "Flood warning Kelani River – No 04, 2026-08-03 15:30") — [DMC River Water Level and Flood Warning reports](https://www.dmc.gov.lk/index.php?option=com_dmcreports&view=reports&Itemid=277&limit=0&report_type_id=6&lang=en); ID's own warning archive — [ID Flood Warning](https://www.irrigation.gov.lk/web/index.php?option=com_content&view=category&layout=blog&id=35&Itemid=260&lang=en)
- Third-party scraping/visualisation of DMC/ID bulletins exists (e.g. GitHub nuuuwan/lk_dmc_vis) — [GitHub lk_dmc_vis](https://github.com/nuuuwan/lk_dmc_vis)
- A World Bank/GFDRR hydromet review found ID's Hydrology Division flood warning service needed ready access to real-time data and short-range precipitation forecasts — [GFDRR Sri Lanka Hydromet Roadmap](https://www.gfdrr.org/sites/default/files/publication/Sri%20Lanka%20Hydromet%20Roadmap.pdf)

**Department of Meteorology (DoM)**
- DoM issues colour-coded rainfall warnings: Red = "take action" level for heavy rain >100 mm at some places (12 Oct 2026); Amber advisories for >100 mm (15 Oct 2026) — [Newswire 12 Oct 2026](https://www.newswire.lk/2026/10/12/red-alert-for-heavy-rain-in-several-parts-of-sri-lanka-on-tuesday/); [NewsNow 15 Oct 2026](https://english.newsnow.lk/2026/10/15/amber-alert-issued-for-heavy-rainfall-exceeding-100-mm-in-several-areas/)
- Conflicting report: an Amber alert for >150 mm (17 Oct 2026) — [Lanka Newspapers 17 Oct 2026](https://www.lankanewspapers.com/2026/10/17/amber-weather-alert-heavy-rainfall-warning-issued-for-six-districts-across-sri-lanka); official tier definitions (amounts vs colours) not found on meteo.gov.lk in this search [unverified].
- GFDRR review: "without accurate, high-resolution gridded rainfall information, it is impossible for the DoM to provide adequate forecasts and warnings of the likelihood of flash floods"; it recommended WMO-linked products such as (Global) Flash Flood Guidance — [GFDRR Hydromet Roadmap](https://www.gfdrr.org/sites/default/files/publication/Sri%20Lanka%20Hydromet%20Roadmap.pdf). Review also notes DoM 10-min AWS data judged unsuitable for climate use (instrumentation concerns) but useful for severe-weather monitoring; much historical record on paper — same source.

**SAsiaFFGS (WMO / Hydrologic Research Center, funded USAID/BHA, NOAA satellite data)**
- Members: Bangladesh, Bhutan, India, Nepal, Sri Lanka; IMD is Regional Centre; officially launched October 2020 — [ReliefWeb: SAsiaFFGS launched](https://reliefweb.int/report/india/south-asia-flash-flood-guidance-system-launched); [Meteorological Technology International](https://www.meteorologicaltechnologyinternational.com/news/climate-measurement/flash-flood-warning-system-for-south-asia-launched.html); [YouTube launch Oct 2020](https://www.youtube.com/watch?v=w-Kra-5pqNQ)
- An earlier SAsiaFFG version reportedly shut down after ~1.5 years due to lack of regional collaboration, then re-established — [BYJU's summary (secondary)](https://byjus.com/free-ias-prep/south-asian-flash-flood-guidance-system-sasiaffg/)
- HRC FFG Gazette (2018, vol 8 issue 1) carries an article by a Sri Lanka DoM meteorologist reporting that SAsiaFFG products captured flash flood events in SW and W Sri Lanka during May 2018 — qualitative case study, no skill statistics retrieved — [HRC FFG Gazette 2018](https://www.hrcwater.org/wp-content/uploads/2018/08/FFG-Gazette_01-08-18_FINAL.pdf)
- 2021 FFG Gazette lists Sri Lanka representation at the launch / hydrometeorologist online training — [HRC FFG Gazette 2021](https://www.hrcwater.org/wp-content/uploads/2021/11/FFG-Gazette_v10_20210520.pdf)

**JAXA / ICHARM / JICA – Kalu Ganga**
- JAXA SAFE prototyping project with Dept of Irrigation (from Dec 2015): objective "development and implementation of an advanced operational prototype system for flood forecasting and early warning by utilizing near-real time in-situ and satellite (GSMaP) observations and rainfall-runoff-inundation models", including GSMaP bias-correction and ID capacity building — [JAXA SAFE Sri Lanka 201512](https://www.eorc.jaxa.jp/SAFE/prototyping/lineup/lka/201512/index.html)
- ICHARM report to Sentinel Asia (2017) lists 2016 GSMaP bias-correction training for ID and Kalu work as ongoing — [ICHARM report JPTM 2017](https://sentinel-asia.org/meetings/SA3JPTM4/agenda/JPTM2017_Day1_PDF/4.1_ICHARM_Report_to_WRD_WG_in_JPTM_2017_in_Hanoi.pdf)
- Integrated flood information system study (Water 2023, Kalu basin): GSMaP-NOW (real time) and GSMaP-NRT detect heavy rain well; merging real-time gauges with GSMaP "significantly improved" rainfall intensity/distribution, flood onset and peak discharge; GSMaP-NRT outperformed GSMaP-NOW; minimum gauge count for bias correction depends on rainfall distribution and basin size — [Water 2023, 15(6):1199](https://doi.org/10.3390/w15061199)
- Kalu basin lead time reported ≈19.5 h considering travel time and GSMaP latency [source is an academia.edu upload; verify] — [academia.edu Kalu River Basin](https://www.academia.edu/87342734/For_Kalu_River_Basin_in_Sri_Lanka)
- UoM thesis: RRI model + satellite flood monitoring for Kalu Ganga; flooded-area estimates for 2016 and 2017 events with accuracy ~25–30% judged acceptable for evacuation/rapid damage assessment — [UoM DL thesis](https://dl.lib.uom.lk/items/ba1a558a-0629-4525-9cc4-39168c82935b)
- Earlier bias-correction/downscaling paper (c. 2014–15): GSMaP_MVK score comparable to CMORPH and 3B42RT — [ResearchGate](https://www.researchgate.net/publication/272263340_Application_of_bias-correction_and_downscaling_method_to_Kalu_Ganga_basin_in_Sri_Lanka)
- JICA flood management planning for Kelani, Kalu, Gin and Nilwala rivers (Part II) — [JICA open report 11931946_02](https://openjicareport.jica.go.jp/pdf/11931946_02.pdf); JICA data collection surveys on disaster management — [JICA 12111894](https://openjicareport.jica.go.jp/pdf/12111894.pdf); [JICA 12291944](https://openjicareport.jica.go.jp/pdf/12291944.pdf). JICA survey found inter-agency sharing of observed hydromet data "inadequate" — [JICA 12291944](https://openjicareport.jica.go.jp/pdf/12291944.pdf)

**World Bank / AIIB CRIP and HMIS**
- CRIP (Climate Resilience Improvement Project) ICR: secured DoM hydromet data free of charge to ID, DMC and NBRO (previously paid) — [World Bank ICR00005564](https://documents1.worldbank.org/curated/en/418431641855234812/pdf/Sri-Lanka-Improving-Climate-Resilience-Project.pdf)
- CRIP Phase II (AIIB co-financed; Climate Resilience Multiphase Programmatic Approach) aims to strengthen DoM, ID, DMC, NBRO forecasting/early warning, focusing on Kelani and possibly Mundeni Aru basins — [AIIB/EWS summary](https://ewsdata.rightsindevelopment.org/projects/000036-sri-lanka-climate-resilience-improvement-project/); [World Bank PAD2176](https://documents1.worldbank.org/curated/en/273601561773732352/pdf/Sri-Lanka-Climate-Resilience-Multiphase-Programmatic-Approach-Project.pdf)
- Integrated Watershed & Water Resources Management Project (PAD3190) plans to expand the HMIS network with 120 new stations providing real-time hydrometric data to ID and Mahaweli Authority with a central monitoring centre — [World Bank PAD3190](https://documents1.worldbank.org/curated/en/890311590112957289/pdf/Sri-Lanka-Integrated-Watershed-and-Water-Resources-Management-Project.pdf). A vendor case study describes telemetry work under CRiP — [Geosense CRiP case study](https://www.geosense.com/case-studies/crip-climate-resilience-improvement-project/)

**NBRO landslide early warning (analogue for rainfall-threshold warning)**
- Regional landslide EWS operating since 2007 with Watch / Alert / Evacuation levels at 75 / 100 / 150 mm per day (or 75 mm/h for evacuation), using an automated network of ~325 rain gauges in landslide-prone areas — [Springer chapter 2023, Early Warning System Against Rainfall-Induced Landslide in Sri Lanka](https://link.springer.com/chapter/10.1007/978-3-031-16898-7_16); [ResearchGate copy](https://www.researchgate.net/publication/367034388_Early_Warning_System_Against_Rainfall-Induced_Landslide_in_Sri_Lanka)
- NBRO issues district/DS-division warnings during heavy rain (dissemination via media/DMC) — [OnLanka](https://www.onlanka.com/news/heavy-rain-landslide-warnings-issued-for-six-districts-in-sri-lanka.html); NBRO overview — [NBRO GR.pdf](https://nbri.gov.lk/images/GR.pdf)
- SATREPS project RRLL (IPL-249; JICA/JST with NBRO) on early warning for rain-induced rapid long-travelling landslides; hourly GSMaP compared to gauges and high-res MSSG simulation: MSSG matched gauge 3-day accumulations and hourly maxima better than GSMaP — [Springer chapter: Local Rainfall Predictions for Operational Landslide EW](https://link.springer.com/chapter/10.1007/978-3-032-18863-2_6); [RRLL achievements chapter](https://link.springer.com/chapter/10.1007/978-3-032-18863-2_12); [High-Resolution Rainfall Simulations chapter](https://link.springer.com/chapter/10.1007/978-3-031-72736-8_10)

### Inferences
- The warning chain is hazard-siloed: stage-based riverine flood (ID), rainfall-amount (DoM), landslide (NBRO). Flash flooding of small, ungauged steep catchments falls between them; only SAsiaFFGS conceptually addresses it, and no quantitative SL verification of SAsiaFFGS was found.
- ID warnings at 24–48 h lead with gauge thresholds suit large wet-zone rivers (Kelani, Kalu, Gin, Nilwala), not catchments with lag of a few hours.
- Kalu Ganga GSMaP-RRI is the most mature satellite-driven forecasting work but remains documented as prototype/research; operational adoption status at ID is not confirmed.

### Gaps
- No published POD/FAR/CSI verification of SAsiaFFGS for Sri Lanka; current (2024–2026) DoM use of SAsiaFFGS unknown (direct HRC/WMO pages unreachable).
- Whether the 120 HMIS stations were installed/transmitting, and whether HMIS data are publicly accessible, unverified.
- No published verification statistics for ID flood warnings (hit/miss/false alarms) found.
- Official DoM colour-tier amount definitions (100 vs 150 mm) unconfirmed.
- Whether NBRO's 2007 thresholds have been formally revised (e.g. after SATREPS) not confirmed.

## 2. Rainfall thresholds (flood / flash flood / landslide analogues)

### Takeaway
No published, operational rainfall threshold for floods or flash floods in Sri Lanka was found. The established analogue is NBRO's landslide threshold scheme (75/100/150 mm/day; 75 mm/h), plus research I–D thresholds (Badulla; a national I–D curve), and a Matara study showing antecedent multi-day rainfall matters.

### Cited Findings
- NBRO generalized national thresholds: 75 mm/24 h (watch), 100 mm/24 h (alert), 150 mm/24 h or 75 mm/h (evacuation) — [Springer 2023 chapter](https://link.springer.com/chapter/10.1007/978-3-031-16898-7_16); [Recommending Rainfall Thresholds for Landslides in Sri Lanka (ResearchGate)](https://www.researchgate.net/publication/317806492_Recommending_Rainfall_Thresholds_for_Landslides_in_Sri_Lanka)
- "Recommending Rainfall Thresholds" proposes a national I–D threshold I = 14.02 D^−0.30 and a Badulla district threshold, compared with Caine (1980), using rainfall associated with "325 landslides 1999–2018" [unverified: the ResearchGate ID suggests a 2017 upload, inconsistent with a 1999–2018 dataset; the "325" may be conflated with the 325 rain gauges — check full text] — [ResearchGate 317806492](https://www.researchgate.net/publication/317806492_Recommending_Rainfall_Thresholds_for_Landslides_in_Sri_Lanka)
- Badulla I–D threshold (Perera, Jayawardana, Jayasinghe 2017, J. Geoscience & Environment Protection 5:135–152): 44 landslide-triggering events (1986–2014), power-law I = α D^−β; short (<2 h) events >54 mm/h and long (>8 h) events <25 mm/h can trigger; most events in NE monsoon and inter-monsoon; SL thresholds "fairly higher" than global — [JGEP 2017 PDF (NBRO host)](https://nbri.gov.lk/images/GEP_2017122214344045.pdf); [SCIRP](https://www.scirp.org/journal/paperinformation?paperid=81276); [ResearchGate](https://www.researchgate.net/publication/322003238_A_Rainfall_Intensity-Duration_Threshold_for_Mass_Movement_in_Badulla_Sri_Lanka)
- A related study proposes hourly thresholds from 12 h pre-event rainfall, arguing short extreme bursts trigger more disastrous landslides — [ResearchGate 317806492](https://www.researchgate.net/publication/317806492_Recommending_Rainfall_Thresholds_for_Landslides_in_Sri_Lanka)
- Matara district (IJDRR 2020/21): NBRO uses generalized national thresholds based only on hourly and 1-day cumulative rainfall, ignoring antecedent rainfall and location; multi-day rainfall significant in Matara — [ScienceDirect S2212420920314461](https://www.sciencedirect.com/science/article/abs/pii/S2212420920314461)
- Kegalle: only a geospatial landslide risk framework (2020) found, no I–D threshold — [Springer MESE 2020](https://link.springer.com/article/10.1007/s40808-020-00811-z). Ratnapura, Nuwara Eliya: no threshold study found.
- No flash-flood threshold for urban Colombo found; nearest are Colombo IDF curves (see §4) — [ResearchGate Colombo IDF](https://www.researchgate.net/publication/328381427_Development_of_Rainfall_Intensity-Duration-Frequency_IDF_Curves_for_Colombo_Sri_Lanka)
- A 2026 flood/cyclone risk-evolution study (1975–2025) reports frequency of events exceeding 100 mm/24 h doubled between the 1975–1990 baseline and the later period [snippet-level] — [Springer Discover 2026, s44288-026-00545-y](https://link.springer.com/article/10.1007/s44288-026-00545-y)

### Inferences
- The 100 mm/24 h value recurs across DoM Red/Amber advisories, NBRO "alert", and climate-trend studies — a de facto heavy-rain benchmark but never validated against flood/flash-flood occurrence.
- Landslide I–D methodology (event catalogue + gauge hyetograph + power-law lower envelope) is directly transferable to flash-flood thresholds, provided a flash-flood event inventory (e.g. DesInventar) is paired with sub-daily rainfall.

### Gaps
- No Sri Lankan flash-flood rainfall threshold (I–D, cumulative, or FFG-type) in peer-reviewed literature found.
- No skill evaluation (POD/FAR) of NBRO thresholds found.

## 3. Satellite and reanalysis rainfall evaluation

### Takeaway
Sri Lankan evaluations are mostly daily/monthly and consistently rank IMERG best overall, with degraded skill in the dry zone and strong negative bias in the wet zone/complex terrain; GSMaP has been bias-corrected for Kalu Ganga flood forecasting; truly sub-daily gauge-based evaluation is rare because quality-controlled hourly gauge data are scarce.

### Cited Findings
- Perera, Senaratne, Gunathilake, Rathnayake (2022, Climate 10:156): six SRPs (incl. IMERG, TRMM-3B42/3B42RT, PERSIANN, PERSIANN-CDR, PERSIANN-CCS) vs >15 years of gauge data in Malwathu (dry), Deduru (intermediate), Kalu (wet) basins; IMERG best on CSI, FAR, PC; PERSIANN-CDR & PERSIANN-CCS best POD (mean 0.82); PERSIANN-CCS worst overall; SRPs underperform in dry zone on CSI and FAR; best CSI in Kalu (mean 0.53); TRMM-3B42 relatively good in dry zone; wet-zone biases mostly negative, most negative −55.71% for TRMM-3B42_RT at Usk Valley — [Climate 2022 DOI](https://doi.org/10.3390/cli10100156); [VU repository PDF](https://vuir.vu.edu.au/46245/1/climate-10-00156-v2.pdf)
- Perera et al. (2022, Advances in Meteorology): Mahaweli basin, six SRPs incl. TRMM-3B42, 14 gauges across 3 climate zones; IMERG best alternative overall but underestimates vs gauges; TRMM-3B42 better at seasonal scale; PERSIANN-CDR worst in detection, CSI and FAR — [Adv. Meteorol. 2022, 1926854](https://onlinelibrary.wiley.com/doi/10.1155/2022/1926854)
- ERA5 better suited to dry/intermediate zones, CHIRPS to the wet zone (Bandara et al. 2022, secondary citation) [unverified] — [ResearchGate figure source](https://www.researchgate.net/figure/a-Correlation-between-rainfall-anomalies-of-Sri-Lanka-from-ERA5-red-and-CHIRPS-blue_fig2_388451095)
- Maha Oya basin (UoM): bias-corrected CHIRPS, AgERA5, PERSIANN for runoff modelling; bias correction significantly changed model performance — [UoM DL](https://dl.lib.uom.lk/items/9462b5ee-252c-4536-b7ea-587093c12b1d)
- CHIRPS used for national 1989–2019 rainfall trend mapping (Alahacoon & Edirisinghe 2021) — [ResearchGate 349440690](https://www.researchgate.net/publication/349440690_Spatial_Variability_of_Rainfall_Trends_in_Sri_Lanka_from_1989_to_2019_as_an_Indication_of_Climate_Change)
- TRMM-era satellite + rainfall trend analysis (2001–2016) for flood hazard mapping — [Remote Sensing 2018, 10(3):448](https://www.mdpi.com/2072-4292/10/3/448)
- GSMaP in Kalu: real-time gauge merging improves GSMaP-NOW/NRT; NRT > NOW (see §1) — [Water 2023](https://doi.org/10.3390/w15061199)
- Sub-daily: SATREPS found hourly GSMaP agrees less well with gauges than MSSG simulation for hourly maxima and 3-day totals — [Springer chapter](https://link.springer.com/chapter/10.1007/978-3-032-18863-2_6)
- A 2026 paper evaluates sub-daily SPPs (1, 3, 6, 12 h; 2020–2021) and diurnal cycle in "a tropical island environment": IMERG detects substantially more events than GSMaP at all scales, GSMaP overestimates trace frequency [study area not confirmed as Sri Lanka] — [Springer Discover 2026, s44288-026-00685-1](https://link.springer.com/article/10.1007/s44288-026-00685-1)
- Diurnal cycle (Atmos. Res. 2023, IMERG 2001–2019): diurnal maximum ~12 UTC (17:30 local) in all seasons; larger amplitude in spring/autumn; authors could not obtain sufficient QC'd hourly gauge data and compared 3-hourly instead — [Atmospheric Research 2023](https://www.sciencedirect.com/science/article/pii/S0169809523000893). Related: MJO modulation of afternoon convection — [npj Clim Atmos Sci 2024](https://www.nature.com/articles/s41612-024-00586-5); ENSO modulation of springtime diurnal rainfall (Koralegedara 2023) — [Earth and Space Science 2023](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2023EA002832); IMD chapter: 3-hourly TRMM 1998–2019 shows evening peak in west, early-hours peak in east — [IMD NE monsoon chapter](https://mausam.imd.gov.in/responsive/pdf_viewer_css/met1/Chapter-7%20page%20155-173/Chapter-7.pdf)
- Commercial microwave links tested for tropical rainfall monitoring in Sri Lanka — [Environ. Res. Lett. 2021](https://iopscience.iop.org/article/10.1088/1748-9326/ac0fa6)
- Regional context (SE Asia vs SA-OBS): IMERG, CHIRPS, ERA5 overestimate and PERSIANN underestimates; largest overestimation over high-precipitation regions for CHIRPS, ERA5, IMERG — [PMC11936298](https://pmc.ncbi.nlm.nih.gov/articles/PMC11936298)

### Inferences
- For flash-flood work, IMERG (Final/Late) is the defensible default, but expect underestimation of wet-zone/orographic extremes (cf. IMERG IDF underestimation at Colombo/Ratnapura, §4) and poorer dry-zone categorical skill; gauge merging is essential.
- Event-scale (hourly, extreme) satellite verification against SL gauges is a clear research gap.

### Gaps
- No found SL study reporting hourly POD/FAR/CSI for IMERG vs gauges for extreme events; no SL evaluation of ERA5/ERA5-Land at sub-daily scale; CHIRPS daily skill metrics for SL not retrieved; no published PERSIANN-CCS-CDR or GSMaP-MVK hourly SL validation with numbers.

## 4. Sub-daily rainfall, IDF, temporal patterns and extreme trends

### Takeaway
Design practice still relies on 1984-era IDF curves (Ponrajah, ID), with updates for Colombo, a regional-frequency/cluster IDF (ASCE JHE), and satellite-derived IDFs for 50 locations; no national Huff-curve set exists (only a Colombo design-pattern study), and hourly gauge data are scarce.

### Cited Findings
- Historical baseline: Ponrajah (1984) island-wide IDF in "Design of Irrigation Headworks for Small Catchments", 6 climatic zones — [lidsen AEER 2023/24 review](https://www.lidsen.com/journals/aeer/aeer-07-03-031); early depth-duration-frequency work — [J. Hydrology 1978, Rainfall depth-duration-frequency studies for Sri Lanka](https://www.sciencedirect.com/science/article/abs/pii/0022169478900185)
- Regional IDF via cluster & regional frequency analysis (ASCE J. Hydrol. Eng.) argues updated IDF needed; future projections under SSP2-4.5/SSP5-8.5 for 11 regions, higher intensities in Regions 5, 7, 9 — [ASCE JHE HEENG-6167](https://doi.org/10.1061/JHYEFF.HEENG-6167); [lidsen AEER](https://www.lidsen.com/journals/aeer/aeer-07-03-031)
- De Zoysa et al. (2024, Case Studies in Chem. & Env. Eng.): 50 location-specific IDF curves from daily gauge + IMERG, TRMM-3B42, PERSIANN-CDR (1990–2019); IMERG best, PERSIANN-CDR poor; gauges often lack 15-min/hourly records; IMERG IDF fits well at Anuradhapura, Trincomalee, Badulla, Nuwara Eliya but severely underestimates at Colombo, Ratnapura, Jaffna — [ScienceDirect S2666016424001075](https://www.sciencedirect.com/science/article/pii/S2666016424001075)
- Colombo IDF: 30 years of short-duration data, 15 min–24 h, 2–100 yr return periods; intensities increased recently — [ResearchGate 328381427](https://www.researchgate.net/publication/328381427_Development_of_Rainfall_Intensity-Duration-Frequency_IDF_Curves_for_Colombo_Sri_Lanka); other Colombo IDFs using 1–24 h annual peaks — [ResearchGate 273448884](https://www.researchgate.net/publication/273448884_RAINFALL_INTENSITY-DURATION-FREQUENCY_RELATIONSHIP_FOR_COLOMBO_REGION_IN_SRI_LANKA); [ResearchGate 313960206](https://www.researchgate.net/publication/313960206_Development_of_IDF_Curves_for_Colombo)
- Design temporal pattern, Greater Colombo: 220 events, MIT = 6 h, dimensionless mass curves and percentile curves by duration (Huff-like); enveloped curve and 10% pattern most critical for streamflow — [ResearchGate 313164355](https://www.researchgate.net/publication/313164355_Determination_of_a_Design_Rainfall_Pattern_by_Comparing_with_its_Effect_on_Streamflow_on_Greater_Colombo_Watershed_in_Sri_Lanka)
- Daily-rainfall space-time distributions — [Climate 2014, 2(4):242](https://doi.org/10.3390/cli2040242)
- Extreme trends: Naveendrakumar et al. (2018, Adv. Meteorol.): 20 stations, 1961–2015 daily, Mann–Kendall & Sen — [Wiley 4217917](https://onlinelibrary.wiley.com/doi/10.1155/2018/4217917); ETCCDI indices 1980–2015 at 19 stations: >80% stations increasing precipitation indices (Rx1day, Rx5day, R95p, R99p mostly rising, low significance) — [SCIRP 88597](https://www.scirp.org/journal/paperinformation?paperid=88597); conflicting: Alahacoon/Nisansala et al. 2019 reported decreasing trends at 77% stations (via review) — [Water Harmony review](https://waterharmony.net/wp-content/uploads/2024/09/A-REVIEW-OF-RECENT-CHANGES-IN-RAINFALL-TREND-IN-SRI-LANKA.pdf); recent trends of extreme weather events — [SLJOL](https://ta.sljol.info/articles/54/files/67d7bd5171720.pdf); Colombo trend-method comparison — [Adv. Meteorol. 2020, 8844052](https://www.hindawi.com/journals/amete/2020/8844052/)

### Inferences
- Sub-daily design rainfall for flash-flood work in SL is effectively limited to Colombo; elsewhere practitioners must use 1984 curves, satellite-derived IDF (with known wet-zone underestimation), or disaggregation of daily data.
- Absence of a national Huff/design-storm set is a specific, citable gap.

### Gaps
- No SL Huff quartile tables; no published rainfall concentration index (CI/PCI at daily scale) study retrieved in this search; Premalal-authored extreme trend paper not located (role unverified); Jayawardena extreme-rainfall papers not retrieved.

## 5. Catchment response (time of concentration, unit hydrograph, flashiness)

### Takeaway
Only scattered basin-specific studies exist (Kalu Tc, Kelani/Nillambe Snyder UH, VRR synthetic UH, Gin peak timing); no national flashiness index (e.g. Richards–Baker) or regional comparison of response was found.

### Cited Findings
- Kalu basin (~2,816 km²): data-driven Tc from rainfall intensity + satellite soil moisture, benchmarked against NRCS/SCS in HEC-HMS (Hydrology 2025) — [Hydrology 12(10):264](https://doi.org/10.3390/hydrology12100264)
- Kelani / Nillambe Oya HEC-HMS: Snyder UH with initial loss reliable; calibration 2009–2014, validation 2015–2019 — [ResearchGate 376856813](https://www.researchgate.net/publication/376856813_RIVER_FLOW_MODELING_IN_THE_KELANI_RIVER_CATCHMENT_SRI_LANKA)
- Victoria–Randenigala–Rantambe sanctuary: NERC/FSR-based synthetic UH for six ungauged sub-catchments; peaks within 2–3 h of storm onset — [ResearchGate 274634436](https://www.researchgate.net/publication/274634436_Prediction_of_Ungaged_Basins_PUB_in_the_Victoria_-_Randenigala_-_Rantambe_VRR_Sanctuary_of_Sri_Lanka_-_Approach_based_on_Synthetic_Unit_Hydrographs)
- Kelani: monsoon peaks ~800–1,500 m³/s; specific discharge computed per outlet before POT analysis [snippet] — related Kelani climate/land-use flood study — [Hydrology 2022, 9(10):177](https://doi.org/10.3390/hydrology9100177)
- Mahaweli streamflow variability 1990–2014 (10/30-day maxima, PQ5/PQ95) — [Water 2019, 11(12):2485](https://www.mdpi.com/2073-4441/11/12/2485); SL environmental flow calculator notes dams/diversions alter peaks and FDCs — [Water Policy 2015](https://doi.org/10.2166/wp.2015.158); basin classification (103 basins / 94 true basins — sources differ) — [ResearchGate 347217399](https://www.researchgate.net/publication/347217399_UNDERSTANDING_THE_RIVER_BASIN_CLASSIFICATION_OF_SRI_LANKA)

### Inferences
- Short response times (2–3 h) reported for upland Mahaweli sub-catchments (and possibly the Gin, unverified) indicate genuine flash-flood potential in central-highland and SW tributaries, much shorter than the 24–48 h lead framing of ID warnings.

### Gaps
- No SL flashiness index, regional lag-time regression, or peak-flow-per-unit-area comparison across basins found.
- A search summary reported a Gin basin study with peak ~4.7 h after storm onset and ~12 h recession, but the source paper could not be identified; treat as unverified until located.

## 6. Data availability and disaster records

### Takeaway
Hourly data exist (ID 42 permanent stations hourly water level + rainfall; DoM AWS 10-min; NBRO ~325 automated gauges), but researcher access is fee-based/request-based, historical records are partly on paper, and QC'd hourly gauge archives are hard to obtain; DesInventar (DMC/UNDP, 1974–present) includes a "flash flood" event category but with known inconsistencies.

### Cited Findings
- ID: 42 permanent gauging stations, hourly water level and rainfall — [ID HDMD page](https://www.irrigation.gov.lk/web/index.php?option=com_content&view=article&id=27&Itemid=128&lang=en); ID publishes Hydrological Annuals (e.g. 2018/19) — [ID Hydrological Annual 18-19](https://www.irrigation.gov.lk/web/images/Hydrological-Annual/12_Hydrological_Annual_18-19.pdf)
- DoM 2023 Annual Performance Report: 937 data reports issued; data sales revenue figures reported (≈Rs 4.03 M and a separate ≈Rs 842,030 — conflicting figures in the snippet); free data for students and approved government organisations — [Parliament APR 2023](https://www.parliament.lk/uploads/documents/paperspresented/1723001776071832.pdf)
- Public can request DoM data for a fee (daily/monthly rainfall listed) — [GIC: Obtaining Meteorological Data](http://gic.gov.lk/gic/index.php/en/component/info/?id=764&catid=71&task=info); [meteo.gov.lk](https://meteo.gov.lk/)
- CRIP made DoM data free for ID, DMC, NBRO — [World Bank ICR00005564](https://documents1.worldbank.org/curated/en/418431641855234812/pdf/Sri-Lanka-Improving-Climate-Resilience-Project.pdf)
- Researchers report inability to obtain sufficient QC'd hourly gauge data — [Atmos. Res. 2023](https://www.sciencedirect.com/science/article/pii/S0169809523000893); hourly/sub-hourly records lacking — [De Zoysa et al. 2024](https://www.sciencedirect.com/science/article/pii/S2666016424001075)
- DesInventar Sri Lanka (DMC + UNDP), records from 1974; flood ~37% of records in decade to Oct 2016 (JICA) — [desinventar.lk](https://www.desinventar.lk/); [About DesInventar SL](https://www.desinventar.lk/des_html/About-us/about_us.html); [Disaster Event & Impact Profile](https://www.desinventar.lk/des_html/disaster_profile/disaster_profile.pdf); [JICA 12111894](https://openjicareport.jica.go.jp/pdf/12111894.pdf); "flash flood" listed as separate category — [DesInventar.net profile LKA](https://www.desinventar.net/DesInventar/profiletab.jsp?countrycode=lka&continue=y)
- Data-quality caveats: preliminary 1974–2007 report notes inconsistencies — [PreventionWeb](https://www.preventionweb.net/publication/documents-and-publications/historical-disaster-information-system-preliminary-analysis); EM-DAT vs DesInventar show significant damage differences; a 2011 flood episode recorded as multiple DesInventar events vs one EM-DAT event — [Springer EconDisCliCha 2019](https://link.springer.com/article/10.1007/s41885-019-00052-0)

### Inferences
- A flash-flood study can feasibly build an event inventory from DesInventar "flash flood" records + DMC situation reports, then pair with ID hourly gauge rainfall (if obtained) or IMERG half-hourly; event timing/location precision in DesInventar is the limiting factor.

### Gaps
- Counts of DesInventar flash-flood records not retrieved; Mahaweli Authority data access terms not found; current DoM fee schedule and hourly data availability to researchers unconfirmed; NBRO gauge data public access unknown.
