import pytest
import numpy as np
import xarray as xr
import ultraplot as uplt


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
