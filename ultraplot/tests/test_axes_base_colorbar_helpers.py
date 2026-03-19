#!/usr/bin/env python3
"""Additional branch coverage for inset colorbar helpers in axes.base."""

from types import SimpleNamespace

import pytest
from matplotlib.backend_bases import ResizeEvent
from matplotlib.transforms import Bbox

import ultraplot as uplt
from ultraplot.axes import base as pbase


@pytest.mark.parametrize(
    ("orientation", "labelloc", "expected"),
    [
        ("horizontal", "left", 90),
        ("horizontal", "right", -90),
        ("horizontal", "bottom", 0),
        ("vertical", "right", -90),
        ("vertical", "top", 0),
    ],
)
def test_inset_colorbar_label_rotation_variants(orientation, labelloc, expected):
    kw_label = {}
    pbase._determine_label_rotation(
        "auto",
        labelloc=labelloc,
        orientation=orientation,
        kw_label=kw_label,
    )
    assert kw_label["rotation"] == expected


@pytest.mark.parametrize(
    ("orientation", "loc", "labelloc", "ticklocation"),
    [
        ("vertical", "upper left", "left", "left"),
        ("vertical", "upper right", "top", "right"),
        ("vertical", "lower right", "top", "right"),
        ("vertical", "lower left", "bottom", "left"),
        ("vertical", "upper right", "bottom", "right"),
        ("horizontal", "upper right", "bottom", "bottom"),
        ("horizontal", "lower left", "bottom", "bottom"),
        ("horizontal", "upper right", "top", "top"),
        ("horizontal", "lower left", "top", "top"),
    ],
)
def test_inset_colorbar_bounds_variants(orientation, loc, labelloc, ticklocation):
    fig, ax = uplt.subplots()
    ax = ax[0]

    bounds_inset, bounds_frame = pbase._solve_inset_colorbar_bounds(
        axes=ax,
        loc=loc,
        orientation=orientation,
        length=0.4,
        width=0.08,
        xpad=0.02,
        ypad=0.02,
        ticklocation=ticklocation,
        labelloc=labelloc,
        label="Inset label",
        labelrotation="auto",
        tick_fontsize=10,
        label_fontsize=12,
    )
    assert len(bounds_inset) == 4
    assert len(bounds_frame) == 4

    legacy_inset, legacy_frame = pbase._legacy_inset_colorbar_bounds(
        axes=ax,
        loc=loc,
        orientation=orientation,
        length=0.4,
        width=0.08,
        xpad=0.02,
        ypad=0.02,
        ticklocation=ticklocation,
        labelloc=labelloc,
        label="Inset label",
        labelrotation="auto",
        tick_fontsize=10,
        label_fontsize=12,
    )
    assert len(legacy_inset) == 4
    assert len(legacy_frame) == 4


def test_inset_colorbar_axis_rotation_and_long_axis_helpers(rng):
    fig, ax = uplt.subplots()
    ax = ax[0]
    mappable = ax.imshow(rng.random((6, 6)))
    colorbar = ax.colorbar(mappable, loc="ur", orientation="vertical")

    long_axis = pbase._get_colorbar_long_axis(colorbar)
    assert (
        pbase._get_axis_for("left", "upper right", ax=colorbar, orientation="vertical")
        is long_axis
    )
    assert (
        pbase._get_axis_for("top", "upper right", ax=colorbar, orientation="vertical")
        is colorbar.ax.xaxis
    )
    assert (
        pbase._get_axis_for(None, "upper right", ax=colorbar, orientation="horizontal")
        is long_axis
    )

    dummy = SimpleNamespace(long_axis=colorbar.ax.yaxis)
    assert pbase._get_colorbar_long_axis(dummy) is colorbar.ax.yaxis

    kw_label = {}
    pbase._determine_label_rotation(
        "auto",
        labelloc="left",
        orientation="vertical",
        kw_label=kw_label,
    )
    assert kw_label["rotation"] == 90
    assert (
        pbase._resolve_label_rotation(
            "auto",
            labelloc="top",
            orientation="horizontal",
        )
        == 0.0
    )
    assert (
        pbase._resolve_label_rotation(
            "bad",
            labelloc="top",
            orientation="horizontal",
        )
        == 0.0
    )

    with pytest.raises(ValueError, match="Could not determine label axis"):
        pbase._get_axis_for(
            "center",
            "upper right",
            ax=colorbar,
            orientation="vertical",
        )
    with pytest.raises(ValueError, match="Label rotation must be a number or 'auto'"):
        pbase._determine_label_rotation(
            "bad",
            labelloc="left",
            orientation="vertical",
            kw_label={},
        )


