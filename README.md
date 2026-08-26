# A day in the Delta

Hourly GPS tracks of four herbivores in the Okavango Delta, Botswana, animated
against the hours when lions and wild dogs hunt. Every dot is a collared animal
and every position is a real fix. The map is dark at every hour, so the animals
are the only bright thing on it.

**Live: https://chillchamp1.github.io/Okavango-Delta-predator-prey-dataset-Botswana-/**

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

Only the animals move. Nothing else is drawn on the map except the landscape
layer you choose, so a dot on screen is an animal at that hour rather than a
smear of everywhere it has ever stood.

Three things move at once. The **clock** is real hour-of-day. The two **lamps**
under it show which predator is in its active window — wild dogs at dawn and
dusk (04–08, 17–19), lions through the night (18–07). A **ring** round an animal
means it is sitting in the top decile of that predator's range while that
predator is active.

The histogram behind the scrubber is the finding the source paper is about: how
far these animals actually move in each hour of the day, with the dog and lion
windows coloured underneath.

Drag to pan, scroll or pinch to zoom (up to 400×), `0` or the **fit** button to
reset. Zooming redraws at the new scale rather than magnifying, and the scale
bar re-steps from 50 km down to 100 m. The legend folds away with a click on its
heading.

### Landscape layers

- **Satellite** — Esri World Imagery, fetched as tiles at view time. Nothing is
  bundled, so it needs a connection; where outbound requests are blocked the
  tiles do not arrive, the dark ground stays and the attribution line says so.
  The imagery is a mosaic of mixed dates, not 2014–2016 — in a delta that floods
  every year, the water in the picture is not the water these animals walked
  around.
- **Wild dog range** / **Lion range** — that predator's utilisation surface,
  switching between its active and inactive state as the clock crosses its
  hunting window, so the landscape lights up when the hunters do.
- **Flood shift** — dry-versus-rainy occupancy for the ten animals collared in
  *both* seasons (four tsessebe, four zebra, two wildebeest; 68,926 fixes).
  Restricting it to animals present in both seasons is what makes it a seasonal
  comparison rather than a comparison of who happened to be wearing a collar.

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

**The predators are in the data, but not as positions.** Ten were collared
alongside the herbivores — six lions (Buzz, Chloe, F3, F8, Hector, Pride) and
four wild dogs (Adiga, Bali, Bongwe, Xerxes), each with habitat selection
measured in both seasons. What the deposit carries of them is their utilisation
surface, evaluated at every prey location (the `UI` column of the RSF tables),
together with their diel activity windows — the range layers and the lamps are
both built from it. What it does not carry is a single predator coordinate or
timestamp, so they cannot be drawn moving, and a ring is a measure of exposure
rather than an observed encounter.

**Positions are quantised** to the 25 m analysis raster, so fine detail is not
real detail.

**Gaps are drawn as absence.** Where a collar missed hours the animal is not
drawn. Gap length is taken as the shortest span consistent with the hours either
side, so long absences are understated, and nothing is ever interpolated across
a gap.

**No vegetation or water map from the data itself.** Satellite imagery is
available as a backdrop (above), but it is a mixed-date mosaic, not a measured
layer for this study period. The deposit gives vegetation
only as aggregate proportions per animal — floodplain, grassland, mixed,
mopane — never mapped, and the 25 m habitat raster behind the original analysis
was not deposited. Public vector data does not fill the gap: at 1:10m scale
Natural Earth resolves the entire Okavango as a single river centreline, which
says nothing across 70 km. So nothing here fetches coastlines or rivers, and
none of the landscape layers is a basemap. **Flood shift** in particular is a
map of where animals went, not of where water is — in the Okavango the flood
arrives during the dry season, so the contrast traces the flood-driven structure
of the range, but it is inference from behaviour, not observation of water.

**Each collar repeats its own record.** The collars ran for very different
lengths, 35 days to 200, and played once through they drop away one by one until
a couple of animals are moving alone. Each therefore loops, on a period rounded
up to whole days so every animal's hour-of-day still matches the clock exactly.
The cost is that elapsed days are no longer comparable between animals once the
shorter records come round again.

## Running it

The page fetches its data, so it needs http(s) — GitHub Pages, or locally:

```sh
python3 -m http.server 8000    # then open http://localhost:8000
```

## Rebuilding the data

The data is **not kept in this repository** — neither the Dryad deposit nor
anything derived from it. The live site and the local page both need
`data/processed/` to exist, so run these first:

```sh
python3 scripts/fetch_dryad.py                 # needs access to datadryad.org
unzip -o 'data/raw/*.zip' -d data/raw/
python3 scripts/build_tracks.py                # -> data/processed/<species>-<season>.json
python3 scripts/build_risk.py                  # -> data/processed/predator-risk.json
python3 scripts/build_seasonal.py              # -> data/processed/seasonal-shift.json
python3 scripts/build_standalone.py            # -> dist/, one self-contained file
```

`build_tracks.py` prints the agreement score for every species-season; treat a
drop below the 95% floor as a reason to distrust the output, not to lower the
floor.

## Source

Bennitt, E. et al. (2024). *Proactive cursorial and ambush predation risk
avoidance in four African herbivore species.* Ecology and Evolution.
Data: <https://doi.org/10.5061/dryad.w0vt4b8zr>
