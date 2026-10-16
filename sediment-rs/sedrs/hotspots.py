"""Longitudinal hotspot detection: abrupt, recurring downstream jumps.

A reach is a candidate when its seasonal median signal is at least
`jump_ratio` times the median of the `k` nearest valid reaches upstream, in at
least `min_years` different years. Recurrence across years separates
persistent sources (in-channel mining, bank collapse, effluent) from one-off
storm plumes. The doubling threshold follows the definition of mining impact
in Dethier et al. (2023, Nature 620:787-793).

Candidates are NOT confirmed sources: tributary confluences produce the same
signature. Each candidate must be checked on high-resolution imagery.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def longitudinal_ratios(df: pd.DataFrame, var="SPM_blend_median", k=3) -> pd.DataFrame:
    """df: reach_id, chain_id, km_from_mouth, season, year, lentic, <var>."""
    out = []
    for (_, _, _), g in df.groupby(["chain_id", "season", "year"]):
        g = g.sort_values("km_from_mouth", ascending=False)   # source -> mouth
        vals = g[var].to_numpy(float)
        lentic = g["lentic"].to_numpy(bool)
        ratio = np.full(len(g), np.nan)
        for i in range(len(g)):
            if lentic[i] or not np.isfinite(vals[i]) or vals[i] <= 0:
                continue
            up = [j for j in range(i - 1, -1, -1) if np.isfinite(vals[j]) and vals[j] > 0]
            up = up[:k]
            if len(up) < k or lentic[up].any():
                continue
            ratio[i] = vals[i] / np.median(vals[up])
        out.append(g.assign(ratio=ratio))
    return pd.concat(out, ignore_index=True)


def candidates(ratios: pd.DataFrame, jump_ratio=2.0, min_years=2) -> pd.DataFrame:
    r = ratios.assign(flag=ratios["ratio"] >= jump_ratio)
    agg = (r.groupby(["reach_id", "chain_id", "river", "km_from_mouth", "season"])
             .agg(years_flagged=("flag", lambda s: int(r.loc[s.index][s]["year"].nunique())),
                  years_observed=("ratio", lambda s: int(r.loc[s.index][s.notna()]["year"].nunique())),
                  median_ratio=("ratio", "median"),
                  max_ratio=("ratio", "max"))
             .reset_index())
    c = agg[agg["years_flagged"] >= min_years]
    return c.sort_values(["years_flagged", "median_ratio"], ascending=False).reset_index(drop=True)


def cluster(cands: pd.DataFrame, seg_km: float = 1.0) -> pd.DataFrame:
    """Merge adjacent flagged reaches into one hotspot.

    With a k-reach upstream median, a single step change is flagged on up to
    ceil(k/2) consecutive reaches. The most upstream reach of a cluster marks
    where the jump begins.
    """
    cols = ["chain_id", "river", "season", "jump_starts_km", "jump_reach_id",
            "n_reaches", "years_flagged", "max_median_ratio"]
    if cands.empty:
        return pd.DataFrame(columns=cols)
    rows = []
    for (chain, season), g in cands.groupby(["chain_id", "season"]):
        g = g.sort_values("km_from_mouth", ascending=False)
        members = []
        for _, r in g.iterrows():
            if members and members[-1]["km_from_mouth"] - r["km_from_mouth"] > 1.5 * seg_km:
                rows.append(_summarise(chain, season, members))
                members = []
            members.append(r)
        if members:
            rows.append(_summarise(chain, season, members))
    return (pd.DataFrame(rows).sort_values(["years_flagged", "max_median_ratio"], ascending=False)
              .reset_index(drop=True))


def _summarise(chain, season, members):
    m = pd.DataFrame(members)
    top = m.iloc[0]
    return {"chain_id": chain, "river": top["river"], "season": season,
            "jump_starts_km": top["km_from_mouth"], "jump_reach_id": top["reach_id"],
            "n_reaches": len(m), "years_flagged": int(m["years_flagged"].max()),
            "max_median_ratio": float(m["median_ratio"].max())}
