"""Scrollable match event feed (goals + cards), newest first."""

from __future__ import annotations

from rich.console import Group
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from ...api.models import EventType, Match, MatchEvent
from ...art import theme
from ...art.glyphs import EVENT_GLYPH
from ...art.pixelflags import team_chip

_GOAL_TYPES = {EventType.GOAL, EventType.OWN_GOAL, EventType.PENALTY_GOAL}


class EventFeed(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Static(id="event-list")

    def update_match(self, m: Match) -> None:
        self.query_one("#event-list", Static).update(self._build(m))

    def _build(self, m: Match):
        # Shootout kicks live in the ShootoutPanel, not the feed.
        events = [e for e in m.events if e.type != EventType.SHOOTOUT]
        if not events:
            return Text("No events yet.", style=theme.TEXT_DIM)
        rows = [self._line(m, e) for e in reversed(events)]
        return Group(*rows)

    @staticmethod
    def _line(m: Match, e: MatchEvent) -> Text:
        team = m.team(e.team_id)
        abbr = team.abbr if team else "?"
        team_hex = team.color_hex if team else theme.AMBER
        glyph = EVENT_GLYPH.get(e.type, "·")
        glyph_style = {
            EventType.YELLOW: theme.CARD_YELLOW,
            EventType.RED: theme.CARD_RED,
        }.get(e.type, team_hex)

        t = Text()
        t.append(f"{e.minute:>7}  ", style=theme.AMBER_DIM)
        t.append(f"{glyph} ", style=f"bold {glyph_style}")
        t.append_text(team_chip(abbr, team_hex))
        t.append("  ")

        if e.type in _GOAL_TYPES:
            who = e.scorer or "Goal"
            extra = " (pen)" if e.type == EventType.PENALTY_GOAL else ""
            extra = " (o.g.)" if e.type == EventType.OWN_GOAL else extra
            t.append(f"{who}{extra}", style=f"bold {team_hex}")
            if e.assist:
                t.append(f"  assist {e.assist}", style=theme.TEXT_DIM)
        elif e.type == EventType.YELLOW:
            t.append(e.scorer or "Yellow card", style=theme.CARD_YELLOW)
        elif e.type == EventType.RED:
            t.append(e.scorer or "Red card", style=f"bold {theme.CARD_RED}")
        else:
            t.append(e.scorer or e.text, style=theme.TEXT_DIM)
        return t
