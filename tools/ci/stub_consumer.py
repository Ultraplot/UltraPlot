"""Representative lazy public imports consumed by static type checkers."""

import ultraplot as uplt

reveal_type(uplt.subplots)
reveal_type(uplt.Axes.format)

figure, axes = uplt.subplots()
figure_check: uplt.Figure = figure
axes_check: uplt.SubplotGrid = axes
axis_check: uplt.Axes = axes[0]
axes[0].format(title="Static typing")
reveal_type(axes.plot)
