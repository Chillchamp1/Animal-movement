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

Three journeys, all real, all CC0, chosen by `scripts/build_globe.py` — and a
fourth view that is not a journey at all, and says so on its face. See
**The eel** below.

| | Bird | Journey |
|---|---|---|
| **White stork** (*Ciconia ciconia*) | DER AR445 | Western Russia to Sudan on its first autumn — **14,835 km over 136 days**, ending 6,596 km from the nest. Coloured by tagging site, with the other 58 birds of the deposit flying the same weeks. |
| **Hudsonian godwit** (*Limosa haemastica*) | KHE | Off the Chilean coast to the Texas Gulf coast — **7,931 km in 5.9 days**, averaging 56 km/h the whole way. 77 GPS fixes, one every ~1.8 h. |
| **Grey-headed albatross** (*Thalassarche chrysostoma*) | 89518 | One foraging trip from Campbell Island out across the antimeridian and back — **12,285 km over 21.9 days**, ending **2 km from where it began**. 5,959 GPS fixes, one every 5 min. |

### Turning it, and following

The globe starts holding one bird. Drag it and the camera lets go; **tap any
bird** — the followed one or any of the faint company — and the camera takes
that one instead, with a tap near it counting too, since a dot is a couple of
pixels and a fingertip is not. **Follow** re-attaches to the view's own bird.
Pinching to zoom deliberately does *not* let go: wanting a closer look at a bird
is not the same as wanting to stop watching it, and the two gestures are told
apart by whether the globe actually rotated between pointer-down and up.

### Scoring a journey

"Best" is not one thing. An albatross foraging trip is a loop that ends where it
began, so what makes it the good one is distance flown. A migration is the
opposite: scored on distance flown, the stork deposit's winner is a bird that
pottered about for a year — 78,932 fixes at 4.4 km/h. So storks are scored on
**displacement**, how far the bird actually got, over an autumn window.

The stork track is also thinned to one fix per 30 minutes; the read-out's
kilometres are measured along the drawn track, so they omit the thermal circling
that thinning removes (14,835 km against 17,598 at full resolution).

### The rest of the deposit

**Flock** adds every other bird that was reporting while the followed one was in
the air — on the **same clock**, not a shared start. Lining them up at minute
zero would invent a formation that never existed, so instead they appear and
vanish as their tags reported, and the read-out counts how many are audible at
that instant.

| | Others in the deposit | Aloft in the focal window | Typical number heard at once |
|---|---:|---:|---:|
| Hudsonian godwit | 11 | 3 | 1 of 3, and all three for stretches |
| Grey-headed albatross | 23 | 19 | 6, up to 10 |

They are short tails rather than full tracks, sampled coarser than the followed
bird. A companion is dropped whenever its last fix is further back than that
deposit's own cadence allows, so no line is ever drawn through a silence — and
that threshold is measured from the tags, not guessed. It has to be: the godwit
tags report roughly every two hours and the albatross tags every five minutes,
and one guessed threshold for both had 91% of ordinary godwit sampling looking
like silence, leaving those companions invisible for almost the entire flight.

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

### The eel

The fourth entry in the picker is the **European eel** (*Anguilla anguilla*),
and it is a **schematic**: a diagram that moves. It draws 900 particles, not
tracked animals, and the page says so in the picker, in a badge that never
leaves the screen, in the read-out and in the notes.

It has to be. The other three views draw recorded GPS fixes because those
recordings exist. For the eel they do not, and cannot with current tags:

- A European eel's life runs about **fifteen years and crosses the Atlantic
  twice**. A pop-up satellite tag lasts around a year and is far too large for
  anything but a full-grown silver eel, so no eel has been followed from
  hatching to spawning, and nothing smaller than an adult has been followed at
  all.
- A century after Johannes Schmidt named the Sargasso Sea as the breeding
  place, **no egg and no spawning adult has ever been recovered from it**. The
  spawning area is inferred from where the smallest larvae are caught.
- The larval drift has never been observed. It is reconstructed from larval
  surveys, ear-stone growth rings and particle-tracking models, and those three
  disagree by more than a year.

So `scripts/build_eels.py` keeps two kinds of number in separate, annotated
blocks, and the page keeps them separate too.

**Measured**, cited, and stated in the chapter text: the presumed breeding area
(24–31°N, 50–70°W, the box holding the smallest larvae); spawning beginning in
December and peaking in February; glass eels reaching Iberia in October and the
Baltic the following spring; silver eel escapement peaking between 10 August
and 20 December across twenty catchments; oceanic swimming at 3–47 km a day;
the daily vertical migration between 200 and 1,000 m through 0–11 °C; the
convergence of every tracked adult route on the Azores; a growth phase of 6–20
years; France's 55-tonne glass eel quota; Europol's 22 tonnes seized in one
season; and the recruitment collapse.

**Drawn**, and an estimate of nothing: the ocean corridor's path, which follows
the real current system — Gulf Stream, North Atlantic Current, Azores Current —
but comes from no current product; how the particles are shared between the 20
river systems, for which ICES publishes no geographic split; and how many dots
the fishery, the barriers and attrition remove. Those removals are placed where
those things happen. **Their number is not a mortality rate.**

Two shapes had to be corrected, because both were claims:

