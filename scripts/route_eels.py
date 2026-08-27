#!/usr/bin/env python3
"""Route the eel schematic's coastal legs over water instead of through it.

`build_eels.py` draws a corridor from the Sargasso Sea to twenty European and
North African river mouths and back. The first version joined the ocean trunk
to each mouth with a straight line, which was wrong in a way that is obvious
once drawn: a straight line from the Azores Current to the Rhone crosses Spain
and the Pyrenees. Measured against a land mask, **32 of the 40 coastal legs
crossed land, the worst of them for 1,100 km**.

Glass eels arrive by sea. They round Iberia into Biscay, pass Gibraltar to
reach the Mediterranean, and come through the Channel or round Scotland for the
North Sea and the Baltic. That is geography, not a modelling choice, so the
routes are computed rather than guessed: a shortest sea path over a real land
mask, with a mild penalty for hugging the coast.

The mask is the same terrarium elevation set the backdrop uses, at zoom 5
(about 3 km a pixel over this window), flood-filled from the open Atlantic so
that lakes at or below sea level -- Norway is full of them, and one of them
swallowed the first attempt at the Oslofjord -- cannot be mistaken for ocean.

Two legs per region are routed:

    approach   the ocean trunk's last point  ->  the river mouth
    home       the river mouth  ->  (a measured via point)  ->  the Azores

The via points are not shortest-path. Righton et al. 2016 tracked Baltic and
North Sea eels going north into the Norwegian Sea before turning west, and
western Mediterranean eels leaving through Gibraltar; a shortest path would
send the Baltic ones down the Channel. The measurement wins, and the router
only makes sure the measured detour stays on water.

Output is `scripts/eel_sea_routes.json`, committed, so `build_eels.py` needs no
network and stays deterministic. Re-run this only when the region list changes.

Usage:
    python3 scripts/route_eels.py                 # fetch, route, write
    python3 scripts/route_eels.py --verify        # re-check the committed file
    python3 scripts/route_eels.py --cache .tiles  # where to keep the tiles
"""

from __future__ import annotations

import argparse
import heapq
import io
import json
import math
import sys
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

TILES = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
UA = "eel-schematic-router/1.0 (+https://github.com/Chillchamp1)"
ZOOM = 5
WINDOW = dict(lon0=-82.0, lon1=40.0, lat0=15.0, lat1=70.0)

OUT = Path("scripts/eel_sea_routes.json")

# An open-ocean cell the flood fill starts from. Anything not reachable from
# here is a lake, an inland sea, or the far side of a continent.
OCEAN_SEED = (45.0, -30.0)

# Cost is multiplied by up to COAST_PENALTY within COAST_CELLS of land, so a
# route prefers a few kilometres of sea room to scraping the shore. A penalty
# rather than an erosion of the mask: erosion can close a strait, and the
# Great Belt is only sixteen kilometres wide.
COAST_CELLS = 4
COAST_PENALTY = 0.65

SIMPLIFY_DEG = 0.22          # Douglas-Peucker tolerance, ~24 km


# --------------------------------------------------------------- tile fetch

def tile_x(lon: float, n: int) -> float:
    return (lon + 180.0) / 360.0 * n


