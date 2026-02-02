from pathlib import Path

import numpy as np

import config
import ioutils

INPUT_DIR = Path("output/select_data")
INPUT_DIR_SCALED = Path("output/scale_precipitation")

OUTPUT_DIR = Path("output/create_experiment")
EXPERIMENT_NAME = "scaled_to_climatology"

OUTPUT_VARIABLES = [
    "temp",
    "precip",
    "rh",
    "swd",
    "wind",
]


# %% Load data

variables = {}
times = {}
for variable in OUTPUT_VARIABLES:
    if variable == "precip":
        input_dir = INPUT_DIR_SCALED
    else:
        input_dir = INPUT_DIR
    variables[variable] = np.load(input_dir / f"{variable}.npy")
    times[variable] = np.load(
        input_dir / f"time_{variable}.npy", allow_pickle=True
    )

lats = np.load(INPUT_DIR / "lats.npy")
lons = np.load(INPUT_DIR / "lons.npy")


# %% Save experiment

OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
exp_dir = OUTPUT_DIR / EXPERIMENT_NAME
ioutils.create_netcdf(
    output_dir=exp_dir,
    start_date=config.EXP_START,
    end_date=config.EXP_END,
    variables=variables,
    times=times,
    lats=lats,
    lons=lons,
)
