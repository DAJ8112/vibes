"""parse_summary: lineups, commentary, stats, and venue from the ESPN summary payload."""

from fifatui.api import parse_summary


def test_venue(summary_payload):
    e = parse_summary(summary_payload)
    assert e.venue_name == "Estadio BBVA"
    assert e.venue_city == "Guadalupe"
    assert e.venue_country == "Mexico"


def test_lineups(summary_payload):
    e = parse_summary(summary_payload)
    assert e.home_lineup.formation == "3-4-2-1"
    assert e.away_lineup.formation == "4-2-3-1"
    assert len(e.home_lineup.starters) == 11
    assert len(e.away_lineup.starters) == 11
    keeper = e.home_lineup.starters[0]
    assert keeper.name == "Bart Verbruggen"
    assert keeper.jersey == "1"
    assert keeper.position == "G"


def test_commentary(summary_payload):
    e = parse_summary(summary_payload)
    assert len(e.commentary) == 117
    # Stored oldest-first; the last line carries the latest clock.
    assert e.commentary[-1].minute == "107'"
    assert any("Goal!" in c.text for c in e.commentary)


def test_stat_rows(summary_payload):
    e = parse_summary(summary_payload)
    labels = [row[0] for row in e.stat_rows]
    assert "Possession" in labels
    assert "Shots" in labels
    poss = next(row for row in e.stat_rows if row[0] == "Possession")
    assert poss[1].endswith("%") and poss[2].endswith("%")


def test_empty_payload_is_safe():
    e = parse_summary({})
    assert e.venue_name == ""
    assert e.stat_rows == []
    assert e.commentary == []
    assert e.home_lineup.starters == []
