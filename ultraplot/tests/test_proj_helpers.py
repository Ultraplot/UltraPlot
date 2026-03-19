#!/usr/bin/env python3
"""
Focused tests for custom projection helpers.
"""

from __future__ import annotations

import pytest

from cartopy.crs import Globe

from ultraplot import proj


@pytest.mark.parametrize(
    ("cls", "proj_name"),
    [
        (proj.Aitoff, "aitoff"),
        (proj.Hammer, "hammer"),
        (proj.KavrayskiyVII, "kav7"),
        (proj.WinkelTripel, "wintri"),
    ],
)
def test_warped_projection_defaults_and_threshold(cls, proj_name):
    projection = cls(central_longitude=45, false_easting=1, false_northing=2)

    assert projection.proj4_params["proj"] == proj_name
    assert projection.proj4_params["lon_0"] == 45
    assert projection.proj4_params["x_0"] == 1
    assert projection.proj4_params["y_0"] == 2
    assert projection.threshold == pytest.approx(1e5)


@pytest.mark.parametrize(
    "cls",
    [proj.Aitoff, proj.Hammer, proj.KavrayskiyVII, proj.WinkelTripel],
)
def test_warped_projection_warns_for_elliptical_globes(cls):
    globe = Globe(semimajor_axis=10, semiminor_axis=9, ellipse=None)

    with pytest.warns(UserWarning, match="does not handle elliptical globes"):
        cls(globe=globe)


@pytest.mark.parametrize(
    ("cls", "central_latitude"),
    [
        (proj.NorthPolarAzimuthalEquidistant, 90),
        (proj.SouthPolarAzimuthalEquidistant, -90),
        (proj.NorthPolarLambertAzimuthalEqualArea, 90),
        (proj.SouthPolarLambertAzimuthalEqualArea, -90),
        (proj.NorthPolarGnomonic, 90),
        (proj.SouthPolarGnomonic, -90),
    ],
)
def test_polar_projection_sets_expected_central_latitude(cls, central_latitude):
    projection = cls(central_longitude=30)

    assert projection.proj4_params["lat_0"] == central_latitude
    assert projection.proj4_params["lon_0"] == 30
