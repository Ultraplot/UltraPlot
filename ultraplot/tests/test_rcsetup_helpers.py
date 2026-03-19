#!/usr/bin/env python3
"""
Focused tests for rc setup validators and helpers.
"""

from __future__ import annotations

from cycler import cycler
import numpy as np
import pytest
import matplotlib.colors as mcolors

from ultraplot import colors as pcolors
from ultraplot.internals import rcsetup
from ultraplot.internals.warnings import UltraPlotWarning


def test_get_default_param_and_membership_validators():
    assert rcsetup._get_default_param("axes.edgecolor") is not None
    with pytest.raises(KeyError, match="Invalid key"):
        rcsetup._get_default_param("not-a-real-key")

    validator = rcsetup._validate_belongs("solid", True, None, 3)
    assert validator("SOLID") == "solid"
    assert validator(True) is True
    assert validator(None) is None
    assert validator(3) == 3
    with pytest.raises(ValueError, match="Options are"):
        validator("missing")


def test_misc_validators_cover_success_and_failure_paths():
    assert rcsetup._validate_abc([True, False]) is False
    assert rcsetup._validate_abc("abc") == "abc"
    assert rcsetup._validate_abc(("a", "b")) == ("a", "b")
    with pytest.raises(TypeError):
        rcsetup._validate_abc(3.5)

    original = rcsetup._rc_ultraplot_default["cftime.time_resolution_format"].copy()
    try:
        result = rcsetup._validate_cftime_resolution_format({"DAILY": "%Y"})
        assert result["DAILY"] == "%Y"
    finally:
        rcsetup._rc_ultraplot_default["cftime.time_resolution_format"] = original

    with pytest.raises(ValueError, match="expects a dict"):
        rcsetup._validate_cftime_resolution_format("bad")
    assert rcsetup._validate_cftime_resolution("DAILY") == "DAILY"
    with pytest.raises(TypeError, match="expecting str"):
        rcsetup._validate_cftime_resolution(1)
    with pytest.raises(ValueError, match="Unit not understood"):
        rcsetup._validate_cftime_resolution("weekly")

    assert rcsetup._validate_bool_or_iterable(True) is True
    assert rcsetup._validate_bool_or_iterable([1, 2]) == [1, 2]
    with pytest.raises(ValueError, match="bool or iterable"):
        rcsetup._validate_bool_or_iterable(object())

    assert rcsetup._validate_bool_or_string("name") == "name"
    with pytest.raises(ValueError, match="bool or string"):
        rcsetup._validate_bool_or_string(1.5)

    assert rcsetup._validate_fontprops("regular") == "regular"
    assert rcsetup._validate_fontsize("med-large") == "med-large"
    assert rcsetup._validate_fontsize(12) == 12
    with pytest.raises(ValueError, match="Invalid font size"):
        rcsetup._validate_fontsize("gigantic")


def test_cmap_color_and_label_validators():
    validator = rcsetup._validate_cmap("continuous")
    assert validator("viridis") == "viridis"

    cmap = mcolors.ListedColormap(["red", "blue"], name="helper_listed")
    assert validator(cmap) == "helper_listed"

    cycle_validator = rcsetup._validate_cmap("continuous", cycle=True)
    from_cycler = cycle_validator(cycler(color=["red", "blue"]))
    assert hasattr(from_cycler, "by_key")
    from_iterable = cycle_validator(["red", "blue"])
    assert hasattr(from_iterable, "by_key")
    with pytest.raises(ValueError, match="Invalid colormap"):
        validator(object())

    assert rcsetup._validate_color("auto", alternative="auto") == "auto"
    assert rcsetup._validate_color("red") == "red"
    with pytest.raises(ValueError, match="not a valid color arg"):
        rcsetup._validate_color("not-a-color")

    assert rcsetup._validate_labels("lr", lon=True) == [True, True, False, False]
    assert rcsetup._validate_labels(("left", "top"), lon=True) == [
        True,
        False,
        False,
        True,
    ]
    assert rcsetup._validate_labels([True, False], lon=False) == [
        True,
        False,
        False,
        False,
    ]
    with pytest.raises(ValueError, match="Invalid lonlabel string"):
        rcsetup._validate_labels("bad", lon=True)
    with pytest.raises(ValueError, match="Invalid latlabel string"):
        rcsetup._validate_labels([True, "bad"], lon=False)


