"""
Unit tests for semantic legend style aliases, color parsing, and advanced markers.
These tests focus on functionality not covered by test_legend.py.
"""

import matplotlib

matplotlib.use("Agg")  # non-interactive backend

import numpy as np
import pytest
from matplotlib import colors as mcolors
from matplotlib import patches as mpatches
from matplotlib.markers import CapStyle, JoinStyle, MarkerStyle
import matplotlib.transforms as mtransforms

import ultraplot as uplt


def _make_fig():
    """Helper to create a figure and axis with axes turned off."""
    fig, ax = uplt.subplots()
    ax.axis("off")
    return fig, ax


# -----------------------------------------------------------------------------
# Non-color properties: scalar, list, dict (single catlegend call)
# -----------------------------------------------------------------------------
def test_non_color_properties():
    """Non-color properties (marker, markersize, linewidth, alpha, fillstyle,
    antialiased, markerfacecoloralt, markerfacecolor, markeredgecolor, size)
    are correctly parsed and applied when passed together."""
    fig, ax = _make_fig()
    try:
        # Combine many non-color properties in one catlegend call.
        h, _ = ax.catlegend(
            ["A", "B", "C"],
            marker="o",
            ms=[10, 20, 30],  # alias list – overrides above for each entry
            lw=[1.5, 2.5, 3.5],  # linewidth via alias list
            alpha=[0.2, 0.5, 0.8],  # length-3 list, not a color
            fs="full",  # fillstyle
            aa=False,  # antialiased scalar
            markerfacecolor="green",  # full name
            markeredgecolor="black",  # full name
            markerfacecoloralt="orange",
            line=True,  # enable lines
            add=False,
        )
        # markersize from ms list
        assert h[0].get_markersize() == 10
        assert h[1].get_markersize() == 20
        assert h[2].get_markersize() == 30
        # linewidth from lw list
        assert h[0].get_linewidth() == 1.5
        assert h[1].get_linewidth() == 2.5
        assert h[2].get_linewidth() == 3.5
        # alpha
        assert h[0].get_alpha() == 0.2
        assert h[1].get_alpha() == 0.5
        assert h[2].get_alpha() == 0.8
        # antialiased
        for hh in h:
            assert hh.get_antialiased() is False
        for hh in h:
            assert hh.get_markerfacecoloralt() == "orange"
            assert hh.get_fillstyle() == "full"
    finally:
        uplt.close(fig)


def test_size_alias_and_markersize_dict():
    """'size' (collection style) maps to markersize, and dict works."""
    fig, ax = _make_fig()
    try:
        # size as list and dict
        h, _ = ax.catlegend(
            ["X", "Y", "Z"],
            marker="s",
            ms={"X": 5, "Y": 12, "Z": 20},  # dict should override per label
            add=False,
        )
        assert h[0].get_markersize() == 5
        assert h[1].get_markersize() == 12
        assert h[2].get_markersize() == 20
    finally:
        uplt.close(fig)


