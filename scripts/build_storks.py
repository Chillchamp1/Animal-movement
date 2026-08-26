#!/usr/bin/env python3
"""Turn the white stork deposits into the map's track files.

Source
------
Flack, A. et al. (2016) "Costs of migratory decisions: a comparison across
eight white stork populations", Science Advances 2:e1500931.
Data: doi:10.5441/001/1.78152p3q, Movebank Data Repository, CC0.

Fetch it first, skipping the accelerometer files nothing here reads:

    python3 scripts/fetch_movebank.py --doi 10.5441/001/1.78152p3q \
        --match gps reference-data README --out data/raw/storks

What this does
--------------
Nothing has to be reconstructed -- every row carries a coordinate pair and a
timestamp. The work is thinning and shaping.

* Thin from the collars' five-minute schedule to hourly. A storkonmigration
  covers 40-60 km/h, so an hour is a legible step at continental scale and a
  twelfth of the data.
* Break a track wherever the tag was silent; nothing is interpolated across.
* Start at the point where the deposit becomes a study rather than one bird.
  Every tag but one goes on in June or July 2013, when that year's chicks were
  ringed at the nest; the months before are a single South African stork, and
  they were 38% of the timeline. August is the further cut: the birds spend
  June and July around the nest, and autumn migration is what the map is for.
* Drop the Uzbek birds. They are Ciconia ciconia asiatica of the Ferghana
  Valley and they do not migrate -- six birds, a median range of 148 km and
  never south of 40 N across up to 365 days each. That is a real finding, and
  it is also six dots that never move on a map about movement.
* Carry each bird's population and, for the 30 that did not survive the study,
  the slot its tag stopped -- the map should be able to say that a track ended
  rather than merely leaving the frame.

Usage
-----
    python3 scripts/build_storks.py
    python3 scripts/build_storks.py --step-min 60 --out data/processed
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SCALE = 100_000          # 1e-5 degrees, ~1 m; far below tag error

DEFAULT_FROM = "2013-08-01"
DEFAULT_EXCLUDE = ("Uzbekistan",)
# These are solar tags: they report through the day and fall silent overnight,
# so a rule of "consecutive hours only" empties the map every night -- at 21:00
# UTC not one of the 72 is reporting. A gap is bridged when the bird cannot
# have gone anywhere across it (the straight line implies a speed a roosting
# stork could not beat) and broken when it could, because then the route across
# the gap is genuinely unknown.
MAX_GAP_SLOTS = 16       # a long winter night, plus margin
BRIDGE_KMH = 8.0         # below this the bird was on the ground, not travelling

# Storks soar, and soaring needs thermals, which do not form over open water.
# So the Mediterranean is crossed at its narrow ends, and where a bird first
# gets south of this parallel says which of the two great flyways it took.
CROSSING_LAT = 36.0
GIBRALTAR_LON = 0.0      # west of this is the Strait
LEVANT_LON = 20.0        # east of this is the Bosphorus and the Levant


def classify_route(g: pd.DataFrame) -> str:
    """Which way this bird left Europe, from where it first crossed 36 N."""
    south = g[g.lat < CROSSING_LAT]
    if south.empty:
        return "stayed"
    lon = float(south.sort_values("timestamp").lon.iloc[0])
    if lon < GIBRALTAR_LON:
        return "west"
    if lon > LEVANT_LON:
        return "east"
    return "central"


def read_gps(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=["timestamp", "location-long", "location-lat",
                                    "individual-local-identifier"],
                     parse_dates=["timestamp"]).rename(columns={
        "location-long": "lon", "location-lat": "lat",
        "individual-local-identifier": "id"})
    return df.dropna(subset=["lat", "lon"])


def read_reference(path: Path) -> pd.DataFrame:
    ref = pd.read_csv(path)
    ref = ref.rename(columns={"animal-id": "id", "study-site": "population",
                              "deployment-end-type": "end_type",
                              "animal-life-stage": "life_stage"})
    keep = [c for c in ("id", "population", "end_type", "life_stage") if c in ref]
    return ref[keep].drop_duplicates(subset=["id"])


def bridgeable(dslot: np.ndarray, lon: np.ndarray, lat: np.ndarray,
               step_h: float) -> np.ndarray:
    """True where a gap may be drawn across: short, and slow enough to be sleep."""
    km = np.hypot(np.diff(lon) * np.cos(np.radians(lat[1:])) * 111.32,
                  np.diff(lat) * 110.574)
    hours = dslot * step_h
    with np.errstate(divide="ignore", invalid="ignore"):
        kmh = np.where(hours > 0, km / hours, np.inf)
    # A consecutive hour is an observation and always connects, however fast the
    # bird was going -- that is the migration. The speed test applies only to
    # gaps, where the question is whether anything could have happened inside
    # one, and a bird that has not moved cannot have gone anywhere.
    return (dslot == 1) | ((dslot <= MAX_GAP_SLOTS) & (kmh < BRIDGE_KMH))


def build_individuals(df: pd.DataFrame, meta: pd.DataFrame, step_h: float) -> list[dict]:
    lookup = meta.set_index("id").to_dict("index")
    lon0 = df.lon.min()
    lat0 = df.lat.min()
    out = []
    for bird, g in df.groupby("id", sort=True):
        g = g.sort_values("slot")
        slot = g.slot.to_numpy()
        xi = np.rint((g.lon.to_numpy() - lon0) * SCALE).astype(int)
        yi = np.rint((g.lat.to_numpy() - lat0) * SCALE).astype(int)

        dslot = np.diff(slot)
        ok = bridgeable(dslot, g.lon.to_numpy(), g.lat.to_numpy(), step_h)
        cuts = np.flatnonzero(~ok) + 1
        segments = []
        for part in np.split(np.arange(len(slot)), cuts):
            if len(part) < 2:
                continue
            s, x, y = slot[part], xi[part], yi[part]
            segments.append({"t": int(s[0]),
                             "ds": np.diff(s).tolist(),   # hours advanced per step
                             "x": [int(x[0])] + np.diff(x).tolist(),
                             "y": [int(y[0])] + np.diff(y).tolist()})
        if not segments:
            continue
        info = lookup.get(bird, {})
        rec = {"id": str(bird),
               "pop": str(info.get("population", "unknown")),
               "route": classify_route(g),
               "segments": segments}
        # A tag that stopped because the bird died is a fact about the bird, not
        # a gap in coverage; the map draws that ending differently.
        if str(info.get("end_type", "")).lower() == "dead":
            rec["died"] = int(slot[-1])
        out.append(rec)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw/storks", type=Path)
    ap.add_argument("--out", default="data/processed", type=Path)
    ap.add_argument("--step-min", type=int, default=60, help="thinning interval in minutes")
    ap.add_argument("--from-date", default=DEFAULT_FROM,
                    help="drop everything before this date; '' keeps the lot")
    ap.add_argument("--exclude", nargs="*", default=list(DEFAULT_EXCLUDE),
                    help="populations to leave out")
    args = ap.parse_args()

    gps = next(args.raw.glob("*-gps.csv"), None)
    ref = next(args.raw.glob("*-reference-data.csv"), None)
    if not gps or not ref:
        raise SystemExit(
            f"missing the gps or reference-data csv in {args.raw}\n"
            "  run: python3 scripts/fetch_movebank.py --doi 10.5441/001/1.78152p3q "
            "--match gps reference-data README --out data/raw/storks")

    print(f"reading {gps.name} ...")
    df = read_gps(gps)
    meta = read_reference(ref)
    print(f"  {len(df):,} fixes, {df.id.nunique()} birds")

    if args.exclude:
        drop = set(meta[meta.population.isin(args.exclude)].id)
        before = df.id.nunique()
        df = df[~df.id.isin(drop)]
        print(f"  excluding {', '.join(args.exclude)}: "
              f"-{before - df.id.nunique()} birds, {len(df):,} fixes left")
    if args.from_date:
        before = df.id.nunique()
        df = df[df.timestamp >= pd.Timestamp(args.from_date)]
        gone = before - df.id.nunique()
        print(f"  from {args.from_date}: {len(df):,} fixes left"
              + (f", {gone} bird(s) had nothing after it" if gone else ""))

    epoch = df.timestamp.min().floor("h")
    minutes = (df.timestamp - epoch).dt.total_seconds() / 60
    df = df.assign(slot=np.floor(minutes / args.step_min + 0.5).astype(int))
    df = (df.sort_values(["id", "slot", "timestamp"])
            .drop_duplicates(subset=["id", "slot"], keep="first"))
    print(f"  thinned to {args.step_min} min: {len(df):,} fixes")

    individuals = build_individuals(df, meta, args.step_min / 60)
    kept = {i["id"] for i in individuals}
    pops = (df[df.id.astype(str).isin(kept)].merge(meta, on="id", how="left")
              .groupby("population").agg(birds=("id", "nunique"), fixes=("id", "size")))

    payload = {
        "source": "Flack et al. 2016, doi:10.5441/001/1.78152p3q (CC0)",
        "window": {"from": args.from_date or None, "excluded": list(args.exclude)},
        "epoch": epoch.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stepMinutes": args.step_min,
        "slots": int(df.slot.max()) + 1,
        "scale": SCALE,
        "origin": {"lon": float(df.lon.min()), "lat": float(df.lat.min())},
        "bounds": {"lon0": float(df.lon.min()), "lat0": float(df.lat.min()),
                   "lon1": float(df.lon.max()), "lat1": float(df.lat.max())},
        "counts": {p: {"birds": int(r.birds), "fixes": int(r.fixes)}
                   for p, r in pops.iterrows()},
        "died": sum(1 for i in individuals if "died" in i),
        "routes": {r: sum(1 for i in individuals if i["route"] == r)
                   for r in ("west", "central", "east", "stayed")},
        "individuals": individuals,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / "storks.json"
    target.write_text(json.dumps(payload, separators=(",", ":")))

    segs = sum(len(i["segments"]) for i in individuals)
    print(f"\n{len(individuals)} birds, {payload['slots']:,} hourly slots, "
          f"{segs:,} segments, {payload['died']} tags ended in death")
    for p, r in pops.iterrows():
        print(f"   {p:<14} {int(r.birds):>3} birds  {int(r.fixes):>7,} fixes")
    print("\nhow they left Europe:")
    for route, count in payload["routes"].items():
        print(f"   {route:<9} {count:>3} birds")
    print(f"\nbounds lon {payload['bounds']['lon0']:.2f}..{payload['bounds']['lon1']:.2f}  "
          f"lat {payload['bounds']['lat0']:.2f}..{payload['bounds']['lat1']:.2f}")
    print(f"wrote {target} ({target.stat().st_size/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
