# Sediment signal analysis summary

Primary SPM product: **SPM_red** (tables labelled SPM refer to it).

Station-image rows: 1466 raw -> 948 after QC (13 stations, 2019-01-01 to 2025-12-25).

## Clear-sky observations per season

| station              |   NEM |   FIM |   SWM |   SIM |
|:---------------------|------:|------:|------:|------:|
| deduru_chilaw        |    25 |    11 |     2 |    11 |
| gin_gintota          |    39 |     4 |     3 |    10 |
| kalu_ellagawa        |    24 |     9 |     0 |     5 |
| kalu_putupaula       |    33 |    13 |     6 |    12 |
| kelani_colombo       |    45 |    19 |     7 |    21 |
| kelani_hanwella      |    27 |    14 |     3 |    16 |
| mahaoya_badalgama    |    21 |     7 |     3 |     9 |
| mahaweli_mahiyangana |    28 |    26 |    44 |    21 |
| mahaweli_manampitiya |    25 |    39 |    47 |    17 |
| mahaweli_peradeniya  |    46 |     8 |    10 |    23 |
| mahaweli_somawathiya |    21 |    14 |    15 |     8 |
| walawe_ambalantota   |    41 |    18 |     6 |    12 |
| walawe_embilipitiya  |    30 |    24 |    17 |     9 |

## Check 1 - Sentinel-2 vs Landsat-8/9 same-day agreement

| variable      |   n |
|:--------------|----:|
| SPM_blend_p50 |   0 |
| T_dog_p50     |   0 |
| ndti_p50      |   0 |
| red_p50       |   0 |

## Check 2 - Red vs NIR Nechad spread (switching window only)

| station              |   n |   median |   p90 |
|:---------------------|----:|---------:|------:|
| deduru_chilaw        |  32 |    1.33  | 1.628 |
| gin_gintota          |  43 |    1.396 | 1.505 |
| kalu_ellagawa        |  15 |    1.102 | 1.463 |
| kalu_putupaula       |  44 |    1.072 | 1.459 |
| kelani_colombo       |  76 |    1.258 | 1.461 |
| kelani_hanwella      |  45 |    1.335 | 1.571 |
| mahaoya_badalgama    |  22 |    1.211 | 1.548 |
| mahaweli_mahiyangana |  83 |    1.326 | 1.573 |
| mahaweli_manampitiya |  95 |    1.025 | 1.37  |
| mahaweli_peradeniya  |  58 |    1.193 | 1.483 |
| mahaweli_somawathiya |  39 |    0.981 | 1.255 |
| walawe_ambalantota   |  47 |    0.943 | 1.342 |
| walawe_embilipitiya  |  69 |    1.188 | 1.496 |

## Check 3 - Reservoir trapping (downstream / upstream SPM)

| up                  | down                 |   n |   ratio_median |   ci95_low |   ci95_high |
|:--------------------|:---------------------|----:|---------------:|-----------:|------------:|
| mahaweli_peradeniya | mahaweli_mahiyangana |  22 |          1.056 |      0.769 |       1.696 |

Expected: ratio < 1.

## Seasonal median SPM (g m-3, uncalibrated estimate)

| station              |   NEM |   FIM |   SWM |   SIM |
|:---------------------|------:|------:|------:|------:|
| deduru_chilaw        |  15.1 |  17.4 |  19.4 |  63.9 |
| gin_gintota          |  15.7 |  12.1 |  29.6 |  18.6 |
| kalu_ellagawa        |  60.3 |  94.9 | nan   |  80   |
| kalu_putupaula       |  34.2 |  32.2 |  38.7 |  56.5 |
| kelani_colombo       |  20.9 |  19.6 |  19.8 |  34.4 |
| kelani_hanwella      |  17.7 |  27.2 |  50.3 |  65.9 |
| mahaoya_badalgama    |  32.7 |  19.1 |  40.3 | 163.3 |
| mahaweli_mahiyangana |  31.2 |  24.9 |  18.4 |  56.6 |
| mahaweli_manampitiya |  39.1 |  36.1 |  23.1 |  62.8 |
| mahaweli_peradeniya  |  15.7 |  23.2 |  24.2 |  56.2 |
| mahaweli_somawathiya |  47.1 |  44.3 |  38.1 |  64.8 |
| walawe_ambalantota   |  37.2 |  46.4 |  33.8 |  61.8 |
| walawe_embilipitiya  |  15   |  26   |  21   |  17.8 |

