"""
Tests for SubplotManager (ultraplot._subplots).
"""

import matplotlib.projections as mproj
import numpy as np
import pytest

import ultraplot as uplt
from ultraplot import gridspec as pgridspec
from ultraplot._subplots import SubplotManager
from ultraplot.axes.container import ExternalAxesContainer


def test_gridspec_setter_rejects_non_ultraplot():
    """Setting gridspec to a non-ultraplot GridSpec raises ValueError."""
    fig = uplt.figure()
    with pytest.raises(ValueError, match="ultraplot.GridSpec"):
        fig.gridspec = "not a gridspec"


def test_gridspec_setter_accepts_ultraplot():
    """Setting gridspec to an ultraplot GridSpec works."""
    fig = uplt.figure()
    gs = pgridspec.GridSpec(2, 2)
    fig.gridspec = gs
    assert fig.gridspec is gs
    uplt.close(fig)


def test_parse_backend_basemap_warns():
    """parse_backend emits a deprecation warning for basemap."""
    with pytest.warns(match="basemap"):
        SubplotManager.parse_backend(backend="basemap")


def test_parse_backend_passthrough():
    """parse_backend returns backend unchanged for non-basemap values."""
    assert SubplotManager.parse_backend(backend="cartopy") == "cartopy"
    assert SubplotManager.parse_backend(backend=None) is None


def test_add_subplot_integer_arg():
    """add_subplot(111) creates a single subplot."""
    fig = uplt.figure()
    ax = fig.add_subplot(111)
    assert ax is not None
    assert ax.number == 1
    uplt.close(fig)


def test_add_subplot_integer_arg_invalid():
    """add_subplot with out-of-range integer raises ValueError."""
    fig = uplt.figure()
    with pytest.raises(ValueError, match="must fall between 111 and 999"):
        fig.add_subplot(10)
    uplt.close(fig)


def test_add_subplot_row_mismatch():
    """Rows that don't divide the gridspec raise ValueError."""
    fig = uplt.figure()
    fig.gridspec = pgridspec.GridSpec(3, 3)
    with pytest.raises(ValueError, match="does not divide"):
        fig.add_subplot(2, 2, 1)
    uplt.close(fig)


def test_add_subplot_col_mismatch():
    """Columns that don't divide the gridspec raise ValueError."""
    fig = uplt.figure()
    fig.gridspec = pgridspec.GridSpec(4, 3)
    with pytest.raises(ValueError, match="does not divide"):
        fig.add_subplot(2, 2, 1)
    uplt.close(fig)


def test_add_subplot_index_out_of_range():
    """Subplot index beyond nrows*ncols raises ValueError."""
    fig = uplt.figure()
    with pytest.raises(ValueError, match="must fall between"):
        fig.add_subplot(2, 2, 5)
    uplt.close(fig)


def test_add_subplot_invalid_args():
    """Unrecognized positional args raise ValueError."""
    fig = uplt.figure()
    with pytest.raises(ValueError, match="Invalid add_subplot"):
        fig.add_subplot("bad", "args")
    uplt.close(fig)


def test_add_subplot_non_ultraplot_gridspec_raises():
    """SubplotSpec from a plain matplotlib GridSpec is rejected."""
    import matplotlib.gridspec as mgridspec

    fig = uplt.figure()
    mpl_gs = mgridspec.GridSpec(2, 2)
    ss = mpl_gs[0, 0]
    with pytest.raises(ValueError, match="ultraplot.GridSpec"):
        fig.add_subplot(ss)
    uplt.close(fig)


def test_add_subplot_wrong_gridspec_raises():
    """SubplotSpec from a different GridSpec than the figure's raises."""
    fig = uplt.figure()
    gs1 = pgridspec.GridSpec(2, 2)
    gs2 = pgridspec.GridSpec(3, 3)
    fig.gridspec = gs1
    ss = gs2[0, 0]
    with pytest.raises(ValueError, match="active figure gridspec"):
        fig.add_subplot(ss)
    uplt.close(fig)


def test_add_subplot_with_subplotspec():
    """add_subplot accepts an ultraplot SubplotSpec directly."""
    fig = uplt.figure()
    gs = pgridspec.GridSpec(2, 2)
    ss = gs[0, 0]
    ax = fig.add_subplot(ss)
    assert ax.number == 1
    uplt.close(fig)


