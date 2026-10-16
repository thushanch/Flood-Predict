"""Rainfall response of the satellite sediment signal.

If the retrieval tracks sediment, it should rise after catchment rainfall.
A non-positive or insignificant response flags a station whose signal is
dominated by something else (bottom reflectance, algae, adjacency, glint).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def antecedent_rain(rain: pd.DataFrame, windows=(1, 3, 7, 14)) -> pd.DataFrame:
    """rain: station, date, rain_mm (daily). Returns rolling sums ending on each date."""
    rain = rain.copy()
    rain["date"] = pd.to_datetime(rain["date"])
    out = []
    for st, g in rain.groupby("station"):
        g = g.set_index("date").sort_index()["rain_mm"].asfreq("D")
        cols = {f"P{w}d": g.rolling(w, min_periods=w).sum() for w in windows}
        out.append(pd.DataFrame(cols).assign(station=st).reset_index())
    return pd.concat(out, ignore_index=True)


def rainfall_response(obs: pd.DataFrame, rain: pd.DataFrame, var: str = "SPM_blend_p50",
                      windows=(1, 3, 7, 14)) -> pd.DataFrame:
    """Spearman correlation between the daily signal and antecedent rainfall."""
    ant = antecedent_rain(rain, windows)
    d = obs.groupby(["station", "date"])[var].mean().reset_index()
    j = d.merge(ant, on=["station", "date"], how="inner")
    rows = []
    for st, g in j.groupby("station"):
        row = {"station": st, "n": len(g)}
        best = (None, -np.inf)
        for w in windows:
            c = f"P{w}d"
            gg = g[[var, c]].dropna()
            if len(gg) < 10:
                continue
            r = stats.spearmanr(gg[var], gg[c])
            row[f"rho_{c}"], row[f"p_{c}"] = r.statistic, r.pvalue
            if r.statistic > best[1]:
                best = (c, r.statistic)
        row["best_window"] = best[0]
        rho_best = row.get(f"rho_{best[0]}") if best[0] else np.nan
        p_best = row.get(f"p_{best[0]}") if best[0] else np.nan
        # best of several windows -> Bonferroni-adjust the significance level
        row["plausible"] = bool(best[0] and rho_best > 0 and p_best < 0.05 / len(windows))
        rows.append(row)
    return pd.DataFrame(rows)