def test_markerfacecolor_and_edgecolor():
    """Test full-name markerfacecolor and markeredgecolor with fillstyle='full'."""
    fig, ax = _make_fig()
    try:
        h, _ = ax.catlegend(
            ["A", "B"],
            marker="o",
            markerfacecolor="green",
            markeredgecolor="black",
            add=False,
        )
        for hh in h:
            assert np.allclose(
                mcolors.to_rgba(hh.get_markerfacecolor()), mcolors.to_rgba("green")
            )
            assert np.allclose(
                mcolors.to_rgba(hh.get_markeredgecolor()), mcolors.to_rgba("black")
            )
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# Alias resolution and conflicts
# -----------------------------------------------------------------------------
def test_alias_resolution_and_conflicts():
    """Aliases (c, m, ms, ls, lw, mec, mew, mfc, mfcalt, aa, fs) work,
    and full names override aliases when both are given."""
    fig, ax = _make_fig()
    try:
        # All aliases in one catlegend call
        h, _ = ax.catlegend(
            ["A", "B"],
            c="red",
            m="^",
            ms=15,
            ls="--",
            lw=3.0,
            mec="blue",
            mew=2.0,
            mfc="yellow",
            mfcalt="orange",
            aa=False,
            fs="full",
            add=False,
        )
        for hh in h:
            assert hh.get_color() == "red"
            assert hh.get_marker() == "^"
            assert hh.get_markersize() == 15
            assert hh.get_linestyle() == "--"
            assert hh.get_linewidth() == 3.0
            assert hh.get_markeredgecolor() == "blue"
            assert hh.get_markeredgewidth() == 2.0
            assert hh.get_markerfacecolor() == "yellow"
            assert hh.get_markerfacecoloralt() == "orange"
            assert hh.get_antialiased() is False
            assert hh.get_fillstyle() == "full"

        # Conflict: full name overrides alias (markersize vs ms)
        h, _ = ax.catlegend(["U", "V"], markersize=15, ms=99, add=False)
        assert h[0].get_markersize() == 15

        # Dict styles with aliases
        h, _ = ax.catlegend(
            ["red", "green", "blue"],
            c={"red": "red", "green": "green", "blue": "blue"},
            ms={"red": 10, "green": 20, "blue": 30},
            add=False,
        )
        assert h[0].get_color() == "red"
        assert h[1].get_color() == "green"
        assert h[2].get_color() == "blue"
        assert h[0].get_markersize() == 10
        assert h[1].get_markersize() == 20
        assert h[2].get_markersize() == 30

        # sizelegend aliases
        h, _ = ax.sizelegend([1, 2, 3], c="purple", mec="green", add=False)
        for hh in h:
            assert hh.get_color() == "purple"
            assert hh.get_markeredgecolor() == "green"
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# Color parsing: many formats (scalar, list, dict, tuple, etc.)
# -----------------------------------------------------------------------------
def test_color_parsing():
    """Color parameters accept many formats (names, hex, tuples, lists, dicts),
    and RGBA tuples are treated as single colors, not unpacked."""
    fig, ax = _make_fig()
    try:
        # Scalar colors: named, hex, grayscale, RGB tuple, RGBA tuple
        for color in ["red", "#ff0000", "0.5", (0.2, 0.4, 0.6), (0.2, 0.4, 0.6, 0.8)]:
            h, _ = ax.catlegend(["x", "y", "z"], color=color, add=False)
            first = h[0].get_color()
            assert all(hh.get_color() == first for hh in h), f"Failed for {color}"

        # List of colors: mixed formats
        c_list = ["red", "#00ff00", (0.0, 0.0, 1.0)]
        h, _ = ax.catlegend(["p", "q", "r"], color=c_list, add=False)
        assert h[0].get_color() == c_list[0]
        assert h[1].get_color() == c_list[1]
        assert h[2].get_color() == c_list[2]

        # List of RGBA tuples
        c_rgba = [(1.0, 0.0, 0.0, 1.0), (0.0, 1.0, 0.0, 1.0)]
        h, _ = ax.catlegend(["X", "Y"], color=c_rgba, add=False)
        assert h[0].get_color() == c_rgba[0]
        assert h[1].get_color() == c_rgba[1]

        # Dict mapping labels to colors
        color_dict = {"A": "red", "B": "green", "C": "blue"}
        h, _ = ax.catlegend(["A", "B", "C"], color=color_dict, add=False)
        assert h[0].get_color() == "red"
        assert h[1].get_color() == "green"
        assert h[2].get_color() == "blue"

        # markerfacecolor as single RGBA tuple
        h, _ = ax.catlegend(
            ["m1", "m2"], marker="o", markerfacecolor=(0.1, 0.2, 0.3, 1.0), add=False
        )
        ref = h[0].get_markerfacecolor()
        assert np.allclose(h[1].get_markerfacecolor(), ref)

        # markerfacecolor via alias (mfc) with list of colors
        h, _ = ax.catlegend(["g", "l"], marker="o", mfc=["gold", "lime"], add=False)
        assert np.allclose(
            mcolors.to_rgba(h[0].get_markerfacecolor()), mcolors.to_rgba("gold")
        )
        assert np.allclose(
            mcolors.to_rgba(h[1].get_markerfacecolor()), mcolors.to_rgba("lime")
        )

        # numlegend facecolor as RGBA tuple
        h, _ = ax.numlegend(
            [1, 2, 3], vmin=0, vmax=4, facecolor=(0.8, 0.2, 0.3, 0.6), add=False
        )
        ref_patch = np.array(h[0].get_facecolor())
        assert all(np.allclose(np.array(hh.get_facecolor()), ref_patch) for hh in h)
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# Advanced marker styles (capstyle, joinstyle, transform)
# -----------------------------------------------------------------------------
def test_marker_advanced():
    """marker_capstyle, marker_joinstyle, marker_transform create MarkerStyle."""
    fig, ax = _make_fig()
    try:
        # cap & join
        h, _ = ax.catlegend(
            ["A", "B"],
            marker_capstyle=[CapStyle.round, CapStyle.butt],
            marker_joinstyle=[JoinStyle.miter, JoinStyle.bevel],
            add=False,
        )
        h[0]._marker.get_capstyle() == CapStyle.round
        h[0]._marker.get_joinstyle() == JoinStyle.miter
        h[1]._marker.get_capstyle() == CapStyle.butt
        h[1]._marker.get_joinstyle() == JoinStyle.bevel

        # transform (rotation)
        h, _ = ax.catlegend(
            ["0°", "45°"],
            marker_transform=[
                mtransforms.Affine2D().rotate_deg(0),
                mtransforms.Affine2D().rotate_deg(45),
            ],
            add=False,
        )
        h[0]._marker.get_transform().get_matrix()[
            :2, :2
        ] == mtransforms.Affine2D().rotate_deg(0).get_matrix()[:2, :2]
        h[1]._marker.get_transform().get_matrix()[
            :2, :2
        ] == mtransforms.Affine2D().rotate_deg(45).get_matrix()[:2, :2]

        # combined with fillstyle and markerfacecoloralt
        h, _ = ax.catlegend(
            ["left", "right"],
            marker="o",
            markersize=25,
            markerfacecolor="tab:blue",
            markerfacecoloralt="lightsteelblue",
            fillstyle=["left", "right"],
            marker_capstyle=CapStyle.round,
            marker_joinstyle="round",
            add=False,
        )
        assert len(h) == 2
        # Check each handle
        for hh, expected_fillstyle in zip(h, ["left", "right"]):
            # MarkerStyle creation
            m = hh._marker
            assert isinstance(m, MarkerStyle)
            assert m.get_capstyle() == CapStyle.round
            # 'round' string should be converted to JoinStyle.round by MarkerStyle
            assert m.get_joinstyle() == JoinStyle.round

            # Check Line2D properties
            assert hh.get_markersize() == 25
            assert np.allclose(
                mcolors.to_rgba(hh.get_markerfacecolor()), mcolors.to_rgba("tab:blue")
            )
            assert hh.get_markerfacecoloralt() == "lightsteelblue"
            assert hh.get_fillstyle() == expected_fillstyle
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# Validation of forbidden legend kwargs
# -----------------------------------------------------------------------------
def test_forbidden_legend_kwargs():
    """Passing 'label' or 'labels' to semantic helpers raises TypeError."""
    fig, ax = _make_fig()
    try:
        with pytest.raises(TypeError, match=r"Use title=\.\.\. for the legend title"):
            ax.catlegend(["A"], label="Legend", add=True)
        with pytest.raises(
            TypeError, match="does not accept the legend kwarg 'labels'"
        ):
            ax.catlegend(["A"], labels=["x"], add=True)
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# Patch aliases and styles (numlegend, geolegend)
# -----------------------------------------------------------------------------
def test_patch_aliases_and_styles():
    """numlegend and geolegend accept Patch aliases (fc, ec, ls, lw)."""
    fig, ax = _make_fig()
    try:
        # numlegend with aliases
        h, _ = ax.numlegend(
            [1, 2],
            vmin=0,
            vmax=2,
            fc=["red", "green"],
            ec="black",
            ls=":",
            lw=1.5,
            add=False,
        )
        assert np.allclose(h[0].get_facecolor()[:3], mcolors.to_rgb("red"))
        assert np.allclose(h[1].get_facecolor()[:3], mcolors.to_rgb("green"))
        assert h[0].get_edgecolor()[:3] == (0, 0, 0)
        assert h[0].get_linestyle() == ":"
        assert h[0].get_linewidth() == 1.5

        # geolegend shape existence
        handles, labels = ax.geolegend(
            [("Triangle", "triangle"), ("Hex", "hexagon")], add=False
        )
        assert labels == ["Triangle", "Hex"]
        assert all(isinstance(hh, mpatches.PathPatch) for hh in handles)
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# Linestyle auto-enables line
# -----------------------------------------------------------------------------
def test_linestyle_auto_enable_line():
    """Providing a non-default linestyle automatically enables line=True."""
    fig, ax = _make_fig()
    try:
        h, _ = ax.catlegend(["A", "B"], ls="--", add=False)
        for hh in h:
            assert hh.get_linestyle() == "--"
            # when line is enabled, marker becomes None
            assert hh.get_marker() == uplt.rc["legend.cat.marker"]
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# geolegend: per‑entry lists
# -----------------------------------------------------------------------------
def test_geolegend_per_entry_lists():
    """geolegend applies per-entry styles from lists (facecolor, edgecolor, linewidth, alpha, fill)."""
    fig, ax = _make_fig()
    try:
        handles, labels = ax.geolegend(
            ["box", "tri", "hex"],
            facecolor=["tab:red", "tab:green", "tab:blue"],
            edgecolor=["black", "gray", "white"],
            linewidth=[1.0, 2.0, 3.0],
            alpha=[0.5, 0.7, 1.0],
            fill=[True, False, True],
            add=False,
        )
        assert len(handles) == 3
        assert labels == ["box", "tri", "hex"]

        # Check per-entry properties
        expected_fc = ["tab:red", "tab:green", "tab:blue"]  # None for fill=False
        expected_ec = ["black", "gray", "white"]
        expected_lw = [1.0, 2.0, 3.0]
        expected_alpha = [0.5, 0.7, 1.0]
        expected_fill = [True, False, True]

        for i, h in enumerate(handles):
            assert isinstance(h, mpatches.PathPatch)
            if expected_fill[i]:
                assert np.allclose(
                    h.get_facecolor(),
                    mcolors.to_rgba(expected_fc[i], expected_alpha[i]),
                )
            else:
                # for fill=False, facecolor is preserved, and set alpha=0
                assert np.allclose(
                    mcolors.to_rgba(h.get_facecolor()[:3], 0),
                    mcolors.to_rgba(expected_fc[i], 0),
                )
            assert np.allclose(
                h.get_edgecolor(), mcolors.to_rgba(expected_ec[i], expected_alpha[i])
            )
            assert h.get_linewidth() == pytest.approx(expected_lw[i])
            assert h.get_alpha() == expected_alpha[i]
            assert h.get_fill() == expected_fill[i]
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# geolegend: per‑entry dicts
# -----------------------------------------------------------------------------
def test_geolegend_per_entry_dicts():
    """geolegend applies per-entry styles from dicts."""
    fig, ax = _make_fig()
    try:
        handles, labels = ax.geolegend(
            ["box", "tri", "hex"],
            facecolor={"box": "red", "tri": "green", "hex": "blue"},
            edgecolor={"box": "black", "tri": "gray", "hex": "white"},
            linewidth={"box": 1.0, "tri": 2.0, "hex": 3.0},
            alpha={"box": 0.5, "tri": 0.7, "hex": 1.0},
            fill={"box": True, "tri": False, "hex": True},
            add=False,
        )
        assert len(handles) == 3
        assert labels == ["box", "tri", "hex"]

        expected = {
            "box": ("red", "black", 1.0, 0.5, True),
            "tri": ("green", "gray", 2.0, 0.7, False),
            "hex": ("blue", "white", 3.0, 1.0, True),
        }
        for h, label in zip(handles, labels):
            fc, ec, lw, alpha, fill = expected[label]
            if fill:
                assert np.allclose(h.get_facecolor(), mcolors.to_rgba(fc, alpha))
            else:
                # for fill=False, facecolor is preserved, and set alpha=0
                assert np.allclose(
                    mcolors.to_rgba(h.get_facecolor()[:3], 0), mcolors.to_rgba(fc, 0)
                )
            assert np.allclose(h.get_edgecolor(), mcolors.to_rgba(ec, alpha))
            assert h.get_linewidth() == pytest.approx(lw)
            assert h.get_alpha() == alpha
            assert h.get_fill() == fill
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# geolegend: alias support
# -----------------------------------------------------------------------------
def test_geolegend_alias_support():
    """geolegend accepts aliases fc, ec, lw, ls, etc."""
    fig, ax = _make_fig()
    try:
        handles, _ = ax.geolegend(
            ["box", "tri"],
            fc=["red", "green"],  # alias for facecolor
            ec=["black", "blue"],  # alias for edgecolor
            lw=2.0,  # alias for linewidth
            ls="--",  # alias for linestyle
            add=False,
        )
        assert len(handles) == 2
        # First geometry
        h0 = handles[0]
        assert np.allclose(h0.get_facecolor(), mcolors.to_rgba("red"))
        assert np.allclose(h0.get_edgecolor(), mcolors.to_rgba("black"))
        assert h0.get_linewidth() == 2.0
        assert h0.get_linestyle() == "--"
        # Second geometry
        h1 = handles[1]
        assert np.allclose(h1.get_facecolor(), mcolors.to_rgba("green"))
        assert np.allclose(h1.get_edgecolor(), mcolors.to_rgba("blue"))
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# geolegend: explicit parameter overrides alias (no conflict error)
# -----------------------------------------------------------------------------
def test_geolegend_explicit_overrides_alias():
    """Explicit facecolor parameter overrides alias fc."""
    fig, ax = _make_fig()
    try:
        # facecolor='red' (explicit) vs fc='blue' (alias) → explicit wins
        handles, _ = ax.geolegend(
            ["box"],
            facecolor="red",
            fc="blue",
            add=False,
        )
        h = handles[0]
        assert np.allclose(h.get_facecolor(), mcolors.to_rgba("red"))
        # edgecolor explicit vs ec
        handles, _ = ax.geolegend(
            ["box"],
            edgecolor="green",
            ec="black",
            add=False,
        )
        h = handles[0]
        assert np.allclose(h.get_edgecolor(), mcolors.to_rgba("green"))
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# geolegend: per-entry scalar applied to all
# -----------------------------------------------------------------------------
def test_geolegend_scalar_applied_to_all():
    """Scalar styles are applied to all geometry entries."""
    fig, ax = _make_fig()
    try:
        handles, _ = ax.geolegend(
            ["box", "tri", "hex"],
            facecolor="cyan",
            edgecolor="black",
            linewidth=2.5,
            alpha=0.6,
            fill=True,
            add=False,
        )
        for h in handles:
            assert np.allclose(h.get_facecolor(), mcolors.to_rgba("cyan", 0.6))
            assert np.allclose(h.get_edgecolor(), mcolors.to_rgba("black", 0.6))
            assert h.get_linewidth() == pytest.approx(2.5)
            assert h.get_alpha() == 0.6
            assert h.get_fill() == True
    finally:
        uplt.close(fig)