def test_add_subplot_3d_projection():
    """'3d' resolves to the native ultraplot ThreeAxes, not a container."""
    fig = uplt.figure()
    ax = fig.add_subplot(111, proj="3d")
    assert ax.number == 1
    assert isinstance(ax, uplt.axes.ThreeAxes)
    uplt.close(fig)


def test_parse_proj_invalid_name():
    """Invalid projection name raises a helpful ValueError."""
    fig = uplt.figure()
    with pytest.raises(ValueError, match="Invalid projection"):
        fig.add_subplot(111, proj="totally_nonexistent_proj_xyz")
    uplt.close(fig)


def test_add_subplots_invalid_order():
    """Invalid order raises ValueError."""
    fig = uplt.figure()
    with pytest.raises(ValueError, match="Invalid order"):
        fig.add_subplots(nrows=2, ncols=2, order="Z")
    uplt.close(fig)


def test_add_subplots_fortran_order():
    """Fortran order ('F') numbers subplots column-major."""
    fig = uplt.figure()
    axs = fig.add_subplots(nrows=2, ncols=2, order="F")
    assert len(axs) == 4
    # Column-major numbering puts subplot 2 below subplot 1 rather than beside it
    rows = [ax.get_subplotspec().rowspan.start for ax in axs]
    cols = [ax.get_subplotspec().colspan.start for ax in axs]
    assert rows == [0, 1, 0, 1]
    assert cols == [0, 0, 1, 1]
    uplt.close(fig)


def test_add_subplots_1d_array_fortran():
    """1D array with order='F' creates a column layout."""
    fig = uplt.figure()
    axs = fig.add_subplots(array=[1, 2, 3], order="F")
    assert len(axs) == 3
    assert fig.gridspec.get_geometry() == (3, 1)
    uplt.close(fig)


def test_add_subplots_3d_array_raises():
    """3D+ array raises ValueError."""
    fig = uplt.figure()
    with pytest.raises(ValueError, match="1D or 2D"):
        fig.add_subplots(array=np.ones((2, 2, 2), dtype=int))
    uplt.close(fig)


def test_add_subplots_negative_indices_raises():
    """Negative indices in the array raise ValueError."""
    fig = uplt.figure()
    with pytest.raises(ValueError, match="positive integers"):
        fig.add_subplots(array=[[-1, 1], [2, 3]])
    uplt.close(fig)


def test_add_subplots_gridspec_kw_warns():
    """Passing gridspec_kw emits a deprecation warning."""
    fig = uplt.figure()
    with pytest.warns(match="gridspec_kw"):
        fig.add_subplots(nrows=1, ncols=2, gridspec_kw={"wspace": 1})
    uplt.close(fig)


def test_add_subplots_subplot_kw_warns():
    """Passing subplot_kw emits a deprecation warning."""
    fig = uplt.figure()
    with pytest.warns(match="subplot_kw"):
        fig.add_subplots(nrows=1, ncols=2, subplot_kw={"facecolor": "red"})
    uplt.close(fig)


def test_add_subplots_per_axes_proj():
    """Per-axes projection as a dict selects different projections."""
    fig = uplt.figure()
    axs = fig.add_subplots(
        nrows=1,
        ncols=2,
        proj={1: "cartesian", 2: "polar"},
    )
    assert isinstance(axs[0], uplt.axes.CartesianAxes)
    assert isinstance(axs[1], uplt.axes.PolarAxes)
    uplt.close(fig)


def test_add_subplots_proj_as_list():
    """Per-axes projection as a list works."""
    fig = uplt.figure()
    axs = fig.add_subplots(
        nrows=1,
        ncols=2,
        proj=["cartesian", "polar"],
    )
    assert isinstance(axs[0], uplt.axes.CartesianAxes)
    assert isinstance(axs[1], uplt.axes.PolarAxes)
    uplt.close(fig)


def test_add_subplots_none_placeholder():
    """None in the array is treated as an empty slot."""
    fig = uplt.figure()
    axs = fig.add_subplots(array=[[1, None], [2, 3]])
    assert len(axs) == 3
    assert fig.gridspec.get_geometry() == (2, 2)
    # The empty slot means subplot 1 spans only the top-left cell
    assert axs[0].get_subplotspec().colspan.stop == 1
    uplt.close(fig)


