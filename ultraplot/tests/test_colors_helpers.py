#!/usr/bin/env python3
"""
Focused tests for colormap and normalization helpers.
"""

from __future__ import annotations

import numpy as np
import numpy.ma as ma
import pytest
import matplotlib as mpl
import matplotlib.cm as mcm
import matplotlib.colors as mcolors

from ultraplot import colors as pcolors
from ultraplot import config
from ultraplot.internals.warnings import UltraPlotWarning


@pytest.fixture(autouse=True)
def reset_color_databases():
    pcolors._cmap_database = pcolors._init_cmap_database()
    config.register_cmaps(default=True)
    config.register_cycles(default=True)
    yield


def test_clip_colors_and_channels_warn_and_offset():
    colors = np.array([[-0.1, 0.5, 1.2], [0.1, 1.5, 0.2]])
    clipped = pcolors._clip_colors(colors.copy(), clip=True)
    assert np.all((0 <= clipped) & (clipped <= 1))

    grayed = pcolors._clip_colors(colors.copy(), clip=False, gray=0.3)
    assert np.isclose(grayed[0, 0], 0.3)
    assert np.isclose(grayed[0, 2], 0.3)

    with pytest.warns(UltraPlotWarning, match="channel"):
        pcolors._clip_colors(colors.copy(), clip=True, warn=True)

    assert pcolors._get_channel(lambda value: value, "hue") is not None
    assert pcolors._get_channel(0.5, "hue") == 0.5
    assert pcolors._get_channel("red+0.2", "luminance") == pytest.approx(
        pcolors.to_xyz("red", "hcl")[2] + 0.2
    )
    with pytest.raises(ValueError, match="Unknown channel"):
        pcolors._get_channel("red", "bad")


def test_make_segment_data_lookup_tables_and_sanitize_levels():
    callable_data = pcolors._make_segment_data(lambda x: x)
    assert callable(callable_data)

    assert pcolors._make_segment_data([0.2]) == [(0, 0.2, 0.2), (1, 0.2, 0.2)]
    assert pcolors._make_segment_data([0.0, 1.0], ratios=[2]) == [
        (0.0, 0.0, 0.0),
        (1.0, 1.0, 1.0),
    ]
    with pytest.warns(UltraPlotWarning, match="ignoring ratios"):
        data = pcolors._make_segment_data([0.0, 1.0], coords=[0, 1], ratios=[1])
    assert data == [(0, 0.0, 0.0), (1, 1.0, 1.0)]
    with pytest.raises(ValueError, match="Coordinates must range from 0 to 1"):
        pcolors._make_segment_data([0.0, 1.0], coords=[0.1, 1.0])
    with pytest.raises(ValueError, match="ratios"):
        pcolors._make_segment_data([0.0, 0.5, 1.0], ratios=[1])

    lookup = pcolors._make_lookup_table(5, [(0, 0, 0), (1, 1, 1)], gamma=2)
    assert lookup.shape == (5,)
    assert lookup[0] == pytest.approx(0)
    assert lookup[-1] == pytest.approx(1)

    inverse_lookup = pcolors._make_lookup_table(
        5, [(0, 0, 0), (1, 1, 1)], gamma=2, inverse=True
    )
    assert inverse_lookup.shape == (5,)

    functional_lookup = pcolors._make_lookup_table(4, lambda values: values**2, gamma=1)
    assert np.allclose(functional_lookup, np.linspace(0, 1, 4) ** 2)

    with pytest.raises(ValueError, match="Gamma can only be in range"):
        pcolors._make_lookup_table(4, [(0, 0, 0), (1, 1, 1)], gamma=0.001)
    with pytest.raises(ValueError, match="Only one gamma allowed"):
        pcolors._make_lookup_table(4, lambda values: values, gamma=[1, 2])

    ascending, descending = pcolors._sanitize_levels([1, 2, 3])
    assert np.array_equal(ascending, np.array([1, 2, 3]))
    assert descending is False
    reversed_levels, descending_flag = pcolors._sanitize_levels([3, 2, 1])
    assert np.array_equal(reversed_levels, np.array([1, 2, 3]))
    assert descending_flag is True
    with pytest.raises(ValueError, match="size >= 2"):
        pcolors._sanitize_levels([1])
    with pytest.raises(ValueError, match="must be monotonic"):
        pcolors._sanitize_levels([1, 3, 2])


