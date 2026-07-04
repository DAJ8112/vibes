"""Split-bar lane distinguishability (hue collision)."""

from fifatui.tui.widgets.statbars import _hue_collision


def test_two_reds_collide():
    # CAN deep red vs a lightened red — same hue, must be flagged as colliding.
    assert _hue_collision("#d52b1e", "#e34234") is True


def test_distinct_hues_do_not_collide():
    # Rose vs sky — clearly different hues, keep both solid.
    assert _hue_collision("#f43f5e", "#38bdf8") is False


def test_dull_greys_collide():
    # Two near-greys have unstable hue; treat as colliding so they get texture.
    assert _hue_collision("#3a3d42", "#4a4d52") is True


def test_saturated_vs_grey_do_not_collide():
    # A vivid colour and a grey are already distinguishable.
    assert _hue_collision("#f43f5e", "#3a3d42") is False
