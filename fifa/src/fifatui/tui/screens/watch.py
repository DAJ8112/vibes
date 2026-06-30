"""Watch view: live scoreboard, stats, event feed, and goal celebrations for one match."""

from __future__ import annotations

import time

from rich.text import Text
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Static

from ...api.models import CELEBRATION_TYPES, EventType, Match, MatchEvent
from ..widgets import EventFeed, GoalCelebration, ScoreBoard, StatBars


class WatchScreen(Screen):
    BINDINGS = [
        ("escape", "back", "Back"),
        ("left", "back", "Back"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, match_id: str, demo: bool = False):
        super().__init__()
        self.match_id = match_id
        self.demo = demo
        self._seen_keys: set[str] = set()
        self._initialized = False
        self._celebrating = False

    def compose(self) -> ComposeResult:
        yield Static(id="topbar")
        yield Static(id="statusbar")
        yield ScoreBoard()
        yield StatBars()
        yield EventFeed()
        yield GoalCelebration()
        yield Footer()

    def on_mount(self) -> None:
        self.on_data_refresh()
        if self.demo:
            self.set_timer(1.5, self._demo_goal)

    # Called by the app after every poll.
    def on_data_refresh(self) -> None:
        m = self.app.match_by_id(self.match_id)
        if m is None:
            self._update_status(None)
            return

        new_goals = self._detect_new_goals(m)
        self.query_one(ScoreBoard).update_match(m)
        self.query_one(StatBars).update_match(m)
        self.query_one(EventFeed).update_match(m)
        self._update_topbar(m)
        self._update_status(m)

        if new_goals and not self._celebrating:
            goal = new_goals[-1]
            self._celebrate(goal, m.team(goal.team_id))

    def _detect_new_goals(self, m: Match) -> list[MatchEvent]:
        current_keys = {e.key for e in m.events}
        if not self._initialized:
            # First load: remember existing events without celebrating historical goals.
            self._seen_keys = current_keys
            self._initialized = True
            return []
        new = [e for e in m.events if e.type in CELEBRATION_TYPES and e.key not in self._seen_keys]
        self._seen_keys |= current_keys
        return new

    def _celebrate(self, event: MatchEvent, team) -> None:
        self._celebrating = True
        self.query_one(GoalCelebration).show(event, team, on_done=self._celebration_done)

    def _celebration_done(self) -> None:
        self._celebrating = False

    def _demo_goal(self) -> None:
        m = self.app.match_by_id(self.match_id)
        team = m.home if m else None
        event = MatchEvent(
            type=EventType.GOAL,
            minute=(m.status_detail if m else "45'"),
            clock_value=1e9,
            team_id=(team.id if team else ""),
            players=["Demo Scorer", "Demo Assist"],
            text="Goal",
        )
        self._celebrate(event, team)

    def _update_topbar(self, m: Match) -> None:
        league = "FIFA World Cup 2026" if m.league == "fifa.world" else m.league
        bits = [f"⚽ {league}"]
        if m.note:
            bits.append(m.note)
        venue = " · ".join(p for p in (m.venue, m.venue_city) if p)
        if venue:
            bits.append(venue)
        self.query_one("#topbar", Static).update("   ".join(bits))

    def _update_status(self, m: Match | None) -> None:
        app = self.app
        if not app.connection_ok:
            left = Text("⚠ reconnecting…", style="yellow")
        elif app.last_updated:
            ago = max(0, int(time.time() - app.last_updated))
            left = Text(f"● updated {ago}s ago", style="green")
        else:
            left = Text("loading…", style="dim")
        if m is None:
            left = Text("match not in today's list", style="yellow")
        line = Text()
        line.append_text(left)
        line.append("     esc back  ·  r refresh  ·  q quit", style="dim")
        self.query_one("#statusbar", Static).update(line)

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        self.app.run_worker(self.app.refresh_data())
