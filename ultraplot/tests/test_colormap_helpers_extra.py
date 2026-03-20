#!/usr/bin/env python3
"""Additional branch coverage for colormap helpers and registries."""

import matplotlib.colors as mcolors
import pytest

from ultraplot import colors as pcolors
from ultraplot.internals.warnings import UltraPlotWarning


def _make_continuous() -> pcolors.ContinuousColormap:
    return pcolors.ContinuousColormap.from_list("helper_map", ["red", "blue"])


def test_colormap_utility_and_roundtrip_helpers(tmp_path, capsys):
    cmap = _make_continuous()

    assert cmap._make_name() == "_helper_map_copy"
    parsed = cmap._parse_path(str(tmp_path), ext="json", subfolder="cmaps")
    assert parsed.endswith("helper_map.json")
    assert "#" in cmap._get_data("hex")

    with pytest.raises(ValueError, match="Invalid extension"):
        cmap._get_data("bad")

    json_path = tmp_path / "helper_map.json"
    rgb_path = tmp_path / "helper_map.rgb"
    hex_path = tmp_path / "helper_cycle.hex"

    cmap.save(str(json_path))
    cmap.save(str(rgb_path))
    cycle = cmap.to_discrete(3, name="helper_cycle")
    cycle.save(str(hex_path))

    assert isinstance(
        pcolors.ContinuousColormap.from_file(str(json_path)),
        pcolors.ContinuousColormap,
    )
    assert isinstance(
        pcolors.ContinuousColormap.from_file(str(rgb_path)),
        pcolors.ContinuousColormap,
    )
    assert isinstance(
        pcolors.DiscreteColormap.from_file(str(hex_path)),
        pcolors.DiscreteColormap,
    )

    assert "Saved colormap" in capsys.readouterr().out


def test_colormap_from_file_error_paths(tmp_path):
    missing = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError):
        pcolors.ContinuousColormap.from_file(str(missing))

    bad_json = tmp_path / "broken.json"
    bad_json.write_text("{broken")
    with pytest.warns(UltraPlotWarning, match="JSON decoding error"):
        assert (
            pcolors.ContinuousColormap.from_file(str(bad_json), warn_on_failure=True)
            is None
        )

    bad_rgb = tmp_path / "broken.rgb"
    bad_rgb.write_text("1 2\n3 4\n")
    with pytest.warns(UltraPlotWarning, match="Expected 3 or 4 columns"):
        assert (
            pcolors.ContinuousColormap.from_file(str(bad_rgb), warn_on_failure=True)
            is None
        )

    bad_hex = tmp_path / "broken.hex"
    bad_hex.write_text("not a hex string")
    with pytest.warns(UltraPlotWarning, match="HEX strings"):
        assert (
            pcolors.DiscreteColormap.from_file(str(bad_hex), warn_on_failure=True)
            is None
        )

    bad_xml = tmp_path / "broken.xml"
    bad_xml.write_text("<ColorMap><Point x='0' r='1'></ColorMap>")
    with pytest.warns(UltraPlotWarning, match="XML parsing error"):
        assert (
            pcolors.ContinuousColormap.from_file(str(bad_xml), warn_on_failure=True)
            is None
        )

    unknown = tmp_path / "broken.foo"
    unknown.write_text("noop")
    with pytest.warns(UltraPlotWarning, match="Unknown colormap file extension"):
        assert (
            pcolors.ContinuousColormap.from_file(str(unknown), warn_on_failure=True)
            is None
        )


