#!/usr/bin/env python3
"""
Test legends.
"""
import numpy as np
import pandas as pd
import pytest

import ultraplot as uplt


@pytest.mark.mpl_image_compare
def test_auto_legend(rng):
    """
    Test retrieval of legends from panels, insets, etc.
    """
    fig, ax = uplt.subplots()
    ax.line(rng.random((5, 3)), labels=list("abc"))
    px = ax.panel_axes("right", share=False)
    px.linex(rng.random((5, 3)), labels=list("xyz"))
    # px.legend(loc='r')
    ix = ax.inset_axes((-0.2, 0.8, 0.5, 0.5), zoom=False)
    ix.line(rng.random((5, 2)), labels=list("pq"))
    ax.legend(loc="b", order="F", edgecolor="red9", edgewidth=3)
    return fig


@pytest.mark.mpl_image_compare
def test_singleton_legend():
    """
    Test behavior when singleton lists are passed.
    Ensure this does not trigger centered-row legends.
    """
    fig, ax = uplt.subplots()
    h1 = ax.plot([0, 1, 2], label="a")
    h2 = ax.plot([0, 1, 1], label="b")
    ax.legend(loc="best")
    ax.legend([h1, h2], loc="bottom")
    return fig


@pytest.mark.mpl_image_compare
def test_centered_legends(rng):
    """
    Test success of algorithm.
    """
    # Basic centered legends
    fig, axs = uplt.subplots(ncols=2, nrows=2, axwidth=2)
    hs = axs[0].plot(rng.random((10, 6)))
    locs = ["l", "t", "r", "uc", "ul", "ll"]
    locs = ["l", "t", "uc", "ll"]
    labels = ["a", "bb", "ccc", "ddddd", "eeeeeeee", "fffffffff"]
    for ax, loc in zip(axs, locs):
        ax.legend(hs, loc=loc, ncol=3, labels=labels, center=True)

    # Pass centered legends with keywords or list-of-list input.
    fig, ax = uplt.subplots()
    hs = ax.plot(rng.random((10, 5)), labels=list("abcde"))
    ax.legend(hs, center=True, loc="b")
    ax.legend(hs + hs[:1], loc="r", ncol=1)
    ax.legend([hs[:2], hs[2:], hs[0]], loc="t")
    return fig


@pytest.mark.mpl_image_compare
def test_manual_labels():
    """
    Test mixed auto and manual labels. Passing labels but no handles does nothing
    This is breaking change but probably best. We should not be "guessing" the
    order objects were drawn in then assigning labels to them. Similar to using
    OO interface and rejecting pyplot "current axes" and "current figure".
    """
    fig, ax = uplt.subplots()
    (h1,) = ax.plot([0, 1, 2], label="label1")
    (h2,) = ax.plot([0, 1, 1], label="label2")
    for loc in ("best", "bottom"):
        ax.legend([h1, h2], loc=loc, labels=[None, "override"])
    fig, ax = uplt.subplots()
    ax.plot([0, 1, 2])
    ax.plot([0, 1, 1])
    for loc in ("best", "bottom"):
        # ax.legend(loc=loc, labels=['a', 'b'])
        ax.legend(["a", "b"], loc=loc)  # same as above
    return fig


@pytest.mark.mpl_image_compare
def test_contour_legend_with_label(rng):
    """
    Support contour element labels. If has no label should trigger warning.
    """
    figs = []
    label = "label"

    fig, axs = uplt.subplots(ncols=2)
    ax = axs[0]
    ax.contour(rng.random((5, 5)), color="k", label=label, legend="b")
    ax = axs[1]
    ax.pcolor(rng.random((5, 5)), label=label, legend="b")
    return fig


@pytest.mark.mpl_image_compare
def test_contour_legend_without_label(rng):
    """
    Support contour element labels. If has no label should trigger warning.
    """
    label = None
    fig, axs = uplt.subplots(ncols=2)
    ax = axs[0]
    ax.contour(rng.random((5, 5)), color="k", label=label, legend="b")
    ax = axs[1]
    ax.pcolor(rng.random((5, 5)), label=label, legend="b")
    return fig


