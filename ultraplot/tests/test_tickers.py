import pytest, numpy as np, xarray as xr, ultraplot as uplt, cftime
from ultraplot.ticker import AutoCFDatetimeLocator
from unittest.mock import patch
import importlib
import cartopy.crs as ccrs


@pytest.mark.mpl_image_compare
def test_datetime_calendars_comparison():
    # Time axis centered at mid-month
    # Standard calendar
    time1 = xr.date_range("2000-01", periods=120, freq="MS")
    time2 = xr.date_range("2000-02", periods=120, freq="MS")
    time = time1 + 0.5 * (time2 - time1)
    # Non-standard calendar (uses cftime)
    time1 = xr.date_range("2000-01", periods=120, freq="MS", calendar="noleap")
    time2 = xr.date_range("2000-02", periods=120, freq="MS", calendar="noleap")
    time_noleap = time1 + 0.5 * (time2 - time1)

    da = xr.DataArray(
        data=np.sin(np.arange(0.0, 2 * np.pi, np.pi / 60.0)),
        dims=("time",),
        coords={
            "time": time,
        },
        attrs={"long_name": "low freq signal", "units": "normalized"},
    )

    da_noleap = xr.DataArray(
        data=np.sin(2.0 * np.arange(0.0, 2 * np.pi, np.pi / 60.0)),
        dims=("time",),
        coords={
            "time": time_noleap,
        },
        attrs={"long_name": "high freq signal", "units": "normalized"},
    )

    fig, axs = uplt.subplots(ncols=2)
    axs.format(title=("Standard calendar", "Non-standard calendar"))
    axs[0].plot(da)
    axs[1].plot(da_noleap)

    return fig


@pytest.mark.parametrize(
    "calendar",
    [
        "standard",
        "gregorian",
        "proleptic_gregorian",
        "julian",
        "all_leap",
        "360_day",
        "365_day",
        "366_day",
    ],
)
def test_datetime_calendars(calendar):
    time = xr.date_range("2000-01-01", periods=365 * 10, calendar=calendar)
    da = xr.DataArray(
        data=np.sin(np.linspace(0, 2 * np.pi, 365 * 10)),
        dims=("time",),
        coords={"time": time},
    )
    fig, ax = uplt.subplots()
    ax.plot(da)
    ax.format(title=f"Calendar: {calendar}")


@pytest.mark.mpl_image_compare
def test_datetime_short_range():
    time = xr.date_range("2000-01-01", periods=10, calendar="standard")
    da = xr.DataArray(
        data=np.sin(np.linspace(0, 2 * np.pi, 10)),
        dims=("time",),
        coords={"time": time},
    )
    fig, ax = uplt.subplots()
    ax.plot(da)
    ax.format(title="Short time range (days)")
    return fig


@pytest.mark.mpl_image_compare
def test_datetime_long_range():
    time = xr.date_range(
        "2000-01-01", periods=365 * 200, calendar="standard"
    )  # 200 years
    da = xr.DataArray(
        data=np.sin(np.linspace(0, 2 * np.pi, 365 * 200)),
        dims=("time",),
        coords={"time": time},
    )
    fig, ax = uplt.subplots()
    ax.plot(da)
    ax.format(title="Long time range (centuries)")
    return fig


def test_datetime_explicit_formatter():
    time = xr.date_range("2000-01-01", periods=365 * 2, calendar="noleap")
    da = xr.DataArray(
        data=np.sin(np.linspace(0, 2 * np.pi, 365 * 2)),
        dims=("time",),
        coords={"time": time},
    )
    fig, ax = uplt.subplots()

    formatter = uplt.ticker.CFDatetimeFormatter("%b %Y", calendar="noleap")
    locator = uplt.ticker.AutoCFDatetimeLocator(calendar="noleap")
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax.plot(da)

    fig.canvas.draw()

    labels = [label.get_text() for label in ax.get_xticklabels()]
    assert len(labels) > 1
    # check first label
    import cftime

    cftime.datetime.strptime(labels[1], "%b %Y", calendar="noleap")


