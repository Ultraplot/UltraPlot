import pytest
import ultraplot as uplt


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
