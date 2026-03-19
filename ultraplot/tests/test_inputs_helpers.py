#!/usr/bin/env python3
"""
Focused tests for plotting input helpers.
"""

from __future__ import annotations

import numpy as np
import pytest
import matplotlib.tri as mtri

from ultraplot.internals import inputs
from ultraplot.internals.warnings import UltraPlotWarning


def test_basic_type_and_array_helpers():
    assert inputs._is_numeric([1, 2, 3]) is True
    assert inputs._is_numeric(["a", "b"]) is False
    assert inputs._is_categorical(["a", "b"]) is True
    assert inputs._is_categorical([1, 2]) is False
    assert inputs._is_descending(np.array([3, 2, 1])) is True
    assert inputs._is_descending(np.array([[3, 2], [1, 0]])) is False

    with pytest.raises(ValueError, match="Invalid data None"):
        inputs._to_duck_array(None)

    masked, units = inputs._to_masked_array(np.array([1, np.nan, 3]))
    assert units is None
    assert np.ma.isMaskedArray(masked)
    assert masked.mask.tolist() == [False, True, False]

    masked_ints, _ = inputs._to_masked_array(np.array([1, 2, 3], dtype=int))
    assert masked_ints.dtype == np.float64


def test_coordinate_conversion_helpers():
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 1.0, 2.0])
    z = np.arange(9.0).reshape(3, 3)
    x_edges, y_edges = inputs._to_edges(x, y, z)
    assert x_edges.shape == (4,)
    assert y_edges.shape == (4,)

    z_small = np.arange(4.0).reshape(2, 2)
    x_centers, y_centers = inputs._to_centers(x, y, z_small)
    assert x_centers.shape == (2,)
    assert y_centers.shape == (2,)

    x2 = np.array([[0.0, 1.0], [0.0, 1.0]])
    y2 = np.array([[0.0, 0.0], [1.0, 1.0]])
    z2 = np.arange(4.0).reshape(2, 2)
    x2_edges, y2_edges = inputs._to_edges(x2, y2, z2)
    assert x2_edges.shape == (3, 3)
    assert y2_edges.shape == (3, 3)

    with pytest.raises(ValueError, match="must match array centers"):
        inputs._to_edges(np.array([0.0, 1.0]), np.array([0.0, 1.0]), np.ones((3, 3)))
    with pytest.raises(ValueError, match="must match z centers"):
        inputs._to_centers(np.array([0.0, 1.0]), np.array([0.0, 1.0]), np.ones((3, 3)))


def test_from_data_and_triangulation_helpers():
    data = {"x": np.array([1, 2, 3]), "y": np.array([4, 5, 6])}
    converted = inputs._from_data(data, "x", "missing", "y")
    assert np.array_equal(converted[0], data["x"])
    assert converted[1] == "missing"
    assert np.array_equal(converted[2], data["y"])
    assert inputs._from_data(data, "missing") == "missing"
    assert inputs._from_data(None, "x") is None

    triangulation = mtri.Triangulation([0, 1, 0], [0, 0, 1])
    tri, z, args, kwargs = inputs._parse_triangulation_inputs(triangulation, [1, 2, 3])
    assert tri is triangulation
    assert z == [1, 2, 3]
    assert args == []
    assert kwargs == {}

    with pytest.raises(ValueError, match="No z values provided"):
        inputs._parse_triangulation_inputs(triangulation)


