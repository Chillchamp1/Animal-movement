#!/usr/bin/env python3
"""Reconstruct chronological hourly GPS tracks from the Bennitt et al. (2024) deposit.

Why this is needed
------------------
The Dryad deposit (doi:10.5061/dryad.w0vt4b8zr) ships analysis-ready tables, not
raw collar downloads. Between two of those tables the full trajectory survives:

  RSF/*.csv          real coordinates (UTM 34S, snapped to a 25 m raster grid),
                     used/available flag, predator utilisation index (UI), but
                     STABLY SORTED BY ACTIVITY -- all "High" rows, then all "Low".
  Distances/*.csv    the same fixes in true chronological order, carrying
                     hour-of-day and step length, but no coordinates.

Predator activity is a deterministic function of hour-of-day (dogs crepuscular,
lions nocturnal), so the activity sort is invertible: walk the chronological hour
sequence, and for each hour draw the next point from whichever activity block that
hour belongs to. The two tables use slightly different activity windows, so the
window is solved per file by testing candidates and scoring each reconstruction
against the authors' own step-length column.

A reconstruction is accepted only if it reproduces that column to within the
25 m grid quantisation. On the reference file (impala) the solved window
{4,5,6,7,8,17,18,19} reproduces 100% of steps within 40 m, median error 7.2 m.

Output
------
data/processed/<species>-<season>.json -- chronological tracks in WGS84, split
into gap-free segments, with per-fix dog and lion utilisation indices.

Usage
-----
    python3 scripts/build_tracks.py [--raw data/raw] [--out data/processed]
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import math
import statistics
import sys
from pathlib import Path

try:
    from pyproj import Transformer
except ImportError:
    sys.exit("pyproj is required: pip install pyproj")

# UTM zone 34S -> WGS84. Verified: the study extent lands at 23.3-24.0E, 19.2-19.6S.
TO_WGS84 = Transformer.from_crs("EPSG:32734", "EPSG:4326", always_xy=True)

# Accept a reconstruction only if it reproduces the authors' step lengths to
# within this tolerance. The 25 m raster snap alone contributes up to ~18 m.
TOLERANCE_M = 40.0
MIN_AGREEMENT = 0.95

DATASETS = [
    ("Impala",     "Dry",   "RSF/Impala RSF.csv",          "Distances/Impala dist to pred act.csv"),
    ("Tsessebe",   "Dry",   "RSF/Tsessebe dry RSF.csv",    "Distances/Tsessebe dist to pred act.csv"),
    ("Tsessebe",   "Rainy", "RSF/Tsessebe rainy RSF.csv",  "Distances/Tsessebe dist to pred act.csv"),
    ("Wildebeest", "Dry",   "RSF/Wildebeest dry RSF.csv",  "Distances/Wildebeest dist to pred act.csv"),
    ("Wildebeest", "Rainy", "RSF/Wildebeest rainy RSF.csv","Distances/Wildebeest dist to pred act.csv"),
    ("Zebra",      "Dry",   "RSF/Zebra dry RSF.csv",       "Distances/Zebra dist to pred act.csv"),
    ("Zebra",      "Rainy", "RSF/Zebra rainy RSF.csv",     "Distances/Zebra dist to pred act.csv"),
]


def load_rsf_blocks(path: Path, pred: str):
    """Used points for one predator context, in file order, split by activity."""
    blocks = collections.defaultdict(list)
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r["Used"] == "1" and r["Pred"] == pred:
                blocks[(r["id"], r["Activity"])].append(
                    (float(r["x"]), float(r["y"]), float(r["UI"]))
                )
    return blocks


def load_chronology(path: Path, pred: str, season: str):
    """Chronological (hour, step-length, activity) per individual."""
    seq = collections.defaultdict(list)
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r["Pred"] == pred and r["Season"] == season:
                seq[r["ID"]].append((int(r["Hour"]), float(r["Dist"]), r["PredAct"]))
    return seq


def candidate_windows(chrono):
    """The activity window as labelled in Distances, plus one-hour perturbations."""
    base = {h for rows in chrono.values() for h, _, a in rows if a == "High"}
    low = {h for rows in chrono.values() for h, _, a in rows if a == "Low"}
    base -= low  # drop hours that appear in both (season-boundary ambiguity)
    cands = [base]
    cands += [base | {h} for h in range(24) if h not in base]
    cands += [base - {h} for h in sorted(base)]
    return cands


def exact_match(ind, rows, blocks, window):
    """True when the activity split implied by `window` matches the RSF blocks."""
    want = sum(1 for h, _, _ in rows if h in window)
    return (len(blocks.get((ind, "High"), [])) == want
            and len(blocks.get((ind, "Low"), [])) == len(rows) - want)


def reconstruct(rows, blocks, ind, window):
    """De-interleave one individual's activity blocks into chronological order.

    Walk the chronological hour sequence; each hour names an activity state, so
    take the next unused point from that state's block. Returns the track and
    the fraction of steps reproducing the published length within tolerance.
    """
    ptr, pts = {"High": 0, "Low": 0}, []
    for h, d, _ in rows:
        act = "High" if h in window else "Low"
        queue = blocks.get((ind, act), [])
        if ptr[act] >= len(queue):
            return [], 0.0
        pts.append(queue[ptr[act]] + (h, d))
        ptr[act] += 1

    errs = [
        abs(math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1])
            - pts[k - 1][4])
        for k in range(1, len(pts))
    ]
    if not errs:
        return [], 0.0
    return pts, sum(1 for e in errs if e < TOLERANCE_M) / len(errs)


def solve(chrono, blocks):
    """Choose the activity window, then reconstruct every individual it explains.

    Only individuals whose activity-block sizes the window explains exactly are
    reconstructed; where the two tables disagree on a fix the interleaving cannot
    be verified, so that individual is dropped rather than emitted unchecked.
    """
    best = None
    for window in candidate_windows(chrono):
        tracks, errs = {}, []
        for ind, rows in chrono.items():
            if not exact_match(ind, rows, blocks, window):
                continue
            pts, agree = reconstruct(rows, blocks, ind, window)
            if agree >= MIN_AGREEMENT:
                tracks[ind] = pts
                errs.extend(
                    abs(math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1])
                        - pts[k - 1][4])
                    for k in range(1, len(pts))
                )
        if not errs:
            continue
        agree = sum(1 for e in errs if e < TOLERANCE_M) / len(errs)
        cand = (agree, statistics.median(errs), tracks, sorted(window),
                sorted(set(chrono) - set(tracks)))
        if best is None or (agree, len(tracks)) > (best[0], len(best[2])):
            best = cand
    return best


def segment(points):
    """Split a track wherever the hourly sequence breaks."""
    segs, cur = [], []
    for i, p in enumerate(points):
        if cur and (points[i - 1][3] + 1) % 24 != p[3]:
            segs.append(cur)
            cur = []
        cur.append(p)
    if cur:
        segs.append(cur)
    return segs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--out", type=Path, default=Path("data/processed"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    print(f"{'species/season':22s} {'fixes':>7s} {'ind':>4s} {'segs':>5s} "
          f"{'agree':>7s} {'med err':>8s}  window")
    print("-" * 88)

    summary = []
    for species, season, rsf_rel, dist_rel in DATASETS:
        rsf_path, dist_path = args.raw / rsf_rel, args.raw / dist_rel
        if not rsf_path.exists() or not dist_path.exists():
            print(f"{species+'/'+season:22s} missing input, skipped")
            continue

        dog = solve(load_chronology(dist_path, "Dog", season),
                    load_rsf_blocks(rsf_path, "Dog"))
        lion = solve(load_chronology(dist_path, "Lion", season),
                     load_rsf_blocks(rsf_path, "Lion"))

        if not dog or dog[0] < MIN_AGREEMENT:
            got = f"{dog[0]:.1%}" if dog else "no window"
            print(f"{species+'/'+season:22s} REJECTED (dog agreement {got})")
            continue

        agree, med, tracks, window, rejected = dog
        # Cross-check: the lion-context reconstruction must recover the same
        # geometry from an independently sorted table.
        geom_ok = True
        if lion and lion[0] >= MIN_AGREEMENT:
            for ind, pts in tracks.items():
                other = lion[2].get(ind, [])
                if len(other) != len(pts) or any(
                    a[0] != b[0] or a[1] != b[1] for a, b in zip(pts, other)
                ):
                    geom_ok = False
                    break
        else:
            geom_ok = False

        individuals, n_fix, n_seg = [], 0, 0
        for ind in sorted(tracks):
            pts = tracks[ind]
            lion_ui = {i: p[2] for i, p in enumerate(lion[2].get(ind, []))} if geom_ok else {}
            segs = []
            offset = 0
            for s in segment(pts):
                coords = []
                for j, (x, y, ui, h, d) in enumerate(s):
                    lon, lat = TO_WGS84.transform(x, y)
                    coords.append([round(lon, 5), round(lat, 5),
                                   round(ui, 12), round(lion_ui.get(offset + j, 0.0), 12)])
                segs.append({"startHour": s[0][3], "coords": coords})
                offset += len(s)
            individuals.append({"id": ind, "fixes": len(pts), "segments": segs})
            n_fix += len(pts)
            n_seg += len(segs)

        payload = {
            "species": species,
            "season": season,
            "source": "Bennitt et al. 2024, doi:10.5061/dryad.w0vt4b8zr",
            "reconstruction": {
                "method": "activity-block de-interleaving keyed on hour-of-day",
                "dogHighHours": window,
                "lionHighHours": lion[3] if lion else None,
                "stepAgreementWithin40m": round(agree, 4),
                "medianStepErrorM": round(med, 2),
                "lionGeometryCrossCheck": geom_ok,
                "gridResolutionM": 25,
            },
            "individuals": individuals,
        }
        out = args.out / f"{species.lower()}-{season.lower()}.json"
        out.write_text(json.dumps(payload, separators=(",", ":")))

        notes = []
        if rejected:
            notes.append(f"dropped {','.join(sorted(rejected))}")
        if not geom_ok:
            notes.append("lion cross-check FAILED")
        print(f"{species+'/'+season:22s} {n_fix:7d} {len(individuals):4d} {n_seg:5d} "
              f"{agree:6.1%} {med:7.1f}m  {window}"
              f"{'   [' + '; '.join(notes) + ']' if notes else ''}")
        summary.append((species, season, n_fix, len(individuals), n_seg, agree))

    if summary:
        print("-" * 88)
        print(f"{'TOTAL':22s} {sum(s[2] for s in summary):7d} fixes, "
              f"{sum(s[4] for s in summary)} segments across {len(summary)} species-seasons")
        print(f"\nWritten to {args.out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
