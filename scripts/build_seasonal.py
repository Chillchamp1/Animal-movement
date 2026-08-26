#!/usr/bin/env python3
"""Derive a seasonal range-shift raster from animals collared in both seasons.

Why this layer exists
---------------------
The deposit carries no spatial habitat layer: vegetation class appears only as
aggregate proportions per animal, never mapped, and the 25 m habitat raster the
original analysis used was not deposited. Public vector data does not fill the
gap either -- Natural Earth at 1:10m resolves the entire Okavango as a single
river centreline, which says nothing at a 70 km window.

What can be measured is where the animals themselves went in each season. In
the Okavango the flood arrives during the dry season, pushing herbivores off the
inundated floodplain and pulling them back as it recedes, so a dry-versus-rainy
contrast in occupancy traces the flood-driven structure of the landscape.

The obvious version of that contrast is confounded: different individuals were
collared in each season, so it would partly measure who was wearing a collar
rather than what the season did. Only animals present in BOTH seasons are used
here, which makes the comparison within-individual.

This is a map of animal behaviour, not a map of water. It is labelled that way
on the page.

Usage
-----
    python3 scripts/build_seasonal.py [--cell 1000] [--min-fixes 30]
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, default=Path("data/processed"))
    ap.add_argument("--cell", type=float, default=1000.0, help="cell size in metres")
    ap.add_argument("--min-fixes", type=int, default=30,
                    help="fixes a cell needs before its ratio is trusted")
    args = ap.parse_args()

    # Collect tracks by species/season, keeping only individuals in both.
    by_species = collections.defaultdict(lambda: collections.defaultdict(dict))
    for path in sorted(args.data.glob("*.json")):
        payload = json.loads(path.read_text())
        if "season" not in payload:
            continue
        for ind in payload["individuals"]:
            by_species[payload["species"]][ind["id"]][payload["season"]] = ind

    paired = []
    for species, inds in sorted(by_species.items()):
        both = [i for i, seasons in inds.items() if len(seasons) == 2]
        if both:
            print(f"  {species:11s} in both seasons: {', '.join(sorted(both))}")
        for ind_id in both:
            for season, ind in inds[ind_id].items():
                paired.append((season, ind))
    if not paired:
        raise SystemExit("no individuals present in both seasons")

    # One degree of latitude is ~110.57 km; longitude shrinks by cos(lat).
    pts = []
    for season, ind in paired:
        for seg in ind["segments"]:
            for c in seg["coords"]:
                pts.append((c[0], c[1], season))
    lat_mid = sum(p[1] for p in pts) / len(pts)
    import math
    m_per_deg_lat = 110574.0
    m_per_deg_lon = 111320.0 * math.cos(math.radians(lat_mid))

    lon0 = min(p[0] for p in pts); lat0 = min(p[1] for p in pts)
    lon1 = max(p[0] for p in pts); lat1 = max(p[1] for p in pts)
    nx = int((lon1 - lon0) * m_per_deg_lon / args.cell) + 1
    ny = int((lat1 - lat0) * m_per_deg_lat / args.cell) + 1

    dry = [0] * (nx * ny)
    rainy = [0] * (nx * ny)
    for lon, lat, season in pts:
        ix = min(nx - 1, int((lon - lon0) * m_per_deg_lon / args.cell))
        iy = min(ny - 1, int((lat - lat0) * m_per_deg_lat / args.cell))
        (dry if season == "Dry" else rainy)[iy * nx + ix] += 1

    # -100 = used only in the rainy season, +100 = only in the dry, 0 = even.
    # Cells below the fixes floor are left empty rather than guessed at.
    cells = []
    covered = 0
    for d, r in zip(dry, rainy):
        total = d + r
        if total < args.min_fixes:
            cells.append(0)
            continue
        covered += 1
        cells.append(max(-100, min(100, round(100 * (d - r) / total))) or 1)

    payload = {
        "source": "Bennitt et al. 2024, doi:10.5061/dryad.w0vt4b8zr",
        "note": ("Dry-versus-rainy occupancy for the animals collared in both "
                 "seasons. A map of where these animals went, not of water or "
                 "vegetation."),
        "individuals": sorted({ind["id"] for _, ind in paired}),
        "fixes": len(pts),
        "bounds": {"lon0": round(lon0, 5), "lat0": round(lat0, 5),
                   "lon1": round(lon0 + nx * args.cell / m_per_deg_lon, 5),
                   "lat1": round(lat0 + ny * args.cell / m_per_deg_lat, 5)},
        "nx": nx, "ny": ny, "cellM": args.cell, "minFixes": args.min_fixes,
        "cells": cells,
    }
    out = args.data / "seasonal-shift.json"
    out.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"\n{len(pts):,} fixes from {len(payload['individuals'])} individuals")
    print(f"grid {nx} x {ny} at {args.cell:.0f} m; {covered} cells above the "
          f"{args.min_fixes}-fix floor")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
