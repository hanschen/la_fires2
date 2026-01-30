#!/usr/bin/env python
"""Extract dry and wet seasons from data.

The year corresponds to the year when the season starts (also for wet season).
"""

from pathlib import Path

import numpy as np

INPUT_DIR = Path("output/select_data")
INPUT_DIR_DRY_SEASON = Path("output/identify_dry_wet_seasons")

OUTPUT_DIR = Path("output/extract_dry_wet_seasons")


def extract_season(data, time, years, dry_start, dry_end, wet_or_dry):
    data_season = []
    time_season = []

    for year in years:
        if wet_or_dry == "dry":
            start = dry_start.replace(year=year)
            end = dry_end.replace(year=year)
        else:
            start = dry_end.replace(year=year)
            end = dry_start.replace(year=year + 1)

        sel = (start <= time) & (time < end)
        data_season.append(data[sel])
        time_season.append(time[sel])

    data_season = np.array(data_season)
    time_season = np.array(time_season)

    return time_season, data_season


# %% Load data

precip = np.load(INPUT_DIR / "precip.npy")
time = np.load(INPUT_DIR / "time_precip.npy", allow_pickle=True)
years = np.unique([d.year for d in time])

dry_start = np.load(
    INPUT_DIR_DRY_SEASON / "dry_start.npy", allow_pickle=True
).item()
dry_end = np.load(
    INPUT_DIR_DRY_SEASON / "dry_end.npy", allow_pickle=True
).item()


# %% Analysis

# Skip last two years (incomplete wet season)
years = years[:-2]

# In the code we treat the year as when a season (dry or wet) starts.
# This makes it easier to deal with.

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

time_dry, precip_dry = extract_season(
    precip, time, years, dry_start, dry_end, "dry"
)

time_wet, precip_wet = extract_season(
    precip, time, years, dry_start, dry_end, "wet"
)

np.save(OUTPUT_DIR / "years", years)
np.save(OUTPUT_DIR / f"precip_dry", precip_dry)
np.save(OUTPUT_DIR / f"time_dry", time_dry)
np.save(OUTPUT_DIR / f"precip_wet", precip_wet)
np.save(OUTPUT_DIR / f"time_wet", time_wet)
