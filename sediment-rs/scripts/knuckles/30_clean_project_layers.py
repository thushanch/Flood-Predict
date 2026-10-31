"""Clean the project's GIS layers (downstream basins, reservoirs, rivers) and log every issue.

    python scripts/knuckles/30_clean_project_layers.py <unzipped-input-dir> <output-dir>

The originals are never modified. Output (GeoPackage, EPSG:5235 SLD99 / Sri Lanka Grid 1999):
  project_layers_clean.gpkg   layers: micro_watersheds, sub_watersheds, basins, project_area,
                              reservoirs, reservoirs_added_from_satellite, rivers
  issues_log.csv              one row per issue: layer, feature, issue, action taken / decision needed

Decisions that belong to the project (duplicate IDs, sub-watershed names) are flagged, not changed.
"""
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import make_valid
from shapely.geometry import Polygon, shape
from shapely.ops import unary_union

warnings.filterwarnings("ignore")
src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
CRS = 5235
issues = []


def log(layer, feature, issue, action):
    issues.append({"layer": layer, "feature": feature, "issue": issue, "action": action})


def polygonal(g):
    """make_valid can return collections with lines/points: keep only the polygon parts."""
    g = make_valid(g)
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    parts = [p for p in getattr(g, "geoms", []) if p.geom_type in ("Polygon", "MultiPolygon")]
    return unary_union(parts) if parts else Polygon()


# ======================================================================= micro-watersheds
mws = gpd.read_file(next(src.rglob("All_Basins_Downstream.shp"))).to_crs(CRS)
mws["orig_row"] = np.arange(len(mws))
for i in np.nonzero(~mws.is_valid.to_numpy())[0]:
    log("micro_watersheds", mws.MWS_ID.iloc[i], "invalid geometry (ring self-intersection)", "repaired with make_valid")
mws["geometry"] = mws.geometry.apply(polygonal)

# null-ID sliver(s): merge into the neighbour sharing the longest boundary
for i in mws.index[mws.MWS_ID.isna()]:
    g = mws.geometry[i]
    nb = mws[(mws.index != i) & mws.intersects(g.buffer(1))]
    j = max(nb.index, key=lambda k: nb.geometry[k].intersection(g.buffer(1)).length)
    log("micro_watersheds", f"row {mws.orig_row[i]} (no MWS_ID, {g.area / 1e6:.3f} km2)",
        "polygon without MWS_ID", f"merged into neighbour {mws.MWS_ID[j]}")
    mws.loc[j, "geometry"] = unary_union([mws.geometry[j], g])
    mws = mws.drop(index=i)

# hairline gaps between neighbours: give each gap to the neighbour sharing the longest boundary
u = unary_union(mws.geometry)
gaps = [Polygon(h) for p in (u.geoms if u.geom_type == "MultiPolygon" else [u]) for h in p.interiors]
gaps = [g for g in gaps if g.area < 1e5]                     # only slivers < 0.1 km2; real holes are kept
sidx = mws.sindex
assign = {}                                                 # receiving polygon -> list of gaps (one union each)
for g in gaps:
    cand = list(sidx.query(g.buffer(1), predicate="intersects"))
    if cand:
        k = max(cand, key=lambda c: mws.geometry.iloc[c].boundary.intersection(g.buffer(1)).length)
        assign.setdefault(mws.index[k], []).append(g)
for idx, gs in assign.items():
    mws.loc[idx, "geometry"] = unary_union([mws.geometry[idx], *gs])
filled = sum(len(v) for v in assign.values())
gap_km2 = sum(g.area for g in gaps) / 1e6
log("micro_watersheds", "all", f"{len(gaps)} hairline gaps between neighbours ({gap_km2:.2f} km2)",
    f"{filled} filled, each assigned to the neighbour with the longest shared boundary")