@pytest.mark.parametrize(
    "date1, date2, num1, num2, expected_resolution, expected_n",
    [
        (
            cftime.datetime(2000, 1, 1, calendar="gregorian"),
            cftime.datetime(2020, 1, 1, calendar="gregorian"),
            0,
            7305,
            "YEARLY",
            20,
        ),
        (
            cftime.datetime(2000, 1, 1, calendar="gregorian"),
            cftime.datetime(2001, 1, 1, calendar="gregorian"),
            0,
            365,
            "MONTHLY",
            12,
        ),
        (
            cftime.datetime(2000, 1, 1, calendar="gregorian"),
            cftime.datetime(2000, 1, 10, calendar="gregorian"),
            0,
            9,
            "DAILY",
            9,
        ),
        (
            cftime.datetime(2000, 1, 1, calendar="gregorian"),
            cftime.datetime(2000, 1, 1, 12, calendar="gregorian"),
            0,
            0.5,
            "HOURLY",
            12,
        ),
        (
            cftime.datetime(2000, 1, 1, calendar="gregorian"),
            cftime.datetime(2000, 1, 1, 0, 0, 10, calendar="gregorian"),
            0,
            1.1574074074074073e-4,
            "SECONDLY",
            10,
        ),
    ],
)
def test_compute_resolution(date1, date2, num1, num2, expected_resolution, expected_n):
    locator = AutoCFDatetimeLocator()
    resolution, n = locator.compute_resolution(num1, num2, date1, date2)
    assert resolution == expected_resolution
    assert np.allclose(n, expected_n)


@pytest.mark.parametrize(
    "date1, date2, num1, num2",
    [
        (
            cftime.datetime(2000, 1, 1, calendar="gregorian"),
            cftime.datetime(2020, 1, 1, calendar="gregorian"),
            0,
            7305,
        ),
        (
            cftime.datetime(2000, 1, 1, calendar="gregorian"),
            cftime.datetime(2001, 1, 1, calendar="gregorian"),
            0,
            365,
        ),
        (
            cftime.datetime(2000, 1, 1, calendar="gregorian"),
            cftime.datetime(2000, 1, 10, calendar="gregorian"),
            0,
            9,
        ),
        (
            cftime.datetime(2000, 1, 1, calendar="gregorian"),
            cftime.datetime(2000, 1, 1, 12, calendar="gregorian"),
            0,
            0.5,
        ),
        (
            cftime.datetime(2000, 1, 1, calendar="gregorian"),
            cftime.datetime(2000, 1, 1, 0, 0, 10, calendar="gregorian"),
            0,
            1.1574074074074073e-4,
        ),
        # Additional test cases to cover the while loop
        (
            cftime.datetime(2000, 1, 1, calendar="gregorian"),
            cftime.datetime(2000, 12, 31, calendar="gregorian"),
            0,
            365,
        ),
        (
            cftime.datetime(2000, 1, 1, calendar="gregorian"),
            cftime.datetime(2000, 1, 2, calendar="gregorian"),
            0,
            1,
        ),
    ],
)
def test_tick_values(date1, date2, num1, num2):
    locator = AutoCFDatetimeLocator()
    locator.compute_resolution(num1, num2, date1, date2)
    ticks = locator.tick_values(num1, num2)
    assert len(ticks) > 0
    assert all(
        isinstance(
            cftime.num2date(t, locator.date_unit, calendar=locator.calendar),
            cftime.datetime,
        )
        for t in ticks
    )


def test_datetime_maxticks():
    time = xr.date_range("2000-01-01", periods=365 * 20, calendar="noleap")
    da = xr.DataArray(
        data=np.sin(np.linspace(0, 2 * np.pi, 365 * 20)),
        dims=("time",),
        coords={"time": time},
    )
    fig, ax = uplt.subplots()
    ax.plot(da)
    locator = ax.xaxis.get_major_locator()
    locator.set_params(maxticks=6)
    fig.canvas.draw()
    assert len(ax.get_xticks()) <= 6


@pytest.mark.parametrize("module_name", ["cftime", "cartopy.crs"])
def test_missing_modules(module_name):
    """Test fallback behavior when modules are missing."""
    with patch.dict("sys.modules", {module_name: None}):
        # Reload the ultraplot.ticker module to apply the mocked sys.modules
        import ultraplot.ticker

        importlib.reload(ultraplot.ticker)

        if module_name == "cftime":
            from ultraplot.ticker import cftime

            assert cftime is None
        elif module_name == "ccrs":
            from ultraplot.ticker import (
                ccrs,
                LatitudeFormatter,
                LongitudeFormatter,
                _PlateCarreeFormatter,
            )

            assert ccrs is None
            assert LatitudeFormatter is object
            assert LongitudeFormatter is object
            assert _PlateCarreeFormatter is object


