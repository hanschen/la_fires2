#!/usr/bin/env python
"""Concatenate NetCDF files from preprocessed MSWX or MSWEP."""

import subprocess
import sys
from pathlib import Path

CDO_COMMAND = ["cdo", "cat"]

INPUT_DIR = Path("/data0/tmp/la_fires")
OUTPUT_DIR = Path("data")


def main(variable):
    OUTPUT_DIR.mkdir(exist_ok=True)

    output_file = OUTPUT_DIR / f"{variable}.nc"
    output_file.unlink(missing_ok=True)
    print(f"Concatenating {variable}...")
    command = CDO_COMMAND + [f"{INPUT_DIR}/{variable}/*.nc", output_file]
    subprocess.run(command)

    print("Done.")


if __name__ == "__main__":
    try:
        variable = sys.argv[1]
    except IndexError:
        print(f"Usage: {sys.argv[0]} VARIABLE")
    else:
        main(variable)
