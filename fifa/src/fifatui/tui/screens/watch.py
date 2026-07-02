"""Watch view: live scoreboard, stats, event feed, and goal celebrations for one match."""

from __future__ import annotations

import time

from rich.text import Text
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Static

from ...api.models import CELEBRATION_TYPES, EventType, Match, MatchEvent, MatchState
from ...art import theme
from ..anim import FrameAnimator
from ..widgets import EventFeed, GoalCelebration, ScoreBoard, StatBars
from ..widgets.banner import EventBanner
from ..widgets.pixelscore import PixelScore
from ..widgets.ticker import ScoreTicker


class WatchScreen(Screen):
    BINDINGS = [
        ("escape", "back", "Back"),
        ("left", "back", "Back"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, match_id: str, demo: str | None = None):
        super().__init__()
        self.match_id = match_id
        self.demo = demo
        self._seen_keys: set[str] = set()
        self._initialized = False
        self._celebrating = False
        self._breath = FrameAnimator(self)
        self._last_state: MatchState | None = None
        self._last_status: str | None = None

    def compose(self) -> ComposeResult:
        yield Static(id="topbar")
        yield Static(id="statusbar")
        yield ScoreBoard()
        yield StatBars()
        yield EventFeed()
        yield ScoreTicker()
        yield EventBanner()
        yield GoalCelebration()
        yield Footer()

    def on_mount(self) -> None:
        self.on_data_refresh()
        if self.demo:
            self.set_timer(1.5, self._run_demo)

    def on_unmount(self) -> None:
        self._breath.stop()

    def _run_demo(self) -> None:
        kind = self.demo
        banner = self.query_one(EventBanner)
        if kind == "goal":
            self._demo_goal()
        elif kind == "yellow":
            banner.show_card(theme.CARD_YELLOW, "YELLOW CARD", "Demo Player", "45'")
        elif kind == "red":
            banner.show_card(theme.CARD_RED, "RED CARD", "Demo Player", "45'")
        elif kind == "sub":
            m = self.app.match_by_id(self.match_id)
            event = MatchEvent(type=EventType.SUB, minute="60'", clock_value=3600.0,
                               team_id=(m.home.id if m else ""),
                               players=["Demo On", "Demo Off"], text="Substitution")
            if m is not None:
                banner.show_line(self._sub_line(m, event))
        elif kind == "kickoff":
            banner.show_pixel("KICK OFF")
        elif kind == "ht":
            banner.show_pixel("HT")
        elif kind == "ft":
            banner.show_pixel("FULL TIME")

    # Called by the app after every poll.
    def on_data_refresh(self) -> None:
        m = self.app.match_by_id(self.match_id)
        if m is None:
            self._update_status(None)
            return

        new_events = self._detect_new_events(m)
        self.query_one(ScoreBoard).update_match(m)
        self.query_one(StatBars).update_match(m)
        self.query_one(EventFeed).update_match(m)
        self.query_one(ScoreTicker).update_matches(self.app.matches, exclude_id=self.match_id)
        self._update_topbar(m)
        self._update_status(m)

        if m.is_live and not self._breath.running:
            self._breath.start(2, self._breathe)
        elif not m.is_live:
            self._breath.stop()

        self._route_events(m, new_events)
        self._detect_transitions(m)

    def _breathe(self, elapsed: float) -> bool:
        if self.is_current and self.app.app_focus:
            self.query_one(ScoreBoard).pulse(int(elapsed * 2))
        return True

    def _detect_new_events(self, m: Match) -> list[MatchEvent]:
        current_keys = {e.key for e in m.events}
        if not self._initialized:
            # First load: remember existing events without replaying historical ones.
            self._seen_keys = current_keys
            self._initialized = True
            return []
        new = [e for e in m.events if e.key not in self._seen_keys]
        self._seen_keys |= current_keys
        return new

    def _route_events(self, m: Match, new: list[MatchEvent]) -> None:
        goals = [e for e in new if e.type in CELEBRATION_TYPES]
        if goals and not self._celebrating:
            goal = goals[-1]
            side = "home" if goal.team_id == m.home.id else "away"
            self.query_one(PixelScore).animate_goal(side)
            self._celebrate(goal, m.team(goal.team_id))
            return  # a goal outranks every banner from this poll
        if self._celebrating:
            return
        banner = self.query_one(EventBanner)
        for e in new:
            if e.type == EventType.YELLOW:
                banner.show_card(theme.CARD_YELLOW, "YELLOW CARD", e.scorer, e.minute)
            elif e.type == EventType.RED:
                banner.show_card(theme.CARD_RED, "RED CARD", e.scorer, e.minute)
            elif e.type == EventType.SUB:
                banner.show_line(self._sub_line(m, e))

    @staticmethod
    def _sub_line(m: Match, e: MatchEvent) -> Text:
        team = m.team(e.team_id)
        line = Text()
        line.append("⇄  ", style=f"bold {theme.AMBER}")
        if team is not None:
            line.append(f"{team.abbr}  ", style=f"bold {team.color_hex}")
        if len(e.players) > 1:
            line.append(f"ON {e.players[0]}", style=theme.AMBER)
            line.append(f"   OFF {e.players[1]}", style=theme.TEXT_DIM)
        else:
            line.append(e.scorer or e.text or "Substitution", style=theme.AMBER)
        if e.minute:
            line.append(f"   {e.minute}", style=theme.AMBER_DIM)
        return line

    def _detect_transitions(self, m: Match) -> None:
        prev_state, prev_status = self._last_state, self._last_status
        self._last_state, self._last_status = m.state, m.status_name
        if prev_state is None or self._celebrating:
            return
        banner = self.query_one(EventBanner)
        if prev_state == MatchState.PRE and m.state == MatchState.IN:
            banner.show_pixel("KICK OFF")
        elif prev_state == MatchState.IN and m.state == MatchState.POST:
            banner.show_pixel("FULL TIME")
        elif "HALFTIME" in (m.status_name or "") and "HALFTIME" not in (prev_status or ""):
            banner.show_pixel("HT")

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
        self.query_one(PixelScore).animate_goal("home")
        self._celebrate(event, team)

    def _update_topbar(self, m: Match) -> None:
        league = "FIFA World Cup 2026" if m.league == "fifa.world" else m.league
        top = Text()
        top.append("◉ ", style=theme.AMBER)
        top.append(league.upper(), style=f"bold {theme.AMBER}")
        bits = []
        if m.note:
            bits.append(m.note)
        venue = " · ".join(p for p in (m.venue, m.venue_city) if p)
        if venue:
            bits.append(venue)
        if bits:
            top.append("   " + "   ".join(bits), style=theme.AMBER_DIM)
        self.query_one("#topbar", Static).update(top)

    def _update_status(self, m: Match | None) -> None:
        app = self.app
        if not app.connection_ok:
            left = Text("▲ RECONNECTING", style=f"bold {theme.CARD_YELLOW}")
        elif app.last_updated:
            ago = max(0, int(time.time() - app.last_updated))
            left = Text(f"● updated {ago}s ago", style=theme.AMBER_DIM)
        else:
            left = Text("loading…", style=theme.TEXT_DIM)
        if m is None:
            left = Text("match not in today's list", style=theme.CARD_YELLOW)
        line = Text()
        line.append_text(left)
        line.append("     esc back  ·  r refresh  ·  q quit", style=theme.TEXT_DIM)
        self.query_one("#statusbar", Static).update(line)

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        self.app.run_worker(self.app.refresh_data())
