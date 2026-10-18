"""List Sentinel-2 L2A scenes over Sri Lanka from the public S3 bucket (no STAC API).

    python scripts/cog/11_list_scenes.py 2019 2025
Writes data/cog/scenes.csv
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd  # noqa: E402

from sedrs import cog  # noqa: E402
from sedrs.config import DATA_DIR  # noqa: E402

y0, y1 = (int(a) for a in sys.argv[1:3]) if len(sys.argv) > 2 else (2024, 2025)
t0 = time.time()
rows = cog.list_scenes(cog.SL_TILES, range(y0, y1 + 1))
df = pd.DataFrame(rows).sort_values(["tile", "date"])
path = DATA_DIR / "cog" / "scenes.csv"
if path.exists():
    df = pd.concat([pd.read_csv(path), df]).drop_duplicates("id").sort_values(["tile", "date"])
df.to_csv(path, index=False)
print(f"{len(df)} scenes listed in {time.time() - t0:.0f}s -> {path}")
print(df.groupby("tile")["cloud"].describe()[["count", "25%", "50%"]].round(0).to_string())
print("baseline/offset:", df.groupby("offset").size().to_dict())
