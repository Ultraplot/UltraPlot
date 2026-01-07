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


def test_ridgeline_kde_kw(rng):
    """
    Test that kde_kw parameter passes arguments to gaussian_kde correctly.
    """
    data = [rng.normal(i, 1, 300) for i in range(3)]
    labels = ["A", "B", "C"]

    # Test with custom bandwidth
    fig, ax = uplt.subplots()
    artists = ax.ridgeline(
        data,
        labels=labels,
        overlap=0.5,
        kde_kw={"bw_method": 0.5},
    )
    assert len(artists) == 3
    uplt.close(fig)

    # Test with weights
    fig, ax = uplt.subplots()
    weights = np.ones(300) * 2  # Uniform weights
    artists = ax.ridgeline(
        data,
        labels=labels,
        overlap=0.5,
        kde_kw={"weights": weights},
    )
    assert len(artists) == 3
    uplt.close(fig)

    # Test with silverman bandwidth
    fig, ax = uplt.subplots()
    artists = ax.ridgeline(
        data,
        labels=labels,
        overlap=0.5,
        kde_kw={"bw_method": "silverman"},
    )
    assert len(artists) == 3
    uplt.close(fig)


def test_ridgeline_points(rng):
    """
    Test that points parameter controls KDE evaluation points.
    """
    data = [rng.normal(i, 1, 300) for i in range(3)]
    labels = ["A", "B", "C"]

    # Test with different point counts
    for points in [50, 200, 500]:
        fig, ax = uplt.subplots()
        artists = ax.ridgeline(
            data,
            labels=labels,
            overlap=0.5,
            points=points,
        )
        assert len(artists) == 3
        uplt.close(fig)


@pytest.mark.mpl_image_compare
def test_ridgeline_continuous_positioning(rng):
    """
    Test continuous (coordinate-based) positioning mode.
    """
    # Simulate temperature data at different depths
    depths = [0, 10, 25, 50, 100]
    mean_temps = [25, 22, 18, 12, 8]
    data = [rng.normal(temp, 2, 400) for temp in mean_temps]
    labels = ["Surface", "10m", "25m", "50m", "100m"]

    fig, ax = uplt.subplots(figsize=(8, 7))
    ax.ridgeline(
        data,
        labels=labels,
        positions=depths,
        height=8,
        cmap="coolwarm",
        alpha=0.75,
    )
    ax.format(
        title="Ocean Temperature by Depth (Continuous)",
        xlabel="Temperature (°C)",
        ylabel="Depth (m)",
        grid=True,
    )
    return fig


@pytest.mark.mpl_image_compare
def test_ridgeline_continuous_vs_categorical(rng):
    """
    Test comparison of continuous vs categorical positioning.
    """
    data = [rng.normal(i * 2, 1.5, 300) for i in range(4)]
    labels = ["A", "B", "C", "D"]

    fig, axs = uplt.subplots(ncols=2, figsize=(12, 5))

    # Categorical mode
    axs[0].ridgeline(data, labels=labels, overlap=0.6, cmap="viridis", alpha=0.7)
    axs[0].format(title="Categorical Positioning", xlabel="Value", grid=False)

    # Continuous mode
    positions = [0, 5, 15, 30]
    axs[1].ridgeline(
        data, labels=labels, positions=positions, height=4, cmap="viridis", alpha=0.7
    )
    axs[1].format(
        title="Continuous Positioning", xlabel="Value", ylabel="Coordinate", grid=True
    )

    return fig


def test_ridgeline_continuous_errors(rng):
    """
    Test error handling in continuous positioning mode.
    """
    data = [rng.normal(i, 1, 300) for i in range(3)]

    # Test position length mismatch
    fig, ax = uplt.subplots()
    with pytest.raises(ValueError, match="Number of positions.*must match"):
        ax.ridgeline(data, positions=[0, 10])
    uplt.close(fig)

    # Test height length mismatch
    fig, ax = uplt.subplots()
    with pytest.raises(ValueError, match="Number of heights.*must match"):
        ax.ridgeline(data, positions=[0, 10, 20], height=[5, 10])
    uplt.close(fig)


def test_ridgeline_continuous_auto_height(rng):
    """
    Test automatic height determination in continuous mode.
    """
    data = [rng.normal(i, 1, 300) for i in range(3)]
    positions = [0, 10, 25]

    # Test auto height (should work without error)
    fig, ax = uplt.subplots()
    artists = ax.ridgeline(data, positions=positions)
    assert len(artists) == 3
    uplt.close(fig)

    # Test with single position
    fig, ax = uplt.subplots()
    artists = ax.ridgeline([data[0]], positions=[0])
    assert len(artists) == 1
    uplt.close(fig)
