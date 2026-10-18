"""Sediment retrieval algorithms (pure NumPy).

Every coefficient here is copied from the ACOLITE reference implementation
(github.com/acolite/acolite), which is maintained by the algorithm authors'
group at RBINS:

* Dogliotti et al. (2015), RSE 156:157-168 -- data/Shared/algorithms/Dogliotti/defaults.txt
* Nechad et al. (2010), RSE 114:854-866, re-calibrated for Sentinel-2 MSI and
  Landsat-8 OLI in Sept 2016 -- data/Shared/algorithms/Nechad/Nechad_calibration_201609.txt

All inputs are water-leaving reflectance rho_w (dimensionless, = pi * Rrs).
The GEE module builds its expressions from the same constants so the cloud
and offline code cannot drift apart.
"""
from __future__ import annotations

import numpy as np

# --- Dogliotti et al. (2015) turbidity, FNU --------------------------------
DOGLIOTTI = {
    "A_red": 228.1, "C_red": 0.1641,     # 645 nm
    "A_nir": 3078.9, "C_nir": 0.2112,    # 859 nm
    "lower": 0.05, "upper": 0.07,        # rho_w(red) switching window
}

# --- Nechad SPM (g m-3), Sept-2016 calibration, B = 0 ----------------------
NECHAD_SPM = {
    "S2": {"red": (342.10, 0.19563),     # MSI B4 665 nm
           "nir": (2932.21, 0.21151)},   # MSI B8A 865 nm
    "L8": {"red": (346.32, 0.19905),     # OLI B4 654 nm
           "nir": (2929.49, 0.21135)},   # OLI B5 864 nm
}
NECHAD_SPM["L9"] = NECHAD_SPM["L8"]      # OLI-2 shares OLI band centres

# ACOLITE's default non-water threshold is rho_t(1600 nm) > 0.0215 (config/defaults.txt),
# defined on ACOLITE's own top-of-atmosphere/DSF reflectance. On Sen2Cor surface
# reflectance, narrow Sri Lankan rivers carry 0.02-0.03 of SWIR adjacency signal
# from bright banks: at 0.0215 most clear river pixels were rejected, while
# raising the limit to 0.04 kept 2-10x more pixels and changed median SPM by
# only a few percent (test: Kelani, Kalu and Mahaweli stations, 29 clear
# scenes, 2024-25). Land contamination is handled by the MNDWI and NDVI tests.
SWIR_WATER_THRESHOLD_ACOLITE = 0.0215
SWIR_WATER_THRESHOLD = 0.04


def nechad(rho, A, C):
    """Single-band semi-analytical model X = A*rho / (1 - rho/C).

    Returns NaN where rho <= 0 or rho >= C (non-physical / saturated).
    """
    rho = np.asarray(rho, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = A * rho / (1.0 - rho / C)
    return np.where((rho > 0) & (rho < C), out, np.nan)


def switch_weight(rho_red, lower=DOGLIOTTI["lower"], upper=DOGLIOTTI["upper"]):
    """Weight of the NIR estimate: 0 below `lower`, 1 above `upper`, linear between."""
    return np.clip((np.asarray(rho_red, float) - lower) / (upper - lower), 0.0, 1.0)


def blend(red_est, nir_est, rho_red):
    """Dogliotti (2015) red/NIR switching applied to any red/NIR estimate pair."""
    w = switch_weight(rho_red)
    red_est = np.asarray(red_est, float)
    nir_est = np.asarray(nir_est, float)
    # Outside the transition zone only one member is needed; don't let a NaN
    # in the unused member poison the result.
    out = (1 - w) * np.nan_to_num(red_est) + w * np.nan_to_num(nir_est)
    bad = ((w < 1) & np.isnan(red_est)) | ((w > 0) & np.isnan(nir_est))
    return np.where(bad, np.nan, out)


def dogliotti_turbidity(rho_red, rho_nir):
    """Turbidity (FNU) after Dogliotti et al. (2015)."""
    d = DOGLIOTTI
    t_red = nechad(rho_red, d["A_red"], d["C_red"])
    t_nir = nechad(rho_nir, d["A_nir"], d["C_nir"])
    return blend(t_red, t_nir, rho_red)


def nechad_spm(rho_red, rho_nir, sensor="S2"):
    """Return (spm_red, spm_nir, spm_blend) in g m-3 (~ mg/L)."""
    c = NECHAD_SPM[sensor]
    spm_red = nechad(rho_red, *c["red"])
    spm_nir = nechad(rho_nir, *c["nir"])
    return spm_red, spm_nir, blend(spm_red, spm_nir, rho_red)


def ndti(rho_red, rho_green):
    """Normalized Difference Turbidity Index, Lacaux et al. (2007): (R-G)/(R+G)."""
    r = np.asarray(rho_red, float)
    g = np.asarray(rho_green, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (r - g) / (r + g)
    return np.where((r + g) > 0, out, np.nan)


def algorithm_spread(spm_red, spm_nir, rho_red, lo=0.03, hi=0.09):
    """Relative disagreement |red - nir| / mean, only where both bands carry signal.

    Below ~0.03 the NIR signal is near the noise floor; above ~0.09 the red
    band is close to saturation, so the comparison is only meaningful in the
    window around the switching zone. Returns NaN elsewhere.
    """
    spm_red = np.asarray(spm_red, float)
    spm_nir = np.asarray(spm_nir, float)
    rho_red = np.asarray(rho_red, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = np.abs(spm_red - spm_nir) / ((spm_red + spm_nir) / 2)
    return np.where((rho_red >= lo) & (rho_red <= hi), rel, np.nan)