@pytest.mark.mpl_image_compare
def test_histogram_legend(rng):
    """
    Support complex histogram legends.
    """
    with uplt.rc.context({"inlineformat": "svg"}):
        fig, ax = uplt.subplots()
        res = ax.hist(
            rng.random((500, 2)), 4, labels=("label", "other"), edgefix=True, legend="b"
        )
        ax.legend(
            res, loc="r", ncol=1
        )  # should issue warning after ignoring numpy arrays
        df = pd.DataFrame(
            {"length": [1.5, 0.5, 1.2, 0.9, 3], "width": [0.7, 0.2, 0.15, 0.2, 1.1]},
            index=["pig", "rabbit", "duck", "chicken", "horse"],
        )
        fig, axs = uplt.subplots(ncols=3)
        ax = axs[0]
        res = ax.hist(df, bins=3, legend=True, lw=3)
        ax.legend(loc="b")
        for ax, meth in zip(axs[1:], ("bar", "area")):
            hs = getattr(ax, meth)(df, legend="ul", lw=3)
            ax.legend(hs, loc="b")
    return fig


@pytest.mark.mpl_image_compare
def test_multiple_calls(rng):
    """
    Test successive plotting additions to guides.
    """
    fig, ax = uplt.subplots()
    ax.pcolor(rng.random((10, 10)), colorbar="b")
    ax.pcolor(rng.random((10, 5)), cmap="grays", colorbar="b")
    ax.pcolor(rng.random((10, 5)), cmap="grays", colorbar="b")

    fig, ax = uplt.subplots()
    data = rng.random((10, 5))
    for i in range(data.shape[1]):
        ax.plot(data[:, i], colorbar="b", label=f"x{i}", colorbar_kw={"label": "hello"})
    return fig


@pytest.mark.mpl_image_compare
def test_tuple_handles(rng):
    """
    Test tuple legend handles.
    """
    from matplotlib import legend_handler

    fig, ax = uplt.subplots(refwidth=3, abc="A.", abcloc="ul", span=False)
    patches = ax.fill_between(rng.random((10, 3)), stack=True)
    lines = ax.line(1 + 0.5 * (rng.random((10, 3)) - 0.5).cumsum(axis=0))
    # ax.legend([(handles[0], lines[1])], ['joint label'], loc='bottom', queue=True)
    for hs in (lines, patches):
        ax.legend(
            [tuple(hs[:3]) if len(hs) == 3 else hs],
            ["joint label"],
            loc="bottom",
            queue=True,
            ncol=1,
            handlelength=4.5,
            handleheight=1.5,
            handler_map={tuple: legend_handler.HandlerTuple(pad=0, ndivide=3)},
        )
    return fig


@pytest.mark.mpl_image_compare
def test_legend_col_spacing(rng):
    """
    Test legend column spacing.
    """
    fig, ax = uplt.subplots()
    ax.plot(rng.random(10), label="short")
    ax.plot(rng.random(10), label="longer label")
    ax.plot(rng.random(10), label="even longer label")
    for idx in range(3):
        spacing = f"{idx}em"
        if idx == 2:
            spacing = 3
        ax.legend(loc="bottom", ncol=3, columnspacing=spacing)

    with pytest.raises(ValueError):
        ax.legend(loc="bottom", ncol=3, columnspacing="15x")
    return fig


def test_sync_label_dict(rng):
    """
    Legends are held within _legend_dict for which the key is a tuple of location and alignment.

    We need to ensure that the legend is updated in the dictionary when its location is changed.
    """
    data = rng.random((2, 100))
    fig, ax = uplt.subplots()
    ax.plot(*data, label="test")
    leg = ax.legend(loc="lower right")
    assert ("lower right", "center") in ax[0]._legend_dict, "Legend not found in dict"
    leg.set_loc("upper left")
    assert ("upper left", "center") in ax[
        0
    ]._legend_dict, "Legend not found in dict after update"
    assert leg is ax[0]._legend_dict[("upper left", "center")]
    assert ("lower right", "center") not in ax[
        0
    ]._legend_dict, "Old legend not removed from dict"
    uplt.close(fig)


