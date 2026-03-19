#!/usr/bin/env python3
"""
Focused tests for scale and transform helpers.
"""

from __future__ import annotations

import numpy as np
import pytest
import matplotlib.scale as mscale
import matplotlib.ticker as mticker

import ultraplot as uplt
from ultraplot import scale as pscale
from ultraplot.internals.warnings import UltraPlotWarning


class DummyAxis:
    axis_name = "x"

    def __init__(self) -> None:
        self.isDefault_majloc = True
        self.isDefault_minloc = True
        self.isDefault_majfmt = True
        self.isDefault_minfmt = True
        self.major_locator = None
        self.minor_locator = None
        self.major_formatter = None
        self.minor_formatter = None

    def set_major_locator(self, locator) -> None:
        self.major_locator = locator

    def set_minor_locator(self, locator) -> None:
        self.minor_locator = locator

    def set_major_formatter(self, formatter) -> None:
        self.major_formatter = formatter

    def set_minor_formatter(self, formatter) -> None:
        self.minor_formatter = formatter


def test_parse_logscale_args_applies_defaults_and_eps():
    kwargs = pscale._parse_logscale_args("subs", "linthresh", subs=None, linthresh=1)

    assert np.array_equal(kwargs["subs"], np.arange(1, 10))
    assert kwargs["linthresh"] > 1


def test_scale_sets_default_locators_and_formatters():
    axis = DummyAxis()
    scale = pscale.LinearScale()

    with uplt.rc.context({"xtick.minor.visible": False}):
        scale.set_default_locators_and_formatters(axis)

    assert isinstance(axis.major_locator, mticker.AutoLocator)
    assert isinstance(axis.minor_locator, mticker.NullLocator)
    assert axis.major_formatter is not None
    assert isinstance(axis.minor_formatter, mticker.NullFormatter)


def test_scale_respects_only_if_default():
    axis = DummyAxis()
    axis.isDefault_majloc = False
    axis.isDefault_minloc = False
    axis.isDefault_majfmt = False
    axis.isDefault_minfmt = False
    sentinel = object()
    axis.major_locator = sentinel
    axis.minor_locator = sentinel
    axis.major_formatter = sentinel
    axis.minor_formatter = sentinel

    pscale.LinearScale().set_default_locators_and_formatters(axis, only_if_default=True)

    assert axis.major_locator is sentinel
    assert axis.minor_locator is sentinel
    assert axis.major_formatter is sentinel
    assert axis.minor_formatter is sentinel


def test_func_transform_roundtrip_and_validation():
    transform = pscale.FuncTransform(
        lambda values: values + 1, lambda values: values - 1
    )
    values = np.array([1.0, 2.0, 3.0])

    assert np.allclose(transform.transform_non_affine(values), values + 1)
    assert np.allclose(transform.inverted().transform_non_affine(values), values - 1)

    with pytest.raises(ValueError, match="must be functions"):
        pscale.FuncTransform("bad", lambda values: values)


def test_func_scale_accepts_callable_tuple_and_scale_specs():
    direct = pscale.FuncScale(transform=lambda values: values + 2)
    assert np.allclose(direct.get_transform().transform([1.0]), [3.0])

    swapped = pscale.FuncScale(
        transform=(lambda values: values * 2, lambda values: values / 2),
        invert=True,
    )
    assert np.allclose(swapped.get_transform().transform([4.0]), [2.0])

    inherited = pscale.FuncScale(transform="inverse")
    assert np.isclose(inherited.get_transform().transform([4.0])[0], 0.25)


def test_func_scale_rewrites_parent_scales_and_validates_inputs():
    cutoff_parent = pscale.CutoffScale(10, 2, 20)
    func_scale = pscale.FuncScale(
        transform=(lambda values: values + 1, lambda values: values - 1),
        parent_scale=cutoff_parent,
    )
    assert func_scale.get_transform() is not None

    symlog_parent = pscale.SymmetricalLogScale(linthresh=1)
    transformed = pscale.FuncScale(
        transform=(lambda values: values + 1, lambda values: values - 1),
        parent_scale=symlog_parent,
    )
    assert transformed.get_transform() is not None

    with pytest.raises(ValueError, match="Expected a function"):
        pscale.FuncScale(transform="unknown-scale")
    with pytest.raises(ValueError, match="Parent scale must be ScaleBase"):
        pscale.FuncScale(transform=lambda values: values, parent_scale="bad")
    with pytest.raises(TypeError, match="unexpected arguments"):
        pscale.FuncScale(transform=lambda values: values, unexpected=True)


