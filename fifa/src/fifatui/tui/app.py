"""The Textual application: owns polling and routes between the list and watch screens."""

from __future__ import annotations

import time
from datetime import datetime, timedelta

from textual.app import App

from ..api.models import EASTERN, Match, eastern_today
from ..api.source import DataSource
from ..art import theme as stadium
from .screens.matchlist import MatchListScreen
from .screens.watch import WatchScreen

UPCOMING_WINDOW_DAYS = 45  # how far ahead the "upcoming fixtures" list reaches


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
        demo: str | None = None,
        demo_goal: bool = False,
        source: DataSource | None = None,
    ):
        super().__init__()
        self.league = league
        self.favorite = favorite
        self.refresh_interval = max(5.0, refresh)
        self.start_match = start_match
        self.date = date
        self.upcoming = False  # showing the forward date-range fixtures list
        self.demo = demo or ("goal" if demo_goal else None)

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

    def get_theme_variable_defaults(self) -> dict[str, str]:
        # Keeps styles.tcss parseable even before the stadium theme is active.
        return dict(stadium.THEME_VARIABLES)

    def on_mount(self) -> None:
        self.register_theme(stadium.build_theme())
        self.theme = "broadcast"
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
            if self.upcoming:
                end = (datetime.now(EASTERN) + timedelta(days=UPCOMING_WINDOW_DAYS)).strftime("%Y%m%d")
                param = f"{eastern_today()}-{end}"
            else:
                param = self.date or eastern_today()
            self.matches = await self.source.scoreboard(self.league, param)
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

    def _base_date(self) -> datetime:
        if self.date:
            try:
                return datetime.strptime(self.date, "%Y%m%d")
            except ValueError:
                pass
        return datetime.now(EASTERN)

    def shift_date(self, days: int) -> None:
        self.upcoming = False
        self.date = (self._base_date() + timedelta(days=days)).strftime("%Y%m%d")
        self.run_worker(self.refresh_data())

    def goto_today(self) -> None:
        self.upcoming = False
        self.date = None  # None => Eastern today (resolved in refresh_data)
        self.run_worker(self.refresh_data())

    def show_upcoming(self) -> None:
        self.upcoming = True  # forward date range (resolved in refresh_data)
        self.run_worker(self.refresh_data())

    def _dispatch_refresh(self) -> None:
        handler = getattr(self.screen, "on_data_refresh", None)
        if callable(handler):
            handler()

    def _handle_autostart(self) -> None:
        target: Match | None = None
        if self.start_match:
            target = self.match_by_id(self.start_match) or self.find_match(self.start_match)
        elif self.demo:
            target = next((m for m in self.matches if m.is_live), None) or (
                self.matches[0] if self.matches else None
            )
        if target is not None:
            self.open_match(target.id, demo=self.demo)

    def match_by_id(self, match_id: str) -> Match | None:
        return next((m for m in self.matches if m.id == match_id), None)

    def find_match(self, query: str) -> Match | None:
        q = query.lower()
        for m in self.matches:
            if q in (m.id, m.home.abbr.lower(), m.away.abbr.lower(),
                     m.home.name.lower(), m.away.name.lower()):
                return m
        return None

    def open_match(self, match_id: str, demo: str | None = None) -> None:
        if isinstance(self.screen, WatchScreen) and self.screen.match_id == match_id:
            return
        self.push_screen(WatchScreen(match_id, demo=demo))

    async def on_unmount(self) -> None:
        aclose = getattr(self.source, "aclose", None)
        if callable(aclose):
            await aclose()