def tile_y(lat: float, n: int) -> float:
    s = math.sin(math.radians(max(-85.0, min(85.0, lat))))
    return (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n


def fetch(url: str, cache: Path) -> bytes:
    key = cache / (url.rsplit("/terrarium/", 1)[1].replace("/", "_"))
    if key.exists():
        return key.read_bytes()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
            key.parent.mkdir(parents=True, exist_ok=True)
            key.write_bytes(raw)
            return raw
        except (urllib.error.URLError, ConnectionResetError, TimeoutError):
            if attempt == 3:
                raise
    raise RuntimeError("unreachable")


class Mask:
    """The ocean, as a grid, with the geography to convert to and from it."""

    def __init__(self, elev: np.ndarray, x0: int, y0: int, z: int):
        self.x0, self.y0, self.z = x0, y0, z
        n = 1 << z
        h, w = elev.shape
        self.lon = np.array([((i + 0.5) / 256 + x0) / n * 360 - 180
                             for i in range(w)])
        self.lat = np.array([
            math.degrees(math.atan(math.sinh(
                math.pi - 2 * math.pi * ((j + 0.5) / 256 + y0) / n)))
            for j in range(h)])
        water = elev <= 0
        self.sea = self._ocean_only(water)
        self.coast = self._distance_to_land(self.sea)
        print(f"  grid {h}x{w}, water {water.mean():.3f}, "
              f"ocean-connected {self.sea.mean():.3f}")

    def _ocean_only(self, water: np.ndarray) -> np.ndarray:
        h, w = water.shape
        seed = self.cell(*OCEAN_SEED)
        assert water[seed], "the ocean seed is not on water"
        seen = np.zeros_like(water)
        q = deque([seed])
        seen[seed] = True
        nb = ((-1, 0), (1, 0), (0, -1), (0, 1),
              (-1, -1), (-1, 1), (1, -1), (1, 1))
        while q:
            j, i = q.popleft()
            for dy, dx in nb:
                a, b = j + dy, i + dx
                if 0 <= a < h and 0 <= b < w and water[a, b] and not seen[a, b]:
                    seen[a, b] = True
                    q.append((a, b))
        return seen

    def _distance_to_land(self, sea: np.ndarray) -> np.ndarray:
        """Cells from the nearest non-ocean cell, saturating at COAST_CELLS."""
        d = np.where(sea, COAST_CELLS, 0).astype(np.int8)
        for step in range(COAST_CELLS - 1, 0, -1):
            near = np.zeros_like(sea)
            src = d <= step
            near[1:, :] |= src[:-1, :]
            near[:-1, :] |= src[1:, :]
            near[:, 1:] |= src[:, :-1]
            near[:, :-1] |= src[:, 1:]
            d = np.where(sea & near & (d > step), step, d)
        return d

    def cell(self, lat: float, lon: float) -> tuple[int, int]:
        j = int(np.clip(np.searchsorted(-self.lat, -lat) - 1,
                        0, len(self.lat) - 1))
        i = int(np.clip(np.searchsorted(self.lon, lon) - 1,
                        0, len(self.lon) - 1))
        return j, i

    def nearest_ocean(self, lat: float, lon: float, maxr: int = 40):
        j, i = self.cell(lat, lon)
        if self.sea[j, i]:
            return j, i
        h, w = self.sea.shape
        for r in range(1, maxr + 1):
            best, bd = None, 1e18
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if max(abs(dy), abs(dx)) != r:
                        continue
                    a, b = j + dy, i + dx
                    if 0 <= a < h and 0 <= b < w and self.sea[a, b]:
                        d = haversine(lat, lon, self.lat[a], self.lon[b])
                        if d < bd:
                            bd, best = d, (a, b)
            if best:
                return best
        return None


def haversine(a: float, b: float, c: float, d: float) -> float:
    R, r = 6371.0, math.pi / 180
    dp, dl = (c - a) * r, (d - b) * r
    q = (math.sin(dp / 2) ** 2
         + math.cos(a * r) * math.cos(c * r) * math.sin(dl / 2) ** 2)
    return 2 * R * math.asin(min(1.0, math.sqrt(q)))


NB = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))


def astar(m: Mask, s: tuple[int, int], g: tuple[int, int]):
    h, w = m.sea.shape
    gy, gx = g

    def est(j, i):
        return haversine(m.lat[j], m.lon[i], m.lat[gy], m.lon[gx])

    dist = {s: 0.0}
    prev: dict = {}
    pq = [(est(*s), s)]
    seen = set()
    while pq:
        _, cur = heapq.heappop(pq)
        if cur in seen:
            continue
        seen.add(cur)
        if cur == g:
            break
        j, i = cur
        for dy, dx in NB:
            a, b = j + dy, i + dx
            if not (0 <= a < h and 0 <= b < w) or not m.sea[a, b]:
                continue
            step = haversine(m.lat[j], m.lon[i], m.lat[a], m.lon[b])
            room = m.coast[a, b] / COAST_CELLS
            d = dist[cur] + step * (1.0 + COAST_PENALTY * (1.0 - room))
            if d < dist.get((a, b), 1e18):
                dist[(a, b)] = d
                prev[(a, b)] = cur
                heapq.heappush(pq, (d + est(a, b), (a, b)))
    if g not in dist and g != s:
        return None
    out = [g]
    while out[-1] != s:
        out.append(prev[out[-1]])
    return [(float(m.lat[j]), float(m.lon[i])) for j, i in reversed(out)]


