"""Scoreboard: team panels (flag/name) flanking a big digital score + clock."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Digits, Static

from ...api.models import Match, MatchState, Team


class ScoreBoard(Vertical):
    def compose(self) -> ComposeResult:
        with Horizontal(id="score-row"):
            yield Static(id="home-panel")
            yield Digits("0 - 0", id="score-digits")
            yield Static(id="away-panel")
        yield Static(id="status-line")

    def update_match(self, m: Match) -> None:
        self.query_one("#home-panel", Static).update(self._panel(m.home))
        self.query_one("#away-panel", Static).update(self._panel(m.away))
        digits = self.query_one("#score-digits", Digits)
        if m.is_upcoming:
            digits.update("0 - 0")
        else:
            digits.update(f"{m.home.score} - {m.away.score}")
        self.query_one("#status-line", Static).update(self._status(m))

    @staticmethod
    def _panel(team: Team) -> Text:
        color = team.color_hex
        t = Text(justify="center")
        t.append(f"{team.flag}\n")
        t.append(team.abbr, style=f"bold {color}")
        if team.winner:
            t.append("  ★", style="bold gold1")
        t.append(f"\n{team.name}", style="dim")
        return t

    @staticmethod
    def _status(m: Match) -> Text:
        if m.state == MatchState.IN:
            t = Text()
            t.append("● ", style="bold red")
            t.append(m.status_detail or m.display_clock, style="bold")
            if m.has_shootout:
                t.append(
                    f"   pens {m.home.shootout_score or 0}-{m.away.shootout_score or 0}",
                    style="yellow",
                )
            return t
        if m.state == MatchState.POST:
            t = Text(m.status_detail or "FT", style="bold")
            if m.has_shootout:
                t.append(
                    f"   penalties {m.home.shootout_score or 0}-{m.away.shootout_score or 0}",
                    style="yellow",
                )
            return t
        # upcoming
        when = ""
        if "T" in m.date:
            when = m.date.split("T", 1)[1].rstrip("Z")[:5] + " UTC"
        return Text(f"Kickoff {when}".strip(), style="cyan")
