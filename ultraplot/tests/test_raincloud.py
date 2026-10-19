"""Check raincloud geometry, data preservation, and component composition."""

import warnings

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
    "alias", ["s", "ms", "markersize", "markersizes", "size", "sizes"]
)
def test_raincloud_scatter_size_aliases(alias):
    fig, ax = uplt.subplots()
    style = {alias: 35}
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        result = ax.raincloud(np.arange(8.0), rain_kw=style)
    np.testing.assert_array_equal(result["rain"][0].get_sizes(), [35])
    assert style == {alias: 35}


@pytest.mark.parametrize(
    "alias", ["lw", "linewidth", "linewidths", "mew", "markeredgewidth"]
)
def test_raincloud_scatter_linewidth_aliases(alias):
    fig, ax = uplt.subplots()
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        result = ax.raincloud(np.arange(8.0), rain_kw={alias: 2})
    np.testing.assert_array_equal(result["rain"][0].get_linewidths(), [2])


@pytest.mark.parametrize(
    "alias", ["c", "color", "colors", "fc", "facecolor", "facecolors", "mfc"]
)
def test_raincloud_scatter_colour_aliases(alias):
    fig, ax = uplt.subplots()
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        result = ax.raincloud(np.arange(8.0), rain_kw={alias: "red"})
    np.testing.assert_allclose(
        result["rain"][0].get_facecolor()[0, :3], to_rgba("red")[:3]
    )


def test_raincloud_scatter_artist_aliases():
    fig, ax = uplt.subplots()
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        result = ax.raincloud(np.arange(8.0), rain_kw={"a": 0.2, "z": 6, "ec": "navy"})
    artist = result["rain"][0]
    assert artist.get_alpha() == 0.2
    assert artist.get_zorder() == 6
    np.testing.assert_allclose(artist.get_edgecolor()[0], to_rgba("navy", alpha=0.2))


@pytest.mark.parametrize("component", ["cloud", "box"])
@pytest.mark.parametrize(
    "aliases",
    [
        {"fc": "red", "ec": "navy", "lw": 2, "a": 0.2, "z": 6},
        {
            "fillcolor": "red",
            "edgecolors": "navy",
            "linewidths": 2,
            "fillalpha": 0.2,
            "zorders": 6,
        },
    ],
)
def test_raincloud_patch_style_aliases(component, aliases):
    fig, ax = uplt.subplots()
    original = dict(aliases)
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        result = ax.raincloud(np.arange(8.0), **{component + "_kw": aliases})
    assert aliases == original
    artist = result[component][0] if component == "cloud" else ax.patches[0]
    np.testing.assert_allclose(
        np.asarray(artist.get_facecolor()).reshape(-1, 4)[0], to_rgba("red", alpha=0.2)
    )
    if component == "box":
        artist = result[component][0]["boxes"][0]
        np.testing.assert_allclose(to_rgba(artist.get_color()), to_rgba("navy"))
    else:
        np.testing.assert_allclose(
            artist.get_edgecolor()[0], to_rgba("navy", alpha=0.2)
        )
    np.testing.assert_allclose(artist.get_linewidth(), 2)
    assert artist.get_zorder() == 6


@pytest.mark.parametrize("component", ["cloud", "box"])
def test_raincloud_patch_generic_colour(component):
    fig, ax = uplt.subplots()
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        result = ax.raincloud(np.arange(8.0), **{component + "_kw": {"c": "red"}})
    artist = result[component][0] if component == "cloud" else ax.patches[0]
    np.testing.assert_allclose(
        np.asarray(artist.get_facecolor()).reshape(-1, 4)[0, :3], to_rgba("red")[:3]
    )


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


@pytest.mark.parametrize("keyword", [False, True])
def test_raincloud_data_lookup_and_keyword_input(keyword):
    frame = pd.DataFrame({"A": [1, 2, 3], "B": [2, 4, 5]})
    frame.columns.name = "Condition"
    fig, ax = uplt.subplots()
    result = (
        ax.raincloud(data=frame)
        if keyword
        else ax.raincloud("samples", data={"samples": frame})
    )
    assert ax.get_xlabel() == "Condition"
    assert [tick.get_text() for tick in ax.get_xticklabels()] == ["A", "B"]
    np.testing.assert_array_equal(result["rain"][1].get_offsets()[:, 1], frame["B"])


