"""The pinned left column: key-events feed on top, match-stats block beneath.

Both sit under labelled header strips (``▚ KEY EVENTS`` / ``▚ MATCH STATS``); the
stats header echoes the currently pinned metric set from the console.
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from ...api.models import Match
from ...art import theme
from .eventfeed import EventFeed
from .statbars import STAT_LABELS, StatBars


class SidePanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static(id="events-header", classes="panel-header")
        yield EventFeed()
        yield Static(id="stats-header", classes="panel-header")
        yield StatBars()

    def on_mount(self) -> None:
        self._pinned = "possession"
        self._live = False
        self._render_headers()

    def update_match(self, m: Match, pinned: str | None = None) -> None:
        if pinned is not None:
            self._pinned = pinned
        self._live = m.is_live
        self.query_one(EventFeed).update_match(m)
        self.query_one(StatBars).update_match(m, pinned=self._pinned)
        self._render_headers()

    def set_pinned(self, pinned: str) -> None:
        self._pinned = pinned
        self.query_one(StatBars).set_pinned(pinned)
        self._render_headers()

    def _render_headers(self) -> None:
        events = Text()
        events.append("▚ KEY EVENTS", style=f"bold {theme.ACCENT}")
        if self._live:
            events.append("  ·  ", style=theme.UNLIT)
            events.append("● LIVE", style=theme.LIVE)
        self.query_one("#events-header", Static).update(events)

        stats = Text()
        stats.append("▚ MATCH STATS", style=f"bold {theme.ACCENT}")
        stats.append("  ·  pinned ", style=theme.DIM)
        stats.append(STAT_LABELS.get(self._pinned, self._pinned), style=theme.ACCENT2)
        self.query_one("#stats-header", Static).update(stats)
