from fifatui.art import pixelflags


def _is_hex(px: str) -> bool:
    return px.startswith("#") and len(px) == 7


def test_known_code_gives_two_flag_rows_small():
    rows = pixelflags.flag_rows("ARG")
    assert rows is not None
    assert len(rows) == 2
    assert all(len(r.plain) == pixelflags.WIDTH for r in rows)
    assert all(set(r.plain) == {"▀"} for r in rows)


def test_large_render_is_eight_rows_twentyfour_wide():
    w, d = pixelflags.LARGE
    rows = pixelflags.flag_rows("ARG", w, d)
    assert rows is not None
    assert len(rows) == d // 2 == 8
    assert all(len(r.plain) == w == 24 for r in rows)
    assert all(set(r.plain) == {"▀"} for r in rows)


def test_unknown_code_gives_no_flag():
    assert pixelflags.flag_rows("XXX") is None
    assert pixelflags.flag_rows(None) is None
    assert pixelflags.flag_rows("") is None


def test_team_mark_large_uses_large_size():
    small = pixelflags.team_mark("FRA", "#3159c4")
    large = pixelflags.team_mark("FRA", "#3159c4", large=True)
    assert len(small) == 2 and len(large) == 8
    assert all(len(r.plain) == 24 for r in large)


def test_team_mark_falls_back_to_badge_with_abbr():
    rows = pixelflags.team_mark("MCI", "#6caee0")
    assert len(rows) == 2
    assert "MCI" in rows[1].plain
    assert all(len(r.plain) == pixelflags.WIDTH for r in rows)


def test_badge_large_scales():
    rows = pixelflags.team_mark("MCI", "#6caee0", large=True)
    assert len(rows) == 8
    assert "MCI" in rows[-1].plain
    assert all(len(r.plain) == 24 for r in rows)


def test_team_chip_contains_abbr():
    chip = pixelflags.team_chip("ARG", "#74acdf")
    assert "ARG" in chip.plain
    assert len(chip.plain) == 5  # cap + 3 letters + cap


def test_every_flag_renders_well_formed_at_both_sizes():
    for code in pixelflags.FLAGS:
        for w, d in (pixelflags.SMALL, pixelflags.LARGE):
            grid = pixelflags.flag_grid(code, w, d)
            assert grid is not None, code
            assert len(grid) == d, code
            for row in grid:
                assert len(row) == w, code
                for px in row:
                    assert _is_hex(px), (code, px)


def test_procedural_emblem_present_at_small_and_large():
    # Morocco's green star should tint the centre even in the compact mark.
    green = "#2f9e50"
    for w, d in (pixelflags.SMALL, pixelflags.LARGE):
        grid = pixelflags.flag_grid("MAR", w, d)
        flat = [px for row in grid for px in row]
        assert green in flat, (w, d)


def test_bitmap_crest_is_large_only():
    # Canada's leaf (bitmap) only paints on the large board; the compact mark is
    # the plain red/white/red field with no extra shapes.
    small = pixelflags.flag_grid("CAN", *pixelflags.SMALL)
    small_colors = {px for row in small for px in row}
    assert small_colors <= {"#e0392e", "#f2efe4"}
    # On the large board the leaf paints red pixels inside the white third
    # (cols 8-15 at 24 wide).
    large = pixelflags.flag_grid("CAN", *pixelflags.LARGE)
    leaf_in_band = any(
        large[r][c] == "#e0392e" for r in range(len(large)) for c in range(9, 15)
    )
    assert leaf_in_band


def test_mar_star_has_top_point():
    # The star's thin top tip must not be dropped by the rasterizer: green must
    # appear well above the flag's vertical centre.
    w, d = pixelflags.LARGE
    grid = pixelflags.flag_grid("MAR", w, d)
    top_half = [px for row in grid[: d // 4] for px in row]
    assert "#2f9e50" in top_half


def test_par_has_seal_at_large():
    grid = pixelflags.flag_grid("PAR", *pixelflags.LARGE)
    flat = [px for row in grid for px in row]
    assert "#2f9e50" in flat and "#f2c832" in flat  # wreath green + star gold


def test_small_marks_unchanged_for_emblem_flags():
    # Emblem work must not disturb the compact match-list marks.
    small = pixelflags.flag_grid("CHI", *pixelflags.SMALL)
    assert small[0][0] == small[1][0]  # canton intact (navy both rows)
    usa = pixelflags.flag_grid("USA", *pixelflags.SMALL)
    # stripes alternate red/white below the canton column
    assert usa[0][5] != usa[1][5]
