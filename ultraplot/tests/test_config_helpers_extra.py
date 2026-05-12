#!/usr/bin/env python3
"""Additional branch coverage for configuration helpers."""

import numpy as np
import pytest

from ultraplot import config
from ultraplot.internals.warnings import UltraPlotWarning


def _fresh_config() -> config.Configurator:
    return config.Configurator(local=False, user=False, default=True)


def test_style_dict_and_inference_helpers():
    with pytest.warns(UltraPlotWarning, match="not related to style"):
        filtered = config._filter_style_dict(
            {"backend": "agg", "axes.facecolor": "white"}
        )
    assert filtered == {"axes.facecolor": "white"}

    alias_style = config._get_style_dict("538")
    assert "axes.facecolor" in alias_style

    inline_style = config._get_style_dict({"axes.facecolor": "black"})
    assert inline_style["axes.facecolor"] == "black"

    combined = {"xtick.labelsize": 9, "axes.titlesize": 14, "text.color": "red"}
    inferred = config._infer_ultraplot_dict(combined)
    assert inferred["tick.labelsize"] == 9
    assert inferred["title.size"] == 14
    assert inferred["grid.labelcolor"] == "red"

    with pytest.raises(TypeError):
        config._get_style_dict(1)
    with pytest.raises(IOError, match="not found in the style library"):
        config._get_style_dict("definitely-not-a-style")


def test_configurator_validation_item_dicts_and_context(tmp_path):
    cfg = _fresh_config()

    with pytest.raises(KeyError, match="Must be string"):
        cfg._validate_key(1)

    key, value = cfg._validate_key("ticklen")
    assert key == "tick.len"
    assert value is None
    assert cfg._validate_value("tick.len", np.array(4.0)) == 4.0

    kw_ultraplot, kw_matplotlib = cfg._get_item_dicts("tick.len", 4)
    assert kw_matplotlib["xtick.minor.size"] == pytest.approx(4 * cfg["tick.lenratio"])
    assert kw_matplotlib["ytick.minor.size"] == pytest.approx(4 * cfg["tick.lenratio"])

    kw_ultraplot, kw_matplotlib = cfg._get_item_dicts("grid", True)
    assert kw_matplotlib["axes.grid"] is True
    assert kw_matplotlib["axes.grid.which"] in ("major", "minor", "both")

    kw_ultraplot, _ = cfg._get_item_dicts("abc.bbox", True)
    assert kw_ultraplot["abc.border"] is False

    style_path = tmp_path / "custom.mplstyle"
    style_path.write_text(
        "\n".join(
            (
                "xtick.labelsize: 11",
                "axes.titlesize: 14",
                "text.color: red",
            )
        )
    )
    kw_ultraplot, kw_matplotlib = cfg._get_item_dicts("style", str(style_path))
    assert kw_matplotlib["xtick.labelsize"] == 11
    assert "tick.labelsize" in kw_ultraplot
    assert kw_ultraplot["title.size"] == pytest.approx(14)
    assert kw_ultraplot["grid.labelcolor"] == "red"

    kw_ultraplot, kw_matplotlib = cfg._get_item_dicts("font.size", 12)
    assert "abc.size" in kw_ultraplot
    assert kw_matplotlib["font.size"] == 12

    with pytest.raises(ValueError, match="Invalid caching mode"):
        cfg._get_item_context("tick.len", mode=99)

    with cfg.context({"ticklen": 6}, mode=2):
        assert cfg.find("tick.len", context=True) == 6
        assert cfg.find("axes.facecolor", context=True) is None
        assert cfg._context_mode == 2
    assert cfg._context_mode == 0

    with pytest.raises(ValueError, match="Non-dictionary argument"):
        cfg.context(1)
    with pytest.raises(ValueError, match="Invalid mode"):
        cfg.context(mode=3)

    cfg.update("axes", labelsize=13)
    assert cfg["axes.labelsize"] == 13
    assert "labelsize" in cfg.category("axes")
    assert cfg.fill({"face": "axes.facecolor"})["face"] == cfg["axes.facecolor"]

    with pytest.raises(ValueError, match="Invalid rc category"):
        cfg.category("not-a-category")
    with pytest.raises(ValueError, match="Invalid arguments"):
        cfg.update("axes", {"labelsize": 1}, {"titlesize": 2})


