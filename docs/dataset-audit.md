# Dryad deposit audit

Before any map gets built on a deposit, it has to answer one question: does it
hold **real fixes — coordinates *and* a timestamp — for predators as well as
prey**, or only the analysis tables that were derived from them?

The Okavango deposit ([doi:10.5061/dryad.w0vt4b8zr]) failed that test on the
predator side: it shipped herbivore coordinates but no lion or wild dog
positions, only their activity windows and a utilisation polygon. Four
candidate Dryad replacements were audited. **All four fail it too.** The
Movebank Data Repository, searched afterwards, answers it: section 5 below.

Reproduce with:

```sh
python3 scripts/fetch_dryad.py    --doi <DOI> --out data/raw/<slug>
python3 scripts/fetch_movebank.py --doi <DOI> --out data/raw/movebank
python3 scripts/fetch_movebank.py --search "predator prey"    # browse the archive
Rscript  scripts/profile_rdata.R  data/raw/<slug>/*.RData     # .RData / .RDS
python3  scripts/profile_tables.py data/raw/<slug>/*.csv      # .csv / .xlsx
```

| # | Deposit | Predator fixes | Prey fixes | Timestamps | Usable for a movement map |
|---|---------|----------------|------------|------------|---------------------------|
| 1 | [`63xsj3v81`] wolves + caribou, Québec | no | no | no | **No** — monthly summary table only |
| 2 | [`kh1893292`] eastern Washington, 5 species | coordinates removed | coordinates removed | season label only | **No** — depositors stripped the coordinates |
| 3 | [`51c59zwkg`] cougar + mule deer | no | coordinates removed | yes | **No** — depositors stripped the coordinates |
| 4 | [`4xgxd257z`] wolves, ambush sites | no | no | date only | **No** — attribute table, no geometry |
| 5 | [Movebank] Utah UDWR, cougars + 4 ungulates | **yes** | **yes** | **yes, 2 h** | **Yes** — verified below |

---

## 1. Michelot et al. 2023 — wolves and migratory caribou, Québec

[doi:10.5061/dryad.63xsj3v81] · CC0 · *Oikos* [10.1111/oik.10150]

The paper describes a ten-year GPS dataset of 59 wolves and 431 caribou at 1–5 h
fix intervals. **None of it is in the deposit.** The deposit is two files
totalling 142 KB: a README and `Table_S2_-_Final_data.xlsx`.

Byte-verified against `Table_S2_-_Final_data.xlsx`, a copy of which sits in this repository:

- Sheet `Final_data`: **765 rows × 26 columns**, one row per **wolf-month**.
  59 wolves (34 M / 25 F), 2011–2020, median 11 wolf-months per animal.
- Sheet `Keys`: the column definitions.
- **No coordinate column. No timestamp finer than `Year` + `Month`.**
- The 131,727 wolf fixes that went into the study survive only as the count
  `Nb_loc` and derived distances (`Dist_tot_month`, `Dist_day_mean`, …).
- **Caribou never appear as a track at all.** Their entire presence is four
  aggregate columns: `Carib_AU` (monthly area used, km²) and the wolf's mean /
  initial / final distance to the edge of that area.

Unlike Okavango there is no reconstruction route here. Okavango worked because
two tables held the *same* fixes under different sort orders, so the ordering
was invertible. Monthly means are lossy in one direction only — 74 fixes
averaged into `Dist_day_mean = 15.52` cannot be unaveraged.

## 2. Bassing et al. 2025 — eastern Washington, five species

[doi:10.5061/dryad.kh1893292] · CC0 · *Ecology* [10.1002/ecy.4448]

The only remaining candidate, and the one that fits the brief: >400 collared
animals, 2017–2021, in two study areas — cougar and wolf as predators, elk,
mule deer and white-tailed deer as prey — with hidden Markov models fitted to
the movement, which requires per-fix coordinates and timestamps upstream.

15 files, 610 MB. The movement data is six of them (~182 MB); the remaining
428 MB are landscape rasters:

