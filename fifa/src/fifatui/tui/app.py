"""The Textual application: owns polling and routes between the list and watch screens."""

from __future__ import annotations

import time

from textual.app import App

from ..api.models import Match
from ..api.source import DataSource
from .screens.matchlist import MatchListScreen
from .screens.watch import WatchScreen


class FifaApp(App):
    CSS_PATH = "styles.tcss"
    TITLE = "fifatui"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        league: str = "fifa.world",
        favorite: str | None = None,
        refresh: float = 15.0,
        start_match: str | None = None,
        date: str | None = None,
        demo_goal: bool = False,
        source: DataSource | None = None,
    ):
        super().__init__()
        self.league = league
        self.favorite = favorite
        self.refresh_interval = max(5.0, refresh)
        self.start_match = start_match
        self.date = date
        self.demo_goal = demo_goal

        if source is None:
            from ..api.espn import ESPNSource

            source = ESPNSource()
        self.source = source

        self.matches: list[Match] = []
        self.connection_ok = True
        self.last_error = ""
        self.last_updated = 0.0
        self._first_load = True
        self._polling = False

    def on_mount(self) -> None:
        self.push_screen(MatchListScreen())
        self.run_worker(self.refresh_data(), exclusive=False)
        self.set_interval(self.refresh_interval, self._scheduled_poll)

    async def _scheduled_poll(self) -> None:
        await self.refresh_data()

    async def refresh_data(self) -> None:
        if self._polling:
            return
        self._polling = True
        try:
            self.matches = await self.source.scoreboard(self.league, self.date)
            self.connection_ok = True
            self.last_error = ""
            self.last_updated = time.time()
        except Exception as exc:  # network hiccup: keep last data, flag the UI
            self.connection_ok = False
            self.last_error = str(exc)
        finally:
            self._polling = False

        self._dispatch_refresh()
        if self._first_load:
            self._first_load = False
            self._handle_autostart()

    def _dispatch_refresh(self) -> None:
        handler = getattr(self.screen, "on_data_refresh", None)
        if callable(handler):
            handler()

    def _handle_autostart(self) -> None:
        target: Match | None = None
        if self.start_match:
            target = self.match_by_id(self.start_match) or self.find_match(self.start_match)
        elif self.demo_goal:
            target = next((m for m in self.matches if m.is_live), None) or (
                self.matches[0] if self.matches else None
            )
        if target is not None:
            demo = self.demo_goal and not self.start_match
            self.open_match(target.id, demo=demo)

    def match_by_id(self, match_id: str) -> Match | None:
        return next((m for m in self.matches if m.id == match_id), None)

    def find_match(self, query: str) -> Match | None:
        q = query.lower()
        for m in self.matches:
            if q in (m.id, m.home.abbr.lower(), m.away.abbr.lower(),
                     m.home.name.lower(), m.away.name.lower()):
                return m
        return None

    def open_match(self, match_id: str, demo: bool = False) -> None:
        if isinstance(self.screen, WatchScreen) and self.screen.match_id == match_id:
            return
        self.push_screen(WatchScreen(match_id, demo=demo))

    async def on_unmount(self) -> None:
        aclose = getattr(self.source, "aclose", None)
        if callable(aclose):
            await aclose()