# duplicate IDs: keep both, add a provisional unique ID
dup = mws.MWS_ID[mws.MWS_ID.duplicated(keep=False)]
mws["MWS_ID_unique"] = mws.MWS_ID
for v in dup.unique():
    rows = mws.index[mws.MWS_ID == v]
    for n, r in enumerate(rows):
        mws.loc[r, "MWS_ID_unique"] = f"{v}{chr(97 + n)}"
    areas = ", ".join(f"{mws.geometry[r].area / 1e6:.1f}" for r in rows)
    log("micro_watersheds", v, f"MWS_ID used by {len(rows)} different polygons ({areas} km2)",
        "kept; provisional MWS_ID_unique with suffix a/b; DECISION NEEDED: correct IDs")

# sub-watershed ID <-> name consistency: majority name by area
mws["area_km2_calc"] = (mws.area / 1e6).round(3)
maj = (mws.groupby(["SubWS_ID", "SubWS_Name"])["area_km2_calc"].sum().reset_index()
          .sort_values("area_km2_calc").groupby("SubWS_ID").tail(1).set_index("SubWS_ID")["SubWS_Name"])
mws["SubWS_Name_majority"] = mws.SubWS_ID.map(maj)
mws["name_mismatch"] = mws.SubWS_Name != mws.SubWS_Name_majority
for r in mws[mws.name_mismatch].itertuples():
    log("micro_watersheds", r.MWS_ID, f"SubWS_ID {r.SubWS_ID} has name '{r.SubWS_Name}' but most of {r.SubWS_ID} "
        f"is '{r.SubWS_Name_majority}'", "flagged; DECISION NEEDED: is the ID or the name wrong?")
for name, ids in mws.groupby("SubWS_Name")["SubWS_ID"].unique().items():
    if len(ids) > 1:
        log("micro_watersheds", name, f"one name used for several SubWS_IDs: {', '.join(ids)}",
            "flagged; DECISION NEEDED")
for r in mws[mws.area_km2_calc < 1].itertuples():
    log("micro_watersheds", r.MWS_ID, f"very small polygon ({r.area_km2_calc:.2f} km2)",
        "kept; check whether it should merge with a neighbour")
small_sw = mws.groupby("SubWS_ID")["area_km2_calc"].sum()
for k, a in small_sw[small_sw < 10].items():
    log("sub_watersheds", k, f"sub-watershed of only {a:.1f} km2", "kept; check whether it is a separate unit")

# ======================================================================= dissolved levels
sw = mws.dissolve(by="SubWS_ID", aggfunc={"Basin_ID": "first", "Basin_Name": "first",
                                          "SubWS_Name_majority": "first", "MWS_ID": "count"}).reset_index()
sw = sw.rename(columns={"MWS_ID": "n_MWS", "SubWS_Name_majority": "SubWS_Name"})
sw["area_km2"] = (sw.area / 1e6).round(2)
basins = mws.dissolve(by="Basin_Name", aggfunc={"Basin_ID": "first"}).reset_index()
basins["area_km2"] = (basins.area / 1e6).round(1)
area = gpd.GeoDataFrame({"name": ["Knuckles downstream project area"]},
                        geometry=[unary_union(mws.geometry)], crs=CRS)
area["area_km2"] = (area.area / 1e6).round(1)

# ======================================================================= reservoirs
res = gpd.read_file(next(src.rglob("reservoirs.shp")))
log("reservoirs", "all", "projection Everest 1830 (1937) Transverse Mercator with NO datum defined: features land "
    "~220 m west of the true position after reprojection", "assigned EPSG:5234 (Kandawala / Sri Lanka Grid), "
    "then reprojected to EPSG:5235")
res = res.set_crs(5234, allow_override=True).to_crs(CRS)
wkb = res.geometry.to_wkb()
for i in res.index[wkb.duplicated()]:
    log("reservoirs", res.NAME[i], "exact duplicate polygon", "removed")
