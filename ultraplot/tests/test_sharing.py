import pytest, ultraplot as uplt

"""
Sharing levels for subplots determine the visbility of the axis labels and tick labels.

Axis labels are pushed to the border subplots when the sharing level is greater than 1.

Ticks are visible only on the border plots when the sharing levels is greater than 2.

Or more verbosely:
    sharey = 0: no sharing, all labels and ticks visible
    sharey = 1: share axis, all labels and ticks visible
    sharey = 2: share limits
    sharey = 3 or True, share both ticks and labels
A similar story holds for sharex.
"""


@pytest.mark.parametrize("share_level", [0, "labels", "labs", 1, True])
@pytest.mark.mpl_image_compare
def test_sharing_levels_y(share_level):
    """
    Test sharing levels for y-axis: left and right ticks/labels.
    """
    fig, axs = uplt.subplots(None, 2, 3, sharey=share_level)
    axs.format(ylabel="Y")
    axs.format(title=f"sharey = {share_level}")
    fig.canvas.draw()  # needed for checks

    if fig._sharey < 3:
        border_axes = set(axs)
    else:
        # Reduce border_axes to a set of axes for left and right
        border_axes = set()
        for direction in ["left", "right"]:
            axes = fig._get_border_axes().get(direction, [])
            if isinstance(axes, (list, tuple, set)):
                border_axes.update(axes)
            else:
                border_axes.add(axes)
    for axi in axs:
        tick_params = axi.yaxis.get_tick_params()
        for direction in ["left", "right"]:
            label_key = f"label{direction}"
            visible = tick_params.get(label_key, False)
            is_border = axi in fig._get_border_axes().get(direction, [])
            if direction == "left" and (fig._sharey < 3 or is_border):
                assert visible
            else:
                assert not visible
    return fig


@pytest.mark.parametrize("share_level", [0, "labels", "labs", 1, True])
@pytest.mark.mpl_image_compare
def test_sharing_levels_x(share_level):
    """
    Test sharing levels for x-axis: top and bottom ticks/labels.
    """
    fig, axs = uplt.subplots(None, 2, 3, sharex=share_level)
    axs.format(xlabel="X")
    axs.format(title=f"sharex = {share_level}")
    fig.canvas.draw()  # needed for checks

    if fig._sharex < 3:
        border_axes = set(axs)
    else:
        # Reduce border_axes to a set of axes for top and bottom
        border_axes = set()
        for direction in ["top", "bottom"]:
            axes = fig._get_border_axes().get(direction, [])
            if isinstance(axes, (list, tuple, set)):
                border_axes.update(axes)
            else:
                border_axes.add(axes)
    for axi in axs:
        tick_params = axi.xaxis.get_tick_params()
        from ultraplot.internals.versions import _version_mpl
        from packaging import version

        directions = (
            ["top", "bottom"]
            if version.parse(str(_version_mpl)) < version.parse("3.10")
            else ["left", "right"]
        )
        for direction in ["top", "bottom"]:
            label_key = f"label{direction}"
            visible = tick_params.get(label_key, False)
            is_border = axi in fig._get_border_axes().get(direction, [])
            if direction == "bottom" and (fig._sharex < 3 or is_border):
                assert visible
            else:
                assert not visible
    return fig
