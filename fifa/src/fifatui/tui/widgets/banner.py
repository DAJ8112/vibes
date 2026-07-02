"""A brief lower-third strip for non-goal moments: cards, subs, kickoff/HT/FT.

Smaller and shorter than the goal celebration; if a new moment arrives while one
is showing, it replaces it. The watch screen suppresses banners entirely while a
goal celebration is running.
"""

from __future__ import annotations

from rich.console import Group
from rich.text import Text
from textual.widgets import Static

from ...art import pixelfont, theme
from ..anim import FrameAnimator

_FPS = 14
_REVEAL = 0.3
_FADE = 0.3

_CARD_ART = ("▄▄▄", "███", "███", "▀▀▀")


class EventBanner(Static):
    def on_mount(self) -> None:
        self.styles.display = "none"
        self._anim = FrameAnimator(self)

    def on_unmount(self) -> None:
        self._anim.stop()

    # -- public moments --------------------------------------------------

    def show_pixel(self, text: str, color: str = theme.AMBER, duration: float = 1.6) -> None:
        """Pixel-font banner: quick pixel reveal, hold, fade out (KICK OFF / HT / FULL TIME)."""
        order = pixelfont.reveal_order(text, seed=11)
        total = len(order)

        def frame(t: float) -> bool:
            if t >= duration:
                return False
            if t < _REVEAL:
                lit = set(order[: int(total * t / _REVEAL)])
                rows = pixelfont.render(text, f"bold {color}", off_style=theme.UNLIT, lit=lit)
            elif t > duration - _FADE:
                k = (t - (duration - _FADE)) / _FADE
                rows = pixelfont.render(text, f"bold {theme.fade(color, k * 0.9, to=theme.BG_PANEL)}",
                                        off_style=theme.UNLIT)
            else:
                rows = pixelfont.render(text, f"bold {color}", off_style=theme.UNLIT)
            self.update(Group(*rows))
            return True

        self._start(frame)

    def show_card(self, color: str, label: str, player: str, minute: str,
                  duration: float = 1.6) -> None:
        """Card moment: the card glyph flicks bright/dim, then holds with the player name."""

        def frame(t: float) -> bool:
            if t >= duration:
                return False
            bright = t >= 0.4 or int(t / 0.1) % 2 == 0
            self.update(self._card_content(color, label, player, minute, bright))
            return True

        self._start(frame)

    def show_line(self, line: Text, duration: float = 1.4) -> None:
        """Generic one-line moment (substitutions)."""

        def frame(t: float) -> bool:
            if t >= duration:
                return False
            self.update(line)
            return True

        self._start(frame)

    # -- internals ---------------------------------------------------------

    def _start(self, frame) -> None:
        self.styles.display = "block"
        frame(0.0)
        self._anim.start(_FPS, frame, on_done=self._hide)

    def _hide(self) -> None:
        self.styles.display = "none"

    @staticmethod
    def _card_content(color: str, label: str, player: str, minute: str, bright: bool) -> Group:
        art_style = color if bright else theme.fade(color, 0.5)
        rows = []
        for i, art in enumerate(_CARD_ART):
            t = Text()
            t.append(art, style=art_style)
            if i == 1:
                t.append(f"  {label}", style=f"bold {color}")
            elif i == 2 and player:
                t.append(f"  {player}" + (f"  {minute}" if minute else ""), style=theme.AMBER)
            rows.append(t)
        width = max(len(r.plain) for r in rows)
        for r in rows:
            r.pad_right(width - len(r.plain))
        return Group(*rows)
