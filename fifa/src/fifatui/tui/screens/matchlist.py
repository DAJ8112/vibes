"""Match list: today's matches grouped live -> upcoming -> finished. Enter opens one."""

from __future__ import annotations

import time

from rich.text import Text
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Static

from ...api.models import Match


class MatchListScreen(Screen):
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Static(id="list-title")
        yield Static(id="list-status")
        yield DataTable(id="match-table", cursor_type="row", zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("When", "Home", "Score", "Away", "Info")
        self.query_one("#list-title", Static).update(self._title())
        self.on_data_refresh()

    def _title(self) -> str:
        league = self.app.league
        name = "FIFA World Cup 2026" if league == "fifa.world" else league
        return f"⚽  {name} — Live Scores"

    # Called by the app after every poll.
    def on_data_refresh(self) -> None:
        table = self.query_one(DataTable)
        if not table.columns:
            # A poll can land before this screen's on_mount has added columns;
            # on_mount will repopulate once they exist.
            return
        prev_key = None
        if table.row_count and table.is_valid_coordinate(table.cursor_coordinate):
            try:
                prev_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            except Exception:
                prev_key = None

        table.clear()
        for m in self.app.matches:
            table.add_row(*self._row(m), key=m.id)

        if prev_key is not None:
            try:
                table.move_cursor(row=table.get_row_index(prev_key))
            except Exception:
                pass
        self._update_status()

    def _update_status(self) -> None:
        app = self.app
        if not app.connection_ok:
            state = Text("⚠ reconnecting…", style="yellow")
        elif app.last_updated:
            ago = max(0, int(time.time() - app.last_updated))
            state = Text(f"● updated {ago}s ago", style="green")
        else:
            state = Text("loading…", style="dim")
        n_live = sum(1 for m in app.matches if m.is_live)
        line = Text()
        line.append_text(state)
        line.append(f"   {n_live} live · {len(app.matches)} today", style="dim")
        line.append("    ↵ open match  ·  r refresh  ·  q quit", style="dim")
        self.query_one("#list-status", Static).update(line)

    def _row(self, m: Match):
        if m.is_live:
            when = Text("● LIVE", style="bold red")
        elif m.is_finished:
            when = Text(m.status_detail or "FT", style="dim")
        else:
            when = Text(self._kickoff(m), style="cyan")

        home = Text(f"{m.home.flag} {m.home.name}", style="bold" if m.home.winner else "")
        away = Text(f"{m.away.name} {m.away.flag}", style="bold" if m.away.winner else "")

        if m.is_upcoming:
            score = Text("vs", style="dim")
        else:
            sc = f"{m.home.score} - {m.away.score}"
            if m.has_shootout:
                sc += f"  ({m.home.shootout_score or 0}-{m.away.shootout_score or 0}p)"
            score = Text(sc, style="bold")

        info = m.note or m.venue_city or m.venue
        return (when, home, score, away, Text(info, style="dim"))

    @staticmethod
    def _kickoff(m: Match) -> str:
        if "T" in m.date:
            return m.date.split("T", 1)[1].rstrip("Z")[:5]
        return "—"

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.app.open_match(event.row_key.value)

    def action_refresh(self) -> None:
        self.app.run_worker(self.app.refresh_data())
