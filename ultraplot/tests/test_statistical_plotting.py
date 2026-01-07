#!/usr/bin/env python3
# import ultraplot as uplt
import numpy as np
import pandas as pd
import pytest

import ultraplot as uplt


@pytest.mark.mpl_image_compare
def test_statistical_boxplot(rng):
    N = 500
    data1 = rng.normal(size=(N, 5)) + 2 * (rng.random((N, 5)) - 0.5) * np.arange(5)
    data1 = pd.DataFrame(data1, columns=pd.Index(list("abcde"), name="label"))
    data2 = rng.random((100, 7))
    data2 = pd.DataFrame(data2, columns=pd.Index(list("abcdefg"), name="label"))

    # Figure
    fig, axs = uplt.subplots([[1, 1, 2, 2], [0, 3, 3, 0]], span=False)
    axs.format(abc="A.", titleloc="l", grid=False, suptitle="Boxes and violins demo")

    # Box plots
    ax = axs[0]
    obj1 = ax.box(data1, means=True, marker="x", meancolor="r", fillcolor="gray4")
    ax.format(title="Box plots")

    # Violin plots
    ax = axs[1]
    obj2 = ax.violin(data1, fillcolor="gray6", means=True, points=100)
    ax.format(title="Violin plots")

    # Boxes with different colors
    ax = axs[2]
    ax.boxh(data2, cycle="pastel2")
    ax.format(title="Multiple colors", ymargin=0.15)
    return fig


@pytest.mark.mpl_image_compare
def test_panel_dist(rng):
    N = 500
    x = rng.normal(size=(N,))
    y = rng.normal(size=(N,))
    bins = uplt.arange(-3, 3, 0.25)

    # Histogram with marginal distributions
    fig, axs = uplt.subplots(ncols=2, refwidth=2.3)
    axs.format(
        abc="A.",
        abcloc="l",
        titleabove=True,
        ylabel="y axis",
        suptitle="Histograms with marginal distributions",
    )
    colors = ("indigo9", "red9")
    titles = ("Group 1", "Group 2")
    for ax, which, color, title in zip(axs, "lr", colors, titles):
        ax.hist2d(
            x,
            y,
            bins,
            vmin=0,
            vmax=10,
            levels=50,
            cmap=color,
            colorbar="b",
            colorbar_kw={"label": "count"},
        )
        color = uplt.scale_luminance(color, 1.5)  # histogram colors
        px = ax.panel(which, space=0)
        px.histh(y, bins, color=color, fill=True, ec="k")
        px.format(grid=False, xlocator=[], xreverse=(which == "l"))
        px = ax.panel("t", space=0)
        px.hist(x, bins, color=color, fill=True, ec="k")
        px.format(grid=False, ylocator=[], title=title, titleloc="l")
    return fig


@pytest.mark.mpl_image_compare
def test_input_violin_box_options():
    """
    Test various box options in violin plots.
    """
    data = np.array([0, 1, 2, 3]).reshape(-1, 1)

    fig, axes = uplt.subplots(ncols=4)
    axes[0].bar(data, median=True, boxpctiles=True, bars=False)
    axes[0].format(title="boxpctiles")

    axes[1].bar(data, median=True, boxpctile=True, bars=False)
    axes[1].format(title="boxpctile")

    axes[2].bar(data, median=True, boxstd=True, bars=False)
    axes[2].format(title="boxstd")

    axes[3].bar(data, median=True, boxstds=True, bars=False)
    axes[3].format(title="boxstds")
    return fig


@pytest.mark.mpl_image_compare
def test_ridgeline_basic(rng):
    """
    Test basic ridgeline plot functionality.
    """
    # Generate test data with different means
    data = [rng.normal(i, 1, 500) for i in range(5)]
    labels = [f"Group {i+1}" for i in range(5)]

    fig, ax = uplt.subplots(figsize=(8, 6))
    ax.ridgeline(data, labels=labels, overlap=0.5, alpha=0.7)
    ax.format(
        title="Basic Ridgeline Plot",
        xlabel="Value",
        grid=False,
    )
    return fig


@pytest.mark.mpl_image_compare
def test_ridgeline_colormap(rng):
    """
    Test ridgeline plot with colormap.
    """
    # Generate test data
    data = [rng.normal(i * 0.5, 1, 300) for i in range(6)]
    labels = [f"Distribution {i+1}" for i in range(6)]

    fig, ax = uplt.subplots(figsize=(8, 6))
    ax.ridgeline(
        data,
        labels=labels,
        overlap=0.7,
        cmap="viridis",
        alpha=0.8,
        linewidth=2,
    )
    ax.format(
        title="Ridgeline Plot with Colormap",
        xlabel="Value",
        grid=False,
    )
    return fig


