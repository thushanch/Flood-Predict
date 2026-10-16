import numpy as np
import pytest

from sedrs import algorithms as alg


def test_nechad_hand_calculation():
    # S2 red: A=342.10, C=0.19563 -> rho=0.03 gives 342.10*0.03/(1-0.03/0.19563)
    expected = 342.10 * 0.03 / (1 - 0.03 / 0.19563)
    red, _, _ = alg.nechad_spm(0.03, 0.001, "S2")
    assert red == pytest.approx(expected)
    assert expected == pytest.approx(12.12, abs=0.01)


def test_nechad_invalid_domain():
    assert np.isnan(alg.nechad(0.0, 100, 0.2))
    assert np.isnan(alg.nechad(-0.01, 100, 0.2))
    assert np.isnan(alg.nechad(0.2, 100, 0.2))      # rho == C -> saturation


def test_dogliotti_uses_red_below_window_and_nir_above():
    t_low = alg.dogliotti_turbidity(0.02, 0.001)
    assert t_low == pytest.approx(228.1 * 0.02 / (1 - 0.02 / 0.1641))
    t_high = alg.dogliotti_turbidity(0.10, 0.03)
    assert t_high == pytest.approx(3078.9 * 0.03 / (1 - 0.03 / 0.2112))


def test_blend_is_continuous_across_window():
    red = np.linspace(0.04, 0.08, 401)
    nir = red * 0.35                                   # plausible turbid-water NIR/red
    t = alg.dogliotti_turbidity(red, nir)
    assert np.all(np.isfinite(t))
    assert np.max(np.abs(np.diff(t))) < 2.0            # no jumps at the switch


def test_blend_ignores_unused_nan_member():
    # NIR invalid but red below switching window -> still valid
    assert np.isfinite(alg.blend(10.0, np.nan, 0.02))
    # inside the window both members are needed
    assert np.isnan(alg.blend(10.0, np.nan, 0.06))


def test_monotonic_in_reflectance():
    rho = np.linspace(0.001, 0.15, 100)
    spm = alg.nechad(rho, *alg.NECHAD_SPM["S2"]["red"])
    assert np.all(np.diff(spm) > 0)


def test_ndti_range_and_sign():
    assert alg.ndti(0.05, 0.03) > 0          # red > green: turbid
    assert alg.ndti(0.02, 0.04) < 0          # green > red: clear
    assert np.isnan(alg.ndti(0, 0))


def test_coefficients_match_acolite_table():
    assert alg.NECHAD_SPM["S2"]["red"] == (342.10, 0.19563)
    assert alg.NECHAD_SPM["S2"]["nir"] == (2932.21, 0.21151)
    assert alg.NECHAD_SPM["L8"]["red"] == (346.32, 0.19905)
    assert alg.NECHAD_SPM["L8"]["nir"] == (2929.49, 0.21135)
    assert alg.DOGLIOTTI["A_red"] == 228.1 and alg.DOGLIOTTI["C_nir"] == 0.2112


def test_algorithm_spread_only_in_window():
    s = alg.algorithm_spread([10, 10, 10], [12, 12, 12], [0.01, 0.05, 0.12])
    assert np.isnan(s[0]) and np.isnan(s[2])
    assert s[1] == pytest.approx(2 / 11)
