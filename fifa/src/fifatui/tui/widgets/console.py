"""Interactive match console: a REPL-style panel with an OUTPUT log + command input.

The right-hand two-thirds of the redesigned watch screen. Typing a command
(``menu``, ``stats``, ``lineups`` …) writes formatted output into a scrollback
log. Commands that need richer detail (lineups / commentary / full stats / venue)
pull it from the match ``summary`` via the host screen, which caches the fetch.
"""

from __future__ import annotations

from typing import Callable

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, RichLog, Static

from ...api.models import EventType, Match, MatchExtras, CommentaryLine
from ...art import globe, theme
from ...art.glyphs import EVENT_GLYPH
from ...venues import find_venue
from .statbars import STAT_LABELS

_PLACEHOLDER = "menu · where · stats · events · lineups · commentary · pin possession"

_GOAL_TYPES = {EventType.GOAL, EventType.OWN_GOAL, EventType.PENALTY_GOAL}

#: (name, help) rows for the `menu` command.
_CMDS = [
    ("menu", "show this command list"),
    ("where", "venue map — ASCII globe"),
    ("stats", "full match stat breakdown"),
    ("events", "full goal & card feed"),
    ("lineups", "starting XIs & formations"),
    ("commentary", "live text commentary — auto-updates; `commentary stop` to end"),
    ("pin <metric>", "pin a stat to the side panel"),
    ("refresh", "poll for fresh data now"),
    ("back", "return to the match list"),
    ("clear", "clear the console"),
    ("quit", "exit fifatui"),
]

#: `pin` argument aliases -> canonical StatBars metric key.
_PIN_ALIASES = {
    "possession": "possession", "poss": "possession",
    "shots": "shots",
    "ontarget": "ontarget", "on-target": "ontarget", "on": "ontarget", "target": "ontarget",
    "corners": "corners",
    "fouls": "fouls",
}
_PIN_METRICS = "possession, shots, ontarget, corners, fouls"


