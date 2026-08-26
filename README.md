# Where the storks went

Seventy-two white storks, tagged as juveniles in nine places between Spain and
Uzbekistan, tracked hourly from the Baltic to the Cape. Every dot is a real bird
at a real date and hour. Storks soar, and thermals do not form over open water —
so the thing to watch is where they cross the Mediterranean, and where they
refuse to.

**Live: https://chillchamp1.github.io/Animal-movement/**

Built from Flack et al. (2016), *Costs of migratory decisions: a comparison
across eight white stork populations*, Science Advances 2:e1500931 —
[`doi:10.5441/001/1.78152p3q`](https://doi.org/10.5441/001/1.78152p3q) in the
Movebank Data Repository, CC0.

## What is on screen

| Origin | Birds | Fixes |
|---|---|---|
| **Germany** | 13 | 42,731 |
| **Russia** | 10 | 34,700 |
| **Armenia** | 8 | 19,761 |
| **Tunisia** | 9 | 18,905 |
| **Spain** | 11 | 17,438 |
| **Greece** | 10 | 16,808 |
| **Poland** | 4 | 15,442 |
| **Uzbekistan** | 6 | 13,644 |
| **South Africa** | 1 | 999 |

180,428 hourly fixes over 594 days, from 55°N to 34°S and from Senegal east to
Uzbekistan. The tags recorded every five minutes; this is thinned to hourly.

The **clock** is a real calendar date and hour. Under it, two counts taken from
the data at that hour: how many birds are covering ground, and how many tags are
reporting at all. The strip behind the scrubber is kilometres per bird per day
across the whole deposit — migration is not something you have to look for in
it, it is the spikes.

Colours run west to east, warm to cool, so when the tracks fan out around the
Mediterranean their colour already says which end of Europe each bird came from.

Drag to pan, scroll or pinch to zoom (up to 2000×), `0` or the **fit** button to
reset. The scale bar re-steps from 5000 km down to 100 m, and is re-measured at
the centre of the view because Mercator stretches with latitude.

## The two crossings

Storks climb in thermals and glide between them, which costs a fraction of what
flapping costs — and thermals form over warm land, not over water. So the sea is
crossed where it is narrow: at Gibraltar in the west, or round the eastern end
through the Levant.

The **Crossing** filter is derived from the data rather than assumed: for each
bird, the longitude at which it first got south of 36°N. Of the 72, **14 crossed
at Gibraltar, 11 through the central Mediterranean, 24 by the Levant, and 23
never went south of 36°N at all.**

That last group is not a gap in the data. Some are Spanish birds that no longer
migrate — they winter on rubbish tips within a few hundred kilometres of the
nest — and some are birds that died before their first autumn.

## The crosses

Thirty of the 72 tags stopped because the bird died, which the deposit records.
Where that happens the track does not simply vanish: a cross stays at the last
position. A juvenile's first migration is the most dangerous journey of its
life, and a track that disappeared silently would read as a coverage gap
instead of what it was.

## Why this deposit

The map began on an Okavango Delta deposit with no predator positions in it,
moved to Utah cougars and their prey, and ended here. The reason is in the
numbers: across all 2,013 deposits in the Movebank Data Repository, large
carnivores account for **1.1% of deposits and 0.5% of the fixes**. Open tracking
data is overwhelmingly birds, and predator–prey interaction is close to the
hardest thing to find in it. Migration is the opposite — it is what the archive
is full of, and it is a story a map can actually tell.

The audit that got here, including four Dryad deposits that all failed and the
profilers that established it, is in
**[docs/dataset-audit.md](docs/dataset-audit.md)**.

## What is missing

**Gaps are drawn as absence, mostly.** These are solar tags: they report through
the day and fall silent overnight — at 21:00 UTC not one of the 72 is reporting.
A rule of "consecutive hours only" would empty the map every night, so a gap is
bridged when the bird cannot have gone anywhere across it, and broken when it
could. A consecutive hour always connects, however fast the bird was flying;
only gaps are tested, and only a gap the bird slept through is drawn across.

**These are 72 birds, not the population.** Roughly half a million white storks
migrate along these flyways. Empty sky is where no tag was.

**The map is Web Mercator**, so area inflates towards the poles: the Baltic is
drawn larger than the Sahel for the same ground. That is why the scale bar
changes as you pan north or south.

**Positions are rounded** to 10⁻⁵ degrees, about a metre, well under the tags'
own error.

## Running it

The page fetches its data, so it needs http(s) — GitHub Pages, or locally:

```sh
python3 -m http.server 8000    # then open http://localhost:8000
```

## Rebuilding the data

The data is **not kept in this repository**. The Pages workflow rebuilds it on
every deploy; to do the same locally:

```sh
python3 scripts/fetch_movebank.py --doi 10.5441/001/1.78152p3q \
    --match gps reference-data README --out data/raw/storks
python3 scripts/build_storks.py         # -> data/processed/storks.json
python3 scripts/build_basemap.py        # -> basemap.json, land and sea baked in
python3 scripts/build_standalone.py     # -> dist/, one self-contained file
```

`--match` matters: the deposit ships 341 MB of accelerometer data that nothing
here reads.

`scripts/profile_rdata.R` and `scripts/profile_tables.py` are the audit's two
profilers: point either at a candidate deposit and it reports columns, row
counts, individuals per species, coordinate and time ranges, and median fix
interval — enough to decide whether a deposit can carry a map at all.

The two earlier pipelines are still here and still run: `build_utah.py` and
`build_utah_layers.py` against the Utah cougar and ungulate deposits, and
`fetch_dryad.py` with `build_tracks.py`, `build_risk.py` and `build_seasonal.py`
against `doi:10.5061/dryad.w0vt4b8zr`, the Okavango reconstruction.

## Source

Flack, A., Fiedler, W., Blas, J., et al. (2016). *Costs of migratory decisions:
a comparison across eight white stork populations.* Science Advances 2:e1500931.
Data: `doi:10.5441/001/1.78152p3q`, Movebank Data Repository, CC0.

Backdrop: elevation and bathymetry from Terrain Tiles on AWS Open Data
(Mapzen/Nextzen terrarium) — SRTM and GMTED on land, ETOPO1 and other surveys
at sea.
