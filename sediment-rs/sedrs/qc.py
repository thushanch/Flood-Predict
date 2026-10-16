"""Quality control of station extractions."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .seasons import season_of, season_year


def load_station_csvs(paths) -> pd.DataFrame:
    df = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    return df


def clean(df: pd.DataFrame, potential: dict | None = None, *, min_pixels: int = 10,
          min_valid_fraction: float = 0.5) -> pd.DataFrame:
    """Filter and de-duplicate station-image rows.

    * drops rows with fewer than `min_pixels` valid water pixels;
    * drops rows where valid / potential water pixels < `min_valid_fraction`
      (partial cloud over the AOI biases the median toward the clear part);
    * keeps one row per station x sensor x date (overlapping S2 tiles or
      Landsat paths): the one with most valid pixels.
    """
    out = df.copy()
    out = out[out["red_count"] >= min_pixels]
    if potential:
        key = out["sensor"].map(lambda s: "S2" if s == "S2" else "L")
        denom = [potential.get(k, {}).get(st, np.nan) for k, st in zip(key, out["station"])]
        out["valid_fraction"] = out["red_count"] / np.asarray(denom, float)
        out = out[out["valid_fraction"].fillna(1.0) >= min_valid_fraction]
    out = (out.sort_values("red_count", ascending=False)
              .drop_duplicates(["station", "sensor", "date"])
              .sort_values(["station", "date", "sensor"]))
    out["season"] = season_of(out["date"]).values
    out["season_year"] = season_year(out["date"]).values
    out["iqr_rel"] = (out["SPM_blend_p75"] - out["SPM_blend_p25"]) / out["SPM_blend_p50"]
    return out.reset_index(drop=True)


def observation_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Valid observations per station x season -- reports the monsoon cloud bias."""
    return (df.groupby(["station", "season"]).size().unstack(fill_value=0)
              .reindex(columns=["NEM", "FIM", "SWM", "SIM"], fill_value=0))


def daily_series(df: pd.DataFrame, var: str = "SPM_blend_p50") -> pd.DataFrame:
    """One value per station-day (mean of sensors on the same day)."""
    return (df.groupby(["station", "date"])[var].mean().rename(var).reset_index())


def monthly_series(df: pd.DataFrame, var: str = "SPM_blend_p50") -> pd.DataFrame:
    """Monthly median per station on a complete monthly index (NaN = no data)."""
    d = daily_series(df, var)
    d["month"] = d["date"].dt.to_period("M")
    m = d.groupby(["station", "month"])[var].median().unstack("station")
    full = pd.period_range(m.index.min(), m.index.max(), freq="M")
    return m.reindex(full)