def test_remaining_scalar_and_sequence_validators():
    validator = rcsetup._validate_or_none(rcsetup._validate_float)
    assert validator(None) is None
    assert validator("none") is None
    assert validator(2) == 2.0

    assert rcsetup._validate_float_or_iterable([1, 2.5]) == (1.0, 2.5)
    with pytest.raises(ValueError, match="float or iterable"):
        rcsetup._validate_float_or_iterable("bad")

    assert rcsetup._validate_string_or_iterable(("a", "b")) == ("a", "b")
    with pytest.raises(ValueError, match="string or iterable"):
        rcsetup._validate_string_or_iterable([1, 2])

    assert rcsetup._validate_rotation("vertical") == "vertical"
    assert rcsetup._validate_rotation(45) == 45.0

    unit_validator = rcsetup._validate_units("pt")
    assert unit_validator("12pt") == pytest.approx(12.0)
    assert rcsetup._validate_float_or_auto("auto") == "auto"
    assert rcsetup._validate_float_or_auto("1.5") == 1.5
    with pytest.raises(ValueError, match="float or 'auto'"):
        rcsetup._validate_float_or_auto("bad")

    assert rcsetup._validate_tuple_int_2(np.array([1, 2])) == (1, 2)
    assert rcsetup._validate_tuple_float_2([1, 2.5]) == (1.0, 2.5)
    with pytest.raises(ValueError, match="2 ints"):
        rcsetup._validate_tuple_int_2([1, 2, 3])
    with pytest.raises(ValueError, match="2 floats"):
        rcsetup._validate_tuple_float_2([1])


def test_rst_yaml_and_string_helpers_emit_expected_content():
    table = rcsetup._rst_table()
    assert "Key" in table
    assert "Description" in table

    assert rcsetup._to_string("#aabbcc") == "aabbcc"
    assert rcsetup._to_string(1.23456789) == "1.234568"
    assert rcsetup._to_string([1, 2]) == "1, 2"
    assert rcsetup._to_string({"k": 1}) == "{k: 1}"

    yaml_table = rcsetup._yaml_table(
        {"axes.alpha": (0.5, rcsetup._validate_float, "alpha value")},
        description=True,
    )
    assert "axes.alpha" in yaml_table
    assert "alpha value" in yaml_table

    with pytest.warns(UltraPlotWarning, match="Failed to write rc setting"):
        assert (
            rcsetup._yaml_table({"bad": (object(), rcsetup._validate_string, "desc")})
            == ""
        )


def test_rcparams_handles_renamed_removed_and_copy():
    params = rcsetup._RcParams({"axes.labelsize": "med-large"}, rcsetup._validate)
    assert params["axes.labelsize"] == "med-large"
    copied = params.copy()
    assert copied["axes.labelsize"] == "med-large"

    key_new, _ = rcsetup._rc_renamed["basemap"]
    with pytest.warns(UltraPlotWarning, match="deprecated"):
        checked_key, checked_value = rcsetup._RcParams._check_key("basemap", True)
    assert checked_key == key_new
    assert checked_value == "basemap"

    removed_key = next(iter(rcsetup._rc_removed))
    with pytest.raises(KeyError, match="was removed"):
        rcsetup._RcParams._check_key(removed_key)

    with pytest.raises(KeyError, match="Invalid rc key"):
        params["not-a-real-key"] = 1
    with pytest.raises(ValueError, match="Key axes.labelsize"):
        params["axes.labelsize"] = object()
