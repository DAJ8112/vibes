"""Full-screen goal celebration overlay.

Shown when a new goal is detected. Animates for ~3.5s — confetti drifts, the word
GOOOAL pulses, the team colour flashes — then auto-dismisses. No sound, no bell.
"""

from __future__ import annotations

import random
from typing import Callable

from rich.align import Align
from rich.console import Group
from rich.text import Text
from textual.widgets import Static

from ...api.models import MatchEvent, Team

CONFETTI = "🎉✨⚽⭐🎊💥🟢🟡"
FRAMES = 50
INTERVAL = 0.07


class GoalCelebration(Static):
    def on_mount(self) -> None:
        self.styles.display = "none"
        self._timer = None
        self._frame = 0
        self._on_done: Callable[[], None] | None = None
        self._event: MatchEvent | None = None
        self._team: Team | None = None

    def show(self, event: MatchEvent, team: Team | None, on_done: Callable[[], None] | None = None) -> None:
        self._event = event
        self._team = team
        self._on_done = on_done
        self._frame = 0
        self.styles.display = "block"
        self.update(self._frame_content())
        self._timer = self.set_interval(INTERVAL, self._tick)

    def _tick(self) -> None:
        self._frame += 1
        if self._frame > FRAMES:
            self._finish()
            return
        self.update(self._frame_content())
        if self._team is not None:
            self.styles.background = self._team.color_hex if self._frame % 2 == 0 else "black"

    def _finish(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self.styles.display = "none"
        self.styles.background = "black"
        cb, self._on_done = self._on_done, None
        if cb is not None:
            cb()

    def _confetti(self, width: int) -> Text:
        chars = [
            random.choice(CONFETTI) if random.random() < 0.16 else " "
            for _ in range(max(1, width // 2))
        ]
        return Text("".join(chars))

    def _frame_content(self):
        width = max(20, (self.size.width or 60))
        team = self._team
        ev = self._event
        color = team.color_hex if team else "yellow"

        os_ = "O" * (3 + self._frame % 4)
        title = Text(f"⚽  G{os_}AL!  ⚽", style=f"bold {color} reverse")
        title.stylize("blink", 0, 0)  # harmless if unsupported

        parts = [self._confetti(width), self._confetti(width), Text()]
        parts.append(title)
        parts.append(Text())
        if team is not None:
            parts.append(Text(f"{team.flag}  {team.name}", style="bold white"))
        if ev is not None and ev.scorer:
            scorer = Text()
            scorer.append(ev.scorer, style="bold gold1")
            if ev.minute:
                scorer.append(f"   {ev.minute}", style="white")
            parts.append(scorer)
            if ev.assist:
                parts.append(Text(f"assist: {ev.assist}", style="dim white"))
        parts += [Text(), self._confetti(width), self._confetti(width)]

        return Group(*[Align.center(p) for p in parts])
