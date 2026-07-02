"""A chunky 5-row pixel font drawn from block characters.

Glyphs are tiny bitmaps ('#' = lit LED). Rendering produces one ``rich.text.Text``
per row, with every cell styled individually — so a score can be tinted per team,
and a digit can be "assembled" pixel by pixel during a goal animation. When an
``off_style`` is given, unlit cells (including the gaps between glyphs) are drawn
as faint dots, which reads as the unlit LED grid of a physical scoreboard.
"""

from __future__ import annotations

import random

from rich.text import Text

ROWS = 5
GAP = 1  # blank columns between glyphs

#: (char, style) for a drawn cell, or None for a transparent one.
Cell = tuple[str, str] | None

_GLYPHS: dict[str, tuple[str, ...]] = {
    "0": ("####", "#  #", "#  #", "#  #", "####"),
    "1": (" # ", "## ", " # ", " # ", "###"),
    "2": ("####", "   #", "####", "#   ", "####"),
    "3": ("####", "   #", " ###", "   #", "####"),
    "4": ("#  #", "#  #", "####", "   #", "   #"),
    "5": ("####", "#   ", "####", "   #", "####"),
    "6": ("####", "#   ", "####", "#  #", "####"),
    "7": ("####", "   #", "  # ", " #  ", " #  "),
    "8": ("####", "#  #", "####", "#  #", "####"),
    "9": ("####", "#  #", "####", "   #", "####"),
    "A": ("####", "#  #", "####", "#  #", "#  #"),
    "B": ("### ", "#  #", "### ", "#  #", "### "),
    "C": ("####", "#   ", "#   ", "#   ", "####"),
    "D": ("### ", "#  #", "#  #", "#  #", "### "),
    "E": ("####", "#   ", "### ", "#   ", "####"),
    "F": ("####", "#   ", "### ", "#   ", "#   "),
    "G": ("####", "#   ", "# ##", "#  #", "####"),
    "H": ("#  #", "#  #", "####", "#  #", "#  #"),
    "I": ("###", " # ", " # ", " # ", "###"),
    "J": ("####", "   #", "   #", "#  #", " ## "),
    "K": ("#  #", "# # ", "##  ", "# # ", "#  #"),
    "L": ("#   ", "#   ", "#   ", "#   ", "####"),
    "M": ("#   #", "## ##", "# # #", "#   #", "#   #"),
    "N": ("#  #", "## #", "# ##", "#  #", "#  #"),
    "O": ("####", "#  #", "#  #", "#  #", "####"),
    "P": ("####", "#  #", "####", "#   ", "#   "),
    "Q": (" ## ", "#  #", "#  #", "# # ", " # #"),
    "R": ("####", "#  #", "####", "# # ", "#  #"),
    "S": ("####", "#   ", "####", "   #", "####"),
    "T": ("###", " # ", " # ", " # ", " # "),
    "U": ("#  #", "#  #", "#  #", "#  #", "####"),
    "V": ("#  #", "#  #", "#  #", "#  #", " ## "),
    "W": ("#   #", "#   #", "# # #", "## ##", "#   #"),
    "X": ("#  #", "#  #", " ## ", "#  #", "#  #"),
    "Y": ("# #", "# #", " # ", " # ", " # "),
    "Z": ("####", "  # ", " #  ", "#   ", "####"),
    " ": ("  ", "  ", "  ", "  ", "  "),
    "-": ("   ", "   ", "###", "   ", "   "),
    ":": (" ", "#", " ", "#", " "),
    "'": ("#", "#", " ", " ", " "),
    "+": ("   ", " # ", "###", " # ", "   "),
    ".": (" ", " ", " ", " ", "#"),
    "!": ("#", "#", "#", " ", "#"),
}


def _glyph(ch: str) -> tuple[str, ...]:
    g = _GLYPHS.get(ch.upper(), _GLYPHS[" "])
    width = max(len(row) for row in g)
    return tuple(row.ljust(width) for row in g)


def measure(s: str) -> int:
    """Total width in columns, including inter-glyph gaps."""
    if not s:
        return 0
    return sum(len(_glyph(c)[0]) for c in s) + GAP * (len(s) - 1)


def pixels(s: str) -> list[tuple[int, int]]:
    """(row, col) of every lit pixel in the string, cols counted across gaps."""
    out: list[tuple[int, int]] = []
    x = 0
    for ch in s:
        g = _glyph(ch)
        for r, row in enumerate(g):
            for c, cell in enumerate(row):
                if cell == "#":
                    out.append((r, x + c))
        x += len(g[0]) + GAP
    return out


def reveal_order(s: str, seed: int = 0) -> list[tuple[int, int]]:
    """Lit pixels in a deterministic shuffled order (for assemble animations)."""
    order = pixels(s)
    random.Random(seed).shuffle(order)
    return order


def cells(
    s: str,
    on_style: str,
    off_style: str | None = None,
    on_char: str = "█",
    off_char: str = "·",
    lit: set[tuple[int, int]] | None = None,
) -> list[list[Cell]]:
    """The string as a cell grid. ``lit`` restricts which pixels are on (partial reveal)."""
    off: Cell = (off_char, off_style) if off_style else None
    grid: list[list[Cell]] = [[] for _ in range(ROWS)]
    x = 0
    for i, ch in enumerate(s):
        g = _glyph(ch)
        for r, row in enumerate(g):
            for c, cell in enumerate(row):
                is_on = cell == "#" and (lit is None or (r, x + c) in lit)
                grid[r].append((on_char, on_style) if is_on else off)
        x += len(g[0]) + GAP
        if i < len(s) - 1:
            for r in range(ROWS):
                grid[r].extend([off] * GAP)
    return grid


def cells_to_text(grid: list[list[Cell]]) -> list[Text]:
    rows = []
    for row in grid:
        t = Text()
        for cell in row:
            if cell is None:
                t.append(" ")
            else:
                t.append(cell[0], style=cell[1])
        rows.append(t)
    return rows


def render(
    s: str,
    on_style: str,
    off_style: str | None = None,
    on_char: str = "█",
    off_char: str = "·",
    lit: set[tuple[int, int]] | None = None,
) -> list[Text]:
    """The string as ROWS styled Text rows."""
    return cells_to_text(cells(s, on_style, off_style, on_char, off_char, lit))


def render_spans(
    spans: list[tuple[str, str]],
    off_style: str | None = None,
    on_char: str = "█",
    off_char: str = "·",
    lit_per_span: list[set[tuple[int, int]] | None] | None = None,
) -> list[Text]:
    """Multi-colour pixel text: each (text, style) span rendered and joined with a gap."""
    off: Cell = (off_char, off_style) if off_style else None
    grid: list[list[Cell]] = [[] for _ in range(ROWS)]
    for i, (text, style) in enumerate(spans):
        lit = lit_per_span[i] if lit_per_span else None
        part = cells(text, style, off_style, on_char, off_char, lit)
        for r in range(ROWS):
            if i > 0:
                grid[r].extend([off] * GAP)
            grid[r].extend(part[r])
    return cells_to_text(grid)
