from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

INPUT_DIR = Path("output/select_data")
INPUT_DIR_SCALED = Path("output/scale_precipitation")

FIG_DIR = Path("fig")

START = datetime(2023, 1, 1)
END = datetime(2025, 4, 1)

time = np.load(INPUT_DIR / "time_precip.npy", allow_pickle=True)
precip = np.load(INPUT_DIR / "precip.npy")
precip_scaled = np.load(INPUT_DIR_SCALED / "precip.npy")


sel = (START <= time) & (time <= END)
time = time[sel]
precip = precip[sel]
precip_scaled = precip_scaled[sel]

precip_mean = precip.mean(axis=(1, 2))
precip_scaled_mean = precip_scaled.mean(axis=(1, 2))

fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(2, 1, 1)

ax.plot(time, precip_mean, label="Observed")
ax.plot(time, precip_scaled_mean, label="Scaled")

ax.set_ylabel("Precipitation (mm/3hr)")
ax.legend()

ax = fig.add_subplot(2, 1, 2)
ax.plot(time, precip_scaled_mean - precip_mean)

ax.set_xlabel("Date")
ax.set_ylabel("Precipitation diff (mm/3hr)")

FIG_DIR.mkdir(exist_ok=True, parents=True)
fig.savefig(FIG_DIR / "precip_diff.png")

plt.show()
