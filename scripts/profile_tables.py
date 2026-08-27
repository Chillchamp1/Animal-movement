#!/usr/bin/env python3
"""Profile CSV/Excel deposits before anything is built from them.

Companion to scripts/profile_rdata.R. The question a deposit has to answer
first is whether it holds real fixes -- coordinates AND a timestamp, for
predators as well as prey -- or only the analysis tables derived from them.

Usage:
    python3 scripts/profile_tables.py data/raw/4xgxd257z/*.csv
    python3 scripts/profile_tables.py data/raw/63xsj3v81/*.xlsx
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

COORD = re.compile(
    r"^(x|y|lon|long|longitude|lat|latitude|utm[._-]?[xy]|easting|northing|mu\.[xy]"
    r"|coords?\.[xy]\d?|location[._-](lon|long|longitude|lat|latitude)"
    r"|(utm|gps)[._-](easting|northing))$"
)
TIME = re.compile(r"(time|date|timestamp|datetime|fixtime|acquisition|dt)")
IDCOL = re.compile(
    r"^(id|animal|animalid|animal[._-]id|indiv|individual|collar|collar[._-]id|uniqueid|tag)"
)
# A taxon column starts with "individual" too, and naming the species is not identifying
# the animal -- rank the local identifier first and drop taxon columns from the candidates.
ID_PREFERRED = re.compile(r"(local[._-]identifier|animal[._-]?id|individual[._-]id)$")
SPP = re.compile(r"(species|spp|taxa|taxon)")


def matching(cols, pattern) -> list[str]:
    return [c for c in cols if pattern.search(str(c).lower())]


def id_columns(cols) -> list[str]:
    found = [c for c in matching(cols, IDCOL) if not SPP.search(str(c).lower())]
    return sorted(found, key=lambda c: not ID_PREFERRED.search(str(c).lower()))


def as_time(series: pd.Series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    parsed = pd.to_datetime(series, errors="coerce", format="mixed")
    return parsed if parsed.notna().mean() > 0.5 else None


def fix_interval(times: pd.Series, ids: pd.Series) -> str:
    """Report the median gap rather than the mean: what matters is the interval
    the collar was programmed to, and how tightly the gaps sit on it."""
    gaps = []
    for _, grp in times.groupby(ids):
        g = grp.dropna().sort_values().diff().dropna().dt.total_seconds() / 3600
        gaps.append(g)
    if not gaps:
        return "  fix interval: not derivable"
    g = pd.concat(gaps)
    g = g[(g > 0) & g.notna()]
    if g.empty:
        return "  fix interval: not derivable"
    med = g.median()
    on_schedule = (g.sub(med).abs() < 0.1 * med).mean() * 100
    return (
        f"  fix interval: median {med:.2f} h  ({on_schedule:.0f}% of {len(g):,} gaps within 10% "
        f"of it; q05={g.quantile(0.05):.2f} q95={g.quantile(0.95):.2f})"
    )


def describe(df: pd.DataFrame, label: str) -> None:
    cols = list(df.columns)
    print(f"\n  {label} -- {len(df):,} rows x {len(cols)} cols")
    print("  columns:")
    for c in cols:
        s = df[c]
        ex = " | ".join(str(v)[:20] for v in s.dropna().head(2)) or "NA"
        print(f"    {str(c)[:28]:<28} {str(s.dtype):<14} nuniq={s.nunique():<9,} nNA={s.isna().sum():<9,} ex= {ex[:46]}")

    coord_cols, time_cols = matching(cols, COORD), matching(cols, TIME)
    id_cols, spp_cols = id_columns(cols), matching(cols, SPP)
    print(
        f"\n  VERDICT INPUTS  coords=[{','.join(map(str, coord_cols))}]  time=[{','.join(map(str, time_cols))}]"
        f"  id=[{','.join(map(str, id_cols))}]  species=[{','.join(map(str, spp_cols))}]"
    )

    for c in coord_cols:
        v = pd.to_numeric(df[c], errors="coerce")
        if v.notna().any():
            print(f"  range {str(c)[:12]:<12} {v.min():.3f} .. {v.max():.3f}")

    tcol = None
    for c in time_cols:
        t = as_time(df[c])
        if t is not None and t.notna().any():
            print(f"  span  {str(c)[:12]:<12} {t.min()} .. {t.max()}")
            if tcol is None:
                tcol = t

    idv = df[id_cols[0]] if id_cols else None
    if idv is not None:
        print(f"  individuals:  {idv.nunique():,} distinct {id_cols[0]}")
    if spp_cols:
        print("  by species:")
        for name, grp in df.groupby(df[spp_cols[0]], dropna=False):
            n_ind = grp[id_cols[0]].nunique() if id_cols else "?"
            print(f"    {str(name)[:24]:<24} {len(grp):>10,} rows  {n_ind} individuals")
    if tcol is not None and idv is not None:
        print(fix_interval(tcol, idv))


def main(paths: list[str]) -> int:
    if not paths:
        print(__doc__)
        return 2
    for path in map(Path, paths):
        print("=" * 100)
        print(f"FILE {path}  ({path.stat().st_size / 1e6:.1f} MB)")
        if path.suffix.lower() in {".xlsx", ".xls", ".xlsm"}:
            book = pd.ExcelFile(path)
            print("sheets:", ", ".join(book.sheet_names))
            for sheet in book.sheet_names:
                describe(book.parse(sheet), f"{path.name}[{sheet}]")
        else:
            describe(pd.read_csv(path, sep=None, engine="python"), path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
