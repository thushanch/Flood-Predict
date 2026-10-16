"""Google Earth Engine side of the pipeline.

Builds per-image water-reflectance products for Sentinel-2 MSI and
Landsat-8/9 OLI using the coefficients in `algorithms.py`, then reduces them
over station or reach polygons. Nothing here runs without an authenticated
Earth Engine session (`earthengine authenticate`).
"""
from __future__ import annotations

import ee

from . import algorithms as alg

S2_ID = "COPERNICUS/S2_SR_HARMONIZED"
CSP_ID = "GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED"
LANDSAT_IDS = {"L8": "LANDSAT/LC08/C02/T1_L2", "L9": "LANDSAT/LC09/C02/T1_L2"}
JRC_ID = "JRC/GSW1_4/GlobalSurfaceWater"
SCALE = {"S2": 20, "L8": 30, "L9": 30}

PRODUCT_BANDS = ["green", "red", "nir", "swir1", "ndti",
                 "T_dog", "SPM_red", "SPM_nir", "SPM_blend"]


def init(project: str) -> None:
    ee.Initialize(project=project)


# --------------------------------------------------------------------------
# Masks
# --------------------------------------------------------------------------
def static_water(occ_min: float, erode_m: float = 0) -> ee.Image:
    """Stable channel from JRC Global Surface Water occurrence (Pekel et al. 2016).

    Eroding by one pixel removes bank pixels contaminated by mixed land/water
    reflectance and the adjacency effect.
    """
    occ = ee.Image(JRC_ID).select("occurrence")
    water = occ.gte(occ_min).unmask(0)
    if erode_m:
        water = water.focalMin(radius=erode_m, units="meters")
    return water.rename("water")


# --------------------------------------------------------------------------
# Water-quality products (same formulas as algorithms.py)
# --------------------------------------------------------------------------
def _nechad(rho: ee.Image, A: float, C: float) -> ee.Image:
    return rho.multiply(A).divide(ee.Image(1).subtract(rho.divide(C)))


def _valid(rho: ee.Image, C: float) -> ee.Image:
    return rho.gt(0).And(rho.lt(C))


def _blend(red_est, nir_est, red_ok, nir_ok, rho_red) -> ee.Image:
    lo, hi = alg.DOGLIOTTI["lower"], alg.DOGLIOTTI["upper"]
    w = rho_red.subtract(lo).divide(hi - lo).clamp(0, 1)
    out = red_est.multiply(ee.Image(1).subtract(w)).add(nir_est.multiply(w))
    ok = (w.gte(1).Or(red_ok)).And(w.lte(0).Or(nir_ok))
    # where w == 0 the NIR term is 0*x, so a NaN/inf NIR value must not leak in
    out = out.where(w.lte(0), red_est).where(w.gte(1), nir_est)
    return out.updateMask(ok)


def add_products(refl: ee.Image, sensor: str, water: ee.Image, swir_max: float) -> ee.Image:
    """refl has bands green, red, nir, swir1 as water-leaving reflectance."""
    g, r, n, s = (refl.select(b) for b in ("green", "red", "nir", "swir1"))
    mndwi = g.subtract(s).divide(g.add(s))                     # Xu (2006)
    mask = (water.And(s.lt(swir_max)).And(mndwi.gt(0))
            .And(r.gt(0)).And(g.gt(0)))

    ndti = r.subtract(g).divide(r.add(g)).rename("ndti")       # Lacaux et al. (2007)

    d = alg.DOGLIOTTI
    t_red, t_nir = _nechad(r, d["A_red"], d["C_red"]), _nechad(n, d["A_nir"], d["C_nir"])
    t_dog = _blend(t_red, t_nir, _valid(r, d["C_red"]), _valid(n, d["C_nir"]), r).rename("T_dog")

    (a_r, c_r), (a_n, c_n) = alg.NECHAD_SPM[sensor]["red"], alg.NECHAD_SPM[sensor]["nir"]
    s_red, s_nir = _nechad(r, a_r, c_r), _nechad(n, a_n, c_n)
    r_ok, n_ok = _valid(r, c_r), _valid(n, c_n)
    spm_blend = _blend(s_red, s_nir, r_ok, n_ok, r).rename("SPM_blend")

    out = ee.Image.cat([
        refl, ndti, t_dog,
        s_red.updateMask(r_ok).rename("SPM_red"),
        s_nir.updateMask(n_ok).rename("SPM_nir"),
        spm_blend,
    ])
    return out.updateMask(mask)


# --------------------------------------------------------------------------
# Sensor collections
# --------------------------------------------------------------------------
def s2_collection(region, start, end, cfg) -> ee.ImageCollection:
    m = cfg["masking"]
    water = static_water(m["jrc_occurrence_min"], m["erode_m"])
    cs = ee.ImageCollection(CSP_ID)
    col = (ee.ImageCollection(S2_ID).filterBounds(region).filterDate(start, end)
           .linkCollection(cs, ["cs_cdf"]))

    def prep(img):
        clear = img.select("cs_cdf").gte(m["cs_plus_threshold"])   # Pasquarella et al. (2023)
        refl = (img.select(["B3", "B4", "B8A", "B11"], ["green", "red", "nir", "swir1"])
                .divide(10000).updateMask(clear))
        prod = add_products(refl, "S2", water, m["swir_max"])
        return ee.Image(prod.copyProperties(img, ["system:time_start"])).set({
            "sensor": "S2",
            "platform": img.get("SPACECRAFT_NAME"),
            "scene": img.get("system:index"),
        })

    return col.map(prep)


