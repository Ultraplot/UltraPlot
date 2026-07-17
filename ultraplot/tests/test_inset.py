import numpy as np
import pytest
from matplotlib import patches as mpatches

import ultraplot as uplt


@pytest.mark.mpl_image_compare
def test_inset_basic():
    # Demonstrate that complex arrangements preserve
    # spacing, aspect ratios, and axis sharing
    gs = uplt.GridSpec(nrows=2, ncols=2)
    fig = uplt.figure(refwidth=1.5, share=False)
    fig.canvas.draw()
    for ss, side in zip(gs, "tlbr"):
        ax = fig.add_subplot(ss)
        px = ax.panel_axes(side, width="3em")
    fig.format(
        xlim=(0, 1),
        ylim=(0, 1),
        xlabel="xlabel",
        ylabel="ylabel",
        xticks=0.2,
        yticks=0.2,
        title="Title",
        suptitle="Complex arrangement of panels",
        toplabels=("Column 1", "Column 2"),
        abc=True,
        abcloc="ul",
        titleloc="uc",
        titleabove=False,
    )
    return fig


def test_geo_inset_preserves_bounds_anchor():
    pytest.importorskip("cartopy.crs")

    fig, ax = uplt.subplots(proj="cyl")
    parent = ax[0]
    inset = parent.inset((0.1, 0.2, 0.4, 0.2), transform="axes")
    fig.canvas.draw()

    expected = fig.transFigure.inverted().transform(
        parent.transAxes.transform((0.1, 0.2))
    )
    actual = inset.get_position()
    np.testing.assert_allclose((actual.x0, actual.y0), expected)
    assert actual.width < 0.4 * parent.get_position().width
    uplt.close(fig)


def test_hawkeye_projection_and_auto_aspects():
    pytest.importorskip("cartopy.crs")

    fig, ax = uplt.subplots(proj="cyl")
    parent = ax[0]
    projected = parent.hawkeye((0.9, 0.9), size=(0.2, 0.2))
    stretched = parent.hawkeye((0.9, 0.6), size=0.2, aspect="auto")
    fig.canvas.draw()

    projected_bbox = projected.get_position()
    stretched_bbox = stretched.get_position()
    np.testing.assert_allclose(
        (stretched_bbox.width, stretched_bbox.height),
        (0.2 * parent.get_position().width, 0.2 * parent.get_position().height),
    )
    assert projected_bbox.width != pytest.approx(projected_bbox.height)
    uplt.close(fig)


def test_hawkeye_extent_and_connectors():
    pytest.importorskip("cartopy.crs")

    fig, ax = uplt.subplots(proj="cyl")
    inset = ax[0].hawkeye(
        (0.9, 0.9),
        size=0.2,
        extent=(120, 180, 10, 30),
        connectors=True,
    )
    fig.canvas.draw()

    assert inset._hawkeye_relation == "detail"
    assert len(inset._hawkeye_indicator.connectors) == 4
    uplt.close(fig)


def test_hawkeye_auto_relation_handles_disjoint_detail_extent():
    pytest.importorskip("cartopy.crs")

    fig, ax = uplt.subplots(proj="cyl")
    ax[0].set_extent((30, 100, -20, 30))
    inset = ax[0].hawkeye((0.9, 0.9), size=0.2, extent=(120, 180, 10, 30))

    assert inset._hawkeye_relation == "detail"
    uplt.close(fig)


def test_hawkeye_connectors_require_extent():
    pytest.importorskip("cartopy.crs")

    fig, ax = uplt.subplots(proj="cyl")
    with pytest.raises(ValueError, match="requires extent"):
        ax[0].hawkeye((0.9, 0.9), size=0.2, connectors=True)
    uplt.close(fig)


def test_hawkeye_circular_cutout_and_leader():
    pytest.importorskip("cartopy.crs")

    fig, ax = uplt.subplots(proj="cyl")
    inset = ax[0].hawkeye(
        (0.9, 0.9),
        size=0.2,
        extent=(120, 180, 10, 30),
        connectors="line",
        shape="circle",
        target="circle",
    )
    fig.canvas.draw()

    assert isinstance(inset._hawkeye_indicator, mpatches.Circle)
    assert len(inset._hawkeye_connectors) == 1
    connector = inset._hawkeye_connectors[0]
    assert connector.patchA is inset.patch
    assert connector.patchB is inset._hawkeye_indicator
    assert connector.axes is ax[0]
    assert not inset.get_in_layout()
    bbox = inset.get_position()
    figure_bbox = fig.bbox
    assert bbox.width * figure_bbox.width == pytest.approx(
        bbox.height * figure_bbox.height
    )
    assert inset.get_aspect() == 1
    assert not inset._gridlines_major.xline_artists
    assert not inset._gridlines_major.yline_artists
    uplt.close(fig)


