"""Pick a team colour that stays readable on a dark terminal background.

ESPN gives each team a primary ``color`` and an ``alternateColor`` (hex). Some are very
dark (navy, black) and vanish on a dark theme, so we fall back to the alternate colour
when it's brighter, or lighten the primary until it clears a luminance floor.
"""

from __future__ import annotations

_DEFAULT = "#3b82f6"


def _parse(hex_str: str | None) -> tuple[int, int, int] | None:
    h = (hex_str or "").strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return None
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return None


def _luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _lighten(rgb: tuple[int, int, int], target: float) -> tuple[int, int, int]:
    r, g, b = rgb
    for _ in range(20):
        if _luminance((r, g, b)) >= target:
            break
        r = int(r + (255 - r) * 0.18)
        g = int(g + (255 - g) * 0.18)
        b = int(b + (255 - b) * 0.18)
    return r, g, b


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def vivid_hex(color: str | None, alt: str | None = None, floor: float = 70.0, target: float = 140.0) -> str:
    """Return a visible-on-dark hex colour for a team, lightening dark ones."""
    rgb = _parse(color)
    if rgb is None:
        return _DEFAULT
    if _luminance(rgb) >= floor:
        return _hex(rgb)
    alt_rgb = _parse(alt)
    if alt_rgb is not None and _luminance(alt_rgb) >= floor:
        return _hex(alt_rgb)
    return _hex(_lighten(rgb, target))
