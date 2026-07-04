"""The "broadcast" palette: a dark broadcast-console look for the match screen.

One metaphor — a live TV match console at night: near-black navy background, cyan
accents for chrome, team colours for team content, and a faint "unlit" tone so
surfaces feel like a physical board. Every colour in the TUI comes from here.
"""

from __future__ import annotations

import math

# ---- broadcast palette -------------------------------------------------------
BG = "#0a0e14"           # the console background
PANEL = "#0d131c"        # chrome bars / prompt row / pinned surfaces
BORDER = "#20304a"       # panel borders and rules
UNLIT = "#182534"        # LEDs / marks that exist but aren't lit
ACCENT = "#22d3ee"       # primary accent (cyan): headers, prompt, chrome
ACCENT2 = "#38bdf8"      # secondary accent (sky): command names, links
DIM = "#5a6c86"          # secondary text: labels, hints, timestamps
FG = "#e2e8f0"           # primary foreground text
LIVE = "#f43f5e"         # the LIVE lamp / error marks
WARN = "#fbbf24"         # yellow cards, cautions
CARD_RED = "#f43f5e"     # red cards (shares the live rose)
WIN_GOLD = "#ffd700"     # winner star
TEXT_DIM = "#3f4c63"     # muted prose (venue, assists) — darker than DIM

# ---- backwards-compatible aliases -------------------------------------------
# The board metaphor changed from an amber LED sign to a broadcast console; these
# keep older widgets readable without a churny rename. Prefer the names above.
AMBER = ACCENT
AMBER_DIM = DIM
LIVE_RED = LIVE
CARD_YELLOW = WARN
BG_PANEL = PANEL


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


#: Breathing ramp for the LIVE lamp: a slow sine between bright and dimmed rose.
LIVE_PULSE = [
    fade(LIVE, 0.55 * (0.5 - 0.5 * math.cos(2 * math.pi * i / 8)))
    for i in range(8)
]

#: Custom variables exposed to styles.tcss (via the theme *and* as defaults, so
#: the stylesheet parses even before the broadcast theme is activated).
THEME_VARIABLES = {
    "accent": ACCENT,
    "accent2": ACCENT2,
    "dim": DIM,
    "fg": FG,
    "border": BORDER,
    "unlit": UNLIT,
    "live": LIVE,
    # legacy names kept so any un-migrated rule still resolves.
    "amber": ACCENT,
    "amber-dim": DIM,
}


def build_theme():
    """The Textual theme object (imported lazily to keep this module rich-only)."""
    from textual.theme import Theme

    return Theme(
        name="broadcast",
        primary=ACCENT,
        secondary=DIM,
        accent=ACCENT2,
        foreground=FG,
        background=BG,
        surface=BG,
        panel=PANEL,
        warning=WARN,
        error=CARD_RED,
        success="#4ade80",
        dark=True,
        variables=THEME_VARIABLES,
    )
