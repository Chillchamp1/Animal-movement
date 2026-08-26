#!/usr/bin/env python3
"""Bake a hillshade of the study block from open elevation data.

Why bake it
-----------
The satellite layer fetches Esri tiles at view time, which means it needs a
host that permits outbound requests -- it never appears in the self-contained
build, and a strict content policy blocks it outright. Terrain does not have
that problem if the relief is computed once, here, and shipped inside the page.

It is also the more honest backdrop for this map. The satellite mosaic is a
composite of mixed dates that has nothing to do with 2019-2020; relief does not
change between winters, and in the Wasatch it is most of the reason the animals
are where they are.

Source
------
Terrain Tiles on AWS Open Data (s3.amazonaws.com/elevation-tiles-prod), the
Mapzen/Nextzen terrarium set. Over the United States it is USGS 3DEP/NED, in
the public domain. Terrarium encodes metres as
`(R * 256 + G + B / 256) - 32768`.

Usage
-----
    python3 scripts/build_terrain.py
    python3 scripts/build_terrain.py --zoom 11 --width 1600
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_utah import REGION  # noqa: E402

TILES = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
UA = "wasatch-movement-map/1.0 (+https://github.com/Chillchamp1)"

# Shipped as an 8-bit greyscale ramp rather than a coloured RGBA image: three
# of the four channels carry the same number, and dropping them takes the PNG
# from 3.0 MB to 1.0 MB. The page multiplies it by the lit colour, which is the
# same ramp from black, and its background is near-black anyway.
SHADE_LEVELS = 48   # posterising this far is invisible on a dark hillshade

AZIMUTH_DEG = 315.0     # light from the north-west, the cartographic convention
ALTITUDE_DEG = 42.0


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


def mosaic(zoom: int, cache: Path) -> tuple[np.ndarray, int, int, int, int]:
    """Stitch every tile covering the region into one elevation raster."""
    n = 2**zoom
    x0, x1 = int(tile_x(REGION["lon0"], n)), int(tile_x(REGION["lon1"], n))
    y0, y1 = int(tile_y(REGION["lat1"], n)), int(tile_y(REGION["lat0"], n))
    cache.mkdir(parents=True, exist_ok=True)

    out = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256), dtype=np.float32)
    total = (x1 - x0 + 1) * (y1 - y0 + 1)
    done = 0
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            path = cache / f"{zoom}_{tx}_{ty}.png"
            if not path.exists():
                path.write_bytes(fetch(TILES.format(z=zoom, x=tx, y=ty)))
            rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)
            elev = rgb[:, :, 0] * 256 + rgb[:, :, 1] + rgb[:, :, 2] / 256 - 32768
            out[(ty - y0) * 256:(ty - y0 + 1) * 256,
                (tx - x0) * 256:(tx - x0 + 1) * 256] = elev
            done += 1
            if done % 16 == 0 or done == total:
                print(f"  {done}/{total} tiles")
    return out, x0, x1, y0, y1


def hillshade(elev: np.ndarray, cell_m: float) -> np.ndarray:
    """Horn's method. Returns illumination in 0..1."""
    dzdx = np.gradient(elev, axis=1) / cell_m
    dzdy = np.gradient(elev, axis=0) / cell_m
    slope = np.arctan(np.hypot(dzdx, dzdy))
    aspect = np.arctan2(-dzdy, dzdx)
    zenith = math.radians(90 - ALTITUDE_DEG)
    azimuth = math.radians(360 - AZIMUTH_DEG + 90)
    shade = (math.cos(zenith) * np.cos(slope)
             + math.sin(zenith) * np.sin(slope) * np.cos(azimuth - aspect))
    return np.clip(shade, 0, 1)


