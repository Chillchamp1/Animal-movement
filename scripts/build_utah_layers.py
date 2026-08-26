#!/usr/bin/env python3
"""Build the two landscape layers for the Utah map, both measured.

The Okavango map's layers were inferences: its predator range came from a
modelled utilisation surface sampled at prey locations, because no predator
was ever positioned, and its "flood shift" was a map of where animals went
rather than of water. Here both layers are observations.

  cougar-use.json   where the collared cougars actually were, per season
  year-shift.json   2019 against 2020, for the animals collared in both years

Usage
-----
    python3 scripts/build_utah_layers.py
    python3 scripts/build_utah_layers.py --cell 1000
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_utah import (COUGAR_NAMES, REGION, SEASONS, UNGULATE_NAMES,  # noqa: E402
                        find, read_deposit)

M_PER_DEG_LAT = 111_320.0


def grid_shape(cell_m: float) -> tuple[int, int, float]:
    m_per_deg_lon = M_PER_DEG_LAT * math.cos(
        math.radians((REGION["lat0"] + REGION["lat1"]) / 2))
    nx = int((REGION["lon1"] - REGION["lon0"]) * m_per_deg_lon / cell_m)
    ny = int((REGION["lat1"] - REGION["lat0"]) * M_PER_DEG_LAT / cell_m)
    return nx, ny, m_per_deg_lon


def occupancy(df: pd.DataFrame, nx: int, ny: int, m_per_deg_lon: float,
              cell_m: float, sigma_cells: float) -> np.ndarray:
    """Fix density on the grid, smoothed so single fixes do not read as range."""
    ix = ((df.lon.to_numpy() - REGION["lon0"]) * m_per_deg_lon / cell_m).astype(int)
    iy = ((df.lat.to_numpy() - REGION["lat0"]) * M_PER_DEG_LAT / cell_m).astype(int)
    keep = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    g = np.zeros((ny, nx))
    np.add.at(g, (iy[keep], ix[keep]), 1.0)
    return smooth(g, sigma_cells)


def smooth(g: np.ndarray, sigma: float) -> np.ndarray:
    """Separable Gaussian blur. Kept local so the script needs no scipy."""
    if sigma <= 0:
        return g
    r = int(math.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    out = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 1, g)
    return np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 0, out)


def bounds_of(nx: int, ny: int, m_per_deg_lon: float, cell_m: float) -> dict:
    return {"lon0": round(REGION["lon0"], 5), "lat0": round(REGION["lat0"], 5),
            "lon1": round(REGION["lon0"] + nx * cell_m / m_per_deg_lon, 5),
            "lat1": round(REGION["lat0"] + ny * cell_m / M_PER_DEG_LAT, 5)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw/movebank", type=Path)
    ap.add_argument("--out", default="data/processed", type=Path)
    ap.add_argument("--cell", default=1000.0, type=float, help="grid cell size in metres")
    args = ap.parse_args()

    df = pd.concat([read_deposit(find(args.raw, COUGAR_NAMES), "Puma concolor"),
                    read_deposit(find(args.raw, UNGULATE_NAMES))], ignore_index=True)
    nx, ny, m_per_deg_lon = grid_shape(args.cell)
    bounds = bounds_of(nx, ny, m_per_deg_lon, args.cell)
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"grid {nx} x {ny} at {args.cell:.0f} m")

    # --- where the cougars were, per season -------------------------------
    surfaces = {}
    for season, (start, end) in SEASONS.items():
        part = df[(df.sp == "cougar") & (df.timestamp >= pd.Timestamp(start))
                  & (df.timestamp < pd.Timestamp(end))]
        g = occupancy(part, nx, ny, m_per_deg_lon, args.cell, sigma_cells=2.0)
        peak = float(g.max())
        surfaces[season] = {
            "peak": peak,
            "animals": int(part.id.nunique()),
            "fixes": int(len(part)),
            "cells": [int(round(255 * v / peak)) if peak else 0 for v in g.ravel()],
        }
        print(f"  cougar {season}: {part.id.nunique()} animals, {len(part):,} fixes")

    (args.out / "cougar-use.json").write_text(json.dumps({
        "source": "Utah DWR, doi:10.5441/001/1.712 (CC0)",
        "note": ("Where the collared cougars actually were, smoothed. Only 8-11 "
                 "cougars were collared here, so blank ground means no collar "
                 "recorded a cougar there, not that none was."),
        "bounds": bounds, "nx": nx, "ny": ny, "cellM": args.cell,
        "surfaces": surfaces,
    }, separators=(",", ":")))

    # --- 2019 against 2020, same animals ----------------------------------
    df = df.assign(yr=df.timestamp.dt.year)
    years = df.groupby(["sp", "id"]).yr.nunique()
    paired = set(years[years == 2].index)
    both = df[df.set_index(["sp", "id"]).index.isin(paired)]

    # Smoothed harder than the cougar layer: this one covers the whole block,
    # so a tight kernel leaves it reading as a grid of squares.
    a = occupancy(both[both.yr == 2019], nx, ny, m_per_deg_lon, args.cell, 2.5)
    b = occupancy(both[both.yr == 2020], nx, ny, m_per_deg_lon, args.cell, 2.5)
    # Share of each cell's use, so an animal with more fixes cannot outvote the
    # comparison; positive means 2019, negative 2020.
    a = a / a.sum() if a.sum() else a
    b = b / b.sum() if b.sum() else b
    tot = a + b
    diff = np.zeros_like(tot)
    live = tot > 0
    diff[live] = (a[live] - b[live]) / tot[live] * 100
    # A cell nobody used is not a finding; leave it transparent.
    floor = np.quantile(tot[live], 0.55) if live.any() else 0
    diff[tot < floor] = 0

    counts = both.groupby("sp").id.nunique().to_dict()
    (args.out / "year-shift.json").write_text(json.dumps({
        "source": "Utah DWR, doi:10.5441/001/1.711 and 1.712 (CC0)",
        "note": ("January-to-May occupancy in 2019 against 2020, for the animals "
                 "collared in both years. A map of where these animals went."),
        "animals": {k: int(v) for k, v in counts.items()},
        "fixes": int(len(both)),
        "bounds": bounds, "nx": nx, "ny": ny, "cellM": args.cell,
        "cells": [int(round(v)) for v in diff.ravel()],
    }, separators=(",", ":")))

    print(f"  year shift: {sum(counts.values())} animals in both years "
          f"({', '.join(f'{k} {v}' for k, v in sorted(counts.items()))}), "
          f"{len(both):,} fixes")
    print(f"\nwrote {args.out}/cougar-use.json and {args.out}/year-shift.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