@pytest.mark.parametrize(
    ("scale", "values", "expected"),
    [
        (pscale.PowerScale(power=2), np.array([1.0, 2.0]), np.array([1.0, 4.0])),
        (pscale.ExpScale(a=2, b=2, c=3), np.array([0.0, 1.0]), np.array([3.0, 12.0])),
        (pscale.InverseScale(), np.array([2.0, 4.0]), np.array([0.5, 0.25])),
    ],
)
def test_basic_scale_transforms(scale, values, expected):
    assert np.allclose(scale.get_transform().transform(values), expected)
    assert scale.get_transform().inverted() is not None


@pytest.mark.parametrize(
    "scale",
    [pscale.PowerScale(power=2), pscale.ExpScale(a=2, b=1, c=1), pscale.InverseScale()],
)
def test_positive_only_scales_limit_ranges(scale):
    lo, hi = scale.limit_range_for_scale(-2, 5, np.nan)
    assert lo > 0
    assert hi == 5


def test_mercator_scale_validates_threshold_and_masks_invalid_values():
    with pytest.raises(ValueError, match="must be <= 90"):
        pscale.MercatorLatitudeScale(thresh=90)

    transform = pscale.MercatorLatitudeScale(thresh=80).get_transform()
    masked = transform.transform_non_affine(np.array([-95.0, -45.0, 0.0, 45.0, 95.0]))
    assert np.ma.isMaskedArray(masked)
    assert masked.mask[0]
    assert masked.mask[-1]
    assert np.allclose(
        transform.inverted().transform_non_affine(
            transform.transform_non_affine(np.array([0.0, 30.0]))
        ),
        [0.0, 30.0],
    )


def test_sine_scale_masks_invalid_values_and_roundtrips():
    transform = pscale.SineLatitudeScale().get_transform()
    masked = transform.transform_non_affine(np.array([-95.0, -45.0, 0.0, 45.0, 95.0]))
    assert np.ma.isMaskedArray(masked)
    assert masked.mask[0]
    assert masked.mask[-1]
    assert np.allclose(
        transform.inverted().transform_non_affine(
            transform.transform_non_affine(np.array([-60.0, 30.0]))
        ),
        [-60.0, 30.0],
    )


def test_cutoff_transform_roundtrip_and_validation():
    transform = pscale.CutoffTransform([10, 20], [2, 1])
    values = np.array([0.0, 10.0, 15.0, 25.0])
    roundtrip = transform.inverted().transform_non_affine(
        transform.transform_non_affine(values)
    )
    assert np.allclose(roundtrip, values)

    with pytest.raises(ValueError, match="Got 2 but 1 scales"):
        pscale.CutoffTransform([10, 20], [1])
    with pytest.raises(ValueError, match="non negative"):
        pscale.CutoffTransform([10, 20], [-1, 1])
    with pytest.raises(ValueError, match="Final scale must be finite"):
        pscale.CutoffTransform([10], [0])
    with pytest.raises(ValueError, match="monotonically increasing"):
        pscale.CutoffTransform([20, 10], [1, 1])
    with pytest.raises(ValueError, match="zero_dists is required"):
        pscale.CutoffTransform([10, 10], [0, 1])
    with pytest.raises(ValueError, match="disagree with discrete step locations"):
        pscale.CutoffTransform([10, 10], [1, 1], zero_dists=[1])


def test_scale_factory_handles_instances_mpl_scales_and_unknown_names(monkeypatch):
    linear = pscale.LinearScale()
    with pytest.warns(UltraPlotWarning, match="Ignoring args"):
        assert pscale._scale_factory(linear, object(), 1, foo=2) is linear

    class DummyMplScale(mscale.ScaleBase):
        name = "dummy_mpl"

        def __init__(self, axis, *args, **kwargs):
            super().__init__(axis)
            self.axis = axis
            self.args = args
            self.kwargs = kwargs

        def get_transform(self):
            return pscale.LinearScale().get_transform()

        def set_default_locators_and_formatters(self, axis):
            return None

        def limit_range_for_scale(self, vmin, vmax, minpos):
            return vmin, vmax

    monkeypatch.setitem(mscale._scale_mapping, "dummy_mpl", DummyMplScale)
    axis = object()
    dummy = pscale._scale_factory("dummy_mpl", axis, 1, color="red")
    assert isinstance(dummy, DummyMplScale)
    assert dummy.axis is axis
    assert dummy.args == (1,)
    assert dummy.kwargs == {"color": "red"}

    with pytest.raises(ValueError, match="Unknown axis scale"):
        pscale._scale_factory("unknown", axis)
