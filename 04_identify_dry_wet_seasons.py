#!/usr/bin/env python
"""Identify dry and wet seasons from climatological median precipitation."""

from datetime import timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from config import AVERAGE_WINDOW_DAYS

INPUT_DIR = Path("output/calculate_temporal_window_mean")
OUTPUT_DIR = Path("output/identify_dry_wet_seasons")
FIG_DIR = Path("fig")

PRECIP_THRESHOLD = 0.02  # mm/3hr

PLOT = False


# %% Load data

precip = np.load(INPUT_DIR / "precip.npy")
window_mid = np.load(INPUT_DIR / "window_mid.npy", allow_pickle=True)


# %% Find wet and dry seasons

# Exclude first and last years (incomplete data)
precip = precip[1:-1]
window_mid = window_mid[1:-1]

median_precip = np.nanmedian(precip, axis=0)
dry_season = np.argwhere(median_precip < PRECIP_THRESHOLD)

t_start = dry_season[0].item()
t_end = dry_season[-1].item()

half_average_window = timedelta(days=AVERAGE_WINDOW_DAYS // 2)
dry_start = window_mid[0][t_start] - half_average_window
dry_end = window_mid[0][t_end] + half_average_window

print(f"Dry season start: {dry_start}")
print(f"Dry season end: {dry_end}")


# %% Save

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
np.save(OUTPUT_DIR / "dry_start", dry_start)
np.save(OUTPUT_DIR / "dry_end", dry_end)


# %% Plot

if PLOT:
    sns.set_style("whitegrid")
    sns.set_color_codes()

    colors = sns.color_palette("deep")

    fig = plt.figure(figsize=(16, 8))
    ax = fig.add_subplot(111)

    ax.plot(days, precip, "o-", color="k")
    ax.axhline(THRESHOLD, linestyle="--", color="r")

    ymin, ymax = plt.ylim()
    xmin, xmax = 1, 365

    plt.fill_between(
        [dry_start, dry_end],
        [ymin, ymin],
        [ymax, ymax],
        color=colors[1],
        alpha=0.5,
    )
    plt.fill_between(
        [xmin, dry_start],
        [ymin, ymin],
        [ymax, ymax],
        color=colors[0],
        alpha=0.5,
    )
    plt.fill_between(
        [dry_end, xmax], [ymin, ymin], [ymax, ymax], color=colors[0], alpha=0.5
    )

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    ax.set_xlabel("Day in year")
    ax.set_ylabel("Precipitation (mm/3hr)")

    fig.tight_layout()
    FIG_DIR.mkdir(exist_ok=True)
    fig.savefig(FIG_DIR / "wet_dry_seasons.png")

    plt.show()
