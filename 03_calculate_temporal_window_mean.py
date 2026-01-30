#!/usr/bin/env python
"""Calculate temporal mean over averaging windows.

The output is a 2D array with dimensions (year, window).
"""

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

import utils
from config import AVERAGE_WINDOW_DAYS

INPUT_DIR = Path("output/select_data")
OUTPUT_DIR = Path("output/calculate_temporal_window_mean")

DEBUG = False


def create_averaging_bounds(window_size):
    """Create averaging bounds for averaging window of size ``window_size.``"""
    arbitrary_nonleap_year = 1901
    start = datetime(arbitrary_nonleap_year, 1, 1)
    end = start + window_size

    bounds = []
    while True:
        bounds.append([start, end])
        start = end
        end = start + window_size

        if end.year > start.year:
            break

    # Collect all remaining elemnts for the last averaging window
    bounds[-1][-1] = None

    return bounds


def temporal_mean(time, array, bounds, debug=False):
    """Temporally average ``array`` over each year using averaging windows
    specified by ``bounds``."""
    years = np.unique([d.year for d in time])
    nyears = years.size
    shape = (nyears, len(bounds))

    temporal_mean = np.zeros(shape)
    window_start = np.zeros(shape, dtype="datetime64[s]")
    window_mid = np.zeros(shape, dtype="datetime64[s]")
    window_end = np.zeros(shape, dtype="datetime64[s]")

    for iyear, year in enumerate(years):
        deviations = []

        if debug:
            print(year)

        for iwindow, (b_start, b_end) in enumerate(bounds):
            start = b_start.replace(year=year)
            if b_end is None:
                end = datetime(year + 1, 1, 1)
            else:
                end = b_end.replace(year=year)

            sel = (time >= start) & (time < end)
            if sel.sum() > 0:
                temporal_mean[iyear, iwindow] = np.nanmean(array[sel])
            else:
                temporal_mean[iyear, iwindow] = np.nan

            if debug:
                # NOTE: Hard-coded for 3-hourly data
                nsel = sel.sum() / 8

                if nsel != AVERAGE_WINDOW_DAYS:
                    deviations.append(f"[{iwindow}]: {nsel}")

            window_start[iyear, iwindow] = start
            window_mid[iyear, iwindow] = start + (end - start) / 2
            window_end[iyear, iwindow] = end

        if debug and deviations:
            print(f"{deviations}")

    return temporal_mean, window_start, window_mid, window_end


# %% Load data

precip = np.load(INPUT_DIR / "precip.npy")
time = np.load(INPUT_DIR / "time_precip.npy", allow_pickle=True)
years = np.array([d.year for d in time])

precip = utils.mask_ocean_values(precip)


# %% Spatial average

precip_spatial_mean = np.nanmean(precip, axis=(-1, -2))


# %% Create average bounds

window_size = timedelta(days=AVERAGE_WINDOW_DAYS)
bounds = create_averaging_bounds(window_size)


# %% Average over averaging windows

if DEBUG:
    print(":: Precipitation")

results = temporal_mean(time, precip, bounds, debug=DEBUG)
precip_temporal_mean, window_start, window_mid, window_end = results

# %% Save

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
np.save(OUTPUT_DIR / "precip", precip_temporal_mean)
np.save(OUTPUT_DIR / "years", np.unique(years))
np.save(OUTPUT_DIR / "window_start", window_start)
np.save(OUTPUT_DIR / "window_mid", window_mid)
np.save(OUTPUT_DIR / "window_end", window_end)
