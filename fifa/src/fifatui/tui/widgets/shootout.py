"""Penalty shootout tracker: one kick-marker row per team plus the latest kick."""

from __future__ import annotations

from rich.console import Group
from rich.text import Text
from textual.widgets import Static

from ...api.models import EventType, Match, MatchEvent, Team
from ...art import theme
from ...art.glyphs import EVENT_GLYPH
from ...art.pixelflags import team_chip

MIN_SLOTS = 5
MARK_SCORED = "██"
MARK_MISSED = "▒▒"
MARK_PENDING = "··"


def kick_scored(e: MatchEvent) -> bool:
    """ESPN kick texts are "Penalty - Scored" / "Penalty - Missed" / "Penalty - Saved";
    anything that isn't explicitly scored counts as a miss."""
    return "scored" in e.text.lower()


def shootout_kicks(m: Match) -> tuple[list[MatchEvent], list[MatchEvent]]:
    """(home, away) kicks in taken order (the stable event sort keeps ESPN's order)."""
    kicks = [e for e in m.events if e.type == EventType.SHOOTOUT]
    home = [e for e in kicks if e.team_id == m.home.id]
    away = [e for e in kicks if e.team_id == m.away.id]
    return home, away


def latest_kick(m: Match) -> MatchEvent | None:
    return next((e for e in reversed(m.events) if e.type == EventType.SHOOTOUT), None)


class ShootoutPanel(Static):
    def update_match(self, m: Match) -> None:
        home_kicks, away_kicks = shootout_kicks(m)
        # Kick details can land a poll before shootoutScore does, and vice versa.
        visible = m.has_shootout or bool(home_kicks or away_kicks)
        self.styles.display = "block" if visible else "none"
        if visible:
            self.update(self._build(m, home_kicks, away_kicks))

    def _build(self, m: Match, home_kicks: list[MatchEvent],
               away_kicks: list[MatchEvent]) -> Group:
        slots = max(MIN_SLOTS, len(home_kicks), len(away_kicks))
        rows = [
            Text("┌ PENALTY SHOOTOUT ┐", style=theme.AMBER_DIM, justify="center"),
            Text(""),
            self._team_row(m.home, home_kicks, slots),
            self._team_row(m.away, away_kicks, slots),
        ]
        last = latest_kick(m)
        if last is not None:
            rows.append(Text(""))
            rows.append(self._latest_line(m, last))
        return Group(*rows)

    @staticmethod
    def _team_row(team: Team, kicks: list[MatchEvent], slots: int) -> Text:
        color = team.color_hex
        t = Text(justify="center")
        t.append_text(team_chip(team.abbr, color))
        t.append("  ")
        for i in range(slots):
            if i >= len(kicks):
                t.append(MARK_PENDING, style=theme.UNLIT)
            elif kick_scored(kicks[i]):
                t.append(MARK_SCORED, style=color)
            else:
                t.append(MARK_MISSED, style=theme.fade(color, 0.6))
            if i < slots - 1:
                t.append(" ")
        score = team.shootout_score
        if score is None:
            score = sum(kick_scored(k) for k in kicks)
        t.append(f"   {score:>2}", style=f"bold {theme.AMBER}")
        return t

    @staticmethod
    def _latest_line(m: Match, e: MatchEvent) -> Text:
        team = m.team(e.team_id)
        color = team.color_hex if team else theme.AMBER
        t = Text(justify="center")
        t.append(f"{EVENT_GLYPH[EventType.SHOOTOUT]} ", style=f"bold {color}")
        t.append(e.scorer or "—", style=theme.AMBER)
        if kick_scored(e):
            t.append(" · scored", style=color)
        else:
            t.append(" · missed", style=theme.TEXT_DIM)
        return t
