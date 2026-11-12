"""Treemap area conservation, hierarchy, and public plotting behavior."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from matplotlib.colors import Normalize, to_rgba

import ultraplot as uplt


def _assert_tiling(patches, bounds):
    x, y, width, height = bounds
    for i, patch in enumerate(patches):
        left, bottom = patch.get_xy()
        assert left >= x - 1e-12
        assert bottom >= y - 1e-12
        assert left + patch.get_width() <= x + width + 1e-12
        assert bottom + patch.get_height() <= y + height + 1e-12
        for other in patches[i + 1 :]:
            dx = min(left + patch.get_width(), other.get_x() + other.get_width()) - max(
                left, other.get_x()
            )
            dy = min(
                bottom + patch.get_height(), other.get_y() + other.get_height()
            ) - max(bottom, other.get_y())
            assert dx <= 1e-12 or dy <= 1e-12
    assert sum(p.get_width() * p.get_height() for p in patches) == pytest.approx(
        width * height
    )


@pytest.mark.parametrize("rect", [(0, 0, 1, 1), (-2, 3, 4, 1), (1, -3, 1, 4)])
def test_treemap_proportional_area_and_no_overlap(rect):
    values = [3, 12, 1, 7, 2]
    fig, ax = uplt.subplots()
    result = ax.treemap(values, labels=list("ABCDE"), rect=rect, pad=0)
    areas = [p.get_width() * p.get_height() for p in result["patches"]]
    np.testing.assert_allclose(
        areas, np.array(values) / sum(values) * rect[2] * rect[3]
    )
    _assert_tiling(result["patches"], rect)
    assert result["values"] == values
    assert [text.get_text() for text in result["texts"]] == list("ABCDE")
    fig.canvas.draw()


def test_treemap_hierarchy_preserves_totals_and_contains_descendants():
    data = {"A": {"a": 4, "nested": {"b": 2, "c": 1}}, "B": {"d": 2}, "E": 1}
    fig, ax = uplt.subplots()
    result = ax.treemap(data, pad=0, group_pad=0, group_labels=False)
    assert result["paths"] == [
        ("A", "a"),
        ("A", "nested", "b"),
        ("A", "nested", "c"),
        ("B", "d"),
        ("E",),
    ]
    np.testing.assert_allclose(
        [p.get_width() * p.get_height() for p in result["patches"]],
        np.array([4, 2, 1, 2, 1]) / 10,
    )
    _assert_tiling(result["patches"], (0, 0, 1, 1))
    assert len(result["groups"]) == 3
    for group, prefix in zip(result["groups"], [("A",), ("A", "nested"), ("B",)]):
        for patch, path in zip(result["patches"], result["paths"]):
            if path[: len(prefix)] == prefix:
                assert patch.get_x() >= group.get_x() - 1e-12
                assert patch.get_y() >= group.get_y() - 1e-12
                assert (
                    patch.get_x() + patch.get_width()
                    <= group.get_x() + group.get_width() + 1e-12
                )
                assert (
                    patch.get_y() + patch.get_height()
                    <= group.get_y() + group.get_height() + 1e-12
                )


def test_treemap_colormap_colorbar_and_zero_alignment():
    fig, ax = uplt.subplots()
    norm = Normalize(0, 8)
    result = ax.treemap({"small": 1, "zero": 0, "large": 7}, cmap="viridis", norm=norm)
    assert result["paths"] == [("small",), ("large",)]
    for patch, value in zip(result["patches"], [1, 7]):
        np.testing.assert_allclose(
            patch.get_facecolor(), result["mappable"].to_rgba(value)
        )
    ax.colorbar(result["mappable"], label="Size")
    fig.canvas.draw()


@pytest.mark.parametrize("container", [dict, pd.DataFrame])
def test_treemap_series_and_lookup_data(container):
    fig, axs = uplt.subplots(ncols=2)
    series = pd.Series([1, 3], index=["A", "B"])
    result = axs[0].treemap(series, color=["red", "blue"])
    assert result["paths"] == [("A",), ("B",)]
    for patch, color in zip(result["patches"], ["red", "blue"]):
        np.testing.assert_allclose(patch.get_facecolor(), to_rgba(color))
    lookup = container({"amount": [1, 3], "names": ["A", "B"]})
    other = axs[1].treemap(
        "amount",
        labels=lookup["names"],
        data=lookup,
        show_values=True,
        value_format="{:.1f}",
    )
    assert [text.get_text() for text in other["texts"]] == ["A\n1.0", "B\n3.0"]


@pytest.mark.parametrize("container", [dict, pd.DataFrame])
@pytest.mark.parametrize("lookup_sizes", [False, True])
def test_treemap_string_labels_are_literal_with_data(container, lookup_sizes):
    _, ax = uplt.subplots()
    data = container({"amount": [2, 0, 3], "name": ["A", "B", "C"]})
    sizes = "amount" if lookup_sizes else data["amount"]
    result = ax.treemap(sizes, labels="name", data=data)
    assert [text.get_text() for text in result["texts"]] == ["name", "name"]
    assert result["values"] == [2, 3]


def test_treemap_string_labels_repeat_without_data():
    _, ax = uplt.subplots()
    result = ax.treemap([2, 0, 3], labels="Category", show_values=True)
    assert [text.get_text() for text in result["texts"]] == [
        "Category\n2",
        "Category\n3",
    ]


@pytest.mark.parametrize("keyword", ["color", "colors", "c"])
@pytest.mark.parametrize("palette", [["r"], ["r", "g"], ["r", "g", "b", "k", "y"]])
def test_treemap_palette_cycles_in_input_order(keyword, palette):
    _, ax = uplt.subplots()
    result = ax.treemap(
        {"GroupA": {"a": 2, "zero": 0, "b": 3}, "GroupB": {"c": 4, "d": 5}},
        **{keyword: palette},
    )
    assert result["paths"] == [
        ("GroupA", "a"),
        ("GroupA", "b"),
        ("GroupB", "c"),
        ("GroupB", "d"),
    ]
    for index, patch in enumerate(result["patches"]):
        np.testing.assert_allclose(
            patch.get_facecolor(), to_rgba(palette[index % len(palette)])
        )


def test_treemap_uses_current_patch_cycle_and_advances():
    _, ax = uplt.subplots()
    ax.set_prop_cycle(color=["r", "g", "b", "k"])
    ax.bar([0], [1])
    result = ax.treemap({"a": 2, "zero": 0, "b": 3})
    for patch, color in zip(result["patches"], ["g", "b"]):
        np.testing.assert_allclose(patch.get_facecolor(), to_rgba(color))
    following = ax.treemap([1])
    np.testing.assert_allclose(following["patches"][0].get_facecolor(), to_rgba("k"))


@pytest.mark.parametrize("kwargs", [{"color": "r"}, {"cmap": "viridis"}])
def test_treemap_explicit_leaf_colors_do_not_advance_cycle(kwargs):
    _, ax = uplt.subplots()
    ax.set_prop_cycle(color=["g", "b"])
    ax.treemap([1, 2], **kwargs)
    result = ax.treemap([1])
    np.testing.assert_allclose(result["patches"][0].get_facecolor(), to_rgba("g"))


def test_treemap_group_colors_do_not_depend_on_size_sorting():
    _, axs = uplt.subplots(ncols=2)
    first = axs[0].treemap(
        {"A": {"a": 1, "b": 2}, "B": {"c": 3, "d": 4}}, cycle=["r", "g"]
    )
    second = axs[1].treemap(
        {"A": {"a": 4, "b": 3}, "B": {"c": 2, "d": 1}}, cycle=["r", "g"]
    )
    for key in ("patches", "groups"):
        np.testing.assert_allclose(
            [p.get_facecolor() for p in first[key]],
            [p.get_facecolor() for p in second[key]],
        )
    np.testing.assert_allclose(first["groups"][0].get_facecolor()[:3], to_rgba("r")[:3])
    np.testing.assert_allclose(first["groups"][1].get_facecolor()[:3], to_rgba("g")[:3])


def test_treemap_named_cycle_and_cycle_options():
    _, ax = uplt.subplots()
    options = {"reverse": True}
    result = ax.treemap([1, 0, 3, 2], cycle="colorblind", cycle_kw=options)
    expected = uplt.Cycle("colorblind", N=3, reverse=True).by_key()["color"]
    np.testing.assert_allclose(
        [p.get_facecolor() for p in result["patches"]],
        [to_rgba(color) for color in expected],
    )


@pytest.mark.parametrize(
    "sizes,kwargs",
    [
        ([], {}),
        ([0, 0], {}),
        ([1, -1], {}),
        ([1, np.nan], {}),
        ([1, np.inf], {}),
        ([[1, 2]], {}),
        ({"A": {}}, {}),
        ([1, 2], {"labels": ["A"]}),
        ([1], {"pad": -1}),
        ([1], {"rect": (0, 0, 0, 1)}),
        ([1], {"color": "red", "cmap": "viridis"}),
        ([1, 2], {"color": []}),
        ([1], {"colors": ["r", "g"], "cmap": "viridis"}),
    ],
)
def test_treemap_invalid_data_does_not_add_artists(sizes, kwargs):
    fig, ax = uplt.subplots()
    before = (list(ax.patches), list(ax.texts))
    with pytest.raises(ValueError):
        ax.treemap(sizes, **kwargs)
    assert list(ax.patches) == before[0]
    assert list(ax.texts) == before[1]


def test_treemap_padding_and_styles_do_not_mutate_input():
    data = {"Group": {"Alpha": 3, "Beta": 2}, "Other": 1}
    text_kw = {"fontsize": 8}
    group_kw = {"lw": 2}
    fig, ax = uplt.subplots()
    result = ax.treemap(
        data, pad=0.02, show_values=True, text_kw=text_kw, group_kw=group_kw, lw=1.5
    )
    assert text_kw == {"fontsize": 8}
    assert group_kw == {"lw": 2}
    assert data == {"Group": {"Alpha": 3, "Beta": 2}, "Other": 1}
    assert all(p.get_linewidth() == 1.5 for p in result["patches"])
    assert result["groups"][0].get_linewidth() == 2
    assert all(text.get_clip_on() for text in result["texts"])
    fig.canvas.draw()


@pytest.mark.parametrize(
    "projection,scale", [("polar", None), (None, "log"), (None, "symlog")]
)
def test_treemap_rejects_axes_that_distort_area(projection, scale):
    fig, axs = uplt.subplots(proj=projection)
    ax = axs[0]
    if scale is not None:
        ax.set_xscale(scale)
    before = list(ax.patches)
    with pytest.raises(ValueError, match="Cartesian axes with linear scales"):
        ax.treemap([1, 2])
    assert list(ax.patches) == before


def test_treemap_rc_layout_and_appearance() -> None:
    settings = {
        "treemap.rect": (2, 3, 2, 1),
        "treemap.pad": 0.025,
        "treemap.group_pad": 0.03,
        "treemap.group_labels": True,
        "treemap.show_values": True,
        "treemap.value_format": "{:.1f} kg",
        "treemap.patch.edgecolor": "navy",
        "treemap.patch.linewidth": 2,
        "treemap.group.edgecolor": "red",
        "treemap.group.linewidth": 3,
        "treemap.group.alpha": 0.4,
        "treemap.text.size": 12,
        "treemap.text.color": "purple",
        "treemap.group.text.size": 14,
        "treemap.group.text.weight": "normal",
    }
    before = {key: uplt.rc[key] for key in settings}
    fig, axs = uplt.subplots()
    ax = axs[0]
    with uplt.rc.context(settings):
        result = ax.treemap({"Group": {"A": 3, "B": 1}})
    assert {key: uplt.rc[key] for key in settings} == before
    np.testing.assert_allclose(ax.get_xlim(), [2, 4])
    np.testing.assert_allclose(ax.get_ylim(), [3, 4])
    assert [text.get_text() for text in result["texts"]] == [
        "A\n3.0 kg",
        "B\n1.0 kg",
    ]
    for patch, text in zip(result["patches"], result["texts"]):
        assert patch.get_linewidth() == 2
        np.testing.assert_allclose(patch.get_edgecolor(), to_rgba("navy"))
        assert text.get_fontsize() == 12
        assert text.get_color() == "purple"
    group = result["groups"][0]
    assert group.get_alpha() == 0.4
    assert group.get_linewidth() == 3
    np.testing.assert_allclose(group.get_edgecolor(), to_rgba("red", 0.4))
    header = result["group_texts"][0]
    assert header.get_fontsize() == 14
    assert header.get_fontweight() == "normal"
    fig.canvas.draw()


def test_treemap_explicit_options_and_aliases_override_rc() -> None:
    settings = {
        "treemap.rect": (5, 5, 2, 2),
        "treemap.pad": 0.1,
        "treemap.group_pad": 0.1,
        "treemap.group_labels": True,
        "treemap.show_values": True,
        "treemap.patch.linewidth": 2,
        "treemap.group.alpha": 0.5,
        "treemap.text.color": "red",
        "treemap.text.size": 20,
    }
    fig, ax = uplt.subplots()
    with uplt.rc.context(settings):
        result = ax.treemap(
            {"Group": {"A": 3, "B": 1}},
            rect=(0, 0, 1, 1),
            pad=0,
            group_pad=0,
            group_labels=False,
            show_values=False,
            lw=0,
            text_kw={"c": "navy", "size": 8},
            group_kw={"a": 0, "lw": 0},
        )
    _assert_tiling(result["patches"], (0, 0, 1, 1))
    assert not result["group_texts"]
    assert [text.get_text() for text in result["texts"]] == ["A", "B"]
    assert all(p.get_linewidth() == 0 for p in result["patches"])
    assert all(text.get_color() == "navy" for text in result["texts"])
    assert all(text.get_fontsize() == 8 for text in result["texts"])
    assert result["groups"][0].get_alpha() == 0
    assert result["groups"][0].get_linewidth() == 0


def test_treemap_rc_file_and_context_restore(tmp_path: Path) -> None:
    path = tmp_path / "treemap.rc"
    path.write_text(
        "treemap.rect: 1, 2, 3, 4\n"
        "treemap.pad: 0\n"
        "treemap.group_labels: False\n"
        "treemap.show_values: True\n"
        "treemap.value_format: {:.1f}\n"
        "treemap.text.color: navy\n"
    )
    before = uplt.rc["treemap.rect"]
    fig, axs = uplt.subplots()
    ax = axs[0]
    with uplt.rc.context(file=str(path)):
        result = ax.treemap({"A": 3, "B": 1})
        assert uplt.rc["treemap.rect"] == (1, 2, 3, 4)
    assert uplt.rc["treemap.rect"] == before
    _assert_tiling(result["patches"], (1, 2, 3, 4))
    assert result["texts"][0].get_text() == "A\n3.0"
    assert result["texts"][0].get_color() == "navy"


def test_treemap_callable_rc_formatter_and_call_override() -> None:
    fig, axs = uplt.subplots(ncols=2)
    with uplt.rc.context(
        {
            "treemap.value_format": lambda value: f"{value:.0f}kg",
            "treemap.show_values": True,
        }
    ):
        first = axs[0].treemap([3], labels=["A"])
        second = axs[1].treemap([3], labels=["A"], value_format="{:.1f}")
    assert first["texts"][0].get_text() == "A\n3kg"
    assert second["texts"][0].get_text() == "A\n3.0"


@pytest.mark.parametrize(
    "key,value",
    [
        ("treemap.rect", (0, 0, 0, 1)),
        ("treemap.rect", (0, 1)),
        ("treemap.pad", -0.1),
        ("treemap.group_pad", float("nan")),
        ("treemap.group.alpha", 1.5),
        ("treemap.value_format", 42),
    ],
)
def test_treemap_rc_rejects_invalid_settings(key: str, value: object) -> None:
    before = uplt.rc[key]
    with pytest.raises(ValueError):
        uplt.rc[key] = value
    assert uplt.rc[key] == before


def test_treemap_defaults_match_original_appearance() -> None:
    fig, axs = uplt.subplots(ncols=2)
    data = {"Group": {"A": 3, "B": 1}, "Other": 2}
    default = axs[0].treemap(data)
    explicit = axs[1].treemap(
        data,
        rect=(0, 0, 1, 1),
        pad=0.008,
        group_pad=0.018,
        group_labels=True,
        show_values=False,
        value_format="{:g}",
        ec="white",
        lw=0.6,
        text_kw={"fontsize": 9},
        group_kw={"ec": "white", "lw": 1.2, "alpha": 0.12},
    )
    for key in ("patches", "groups"):
        for actual, expected in zip(default[key], explicit[key]):
            np.testing.assert_allclose(
                actual.get_bbox().bounds, expected.get_bbox().bounds
            )
            np.testing.assert_allclose(actual.get_facecolor(), expected.get_facecolor())
            assert actual.get_linewidth() == expected.get_linewidth()
    for actual, expected in zip(default["texts"], explicit["texts"]):
        assert actual.get_fontsize() == expected.get_fontsize()
        assert actual.get_color() == expected.get_color()
