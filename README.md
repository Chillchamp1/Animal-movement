# Cougars and their prey

Two-hourly GPS tracks of cougars, elk and mule deer in the northern Wasatch,
Utah, played on one calendar clock. Every dot is a collared animal and every
position is a real fix at a real date and hour. When a prey animal comes within
a kilometre of a collared cougar, a ring and a hairline appear — and that is a
distance that was measured, not a modelled range it happens to be standing in.

**Live: https://chillchamp1.github.io/Animal-movement/**

Built from two deposits by the Utah Division of Wildlife Resources in the
[Movebank Data Repository](https://datarepository.movebank.org/), both CC0:
[`doi:10.5441/001/1.712`](https://doi.org/10.5441/001/1.712) (cougars) and
[`doi:10.5441/001/1.711`](https://doi.org/10.5441/001/1.711) (ungulates).

## What is on screen

| Species | Collars (2019 / 2020) | Fixes |
|---|---|---|
| **Mule deer** | 83 / 89 | 168,583 |
| **Elk** | 74 / 85 | 144,049 |
| **Cougar** | 8 / 11 | 19,012 |

331,644 fixes in a 100 × 91 km block, over two seasons. Both guilds ran on the
same two-hour schedule, so predator and prey share the clock exactly.

Three things move at once. The **clock** is a real calendar date and hour. The
**lamp** under it lights in the hours when the collared cougars were actually
covering ground — measured from their own step lengths, not from a stated
hunting window. A **ring** and its hairline mark a prey animal within a
kilometre of a cougar that was there at that hour, brightening as the distance
closes; the readout gives the closest one on screen.

The strip behind the scrubber is the season rather than the day: mean distance
covered per two-hour step, one bar per day, with the months marked. Spring
shows up in it.

Drag to pan, scroll or pinch to zoom (up to 400×), `0` or the **fit** button to
reset. Zooming redraws at the new scale rather than magnifying, and the scale
bar re-steps from 500 km down to 100 m. The legend folds away with a click on
its heading.

### Landscape layers

- **Satellite** — Esri World Imagery, fetched as tiles at view time. Nothing is
  bundled, so it needs a connection; where outbound requests are blocked the
  tiles do not arrive, the dark ground stays and the attribution line says so.
  The imagery is a mosaic of mixed dates, not 2019–2020.
- **Cougar range** — where the collared cougars actually were that season,
  smoothed. An observation, not a model, so it has no active and inactive
  state: there is only one place a cougar was.
- **Year shift** — January-to-May occupancy in 2019 against 2020, for the 96
  animals collared in *both* years (54 elk, 40 mule deer, 2 cougars; 223,011
  fixes). Restricting it to animals present in both is what makes it a
  comparison of behaviour rather than of who happened to be wearing a collar.

## Why this deposit

The map began on an Okavango Delta deposit that turned out to carry no predator
positions at all — lions and wild dogs existed in it only as a utilisation
surface and a set of activity windows, so a ring could mean exposure but never
an encounter. Four candidate replacements on Dryad were audited against a
single question: **does it hold coordinates *and* a timestamp, for predators as
well as prey?** All four failed. Two of them had their coordinates removed
deliberately, for animal safety.

The pattern turned out to be structural, and it is what pointed the search at
Movebank: a deposit carries what the analysis consumed, and modern movement
analyses — resource-selection functions, hidden Markov models, step selection —
consume *covariates extracted at locations* rather than the locations, so the
coordinates drop out one step before publication. A tracking archive inverts
that: there the deposit is the collar download.

The full audit, the evidence for each verdict, and the profilers it was made
with are in **[docs/dataset-audit.md](docs/dataset-audit.md)**.

## What is missing

**The year stops in May.** Both deposits cover 1 January to 16 May, in 2019 and
again in 2020, and nothing in between — this is winter and spring range
monitoring. Rather than run a calendar across seven empty months, the two
windows are offered as two seasons: the same months, a year apart, which is
what makes the year-shift layer a comparison rather than a coincidence.

**No ring is not no cougar.** Only 8 to 11 cougars wore collars in this block.
An unringed animal means no *collared* cougar was within a kilometre at that
hour, which is a much weaker statement than safety. Distances above 5.1 km are
stored as "far" and never drawn.

**These are the collared animals, not the population.** Empty ground is where no
collar was, not where no animal was.

**Gaps are drawn as absence.** A track segment holds consecutive fixes only — a
single missed fix ends it, and nothing is ever drawn across the silence. An
animal is simply not there until its collar reports again.

**Positions are rounded** to 10⁻⁵ degrees, about a metre, well under the
collars' own error.

**The block is a rectangle.** The 100 × 91 km clip is the region where the two
guilds overlap most densely; its edges are a choice, not a boundary the animals
respect.

## Running it

The page fetches its data, so it needs http(s) — GitHub Pages, or locally:

```sh
python3 -m http.server 8000    # then open http://localhost:8000
```

## Rebuilding the data

The data is **not kept in this repository** — neither the deposits nor anything
derived from them. The Pages workflow rebuilds it on every deploy; to do the
same locally:

```sh
python3 scripts/fetch_movebank.py --doi 10.5441/001/1.712   # cougars
python3 scripts/fetch_movebank.py --doi 10.5441/001/1.711   # ungulates, 63 MB
python3 scripts/build_utah.py                # -> data/processed/tracks-<year>.json
python3 scripts/build_utah_layers.py         # -> cougar-use.json, year-shift.json
python3 scripts/build_standalone.py          # -> dist/, one self-contained file
```

`scripts/profile_rdata.R` and `scripts/profile_tables.py` are the two profilers
from the audit: point either at a candidate deposit and it reports the columns,
row counts, individuals per species, coordinate and time ranges, and median fix
interval — enough to answer the question above without reading the files by eye.

The Okavango pipeline is still here — `fetch_dryad.py`, `build_tracks.py`,
`build_risk.py`, `build_seasonal.py` — and still runs against
`doi:10.5061/dryad.w0vt4b8zr`. It is the record of the reconstruction that made
that map possible, and of what it could not overcome.

## Source

Utah Division of Wildlife Resources. *GPS tracking of cougars in Utah by UDWR
(2019-2020)*, `doi:10.5441/001/1.712`, and *GPS tracking of ungulates in Utah by
UDWR (2019-2020)*, `doi:10.5441/001/1.711`. Movebank Data Repository, both CC0.
