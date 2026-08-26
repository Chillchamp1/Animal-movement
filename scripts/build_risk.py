#!/usr/bin/env python3
"""Bin the predator utilisation index into a raster for the map's risk layer.

The deposit carries no predator coordinates -- lions and wild dogs appear only
as (a) diel activity windows and (b) a utilisation index (UI) evaluated at every
prey location, used and available alike. The available points are drawn across
the whole study extent, so pooling all of them recovers a spatial sample of each
predator's utilisation distribution.

Four surfaces are produced -- dog and lion, each in their active and inactive
state -- as coarse rasters in WGS84.

Usage
-----
    python3 scripts/build_risk.py [--raw data/raw] [--out data/processed]
                                  [--cell 500]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

try:
    from pyproj import Transformer
except ImportError:
    sys.exit("pyproj is required: pip install pyproj")

TO_WGS84 = Transformer.from_crs("EPSG:32734", "EPSG:4326", always_xy=True)

RSF_FILES = [
    "RSF/Impala RSF.csv",
    "RSF/Tsessebe dry RSF.csv",
    "RSF/Tsessebe rainy RSF.csv",
    "RSF/Wildebeest dry RSF.csv",
    "RSF/Wildebeest rainy RSF.csv",
    "RSF/Zebra dry RSF.csv",
    "RSF/Zebra rainy RSF.csv",
]

# A cell needs a few samples before its mean means anything.
MIN_SAMPLES = 3


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--out", type=Path, default=Path("data/processed"))
    ap.add_argument("--cell", type=float, default=500.0, help="cell size in metres")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    # Pass 1: extent.
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    for rel in RSF_FILES:
        path = args.raw / rel
        if not path.exists():
            continue
        with path.open(newline="") as fh:
            for r in csv.DictReader(fh):
                x, y = float(r["x"]), float(r["y"])
                x0, x1 = min(x0, x), max(x1, x)
                y0, y1 = min(y0, y), max(y1, y)
    if x0 == float("inf"):
        sys.exit(f"no RSF files found under {args.raw}")

    cell = args.cell
    nx = int((x1 - x0) / cell) + 1
    ny = int((y1 - y0) / cell) + 1
    print(f"extent {x1-x0:.0f} x {y1-y0:.0f} m -> {nx} x {ny} cells of {cell:.0f} m")

    # Pass 2: accumulate UI per predator/activity per cell. Grids are allocated
    # once up front -- building them per row is what makes this crawl.
    ncell = nx * ny
    acc = {(p, a): ([0.0] * ncell, [0] * ncell)
           for p in ("Dog", "Lion") for a in ("High", "Low")}
    for rel in RSF_FILES:
        path = args.raw / rel
        if not path.exists():
            print(f"  missing {rel}, skipped")
            continue
        with path.open(newline="") as fh:
            for r in csv.DictReader(fh):
                total, count = acc[(r["Pred"], r["Activity"])]
                idx = (int((float(r["y"]) - y0) / cell) * nx
                       + int((float(r["x"]) - x0) / cell))
                total[idx] += float(r["UI"])
                count[idx] += 1

    lon0, lat0 = TO_WGS84.transform(x0, y0)
    lon1, lat1 = TO_WGS84.transform(x0 + nx * cell, y0 + ny * cell)

    surfaces = {}
    for (pred, act), (total, count) in sorted(acc.items()):
        means = [t / c if c >= MIN_SAMPLES else 0.0 for t, c in zip(total, count)]
        peak = max(means)
        covered = sum(1 for c in count if c >= MIN_SAMPLES)
        # Quantise to a byte; the layer is a wash of colour, not a readout.
        surfaces[f"{pred.lower()}-{act.lower()}"] = {
            "peak": peak,
            "cells": [round(255 * m / peak) if peak else 0 for m in means],
            "covered": covered,
        }
        print(f"  {pred:5s} {act:4s}  peak UI={peak:.3e}  "
              f"cells with data={covered}/{ncell}")

    payload = {
        "source": "Bennitt et al. 2024, doi:10.5061/dryad.w0vt4b8zr",
        "note": ("Predator utilisation index sampled at prey used/available "
                 "locations; not a predator track."),
        "bounds": {"lon0": round(lon0, 5), "lat0": round(lat0, 5),
                   "lon1": round(lon1, 5), "lat1": round(lat1, 5)},
        "nx": nx, "ny": ny, "cellM": cell, "minSamples": MIN_SAMPLES,
        "surfaces": surfaces,
    }
    out = args.out / "predator-risk.json"
    out.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"\nWritten to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
