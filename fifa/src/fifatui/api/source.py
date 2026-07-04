"""Data-source abstraction.

Anything that can produce a list of normalized ``Match`` objects for a league is a
``DataSource``. ESPN is the only implementation today; football-data.org or API-Football
can be added later without the UI knowing the difference.
"""

from __future__ import annotations

from typing import Protocol

from .models import Match, MatchExtras


class DataSource(Protocol):
    async def scoreboard(self, league: str, date: str | None = None) -> list[Match]:
        """Return today's (or ``date``'s) matches for ``league``, normalized."""
        ...

    async def summary(self, league: str, match_id: str) -> MatchExtras | None:
        """Return richer detail (lineups, commentary, full stats, venue) for one match.

        Optional: a source may return ``None`` when it has no summary data.
        """
        ...