@pytest.mark.parametrize("explicit", [False, True])
def test_raincloud_respects_autoformat(explicit):
    frame = pd.DataFrame({"A": [1, 2, 3], "B": [2, 4, 5]})
    frame.columns.name = "Condition"
    fig, ax = uplt.subplots()
    labels = ["First", "Second"] if explicit else None
    with uplt.rc.context({"autoformat": False}):
        ax.raincloud(frame, labels=labels)
    assert ax.get_xlabel() == ""
    assert [tick.get_text() for tick in ax.get_xticklabels()] == (labels or ["0", "1"])


def test_raincloud_xarray_metadata_and_existing_labels():
    xr = pytest.importorskip("xarray")
    samples = xr.DataArray(
        np.arange(12.0).reshape(6, 2),
        dims=["sample", "condition"],
        coords={"condition": ["A", "B"]},
        name="rate",
        attrs={"long_name": "Growth", "units": "mm"},
    )
    fig, axes = uplt.subplots(ncols=2, share=False)
    axes[0].raincloud(samples, vert=False)
    assert axes[0].get_xlabel() == "Growth (mm)"
    assert axes[0].get_ylabel() == "condition"
    assert [tick.get_text() for tick in axes[0].get_yticklabels()] == ["A", "B"]
    axes[1].format(xlabel="Custom group", ylabel="Custom value")
    axes[1].raincloud(samples)
    assert axes[1].get_xlabel() == "Custom group"
    assert axes[1].get_ylabel() == "Custom value"


@pytest.mark.parametrize(
    "disabled", [{}, {"cloud": False}, {"cloud": False, "rain": False}]
)
def test_raincloud_legend_one_entry_per_group(disabled):
    from matplotlib.legend import Legend

    fig, ax = uplt.subplots()
    options = {"title": "Condition"}
    result = ax.raincloud(
        np.arange(12.0).reshape(6, 2),
        labels=["A", "B"],
        legend=True,
        legend_kw=options,
        **disabled,
    )
    fig.canvas.draw()
    legends = fig.findobj(Legend)
    assert len(legends) == 1
    assert [text.get_text() for text in legends[0].get_texts()] == ["A", "B"]
    assert legends[0].get_title().get_text() == "Condition"
    assert options == {"title": "Condition"}


def test_raincloud_filters_observation_styles():
    values = np.ma.array([1.0, 2.0, np.nan, 3.0, 4.0, 99.0], mask=[0, 0, 0, 0, 0, 1])
    sizes = np.arange(10.0, 70.0, 10.0)
    colours = np.arange(6.0)
    fig, ax = uplt.subplots()
    result = ax.raincloud(
        values, rain_kw={"ms": sizes, "c": colours, "absolute_size": True}
    )
    points = result["rain"][0]
    np.testing.assert_array_equal(points.get_sizes(), sizes[[0, 1, 3, 4]])
    np.testing.assert_array_equal(points.get_array(), colours[[0, 1, 3, 4]])
    np.testing.assert_array_equal(points.get_offsets()[:, 1], [1.0, 2.0, 3.0, 4.0])


@pytest.mark.parametrize(
    "option,value",
    [
        ("showmeans", True),
        ("showmedians", True),
        ("showextrema", True),
        ("quantiles", [0.25, 0.75]),
    ],
)
def test_raincloud_violin_summary_options(option, value):
    fig, ax = uplt.subplots()
    result = ax.raincloud(np.arange(8.0), cloud_kw={option: value})
    assert result["cloud"][0] in ax.collections
    assert result["cloud_extras"][0]
    fig.canvas.draw()


def test_raincloud_nested_boxplot_properties():
    fig, ax = uplt.subplots()
    result = ax.raincloud(
        np.r_[np.arange(8.0), 100],
        box_kw={
            "showfliers": True,
            "showmeans": True,
            "boxprops": {"lw": 4, "color": "red"},
            "medianprops": {"lw": 3, "color": "blue"},
            "whiskerprops": {"lw": 2, "color": "green"},
            "flierprops": {"marker": "x", "ms": 9},
            "meanprops": {"color": "purple"},
        },
    )
    artists = result["box"][0]
    for name, width, colour in [
        ("boxes", 4, "red"),
        ("medians", 3, "blue"),
        ("whiskers", 2, "green"),
    ]:
        for artist in artists[name]:
            assert artist.get_linewidth() == width
            assert artist.get_color() == colour
    assert artists["fliers"][0].get_marker() == "x"
    assert artists["fliers"][0].get_markersize() == 9
    assert artists["means"][0].get_color() == "purple"
    assert artists["patches"][0] in ax.patches


