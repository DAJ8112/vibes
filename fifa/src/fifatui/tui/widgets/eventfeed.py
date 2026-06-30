"""Scrollable match event feed (goals + cards), newest first."""

from __future__ import annotations

from rich.console import Group
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from ...api.models import EVENT_ICON, EventType, Match, MatchEvent

_GOAL_TYPES = {EventType.GOAL, EventType.OWN_GOAL, EventType.PENALTY_GOAL}


class EventFeed(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Static(id="event-list")

    def update_match(self, m: Match) -> None:
        self.query_one("#event-list", Static).update(self._build(m))

    def _build(self, m: Match):
        if not m.events:
            return Text("No events yet.", style="dim")
        rows = [self._line(m, e) for e in reversed(m.events)]
        return Group(*rows)

    @staticmethod
    def _line(m: Match, e: MatchEvent) -> Text:
        team = m.team(e.team_id)
        abbr = team.abbr if team else "?"
        flag = team.flag if team else ""
        icon = EVENT_ICON.get(e.type, "•")

        t = Text()
        t.append(f"{e.minute:>7}  ", style="dim")
        t.append(f"{icon} ", style="")
        t.append(f"{flag} {abbr:<3}  ", style="bold")

        if e.type in _GOAL_TYPES:
            who = e.scorer or "Goal"
            extra = " (pen)" if e.type == EventType.PENALTY_GOAL else ""
            extra = " (o.g.)" if e.type == EventType.OWN_GOAL else extra
            color = team.color_hex if team else "white"
            t.append(f"{who}{extra}", style=f"bold {color}")
            if e.assist:
                t.append(f"  assist {e.assist}", style="dim")
        elif e.type == EventType.YELLOW:
            t.append(e.scorer or "Yellow card", style="yellow")
        elif e.type == EventType.RED:
            t.append(e.scorer or "Red card", style="bold red")
        elif e.type == EventType.SHOOTOUT:
            t.append(f"{e.text}: {e.scorer}".strip(": "), style="dim cyan")
        else:
            t.append(e.scorer or e.text, style="dim")
        return t
