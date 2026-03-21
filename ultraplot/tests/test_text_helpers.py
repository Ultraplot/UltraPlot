#!/usr/bin/env python3
"""
Focused tests for curved text helper behavior.
"""

from __future__ import annotations

import numpy as np
import pytest

import ultraplot as uplt
from ultraplot.text import CurvedText


def _make_curve():
    x = np.linspace(0, 1, 50)
    y = np.sin(2 * np.pi * x) * 0.1 + 0.5
    return x, y


def test_curved_text_validates_inputs():
    fig, ax = uplt.subplots()
    x, y = _make_curve()

    with pytest.raises(ValueError, match="'axes' is required"):
        CurvedText(x, y, "text", None)
    with pytest.raises(ValueError, match="same length"):
        CurvedText(x, y[:-1], "text", ax)
    with pytest.raises(ValueError, match="at least two points"):
        CurvedText([0], [0], "text", ax)


def test_curved_text_curve_accessors_and_zorder():
    fig, ax = uplt.subplots()
    x, y = _make_curve()
    text = CurvedText(x, y, "abc", ax)

    curve_x, curve_y = text.get_curve()
    curve_x[0] = -1
    curve_y[0] = -1
    check_x, check_y = text.get_curve()
    assert check_x[0] != -1
    assert check_y[0] != -1

    text.set_curve(x[::-1], y[::-1])
    new_x, new_y = text.get_curve()
    assert np.array_equal(new_x, x[::-1])
    assert np.array_equal(new_y, y[::-1])

    text.set_zorder(10)
    assert all(artist.get_zorder() == 11 for _, artist in text._characters)

    with pytest.raises(ValueError, match="same length"):
        text.set_curve(x, y[:-1])
    with pytest.raises(ValueError, match="at least two points"):
        text.set_curve([0], [0])


def test_curved_text_update_positions_handles_noninvertible_transform(monkeypatch):
    fig, ax = uplt.subplots()
    x, y = _make_curve()
    text = CurvedText(x, y, "abc", ax)

    class BadTransform:
        def inverted(self):
            raise RuntimeError("no inverse")

    monkeypatch.setattr(text, "get_transform", lambda: BadTransform())
    renderer = fig.canvas.get_renderer()
    text.update_positions(renderer)

    assert [artist.get_text() for _, artist in text._characters] == list("abc")


def test_curved_text_hides_zero_length_segments():
    fig, ax = uplt.subplots()
    text = CurvedText([0, 0], [0, 0], "abc", ax)
    fig.canvas.draw()

    assert all(artist.get_alpha() == 0.0 for _, artist in text._characters)


def test_curved_text_applies_label_properties():
    fig, ax = uplt.subplots()
    x, y = _make_curve()
    text = CurvedText(x, y, "abc", ax)

    text._apply_label_props({"color": "red", "fontweight": "bold"})

    for _, artist in text._characters:
        assert artist.get_color() == "red"
        assert artist.get_fontweight() == "bold"


def test_curved_text_supports_ellipsis_and_text_updates():
    fig, ax = uplt.subplots()
    x = np.linspace(0, 0.05, 20)
    y = np.linspace(0, 0.05, 20)
    text = CurvedText(x, y, "abcdefghij", ax, ellipsis=True)
    fig.canvas.draw()

    visible = [artist for _, artist in text._characters if artist.get_alpha()]
    assert visible
    assert [artist.get_text() for artist in visible][-1] == "."

    text.set_text("xy")
    fig.canvas.draw()
    assert text.get_text() == "xy"
    assert [artist.get_text() for _, artist in text._characters] == ["x", "y"]


def test_curved_text_reverses_curve_to_keep_text_upright():
    fig, ax = uplt.subplots()
    x = np.linspace(1, 0, 50)
    y = np.full_like(x, 0.5)
    text = CurvedText(x, y, "abc", ax, upright=True)
    fig.canvas.draw()

    rotations = [
        artist.get_rotation() for _, artist in text._characters if artist.get_alpha()
    ]
    assert rotations
    assert all(-90 <= rotation <= 90 for rotation in rotations)


def test_curved_text_draw_is_noop_for_empty_character_list():
    fig, ax = uplt.subplots()
    x, y = _make_curve()
    text = CurvedText(x, y, "abc", ax)
    text._characters = []

    renderer = fig.canvas.get_renderer()
    text.draw(renderer)