@pytest.mark.parametrize("filled", [False, True])
def test_raincloud_box_fill_and_patch_artist(filled):
    fig, ax = uplt.subplots()
    result = ax.raincloud(
        np.arange(8.0),
        box_kw={
            "patch_artist": True,
            "filled": filled,
            "boxprops": {"fc": "red", "ec": "navy"},
        },
    )
    patch = result["box"][0]["boxes"][0]
    assert patch.get_fill() == filled
    np.testing.assert_allclose(patch.get_facecolor()[:3], to_rgba("red")[:3])
    np.testing.assert_allclose(patch.get_edgecolor()[:3], to_rgba("navy")[:3])
    assert result["box"][0]["patches"] == [patch]
    assert len(ax.patches) == 1


def test_raincloud_unfilled_boxes_and_hidden_box_legend():
    fig, ax = uplt.subplots()
    ax.raincloud(np.arange(8.0), box_kw={"filled": False})
    assert not ax.patches
    result = ax.raincloud(
        np.arange(8.0), cloud=False, rain=False, box_kw={"showbox": False}, legend=True
    )
    assert not result["box"][0]["boxes"]
    fig.canvas.draw()


def test_raincloud_colormap_colour_shorthand():
    fig, ax = uplt.subplots()
    result = ax.raincloud(np.arange(8.0), color=("reds", 0.6))
    expected = uplt.Colormap("reds")(0.6)
    np.testing.assert_allclose(
        result["cloud"][0].get_facecolor()[0, :3], expected[:3], atol=1 / 255
    )
    np.testing.assert_allclose(
        result["rain"][0].get_facecolor()[0, :3], expected[:3], atol=1 / 255
    )


def test_raincloud_subplot_grid_and_shared_ticks():
    fig, axes = uplt.subplots(ncols=2)
    axes.raincloud(np.arange(12.0).reshape(6, 2), labels=["A", "B"])
    for ax in axes:
        assert [tick.get_text() for tick in ax.get_xticklabels()] == ["A", "B"]
        assert len(ax.get_xticks()) == 2
    fig.canvas.draw()


def test_raincloud_per_group_widths_and_quantiles():
    fig, ax = uplt.subplots()
    result = ax.raincloud(
        np.arange(12.0).reshape(6, 2),
        cloud_kw={"widths": [0.4, 0.8], "quantiles": [[0.25, 0.75], [0.5]]},
        box_kw={"widths": [0.1, 0.2], "capwidths": [0.05, 0.1]},
    )
    for i, width in enumerate([0.4, 0.8]):
        vertices = result["cloud"][i].get_paths()[0].vertices
        np.testing.assert_allclose(np.ptp(vertices[:, 0]), width / 2)
        np.testing.assert_allclose(
            np.ptp(result["box"][i]["boxes"][0].get_xdata()), [0.1, 0.2][i]
        )
        assert result["cloud_extras"][i]
    fig.canvas.draw()


def test_raincloud_rc_layout_and_appearance():
    fig, ax = uplt.subplots()
    settings = {
        "raincloud.orientation": "horizontal",
        "raincloud.side": "low",
        "raincloud.jitter": 0,
        "raincloud.offset": 0.3,
        "raincloud.cloud.width": 0.8,
        "raincloud.cloud.alpha": 0.2,
        "raincloud.rain.markersize": 36,
        "raincloud.rain.linewidth": 1.5,
        "raincloud.rain.alpha": 0.7,
        "raincloud.box.width": 0.2,
        "raincloud.box.fill": False,
        "raincloud.box.showfliers": True,
        "raincloud.box.zorder": 5,
    }
    with uplt.rc.context(settings):
        result = ax.raincloud(np.r_[np.arange(8.0), 100])
    points = result["rain"][0]
    np.testing.assert_allclose(points.get_offsets()[:, 1], 0.3)
    np.testing.assert_array_equal(points.get_sizes(), [36])
    np.testing.assert_allclose(points.get_linewidths(), [1.5])
    assert points.get_alpha() == 0.7
    density = result["cloud"][0]
    vertices = density.get_paths()[0].vertices[:, 1]
    assert vertices.max() == pytest.approx(-0.3)
    assert np.ptp(vertices) == pytest.approx(0.4)
    assert density.get_alpha() == 0.2
    box = result["box"][0]
    assert np.ptp(box["boxes"][0].get_ydata()) == pytest.approx(0.2)
    assert box["boxes"][0].get_zorder() == 5
    np.testing.assert_array_equal(box["fliers"][0].get_xdata(), [100])
    assert not ax.patches
    fig.canvas.draw()


