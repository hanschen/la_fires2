#!/usr/bin/env python
"""Extract dry and wet seasons from data.

The year corresponds to the year when the season starts (also for wet season).
"""

from pathlib import Path

import numpy as np

INPUT_DIR = Path("output/select_data")
INPUT_DIR_DRY_SEASON = Path("output/identify_dry_wet_seasons")

OUTPUT_DIR = Path("output/extract_dry_wet_seasons")


# %% Load data

precip = np.load(INPUT_DIR / "precip.npy")
time = np.load(INPUT_DIR / "time_precip.npy", allow_pickle=True)
years = np.array([d.year for d in time])

dry_start = np.load(
    INPUT_DIR_DRY_SEASON / "dry_start.npy", allow_pickle=True
).item()
dry_end = np.load(
    INPUT_DIR_DRY_SEASON / "dry_end.npy", allow_pickle=True
).item()


# %% Analysis

years = np.unique(years)

# Skip last two years
years = years[:-2]

# In the code we treat the year as when a season (dry or wet) starts.
# This makes it easier to deal with.

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for wet_or_dry in ["wet", "dry"]:
    precip_season = []
    time_season = []

    for year in years:
        if wet_or_dry == "dry":
            start = dry_start.replace(year=year)
            end = dry_end.replace(year=year)
        else:
            start = dry_end.replace(year=year)
            end = dry_start.replace(year=year + 1)

        sel = (start <= time) & (time < end)
        precip_season.append(precip[sel])
        time_season.append(time[sel])

    precip_season = np.array(precip_season)
    time_season = np.array(time_season)

    np.save(OUTPUT_DIR / f"{wet_or_dry}_precip", precip_season)
    np.save(OUTPUT_DIR / f"{wet_or_dry}_time", time_season)

np.save(OUTPUT_DIR / "years", years)
