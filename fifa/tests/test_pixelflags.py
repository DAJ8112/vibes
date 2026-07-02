from fifatui.art import pixelflags


def test_known_code_gives_two_flag_rows():
    rows = pixelflags.flag_rows("ARG")
    assert rows is not None
    assert len(rows) == 2
    assert all(len(r.plain) == pixelflags.WIDTH for r in rows)
    assert all(set(r.plain) == {"▀"} for r in rows)


def test_unknown_code_gives_no_flag():
    assert pixelflags.flag_rows("XXX") is None
    assert pixelflags.flag_rows(None) is None
    assert pixelflags.flag_rows("") is None


def test_team_mark_falls_back_to_badge_with_abbr():
    rows = pixelflags.team_mark("MCI", "#6caee0")
    assert len(rows) == 2
    assert "MCI" in rows[1].plain
    assert all(len(r.plain) == pixelflags.WIDTH for r in rows)


def test_team_chip_contains_abbr():
    chip = pixelflags.team_chip("ARG", "#74acdf")
    assert "ARG" in chip.plain
    assert len(chip.plain) == 5  # cap + 3 letters + cap


def test_every_flag_spec_is_well_formed():
    for code, spec in pixelflags.FLAGS.items():
        assert len(spec.pixels) == pixelflags.DEPTH, code
        for row in spec.pixels:
            assert len(row) == pixelflags.WIDTH, code
            for px in row:
                assert px.startswith("#") and len(px) == 7, (code, px)