def test_external_mode_defers_on_the_fly_legend():
    """
    External mode should defer on-the-fly legend creation until explicitly requested.
    """
    fig, ax = uplt.subplots()
    ax.set_external(True)
    (h,) = ax.plot([0, 1], label="a", legend="b")

    # No legend should have been created yet
    assert getattr(ax[0], "legend_", None) is None

    # Explicit legend creation should include the plotted label
    leg = ax.legend(h, loc="b")
    labels = [t.get_text() for t in leg.get_texts()]
    assert "a" in labels
    uplt.close(fig)


def test_external_mode_mixing_context_manager():
    """
    Mixing external and internal plotting on the same axes:
    - Inside ax.external(): on-the-fly legend is deferred
    - Outside: UltraPlot-native plotting resumes as normal
    - Final explicit ax.legend() consolidates both kinds of artists
    """
    fig, ax = uplt.subplots()

    with ax.external():
        (ext,) = ax.plot([0, 1], label="ext", legend="b")  # deferred

    (intr,) = ax.line([0, 1], label="int")  # normal UL behavior

    leg = ax.legend([ext, intr], loc="b")
    labels = {t.get_text() for t in leg.get_texts()}
    assert {"ext", "int"}.issubset(labels)
    uplt.close(fig)


def test_external_mode_toggle_enables_auto():
    """
    Toggling external mode back off should resume on-the-fly guide creation.
    """
    fig, ax = uplt.subplots()

    ax.set_external(True)
    (ha,) = ax.plot([0, 1], label="a", legend="b")
    assert getattr(ax[0], "legend_", None) is None  # deferred

    ax.set_external(False)
    (hb,) = ax.plot([0, 1], label="b", legend="b")
    # Now legend is queued for creation; verify it is registered in the outer legend dict
    assert ("bottom", "center") in ax[0]._legend_dict

    # Ensure final legend contains both entries
    leg = ax.legend([ha, hb], loc="b")
    labels = {t.get_text() for t in leg.get_texts()}
    assert {"a", "b"}.issubset(labels)
    uplt.close(fig)


def test_synthetic_handles_filtered():
    """
    Synthetic-tagged helper artists must be ignored by legend parsing even when
    explicitly passed as handles.
    """
    fig, ax = uplt.subplots()
    (h1,) = ax.plot([0, 1], label="visible")
    (h2,) = ax.plot([1, 0], label="helper")
    # Mark helper as synthetic; it should be filtered out from legend entries
    setattr(h2, "_ultraplot_synthetic", True)

    leg = ax.legend([h1, h2], loc="best")
    labels = [t.get_text() for t in leg.get_texts()]
    assert "visible" in labels
    assert "helper" not in labels
    uplt.close(fig)


def test_fill_between_included_in_legend():
    """
    Legitimate fill_between/area handles must appear in legends (regression for
    previously skipped FillBetweenPolyCollection).
    """
    fig, ax = uplt.subplots()
    x = np.arange(5)
    y1 = np.zeros(5)
    y2 = np.ones(5)
    ax.fill_between(x, y1, y2, label="band")

    leg = ax.legend(loc="best")
    labels = [t.get_text() for t in leg.get_texts()]
    assert "band" in labels
    uplt.close(fig)


def test_legend_span_bottom():
    """Test bottom legend with span parameter."""

    fig, axs = uplt.subplots(nrows=2, ncols=3)
    axs[0, 0].plot([], [], label="test")

    # Legend below row 1, spanning columns 1-2
    leg = fig.legend(ax=axs[0, :], span=(1, 2), loc="bottom")

    # Verify legend was created
    assert leg is not None


def test_legend_span_top():
    """Test top legend with span parameter."""

    fig, axs = uplt.subplots(nrows=2, ncols=3)
    axs[0, 0].plot([], [], label="test")

    # Legend above row 2, spanning columns 2-3
    leg = fig.legend(ax=axs[1, :], cols=(2, 3), loc="top")

    assert leg is not None


def test_legend_span_right():
    """Test right legend with rows parameter."""

    fig, axs = uplt.subplots(nrows=3, ncols=2)
    axs[0, 0].plot([], [], label="test")

    # Legend right of column 1, spanning rows 1-2
    leg = fig.legend(ax=axs[:, 0], rows=(1, 2), loc="right")

    assert leg is not None


