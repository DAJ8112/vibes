"""Shootout kick derivation and the ShootoutPanel tracker widget."""

from rich.console import Group

from fifatui.api import EventType, MatchEvent
from fifatui.tui.app import FifaApp
from fifatui.tui.widgets import EventFeed, ShootoutPanel
from fifatui.tui.widgets.shootout import kick_scored, latest_kick, shootout_kicks


def _shootout_match(matches):
    return next(m for m in matches if m.has_shootout)


def _kick(text, team_id="1", taker="Taker"):
    return MatchEvent(type=EventType.SHOOTOUT, minute="120'", clock_value=7200.0,
                      team_id=team_id, players=[taker], text=text)


def test_kick_derivation(matches):
    m = _shootout_match(matches)  # GER 3 - PAR 4 in the fixture
    home, away = shootout_kicks(m)
    assert len(home) == 3 and len(away) == 4
    # ESPN kick order survives the stable event sort (all kicks share 120').
    assert home[0].scorer == "Joshua Kimmich"
    assert away[0].scorer == "Maurício"
    assert all(kick_scored(k) for k in home + away)


def test_kick_scored_parsing():
    # The fixture has no missed kick; document the defensive contract instead.
    assert kick_scored(_kick("Penalty - Scored"))
    assert not kick_scored(_kick("Penalty - Missed"))
    assert not kick_scored(_kick("Penalty - Saved"))
    assert not kick_scored(_kick(""))


def test_latest_kick(matches):
    m = _shootout_match(matches)
    assert latest_kick(m).scorer == "José Canale"


def test_feed_omits_shootout_rows(matches):
    m = _shootout_match(matches)
    built = EventFeed()._build(m)
    rows = built.renderables if isinstance(built, Group) else [built]
    assert "Penalty" not in "\n".join(r.plain for r in rows)


async def test_panel_visible_for_shootout_match(fixture_source):
    m = next(x for x in fixture_source.matches if x.has_shootout)
    app = FifaApp(source=fixture_source, start_match=m.id, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        panel = app.screen.query_one(ShootoutPanel)
        assert str(panel.styles.display) == "block"


async def test_panel_hidden_without_shootout(fixture_source):
    live = next(m for m in fixture_source.matches if m.is_live)
    app = FifaApp(source=fixture_source, start_match=live.id, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        panel = app.screen.query_one(ShootoutPanel)
        assert str(panel.styles.display) == "none"
