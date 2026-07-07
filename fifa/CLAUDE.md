# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`fifatui` — a live football score tracker for the terminal, built around ESPN's free soccer API. Two frontends share one data layer:

- `fifa` — a full-screen Textual TUI (match list → watch screen with scoreboard, pinned side panel, and an interactive REPL console).
- `fifa --line` — a single Textual-free status line for tmux / shell prompt / Claude Code statusline. Fetches once, prints, exits.

## Commands

```bash
pip install -e ".[dev]"                       # install with dev deps (pytest, pytest-asyncio)
pytest                                         # full suite, offline against tests/fixtures/
pytest tests/test_normalize.py                 # one file
pytest tests/test_console.py -k commentary     # one test by name
ruff check src tests                           # lint (ruff 0.15+; no config file, uses defaults)
```

Run the app offline (no network) for visual/dev work:

```bash
fifa --fixture tests/fixtures/scoreboard.json  # drive the TUI from a saved scoreboard
fifa --fixture tests/fixtures/scoreboard.json --summary-fixture tests/fixtures/summary.json  # + console detail commands
fifa --fixture tests/fixtures/scoreboard.json --demo goal   # preview an animation: goal|yellow|red|sub|kickoff|ht|ft|pens
fifa --line --fixture ...                       # NOTE: --line ignores --fixture and hits the network (see cli._run_line)
```

`pytest` needs no network — tests run against captured JSON in `tests/fixtures/` and drive the TUI headless via Textual's `run_test()` pilot.

## Architecture

The design goal is that **the UI never touches raw ESPN JSON**. Data flows through one normalization boundary, and everything downstream depends only on the normalized dataclasses.

```
ESPN JSON ──parse_scoreboard/parse_summary──▶ api/models.py dataclasses ──▶ line.py  (status line)
           (api/espn.py)                                                └──▶ tui/    (Textual app)
```

### Data layer (`api/`)
- **`models.py`** — the normalized dataclasses (`Match`, `Team`, `MatchEvent`, `MatchExtras`, `Lineup`, …) plus enums (`MatchState`, `EventType`). These are the *only* shapes the UI sees. Live-clock display logic (`Match.clock_display`, which interpolates seconds between per-minute polls) and event identity (`MatchEvent.key`, used to diff polls for goal/card detection) live here.
- **`espn.py`** — ESPN implementation. `parse_scoreboard` / `parse_summary` are **pure functions** (raw dict → models) so they're unit-testable without network; `ESPNSource` is the async httpx client wrapping them. `FixtureSource` serves pre-loaded matches for offline mode. One `scoreboard` request drives all always-on polling; the richer `summary` endpoint (lineups/commentary/full stats/venue) is fetched on demand and cached.
- **`source.py`** — the `DataSource` Protocol (`scoreboard`, `summary`). Adding a new provider (football-data.org, API-Football) means writing one class that returns normalized models — no UI changes. `ESPNSource`, `FixtureSource`, and the test `conftest.FixtureSource` all satisfy it.

### Status line (`line.py`)
Deliberately Textual-free and fast. `pick_match` chooses the single most relevant match (live > favorite > next upcoming > recent); `detect_goal_flash` uses a small JSON cache file (`~/.cache/fifatui/`) to flash `GOAL!` on the poll right after a score rises. A statusline must never crash, so `cli._run_line` swallows all exceptions and prints a neutral placeholder.

### TUI (`tui/`)
- **`app.py`** — `FifaApp` owns the poll loop (`refresh_data` on a `set_interval`) and stores `self.matches`. After each poll it calls `on_data_refresh()` on the current screen (duck-typed). Network errors keep the last data and flag the UI rather than crashing. Registers the `broadcast` theme and pushes `MatchListScreen`.
- **`screens/`** — `matchlist.py` (list, `↵` opens a match) and `watch.py` (the single-match view). `WatchScreen` is the **ConsoleHost**: it implements `current_match` / `cached_extras` / `request_extras` / `pin_metric` / `do_refresh` / `go_back` / `do_quit`, and the console widget calls back into it. It also does new-event detection (diffing `MatchEvent.key` sets across polls) and routes goals → celebration, cards/subs → banners, and PRE/IN/POST changes → kickoff/HT/FT banners.
- **`widgets/`** — `scoreboard.py`, `pixelscore.py` (chunky pixel-font score), `sidepanel.py` + `statbars.py` (pinnable comparison bars), `console.py` (the REPL — command dispatch table in `run_command`), `eventfeed.py`, `banner.py`, `goal_celebration.py`, `shootout.py`, `ticker.py`.
- **`styles.tcss`** — Textual CSS (packaged via `pyproject` `package-data`). It references theme variables (`$accent`, `$dim`, …) that `art/theme.py` exposes both through the theme and as `get_theme_variable_defaults`, so the sheet parses even before the theme activates.

### Art layer (`art/`)
Pure rendering, **Textual-free** — returns `rich.text.Text` / style strings, so it's unit-tested offline. `theme.py` (the `broadcast` palette; every color in the UI comes from here — `theme.py` only imports Textual lazily inside `build_theme()`), `pixelfont.py`, `pixelflags.py`, `particles.py` (goal fireworks), `globe.py` (ASCII venue map), `canvas.py`, `glyphs.py`.

Supporting pure modules: `colors.py` (lightens dark team colors to stay readable on the dark background), `flags.py` (FIFA trigramme → flag emoji), `venues.py` (stadium lat/long + facts for the `where` command).

## Conventions

- **New data fields:** add to the `api/models.py` dataclass, populate it in `parse_scoreboard`/`parse_summary`, then consume it in the UI — never read ESPN's raw keys outside `api/espn.py`.
- **Keep `art/` and `line.py` Textual-free** (import-time). That's what lets them be tested without a running app.
- **Pure parse functions stay pure** — `parse_scoreboard`/`parse_summary` take a dict and return models with no I/O, which is why the fixture-based tests work.
- TUI tests drive the real app: `async with FifaApp(source=fixture_source, ...).run_test(size=(w, h)) as pilot`, then `await app.refresh_data()` and assert on widget state.
