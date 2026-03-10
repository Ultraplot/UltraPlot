import warnings

import numpy as np
import pytest

import ultraplot as uplt
from ultraplot import axes as paxes

pytest.importorskip("astropy.visualization.wcsaxes")
from astropy.wcs import WCS


def _make_test_wcs():
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [50.0, 50.0]
    wcs.wcs.cdelt = [-0.066667, 0.066667]
    wcs.wcs.crval = [0.0, -90.0]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    wcs.wcs.cunit = ["deg", "deg"]
    return wcs


def test_add_subplot_with_wcs_projection_returns_native_astro_axes():
    fig = uplt.figure()
    ax = fig.add_subplot(111, projection=_make_test_wcs())

    assert paxes.AstroAxes is not None
    assert isinstance(ax, paxes.AstroAxes)
    assert not (hasattr(ax, "has_external_axes") and ax.has_external_axes())
    assert ax.get_transform("icrs") is not None

    fig.canvas.draw()
    bbox = ax.get_tightbbox(fig.canvas.get_renderer())
    assert bbox.width > 0
    assert bbox.height > 0


def test_add_axes_with_wcs_projection_supports_basic_formatting():
    fig = uplt.figure()
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], projection=_make_test_wcs())

    ax.format(xlabel="RA", ylabel="Dec", title="Sky", xgrid=True, ygrid=True)

    assert isinstance(ax, paxes.AstroAxes)
    assert ax.get_xlabel() == "RA"
    assert ax.get_ylabel() == "Dec"
    assert ax.get_title() == "Sky"

    fig.canvas.draw()
    bbox = ax.get_tightbbox(fig.canvas.get_renderer())
    assert bbox.width > 0
    assert bbox.height > 0


def test_string_wcs_projection_uses_native_astro_axes():
    fig = uplt.figure()
    ax = fig.add_subplot(111, projection="wcs", wcs=_make_test_wcs())

    assert isinstance(ax, paxes.AstroAxes)


def test_same_family_astro_axes_can_share_without_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig, (ax1, ax2) = uplt.subplots(
            nrows=2,
            proj=[_make_test_wcs(), _make_test_wcs()],
            sharex=2,
        )

    messages = [str(item.message) for item in caught]
    assert not any("Skipping incompatible x-axis sharing" in msg for msg in messages)
    assert ax1.get_shared_x_axes().joined(ax1, ax2)


def test_different_astro_coordinate_families_do_not_share():
    galactic = _make_test_wcs()
    galactic.wcs.ctype = ["GLON-TAN", "GLAT-TAN"]

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig, (ax1, ax2) = uplt.subplots(
            nrows=2,
            proj=[_make_test_wcs(), galactic],
            sharex=2,
        )

    messages = [str(item.message) for item in caught]
    assert any("different Astro coordinate families" in msg for msg in messages)
    assert not ax1.get_shared_x_axes().joined(ax1, ax2)


def test_subplot_grid_arrow_dispatches_per_axes_transforms():
    fig, axs = uplt.subplots(
        ncols=2,
        proj=[_make_test_wcs(), _make_test_wcs()],
        share=0,
    )
    axs.imshow(np.zeros((16, 16)), origin="lower")

    arrows = axs.arrow(
        0.0,
        -89.95,
        0.0,
        0.02,
        head_width=0,
        head_length=0,
        width=0.01,
        transform=axs.get_transform("icrs"),
    )

    assert len(arrows) == 2
    fig.canvas.draw()


def test_astro_axes_share_ticklabels_without_hiding_outer_wcs_labels():
    fig, axs = uplt.subplots(
        ncols=2,
        proj=[_make_test_wcs(), _make_test_wcs()],
    )
    axs.imshow(np.zeros((16, 16)), origin="lower")

    fig.canvas.draw()

    assert axs[0].coords[1].get_ticklabel_visible()
    assert axs[0].coords[1].get_axislabel_position()
    assert not axs[1].coords[1].get_ticklabel_visible()
    assert not axs[1].coords[1].get_axislabel_position()


def test_astro_axes_preserve_shared_top_labels():
    fig, axs = uplt.subplots(
        nrows=2,
        proj=[_make_test_wcs(), _make_test_wcs()],
    )
    axs.imshow(np.zeros((16, 16)), origin="lower")
    for ax in axs:
        ax.coords[0].set_ticklabel_position("t")
        ax.coords[0].set_axislabel_position("t")

    fig.canvas.draw()

    assert axs[0].coords[0].get_ticklabel_position() == ["t"]
    assert axs[0].coords[0].get_axislabel_position() == ["t"]
    assert not axs[1].coords[0].get_ticklabel_position()
    assert not axs[1].coords[0].get_axislabel_position()


def test_astro_axes_preserve_shared_right_labels():
    fig, axs = uplt.subplots(
        ncols=2,
        proj=[_make_test_wcs(), _make_test_wcs()],
    )
    axs.imshow(np.zeros((16, 16)), origin="lower")
    for ax in axs:
        ax.coords[1].set_ticklabel_position("r")
        ax.coords[1].set_axislabel_position("r")

    fig.canvas.draw()

    assert not axs[0].coords[1].get_ticklabel_position()
    assert not axs[0].coords[1].get_axislabel_position()
    assert axs[1].coords[1].get_ticklabel_position() == ["r"]
    assert axs[1].coords[1].get_axislabel_position() == ["r"]


def test_astro_axes_panels_preserve_explicit_top_right_labels():
    fig, axs = uplt.subplots(
        nrows=2,
        ncols=2,
        proj=[_make_test_wcs() for _ in range(4)],
    )
    axs.imshow(np.zeros((16, 16)), origin="lower")
    for ax in axs:
        ax.coords[0].set_ticklabel_position("t")
        ax.coords[0].set_axislabel_position("t")
        ax.coords[1].set_ticklabel_position("r")
        ax.coords[1].set_axislabel_position("r")

    pax_top = axs[0].panel("top")
    pax_right = axs[1].panel("right")
    fig.canvas.draw()

    assert not axs[0].coords[0].get_ticklabel_position()
    assert not axs[0].coords[0].get_axislabel_position()
    assert pax_top._is_ticklabel_on("labeltop")
    assert not pax_top._is_ticklabel_on("labelbottom")

    assert not axs[1].coords[1].get_ticklabel_position()
    assert not axs[1].coords[1].get_axislabel_position()
    assert pax_right._is_ticklabel_on("labelright")
    assert not pax_right._is_ticklabel_on("labelleft")
