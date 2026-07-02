"""A slow bottom ticker with the other live scores (like the strip on a stadium board).

Fed from the app's existing poll — no extra requests. Hidden (and its timer
stopped) when no other live matches exist.
"""

from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

from ...api.models import Match
from ...art import theme
from ..anim import FrameAnimator

_FPS = 4
_SEP = "   ·   "


class ScoreTicker(Static):
    def on_mount(self) -> None:
        self.display = False
        self._anim = FrameAnimator(self)
        self._cells: list[tuple[str, str]] = []
        self._offset = 0

    def on_unmount(self) -> None:
        self._anim.stop()

    def update_matches(self, matches: list[Match], exclude_id: str) -> None:
        others = [m for m in matches if m.is_live and m.id != exclude_id]
        if not others:
            self._anim.stop()
            self._cells = []
            self.display = False
            return
        self._cells = self._build(others)
        self.display = True
        if not self._anim.running:
            self._anim.start(_FPS, self._frame)

    @staticmethod
    def _build(matches: list[Match]) -> list[tuple[str, str]]:
        cells: list[tuple[str, str]] = []

        def add(text: str, style: str) -> None:
            cells.extend((ch, style) for ch in text)

        for m in matches:
            add(m.home.abbr, f"bold {m.home.color_hex}")
            add(f" {m.home.score}-{m.away.score} ", f"bold {theme.AMBER}")
            add(m.away.abbr, f"bold {m.away.color_hex}")
            clock = m.status_detail or m.display_clock
            if clock:
                add(f" {clock}", theme.AMBER_DIM)
            add(" ●", theme.LIVE_RED)
            add(_SEP, theme.UNLIT)
        return cells

    def _frame(self, elapsed: float) -> bool:
        if not self._cells:
            return True
        screen = self.screen
        if not (screen.is_current and self.app.app_focus):
            return True
        if getattr(screen, "_celebrating", False):
            return True  # give the goal celebration the frame budget
        self._offset = (self._offset + 1) % len(self._cells)
        self._render_window()
        return True

    def _render_window(self) -> None:
        width = max(10, self.size.width or 80)
        n = len(self._cells)
        t = Text()
        for i in range(width):
            ch, style = self._cells[(self._offset + i) % n]
            t.append(ch, style=style)
        self.update(t)