res = res[~wkb.duplicated()].copy()
res["name_clean"] = res.NAME.str.strip().str.replace(r"\s+", " ", regex=True).str.title()
for i in res.index[(res.AREA <= 0) | (res.PERIMETER <= 0)]:
    log("reservoirs", res.NAME[i], "AREA/PERIMETER attribute is 0", "recomputed from geometry")
# same name AND within 1.5 km = parts of one reservoir; same name far apart = different reservoirs
# (e.g. Tissa Wewa in Anuradhapura and in Tissamaharama)
res["part_group"] = 0
for n, g in res.groupby("name_clean"):
    if len(g) == 1:
        continue
    idx = list(g.index)
    grp = {i: k for k, i in enumerate(idx)}
    for i in idx:
        for j in idx:
            if i < j and res.geometry[i].distance(res.geometry[j]) < 1500:
                gi, gj = grp[i], grp[j]
                for k in grp:
                    if grp[k] == gj:
                        grp[k] = gi
    for i in idx:
        res.loc[i, "part_group"] = grp[i]
    n_res = len(set(grp.values()))
    if n_res < len(g):
        log("reservoirs", n, f"split into {len(g)} polygons", f"dissolved into {n_res} feature(s) "
            "(parts within 1.5 km merged)")
    if n_res > 1:
        log("reservoirs", n, f"{n_res} different reservoirs share this name", "kept separate; suffix (1), (2) added")
res = res.dissolve(by=["name_clean", "part_group"]).reset_index()
dupname = res.name_clean.duplicated(keep=False)
res.loc[dupname, "name_clean"] = (res.loc[dupname, "name_clean"] + " ("
                                  + (res[dupname].groupby("name_clean").cumcount() + 1).astype(str) + ")")
res = res[["name_clean", "geometry"]].rename(columns={"name_clean": "name"})
res["area_km2"] = (res.area / 1e6).round(3)
res["perimeter_km"] = (res.length / 1e3).round(2)
res["in_project_area"] = res.intersects(area.geometry.iloc[0])
log("reservoirs", "Allai Wewa", "polygon does not overlap any mapped water (JRC occurrence >= 50 %)",
    "kept; check position or whether it is a seasonal wetland")
log("reservoirs", "Moragahakanda, Kalu Ganga reservoir", "missing from the layer (impounded 2018-2021)",
    "added from Sentinel-2/JRC water extent in layer reservoirs_added_from_satellite")

# Moragahakanda and Kalu Ganga from the satellite-derived masks (JRC union S2, as in 22_reservoirs.py)
added = []
try:
    import rasterio
    from rasterio.features import shapes
    from scipy import ndimage as ndi
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from sedrs import s2grid
    from sedrs.config import DATA_DIR
    freq_ds = rasterio.open(DATA_DIR / "cog" / "water_freq_20m.tif")
    sat = {"Moragahakanda (satellite)": (80.756, 7.671), "Kalu Ganga reservoir (satellite)": (80.834, 7.544)}
    for name, (lon, lat) in sat.items():
        x, y = gpd.GeoSeries(gpd.points_from_xy([lon], [lat]), crs=4326).to_crs(s2grid.CRS).iloc[0].coords[0]
        c, r = ~freq_ds.transform * (x, y)
        w = rasterio.windows.Window(int(c) - 400, int(r) - 400, 800, 800)
        f = np.nan_to_num(freq_ds.read(1, window=w)) >= 0.2
        lab, _ = ndi.label(f, structure=np.ones((3, 3)))
        k = lab[400, 400] or np.bincount(lab[380:420, 380:420].ravel())[1:].argmax() + 1
        geom = unary_union([shape(p) for p, v in shapes((lab == k).astype("uint8"),
                                                        transform=freq_ds.window_transform(w)) if v == 1])
        added.append({"name": name, "geometry": geom})
    added = gpd.GeoDataFrame(added, crs=s2grid.CRS).to_crs(CRS)
    added["area_km2"] = (added.area / 1e6).round(2)
    added["source"] = "Sentinel-2 water frequency >= 0.2 (clearest scenes 2022-25), 20 m"
