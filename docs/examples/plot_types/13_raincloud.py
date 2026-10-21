"""
Raincloud plots
===============

These synthetic samples have exactly the same sample mean and standard
deviation, but different shapes. Half violins reveal the shapes, points show
the observations, and boxes show the median and interquartile range.
"""

import numpy as np

import ultraplot as uplt

# Fixed seeds make both the observations and the point positions reproducible.
rng = np.random.default_rng(42)
data = np.column_stack(
    [
        rng.normal(size=100),
        rng.lognormal(mean=0, sigma=0.65, size=100),
        np.r_[rng.normal(-1.2, 0.3, 50), rng.normal(1.2, 0.3, 50)],
    ]
)
data = (data - data.mean(axis=0)) / data.std(axis=0, ddof=1)
labels = ["Normal", "Right-skewed", "Bimodal"]
colors = ["#4477AA", "#228833", "#AA3377"]
limits = (np.floor(data.min()), np.ceil(data.max()))

fig, axs = uplt.subplots(ncols=2, refwidth=3.8, refaspect=1.1, share=False)

artists = axs[0].raincloud(
    data,
    labels=labels,
    orientation="horizontal",
    cycle=colors,
    seed=7,
)
axs[0].format(
    title="Horizontal raincloud",
    xlabel="Standardised value",
    yreverse=True,
    xlim=limits,
    grid=False,
)

axs[1].raincloud(data, labels=labels, cycle=colors, side="low", seed=7)
axs[1].format(
    title="Vertical raincloud · cloud on low side",
    ylabel="Standardised value",
    ylim=limits,
    grid=False,
)
axs.format(suptitle="Same mean and standard deviation, different distributions")
fig.show()
