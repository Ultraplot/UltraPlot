import pytest

import ultraplot as uplt
from ultraplot.gridspec import SubplotGrid


def test_grid_has_dynamic_methods():
    """
    Check that we can apply the methods to a SubplotGrid object.
    """
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    for method in ("altx", "dualx", "twinx", "panel"):
        assert hasattr(axs, method)
        assert callable(getattr(axs, method))
        args = []
        if method == "dualx":
            # needs function argument
            args = ["linear"]
        subplotgrid = getattr(axs, method)(*args)
        assert isinstance(subplotgrid, SubplotGrid)
        assert len(subplotgrid) == 2


def test_altx_calls_all_axes_methods():
    """
    Check the return types of newly added methods such as altx, dualx, and twinx.
    """
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    result = axs.altx()
    assert isinstance(result, SubplotGrid)
    assert len(result) == 2
    for ax in result:
        assert isinstance(ax, uplt.axes.Axes)


def test_missing_command_is_skipped_gracefully():
    """For missing commands, we should raise an error."""
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    # Pretend we have a method that doesn't exist on these axes
    with pytest.raises(AttributeError):
        axs.nonexistent()


def test_docstring_injection():
    """
    @_apply_to_all should inject the docstring
    """
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    doc = axs.altx.__doc__
    assert "for every axes in the grid" in doc
    assert "Returns" in doc


def test_subplot_repr():
    """
    Panels don't have a subplotspec, so they return "unknown" in their repr, but normal subplots should
    """
    fig, ax = uplt.subplots()
    panel = ax.panel("r")
    assert panel.get_subplotspec().__repr__() == "SubplotSpec(unknown)"
    assert (
        ax[0].get_subplotspec().__repr__()
        == "SubplotSpec(nrows=1, ncols=1, index=(0, 0))"
    )


def test_tight_layout_disabled():
    """
    Some methods are disabled in gridspec, such as tight_layout.
    This should raise a RuntimeErrror when called on a SubplotGrid.
    """
    fig, ax = uplt.subplots()
    gs = ax.get_subplotspec().get_gridspec()
    with pytest.raises(RuntimeError):
        gs.tight_layout(fig)


def test_gridspec_slicing():
    """
    Test various slicing methods on SubplotGrid, including 1D list/array indexing.
    """
    import numpy as np

    fig, axs = uplt.subplots(nrows=4, ncols=4)

    # Test 1D integer indexing
    assert axs[0].number == 1
    assert axs[15].number == 16

    # Test 1D slice indexing
    subset = axs[0:2]
    assert isinstance(subset, SubplotGrid)
    assert len(subset) == 2
    assert subset[0].number == 1
    assert subset[1].number == 2

    # Test 1D list indexing (Fix #1)
    subset_list = axs[[0, 5]]
    assert isinstance(subset_list, SubplotGrid)
    assert len(subset_list) == 2
    assert subset_list[0].number == 1
    assert subset_list[1].number == 6

    # Test 1D array indexing
    subset_array = axs[np.array([0, 5])]
    assert isinstance(subset_array, SubplotGrid)
    assert len(subset_array) == 2
    assert subset_array[0].number == 1
    assert subset_array[1].number == 6

    # Test 2D slicing (tuple of slices)
    # axs[0:2, :] -> Rows 0 and 1, all cols
    subset_2d = axs[0:2, :]
    assert isinstance(subset_2d, SubplotGrid)
    # 2 rows * 4 cols = 8 axes
    assert len(subset_2d) == 8

    # Test 2D mixed slicing (list in one dim) (Fix #2 related to _encode_indices)
    # axs[[0, 1], :] -> Row indices 0 and 1, all cols
    subset_mixed = axs[[0, 1], :]
    assert isinstance(subset_mixed, SubplotGrid)
    assert len(subset_mixed) == 8

    # Verify content
    # subset_mixed[0] -> Row 0, Col 0 -> Number 1
    # subset_mixed[4] -> Row 1, Col 0 -> Number 5 (since 4 cols per row)
    assert subset_mixed[0].number == 1
    assert subset_mixed[4].number == 5