class ConsolePanel(Vertical):
    """Command console. Its *host* (the WatchScreen) supplies match data & actions."""

    def compose(self) -> ComposeResult:
        yield Static(id="output-header", classes="panel-header")
        yield RichLog(id="console-log", wrap=True, markup=False, auto_scroll=True)
        with Horizontal(id="console-prompt-row"):
            yield Static("fifatui ❯", id="console-sigil")
            yield Input(placeholder=_PLACEHOLDER, id="console-input")

    def on_mount(self) -> None:
        self._host: "ConsoleHost" | None = None
        self._comm_live = False
        self._comm_seen: set[tuple[str, str]] = set()
        self._comm_timer = None
        self.query_one("#output-header", Static).update(self._header())

    def on_unmount(self) -> None:
        # Leaving the watch screen ends any live commentary stream.
        if self._comm_timer is not None:
            self._comm_timer.stop()
            self._comm_timer = None

    def bind_host(self, host: "ConsoleHost") -> None:
        self._host = host

    def welcome(self, m: Match | None) -> None:
        log = self.query_one(RichLog)
        log.clear()
        title = Text()
        title.append("fifatui", style=f"bold {theme.ACCENT}")
        title.append(" v2  —  live match console", style=theme.DIM)
        log.write(title)
        if m is not None:
            log.write(self._score_line(m))
        log.write(Text("type `menu` for commands, or `where` for the venue map.", style=theme.DIM))
        self._spacer()

    def focus_input(self) -> None:
        self.query_one(Input).focus()

    # -- input plumbing --------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "console-input":
            return
        raw = event.value
        event.input.value = ""
        self.run_command(raw)

    def on_click(self) -> None:
        self.focus_input()

    # -- command dispatch ------------------------------------------------

    def run_command(self, raw: str) -> None:
        text = (raw or "").strip()
        if not text:
            return
        parts = text.split()
        cmd = parts[0].lower()
        arg = parts[1].lower() if len(parts) > 1 else ""

        # Any command other than `commentary` ends a running live stream, so its
        # lines don't interleave with the next command's output.
        if self._comm_live and cmd not in ("commentary", "comm"):
            self._stop_commentary_stream("paused")

        if cmd in ("clear", "cls"):
            self.query_one(RichLog).clear()
            return
        if cmd in ("where", "map"):
            self.query_one(RichLog).clear()
            self._echo(text)
            self._cmd_where()
            return

        self._echo(text)
        if cmd in ("menu", "help", "?"):
            self._emit(self._cmd_menu())
        elif cmd in ("stats", "stat"):
            self._with_extras(self._render_stats)
        elif cmd in ("events", "feed"):
            self._emit(self._cmd_events())
        elif cmd in ("lineups", "lineup", "xi"):
            self._with_extras(self._render_lineups)
        elif cmd in ("commentary", "comm"):
            self._cmd_commentary(arg)
        elif cmd == "pin":
            self._emit(self._cmd_pin(arg))
        elif cmd == "refresh":
            if self._host:
                self._host.do_refresh()
            self._emit([self._ok("refreshing…")])
        elif cmd in ("back", "list"):
            if self._host:
                self._host.go_back()
            return
        elif cmd in ("quit", "exit"):
            if self._host:
                self._host.do_quit()
            return
        else:
            self._emit([self._err(f"command not found: {cmd}  —  type `menu`")])
        self._spacer()

    # -- log write helpers -----------------------------------------------

    def _emit(self, renderables) -> None:
        log = self.query_one(RichLog)
        for r in renderables:
            log.write(r)

    def _spacer(self) -> None:
        self.query_one(RichLog).write(Text(""))

    def _echo(self, text: str) -> None:
        t = Text()
        t.append("fifatui ❯ ", style=theme.DIM)
        t.append(text, style=f"bold {theme.FG}")
        self.query_one(RichLog).write(t)

    def _head(self, text: str) -> Text:
        return Text(text, style=f"bold {theme.ACCENT}")

    def _ok(self, text: str) -> Text:
        t = Text()
        t.append("✓ ", style=theme.ACCENT)
        t.append(text, style=theme.FG)
        return t

    def _err(self, text: str) -> Text:
        t = Text()
        t.append("✗ ", style=theme.LIVE)
        t.append(text, style=theme.LIVE)
        return t

    def _score_line(self, m: Match) -> Text:
        t = Text()
        t.append(f"{m.home.abbr} ", style=f"bold {m.home.color_hex}")
        t.append(str(m.home.score), style=f"bold {m.home.color_hex}")
        t.append("  ·  ", style=theme.DIM)
        t.append(str(m.away.score), style=f"bold {m.away.color_hex}")
        t.append(f" {m.away.abbr}", style=f"bold {m.away.color_hex}")
        t.append(f"     {m.status_detail or m.display_clock}", style=theme.FG)
        if m.is_live:
            t.append("  LIVE", style=theme.LIVE)
        return t

    # -- extras-backed commands ------------------------------------------

    def _with_extras(self, render: Callable[[MatchExtras], list]) -> None:
        """Render now if the summary is cached; otherwise fetch, then render."""
        host = self._host
        if host is None:
            self._emit([self._err("no data source")])
            self._spacer()
            return
        cached = host.cached_extras()
        if cached is not None:
            self._emit(render(cached))
            self._spacer()
            return
        self._emit([Text("fetching match detail…", style=theme.DIM)])

        def done(extras: MatchExtras | None) -> None:
            if extras is None:
                self._emit([self._err("match detail unavailable")])
            else:
                self._emit(render(extras))
            self._spacer()

        host.request_extras(done)

    # -- individual command builders -------------------------------------

    def _cmd_menu(self) -> list:
        rows = [self._head("AVAILABLE COMMANDS")]
        for name, desc in _CMDS:
            t = Text("  ")
            t.append(f"{name:<15}", style=theme.ACCENT2)
            t.append(desc, style=theme.DIM)
            rows.append(t)
        return rows

    def _cmd_pin(self, arg: str) -> list:
        if not arg:
            return [self._err(f"pin: name a metric — {_PIN_METRICS}")]
        key = _PIN_ALIASES.get(arg)
        if key is None:
            return [self._err(f"pin: unknown metric `{arg}` — try {_PIN_METRICS}")]
        if self._host:
            self._host.pin_metric(key)
        return [self._ok(f"pinned {STAT_LABELS.get(key, key)} to the side panel ▚")]

    def _cmd_events(self) -> list:
        m = self._host.current_match() if self._host else None
        if m is None:
            return [self._err("no match loaded")]
        events = [e for e in m.events if e.type != EventType.SHOOTOUT]
        if not events:
            return [self._head("FULL EVENT FEED"), Text("No events yet.", style=theme.DIM)]
        rows = [self._head("FULL EVENT FEED")]
        for e in reversed(events):
            rows.append(self._event_row(m, e))
        return rows

    def _event_row(self, m: Match, e) -> Text:
        team = m.team(e.team_id)
        abbr = team.abbr if team else "?"
        tc = team.color_hex if team else theme.ACCENT
        glyph = EVENT_GLYPH.get(e.type, "·")
        gc = {EventType.YELLOW: theme.WARN, EventType.RED: theme.CARD_RED}.get(e.type, tc)
        kind = {
            EventType.GOAL: "goal", EventType.OWN_GOAL: "own goal",
            EventType.PENALTY_GOAL: "penalty", EventType.YELLOW: "yellow card",
            EventType.RED: "red card", EventType.SUB: "sub",
        }.get(e.type, "")
        t = Text(f"  {e.minute:>7} ", style=theme.DIM)
        t.append(f"{glyph} ", style=f"bold {gc}")
        t.append(f"{abbr:<4}", style=f"bold {tc}")
        t.append(e.scorer or e.text or "—", style=theme.FG)
        detail = kind
        if e.type in _GOAL_TYPES and e.assist:
            detail = f"{kind}, assist {e.assist}"
        if detail:
            t.append(f"  ({detail})", style=theme.DIM)
        return t

    def _render_stats(self, extras: MatchExtras) -> list:
        m = self._host.current_match() if self._host else None
        home = m.home.abbr if m else "HOME"
        away = m.away.abbr if m else "AWAY"
        hc = m.home.color_hex if m else theme.ACCENT
        ac = m.away.color_hex if m else theme.ACCENT2
        if not extras.stat_rows:
            return [self._head("MATCH STATS"), Text("No stats available yet.", style=theme.DIM)]
        header = Text("  ")
        header.append(f"{'STAT':<16}", style=theme.DIM)
        header.append(f"{home:<8}", style=f"bold {hc}")
        header.append(away, style=f"bold {ac}")
        rows = [self._head(f"MATCH STATS  ·  {home} vs {away}"), header]
        for label, hv, av in extras.stat_rows:
            t = Text("  ")
            t.append(f"{label:<16}", style=theme.FG)
            t.append(f"{hv:<8}", style=hc)
            t.append(av, style=ac)
            rows.append(t)
        return rows

    def _render_lineups(self, extras: MatchExtras) -> list:
        m = self._host.current_match() if self._host else None
        home = m.home.abbr if m else "HOME"
        away = m.away.abbr if m else "AWAY"
        hc = m.home.color_hex if m else theme.ACCENT
        ac = m.away.color_hex if m else theme.ACCENT2
        hl, al = extras.home_lineup, extras.away_lineup
        if not hl.starters and not al.starters:
            return [self._head("STARTING XI"), Text("Lineups not published yet.", style=theme.DIM)]
        col_w = 26
        head = Text("  ")
        head.append(f"{home} {hl.formation}".ljust(col_w), style=f"bold {hc}")
        head.append(f"{away} {al.formation}", style=f"bold {ac}")
        rows = [self._head("STARTING XI"), head]
        for i in range(max(len(hl.starters), len(al.starters))):
            t = Text("  ")
            self._append_player(t, hl.starters[i] if i < len(hl.starters) else None, hc, col_w)
            self._append_player(t, al.starters[i] if i < len(al.starters) else None, ac, 0)
            rows.append(t)
        return rows

    def _append_player(self, t: Text, player, color: str, pad_to: int) -> None:
        if player is None:
            if pad_to:
                t.append(" " * pad_to)
            return
        start = len(t.plain)
        t.append(f"{player.jersey:>2} ", style=theme.DIM)
        t.append(player.name, style=theme.FG)
        if pad_to:
            written = len(t.plain) - start
            if written < pad_to:
                t.append(" " * (pad_to - written))

    # -- live commentary stream ------------------------------------------

    _COMM_BACKLOG = 14  # how many past lines to print when the stream starts

    def _cmd_commentary(self, arg: str) -> None:
        if arg in ("stop", "off", "end"):
            if self._comm_live:
                self._stop_commentary_stream("stopped")
            else:
                self._emit([Text("commentary is not streaming.", style=theme.DIM)])
            return
        if self._comm_live:
            self._emit([Text("already streaming — `commentary stop` to end.", style=theme.DIM)])
            return
        self._start_commentary_stream()

    def _start_commentary_stream(self) -> None:
        host = self._host
        if host is None:
            self._emit([self._err("no data source")])
            return
        self._comm_seen = set()
        cached = host.cached_extras()
        if cached is not None:
            self._emit_commentary_backlog(cached)
            self._begin_comm_timer()
            return
        self._emit([Text("fetching commentary…", style=theme.DIM)])

        def done(extras: MatchExtras | None) -> None:
            if extras is None:
                self._emit([self._err("commentary unavailable")])
                self._spacer()
                return
            self._emit_commentary_backlog(extras)
            self._begin_comm_timer()

        host.request_extras(done)

    def _begin_comm_timer(self) -> None:
        self._comm_live = True
        self._emit([Text("● streaming live — any command or `commentary stop` to end",
                         style=theme.DIM)])
        interval = getattr(self.app, "refresh_interval", 15.0)
        self._comm_timer = self.set_interval(interval, self._comm_tick)

    def _emit_commentary_backlog(self, extras: MatchExtras) -> None:
        # Mark *all* current lines as seen (so ticks only ever add newer ones),
        # but only print the recent tail. Oldest→newest, so live lines append
        # naturally at the bottom of the scrollback.
        self._comm_seen = {self._comm_key(c) for c in extras.commentary}
        self._emit([self._head("LIVE COMMENTARY")])
        if not extras.commentary:
            self._emit([Text("No commentary yet — new lines stream in as they arrive.",
                             style=theme.DIM)])
            return
        for c in extras.commentary[-self._COMM_BACKLOG:]:
            self._emit([self._commentary_row(c)])

    def _comm_tick(self) -> None:
        if not self._comm_live or self._host is None:
            return
        self._host.request_extras(self._on_comm_extras)

    def _on_comm_extras(self, extras: MatchExtras | None) -> None:
        if not self._comm_live:
            return
        if extras is not None:
            for c in extras.commentary:
                key = self._comm_key(c)
                if key in self._comm_seen:
                    continue
                self._comm_seen.add(key)
                self._emit([self._commentary_row(c)])
        # Once the match is over there's no more commentary coming — stop.
        m = self._host.current_match() if self._host else None
        if m is not None and m.is_finished:
            self._stop_commentary_stream("fulltime")
            self._spacer()

    def _stop_commentary_stream(self, reason: str = "stopped") -> None:
        if self._comm_timer is not None:
            self._comm_timer.stop()
            self._comm_timer = None
        was_live = self._comm_live
        self._comm_live = False
        if was_live:
            note = {
                "paused": "— commentary paused",
                "stopped": "— commentary stopped",
                "fulltime": "— commentary ended · full time",
            }.get(reason, "— commentary stopped")
            self._emit([Text(note, style=theme.DIM)])

    @staticmethod
    def _comm_key(c: CommentaryLine) -> tuple[str, str]:
        return (c.minute, c.text)

    def _commentary_row(self, c: CommentaryLine) -> Text:
        goal = c.text.lower().startswith("goal")
        t = Text("  ")
        t.append(f"{(c.minute or '·'):>6}  ", style=f"bold {theme.ACCENT2}")
        t.append(c.text, style=f"bold {theme.WARN}" if goal else theme.FG)
        return t

    def _cmd_where(self) -> None:
        host = self._host
        extras = host.cached_extras() if host else None
        if extras is not None:
            self._emit(self._where_output(extras))
            self._spacer()
            return
        self._emit([Text("fetching venue…", style=theme.DIM)])

        def done(ex: MatchExtras | None) -> None:
            if ex is None:
                self._emit([self._err("venue detail unavailable")])
            else:
                self._emit(self._where_output(ex))
            self._spacer()

        if host is not None:
            host.request_extras(done)
        else:
            self._emit([self._err("no data source")])
            self._spacer()

    def _where_output(self, extras: MatchExtras) -> list:
        venue = find_venue(extras.venue_name, extras.venue_city)
        lat = venue.lat if venue else None
        lon = venue.lon if venue else None
        rows = [self._head("VENUE")]
        for line in globe.world_map(lat, lon):
            rows.append(self._globe_line(line))
        rows.append(Text(""))
        name = extras.venue_name or (venue.name if venue else "Unknown venue")
        where = Text()
        where.append("◉ ", style=theme.LIVE)
        where.append(name, style=f"bold {theme.FG}")
        rows.append(where)
        locale = " · ".join(p for p in (extras.venue_city, extras.venue_country) if p)
        if locale:
            rows.append(Text(f"  {locale}", style=theme.DIM))
        if venue is not None:
            rows.append(Text(
                f"  {venue.lat:.2f}°N, {abs(venue.lon):.2f}°W · capacity {venue.capacity:,}",
                style=theme.DIM,
            ))
            rows.append(Text(f"  {venue.roof}", style=theme.DIM))
        return rows

    def _globe_line(self, line: str) -> Text:
        t = Text()
        for ch in line:
            if ch == globe.MARK:
                t.append(ch, style=f"bold {theme.LIVE}")
            elif ch == globe.LAND:
                t.append(ch, style=theme.fade(theme.ACCENT, 0.45))
            else:
                t.append(ch, style=theme.UNLIT)
        return t

    def _header(self) -> Text:
        t = Text()
        t.append("▸ OUTPUT", style=f"bold {theme.ACCENT}")
        t.append("   type ", style=theme.DIM)
        t.append("menu", style=theme.ACCENT2)
        t.append(" for commands", style=theme.DIM)
        return t


class ConsoleHost:
    """The interface the ConsolePanel expects from its host screen (docs only)."""

    def current_match(self) -> Match | None: ...
    def cached_extras(self) -> MatchExtras | None: ...
    def request_extras(self, callback: Callable[[MatchExtras | None], None]) -> None: ...
    def pin_metric(self, key: str) -> None: ...
    def do_refresh(self) -> None: ...
    def go_back(self) -> None: ...
    def do_quit(self) -> None: ...
