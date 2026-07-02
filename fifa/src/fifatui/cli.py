"""Command-line entry point.

``fifa``            -> full-screen TUI (match list)
``fifa --line``    -> one compact status line, then exit (tmux / prompt / statusline)
``fifa --match ID``-> open a specific match in the TUI
"""

from __future__ import annotations

import argparse
import asyncio

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fifa",
        description="Live football score tracker in your terminal, with visuals.",
    )
    p.add_argument("--line", action="store_true",
                   help="Print one compact status line and exit (for tmux/prompt/statusline).")
    p.add_argument("--league", default="fifa.world",
                   help="ESPN league slug (default: fifa.world = FIFA World Cup).")
    p.add_argument("--team", default=None,
                   help="Favorite team (abbreviation or name) to focus on.")
    p.add_argument("--match", default=None,
                   help="Open a specific match id directly in the TUI.")
    p.add_argument("--date", default=None,
                   help="View a specific date YYYYMMDD instead of today.")
    p.add_argument("--refresh", type=float, default=15.0,
                   help="Polling interval in seconds (default: 15).")
    p.add_argument("--no-emoji", action="store_true",
                   help="ASCII-only output for --line.")
    p.add_argument("--demo-goal", action="store_true",
                   help="Fire a demo goal celebration shortly after launch (to preview it).")
    p.add_argument("--demo", default=None, metavar="EVENT",
                   choices=["goal", "yellow", "red", "sub", "kickoff", "ht", "ft"],
                   help="Preview an animation shortly after launch: "
                        "goal, yellow, red, sub, kickoff, ht, ft.")
    p.add_argument("--fixture", default=None, metavar="PATH",
                   help="Serve matches from a saved scoreboard JSON instead of the network "
                        "(offline/dev mode, e.g. tests/fixtures/scoreboard.json).")
    p.add_argument("--version", action="version", version=f"fifatui {__version__}")
    return p


def _run_line(args) -> int:
    from .api.espn import ESPNSource
    from .line import oneline

    async def fetch():
        src = ESPNSource()
        try:
            return await src.scoreboard(args.league, args.date)
        finally:
            await src.aclose()

    try:
        matches = asyncio.run(fetch())
    except Exception:
        # A statusline must never blow up; emit a neutral placeholder instead.
        print("⚽ —" if not args.no_emoji else "-")
        return 0
    print(oneline(matches, favorite=args.team, emoji=not args.no_emoji))
    return 0


def _run_tui(args) -> int:
    from .tui.app import FifaApp

    source = None
    if args.fixture:
        from .api.espn import FixtureSource, load_fixture

        source = FixtureSource(load_fixture(args.fixture, args.league))

    demo = args.demo or ("goal" if args.demo_goal else None)
    app = FifaApp(
        league=args.league,
        favorite=args.team,
        refresh=args.refresh,
        start_match=args.match,
        date=args.date,
        demo=demo,
        source=source,
    )
    app.run()
    return 0


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.line:
        return _run_line(args)
    return _run_tui(args)


if __name__ == "__main__":
    raise SystemExit(main())
