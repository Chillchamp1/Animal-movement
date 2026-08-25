#!/usr/bin/env python3
"""Download the Okavango Delta predator-prey GPS deposit from Dryad.

Source dataset
--------------
Bennitt, E. et al. (2024) "Proactive cursorial and ambush predation risk
avoidance in four African herbivore species", Ecology and Evolution.
Data: https://doi.org/10.5061/dryad.w0vt4b8zr

GPS collar data from impala, tsessebe, wildebeest, zebra, African wild dog
and lion in the Okavango Delta, Botswana, 2014-2016.

Usage
-----
    python3 scripts/fetch_dryad.py
    python3 scripts/fetch_dryad.py --doi 10.5061/dryad.w0vt4b8zr --out data/raw

Requires outbound HTTPS access to datadryad.org. In a sandboxed environment
whose egress policy denies that host, the script exits with a clear message
rather than hanging.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

API_ROOT = "https://datadryad.org/api/v2"
DEFAULT_DOI = "10.5061/dryad.w0vt4b8zr"
USER_AGENT = "okavango-movement-map/1.0 (+https://github.com/Chillchamp1)"


def _get(url: str, accept: str = "application/json") -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def _get_json(url: str) -> dict:
    return json.loads(_get(url).decode("utf-8"))


def latest_version_path(doi: str) -> str:
    """Resolve a DOI to the API path of its most recent version."""
    encoded = urllib.parse.quote(f"doi:{doi}", safe="")
    dataset = _get_json(f"{API_ROOT}/datasets/{encoded}")
    version = dataset.get("_links", {}).get("stash:version", {}).get("href")
    if not version:
        raise SystemExit(f"No version link found for DOI {doi}")
    print(f"  title:   {dataset.get('title', '?')}")
    print(f"  license: {dataset.get('license', '?')}")
    return version


def list_files(version_path: str) -> list[dict]:
    """Return every file record in a dataset version, following pagination."""
    files: list[dict] = []
    url = f"https://datadryad.org{version_path}/files?per_page=100"
    while url:
        page = _get_json(url)
        files.extend(page.get("_embedded", {}).get("stash:files", []))
        nxt = page.get("_links", {}).get("next", {}).get("href")
        url = f"https://datadryad.org{nxt}" if nxt else None
    return files


def download(files: list[dict], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for rec in files:
        name = rec.get("path") or rec.get("filename")
        href = rec.get("_links", {}).get("stash:file-download", {}).get("href")
        if not name or not href:
            print(f"  ! skipping malformed file record: {rec.get('path', rec)}")
            continue
        target = out_dir / Path(name).name
        if target.exists() and target.stat().st_size == rec.get("size", -1):
            print(f"  = {target.name} (already downloaded)")
            written.append(target)
            continue
        print(f"  + {target.name} ({rec.get('size', '?')} bytes)")
        data = _get(f"https://datadryad.org{href}", accept="*/*")
        target.write_bytes(data)
        written.append(target)
    return written


def extract_archives(paths: list[Path], out_dir: Path) -> None:
    """Unpack any zips in place so the CSV/R tree is directly browsable."""
    for path in paths:
        if path.suffix.lower() != ".zip":
            continue
        dest = out_dir / path.stem
        print(f"  unzip {path.name} -> {dest.relative_to(out_dir.parent)}/")
        with zipfile.ZipFile(path) as zf:
            for member in zf.namelist():
                # Guard against path traversal in untrusted archives.
                resolved = (dest / member).resolve()
                if not str(resolved).startswith(str(dest.resolve())):
                    raise SystemExit(f"Unsafe archive member: {member}")
            zf.extractall(dest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doi", default=DEFAULT_DOI, help="Dryad DOI to fetch")
    parser.add_argument("--out", default="data/raw", type=Path, help="output directory")
    args = parser.parse_args()

    print(f"Resolving {args.doi} ...")
    try:
        version = latest_version_path(args.doi)
        files = list_files(version)
    except urllib.error.URLError as exc:
        print(
            f"\nCould not reach datadryad.org: {exc}\n"
            "If this session runs behind an egress proxy, datadryad.org must be "
            "allowed by the network policy before this script can run.",
            file=sys.stderr,
        )
        return 1

    print(f"Found {len(files)} file(s); downloading to {args.out}/")
    written = download(files, args.out)
    extract_archives(written, args.out)
    print(f"\nDone. {len(written)} file(s) in {args.out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
