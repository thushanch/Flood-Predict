import numpy as np
import pandas as pd
import pytest

from sedrs import consistency, drivers, hotspots, reaches, seasons, trends


def test_seasons():
    d = ["2020-12-15", "2021-01-10", "2021-03-01", "2021-06-01", "2021-10-31"]
    assert list(seasons.season_of(d)) == ["NEM", "NEM", "FIM", "SWM", "SIM"]
    assert list(seasons.season_year(d)) == [2021, 2021, 2021, 2021, 2021]


def _monthly(trend_pct=0.0, years=8, seed=1, missing=0.3):
    rng = np.random.default_rng(seed)
    idx = pd.period_range("2017-01", periods=12 * years, freq="M")
    t = np.arange(len(idx)) / 12
    seasonal = 0.4 * np.sin(2 * np.pi * (idx.month.to_numpy() - 3) / 12)
    logv = 1.5 + seasonal + np.log10(1 + trend_pct / 100) * t + rng.normal(0, 0.08, len(idx))
    s = pd.Series(10 ** logv, index=idx)
    s[rng.random(len(s)) < missing] = np.nan        # monsoon cloud gaps
    return s


def test_seasonal_kendall_detects_trend():
    r = trends.seasonal_kendall(_monthly(trend_pct=8))
    assert r["trend"] == "increasing" and r["p"] < 0.01
    assert r["pct_per_yr"] == pytest.approx(8, abs=3)


def test_seasonal_kendall_no_false_trend():
    r = trends.seasonal_kendall(_monthly(trend_pct=0, seed=3))
    assert r["trend"] == "no trend"


def test_pettitt_finds_step():
    rng = np.random.default_rng(0)
    x = np.r_[rng.normal(0, 0.1, 40), rng.normal(0.5, 0.1, 40)]
    r = trends.pettitt(x)
    assert r["p"] < 0.001 and abs(r["cp"] - 39) <= 2


def test_cross_sensor_agreement_metrics():
    rng = np.random.default_rng(0)
    x = 10 ** rng.uniform(0.5, 2.5, 200)
    y = x * 1.10 * 10 ** rng.normal(0, 0.05, 200)    # +10 % bias, ~12 % scatter
    r = consistency.agreement(x, y)
    assert r["bias_pct"] == pytest.approx(10, abs=3)
    assert r["pearson_r"] > 0.95 and r["rma_slope"] == pytest.approx(1, abs=0.05)


def test_reservoir_trapping_ratio():
    dates = pd.date_range("2020-01-01", periods=60, freq="7D")
    up = pd.DataFrame({"station": "up", "date": dates, "SPM_blend_p50": 50.0})
    dn = pd.DataFrame({"station": "dn", "date": dates, "SPM_blend_p50": 20.0})
    r = consistency.reservoir_trapping(pd.concat([up, dn]), "up", "dn")
    assert r["ratio_median"] == pytest.approx(0.4)


def test_rainfall_response_positive():
    rng = np.random.default_rng(2)
    days = pd.date_range("2020-01-01", periods=1000, freq="D")
    rain = pd.DataFrame({"station": "s", "date": days, "rain_mm": rng.gamma(0.6, 12, len(days))})
    p3 = rain["rain_mm"].rolling(3).sum()
    spm = 5 + 0.8 * p3 + rng.normal(0, 3, len(days))
    obs = pd.DataFrame({"station": "s", "date": days, "SPM_blend_p50": spm})[::5].dropna()
    r = drivers.rainfall_response(obs, rain).iloc[0]
    assert r["plausible"] and r["best_window"] in ("P3d", "P7d")


def test_reach_chaining_and_cutting():
    # two reaches digitised in opposite directions, upstream one smaller area
    down = {"type": "Feature", "properties": {"BB_ID": 1, "BB_NAME": "Test", "UPLAND_SKM": 900},
            "geometry": {"type": "LineString", "coordinates": [[80.00, 7.00], [80.05, 7.00]]}}
    up = {"type": "Feature", "properties": {"BB_ID": 1, "BB_NAME": "Test", "UPLAND_SKM": 500},
          "geometry": {"type": "LineString", "coordinates": [[80.10, 7.00], [80.05, 7.00]]}}
    ch = reaches.chain_reaches([up, down], min_len_km=1)
    assert len(ch) == 1
    total = reaches.line_length_km(ch[0]["coords"])
    assert total == pytest.approx(0.10 * 111.32 * np.cos(np.radians(7)), rel=0.01)
    segs = reaches.build_reaches([up, down], seg_km=1.0, min_len_km=1)
    assert len(segs) == int(np.ceil(total))
    kms = [s["properties"]["km_from_mouth"] for s in segs]
    assert kms == sorted(kms) and kms[0] == pytest.approx(0.5)
    # chainage 0 is at the mouth end (the larger-area reach)
    assert ch[0]["coords"][0] in ([80.00, 7.00], [80.05, 7.00])


def test_hotspot_detection_recurring_jump():
    rows = []
    for year in range(2019, 2024):
        for i in range(30):
            km = 30 - i
            val = 20.0 * (1 + 0.01 * i)
            if km <= 12:                     # mining reach starts at km 12 every year
                val *= 3
            rows.append({"reach_id": f"r{km}", "chain_id": "c", "river": "X", "km_from_mouth": km,
                         "season": "NEM", "year": year, "lentic": False, "SPM_blend_median": val})
    df = pd.DataFrame(rows)
    c = hotspots.candidates(hotspots.longitudinal_ratios(df), jump_ratio=2, min_years=2)
    assert list(c["reach_id"])[:1] == ["r12"]
    assert c.iloc[0]["years_flagged"] == 5


def test_bh_fdr():
    q = trends.bh_fdr([0.01, 0.04, 0.03, np.nan, 0.5])
    assert np.isnan(q[3])
    assert q[0] == pytest.approx(0.04) and q[4] == pytest.approx(0.5)
    # sorted p = .01,.03,.04,.5 -> raw .04,.06,.0533,.5 -> step-up min gives .0533 for .03 and .04
    assert q[1] == pytest.approx(0.04 * 4 / 3) and q[2] == pytest.approx(0.04 * 4 / 3)


def test_hotspot_clustering_merges_adjacent_reaches():
    rows = []
    for year in range(2019, 2023):
        for km in range(30, 0, -1):
            val = 20.0 * (3 if km <= 12 else 1)
            rows.append({"reach_id": f"r{km}", "chain_id": "c", "river": "X", "km_from_mouth": km,
                         "season": "NEM", "year": year, "lentic": False, "SPM_blend_median": val})
    c = hotspots.candidates(hotspots.longitudinal_ratios(pd.DataFrame(rows)))
    cl = hotspots.cluster(c)
    assert len(cl) == 1 and cl.iloc[0]["jump_starts_km"] == 12