def landsat_collection(sensor, region, start, end, cfg) -> ee.ImageCollection:
    m = cfg["masking"]
    water = static_water(m["jrc_occurrence_min"], m["erode_m"])
    col = ee.ImageCollection(LANDSAT_IDS[sensor]).filterBounds(region).filterDate(start, end)

    def prep(img):
        # QA_PIXEL bits 1-4: dilated cloud, cirrus, cloud, cloud shadow
        clear = img.select("QA_PIXEL").bitwiseAnd(0b11110).eq(0)
        unsat = img.select("QA_RADSAT").eq(0)
        refl = (img.select(["SR_B3", "SR_B4", "SR_B5", "SR_B6"], ["green", "red", "nir", "swir1"])
                .multiply(0.0000275).add(-0.2)                    # Collection-2 L2 scaling
                .updateMask(clear.And(unsat)))
        prod = add_products(refl, sensor, water, m["swir_max"])
        return ee.Image(prod.copyProperties(img, ["system:time_start"])).set({
            "sensor": sensor,
            "platform": img.get("SPACECRAFT_ID"),
            "scene": img.get("system:index"),
        })

    return col.map(prep)


def collection(sensor, region, start, end, cfg) -> ee.ImageCollection:
    if sensor == "S2":
        return s2_collection(region, start, end, cfg)
    return landsat_collection(sensor, region, start, end, cfg)


# --------------------------------------------------------------------------
# Reductions
# --------------------------------------------------------------------------
def _reducer():
    return ee.Reducer.percentile([25, 50, 75]).combine(ee.Reducer.count(), sharedInputs=True)


def stations_fc(stations, buffer_m) -> ee.FeatureCollection:
    feats = [ee.Feature(ee.Geometry.Point([s["lon"], s["lat"]]).buffer(buffer_m),
                        {"station": s["id"], "river": s["river"]}) for s in stations]
    return ee.FeatureCollection(feats)


def reduce_images(col: ee.ImageCollection, regions: ee.FeatureCollection,
                  sensor: str, min_pixels: int) -> ee.FeatureCollection:
    scale = SCALE[sensor]

    def per_image(img):
        date = img.date()
        fc = img.reduceRegions(collection=regions, reducer=_reducer(), scale=scale, tileScale=4)
        return fc.map(lambda f: ee.Feature(None, f.toDictionary()).set({
            "date": date.format("YYYY-MM-dd"),
            "sensor": img.get("sensor"),
            "platform": img.get("platform"),
            "scene": img.get("scene"),
        }))

    return (col.map(per_image).flatten()
            .filter(ee.Filter.gte("red_count", min_pixels)))


def potential_pixels(regions: ee.FeatureCollection, cfg, scale: int, key: str = "station") -> dict:
    """Number of static-water pixels per region (denominator of valid fraction)."""
    m = cfg["masking"]
    water = static_water(m["jrc_occurrence_min"], m["erode_m"]).selfMask()
    fc = water.reduceRegions(collection=regions, reducer=ee.Reducer.count(), scale=scale)
    rows = fc.select([key, "count"]).getInfo()["features"]
    return {r["properties"][key]: r["properties"].get("count", 0) for r in rows}


def snap_station(lon, lat, cfg) -> dict:
    """Move a point to the nearest stable-water pixel within snap_search_m."""
    m = cfg["masking"]
    search = cfg["snap_search_m"]
    pt = ee.Geometry.Point([lon, lat])
    water = static_water(m["jrc_occurrence_min"], m["erode_m"])
    dist = ee.FeatureCollection([ee.Feature(pt)]).distance(search)
    img = dist.addBands(ee.Image.pixelLonLat()).updateMask(water)
    res = img.reduceRegion(ee.Reducer.min(3), pt.buffer(search), scale=30, maxPixels=1e8).getInfo()
    if res.get("min") is None:
        return {"ok": False}
    # inputs in band order: distance, longitude, latitude (pixelLonLat order)
    if not {"min1", "min2"} <= res.keys():
        raise RuntimeError(f"unexpected Reducer.min(3) output keys {sorted(res)}; update snap_station")
    new_lon, new_lat = res["min1"], res["min2"]
    # how much of the AOI is water? (high values => reservoir / lagoon, not a channel)
    aoi = ee.Geometry.Point([new_lon, new_lat]).buffer(cfg["station_buffer_m"])
    frac = (static_water(m["jrc_occurrence_min"]).reduceRegion(
        ee.Reducer.mean(), aoi, scale=30).get("water").getInfo())
    return {"ok": True, "lon": round(new_lon, 6), "lat": round(new_lat, 6),
            "moved_m": round(res["min"], 1), "water_fraction": round(frac or 0, 3)}