def to_equirect(src: np.ndarray, y0: int, y1: int, n: int, rows: int) -> np.ndarray:
    """Resample the Mercator rows onto evenly spaced latitudes.

    The page draws in equirectangular, so a Mercator raster stretched into the
    same rectangle would sit a little north of the ground it describes. Rather
    than correct for that in the browser the rows are resampled here, once.
    """
    lat_top, lat_bot = REGION["lat1"], REGION["lat0"]
    wanted = np.linspace(lat_top, lat_bot, rows)
    # Where each wanted latitude falls in the source raster, in pixel rows.
    src_rows = np.array([(tile_y(lat, n) - y0) * 256 for lat in wanted])
    src_rows = np.clip(src_rows, 0, src.shape[0] - 1)
    lo = np.floor(src_rows).astype(int)
    hi = np.minimum(lo + 1, src.shape[0] - 1)
    f = (src_rows - lo)[:, None]
    return src[lo] * (1 - f) + src[hi] * f


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zoom", type=int, default=11, help="tile zoom (11 is ~57 m/px here)")
    ap.add_argument("--width", type=int, default=1600, help="output width in pixels")
    ap.add_argument("--cache", default="data/raw/terrain", type=Path)
    ap.add_argument("--out", default="data/processed", type=Path)
    args = ap.parse_args()

    n = 2**args.zoom
    print(f"fetching zoom {args.zoom} terrain tiles ...")
    elev, x0, x1, y0, y1 = mosaic(args.zoom, args.cache)

    # Crop to the region's own edges before shading, so the relief lines up with
    # the tracks rather than with whatever the tile grid happened to cover.
    left = int(round((tile_x(REGION["lon0"], n) - x0) * 256))
    right = int(round((tile_x(REGION["lon1"], n) - x0) * 256))
    top = int(round((tile_y(REGION["lat1"], n) - y0) * 256))
    bottom = int(round((tile_y(REGION["lat0"], n) - y0) * 256))
    elev = elev[top:bottom, left:right]
    print(f"  raster {elev.shape[1]} x {elev.shape[0]}, "
          f"elevation {elev.min():.0f}-{elev.max():.0f} m")

    mid = (REGION["lat0"] + REGION["lat1"]) / 2
    cell_m = 156543.03392 * math.cos(math.radians(mid)) / n
    shade = hillshade(elev, cell_m)

    # Equirectangular rows, at the aspect ratio the page will draw it into.
    aspect = ((REGION["lat1"] - REGION["lat0"])
              / ((REGION["lon1"] - REGION["lon0"]) * math.cos(math.radians(mid))))
    rows = int(round(args.width * aspect))
    shade = to_equirect(shade, y0 + top / 256, y1, n, rows)
    img = Image.fromarray((shade * 255).astype(np.uint8)).resize(
        (args.width, rows), Image.LANCZOS)
    levels = np.asarray(img, dtype=float) / 255.0
    levels = np.round(levels * (SHADE_LEVELS - 1)) / (SHADE_LEVELS - 1)

    buf = io.BytesIO()
    Image.fromarray((levels * 255).astype(np.uint8), mode="L").save(
        buf, format="PNG", optimize=True)
    png = buf.getvalue()

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "terrain.json").write_text(json.dumps({
        "source": "Terrain Tiles on AWS Open Data (Mapzen/Nextzen terrarium); "
                  "USGS 3DEP/NED over the United States, public domain",
        "note": "Hillshade computed from elevation, reprojected to equirectangular "
                "and baked in, so it needs no requests at view time.",
        "attribution": "Elevation: USGS 3DEP via Terrain Tiles on AWS Open Data",
        "bounds": {k: round(v, 5) for k, v in REGION.items()},
        "azimuth": AZIMUTH_DEG, "altitude": ALTITUDE_DEG,
        "shadeLevels": SHADE_LEVELS,
        "elevationM": [int(elev.min()), int(elev.max())],
        "zoom": args.zoom, "cellM": round(cell_m, 1),
        "width": args.width, "height": rows,
        "png": "data:image/png;base64," + base64.b64encode(png).decode("ascii"),
    }, separators=(",", ":")))
    print(f"  hillshade {args.width} x {rows}, PNG {len(png)/1e6:.2f} MB")
    print(f"wrote {args.out}/terrain.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
