"""Tiny pixel-art flags drawn from half-blocks (no emoji, no width glitches).

A flag is 6 cells wide and 2 text rows tall; each cell is a ``▀`` whose foreground
paints the top pixel and background the bottom — a 6×4 pixel bitmap. Flags are
stripe-level approximations (no crests) built from a few pattern constructors,
keyed by the same FIFA trigrammes as :mod:`fifatui.flags`. Codes without a flag
(clubs, rare nations) get an LED badge with the team abbreviation instead, so the
UI never breaks.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.text import Text

from . import theme

WIDTH = 6   # cells
DEPTH = 4   # pixels (2 per text row)

# Flag ink: slightly softened primaries that read as lit LEDs on the dark board.
_W = "#f2efe4"    # white
_R = "#e0392e"    # red
_MAR = "#8d1b3d"  # maroon
_ORA = "#f7852d"  # orange
_Y = "#f2c832"    # yellow / gold
_GRN = "#2f9e50"  # green
_SKY = "#7fb8e6"  # sky blue
_B = "#3159c4"    # blue
_NAVY = "#25317d" # navy
_BLK = "#3a352b"  # "black" that stays visible on the near-black board


@dataclass(frozen=True)
class FlagSpec:
    pixels: tuple[tuple[str, ...], ...]  # DEPTH rows × WIDTH cols of hex colours


def _grid(fn) -> FlagSpec:
    return FlagSpec(tuple(tuple(fn(r, c) for c in range(WIDTH)) for r in range(DEPTH)))


def solid(color: str) -> FlagSpec:
    return _grid(lambda r, c: color)


def h_stripes(*colors: str) -> FlagSpec:
    rows = {2: (0, 0, 1, 1), 3: (0, 1, 1, 2), 4: (0, 1, 2, 3)}[len(colors)]
    return _grid(lambda r, c: colors[rows[r]])


def v_stripes(*colors: str) -> FlagSpec:
    cols = {2: (0, 0, 0, 1, 1, 1), 3: (0, 0, 1, 1, 2, 2), 6: tuple(range(6))}[len(colors)]
    return _grid(lambda r, c: colors[cols[c]])


def disc(bg: str, fg: str) -> FlagSpec:
    return _grid(lambda r, c: fg if r in (1, 2) and c in (2, 3) else bg)


def overlay_disc(base: FlagSpec, fg: str) -> FlagSpec:
    return _grid(lambda r, c: fg if r in (1, 2) and c in (2, 3) else base.pixels[r][c])


def nordic(bg: str, cross: str) -> FlagSpec:
    # Hoist-shifted cross (Denmark, Sweden, ...).
    return _grid(lambda r, c: cross if r in (1, 2) or c in (1, 2) else bg)


def george(bg: str, cross: str) -> FlagSpec:
    # Centred cross (England, Georgia, ...).
    return _grid(lambda r, c: cross if r in (1, 2) or c in (2, 3) else bg)


def saltire(bg: str, fg: str) -> FlagSpec:
    def px(r: int, c: int) -> str:
        d = round(c * (DEPTH - 1) / (WIDTH - 1))
        return fg if r in (d, DEPTH - 1 - d) else bg

    return _grid(px)


def canton(base: FlagSpec, color: str, w: int = 2, h: int = 2) -> FlagSpec:
    return _grid(lambda r, c: color if r < h and c < w else base.pixels[r][c])


def hoist(base: FlagSpec, color: str, w: int = 1) -> FlagSpec:
    return _grid(lambda r, c: color if c < w else base.pixels[r][c])


def quarters(tl: str, tr: str, bl: str, br: str) -> FlagSpec:
    return _grid(lambda r, c: (tl if c < 3 else tr) if r < 2 else (bl if c < 3 else br))


FLAGS: dict[str, FlagSpec] = {
    # South America
    "ARG": h_stripes(_SKY, _W, _SKY),
    "BRA": disc(_GRN, _Y),
    "URU": h_stripes(_W, _SKY, _W, _SKY),
    "COL": h_stripes(_Y, _Y, _B, _R),
    "ECU": h_stripes(_Y, _Y, _B, _R),
    "PER": v_stripes(_R, _W, _R),
    "CHI": canton(h_stripes(_W, _W, _R, _R), _NAVY),
    "VEN": h_stripes(_Y, _B, _R),
    "PAR": h_stripes(_R, _W, _B),
    "BOL": h_stripes(_R, _Y, _GRN),
    # North/Central America
    "USA": canton(h_stripes(_R, _W, _R, _W), _NAVY),
    "MEX": v_stripes(_GRN, _W, _R),
    "CAN": v_stripes(_R, _W, _R),
    "CRC": h_stripes(_B, _R, _R, _B),
    "HON": h_stripes(_SKY, _W, _SKY),
    "PAN": quarters(_W, _R, _B, _W),
    "JAM": saltire(_GRN, _Y),
    # Europe
    "FRA": v_stripes(_NAVY, _W, _R),
    "ITA": v_stripes(_GRN, _W, _R),
    "GER": h_stripes(_BLK, _R, _Y),
    "ESP": h_stripes(_R, _Y, _R),
    "POR": v_stripes(_GRN, _GRN, _R, _R, _R, _R),
    "NED": h_stripes(_R, _W, _NAVY),
    "BEL": v_stripes(_BLK, _Y, _R),
    "ENG": george(_W, _R),
    "SCO": saltire(_B, _W),
    "WAL": h_stripes(_W, _GRN),
    "IRL": v_stripes(_GRN, _W, _ORA),
    "CRO": h_stripes(_R, _W, _B),
    "SRB": h_stripes(_R, _B, _W),
    "SUI": disc(_R, _W),
    "AUT": h_stripes(_R, _W, _R),
    "POL": h_stripes(_W, _R),
    "CZE": hoist(h_stripes(_W, _R), _B, w=2),
    "SVK": h_stripes(_W, _B, _R),
    "SVN": h_stripes(_W, _B, _R),
    "UKR": h_stripes(_B, _Y),
    "DEN": nordic(_R, _W),
    "SWE": nordic(_B, _Y),
    "NOR": nordic(_R, _W),
    "FIN": nordic(_W, _B),
    "ISL": nordic(_B, _W),
    "TUR": disc(_R, _W),
    "GRE": canton(h_stripes(_B, _W, _B, _W), _B),
    "ROU": v_stripes(_B, _Y, _R),
    "HUN": h_stripes(_R, _W, _GRN),
    "BIH": disc(_B, _Y),
    "ALB": disc(_R, _BLK),
    "MKD": disc(_R, _Y),
    "GEO": george(_W, _R),
    # Africa
    "SEN": v_stripes(_GRN, _Y, _R),
    "MLI": v_stripes(_GRN, _Y, _R),
    "CIV": v_stripes(_ORA, _W, _GRN),
    "GHA": h_stripes(_R, _Y, _GRN),
    "CMR": v_stripes(_GRN, _R, _Y),
    "NGA": v_stripes(_GRN, _W, _GRN),
    "EGY": h_stripes(_R, _W, _BLK),
    "ALG": overlay_disc(v_stripes(_GRN, _W), _R),
    "TUN": disc(_R, _W),
    "MAR": disc(_R, _GRN),
    "RSA": h_stripes(_R, _W, _GRN, _B),
    "KEN": h_stripes(_BLK, _R, _GRN),
    "UGA": h_stripes(_BLK, _Y, _R),
    "ETH": h_stripes(_GRN, _Y, _R),
    "TAN": saltire(_GRN, _BLK),
    "COD": saltire(_SKY, _R),
    "GAB": h_stripes(_GRN, _Y, _B),
    # Asia & Oceania
    "JPN": disc(_W, _R),
    "KOR": disc(_W, _R),
    "CHN": canton(solid(_R), _Y, w=2, h=1),
    "SAU": disc(_GRN, _W),
    "IRN": h_stripes(_GRN, _W, _R),
    "IRQ": h_stripes(_R, _W, _BLK),
    "QAT": v_stripes(_W, _W, _MAR, _MAR, _MAR, _MAR),
    "UAE": hoist(h_stripes(_GRN, _W, _BLK), _R),
    "JOR": h_stripes(_BLK, _W, _GRN),
    "UZB": h_stripes(_SKY, _W, _GRN),
    "PRK": h_stripes(_B, _R, _R, _B),
    "THA": h_stripes(_R, _NAVY, _NAVY, _R),
    "VIE": disc(_R, _Y),
    "IDN": h_stripes(_R, _W),
    "IND": h_stripes(_ORA, _W, _GRN),
    "MAS": canton(h_stripes(_R, _W, _R, _W), _NAVY),
    "PHI": hoist(h_stripes(_B, _R), _W),
    "AUS": canton(solid(_NAVY), _R),
    "NZL": canton(solid(_NAVY), _R),
}


def flag_rows(abbr: str | None) -> list[Text] | None:
    """The flag as 2 half-block Text rows, or None for unknown codes."""
    spec = FLAGS.get((abbr or "").upper())
    if spec is None:
        return None
    rows = []
    for tr in range(2):
        t = Text()
        for c in range(WIDTH):
            top = spec.pixels[tr * 2][c]
            bottom = spec.pixels[tr * 2 + 1][c]
            t.append("▀", style=f"{top} on {bottom}")
        rows.append(t)
    return rows


def badge_rows(abbr: str, color_hex: str) -> list[Text]:
    """Fallback team mark: a small LED badge with the abbreviation (clubs etc.)."""
    label = (abbr or "?")[:4].upper().center(WIDTH)
    return [
        Text("▄" * WIDTH, style=color_hex),
        Text(label, style=f"bold {color_hex} on {theme.UNLIT}"),
    ]


def team_mark(abbr: str, color_hex: str) -> list[Text]:
    """Flag if we know the code, LED badge otherwise. Always 2 rows × 6 cells."""
    return flag_rows(abbr) or badge_rows(abbr, color_hex)


def team_chip(abbr: str, color_hex: str) -> Text:
    """One-row team mark for dense lines (event feed, ticker): ▐ABC▌-style chip."""
    t = Text()
    t.append("▐", style=color_hex)
    t.append((abbr or "?")[:3].upper(), style=f"bold {color_hex} on {theme.UNLIT}")
    t.append("▌", style=color_hex)
    return t
