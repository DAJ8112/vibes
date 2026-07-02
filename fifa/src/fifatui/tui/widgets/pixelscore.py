"""The big score, drawn in the chunky pixel font and tinted per team."""

from __future__ import annotations

from rich.console import Group
from textual.widgets import Static

from ...art import pixelfont, theme
from ..anim import FrameAnimator

_ASSEMBLE = 0.6   # seconds: new digit lights up pixel by pixel
_PULSE = 0.3      # seconds: one bright flash of the changed digit
_FPS = 14


class PixelScore(Static):
    """Renders ``2 - 1`` as pixel digits: home side in home colour, away in away."""

    def on_mount(self) -> None:
        self._home = 0
        self._away = 0
        self._home_hex = theme.AMBER
        self._away_hex = theme.AMBER
        self._board_on = True
        self._anim = FrameAnimator(self)

    def on_unmount(self) -> None:
        self._anim.stop()

    def set_score(
        self,
        home: int,
        away: int,
        home_hex: str,
        away_hex: str,
        board_on: bool = True,
    ) -> None:
        self._home, self._away = home, away
        self._home_hex, self._away_hex = home_hex, away_hex
        self._board_on = board_on
        self.update(self._content())

    def _spans(self) -> list[tuple[str, str]]:
        if not self._board_on:
            # Upcoming match: the board hasn't been switched on yet.
            dim = theme.UNLIT
            return [(str(self._home), dim), (" - ", dim), (str(self._away), dim)]
        return [
            (str(self._home), f"bold {self._home_hex}"),
            (" - ", theme.AMBER_DIM),
            (str(self._away), f"bold {self._away_hex}"),
        ]

    def _content(self, lit_per_span=None, spans=None) -> Group:
        off = theme.fade(theme.UNLIT, 0.45) if not self._board_on else theme.UNLIT
        rows = pixelfont.render_spans(spans or self._spans(), off_style=off, lit_per_span=lit_per_span)
        return Group(*rows)

    def animate_goal(self, side: str) -> None:
        """The changed side's digits assemble pixel by pixel, then flash once."""
        idx = 0 if side == "home" else 2
        team_hex = self._home_hex if side == "home" else self._away_hex
        text = str(self._home if side == "home" else self._away)
        order = pixelfont.reveal_order(text, seed=7)
        total = len(order)
        bright = f"bold {theme.fade(team_hex, 0.65, to='#ffffff')}"

        def frame(t: float) -> bool:
            if t >= _ASSEMBLE + _PULSE:
                self.update(self._content())
                return False
            spans = self._spans()
            if t < _ASSEMBLE:
                lits: list = [None] * len(spans)
                lits[idx] = set(order[: int(total * t / _ASSEMBLE)])
                self.update(self._content(lit_per_span=lits))
            else:
                if int((t - _ASSEMBLE) / _PULSE * 4) % 2 == 0:
                    spans[idx] = (text, bright)
                self.update(self._content(spans=spans))
            return True

        self._anim.start(_FPS, frame)
