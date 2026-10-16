"""Generate SYNTHETIC data with known answers to test the analysis end to end.

Planted signals the analysis must recover:
  * kelani_hanwella: +6 %/yr trend
  * kalu_ellagawa:   step increase in 2021-07 (x1.8)
  * Mahaweli dam pair: downstream = 0.45 x upstream
  * Landsat reads 8 % higher than Sentinel-2 on same-day pairs
  * reach chain "demo_0": recurring jump x3 at km 18 (all years, NEM season)
None of these numbers describe real Sri Lankan rivers.

    python scripts/make_demo_data.py && python scripts/05_analyse.py --data demo_data --out demo_outputs
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sedrs import algorithms as alg  # noqa: E402
from sedrs.config import ROOT, load_settings  # noqa: E402

rng = np.random.default_rng(42)
out = ROOT / "demo_data"
for sub in ("stations", "rainfall", "reaches"):
    (out / sub).mkdir(parents=True, exist_ok=True)

cfg = load_settings()
stations = [s["id"] for s in cfg["stations"]]
days = pd.date_range("2017-01-01", "2025-12-31", freq="D")

# --- rainfall: monsoon-modulated gamma ---------------------------------------
month = days.month.to_numpy()
wet = np.isin(month, [5, 6, 7, 8, 9, 10, 11]).astype(float)
rain_rows, base = [], {}
for st in stations:
    mean_mm = 4 + 8 * wet
    r = rng.gamma(0.5, mean_mm / 0.5) * (rng.random(len(days)) < 0.55)
    rain_rows.append(pd.DataFrame({"station": st, "date": days.strftime("%Y-%m-%d"), "rain_mm": r.round(2)}))
    p7 = pd.Series(r).rolling(7, min_periods=1).sum().to_numpy()
    t_yr = (days - days[0]).days.to_numpy() / 365.25
    lvl = 10 ** rng.uniform(0.9, 1.5)
    spm = lvl * (1 + 0.04 * p7)
    if st == "kelani_hanwella":
        spm *= 1.06 ** t_yr
    if st == "kalu_ellagawa":
        spm *= np.where(days >= "2021-07-01", 1.8, 1.0)
    base[st] = spm
base["mahaweli_mahiyangana"] = 0.45 * base["mahaweli_peradeniya"] * 10 ** rng.normal(0, 0.05, len(days))
rain = pd.concat(rain_rows)
for y, g in rain.groupby(rain["date"].str[:4]):
    g.to_csv(out / "rainfall" / f"rainfall_{y}.csv", index=False)


# --- station observations ---------------------------------------------------
def spm_to_rho_red(spm, A=342.10, C=0.19563):
    """Invert Nechad red: rho = SPM / (A + SPM / C)."""
    return spm / (A + spm / C)


rows = []
for sensor, revisit, gain in (("S2", 5, 1.0), ("L8", 16, 1.08), ("L9", 16, 1.08)):
    first = (pd.Timestamp("2021-11-01") - days[0]).days + 8 if sensor == "L9" else 0
    idx = np.arange(first, len(days), revisit)
    for st in stations:
        for i in idx:
            cloud_p = 0.75 if wet[i] else 0.3
            if rng.random() < cloud_p:
                continue
            spm = base[st][i] * gain * 10 ** rng.normal(0, 0.06)
            rho_r = spm_to_rho_red(spm)
            rho_n = rho_r * 0.12 * (1 + spm / 150)
            rho_g = rho_r / (1 + 0.004 * spm) * 1.05
            red, nir, bl = alg.nechad_spm(rho_r, rho_n, "S2" if sensor == "S2" else "L8")
            t = alg.dogliotti_turbidity(rho_r, rho_n)
            nd = alg.ndti(rho_r, rho_g)
            n_px = int(rng.integers(80, 160)) if sensor == "S2" else int(rng.integers(30, 75))
            row = {"station": st, "river": st.split("_")[0], "date": days[i].strftime("%Y-%m-%d"),
                   "sensor": sensor, "platform": sensor, "scene": f"synthetic_{i}",
                   "red_count": n_px, "SPM_blend_count": n_px}
            for b, v in (("green", rho_g), ("red", rho_r), ("nir", rho_n), ("swir1", 0.004),
                         ("ndti", nd), ("T_dog", t), ("SPM_red", red), ("SPM_nir", nir), ("SPM_blend", bl)):
                row[f"{b}_p50"] = float(v)
                row[f"{b}_p25"] = float(v) * (0.85 if b != "ndti" else 1)
                row[f"{b}_p75"] = float(v) * (1.15 if b != "ndti" else 1)
            rows.append(row)
obs = pd.DataFrame(rows)
for (s, y), g in obs.groupby(["sensor", obs["date"].str[:4]]):
    g.to_csv(out / "stations" / f"stations_{s}_{y}.csv", index=False)

# --- reaches: one 40 km chain with a recurring x3 jump at km 18 -----------
rr, wf = [], []
for y in range(2019, 2026):
    for season in ("NEM", "FIM", "SWM", "SIM"):
        for km in np.arange(0.5, 40.5, 1.0):
            v = 15 * (1 + (40 - km) * 0.01) * 10 ** rng.normal(0, 0.05)
            if km <= 18 and season == "NEM":
                v *= 3
            rid = f"demo_0_{int(km):04d}"
            rr.append({"reach_id": rid, "chain_id": "demo_0", "river": "DemoRiver",
                       "km_from_mouth": km, "season": season, "year": y,
                       "SPM_blend_median": v, "ndti_median": np.nan, "T_dog_median": np.nan,
                       "n_obs_median": 5, "sensor": "S2"})
pd.DataFrame(rr).to_csv(out / "reaches" / "reaches_S2_demo.csv", index=False)
pd.DataFrame({"reach_id": sorted({r["reach_id"] for r in rr}), "water_fraction": 0.2}).to_csv(
    out / "reaches" / "reaches_water_fraction.csv", index=False)

(out / "potential_pixels.json").write_text(json.dumps(
    {"S2": {s: 160 for s in stations}, "L": {s: 75 for s in stations}}))
print(f"synthetic data written to {out}  ({len(obs)} station-image rows)")
