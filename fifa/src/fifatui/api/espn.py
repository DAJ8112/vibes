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
    CommentaryLine,
    EventType,
    Lineup,
    LineupPlayer,
    Match,
    MatchEvent,
    MatchExtras,
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
        clock_seconds=_to_float((comp.get("status") or {}).get("clock")) or 0.0,
        period=_to_int((comp.get("status") or {}).get("period")),
        home=home,
        away=away,
        events=events,
        venue=venue.get("fullName", ""),
        venue_city=address.get("city", ""),
        note=note,
        date=event.get("date", ""),
    )


# Curated boxscore stats for the console `stats` table: (ESPN name, label, suffix).
_SUMMARY_STATS = [
    ("possessionPct", "Possession", "%"),
    ("totalShots", "Shots", ""),
    ("shotsOnTarget", "On target", ""),
    ("saves", "Saves", ""),
    ("wonCorners", "Corners", ""),
    ("foulsCommitted", "Fouls", ""),
    ("offsides", "Offsides", ""),
    ("accuratePasses", "Passes", ""),
    ("totalTackles", "Tackles", ""),
    ("interceptions", "Interceptions", ""),
]


def _stat_lookup(team: dict) -> dict[str, str]:
    return {
        s.get("name"): s.get("displayValue", "")
        for s in team.get("statistics") or []
        if s.get("name")
    }


def _fmt_stat(value: str, suffix: str) -> str:
    value = (value or "").strip()
    if not value:
        return "—"
    if suffix and suffix not in value:
        value += suffix
    return value


def _parse_lineup(roster: dict) -> Lineup:
    starters = []
    for p in roster.get("roster") or []:
        if not p.get("starter"):
            continue
        athlete = p.get("athlete") or {}
        position = p.get("position") or {}
        starters.append(
            LineupPlayer(
                jersey=str(p.get("jersey", "") or ""),
                name=athlete.get("displayName", "?"),
                position=position.get("abbreviation", "") or "",
            )
        )
    return Lineup(formation=str(roster.get("formation", "") or ""), starters=starters)


def parse_summary(payload: dict) -> MatchExtras:
    """Normalize a raw ESPN ``summary`` payload into MatchExtras (pure; testable)."""
    extras = MatchExtras()

    venue = payload.get("gameInfo", {}).get("venue") or {}
    address = venue.get("address") or {}
    extras.venue_name = venue.get("fullName", "")
    extras.venue_city = address.get("city", "")
    extras.venue_country = address.get("country", "")

    rosters = payload.get("rosters") or []
    for roster in rosters:
        lineup = _parse_lineup(roster)
        if roster.get("homeAway") == "home":
            extras.home_lineup = lineup
        elif roster.get("homeAway") == "away":
            extras.away_lineup = lineup

    teams = (payload.get("boxscore") or {}).get("teams") or []
    home_team = next((t for t in teams if t.get("homeAway") == "home"), None)
    away_team = next((t for t in teams if t.get("homeAway") == "away"), None)
    if home_team and away_team:
        home_stats = _stat_lookup(home_team)
        away_stats = _stat_lookup(away_team)
        for name, label, suffix in _SUMMARY_STATS:
            if name not in home_stats and name not in away_stats:
                continue
            extras.stat_rows.append((
                label,
                _fmt_stat(home_stats.get(name, ""), suffix),
                _fmt_stat(away_stats.get(name, ""), suffix),
            ))

    for c in payload.get("commentary") or []:
        text = (c.get("text") or "").strip()
        if not text:
            continue
        clock = c.get("time") or {}
        extras.commentary.append(
            CommentaryLine(minute=clock.get("displayValue", ""), text=text)
        )

    return extras


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

    async def summary(self, league: str, match_id: str) -> MatchExtras | None:
        client = await self._get_client()
        resp = await client.get(f"{BASE}/{league}/summary", params={"event": match_id})
        resp.raise_for_status()
        return parse_summary(resp.json())

    async def aclose(self) -> None:
        if self._own_client and self._client is not None:
            await self._client.aclose()
            self._client = None


def load_fixture(path: str, league: str = "fifa.world") -> list[Match]:
    """Parse a saved scoreboard JSON file (used by tests and offline demos)."""
    with open(path, encoding="utf-8") as fh:
        return parse_scoreboard(json.load(fh), league)


def load_summary_fixture(path: str) -> MatchExtras:
    """Parse a saved summary JSON file (offline dev of the console commands)."""
    with open(path, encoding="utf-8") as fh:
        return parse_summary(json.load(fh))


class FixtureSource:
    """A DataSource that serves pre-loaded matches (offline/dev mode, no network).

    An optional ``extras`` MatchExtras is returned for every ``summary`` call, so
    the console commands can be exercised offline against a saved summary payload.
    """

    def __init__(self, matches: list[Match], extras: MatchExtras | None = None):
        self.matches = list(matches)
        self.extras = extras

    async def scoreboard(self, league: str = "fifa.world", date: str | None = None) -> list[Match]:
        return list(self.matches)

    async def summary(self, league: str, match_id: str) -> MatchExtras | None:
        return self.extras
