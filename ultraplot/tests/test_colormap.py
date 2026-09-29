import numpy as np
import pytest

import ultraplot as uplt


def test_colormap_reversal():
    # Rainbow uses a callable which went wrong see
    # https://github.com/Ultraplot/UltraPlot/issues/294#issuecomment-3016653770
    cmap = uplt.Colormap("rainbow")
    cmap_r = cmap.reversed()
    for i in range(256):
        assert np.allclose(cmap(i), cmap_r(255 - i)), (
            f"Reversed colormap mismatch at index {i}"
        )


def test_colormap_name_sensitivty():
    assert "fire" in uplt.colormaps
    assert "Fire" in uplt.colormaps