def test_inset_colorbar_measurement_helpers():
    class BrokenFigure:
        dpi = 72

        def _get_renderer(self):
            raise RuntimeError("broken")

    class BrokenAxis:
        def get_ticklabels(self):
            raise RuntimeError("broken")

    fig, ax = uplt.subplots()
    ax = ax[0]
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["left tick label", "right tick label"], rotation=35)
    text = ax.text(-0.1, 1.05, "outside", transform=ax.transAxes)
    fig.canvas.draw()

    label_extent = pbase._measure_label_points("label", 45, 12, fig)
    assert label_extent is not None
    assert label_extent[0] > 0

    text_extent = pbase._measure_text_artist_points(text, fig)
    assert text_extent is not None
    assert text_extent[1] > 0

    tick_extent = pbase._measure_ticklabel_extent_points(ax.xaxis, fig)
    assert tick_extent is not None
    assert tick_extent[0] > 0

    text_overhang = pbase._measure_text_overhang_axes(text, ax)
    assert text_overhang is not None
    assert text_overhang[0] > 0 or text_overhang[3] > 0

    tick_overhang = pbase._measure_ticklabel_overhang_axes(ax.xaxis, ax)
    assert tick_overhang is not None

    assert pbase._measure_label_points("label", 0, 12, BrokenFigure()) is None
    assert pbase._measure_ticklabel_extent_points(BrokenAxis(), fig) is None


def test_inset_colorbar_layout_solver_and_reflow_helpers(rng):
    fig, ax = uplt.subplots()
    ax = ax[0]
    mappable = ax.imshow(rng.random((10, 10)))
    colorbar = ax.colorbar(
        mappable,
        loc="ur",
        frameon=True,
        label="Inset label",
        labelloc="top",
        orientation="vertical",
    )
    fig.canvas.draw()

    bounds_inset, bounds_frame = pbase._solve_inset_colorbar_bounds(
        axes=ax,
        loc="upper right",
        orientation="vertical",
        length=0.4,
        width=0.08,
        xpad=0.02,
        ypad=0.02,
        ticklocation="right",
        labelloc="top",
        label="Inset label",
        labelrotation="auto",
        tick_fontsize=10,
        label_fontsize=12,
    )
    assert len(bounds_inset) == 4
    assert len(bounds_frame) == 4

    legacy_inset, legacy_frame = pbase._legacy_inset_colorbar_bounds(
        axes=ax,
        loc="upper right",
        orientation="horizontal",
        length=0.4,
        width=0.08,
        xpad=0.02,
        ypad=0.02,
        ticklocation="bottom",
        labelloc="bottom",
        label="Inset label",
        labelrotation="auto",
        tick_fontsize=10,
        label_fontsize=12,
    )
    assert len(legacy_inset) == 4
    assert legacy_frame[2] >= legacy_inset[2]

    frame = colorbar.ax._inset_colorbar_frame
    assert frame is not None
    pbase._apply_inset_colorbar_layout(
        colorbar.ax,
        bounds_inset=bounds_inset,
        bounds_frame=bounds_frame,
        frame=frame,
    )
    assert colorbar.ax._inset_colorbar_bounds["inset"] == bounds_inset

    pbase._register_inset_colorbar_reflow(fig)
    callback_id = fig._inset_colorbar_reflow_cid
    pbase._register_inset_colorbar_reflow(fig)
    assert fig._inset_colorbar_reflow_cid == callback_id

    ax._inset_colorbar_obj = colorbar
    colorbar.ax._inset_colorbar_obj = colorbar
    event = ResizeEvent("resize_event", fig.canvas)
    fig.canvas.callbacks.process("resize_event", event)
    assert getattr(ax, "_inset_colorbar_needs_reflow", False) is True

    renderer = fig.canvas.get_renderer()
    labelloc = colorbar.ax._inset_colorbar_labelloc
    assert not bool(
        pbase._inset_colorbar_frame_needs_reflow(
            colorbar,
            labelloc=labelloc,
            renderer=renderer,
        )
    )

    original_get_window_extent = frame.get_window_extent
    frame.get_window_extent = lambda renderer=None: Bbox.from_bounds(0, 0, 1, 1)
    assert pbase._inset_colorbar_frame_needs_reflow(
        colorbar,
        labelloc=labelloc,
        renderer=renderer,
    )
    frame.get_window_extent = original_get_window_extent

    pbase._reflow_inset_colorbar_frame(
        colorbar,
        labelloc=labelloc,
        ticklen=colorbar.ax._inset_colorbar_ticklen,
        renderer=renderer,
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    assert not bool(
        pbase._inset_colorbar_frame_needs_reflow(
            colorbar,
            labelloc=labelloc,
            renderer=renderer,
        )
    )