def test_interpolation_and_norm_helpers_cover_edge_cases():
    assert pcolors._interpolate_scalar(0.5, 0, 1, 10, 20) == pytest.approx(15)

    xq = ma.masked_array([-1.0, 0.5, 2.0], mask=[False, False, True])
    yq = pcolors._interpolate_extrapolate_vector(xq, [0, 1], [10, 20])
    assert np.allclose(yq[:2], [0, 15])
    assert yq.mask.tolist() == [False, False, True]

    norm = pcolors.DiscreteNorm([3, 2, 1], unique="both", step=0.5, clip=True)
    values = norm(np.array([1.0, 2.0, 3.0]))
    assert float(np.min(values)) >= 0.0
    assert float(np.max(values)) <= 1.0 + 1e-9
    assert norm.descending is True
    with pytest.raises(ValueError, match="not invertible"):
        norm.inverse([0.5])
    with pytest.raises(ValueError, match="BoundaryNorm"):
        pcolors.DiscreteNorm([1, 2, 3], norm=mcolors.BoundaryNorm([1, 2, 3], 2))
    with pytest.raises(ValueError, match="Normalize"):
        pcolors.DiscreteNorm([1, 2, 3], norm="bad")
    with pytest.raises(ValueError, match="Unknown unique setting"):
        pcolors.DiscreteNorm([1, 2, 3], unique="bad")

    segmented = pcolors.SegmentedNorm([1, 2, 4], clip=True)
    transformed = segmented(np.array([1.0, 2.0, 4.0]))
    assert np.allclose(transformed, [0.0, 0.5, 1.0])
    assert np.allclose(segmented.inverse(transformed), [1.0, 2.0, 4.0])

    diverging = pcolors.DivergingNorm(vcenter=0, vmin=-2, vmax=4, fair=False)
    assert np.isclose(diverging(-2), 0.0)
    assert np.isclose(diverging(0), 0.5)
    assert np.isclose(diverging(4), 1.0)
    autoscaled = pcolors.DivergingNorm(vcenter=0)
    autoscaled.autoscale_None(np.array([2.0, 3.0]))
    assert autoscaled.vmin == 0
    assert autoscaled.vmax == 3
    adjusted = pcolors.DivergingNorm(vcenter=0, vmin=2, vmax=1)
    assert np.isfinite(adjusted(0.5))
    assert adjusted.vmin == 0
    assert adjusted.vmax == 1


def test_cmap_translation_type_checks_and_color_cache_helpers():
    with pytest.raises(RuntimeError, match="Invalid subtype"):
        pcolors._get_cmap_subtype("viridis", "bad")
    with pytest.raises(ValueError, match="Invalid discrete colormap name"):
        pcolors._get_cmap_subtype("viridis", "discrete")

    listed = mcolors.ListedColormap(["red", "blue"], name="listed_small")
    translated_listed = pcolors._translate_cmap(listed, listedthresh=10)
    assert isinstance(translated_listed, pcolors.DiscreteColormap)

    dense = mcolors.ListedColormap(
        np.linspace(0, 1, 20)[:, None].repeat(3, axis=1), name="listed_dense"
    )
    translated_dense = pcolors._translate_cmap(dense, listedthresh=5)
    assert isinstance(translated_dense, pcolors.ContinuousColormap)

    segment_data = {
        "red": [(0, 0, 0), (1, 1, 1)],
        "green": [(0, 0, 0), (1, 1, 1)],
        "blue": [(0, 0, 0), (1, 1, 1)],
    }
    translated_segmented = pcolors._translate_cmap(
        mcolors.LinearSegmentedColormap("seg", segment_data)
    )
    assert isinstance(translated_segmented, pcolors.ContinuousColormap)

    base = mcolors.Colormap("base")
    assert pcolors._translate_cmap(base) is base
    with pytest.raises(ValueError, match="Invalid colormap type"):
        pcolors._translate_cmap("bad")

    discrete = pcolors.DiscreteColormap(["red", "blue"], name="helper_cycle")
    pcolors._cmap_database.register(discrete)
    cache = pcolors._ColorCache()
    cycle_rgba = cache._get_rgba(("helper_cycle", 1), None)
    assert cycle_rgba[-1] == 1
    with pytest.raises(ValueError, match="must be between 0 and 1"):
        cache._get_rgba(("viridis", 2), None)
    with pytest.raises(ValueError, match="must be between 0 and 1"):
        cache._get_rgba(("helper_cycle", 3), None)
    with pytest.raises(KeyError):
        cache._get_rgba(("not-a-cmap", 0.2), None)
