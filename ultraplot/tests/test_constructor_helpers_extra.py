#!/usr/bin/env python3
"""Additional branch coverage for constructor helpers."""

import importlib

import cycler
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np
import pytest

import ultraplot as uplt
from ultraplot import colors as pcolors
from ultraplot import constructor
from ultraplot import scale as pscale
from ultraplot import ticker as pticker
from ultraplot.internals.warnings import UltraPlotWarning


def test_colormap_constructor_branches(tmp_path, monkeypatch):
    hex_path = tmp_path / "cycle.hex"
    hex_path.write_text("#ff0000, #00ff00, #0000ff")

    saved = {}

    def fake_save(self, **kwargs):
        saved.update(kwargs)

    monkeypatch.setattr(pcolors.DiscreteColormap, "save", fake_save)

    with pytest.warns(UltraPlotWarning, match="listmode='discrete'"):
        deprecated = constructor.Colormap(["red", "blue"], listmode="listed")
    assert isinstance(deprecated, pcolors.DiscreteColormap)

    cmap = constructor.Colormap(
        str(hex_path),
        filemode="discrete",
        samples=2,
        name="saved_cycle",
        save=True,
        save_kw={"path": str(tmp_path / "saved.hex")},
    )
    assert isinstance(cmap, pcolors.DiscreteColormap)
    assert cmap.name == "saved_cycle"
    assert saved["path"].endswith("saved.hex")

    perceptual = constructor.Colormap(
        hue=(0, 240),
        saturation=(100, 100),
        luminance=(100, 40),
        alpha=(0.25, 1.0),
    )
    assert isinstance(perceptual, pcolors.PerceptualColormap)
    assert "alpha" in perceptual._segmentdata

    reversed_color = constructor.Colormap("red_r")
    assert isinstance(reversed_color, pcolors.PerceptualColormap)

    with pytest.raises(ValueError, match="requires either positional arguments"):
        constructor.Colormap()
    with pytest.raises(ValueError, match="Invalid listmode"):
        constructor.Colormap(["red"], listmode="bad")
    with pytest.raises(ValueError, match="Got 2 colormap-specs but 3 values"):
        constructor.Colormap("Reds", "Blues", reverse=[True, False, True])
    with pytest.raises(ValueError, match="The colormap name must be a string"):
        constructor.Colormap(["red"], name=1)
    with pytest.raises(ValueError, match="Invalid colormap, color cycle, or color"):
        constructor.Colormap(object())


def test_cycle_constructor_branches():
    base = cycler.cycler(color=["red", "blue"])

    merged = constructor.Cycle(base, marker=["o"])
    assert merged.get_next() == {"color": "red", "marker": "o"}
    assert merged == constructor.Cycle(base, marker=["o"])

    sampled = constructor.Cycle("Blues", 3, marker=["x"])
    props = [sampled.get_next() for _ in range(3)]
    assert all(prop["marker"] == "x" for prop in props)

    with pytest.warns(UltraPlotWarning, match="Ignoring Cycle"):
        defaulted = constructor.Cycle(right=0.5)
    assert defaulted.get_next() == {"color": "black"}

    with pytest.warns(UltraPlotWarning, match="Ignoring Cycle"):
        ignored = constructor.Cycle(base, left=0.25)
    assert ignored.get_next()["color"] == "red"