def test_continuous_discrete_and_perceptual_colormap_methods():
    cmap = _make_continuous()
    assert cmap.append() is cmap

    with pytest.raises(TypeError, match="LinearSegmentedColormaps"):
        cmap.append("bad")

    assert isinstance(cmap.cut(-0.2), pcolors.ContinuousColormap)
    with pytest.raises(ValueError, match="Invalid cut"):
        cmap.cut(0.8, left=0.4, right=0.6)

    assert cmap.shifted(0) is cmap
    assert cmap.truncate(0, 1) is cmap
    assert isinstance(cmap.truncate(0.2, 0.8), pcolors.ContinuousColormap)
    assert isinstance(cmap.to_discrete(3), pcolors.DiscreteColormap)

    with pytest.raises(TypeError, match="Samples must be integer or iterable"):
        cmap.to_discrete(1.5)
    with pytest.raises(TypeError, match="Colors must be iterable"):
        pcolors.ContinuousColormap.from_list("bad", 1.0)

    cycle = pcolors.DiscreteColormap(["red", "red"], name="mono")
    assert cycle.monochrome is True
    assert cycle.append() is cycle

    with pytest.raises(TypeError, match="Arguments .* must be DiscreteColormap"):
        cycle.append("bad")

    assert cycle.shifted(0) is cycle
    assert cycle.truncate() is cycle
    assert cycle.reversed().name.endswith("_r")
    assert cycle.shifted(1).name.endswith("_s")

    pmap = pcolors.PerceptualColormap.from_list(
        ["blue", "white", "red"], adjust_grays=True
    )
    assert isinstance(pmap, pcolors.PerceptualColormap)
    pmap.set_gamma(2)
    assert isinstance(pmap.copy(gamma=1.5, space="hcl"), pcolors.PerceptualColormap)
    assert isinstance(pmap.to_continuous(), pcolors.ContinuousColormap)

    with pytest.raises(TypeError, match="unexpected keyword argument 'hue'"):
        pcolors.PerceptualColormap.from_color("red", hue=10)
    with pytest.raises(ValueError, match="Unknown colorspace"):
        pcolors.PerceptualColormap.from_hsl(space="bad")
    with pytest.raises(ValueError, match="Colors must be iterable"):
        pcolors.PerceptualColormap.from_list("bad", 1.0)


def test_color_and_colormap_database_helpers(tmp_path):
    color_db = pcolors.ColorDatabase(
        {"greything": "#010203", "kelley green": "#00ff00"}
    )
    assert color_db["graything"] == "#010203"
    assert color_db["kelly green"] == "#00ff00"

    with pytest.raises(ValueError, match="Must be string"):
        color_db._parse_key(1)

    helper_cycle = pcolors.DiscreteColormap(["red", "blue"], name="helper_cycle_db")
    helper_map = pcolors.ContinuousColormap.from_list(
        "helper_map_db", ["black", "white"]
    )
    pcolors._cmap_database.register(helper_cycle, name="helper_cycle_db", force=True)
    pcolors._cmap_database.register(helper_map, name="helper_map_db", force=True)

    rgba_cycle = color_db.cache._get_rgba(("helper_cycle_db", 1), None)
    assert rgba_cycle[:3] == pytest.approx(mcolors.to_rgba("blue")[:3])

    rgba_map = color_db.cache._get_rgba(("helper_map_db", 0.5), 0.4)
    assert rgba_map[3] == pytest.approx(0.4)

    with pytest.raises(ValueError, match="between 0 and 1"):
        color_db.cache._get_rgba(("helper_map_db", 2), None)
    with pytest.raises(ValueError, match="between 0 and 1"):
        color_db.cache._get_rgba(("helper_cycle_db", 5), None)

    assert isinstance(
        pcolors._get_cmap_subtype("helper_cycle_db", "discrete"),
        pcolors.DiscreteColormap,
    )
    with pytest.raises(RuntimeError, match="Invalid subtype"):
        pcolors._get_cmap_subtype("helper_cycle_db", "bad")
    with pytest.raises(ValueError, match="Invalid perceptual colormap name"):
        pcolors._get_cmap_subtype("helper_cycle_db", "perceptual")

    listed = mcolors.ListedColormap(["red", "green", "blue"], name="listed_db")
    assert isinstance(
        pcolors._translate_cmap(listed, listedthresh=2),
        pcolors.ContinuousColormap,
    )
    small_listed = mcolors.ListedColormap(["red", "blue"], name="small_listed_db")
    assert isinstance(
        pcolors._translate_cmap(small_listed, listedthresh=10),
        pcolors.DiscreteColormap,
    )

    base = mcolors.Colormap("base_db")
    assert pcolors._translate_cmap(base) is base

    lazy_hex = tmp_path / "lazy.hex"
    lazy_hex.write_text("#ff0000, #00ff00")
    lazy_db = pcolors.ColormapDatabase({})
    lazy_db.register_lazy("lazycycle", str(lazy_hex), "discrete")
    assert isinstance(lazy_db["lazycycle"], pcolors.DiscreteColormap)

    with pytest.raises(KeyError, match="Key must be a string"):
        lazy_db[1]
