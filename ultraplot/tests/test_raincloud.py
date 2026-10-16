"""Check raincloud geometry, data preservation, and component composition."""

import numpy as np
import pandas as pd
import pytest
from matplotlib.colors import to_rgba

import ultraplot as uplt


@pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
@pytest.mark.parametrize("side,direction", [("low", -1), ("high", 1)])
def test_raincloud_geometry(orientation, side, direction):
    data = [np.linspace(-2, 2, 11), np.linspace(0, 3, 17)]
    positions = [2.0, 5.0]
    fig, ax = uplt.subplots()
    result = ax.raincloud(
        data,
        positions=positions,
        labels=["A", "B"],
        orientation=orientation,
        side=side,
        seed=42,
        color="teal",
    )
    category = 0 if orientation == "vertical" else 1
    for i, values in enumerate(data):
        points = result["rain"][i].get_offsets()
        np.testing.assert_array_equal(points[:, 1 - category], values)
        centre = positions[i] - direction * 0.15
        assert np.all(np.abs(points[:, category] - centre) <= 0.08)
        vertices = result["cloud"][i].get_paths()[0].vertices[:, category]
        baseline = positions[i] + direction * 0.15
        assert np.all(direction * (vertices - baseline) >= -1e-12)
        median = result["box"][i]["medians"][0]
        median_values = median.get_ydata() if category == 0 else median.get_xdata()
        np.testing.assert_allclose(median_values, np.median(values))
        np.testing.assert_allclose(
            result["cloud"][i].get_facecolor()[0, :3], to_rgba("teal")[:3]
        )
        np.testing.assert_allclose(
            result["rain"][i].get_facecolor()[0, :3], to_rgba("teal")[:3]
        )
    ticks = ax.get_xticklabels() if category == 0 else ax.get_yticklabels()
    assert [tick.get_text() for tick in ticks] == ["A", "B"]
    fig.canvas.draw()


def test_raincloud_columns_and_cycle():
    data = pd.DataFrame({"Alpha": [1, 2, 3], "Beta": [2, 4, 8]})
    data.columns.name = "Condition"
    fig, ax = uplt.subplots()
    result = ax.raincloud(data, cycle=["red", "blue"])
    assert [tick.get_text() for tick in ax.get_xticklabels()] == ["Alpha", "Beta"]
    assert ax.get_xlabel() == "Condition"
    np.testing.assert_array_equal(result["rain"][0].get_offsets()[:, 1], data["Alpha"])
    for i, color in enumerate(["red", "blue"]):
        np.testing.assert_allclose(
            result["cloud"][i].get_facecolor()[0, :3], to_rgba(color)[:3]
        )
        np.testing.assert_allclose(
            ax.patches[i].get_facecolor()[:3], to_rgba(color)[:3]
        )


def test_raincloud_masks_empty_and_degenerate_groups():
    data = [
        np.ma.array([1.0, 999.0, 2.0, np.inf, np.nan], mask=[0, 1, 0, 0, 0]),
        [],
        [4.0],
        [5.0, 5.0, 5.0],
    ]
    fig, ax = uplt.subplots()
    with pytest.warns(UserWarning, match="Distribution 1.*skipping"):
        result = ax.raincloud(data, labels=["A", "Empty", "Single", "Constant"])
    np.testing.assert_array_equal(result["rain"][0].get_offsets()[:, 1], [1.0, 2.0])
    assert all(result[key][1] is None for key in result)
    assert result["rain"][2].get_offsets().shape == (1, 2)
    np.testing.assert_array_equal(ax.get_xticks(), [0, 1, 2, 3])
    fig.canvas.draw()


@pytest.mark.parametrize("component", ["cloud", "rain", "box"])
def test_raincloud_disabled_components(component):
    fig, ax = uplt.subplots()
    result = ax.raincloud(np.arange(5.0), **{component: False})
    assert result[component] == [None]
    assert all(result[key][0] is not None for key in result if key != component)


def test_raincloud_jitter_reproducible_without_global_rng():
    data = np.arange(12.0).reshape(6, 2)
    state = np.random.get_state()
    fig, axes = uplt.subplots(ncols=2)
    first = axes[0].raincloud(data, seed=24)
    second = axes[1].raincloud(data, seed=24)
    for a, b in zip(first["rain"], second["rain"]):
        np.testing.assert_array_equal(a.get_offsets(), b.get_offsets())
    after = np.random.get_state()
    assert state[0] == after[0]
    np.testing.assert_array_equal(state[1], after[1])
    assert state[2:] == after[2:]


def test_raincloud_component_styles_are_not_mutated():
    cloud_kw = {"alpha": 0.2, "widths": 0.8, "fillcolor": "red"}
    rain_kw = {"s": 35, "alpha": 0.7}
    box_kw = {"widths": 0.2, "showfliers": True}
    originals = [dict(kw) for kw in (cloud_kw, rain_kw, box_kw)]
    fig, ax = uplt.subplots()
    result = ax.raincloud(
        np.arange(8.0), cloud_kw=cloud_kw, rain_kw=rain_kw, box_kw=box_kw
    )
    assert [cloud_kw, rain_kw, box_kw] == originals
    assert result["cloud"][0].get_alpha() == 0.2
    np.testing.assert_allclose(
        result["cloud"][0].get_facecolor()[0, :3], to_rgba("red")[:3]
    )
    np.testing.assert_array_equal(result["rain"][0].get_sizes(), [35])


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"orientation": "diagonal"}, "orientation"),
        ({"side": "both"}, "side"),
        ({"jitter": -1}, "jitter"),
        ({"offset": np.inf}, "offset"),
        ({"labels": ["A", "B"]}, "labels"),
        ({"positions": [0, 1]}, "positions"),
        ({"positions": [np.nan]}, "positions"),
        ({"cloud": False, "rain": False, "box": False}, "At least one"),
        ({"cloud_kw": {"side": "low"}}, "layout"),
    ],
)
def test_raincloud_invalid_options(kwargs, match):
    fig, ax = uplt.subplots()
    with pytest.raises(ValueError, match=match):
        ax.raincloud(np.arange(5.0), **kwargs)
    assert not ax.collections and not ax.lines and not ax.patches


@pytest.mark.parametrize("data", [[], [[], []], [np.nan, np.inf]])
def test_raincloud_no_observations(data):
    fig, ax = uplt.subplots()
    with pytest.raises(ValueError, match="No finite observations"):
        ax.raincloud(data)
