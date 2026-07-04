"""Host-venue facts for the 2026 World Cup, used by the console ``where`` command.

ESPN's ``summary`` endpoint gives us a venue name + city, but no coordinates or
capacity. This small static table fills that in for the 16 host stadiums so the
console can draw a world-map marker and a facts block. Lookup is fuzzy (name or
city substring) so minor naming differences from ESPN still match.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Venue:
    name: str
    city: str
    country: str
    lat: float
    lon: float
    capacity: int
    roof: str  # "open", "retractable roof", "fixed roof"


#: The 16 host venues. ``lat``/``lon`` in decimal degrees (N/E positive).
WC2026_VENUES: tuple[Venue, ...] = (
    Venue("MetLife Stadium", "East Rutherford", "United States", 40.81, -74.07, 82500, "open"),
    Venue("AT&T Stadium", "Arlington", "United States", 32.75, -97.09, 80000, "retractable roof"),
    Venue("Mercedes-Benz Stadium", "Atlanta", "United States", 33.75, -84.40, 71000, "retractable roof"),
    Venue("NRG Stadium", "Houston", "United States", 29.68, -95.41, 72000, "retractable roof"),
    Venue("Arrowhead Stadium", "Kansas City", "United States", 39.05, -94.48, 76000, "open"),
    Venue("SoFi Stadium", "Inglewood", "United States", 33.95, -118.34, 70000, "fixed roof"),
    Venue("Levi's Stadium", "Santa Clara", "United States", 37.40, -121.97, 68500, "open"),
    Venue("Lumen Field", "Seattle", "United States", 47.60, -122.33, 69000, "open"),
    Venue("Gillette Stadium", "Foxborough", "United States", 42.09, -71.26, 65000, "open"),
    Venue("Hard Rock Stadium", "Miami Gardens", "United States", 25.96, -80.24, 65000, "open"),
    Venue("Lincoln Financial Field", "Philadelphia", "United States", 39.90, -75.17, 69000, "open"),
    Venue("BMO Field", "Toronto", "Canada", 43.63, -79.42, 45000, "open"),
    Venue("BC Place", "Vancouver", "Canada", 49.28, -123.11, 54000, "retractable roof"),
    Venue("Estadio Azteca", "Mexico City", "Mexico", 19.30, -99.15, 87000, "open"),
    Venue("Estadio BBVA", "Guadalupe", "Mexico", 25.67, -100.24, 53500, "open"),
    Venue("Estadio Akron", "Zapopan", "Mexico", 20.68, -103.46, 48000, "open"),
)


def _norm(s: str) -> str:
    return "".join(ch for ch in (s or "").lower() if ch.isalnum() or ch == " ").strip()


def find_venue(name: str = "", city: str = "") -> Venue | None:
    """Best-effort match of an ESPN venue name / city to a known host venue."""
    n, c = _norm(name), _norm(city)
    for v in WC2026_VENUES:
        vn, vc = _norm(v.name), _norm(v.city)
        if n and (n == vn or n in vn or vn in n):
            return v
        if c and (c == vc or c in vc or vc in c):
            return v
    return None
