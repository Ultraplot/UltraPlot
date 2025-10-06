from cycler import V
import pandas as pd
from pandas.core.arrays.arrow.accessors import pa
import ultraplot as uplt, pytest, numpy as np
from unittest import mock
from unittest.mock import patch

from ultraplot.internals.warnings import UltraPlotWarning

"""
This file is used to test base properties of ultraplot.axes.plot. For higher order plotting related functions, please use 1d and 2plots
"""


def test_graph_nodes_kw():
    """Test the graph method by setting keywords for nodes"""
    import networkx as nx

    g = nx.path_graph(5)
    labels_in = {node: node for node in range(2)}

    fig, ax = uplt.subplots()
    nodes, edges, labels = ax.graph(g, nodes=[0, 1], labels=labels_in)

    # Expecting 2 nodes 1 edge
    assert len(edges.get_offsets()) == 1
    assert len(nodes.get_offsets()) == 2
    assert len(labels) == len(labels_in)


def test_graph_edges_kw():
    """Test the graph method by setting keywords for nodes"""
    import networkx as nx

    g = nx.path_graph(5)
    edges_in = [(0, 1)]

    fig, ax = uplt.subplots()
    nodes, edges, labels = ax.graph(g, edges=edges_in)

    # Expecting 2 nodes 1 edge
    assert len(edges.get_offsets()) == 1
    assert len(nodes.get_offsets()) == 5
    assert labels == False


def test_graph_input():
    """
    Test graph input methods. We allow for graphs, adjacency matrices, and edgelists.
    """
    import networkx as nx

    g = nx.path_graph(5)
    A = nx.to_numpy_array(g)
    el = np.array(g.edges())
    fig, ax = uplt.subplots()
    # Test input methods
    ax.graph(g)  # Graphs
    ax.graph(A)  # Adjcency matrices
    ax.graph(el)  # edgelists
    with pytest.raises(TypeError):
        ax.graph("invalid_input")


def test_graph_layout_input():
    """
    Test if layout is in a [0, 1] x [0, 1] box
    """
    import networkx as nx

    g = nx.path_graph(5)
    circular = nx.circular_layout(g)
    layouts = [None, nx.spring_layout, circular, "forceatlas2", "spring_layout"]
    fig, ax = uplt.subplots(ncols=len(layouts))
    for axi, layout in zip(ax[1:], layouts):
        axi.graph(g, layout=layout)


def test_graph_rescale():
    """
    Graphs can be normalized such that the node size is the same independnt of the fig size
    """
    import networkx as nx

    g = nx.path_graph(5)
    layout = nx.spring_layout(g)
    # shift layout outside the box
    layout = {node: np.array(pos) + np.array([10, 10]) for node, pos in layout.items()}

    fig, ax = uplt.subplots()
    nodes1 = ax.graph(g, layout=layout, rescale=True)[0]

    xlim_scaled = np.array(ax.get_xlim())
    ylim_scaled = np.array(ax.get_ylim())

    fig, ax = uplt.subplots()
    nodes2 = ax.graph(g, layout=layout, rescale=False)[0]

    for x, y in nodes1.get_offsets():
        assert x >= 0 and x <= 1
        assert y >= 0 and y <= 1
    for x, y in nodes2.get_offsets():
        assert x > 1
        assert y > 1


def test_violin_labels():
    """
    Test the labels functionality of violinplot and violinploth.
    """
    labels = "hello world !".split()
    fig, ax = uplt.subplots()
    bodies = ax.violinplot(y=[1, 2, 3], labels=labels)
    for label, body in zip(labels, bodies):
        assert body.get_label() == label

    # # Also test the horizontal ticks
    bodies = ax.violinploth(x=[1, 2, 3], labels=labels)
    ytick_labels = ax.get_yticklabels()
    for label, body in zip(labels, bodies):
        assert body.get_label() == label

    # Labels are padded if they are shorter than the data
    shorter_labels = [labels[0]]
    with pytest.warns(UltraPlotWarning):
        bodies = ax.violinplot(y=[[1, 2, 3], [2, 3, 4]], labels=shorter_labels)
        assert len(bodies) == 3
        assert bodies[0].get_label() == shorter_labels[0]


