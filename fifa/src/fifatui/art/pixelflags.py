"""Pixel-art flags drawn from half-blocks (no emoji, no width glitches).

A flag is a **resolution-independent** pattern that renders to any ``width`` (cells)
× ``depth`` (pixels) grid; each ``▀`` cell packs two vertical pixels (top = fg, bottom
= bg). The compact contexts (match list, shootout) render at ``SMALL`` (6×4 → 2 rows);
the scoreboard renders at ``LARGE`` (18×12 → 6 rows), where flags gain real detail:
crisp stripes/crosses, procedural stars & crescents, and a curated set of hand-drawn
crest bitmaps (Canada leaf, Korea taegeuk, Brazil globe, Mexico emblem). Codes without
a flag get an LED badge with the abbreviation, so the UI never breaks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from rich.text import Text

from . import theme

#: Default (compact) render size, in cells wide × pixels deep. 2 text rows.
WIDTH = 6
DEPTH = 4
SMALL = (WIDTH, DEPTH)
#: Scoreboard render size — 8 text rows, same 3:2 aspect as the compact mark.
LARGE = (24, 16)
#: Hand-drawn crest bitmaps only paint at/above this depth (large board only);
#: below it a marquee flag falls back to its plain field pattern.
_BITMAP_MIN_DEPTH = 8

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

Grid = list  # list[list[str]]
FieldFn = Callable[[int, int], "list[list[str]]"]
EmblemFn = Callable[["list[list[str]]", int, int], None]


@dataclass(frozen=True)
class Flag:
    """A field pattern plus an optional emblem painted on top."""

    field: FieldFn
    emblem: EmblemFn | None = None


# ---- field pattern constructors (resolution-relative) -----------------------

def solid(color: str) -> FieldFn:
    return lambda W, D: [[color] * W for _ in range(D)]


def h_stripes(*colors: str) -> FieldFn:
    n = len(colors)
    return lambda W, D: [[colors[min(n - 1, r * n // D)]] * W for r in range(D)]


def v_stripes(*colors: str) -> FieldFn:
    n = len(colors)

    def f(W: int, D: int) -> list[list[str]]:
        row = [colors[min(n - 1, c * n // W)] for c in range(W)]
        return [list(row) for _ in range(D)]

    return f


def _ellipse(g: list[list[str]], W: int, D: int, fg: str, rxf: float, ryf: float,
             cxf: float = 0.5, cyf: float = 0.5) -> None:
    cx, cy = W * cxf - 0.5, D * cyf - 0.5
    rx, ry = W * rxf, D * ryf
    for r in range(D):
        for c in range(W):
            if ((c - cx) / rx) ** 2 + ((r - cy) / ry) ** 2 <= 1.0:
                g[r][c] = fg


def disc(bg: str, fg: str) -> FieldFn:
    def f(W: int, D: int) -> list[list[str]]:
        g = [[bg] * W for _ in range(D)]
        _ellipse(g, W, D, fg, 0.28, 0.34)
        return g

    return f


def overlay_disc(base: FieldFn, fg: str) -> FieldFn:
    def f(W: int, D: int) -> list[list[str]]:
        g = base(W, D)
        _ellipse(g, W, D, fg, 0.24, 0.30)
        return g

    return f


def _band(center: float, thick: int, n: int) -> range:
    start = int(round(center - thick / 2))
    start = max(0, min(start, n - thick))
    return range(start, start + thick)


def nordic(bg: str, cross: str) -> FieldFn:
    def f(W: int, D: int) -> list[list[str]]:
        g = [[bg] * W for _ in range(D)]
        vcols = set(_band(W * 0.34, max(2, round(W * 0.16)), W))
        hrows = set(_band((D - 1) / 2, max(2, round(D * 0.22)), D))
        for r in range(D):
            for c in range(W):
                if c in vcols or r in hrows:
                    g[r][c] = cross
        return g

    return f


def george(bg: str, cross: str) -> FieldFn:
    def f(W: int, D: int) -> list[list[str]]:
        g = [[bg] * W for _ in range(D)]
        vcols = set(_band((W - 1) / 2, max(2, round(W * 0.16)), W))
        hrows = set(_band((D - 1) / 2, max(2, round(D * 0.22)), D))
        for r in range(D):
            for c in range(W):
                if c in vcols or r in hrows:
                    g[r][c] = cross
        return g

    return f


def saltire(bg: str, fg: str) -> FieldFn:
    def f(W: int, D: int) -> list[list[str]]:
        g = [[bg] * W for _ in range(D)]
        t = 0.16
        for r in range(D):
            y = r / (D - 1) if D > 1 else 0.5
            for c in range(W):
                x = c / (W - 1) if W > 1 else 0.5
                if abs(x - y) < t or abs(x - (1 - y)) < t:
                    g[r][c] = fg
        return g

    return f


def saltire4(tb: str, lr: str, cross: str) -> FieldFn:
    """Saltire with distinct top/bottom and left/right triangles (Jamaica)."""

    def f(W: int, D: int) -> list[list[str]]:
        g = [[tb] * W for _ in range(D)]
        t = 0.16
        for r in range(D):
            y = (r + 0.5) / D
            for c in range(W):
                x = (c + 0.5) / W
                if abs(x - y) < t or abs(x - (1 - y)) < t:
                    g[r][c] = cross
                elif abs(x - 0.5) > abs(y - 0.5):
                    g[r][c] = lr
        return g

    return f


def diagonal(tl: str, br: str, band: str, edge: str) -> FieldFn:
    """Diagonal band (lower-hoist to upper-fly) with edging (Tanzania, DR Congo)."""

    def f(W: int, D: int) -> list[list[str]]:
        g = [[tl] * W for _ in range(D)]
        for r in range(D):
            y = (r + 0.5) / D
            for c in range(W):
                s = (c + 0.5) / W + y
                d = abs(s - 1)
                if d < 0.14:
                    g[r][c] = band
                elif d < 0.24:
                    g[r][c] = edge
                elif s > 1:
                    g[r][c] = br
        return g

    return f


def wedge(base: FieldFn, color: str, wf: float = 0.45) -> FieldFn:
    """Hoist-side triangle over a striped field (Czechia, Philippines, Jordan)."""

    def f(W: int, D: int) -> list[list[str]]:
        g = base(W, D)
        for r in range(D):
            depth = W * wf * (1 - abs(2 * (r + 0.5) / D - 1))
            for c in range(W):
                if c + 0.5 <= depth:
                    g[r][c] = color
        return g

    return f


def serrated(left: str, right: str, split_f: float = 0.34, teeth: int = 9) -> FieldFn:
    """Vertical split with a toothed boundary (Qatar)."""

    def f(W: int, D: int) -> list[list[str]]:
        depth = max(1.0, W * 0.06)
        base_edge = W * split_f
        g = []
        for r in range(D):
            out = ((r * teeth) // D) % 2 == 0
            edge = base_edge + (depth / 2 if out else -depth / 2)
            g.append([left if c + 0.5 < edge else right for c in range(W)])
        return g

    return f


def canton(base: FieldFn, color: str, wf: float = 1 / 3, hf: float = 1 / 2) -> FieldFn:
    def f(W: int, D: int) -> list[list[str]]:
        g = base(W, D)
        cw, ch = max(1, round(W * wf)), max(1, round(D * hf))
        for r in range(ch):
            for c in range(cw):
                g[r][c] = color
        return g

    return f


def hoist(base: FieldFn, color: str, wf: float = 1 / 6) -> FieldFn:
    def f(W: int, D: int) -> list[list[str]]:
        g = base(W, D)
        cw = max(1, round(W * wf))
        for r in range(D):
            for c in range(cw):
                g[r][c] = color
        return g

    return f


def quarters(tl: str, tr: str, bl: str, br: str) -> FieldFn:
    def f(W: int, D: int) -> list[list[str]]:
        mw, mh = W // 2, D // 2
        return [
            [(tl if c < mw else tr) if r < mh else (bl if c < mw else br)
             for c in range(W)]
            for r in range(D)
        ]

    return f


# ---- procedural emblems (scale cleanly to any size) -------------------------

def _star_poly(cx: float, cy: float, rout: float, rin: float, points: int,
               rot_deg: float) -> list[tuple[float, float]]:
    verts = []
    for i in range(points * 2):
        ang = math.radians(rot_deg) + math.pi * i / points
        rad = rout if i % 2 == 0 else rin
        verts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    return verts


def _in_poly(x: float, y: float, poly: list[tuple[float, float]]) -> bool:
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


#: Sub-pixel sample offsets: 2×2 supersampling so thin shapes (star tips) that
#: pass between pixel centres still land on a pixel.
_SUBSAMPLES = ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75))


def _paint_poly(g: list[list[str]], W: int, D: int, fg: str,
                poly: list[tuple[float, float]]) -> None:
    for r in range(D):
        for c in range(W):
            if any(_in_poly(c + dx, r + dy, poly) for dx, dy in _SUBSAMPLES):
                g[r][c] = fg


def star(fg: str, points: int = 5, r_frac: float = 0.42,
         cxf: float = 0.5, cyf: float = 0.5) -> EmblemFn:
    def emblem(g: list[list[str]], W: int, D: int) -> None:
        rout = D * r_frac
        poly = _star_poly(W * cxf, D * cyf, rout, rout * 0.44, points, -90)
        _paint_poly(g, W, D, fg, poly)

    return emblem


def crescent(fg: str, with_star: bool = True) -> EmblemFn:
    def emblem(g: list[list[str]], W: int, D: int) -> None:
        cx, cy = W * 0.42, D * 0.5
        rout = D * 0.40
        cx2, r2 = cx + rout * 0.55, rout * 0.88
        for r in range(D):
            for c in range(W):
                hit = False
                for dx, dy in _SUBSAMPLES:
                    x, y = c + dx, r + dy
                    d1 = ((x - cx) / rout) ** 2 + ((y - cy) / rout) ** 2
                    d2 = ((x - cx2) / r2) ** 2 + ((y - cy) / r2) ** 2
                    if d1 <= 1 and d2 > 1:
                        hit = True
                        break
                if hit:
                    g[r][c] = fg
        if with_star and W >= 10:
            rs = D * 0.20
            poly = _star_poly(W * 0.62, D * 0.5, rs, rs * 0.44, 5, -90)
            _paint_poly(g, W, D, fg, poly)

    return emblem


def dot(fg: str, cxf: float = 0.5, cyf: float = 0.5, r_frac: float = 0.16) -> EmblemFn:
    """A small filled disc — crest hints (POR sphere, ESP crest) and seals."""

    def emblem(g: list[list[str]], W: int, D: int) -> None:
        _ellipse(g, W, D, fg, r_frac * D / W, r_frac, cxf, cyf)

    return emblem


def fly_triangle(fg: str, x0: float = 0.30, x1: float = 0.92, y1: float = 0.85) -> EmblemFn:
    """Right triangle hanging from the top edge toward the fly (Bosnia)."""

    def emblem(g: list[list[str]], W: int, D: int) -> None:
        for r in range(D):
            yf = (r + 0.5) / D
            for c in range(W):
                xf = (c + 0.5) / W
                if x0 <= xf <= x1 and yf <= (xf - x0) / (x1 - x0) * y1:
                    g[r][c] = fg

    return emblem


def diamond(fg: str, rxf: float = 0.40, ryf: float = 0.42) -> EmblemFn:
    def emblem(g: list[list[str]], W: int, D: int) -> None:
        cx, cy = (W - 1) / 2, (D - 1) / 2
        for r in range(D):
            for c in range(W):
                if abs((c - cx) / (W * rxf)) + abs((r - cy) / (D * ryf)) <= 1:
                    g[r][c] = fg

    return emblem


# ---- hand-drawn crest bitmaps (large board only) ----------------------------

def bitmap(art: list[str], key: dict[str, str],
           cxf: float = 0.5, cyf: float = 0.5) -> EmblemFn:
    """Paint an indexed-colour bitmap **1:1** (no scaling — art is authored at its
    true pixel size for the large board), centred at the fractional anchor and
    clipped to the grid. Chars absent from ``key`` are transparent. Skipped below
    the large threshold so compact marks keep their plain field."""
    ah = len(art)
    aw = max(len(row) for row in art)

    def emblem(g: list[list[str]], W: int, D: int) -> None:
        if D < _BITMAP_MIN_DEPTH:
            return
        x0 = round(W * cxf - aw / 2)
        y0 = round(D * cyf - ah / 2)
        for ar, row in enumerate(art):
            r = y0 + ar
            if not 0 <= r < D:
                continue
            for ac, ch in enumerate(row):
                c = x0 + ac
                col = key.get(ch)
                if col is not None and 0 <= c < W:
                    g[r][c] = col

    return emblem


def compose(*emblems: EmblemFn) -> EmblemFn:
    def emblem(g: list[list[str]], W: int, D: int) -> None:
        for e in emblems:
            e(g, W, D)

    return emblem


def large_only(inner: EmblemFn) -> EmblemFn:
    """Skip a procedural emblem below the large threshold (where it would smear
    over a feature that is itself only 1–2 px, e.g. a canton)."""

    def emblem(g: list[list[str]], W: int, D: int) -> None:
        if D >= _BITMAP_MIN_DEPTH:
            inner(g, W, D)

    return emblem


# Crest art is authored at its exact display pixel size for the LARGE (24×16)
# board and painted 1:1 — never resampled, so shapes stay whole. "." = transparent.

#: Canada — 8×9 maple leaf (three-point crown, solid body, stem), white third.
_CAN_LEAF = bitmap(
    [
        "...rr...",
        ".r.rr.r.",
        ".rrrrrr.",
        "rrrrrrrr",
        "rrrrrrrr",
        ".rrrrrr.",
        "..rrrr..",
        "...rr...",
        "...rr...",
    ],
    {"r": _R},
)

#: South Korea — full 24×16 face: taegeuk disc + the four corner trigrams
#: (☰ geon, ☵ gam, ☲ ri, ☷ gon). Opaque white masks the small-size disc field.
_KOR_FACE = bitmap(
    [
        "wwwwwwwwwwwwwwwwwwwwwwww",
        "wwwwwwwwwwwwwwwwwwwwwwww",
        "wwkkkkkwwwwwwwwwwwkkwkkw",
        "wwwwwwwwwwrrrrrwwwwwwwww",
        "wwkkkkkwwrrrrrrrwwkkkkkw",
        "wwwwwwwwrrrrrrrrrwwwwwww",
        "wwkkkkkrrrrrrrrrrrkkwkkw",
        "wwwwwwwrrrrrrrrbbbwwwwww",
        "wwwwwwwrrrrrbbbbbbwwwwww",
        "wwkkkkkrrbbbbbbbbbkkwkkw",
        "wwwwwwwbbbbbbbbbbbwwwwww",
        "wwkkwkkwbbbbbbbbbwkkwkkw",
        "wwwwwwwwwbbbbbbbwwwwwwww",
        "wwkkkkkwwwbbbbbwwwkkwkkw",
        "wwwwwwwwwwwwwwwwwwwwwwww",
        "wwwwwwwwwwwwwwwwwwwwwwww",
    ],
    {"w": _W, "r": _R, "b": _NAVY, "k": _BLK},
)

#: Brazil — 10×8 blue globe with the white banner, sits inside the yellow diamond.
_BRA_GLOBE = bitmap(
    [
        "...bbbb...",
        ".bbbbbbbb.",
        "bbbbbbbbbb",
        "wwwwwwwwww",
        "bbbbbbbbbb",
        "bbbbbbbbbb",
        ".bbbbbbbb.",
        "...bbbb...",
    ],
    {"b": _B, "w": _W},
)

#: Mexico — 6×10 eagle over the cactus, centred in the white third.
_MEX_EAGLE = bitmap(
    [
        "k....k",
        "kk..kk",
        ".kkkk.",
        "kkkkkk",
        "kkkkkk",
        ".kkkk.",
        "..kk..",
        ".gg.g.",
        ".gggg.",
        "..gg..",
    ],
    {"k": _BLK, "g": _GRN},
)

#: Paraguay — 7×5 seal: green wreath ring around a gold star, in the white band.
_PAR_SEAL = bitmap(
    [
        ".ggggg.",
        "gg...gg",
        "g.yyy.g",
        "gg...gg",
        ".ggggg.",
    ],
    {"g": _GRN, "y": _Y},
)

#: Argentina — 8×5 sun of May, kept inside the white band.
_ARG_SUN = bitmap(
    [
        "y..yy..y",
        ".yyyyyy.",
        "yyyyyyyy",
        ".yyyyyy.",
        "y..yy..y",
    ],
    {"y": _Y},
)

#: Uruguay — 10×8 white canton with the gold sun, anchored at the hoist top.
_URU_SUN = bitmap(
    [
        "wwwwwwwwww",
        "wwywyywyww",
        "wwwyyyywww",
        "wwyyyyyyww",
        "wwyyyyyyww",
        "wwwyyyywww",
        "wwywyywyww",
        "wwwwwwwwww",
    ],
    {"w": _W, "y": _Y},
    cxf=5 / 24, cyf=0.25,
)

#: USA — scattered white stars for the canton.
_USA_STARS = bitmap(
    [
        "w.w.w.w",
        ".w.w.w.",
        "w.w.w.w",
        ".w.w.w.",
        "w.w.w.w",
    ],
    {"w": _W},
    cxf=4.5 / 24, cyf=3.5 / 16,
)

#: China — the four small stars arcing beside the big one.
_CHN_STARS = bitmap(
    [
        ".y",
        "y.",
        "y.",
        ".y",
    ],
    {"y": _Y},
    cxf=11 / 24, cyf=4 / 16,
)

#: Malaysia — gold crescent + star in the canton.
_MAS_MOON = bitmap(
    [
        ".yy.",
        "yy..",
        "yy.y",
        "yy..",
        ".yy.",
    ],
    {"y": _Y},
    cxf=4 / 24, cyf=3.5 / 16,
)

#: Switzerland — opaque 16×12 face: white couped cross on red (covers the
#: small-size disc field entirely).
_SUI_CROSS = bitmap(
    [
        "rrrrrrrrrrrrrrrr",
        "rrrrrrrrrrrrrrrr",
        "rrrrrrrwwrrrrrrr",
        "rrrrrrrwwrrrrrrr",
        "rrrrrrrwwrrrrrrr",
        "rrrrwwwwwwwwrrrr",
        "rrrrwwwwwwwwrrrr",
        "rrrrrrrwwrrrrrrr",
        "rrrrrrrwwrrrrrrr",
        "rrrrrrrwwrrrrrrr",
        "rrrrrrrrrrrrrrrr",
        "rrrrrrrrrrrrrrrr",
    ],
    {"r": _R, "w": _W},
)

#: Albania — opaque 16×12 face: black double-headed eagle on red.
_ALB_EAGLE = bitmap(
    [
        "rrrrrrrrrrrrrrrr",
        "rrrkkrrrrrrkkrrr",
        "rrrrkkrrrrkkrrrr",
        "rrrrrkkkkkkrrrrr",
        "rrkkkkkkkkkkkkrr",
        "rkkkkkkkkkkkkkkr",
        "rrkkkrkkkkrkkkrr",
        "rrrkkkkkkkkkkrrr",
        "rrrrkkrkkrkkrrrr",
        "rrrrrrrkkrrrrrrr",
        "rrrrrrkrrkrrrrrr",
        "rrrrrrrrrrrrrrrr",
    ],
    {"r": _R, "k": _BLK},
)

#: North Macedonia — opaque 16×12 face: Kutlesh sun with eight rays on red.
_MKD_SUN = bitmap(
    [
        "rrrrrrryyrrrrrrr",
        "rryrrrryyrrrryrr",
        "rrryrrryyrrryrrr",
        "rrrryryyyyryrrrr",
        "rrrrrryyyyrrrrrr",
        "yyyryyyyyyyyryyy",
        "yyyryyyyyyyyryyy",
        "rrrrrryyyyrrrrrr",
        "rrrryryyyyryrrrr",
        "rrryrrryyrrryrrr",
        "rryrrrryyrrrryrr",
        "rrrrrrryyrrrrrrr",
    ],
    {"r": _R, "y": _Y},
)

#: Slovakia — red shield with the white double cross, hoist side.
_SVK_SHIELD = bitmap(
    [
        "rrwrr",
        "rwwwr",
        "rrwrr",
        "rwwwr",
        "rrwrr",
        ".rrr.",
    ],
    {"r": _R, "w": _W},
    cxf=0.30, cyf=0.5,
)

#: Slovenia — blue shield with the white Triglav peaks, upper hoist.
_SVN_SHIELD = bitmap(
    [
        "bbbbb",
        "bbwbb",
        "bwwwb",
        "bbbbb",
        ".bbb.",
    ],
    {"b": _B, "w": _W},
    cxf=0.28, cyf=0.38,
)

#: Greece — white cross for the canton.
_GRE_CROSS = bitmap(
    [
        "..w..",
        "..w..",
        "wwwww",
        "..w..",
        "..w..",
    ],
    {"w": _W},
    cxf=4 / 24, cyf=0.25,
)

#: Venezuela — arc of white stars in the blue band.
_VEN_STARS = bitmap(
    [
        "..w.w.w..",
        ".w.....w.",
    ],
    {"w": _W},
)

#: Peru — small red/green crest in the white band.
_PER_CREST = bitmap(
    [
        ".rr.",
        "rggr",
        "rggr",
        ".rr.",
    ],
    {"r": _R, "g": _GRN},
)

#: Bolivia — green wreath ring in the yellow band.
_BOL_WREATH = bitmap(
    [
        ".gg.",
        "g..g",
        ".gg.",
    ],
    {"g": _GRN},
)

#: Bosnia — white stars along the triangle's hypotenuse.
_BIH_STARS = compose(
    *(dot(_W, cxf=x, cyf=y, r_frac=0.06)
      for x, y in ((0.28, 0.10), (0.41, 0.29), (0.54, 0.48),
                   (0.67, 0.67), (0.80, 0.86)))
)

#: Georgia — the four small red crosses of the five-cross flag.
_GEO_DOTS = compose(
    *(dot(_R, cxf=x, cyf=y, r_frac=0.07)
      for x, y in ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)))
)

#: Saudi Arabia — white shahada line and sword on green.
_SAU_MARKS = bitmap(
    [
        "ww.w.ww.ww",
        "..........",
        ".wwwwwwww.",
    ],
    {"w": _W},
    cxf=0.5, cyf=0.44,
)

#: Iraq — green takbir marks in the white band.
_IRQ_MARKS = bitmap([("gg.g.gg")], {"g": _GRN})

#: Egypt — gold eagle of Saladin in the white band.
_EGY_EAGLE = bitmap(
    [
        ".y.",
        "yyy",
        "y.y",
    ],
    {"y": _Y},
)

#: Uganda — crane silhouette for the white disc.
_UGA_CRANE = bitmap(
    [
        ".k.",
        "kkk",
        ".k.",
        ".k.",
    ],
    {"k": _BLK},
)

#: Union Jack impression for the AUS/NZL canton (10×8, opaque).
_UNION_JACK = bitmap(
    [
        "wNNwrrwNNw",
        "NwNwrrwNwN",
        "NNwwrrwwNN",
        "rrrrrrrrrr",
        "rrrrrrrrrr",
        "NNwwrrwwNN",
        "NwNwrrwNwN",
        "wNNwrrwNNw",
    ],
    {"w": _W, "N": _NAVY, "r": _R},
    cxf=5 / 24, cyf=4 / 16,
)

#: Southern Cross for Australia (white) / New Zealand (red), fly half.
_AUS_STARS = bitmap(
    [
        "...w..",
        "w.....",
        "...w..",
        ".w....",
        "....w.",
    ],
    {"w": _W},
    cxf=0.70, cyf=0.55,
)
_NZL_STARS = bitmap(
    [
        "...r..",
        "r.....",
        "...r..",
        "....r.",
    ],
    {"r": _R},
    cxf=0.70, cyf=0.55,
)


# ---- the flag registry ------------------------------------------------------
# Values are a bare FieldFn (plain flag) or a Flag (field + emblem).
FLAGS: dict[str, FieldFn | Flag] = {
    # South America
    "ARG": Flag(h_stripes(_SKY, _W, _SKY), _ARG_SUN),
    "BRA": Flag(solid(_GRN), compose(diamond(_Y), _BRA_GLOBE)),
    "URU": Flag(h_stripes(_W, _SKY, _W, _SKY, _W), _URU_SUN),
    "COL": h_stripes(_Y, _Y, _B, _R),
    "ECU": Flag(
        h_stripes(_Y, _Y, _B, _R),
        compose(dot(_B, r_frac=0.14), dot(_Y, r_frac=0.07)),
    ),
    "PER": Flag(v_stripes(_R, _W, _R), _PER_CREST),
    "CHI": Flag(
        canton(h_stripes(_W, _W, _R, _R), _NAVY),
        large_only(star(_W, r_frac=0.14, cxf=1 / 6, cyf=0.25)),
    ),
    "VEN": Flag(h_stripes(_Y, _B, _R), _VEN_STARS),
    "PAR": Flag(h_stripes(_R, _W, _B), _PAR_SEAL),
    "BOL": Flag(h_stripes(_R, _Y, _GRN), _BOL_WREATH),
    # North/Central America
    "USA": Flag(
        canton(
            h_stripes(_R, _W, _R, _W, _R, _W, _R, _W, _R, _W, _R, _W, _R),
            _NAVY, wf=0.4, hf=0.45,
        ),
        _USA_STARS,
    ),
    "MEX": Flag(v_stripes(_GRN, _W, _R), _MEX_EAGLE),
    "CAN": Flag(v_stripes(_R, _W, _R), _CAN_LEAF),
    "CRC": h_stripes(_B, _W, _R, _R, _W, _B),
    "HON": h_stripes(_SKY, _W, _SKY),
    "PAN": Flag(
        quarters(_W, _R, _B, _W),
        large_only(compose(
            star(_B, r_frac=0.12, cxf=0.25, cyf=0.25),
            star(_R, r_frac=0.12, cxf=0.75, cyf=0.75),
        )),
    ),
    "JAM": saltire4(_GRN, _BLK, _Y),
    # Europe
    "FRA": v_stripes(_NAVY, _W, _R),
    "ITA": v_stripes(_GRN, _W, _R),
    "GER": h_stripes(_BLK, _R, _Y),
    "ESP": Flag(h_stripes(_R, _Y, _R), dot(_R, cxf=0.22, r_frac=0.12)),
    "POR": Flag(v_stripes(_GRN, _GRN, _R, _R, _R, _R), dot(_Y, cxf=1 / 3, r_frac=0.14)),
    "NED": h_stripes(_R, _W, _NAVY),
    "BEL": v_stripes(_BLK, _Y, _R),
    "ENG": george(_W, _R),
    "SCO": saltire(_B, _W),
    "WAL": h_stripes(_W, _GRN),
    "IRL": v_stripes(_GRN, _W, _ORA),
    "CRO": h_stripes(_R, _W, _B),
    "SRB": h_stripes(_R, _B, _W),
    "SUI": Flag(disc(_R, _W), _SUI_CROSS),
    "AUT": h_stripes(_R, _W, _R),
    "POL": h_stripes(_W, _R),
    "CZE": wedge(h_stripes(_W, _R), _B),
    "SVK": Flag(h_stripes(_W, _B, _R), _SVK_SHIELD),
    "SVN": Flag(h_stripes(_W, _B, _R), _SVN_SHIELD),
    "UKR": h_stripes(_B, _Y),
    "DEN": nordic(_R, _W),
    "SWE": nordic(_B, _Y),
    "NOR": nordic(_R, _W),
    "FIN": nordic(_W, _B),
    "ISL": nordic(_B, _W),
    "TUR": Flag(solid(_R), crescent(_W)),
    "GRE": Flag(canton(h_stripes(_B, _W, _B, _W), _B), _GRE_CROSS),
    "ROU": v_stripes(_B, _Y, _R),
    "HUN": h_stripes(_R, _W, _GRN),
    "BIH": Flag(solid(_B), compose(fly_triangle(_Y), _BIH_STARS)),
    "ALB": Flag(disc(_R, _BLK), _ALB_EAGLE),
    "MKD": Flag(disc(_R, _Y), _MKD_SUN),
    "GEO": Flag(george(_W, _R), _GEO_DOTS),
    # Africa
    "SEN": Flag(v_stripes(_GRN, _Y, _R), star(_GRN, r_frac=0.16)),
    "MLI": v_stripes(_GRN, _Y, _R),
    "CIV": v_stripes(_ORA, _W, _GRN),
    "GHA": Flag(h_stripes(_R, _Y, _GRN), star(_BLK, r_frac=0.16)),
    "CMR": Flag(v_stripes(_GRN, _R, _Y), star(_Y, r_frac=0.14)),
    "NGA": v_stripes(_GRN, _W, _GRN),
    "EGY": Flag(h_stripes(_R, _W, _BLK), _EGY_EAGLE),
    "ALG": Flag(v_stripes(_GRN, _W), crescent(_R)),
    "TUN": Flag(solid(_R), crescent(_W)),
    "MAR": Flag(solid(_R), star(_GRN, points=5, r_frac=0.44)),
    "RSA": h_stripes(_R, _W, _GRN, _B),
    "KEN": h_stripes(_BLK, _R, _GRN),
    "UGA": Flag(h_stripes(_BLK, _Y, _R), compose(dot(_W, r_frac=0.20), _UGA_CRANE)),
    "ETH": h_stripes(_GRN, _Y, _R),
    "TAN": diagonal(_GRN, _B, _BLK, _Y),
    "COD": Flag(
        diagonal(_SKY, _SKY, _R, _Y),
        large_only(star(_Y, r_frac=0.12, cxf=0.14, cyf=0.2)),
    ),
    "GAB": h_stripes(_GRN, _Y, _B),
    # Asia & Oceania
    "JPN": disc(_W, _R),
    "KOR": Flag(disc(_W, _R), _KOR_FACE),
    "CHN": Flag(
        solid(_R),
        compose(star(_Y, r_frac=0.22, cxf=0.16, cyf=0.30), _CHN_STARS),
    ),
    "SAU": Flag(solid(_GRN), _SAU_MARKS),
    "IRN": Flag(h_stripes(_GRN, _W, _R), large_only(dot(_R, r_frac=0.12))),
    "IRQ": Flag(h_stripes(_R, _W, _BLK), _IRQ_MARKS),
    "QAT": serrated(_W, _MAR),
    "UAE": hoist(h_stripes(_GRN, _W, _BLK), _R),
    "JOR": Flag(
        wedge(h_stripes(_BLK, _W, _GRN), _R, wf=0.42),
        large_only(dot(_W, cxf=0.13, r_frac=0.09)),
    ),
    "UZB": h_stripes(_SKY, _W, _GRN),
    "PRK": h_stripes(_B, _R, _R, _B),
    "THA": h_stripes(_R, _NAVY, _NAVY, _R),
    "VIE": Flag(solid(_R), star(_Y, points=5, r_frac=0.42)),
    "IDN": h_stripes(_R, _W),
    "IND": Flag(h_stripes(_ORA, _W, _GRN), large_only(dot(_NAVY, r_frac=0.14))),
    "MAS": Flag(
        canton(
            h_stripes(_R, _W, _R, _W, _R, _W, _R, _W, _R, _W, _R, _W, _R),
            _NAVY, wf=0.4, hf=0.45,
        ),
        _MAS_MOON,
    ),
    "PHI": wedge(h_stripes(_B, _R), _W),
    "AUS": Flag(canton(solid(_NAVY), _R), compose(_UNION_JACK, _AUS_STARS)),
    "NZL": Flag(canton(solid(_NAVY), _R), compose(_UNION_JACK, _NZL_STARS)),
}


def _flag(abbr: str | None) -> Flag | None:
    val = FLAGS.get((abbr or "").upper())
    if val is None:
        return None
    return val if isinstance(val, Flag) else Flag(val)


def flag_grid(abbr: str | None, width: int, depth: int) -> list[list[str]] | None:
    """The flag as a ``depth`` × ``width`` grid of hex colours, or None if unknown."""
    flag = _flag(abbr)
    if flag is None:
        return None
    g = [list(row) for row in flag.field(width, depth)]
    if flag.emblem is not None:
        flag.emblem(g, width, depth)
    return g


def flag_rows(abbr: str | None, width: int = WIDTH, depth: int = DEPTH) -> list[Text] | None:
    """The flag as ``depth // 2`` half-block Text rows, or None for unknown codes."""
    g = flag_grid(abbr, width, depth)
    if g is None:
        return None
    rows = []
    for tr in range(depth // 2):
        t = Text()
        for c in range(width):
            t.append("▀", style=f"{g[tr * 2][c]} on {g[tr * 2 + 1][c]}")
        rows.append(t)
    return rows


def badge_rows(abbr: str, color_hex: str, width: int = WIDTH, depth: int = DEPTH) -> list[Text]:
    """Fallback team mark: an LED badge with the abbreviation (clubs etc.)."""
    n = max(1, depth // 2)
    label = (abbr or "?")[:width].upper().center(width)
    label_row = Text(label, style=f"bold {color_hex} on {theme.UNLIT}")
    if n == 1:
        return [label_row]
    rows = [Text("▄" * width, style=color_hex)]
    rows.extend(Text("█" * width, style=color_hex) for _ in range(n - 2))
    rows.append(label_row)
    return rows


def team_mark(abbr: str, color_hex: str, *, large: bool = False) -> list[Text]:
    """Flag if we know the code, LED badge otherwise. Compact (2×6) or large (6×18)."""
    width, depth = LARGE if large else SMALL
    return flag_rows(abbr, width, depth) or badge_rows(abbr, color_hex, width, depth)


def team_chip(abbr: str, color_hex: str) -> Text:
    """One-row team mark for dense lines (event feed, ticker): ▐ABC▌-style chip."""
    t = Text()
    t.append("▐", style=color_hex)
    t.append((abbr or "?")[:3].upper(), style=f"bold {color_hex} on {theme.UNLIT}")
    t.append("▌", style=color_hex)
    return t
