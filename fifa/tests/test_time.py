"""US Eastern kickoff conversion (Match.kickoff_et)."""

from dataclasses import replace

import pytest


@pytest.fixture
def a_match(matches):
    return matches[0]


def test_kickoff_et_summer_is_edt(a_match):
    # 20:00 UTC in July → EDT (UTC-4) → 16:00.
    m = replace(a_match, date="2026-07-09T20:00Z")
    assert m.kickoff_et() == "16:00"


def test_kickoff_et_winter_is_est(a_match):
    # 20:00 UTC in January → EST (UTC-5) → 15:00.
    m = replace(a_match, date="2026-01-15T20:00Z")
    assert m.kickoff_et() == "15:00"


def test_kickoff_et_with_seconds(a_match):
    m = replace(a_match, date="2026-07-09T20:00:00Z")
    assert m.kickoff_et() == "16:00"


def test_kickoff_et_missing_or_bad_date(a_match):
    assert replace(a_match, date="").kickoff_et() == ""
    assert replace(a_match, date="not-a-date").kickoff_et() == ""
