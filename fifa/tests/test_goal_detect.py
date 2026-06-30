"""Goal detection -> celebration, driven through the live app with a fixture source."""

from fifatui.api import EventType, MatchEvent
from fifatui.tui.app import FifaApp
from fifatui.tui.screens.watch import WatchScreen
from fifatui.tui.widgets import GoalCelebration


async def test_no_celebration_for_historical_goals(fixture_source):
    live = next(m for m in fixture_source.matches if m.is_live)
    app = FifaApp(source=fixture_source, start_match=live.id, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        assert isinstance(app.screen, WatchScreen)
        cel = app.screen.query_one(GoalCelebration)
        # The match already had goals on first load; none should be celebrated.
        assert str(cel.styles.display) == "none"


async def test_new_goal_triggers_celebration(fixture_source):
    live = next(m for m in fixture_source.matches if m.is_live)
    app = FifaApp(source=fixture_source, start_match=live.id, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        # A brand-new goal arrives in the next poll.
        live.home.score += 1
        live.events.append(
            MatchEvent(
                type=EventType.GOAL,
                minute="120'",
                clock_value=7200.0,
                team_id=live.home.id,
                players=["New Hero", "Provider"],
                text="Goal",
            )
        )
        await app.refresh_data()
        await pilot.pause(0.2)
        cel = app.screen.query_one(GoalCelebration)
        assert str(cel.styles.display) == "block"


async def test_match_list_to_watch_navigation(fixture_source):
    app = FifaApp(source=fixture_source, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        from fifatui.tui.screens.matchlist import MatchListScreen

        assert isinstance(app.screen, MatchListScreen)
        # Selecting the first (live) row opens the watch screen.
        await pilot.press("enter")
        await pilot.pause(0.2)
        assert isinstance(app.screen, WatchScreen)