# --------------------------------------------------------------------------
# Export helpers
# --------------------------------------------------------------------------
STATION_COLUMNS = (["station", "river", "date", "sensor", "platform", "scene"]
                   + [f"{b}_{s}" for b in PRODUCT_BANDS for s in ("p25", "p50", "p75")]
                   + ["red_count", "SPM_blend_count"])


def export_table(fc, description, folder, selectors=None):
    task = ee.batch.Export.table.toDrive(
        collection=fc, description=description, folder=folder,
        fileFormat="CSV", selectors=selectors)
    task.start()
    return task


def download_table(fc, path, selectors=None):
    """Small tables only: direct CSV download instead of a Drive export."""
    import urllib.request
    url = fc.getDownloadURL(filetype="csv", selectors=selectors)
    urllib.request.urlretrieve(url, path)
    return path


# --------------------------------------------------------------------------
# Seasonal composites for the reach atlas
# --------------------------------------------------------------------------
def season_range(season: str, year: int):
    """Sri Lanka Dept. of Meteorology seasons; NEM of `year` = Dec(year-1)..Feb(year)."""
    return {
        "NEM": (f"{year - 1}-12-01", f"{year}-03-01"),
        "FIM": (f"{year}-03-01", f"{year}-05-01"),
        "SWM": (f"{year}-05-01", f"{year}-10-01"),
        "SIM": (f"{year}-10-01", f"{year}-12-01"),
    }[season]


def season_composite(sensor, region, season, year, cfg) -> ee.Image:
    start, end = season_range(season, year)
    col = collection(sensor, region, start, end, cfg)
    med = col.select(PRODUCT_BANDS).median()
    nobs = col.select("red").count().rename("n_obs")
    return med.addBands(nobs).set({"season": season, "year": year})


def reduce_reaches(img: ee.Image, reaches: ee.FeatureCollection, sensor: str) -> ee.FeatureCollection:
    reducer = ee.Reducer.median().combine(ee.Reducer.count(), sharedInputs=True)
    fc = img.select(["ndti", "T_dog", "SPM_blend", "n_obs"]).reduceRegions(
        collection=reaches, reducer=reducer, scale=SCALE[sensor], tileScale=4)
    return fc.map(lambda f: ee.Feature(None, f.toDictionary()).set({
        "season": img.get("season"), "year": img.get("year"), "sensor": sensor}))


def water_fraction(reaches: ee.FeatureCollection, cfg) -> ee.FeatureCollection:
    """Share of each reach buffer that is (non-eroded) stable water -> lentic flag."""
    water = static_water(cfg["masking"]["jrc_occurrence_min"])
    return water.reduceRegions(collection=reaches, reducer=ee.Reducer.mean(), scale=30)


# --------------------------------------------------------------------------
# Rainfall over upstream catchments (HydroBASINS, Lehner & Grill 2013)
# --------------------------------------------------------------------------
def basin_graph(bbox, basins_id):
    fc = ee.FeatureCollection(basins_id).filterBounds(ee.Geometry.Rectangle(bbox))
    ids = fc.aggregate_array("HYBAS_ID").getInfo()
    nxt = fc.aggregate_array("NEXT_DOWN").getInfo()
    return dict(zip(ids, nxt))


def upstream_ids(start_id, next_down: dict) -> list:
    """All basins draining to `start_id`, including itself."""
    children = {}
    for b, d in next_down.items():
        children.setdefault(d, []).append(b)
    out, stack = [], [start_id]
    while stack:
        b = stack.pop()
        out.append(b)
        stack.extend(children.get(b, []))
    return out


def catchment_fc(stations, cfg) -> ee.FeatureCollection:
    r = cfg["rainfall"]
    graph = basin_graph(cfg["reaches"]["bbox"], r["basins"])
    basins = ee.FeatureCollection(r["basins"])
    feats = []
    for s in stations:
        pt = ee.Geometry.Point([s["lon"], s["lat"]])
        hid = basins.filterBounds(pt).first().get("HYBAS_ID").getInfo()
        ids = upstream_ids(hid, graph)
        geom = basins.filter(ee.Filter.inList("HYBAS_ID", ids)).union().geometry()
        feats.append(ee.Feature(geom, {"station": s["id"], "n_basins": len(ids)}))
    return ee.FeatureCollection(feats)


def rainfall_series(catchments: ee.FeatureCollection, start, end, dataset) -> ee.FeatureCollection:
    col = ee.ImageCollection(dataset).filterDate(start, end).select("precipitation")

    def per_day(img):
        fc = img.reduceRegions(collection=catchments, reducer=ee.Reducer.mean(), scale=5566)
        return fc.map(lambda f: ee.Feature(None, {
            "station": f.get("station"),
            "date": img.date().format("YYYY-MM-dd"),
            "rain_mm": f.get("mean"),
        }))

    return col.map(per_day).flatten()
