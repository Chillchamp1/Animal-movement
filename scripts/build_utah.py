#!/usr/bin/env python3
"""Turn the Utah Movebank deposits into the map's per-season track files.

Source
------
Utah Division of Wildlife Resources, deposited in the Movebank Data Repository
under CC0:

  cougars   doi:10.5441/001/1.712   40 animals,    47,777 fixes
  ungulates doi:10.5441/001/1.711   2,694 animals, 4,916,617 fixes

Fetch both with scripts/fetch_movebank.py before running this.

What this does
--------------
Unlike the Okavango deposit, nothing here has to be reconstructed: every row
already carries a coordinate pair and a timestamp. The work is selection and
shaping.

* Clip to the northern Wasatch / Cache Valley, the block where cougars and
  ungulates actually share ground (see docs/dataset-audit.md).
* Snap fixes to the 2 h schedule the collars were programmed to.
* Split into the two seasons the deposit covers -- January to mid-May of 2019
  and of 2020. There is no data at all between them.
* Break a track wherever the collar was silent; nothing is interpolated across
  a gap.
* Precompute, per fix, the distance to the nearest animal of the other guild
  *at that same hour*. This is what lets the map show a measured distance
  instead of an overlap with a modelled range.

Usage
-----
    python3 scripts/build_utah.py
    python3 scripts/build_utah.py --raw data/raw/movebank --out data/processed
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

# The overlap block, chosen in the audit: 100 x 91 km holding 17 cougars and
# 239 ungulates, with an ungulate in the same 5 km cell on 56% of cougar-days.
REGION = dict(lat0=41.20, lat1=42.10, lon0=-112.35, lon1=-111.25)

# The collars ran on a two-hour schedule; 95% of gaps sit within 10% of it.
STEP_H = 2
# A segment holds consecutive slots only. Any missed fix ends it, so the map
# never draws a line across a silence -- not even a single skipped step.
MAX_GAP_STEPS = 1

SEASONS = {
    "2019": ("2019-01-01", "2019-05-17"),
    "2020": ("2020-01-01", "2020-05-17"),
}

SPECIES = {
    "Puma concolor": "cougar",
    "Cervus elaphus": "elk",
    "Odocoileus hemionus": "muledeer",
}
PREDATORS = {"cougar"}

# Coordinates are stored as integer 1e-5 degree offsets: ~1.1 m north-south,
# ~0.8 m east-west here, well under the collars' own error.
SCALE = 100_000
# Cross-guild distance is stored in one byte, 20 m per unit, 255 = "5.1 km or
# more", which is far enough away to mean nothing on this map.
DIST_UNIT_M = 20
DIST_CAP = 255

M_PER_DEG_LAT = 111_320.0


# fetch_movebank.py saves each file under its name in the deposit; a local copy
# may have been renamed to something easier to type. Accept either.
COUGAR_NAMES = ["GPS tracking of cougars in Utah by UDWR (2019-2020).csv",
                "utah-cougars.csv"]
UNGULATE_NAMES = ["GPS tracking of ungulates in Utah by UDWR (2019-2020).csv",
                  "utah-ungulates.csv"]


def find(raw: Path, names: list[str]) -> Path:
    for name in names:
        if (raw / name).exists():
            return raw / name
    raise SystemExit(
        f"none of {names} found in {raw}\n"
        "  run: python3 scripts/fetch_movebank.py --doi 10.5441/001/1.712\n"
        "       python3 scripts/fetch_movebank.py --doi 10.5441/001/1.711")


def read_deposit(path: Path, forced_species: str | None = None) -> pd.DataFrame:
    cols = ["timestamp", "location-long", "location-lat", "individual-local-identifier"]
    if forced_species is None:
        cols.append("individual-taxon-canonical-name")
    df = pd.read_csv(path, usecols=cols, parse_dates=["timestamp"]).rename(columns={
        "location-long": "lon", "location-lat": "lat",
        "individual-local-identifier": "id",
        "individual-taxon-canonical-name": "taxon",
    })
    if forced_species is not None:
        df["taxon"] = forced_species
    df = df[df.lat.between(REGION["lat0"], REGION["lat1"])
            & df.lon.between(REGION["lon0"], REGION["lon1"])]
    df["sp"] = df.taxon.map(SPECIES)
    return df.dropna(subset=["sp", "lat", "lon"]).drop(columns=["taxon"])


def schedule_phase(df: pd.DataFrame, start: pd.Timestamp) -> int:
    """Which hour of the step the collars actually fire on.

    These collars fire on odd hours -- 07:00, 09:00, 11:00. Measured from a
    midnight epoch every fix lands halfway between two slots, and half of them
    round onto their neighbour. Anchoring the epoch to the schedule's own phase
    puts each fix on an integer slot, so nothing has to be rounded away.
    """
    hours = (df.timestamp - start).dt.total_seconds() / 3600
    return int(np.bincount(np.floor(hours).astype(int) % STEP_H).argmax())


def to_slots(df: pd.DataFrame, epoch: pd.Timestamp) -> pd.DataFrame:
    """Snap to the collar schedule and keep one fix per animal per slot."""
    hours = (df.timestamp - epoch).dt.total_seconds() / 3600
    # floor(x + 0.5), not rint: numpy rounds halves to even, which would merge
    # a 3.5 and a 4.5 into the same slot instead of separating them.
    df = df.assign(slot=np.floor(hours / STEP_H + 0.5).astype(int))
    df = df[df.slot >= 0]
    return (df.sort_values(["id", "slot", "timestamp"])
              .drop_duplicates(subset=["id", "slot"], keep="first"))


def cross_guild_distance(df: pd.DataFrame) -> np.ndarray:
    """Metres to the nearest animal of the other guild in the same slot.

    Prey are measured against cougars and cougars against prey, so the number
    means the same thing from either side: how close the other guild actually
    was, at that hour, in this data. Slots where the other guild has no fix at
    all return the cap -- absence of a collared animal is not evidence of
    absence, and the map says so rather than drawing a ring.
    """
    out = np.full(len(df), DIST_CAP * DIST_UNIT_M, dtype=float)
    is_pred = df.sp.isin(PREDATORS).to_numpy()
    lat = df.lat.to_numpy()
    lon = df.lon.to_numpy()
    m_per_deg_lon = M_PER_DEG_LAT * math.cos(math.radians(float(np.mean(lat))))

    for _, idx in df.groupby("slot", sort=False).indices.items():
        pred = idx[is_pred[idx]]
        prey = idx[~is_pred[idx]]
        if not len(pred) or not len(prey):
            continue
        dx = (lon[prey][:, None] - lon[pred][None, :]) * m_per_deg_lon
        dy = (lat[prey][:, None] - lat[pred][None, :]) * M_PER_DEG_LAT
        d = np.hypot(dx, dy)
        out[prey] = d.min(axis=1)
        out[pred] = d.min(axis=0)
    return out


def build_individuals(df: pd.DataFrame) -> list[dict]:
    """One record per animal: segments of consecutive slots, delta-encoded."""
    lon0, lat0 = REGION["lon0"], REGION["lat0"]
    individuals = []
    for (sp, animal), g in df.groupby(["sp", "id"], sort=True):
        g = g.sort_values("slot")
        slot = g.slot.to_numpy()
        xi = np.rint((g.lon.to_numpy() - lon0) * SCALE).astype(int)
        yi = np.rint((g.lat.to_numpy() - lat0) * SCALE).astype(int)
        di = np.clip(np.rint(g.dist.to_numpy() / DIST_UNIT_M), 0, DIST_CAP).astype(int)

        # A jump of more than MAX_GAP_STEPS slots is a silence, not a step.
        cuts = np.flatnonzero(np.diff(slot) > MAX_GAP_STEPS) + 1
        segments = []
        for part in np.split(np.arange(len(slot)), cuts):
            if len(part) < 2:      # a lone fix draws no movement
                continue
            s, x, y, d = slot[part], xi[part], yi[part], di[part]
            # Slots inside a segment are consecutive, so the start slot is the
            # only one worth storing; positions are delta-encoded from the first.
            segments.append({
                "t": int(s[0]),
                "x": [int(x[0])] + np.diff(x).tolist(),
                "y": [int(y[0])] + np.diff(y).tolist(),
                "d": d.tolist(),
            })
        if segments:
            individuals.append({"id": str(animal), "sp": sp, "segments": segments})
    return individuals


def diel_profile(df: pd.DataFrame, epoch: pd.Timestamp) -> dict:
    """Median step length by hour-of-day, per species -- measured, not assumed.

    In the Okavango map the predator lamps came from activity windows the
    deposit stated. Here the cougars are in the data, so their own movement
    says when they were active.
    """
    df = df.sort_values(["id", "slot"])
    step_m = np.full(len(df), np.nan)
    lat = df.lat.to_numpy(); lon = df.lon.to_numpy(); slot = df.slot.to_numpy()
    same = df.id.to_numpy()[1:] == df.id.to_numpy()[:-1]
    adjacent = (np.diff(slot) == 1) & same
    m_per_deg_lon = M_PER_DEG_LAT * math.cos(math.radians(float(np.mean(lat))))
    step_m[1:][adjacent] = np.hypot(
        np.diff(lon)[adjacent] * m_per_deg_lon, np.diff(lat)[adjacent] * M_PER_DEG_LAT)

    hod = ((epoch + pd.to_timedelta(slot * STEP_H, unit="h")).hour)
    out = {}
    frame = pd.DataFrame({"sp": df.sp.to_numpy(), "hod": hod, "m": step_m}).dropna()
    for sp, g in frame.groupby("sp"):
        med = g.groupby("hod").m.median()
        out[sp] = {int(h): round(float(v), 1) for h, v in med.items()}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw/movebank", type=Path)
    ap.add_argument("--out", default="data/processed", type=Path)
    args = ap.parse_args()

    coug = find(args.raw, COUGAR_NAMES)
    ung = find(args.raw, UNGULATE_NAMES)

    print("reading deposits ...")
    df = pd.concat([read_deposit(coug, "Puma concolor"), read_deposit(ung)],
                   ignore_index=True)
    print(f"  {len(df):,} fixes in region, {df.id.nunique():,} animals")

    args.out.mkdir(parents=True, exist_ok=True)
    index = {"region": REGION, "stepHours": STEP_H, "seasons": {}}

    for season, (start, end) in SEASONS.items():
        window = df[(df.timestamp >= pd.Timestamp(start))
                    & (df.timestamp < pd.Timestamp(end))].copy()
        epoch = pd.Timestamp(start) + pd.Timedelta(hours=schedule_phase(window, pd.Timestamp(start)))
        part = to_slots(window, epoch)
        part["dist"] = cross_guild_distance(part)

        individuals = build_individuals(part)
        kept = {i["id"] for i in individuals}
        counts = (part[part.id.isin(kept)].groupby("sp")
                  .agg(individuals=("id", "nunique"), fixes=("id", "size")))

        payload = {
            "season": season,
            "epoch": epoch.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stepHours": STEP_H,
            "steps": int(part.slot.max()) + 1,
            "scale": SCALE,
            "distUnitM": DIST_UNIT_M,
            "distCap": DIST_CAP,
            "origin": {"lon": REGION["lon0"], "lat": REGION["lat0"]},
            "bounds": REGION,
            "counts": {sp: {"individuals": int(r.individuals), "fixes": int(r.fixes)}
                       for sp, r in counts.iterrows()},
            "diel": diel_profile(part, epoch),
            "individuals": individuals,
        }
        target = args.out / f"tracks-{season}.json"
        target.write_text(json.dumps(payload, separators=(",", ":")))
        index["seasons"][season] = {
            "file": target.name,
            "epoch": payload["epoch"],
            "steps": payload["steps"],
            "counts": payload["counts"],
        }
        print(f"  {season}: {len(individuals):>3} animals, "
              f"{int(counts.fixes.sum()):>7,} fixes, "
              f"{target.stat().st_size / 1e6:5.2f} MB -> {target.name}")
        for sp, r in counts.iterrows():
            print(f"       {sp:<10} {int(r.individuals):>4} animals  {int(r.fixes):>8,} fixes")

    (args.out / "index.json").write_text(json.dumps(index, separators=(",", ":")))
    print(f"\nwrote {args.out}/index.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
