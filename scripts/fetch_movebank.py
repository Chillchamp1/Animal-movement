#!/usr/bin/env python3
"""Download published deposits from the Movebank Data Repository.

Unlike the Dryad deposits audited in docs/dataset-audit.md, these carry the
collar download itself: one row per fix, with `location-long`, `location-lat`
and `timestamp`. See docs/dataset-audit.md for why that distinction decided
the search.

The repository runs DSpace 7, whose REST API is open -- no account, no licence
click-through -- so a deposit is addressed by its DOI and its files come back
by bitstream id.

Usage
-----
    python3 scripts/fetch_movebank.py --doi 10.5441/001/1.712
    python3 scripts/fetch_movebank.py --list-only --doi 10.5441/001/1.711
    python3 scripts/fetch_movebank.py --search "predator prey"

    # Bird deposits ship accelerometer files many times the size of the GPS
    # ones. Nothing here reads acceleration, so skip it.
    python3 scripts/fetch_movebank.py --doi 10.5441/001/1.78152p3q \
        --match gps reference-data README
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

API = "https://datarepository.movebank.org/server/api"
# DSpace answers a default urllib user agent with a connection reset.
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"


def _get(url: str, accept: str = "application/json", retries: int = 5) -> bytes:
    """DSpace resets the connection under load; back off rather than give up."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=900) as resp:
                return resp.read()
        except (urllib.error.URLError, ConnectionResetError, TimeoutError) as exc:
            if attempt == retries - 1:
                raise
            print(f"    retry {attempt + 1}: {type(exc).__name__}", file=sys.stderr)
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def _get_json(path: str, **params) -> dict:
    return json.loads(_get(f"{API}/{path}?{urllib.parse.urlencode(params)}").decode("utf-8"))


def _meta(item: dict, key: str) -> str:
    return " | ".join(v["value"] for v in item.get("metadata", {}).get(key, []))


def search(query: str, size: int = 20) -> list[dict]:
    page = _get_json("discover/search/objects", query=query, size=size, dsoType="item")
    return [o["_embedded"]["indexableObject"]
            for o in page["_embedded"]["searchResult"]["_embedded"]["objects"]]


def find_by_doi(doi: str) -> dict:
    """Resolve a deposit DOI to its item record. Search is fuzzy, so confirm the hit."""
    for item in search(f'"{doi}"', size=10):
        if doi in _meta(item, "dc.identifier.doi"):
            return item
    raise SystemExit(f"No deposit found for DOI {doi}")


def list_files(item: dict) -> list[dict]:
    files = []
    for bundle in _get_json(f"core/items/{item['uuid']}/bundles")["_embedded"]["bundles"]:
        if bundle["name"] != "ORIGINAL":  # skip LICENSE and derived TEXT bundles
            continue
        files.extend(_get_json(f"core/bundles/{bundle['uuid']}/bitstreams")["_embedded"]["bitstreams"])
    return files


def describe(item: dict) -> None:
    print(f"  title:   {_meta(item, 'dc.title')}")
    print(f"  taxon:   {_meta(item, 'dwc.ScientificName')}")
    print(f"  licence: {_meta(item, 'dc.rights')}")
    print(f"  size:    {_meta(item, 'mdr.animal.count')} animals, "
          f"{_meta(item, 'mdr.location.count')} locations")


def download(files: list[dict], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for rec in files:
        target = out_dir / rec["name"]
        if target.exists() and target.stat().st_size == rec["sizeBytes"]:
            print(f"  = {target.name} (already downloaded)")
            written.append(target)
            continue
        print(f"  + {target.name} ({rec['sizeBytes']:,} bytes)")
        target.write_bytes(_get(f"{API}/core/bitstreams/{rec['uuid']}/content", accept="*/*"))
        written.append(target)
    return written


def extract_archives(paths: list[Path], out_dir: Path) -> None:
    for path in paths:
        if path.suffix.lower() != ".zip":
            continue
        print(f"  unzip {path.name}")
        with zipfile.ZipFile(path) as zf:
            for member in zf.namelist():
                if member.startswith("__MACOSX/"):  # archive metadata, not data
                    continue
                resolved = (out_dir / member).resolve()
                if not str(resolved).startswith(str(out_dir.resolve())):
                    raise SystemExit(f"Unsafe archive member: {member}")
                zf.extract(member, out_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--doi", help="deposit DOI, e.g. 10.5441/001/1.712")
    parser.add_argument("--search", help="free-text search over the repository")
    parser.add_argument("--list-only", action="store_true", help="describe the deposit, download nothing")
    parser.add_argument("--match", nargs="+", metavar="SUBSTR",
                        help="only fetch files whose name contains one of these")
    parser.add_argument("--out", default="data/raw/movebank", type=Path, help="output directory")
    args = parser.parse_args()

    if args.search:
        for item in search(args.search):
            print()
            describe(item)
            print(f"  doi:     {_meta(item, 'dc.identifier.doi')}")
        return 0

    if not args.doi:
        parser.error("pass --doi or --search")

    print(f"Resolving {args.doi} ...")
    item = find_by_doi(args.doi)
    describe(item)
    files = list_files(item)
    if args.match:
        keep = [f for f in files if any(m.lower() in f["name"].lower() for m in args.match)]
        skipped = sum(f["sizeBytes"] for f in files) - sum(f["sizeBytes"] for f in keep)
        print(f"  --match kept {len(keep)} of {len(files)} file(s), "
              f"skipping {skipped / 1e6:.0f} MB")
        files = keep
    if args.list_only:
        for rec in files:
            print(f"  {rec['sizeBytes']:>14,} B  {rec['name']}")
        return 0

    print(f"\nDownloading {len(files)} file(s) to {args.out}/")
    extract_archives(download(files, args.out), args.out)
    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
