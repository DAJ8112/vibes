# ⚽ fifatui

A **live football score tracker for your terminal** — with visuals, not just `ARG 2 - 0 FRA`.

Built for the **FIFA World Cup 2026** (works for any ESPN soccer league). Two ways to use it:

- **`fifa`** — a full-screen TUI styled like an **LED stadium scoreboard**: pick a match
  and watch it live with a chunky pixel-font score tinted in team colours, pixel-art team
  flags, possession & stat bars, an event feed, a bottom ticker with the other live scores,
  and animations for the big moments — **pixel fireworks** when someone scores, plus
  kickoff / half-time / full-time / card / substitution banners.
- **`fifa --line`** — one compact status line for your **tmux bar, shell prompt, or
  Claude Code statusline**, so you can keep an eye on the score while you work.

```
🔴 NED 1-1 MAR 104'        # live
FT BRA 2-1 JPN             # finished
FT-Pens GER 1-1 PAR (3-4p) # decided on penalties
```

## Install

```bash
pip install -e .          # from this directory
# or: pipx install .
```

Requires Python ≥ 3.10 and a truecolor terminal. Dependencies:
[Textual](https://textual.textualize.io/) ≥ 1.0 (the custom theme API) and
[httpx](https://www.python-httpx.org/).

## Usage

```bash
fifa                      # open the TUI (today's World Cup matches)
fifa --team BRA           # focus a favourite team
fifa --match 760488       # jump straight into one match
fifa --league eng.1       # a different league (Premier League)
fifa --date 20260629      # a specific date (YYYYMMDD)
fifa --refresh 10         # poll every 10s (default 15)
fifa --demo goal          # preview an animation: goal|yellow|red|sub|kickoff|ht|ft
fifa --line               # print one status line and exit
```

For offline visual tinkering, `fifa --fixture tests/fixtures/scoreboard.json` runs the
full TUI against a saved scoreboard instead of the network (combine with `--demo …`).

**Keys in the TUI:** `↵` open match · `r` refresh · `esc`/`←` back · `q` quit.

## Statusline integration

**tmux** — add to `~/.tmux.conf`:

```tmux
set -g status-interval 15
set -g status-right '#(fifa --line)'
```

**Claude Code** — set the statusline command to `fifa --line` (via `/statusline` or in
`settings.json`).

**Shell prompt (zsh)** — call `fifa --line` in your prompt, or for Starship add a
[`custom` command](https://starship.rs/config/#custom-commands) running `fifa --line`.

The `--line` mode caches the last score, so the run right after a goal briefly shows
`⚽ GOAL!` before settling back to the score. Use `--no-emoji` for ASCII-only output.

## Data source

Scores come from ESPN's free, no-auth site API (`site.api.espn.com`). It's *unofficial*
and can change, so all data is normalized behind a small `DataSource` protocol
(`fifatui/api/source.py`) — swapping in a paid provider (football-data.org, API-Football)
later means writing one new source class, not touching the UI.

A single `scoreboard` request per poll provides everything: live clock, score, penalty
shootout, possession / shots / corners / fouls, and the goal & card feed with player names.

## Development

```bash
pip install -e ".[dev]"
pytest                    # runs offline against tests/fixtures/
```

Tests run against captured fixtures (`tests/fixtures/`) so they don't need the network.
The TUI tests drive the real app headless via Textual's `run_test()` pilot.

## Roadmap

v1 keeps the visuals focused: live info + the goal celebration. Natural next steps:
ASCII pitch with momentum, stat "tug-of-war" history, lineups & substitutions and live
commentary (ESPN's `summary` endpoint), group standings / bracket views, and more leagues.
