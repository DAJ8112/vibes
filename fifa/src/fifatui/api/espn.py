"""ESPN data source.

ESPN's site API is free and needs no auth. A single ``scoreboard`` request per league
returns everything v1 needs: live clock, score, shootout score, per-team stats
(possession, shots, corners, fouls) and an event feed (goals + cards with player names).
That keeps polling to one lightweight request, which is both fast and polite.

Docs (community): https://github.com/pseudo-r/Public-ESPN-API
"""

from __future__ import annotations

import json

import httpx

from .models import (
    EventType,
    Match,
    MatchEvent,
    MatchState,
    Team,
    TeamStats,
)

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
_UA = "fifatui/0.1 (+https://github.com/local/fifatui)"

# Map ESPN statistic names -> our TeamStats fields.
_STAT_MAP = {
    "possessionPct": "possession",
    "totalShots": "shots",
    "shotsOnTarget": "shots_on_target",
    "wonCorners": "corners",
    "foulsCommitted": "fouls",
}


def _to_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _event_type(detail: dict) -> EventType:
    if detail.get("redCard"):
        return EventType.RED
    if detail.get("yellowCard"):
        return EventType.YELLOW
    if detail.get("shootout"):
        return EventType.SHOOTOUT
    if detail.get("scoringPlay"):
        if detail.get("ownGoal"):
            return EventType.OWN_GOAL
        if detail.get("penaltyKick"):
            return EventType.PENALTY_GOAL
        return EventType.GOAL
    return EventType.OTHER


def _parse_event(detail: dict) -> MatchEvent:
    clock = detail.get("clock") or {}
    players = [a.get("displayName", "") for a in detail.get("athletesInvolved") or []]
    players = [p for p in players if p]
    return MatchEvent(
        type=_event_type(detail),
        minute=clock.get("displayValue", ""),
        clock_value=_to_float(clock.get("value")) or 0.0,
        team_id=str((detail.get("team") or {}).get("id", "")),
        players=players,
        text=(detail.get("type") or {}).get("text", ""),
    )


def _parse_team(competitor: dict) -> Team:
    team = competitor.get("team") or {}
    stats = TeamStats()
    for s in competitor.get("statistics") or []:
        field_name = _STAT_MAP.get(s.get("name"))
        if not field_name:
            continue
        raw = s.get("displayValue")
        if field_name == "possession":
            stats.possession = _to_float(raw)
        else:
            setattr(stats, field_name, _to_int(raw))
    shootout = competitor.get("shootoutScore")
    return Team(
        id=str(team.get("id", "")),
        name=team.get("displayName", "?"),
        abbr=team.get("abbreviation", "?"),
        score=_to_int(competitor.get("score")),
        shootout_score=_to_int(shootout) if shootout not in (None, "") else None,
        home_away=competitor.get("homeAway", ""),
        color=team.get("color"),
        alt_color=team.get("alternateColor"),
        winner=bool(competitor.get("winner")),
        stats=stats,
    )


def _parse_match(event: dict, league: str) -> Match | None:
    competitions = event.get("competitions") or []
    if not competitions:
        return None
    comp = competitions[0]
    competitors = comp.get("competitors") or []
    if len(competitors) < 2:
        return None

    teams = [_parse_team(c) for c in competitors]
    home = next((t for t in teams if t.home_away == "home"), teams[0])
    away = next((t for t in teams if t.home_away == "away"), teams[-1])

    status = (comp.get("status") or {}).get("type") or {}
    venue = comp.get("venue") or {}
    address = venue.get("address") or {}
    notes = comp.get("notes") or []
    note = notes[0].get("headline", "") if notes else ""

    events = [_parse_event(d) for d in comp.get("details") or []]
    events.sort(key=lambda e: e.clock_value)

    return Match(
        id=str(event.get("id", "")),
        name=event.get("name", ""),
        league=league,
        state=MatchState(status.get("state", "pre")),
        status_detail=status.get("shortDetail") or status.get("detail", ""),
        status_name=status.get("name", ""),
        display_clock=(comp.get("status") or {}).get("displayClock", ""),
        period=_to_int((comp.get("status") or {}).get("period")),
        home=home,
        away=away,
        events=events,
        venue=venue.get("fullName", ""),
        venue_city=address.get("city", ""),
        note=note,
        date=event.get("date", ""),
    )


def parse_scoreboard(payload: dict, league: str) -> list[Match]:
    """Normalize a raw ESPN scoreboard payload into Match objects (pure; testable)."""
    matches = []
    for event in payload.get("events") or []:
        match = _parse_match(event, league)
        if match is not None:
            matches.append(match)
    matches.sort(key=Match.sort_key)
    return matches


class ESPNSource:
    """Async ESPN scoreboard client implementing the DataSource protocol."""

    def __init__(self, client: httpx.AsyncClient | None = None, timeout: float = 12.0):
        self._client = client
        self._own_client = client is None
        self._timeout = timeout

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                headers={"User-Agent": _UA},
            )
        return self._client

    async def scoreboard(self, league: str = "fifa.world", date: str | None = None) -> list[Match]:
        client = await self._get_client()
        params = {"dates": date} if date else None
        resp = await client.get(f"{BASE}/{league}/scoreboard", params=params)
        resp.raise_for_status()
        return parse_scoreboard(resp.json(), league)

    async def aclose(self) -> None:
        if self._own_client and self._client is not None:
            await self._client.aclose()
            self._client = None


def load_fixture(path: str, league: str = "fifa.world") -> list[Match]:
    """Parse a saved scoreboard JSON file (used by tests and offline demos)."""
    with open(path, encoding="utf-8") as fh:
        return parse_scoreboard(json.load(fh), league)


class FixtureSource:
    """A DataSource that serves pre-loaded matches (offline/dev mode, no network)."""

    def __init__(self, matches: list[Match]):
        self.matches = list(matches)

    async def scoreboard(self, league: str = "fifa.world", date: str | None = None) -> list[Match]:
        return list(self.matches)
