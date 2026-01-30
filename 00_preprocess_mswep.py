#!/usr/bin/env python
"""Select area for precipitation from MSWEP."""

import subprocess
from pathlib import Path

from tqdm import tqdm

CDO_COMMAND = [
    "cdo",
    "-L",
    "-sellonlatbox,-118.6,-117.4,33.4,34.6",
    "-selname,precipitation",
]

MSWEP_DIR = Path("/data0/data/mswep_v280")

LOG_DIR = Path("log")
OUTPUT_DIR = Path("/data0/tmp/la_fires/precip")


def main():
    LOG_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    nrt_dir = MSWEP_DIR / "NRT" / "3hourly"
    past_dir = MSWEP_DIR / "Past" / "3hourly"

    files = {
        "skipped": [],
        "past": [],
        "nrt": [],
        "error": [],
    }

    # Past
    for f in tqdm(sorted(past_dir.glob("*.nc"))):
        output_file = OUTPUT_DIR / f.name
        if output_file.exists():
            files["skipped"].append(f)
            continue

        command = CDO_COMMAND + [f, output_file]
        result = subprocess.run(command, stdout=subprocess.DEVNULL)

        if result.returncode != 0:
            files["error"].append(f)
        else:
            files["past"].append(f)

    # NRT
    for f in tqdm(sorted(nrt_dir.glob("*.nc"))):
        output_file = OUTPUT_DIR / f.name
        if output_file.exists():
            files["skipped"].append(f)
            continue

        command = CDO_COMMAND + [f, output_file]
        result = subprocess.run(command, stdout=subprocess.DEVNULL)

        if result.returncode != 0:
            files["error"].append(f)
        else:
            files["nrt"].append(f)

    # Save logs
    for logtype, filepaths in files.items():
        with open(LOG_DIR / f"precip_{logtype}.log", "w") as logfile:
            for f in filepaths:
                logfile.write(f"{f}\n")

    if files["error"]:
        print("Could not properly process the following files:")
        for f in files["error"]:
            print(f)

    print("Done.")


if __name__ == "__main__":
    main()
