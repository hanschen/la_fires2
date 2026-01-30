#!/usr/bin/env python
"""Select area for temperature from MSWX."""

import subprocess
import sys
from pathlib import Path

from tqdm import tqdm

CDO_COMMAND = [
    "cdo",
    "-L",
    "-sellonlatbox,-118.6,-117.4,33.4,34.6",
]

MSWX_DIR = Path("/data0/data/mswx_v100")
VARIABLES = {
    "temp": "Temp",
    "swd": "SWd",
    "rh": "RelHum",
    "wind": "Wind",
}

LOG_DIR = Path("log")
OUTPUT_DIR = Path("/data0/tmp/la_fires")


def main(variable="temp"):
    log_dir = LOG_DIR / variable
    output_dir = OUTPUT_DIR / variable
    log_dir.mkdir(exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    past_dir = MSWX_DIR / "Past" / VARIABLES[variable] / "3hourly"

    files = {
        "skipped": [],
        "past": [],
        "error": [],
    }

    for f in tqdm(sorted(past_dir.glob("*.nc"))):
        output_file = output_dir / f.name
        if output_file.exists():
            files["skipped"].append(f)
            continue

        command = CDO_COMMAND + [f, output_file]
        result = subprocess.run(command, stdout=subprocess.DEVNULL)

        if result.returncode != 0:
            files["error"].append(f)
        else:
            files["past"].append(f)

    # Save logs
    for logtype, filepaths in files.items():
        with open(LOG_DIR / f"temp_{logtype}.log", "w") as logfile:
            for f in filepaths:
                logfile.write(f"{f}\n")

    if files["error"]:
        print("Could not properly process the following files:")
        for f in files["error"]:
            print(f)

    print("Done.")


if __name__ == "__main__":
    try:
        variable = sys.argv[1]
    except IndexError:
        print(f"Usage: {sys.argv[0]} VARIABLE")
        print("")
        print("Possible variables: " + ", ".join(VARIABLES.keys()))
    else:
        main(variable)
