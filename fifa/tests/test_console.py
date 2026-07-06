"""The interactive match console: command dispatch, pin, clear, and input plumbing."""

from textual.widgets import Input, RichLog

from fifatui.art import globe
from fifatui.tui.app import FifaApp
from fifatui.tui.screens.watch import WatchScreen
from fifatui.tui.widgets import ConsolePanel
from fifatui.tui.widgets.statbars import StatBars
from fifatui.venues import find_venue


def _log_text(console: ConsolePanel) -> str:
    return "\n".join(strip.text for strip in console.query_one(RichLog).lines)


async def _open(fixture_source_full):
    live = next(m for m in fixture_source_full.matches if m.is_live)
    app = FifaApp(source=fixture_source_full, start_match=live.id, refresh=5.0)
    return app, live


async def test_menu_lists_commands(fixture_source_full):
    app, _ = await _open(fixture_source_full)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.3)
        console = app.screen.query_one(ConsolePanel)
        console.run_command("menu")
        await pilot.pause(0.1)
        text = _log_text(console)
        assert "AVAILABLE COMMANDS" in text
        assert "lineups" in text and "commentary" in text


async def test_unknown_command_errors(fixture_source_full):
    app, _ = await _open(fixture_source_full)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.3)
        console = app.screen.query_one(ConsolePanel)
        console.run_command("frobnicate")
        await pilot.pause(0.1)
        assert "command not found: frobnicate" in _log_text(console)


async def test_clear_empties_log(fixture_source_full):
    app, _ = await _open(fixture_source_full)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.3)
        console = app.screen.query_one(ConsolePanel)
        console.run_command("menu")
        await pilot.pause(0.1)
        assert _log_text(console).strip()
        console.run_command("clear")
        await pilot.pause(0.1)
        assert _log_text(console).strip() == ""


async def test_pin_alias_updates_statbars(fixture_source_full):
    app, _ = await _open(fixture_source_full)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.3)
        console = app.screen.query_one(ConsolePanel)
        console.run_command("pin on")  # alias for on-target
        await pilot.pause(0.1)
        assert app.screen._pinned == "ontarget"
        assert app.screen.query_one(StatBars)._pinned == "ontarget"
        assert "pinned On target" in _log_text(console)


async def test_pin_unknown_metric_errors(fixture_source_full):
    app, _ = await _open(fixture_source_full)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.3)
        console = app.screen.query_one(ConsolePanel)
        console.run_command("pin bananas")
        await pilot.pause(0.1)
        assert "unknown metric" in _log_text(console)
        assert app.screen._pinned == "possession"


async def test_input_submit_runs_command(fixture_source_full):
    app, _ = await _open(fixture_source_full)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.3)
        console = app.screen.query_one(ConsolePanel)
        inp = console.query_one(Input)
        assert app.focused is inp  # console is input-first
        inp.value = "menu"
        await pilot.press("enter")
        await pilot.pause(0.1)
        assert "AVAILABLE COMMANDS" in _log_text(console)
        assert inp.value == ""  # cleared after submit


async def test_stats_command_uses_summary(fixture_source_full):
    app, _ = await _open(fixture_source_full)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.3)
        console = app.screen.query_one(ConsolePanel)
        console.run_command("stats")
        await pilot.pause(0.3)  # allow the summary worker to resolve
        text = _log_text(console)
        assert "MATCH STATS" in text and "Possession" in text


async def test_commentary_streams_and_stops(fixture_source_full):
    app, _ = await _open(fixture_source_full)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.3)
        console = app.screen.query_one(ConsolePanel)
        console.run_command("commentary")
        await pilot.pause(0.3)  # allow the summary worker to resolve
        assert "LIVE COMMENTARY" in _log_text(console)
        assert console._comm_live is True
        assert console._comm_timer is not None
        # New lines can only ever be *newer* than the backlog already shown.
        assert console._comm_seen

        console.run_command("commentary stop")
        await pilot.pause(0.1)
        assert console._comm_live is False
        assert console._comm_timer is None
        assert "commentary stopped" in _log_text(console)


async def test_commentary_paused_by_other_command(fixture_source_full):
    app, _ = await _open(fixture_source_full)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.3)
        console = app.screen.query_one(ConsolePanel)
        console.run_command("commentary")
        await pilot.pause(0.3)
        assert console._comm_live is True

        console.run_command("menu")  # any other command ends the stream
        await pilot.pause(0.1)
        assert console._comm_live is False
        assert console._comm_timer is None
        text = _log_text(console)
        assert "commentary paused" in text
        assert "AVAILABLE COMMANDS" in text


async def test_back_command_pops_screen(fixture_source_full):
    app, _ = await _open(fixture_source_full)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.3)
        assert isinstance(app.screen, WatchScreen)
        app.screen.query_one(ConsolePanel).run_command("back")
        await pilot.pause(0.2)
        assert not isinstance(app.screen, WatchScreen)


def test_venue_lookup():
    v = find_venue("AT&T Stadium", "Arlington")
    assert v is not None and v.city == "Arlington"
    assert find_venue("Estadio BBVA", "") is not None


def test_globe_marker_on_map():
    rows = globe.world_map(25.67, -100.24)  # Monterrey, Mexico
    joined = "\n".join(rows)
    assert globe.MARK in joined
    # Marker sits in the northern-hemisphere Americas (left half, upper rows).
    r, c = globe.project(25.67, -100.24)
    assert c < globe.GLOBE_W // 2 and r < globe.GLOBE_H // 2
