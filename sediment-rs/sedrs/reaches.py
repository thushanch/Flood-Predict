"""Turn HydroSHEDS river lines into ordered ~1 km reaches with chainage from the mouth.

Works on plain GeoJSON-like dicts so it needs no GIS stack. Ordering uses
upstream drainage area (UPLAND_SKM), which increases monotonically downstream
along any river, so it does not depend on the digitising direction of the lines.
"""
from __future__ import annotations

import math

R_EARTH_KM = 6371.0088


def haversine_km(a, b) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * R_EARTH_KM * math.asin(math.sqrt(h))


def _lines(geom) -> list:
    if geom["type"] == "LineString":
        return [geom["coordinates"]]
    if geom["type"] == "MultiLineString":
        return list(geom["coordinates"])
    raise ValueError(f"unsupported geometry {geom['type']}")


def _merge_parts(parts, tol_km):
    """Join the parts of a MultiLineString end-to-end where they touch."""
    line = list(parts[0])
    rest = [list(p) for p in parts[1:]]
    while rest:
        best = None
        for i, p in enumerate(rest):
            for rev_p in (False, True):
                q = p[::-1] if rev_p else p
                for at_end in (True, False):
                    d = haversine_km(line[-1] if at_end else line[0], q[0] if at_end else q[-1])
                    if best is None or d < best[0]:
                        best = (d, i, q, at_end)
        d, i, q, at_end = best
        if d > tol_km:
            break
        line = line + q[1:] if at_end else q[:-1] + line
        rest.pop(i)
    return line


def chain_reaches(features, group_key="BB_ID", name_key="BB_NAME", area_key="UPLAND_SKM",
                  tol_km=0.25, min_len_km=5.0) -> list[dict]:
    """Greedy upstream walks from the largest-area reach of each group.

    Returns chains as {"chain_id", "name", "coords"} with coords ordered
    mouth (downstream) -> source (upstream).
    """
    groups: dict = {}
    for f in features:
        groups.setdefault(f["properties"].get(group_key), []).append(f)

    chains = []
    for gid, feats in groups.items():
        items = [(f["properties"].get(area_key, 0) or 0,
                  _merge_parts(_lines(f["geometry"]), tol_km), f["properties"]) for f in feats]
        items.sort(key=lambda t: -t[0])
        remaining = items[:]
        k = 0
        while remaining:
            area, coords, props = remaining.pop(0)
            path = list(coords)
            # orient the outlet reach: its upstream end touches the next-smaller reach
            if remaining:
                nxt = remaining[0][1]
                d_end = min(haversine_km(path[-1], nxt[0]), haversine_km(path[-1], nxt[-1]))
                d_start = min(haversine_km(path[0], nxt[0]), haversine_km(path[0], nxt[-1]))
                if d_start < d_end:
                    path.reverse()
            while True:
                best = None
                for i, (a, c, _) in enumerate(remaining):
                    for rev in (False, True):
                        q = c[::-1] if rev else c
                        d = haversine_km(path[-1], q[0])
                        if d <= tol_km and (best is None or a > best[0]):
                            best = (a, i, q)
                if best is None:
                    break
                _, i, q = best
                path.extend(q[1:])
                remaining.pop(i)
            if line_length_km(path) >= min_len_km:
                name = props.get(name_key) or f"river_{gid}"
                chains.append({"chain_id": f"{gid}_{k}", "name": name, "coords": path})
                k += 1
    return chains


def line_length_km(coords) -> float:
    return sum(haversine_km(a, b) for a, b in zip(coords[:-1], coords[1:]))


def _interp(a, b, frac):
    return [a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac]


def cut_line(coords, seg_km: float) -> list[tuple[list, float, float]]:
    """Cut a polyline into consecutive pieces of `seg_km` (last piece may be shorter)."""
    out, cur, start_km, acc = [], [coords[0]], 0.0, 0.0
    for a, b in zip(coords[:-1], coords[1:]):
        d = haversine_km(a, b)
        pos = 0.0
        while d - pos > 0 and acc + (d - pos) >= seg_km:
            step = seg_km - acc
            pos += step
            p = _interp(a, b, pos / d)
            cur.append(p)
            out.append((cur, start_km, start_km + seg_km))
            start_km += seg_km
            cur, acc = [p], 0.0
        acc += d - pos
        cur.append(b)
    if len(cur) > 1 and acc > 1e-9:
        out.append((cur, start_km, start_km + acc))
    return out


def build_reaches(features, seg_km=1.0, **kw) -> list[dict]:
    """Ordered reach segments as GeoJSON features (chainage 0 = river mouth)."""
    reaches = []
    for ch in chain_reaches(features, **kw):
        for i, (seg, k0, k1) in enumerate(cut_line(ch["coords"], seg_km)):
            reaches.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": seg},
                "properties": {"reach_id": f"{ch['chain_id']}_{i:04d}", "chain_id": ch["chain_id"],
                               "river": ch["name"], "km_from_mouth": round((k0 + k1) / 2, 3)},
            })
    return reaches