def test_legend_span_left():
    """Test left legend with rows parameter."""

    fig, axs = uplt.subplots(nrows=3, ncols=2)
    axs[0, 0].plot([], [], label="test")

    # Legend left of column 2, spanning rows 2-3
    leg = fig.legend(ax=axs[:, 1], rows=(2, 3), loc="left")

    assert leg is not None


def test_legend_span_validation_left_with_cols_error():
    """Test that LEFT legend raises error with cols parameter."""

    fig, axs = uplt.subplots(nrows=3, ncols=2)
    axs[0, 0].plot([], [], label="test")

    with pytest.raises(ValueError, match="left.*vertical.*use 'rows='.*not 'cols='"):
        fig.legend(ax=axs[0, 0], cols=(1, 2), loc="left")


def test_legend_span_validation_right_with_cols_error():
    """Test that RIGHT legend raises error with cols parameter."""
    fig, axs = uplt.subplots(nrows=3, ncols=2)
    axs[0, 0].plot([], [], label="test")

    with pytest.raises(ValueError, match="right.*vertical.*use 'rows='.*not 'cols='"):
        fig.legend(ax=axs[0, 0], cols=(1, 2), loc="right")


def test_legend_span_validation_top_with_rows_error():
    """Test that TOP legend raises error with rows parameter."""
    fig, axs = uplt.subplots(nrows=2, ncols=3)
    axs[0, 0].plot([], [], label="test")

    with pytest.raises(ValueError, match="top.*horizontal.*use 'cols='.*not 'rows='"):
        fig.legend(ax=axs[0, 0], rows=(1, 2), loc="top")


def test_legend_span_validation_bottom_with_rows_error():
    """Test that BOTTOM legend raises error with rows parameter."""
    fig, axs = uplt.subplots(nrows=2, ncols=3)
    axs[0, 0].plot([], [], label="test")

    with pytest.raises(
        ValueError, match="bottom.*horizontal.*use 'cols='.*not 'rows='"
    ):
        fig.legend(ax=axs[0, 0], rows=(1, 2), loc="bottom")


def test_legend_span_validation_left_with_span_warns():
    """Test that LEFT legend with span parameter issues warning."""
    fig, axs = uplt.subplots(nrows=3, ncols=2)
    axs[0, 0].plot([], [], label="test")

    with pytest.warns(match="left.*vertical.*prefer 'rows='"):
        leg = fig.legend(ax=axs[0, 0], span=(1, 2), loc="left")
        assert leg is not None


def test_legend_span_validation_right_with_span_warns():
    """Test that RIGHT legend with span parameter issues warning."""
    fig, axs = uplt.subplots(nrows=3, ncols=2)
    axs[0, 0].plot([], [], label="test")

    with pytest.warns(match="right.*vertical.*prefer 'rows='"):
        leg = fig.legend(ax=axs[0, 0], span=(1, 2), loc="right")
        assert leg is not None


def test_legend_array_without_span():
    """Test that legend on array without span preserves original behavior."""
    fig, axs = uplt.subplots(nrows=2, ncols=2)
    axs[0, 0].plot([], [], label="test")

    # Should create legend for all axes in the array
    leg = fig.legend(ax=axs[:], loc="right")
    assert leg is not None


def test_legend_array_with_span():
    """Test that legend on array with span uses first axis + span extent."""
    fig, axs = uplt.subplots(nrows=2, ncols=3)
    axs[0, 0].plot([], [], label="test")

    # Should use first axis position with span extent
    leg = fig.legend(ax=axs[0, :], span=(1, 2), loc="bottom")
    assert leg is not None


def test_legend_row_without_span():
    """Test that legend on row without span spans entire row."""
    fig, axs = uplt.subplots(nrows=2, ncols=3)
    axs[0, 0].plot([], [], label="test")

    # Should span all 3 columns
    leg = fig.legend(ax=axs[0, :], loc="bottom")
    assert leg is not None


def test_legend_column_without_span():
    """Test that legend on column without span spans entire column."""
    fig, axs = uplt.subplots(nrows=3, ncols=2)
    axs[0, 0].plot([], [], label="test")

    # Should span all 3 rows
    leg = fig.legend(ax=axs[:, 0], loc="right")
    assert leg is not None


