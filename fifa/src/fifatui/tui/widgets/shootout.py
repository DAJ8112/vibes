"""Penalty shootout tracker: one kick-marker row per team plus the latest kick."""

from __future__ import annotations

from typing import NamedTuple

from rich.console import Group
from rich.text import Text
from textual.widgets import Static

from ...api.models import EventType, Match, MatchEvent, MatchExtras, Team
from ...art import theme
from ...art.glyphs import EVENT_GLYPH
from ...art.pixelflags import team_chip

MIN_SLOTS = 5
MARK_SCORED = "██"
MARK_MISSED = "▒▒"
MARK_PENDING = "··"


class _Kick(NamedTuple):
    scored: bool
    player: str


class _Latest(NamedTuple):
    team: Team | None
    player: str
    scored: bool


def kick_scored(e: MatchEvent) -> bool:
    """ESPN kick texts are "Penalty - Scored" / "Penalty - Missed" / "Penalty - Saved";
    anything that isn't explicitly scored counts as a miss."""
    return "scored" in e.text.lower()


def shootout_kicks(m: Match) -> tuple[list[MatchEvent], list[MatchEvent]]:
    """(home, away) kicks in taken order (the stable event sort keeps ESPN's order)."""
    kicks = [e for e in m.events if e.type == EventType.SHOOTOUT]
    home = [e for e in kicks if e.team_id == m.home.id]
    away = [e for e in kicks if e.team_id == m.away.id]
    return home, away


def latest_kick(m: Match) -> MatchEvent | None:
    return next((e for e in reversed(m.events) if e.type == EventType.SHOOTOUT), None)


class ShootoutPanel(Static):
    def update_match(self, m: Match, extras: MatchExtras | None = None) -> None:
        home, away, latest = self._kick_rows(m, extras)
        # Kick details can land a poll before shootoutScore does, and vice versa.
        visible = m.has_shootout or bool(home or away)
        self.styles.display = "block" if visible else "none"
        if visible:
            self.update(self._build(m, home, away, latest))

    @staticmethod
    def _kick_rows(
        m: Match, extras: MatchExtras | None
    ) -> tuple[list[_Kick], list[_Kick], _Latest | None]:
        """Uniform (home, away, latest) kick rows.

        The summary's per-kick sequence (incl. misses) wins when loaded; otherwise fall
        back to the scoreboard SHOOTOUT events (scored kicks only, plus the ``--demo``
        scripted kicks)."""
        if extras is not None and extras.shootout:
            def row(team_id: str) -> list[_Kick]:
                shots = sorted(
                    (k for k in extras.shootout if k.team_id == team_id),
                    key=lambda k: k.order,
                )
                return [_Kick(k.scored, k.player) for k in shots]

            last = max(extras.shootout, key=lambda k: k.order)
            latest = _Latest(m.team(last.team_id), last.player, last.scored)
            return row(m.home.id), row(m.away.id), latest

        home_ev, away_ev = shootout_kicks(m)
        home = [_Kick(kick_scored(e), e.scorer) for e in home_ev]
        away = [_Kick(kick_scored(e), e.scorer) for e in away_ev]
        last_ev = latest_kick(m)
        latest = (
            _Latest(m.team(last_ev.team_id), last_ev.scorer, kick_scored(last_ev))
            if last_ev is not None
            else None
        )
        return home, away, latest

    def _build(self, m: Match, home: list[_Kick], away: list[_Kick],
               latest: _Latest | None) -> Group:
        slots = max(MIN_SLOTS, len(home), len(away))
        rows = [
            Text("┌ PENALTY SHOOTOUT ┐", style=theme.AMBER_DIM, justify="center"),
            Text(""),
            self._team_row(m.home, home, slots),
            self._team_row(m.away, away, slots),
        ]
        if latest is not None:
            rows.append(Text(""))
            rows.append(self._latest_line(latest))
        return Group(*rows)

    @staticmethod
    def _team_row(team: Team, kicks: list[_Kick], slots: int) -> Text:
        color = team.color_hex
        t = Text(justify="center")
        t.append_text(team_chip(team.abbr, color))
        t.append("  ")
        for i in range(slots):
            if i >= len(kicks):
                t.append(MARK_PENDING, style=theme.UNLIT)
            elif kicks[i].scored:
                t.append(MARK_SCORED, style=color)
            else:
                t.append(MARK_MISSED, style=theme.fade(color, 0.6))
            if i < slots - 1:
                t.append(" ")
        score = team.shootout_score
        if score is None:
            score = sum(k.scored for k in kicks)
        t.append(f"   {score:>2}", style=f"bold {theme.AMBER}")
        return t

    @staticmethod
    def _latest_line(latest: _Latest) -> Text:
        color = latest.team.color_hex if latest.team else theme.AMBER
        t = Text(justify="center")
        t.append(f"{EVENT_GLYPH[EventType.SHOOTOUT]} ", style=f"bold {color}")
        t.append(latest.player or "—", style=theme.AMBER)
        if latest.scored:
            t.append(" · scored", style=color)
        else:
            t.append(" · missed", style=theme.TEXT_DIM)
        return t
