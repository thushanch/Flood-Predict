"""Sri Lanka climate seasons (Department of Meteorology).

FIM  First Inter-Monsoon   Mar-Apr
SWM  Southwest Monsoon     May-Sep
SIM  Second Inter-Monsoon  Oct-Nov
NEM  Northeast Monsoon     Dec-Feb   (December is assigned to the following year)
"""
from __future__ import annotations

import pandas as pd

SEASONS = ["NEM", "FIM", "SWM", "SIM"]
_MONTH_TO_SEASON = {12: "NEM", 1: "NEM", 2: "NEM", 3: "FIM", 4: "FIM",
                    5: "SWM", 6: "SWM", 7: "SWM", 8: "SWM", 9: "SWM",
                    10: "SIM", 11: "SIM"}


def season_of(dates) -> pd.Series:
    d = pd.to_datetime(pd.Series(dates))
    return d.dt.month.map(_MONTH_TO_SEASON)


def season_year(dates) -> pd.Series:
    d = pd.to_datetime(pd.Series(dates))
    return d.dt.year + (d.dt.month == 12).astype(int)
