"""Day-stepping navigation on the match list, driven through the live app.

The app anchors "today" to US Eastern and always sends an explicit ``dates=`` param
(never ``None``), so expectations here are computed in US Eastern too.
"""

import copy
from datetime import datetime, timedelta

from fifatui.api.models import EASTERN, MatchState, eastern_today
from fifatui.tui.app import FifaApp
from fifatui.tui.screens.matchlist import MatchListScreen
from fifatui.tui.screens.watch import WatchScreen


class DateAwareSource:
    """A DataSource returning a different slate per requested date."""

    def __init__(self, by_date):
        self.by_date = by_date  # {"YYYYMMDD": [Match, ...]}
        self.calls = []

    async def scoreboard(self, league="fifa.world", date=None):
        self.calls.append(date)
        return list(self.by_date.get(date, []))

    async def summary(self, league, match_id):
        return None


def _eastern_yesterday() -> str:
    return (datetime.now(EASTERN) - timedelta(days=1)).strftime("%Y%m%d")


def _finished_clone(match, new_id):
    clone = copy.deepcopy(match)
    clone.id = new_id
    clone.state = MatchState.POST
    clone.status_detail = "FT"
    return clone


def _source(matches):
    past = _finished_clone(matches[0], "PAST-MATCH-1")
    return DateAwareSource({eastern_today(): list(matches), _eastern_yesterday(): [past]})


async def test_first_load_fetches_eastern_today(matches):
    src = _source(matches)
    app = FifaApp(source=src, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        assert app.date is None
        assert src.calls[0] == eastern_today()
        assert MatchListScreen._date_label(app.date) == "TODAY"


async def test_prev_day_fetches_previous_date(matches):
    src = _source(matches)
    app = FifaApp(source=src, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        await pilot.press("left_square_bracket")
        await pilot.pause(0.3)

        assert app.date == _eastern_yesterday()
        assert src.calls[-1] == _eastern_yesterday()
        ol = app.screen.query_one("#match-list")
        assert ol.get_option_index("PAST-MATCH-1") is not None


async def test_today_resets_to_default(matches):
    src = _source(matches)
    app = FifaApp(source=src, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        await pilot.press("left_square_bracket")
        await pilot.pause(0.3)
        assert app.date == _eastern_yesterday()

        await pilot.press("t")
        await pilot.pause(0.3)
        assert app.date is None
        assert src.calls[-1] == eastern_today()


async def test_open_past_match_pushes_watch_screen(matches):
    src = _source(matches)
    app = FifaApp(source=src, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        await pilot.press("left_square_bracket")
        await pilot.pause(0.3)

        app.open_match("PAST-MATCH-1")
        await pilot.pause(0.3)
        assert isinstance(app.screen, WatchScreen)
        assert app.screen.match_id == "PAST-MATCH-1"
