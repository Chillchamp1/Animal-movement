#!/usr/bin/env python3
"""Bake the land and sea the storks fly over, from open elevation data.

Why bake it
-----------
A migration map without a coastline is unreadable: the whole point is that
these birds will not cross open water, so they funnel through Gibraltar and the
Levant. Tiles fetched at view time cannot provide that -- they need a host that
permits outbound requests, so they never appear in the self-contained build and
a strict content policy blocks them outright. Computed once, here, the backdrop
ships inside the page and works anywhere.

One source gives both halves. Terrarium tiles encode bathymetry as negative
elevation, so the same raster that hillshades the Atlas and the Alps also draws
every coastline, the continental shelf and the Mediterranean basin.

Source
------
Terrain Tiles on AWS Open Data (s3.amazonaws.com/elevation-tiles-prod), the
Mapzen/Nextzen terrarium set: SRTM and GMTED on land, ETOPO1 and other surveys
at sea. Terrarium encodes metres as `(R * 256 + G + B / 256) - 32768`.

The output is Web Mercator, matching the page's own projection, so no
reprojection is involved and the image drops straight into its rectangle.

Usage
-----
    python3 scripts/build_basemap.py
    python3 scripts/build_basemap.py --zoom 5 --tracks data/processed/storks.json
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import math
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

TILES = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
UA = "stork-migration-map/1.0 (+https://github.com/Chillchamp1)"

# A night map: the birds have to stay the brightest thing on it, so the ground
# sits just clear of the background and the sea just below it.
SEA_DEEP = (6, 11, 18)
SEA_SHELF = (10, 22, 35)
LAND_SHADOW = (11, 14, 19)
LAND_LIT = (46, 54, 66)
SHELF_M = -200.0          # the continental shelf break, roughly

AZIMUTH_DEG = 315.0
ALTITUDE_DEG = 42.0
PALETTE = 64              # colours kept after quantising; PNG shrinks by ~4x


def tile_x(lon: float, n: int) -> float:
    return (lon + 180.0) / 360.0 * n


def tile_y(lat: float, n: int) -> float:
    r = math.radians(lat)
    return (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n


def lat_of_tile_y(y: float, n: int) -> float:
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))


def fetch(url: str, retries: int = 5) -> bytes:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except (urllib.error.URLError, ConnectionResetError, TimeoutError) as exc:
            if attempt == retries - 1:
                raise
            print(f"    retry {attempt + 1}: {type(exc).__name__}", file=sys.stderr)
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def mosaic(zoom: int, region: dict, cache: Path):
    n = 2**zoom
    x0, x1 = int(tile_x(region["lon0"], n)), int(tile_x(region["lon1"], n))
    y0, y1 = int(tile_y(region["lat1"], n)), int(tile_y(region["lat0"], n))
    cache.mkdir(parents=True, exist_ok=True)

    out = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256), dtype=np.float32)
    total, done = (x1 - x0 + 1) * (y1 - y0 + 1), 0
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            path = cache / f"{zoom}_{tx}_{ty}.png"
            if not path.exists():
                path.write_bytes(fetch(TILES.format(z=zoom, x=tx % n, y=ty)))
            rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)
            elev = rgb[:, :, 0] * 256 + rgb[:, :, 1] + rgb[:, :, 2] / 256 - 32768
            out[(ty - y0) * 256:(ty - y0 + 1) * 256,
                (tx - x0) * 256:(tx - x0 + 1) * 256] = elev
            done += 1
            if done % 20 == 0 or done == total:
                print(f"  {done}/{total} tiles")
    # The exact edges of the stitched raster, which is what the page draws into.
    return out, {"lon0": (x0 / n) * 360 - 180, "lon1": ((x1 + 1) / n) * 360 - 180,
                 "lat1": lat_of_tile_y(y0, n), "lat0": lat_of_tile_y(y1 + 1, n)}


def hillshade(elev: np.ndarray, cell_m: np.ndarray) -> np.ndarray:
    """Horn's method. cell_m varies by row: Mercator pixels shrink with latitude."""
    dzdx = np.gradient(elev, axis=1) / cell_m
    dzdy = np.gradient(elev, axis=0) / cell_m
    slope = np.arctan(np.hypot(dzdx, dzdy))
    aspect = np.arctan2(-dzdy, dzdx)
    zenith = math.radians(90 - ALTITUDE_DEG)
    azimuth = math.radians(360 - AZIMUTH_DEG + 90)
    return np.clip(math.cos(zenith) * np.cos(slope)
                   + math.sin(zenith) * np.sin(slope) * np.cos(azimuth - aspect), 0, 1)


