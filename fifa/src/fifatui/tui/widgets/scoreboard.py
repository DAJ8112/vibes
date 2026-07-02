"""Scoreboard: team panels (flag/name) flanking a big digital score + clock."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from ...api.models import Match, MatchState, Team
from ...art import theme
from ...art.pixelflags import team_mark
from .pixelscore import PixelScore


class ScoreBoard(Vertical):
    def compose(self) -> ComposeResult:
        with Horizontal(id="score-row"):
            yield Static(id="home-panel")
            yield PixelScore(id="score-digits")
            yield Static(id="away-panel")
        yield Static(id="status-line")

    def on_mount(self) -> None:
        self._match: Match | None = None

    def update_match(self, m: Match) -> None:
        self._match = m
        self.query_one("#home-panel", Static).update(self._panel(m.home))
        self.query_one("#away-panel", Static).update(self._panel(m.away))
        score = self.query_one("#score-digits", PixelScore)
        if m.is_upcoming:
            score.set_score(0, 0, m.home.color_hex, m.away.color_hex, board_on=False)
        else:
            score.set_score(m.home.score, m.away.score, m.home.color_hex, m.away.color_hex)
        self.query_one("#status-line", Static).update(self._status(m))

    def pulse(self, phase: int) -> None:
        """Re-render only the status line with the breathing LIVE lamp."""
        if self._match is not None and self._match.is_live:
            self.query_one("#status-line", Static).update(self._status(self._match, phase))

    @staticmethod
    def _panel(team: Team) -> Text:
        color = team.color_hex
        t = Text(justify="center")
        for row in team_mark(team.abbr, color):
            t.append_text(row)
            t.append("\n")
        t.append(team.abbr, style=f"bold {color}")
        if team.winner:
            t.append("  ★", style=f"bold {theme.WIN_GOLD}")
        t.append(f"\n{team.name}", style=theme.TEXT_DIM)
        return t

    @staticmethod
    def _status(m: Match, phase: int = 0) -> Text:
        if m.state == MatchState.IN:
            dot = theme.LIVE_PULSE[phase % len(theme.LIVE_PULSE)]
            t = Text()
            t.append("● ", style=f"bold {dot}")
            t.append(m.status_detail or m.display_clock, style=f"bold {theme.AMBER}")
            if m.has_shootout:
                t.append(
                    f"   pens {m.home.shootout_score or 0}-{m.away.shootout_score or 0}",
                    style=theme.CARD_YELLOW,
                )
            return t
        if m.state == MatchState.POST:
            t = Text(m.status_detail or "FT", style=f"bold {theme.AMBER}")
            if m.has_shootout:
                t.append(
                    f"   penalties {m.home.shootout_score or 0}-{m.away.shootout_score or 0}",
                    style=theme.CARD_YELLOW,
                )
            return t
        # upcoming
        when = ""
        if "T" in m.date:
            when = m.date.split("T", 1)[1].rstrip("Z")[:5] + " UTC"
        return Text(f"Kickoff {when}".strip(), style=theme.AMBER_DIM)
