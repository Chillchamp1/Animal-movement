# A day in the Delta

Hourly GPS tracks of four herbivores in the Okavango Delta, Botswana, animated
against the hours when lions and wild dogs hunt. Every dot is a collared animal
and every position is a real fix. The map is dark at every hour, so the animals
are the only bright thing on it.

Built from Bennitt et al. (2024), `doi:10.5061/dryad.w0vt4b8zr` — impala,
tsessebe, wildebeest and zebra collared in 2014–2016, alongside the lions and
wild dogs whose ranges they had to share.

## What is on screen

| Species | Collars (dry / rainy) | Fixes |
|---|---|---|
| **Zebra** | 7 / 7 | 42,400 |
| **Tsessebe** | 5 / 6 | 44,602 |
| **Wildebeest** | 4 / 4 | 15,651 |
| **Impala** | 5 / — | 14,315 |

116,968 verified hourly fixes over 38 individual-seasons. Impala were only
collared in the dry season.

Three things move at once. The **clock** is real hour-of-day. The two **lamps**
under it show which predator is in its active window — wild dogs at dawn and
dusk (04–08, 17–19), lions through the night (18–07). The **risk layer** is the
predator's utilisation surface, and it switches between its active and inactive
state as the clock crosses those windows, so the landscape itself lights up when
the hunters do. A **ring** round an animal means it is sitting in the top decile
of that predator's range while that predator is active.

The histogram behind the scrubber is the finding the source paper is about: how
far these animals actually move in each hour of the day, with the dog and lion
windows coloured underneath.

## How the tracks were recovered

The Dryad deposit ships analysis-ready tables, not raw collar downloads, and at
first glance the trajectories look unrecoverable — nothing in it carries a
timestamp. They survive across two of the tables:

- `RSF/*.csv` holds real coordinates (UTM 34S, snapped to the 25 m habitat
  raster) but is **stably sorted by predator activity state** — every "High"
  row, then every "Low" row — which destroys chronological order.
- `Distances/*.csv` holds the same fixes in **true chronological order** with
  hour-of-day and step length, but no coordinates.

Predator activity turns out to be a deterministic function of hour-of-day, so
that sort is invertible: walk the chronological hour sequence and, for each
hour, take the next unused point from whichever activity block that hour belongs
to. The two tables use slightly different activity windows, so the window is
solved per file and each reconstruction is scored against the authors' own
step-length column.

All seven species-seasons independently resolve to the same window
`{4,5,6,7,8,17,18,19}` and reproduce the published step lengths at **98.8–100%
within 40 m**, median error 5–7 m — the residual expected from 25 m grid
quantisation. As a further check, the lion-context rows, sorted by an unrelated
nocturnal rule, reconstruct to identical geometry. Individuals where the two
tables disagree about a fix are dropped rather than shown unverified.

## What is missing

**No calendar dates.** The deposit records hour-of-day but never a date. The
clock is real; the day counter is only elapsed time from each collar's first
fix. Animals are aligned by time of day, not by date — two dots side by side
were not necessarily there in the same week.

**No predator positions.** Lions and wild dogs were collared, but none of their
coordinates are in the deposit. They appear only as activity windows and as a
utilisation surface sampled at prey locations. A ring is a measure of exposure,
not an observed encounter.

**Positions are quantised** to the 25 m analysis raster, so fine detail is not
real detail.

**Gaps are drawn as absence.** Where a collar missed hours the animal is not
drawn. Gap length is taken as the shortest span consistent with the hours either
side, so long absences are understated, and nothing is ever interpolated across
a gap.

**No basemap.** Nothing here fetches coastlines or rivers; the landscape is
drawn from the fixes themselves. What you see is where these animals went, and
nothing they did not.

## Running it

The page fetches its data, so it needs http(s) — GitHub Pages, or locally:

```sh
python3 -m http.server 8000    # then open http://localhost:8000
```

## Rebuilding the data

```sh
python3 scripts/fetch_dryad.py                 # needs access to datadryad.org
unzip -o '*.zip' -d data/raw/                  # or use the committed zips
python3 scripts/build_tracks.py                # -> data/processed/<species>-<season>.json
python3 scripts/build_risk.py                  # -> data/processed/predator-risk.json
```

`build_tracks.py` prints the agreement score for every species-season; treat a
drop below the 95% floor as a reason to distrust the output, not to lower the
floor.

## Source

Bennitt, E. et al. (2024). *Proactive cursorial and ambush predation risk
avoidance in four African herbivore species.* Ecology and Evolution.
Data: <https://doi.org/10.5061/dryad.w0vt4b8zr>
