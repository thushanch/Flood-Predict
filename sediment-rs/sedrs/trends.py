"""Trend and change-point tests for monthly sediment series.

* Seasonal Kendall test + seasonal Sen slope (Hirsch et al. 1982) on monthly
  medians -- handles the strong monsoon cycle without deseasonalising.
* Hamed & Rao (1998) modified Mann-Kendall on annual medians -- corrects the
  variance for serial correlation.
* Pettitt (1979) change-point test on deseasonalised monthly anomalies.

All tests run on log10 values: sediment concentrations are right-skewed and
multiplicative changes (e.g. "+5 % per year") are the natural unit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pymannkendall as mk


def _log(s: pd.Series) -> pd.Series:
    return np.log10(s.where(s > 0))


def seasonal_kendall(monthly: pd.Series) -> dict:
    """`monthly` is indexed by a complete monthly PeriodIndex (NaN = missing)."""
    x = _log(monthly)
    n_obs = int(x.notna().sum())
    if n_obs < 36:
        return {"test": "seasonal_kendall", "n": n_obs, "trend": "insufficient data"}
    # pymannkendall needs whole years starting in January
    start = pd.Period(f"{x.index[0].year}-01", "M")
    end = pd.Period(f"{x.index[-1].year}-12", "M")
    x = x.reindex(pd.period_range(start, end, freq="M"))
    r = mk.seasonal_test(x.to_numpy(), period=12)
    slope = r.slope  # log10 units per year
    return {"test": "seasonal_kendall", "n": n_obs, "trend": r.trend, "p": r.p, "tau": r.Tau,
            "slope_log10_per_yr": slope, "pct_per_yr": (10 ** slope - 1) * 100}


def annual_hamed_rao(monthly: pd.Series, min_months: int = 4) -> dict:
    x = _log(monthly)
    g = x.groupby(x.index.year)
    ann = g.median()[g.count() >= min_months]
    if len(ann) < 6:
        return {"test": "hamed_rao", "n": len(ann), "trend": "insufficient data"}
    r = mk.hamed_rao_modification_test(ann.to_numpy())
    return {"test": "hamed_rao", "n": len(ann), "trend": r.trend, "p": r.p,
            "slope_log10_per_yr": r.slope, "pct_per_yr": (10 ** r.slope - 1) * 100}


def anomalies(monthly: pd.Series) -> pd.Series:
    """log10 value minus the station's median for that calendar month."""
    x = _log(monthly)
    clim = x.groupby(x.index.month).transform("median")
    return (x - clim).dropna()


def pettitt(x) -> dict:
    """Pettitt (1979) non-parametric single change-point test.

    p-value approximation: p ~= 2 exp(-6 K^2 / (n^3 + n^2)).
    Returns the index of the last point *before* the change.
    """
    x = np.asarray(x, float)
    n = len(x)
    if n < 10:
        return {"n": n, "p": np.nan, "cp": None}
    sign = np.sign(x[:, None] - x[None, :])            # sign(x_i - x_j)
    # U_t = sum_{i<=t} sum_{j>t} sign(x_i - x_j)
    U = np.array([sign[: t + 1, t + 1:].sum() for t in range(n - 1)])
    t = int(np.argmax(np.abs(U)))
    K = abs(U[t])
    p = min(1.0, 2 * np.exp(-6 * K ** 2 / (n ** 3 + n ** 2)))
    return {"n": n, "K": float(K), "p": float(p), "cp": t}


def change_point(monthly: pd.Series) -> dict:
    a = anomalies(monthly)
    r = pettitt(a.to_numpy())
    if r.get("cp") is None:
        return r
    before, after = a.iloc[: r["cp"] + 1], a.iloc[r["cp"] + 1:]
    r["date"] = str(a.index[r["cp"]])
    r["shift_pct"] = (10 ** (after.median() - before.median()) - 1) * 100
    return r


def bh_fdr(p) -> np.ndarray:
    """Benjamini-Hochberg (1995) adjusted p-values (q-values); NaN-safe."""
    p = np.asarray(p, float)
    q = np.full_like(p, np.nan)
    ok = np.isfinite(p)
    n = ok.sum()
    if n == 0:
        return q
    order = np.argsort(p[ok])
    ranked = p[ok][order] * n / np.arange(1, n + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1].clip(max=1)
    tmp = np.empty(n)
    tmp[order] = ranked
    q[ok] = tmp
    return q


def trend_table(monthly_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    rows = []
    for st in monthly_df.columns:
        s = monthly_df[st]
        sk, hr, cp = seasonal_kendall(s), annual_hamed_rao(s), change_point(s)
        rows.append({
            "station": st,
            "n_months": sk["n"],
            "sk_trend": sk["trend"], "sk_p": sk.get("p"), "sk_pct_per_yr": sk.get("pct_per_yr"),
            "hr_trend": hr["trend"], "hr_p": hr.get("p"), "hr_pct_per_yr": hr.get("pct_per_yr"),
            "pettitt_date": cp.get("date"), "pettitt_p": cp.get("p"),
            "pettitt_shift_pct": cp.get("shift_pct"),
        })
    out = pd.DataFrame(rows)
    # many stations are tested at once -> control the false discovery rate
    for col in ("sk_p", "hr_p", "pettitt_p"):
        out[col.replace("_p", "_q")] = bh_fdr(out[col])
    out["sk_significant"] = out["sk_q"] < alpha
    out["pettitt_significant"] = out["pettitt_q"] < alpha
    return out
