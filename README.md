# Where the storks went

Fifty-nine white storks, ringed as chicks in seven places between Spain and
Armenia, tracked hourly from the start of their first autumn migration to the
following July. Every dot is a real bird at a real date and hour, and the routes
are drawn by the birds as they fly them. Storks soar, and thermals do not form
over open water — so the thing to watch is where they cross the Mediterranean,
and where they refuse to.

## Run it

- **Self-contained page** — <https://claude.ai/code/artifact/f84a4d5e-c726-4d82-a258-d838297828c4>
  Everything is inside the file: tracks, backdrop, code. No data fetch, no tile
  server, works offline. It is private until shared from the page's own menu.
- **GitHub Pages** — <https://chillchamp1.github.io/Animal-movement/>
  The same map, fetching its data at load. It serves whatever is on the default
  branch, so it follows this work once the branch is merged.
- **Locally** — the page fetches its data, so it needs http(s):

  ```sh
  python3 -m http.server 8000    # then open http://localhost:8000
  ```

Built from two Movebank Data Repository deposits, both CC0, shown as two views
and never pooled:

- **Origins** — Flack et al. (2016), *Costs of migratory decisions: a comparison
  across eight white stork populations*, Science Advances 2:e1500931,
  [`doi:10.5441/001/1.78152p3q`](https://doi.org/10.5441/001/1.78152p3q).
  Fifty-nine juveniles from seven tagging sites, Aug 2013 – Jul 2014.
- **Ages** — Rotics et al. (2016), *The challenges of the first migration*,
  Journal of Animal Ecology 85:938–947,
  [`doi:10.5441/001/1.hn1bd23k`](https://doi.org/10.5441/001/1.hn1bd23k).
  Seventy-four storks from one colony in Sachsen-Anhalt over autumn 2013 — 37 on
  their first migration, 37 adults, same route and same weeks.

## What is on screen

| Origin | Birds | Fixes |
|---|---|---|
| **Germany** | 12 | 34,532 |
| **Russia** | 10 | 31,754 |
| **Armenia** | 8 | 14,560 |
| **Poland** | 4 | 14,434 |
| **Tunisia** | 8 | 11,572 |
| **Greece** | 10 | 11,504 |
| **Spain** | 7 | 9,250 |

127,606 hourly fixes over 350 days, from 55°N in the Baltic to 27°S in southern
Africa and from Senegal east to Kazakhstan. The tags recorded every five
minutes; this is thinned to hourly.

The **clock** is a real calendar date and hour. Under it, two counts taken from
the data at that hour: how many birds are covering ground, and how many tags are
reporting at all. The strip behind the scrubber is kilometres per bird per day
across the whole deposit — migration is not something you have to look for in
it, it is the spikes.

Colours run west to east, warm to cool, so when the tracks fan out around the
Mediterranean their colour already says which end of Europe each bird came from.

Drag to pan, scroll or pinch to zoom (up to 2000×), `0` or the **fit** button to
reset.

## The two crossings

Storks climb in thermals and glide between them, which costs a fraction of what
flapping costs — and thermals form over warm land, not over water. So the sea is
crossed where it is narrow: at Gibraltar in the west, or round the eastern end
through the Levant.

The **Crossing** filter is derived from the data rather than assumed: for each
bird, the longitude at which it first got south of 36°N. Of the 59, **12 crossed
at Gibraltar, 9 through the central Mediterranean, 24 by the Levant, and 14
never went south of 36°N at all.**

That last group is not a gap in the data. Some are Spanish birds that no longer
migrate — they winter on rubbish tips within a few hundred kilometres of the
nest — and some are birds that died before their first autumn.

## What was left out, and why

The deposit holds 72 birds and runs from November 2012. Two parts of it were not
worth drawing, and both absences are findings rather than omissions.

**The first six months are one bird.** Every tag but one goes on in June or July
2013, when that year's chicks were ringed at the nest. Before that there is a
single South African stork and nothing else — 226 days, 38% of the original
timeline, one dot. The map starts on **1 August 2013**, which drops that bird
along with the empty stretch, and also the two months the new birds spent
standing around the nest before autumn migration began.

**The Uzbek birds do not migrate.** Six storks of the Ferghana Valley, ranging a
median of 148 km and never going south of 40°N in up to 365 days each. That is a
real thing about *Ciconia ciconia asiatica*, not a gap in the data — but on a
map about movement they were six dots that never moved.

## The second view: first autumn against adult

Every bird in the first deposit is a juvenile — all 72, checked in the
reference data. It can show where a generation goes; it has nobody to measure
them against. The second deposit supplies exactly that, and only that: one
colony, both age classes, the same eastern flyway. In autumn 2013 it carries 37
first-year birds and 37 adults over the same 92 days.

They are deliberately **not** folded into the first view. They are a single
site, they outnumber the whole first deposit two to one, and dropping them into
a palette keyed on origin would turn a seven-population map into a German one.
So the toggle swaps the entire dataset — and the clock with it, since the second
deposit is fall migration only and stops on 31 October. That is also why the
**Crossing** filter is not offered there: a bird that has not passed 36°N by the
end of October has not decided against migrating, the window simply ended first.

## Why not LifeTrack

The obvious larger option was the LifeTrack series — 7 studies, 326 birds,
42.4 million fixes, CC0. It was measured and rejected:

- **251 of the 326 birds are German or Austrian**, so western flyway only. The
  map's subject is the fork into two flyways; LifeTrack thickens one cord.
- Its question is the *ontogeny* of migration — how one bird refines a route
  across its life — so its value is a decade of depth on one population. This
  map is a 350-day window, which would keep about a tenth of it.
- The five German and Austrian studies alone are 1.56 GB of GPS archives, and
  42.4 M fixes thinned to hourly is still roughly 14 M — around a hundred times
  what the page carries.

LifeTrack deserves its own map. It is not an addition to this one.

## The globe

`globe.html` is a second page and a different question. The map above shows many
birds at once on a fixed frame; the globe follows **one** bird, turning under it
so the animal stays in the middle of the view — which is the only honest way to
show a journey that crosses the date line or most of a hemisphere.

Two journeys, both real, both CC0, chosen by `scripts/build_globe.py`:

| | Bird | Journey |
|---|---|---|
| **Hudsonian godwit** (*Limosa haemastica*) | KHE | Off the Chilean coast to the Texas Gulf coast — **7,931 km in 5.9 days**, averaging 56 km/h the whole way. 77 GPS fixes, one every ~1.8 h. |
| **Grey-headed albatross** (*Thalassarche chrysostoma*) | 89518 | One foraging trip from Campbell Island out across the antimeridian and back — **12,285 km over 21.9 days**, ending **2 km from where it began**. 5,959 GPS fixes, one every 5 min. |

### Two birds this is not

The page was asked for the bar-tailed godwit `4BBRW` of the record
Alaska–New Zealand flight, and for a wandering albatross. Neither is open data,
so rather than fake them the page shows the nearest real thing and says so.

- **Bar-tailed godwit.** The one deposit in the archive,
  `doi:10.5441/001/1.327`, is geolocator work: 18 birds and **103 fixes in
  total**, a median of six per bird, with explicit `lat-lower`/`lat-upper` error
  columns because that is what geolocators give. An eleven-day flight would be
  two or three points, each uncertain by a hundred kilometres.
- **Wandering albatross.** No deposit at all. Procellariiform tracking lives in
  BirdLife International's Seabird Tracking Database, which releases data per
  request and per data owner, not by open download.

### What was thrown away

173 of the 3,548 godwit GPS rows — 4.9% — carry impossible coordinates, latitude
−213 among them, and they are almost all **unflagged**:
`manually-marked-outlier` is empty for 171 of them and the tag calls 158 of them
good 3D fixes. They have to be caught on the coordinate range, not the quality
flag. Inside the valid range a forward pass drops any fix that could only be
reached faster than the bird can fly, anchored on the last *accepted* fix.
Distance is only ever summed inside a continuous run: a four-day silence spans
thousands of kilometres at a plausible average speed, and counting it inflated
one bird's total to 458,000 km before that rule went in.

### Rendering

globe.gl (MIT, bundles three.js) over NASA's Blue Marble Next Generation, with a
global elevation map as a bump layer. All of it is checked into `vendor/` rather
than fetched from a CDN — see `vendor/README.md` for provenance and how to
refresh it — so the page works on a host that permits no outbound requests.

The camera eases toward the bird on a time constant rather than a fixed
fraction per frame, so the lag does not depend on the frame rate: measured 50 km
steady-state, 117 km worst case, on a software renderer.

## The ground under them

**Satellite** — Esri World Imagery, fetched as tiles at view time — is the
default on the web app, because imagery is the only real picture of this
ground. It needs a host that permits outbound requests, so where those are
blocked the page falls back to the backdrop it already carries rather than
showing an empty map, and says why in the attribution line. An explicit choice
of satellite is never overridden that way; only the default is.

**Land & sea** is that baked backdrop: one elevation raster for the hillshade,
the bathymetry and every coastline, plus ESA WorldCover for standing water and
a faint green wash. It needs no connection, so it is what the self-contained
build starts on — that build has no network by design.

## The crosses

Twenty-two of the 59 tags in **Origins**, and 21 of the 74 in **Ages**, stopped
because the bird died, which both deposits record.
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

**Gaps.** These are solar tags: they report through the day and fall silent
overnight — at 21:00 UTC not one of them reports — and coverage thins badly on
the long crossings. What decides whether a gap may be drawn across is how far
wrong a straight line could be, and that is a question about the gap's length
rather than the bird's speed. Up to a day the line is a fair approximation: a
stork covers a few hundred kilometres at most, a short step at this scale.
Longer gaps are bridged only where the bird plainly did not move, which is the
case on wintering grounds where a tag can go quiet for a week between reports
from the same field. Where a gap is too long even for that, the bird waits as a
hollow ring at the last place its tag reported — Pelopidas goes quiet for
twenty-eight days in the middle of Africa — because an empty patch of map would
say it was gone, which is a stronger claim than the data makes.

**These are 72 birds, not the population.** Roughly half a million white storks
migrate along these flyways. Empty sky is where no tag was.

**The map is Web Mercator**, so area inflates towards the poles: the Baltic is
drawn larger than the Sahel for the same ground. Judge distance along the tracks
rather than across the frame.

**Positions are rounded** to 10⁻⁵ degrees, about a metre, well under the tags'
own error.

## A video of it

`scripts/render_video.py` drives a headless browser through the whole timeline,
captures a frame per step and hands them to ffmpeg. Playback is stopped and each
frame is seeked exactly, so the output does not depend on how fast the machine
rendered. Portrait 1080×1920 by default, because these birds span 82 degrees of
latitude against 66 of longitude and a vertical frame wastes less of that than a
landscape one; the interactive controls are hidden, leaving the date, the key
and the attribution.

```sh
python3 scripts/build_standalone.py       # the video reads the self-contained build
python3 scripts/render_video.py           # -> dist/where-the-storks-went.mp4
python3 scripts/render_video.py --view ages   # -> dist/first-autumn-or-fiftieth.mp4
python3 scripts/render_video.py --size 1080x1080 --seconds 25
```

## Rebuilding the data

The data is **not kept in this repository**. The Pages workflow rebuilds it on
every deploy; to do the same locally:

```sh
python3 scripts/fetch_movebank.py --doi 10.5441/001/1.78152p3q \
    --match gps reference-data README --out data/raw/storks
python3 scripts/fetch_movebank.py --doi 10.5441/001/1.hn1bd23k \
    --match gps reference-data README --out data/raw/storks-ages
python3 scripts/build_storks.py         # -> data/processed/storks.json
python3 scripts/build_storks.py --raw data/raw/storks-ages \
    --out-name storks-ages.json --from-date 2013-08-01 --to-date 2013-11-01 \
    --exclude --source "Rotics et al. 2016, doi:10.5441/001/1.hn1bd23k (CC0)"
python3 scripts/fetch_movebank.py --doi 10.5441/001/1.t81488n5 \
    --match gps reference-data README --out data/raw/godwit-hud
python3 scripts/fetch_movebank.py --doi 10.5441/001/1.694p666h \
    --match Torres README --out data/raw/albatross
python3 scripts/build_globe.py          # -> globe-tracks.json, one journey per species
python3 scripts/build_landcover.py      # -> water and greenness, ~15 min, cached
python3 scripts/build_basemap.py        # -> basemap.json, the whole backdrop baked in
python3 scripts/build_standalone.py     # -> dist/, one self-contained file
```

`--match` matters: between them the two deposits ship 640 MB of accelerometer
data that nothing here reads.

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

Rotics, S., Kaatz, M., Resheff, Y. S., et al. (2016). *The challenges of the
first migration: movement and behavior of juvenile versus adult white storks
with insights regarding juvenile mortality.* Journal of Animal Ecology
85:938–947. Data: `doi:10.5441/001/1.hn1bd23k`, Movebank Data Repository, CC0.

For the globe:

Senner, N. R., Stager, M., Verhoeven, M. A., et al. *Compensation for wind drift
prevails for a shorebird on a long-distance, transoceanic flight.* Data:
`doi:10.5441/001/1.t81488n5`, Movebank Data Repository, CC0.

Torres, L. G., Orben, R. A., Tolkova, I., Thompson, D. R. *Classification of
animal movement behavior through residence in space and time.* Data:
`doi:10.5441/001/1.694p666h`, Movebank Data Repository, CC0.

Backdrop, from two measured sources:

- Elevation and bathymetry — Terrain Tiles on AWS Open Data (Mapzen/Nextzen
  terrarium), SRTM and GMTED on land, ETOPO1 and other surveys at sea. Height
  sets the colour and slope sets how it is lit, because height is what a soaring
  bird lives on: thermals form over warm broken ground, so the Atlas, the
  Iberian meseta, the Anatolian plateau and the Ethiopian highlands are the
  corridors.
- Water and vegetation — ESA WorldCover 2021 v200 (CC BY 4.0), 10 m global land
  cover on AWS Open Data, read at its coarsest internal overview and reduced to
  about 5 km. Lakes, the Nile, the Niger and the Sudd are drawn as water; the
  green is a faint wash keyed to tree, shrub, grass and crop cover. Its job is
  one edge: the Sahara is bare and the Sahel below it is not, and that line is
  where the desert crossing ends.
