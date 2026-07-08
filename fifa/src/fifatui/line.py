"""Compact one-line renderer for statusline / tmux / shell-prompt use.

Textual-free and fast: it does a single scoreboard fetch, renders one line for the most
relevant match, and exits. A tiny cache file lets it flash a goal marker on the run right
after a score changes, so a tmux/prompt that re-runs ``fifa --line`` on an interval gets a
brief "GOAL!" pulse.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .api.models import Match, MatchState

_CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "fifatui" / "line_scores.json"


def pick_match(matches: list[Match], favorite: str | None = None) -> Match | None:
    """Choose the single most relevant match: live > favorite > next upcoming > recent."""
    if not matches:
        return None

    def involves_fav(m: Match) -> bool:
        if not favorite:
            return False
        fav = favorite.lower()
        return fav in (m.home.abbr.lower(), m.away.abbr.lower(), m.home.name.lower(), m.away.name.lower())

    live = [m for m in matches if m.is_live]
    if live:
        return next((m for m in live if involves_fav(m)), live[0])
    if favorite:
        fav_matches = [m for m in matches if involves_fav(m)]
        if fav_matches:
            fav_matches.sort(key=Match.sort_key)
            return fav_matches[0]
    upcoming = [m for m in matches if m.is_upcoming]
    if upcoming:
        upcoming.sort(key=lambda m: m.date)
        return upcoming[0]
    return matches[-1]  # most recent finished


def _shootout_suffix(m: Match) -> str:
    if m.has_shootout:
        return f" ({m.home.shootout_score or 0}-{m.away.shootout_score or 0}p)"
    return ""


def render_line(match: Match | None, goal_flash: bool = False, emoji: bool = True) -> str:
    """Render one compact status line for a match."""
    if match is None:
        return "⚽ no matches" if emoji else "no matches"

    h, a = match.home, match.away
    score = f"{h.abbr} {h.score}-{a.score} {a.abbr}"

    if match.state == MatchState.IN:
        live = "🔴" if emoji else "LIVE"
        clock = match.status_detail or match.display_clock
        suffix = _shootout_suffix(match)
        if goal_flash:
            mark = "⚽ GOAL!" if emoji else "GOAL!"
            return f"{mark} {score} {clock}{suffix}"
        return f"{live} {score} {clock}{suffix}"

    if match.state == MatchState.POST:
        tag = match.status_detail or "FT"
        return f"{tag} {score}{_shootout_suffix(match)}"

    # Pre-match: show kickoff time in US Eastern when available.
    et = match.kickoff_et()
    when = f"{et} ET" if et else ""
    clk = "⏱" if emoji else "@"
    return f"{clk} {h.abbr} v {a.abbr} {when}".rstrip()


def _read_cache() -> dict:
    try:
        return json.loads(_CACHE.read_text())
    except (OSError, ValueError):
        return {}


def _write_cache(data: dict) -> None:
    try:
        _CACHE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE.write_text(json.dumps(data))
    except OSError:
        pass  # statusline must never fail on cache problems


def detect_goal_flash(matches: list[Match], picked: Match | None) -> bool:
    """Return True if the picked match's total goals rose since the last invocation.

    Side effect: persists the current goal totals so the next call can compare.
    """
    prev = _read_cache()
    current = {m.id: m.home.score + m.away.score for m in matches}
    flash = False
    if picked is not None and picked.is_live:
        before = prev.get(picked.id)
        total = picked.home.score + picked.away.score
        flash = before is not None and total > before
    _write_cache(current)
    return flash


def oneline(matches: list[Match], favorite: str | None = None, emoji: bool = True, use_cache: bool = True) -> str:
    """Top-level helper: pick a match, compute the goal flash, render the line."""
    picked = pick_match(matches, favorite)
    flash = detect_goal_flash(matches, picked) if use_cache else False
    return render_line(picked, goal_flash=flash, emoji=emoji)
