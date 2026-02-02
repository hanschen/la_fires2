"""Utils to create BEPS input.

Daily netCDF files with all metetorology variables for BEPS.
Also linearly interpolate to hourly values.
"""

from datetime import timedelta
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


def create_netcdf(
    output_dir, start_date, end_date, variables, times, lats, lons, force=False
):
    OUTPUT_VARIABLES = {
        "PRCP": "precip",
        "RH": "rh",
        "SSRD": "swd",
        "T": "temp",
        "WS": "wind",
    }

    VARIABLE_UNITS = {
        "PRCP": "mm/h",
        "RH": " ",
        "SSRD": "W/m2",
        "T": "K",
        "WS": "m/s",
    }

    start_of_start_date = start_date.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    if start_date != start_of_start_date:
        print("warning: Setting start_date to start of the day")
        start_date = start_of_start_date

    start_of_end_date = end_date.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    if end_date != start_of_end_date:
        print("warning: Setting end_date to start of the day")
        end_date = start_of_end_date

    output_dir = Path(output_dir)
    variables = variables.copy()

    dates = [
        date
        for date in utils.iterdates(start_date, end_date, timedelta(days=1))
    ]
    output_hours = np.arange(24, dtype=int)

    # Convert temperature to kelvin
    if "temp" in variables:
        variables["temp"] = variables["temp"] + 273.15

    # Convert RH % to fraction
    if "rh" in variables:
        variables["rh"] = variables["rh"] / 100.0

    output_dir.mkdir(exist_ok=True, parents=True)

    for date in tqdm(dates):
        # Skip leap days
        if date.month == 2 and date.day == 29:
            continue

        filename = (
            f"beps_meteo_0.1_{date.year}{date.month:02d}{date.day:02d}.nc"
        )
        outfile = output_dir / filename

        if outfile.exists() and not force:
            continue

        # Select data
        end = date + timedelta(days=1)

        # If the selection ends on a leap day, we need to skip to the next day
        # because we have removed all leap days
        if end.month == 2 and end.day == 29:
            end = end + timedelta(days=1)

        variables_current = {}
        hours_current = {}
        for variable, values in variables.items():
            start = date

            # For precipitation, we need to include the previous 3-hour bin to
            # calculate the adjustment
            if variable == "precip":
                start = start - timedelta(hours=3)

            time = times[variable]
            variables_current[variable] = utils.select_time(
                values, time, start=start, end=end, include_endpoint=True
            )
            time_current = utils.select_time(
                time, time, start=start, end=end, include_endpoint=True
            )
            hours_current[variable] = np.array(
                [
                    int(delta.total_seconds() / 60 / 60)
                    for delta in time_current - date
                ]
            )

        # Interpolate
        interpolated_variables = {}
        for variable, values in variables_current.items():
            hours = hours_current[variable]
            if variable == "precip":
                interp_values = interp_precip(output_hours, hours, values)
            else:
                interp = interp1d(hours, values, kind="linear", axis=0)
                interp_values = interp(output_hours)
            interpolated_variables[variable] = interp_values

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
        time_units = (
            f"hours since {date.year}-{date.month:02d}-{date.day:02d} 00:00:00"
        )
        nc_time.units = time_units
        nc_time.calendar = "gregorian"
        nc_time[:] = output_hours

        nc_lat = ncfile.createVariable("lat", "f4", ("lat",))
        nc_lat.units = "degrees_north"
        nc_lat[:] = lats

        nc_lon = ncfile.createVariable("lon", "f4", ("lon",))
        nc_lon.units = "degrees_east"
        nc_lon[:] = lons

        for output_variable, variable in OUTPUT_VARIABLES.items():
            if variable not in variables:
                continue

            if variable == "precip":
                datatype = "f4"
            else:
                datatype = "f8"
            nc_var = ncfile.createVariable(
                output_variable, datatype, ("time", "lat", "lon")
            )
            nc_var.units = VARIABLE_UNITS[output_variable]
            nc_var[:] = interpolated_variables[variable]

        ncfile.close()
