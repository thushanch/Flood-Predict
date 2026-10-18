"""Offline analysis: QC, consistency checks, climatology, trends, rainfall response, hotspots.

    python scripts/05_analyse.py                       # data/ -> outputs/
    python scripts/05_analyse.py --data demo_data --out demo_outputs

Expected inputs under --data:
    stations/*.csv          from 01_extract_stations.py
    potential_pixels.json   from 01_extract_stations.py (optional)
    rainfall/*.csv          from 04_rainfall.py         (optional)
    reaches/*.csv           from 03_extract_reaches.py  (optional)
    reaches/reaches_water_fraction.csv                  (optional)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd  # noqa: E402

from sedrs import consistency, drivers, hotspots, plotting, qc, trends  # noqa: E402
from sedrs.config import DATA_DIR, OUT_DIR, load_settings  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--data", type=Path, default=DATA_DIR)
ap.add_argument("--out", type=Path, default=OUT_DIR)
ap.add_argument("--primary", default="SPM_blend",
                help="SPM product analysed as the primary variable (e.g. SPM_red for narrow, "
                     "NIR-contaminated channels)")
args = ap.parse_args()

cfg = load_settings()
m = cfg["masking"]
fig_dir = args.out / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)
summary = ["# Sediment signal analysis summary", ""]
if args.primary != "SPM_blend":
    summary += [f"Primary SPM product: **{args.primary}** (tables labelled SPM refer to it).", ""]

# ---------------------------------------------------------------- stations
raw = qc.load_station_csvs(sorted((args.data / "stations").glob("*.csv")))
pot_path = args.data / "potential_pixels.json"
pot = json.loads(pot_path.read_text()) if pot_path.exists() else None
if args.primary != "SPM_blend":
    # the analysis functions read SPM_blend_*; point them at the chosen product
    for q in ("p25", "p50", "p75"):
        raw[f"SPM_blend_{q}"] = raw[f"{args.primary}_{q}"]
df = qc.clean(raw, pot, min_pixels=m["min_pixels"], min_valid_fraction=m["min_valid_fraction"])
df.to_csv(args.out / "stations_clean.csv", index=False)
summary += [f"Station-image rows: {len(raw)} raw -> {len(df)} after QC "
            f"({df['station'].nunique()} stations, {df['date'].min():%Y-%m-%d} to {df['date'].max():%Y-%m-%d}).", ""]

counts = qc.observation_counts(df)
counts.to_csv(args.out / "observation_counts.csv")
plotting.obs_heatmap(counts, fig_dir / "observation_counts.png")
summary += ["## Clear-sky observations per season", "", counts.to_markdown(), ""]

# ---------------------------------------------------------------- consistency
xs = consistency.cross_sensor_table(df)
xs.to_csv(args.out / "cross_sensor.csv", index=False)
pairs = consistency.same_day_pairs(df, "SPM_blend_p50")
if len(pairs):
    plotting.cross_sensor(pairs, "SPM_blend_p50", fig_dir / "cross_sensor_spm.png")
summary += ["## Check 1 - Sentinel-2 vs Landsat-8/9 same-day agreement", "",
            xs.round(3).to_markdown(index=False), ""]

sp = consistency.spread_summary(df)
sp.to_csv(args.out / "algorithm_spread.csv")
summary += ["## Check 2 - Red vs NIR Nechad spread (switching window only)", "",
            sp.round(3).to_markdown(), ""]

dam_rows = [consistency.reservoir_trapping(df, p["up"], p["down"]) for p in cfg.get("dam_pairs", [])]
if dam_rows:
    dams = pd.DataFrame(dam_rows)
    dams.to_csv(args.out / "reservoir_trapping.csv", index=False)
    summary += ["## Check 3 - Reservoir trapping (downstream / upstream SPM)", "",
                dams.round(3).to_markdown(index=False), "", "Expected: ratio < 1.", ""]

# ---------------------------------------------------------------- rainfall
rain_files = sorted((args.data / "rainfall").glob("*.csv"))
rain = None
if rain_files:
    rain = pd.concat([pd.read_csv(p) for p in rain_files], ignore_index=True)
    rain["date"] = pd.to_datetime(rain["date"])
    rr = drivers.rainfall_response(df, rain)
    rr.to_csv(args.out / "rainfall_response.csv", index=False)
    summary += ["## Check 4 - Rainfall response (Spearman, antecedent catchment rain)", "",
                rr.round(3).to_markdown(index=False), "",
                "`plausible` = best window positive and significant (Bonferroni-adjusted).", ""]

# ---------------------------------------------------------------- patterns
plotting.climatology(df, path=fig_dir / "climatology_spm.png")
plotting.climatology(df, var="ndti_p50", path=fig_dir / "climatology_ndti.png", ylabel="NDTI")
for st in df["station"].unique():
    plotting.timeseries(df, st, rain, path=fig_dir / f"ts_{st}.png")

season_tab = (df.groupby(["station", "season"])["SPM_blend_p50"].median().unstack()
                .reindex(columns=["NEM", "FIM", "SWM", "SIM"]))
season_tab.to_csv(args.out / "seasonal_median_spm.csv")
summary += ["## Seasonal median SPM (g m-3, uncalibrated estimate)", "",
            season_tab.round(1).to_markdown(), ""]

monthly = qc.monthly_series(df)
tt = trends.trend_table(monthly)
tt.to_csv(args.out / "trends.csv", index=False)
summary += ["## Trends (seasonal Kendall / Hamed-Rao MK / Pettitt)", "",
            tt.round(3).to_markdown(index=False), "",
            "q = Benjamini-Hochberg FDR-adjusted p across stations; interpret only `*_significant`.", ""]

# ---------------------------------------------------------------- reaches
reach_files = [p for p in sorted((args.data / "reaches").glob("reaches_*.csv"))
               if "water_fraction" not in p.name]
if reach_files:
    rd = pd.concat([pd.read_csv(p) for p in reach_files], ignore_index=True)
    wf_path = args.data / "reaches" / "reaches_water_fraction.csv"
    if wf_path.exists():
        wf = pd.read_csv(wf_path)[["reach_id", "water_fraction"]]
        rd = rd.merge(wf, on="reach_id", how="left")
        rd["lentic"] = rd["water_fraction"] > cfg["reaches"]["lentic_water_fraction"]
    else:
        rd["lentic"] = False
    h = cfg["hotspots"]
    ratios = hotspots.longitudinal_ratios(rd, k=h["upstream_window"])
    ratios.to_csv(args.out / "reach_ratios.csv", index=False)
    cand = hotspots.candidates(ratios, h["jump_ratio"], h["min_years"])
    cand.to_csv(args.out / "hotspot_candidate_reaches.csv", index=False)
    clusters = hotspots.cluster(cand, cfg["reaches"]["segment_km"])
    clusters.to_csv(args.out / "hotspots.csv", index=False)
    for cid in cand["chain_id"].unique()[:10]:
        plotting.longitudinal(ratios, cid, path=fig_dir / f"profile_{cid}.png")
    summary += ["## Hotspot candidates (recurring downstream jumps)", "",
                clusters.head(30).round(2).to_markdown(index=False) if len(clusters) else "None found.", "",
                "Candidates must be verified on high-resolution imagery (confluences mimic hotspots).", ""]

(args.out / "summary.md").write_text("\n".join(summary), encoding="utf-8")
print("\n".join(summary))
print(f"\nOutputs in {args.out}")
