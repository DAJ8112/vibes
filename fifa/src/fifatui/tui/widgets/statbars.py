"""Per-stat comparison rows — home value | label | away value over a split bar.

One stat per row; the currently *pinned* metric (set from the console's ``pin``
command) gets an accent left-edge and an accent label. Mirrors the design's
side-panel stat block.
"""

from __future__ import annotations

from rich.console import Group
from rich.text import Text
from textual.widgets import Static

from ...api.models import Match
from ...art import theme

BAR = "█"
#: Textured fill for the away lane, always used so the away side reads as distinct
#: from the solid home lane (each keeps its real team colour).
HATCH = "▒"

#: (metric key, label, accessor) — the metrics shown, in order. Keys match the
#: console ``pin`` command's canonical names.
_STATS = [
    ("possession", "Possession", lambda s: s.possession),
    ("shots", "Shots", lambda s: s.shots),
    ("ontarget", "On target", lambda s: s.shots_on_target),
    ("corners", "Corners", lambda s: s.corners),
    ("fouls", "Fouls", lambda s: s.fouls),
]

#: Console pin key -> display label (for the panel header + `pin` feedback).
STAT_LABELS = {key: label for key, label, _ in _STATS}


def _value_text(key: str, raw) -> str:
    if raw is None:
        return "0" if key != "possession" else "0%"
    if key == "possession":
        return f"{round(raw)}%"
    return str(int(raw))


class StatBars(Static):
    def on_mount(self) -> None:
        self._match: Match | None = None
        self._pinned = "possession"

    def update_match(self, m: Match, pinned: str | None = None) -> None:
        self._match = m
        if pinned is not None:
            self._pinned = pinned
        self.update(self._build(m))

    def set_pinned(self, pinned: str) -> None:
        self._pinned = pinned
        if self._match is not None:
            self.update(self._build(self._match))

    def on_resize(self) -> None:
        # Bars are sized in characters from ``self.size.width``, which is 0 until
        # the panel is laid out. Rebuild once the true width is known so the bar
        # snaps to full width immediately instead of on the next data poll.
        if self._match is not None:
            self.update(self._build(self._match))

    def _bar_width(self) -> int:
        # Leave room for the value columns and the pinned edge glyph.
        return max(10, (self.size.width or 30) - 8)

    def _build(self, m: Match) -> Group | Text:
        hs, as_ = m.home.stats, m.away.stats
        has_stats = any(
            fn(hs) is not None or fn(as_) is not None for _, _, fn in _STATS
        )
        if not has_stats:
            return Text("No live stats yet.", style=theme.TEXT_DIM)

        hc, ac = m.home.color_hex, m.away.color_hex
        # The away lane is always hatched so it reads as distinct from the solid
        # home lane; both keep their real team colours.
        away_glyph = HATCH
        rows: list = []
        for key, label, fn in _STATS:
            rows.append(self._row(key, label, fn(hs), fn(as_), hc, ac))
            rows.append(self._bar(fn(hs), fn(as_), hc, ac, away_glyph))
        return Group(*rows)

    def _row(self, key: str, label: str, hv, av, hc: str, ac: str) -> Text:
        pinned = key == self._pinned
        hv_txt = _value_text(key, hv)
        av_txt = _value_text(key, av)
        width = self._bar_width()
        label_style = theme.ACCENT if pinned else theme.DIM

        t = Text()
        t.append("▎" if pinned else " ", style=theme.ACCENT if pinned else theme.UNLIT)
        t.append(f"{hv_txt:<4}", style=f"bold {hc}")
        gap = max(1, width - 8 - len(label))
        left = gap // 2
        t.append(" " * left)
        t.append(label, style=label_style)
        t.append(" " * (gap - left))
        t.append(f"{av_txt:>4}", style=f"bold {ac}")
        return t

    def _bar(self, hv, av, hc: str, ac: str, away_glyph: str = BAR) -> Text:
        # Reserve one cell for a gap so the split point is always visible, even
        # when the two lane colours are similar.
        width = max(4, self._bar_width() - 1)
        h = float(hv or 0)
        a = float(av or 0)
        total = h + a
        if total > 0:
            hw = round(width * h / total)
        else:
            hw = width // 2
        aw = width - hw
        t = Text()
        t.append(" ")
        t.append(BAR * hw, style=hc)
        t.append(" ", style=theme.BG)
        t.append(away_glyph * aw, style=ac)
        return t