except Exception as e:  # satellite layer is optional
    log("reservoirs", "satellite additions", f"could not build: {e!r}", "skipped")
    added = gpd.GeoDataFrame({"name": [], "area_km2": [], "source": []}, geometry=[], crs=CRS)

# ======================================================================= rivers: Strahler order from topology
riv = gpd.read_file(next(src.rglob("Rivers.shp"))).to_crs(CRS)
log("rivers", "all", "GRID_CODE is 1 for every segment; no names or stream order",
    "Strahler order computed from FROM_NODE/TO_NODE; names still needed from Survey Department data")
log("rivers", "all", "DEM-derived lines drift from observed channels on floodplains (median 73 m Mahaweli, "
    "296 m Kelani, 764 m Kalu vs Sentinel-2 channels)", "not corrected; use for overview only")
# Kahn topological pass: a segment's order is known once all segments ending at its FROM_NODE are done
frm, to = riv.FROM_NODE.to_numpy(), riv.TO_NODE.to_numpy()
ups = {}
for i, t in enumerate(to):
    ups.setdefault(t, []).append(i)
n_up = np.array([len(ups.get(f, [])) for f in frm])
down = {}
for i, f in enumerate(frm):
    for k in ups.get(f, []):
        down.setdefault(k, []).append(i)
order = np.zeros(len(riv), int)
ready = list(np.nonzero(n_up == 0)[0])
remaining = n_up.copy()
while ready:
    i = ready.pop()
    o = [order[k] for k in ups.get(frm[i], [])]
    if o:
        m = max(o)
        order[i] = m + 1 if o.count(m) > 1 else m
    else:
        order[i] = 1
    for j in down.get(i, []):
        remaining[j] -= 1
        if remaining[j] == 0:
            ready.append(j)
cyc = int((order == 0).sum())
if cyc:
    log("rivers", f"{cyc} segments", "segments on flow loops (topology cycles)", "stream order left as 0; check")
riv["strahler"] = order
riv["length_km"] = (riv.length / 1e3).round(3)
riv["in_project_area"] = riv.intersects(area.geometry.iloc[0])

# ======================================================================= write
gpkg = out / "project_layers_clean.gpkg"
keep = ["SubWS_ID", "Basin_ID", "Basin_Name", "SubWS_Name", "SubWS_Name_majority", "name_mismatch", "MWS_ID",
        "MWS_ID_unique", "Flow_Pos", "Area_km2", "area_km2_calc", "geometry"]
mws[keep].to_file(gpkg, layer="micro_watersheds", driver="GPKG")
sw.to_file(gpkg, layer="sub_watersheds", driver="GPKG")
basins.to_file(gpkg, layer="basins", driver="GPKG")
area.to_file(gpkg, layer="project_area", driver="GPKG")
res.to_file(gpkg, layer="reservoirs", driver="GPKG")
added.to_file(gpkg, layer="reservoirs_added_from_satellite", driver="GPKG")
riv.to_file(gpkg, layer="rivers", driver="GPKG")
pd.DataFrame(issues).to_csv(out / "issues_log.csv", index=False)
print(f"micro-watersheds {len(mws)}, sub-watersheds {len(sw)}, basins {len(basins)}, area {area.area_km2.iloc[0]} km2")
print(f"reservoirs {len(res)} ({int(res.in_project_area.sum())} in project area) + {len(added)} from satellite")
print(f"rivers {len(riv)}; Strahler orders {riv.strahler.value_counts().sort_index().to_dict()}")
print(f"issues logged: {len(issues)} -> {out / 'issues_log.csv'}")
print("valid after cleaning:", bool(mws.is_valid.all()), "| remaining gaps:",
      sum(1 for p in (lambda x: x.geoms if x.geom_type == "MultiPolygon" else [x])(unary_union(mws.geometry))
          for _ in p.interiors))
