"""State-transition and non-goal event banners, driven through the live app."""

from fifatui.api import EventType, MatchEvent
from fifatui.api.models import MatchState
from fifatui.tui.app import FifaApp
from fifatui.tui.widgets import EventBanner


async def test_kickoff_banner_on_pre_to_in(fixture_source):
    # The fixture has no upcoming match; rewind the live one to kickoff-pending.
    pre = next(m for m in fixture_source.matches if m.is_live)
    pre.state = MatchState.PRE
    app = FifaApp(source=fixture_source, start_match=pre.id, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        banner = app.screen.query_one(EventBanner)
        assert str(banner.styles.display) == "none"

        pre.state = MatchState.IN
        pre.status_detail = "1'"
        await app.refresh_data()
        await pilot.pause(0.2)
        assert str(banner.styles.display) == "block"


async def test_fulltime_banner_on_in_to_post(fixture_source):
    live = next(m for m in fixture_source.matches if m.is_live)
    app = FifaApp(source=fixture_source, start_match=live.id, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        live.state = MatchState.POST
        live.status_detail = "FT"
        await app.refresh_data()
        await pilot.pause(0.2)
        assert str(app.screen.query_one(EventBanner).styles.display) == "block"


async def test_yellow_card_banner(fixture_source):
    live = next(m for m in fixture_source.matches if m.is_live)
    app = FifaApp(source=fixture_source, start_match=live.id, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        live.events.append(
            MatchEvent(
                type=EventType.YELLOW,
                minute="115'",
                clock_value=6900.0,
                team_id=live.home.id,
                players=["Hot Head"],
                text="Yellow card",
            )
        )
        await app.refresh_data()
        await pilot.pause(0.2)
        assert str(app.screen.query_one(EventBanner).styles.display) == "block"


async def test_historical_events_do_not_banner_on_first_load(fixture_source):
    live = next(m for m in fixture_source.matches if m.is_live)
    app = FifaApp(source=fixture_source, start_match=live.id, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        # The fixture match already contains a yellow card; it must not replay.
        assert str(app.screen.query_one(EventBanner).styles.display) == "none"