## Trends (seasonal Kendall / Hamed-Rao MK / Pettitt)

| station              |   n_months | sk_trend          |    sk_p |   sk_pct_per_yr | hr_trend          |    hr_p |   hr_pct_per_yr | pettitt_date   |   pettitt_p |   pettitt_shift_pct |    sk_q |    hr_q |   pettitt_q | sk_significant   | pettitt_significant   |
|:---------------------|-----------:|:------------------|--------:|----------------:|:------------------|--------:|----------------:|:---------------|------------:|--------------------:|--------:|--------:|------------:|:-----------------|:----------------------|
| deduru_chilaw        |         33 | insufficient data | nan     |         nan     | no trend          |   1     |          -1.381 | 2022-12        |       0.047 |              62.873 | nan     |   1     |       0.162 | False            | False                 |
| gin_gintota          |         25 | insufficient data | nan     |         nan     | insufficient data | nan     |         nan     | 2022-01        |       0.05  |              22.809 | nan     | nan     |       0.162 | False            | False                 |
| kalu_ellagawa        |         22 | insufficient data | nan     |         nan     | insufficient data | nan     |         nan     | 2022-12        |       0.037 |              68.804 | nan     | nan     |       0.162 | False            | False                 |
| kalu_putupaula       |         36 | increasing        |   0.001 |          17.553 | insufficient data | nan     |         nan     | 2021-11        |       0     |              48.306 |   0.004 | nan     |       0.005 | True             | True                  |
| kelani_colombo       |         47 | no trend          |   0.943 |          -0.483 | no trend          |   0.072 |          -6.974 | 2023-04        |       1     |              -7.327 |   1     |   0.644 |       1     | False            | False                 |
| kelani_hanwella      |         35 | insufficient data | nan     |         nan     | no trend          |   0.707 |          -4.291 | 2023-02        |       0.632 |             -12.915 | nan     |   0.859 |       0.913 | False            | False                 |
| mahaoya_badalgama    |         27 | insufficient data | nan     |         nan     | no trend          |   0.26  |         -13.146 | 2021-03        |       1     |              -5.874 | nan     |   0.662 |       1     | False            | False                 |
| mahaweli_mahiyangana |         60 | no trend          |   0.089 |           5.352 | no trend          |   0.23  |           6.014 | 2021-12        |       0.277 |              12.119 |   0.208 |   0.662 |       0.45  | False            | False                 |
| mahaweli_manampitiya |         61 | no trend          |   0.8   |           1.563 | no trend          |   0.764 |          -3.53  | 2024-02        |       1     |             -12.275 |   1     |   0.859 |       1     | False            | False                 |
| mahaweli_peradeniya  |         40 | increasing        |   0.031 |          11.81  | no trend          |   0.368 |          15.592 | 2023-10        |       0.125 |              75.461 |   0.108 |   0.662 |       0.272 | False            | False                 |
| mahaweli_somawathiya |         33 | insufficient data | nan     |         nan     | no trend          |   0.452 |           1.728 | 2023-04        |       0.069 |              11.658 | nan     |   0.679 |       0.181 | False            | False                 |
| walawe_ambalantota   |         41 | no trend          |   0.327 |          -3.133 | no trend          |   0.368 |          -7.685 | 2022-01        |       0.153 |             -20.831 |   0.572 |   0.662 |       0.283 | False            | False                 |
| walawe_embilipitiya  |         39 | no trend          |   1     |          -0.182 | insufficient data | nan     |         nan     | 2023-03        |       1     |              22.306 |   1     | nan     |       1     | False            | False                 |

q = Benjamini-Hochberg FDR-adjusted p across stations; interpret only `*_significant`.
