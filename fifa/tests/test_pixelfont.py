from fifatui.art import pixelfont


def test_measure_counts_glyphs_and_gaps():
    # "21" = 3 + gap + 3
    assert pixelfont.measure("1") == 3
    assert pixelfont.measure("11") == 7
    assert pixelfont.measure("") == 0


def test_render_has_five_uniform_rows():
    rows = pixelfont.render("GOAL", on_style="bold red")
    assert len(rows) == pixelfont.ROWS
    widths = {len(r.plain) for r in rows}
    assert widths == {pixelfont.measure("GOAL")}


def test_off_style_fills_unlit_cells():
    rows = pixelfont.render("0", on_style="red", off_style="grey", off_char="~")
    joined = "".join(r.plain for r in rows)
    assert "~" in joined  # the hole in the middle of 0
    rows_no_off = pixelfont.render("0", on_style="red")
    joined_no_off = "".join(r.plain for r in rows_no_off)
    assert "~" not in joined_no_off


def test_reveal_order_is_deterministic_and_complete():
    a = pixelfont.reveal_order("8", seed=42)
    b = pixelfont.reveal_order("8", seed=42)
    assert a == b
    assert set(a) == set(pixelfont.pixels("8"))


def test_partial_reveal_lights_only_given_pixels():
    order = pixelfont.reveal_order("8", seed=1)
    half = set(order[: len(order) // 2])
    rows = pixelfont.render("8", on_style="red", lit=half)
    lit_count = sum(r.plain.count("█") for r in rows)
    assert lit_count == len(half)


def test_render_spans_concatenates_with_gap():
    rows = pixelfont.render_spans([("2", "red"), ("1", "blue")])
    expected = pixelfont.measure("2") + pixelfont.GAP + pixelfont.measure("1")
    assert all(len(r.plain) == expected for r in rows)


def test_unknown_glyph_falls_back_to_space():
    rows = pixelfont.render("~", on_style="red")
    assert all(set(r.plain) <= {" "} for r in rows)
