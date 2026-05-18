"""
Unit tests for semantic legend style aliases and color detection.
"""
import matplotlib
matplotlib.use('Agg')          # Must be before any other matplotlib import for local test
import numpy as np
import pytest
from matplotlib import colors as mcolors

import ultraplot as uplt


# -----------------------------------------------------------------------------
# Color detection
# -----------------------------------------------------------------------------
def test_catlegend_rgba_tuple_is_color():
    """RGBA tuple like (1, 0, 0.5, 0.5) is treated as a single color."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(
            list("ABC"), color=(0.2, 0.4, 0.6, 0.8), add=False
        )
        colors = [h.get_color() for h in handles]
        assert all(c == colors[0] for c in colors), (
            f"All entries should share the same color, got {colors}"
        )
    finally:
        uplt.close(fig)


def test_catlegend_rgba_list_of_tuples():
    """List of RGBA tuples is treated as a per‑entry color list."""
    c1 = (1.0, 0.0, 0.0, 1.0)
    c2 = (0.0, 1.0, 0.0, 1.0)
    c3 = (0.0, 0.0, 1.0, 1.0)
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("ABC"), color=[c1, c2, c3], add=False)
        assert handles[0].get_color() == c1
        assert handles[1].get_color() == c2
        assert handles[2].get_color() == c3
    finally:
        uplt.close(fig)


def test_numlegend_facecolor_rgba_tuple_is_color():
    """RGBA facecolor for numlegend is not mistaken for a list."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.numlegend(
            [1, 2, 3], vmin=0, vmax=4,
            facecolor=(0.8, 0.2, 0.3, 0.6), add=False
        )
        ref = np.array(handles[0].get_facecolor())
        for h in handles:
            assert np.allclose(np.array(h.get_facecolor()), ref), (
                "All patches should have identical facecolor"
            )
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# Line2D style aliases (catlegend)
# -----------------------------------------------------------------------------
def test_alias_c_color():
    """'c' is an alias for 'color'."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("AB"), c="red", add=False)
        for h in handles:
            assert h.get_color() == "red"
    finally:
        uplt.close(fig)


def test_alias_m_marker():
    """'m' is an alias for 'marker'."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("AB"), m="^", add=False)
        for h in handles:
            assert h.get_marker() == "^"
    finally:
        uplt.close(fig)


def test_alias_ms_markersize_list():
    """'ms' can be a list that cycles through entries."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("ABCD"), ms=[10, 20], add=False)
        assert handles[0].get_markersize() == 10
        assert handles[1].get_markersize() == 20
        assert handles[2].get_markersize() == 10  # wraps around
    finally:
        uplt.close(fig)


def test_alias_ls_linestyle():
    """'ls' is an alias for 'linestyle'."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("AB"), ls="--", add=False)
        for h in handles:
            assert h.get_linestyle() == "--"
    finally:
        uplt.close(fig)


def test_alias_lw_linewidth():
    """'lw' is an alias for 'linewidth'."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("AB"), lw=3.0, add=False)
        for h in handles:
            assert h.get_linewidth() == 3.0
    finally:
        uplt.close(fig)


def test_alias_mec_markeredgecolor():
    """'mec' is an alias for 'markeredgecolor'."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("AB"), mec="blue", add=False)
        for h in handles:
            assert h.get_markeredgecolor() == "blue"
    finally:
        uplt.close(fig)


def test_alias_mew_markeredgewidth():
    """'mew' is an alias for 'markeredgewidth'."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("AB"), mew=2.0, add=False)
        for h in handles:
            assert h.get_markeredgewidth() == 2.0
    finally:
        uplt.close(fig)


def test_alias_mfc_markerfacecolor():
    """'mfc' is an alias for 'markerfacecolor'."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("AB"), mfc="yellow", add=False)
        for h in handles:
            assert h.get_markerfacecolor() == "yellow"
    finally:
        uplt.close(fig)


def test_alias_mfcalt_markerfacecoloralt():
    """'mfcalt' is an alias for 'markerfacecoloralt'."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("AB"), mfcalt="orange", add=False)
        for h in handles:
            assert h.get_markerfacecoloralt() == "orange"
    finally:
        uplt.close(fig)


def test_alias_aa_antialiased():
    """'aa' is an alias for 'antialiased'."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("AB"), aa=False, add=False)
        for h in handles:
            assert h.get_antialiased() is False
    finally:
        uplt.close(fig)


