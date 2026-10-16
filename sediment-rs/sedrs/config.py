"""Load settings.yaml and (if present) the snapped station file."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"


def load_settings(path: Path | str | None = None) -> dict:
    path = Path(path) if path else CONFIG_DIR / "settings.yaml"
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    snapped = CONFIG_DIR / "stations_snapped.yaml"
    if path.parent == CONFIG_DIR and snapped.exists():
        with open(snapped, encoding="utf-8") as f:
            cfg["stations"] = yaml.safe_load(f)["stations"]
        cfg["_stations_snapped"] = True
    else:
        cfg["_stations_snapped"] = False
    return cfg


def station_table(cfg: dict):
    import pandas as pd
    return pd.DataFrame(cfg["stations"]).set_index("id")
