"""Statusline rendering and match-picking."""

import fifatui.line as line_mod
from fifatui.line import detect_goal_flash, pick_match, render_line


def test_render_live(matches):
    m = next(m for m in matches if m.is_live)
    out = render_line(m)
    assert m.home.abbr in out and m.away.abbr in out
    assert "🔴" in out and m.status_detail in out


def test_render_finished(matches):
    m = next(m for m in matches if m.is_finished and not m.has_shootout)
    out = render_line(m)
    assert "FT" in out
    assert f"{m.home.score}-{m.away.score}" in out


def test_render_shootout(matches):
    m = next(m for m in matches if m.has_shootout)
    out = render_line(m)
    assert "p)" in out  # penalties suffix, e.g. "(3-4p)"


def test_render_goal_flash(matches):
    m = next(m for m in matches if m.is_live)
    out = render_line(m, goal_flash=True)
    assert "GOAL" in out


def test_render_no_emoji(matches):
    m = next(m for m in matches if m.is_live)
    out = render_line(m, emoji=False)
    assert "🔴" not in out and "LIVE" in out


def test_render_none():
    assert render_line(None)  # must not crash


def test_pick_prefers_live(matches):
    picked = pick_match(matches)
    assert picked is not None and picked.is_live


def test_goal_flash_cache(tmp_path, monkeypatch, matches):
    monkeypatch.setattr(line_mod, "_CACHE", tmp_path / "scores.json")
    picked = pick_match(matches)
    # First invocation: no prior state -> no flash, but state is now persisted.
    assert detect_goal_flash(matches, picked) is False
    # A goal goes in for the picked (live) match -> next call flashes.
    picked.home.score += 1
    assert detect_goal_flash(matches, picked) is True
    # No further change -> no flash.
    assert detect_goal_flash(matches, picked) is False
