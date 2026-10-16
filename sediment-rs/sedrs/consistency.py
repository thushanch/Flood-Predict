"""Checks that stand in for in-situ validation.

1. Cross-sensor agreement: same-day Sentinel-2 vs Landsat-8/9 retrievals at
   the same station (cf. Pahlevan et al. 2019, RSE 220:19-29).
2. Algorithm spread: red- vs NIR-band Nechad SPM in the switching window.
3. Physical plausibility: rainfall response (drivers.py) and reservoir trapping.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .algorithms import algorithm_spread


def same_day_pairs(df: pd.DataFrame, var: str) -> pd.DataFrame:
    s2 = df[df["sensor"] == "S2"][["station", "date", var]]
    ls = df[df["sensor"].isin(["L8", "L9"])][["station", "date", "sensor", var]]
    return s2.merge(ls, on=["station", "date"], suffixes=("_s2", "_ls")).dropna()


def agreement(x, y, log: bool = True) -> dict:
    """Agreement metrics between two retrievals of the same quantity.

    MAPD and bias are computed from the log ratio, which is symmetric and
    robust for concentrations spanning orders of magnitude (Seegers et al. 2018).
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    if log:
        ok &= (x > 0) & (y > 0)
    x, y = x[ok], y[ok]
    n = len(x)
    if n < 3:
        return {"n": n}
    res = {"n": n,
           "spearman_r": stats.spearmanr(x, y).statistic,
           "pearson_r": stats.pearsonr(np.log10(x), np.log10(y)).statistic if log
           else stats.pearsonr(x, y).statistic}
    if log:
        lr = np.log10(y / x)
        res["bias_pct"] = (10 ** np.median(lr) - 1) * 100
        res["mapd_pct"] = (10 ** np.median(np.abs(lr)) - 1) * 100
        # reduced major axis in log space (both variables carry error)
        lx, ly = np.log10(x), np.log10(y)
        slope = np.sign(np.corrcoef(lx, ly)[0, 1]) * ly.std() / lx.std()
        res["rma_slope"] = slope
        res["rma_intercept"] = ly.mean() - slope * lx.mean()
    else:
        d = y - x
        res["bias"] = np.median(d)
        res["mad"] = np.median(np.abs(d))
    return res


def cross_sensor_table(df: pd.DataFrame, variables=("SPM_blend_p50", "T_dog_p50", "ndti_p50",
                                                    "red_p50")) -> pd.DataFrame:
    rows = []
    for var in variables:
        pairs = same_day_pairs(df, var)
        log = var != "ndti_p50"
        rows.append({"variable": var, **agreement(pairs[f"{var}_s2"], pairs[f"{var}_ls"], log=log)})
    return pd.DataFrame(rows)


def spread_summary(df: pd.DataFrame) -> pd.DataFrame:
    sp = algorithm_spread(df["SPM_red_p50"], df["SPM_nir_p50"], df["red_p50"])
    d = df.assign(alg_spread=sp)
    return (d.groupby("station")["alg_spread"]
              .agg(n="count", median="median", p90=lambda s: s.quantile(0.9)))


def reservoir_trapping(df: pd.DataFrame, up: str, down: str, var: str = "SPM_blend_p50",
                       n_boot: int = 2000, seed: int = 0) -> dict:
    """Median downstream/upstream ratio on dates with both observed, bootstrap 95% CI.

    A ratio < 1 is the expected signature of sediment trapping by reservoirs.
    """
    a = df[df["station"] == up].groupby("date")[var].mean()
    b = df[df["station"] == down].groupby("date")[var].mean()
    j = pd.concat([a.rename("up"), b.rename("down")], axis=1).dropna()
    j = j[(j["up"] > 0) & (j["down"] > 0)]
    if len(j) < 5:
        return {"up": up, "down": down, "n": len(j)}
    lr = np.log(j["down"] / j["up"]).to_numpy()
    rng = np.random.default_rng(seed)
    boots = np.median(rng.choice(lr, (n_boot, len(lr))), axis=1)
    return {"up": up, "down": down, "n": len(j),
            "ratio_median": float(np.exp(np.median(lr))),
            "ci95_low": float(np.exp(np.percentile(boots, 2.5))),
            "ci95_high": float(np.exp(np.percentile(boots, 97.5)))}
