#!/usr/bin/env python3
"""Reduce ESA WorldCover to a coarse green-and-water grid for the backdrop.

Why
---
The hillshade says where the ground is high and the bathymetry says where the
sea is, but neither says where a stork can feed. Two things matter on this
route: standing water, and the green belt of the Sahel that ends the desert
crossing. WorldCover measures both.

Source
------
ESA WorldCover 2021 v200 (CC BY 4.0), 10 m global land cover, on AWS Open Data
as cloud-optimised GeoTIFFs in 3-degree tiles. Full resolution would be ~500 GB
over this region; the map needs about 5 km per pixel, so each tile is read at
its coarsest internal overview -- one small request each, 562x562 instead of
36000x36000 -- and reduced further to a 0.05-degree grid.

Classes used: 80 permanent water and 90 herbaceous wetland are water; 10 tree
cover, 20 shrubland, 30 grassland, 40 cropland, 95 mangroves and 100 moss and
lichen are green. 60 bare and sparse vegetation -- the Sahara -- is neither.

The result is cached, because fetching it takes about ten minutes and it never
changes.

Usage
-----
    python3 scripts/build_landcover.py
    python3 scripts/build_landcover.py --cell 0.05 --out data/raw/landcover
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")

import numpy as np  # noqa: E402
import rasterio  # noqa: E402

BUCKET = "https://esa-worldcover.s3.eu-central-1.amazonaws.com"
GRID = f"{BUCKET}/esa_worldcover_grid.geojson"
TILE = BUCKET + "/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
UA = "stork-migration-map/1.0 (+https://github.com/Chillchamp1)"

WATER = (80, 90)
GREEN = (10, 20, 30, 40, 95, 100)
TILE_DEG = 3


def tile_origin(name: str) -> tuple[int, int]:
    """'N12E000' -> (lat, lon) of the tile's south-west corner."""
    lat = int(name[1:3]) * (1 if name[0] == "N" else -1)
    lon = int(name[4:7]) * (1 if name[3] == "E" else -1)
    return lat, lon


def tiles_over(region: dict) -> list[str]:
    req = urllib.request.Request(GRID, headers={"User-Agent": UA})
    grid = json.loads(urllib.request.urlopen(req, timeout=180).read())
    out = []
    for f in grid["features"]:
        name = f["properties"]["ll_tile"]
        lat, lon = tile_origin(name)
        if (region["lat0"] - TILE_DEG <= lat <= region["lat1"]
                and region["lon0"] - TILE_DEG <= lon <= region["lon1"]):
            out.append(name)
    return sorted(out)


def reduce_tile(name: str, cell: float) -> tuple[np.ndarray, np.ndarray] | None:
    """Fractions of water and green in each cell-sized block of one tile."""
    try:
        with rasterio.open("/vsicurl/" + TILE.format(tile=name)) as src:
            levels = src.overviews(1)
            lvl = levels[-1] if levels else 1
            a = src.read(1, out_shape=(1, src.height // lvl, src.width // lvl))
    except Exception as exc:
        print(f"    ! {name}: {type(exc).__name__}", file=sys.stderr)
        return None

    n = int(round(TILE_DEG / cell))          # cells per tile side
    h, w = a.shape
    # The overview is 562 px, which n does not divide. Trimming to a multiple
    # would drop the last 4% of each tile while still placing it as a full
    # three degrees -- a systematic shift that shows up as seams between tiles.
    # Binning every pixel by where it actually falls keeps the registration.
    bins = ((np.arange(h) * n) // h)[:, None] * n + ((np.arange(w) * n) // w)[None, :]
    flat = bins.ravel()
    count = np.bincount(flat, minlength=n * n).astype(float)
    def frac(mask):
        return (np.bincount(flat, weights=mask.ravel().astype(float),
                            minlength=n * n) / count).reshape(n, n)
    return frac(np.isin(a, WATER)), frac(np.isin(a, GREEN))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tracks", default="data/processed/storks.json", type=Path)
    ap.add_argument("--pad", type=float, default=25.0,
                    help="degrees beyond the data, to cover the whole drawn frame")
    ap.add_argument("--cell", type=float, default=0.05, help="output cell size in degrees")
    ap.add_argument("--out", default="data/raw/landcover", type=Path)
    args = ap.parse_args()

    b = json.loads(args.tracks.read_text())["bounds"]
    region = {"lon0": max(-180, b["lon0"] - args.pad), "lon1": min(180, b["lon1"] + args.pad),
              "lat0": max(-84, b["lat0"] - args.pad), "lat1": min(84, b["lat1"] + args.pad)}
    # Snap to the tile grid so every tile lands on a whole number of cells.
    for k, v in (("lon0", -1), ("lon1", 1), ("lat0", -1), ("lat1", 1)):
        region[k] = (int(region[k] // TILE_DEG) + (1 if v > 0 else 0)) * TILE_DEG

    names = tiles_over(region)
    nx = int(round((region["lon1"] - region["lon0"]) / args.cell))
    ny = int(round((region["lat1"] - region["lat0"]) / args.cell))
    print(f"region lon {region['lon0']}..{region['lon1']} lat {region['lat0']}..{region['lat1']}")
    print(f"{len(names)} tiles -> grid {nx} x {ny} at {args.cell} deg")

    water = np.zeros((ny, nx), dtype=np.float32)
    green = np.zeros((ny, nx), dtype=np.float32)
    per = int(round(TILE_DEG / args.cell))
    done = 0
    for name in names:
        lat, lon = tile_origin(name)
        col = int(round((lon - region["lon0"]) / args.cell))
        row = int(round((region["lat1"] - (lat + TILE_DEG)) / args.cell))
        if col < 0 or row < 0 or col + per > nx or row + per > ny:
            continue
        got = reduce_tile(name, args.cell)
        done += 1
        if got is None:
            continue
        w, g = got
        water[row:row+per, col:col+per] = w
        green[row:row+per, col:col+per] = g
        if done % 25 == 0 or done == len(names):
            print(f"  {done}/{len(names)} tiles", flush=True)

    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / "landcover.npz"
    np.savez_compressed(target, water=water, green=green,
                        bounds=np.array([region["lon0"], region["lat0"],
                                         region["lon1"], region["lat1"]]),
                        cell=np.array([args.cell]))
    print(f"\nwrote {target} ({target.stat().st_size/1e6:.2f} MB); "
          f"water covers {float((water > 0.5).mean())*100:.1f}% of cells, "
          f"green {float((green > 0.5).mean())*100:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