@pytest.mark.parametrize(
    "mpl_version, expected_key, expected_value",
    [
        ("3.10.0", "orientation", "vertical"),
        ("3.9.0", "vert", True),
    ],
)
def test_violinplot_mpl_versions(
    mpl_version: str,
    expected_key: str,
    expected_value: bool | str,
):
    """
    Test specific logic for violinplot to ensure that past and current versions work as expected.
    """
    fig, ax = uplt.subplots()
    with mock.patch("ultraplot.axes.plot._version_mpl", new=mpl_version):
        with mock.patch.object(ax.axes, "_call_native") as mock_call:
            # Note: implicit testing of labels passing. It should work
            ax.violinplot(y=[1, 2, 3], vert=True)

            mock_call.assert_called_once()
            _, kwargs = mock_call.call_args
            assert kwargs[expected_key] == expected_value
            if expected_key == "orientation":
                assert "vert" not in kwargs
            else:
                assert "orientation" not in kwargs


def test_violinplot_hatches():
    """
    Test the input on the hatches parameter. Either a singular or a list of strings. When a list is provided, it must be of the same length as the number of violins.
    """
    # should be ok
    fig, ax = uplt.subplots()
    ax.violinplot(y=[1, 2, 3], vert=True, hatch="x")

    with pytest.raises(ValueError):
        ax.violinplot(y=[1, 2, 3], vert=True, hatches=["x", "o"])


@pytest.mark.parametrize(
    "mpl_version, expected_key, expected_value",
    [
        ("3.10.0", "orientation", "vertical"),
        ("3.9.0", "vert", True),
    ],
)
def test_boxplot_mpl_versions(
    mpl_version: str,
    expected_key: str,
    expected_value: bool | str,
):
    """
    Test specific logic for violinplot to ensure that past and current versions work as expected.
    """
    fig, ax = uplt.subplots()
    with mock.patch("ultraplot.axes.plot._version_mpl", new=mpl_version):
        with mock.patch.object(ax.axes, "_call_native") as mock_call:
            # Note: implicit testing of labels passing. It should work
            ax.boxplot(y=[1, 2, 3], vert=True)

            mock_call.assert_called_once()
            _, kwargs = mock_call.call_args
            assert kwargs[expected_key] == expected_value
            if expected_key == "orientation":
                assert "vert" not in kwargs
            else:
                assert "orientation" not in kwargs


def test_quiver_discrete_colors(rng):
    """
    Edge case where colors are discrete for quiver plots
    """
    X = np.array([0, 1, 2])
    Y = np.array([0, 1, 2])

    U = np.array([1, 1, 0])
    V = np.array([0, 1, 1])

    colors = ["r", "g", "b"]

    fig, ax = uplt.subplots()
    q = ax.quiver(X, Y, U, V, color=colors, infer_rgb=True)
    expectations = [uplt.colors.mcolors.to_rgba(color) for color in colors]
    facecolors = q.get_facecolors()
    for expectation, facecolor in zip(expectations, facecolors):
        assert np.allclose(
            facecolor, expectation, 0.1
        ), f"Expected {expectation} but got {facecolor}"
    C = ["#ff0000", "#00ff00", "#0000ff"]
    ax.quiver(X - 1, Y, U, V, color=C, infer_rgb=True)

    # pass rgba values
    C = rng.random((3, 4))
    ax.quiver(X - 2, Y, U, V, C)
    ax.quiver(X - 3, Y, U, V, color="red", infer_rgb=True)
    uplt.close(fig)