def test_index_locator():
    from ultraplot.ticker import IndexLocator

    # Initialize with default values
    locator = IndexLocator()
    assert locator._base == 1
    assert locator._offset == 0

    # Update parameters
    locator.set_params(base=2, offset=1)
    assert locator._base == 2
    assert locator._offset == 1


def test_default_precision_zerotrim():
    from ultraplot.ticker import _default_precision_zerotrim

    # Case 1: Default behavior
    precision, zerotrim = _default_precision_zerotrim()
    assert precision == 6  # Default when zerotrim is True
    assert zerotrim is True

    # Case 2: Explicit precision and zerotrim
    precision, zerotrim = _default_precision_zerotrim(precision=3, zerotrim=False)
    assert precision == 3
    assert zerotrim is False


def test_index_locator_tick_values():
    from ultraplot.ticker import IndexLocator

    locator = IndexLocator(base=2, offset=1)
    ticks = locator.tick_values(0, 10)
    assert np.array_equal(ticks, [1, 3, 5, 7, 9])


def test_discrete_locator_call():
    from ultraplot.ticker import DiscreteLocator

    locator = DiscreteLocator(locs=[0, 1, 2, 3, 4])
    ticks = locator()
    assert np.array_equal(ticks, [0, 1, 2, 3, 4])


def test_discrete_locator_set_params():
    from ultraplot.ticker import DiscreteLocator

    locator = DiscreteLocator(locs=[0, 1, 2, 3, 4])
    locator.set_params(steps=[1, 2], nbins=3, minor=True, min_n_ticks=2)

    assert np.array_equal(locator._steps, [1, 2, 10])
    assert locator._nbins == 3
    assert locator._minor is True
    assert locator._min_n_ticks == 2