def test_legend_multiple_sides_with_span():
    """Test multiple legends on different sides with span control."""
    fig, axs = uplt.subplots(nrows=3, ncols=3)
    axs[0, 0].plot([], [], label="test")

    # Create legends on all 4 sides with different spans
    leg_bottom = fig.legend(ax=axs[0, 0], span=(1, 2), loc="bottom")
    leg_top = fig.legend(ax=axs[1, 0], span=(2, 3), loc="top")
    leg_right = fig.legend(ax=axs[0, 0], rows=(1, 2), loc="right")
    leg_left = fig.legend(ax=axs[0, 1], rows=(2, 3), loc="left")

    assert leg_bottom is not None
    assert leg_top is not None
    assert leg_right is not None
    assert leg_left is not None


def test_legend_auto_collect_handles_labels_with_span():
    """Test automatic collection of handles and labels from multiple axes with span parameters."""

    fig, axs = uplt.subplots(nrows=2, ncols=2)

    # Create different plots in each subplot with labels
    axs[0, 0].plot([0, 1], [0, 1], label="line1")
    axs[0, 1].plot([0, 1], [1, 0], label="line2")
    axs[1, 0].scatter([0.5], [0.5], label="point1")
    axs[1, 1].scatter([0.5], [0.5], label="point2")

    # Test automatic collection with span parameter (no explicit handles/labels)
    leg = fig.legend(ax=axs[0, :], span=(1, 2), loc="bottom")

    # Verify legend was created and contains all handles/labels from both axes
    assert leg is not None
    assert len(leg.get_texts()) == 2  # Should have 2 labels (line1, line2)

    # Test with rows parameter
    leg2 = fig.legend(ax=axs[:, 0], rows=(1, 2), loc="right")
    assert leg2 is not None
    assert len(leg2.get_texts()) == 2  # Should have 2 labels (line1, point1)


def test_legend_explicit_handles_labels_override_auto_collection():
    """Test that explicit handles/labels override auto-collection."""

    fig, axs = uplt.subplots(nrows=1, ncols=2)

    # Create plots with labels
    (h1,) = axs[0].plot([0, 1], [0, 1], label="auto_label1")
    (h2,) = axs[1].plot([0, 1], [1, 0], label="auto_label2")

    # Test with explicit handles/labels (should override auto-collection)
    custom_handles = [h1]
    custom_labels = ["custom_label"]
    leg = fig.legend(
        ax=axs, span=(1, 2), loc="bottom", handles=custom_handles, labels=custom_labels
    )

    # Verify legend uses explicit handles/labels, not auto-collected ones
    assert leg is not None
    assert len(leg.get_texts()) == 1
    assert leg.get_texts()[0].get_text() == "custom_label"


import numpy as np

import ultraplot as uplt


def test_legend_ref_argument():
    """Test using 'ref' to decouple legend location from content axes."""
    fig, axs = uplt.subplots(nrows=2, ncols=2)
    axs[0, 0].plot([], [], label="line1")  # Row 0
    axs[1, 0].plot([], [], label="line2")  # Row 1

    # Place legend below Row 0 (axs[0, :]) using content from Row 1 (axs[1, :])
    leg = fig.legend(ax=axs[1, :], ref=axs[0, :], loc="bottom")

    assert leg is not None

    # Should be a single legend because span is inferred from ref
    assert not isinstance(leg, tuple)

    texts = [t.get_text() for t in leg.get_texts()]
    assert "line2" in texts
    assert "line1" not in texts


def test_legend_ref_argument_no_ax():
    """Test using 'ref' where 'ax' is implied to be 'ref'."""
    fig, axs = uplt.subplots(nrows=1, ncols=1)
    axs[0].plot([], [], label="line1")

    # ref provided, ax=None. Should behave like ax=ref.
    leg = fig.legend(ref=axs[0], loc="bottom")
    assert leg is not None

    # Should be a single legend
    assert not isinstance(leg, tuple)

    texts = [t.get_text() for t in leg.get_texts()]
    assert "line1" in texts
