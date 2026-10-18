"""Build the interactive atlas page (outputs/cog/river_sediment_atlas.html).

Reads outputs/cog/river_cells.csv, the QC'd station table and the station
analysis (outputs/cog_stations/*.csv), and injects them into map_template.html.
Narrative findings are generated from the numbers; edit FINDINGS_EXTRA to add
hand-written interpretation.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from sedrs.config import DATA_DIR, OUT_DIR, load_settings  # noqa: E402
from sedrs.seasons import season_of  # noqa: E402

HERE = Path(__file__).resolve().parent
cfg = load_settings()
cells = pd.read_csv(OUT_DIR / "cog" / "river_cells.csv")
st = pd.read_csv(DATA_DIR / "cog_analysis" / "stations" / "stations_S2.csv", parse_dates=["date"])
scenes = sum(1 for _ in (DATA_DIR / "cog" / "cells").glob("*.csv"))
sinfo = pd.read_csv(DATA_DIR / "cog" / "stations.csv").set_index("id")
extra_path = HERE / "findings_extra.json"
extra = json.loads(extra_path.read_text()) if extra_path.exists() else {}

SEAS = ["NEM", "FIM", "SWM", "SIM"]
LABEL = {
    "kelani_hanwella": "Kelani · Hanwella", "kelani_colombo": "Kelani · Colombo",
    "kalu_putupaula": "Kalu · Putupaula", "gin_baddegama": "Gin · Baddegama", "gin_gintota": "Gin · Gintota",
    "nilwala_matara": "Nilwala · Matara", "mahaweli_peradeniya": "Mahaweli · Peradeniya",
    "mahaweli_mahiyangana": "Mahaweli · Mahiyangana", "mahaweli_manampitiya": "Mahaweli · Manampitiya",
    "mahaweli_somawathiya": "Mahaweli · Somawathiya", "walawe_embilipitiya": "Walawe · Embilipitiya",
    "walawe_ambalantota": "Walawe · Ambalantota", "deduru_chilaw": "Deduru · Chilaw",
    "mahaoya_badalgama": "Maha Oya · Badalgama", "kelani_kitulgala": "Kelani · Kitulgala",
    "kalu_ratnapura": "Kalu · Ratnapura", "kalu_ellagawa": "Kalu · Ellagawa",
}


def r(v, nd=1):
    return None if v is None or not np.isfinite(v) else round(float(v), nd)


# ---------------------------------------------------------------- stations
st["season"] = season_of(st["date"]).values
stations = []
for sid, g in st.groupby("station"):
    if len(g) < 10:
        continue
    seas = g.groupby("season")["SPM_blend_p50"].agg(["median", "count"])
    m = g.groupby(g["date"].dt.month)["SPM_blend_p50"].agg(["median", "count"])
    monthly = [r(m.loc[k, "median"]) if k in m.index and m.loc[k, "count"] >= 3 else None for k in range(1, 13)]
    sv = {k: (r(seas.loc[k, "median"]) if k in seas.index and seas.loc[k, "count"] >= 3 else None) for k in SEAS}
    known = {k: v for k, v in sv.items() if v}
    note = ""
    if len(known) >= 2:
        hi, lo = max(known, key=known.get), min(known, key=known.get)
        note = (f"Highest in {hi} ({known[hi]:.0f} g m⁻³), lowest in {lo} ({known[lo]:.0f} g m⁻³): "
                f"a {known[hi] / known[lo]:.1f}× seasonal swing.")
    info = sinfo.loc[sid]
    stations.append({"id": sid, "label": LABEL.get(sid, sid), "river": info["river"], "zone": info["zone"],
                     "lon": float(info["lon"]), "lat": float(info["lat"]), "n": int(len(g)),
                     "all": r(g["SPM_blend_p50"].median()), "seasons": sv, "monthly": monthly,
                     "note": note + extra.get("station_notes", {}).get(sid, "")})
stations.sort(key=lambda s: (-s["lat"]))

# ---------------------------------------------------------------- cells
def arr(col, nd=1):
    return [r(v, nd) for v in cells[col]]


cell_json = {"lon": [round(v, 4) for v in cells["lon"]], "lat": [round(v, 4) for v in cells["lat"]],
             "spm_all": arr("spm_all"), "turb_all": arr("turb_all"), "ndti_all": arr("ndti_all", 3),
             "n": [int(v) for v in cells["n_scenes"]], "spm": {k: arr(f"spm_{k}") for k in SEAS}}

# ---------------------------------------------------------------- numbers for the summary
both = cells.dropna(subset=[f"spm_{k}" for k in SEAS])
seas_med = {k: both[f"spm_{k}"].median() for k in SEAS}
wet = [s for s in stations if s["zone"] == "wet" and s["all"]]
dry = [s for s in stations if s["zone"] == "dry" and s["all"]]
stats = [
    {"value": f"{scenes:,}", "label": "Sentinel-2 scenes read"},
    {"value": f"{len(cells):,}", "label": "1 km river cells mapped"},
    {"value": f"{np.median(cells['spm_all']):.0f}", "label": "median SPM, g m⁻³"},
    {"value": f"{max(seas_med.values()) / min(seas_med.values()):.1f}×", "label": "wettest / clearest season"},
]
hi_s, lo_s = max(seas_med, key=seas_med.get), min(seas_med, key=seas_med.get)
findings = [
    f"Across {len(both):,} river cells seen in all four seasons, the sediment signal peaks in <b>{hi_s}</b> "
    f"(median {seas_med[hi_s]:.0f} g m⁻³) and is lowest in <b>{lo_s}</b> ({seas_med[lo_s]:.0f} g m⁻³). "
    + " · ".join(f"{k} {v:.0f}" for k, v in seas_med.items()) + ".",
]
if wet and dry:
    findings.append(f"Wet-zone stations have a median of <b>{np.median([s['all'] for s in wet]):.0f}</b> g m⁻³ "
                    f"against <b>{np.median([s['all'] for s in dry]):.0f}</b> g m⁻³ at dry-zone stations "
                    f"({len(wet)} and {len(dry)} stations).")
findings += extra.get("findings", [])

meta = {
    "period": extra.get("period", "2024–2025"),
    "station_period": extra.get("station_period", "2019–2025"),
    "n_scenes": scenes,
    "default_station": extra.get("default_station", "kelani_hanwella"),
    "lede": extra.get("lede", ""),
    "how": extra.get("how", ""),
    "caveats": extra.get("caveats", []),
    "repro": extra.get("repro", ""),
}

ne = json.load(open(DATA_DIR / "cog" / "ne" / "ne_10m_admin_0_countries.geojson"))
g = next(f for f in ne["features"] if f["properties"].get("ADM0_A3") == "LKA")["geometry"]
polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
outline = [[[round(x, 3), round(y, 3)] for x, y in p[0]] for p in polys]

data = {"outline": outline, "cells": cell_json, "stations": stations, "stats": stats,
        "findings": findings, "meta": meta}
html = (HERE / "map_template.html").read_text().replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
path = OUT_DIR / "cog" / "river_sediment_atlas.html"
path.write_text(html, encoding="utf-8")
print(f"wrote {path} ({path.stat().st_size / 1e6:.2f} MB), {len(stations)} stations, {len(cells)} cells")
print("season medians:", {k: round(v, 1) for k, v in seas_med.items()})
