import numpy as np

from sedrs import cog, s2grid


def test_river_mask_keeps_channels_drops_tanks_and_lakes():
    occ = np.zeros((400, 400), np.uint8)
    occ[50:53, 20:380] = 100              # 3-px river, 360 px long (~10 km at 27.7 m)
    occ[52, 200:203] = 0                  # small gap (bridge) - must still be one river
    occ[200:215, 50:65] = 100             # compact tank 15x15
    occ[250:380, 200:380] = 100           # wide lake / reservoir
    mask, stats, _ = cog.river_mask(occ, occ_min=50)
    assert mask[51, 100] and mask[51, 300]
    assert not mask[207, 57]
    assert not mask[300, 300]
    assert stats["kept_components"] == 1


def test_national_grid_alignment():
    from rasterio.transform import from_origin
    # S2 tile 44NLN upper-left corner (300000, 800040) lies on the 20 m grid
    r, c = s2grid.offset(from_origin(300000.0, 800040.0, 20, 20))
    assert (s2grid.X0 + c * 20, s2grid.Y1 - r * 20) == (300000.0, 800040.0)