def test_setting_log_with_rc():
    """
    Test setting log scale with rc context manager
    """
    import re

    x, y = np.linspace(0, 1e6, 10), np.linspace(0, 1e6, 10)

    def check_ticks(axis, target=True):
        pattern = r"\$\\mathdefault\{10\^\{(\d+)\}\}\$"
        for tick in axis.get_ticklabels():
            match = re.match(pattern, tick.get_text())
            expectation = False
            if match:
                expectation = True
            assert expectation == target

    def reset(ax):
        ax.set_xscale("linear")
        ax.set_yscale("linear")

    funcs = [
        "semilogx",
        "semilogy",
        "loglog",
    ]
    conditions = [
        ["x"],
        ["y"],
        ["x", "y"],
    ]

    with uplt.rc.context({"formatter.log": True}):
        fig, ax = uplt.subplots()
        for func, targets in zip(funcs, conditions):
            reset(ax)
            # Call the function
            getattr(ax, func)(x, y)
            # Check if the formatter is set
            for target in targets:
                axi = getattr(ax, f"{target}axis")
                check_ticks(axi, target=True)

    with uplt.rc.context({"formatter.log": False}):
        fig, ax = uplt.subplots()
        for func, targets in zip(funcs, conditions):
            reset(ax)
            getattr(ax, func)(x, y)
            for target in targets:
                axi = getattr(ax, f"{target}axis")
                check_ticks(axi, target=False)

    uplt.close(fig)


def test_shading_pcolor(rng):
    """
    Pcolormesh by default adjusts the plot by
    getting the edges of the data for x and y.
    This creates a conflict when shading is used
    such as nearest and Gouraud.
    """
    nx, ny = 5, 7
    x = np.linspace(0, 5, nx)
    y = np.linspace(0, 4, ny)
    X, Y = np.meshgrid(x, y)
    Z = rng.random((nx, ny)).T
    fig, ax = uplt.subplots()

    results = []

    # Custom wrapper to capture return values
    def wrapped_parse_2d_args(x, y, z, *args, **kwargs):
        out = original_parse_2d_args(x, y, z, *args, **kwargs)
        results.append(out[:3])  # Capture x, y, z only
        return out

    # Save original method
    original_parse_2d_args = ax[0]._parse_2d_args
    shadings = ["flat", "nearest", "gouraud"]

    with patch.object(ax[0], "_parse_2d_args", side_effect=wrapped_parse_2d_args):
        for shading in shadings:
            ax.pcolormesh(X, Y, Z, shading=shading)

    # Now check results
    for i, (shading, (x, y, z)) in enumerate(zip(shadings, results)):
        assert x.shape[0] == y.shape[0]
        assert x.shape[1] == y.shape[1]
        if shading == "flat":
            assert x.shape[0] == z.shape[0] + 1
            assert x.shape[1] == z.shape[1] + 1
        else:
            assert x.shape[0] == z.shape[0]
            assert x.shape[1] == z.shape[1]
    uplt.close(fig)


def test_cycle_with_singular_column(rng):
    """
    While parsing singular columns the ncycle attribute should
    be ignored.
    """

    cycle = "qual1"
    # Create mock data that triggers the cycle
    # when plot directly but is is ignored when plot in
    # a loop
    data = rng.random((3, 6))

    fig, ax = uplt.subplots()
    active_cycle = ax[0]._active_cycle
    original_init = uplt.constructor.Cycle.__init__
    with mock.patch.object(
        uplt.constructor.Cycle,
        "__init__",
        wraps=uplt.constructor.Cycle.__init__,
        autospec=True,
        side_effect=original_init,
    ) as mocked:
        ax[0]._active_cycle = active_cycle  # reset the cycler
        ax.plot(data, cycle=cycle)
        assert mocked.call_args.kwargs["N"] == 6

        ax[0]._active_cycle = active_cycle  # reset the cycler
        for col in data.T:
            ax.plot(col, cycle=cycle)
            assert "N" not in mocked.call_args.kwargs
    uplt.close(fig)


