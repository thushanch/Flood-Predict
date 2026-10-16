"""Figures for the station analysis."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SENSOR_COLORS = {"S2": "#1f77b4", "L8": "#d62728", "L9": "#ff7f0e"}
SEASON_SPANS = [(5, 9, "SWM"), (10, 11, "SIM"), (12, 2, "NEM"), (3, 4, "FIM")]


def climatology(df, var="SPM_blend_p50", path=None, ylabel="SPM (g m$^{-3}$)"):
    stations = sorted(df["station"].unique())
    n = len(stations)
    ncol = 3
    nrow = int(np.ceil(n / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4 * ncol, 2.6 * nrow), sharex=True, squeeze=False)
    for ax, st in zip(axes.flat, stations):
        g = df[df["station"] == st]
        m = g.groupby(g["date"].dt.month)[var]
        med, q1, q3, cnt = m.median(), m.quantile(0.25), m.quantile(0.75), m.count()
        med, q1, q3 = (s.reindex(range(1, 13)) for s in (med, q1, q3))
        ax.axvspan(4.5, 9.5, color="0.9", lw=0)
        ax.fill_between(range(1, 13), q1, q3, alpha=0.3)
        ax.plot(range(1, 13), med, "o-", ms=3)
        ax.set_yscale("log")
        ax.set_title(f"{st}  (n={int(cnt.sum())})", fontsize=9)
        ax.set_xticks(range(1, 13), list("JFMAMJJASOND"))
    for ax in axes.flat[n:]:
        ax.set_visible(False)
    for ax in axes[:, 0]:
        ax.set_ylabel(ylabel)
    fig.suptitle("Monthly climatology (median, IQR); shaded = SW monsoon", fontsize=10)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=200)
    plt.close(fig)


def timeseries(df, station, rain=None, var="SPM_blend_p50", path=None):
    g = df[df["station"] == station]
    fig, ax = plt.subplots(figsize=(11, 3.2))
    if rain is not None:
        r = rain[rain["station"] == station]
        ax2 = ax.twinx()
        ax2.bar(pd.to_datetime(r["date"]), r["rain_mm"], width=1, color="0.75")
        ax2.invert_yaxis()
        ax2.set_ylabel("Catchment rain (mm/d)")
    for s, gg in g.groupby("sensor"):
        ax.errorbar(gg["date"], gg[var], yerr=[gg[var] - gg["SPM_blend_p25"], gg["SPM_blend_p75"] - gg[var]]
                    if var == "SPM_blend_p50" else None, fmt="o", ms=3, lw=0.6,
                    color=SENSOR_COLORS.get(s), label=s)
    ax.set_yscale("log")
    ax.set_ylabel(var)
    ax.legend(loc="upper left", fontsize=8)
    ax.set_title(station)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=200)
    plt.close(fig)


def cross_sensor(pairs, var, path=None):
    fig, ax = plt.subplots(figsize=(4, 4))
    x, y = pairs[f"{var}_s2"], pairs[f"{var}_ls"]
    ax.scatter(x, y, s=8, alpha=0.6)
    lo, hi = np.nanmin([x.min(), y.min()]), np.nanmax([x.max(), y.max()])
    ax.plot([lo, hi], [lo, hi], "k--", lw=0.8)
    if var != "ndti_p50":
        ax.set_xscale("log")
        ax.set_yscale("log")
    ax.set_xlabel(f"Sentinel-2 {var}")
    ax.set_ylabel(f"Landsat-8/9 {var}")
    ax.set_title(f"Same-day pairs (n={len(pairs)})", fontsize=9)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=200)
    plt.close(fig)


def obs_heatmap(counts, path=None):
    fig, ax = plt.subplots(figsize=(5, 0.3 * len(counts) + 1.2))
    im = ax.imshow(counts.to_numpy(), cmap="Blues", aspect="auto")
    ax.set_xticks(range(counts.shape[1]), counts.columns)
    ax.set_yticks(range(len(counts)), counts.index, fontsize=8)
    for (i, j), v in np.ndenumerate(counts.to_numpy()):
        ax.text(j, i, int(v), ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax, label="valid observations")
    ax.set_title("Clear-sky observations per season", fontsize=9)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=200)
    plt.close(fig)


def longitudinal(ratios, chain_id, var="SPM_blend_median", path=None):
    g = ratios[ratios["chain_id"] == chain_id]
    fig, ax = plt.subplots(figsize=(9, 3))
    for (season, year), gg in g.groupby(["season", "year"]):
        gg = gg.sort_values("km_from_mouth")
        ax.plot(gg["km_from_mouth"], gg[var], lw=0.7, alpha=0.6, label=f"{season} {year}")
    ax.invert_xaxis()
    ax.set_yscale("log")
    ax.set_xlabel("km from mouth")
    ax.set_ylabel(var)
    ax.set_title(f"{g['river'].iloc[0]} ({chain_id})")
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=200)
    plt.close(fig)