- **The breeding area is an ellipse, not a rectangle.** The cited figure is two
  corner coordinates, 31°N 50°W and 24°N 70°W, and the first version scattered
  eggs uniformly through the box between them. A rectangle asserts straight
  edges and square corners running true north and true east, which no survey
  has found; the larval surveys describe a long narrow band along the
  subtropical convergence front. The corners are now read as the ends of that
  band's axis, the eggs fill an ellipse around it, and the outline is drawn
  dashed because the edge is a sampling boundary, not a fence.
- **The coastal legs go by sea.** Joining the ocean corridor to each river
  mouth with a straight line put the eels over land: a straight line from the
  Azores Current to the Rhône crosses Spain and the Pyrenees. Measured against
  a land mask, **32 of the 40 coastal legs ran overland, the worst for
  1,100 km**. `scripts/route_eels.py` now computes them as shortest sea paths
  over terrarium elevation at zoom 5 (~3 km), flood-filled from the open
  Atlantic so that lakes at or below sea level cannot pass for ocean — one of
  them swallowed the first attempt at the Oslofjord. Douglas–Peucker
  simplification is land-aware: a chord is only taken if the sea allows it,
  which is what brought the worst overland run from 100 km to a single 20 km
  sample step where a line grazes a headland. Routes are committed as
  `scripts/eel_sea_routes.json`, so `build_eels.py` still downloads nothing.

  The measured detours survive the routing: Righton's Baltic and North Sea eels
  went north into the Norwegian Sea before turning west and the Mediterranean
  ones left through Gibraltar, so those are via points. A shortest path would
  have sent the Baltic eels down the Channel.

One thing on this view *is* a quantitative claim, and it is measured. The
**Today** button thins the swarm to 7.2%, where ICES's glass eel recruitment
index stood in 2024 against the 1960–79 mean for its "Elsewhere Europe" series;
the "North Sea" series is at 1.3%. The species is Critically Endangered, has
been on CITES Appendix II since March 2009, and the EU has run a zero export
quota since December 2010.

The drift duration is the one place the animation cannot stay neutral, because
the drift length and the arrival calendar are the same number seen twice.
February spawning plus an October landfall in Portugal and a spring landfall in
the Baltic only fit at roughly twenty to twenty-six months — the long reading.
The short reading, from ear-stone growth rings, needs eels to spawn all year
round, which the larval surveys do not show. The notes panel says this too.

Because a fifteen-year life cannot run at one rate, each of the eight chapters
declares its own — a tenth of a month per second in the estuaries, more than
eight in the growth years — and the read-out states the rate and the eel's real
age side by side. The build is seeded, so a given commit always produces the
same animation.

**The camera on this view is locked and follows the migration by itself.** It
points at the mean position of every drawn eel and stands back far enough to
hold the spread, so it tracks the swarm out of the Sargasso, across the
Atlantic, up the rivers and back without stage directions. The mean is taken
over unit vectors rather than over degrees — averaging degrees puts the centre
of a swarm straddling the antimeridian in the middle of Asia — and the standoff
comes from the 90th percentile of the spread rather than the maximum, so one
straggler mid-ocean does not pull the view back off Europe. The orbit controls
are switched off rather than overridden: leaving them on and snapping the
camera back each frame is a bug this page has already had once. The three bird
views still hand you their camera on a drag.

The descriptions sit in the bottom-left corner and fold. The chapter number,
its title and a one-line lead are always visible; the body is one click (or
<kbd>c</kbd>) away, and the choice sticks across chapters.

### Rendering

globe.gl (MIT, bundles three.js) over NASA's Blue Marble Next Generation, with a
global elevation map as a bump layer. All of it is checked into `vendor/` rather
than fetched from a CDN — see `vendor/README.md` for provenance and how to
refresh it — so the page works on a host that permits no outbound requests.

The camera eases toward the bird on a time constant rather than a fixed
fraction per frame, so the lag does not depend on the frame rate: measured 50 km
steady-state, 117 km worst case, on a software renderer.

The eel's swarm is drawn on a 2-D canvas over the globe rather than as globe.gl
points: 900 cylinders would be 900 meshes rebuilt every frame, and this way the
trails, the fading removals and the far-side culling are each a few lines of
arithmetic. Each dot's trail is recomputed from the clock rather than
remembered, so it stays correct when the scrubber jumps and when the globe is
turned by hand. Measured at 6 ms per frame for 900 particles on a software
renderer.

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
python3 scripts/route_eels.py           # -> scripts/eel_sea_routes.json; fetches 96 elevation tiles
python3 scripts/build_eels.py           # -> eel-migration.json, the schematic; downloads nothing
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

For the eel schematic — no deposit, because none exists; these are the papers
every measured figure on that view comes from:

Righton, D., Westerberg, H., Feunteun, E., et al. (2016). *Empirical
observations of the spawning migration of European eels: the long and dangerous
road to the Sargasso Sea.* Science Advances 2:e1501694.
`doi:10.1126/sciadv.1501694`

Wright, R. M., Piper, A. T., Aarestrup, K., et al. (2022). *First direct
evidence of adult European eels migrating to their breeding place in the
Sargasso Sea.* Scientific Reports 12:15362. `doi:10.1038/s41598-022-19248-8`

Schmidt, J. (1923). *The breeding places of the eel.* Philosophical
Transactions of the Royal Society B 211:179–208. `doi:10.1098/rstb.1923.0004`

ICES (2025). *European eel (Anguilla anguilla) throughout its natural range.*
ICES Advice: Recurrent Advice — the glass eel recruitment indices.

Europol (2025). *Operation LAKE* — 22 tonnes of glass eels seized in the
2024–25 season across 21 countries.

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
