"""Utility functions."""

import netCDF4 as nc
import numpy as np

from config import OCEAN_THRESHOLD


def mask_ocean_values(array):
    """Set values over the ocean to np.array in ``array``."""
    with nc.Dataset("data/IMERG_land_sea_mask.nc") as ncfile:
        sea_mask = ncfile.variables["landseamask"][:]

    sea_mask = sea_mask[::-1]
    sea_mask[sea_mask <= OCEAN_THRESHOLD] = 0
    sea_mask[sea_mask > OCEAN_THRESHOLD] = 1
    sea_mask = sea_mask.astype(bool)

    array_masked = array.copy()
    array_masked[..., sea_mask] = np.nan

    return array_masked


def repeat(array, size):
    """Repeat `array` (for example climatology) to fit length `size`."""
    return np.tile(array, 99)[:size]


def select_time(array, time, start, end, include_endpoint=False):
    """Select slice in ``array`` between ``start`` and ``end``."""
    if not include_endpoint:
        sel = (time >= start) & (time < end)
    else:
        sel = (time >= start) & (time <= end)
    return array[sel]


def set_small_values_to_zero(array, threshold=0.6e-1):
    """Set small values in ``array`` (<= ``threshold``) to 0."""
    res = array.copy()
    res[res <= threshold] = 0
    return res


def iterdates(start, end, interval, include_endpoint=False):
    date = start
    while date < end:
        yield date
        date += interval

    if include_endpoint and date == end:
        yield date