def test_colorbar_center_levels(rng):
    """
    Allow centering of the colorbar ticks to the center
    """
    data = rng.random((10, 10)) * 2 - 1
    expectation = np.linspace(-1, 1, uplt.rc["cmap.levels"])
    fig, ax = uplt.subplots(ncols=2)
    for axi, center_levels in zip(ax, [False, True]):
        h = axi.pcolormesh(data, colorbar="r", center_levels=center_levels)
        cbar = axi._colorbar_dict[("right", "center")]
        if center_levels:
            deltas = cbar.get_ticks() - expectation
            assert np.all(np.allclose(deltas, 0))
            # For centered levels we are off by 1;
            # We have 1 more boundary bin than the expectation
            assert len(cbar.norm.boundaries) == expectation.size + 1
            w = np.diff(expectation)[0]
            # We check if the expectation is a center for the
            # the boundary
            assert expectation[0] - w * 0.5 == cbar.norm.boundaries[0]
        axi.set_title(f"{center_levels=}")
    uplt.close(fig)


def test_center_labels_colormesh_data_type(rng):
    """
    Test if how center_levels respond for discrete of continuous data
    """
    data = rng.random((10, 10)) * 2 - 1
    fig, ax = uplt.subplots(ncols=2)
    for axi, discrete in zip(ax, [True, False]):
        axi.pcolormesh(
            data,
            discrete=discrete,
            center_levels=True,
            colorbar="r",
        )

    uplt.close(fig)


def test_pie_labeled_series_in_dataframes():
    """
    Test an edge case where labeled indices cause
    labels to be grouped and passed on to pie chart
    which does not support this way of parsing.

    This only occurs when dataframes are passed.
    See https://github.com/Ultraplot/UltraPlot/issues/259
    """
    data = pd.DataFrame(
        index=pd.Index(list("abcd"), name="x"),
        data=dict(y=range(1, 5)),
    )
    fig, ax = uplt.subplots()
    wedges, texts = ax.pie("y", data=data)
    for text, index in zip(texts, data.index):
        assert text.get_text() == index
    uplt.close(fig)


def test_color_parsing_for_none():
    """
    Ensure that none is not parsed to white
    """
    fig, ax = uplt.subplots()
    ax.scatter(0.4, 0.5, 100, fc="none", ec="k", alpha=0.2)
    ax.scatter(0.5, 0.5, 100, fc="none", ec="k")
    ax.scatter(0.6, 0.5, 100, fc="none", ec="k", alpha=1)
    for artist in ax[0].collections:
        assert artist.get_facecolor().shape[0] == 0
    uplt.close(fig)


@pytest.mark.mpl_image_compare
def test_inhomogeneous_violin(rng):
    """
    Test that inhomogeneous violin plots work correctly.
    """
    fig, ax = uplt.subplots()
    data = [rng.normal(size=100), rng.normal(size=200)]
    violins = ax.violinplot(data, vert=True, labels=["A", "B"])
    assert len(violins) == 2
    for violin in violins:
        assert violin.get_paths()  # Ensure paths are created
    return fig


@pytest.mark.mpl_image_compare
def test_curved_quiver(rng):
    # Create a grid
    x = np.linspace(-4, 4, 20)
    y = np.linspace(-3, 3, 20)
    X, Y = np.meshgrid(x, y)

    # Define a rotational vector field (circular flow)
    U = -Y
    V = X
    speed = np.sqrt(U**2 + V**2)

    # Create a figure and axes
    fig, axs = uplt.subplots(ncols=3, sharey=True, figsize=(12, 4))

    # Left plot: matplotlib's streamplot
    axs[0].streamplot(X, Y, U, V, color=speed)
    axs[0].set_title("streamplot (native)")

    # Middle plot: quiver
    axs[1].quiver(X, Y, U, V, speed)
    axs[1].set_title("quiver")

    # Right plot: curved_quiver
    m = axs[2].curved_quiver(
        X, Y, U, V, color=speed, arrow_at_end=True, scale=2.0, grains=10
    )
    axs[2].set_title("curved_quiver")
    fig.colorbar(m.lines, ax=axs[:], label="speed")
    return fig