| File | Size | What it is |
|------|------|-----------|
| `wolf_dat_all_for_pub.RData` | 4.0 MB | wolf locations |
| `coug_dat_all_for_pub.RData` | 14.6 MB | cougar locations |
| `wtd_dat_all_for_pub.RData` | 31.4 MB | white-tailed deer locations |
| `elk_dat_all_for_pub.RData` | 36.8 MB | elk locations |
| `md_dat_all_for_pub.RData` | 68.5 MB | mule deer locations |
| `crwOut_ALL_wCovs_for_pub.RData` | 26.5 MB | continuous-time random-walk output, all species, with covariates |
| `NE_/OK_covariates_30m.RData`, `*_grid_mask.tif`, `*_covariates_1km.RData` | 428 MB | RSF/HMM landscape layers for the two study areas — not animal data |

The 428 MB of landscape layers are worth more than their "not animal data"
row suggests. The Okavango deposit's largest documented gap is that *"the 25 m
habitat raster behind the original analysis was not deposited"* — which left
that map with a mixed-date satellite mosaic and no measured ground under the
animals at all. This deposit ships what that one withheld: land cover, terrain
and canopy structure at 30 m, over the real study areas, for roughly the study
period. The paper's RSFs are fitted from these rasters, so with the published
coefficients the predator utilisation surfaces are reconstructible too — the
Okavango range layers' equivalent, except here with real predator tracks to
draw *over* them rather than in place of them.

What argues against them is logistics rather than value: 428 MB raw, `.RData`
stacks that need R to open, a CRS and extent that have to line up with the
fixes, and two separate study areas — so two map extents, not one continuous
canvas. Any browser map would downsample them heavily in any case, and the
`*_covariates_1km.RData` pair is that aggregation already done, at 0.5 MB for
both. All of it waits on the fixes: rasters with nothing to put on them are
decoration.

**Verified, and it fails the same test as deposit 3.** The deposit's own README
says so three times, and the files bear it out:

> The coordinates of each observation are excluded due to sensitivity of the
> information.

