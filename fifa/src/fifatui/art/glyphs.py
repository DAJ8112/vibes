"""Drawn glyphs that replace emoji in the TUI (single-width, LED-friendly).

Everything visual that used to be an emoji goes through here, so a terminal with
misbehaving ambiguous-width fonts is one table-swap away from ASCII.
"""

from __future__ import annotations

from ..api.models import EventType

EVENT_GLYPH = {
    EventType.GOAL: "◉",
    EventType.OWN_GOAL: "◉",
    EventType.PENALTY_GOAL: "◉",
    EventType.YELLOW: "▮",
    EventType.RED: "▮",
    EventType.SUB: "⇄",
    EventType.SHOOTOUT: "◎",
    EventType.OTHER: "·",
}

#: Drop-in replacement if the drawn glyphs misrender in a terminal font.
EVENT_GLYPH_ASCII = {
    EventType.GOAL: "o",
    EventType.OWN_GOAL: "o",
    EventType.PENALTY_GOAL: "o",
    EventType.YELLOW: "|",
    EventType.RED: "|",
    EventType.SUB: "<>",
    EventType.SHOOTOUT: "()",
    EventType.OTHER: ".",
}

BALL = "◉"
LIVE_DOT = "●"
WINNER_STAR = "★"
WARN = "▲"
