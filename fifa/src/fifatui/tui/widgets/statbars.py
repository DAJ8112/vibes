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

#: Minimum Manhattan RGB distance for two team colours to read as distinct in a
#: split bar. Below this (e.g. two near-identical golds), the away side is given
#: a guaranteed-contrasting lane colour instead.
_MIN_CONTRAST = 150
#: Fallback lane colours for the away side when it collides with the home colour.
_FALLBACK_LANES = ("#38bdf8", "#f97316", "#4ade80", "#f43f5e", "#c084fc")


def _distance(a: str, b: str) -> int:
    ar, ag, ab = theme._parse(a)
    br, bg, bb = theme._parse(b)
    return abs(ar - br) + abs(ag - bg) + abs(ab - bb)


def _lane_colors(hc: str, ac: str) -> tuple[str, str]:
    """(home, away) bar colours, substituting the away colour if it's too close
    to the home colour to tell the two halves apart."""
    if _distance(hc, ac) >= _MIN_CONTRAST:
        return hc, ac
    substitute = max(_FALLBACK_LANES, key=lambda c: _distance(hc, c))
    return hc, substitute


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

        hc, ac = _lane_colors(m.home.color_hex, m.away.color_hex)
        rows: list = []
        for key, label, fn in _STATS:
            rows.append(self._row(key, label, fn(hs), fn(as_), hc, ac))
            rows.append(self._bar(fn(hs), fn(as_), hc, ac))
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

    def _bar(self, hv, av, hc: str, ac: str) -> Text:
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
        t.append(BAR * aw, style=ac)
        return t
