import os
import warnings

import matplotlib as mpl
import matplotlib.colors as mcolors
import pytest
import numpy as np

from ultraplot import colors as pcolors
from ultraplot import config


@pytest.mark.parametrize(
    ("N", "expected"),
    (
        (None, ["#ff0000", "#0000ff"]),
        (0, []),
        (1, ["#ff0000"]),
        (3, ["#ff0000", "#0000ff", "#ff0000"]),
    ),
)
def test_discrete_colormap_resizes_without_listed_n_warning(N, expected):
    """DiscreteColormap preserves N semantics without deprecated mpl input."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "error",
            message=r"Passing 'N' to ListedColormap.*",
            category=mpl.MatplotlibDeprecationWarning,
        )
        cmap = pcolors.DiscreteColormap(["red", "blue"], N=N)

    assert cmap.N == len(expected)
    assert [mcolors.to_hex(color) for color in cmap.colors] == expected


@pytest.mark.parametrize(
    ("N", "expected_size"),
    (
        (None, 3),
        (1, 1),
        (4, 4),
    ),
)
def test_discrete_colormap_expands_scalar_color(N, expected_size):
    """Scalar color strings produce the requested monochromatic colormap."""
    cmap = pcolors.DiscreteColormap("red", N=N)

    assert cmap.N == expected_size
    assert [mcolors.to_hex(color) for color in cmap.colors] == [
        "#ff0000"
    ] * expected_size
    assert cmap.monochrome is True


def test_discrete_colormap_resizing_preserves_alpha_override():
    """Alpha replacement is applied to every color after cycling the input."""
    cmap = pcolors.DiscreteColormap([(1, 0, 0, 0.2), (0, 0, 1, 0.8)], N=3, alpha=0.5)

    assert [mcolors.to_hex(color, keep_alpha=True) for color in cmap.colors] == [
        "#ff000080",
        "#0000ff80",
        "#ff000080",
    ]
    assert cmap.monochrome is False


@pytest.mark.parametrize(
    ("colors", "expected"),
    (
        (["red", "red"], True),
        (["red", "blue"], False),
    ),
)
def test_discrete_colormap_monochrome_is_python_bool(colors, expected):
    """Monochrome detection remains available across matplotlib versions."""
    cmap = pcolors.DiscreteColormap(colors)

    assert cmap.monochrome is expected


@pytest.fixture(autouse=True)
def setup_teardown():
    """
    Reset the colormap database before and after each test.
    """
    # This ensures a clean state for each test.
    # The singleton instance is replaced with a new one.
    pcolors._cmap_database = pcolors._init_cmap_database()
    config.register_cmaps(default=True)
    config.register_cycles(default=True)
    yield


def test_lazy_loading_builtin():
    """
    Test that built-in colormaps are lazy-loaded.
    """
    # Before access, it should be a matplotlib colormap
    cmap_raw = pcolors._cmap_database._cmaps["viridis"]
    assert isinstance(
        cmap_raw,
        (
            pcolors.ContinuousColormap,
            pcolors.DiscreteColormap,
            mcolors.ListedColormap,
        ),
    )

    # After access, it should be an ultraplot colormap
    cmap_get = pcolors._cmap_database.get_cmap("viridis")
    assert isinstance(cmap_get, pcolors.ContinuousColormap)

    # The internal representation should also be updated
    cmap_raw_after = pcolors._cmap_database._cmaps["viridis"]
    assert isinstance(cmap_raw_after, pcolors.ContinuousColormap)


def test_case_insensitivity():
    """
    Test that colormap lookup is case-insensitive.
    """
    cmap1 = pcolors._cmap_database.get_cmap("ViRiDiS")
    cmap2 = pcolors._cmap_database.get_cmap("viridis")
    assert cmap1.name.lower().startswith("_viridis")
    assert cmap2.name.lower().startswith("_viridis")


def test_reversed_shifted():
    """
    Test reversed and shifted colormaps.
    """
    # Create a simple colormap to test the reversal logic
    # This avoids dependency on the exact definition of 'viridis' in matplotlib
    colors_list = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]  # Red, Green, Blue
    test_cmap = pcolors.ContinuousColormap.from_list("test_cmap", colors_list)
    pcolors._cmap_database.register(test_cmap)

    cmap = pcolors._cmap_database.get_cmap("test_cmap")
    cmap_r = pcolors._cmap_database.get_cmap("test_cmap_r")

    # Check name
    assert cmap_r.name == "_test_cmap_copy_r"
    # Check colors
    # Start of original should be end of reversed
    assert np.allclose(cmap(0.0), cmap_r(1.0))
    # End of original should be start of reversed
    assert np.allclose(cmap(1.0), cmap_r(0.0))
    # Middle should be the same
    assert np.allclose(cmap(0.5)[:3], cmap_r(0.5)[:3][::-1])


def test_grays_translation():
    """
    Test that 'Grays' is translated to 'greys'.
    """
    cmap_grays = pcolors._cmap_database.get_cmap("Grays")
    assert cmap_grays.name.lower().startswith("_greys")


def test_lazy_loading_file(tmp_path):
    """
    Test that colormaps from files are lazy-loaded.
    """
    # Create a dummy colormap file
    cmap_data = "1, 0, 0\n0, 1, 0\n0, 0, 1"
    cmap_file = tmp_path / "my_test_cmap.rgb"
    cmap_file.write_text(cmap_data)

    # Register it lazily
    pcolors._cmap_database.register_lazy("my_test_cmap", str(cmap_file), "continuous")

    # Before access, it should be a lazy-load dict
    cmap_raw = pcolors._cmap_database._cmaps["my_test_cmap"]
    assert isinstance(cmap_raw, dict)
    assert cmap_raw["is_lazy"]

    # After access, it should be an ultraplot colormap
    cmap_get = pcolors._cmap_database.get_cmap("my_test_cmap")
    assert isinstance(cmap_get, pcolors.ContinuousColormap)
    assert cmap_get.name.lower().startswith("_my_test_cmap")

    # The internal representation should also be updated
    cmap_raw_after = pcolors._cmap_database._cmaps["my_test_cmap"]
    assert isinstance(cmap_raw_after, pcolors.ContinuousColormap)


def test_register_new():
    """
    Test registering a new colormap.
    """
    colors_list = [(0, 0, 0), (1, 1, 1)]
    new_cmap = pcolors.DiscreteColormap(colors_list, name="my_new_cmap")
    pcolors._cmap_database.register(new_cmap)

    # Check it was registered
    cmap_get = pcolors._cmap_database.get_cmap("my_new_cmap")
    assert cmap_get.name.lower().startswith(
        "_my_new_cmap"
    ), f"Received {cmap_get.name.lower()} expected _my_new_cmap"
    assert len(cmap_get.colors) == 2


def test_get_cmap_accepts_colormap_objects():
    """
    Colormap lookups should accept colormap objects directly.
    """
    cmap = pcolors._cmap_database.get_cmap("viridis")
    cmap_from_obj = pcolors._cmap_database.get_cmap(cmap)
    assert cmap_from_obj is not cmap
    assert cmap_from_obj.name == cmap.name
