#!/usr/bin/env python3
"""Fold index.html and its data into one self-contained page.

The served page fetches data/processed/*.json at runtime, which needs a web
server. This build inlines the same JSON as `window.__DELTA_DATA__` so the
result is a single file that runs anywhere, including hosts that permit no
outbound requests at all.

The utilisation indices are rescaled to small integers on the way in. The page
only ever compares them against a percentile drawn from the same values, so a
monotonic rescale leaves its behaviour identical while removing the twelve
decimal places from every fix.

Usage
-----
    python3 scripts/build_standalone.py [--out dist/a-day-in-the-delta.html]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DATASETS = [
    "impala-dry", "tsessebe-dry", "tsessebe-rainy",
    "wildebeest-dry", "wildebeest-rainy", "zebra-dry", "zebra-rainy",
]
UI_STEPS = 1000


def rescale(payload: dict) -> dict:
    """Map both utilisation columns onto 0..UI_STEPS."""
    peak_dog = peak_lion = 0.0
    for ind in payload["individuals"]:
        for seg in ind["segments"]:
            for c in seg["coords"]:
                peak_dog = max(peak_dog, c[2])
                peak_lion = max(peak_lion, c[3])
    for ind in payload["individuals"]:
        for seg in ind["segments"]:
            seg["coords"] = [
                [c[0], c[1],
                 round(UI_STEPS * c[2] / peak_dog) if peak_dog else 0,
                 round(UI_STEPS * c[3] / peak_lion) if peak_lion else 0]
                for c in seg["coords"]
            ]
    payload["uiScale"] = {"dogPeak": peak_dog, "lionPeak": peak_lion,
                          "steps": UI_STEPS}
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", type=Path, default=Path("index.html"))
    ap.add_argument("--data", type=Path, default=Path("data/processed"))
    ap.add_argument("--out", type=Path,
                    default=Path("dist/a-day-in-the-delta.html"))
    args = ap.parse_args()

    src = args.page.read_text()

    title = re.search(r"<title>(.*?)</title>", src, re.S).group(1)
    styles = re.search(r"<style>.*?</style>", src, re.S).group(0)
    fonts = "\n".join(re.findall(
        r'<link rel="(?:preconnect|stylesheet)"[^>]*>', src))
    body = re.search(r"<body>(.*?)</body>", src, re.S).group(1)
    body = re.sub(r"<script>.*?</script>", "", body, flags=re.S).strip()
    app = re.search(r"<script>\n?(.*?)</script>\s*</body>", src, re.S).group(1)

    bundle = {}
    total_fixes = 0
    for name in DATASETS:
        path = args.data / f"{name}.json"
        if not path.exists():
            print(f"  missing {path}, skipped")
            continue
        payload = rescale(json.loads(path.read_text()))
        total_fixes += sum(i["fixes"] for i in payload["individuals"])
        bundle[name] = payload
    for name in ("predator-risk", "seasonal-shift"):
        path = args.data / f"{name}.json"
        if path.exists():
            bundle[name] = json.loads(path.read_text())
        else:
            print(f"  missing {path}, the matching layer will be unavailable")

    data_js = json.dumps(bundle, separators=(",", ":"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # The artifact host supplies its own <head>, so this file loses index.html's
    # charset declaration. The page is written in pure ASCII for that reason;
    # the meta is a second line of defence, not the primary one.
    args.out.write_text(
        f'<meta charset="utf-8">\n<title>{title}</title>\n{fonts}\n{styles}\n{body}\n'
        f"<script>window.__DELTA_DATA__={data_js};</script>\n"
        f"<script>\n{app}</script>\n"
    )

    mb = args.out.stat().st_size / 1_048_576
    print(f"{len(bundle)} payloads, {total_fixes:,} fixes")
    print(f"wrote {args.out} ({mb:.2f} MB)")
    if mb > 16:
        print("  WARNING: over the 16 MB artifact limit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
