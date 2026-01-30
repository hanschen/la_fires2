#!/usr/bin/env python
"""Select data for analysis.

This script:
- Fills in precipitation values for invalid time steps.
- Selects data between START and END (inclusive).
- Removes leap days.

"""

from datetime import datetime
from pathlib import Path

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np

import utils

START = datetime(1979, 1, 1)
END = datetime(2025, 3, 1)

VARIABLES = ["temp", "precip", "rh", "swd", "wind"]

NETCDF_NAMES = {
    "temp": "air_temperature",
    "precip": "precipitation",
    "rh": "relative_humidity",
    "swd": "downward_shortwave_radiation",
    "wind": "wind_speed",
}

OUTPUT_DIR = Path("output/select_data")
FIG_DIR = Path("fig")

DEBUG = True
PLOT = False

LAT_LA = 34.05
LON_LA = -118.25


def remove_leap_days(value, time):
    leap_days = np.array([d.month == 2 and d.day == 29 for d in time])
    return value[~leap_days]


# %% Load data

variables = {}
dates = {}

lats: np.ndarray = None  # type: ignore
lons: np.ndarray = None  # type: ignore

for i, varname in enumerate(VARIABLES):
    with nc.Dataset(f"data/{varname}.nc") as ncfile:
        ncfile.set_auto_mask(False)

        nc_variable = NETCDF_NAMES[varname]
        variables[varname] = ncfile.variables[nc_variable][:]

        time = ncfile.variables["time"]
        dates[varname] = nc.num2date(
            time[:], time.units, only_use_cftime_datetimes=False
        )

        if i == 0:
            lats = ncfile.variables["lat"][:]
            lons = ncfile.variables["lon"][:]


# %% Fill in missing precipitation time steps

# MSWEP includes some time steps where all precipitation values are invalid.
# Replace the precipitation values at these time steps with the linearly
# interpolated value between the previous and next time steps.
precip = variables["precip"]
invalid_precip = np.all(precip > 1e9, axis=(-1, -2))

for timestep in np.argwhere(invalid_precip):
    t = timestep.item()
    date = dates["precip"][t]
    print(f"-> Missing precipitation: {date}")
    if t == 0 or t == precip.shape[0] - 1:
        raise NotImplementedError
    precip[t] = 0.5 * (precip[t - 1] + precip[t + 1])


# %% Select time steps

options = dict(start=START, end=END, include_endpoint=True)

for varname, values in variables.items():
    time = dates[varname]
    variables[varname] = utils.select_time(values, time, **options)
    dates[varname] = utils.select_time(time, time, **options)


# %% Remove leap days

for varname, values in variables.items():
    time = dates[varname]
    variables[varname] = remove_leap_days(values, time)
    dates[varname] = remove_leap_days(time, time)


# %% Save

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
np.save(OUTPUT_DIR / "lats", lats)
np.save(OUTPUT_DIR / "lons", lons)
for varname, values in variables.items():
    time = dates[varname]
    np.save(OUTPUT_DIR / f"{varname}", values)
    np.save(OUTPUT_DIR / f"time_{varname}", time)


# %% Check precipitaiton in LA

if DEBUG:
    months = np.arange(1, 12 + 1)
    days_in_months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    j = np.argmin(np.abs(lats - LAT_LA))
    i = np.argmin(np.abs(lons - LON_LA))

    precip_LA = variables["precip"][:, j, i]
    precip_months = np.array([d.month for d in dates["precip"]])

    print(":: Average precipitation in LA (mm)")
    for m, days in zip(months, days_in_months, strict=True):
        sel = precip_months == m
        avg_precip = precip_LA[sel].mean() * 8 * days
        print(f"Month {m}: {avg_precip:.2f}")

# %% Plot

if PLOT:
    temp = utils.apply_mask(variables["temp"])
    precip = utils.apply_mask(variables["precip"])

    fig = plt.figure(figsize=(5, 4))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.coastlines()
    ax.plot(LON_LA, LAT_LA, "k*", label="LA")
    cs = ax.pcolormesh(lons, lats, temp[0], cmap="inferno")
    # ax.pcolormesh(lons, lats, precip[20])
    ax.legend()
    gl = ax.gridlines(
        draw_labels=True,
        dms=True,
        x_inline=False,
        y_inline=False,
        color="none",
    )
    gl.top_labels = False
    gl.right_labels = False

    cbar = fig.colorbar(cs)
    cbar.set_label("Temperature (°C)")

    fig.tight_layout()

    FIG_DIR.mkdir(exist_ok=True, parents=True)
    fig.savefig(FIG_DIR / "domain.png")

    plt.show()