def test_subplotgrid_sorted_by_number():
    """subplotgrid returns subplots sorted by number."""
    fig = uplt.figure()
    gs = pgridspec.GridSpec(1, 3)
    # Add out of order to prove subplotgrid sorts rather than preserving insertion
    fig.add_subplot(gs[0, 2], number=3)
    fig.add_subplot(gs[0, 0], number=1)
    fig.add_subplot(gs[0, 1], number=2)
    assert [ax.number for ax in fig.subplotgrid] == [1, 2, 3]
    uplt.close(fig)


def test_get_subplot_returns_correct_axes():
    """_get_subplot returns the axes with the given number."""
    fig, axs = uplt.subplots(nrows=1, ncols=3)
    for i in range(1, 4):
        ax = fig._get_subplot(i)
        assert ax is not None
        assert ax.number == i
    uplt.close(fig)


def test_get_subplot_missing_returns_none():
    """_get_subplot returns None for a nonexistent number."""
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    assert fig._get_subplot(999) is None
    uplt.close(fig)


def test_iter_subplots_yields_all():
    """_iter_subplots yields all numbered subplots."""
    fig, axs = uplt.subplots(nrows=2, ncols=2)
    count = sum(1 for _ in fig._iter_subplots())
    assert count == 4
    uplt.close(fig)


def test_parse_proj_polar():
    """'polar' is found via matplotlib's projection registry."""
    fig = uplt.figure()
    ax = fig.add_subplot(111, proj="polar")
    assert isinstance(ax, uplt.axes.PolarAxes)
    uplt.close(fig)


def test_add_subplots_proj_kw_mixed_nested_raises():
    """Mixed nested/flat proj_kw dicts raise ValueError."""
    fig = uplt.figure()
    with pytest.raises(ValueError):
        fig.add_subplots(
            nrows=1,
            ncols=2,
            proj_kw={1: {"key": "val"}, 2: "not_a_dict"},
        )
    uplt.close(fig)


def test_add_subplots_proj_dict_wrong_keys_raises():
    """proj dict with wrong axes numbers raises ValueError."""
    fig = uplt.figure()
    with pytest.raises(ValueError, match="Have 2 axes"):
        fig.add_subplots(
            nrows=1,
            ncols=2,
            proj={1: "cartesian", 2: "cartesian", 3: "polar"},
        )
    uplt.close(fig)


def test_add_subplot_external_projection_wrapped():
    """
    Non-ultraplot projections get wrapped in a container.

    NOTE: Use 'mollweide' rather than e.g. 'hammer'. Names that cartopy also
    knows resolve to a GeoAxes when cartopy is installed, so the projection
    used here must be one only matplotlib provides.
    """
    fig = uplt.figure()
    ax = fig.add_subplot(111, proj="mollweide")
    assert isinstance(ax, ExternalAxesContainer)
    assert "_ultraplot_container_mollweide" in mproj.get_projection_names()
    uplt.close(fig)


def test_add_subplot_external_projection_reuses_container():
    """Calling add_subplot twice with same external projection reuses container."""
    fig = uplt.figure()
    gs = pgridspec.GridSpec(1, 2)
    ax1 = fig.add_subplot(gs[0, 0], proj="mollweide")
    ax2 = fig.add_subplot(gs[0, 1], proj="mollweide")
    # The container class is registered once and shared, not rebuilt per subplot
    assert type(ax1) is type(ax2)
    assert isinstance(ax1, ExternalAxesContainer)
    uplt.close(fig)


@pytest.mark.parametrize("key", ["proj", "projection"])
def test_ui_subplot_routes_projection_kwargs(key):
    """
    ``uplt.subplot`` must route projection keywords to the subplot, not the figure.

    ``ui.subplot`` introspects the signature of ``Figure._parse_proj`` to split
    figure keywords from subplot keywords, so collapsing that signature into
    ``**kwargs`` silently sends ``proj`` to ``Figure.set()``.
    """
    fig, ax = uplt.subplot(**{key: "polar"})
    assert isinstance(ax, uplt.axes.PolarAxes)
    uplt.close(fig)


def test_ui_subplot_routes_proj_kw():
    """``uplt.subplot`` routes proj_kw to the subplot alongside proj."""
    fig, ax = uplt.subplot(proj="polar", proj_kw={})
    assert isinstance(ax, uplt.axes.PolarAxes)
    uplt.close(fig)


def test_ui_subplots_routes_projection_kwargs():
    """``uplt.subplots`` routes projection keywords to the subplots."""
    fig, axs = uplt.subplots(nrows=1, ncols=2, proj="polar")
    assert all(isinstance(ax, uplt.axes.PolarAxes) for ax in axs)
    uplt.close(fig)