def test_distribution_helpers_cover_clean_reduce_and_ranges():
    object_array = np.array([[1, 2], [3]], dtype=object)
    cleaned = inputs._dist_clean(object_array)
    assert len(cleaned) == 2
    assert np.allclose(cleaned[0], [1.0, 2.0])

    numeric_cleaned = inputs._dist_clean(np.array([[1.0, np.nan], [2.0, 3.0]]))
    assert len(numeric_cleaned) == 2
    assert np.allclose(numeric_cleaned[0], [1.0, 2.0])

    list_cleaned = inputs._dist_clean([[1, 2], [], [3]])
    assert len(list_cleaned) == 2
    with pytest.raises(ValueError, match="numpy array or a list of lists"):
        inputs._dist_clean("bad")

    data = np.array([[1.0, 3.0], [2.0, 4.0]])
    with pytest.warns(
        UltraPlotWarning, match="Cannot have both means=True and medians=True"
    ):
        reduced, kwargs = inputs._dist_reduce(data, means=True, medians=True)
    assert np.allclose(reduced, [1.5, 3.5])
    assert "distribution" in kwargs

    with pytest.raises(ValueError, match="Expected 2D array"):
        inputs._dist_reduce(np.array([1.0, 2.0]), means=True)

    distribution = np.array([[1.0, 2.0], [3.0, 4.0]])
    err, label = inputs._dist_range(
        np.array([2.0, 3.0]),
        distribution,
        stds=[-1, 1],
        pctiles=[10, 90],
        label=True,
    )
    assert err.shape == (2, 2)
    assert label == "1$\\sigma$ range"

    err_abs, label_abs = inputs._dist_range(
        np.array([2.0, 3.0]),
        None,
        errdata=np.array([0.5, 0.25]),
        absolute=True,
        label=True,
    )
    assert np.allclose(err_abs[0], [1.5, 2.75])
    assert label_abs == "uncertainty"

    with pytest.raises(ValueError, match="must pass means=True or medians=True"):
        inputs._dist_range(np.array([1.0]), None, stds=1)
    with pytest.raises(
        ValueError, match="Passing both 2D data coordinates and 'errdata'"
    ):
        inputs._dist_range(np.ones((2, 2)), None, errdata=np.ones(2))


def test_mask_range_and_metadata_helpers():
    masked = inputs._safe_mask(np.array([True, False, True]), np.array([1.0, 2.0, 3.0]))
    assert np.isnan(masked[1])
    with pytest.raises(ValueError, match="incompatible with array shape"):
        inputs._safe_mask(np.array([True, False]), np.array([1.0, 2.0, 3.0]))

    lo, hi = inputs._safe_range(np.array([1.0, np.nan, 5.0]), lo=0, hi=100)
    assert lo == 1.0
    assert hi == 5.0

    coords, kwargs = inputs._meta_coords(np.array(["a", "b"]), which="x")
    assert np.array_equal(coords, np.array([0, 1]))
    assert {"xlocator", "xformatter", "xminorlocator"} <= set(kwargs)
    numeric_coords, kwargs_numeric = inputs._meta_coords(
        np.array([1.0, 2.0]), which="y"
    )
    assert np.array_equal(numeric_coords, np.array([1.0, 2.0]))
    assert kwargs_numeric == {}
    with pytest.raises(ValueError, match="Non-1D string coordinate input"):
        inputs._meta_coords(np.array([["a", "b"]]), which="x")

    assert np.array_equal(
        inputs._meta_labels(np.array([1, 2, 3]), axis=0), np.array([0, 1, 2])
    )
    assert np.array_equal(
        inputs._meta_labels(np.array([1, 2, 3]), axis=1), np.array([0])
    )
    assert inputs._meta_labels(np.array([1, 2, 3]), axis=2, always=False) is None
    with pytest.raises(ValueError, match="Invalid axis"):
        inputs._meta_labels(np.array([1, 2, 3]), axis=3)

    assert inputs._meta_title(np.array([1, 2, 3])) is None
    assert inputs._meta_units(np.array([1, 2, 3])) is None


def test_geographic_helpers_cover_clipping_bounds_and_globes():
    clipped = inputs._geo_clip(np.array([-100.0, 0.0, 100.0]))
    assert np.allclose(clipped, [-90.0, 0.0, 90.0])

    x = np.array([0.0, 180.0, 540.0])
    y = np.array([1.0, 2.0, 3.0])
    rolled_x, rolled_y = inputs._geo_inbounds(x, y, xmin=-180, xmax=180)
    assert np.array_equal(rolled_x, np.array([180.0, 0.0, 180.0]))
    assert np.array_equal(rolled_y, np.array([3.0, 1.0, 2.0]))

    xg = np.array([0.0, 180.0])
    yg = np.array([-45.0, 45.0])
    zg = np.array([[1.0, 2.0], [3.0, 4.0]])
    globe_x, globe_y, globe_z = inputs._geo_globe(xg, yg, zg, modulo=True)
    assert globe_x.shape[0] == 3
    assert globe_y.shape[0] == 4
    assert globe_z.shape == (4, 3)

    seam_x, seam_y, seam_z = inputs._geo_globe(xg, yg, zg, xmin=-180, modulo=False)
    assert seam_x.shape[0] == 4
    assert seam_y.shape[0] == 4
    assert seam_z.shape == (4, 4)

    with pytest.raises(ValueError, match="Unexpected shapes"):
        inputs._geo_globe(np.array([0.0, 1.0, 2.0, 3.0]), yg, zg, modulo=False)
