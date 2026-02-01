"""Utils to create BEPS input.

Daily netCDF files with all metetorology variables for BEPS.
Also linearly interpolate to hourly values.
"""

from datetime import datetime, timedelta
from pathlib import Path

import netCDF4 as nc
import numpy as np
from scipy.interpolate import interp1d
from tqdm import tqdm

import utils

INPUT_DIR = Path("output/experiments")
OUTPUT_DIR = Path("output/netcdf")


def interp_precip(x, xp, yp):
    """Interpolate 3-hourly precipitation (mm/3hr) to hourly (mm/hr).

    Perform linear interpolation, then adjust so that the sum of hourly
    precipitation in 3-hour bins match the 3-hourly precipitation at the end of
    the bin.

    Currently hard-coded for 3-dimensional ``yp`` corresponding to
    (time, lat, lon).

    """
    res = np.zeros(x.shape + yp.shape[1:])

    # Extended x array to include margins
    xx = np.arange(xp[0], xp[-1] + 1)
    sel = np.isin(xx, x)

    for j in range(yp.shape[1]):
        for i in range(yp.shape[2]):
            interp_func = interp1d(xp, yp[:, j, i], kind="linear", axis=0)
            y = interp_func(xx)

            for xi, yi in zip(xp, yp[:, j, i], strict=True):
                bin = (xx > xi - 3) & (xx <= xi)

                if yi == 0:  # to avoid division by zero warning
                    y[bin] = 0
                else:
                    y[bin] = y[bin] * (yi / y[bin].sum())

            res[:, j, i] = y[sel]

    return res


def unique(seq):
    """Return unique elements in ``seq``."""
    seen = set()
    return [x for x in seq if not (x in seen or seen.add(x))]


def create_netcdf(output_dir, variables, time, lats, lons, force=False):
    output_dir = Path(output_dir)

    temp = variables["temp"]
    precip = variables["precip"]
    rh = variables["rh"]
    swd = variables["swd"]
    wind = variables["wind"]

    dates = [(d.year, d.month, d.day) for d in time]
    dates = unique(dates)
    dates = dates[1:-1]  # skip margin dates

    if time[0].hour != 0:
        raise NotImplementedError

    output_hours = np.arange(24).astype(int)

    # Convert temperature to kelvin
    temp = temp + 273.15

    # Convert RH % to fraction
    rh = rh / 100.0

    output_dir.mkdir(exist_ok=True, parents=True)

    for year, month, day in tqdm(dates):
        filename = f"beps_meteo_0.1_{year}{month:02d}{day:02d}.nc"
        outfile = output_dir / filename

        if outfile.exists() and not force:
            continue

        # Select data
        start = datetime(year, month, day)
        end = start + timedelta(days=1)

        # skip leap days
        if end.month == 2 and end.day == 29:
            end = end + timedelta(days=1)

        opts = dict(start=start, end=end, include_endpoint=True)
        temp_day = utils.select_time(temp, time, **opts)
        rh_day = utils.select_time(rh, time, **opts)
        swd_day = utils.select_time(swd, time, **opts)
        wind_day = utils.select_time(wind, time, **opts)

        time_day = utils.select_time(time, time, **opts)
        hours = np.array(
            [
                int(delta.total_seconds() / 60 / 60)
                for delta in time_day - start
            ]
        )

        # Include larger margin for precipitation
        opts = dict(
            start=start - timedelta(hours=3), end=end, include_endpoint=True
        )
        precip_day = utils.select_time(precip, time, **opts)
        time_day_precip = utils.select_time(time, time, **opts)
        hours_precip = np.array(
            [
                int(delta.total_seconds() / 60 / 60)
                for delta in time_day_precip - start
            ]
        )

        # Interpolate
        interp_temp = interp1d(hours, temp_day, kind="linear", axis=0)
        interp_rh = interp1d(hours, rh_day, kind="linear", axis=0)
        interp_swd = interp1d(hours, swd_day, kind="linear", axis=0)
        interp_wind = interp1d(hours, wind_day, kind="linear", axis=0)

        temp_hourly = interp_temp(output_hours)
        rh_hourly = interp_rh(output_hours)
        swd_hourly = interp_swd(output_hours)
        wind_hourly = interp_wind(output_hours)

        precip_hourly = interp_precip(output_hours, hours_precip, precip_day)

        # Create netCDF
        ncfile = nc.Dataset(
            outfile,
            mode="w",
            format="NETCDF4",
        )
        ncfile.createDimension("time", None)
        ncfile.createDimension("lat", lats.size)
        ncfile.createDimension("lon", lons.size)

        nc_time = ncfile.createVariable("time", "f4", ("time",))
        nc_lat = ncfile.createVariable("lat", "f4", ("lat",))
        nc_lon = ncfile.createVariable("lon", "f4", ("lon",))

        nc_precip = ncfile.createVariable("PRCP", "f4", ("time", "lat", "lon"))
        nc_rh = ncfile.createVariable("RH", "f8", ("time", "lat", "lon"))
        nc_swd = ncfile.createVariable("SSRD", "f8", ("time", "lat", "lon"))
        nc_temp = ncfile.createVariable("T", "f8", ("time", "lat", "lon"))
        nc_wind = ncfile.createVariable("WS", "f8", ("time", "lat", "lon"))

        nc_time.units = f"hours since {year}-{month:02d}-{day:02d} 00:00:00"
        nc_time.calendar = "gregorian"
        nc_lat.units = "degrees_north"
        nc_lon.units = "degrees_east"
        nc_precip.units = "mm/h"
        nc_rh.units = " "
        nc_swd.units = "W/m2"
        nc_temp.units = "K"
        nc_wind.units = "m/s"

        nc_time[:] = output_hours
        nc_lat[:] = lats
        nc_lon[:] = lons
        nc_precip[:] = precip_hourly
        nc_rh[:] = rh_hourly
        nc_swd[:] = swd_hourly
        nc_temp[:] = temp_hourly
        nc_wind[:] = wind_hourly

        ncfile.close()