def test_hawkeye_overview_connectors():
    pytest.importorskip("cartopy.crs")

    fig, ax = uplt.subplots(proj="cyl")
    parent = ax[0]
    parent.set_extent((145, 155, -38, -32))
    inset = parent.hawkeye(
        (0.9, 0.9),
        size=0.2,
        extent=(110, 180, -50, 0),
        connectors=True,
    )
    fig.canvas.draw()

    assert inset._hawkeye_relation == "overview"
    assert inset._hawkeye_indicator in inset.patches
    assert len(inset._hawkeye_connectors) == 2
    uplt.close(fig)


def test_hawkeye_overview_indicator():
    pytest.importorskip("cartopy.crs")

    fig, ax = uplt.subplots(proj="cyl")
    parent = ax[0]
    parent.set_extent((145, 155, -38, -32))
    inset = parent.hawkeye(
        (0.9, 0.9), size=0.2, extent=(110, 180, -50, 0), relation="overview"
    )
    fig.canvas.draw()

    assert inset._hawkeye_indicator in inset.patches
    assert inset._hawkeye_indicator not in parent.patches
    uplt.close(fig)


def test_hawkeye_zoom_indicator_normalizes_legacy_tuple(monkeypatch) -> None:
    """The corners+detail indicator exposes ``.connectors`` on every mpl version.

    matplotlib < 3.10 returns a ``(rectangle, connectors)`` tuple from
    ``indicate_inset_zoom`` instead of an ``InsetIndicator``; the helper must
    normalize both to something exposing ``.rectangle`` / ``.connectors``.
    """
    import matplotlib.axes as maxes
    from ultraplot.axes import geo

    fig, ax = uplt.subplots()
    inset = fig.add_axes([0.6, 0.6, 0.3, 0.3])

    # Force the pre-3.10 tuple return regardless of the installed matplotlib.
    original = maxes.Axes.indicate_inset_zoom

    def legacy(self, inset_ax, **kwargs):
        indicator = original(self, inset_ax, **kwargs)
        return indicator.rectangle, tuple(indicator.connectors)

    monkeypatch.setattr(maxes.Axes, "indicate_inset_zoom", legacy)
    normalized = geo._add_hawkeye_zoom_indicator(ax[0], inset)
    assert hasattr(normalized, "rectangle")
    assert len(normalized.connectors) == 4
    uplt.close(fig)


def test_hawkeye_indicator_disabled() -> None:
    pytest.importorskip("cartopy.crs")

    fig, ax = uplt.subplots(proj="cyl")
    inset = ax[0].hawkeye(
        (0.9, 0.9), size=0.2, extent=(120, 180, 10, 30), indicator=False
    )

    # Relation is still resolved, but no indicator artist is drawn.
    assert inset._hawkeye_relation == "detail"
    assert not hasattr(inset, "_hawkeye_indicator")
    uplt.close(fig)


def test_hawkeye_overview_leader() -> None:
    pytest.importorskip("cartopy.crs")

    fig, ax = uplt.subplots(proj="cyl")
    parent = ax[0]
    parent.set_extent((145, 155, -38, -32))
    inset = parent.hawkeye(
        (0.9, 0.9),
        size=0.2,
        extent=(110, 180, -50, 0),
        connectors="line",
        relation="overview",
    )
    fig.canvas.draw()

    assert inset._hawkeye_relation == "overview"
    assert inset._hawkeye_indicator in inset.patches
    assert len(inset._hawkeye_connectors) == 1
    uplt.close(fig)


def test_hawkeye_invalid_relation_raises() -> None:
    pytest.importorskip("cartopy.crs")

    fig, ax = uplt.subplots(proj="cyl")
    with pytest.raises(ValueError, match="relation must be"):
        ax[0].hawkeye((0.9, 0.9), size=0.2, relation="sideways")
    uplt.close(fig)