def crosses_land(m: "Mask", a, b, step_km: float = 8.0) -> bool:
    """Whether the straight chord from a to b passes over land."""
    d = haversine(a[0], a[1], b[0], b[1])
    n = max(2, int(d / step_km))
    for k in range(1, n):
        f = k / n
        j, i = m.cell(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        if not m.sea[j, i]:
            return True
    return False


def simplify(m: "Mask", pts: list[tuple[float, float]],
             tol: float) -> list[list[float]]:
    """Douglas-Peucker, but a chord is only accepted if the sea allows it.

    Plain Douglas-Peucker at a 24 km tolerance put the routes back on land:
    a chord within tolerance of the path can still cut straight across a
    headland, and the Oslofjord approach came out with 100 km of Norway on it.
    Testing each candidate chord against the mask costs a little more geometry
    and removes the whole class of error.
    """
    if len(pts) < 3:
        return [[round(a, 3), round(b, 3)] for a, b in pts]
    k = math.cos(math.radians(sum(p[0] for p in pts) / len(pts)))

    def rdp(seq):
        if len(seq) < 3:
            return seq
        a, b = seq[0], seq[-1]
        ax, ay = a[1] * k, a[0]
        bx, by = b[1] * k, b[0]
        dx, dy = bx - ax, by - ay
        n = math.hypot(dx, dy) or 1e-9
        worst, wi = -1.0, 0
        for idx in range(1, len(seq) - 1):
            px, py = seq[idx][1] * k, seq[idx][0]
            d = abs(dx * (ay - py) - (ax - px) * dy) / n
            if d > worst:
                worst, wi = d, idx
        if worst <= tol and not crosses_land(m, a, b):
            return [a, b]
        return rdp(seq[:wi + 1])[:-1] + rdp(seq[wi:])

    sys.setrecursionlimit(10000)
    return [[round(a, 3), round(b, 3)] for a, b in rdp(pts)]


def route(m: Mask, waypoints: list[tuple[float, float]], label: str):
    """Sea path through a list of waypoints, ending exactly at the last one."""
    legs: list[tuple[float, float]] = []
    anchors = [m.nearest_ocean(*w) for w in waypoints]
    if any(a is None for a in anchors):
        raise SystemExit(f"{label}: a waypoint is nowhere near the ocean")
    for a, b in zip(anchors, anchors[1:]):
        seg = astar(m, a, b)
        if seg is None:
            raise SystemExit(f"{label}: no sea path between waypoints")
        legs.extend(seg if not legs else seg[1:])
    out = simplify(m, legs, SIMPLIFY_DEG)
    # The mouth itself is inland of the last ocean cell by a few kilometres.
    # Ending on it is right: that last hop is the estuary.
    end = [round(waypoints[-1][0], 3), round(waypoints[-1][1], 3)]
    if out[-1] != end:
        out.append(end)
    start = [round(waypoints[0][0], 3), round(waypoints[0][1], 3)]
    if out[0] != start:
        out.insert(0, start)
    return out


def scan_land(m: Mask, pts, step_km: float = 20.0):
    """How much of a polyline is over land, and its worst unbroken run."""
    hits = tot = 0
    runs: list[int] = []
    run = 0
    for a, b in zip(pts, pts[1:]):
        d = haversine(a[0], a[1], b[0], b[1])
        n = max(2, int(d / step_km))
        for k in range(n):
            f = k / n
            la = a[0] + (b[0] - a[0]) * f
            lo = a[1] + (b[1] - a[1]) * f
            j, i = m.cell(la, lo)
            tot += 1
            if not m.sea[j, i]:
                hits += 1
                run += 1
            else:
                if run:
                    runs.append(run)
                run = 0
    if run:
        runs.append(run)
    return hits, tot, (max(runs) * step_km if runs else 0.0)


def load_mask(cache: Path) -> Mask:
    n = 1 << ZOOM
    x0 = int(tile_x(WINDOW["lon0"], n))
    x1 = int(tile_x(WINDOW["lon1"], n))
    y0 = int(tile_y(WINDOW["lat1"], n))
    y1 = int(tile_y(WINDOW["lat0"], n))
    h, w = (y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256
    elev = np.zeros((h, w), np.float32)
    total = (x1 - x0 + 1) * (y1 - y0 + 1)
    print(f"  {total} terrarium tiles at z{ZOOM}")
    for i, x in enumerate(range(x0, x1 + 1)):
        for j, y in enumerate(range(y0, y1 + 1)):
            a = np.asarray(Image.open(io.BytesIO(
                fetch(TILES.format(z=ZOOM, x=x, y=y), cache))).convert("RGB"),
                np.float32)
            elev[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = (
                a[:, :, 0] * 256 + a[:, :, 1] + a[:, :, 2] / 256 - 32768)
    return Mask(elev, x0, y0, ZOOM)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", default=".tilecache/eel-routes")
    ap.add_argument("--verify", action="store_true",
                    help="check the committed routes and change nothing")
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_eels import REGIONS, TRUNK_NORTH, TRUNK_SOUTH, BRANCH, AZORES

    # Measured detours, from Righton et al. 2016: Baltic and North Sea eels ran
    # north into the Norwegian Sea before turning west; western Mediterranean
    # eels left through Gibraltar.
    VIA = {"baltic": [(62.0, 0.0)], "northsea": [(62.0, 0.0)],
           "med": [(35.95, -5.6)]}

    print("Loading the land mask")
    m = load_mask(Path(args.cache))

    if args.verify:
        data = json.loads(OUT.read_text())
        worst = 0.0
        bad = 0
        for key, legs in data["routes"].items():
            for name, pts in legs.items():
                hits, tot, run = scan_land(m, pts)
                # The final hop into the mouth is the estuary and is expected
                # to touch land in a 3 km mask.
                if run > 45:
                    bad += 1
                    print(f"  {key}/{name}: {hits}/{tot} on land, "
                          f"worst run {run:.0f} km")
                worst = max(worst, run)
        print(f"verify: {bad} legs with an overland run past the estuary; "
              f"worst run anywhere {worst:.0f} km")
        return 1 if bad else 0

    routes: dict[str, dict[str, list]] = {}
    print("Routing")
    for r in REGIONS:
        trunk = TRUNK_NORTH if BRANCH[r["group"]] == "north" else TRUNK_SOUTH
        approach = route(m, [trunk[-1], r["mouth"]], f"{r['key']}/approach")
        home = route(m, [r["mouth"]] + VIA.get(r["group"], []) + [AZORES],
                     f"{r['key']}/home")
        routes[r["key"]] = {"approach": approach, "home": home}
        ah, at, ar = scan_land(m, approach)
        hh, ht, hr = scan_land(m, home)
        print(f"  {r['key']:<14} approach {len(approach):>3} pts "
              f"(worst land run {ar:>5.0f} km)   "
              f"home {len(home):>3} pts (worst {hr:>5.0f} km)")

    OUT.write_text(json.dumps({
        "note": ("Shortest sea paths over a terrarium land mask at zoom 5, "
                 "flood-filled from the open Atlantic. Generated by "
                 "scripts/route_eels.py; see that file's header."),
        "zoom": ZOOM,
        "coastPenalty": COAST_PENALTY,
        "simplifyDeg": SIMPLIFY_DEG,
        "via": VIA,
        "routes": routes,
    }, indent=1))
    pts = sum(len(v["approach"]) + len(v["home"]) for v in routes.values())
    print(f"-> {OUT}  ({OUT.stat().st_size/1024:.0f} kB, {pts} points)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
