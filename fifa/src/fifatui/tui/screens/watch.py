"""Watch view: scoreboard + pinned side panel + interactive console for one match.

Layout mirrors the broadcast redesign: a bordered scoreboard on top, a pinned
key-events/stats column bottom-left, and a REPL-style command console bottom-right.
Goal celebrations and event banners still play as full-screen / lower-third overlays.
"""

from __future__ import annotations

import time

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen

from ...api.models import (
    CELEBRATION_TYPES,
    EventType,
    Match,
    MatchEvent,
    MatchExtras,
    MatchState,
)
from ...art import theme
from ..anim import FrameAnimator
from ..widgets import (
    ConsolePanel,
    EventBanner,
    GoalCelebration,
    ScoreBoard,
    ShootoutPanel,
    SidePanel,
)
from ..widgets.pixelscore import PixelScore
from ..widgets.ticker import ScoreTicker

#: How long a fetched summary stays fresh before the console re-fetches it.
_EXTRAS_TTL = 30.0

#: Scripted shootout for --demo pens: (side, scored, taker). Home wins 4-3.
_DEMO_KICKS = [
    ("home", True, "Demo Taker 1"), ("away", True, "Demo Taker 2"),
    ("home", False, "Demo Taker 3"), ("away", True, "Demo Taker 4"),
    ("home", True, "Demo Taker 5"), ("away", False, "Demo Taker 6"),
    ("home", True, "Demo Taker 7"), ("away", True, "Demo Taker 8"),
    ("home", True, "Demo Taker 9"), ("away", False, "Demo Taker 10"),
]


class WatchScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back", priority=True),
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
        self._demo_queue: list[tuple[str, bool, str]] = []
        self._demo_timer = None
        self._pinned = "possession"
        self._extras: MatchExtras | None = None
        self._extras_ts = 0.0

    def compose(self) -> ComposeResult:
        yield ScoreBoard()
        with Horizontal(id="watch-bottom"):
            yield SidePanel()
            yield ConsolePanel()
        yield ScoreTicker()
        yield EventBanner()
        yield GoalCelebration()

    def on_mount(self) -> None:
        console = self.query_one(ConsolePanel)
        console.bind_host(self)
        self.on_data_refresh()
        console.welcome(self.app.match_by_id(self.match_id))
        console.focus_input()
        if self.demo:
            self.set_timer(1.5, self._run_demo)

    def on_screen_resume(self) -> None:
        try:
            self.query_one(ConsolePanel).focus_input()
        except Exception:
            pass

    def on_unmount(self) -> None:
        self._breath.stop()
        if self._demo_timer is not None:
            self._demo_timer.stop()

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
        elif kind == "pens":
            self._demo_pens()
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
            self._update_board_header(None)
            return

        new_events = self._detect_new_events(m)
        self.query_one(ScoreBoard).update_match(m)
        self.query_one(SidePanel).update_match(m, pinned=self._pinned)
        self.query_one(ScoreTicker).update_matches(self.app.matches, exclude_id=self.match_id)
        self._update_board_header(m)

        if m.is_live and not self._breath.running:
            self._breath.start(2, self._breathe)
        elif not m.is_live:
            self._breath.stop()

        self._route_events(m, new_events)
        self._detect_transitions(m)

    def _breathe(self, elapsed: float) -> bool:
        if self.is_current and self.app.app_focus:
            self.query_one(ScoreBoard).pulse(int(elapsed * 2))
            self._update_board_header(self.app.match_by_id(self.match_id))
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
        line.append("⇄  ", style=f"bold {theme.ACCENT}")
        if team is not None:
            line.append(f"{team.abbr}  ", style=f"bold {team.color_hex}")
        if len(e.players) > 1:
            line.append(f"ON {e.players[0]}", style=theme.FG)
            line.append(f"   OFF {e.players[1]}", style=theme.DIM)
        else:
            line.append(e.scorer or e.text or "Substitution", style=theme.FG)
        if e.minute:
            line.append(f"   {e.minute}", style=theme.DIM)
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

    def _demo_pens(self) -> None:
        m = self.app.match_by_id(self.match_id)
        if m is None:
            return
        if m.home.shootout_score is None:
            m.home.shootout_score = 0
        if m.away.shootout_score is None:
            m.away.shootout_score = 0
        self._demo_queue = list(_DEMO_KICKS)
        self._demo_timer = self.set_interval(1.2, self._demo_pens_tick)

    def _demo_pens_tick(self) -> None:
        m = self.app.match_by_id(self.match_id)
        if m is None or not self._demo_queue:
            if self._demo_timer is not None:
                self._demo_timer.stop()
            return
        side, scored, taker = self._demo_queue.pop(0)
        team = m.home if side == "home" else m.away
        event = MatchEvent(
            type=EventType.SHOOTOUT,
            minute="120'",
            clock_value=7200.0,
            team_id=team.id,
            players=[taker],
            text="Penalty - Scored" if scored else "Penalty - Missed",
        )
        m.events.append(event)
        self._seen_keys.add(event.key)  # keep _detect_new_events from replaying it
        if scored:
            team.shootout_score = (team.shootout_score or 0) + 1
        self.query_one(ShootoutPanel).update_match(m)
        self.query_one(ScoreBoard).update_match(m)
        if not self._demo_queue and self._demo_timer is not None:
            self._demo_timer.stop()

    def _update_board_header(self, m: Match | None) -> None:
        board = self.query_one(ScoreBoard)
        league = "FIFA World Cup 2026" if self.app.league == "fifa.world" else self.app.league
        left = Text()
        left.append("◉ ", style=theme.ACCENT)
        left.append(league.upper(), style=f"bold {theme.ACCENT}")
        if m is not None:
            for bit in (m.note, m.venue, m.venue_city):
                if bit:
                    left.append("  ·  ", style=theme.UNLIT)
                    left.append(bit, style=theme.DIM)
        board.set_header(left, self._refresh_state(m))

    def _refresh_state(self, m: Match | None) -> Text:
        app = self.app
        if m is None:
            return Text("match not in today's list", style=theme.WARN)
        if not app.connection_ok:
            return Text("▲ reconnecting", style=f"bold {theme.WARN}")
        if app.last_updated:
            ago = max(0, int(time.time() - app.last_updated))
            return Text(f"updated {ago}s ago", style=theme.DIM)
        return Text("loading…", style=theme.DIM)

    # -- ConsoleHost interface -------------------------------------------

    def current_match(self) -> Match | None:
        return self.app.match_by_id(self.match_id)

    def cached_extras(self) -> MatchExtras | None:
        if self._extras is not None and (time.time() - self._extras_ts) < _EXTRAS_TTL:
            return self._extras
        return None

    def request_extras(self, callback) -> None:
        self.app.run_worker(self._fetch_extras(callback), exclusive=False)

    async def _fetch_extras(self, callback) -> None:
        extras: MatchExtras | None = None
        summary = getattr(self.app.source, "summary", None)
        if callable(summary):
            try:
                extras = await summary(self.app.league, self.match_id)
            except Exception:
                extras = None
        if extras is not None:
            self._extras = extras
            self._extras_ts = time.time()
        callback(extras if extras is not None else self._extras)

    def pin_metric(self, key: str) -> None:
        self._pinned = key
        self.query_one(SidePanel).set_pinned(key)

    def do_refresh(self) -> None:
        self.action_refresh()

    def go_back(self) -> None:
        self.action_back()

    def do_quit(self) -> None:
        self.app.exit()

    # -- actions ----------------------------------------------------------

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        self.app.run_worker(self.app.refresh_data())
