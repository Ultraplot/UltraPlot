import matplotlib.colors as mcolors
import pytest
import ultraplot as uplt


def _all_match_color(colors, expected):
    expected = mcolors.to_rgba(expected)
    return all(mcolors.to_rgba(color) == expected for color in colors)


def test_alt_axes_styling_dark_background():
    """
    Test that applying dark_background style does not leak tick visibility
    settings and correctly preserves alternative axes tick locations.
    """
    with uplt.rc.context(style="dark_background"):
        fig, ax = uplt.subplots()
        ax.format(ycolor="C0", ylabel="Left Axis")

        ax2 = ax.alty(color="C1")
        ax2.format(ycolor="C1", ylabel="Right Axis", ylim=(0, 1))

        # The left axis should ONLY have visible ticks on the left
        left_ax_left_ticks = sum(
            1
            for t in ax.yaxis.get_ticklines()
            if t.get_visible() and t.get_xdata()[0] == 0
        )
        left_ax_right_ticks = sum(
            1
            for t in ax.yaxis.get_ticklines()
            if t.get_visible() and t.get_xdata()[0] == 1
        )

        # The right axis (ax2) should ONLY have visible ticks on the right
        right_ax_left_ticks = sum(
            1
            for t in ax2.yaxis.get_ticklines()
            if t.get_visible() and t.get_xdata()[0] == 0
        )
        right_ax_right_ticks = sum(
            1
            for t in ax2.yaxis.get_ticklines()
            if t.get_visible() and t.get_xdata()[0] == 1
        )

        assert left_ax_left_ticks > 0, "Left axis should have left ticks"
        assert left_ax_right_ticks == 0, "Left axis should NOT have right ticks"

        assert right_ax_left_ticks == 0, "Right axis should NOT have left ticks"
        assert right_ax_right_ticks > 0, "Right axis should have right ticks"

        assert _all_match_color(
            [
                line.get_color()
                for line in ax2.yaxis.get_ticklines()
                if line.get_visible()
            ],
            "C1",
        )
        assert {
            mcolors.to_rgba(ax2.spines[side].get_edgecolor())
            for side in ("left", "right")
            if ax2.spines[side].get_visible()
        } == {mcolors.to_rgba("C1")}


@pytest.mark.parametrize(
    ("setup", "format_kwargs", "expected_color", "expected_linewidth"),
    [
        (
            lambda ax: ax,
            {"ycolor": "C0", "ylinewidth": 3, "ylabel": "Left Axis"},
            "C0",
            3,
        ),
        (
            lambda ax: ax.alty(color="C1", linewidth=3),
            {"ylabel": "Right Axis", "ylim": (0, 1)},
            "C1",
            3,
        ),
    ],
)
def test_dark_background_preserves_axis_colors_on_reformat(
    setup, format_kwargs, expected_color, expected_linewidth
):
    with uplt.rc.context(style="dark_background"):
        fig, ax = uplt.subplots()
        target = setup(ax)
        target.format(**format_kwargs)
        target.format(ylabel="Updated Label")

        assert _all_match_color(
            [label.get_color() for label in target.get_yticklabels()], expected_color
        )
        assert mcolors.to_rgba(target.yaxis.label.get_color()) == mcolors.to_rgba(
            expected_color
        )
        assert _all_match_color(
            [
                line.get_color()
                for line in target.yaxis.get_ticklines()
                if line.get_visible()
            ],
            expected_color,
        )
        assert {
            mcolors.to_rgba(target.spines[side].get_edgecolor())
            for side in ("left", "right")
            if target.spines[side].get_visible()
        } == {mcolors.to_rgba(expected_color)}
        assert {
            target.spines[side].get_linewidth()
            for side in ("left", "right")
            if target.spines[side].get_visible()
        } == {expected_linewidth}


def test_dark_background_updates_unspecified_axis_frame_style():
    fig, ax = uplt.subplots()

    with uplt.rc.context(style="dark_background"):
        ax.format(ylabel="Updated Label")

        expected = mcolors.to_rgba(uplt.rc["axes.edgecolor"])
        assert {
            mcolors.to_rgba(ax.spines[side].get_edgecolor())
            for side in ("left", "right")
            if ax.spines[side].get_visible()
        } == {expected}
        assert _all_match_color(
            [
                line.get_color()
                for line in ax.yaxis.get_ticklines()
                if line.get_visible()
            ],
            expected,
        )