def test_alias_fs_fillstyle():
    """'fs' is an alias for 'fillstyle'."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("AB"), fs="none", add=False)
        for h in handles:
            assert h.get_fillstyle() == "none"
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# Patch style aliases (numlegend)
# -----------------------------------------------------------------------------
def test_numlegend_alias_fc_facecolor():
    """'fc' is an alias for 'facecolor' in numlegend."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.numlegend(
            [1, 2, 3], vmin=0, vmax=4, fc="lightblue", add=False
        )
        for h in handles:
            assert h.get_facecolor()[:3] == mcolors.to_rgb("lightblue")
    finally:
        uplt.close(fig)


def test_numlegend_alias_ec_edgecolor():
    """'ec' is an alias for 'edgecolor' in numlegend."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.numlegend(
            [1, 2, 3], vmin=0, vmax=4, ec="black", add=False
        )
        for h in handles:
            assert h.get_edgecolor()[:3] == (0.0, 0.0, 0.0)
    finally:
        uplt.close(fig)


def test_numlegend_alias_ls_linestyle():
    """'ls' is an alias for 'linestyle' in numlegend."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.numlegend(
            [1, 2, 3], vmin=0, vmax=4, ls=":", add=False
        )
        for h in handles:
            assert h.get_linestyle() == ":"
    finally:
        uplt.close(fig)


def test_numlegend_alias_lw_linewidth():
    """'lw' is an alias for 'linewidth' in numlegend."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.numlegend(
            [1, 2, 3], vmin=0, vmax=4, lw=1.5, add=False
        )
        for h in handles:
            assert h.get_linewidth() == 1.5
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# Alias priority & dict styles
# -----------------------------------------------------------------------------
def test_alias_and_fullname_priority():
    """Full name should override its alias."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(
            list("AB"), markersize=15, ms=99, add=False
        )
        for h in handles:
            assert h.get_markersize() == 15
    finally:
        uplt.close(fig)


def test_alias_dict_style():
    """Aliases work with dictionary-based per‑label styles."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(
            list("ABC"),
            c={"A": "red", "B": "green", "C": "blue"},
            ms={"A": 10, "B": 20, "C": 30},
            add=False,
        )
        assert handles[0].get_color() == "red"
        assert handles[1].get_color() == "green"
        assert handles[2].get_color() == "blue"
        assert handles[0].get_markersize() == 10
        assert handles[1].get_markersize() == 20
        assert handles[2].get_markersize() == 30
    finally:
        uplt.close(fig)


# -----------------------------------------------------------------------------
# sizelegend alias support
# -----------------------------------------------------------------------------
def test_sizelegend_alias_c():
    """sizelegend accepts 'c' as color alias."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.sizelegend([1, 2, 3], c="purple", add=False)
        for h in handles:
            assert h.get_color() == "purple"
    finally:
        uplt.close(fig)


def test_sizelegend_alias_mec():
    """sizelegend accepts 'mec' for markeredgecolor."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.sizelegend([1, 2, 3], mec="green", add=False)
        for h in handles:
            assert h.get_markeredgecolor() == "green"
    finally:
        uplt.close(fig)

def test_catlegend_ms_length_three_is_not_color():
    """ms list of length 3 should be treated as per‑entry markersize, not a color."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("abc"), ms=[10, 20, 30], add=False)
        assert handles[0].get_markersize() == 10
        assert handles[1].get_markersize() == 20
        assert handles[2].get_markersize() == 30
    finally:
        uplt.close(fig)


def test_catlegend_lw_length_three():
    """Linewidth list of length 3 should work."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("abc"), lw=[1.5, 2.5, 3.5], line=True, add=False)
        assert handles[0].get_linewidth() == 1.5
        assert handles[1].get_linewidth() == 2.5
        assert handles[2].get_linewidth() == 3.5
    finally:
        uplt.close(fig)


def test_catlegend_alpha_length_three():
    """Alpha list of length 3 should be per‑entry, not mistaken for a color."""
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("abc"), alpha=[0.2, 0.5, 0.8], add=False)
        assert handles[0].get_alpha() == 0.2
        assert handles[1].get_alpha() == 0.5
        assert handles[2].get_alpha() == 0.8
    finally:
        uplt.close(fig)

def test_catlegend_color_as_list_of_rgba_tuples():
    """Color with list of RGBA tuples still works correctly."""
    c1 = (1.0, 0.0, 0.0, 1.0)
    c2 = (0.0, 1.0, 0.0, 1.0)
    c3 = (0.0, 0.0, 1.0, 1.0)
    fig, ax = uplt.subplots()
    try:
        ax.axis("off")
        handles, _ = ax.catlegend(list("abc"), color=[c1, c2, c3], add=False)
        assert handles[0].get_color() == c1
        assert handles[1].get_color() == c2
        assert handles[2].get_color() == c3
    finally:
        uplt.close(fig)
