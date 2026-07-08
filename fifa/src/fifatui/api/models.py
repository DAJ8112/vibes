"""Normalized data models.

These dataclasses are the *only* shapes the UI layer ever sees. Every data source
(ESPN today, football-data.org / API-Football tomorrow) normalizes its raw JSON into
these, so swapping the source never touches the TUI or statusline code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from zoneinfo import ZoneInfo

from ..colors import vivid_hex
from ..flags import flag_for


_MINUTE_RE = re.compile(r"^\d+'")  # a running minute clock, e.g. "72'"

# All match times display in US Eastern, labeled generically "ET" (avoids EST/EDT/DST
# confusion). ESPN's raw dates are UTC (see Match.date).
EASTERN = ZoneInfo("America/New_York")
ET_LABEL = "ET"


def eastern_today() -> str:
    """Today's date (YYYYMMDD) in US Eastern — the 'today' anchor for ESPN.

    ESPN's default scoreboard (no ``dates=``) jumps ahead to the next matchday, so we
    always pass an explicit Eastern date instead of relying on the server default.
    """
    return datetime.now(EASTERN).strftime("%Y%m%d")


class MatchState(str, Enum):
    PRE = "pre"
    IN = "in"
    POST = "post"


class EventType(str, Enum):
    GOAL = "goal"
    OWN_GOAL = "own_goal"
    PENALTY_GOAL = "penalty_goal"
    YELLOW = "yellow"
    RED = "red"
    SUB = "sub"
    SHOOTOUT = "shootout"
    OTHER = "other"


#: Event types that should trigger the full-screen goal celebration.
CELEBRATION_TYPES = {EventType.GOAL, EventType.OWN_GOAL, EventType.PENALTY_GOAL}

#: Icon shown next to each event in the feed.
EVENT_ICON = {
    EventType.GOAL: "⚽",          # ⚽
    EventType.OWN_GOAL: "⚽",      # ⚽ (own goal, styled differently)
    EventType.PENALTY_GOAL: "⚽",  # ⚽
    EventType.YELLOW: "\U0001f7e8",    # 🟨
    EventType.RED: "\U0001f7e5",       # 🟥
    EventType.SUB: "\U0001f501",       # 🔁
    EventType.SHOOTOUT: "\U0001f3af",  # 🎯
    EventType.OTHER: "•",         # •
}


@dataclass
class TeamStats:
    possession: float | None = None
    shots: int | None = None
    shots_on_target: int | None = None
    corners: int | None = None
    fouls: int | None = None


@dataclass
class Team:
    id: str
    name: str
    abbr: str
    score: int = 0
    shootout_score: int | None = None
    home_away: str = ""  # "home" | "away"
    color: str | None = None  # hex string, no leading '#'
    alt_color: str | None = None
    winner: bool = False
    stats: TeamStats = field(default_factory=TeamStats)

    @property
    def flag(self) -> str:
        return flag_for(self.abbr)

    @property
    def color_hex(self) -> str:
        """Team colour, lightened if needed to stay readable on a dark background."""
        return vivid_hex(self.color, self.alt_color)


@dataclass
class MatchEvent:
    type: EventType
    minute: str  # display clock, e.g. "72'" or "90'+1'"
    clock_value: float  # numeric seconds, for ordering
    team_id: str
    players: list[str] = field(default_factory=list)  # [scorer, assist...] / [recipient]
    text: str = ""

    @property
    def key(self) -> str:
        """Stable identity used to diff event lists between polls (goal detection)."""
        who = self.players[0] if self.players else ""
        return f"{self.type.value}|{self.minute}|{self.team_id}|{who}"

    @property
    def scorer(self) -> str:
        return self.players[0] if self.players else ""

    @property
    def assist(self) -> str:
        return self.players[1] if len(self.players) > 1 else ""


@dataclass
class LineupPlayer:
    jersey: str
    name: str
    position: str = ""  # "G", "D", "M", "F" when known


@dataclass
class Lineup:
    formation: str = ""
    starters: list[LineupPlayer] = field(default_factory=list)


@dataclass
class CommentaryLine:
    minute: str  # display clock, e.g. "58'" ("" for pre-match notes)
    text: str


@dataclass
class MatchExtras:
    """Richer per-match detail from ESPN's ``summary`` endpoint (fetched on demand).

    Everything the console's ``lineups`` / ``commentary`` / ``stats`` / ``where``
    commands need beyond the always-polled scoreboard.
    """

    venue_name: str = ""
    venue_city: str = ""
    venue_country: str = ""
    home_lineup: Lineup = field(default_factory=Lineup)
    away_lineup: Lineup = field(default_factory=Lineup)
    commentary: list[CommentaryLine] = field(default_factory=list)  # oldest first
    #: Full boxscore comparison table, ordered: (label, home_display, away_display).
    stat_rows: list[tuple[str, str, str]] = field(default_factory=list)


@dataclass
class Match:
    id: str
    name: str
    league: str
    state: MatchState
    status_detail: str  # "108'", "HT", "FT", "FT-Pens"
    status_name: str  # raw STATUS_* token
    display_clock: str  # minute-only clock, e.g. "72'" or "90'+3'"
    clock_seconds: float  # numeric elapsed seconds, for M:SS display
    period: int
    home: Team
    away: Team
    events: list[MatchEvent] = field(default_factory=list)
    venue: str = ""
    venue_city: str = ""
    note: str = ""  # group/round headline, e.g. "Paraguay advance 4-3 on penalties"
    date: str = ""  # ISO start time (UTC)

    def clock_display(self, extra_seconds: float = 0.0) -> str:
        """Match clock for the UI. While the clock is running (live, in a half)
        show M:SS, advancing `extra_seconds` past the last poll's value but never
        rolling into the next minute (ESPN reports the clock per whole minute, so
        the true time is within [base, base+60) and we estimate the seconds
        locally). Keep the source label for stoppage time ("90'+3'", where the
        numeric clock is capped), breaks ("HT"), and any non-live state ("FT",
        kickoff time)."""
        detail = self.status_detail or self.display_clock
        if self.state == MatchState.IN and _MINUTE_RE.match(detail) and "+" not in detail:
            base = max(0, int(self.clock_seconds))
            minute_cap = (base // 60) * 60 + 59
            total = int(min(base + max(0.0, extra_seconds), minute_cap))
            return f"{total // 60}:{total % 60:02d}"
        return detail

    def kickoff_et(self) -> str:
        """Kickoff 'HH:MM' in US Eastern, or '' if the date is unknown/unparseable.

        ESPN dates are UTC with a fixed format (``2026-07-09T20:00Z``); strptime keeps
        the parse deterministic across Python versions (3.10 fromisoformat is fussy
        about the ``Z`` suffix and missing seconds).
        """
        for fmt in ("%Y-%m-%dT%H:%MZ", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                dt = datetime.strptime(self.date, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            return dt.astimezone(EASTERN).strftime("%H:%M")
        return ""

    @property
    def is_live(self) -> bool:
        return self.state == MatchState.IN

    @property
    def is_finished(self) -> bool:
        return self.state == MatchState.POST

    @property
    def is_upcoming(self) -> bool:
        return self.state == MatchState.PRE

    @property
    def has_shootout(self) -> bool:
        return self.home.shootout_score is not None or self.away.shootout_score is not None

    def team(self, team_id: str) -> Team | None:
        if self.home.id == team_id:
            return self.home
        if self.away.id == team_id:
            return self.away
        return None

    def sort_key(self) -> tuple:
        """Order for the match list: live first, then upcoming, then finished."""
        order = {MatchState.IN: 0, MatchState.PRE: 1, MatchState.POST: 2}
        return (order.get(self.state, 3), self.date)
