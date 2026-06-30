"""Map a team's 3-letter code to a flag emoji.

ESPN uses FIFA trigrammes for national teams (NED, MAR, BRA, ...). We translate those
to ISO 3166-1 alpha-2 codes and build the corresponding regional-indicator emoji.
England / Scotland / Wales have their own subdivision flag emoji and are special-cased.
Unknown codes fall back to a neutral football emoji so the UI never breaks.
"""

from __future__ import annotations

# Subdivision flags that aren't simple two-letter regional indicators.
_SPECIAL = {
    "ENG": "\U0001f3f4\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f",  # England
    "SCO": "\U0001f3f4\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f",  # Scotland
    "WAL": "\U0001f3f4\U000e0067\U000e0062\U000e0077\U000e006c\U000e0073\U000e007f",  # Wales
}

# FIFA trigramme -> ISO 3166-1 alpha-2. Covers WC2026 qualifiers and major nations.
_FIFA_TO_ISO2 = {
    "NED": "NL", "MAR": "MA", "BRA": "BR", "JPN": "JP", "GER": "DE", "PAR": "PY",
    "ARG": "AR", "FRA": "FR", "ESP": "ES", "POR": "PT", "USA": "US", "MEX": "MX",
    "CAN": "CA", "ITA": "IT", "BEL": "BE", "CRO": "HR", "URU": "UY", "COL": "CO",
    "SUI": "CH", "DEN": "DK", "POL": "PL", "SEN": "SN", "KOR": "KR", "AUS": "AU",
    "ECU": "EC", "GHA": "GH", "CMR": "CM", "SRB": "RS", "TUN": "TN", "CRC": "CR",
    "SAU": "SA", "IRN": "IR", "QAT": "QA", "NGA": "NG", "EGY": "EG", "ALG": "DZ",
    "CIV": "CI", "RSA": "ZA", "NZL": "NZ", "PER": "PE", "CHI": "CL", "VEN": "VE",
    "PAN": "PA", "HON": "HN", "JAM": "JM", "NOR": "NO", "SWE": "SE", "AUT": "AT",
    "TUR": "TR", "UKR": "UA", "CZE": "CZ", "GRE": "GR", "ROU": "RO", "HUN": "HU",
    "IRL": "IE", "SVK": "SK", "SVN": "SI", "BIH": "BA", "ALB": "AL", "MKD": "MK",
    "GEO": "GE", "ISL": "IS", "FIN": "FI", "BOL": "BO", "IRQ": "IQ", "UZB": "UZ",
    "JOR": "JO", "UAE": "AE", "OMA": "OM", "BHR": "BH", "CHN": "CN", "IND": "IN",
    "PRK": "KP", "THA": "TH", "VIE": "VN", "IDN": "ID", "MAS": "MY", "PHI": "PH",
    "COD": "CD", "MLI": "ML", "BFA": "BF", "GUI": "GN", "GAB": "GA", "CPV": "CV",
    "ANG": "AO", "ZAM": "ZM", "KEN": "KE", "UGA": "UG", "BEN": "BJ", "TOG": "TG",
    "LBY": "LY", "ZIM": "ZW", "MOZ": "MZ", "NAM": "NA", "GAM": "GM", "NIG": "NE",
    "SLE": "SL", "LBR": "LR", "CGO": "CG", "RWA": "RW", "ETH": "ET", "TAN": "TZ",
    "EQG": "GQ", "MTN": "MR", "CTA": "CF", "SDN": "SD", "BDI": "BI", "MWI": "MW",
    "BOT": "BW", "LES": "LS", "SWZ": "SZ", "COM": "KM", "GNB": "GW",
}


def _regional(iso2: str) -> str:
    """Two ISO letters -> regional indicator symbol emoji (e.g. NL -> 🇳🇱)."""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in iso2.upper())


def flag_for(abbr: str | None) -> str:
    """Return a flag emoji for a FIFA 3-letter team code, or a fallback."""
    if not abbr:
        return "\U0001f3f3"  # 🏳
    code = abbr.upper()
    if code in _SPECIAL:
        return _SPECIAL[code]
    iso2 = _FIFA_TO_ISO2.get(code)
    if iso2:
        return _regional(iso2)
    return "⚽"  # ⚽ fallback for unmapped codes
