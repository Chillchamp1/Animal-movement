# Dryad deposit audit

Before any map gets built on a deposit, it has to answer one question: does it
hold **real fixes — coordinates *and* a timestamp — for predators as well as
prey**, or only the analysis tables that were derived from them?

The Okavango deposit ([doi:10.5061/dryad.w0vt4b8zr]) failed that test on the
predator side: it shipped herbivore coordinates but no lion or wild dog
positions, only their activity windows and a utilisation polygon. Four
candidate replacements were audited. This is what they contain.

Reproduce with:

```sh
python3 scripts/fetch_dryad.py --doi <DOI> --out data/raw/<slug>
Rscript  scripts/profile_rdata.R  data/raw/<slug>/*.RData     # .RData / .RDS
python3  scripts/profile_tables.py data/raw/<slug>/*.csv      # .csv / .xlsx
```

| # | Deposit | Predator fixes | Prey fixes | Timestamps | Usable for a movement map |
|---|---------|----------------|------------|------------|---------------------------|
| 1 | [`63xsj3v81`] wolves + caribou, Québec | no | no | no | **No** — monthly summary table only |
| 2 | [`kh1893292`] eastern Washington, 5 species | unverified | unverified | unverified | **Pending** — download blocked, see below |
| 3 | [`51c59zwkg`] cougar + mule deer | no | coordinates removed | yes | **No** — depositors stripped the coordinates |
| 4 | [`4xgxd257z`] wolves, ambush sites | no | no | date only | **No** — attribute table, no geometry |

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

**Status: unverified.** Dryad now gates every download route — the API path
returns `401 Unauthorized, must have current bearer token`, and the web path
sits behind an Anubis proof-of-work interstitial. The file names and sizes
above come from the Dryad API, which still serves metadata freely; the
*contents* have not been inspected, and deposit 3 below is the standing
reminder that plausible file names are not evidence.

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

## What this leaves

Deposit 2 is the only one that can carry a predator-and-prey movement map, and
it is unverified. The cheapest thing that settles it is the two predator files
— `wolf_dat_all_for_pub.RData` (4.0 MB) and `coug_dat_all_for_pub.RData`
(14.6 MB). Predator positions are precisely what Okavango lacked, so if those
two carry coordinates and timestamps the question is answered and the three
larger prey files can follow; adding the two 1 km covariate files (0.5 MB)
settles at the same time what the landscape stack actually contains, rather
than inferring it from file names.

If it turns out to hold coordinates and timestamps for all
five species, the map's time model has to change: these are real calendar
dates, so the de-interleaving, the per-collar day loop and the "day N of M"
counter all come out and are replaced by a calendar clock, predators become a
second set of moving points, and the proximity rings can show measured distance
instead of range overlap.

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
