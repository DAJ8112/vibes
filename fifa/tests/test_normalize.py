"""ESPN JSON -> normalized models."""

from fifatui.api import EventType, MatchState


def test_match_count(matches):
    assert len(matches) == 3


def test_live_match_parsed(matches):
    live = [m for m in matches if m.is_live]
    assert len(live) == 1
    m = live[0]
    assert {m.home.abbr, m.away.abbr} == {"NED", "MAR"}
    assert m.home.score == 1 and m.away.score == 1
    assert m.status_detail  # non-empty live clock, e.g. "108'"


def test_possession_and_stats(matches):
    m = next(m for m in matches if m.is_live)
    assert m.home.stats.possession is not None
    assert abs((m.home.stats.possession + m.away.stats.possession) - 100) < 1.5
    assert m.home.stats.shots is not None
    assert m.home.stats.corners is not None


def test_goals_carry_scorers(matches):
    m = next(m for m in matches if m.is_live)
    goals = [e for e in m.events if e.type == EventType.GOAL]
    assert goals
    assert all(g.scorer for g in goals)


def test_cards_parsed(matches):
    m = next(m for m in matches if m.is_live)
    assert any(e.type == EventType.YELLOW for e in m.events)


def test_shootout_detected(matches):
    shootouts = [m for m in matches if m.has_shootout]
    assert len(shootouts) == 1
    m = shootouts[0]
    assert m.home.shootout_score is not None
    assert m.away.shootout_score is not None
    assert "penalt" in m.note.lower()


def test_flags_resolve(matches):
    m = next(m for m in matches if m.is_live)
    # Known nations must map to a real flag, not the ⚽ fallback.
    assert m.home.flag != "⚽"
    assert m.away.flag != "⚽"


def test_ordering_live_first(matches):
    states = [m.state for m in matches]
    first_post = next(i for i, s in enumerate(states) if s == MatchState.POST)
    assert states.index(MatchState.IN) < first_post


def test_events_sorted_by_clock(matches):
    m = next(m for m in matches if m.is_live)
    values = [e.clock_value for e in m.events]
    assert values == sorted(values)
