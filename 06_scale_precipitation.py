"""Scale precipitation to climatological seasonal total."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

INPUT_DIR = Path("output/select_data")
INPUT_DIR_SEASONS = Path("output/extract_dry_wet_seasons/")

OUTPUT_DIR = Path("output/scale_precipitation")
FIG_DIR = Path("fig")

TARGET_YEAR = 2023

PLOT = False


# %% Load data

years = np.load(INPUT_DIR_SEASONS / "years.npy")
precip_dry = np.load(INPUT_DIR_SEASONS / "precip_dry.npy")
precip_wet = np.load(INPUT_DIR_SEASONS / "precip_wet.npy")
time_dry = np.load(INPUT_DIR_SEASONS / "time_dry.npy", allow_pickle=True)
time_wet = np.load(INPUT_DIR_SEASONS / "time_wet.npy", allow_pickle=True)

precip = np.load(INPUT_DIR / "precip.npy")
time = np.load(INPUT_DIR / "time_precip.npy", allow_pickle=True)

wet_start = time_wet[0, 0]
wet_end = time_wet[0, -1]


# %% Get climatology

precip_dry_clim = precip_dry.mean(axis=0)
precip_wet_clim = precip_wet.mean(axis=0)


# %% Scale

wet_start_target = wet_start.replace(year=TARGET_YEAR)
wet_end_target = wet_end.replace(year=TARGET_YEAR + 1)
sel = (wet_start_target <= time) & (time <= wet_end_target)

precip_target = precip[sel]
time_target = time[sel]

precip_target_sum = precip_target.sum(axis=0)

scaling_factor = precip_wet_clim.sum(axis=0) / precip_target_sum

precip_scaled = precip.copy()
precip_scaled[sel] = scaling_factor * precip[sel]


# %% Save

OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
np.save(OUTPUT_DIR / "precip", precip_scaled)
np.save(OUTPUT_DIR / "time", time)


# %% Plot

if PLOT:
    FIG_DIR.mkdir(exist_ok=True, parents=True)

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111)

    c = ax.pcolormesh(scaling_factor, vmin=0, vmax=2, cmap="RdBu_r")
    plt.colorbar(c)

    fig.savefig(FIG_DIR / "scaling_factor.png")

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111)

    csum_precip = np.cumsum(precip[sel].mean(axis=(-1, -2)))
    csum_precip_scaled = np.cumsum(precip_scaled[sel].mean(axis=(-1, -2)))
    csum_precip_clim = np.cumsum(precip_wet_clim.mean(axis=(-1, -2)))

    ax.plot(time_target, csum_precip_clim, "k-", lw=2, label="Climatology")
    ax.plot(time_target, csum_precip, label="Original")
    ax.plot(time_target, csum_precip_scaled, label="Scaled")

    ax.legend()

    fig.savefig(FIG_DIR / "cumulative_sum.png")

    plt.show()
