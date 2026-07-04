import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

FIXTURES = pathlib.Path(__file__).parent / "fixtures"

from fifatui.api import parse_scoreboard, parse_summary  # noqa: E402


@pytest.fixture
def scoreboard_payload():
    return json.loads((FIXTURES / "scoreboard.json").read_text())


@pytest.fixture
def summary_payload():
    return json.loads((FIXTURES / "summary.json").read_text())


@pytest.fixture
def matches(scoreboard_payload):
    return parse_scoreboard(scoreboard_payload, "fifa.world")


@pytest.fixture
def extras(summary_payload):
    return parse_summary(summary_payload)


class FixtureSource:
    """A DataSource that serves pre-loaded matches (no network)."""

    def __init__(self, matches, extras=None):
        self.matches = list(matches)
        self.extras = extras

    async def scoreboard(self, league="fifa.world", date=None):
        return list(self.matches)

    async def summary(self, league, match_id):
        return self.extras


@pytest.fixture
def fixture_source(matches):
    return FixtureSource(matches)


@pytest.fixture
def fixture_source_full(matches, extras):
    return FixtureSource(matches, extras=extras)
