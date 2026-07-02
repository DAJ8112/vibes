"""Possession split-bar plus a compact comparison of the key match stats."""

from __future__ import annotations

from rich.console import Group
from rich.text import Text
from textual.widgets import Static

from ...api.models import Match
from ...art import theme

BAR = "█"
BAR_WIDTH = 30


class StatBars(Static):
    def update_match(self, m: Match) -> None:
        self.update(self._build(m))

    def _build(self, m: Match):
        hs, as_ = m.home.stats, m.away.stats
        hc, ac = m.home.color_hex, m.away.color_hex
        has_stats = any(
            v is not None
            for v in (hs.possession, hs.shots, hs.corners, hs.fouls, as_.possession)
        )
        if not has_stats:
            return Text("No live stats yet.", style=theme.TEXT_DIM)

        rows = []
        if hs.possession is not None or as_.possession is not None:
            rows.append(self._possession(hs.possession or 0.0, as_.possession or 0.0, hc, ac))
            rows.append(Text(""))
        rows.append(self._stat("Shots", hs.shots, as_.shots, hc, ac))
        rows.append(self._stat("On target", hs.shots_on_target, as_.shots_on_target, hc, ac))
        rows.append(self._stat("Corners", hs.corners, as_.corners, hc, ac))
        rows.append(self._stat("Fouls", hs.fouls, as_.fouls, hc, ac))
        return Group(*rows)

    @staticmethod
    def _possession(hp: float, ap: float, hc: str, ac: str) -> Text:
        total = hp + ap or 100.0
        hw = round(BAR_WIDTH * hp / total)
        aw = BAR_WIDTH - hw
        t = Text()
        t.append(f"{round(hp):>3}% ", style=f"bold {hc}")
        t.append(BAR * hw, style=hc)
        t.append("│", style=theme.AMBER_DIM)
        t.append(BAR * aw, style=ac)
        t.append(f" {round(ap)}%", style=f"bold {ac}")
        t.append("   Possession", style=theme.AMBER_DIM)
        return t

    @staticmethod
    def _stat(label: str, hv, av, hc: str, ac: str) -> Text:
        hv = hv or 0
        av = av or 0
        total = hv + av
        if total > 0:
            hw = round(BAR_WIDTH * hv / total)
        else:
            hw = BAR_WIDTH // 2
        aw = BAR_WIDTH - hw
        t = Text()
        t.append(f"{hv:>3} ", style=f"bold {theme.AMBER}")
        t.append(BAR * hw, style=hc)
        t.append("│", style=theme.AMBER_DIM)
        t.append(BAR * aw, style=ac)
        t.append(f" {av}", style=f"bold {theme.AMBER}")
        t.append(f"   {label}", style=theme.AMBER_DIM)
        return t