def test_configurator_background_and_grid_helpers():
    cfg = _fresh_config()
    cfg["axes.grid"] = True
    cfg["axes.grid.which"] = "both"
    cfg["axes.grid.axis"] = "x"
    cfg["axes.axisbelow"] = "line"
    cfg["axes.facecolor"] = "white"
    cfg["axes.edgecolor"] = "black"
    cfg["axes.linewidth"] = 1.5

    with pytest.warns(UltraPlotWarning, match="patch_kw"):
        kw_face, kw_edge = cfg._get_background_props(
            patch_kw={"linewidth": 2},
            color="red",
            facecolor="blue",
        )
    assert kw_face["facecolor"] == "blue"
    assert kw_edge["edgecolor"] == "red"
    assert kw_edge["capstyle"] == "projecting"

    with pytest.raises(TypeError, match="Unexpected keyword"):
        cfg._get_background_props(unexpected=True)

    assert cfg._get_gridline_bool(axis="x", which="major") is True
    assert cfg._get_gridline_bool(axis="x", which="minor") is True
    assert cfg._get_gridline_bool(axis="y", which="major") is False

    props = cfg._get_gridline_props(which="major", native=False)
    assert props["zorder"] == pytest.approx(1.5)

    label_props = cfg._get_label_props(color="red")
    assert label_props["color"] == "red"

    with cfg.context({"xtick.top": True, "xtick.bottom": False}, mode=2):
        assert cfg._get_loc_string("xtick", axis="x") == "top"

    tick_props = cfg._get_tickline_props(axis="x", which="major")
    assert "size" in tick_props
    assert "color" in tick_props

    ticklabel_props = cfg._get_ticklabel_props(axis="x")
    assert "size" in ticklabel_props
    assert "color" in ticklabel_props

    assert cfg._get_axisbelow_zorder(True) == 0.5
    assert cfg._get_axisbelow_zorder(False) == 2.5
    assert cfg._get_axisbelow_zorder("line") == 1.5
    with pytest.raises(ValueError, match="Unexpected axisbelow value"):
        cfg._get_axisbelow_zorder("bad")


def test_configurator_path_resolution_and_file_io(tmp_path, monkeypatch):
    home = tmp_path / "home"
    xdg = tmp_path / "xdg"
    home.mkdir()
    xdg.mkdir()

    universal_dir = home / ".ultraplot"
    xdg_dir = xdg / "ultraplot"
    universal_dir.mkdir()
    xdg_dir.mkdir()

    loose_file = home / ".ultraplotrc"
    folder_file = universal_dir / "ultraplotrc"
    loose_file.write_text("tick.len: 5\n")
    folder_file.write_text("tick.len: 6\n")

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    monkeypatch.setattr(config.sys, "platform", "linux")

    assert config.Configurator._config_folder() == str(xdg_dir)
    with pytest.warns(
        UltraPlotWarning, match="conflicting default user ultraplot folders"
    ):
        assert config.Configurator.user_folder() == str(universal_dir)
    with pytest.warns(
        UltraPlotWarning, match="conflicting default user ultraplotrc files"
    ):
        assert config.Configurator.user_file() == str(loose_file)

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    visible = data_dir / "colors.txt"
    visible.write_text("blue : #0000ff\n")
    (data_dir / ".hidden.txt").write_text("hidden")

    monkeypatch.setattr(
        config,
        "_get_data_folders",
        lambda folder, **kwargs: [str(data_dir)],
    )
    assert list(
        config._iter_data_objects("colors", user=False, local=False, default=False)
    ) == [(0, str(visible))]

    with pytest.raises(FileNotFoundError):
        list(
            config._iter_data_objects(
                "colors",
                str(tmp_path / "missing.txt"),
                user=False,
                local=False,
                default=False,
            )
        )

    cfg = _fresh_config()
    rc_file = tmp_path / "sample.rc"
    rc_file.write_text(
        "\n".join(
            (
                "tick.len: 4",
                "illegal line",
                "unknown.key: 1",
                "tick.len: 5",
            )
        )
    )
    with pytest.warns(UltraPlotWarning):
        loaded = cfg._load_file(str(rc_file))
    assert loaded["tick.len"] == pytest.approx(5)

    save_path = tmp_path / "ultraplotrc"
    save_path.write_text("old config")
    cfg["tick.len"] = 7
    with pytest.warns(UltraPlotWarning, match="was moved to"):
        cfg.save(str(save_path), backup=True)
    assert save_path.exists()
    assert (tmp_path / "ultraplotrc.bak").exists()
