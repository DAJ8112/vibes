"""Team colour readability."""

from fifatui.colors import _luminance, _parse, vivid_hex


def test_bright_color_kept():
    assert vivid_hex("fb5d00", "fb5d00") == "#fb5d00"


def test_dark_color_lightened():
    # Japan navy (#000555) is near-black; it must be brightened to stay visible.
    out = vivid_hex("000555", "000555")
    assert out != "#000555"
    assert _luminance(_parse(out)) >= 70


def test_alt_used_when_brighter():
    # Primary near-black, alternate is bright cyan -> prefer the alternate.
    out = vivid_hex("000000", "00CED1")
    assert out == "#00ced1"


def test_invalid_falls_back():
    assert vivid_hex(None) == "#3b82f6"
    assert vivid_hex("zzz") == "#3b82f6"
