"""Full-screen goal celebration overlay.

Pixel fireworks in the scoring team's colours while big pixel-font GOAL letters
rise from the bottom of the board; scorer and minute light up beneath. Runs ~3s
and auto-dismisses. No background flashing, no sound, no bell.
"""

from __future__ import annotations

import random
from typing import Callable

from textual.widgets import Static

from ...api.models import EventType, MatchEvent, Team
from ...art import pixelfont, theme
from ...art.canvas import CharGrid
from ...art.particles import Fireworks
from ..anim import FrameAnimator

DURATION = 3.0
FPS = 14
_BURSTS = (0.1, 0.5, 0.9, 1.4)   # seconds at which a new firework goes off
_RISE = 0.8                      # seconds for GOAL to rise into place
_FADE_FROM = 2.4                 # letters start fading toward the board


class GoalCelebration(Static):
    def on_mount(self) -> None:
        self.styles.display = "none"
        self._anim = FrameAnimator(self)
        self._on_done: Callable[[], None] | None = None
        self._event: MatchEvent | None = None
        self._team: Team | None = None
        self._color = theme.AMBER
        self._fireworks: Fireworks | None = None
        self._pending: list[float] = []
        self._rng = random.Random()

    def on_unmount(self) -> None:
        self._anim.stop()

    def show(self, event: MatchEvent, team: Team | None, on_done: Callable[[], None] | None = None) -> None:
        self._event = event
        self._team = team
        self._on_done = on_done
        self._color = team.color_hex if team else theme.AMBER
        w, h = self._dims()
        self._fireworks = Fireworks(
            w, h,
            colors=["#f5f0e0", self._color, theme.fade(self._color, 0.35), theme.AMBER],
            rng=self._rng,
        )
        self._pending = list(_BURSTS)
        self.styles.display = "block"
        self._paint(0.0)
        self._anim.start(FPS, self._frame, on_done=self._finish)

    def _dims(self) -> tuple[int, int]:
        w = self.size.width or self.screen.size.width or 80
        h = self.size.height or self.screen.size.height or 24
        return max(20, w), max(10, h)

    def _frame(self, t: float) -> bool:
        if t >= DURATION:
            return False
        self._paint(t)
        return True

    def _finish(self) -> None:
        self.styles.display = "none"
        cb, self._on_done = self._on_done, None
        if cb is not None:
            cb()

    # -- frame rendering ------------------------------------------------

    def _paint(self, t: float) -> None:
        w, h = self._dims()
        grid = CharGrid(w, h)

        fw = self._fireworks
        if fw is not None:
            while self._pending and t >= self._pending[0]:
                self._pending.pop(0)
                fw.spawn_burst(
                    x=self._rng.uniform(w * 0.2, w * 0.8),
                    y=self._rng.uniform(h * 0.15, h * 0.45),
                )
            fw.step(1.0 / FPS)
            fw.paint(grid)

        self._paint_letters(grid, t, w, h)
        self._paint_scorer(grid, t, w, h)
        self.update(grid.to_group())

    def _paint_letters(self, grid: CharGrid, t: float, w: int, h: int) -> None:
        target_y = h // 2 - 5
        if t < _RISE:
            k = t / _RISE
            ease = 1 - (1 - k) ** 3
            y = round(h - (h - target_y) * ease)
        else:
            y = target_y
        color = self._color
        if t > _FADE_FROM:
            color = theme.fade(color, (t - _FADE_FROM) / (DURATION - _FADE_FROM) * 0.9)
        cells = pixelfont.cells("GOAL!", on_style=f"bold {color}")
        grid.stamp_cells((w - pixelfont.measure("GOAL!")) // 2, y, cells)

    def _paint_scorer(self, grid: CharGrid, t: float, w: int, h: int) -> None:
        if t < 1.0:
            return
        ev, team = self._event, self._team
        y = h // 2 + 2
        if team is not None:
            name = team.name.upper()
            grid.stamp_text((w - len(name)) // 2, y, name, f"bold {self._color}")
        if ev is not None and ev.scorer:
            extra = " (pen)" if ev.type == EventType.PENALTY_GOAL else ""
            extra = " (o.g.)" if ev.type == EventType.OWN_GOAL else extra
            line = f"{ev.scorer}{extra}" + (f"   {ev.minute}" if ev.minute else "")
            grid.stamp_text((w - len(line)) // 2, y + 2, line, f"bold {theme.AMBER}")
            if ev.assist:
                assist = f"assist: {ev.assist}"
                grid.stamp_text((w - len(assist)) // 2, y + 3, assist, theme.TEXT_DIM)
