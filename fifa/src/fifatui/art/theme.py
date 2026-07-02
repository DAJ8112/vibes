"""The "stadium" palette: one physical metaphor — an LED scoreboard at night.

Near-black warm background, amber LEDs for chrome, team colours for team content,
and a faint "unlit dot" tone so surfaces feel like a physical board. Every colour
in the TUI comes from here.
"""

from __future__ import annotations

import math

BG = "#0b0a07"           # the board itself, switched off
BG_PANEL = "#141109"     # chrome bars (title/status)
UNLIT = "#2a2314"        # LEDs that exist but aren't lit
AMBER = "#ffb52e"        # the primary LED
AMBER_DIM = "#8a6418"    # secondary LED: labels, hints
LIVE_RED = "#ff4b3e"     # the LIVE lamp
CARD_YELLOW = "#ffd23e"
CARD_RED = "#ff3b30"
WIN_GOLD = "#ffd700"
TEXT_DIM = "#6e6350"     # muted prose (venue, assists)


def _parse(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def fade(hex_color: str, t: float, to: str = BG) -> str:
    """Blend ``hex_color`` toward ``to`` by t in [0, 1] (1 = fully faded)."""
    t = min(1.0, max(0.0, t))
    r1, g1, b1 = _parse(hex_color)
    r2, g2, b2 = _parse(to)
    return "#{:02x}{:02x}{:02x}".format(
        round(r1 + (r2 - r1) * t),
        round(g1 + (g2 - g1) * t),
        round(b1 + (b2 - b1) * t),
    )


#: Breathing ramp for the LIVE lamp: a slow sine between bright and dimmed red.
LIVE_PULSE = [
    fade(LIVE_RED, 0.55 * (0.5 - 0.5 * math.cos(2 * math.pi * i / 8)))
    for i in range(8)
]

#: Custom variables exposed to styles.tcss (via the theme *and* as defaults, so
#: the stylesheet parses even before the stadium theme is activated).
THEME_VARIABLES = {
    "amber": AMBER,
    "amber-dim": AMBER_DIM,
    "unlit": UNLIT,
    "live": LIVE_RED,
}


def build_theme():
    """The Textual theme object (imported lazily to keep this module rich-only)."""
    from textual.theme import Theme

    return Theme(
        name="stadium",
        primary=AMBER,
        secondary=AMBER_DIM,
        accent=AMBER,
        foreground="#e8ddc0",
        background=BG,
        surface=BG,
        panel=BG_PANEL,
        warning=CARD_YELLOW,
        error=CARD_RED,
        success="#7dc95e",
        dark=True,
        variables=THEME_VARIABLES,
    )