def test_setup_grid_and_mask():
    """
    Test that _setup_grid_and_mask creates grid, mask, and domain map objects
    with expected attributes and shapes for a simple input.
    """
    x = np.linspace(0, 1, 5)
    y = np.linspace(0, 1, 5)
    grid, mask, dmap = uplt.axes.plot._setup_grid_and_mask(x, y, density=5)
    assert grid.shape == (5, 5)
    assert hasattr(mask, "shape")
    assert hasattr(dmap, "grid")
    assert hasattr(dmap, "mask")


def test_validate_vector_shapes_pass():
    """
    Test that _validate_vector_shapes passes when u and v match the grid shape.
    """
    x = np.linspace(0, 1, 3)
    y = np.linspace(0, 1, 3)
    grid, _, _ = uplt.axes.plot._setup_grid_and_mask(x, y, density=3)
    u = np.ones(grid.shape)
    v = np.ones(grid.shape)
    # Should not raise
    uplt.axes.plot._validate_vector_shapes(u, v, grid)


def test_validate_vector_shapes_fail():
    """
    Test that _validate_vector_shapes raises ValueError when u and v do not match the grid shape.
    """
    x = np.linspace(0, 1, 3)
    y = np.linspace(0, 1, 3)
    grid, _, _ = uplt.axes.plot._setup_grid_and_mask(x, y, density=3)
    u = np.ones((2, 2))
    v = np.ones(grid.shape)
    import pytest

    with pytest.raises(ValueError):
        uplt.axes.plot._validate_vector_shapes(u, v, grid)


def test_normalize_magnitude():
    """
    Test that _normalize_magnitude returns a normalized array with max value 1.0 and correct shape.
    """
    u = np.array([[1, 2], [3, 4]])
    v = np.array([[4, 3], [2, 1]])
    mag = uplt.axes.plot._normalize_magnitude(u, v)
    assert np.allclose(np.max(mag), 1.0)
    assert mag.shape == u.shape


def test_generate_start_points():
    """
    Test that _generate_start_points returns valid grid coordinates for seed points,
    and raises ValueError for points outside the grid boundaries.
    """
    x = np.linspace(0, 1, 5)
    y = np.linspace(0, 1, 5)
    grid, _, _ = uplt.axes.plot._setup_grid_and_mask(x, y, density=5)
    sp2 = uplt.axes.plot._generate_start_points(
        x, y, grains=5, start_points=None, grid=grid
    )
    assert sp2.shape[1] == 2
    # Should raise if outside boundaries
    import pytest

    bad_points = np.array([[10, 10]])
    with pytest.raises(ValueError):
        uplt.axes.plot._generate_start_points(
            x, y, grains=5, start_points=bad_points, grid=grid
        )


def test_calculate_trajectories():
    """
    Test that _calculate_trajectories calls the integrator for each seed point
    and returns lists of trajectories and edges of correct length.
    """

    # Use a dummy integrator that returns a fixed trajectory
    def dummy_integrate(xg, yg):
        return ([np.array([xg, xg + 1]), np.array([yg, yg + 1])], False)

    sp2 = np.array([[0, 0], [1, 1]])

    class DummyDMap:
        def data2grid(self, xs, ys):
            return xs, ys

    trajectories, edges = uplt.axes.plot._calculate_trajectories(
        sp2, DummyDMap(), dummy_integrate
    )
    assert len(trajectories) == 2
    assert len(edges) == 2


def test_handle_multicolor_lines():
    """
    Test that _handle_multicolor_lines returns masked color array, norm, cmap, and an empty line_colors list.
    """
    color = np.array([[0, 1], [2, 3]])
    norm = None
    cmap = None
    grid = mock.Mock()
    out_color, out_norm, out_cmap, line_colors = (
        uplt.axes.plot._handle_multicolor_lines(color, norm, cmap, grid)
    )
    assert out_color.shape == color.shape
    assert hasattr(out_norm, "autoscale")
    assert hasattr(out_cmap, "__call__")
    assert isinstance(line_colors, list)
