import pytest, numpy as np, xarray as xr, ultraplot as uplt, cftime
from ultraplot.ticker import AutoDatetimeLocator


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

    formatter = uplt.ticker.DatetimeFormatter("%b %Y", calendar="noleap")
    locator = uplt.ticker.AutoDatetimeLocator(calendar="noleap")
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax.plot(da)

    fig.canvas.draw()

    labels = [label.get_text() for label in ax.get_xticklabels()]
    assert len(labels) > 0
    # check first label
    try:
        import cftime

        cftime.datetime.strptime(labels[1], "%b %Y", calendar="noleap")
    except (ValueError, IndexError):
        assert False, f"Label {labels[1]} does not match format %b %Y"


@pytest.mark.parametrize(
    "date1, date2, num1, num2, expected_resolution, expected_n",
    [
        (
            cftime.DatetimeGregorian(2000, 1, 1),
            cftime.DatetimeGregorian(2020, 1, 1),
            0,
            7305,
            "YEARLY",
            20,
        ),
        (
            cftime.DatetimeGregorian(2000, 1, 1),
            cftime.DatetimeGregorian(2001, 1, 1),
            0,
            365,
            "MONTHLY",
            12,
        ),
        (
            cftime.DatetimeGregorian(2000, 1, 1),
            cftime.DatetimeGregorian(2000, 1, 10),
            0,
            9,
            "DAILY",
            9,
        ),
        (
            cftime.DatetimeGregorian(2000, 1, 1),
            cftime.DatetimeGregorian(2000, 1, 1, 12),
            0,
            0.5,
            "HOURLY",
            12,
        ),
        (
            cftime.DatetimeGregorian(2000, 1, 1),
            cftime.DatetimeGregorian(2000, 1, 1, 0, 0, 10),
            0,
            1.1574074074074073e-4,
            "SECONDLY",
            10,
        ),
    ],
)
def test_compute_resolution(date1, date2, num1, num2, expected_resolution, expected_n):
    locator = AutoDatetimeLocator()
    resolution, n = locator.compute_resolution(num1, num2, date1, date2)
    assert resolution == expected_resolution
    assert np.allclose(n, expected_n)


@pytest.mark.parametrize(
    "date1, date2, num1, num2",
    [
        (
            cftime.DatetimeGregorian(2000, 1, 1),
            cftime.DatetimeGregorian(2020, 1, 1),
            0,
            7305,
        ),
        (
            cftime.DatetimeGregorian(2000, 1, 1),
            cftime.DatetimeGregorian(2001, 1, 1),
            0,
            365,
        ),
        (
            cftime.DatetimeGregorian(2000, 1, 1),
            cftime.DatetimeGregorian(2000, 1, 10),
            0,
            9,
        ),
        (
            cftime.DatetimeGregorian(2000, 1, 1),
            cftime.DatetimeGregorian(2000, 1, 1, 12),
            0,
            0.5,
        ),
        (
            cftime.DatetimeGregorian(2000, 1, 1),
            cftime.DatetimeGregorian(2000, 1, 1, 0, 0, 10),
            0,
            1.1574074074074073e-4,
        ),
    ],
)
def test_tick_values(date1, date2, num1, num2):
    locator = AutoDatetimeLocator()
    locator.compute_resolution(num1, num2, date1, date2)
    ticks = locator.tick_values(num1, num2)
    assert len(ticks) > 0
    assert all(
        isinstance(
            cftime.num2date(t, locator.date_unit, calendar=locator.calendar),
            cftime.DatetimeGregorian,
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