def test_raincloud_explicit_options_override_rc():
    fig, ax = uplt.subplots()
    settings = {
        "raincloud.orientation": "horizontal",
        "raincloud.side": "low",
        "raincloud.jitter": 0.5,
        "raincloud.offset": 0.4,
        "raincloud.rain.markersize": 40,
        "raincloud.rain.linewidth": 3,
        "raincloud.rain.alpha": 0.8,
        "raincloud.cloud.alpha": 0.9,
        "raincloud.box.fill": False,
        "raincloud.box.width": 0.5,
    }
    with uplt.rc.context(settings):
        result = ax.raincloud(
            np.arange(8.0),
            orientation="vertical",
            side="high",
            jitter=0,
            offset=0,
            rain_kw={"ms": 20, "lw": 1, "a": 0.3},
            cloud_kw={"a": 0.25},
            box_kw={"filled": True, "widths": 0.1},
        )
    points = result["rain"][0]
    np.testing.assert_array_equal(points.get_offsets()[:, 0], np.zeros(8))
    np.testing.assert_array_equal(points.get_sizes(), [20])
    np.testing.assert_array_equal(points.get_linewidths(), [1])
    assert points.get_alpha() == 0.3
    assert result["cloud"][0].get_alpha() == 0.25
    assert result["cloud"][0].get_paths()[0].vertices[:, 0].min() == 0
    assert np.ptp(result["box"][0]["boxes"][0].get_xdata()) == pytest.approx(0.1)
    assert len(ax.patches) == 1


def test_raincloud_rc_visibility_and_explicit_false():
    fig, axes = uplt.subplots(ncols=2)
    with uplt.rc.context({"raincloud.cloud": False, "raincloud.box": False}):
        first = axes[0].raincloud(np.arange(8.0))
        second = axes[1].raincloud(np.arange(8.0), cloud=True, rain=False)
    assert first["cloud"] == first["box"] == [None]
    assert first["rain"][0] is not None
    assert second["cloud"][0] is not None
    assert second["rain"] == second["box"] == [None]


def test_raincloud_rc_seed_and_generator_override():
    fig, axes = uplt.subplots(ncols=3)
    with uplt.rc.context({"raincloud.seed": 17}):
        first = axes[0].raincloud(np.arange(8.0))
        second = axes[1].raincloud(np.arange(8.0), seed=17)
        third = axes[2].raincloud(np.arange(8.0), seed=np.random.default_rng(7))
    np.testing.assert_array_equal(
        first["rain"][0].get_offsets(), second["rain"][0].get_offsets()
    )
    assert not np.array_equal(
        first["rain"][0].get_offsets(), third["rain"][0].get_offsets()
    )


def test_raincloud_rc_file_and_context_restore(tmp_path):
    original = uplt.rc["raincloud.side"]
    path = tmp_path / "raincloud.rc"
    path.write_text(
        "raincloud.side: low\nraincloud.cloud.alpha: 0.25\nraincloud.seed: None\n"
    )
    fig, ax = uplt.subplots()
    with uplt.rc.context(file=str(path)):
        result = ax.raincloud(np.arange(8.0))
        assert uplt.rc["raincloud.seed"] is None
        assert result["cloud"][0].get_alpha() == 0.25
        assert result["cloud"][0].get_paths()[0].vertices[:, 0].max() == pytest.approx(
            -0.15
        )
    assert uplt.rc["raincloud.side"] == original