def ramp(t: np.ndarray, lo: tuple, hi: tuple) -> np.ndarray:
    lo_a, hi_a = np.array(lo, dtype=float), np.array(hi, dtype=float)
    return lo_a + (hi_a - lo_a) * t[:, :, None]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tracks", default="data/processed/storks.json", type=Path,
                    help="track file whose bounds set the frame")
    ap.add_argument("--zoom", type=int, default=5, help="tile zoom (5 is ~4.9 km/px)")
    ap.add_argument("--pad", type=float, default=1.5, help="degrees of margin round the data")
    ap.add_argument("--aspect", type=float, default=2.0,
                    help="widest window shape the backdrop should still fill")
    ap.add_argument("--width", type=int, default=3600, help="output width in pixels")
    ap.add_argument("--cache", default="data/raw/terrain", type=Path)
    ap.add_argument("--out", default="data/processed", type=Path)
    args = ap.parse_args()

    if not args.tracks.exists():
        raise SystemExit(f"missing {args.tracks}\n  run: python3 scripts/build_storks.py")
    b = json.loads(args.tracks.read_text())["bounds"]
    lat0 = max(-84, b["lat0"] - args.pad)
    lat1 = min(84, b["lat1"] + args.pad)

    # These birds span 91 degrees of latitude and 87 of longitude, so on any
    # ordinary window the page fits to the latitude and letterboxes the sides.
    # Filling that space with ground rather than void means covering the frame
    # the page will actually show, not just the frame the data occupies.
    def mer(lat):
        return math.log(math.tan(math.pi/4 + math.radians(lat)/2))
    need_lon = math.degrees(mer(lat1) - mer(lat0)) * args.aspect
    lon_c = (b["lon0"] + b["lon1"]) / 2
    half = max((b["lon1"] - b["lon0"]) / 2 + args.pad, need_lon / 2)
    region = {"lon0": max(-179, lon_c - half), "lon1": min(179, lon_c + half),
              "lat0": lat0, "lat1": lat1}
    print(f"frame lon {region['lon0']:.1f}..{region['lon1']:.1f}  "
          f"lat {region['lat0']:.1f}..{region['lat1']:.1f}, zoom {args.zoom}")

    elev, bounds = mosaic(args.zoom, region, args.cache)
    print(f"  raster {elev.shape[1]} x {elev.shape[0]}, "
          f"{elev.min():.0f} m to {elev.max():.0f} m")

    # A Mercator pixel covers less ground the further it is from the equator, so
    # the shading cell size is per row rather than a single number.
    n = 2**args.zoom
    rows = np.arange(elev.shape[0])
    y_tiles = int(tile_y(bounds["lat1"], n)) + rows / 256
    lats = np.array([lat_of_tile_y(y, n) for y in y_tiles])
    cell_m = (156543.03392 * np.cos(np.radians(lats)) / n)[:, None]

    sea = elev <= 0
    shade = hillshade(np.where(sea, 0, elev), cell_m)
    # Depth only needs to separate shelf from basin; past the shelf it is flat.
    depth = np.clip(elev / SHELF_M, 0, 1)

    # Flat ground returns cos(zenith) from the hillshade -- about 0.67 -- so a
    # straight ramp paints the Sahara and the Russian plain a solid mid-grey and
    # the continents read as pale slabs. Rebasing on that value drops flat land
    # close to the background and keeps the range for slopes that actually face
    # the light, which is what the relief is for.
    flat = math.cos(math.radians(90 - ALTITUDE_DEG))
    lift = np.clip((shade - flat * 0.82) / (1 - flat * 0.82), 0, 1)
    rgb = np.where(sea[:, :, None],
                   ramp(1 - depth, SEA_DEEP, SEA_SHELF),
                   ramp(lift, LAND_SHADOW, LAND_LIT))

    img = Image.fromarray(rgb.astype(np.uint8), mode="RGB")
    height = int(round(args.width * img.height / img.width))
    img = img.resize((args.width, height), Image.LANCZOS).quantize(
        colors=PALETTE, method=Image.MEDIANCUT)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    png = buf.getvalue()

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "basemap.json").write_text(json.dumps({
        "source": "Terrain Tiles on AWS Open Data (Mapzen/Nextzen terrarium): SRTM and "
                  "GMTED on land, ETOPO1 and other surveys at sea",
        "note": "Land hillshade and sea depth from one elevation raster, in Web "
                "Mercator to match the page, baked in so it needs no requests at "
                "view time.",
        "attribution": "Elevation and bathymetry: Terrain Tiles on AWS Open Data",
        "bounds": {k: round(v, 5) for k, v in bounds.items()},
        "projection": "web-mercator",
        "zoom": args.zoom, "azimuth": AZIMUTH_DEG, "altitude": ALTITUDE_DEG,
        "elevationM": [int(elev.min()), int(elev.max())],
        "width": args.width, "height": height,
        "png": "data:image/png;base64," + base64.b64encode(png).decode("ascii"),
    }, separators=(",", ":")))
    print(f"  basemap {args.width} x {height}, PNG {len(png)/1e6:.2f} MB")
    print(f"wrote {args.out}/basemap.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
