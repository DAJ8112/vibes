"""A blocky ASCII world map for the console ``where`` command.

Continents are rasterized from a handful of lat/lon boxes onto an equirectangular
grid, so a marker placed with the *same* projection always lands on the right
landmass. The chunky, low-res look is deliberate — it matches the board's pixel
aesthetic rather than aiming for cartographic accuracy.
"""

from __future__ import annotations

GLOBE_W = 56
GLOBE_H = 18

LAND = "▓"
OCEAN = " "
MARK = "◉"

# Rough continent silhouettes as (lat_hi, lat_lo, lon_west, lon_east) boxes.
_LAND_BOXES = (
    # North America
    (72, 55, -168, -62),
    (55, 30, -128, -68),
    (30, 16, -116, -86),
    (24, 8, -106, -60),   # Central America / Caribbean
    # South America
    (11, -6, -82, -35),
    (-6, -35, -74, -35),
    (-35, -55, -74, -64),
    # Europe
    (71, 46, -10, 30),
    (60, 40, 6, 42),
    # Africa
    (37, 16, -16, 32),
    (16, -12, -12, 44),
    (-12, -35, 12, 40),
    # Asia
    (75, 46, 42, 180),
    (46, 22, 46, 146),
    (34, 8, 70, 122),     # India / SE Asia
    # Australia
    (-11, -39, 113, 154),
)


def project(lat: float, lon: float) -> tuple[int, int]:
    """Map lat/lon to (row, col) on the GLOBE_W×GLOBE_H equirectangular grid."""
    col = round((lon + 180.0) / 360.0 * (GLOBE_W - 1))
    row = round((90.0 - lat) / 180.0 * (GLOBE_H - 1))
    col = min(GLOBE_W - 1, max(0, col))
    row = min(GLOBE_H - 1, max(0, row))
    return row, col


def _blank_grid() -> list[list[str]]:
    grid = [[OCEAN] * GLOBE_W for _ in range(GLOBE_H)]
    for lat_hi, lat_lo, lon_w, lon_e in _LAND_BOXES:
        r0, c0 = project(lat_hi, lon_w)
        r1, c1 = project(lat_lo, lon_e)
        for r in range(min(r0, r1), max(r0, r1) + 1):
            for c in range(min(c0, c1), max(c0, c1) + 1):
                grid[r][c] = LAND
    return grid


def world_map(mark_lat: float | None = None, mark_lon: float | None = None) -> list[str]:
    """The world map as rows of chars; a marker is stamped at mark_lat/lon if given."""
    grid = _blank_grid()
    if mark_lat is not None and mark_lon is not None:
        r, c = project(mark_lat, mark_lon)
        grid[r][c] = MARK
    return ["".join(row) for row in grid]
