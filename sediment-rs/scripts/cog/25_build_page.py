"""Assemble the interactive 10 m river sediment page from the template and the web tiles.

    python scripts/cog/25_build_page.py
Writes data/cog/r10m/web/index.html (publish the web/ folder: index.html, index.json, cells.json, *.bin)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from sedrs.config import DATA_DIR  # noqa: E402

HERE = Path(__file__).resolve().parent
R = DATA_DIR / "cog" / "r10m"
WEB = R / "web"
stats = json.loads((R / "maps" / "stats.json").read_text())
metas = [json.loads(p.read_text()) for p in R.glob("*/meta.json")]
km = sum(m.get("river_skeleton_km", 0) for m in metas)
freq_n = sum(m.get("freq_scenes", 0) for m in metas)
views = np.median([v["median_views"] for v in stats["tiles"].values() if v["mapped_px"]])
cmap = plt.get_cmap("YlOrBr")
stops = [[int(round(c * 255)) for c in cmap(x)[:3]] for x in np.linspace(0, 1, 9)]
ramp = ", ".join(f"rgb({r},{g},{b}) {100 * i / 8:.0f}%" for i, (r, g, b) in enumerate(stops))
html = (HERE / "map10m_template.html").read_text()
for k, v in {"__RAMP__": ramp, "__STOPS__": json.dumps(stops), "__OUTLINE__": (R / "sl_outline.json").read_text(),
             "__LEAFLET_CSS__": (HERE / "vendor" / "leaflet-1.9.4.css").read_text(),
             "__KM__": f"{km:,.0f}", "__CELLS__": f"{stats['cells_1km']:,}",
             "__MED__": f"{stats['median_spm_cells']:.0f}", "__FREQN__": f"{freq_n:,}",
             "__VIEWS__": f"{views:.0f}"}.items():
    assert k in html, k
    html = html.replace(k, v)
(WEB / "index.html").write_text(html)
print("page", len(html) // 1024, "KB; files:", sorted(p.name for p in WEB.iterdir()))
