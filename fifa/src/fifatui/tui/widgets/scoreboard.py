"""Scoreboard: the top panel — league/venue header, team panels flanking a big
digital score + live clock, a footer note, and (during pens) the shootout tracker."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from ...api.models import Match, MatchState, Team
from ...art import theme
from ...art.pixelflags import team_mark
from .pixelscore import PixelScore
from .shootout import ShootoutPanel


class ScoreBoard(Vertical):
    def compose(self) -> ComposeResult:
        yield Static(id="board-header")
        with Horizontal(id="score-row"):
            yield Static(id="home-panel")
            yield PixelScore(id="score-digits")
            yield Static(id="away-panel")
        yield Static(id="status-line")
        yield ShootoutPanel()
        yield Static(id="board-footer")

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
        self.query_one("#board-footer", Static).update(self._footer(m))
        self.query_one(ShootoutPanel).update_match(m)

    def set_header(self, left: Text, right: Text) -> None:
        """Render the top strip: league/round/venue (left), refresh state (right)."""
        width = self.query_one("#board-header", Static).size.width or 0
        line = Text()
        line.append_text(left)
        pad = max(2, width - len(left.plain) - len(right.plain))
        line.append(" " * pad)
        line.append_text(right)
        self.query_one("#board-header", Static).update(line)

    def pulse(self, phase: int) -> None:
        """Re-render only the status line with the breathing LIVE lamp."""
        if self._match is not None and self._match.is_live:
            self.query_one("#status-line", Static).update(self._status(self._match, phase))

    @staticmethod
    def _panel(team: Team) -> Text:
        color = team.color_hex
        t = Text(justify="center")
        t.append(team.abbr, style=f"bold {color}")
        if team.winner:
            t.append("  ★", style=f"bold {theme.WIN_GOLD}")
        t.append(f"\n{team.name}\n", style=theme.DIM)
        for row in team_mark(team.abbr, color, large=True):
            t.append_text(row)
            t.append("\n")
        return t

    @staticmethod
    def _status(m: Match, phase: int = 0) -> Text:
        if m.state == MatchState.IN:
            dot = theme.LIVE_PULSE[phase % len(theme.LIVE_PULSE)]
            t = Text()
            t.append("● ", style=f"bold {dot}")
            t.append(m.status_detail or m.display_clock, style=f"bold {theme.FG}")
            t.append("  ·  ", style=theme.DIM)
            t.append("LIVE", style=f"bold {theme.LIVE}")
            if m.has_shootout:
                t.append(
                    f"   pens {m.home.shootout_score or 0}-{m.away.shootout_score or 0}",
                    style=theme.WARN,
                )
            return t
        if m.state == MatchState.POST:
            t = Text(m.status_detail or "FT", style=f"bold {theme.ACCENT}")
            if m.has_shootout:
                t.append(
                    f"   penalties {m.home.shootout_score or 0}-{m.away.shootout_score or 0}",
                    style=theme.WARN,
                )
            return t
        # upcoming
        when = ""
        if "T" in m.date:
            when = m.date.split("T", 1)[1].rstrip("Z")[:5] + " UTC"
        return Text(f"Kickoff {when}".strip(), style=theme.DIM)

    @staticmethod
    def _footer(m: Match) -> Text:
        bits = []
        if m.note:
            bits.append(m.note)
        if m.is_upcoming and "T" in m.date:
            bits.append("kickoff " + m.date.split("T", 1)[1].rstrip("Z")[:5])
        return Text("   ·   ".join(bits), style=theme.DIM)
