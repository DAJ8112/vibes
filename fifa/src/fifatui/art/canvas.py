"""A tiny char-grid compositor for full-screen animation frames."""

from __future__ import annotations

from rich.console import Group
from rich.text import Text


class CharGrid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._chars = [[" "] * width for _ in range(height)]
        self._styles = [[""] * width for _ in range(height)]

    def put(self, x: int, y: int, char: str, style: str) -> None:
        """Draw one cell; silently ignores anything outside the grid."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self._chars[y][x] = char
            self._styles[y][x] = style

    def stamp_cells(self, x: int, y: int, cells) -> None:
        """Blit pixel-font cell rows (None cells are transparent)."""
        for r, row in enumerate(cells):
            for c, cell in enumerate(row):
                if cell is not None:
                    self.put(x + c, y + r, cell[0], cell[1])

    def stamp_text(self, x: int, y: int, text: str, style: str) -> None:
        for i, ch in enumerate(text):
            self.put(x + i, y, ch, style)

    def to_group(self) -> Group:
        rows = []
        for y in range(self.height):
            t = Text()
            run = []
            run_style = self._styles[y][0]
            for x in range(self.width):
                if self._styles[y][x] != run_style:
                    t.append("".join(run), style=run_style)
                    run = []
                    run_style = self._styles[y][x]
                run.append(self._chars[y][x])
            t.append("".join(run), style=run_style)
            rows.append(t)
        return Group(*rows)
