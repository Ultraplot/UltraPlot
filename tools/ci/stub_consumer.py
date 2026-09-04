"""Representative lazy public imports consumed by static type checkers."""

from collections.abc import Callable
from typing import Any, assert_type

import ultraplot as uplt

reveal_type(uplt.subplots)
reveal_type(uplt.Axes.format)

figure, axes = uplt.subplots()
assert_type(figure, uplt.Figure)
assert_type(axes, uplt.SubplotGrid)
assert_type(axes[0], uplt.Axes)
axes[0].format(title="Static typing")
assert_type(axes.plot, Callable[..., Any])
_ = axes.plot([0, 1], [0, 1])
reveal_type(axes.plot)
