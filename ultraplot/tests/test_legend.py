import numpy as np
import pytest

import ultraplot as uplt
from ultraplot.axes import Axes as UAxes


def _decode_panel_span(panel_ax, axis):
    ss = panel_ax.get_subplotspec().get_topmost_subplotspec()
    r1, r2, c1, c2 = ss._get_rows_columns()
    gs = ss.get_gridspec()
    if axis == "rows":
        r1, r2 = gs._decode_indices(r1, r2, which="h")
        return int(r1), int(r2)
    if axis == "cols":
        c1, c2 = gs._decode_indices(c1, c2, which="w")
        return int(c1), int(c2)
    raise ValueError(f"Unknown axis {axis!r}.")


def _anchor_axis(ref):
    if np.iterable(ref) and not isinstance(ref, (str, UAxes)):
        return next(iter(ref))
    return ref


@pytest.mark.parametrize(
    "first_loc, first_ref, second_loc, second_ref, span_axis",
    [
        ("b", lambda axs: axs[0], "r", lambda axs: axs[:, 1], "rows"),
        ("r", lambda axs: axs[:, 2], "b", lambda axs: axs[1, :], "cols"),
        ("t", lambda axs: axs[2], "l", lambda axs: axs[:, 0], "rows"),
        ("l", lambda axs: axs[:, 0], "t", lambda axs: axs[1, :], "cols"),
    ],
)
def test_legend_span_inference_with_multi_panels(
    first_loc, first_ref, second_loc, second_ref, span_axis
):
    fig, axs = uplt.subplots(nrows=3, ncols=3)
    axs.plot([0, 1], [0, 1], label="line")

    fig.legend(ref=first_ref(axs), loc=first_loc)
    fig.legend(ref=second_ref(axs), loc=second_loc)

    side_map = {"l": "left", "r": "right", "t": "top", "b": "bottom"}
    anchor = _anchor_axis(second_ref(axs))
    panel_ax = anchor._panel_dict[side_map[second_loc]][-1]
    span = _decode_panel_span(panel_ax, span_axis)
    assert span == (0, 2)
