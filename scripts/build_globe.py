#!/usr/bin/env python3
"""Pick one real journey per species for the 3D globe.

Sources
-------
Both are Movebank Data Repository deposits, CC0, one row per fix.

* Senner, N. R. et al. "Compensation for wind drift prevails for a shorebird on
  a long-distance, transoceanic flight." doi:10.5441/001/1.t81488n5
  -- Hudsonian godwits (Limosa haemastica), 25 birds, Alaska and Canada to
  southern South America.

* Torres, L. G. et al. "Classification of animal movement behavior through
  residence in space and time." doi:10.5441/001/1.694p666h
  -- grey-headed albatrosses (Thalassarche chrysostoma) from Campbell Island,
  New Zealand, 24 birds at a five-minute fix interval.

Why not the two birds the brief named
-------------------------------------
Neither is available as open data:

* The bar-tailed godwit "4BBRW" flew Alaska to New Zealand nonstop, and its
  satellite data is not in any open repository. The only bar-tailed godwit
  deposit in the archive, doi:10.5441/001/1.327, is geolocator work: 18 birds
  and 103 fixes in total, a median of six per bird, carrying explicit
  lat-lower/lat-upper error columns because that is what geolocators give. An
  eleven-day flight would be two or three points, each uncertain by a hundred
  kilometres or more. It cannot be animated and it is not offered here.

* Wandering albatross (Diomedea exulans) returns nothing at all. The
  Procellariiform tracking data lives in BirdLife International's Seabird
  Tracking Database, which releases data per request and per owner, not by
  open download.

The two deposits above are the same phenomena in real, downloadable data: a
godwit crossing open ocean, and an albatross looping the Southern Ocean. The
page says which species it is showing and why.

What this does
--------------
Neither deposit is clean, and one is quietly dirty:

* 173 of 3,548 godwit GPS rows -- 4.9% -- carry impossible coordinates, such as
  latitude -213. They are almost all unflagged: `manually-marked-outlier` is
  empty for 171 of them, and the tag calls 158 of them good 3D fixes. So they
  have to be caught on the coordinate range itself, never on the quality flag.
* Inside the valid range there are further errors that a range test cannot see.
  A forward pass anchored on the last accepted fix drops any position that
  could only be reached faster than the bird can fly.
* Even then, a four-day gap spans thousands of kilometres at a plausible
  average speed. Distance is therefore only ever summed inside a segment, and
  a segment ends wherever the tag went quiet for longer than MAX_GAP_H.

What comes out is the single longest continuous journey per species -- for the
albatross a complete foraging trip that returns to the colony, for the godwit a
spring migration leg over the Pacific.

Usage
-----
    python3 scripts/fetch_movebank.py --doi 10.5441/001/1.t81488n5 \
        --match gps reference-data README --out data/raw/godwit-hud
    python3 scripts/fetch_movebank.py --doi 10.5441/001/1.694p666h \
        --match Torres README --out data/raw/albatross
    python3 scripts/build_globe.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

R_KM = 6371.0088

SPECIES = {
    "godwit": {
        "label": "Hudsonian godwit",
        "scientific": "Limosa haemastica",
        "raw": "data/raw/godwit-hud",
        "glob": "*-gps.csv",
        "source": "Senner et al., doi:10.5441/001/1.t81488n5 (CC0)",
        "study": "Compensation for wind drift prevails for a shorebird on a "
                 "long-distance, transoceanic flight",
        # A godwit cruises at 60-80 km/h and can exceed 100 with a tailwind.
        "vmax_kmh": 120.0,
        "max_gap_h": 12.0,
        "min_fixes": 40,
        "companion_step_min": 20,
        "note": "A spring migration leg up the Pacific. The bar-tailed godwit "
                "of the record Alaska-New Zealand flight is not open data; "
                "this is the same journey in a species that is.",
    },
    "albatross": {
        "label": "Grey-headed albatross",
        "scientific": "Thalassarche chrysostoma",
        "raw": "data/raw/albatross",
        "glob": "*Torres*.csv",
        "source": "Torres et al., doi:10.5441/001/1.694p666h (CC0)",
        "study": "Classification of animal movement behavior through residence "
                 "in space and time",
        # Albatrosses ride the wind; 150 km/h between five-minute fixes is
        # generous rather than tight, which is what an outlier cut should be.
        "vmax_kmh": 150.0,
        "max_gap_h": 6.0,
        "min_fixes": 200,
        "companion_step_min": 25,
        "note": "One foraging trip from Campbell Island and back. Not the "
                "wandering albatross, whose tracking data is not open; this is "
                "its neighbour over the same ocean.",
    },
}


def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = (np.sin((p2 - p1) / 2) ** 2
         + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2)
    return 2 * R_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def speed_filter(lat, lon, t, vmax):
    """Drop fixes that could only be reached faster than the animal can fly.

    Anchored on the last *accepted* fix rather than the previous row, so one
    bad position does not disqualify the good one after it.
    """
    keep = np.zeros(len(lat), bool)
    keep[0] = True
    anchor = 0
    for i in range(1, len(lat)):
        hours = (t[i] - t[anchor]) / np.timedelta64(1, "h")
        if hours <= 0:
            continue
        if haversine(lat[anchor], lon[anchor], lat[i], lon[i]) / hours <= vmax:
            keep[i] = True
            anchor = i
    return keep


def find_fix_file(raw: Path, pattern: str) -> Path:
    """The deposit's fix table, not its reference table.

    Both are CSVs sitting in the same directory and a loose glob will happily
    hand back the wrong one, so the column that matters decides: a fix table
    has a timestamp, a reference table has one row per animal and does not.
    """
    for path in sorted(raw.glob(pattern)):
        if "reference-data" in path.name:
            continue
        head = pd.read_csv(path, nrows=1, low_memory=False)
        if "timestamp" in head.columns:
            return path
    raise SystemExit(f"no fix table matching {pattern} in {raw}\n"
                     "  see the fetch commands in this script's docstring")


def read_fixes(cfg: dict) -> pd.DataFrame:
    path = find_fix_file(Path(cfg["raw"]), cfg["glob"])
    df = pd.read_csv(path, low_memory=False)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.rename(columns={"location-long": "lon", "location-lat": "lat",
                            "individual-local-identifier": "id"})
    n0 = len(df)
    df = df.dropna(subset=["lat", "lon", "timestamp"])

    # The range test comes first and does not consult the quality flag, because
    # in this deposit the quality flag does not know.
    ok = (df.lat.abs() <= 90) & (df.lon.abs() <= 180)
    n_bad = int((~ok).sum())
    df = df[ok]
    if "manually-marked-outlier" in df:
        df = df[df["manually-marked-outlier"] != True]  # noqa: E712

    print(f"  {path.name}")
    print(f"    {n0:,} rows -> {len(df):,} usable"
          + (f"; {n_bad} had impossible coordinates" if n_bad else ""))
    return df.sort_values(["id", "timestamp"])


def best_journey(df: pd.DataFrame, cfg: dict) -> dict:
    """The longest run of fixes with no silence longer than max_gap_h."""
    best = None
    dropped = 0
    for bird, g in df.groupby("id"):
        lat, lon = g.lat.to_numpy(), g.lon.to_numpy()
        t = g.timestamp.to_numpy()
        keep = speed_filter(lat, lon, t, cfg["vmax_kmh"])
        dropped += int((~keep).sum())
        lat, lon, t = lat[keep], lon[keep], t[keep]
        if len(lat) < 2:
            continue
        hours = np.diff(t) / np.timedelta64(1, "h")
        for part in np.split(np.arange(len(lat)),
                             np.flatnonzero(hours > cfg["max_gap_h"]) + 1):
            if len(part) < cfg["min_fixes"]:
                continue
            a, o, ts = lat[part], lon[part], t[part]
            km = float(haversine(a[:-1], o[:-1], a[1:], o[1:]).sum())
            if best is None or km > best["km"]:
                best = {"id": str(bird), "lat": a, "lon": o, "t": ts, "km": km}
    if best is None:
        raise SystemExit("no segment met the minimum length")
    print(f"    speed filter dropped {dropped:,} fixes above "
          f"{cfg['vmax_kmh']:.0f} km/h")
    return best


def companions(df: pd.DataFrame, cfg: dict, seg: dict) -> list[dict]:
    """The rest of the deposit, over the focal bird's own window.

    On the real clock, not a shared start: these birds did not set off
    together, and pretending they did would be the one dishonest thing this
    page could do. A companion appears when its tag was reporting and vanishes
    when it was not, which is why several are absent for stretches.

    Sampled coarser than the focal bird -- the page draws them as short tails
    rather than full histories, so five-minute detail would be paid for and
    never seen.
    """
    t0, t1 = seg["t"][0], seg["t"][-1]
    step = np.timedelta64(int(cfg["companion_step_min"]), "m")
    out = []
    for bird, g in df.groupby("id"):
        if str(bird) == seg["id"]:
            continue
        lat, lon = g.lat.to_numpy(), g.lon.to_numpy()
        t = g.timestamp.to_numpy()
        keep = speed_filter(lat, lon, t, cfg["vmax_kmh"])
        lat, lon, t = lat[keep], lon[keep], t[keep]
        inwin = (t >= t0) & (t <= t1)
        if inwin.sum() < 8:
            continue
        lat, lon, t = lat[inwin], lon[inwin], t[inwin]

        # Thin by time rather than by index, so a burst of fixes does not buy
        # more resolution than a quiet stretch.
        pick = [0]
        for i in range(1, len(t)):
            if t[i] - t[pick[-1]] >= step:
                pick.append(i)
        pick = np.array(pick)
        lat, lon, t = lat[pick], lon[pick], t[pick]
        minutes = ((t - t0) / np.timedelta64(1, "m")).astype(float)
        lon_u = np.degrees(np.unwrap(np.radians(lon)))
        out.append({
            "id": str(bird),
            "lat": [round(float(v), 4) for v in lat],
            "lon": [round(float(v), 4) for v in lon_u],
            "min": [round(float(v), 1) for v in minutes],
        })
    out.sort(key=lambda d: -len(d["min"]))
    return out


def companion_tolerance(others: list[dict], cfg: dict) -> float:
    """How long a companion may go unheard before the page stops drawing it.

    Derived from the cadence these tags actually achieved, not from the
    interval asked for: the godwit tags report roughly every two hours, so a
    tolerance guessed from the requested twenty-minute step would have called
    91% of ordinary sampling a silence and left the companions invisible for
    almost the whole flight.
    """
    gaps = np.concatenate([np.diff(o["min"]) for o in others if len(o["min"]) > 1]) \
        if others else np.array([])
    gaps = gaps[gaps > 0]
    if not len(gaps):
        return float(cfg["companion_step_min"] * 3)
    return float(round(max(2.5 * np.median(gaps), cfg["companion_step_min"] * 2), 1))


def payload(key: str, cfg: dict, seg: dict, others: list[dict]) -> dict:
    lat, lon, t = seg["lat"], seg["lon"], seg["t"]
    minutes = ((t - t[0]) / np.timedelta64(1, "m")).astype(float)
    step = np.concatenate([[0.0], haversine(lat[:-1], lon[:-1], lat[1:], lon[1:])])
    cum = np.cumsum(step)
    hours = float(minutes[-1] / 60)

    # Longitude is unwrapped so a track crossing the dateline is a continuous
    # run of numbers. The globe wraps it back; a chart of it would not.
    lon_unwrapped = np.degrees(np.unwrap(np.radians(lon)))

    return {
        "key": key,
        "label": cfg["label"],
        "scientific": cfg["scientific"],
        "individual": seg["id"],
        "source": cfg["source"],
        "study": cfg["study"],
        "note": cfg["note"],
        "start": pd.Timestamp(t[0]).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hours": round(hours, 2),
        "km": round(seg["km"], 1),
        "fixes": int(len(lat)),
        "medianGapMin": round(float(np.median(np.diff(minutes))), 1),
        "returnKm": round(float(haversine(lat[0], lon[0], lat[-1], lon[-1])), 1),
        "bounds": {"lat0": float(lat.min()), "lat1": float(lat.max()),
                   "lon0": float(lon_unwrapped.min()),
                   "lon1": float(lon_unwrapped.max())},
        # lat, lon, minutes since the first fix, kilometres flown so far.
        "lat": [round(float(v), 5) for v in lat],
        "lon": [round(float(v), 5) for v in lon_unwrapped],
        "min": [round(float(v), 1) for v in minutes],
        "cum": [round(float(v), 2) for v in cum],
        "others": others,
        "othersStepMin": cfg["companion_step_min"],
        "othersTolMin": companion_tolerance(others, cfg),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="data/processed", type=Path)
    args = ap.parse_args()

    tracks = {}
    for key, cfg in SPECIES.items():
        print(f"{cfg['label']} ({cfg['scientific']})")
        df = read_fixes(cfg)
        seg = best_journey(df, cfg)
        others = companions(df, cfg, seg)
        p = payload(key, cfg, seg, others)
        tracks[key] = p
        print(f"    chosen: {p['individual']} -- {p['fixes']:,} fixes, "
              f"{p['km']:,.0f} km over {p['hours']/24:.1f} days, "
              f"{p['km']/p['hours']:.1f} km/h mean")
        print(f"    median gap {p['medianGapMin']:.0f} min; ends "
              f"{p['returnKm']:,.0f} km from where it began")
        pts = sum(len(o["min"]) for o in others)
        print(f"    {len(others)} other birds of the deposit were reporting in "
              f"that window, {pts:,} points at {cfg['companion_step_min']} min; "
              f"drawn while heard within {p['othersTolMin']:.0f} min\n")

    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / "globe-tracks.json"
    target.write_text(json.dumps({"tracks": tracks}, separators=(",", ":")))
    print(f"wrote {target} ({target.stat().st_size/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
