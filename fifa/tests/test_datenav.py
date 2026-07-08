"""Day-stepping navigation on the match list, driven through the live app."""

import copy
from datetime import datetime, timedelta

from fifatui.api.models import MatchState
from fifatui.tui.app import FifaApp
from fifatui.tui.screens.matchlist import MatchListScreen
from fifatui.tui.screens.watch import WatchScreen


class DateAwareSource:
    """A DataSource returning a different slate per requested date."""

    def __init__(self, default, by_date):
        self.default = list(default)          # date=None => "today"
        self.by_date = by_date                # {"YYYYMMDD": [Match, ...]}
        self.calls = []

    async def scoreboard(self, league="fifa.world", date=None):
        self.calls.append(date)
        if date is None:
            return list(self.default)
        return list(self.by_date.get(date, []))

    async def summary(self, league, match_id):
        return None


def _yesterday() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")


def _finished_clone(match, new_id):
    clone = copy.deepcopy(match)
    clone.id = new_id
    clone.state = MatchState.POST
    clone.status_detail = "FT"
    return clone


async def test_prev_day_fetches_previous_date(matches):
    past = _finished_clone(matches[0], "PAST-MATCH-1")
    src = DateAwareSource(default=matches, by_date={_yesterday(): [past]})
    app = FifaApp(source=src, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        assert app.date is None
        assert MatchListScreen._date_label(app.date) == "TODAY"

        await pilot.press("left_square_bracket")
        await pilot.pause(0.3)

        assert app.date == _yesterday()
        assert src.calls[-1] == _yesterday()
        ol = app.screen.query_one("#match-list")
        assert ol.get_option_index("PAST-MATCH-1") is not None


async def test_today_resets_to_default(matches):
    past = _finished_clone(matches[0], "PAST-MATCH-1")
    src = DateAwareSource(default=matches, by_date={_yesterday(): [past]})
    app = FifaApp(source=src, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        await pilot.press("left_square_bracket")
        await pilot.pause(0.3)
        assert app.date == _yesterday()

        await pilot.press("t")
        await pilot.pause(0.3)
        assert app.date is None
        assert src.calls[-1] is None


async def test_open_past_match_pushes_watch_screen(matches):
    past = _finished_clone(matches[0], "PAST-MATCH-1")
    src = DateAwareSource(default=matches, by_date={_yesterday(): [past]})
    app = FifaApp(source=src, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        await pilot.press("left_square_bracket")
        await pilot.pause(0.3)

        app.open_match("PAST-MATCH-1")
        await pilot.pause(0.3)
        assert isinstance(app.screen, WatchScreen)
        assert app.screen.match_id == "PAST-MATCH-1"
