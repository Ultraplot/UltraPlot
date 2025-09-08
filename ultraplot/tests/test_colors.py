import os
import pytest
import numpy as np
import matplotlib.colors as mcolors

from ultraplot import colors as pcolors
from ultraplot import config


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
    pcolors._cmap_database = pcolors._init_cmap_database()  # ensure pristine state
    # Before access, it should be a matplotlib colormap
    cmap_raw = pcolors._cmap_database._cmaps["viridis"]
    assert not isinstance(
        cmap_raw, (pcolors.ContinuousColormap, pcolors.DiscreteColormap)
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
    cmap = pcolors._cmap_database.get_cmap("viridis")
    cmap_r = pcolors._cmap_database.get_cmap("viridis_r")
    assert cmap_r.name.lower().startswith("_viridis_copy_r")
    assert np.allclose(cmap(0.0), cmap_r(1.0))


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
