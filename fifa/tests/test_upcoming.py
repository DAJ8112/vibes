"""Upcoming fixtures list (range fetch, day-grouped), driven through the live app."""

import copy

from fifatui.api.models import MatchState, eastern_today
from fifatui.tui.app import FifaApp
from fifatui.tui.screens.matchlist import MatchListScreen


def _upcoming(match, new_id, date):
    clone = copy.deepcopy(match)
    clone.id = new_id
    clone.state = MatchState.PRE
    clone.date = date
    return clone


class RangeAwareSource:
    """Returns a multi-day PRE slate for a range 'YYYYMMDD-YYYYMMDD', else one day."""

    def __init__(self, matches):
        self.upcoming = [
            _upcoming(matches[0], "UP-1", "2026-07-09T20:00Z"),  # THU 9 JUL
            _upcoming(matches[0], "UP-2", "2026-07-10T19:00Z"),  # FRI 10 JUL
            _upcoming(matches[0], "UP-3", "2026-07-11T21:00Z"),  # SAT 11 JUL
        ]
        self.calls = []

    async def scoreboard(self, league="fifa.world", date=None):
        self.calls.append(date)
        return list(self.upcoming) if date and "-" in date else []

    async def summary(self, league, match_id):
        return None


async def test_n_enters_upcoming_range_view(matches):
    src = RangeAwareSource(matches)
    app = FifaApp(source=src, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        assert app.upcoming is False

        await pilot.press("n")
        await pilot.pause(0.3)

        assert app.upcoming is True
        assert "-" in src.calls[-1]
        assert src.calls[-1].startswith(eastern_today())
        assert "UPCOMING" in app.screen.query_one("#list-title").render().plain

        ol = app.screen.query_one("#match-list")
        assert ol.get_option_index("UP-2") is not None
        # 3 day-group headers (disabled) + 3 fixtures.
        disabled = sum(1 for i in range(ol.option_count) if ol.get_option_at_index(i).disabled)
        assert disabled == 3
        assert ol.option_count == 6


async def test_escape_and_today_leave_upcoming(matches):
    src = RangeAwareSource(matches)
    app = FifaApp(source=src, refresh=5.0)
    async with app.run_test(size=(100, 34)) as pilot:
        await pilot.pause(0.3)
        await pilot.press("n")
        await pilot.pause(0.3)
        assert app.upcoming is True

        await pilot.press("escape")
        await pilot.pause(0.3)
        assert app.upcoming is False
        assert src.calls[-1] == eastern_today()  # single day, no range

        await pilot.press("n")
        await pilot.pause(0.3)
        await pilot.press("t")
        await pilot.pause(0.3)
        assert app.upcoming is False
        assert MatchListScreen._date_label(app.date) == "TODAY"