@pytest.mark.mpl_image_compare
def test_ridgeline_horizontal(rng):
    """
    Test horizontal ridgeline plot (vertical orientation).
    """
    # Generate test data
    data = [rng.normal(i, 0.8, 400) for i in range(4)]
    labels = ["Alpha", "Beta", "Gamma", "Delta"]

    fig, ax = uplt.subplots(figsize=(6, 8))
    ax.ridgelineh(
        data,
        labels=labels,
        overlap=0.6,
        facecolor="skyblue",
        alpha=0.6,
    )
    ax.format(
        title="Horizontal Ridgeline Plot",
        ylabel="Value",
        grid=False,
    )
    return fig


@pytest.mark.mpl_image_compare
def test_ridgeline_custom_colors(rng):
    """
    Test ridgeline plot with custom colors.
    """
    # Generate test data
    data = [rng.normal(i * 2, 1.5, 350) for i in range(4)]
    labels = ["Red", "Green", "Blue", "Yellow"]
    colors = ["red", "green", "blue", "yellow"]

    fig, ax = uplt.subplots(figsize=(8, 6))
    ax.ridgeline(
        data,
        labels=labels,
        overlap=0.5,
        facecolor=colors,
        alpha=0.7,
        edgecolor="black",
        linewidth=1.5,
    )
    ax.format(
        title="Ridgeline Plot with Custom Colors",
        xlabel="Value",
        grid=False,
    )
    return fig


def test_ridgeline_empty_data():
    """
    Test that ridgeline plot raises error with empty data.
    """
    fig, ax = uplt.subplots()
    with pytest.raises(ValueError, match="No valid distributions to plot"):
        ax.ridgeline([[], []])


def test_ridgeline_label_mismatch():
    """
    Test that ridgeline plot raises error when labels don't match data length.
    """
    data = [np.random.normal(0, 1, 100) for _ in range(3)]
    labels = ["A", "B"]  # Only 2 labels for 3 distributions

    fig, ax = uplt.subplots()
    with pytest.raises(ValueError, match="Number of labels.*must match"):
        ax.ridgeline(data, labels=labels)


@pytest.mark.mpl_image_compare
def test_ridgeline_histogram(rng):
    """
    Test ridgeline plot with histograms instead of KDE.
    """
    # Generate test data with different means
    data = [rng.normal(i * 1.5, 1, 500) for i in range(5)]
    labels = [f"Group {i+1}" for i in range(5)]

    fig, ax = uplt.subplots(figsize=(8, 6))
    ax.ridgeline(
        data,
        labels=labels,
        overlap=0.5,
        alpha=0.7,
        hist=True,
        bins=20,
    )
    ax.format(
        title="Ridgeline Plot with Histograms",
        xlabel="Value",
        grid=False,
    )
    return fig


@pytest.mark.mpl_image_compare
def test_ridgeline_histogram_colormap(rng):
    """
    Test ridgeline histogram plot with colormap.
    """
    # Generate test data
    data = [rng.normal(i * 0.8, 1.2, 400) for i in range(6)]
    labels = [f"Dist {i+1}" for i in range(6)]

    fig, ax = uplt.subplots(figsize=(8, 6))
    ax.ridgeline(
        data,
        labels=labels,
        overlap=0.6,
        cmap="plasma",
        alpha=0.75,
        hist=True,
        bins=25,
        linewidth=1.5,
    )
    ax.format(
        title="Histogram Ridgeline with Plasma Colormap",
        xlabel="Value",
        grid=False,
    )
    return fig


@pytest.mark.mpl_image_compare
def test_ridgeline_comparison_kde_vs_hist(rng):
    """
    Test comparison of KDE vs histogram ridgeline plots.
    """
    # Generate test data
    data = [rng.normal(i, 0.8, 300) for i in range(4)]
    labels = ["A", "B", "C", "D"]

    fig, axs = uplt.subplots(ncols=2, figsize=(12, 5))

    # KDE version
    axs[0].ridgeline(
        data,
        labels=labels,
        overlap=0.5,
        cmap="viridis",
        alpha=0.7,
    )
    axs[0].format(title="KDE Ridgeline", xlabel="Value", grid=False)

    # Histogram version
    axs[1].ridgeline(
        data,
        labels=labels,
        overlap=0.5,
        cmap="viridis",
        alpha=0.7,
        hist=True,
        bins=15,
    )
    axs[1].format(title="Histogram Ridgeline", xlabel="Value", grid=False)

    fig.format(suptitle="KDE vs Histogram Ridgeline Comparison")
    return fig