Byte-verified against `wolf_dat_all_for_pub.RData` and
`coug_dat_all_for_pub.RData` (`docs/kh1893292-dryad-readme.md` holds the
deposit's README):

| | wolves | cougars |
|---|---|---|
| rows | 253,050 | 959,805 |
| of which real fixes (`Used == 1`) | 12,050 | 45,705 |
| individuals | 13 | 42 |
| coordinate columns | **none** | **none** |
| time columns | **none** | **none** |

What each row carries instead is the covariate values sampled at that location
— `Elev`, `Slope`, `RoadDen`, `Dist2Water`, `HumanMod`, `CanopyCover`,
`Dist2Edge`, `Landcover_type` — plus a `Season` label (`Summer18`,
`Winter1819`, …). That is the coarsest time signal of the four deposits: not a
date, not an hour, a six-level factor spanning three years. Most rows are not
even fixes: the RSF design samples 20 available points per used one, so 95% of
the table is random background.

`crwOut_ALL_wCovs_for_pub.RData` is documented as holding `time` (floored to
the hour), `step`, `angle` and `burst` per animal — but the README states the
coordinates are excluded there too. Step lengths and turning angles integrate
into a trajectory *shape*, at true scale and true timing, but with no origin
and no initial bearing it cannot be placed on the ground, and no two animals
can be placed relative to each other — which is exactly the predator-prey
geometry the map would exist to show.

The coordinates were withheld deliberately, to protect animals from being
located: they are available only to qualified researchers via the Wildlife
Chief Scientist of the Washington Department of Fish and Wildlife. Every fix
does carry a covariate signature, and the covariate rasters cover the whole
study area, so the withheld positions are in principle recoverable by matching
signatures against the grid. **That is not a route this project will take.**
Undoing a de-identification that exists to keep collared cougars and wolves
from being found is not a reconstruction problem, it is the harm the measure
was put there to prevent. The Okavango reconstruction was legitimate because
nothing there was withheld for safety — only a sort order had destroyed the
chronology.

The landscape data is a different matter and is genuinely usable:
`NE_covariates_1km.RData` holds 11,758 rows, one per 1 km pixel, with
elevation, slope, road density, distance to water, human modification, and
canopy cover / distance-to-edge / land cover in per-year versions (2018, 2019,
2020). Its `ID` is the raster grid index, so the accompanying `.tif` supplies
the georeference. Measured ground, properly placed — with nothing left to
draw on it.

## 3. Abernathy et al. 2025 — cougar, deer and human presence

[doi:10.5061/dryad.51c59zwkg] · CC0 · *Ecography* [10.1002/ecog.07626]

Ruled out on the depositors' own statement:

> To protect sensitive wildlife location information, all raw spatial
> coordinates have been removed or generalized. Derived environmental and
> behavioral metrics are retained for reuse.

What remains is per-fix rows with season, diel period, step length, turn angle
and extracted covariates — but no geometry to draw. The cougar side is worse:
there are no cougar fixes at any point, only a modelled encounter-risk surface,
which is the same shape of gap that disqualified Okavango. The human mobility
data is withheld under a redistribution ban.

## 4. Gable et al. 2020 — wolves choosing ambush sites

[doi:10.5061/dryad.4xgxd257z] · CC0 · *Behavioral Ecology* [10.1093/beheco/araa147]

Two CSVs, 57 KB total. The depositors publish the complete field list in the
Dryad usage notes, and it contains no coordinates:

- `AmbushingAttempts_Data_2015-2019.csv` — one row per ambush attempt: hunting
  attempt ID, wolf ID, up to three beaver features, feeding-trail length,
  distance from beaver activity, distance from water, min/max time at the
  ambush site, average wind bearing, whether the beaver would have smelled the
  wolf.
- `BeaverKillSiteData_BEHECO.csv` — one row per killed beaver: kill ID,
  `dateFound`, wolf ID, beaver feature.

The underlying 20-minute-interval wolf collar data — 11,817 GPS clusters — is
not deposited. `dateFound` is the date a carcass was found in the field, not a
fix time. Nothing here is mappable as movement.

---

## 5. Movebank Data Repository — the search that worked

Dryad is a general-purpose repository: what gets deposited there is whatever a
paper's reviewers needed. The [Movebank Data Repository] is a tracking archive,
and what gets deposited is the collar download — one row per fix, with
`location-long`, `location-lat` and `timestamp`, published under a DOI and an
open licence. Its DSpace API is open: no account, no licence click-through.

All 2,013 deposits were harvested and filtered for a predator taxon and a prey
taxon (`scripts/fetch_movebank.py --search`). Three deposits carry both guilds
in one file; several authors hold one of each. The best fit is a pair.

### Utah, 2019–2020 — cougars and four ungulates, both CC0

| | cougars | ungulates |
|---|---|---|
| DOI | [10.5441/001/1.712] | [10.5441/001/1.711] |
| licence | CC0 1.0 | CC0 1.0 |
| individuals | 40 | 2,694 |
| fixes | 47,777 | 4,916,617 |
| span | 2019-01-01 → 2020-05-16 | 2019-01-01 → 2020-05-16 |
| fix interval | median 2.00 h, 95% within 10% | median 2.00 h, 94% within 10% |
| missing coordinates | none | none |

Both deposits come from the same agency, on the same two-hour schedule, over
the *same* window to the day. The ungulate side is mule deer (3,234,515 fixes
/ 1,771 animals), bighorn (686,698 / 352), elk (610,062 / 349) and pronghorn
(385,342 / 222).

They also share ground. Binned to roughly 5 km cells, cougars and ungulates
share 275 cells; **80% of all cougar fixes fall in cells ungulates also used**,
and 34 of the 40 cougars overlap 627 individual ungulates — 423 mule deer, 195
elk. There are **2,168 cell-days on which a cougar and an ungulate were in the
same cell on the same day**.

That is the thing Okavango could only approximate. There, a ring round an
animal meant "this animal is sitting in the top decile of a predator's
*modelled range* while that predator's *activity window* is open" — exposure,
inferred. Here both animals are on the same calendar clock with real
positions, so a ring can mean a measured distance to a predator that was
actually there, at that hour.

### Also viable

- **Illinois white-tailed deer and predators** — [10.5441/001/1.649], one
  deposit, three species: white-tailed deer (111,126 fixes / 45), coyote
  (44,142 / 25), bobcat (13,055 / 9), 2019-02-23 → 2021-11-13. Mixed guilds in
  a single file, but the schedule is ragged (median 1.99 h, only 30% of gaps
  within 10% of it, 95th percentile 6 h) and CC BY-NC rather than CC0.
- **Utah coyote and puma** — [10.5441/001/1.7d8301h2], 18 animals, 198,705
  fixes, CC0. A second predator layer for the same state.
- **Hebblewhite Alberta–BC** — wolves ([10.5441/001/1.662], 68 animals,
  174,443 fixes, CC BY 4.0) alongside Ya Ha Tinda elk
  ([10.5441/001/1.5g4h5t6c], 175 animals, 1,585,456 fixes, CC0). A classic
  wolf–elk system, but the two deposits have to be checked for a common window
  before they can share a clock.

---

## What this leaves

**All four Dryad deposits fail; Movebank answers.** Of the Dryad four, three —
deposits 2, 3 and 4 — hold per-fix rows with covariates, behaviour metrics or
attributes but no geometry; deposit 1 holds monthly means. Two of them had
their coordinates removed deliberately, for animal safety, which is a decision
to respect rather than a problem to solve.

The pattern is worth naming, because it explains the whole search: **a deposit
carries what the analysis consumed.** Modern movement analyses — RSFs, HMMs,
step selection — consume *covariates extracted at locations*, not the
locations, so the coordinates drop out one step before publication. Okavango
was the exception only because its RSF tables kept the projected coordinates in
order to be reproducible. A tracking archive inverts this: there the deposit is
the collar download, and coordinates are the point rather than an intermediate.

The Utah pair changes what the map can be. The Okavango time model exists
entirely to work around a missing calendar — the de-interleaving, the per-collar
loop, the "day N of M" counter. All of it comes out. In its place: a real
calendar clock over sixteen months, predators as a second set of moving points
rather than a static surface, and rings that show measured distance instead of
range overlap.

[doi:10.5061/dryad.w0vt4b8zr]: https://doi.org/10.5061/dryad.w0vt4b8zr
[`63xsj3v81`]: https://doi.org/10.5061/dryad.63xsj3v81
[`kh1893292`]: https://doi.org/10.5061/dryad.kh1893292
[`51c59zwkg`]: https://doi.org/10.5061/dryad.51c59zwkg
[`4xgxd257z`]: https://doi.org/10.5061/dryad.4xgxd257z
[doi:10.5061/dryad.63xsj3v81]: https://doi.org/10.5061/dryad.63xsj3v81
[doi:10.5061/dryad.kh1893292]: https://doi.org/10.5061/dryad.kh1893292
[doi:10.5061/dryad.51c59zwkg]: https://doi.org/10.5061/dryad.51c59zwkg
[doi:10.5061/dryad.4xgxd257z]: https://doi.org/10.5061/dryad.4xgxd257z
[10.1111/oik.10150]: https://doi.org/10.1111/oik.10150
[10.1002/ecy.4448]: https://doi.org/10.1002/ecy.4448
[10.1002/ecog.07626]: https://doi.org/10.1002/ecog.07626
[10.1093/beheco/araa147]: https://doi.org/10.1093/beheco/araa147
[Movebank Data Repository]: https://datarepository.movebank.org/
[10.5441/001/1.712]: https://doi.org/10.5441/001/1.712
[10.5441/001/1.711]: https://doi.org/10.5441/001/1.711
[10.5441/001/1.649]: https://doi.org/10.5441/001/1.649
[10.5441/001/1.7d8301h2]: https://doi.org/10.5441/001/1.7d8301h2
[10.5441/001/1.662]: https://doi.org/10.5441/001/1.662
[10.5441/001/1.5g4h5t6c]: https://doi.org/10.5441/001/1.5g4h5t6c