@pytest.mark.parametrize(
    ("format_kwargs", "getter", "expected_color"),
    [
        (
            {"ytickcolor": "red"},
            lambda ax: [
                line.get_color()
                for line in ax.yaxis.get_ticklines()
                if line.get_visible()
            ],
            "red",
        ),
        (
            {"yticklabelcolor": "blue"},
            lambda ax: [label.get_color() for label in ax.get_yticklabels()],
            "blue",
        ),
        (
            {"ylabelcolor": "green"},
            lambda ax: [ax.yaxis.label.get_color()],
            "green",
        ),
    ],
)
def test_subplots_preserve_explicit_axis_property_overrides_on_reformat(
    format_kwargs, getter, expected_color
):
    with uplt.rc.context(style="dark_background"):
        fig, axs = uplt.subplots()
        ax = axs[0]
        axs.format(**format_kwargs)
        axs.format(ylabel="Updated Label")

        assert _all_match_color(getter(ax), expected_color)


def test_subplots_preserve_generic_tickcolor_across_later_axis_color():
    with uplt.rc.context(style="dark_background"):
        fig, axs = uplt.subplots()
        ax = axs[0]
        axs.format(tickcolor="red")
        axs.format(ycolor="C1")

        assert _all_match_color(
            [
                line.get_color()
                for line in ax.yaxis.get_ticklines()
                if line.get_visible()
            ],
            "red",
        )
        assert {
            mcolors.to_rgba(ax.spines[side].get_edgecolor())
            for side in ("left", "right")
            if ax.spines[side].get_visible()
        } == {mcolors.to_rgba("C1")}


def test_subplots_preserve_per_axes_axesedgecolor_on_reformat():
    fig, axs = uplt.subplots(ncols=2)
    expected = []
    for i, ax in enumerate(axs):
        color = f"C{i}"
        expected.append(mcolors.to_rgba(color))
        ax.format(axesedgecolor=color)

    axs.format(title="Axes edge color")

    actual = [mcolors.to_rgba(ax.spines["left"].get_edgecolor()) for ax in axs]
    assert actual == expected


def test_subplots_preserve_per_axes_axeslinewidth_on_reformat():
    fig, axs = uplt.subplots(ncols=2)
    expected = []
    for i, ax in enumerate(axs):
        linewidth = i + 1
        expected.append(linewidth)
        ax.format(axeslinewidth=linewidth)

    axs.format(title="Axes line width")

    actual = [ax.spines["left"].get_linewidth() for ax in axs]
    assert actual == expected


def test_subplots_apply_generic_labelcolor():
    fig, axs = uplt.subplots()
    ax = axs[0]

    axs.format(labelcolor="green")

    assert _all_match_color(
        [ax.xaxis.label.get_color(), ax.yaxis.label.get_color()], "green"
    )


@pytest.mark.parametrize("format_kwargs", [{"ytickcolor": "red"}, {"tickcolor": "red"}])
def test_subplots_can_clear_explicit_tickcolor_override(format_kwargs):
    with uplt.rc.context(style="dark_background"):
        fig, axs = uplt.subplots()
        ax = axs[0]
        axs.format(**format_kwargs)
        clear_kwargs = {key: None for key in format_kwargs}
        axs.format(**clear_kwargs)

        assert _all_match_color(
            [
                line.get_color()
                for line in ax.yaxis.get_ticklines()
                if line.get_visible()
            ],
            uplt.rc["ytick.color"],
        )


@pytest.mark.parametrize("format_kwargs", [{"ytickcolor": "red"}, {"tickcolor": "red"}])
def test_direct_axes_can_clear_explicit_tickcolor_override(format_kwargs):
    with uplt.rc.context(style="dark_background"):
        fig = uplt.figure()
        ax = fig.subplot(111)
        ax.format(**format_kwargs)
        clear_kwargs = {key: None for key in format_kwargs}
        ax.format(ylabel="Updated Label", **clear_kwargs)

        assert _all_match_color(
            [
                line.get_color()
                for line in ax.yaxis.get_ticklines()
                if line.get_visible()
            ],
            uplt.rc["ytick.color"],
        )


def test_polar_format_updates_frame_style():
    fig = uplt.figure()
    ax = fig.subplot(111, proj="polar")

    ax.format(color="C3", linewidth=3)

    assert mcolors.to_rgba(ax.spines["polar"].get_edgecolor()) == mcolors.to_rgba("C3")
    assert ax.spines["polar"].get_linewidth() == 3
