#!/usr/bin/env python3
"""Fold index.html and its data into one self-contained page.

The served page fetches data/processed/*.json at runtime, which needs a web
server. This build inlines the same JSON as `window.__STORK_DATA__` so the
result is a single file that runs anywhere, including hosts that permit no
outbound requests at all.

Usage
-----
    python3 scripts/build_standalone.py [--out dist/cougars-and-their-prey.html]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# The tracks are already delta-encoded integers by scripts/build_utah.py, so
# there is nothing left to rescale here -- the files go in as they are.
DATASETS = ["storks"]
LAYERS = ["basemap"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", type=Path, default=Path("index.html"))
    ap.add_argument("--data", type=Path, default=Path("data/processed"))
    ap.add_argument("--out", type=Path,
                    default=Path("dist/where-the-storks-went.html"))
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
        payload = json.loads(path.read_text())
        total_fixes += sum(len(seg["x"]) for ind in payload["individuals"]
                           for seg in ind["segments"])
        bundle[name] = payload
    for name in LAYERS:
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
        f"<script>window.__STORK_DATA__={data_js};</script>\n"
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