def test_norm_locator_formatter_and_scale_branches():
    copied_norm = constructor.Norm(mcolors.Normalize(vmin=0, vmax=1))
    assert isinstance(copied_norm, mcolors.Normalize)
    assert copied_norm is not constructor.Norm(copied_norm)

    symlog = constructor.Norm(("symlog",), vmin=-1, vmax=1)
    assert symlog.linthresh == 1
    assert isinstance(constructor.Norm(("power", 2), vmin=0, vmax=1), mcolors.PowerNorm)

    with pytest.raises(ValueError, match="Invalid norm name"):
        constructor.Norm(object())
    with pytest.raises(ValueError, match="Unknown normalizer"):
        constructor.Norm("badnorm")

    copied_locator = constructor.Locator(mticker.MaxNLocator(4))
    assert isinstance(copied_locator, mticker.MaxNLocator)
    index_locator = constructor.Locator("index")
    assert index_locator._base == 1
    assert index_locator._offset == 0
    assert isinstance(constructor.Locator("logminor"), mticker.LogLocator)
    assert isinstance(constructor.Locator("logitminor"), mticker.LogitLocator)
    assert isinstance(
        constructor.Locator("symlogminor", base=10, linthresh=1),
        mticker.SymmetricalLogLocator,
    )
    assert isinstance(constructor.Locator(True), mticker.AutoLocator)
    assert isinstance(constructor.Locator(False), mticker.NullLocator)
    assert isinstance(constructor.Locator(2), mticker.MultipleLocator)
    assert isinstance(constructor.Locator([1, 2, 3]), mticker.FixedLocator)
    assert isinstance(
        constructor.Locator([1, 2, 3], discrete=True), pticker.DiscreteLocator
    )

    with pytest.raises(ValueError, match="Unknown locator"):
        constructor.Locator("not-a-locator")
    with pytest.raises(ValueError, match="Invalid locator"):
        constructor.Locator(object())

    copied_formatter = constructor.Formatter(mticker.ScalarFormatter())
    assert isinstance(copied_formatter, mticker.ScalarFormatter)
    assert isinstance(constructor.Formatter("{x:.1f}"), mticker.StrMethodFormatter)
    assert isinstance(
        constructor.Formatter("%0.1f", tickrange=(0, 1)),
        mticker.FormatStrFormatter,
    )
    assert isinstance(constructor.Formatter("%Y-%m", date=True), mdates.DateFormatter)
    assert isinstance(constructor.Formatter(("sigfig", 3)), pticker.SigFigFormatter)
    assert isinstance(constructor.Formatter(True), pticker.AutoFormatter)
    assert isinstance(constructor.Formatter(False), mticker.NullFormatter)
    assert isinstance(
        constructor.Formatter(["a", "b"], index=True), pticker.IndexFormatter
    )
    assert isinstance(
        constructor.Formatter(lambda value, pos=None: str(value)),
        mticker.FuncFormatter,
    )

    with pytest.raises(ValueError, match="Unknown formatter"):
        constructor.Formatter("not-a-formatter")
    with pytest.raises(ValueError, match="Invalid formatter"):
        constructor.Formatter(object())

    copied_scale = constructor.Scale(pscale.LinearScale())
    assert isinstance(copied_scale, pscale.LinearScale)

    tuple_scale = constructor.Scale(("power", 3))
    transformed = tuple_scale.get_transform().transform_non_affine(np.array([2.0]))
    assert transformed[0] == pytest.approx(8.0)

    with pytest.warns(UltraPlotWarning, match="scale \\*preset\\*"):
        quadratic = constructor.Scale("quadratic", 99)
    quadratic_values = quadratic.get_transform().transform_non_affine(np.array([3.0]))
    assert quadratic_values[0] == pytest.approx(9.0)

    with pytest.raises(ValueError, match="Unknown scale or preset"):
        constructor.Scale("not-a-scale")
    with pytest.raises(ValueError, match="Invalid scale name"):
        constructor.Scale(object())


def test_formatter_registry_refreshes_after_ticker_reload():
    import ultraplot.ticker

    importlib.reload(ultraplot.ticker)

    assert constructor.FORMATTERS["sigfig"] is pticker.SigFigFormatter
    formatter = constructor.Formatter(("sigfig", 3))
    assert isinstance(formatter, pticker.SigFigFormatter)


def test_proj_constructor_branches():
    ccrs = pytest.importorskip("cartopy.crs")

    proj = ccrs.PlateCarree()
    with pytest.warns(UltraPlotWarning, match="Ignoring Proj\\(\\) keyword"):
        same_proj = constructor.Proj(proj, backend="cartopy", lon0=10)
    assert same_proj is proj
    assert same_proj._proj_backend == "cartopy"

    with pytest.raises(ValueError, match="Invalid backend"):
        constructor.Proj("merc", backend="bad")
    with pytest.raises(ValueError, match="Unexpected projection"):
        constructor.Proj(10)
    with pytest.raises(ValueError, match="Must be passed to GeoAxes.format"):
        constructor.Proj("merc", backend="cartopy", round=True)
    with pytest.raises(ValueError, match="unknown cartopy projection class"):
        constructor.Proj("not-a-proj", backend="cartopy")
