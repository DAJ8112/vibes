"""Match list: today's matches as rows on the stadium board. Enter opens one."""

from __future__ import annotations

import time
from datetime import datetime

from rich.console import Group
from rich.text import Text
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, OptionList, Static
from textual.widgets.option_list import Option

from ...api.models import Match, MatchState
from ...art import theme
from ...art.pixelflags import team_mark
from ..anim import FrameAnimator

_WHEN_W = 8    # left column: pulse dot + clock / kickoff / FT
_NAME_W = 20
_SCORE_W = 16
_MID_W = _NAME_W + _SCORE_W + _NAME_W

_GROUP_LABEL = {
    MatchState.IN: "LIVE",
    MatchState.PRE: "UPCOMING",
    MatchState.POST: "FULL TIME",
}


class MatchListScreen(Screen):
    BINDINGS = [
        ("left_square_bracket", "prev_day", "Prev day"),
        ("right_square_bracket", "next_day", "Next day"),
        ("t", "today", "Today"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Static(id="list-title")
        yield Static(id="list-status")
        yield OptionList(id="match-list")
        yield Footer()

    def __init__(self) -> None:
        super().__init__()
        self._breath = FrameAnimator(self)

    def on_mount(self) -> None:
        self.query_one("#list-title", Static).update(self._title())
        self.query_one(OptionList).focus()
        self.on_data_refresh()

    def on_unmount(self) -> None:
        self._breath.stop()

    def _breathe(self, elapsed: float) -> bool:
        if not (self.is_current and self.app.app_focus):
            return True
        ol = self.query_one(OptionList)
        phase = int(elapsed * 2)
        for m in self.app.matches:
            if m.is_live:
                try:
                    ol.replace_option_prompt(m.id, self._row(m, phase))
                except Exception:
                    pass
        return True

    def _title(self) -> Text:
        league = self.app.league
        name = "FIFA World Cup 2026" if league == "fifa.world" else league
        t = Text()
        t.append("◉ ", style=theme.AMBER)
        t.append(f"{name.upper()} — ", style=f"bold {theme.AMBER}")
        t.append(self._date_label(self.app.date), style=f"bold {theme.AMBER}")
        return t

    @staticmethod
    def _date_label(date: str | None) -> str:
        if not date:
            return "TODAY"
        try:
            d = datetime.strptime(date, "%Y%m%d")
        except ValueError:
            return date
        return f"{d:%a} · {d.day} {d:%b} {d.year}".upper()

    # Called by the app after every poll.
    def on_data_refresh(self) -> None:
        try:
            ol = self.query_one(OptionList)
        except Exception:
            return

        prev_id = None
        if ol.highlighted is not None:
            try:
                prev_id = ol.get_option_at_index(ol.highlighted).id
            except Exception:
                prev_id = None

        ol.clear_options()
        state = None
        for m in self.app.matches:
            if m.state != state:
                state = m.state
                header = Text()
                header.append("· · ", style=theme.UNLIT)
                header.append(_GROUP_LABEL.get(state, ""), style=f"bold {theme.AMBER_DIM}")
                header.append(" · ·", style=theme.UNLIT)
                ol.add_option(Option(Group(Text(""), header), disabled=True))
            ol.add_option(Option(self._row(m), id=m.id))
        if not self.app.matches:
            empty = "No matches today." if self.app.date is None else "No matches on this date."
            ol.add_option(Option(Text(empty, style=theme.TEXT_DIM), disabled=True))

        self._highlight(ol, prev_id)
        self.query_one("#list-title", Static).update(self._title())
        self._update_status()

        any_live = any(m.is_live for m in self.app.matches)
        if any_live and not self._breath.running:
            self._breath.start(2, self._breathe)
        elif not any_live:
            self._breath.stop()

    def _highlight(self, ol: OptionList, prev_id: str | None) -> None:
        if prev_id is not None:
            try:
                ol.highlighted = ol.get_option_index(prev_id)
                return
            except Exception:
                pass
        for i in range(ol.option_count):
            if not ol.get_option_at_index(i).disabled:
                ol.highlighted = i
                return

    def _update_status(self) -> None:
        app = self.app
        if not app.connection_ok:
            state = Text("▲ RECONNECTING", style=f"bold {theme.CARD_YELLOW}")
        elif app.last_updated:
            ago = max(0, int(time.time() - app.last_updated))
            state = Text(f"● updated {ago}s ago", style=theme.AMBER_DIM)
        else:
            state = Text("loading…", style=theme.TEXT_DIM)
        n_live = sum(1 for m in app.matches if m.is_live)
        when = "today" if app.date is None else "that day"
        line = Text()
        line.append_text(state)
        line.append(f"   {n_live} live · {len(app.matches)} {when}", style=theme.TEXT_DIM)
        line.append("    times in ET  ·  ↵ open  ·  [ ] day  ·  t today  ·  r refresh  ·  q quit",
                    style=theme.TEXT_DIM)
        self.query_one("#list-status", Static).update(line)

    def _row(self, m: Match, phase: int = 0) -> Group:
        home_mark = team_mark(m.home.abbr, m.home.color_hex)
        away_mark = team_mark(m.away.abbr, m.away.color_hex)

        line1 = Text()
        line1.append_text(self._when(m, phase))
        line1.append(" ")
        line1.append_text(home_mark[0])
        line1.append(" ")
        line1.append_text(self._name_cell(m.home, align="right"))
        line1.append_text(self._score_cell(m))
        line1.append_text(self._name_cell(m.away, align="left"))
        line1.append(" ")
        line1.append_text(away_mark[0])

        line2 = Text()
        line2.append(" " * (_WHEN_W + 1))
        line2.append_text(home_mark[1])
        line2.append(" ")
        info = m.note or m.venue_city or m.venue or ""
        if len(info) > _MID_W:
            info = info[: _MID_W - 1] + "…"
        line2.append(info.center(_MID_W), style=theme.TEXT_DIM)
        line2.append(" ")
        line2.append_text(away_mark[1])

        return Group(line1, line2)

    @staticmethod
    def _when(m: Match, phase: int = 0) -> Text:
        t = Text()
        if m.is_live:
            dot_style = theme.LIVE_PULSE[phase % len(theme.LIVE_PULSE)]
            clock = (m.status_detail or "LIVE")[: _WHEN_W - 2]
            t.append("● ", style=f"bold {dot_style}")
            t.append(clock.ljust(_WHEN_W - 2), style=f"bold {theme.AMBER}")
        elif m.is_finished:
            t.append((m.status_detail or "FT")[:_WHEN_W].ljust(_WHEN_W), style=theme.TEXT_DIM)
        else:
            t.append(MatchListScreen._kickoff(m).ljust(_WHEN_W), style=theme.AMBER_DIM)
        return t

    @staticmethod
    def _name_cell(team, align: str) -> Text:
        star = 2 if team.winner else 0
        label = team.name
        if len(label) > _NAME_W - star:
            label = label[: _NAME_W - star - 1] + "…"
        pad = _NAME_W - len(label) - star
        style = f"bold {team.color_hex}" if team.winner else team.color_hex
        t = Text()
        if align == "right":
            t.append(" " * pad)
        t.append(label, style=style)
        if team.winner:
            t.append(" ★", style=f"bold {theme.WIN_GOLD}")
        if align == "left":
            t.append(" " * pad)
        return t

    @staticmethod
    def _score_cell(m: Match) -> Text:
        if m.is_upcoming:
            return Text("vs".center(_SCORE_W), style=theme.TEXT_DIM)
        sc = f"{m.home.score} - {m.away.score}"
        if m.has_shootout:
            sc += f" ({m.home.shootout_score or 0}-{m.away.shootout_score or 0}p)"
        if len(sc) > _SCORE_W:
            sc = sc[:_SCORE_W]
        return Text(sc.center(_SCORE_W), style=f"bold {theme.AMBER}")

    @staticmethod
    def _kickoff(m: Match) -> str:
        return m.kickoff_et() or "—"

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_id is not None:
            self.app.open_match(event.option_id)

    def action_refresh(self) -> None:
        self.app.run_worker(self.app.refresh_data())

    def action_prev_day(self) -> None:
        self.app.shift_date(-1)

    def action_next_day(self) -> None:
        self.app.shift_date(1)

    def action_today(self) -> None:
        self.app.goto_today()
