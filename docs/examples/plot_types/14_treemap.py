"""
Treemaps
========

``PlotAxes.treemap`` represents each value by a rectangle's area. Nested
mappings group related categories inside parent rectangles. Both examples use
synthetic data. Layout and rendering require only UltraPlot's core dependencies.
"""

import ultraplot as uplt

fig, axs = uplt.subplots(ncols=2, refwidth=4.2, refaspect=1, share=False)

axs[0].treemap(
    {"Solar": 36, "Wind": 28, "Hydro": 18, "Nuclear": 12, "Other": 6},
    color=["#3c8d87", "#5286b0", "#69a4b7", "#af8a55", "#959baa"],
    show_values=True,
    value_format="{:.0f}%",
    pad=0.012,
    text_kw={"fontsize": 11},
)
axs[0].format(title="Flat categories")

axs[1].treemap(
    {
        "Research": {"Fieldwork": 24, "Equipment": 16, "Data": 10},
        "People": {"Staff": 20, "Training": 10},
        "Operations": {"Travel": 12, "Services": 8},
    },
    show_values=True,
    value_format="{:.0f}",
    pad=0.012,
    group_pad=0.018,
    text_kw={"fontsize": 10},
)
axs[1].format(title="Nested categories")
axs.format(suptitle="Treemaps · area shows value")
fig.show()