def test_discrete_locator_tick_values():
    from ultraplot.ticker import DiscreteLocator

    # Create a locator with specific locations
    locator = DiscreteLocator(locs=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    locator.set_params(steps=[1, 2], nbins=5, minor=False, min_n_ticks=2)

    ticks = locator.tick_values(None, None)

    assert np.array_equal(ticks, list(range(10)))


@pytest.mark.parametrize(
    "value, string, expected",
    [
        (1e-10, "0.0", True),  # Case 1: Small number close to zero
        (1000, "1000", False),  # Case 2: Large number
    ],
)
def test_auto_formatter_fix_small_number(value, string, expected):
    from ultraplot.ticker import AutoFormatter

    formatter = AutoFormatter()
    result = formatter._fix_small_number(value, string)
    if expected:
        assert result != string
    else:
        assert result == string


@pytest.mark.parametrize(
    "start_date, end_date",
    [
        (
            cftime.date2num(
                cftime.datetime(2000, 1, 1, calendar="gregorian"),
                "days since 2000-01-01",
            ),
            cftime.date2num(
                cftime.datetime(2020, 1, 1, calendar="gregorian"),
                "days since 2000-01-01",
            ),
        ),
        # Case 2: Monthly resolution
        (
            cftime.date2num(
                cftime.datetime(2000, 1, 1, calendar="gregorian"),
                "days since 2000-01-01",
            ),
            cftime.date2num(
                cftime.datetime(2000, 12, 31, calendar="gregorian"),
                "days since 2000-01-01",
            ),
        ),
    ],
)
def test_auto_datetime_locator_tick_values(start_date, end_date):
    from ultraplot.ticker import AutoCFDatetimeLocator

    locator = AutoCFDatetimeLocator(calendar="gregorian")
    import cftime

    ticks = locator.tick_values(start_date, end_date)
    assert len(ticks) > 0  # Ensure ticks are generated


@pytest.mark.parametrize(
    "start_date, end_date, calendar, expected_exception, expected_resolution",
    [
        (
            cftime.date2num(
                cftime.datetime(2000, 1, 1, calendar="gregorian"),
                "days since 2000-01-01",
            ),
            cftime.date2num(
                cftime.datetime(2020, 1, 1, calendar="gregorian"),
                "days since 2000-01-01",
            ),
            "gregorian",
            None,
            "YEARS",
        ),  # Case 1: Valid yearly resolution
        (
            cftime.date2num(
                cftime.datetime(2000, 1, 1, calendar="gregorian"),
                "days since 2000-01-01",
            ),
            cftime.date2num(
                cftime.datetime(2000, 12, 31, calendar="gregorian"),
                "days since 2000-01-01",
            ),
            "gregorian",
            None,
            "MONTHS",
        ),  # Case 2: Valid monthly resolution
        (
            cftime.date2num(
                cftime.datetime(2000, 1, 1, calendar="gregorian"),
                "days since 2000-01-01",
            ),
            cftime.date2num(
                cftime.datetime(2000, 1, 1, calendar="gregorian"),
                "days since 2000-01-01",
            ),
            "gregorian",
            None,
            "DAYS",
        ),  # Case 3: Empty range
        (
            cftime.date2num(
                cftime.datetime(2000, 1, 1, calendar="gregorian"),
                "days since 2000-01-01",
            ),
            cftime.date2num(
                cftime.datetime(2000, 12, 31, calendar="gregorian"),
                "days since 2000-01-01",
            ),
            "gregorian",
            None,
            "MONTHS",
        ),  # Case 4: Months data range
        (
            cftime.date2num(
                cftime.datetime(2000, 1, 1, calendar="gregorian"),
                "days since 2000-01-01",
            ),
            cftime.date2num(
                cftime.datetime(2000, 1, 1, calendar="gregorian"),
                "days since 2000-01-01",
            ),
            "gregorian",
            None,
            None,
        ),  # Case 5: Empty range (valid calendar)
    ],
)
def test_auto_datetime_locator_tick_values(
    start_date,
    end_date,
    calendar,
    expected_exception,
    expected_resolution,
):
    from ultraplot.ticker import AutoCFDatetimeLocator
    import cftime

    locator = AutoCFDatetimeLocator(calendar=calendar)
    resolution = expected_resolution
    if expected_exception == ValueError:
        with pytest.raises(
            ValueError, match="Incorrectly formatted CF date-time unit_string"
        ):
            cftime.date2num(
                cftime.datetime(2000, 1, 1, calendar="gregorian"), "invalid unit"
            )
    if expected_exception:
        with pytest.raises(expected_exception):
            locator.tick_values(start_date, end_date)
    else:
        ticks = locator.tick_values(start_date, end_date)
        assert len(ticks) > 0

        # Verify that the ticks are at the correct resolution
        if expected_resolution == "YEARLY":
            assert all(
                cftime.num2date(t, locator.date_unit, calendar=locator.calendar).month
                == 1
                for t in ticks
            )
            assert all(
                cftime.num2date(t, locator.date_unit, calendar=locator.calendar).day
                == 1
                for t in ticks
            )
        elif expected_resolution == "MONTHLY":
            assert all(
                cftime.num2date(t, locator.date_unit, calendar=locator.calendar).day
                == 1
                for t in ticks
            )
        elif expected_resolution == "DAILY":
            assert all(
                cftime.num2date(t, locator.date_unit, calendar=locator.calendar).hour
                == 0
                for t in ticks
            )
        elif expected_resolution == "HOURLY":
            assert all(
                cftime.num2date(t, locator.date_unit, calendar=locator.calendar).minute
                == 0
                for t in ticks
            )
        elif expected_resolution == "MINUTELY":
            assert all(
                cftime.num2date(t, locator.date_unit, calendar=locator.calendar).second
                == 0
                for t in ticks
            )


@pytest.mark.parametrize(
    "vmin, vmax, expected_ticks",
    [
        (5, 5, []),  # Case 1: Empty range
        (-5, 5, [1, 3]),  # Case 2: Negative range
    ],
)
def test_index_locator_tick_values_edge_cases(vmin, vmax, expected_ticks):
    from ultraplot.ticker import IndexLocator

    locator = IndexLocator(base=2, offset=1)
    ticks = locator.tick_values(vmin, vmax)
    print(f"vmin: {vmin}, vmax: {vmax}, ticks: {ticks}")
    assert np.array_equal(ticks, expected_ticks)


@pytest.mark.parametrize(
    "locs, steps, nbins, expected_length, expected_ticks",
    [
        ([], None, None, 0, []),  # Case 1: Empty locs
        ([5], None, None, 1, [5]),  # Case 2: Single loc
        (np.arange(0, 100, 1), [1, 2], 10, 100, None),  # Case 3: Large range with steps
    ],
)
def test_discrete_locator_tick_values_edge_cases(
    locs, steps, nbins, expected_length, expected_ticks
):
    from ultraplot.ticker import DiscreteLocator

    locator = DiscreteLocator(locs=locs)
    if steps and nbins:
        locator.set_params(steps=steps, nbins=nbins)
    ticks = locator.tick_values(None, None)

    assert len(ticks) == expected_length  # Check the number of ticks
    if expected_ticks is not None:
        assert np.array_equal(ticks, expected_ticks)  # Check the tick values


@pytest.mark.parametrize(
    "steps, expected",
    [
        ((0, 2000000), [1, 2, 3, 6, 10]),  # large range
        ((0, 2), [1, 1.5, 2, 2.5, 3, 5, 10]),  # small range
    ],
)
def test_degree_locator_guess_steps(steps, expected):
    from ultraplot.ticker import DegreeLocator

    locator = DegreeLocator()
    locator._guess_steps(*steps)
    assert np.array_equal(locator._steps, expected)


import pytest


@pytest.mark.parametrize(
    "formatter_args, value, expected",
    [
        ({"precision": 2, "zerotrim": True}, 12345, r"$1.23{\times}10^{4}$"),
        ({"precision": 2, "zerotrim": True}, 0.12345, r"$1.23{\times}10^{−1}$"),
        ({"precision": 2, "zerotrim": True}, 0, r"$0$"),
        ({"precision": 2, "zerotrim": True}, 1.2, r"$1.2$"),
        ({"precision": 2, "zerotrim": False}, 1.2, r"$1.20$"),
    ],
)
def test_sci_formatter(formatter_args, value, expected):
    from ultraplot.ticker import SciFormatter

    formatter = SciFormatter(**formatter_args)
    assert formatter(value) == expected


@pytest.mark.parametrize(
    "formatter_args, value, expected",
    [
        ({"sigfig": 3}, 12345, "12300"),
        ({"sigfig": 3}, 123.45, "123"),
        ({"sigfig": 3}, 0.12345, "0.123"),
        ({"sigfig": 3}, 0.0012345, "0.00123"),
        ({"sigfig": 2, "base": 5}, 87, "85"),
        ({"sigfig": 2, "base": 5}, 8.7, "8.5"),
    ],
)
def test_sig_fig_formatter(formatter_args, value, expected):
    from ultraplot.ticker import SigFigFormatter

    formatter = SigFigFormatter(**formatter_args)
    assert formatter(value) == expected


@pytest.mark.parametrize(
    "formatter_args, value, expected",
    [
        (
            {"symbol": r"$\\pi$", "number": 3.141592653589793},
            3.141592653589793 / 2,
            r"$\\pi$/2",
        ),
        (
            {"symbol": r"$\\pi$", "number": 3.141592653589793},
            3.141592653589793,
            r"$\\pi$",
        ),
        (
            {"symbol": r"$\\pi$", "number": 3.141592653589793},
            2 * 3.141592653589793,
            r"2$\\pi$",
        ),
        ({"symbol": r"$\\pi$", "number": 3.141592653589793}, 0, "0"),
        ({}, 0.5, "1/2"),
        ({}, 1, "1"),
        ({}, 1.5, "3/2"),
    ],
)
def test_frac_formatter(formatter_args, value, expected):
    from ultraplot.ticker import FracFormatter

    formatter = FracFormatter(**formatter_args)
    assert formatter(value) == expected


def test_frac_formatter_unicode_minus():
    from ultraplot.ticker import FracFormatter
    from ultraplot.config import rc
    import numpy as np

    formatter = FracFormatter(symbol=r"$\\pi$", number=np.pi)
    with rc.context({"axes.unicode_minus": True}):
        assert formatter(-np.pi / 2) == r"−$\\pi$/2"


@pytest.mark.parametrize(
    "fmt, calendar, dt_args, expected",
    [
        ("%Y-%m-%d", "noleap", (2001, 2, 28), "2001-02-28"),
    ],
)
def test_cfdatetime_formatter_direct_call(fmt, calendar, dt_args, expected):
    from ultraplot.ticker import CFDatetimeFormatter
    import cftime

    formatter = CFDatetimeFormatter(fmt, calendar=calendar)
    dt = cftime.datetime(*dt_args, calendar=calendar)
    assert formatter(dt) == expected


@pytest.mark.parametrize(
    "start_date_str, end_date_str, calendar, resolution",
    [
        ("2000-01-01 00:00:00", "2000-01-01 12:00:00", "standard", "HOURLY"),
        ("2000-01-01 00:00:00", "2000-01-01 00:10:00", "standard", "MINUTELY"),
        ("2000-01-01 00:00:00", "2000-01-01 00:00:10", "standard", "SECONDLY"),
    ],
)
def test_autocftime_locator_subdaily(
    start_date_str, end_date_str, calendar, resolution
):
    from ultraplot.ticker import AutoCFDatetimeLocator
    import cftime

    locator = AutoCFDatetimeLocator(calendar=calendar)
    units = locator.date_unit

    start_dt = cftime.datetime.strptime(
        start_date_str, "%Y-%m-%d %H:%M:%S", calendar=calendar
    )
    end_dt = cftime.datetime.strptime(
        end_date_str, "%Y-%m-%d %H:%M:%S", calendar=calendar
    )

    start_num = cftime.date2num(start_dt, units, calendar=calendar)
    end_num = cftime.date2num(end_dt, units, calendar=calendar)

    res, _ = locator.compute_resolution(start_num, end_num, start_dt, end_dt)
    assert res == resolution

    ticks = locator.tick_values(start_num, end_num)
    assert len(ticks) > 0


def test_autocftime_locator_safe_helpers():
    from ultraplot.ticker import AutoCFDatetimeLocator
    import cftime

    # Test _safe_num2date with invalid value
    locator_gregorian = AutoCFDatetimeLocator(calendar="gregorian")
    with pytest.raises(OverflowError):
        locator_gregorian._safe_num2date(1e30)

    # Test _safe_create_datetime with invalid date
    locator_noleap = AutoCFDatetimeLocator(calendar="noleap")
    assert locator_noleap._safe_create_datetime(2001, 2, 29) is None


def test_autocftime_locator_safe_daily_locator():
    from ultraplot.ticker import AutoCFDatetimeLocator

    locator = AutoCFDatetimeLocator()
    assert locator._safe_daily_locator(0, 10) is not None


def test_latitude_locator():
    from ultraplot.ticker import LatitudeLocator
    import numpy as np

    locator = LatitudeLocator()
    ticks = np.array(locator.tick_values(-100, 100))
    assert np.all(ticks >= -90)
    assert np.all(ticks <= 90)


def test_cftime_converter():
    from ultraplot.ticker import CFTimeConverter, cftime
    from ultraplot.config import rc
    import numpy as np

    converter = CFTimeConverter()

    # test default_units
    assert converter.default_units(np.array([1, 2]), None) is None
    assert converter.default_units([], None) is None
    assert converter.default_units([1, 2], None) is None
    with pytest.raises(ValueError):
        converter.default_units(
            [
                cftime.datetime(2000, 1, 1, calendar="gregorian"),
                cftime.datetime(2000, 1, 1, calendar="noleap"),
            ],
            None,
        )

    with pytest.raises(ValueError):
        converter.default_units(cftime.datetime(2000, 1, 1, calendar=""), None)

    # test convert
    assert converter.convert(1, None, None) == 1
    assert np.array_equal(
        converter.convert(np.array([1, 2]), None, None), np.array([1, 2])
    )
    assert converter.convert([1, 2], None, None) == [1, 2]
    assert converter.convert([], None, None) == []

    # test axisinfo with no unit
    with rc.context({"cftime.time_unit": "days since 2000-01-01"}):
        info = converter.axisinfo(None, None)
        assert isinstance(info.majloc, uplt.ticker.AutoCFDatetimeLocator)
