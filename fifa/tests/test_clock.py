"""Match.clock_display: live M:SS with local per-second interpolation."""

import fifatui.tui.widgets.scoreboard as sb_mod
from fifatui.api.models import Match, MatchState, Team
from fifatui.tui.app import FifaApp
from fifatui.tui.widgets import ScoreBoard


def _match(state, status_detail, display_clock, clock_seconds):
    t = Team(id="1", name="A", abbr="A", score=0)
    return Match(
        id="x", name="", league="", state=state,
        status_detail=status_detail, status_name="", display_clock=display_clock,
        clock_seconds=clock_seconds, period=1, home=t, away=t,
    )


def test_live_shows_mmss_from_clock_seconds():
    m = _match(MatchState.IN, "72'", "72'", 4320.0)  # ESPN minute-granular: 72:00
    assert m.clock_display() == "72:00"


def test_extra_seconds_ticks_up():
    m = _match(MatchState.IN, "72'", "72'", 4320.0)
    assert m.clock_display(7) == "72:07"
    assert m.clock_display(45) == "72:45"
    assert m.clock_display(59) == "72:59"


def test_extra_seconds_clamped_to_current_minute():
    # Never rolls into the next minute — waits for the next poll to bump it.
    m = _match(MatchState.IN, "72'", "72'", 4320.0)
    assert m.clock_display(80) == "72:59"
    assert m.clock_display(3600) == "72:59"


def test_stoppage_time_kept_verbatim():
    m = _match(MatchState.IN, "90'+3'", "90'+3'", 5400.0)
    assert m.clock_display(30) == "90'+3'"


def test_halftime_kept_verbatim():
    m = _match(MatchState.IN, "HT", "45'", 2700.0)
    assert m.clock_display(30) == "HT"


def test_non_live_states_ignore_extra():
    assert _match(MatchState.POST, "FT", "90'+11'", 5400.0).clock_display(30) == "FT"
    assert _match(MatchState.PRE, "", "", 0.0).clock_display(30) == ""


async def test_clock_climbs_across_repeat_polls(fixture_source, monkeypatch):
    """A poll that repeats the same whole-minute value must not reset the tick
    back to :00 — the anchor is pinned to when the minute changed."""
    live = next(m for m in fixture_source.matches if m.is_live)
    app = FifaApp(source=fixture_source, start_match=live.id, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        board = app.screen.query_one(ScoreBoard)
        m = app.match_by_id(live.id)
        m.status_detail, m.clock_seconds = "26'", 1560.0  # running clock at 26:00

        now = {"t": 1000.0}
        monkeypatch.setattr(sb_mod.time, "monotonic", lambda: now["t"])

        board.update_match(m)                       # base 26:00, anchor 1000
        assert "26:00" in board._status(m).plain

        now["t"] = 1007.0                           # 7s later, poll repeats 26:00
        board.update_match(m)                       # anchor preserved
        assert "26:07" in board._status(m).plain    # climbs, not reset to 26:00

        now["t"] = 1020.0                           # next poll, ESPN bumps minute
        m.clock_seconds = 1620.0                    # 27:00
        board.update_match(m)                       # base changed -> anchor resets
        assert "27:00" in board._status(m).plain    # forward, no backward jump
