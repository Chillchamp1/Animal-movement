#!/usr/bin/env python3
"""Build the European eel life-cycle animation payload.

This script is different in kind from every other builder in this repository,
and the difference is the whole point of reading this header.

`build_globe.py`, `build_storks.py` and `build_tracks.py` all take a published
deposit of GPS fixes and thin it. Nothing in their output is invented. This one
invents its geometry, because for the European eel there is no equivalent
deposit and there cannot be:

  * No eel has ever been tracked through its whole life. The life cycle spans
    fifteen years and four oceans' worth of distance; a pop-up satellite tag
    lasts about a year and is far too large for anything but a full-grown
    silver eel.
  * No eel egg and no spawning adult has ever been recovered from the Sargasso
    Sea, a century after Johannes Schmidt proposed it as the breeding place.
    The spawning area is inferred from where the smallest larvae are caught.
  * The larval drift has never been observed. It is reconstructed from larval
    surveys, otolith microstructure and particle-tracking models, and those
    three disagree with each other by more than a year.

So what this file produces is a **schematic**: a drawn diagram that moves. The
page says so on its face, in the picker, in the read-out and in the notes, and
this script keeps the two kinds of number apart:

  MEASURED   values carry a citation in the comment beside them and appear in
             the page's text. Speeds, dates, depths, the spawning box, the
             recruitment collapse, the fishery quota.
  SCHEMATIC  values are geometry and staging -- how many dots, where the drawn
             corridor runs, how the dots are shared out between rivers. These
             are chosen to be *shaped* like the real thing and are never
             presented as estimates.

The one number the animation makes a quantitative claim about is the
recruitment collapse, and that one is measured: ICES's glass eel index, which
is why the page can offer a 1960s swarm and a present-day swarm side by side.

Sources are listed in SOURCES below and reproduced in the page's notes panel.

Usage:
    python3 scripts/build_eels.py [--out data/processed/eel-migration.json]
                                  [--particles 900] [--seed 20260827]
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

# --------------------------------------------------------------------------
# Sources. Every measured figure below cites one of these by key.
# --------------------------------------------------------------------------

SOURCES = [
    {
        "key": "righton2016",
        "text": ("Righton, D., Westerberg, H., Feunteun, E., et al. (2016). "
                 "Empirical observations of the spawning migration of European "
                 "eels: The long and dangerous road to the Sargasso Sea. "
                 "Science Advances 2:e1501694."),
        "doi": "10.1126/sciadv.1501694",
    },
    {
        "key": "wright2022",
        "text": ("Wright, R. M., Piper, A. T., Aarestrup, K., et al. (2022). "
                 "First direct evidence of adult European eels migrating to "
                 "their breeding place in the Sargasso Sea. "
                 "Scientific Reports 12:15362."),
        "doi": "10.1038/s41598-022-19248-8",
    },
    {
        "key": "ices2025",
        "text": ("ICES (2025). European eel (Anguilla anguilla) throughout its "
                 "natural range. ICES Advice: Recurrent Advice."),
        "doi": "",
    },
    {
        "key": "schmidt1923",
        "text": ("Schmidt, J. (1923). The breeding places of the eel. "
                 "Philosophical Transactions of the Royal Society B 211:179-208."),
        "doi": "10.1098/rstb.1923.0004",
    },
    {
        "key": "europol2025",
        "text": ("Europol (2025). Operation LAKE: 22 tonnes of glass eels "
                 "seized in the 2024-2025 season across 21 countries."),
        "doi": "",
    },
    {
        "key": "cites2009",
        "text": ("CITES (2009). Anguilla anguilla listed on Appendix II, "
                 "effective March 2009; EU zero-quota export policy from "
                 "3 December 2010."),
        "doi": "",
    },
]

# --------------------------------------------------------------------------
# MEASURED constants
# --------------------------------------------------------------------------

# The presumed breeding area, taken as the box containing the smallest
# (< 7 mm) leptocephali: 31 N 50 W to 24 N 70 W.  [wright2022, schmidt1923]
SPAWN_BOX = {"lat0": 24.0, "lat1": 31.0, "lon0": -70.0, "lon1": -50.0}

# Spawning begins in December, peaks in February, extends into May, from
# larval survey data.  [righton2016, wright2022]
SPAWN_PEAK_MONTH = 2          # February
SPAWN_FIRST_MONTH = 12        # December
SPAWN_LAST_MONTH = 5          # May

# Larval drift duration. This is the single most contested number in the eel
# literature: otolith microstructure gives under a year, cohort analysis and
# particle-tracking models give more than eighteen months.
#
# The animation cannot avoid taking a side, because the drift duration and the
# arrival calendar are the same number seen twice. Spawning peaks in February.
# Glass eels reach Portugal in October and the Baltic the following spring.
# Those two measured facts only fit together if the drift runs about twenty
# months for the earliest arrivals and twenty-six for the latest -- the long
# reading. The short reading requires spawning all year round, which the
# larval surveys do not show. So drift here is derived from each region's
# arrival month rather than drawn independently, the realised range is
# reported in the payload, and the chapter text says which way it leans.
DRIFT_MONTHS = (12.0, 24.0)         # the literature's disputed span
DRIFT_JITTER = 1.15                 # months, per particle

# Silver eel escapement from European catchments: peak between 10 August and
# 20 December, average Julian day 287 (14 October).  [righton2016]
ESCAPE_DAY_RANGE = (222, 354)
ESCAPE_DAY_MEAN = 287

# Oceanic migration speed of tagged silver eels, 3 to 47 km/day, mean 19.4.
# [righton2016]  Azores-released eels: 2.9 to 11.9 km/day, mean 6.8.
# [wright2022]
SPEED_KMD = (3.0, 47.0)

# Yellow-eel growth phase: 6-12 years in males, 9-20 years in females.
GROWTH_MONTHS = (72.0, 240.0)

# ICES glass eel recruitment as a percentage of the 1960-79 geometric mean,
# 2024 assessment: "North Sea" series 1.3%, "Elsewhere Europe" 7.2%.
# [ices2025]
RECRUIT_NOW = {"north_sea": 1.3, "elsewhere": 7.2}

# --------------------------------------------------------------------------
# SCHEMATIC geometry
#
# The corridor polylines below are hand-drawn to follow the real surface
# current system, because that is what carries the larvae and what the adults
# swim back against. They are not derived from a current product and no
# position on them is a measurement.
#
#   Gulf Stream      leaves the American coast at Cape Hatteras (~35 N 75 W)
#                    and runs north-east.
#   North Atlantic   continues north-east across the basin toward the
#   Current          European shelf near 50 N.
#   Azores Current   branches south-east around 35 N 45 W and runs east
#                    toward the Gulf of Cadiz.
#
# The two branches are why a glass eel reaches Portugal in October and the
# Baltic in spring.
# --------------------------------------------------------------------------

SPAWN_CENTRE = (27.5, -60.0)

# Common leg out of the spawning area and into the Gulf Stream.
TRUNK_COMMON = [
    (27.5, -60.0), (29.5, -65.0), (32.0, -71.0), (35.0, -74.5),
    (37.5, -70.0), (39.5, -64.0),
]

# Northern branch: North Atlantic Current toward the European shelf.
TRUNK_NORTH = [
    (41.0, -57.0), (43.5, -49.0), (46.0, -40.0), (48.5, -31.0),
    (50.5, -23.0), (51.0, -15.0),
]

# Southern branch: Azores Current toward Iberia and the Strait of Gibraltar.
TRUNK_SOUTH = [
    (38.5, -57.0), (36.5, -49.0), (35.0, -41.0), (34.5, -33.0),
    (35.0, -25.0), (36.0, -16.0), (36.5, -10.0),
]

# The Azores, where the tagged adults' routes converge on the way back.
# [righton2016]
AZORES = (38.5, -28.0)

# Return trunk, Azores to the spawning box, following the reverse of the
# subtropical gyre rather than a great circle.  [righton2016]
RETURN_TRUNK = [
    (38.5, -28.0), (36.5, -36.0), (34.0, -44.0), (31.0, -52.0),
    (28.5, -58.0), (27.5, -60.0),
]

# Shelf exits on the way back, by region group. Baltic and North Sea eels
# tracked in 2016 went north into the Norwegian Sea before turning west;
# Mediterranean eels went to the Strait of Gibraltar.  [righton2016]
EXIT_NORTH = [(58.0, 2.0), (62.0, 0.0), (62.0, -10.0), (56.0, -20.0)]
EXIT_WEST = [(48.0, -10.0), (44.0, -18.0)]
EXIT_GIBRALTAR = [(36.0, -5.6), (35.5, -9.0), (36.0, -14.0)]

# Recruitment destinations. Mouth coordinates are real; the river courses are
# simplified real courses, four to six points each, enough to read as the
# right river at globe scale and no more.
#
# `share` is a SCHEMATIC weighting. It is not an estimate of recruitment
# share -- ICES publishes no such geographic split -- but it is shaped by the
# one thing the indices do say, which is that recruitment in the south is
# several times that of the North Sea. `arrive` is the peak glass eel arrival
# month, which IS measured: immigration starts in October off Iberia, November
# off France, and runs progressively later north; the Mediterranean peaks in
# January; the Baltic is last.
REGIONS = [
    dict(key="sebou", label="Sebou", country="Morocco", group="south",
         share=0.045, arrive=11.5, mouth=(34.28, -6.67),
         river=[(34.28, -6.67), (34.26, -6.58), (34.16, -6.10), (34.10, -5.40)],
         note="North Africa is the southern edge of the range."),
    dict(key="guadalquivir", label="Guadalquivir", country="Spain", group="south",
         share=0.055, arrive=11.8, mouth=(36.79, -6.35),
         river=[(36.79, -6.35), (36.95, -6.35), (37.38, -6.00), (37.55, -5.35),
                (37.88, -4.78)],
         note="Tidal to Seville, ninety kilometres inland."),
    dict(key="tagus", label="Tagus", country="Portugal", group="south",
         share=0.055, arrive=10.8, mouth=(38.68, -9.32),
         river=[(38.68, -9.32), (38.80, -8.95), (39.00, -8.60), (39.35, -8.10),
                (39.55, -7.60)],
         note="Iberia is where the glass eels arrive first, from October."),
    dict(key="minho", label="Minho / Mino", country="Portugal / Spain", group="south",
         share=0.040, arrive=11.4, mouth=(41.86, -8.87),
         river=[(41.86, -8.87), (41.95, -8.65), (42.05, -8.35), (42.20, -7.90),
                (42.32, -7.60)],
         note="One of the longest-running glass eel counts in Europe."),
    dict(key="adour", label="Adour", country="France", group="biscay",
         share=0.075, arrive=12.4, mouth=(43.53, -1.51),
         river=[(43.53, -1.51), (43.50, -1.20), (43.50, -0.90), (43.55, -0.50),
                (43.62, -0.30)],
         note="Southern Bay of Biscay: the glass eel fishery peaks here in "
              "December and January."),
    dict(key="gironde", label="Gironde / Garonne", country="France", group="biscay",
         share=0.105, arrive=12.7, mouth=(45.58, -1.06),
         river=[(45.58, -1.06), (45.28, -0.75), (45.00, -0.60), (44.85, -0.57),
                (44.55, -0.10), (44.20, 0.60), (43.85, 1.05), (43.60, 1.44)],
         note="The largest glass eel fishery in Europe works this estuary."),
    dict(key="vilaine", label="Vilaine", country="France", group="biscay",
         share=0.045, arrive=13.0, mouth=(47.50, -2.49),
         river=[(47.50, -2.49), (47.52, -2.20), (47.55, -2.00), (47.70, -1.75)],
         note="A tidal barrage at Arzal, 8 km up, with an eel pass."),
    dict(key="loire", label="Loire", country="France", group="biscay",
         share=0.085, arrive=13.1, mouth=(47.28, -2.19),
         river=[(47.28, -2.19), (47.21, -1.90), (47.21, -1.55), (47.30, -0.55),
                (47.40, 0.69), (47.75, 1.35), (47.90, 1.90), (47.35, 2.85),
                (46.99, 3.16)],
         note="A thousand kilometres of river, and eels once reached the "
              "headwaters."),
    dict(key="shannon", label="Shannon", country="Ireland", group="isles",
         share=0.035, arrive=13.8, mouth=(52.60, -9.65),
         river=[(52.60, -9.65), (52.62, -9.20), (52.66, -8.63), (53.00, -8.30),
                (53.40, -8.00), (53.70, -7.95)],
         note="Ardnacrusha's turbines sit on the way back down."),
    dict(key="severn", label="Severn", country="United Kingdom", group="isles",
         share=0.045, arrive=13.9, mouth=(51.50, -3.00),
         river=[(51.50, -3.00), (51.60, -2.65), (51.75, -2.45), (52.10, -2.22),
                (52.40, -2.30), (52.71, -2.75)],
         note="The Severn elver fishery is the last large one in Britain."),
    dict(key="thames", label="Thames", country="United Kingdom", group="isles",
         share=0.030, arrive=14.2, mouth=(51.47, 0.75),
         river=[(51.47, 0.75), (51.46, 0.35), (51.50, 0.00), (51.48, -0.55),
                (51.55, -0.90), (51.70, -1.28)],
         note="Elvers are counted at Tilbury each spring."),
    dict(key="rhine", label="Rhine / Meuse", country="Netherlands / Germany", group="northsea",
         share=0.085, arrive=14.4, mouth=(51.98, 4.10),
         river=[(51.98, 4.10), (51.90, 4.90), (51.85, 5.85), (51.55, 6.30),
                (51.20, 6.80), (50.75, 7.15), (50.05, 8.30), (49.00, 8.35),
                (48.58, 7.78), (47.55, 7.59)],
         note="From the North Sea to Basel is 800 river kilometres and more "
              "than ten weirs."),
    dict(key="elbe", label="Elbe", country="Germany", group="northsea",
         share=0.055, arrive=14.7, mouth=(53.87, 8.70),
         river=[(53.87, 8.70), (53.75, 9.40), (53.55, 9.99), (53.20, 10.75),
                (52.85, 11.90), (52.20, 12.35), (51.87, 12.65)],
         note="Restocked with glass eels bought from the Atlantic fishery."),
    dict(key="oder", label="Oder", country="Poland / Germany", group="baltic",
         share=0.030, arrive=16.0, mouth=(53.92, 14.25),
         river=[(53.92, 14.25), (53.65, 14.45), (53.43, 14.55), (52.90, 14.65),
                (52.35, 14.55)],
         note="The Baltic is the far end of the drift."),
    dict(key="vistula", label="Vistula", country="Poland", group="baltic",
         share=0.030, arrive=16.4, mouth=(54.35, 18.95),
         river=[(54.35, 18.95), (53.90, 18.80), (53.50, 18.75), (52.90, 19.10),
                (52.55, 19.70), (52.25, 21.02)],
         note="Arrives in spring, a year and a half after Portugal."),
    dict(key="glomma", label="Glomma", country="Norway", group="baltic",
         share=0.020, arrive=16.8, mouth=(59.20, 10.95),
         river=[(59.20, 10.95), (59.45, 11.10), (59.90, 11.25), (60.45, 11.40)],
         note="The northern limit of any numbers worth counting."),
    dict(key="rhone", label="Rhone / Camargue", country="France", group="med",
         share=0.055, arrive=13.0, mouth=(43.33, 4.85),
         river=[(43.33, 4.85), (43.50, 4.70), (43.68, 4.62), (44.00, 4.80),
                (44.60, 4.78), (45.20, 4.82), (45.76, 4.84)],
         note="The Camargue lagoons are the biggest Mediterranean nursery."),
    dict(key="ebro", label="Ebro", country="Spain", group="med",
         share=0.040, arrive=12.9, mouth=(40.72, 0.86),
         river=[(40.72, 0.86), (40.82, 0.72), (41.02, 0.55), (41.20, 0.30),
                (41.35, -0.20), (41.65, -0.88)],
         note="Three large dams below Zaragoza now stop the ascent."),
    dict(key="po", label="Po", country="Italy", group="med",
         share=0.045, arrive=13.2, mouth=(44.95, 12.50),
         river=[(44.95, 12.50), (44.98, 12.10), (45.03, 11.60), (45.08, 10.90),
                (45.13, 10.30), (45.10, 9.70)],
         note="Comacchio's lagoons ran an eel fishery for two thousand years."),
    dict(key="ichkeul", label="Ichkeul", country="Tunisia", group="med",
         share=0.025, arrive=12.6, mouth=(37.20, 9.90),
         river=[(37.20, 9.90), (37.18, 9.80), (37.16, 9.68), (37.14, 9.58)],
         note="A shallow North African lake, fed by a sea channel."),
]

EXITS = {
    "south": EXIT_WEST, "biscay": EXIT_WEST, "isles": EXIT_WEST,
    "northsea": EXIT_NORTH, "baltic": EXIT_NORTH, "med": EXIT_GIBRALTAR,
}

# Where each region's larvae leave the trunk. Southern groups ride the Azores
# Current; everything from the Channel north rides the North Atlantic Current.
BRANCH = {
    "south": "south", "med": "south", "biscay": "south",
    "isles": "north", "northsea": "north", "baltic": "north",
}

# --------------------------------------------------------------------------
# Phases: what the camera looks at, what the text says, and how much real time
# each screen second is worth. The compression is stated on screen, because a
# fifteen-year life cannot be shown at one rate and pretending otherwise is
# how the stork view ended up looking broken.
# --------------------------------------------------------------------------

PHASES = [
    dict(key="spawn", title="Nobody has ever seen it happen",
         m0=0.0, m1=3.0, seconds=10.0, stage="egg",
         cam=dict(lat=27.5, lng=-58.0, alt=1.55),
         lead="The Sargasso Sea, February.",
         body=[
             "Every European eel alive was born somewhere in this box: 24&ndash;31&deg;N, "
             "50&ndash;70&deg;W, a patch of the western Atlantic with no coast and no "
             "bottom in reach. Johannes Schmidt worked it out in 1923 by trawling "
             "the whole ocean for larvae and following the small ones home.",
             "A hundred years on, <strong>no egg and no spawning adult has ever been "
             "recovered there</strong>. The spawning season is read off larval "
             "surveys: it begins in December, peaks in February, and runs into May.",
         ]),
    dict(key="drift", title="The drift",
         m0=3.0, m1=20.0, seconds=21.0, stage="lepto",
         cam=dict(lat=40.0, lng=-45.0, alt=1.75),
         lead="Five thousand kilometres, on the current.",
         body=[
             "The larva is a leptocephalus: flat, transparent, shaped like a willow "
             "leaf, and a poor swimmer. It does not cross the Atlantic so much as "
             "get carried &mdash; into the Gulf Stream off Cape Hatteras, then "
             "north-east on the North Atlantic Current, with a southern arm peeling "
             "off toward Iberia.",
             "How long this takes is <strong>the biggest open argument in eel "
             "biology</strong>. Growth rings in the ear-stones say under a year; "
             "cohort analysis and drift models say more than eighteen months.",
             "This animation cannot dodge the question, because the drift length "
             "and the arrival calendar are one number seen twice. Spawning peaks "
             "in February; glass eels reach Portugal in October and the Baltic "
             "the following spring. Those only fit together at <strong>about "
             "twenty months for the first arrivals and twenty-six for the "
             "last</strong> &mdash; the long reading. The short one needs eels "
             "to spawn all year round, and the larval surveys do not show that.",
         ]),
    dict(key="landfall", title="Glass eels",
         m0=20.0, m1=27.0, seconds=14.0, stage="glass",
         cam=dict(lat=45.0, lng=-11.0, alt=1.15),
         lead="October to June, south to north.",
         body=[
             "On the continental shelf the leaf shrinks and becomes an eel: 7 cm "
             "long, weighing a third of a gram, and completely transparent. Now it "
             "swims, and it uses the tide to do it &mdash; riding the flood upriver "
             "and holding on the ebb.",
             "Landfall runs on a calendar you can read off the map. Immigration "
             "starts in <strong>October off Portugal and Spain</strong>, November "
             "off France, and works progressively north; the Mediterranean peaks in "
             "January; the Baltic is last, in spring. A glass eel reaching the "
             "Vistula in May and one reaching the Tagus the previous October "
             "were spawned in the same weeks &mdash; what differs is how long "
             "the current took to deliver them.",
         ]),
    dict(key="fishery", title="The estuaries",
         m0=27.0, m1=31.0, seconds=13.0, stage="glass",
         cam=dict(lat=45.0, lng=-4.0, alt=0.92),
         lead="Where the journey meets a net.",
         body=[
             "The glass eel fishery is a winter fishery of the Bay of Biscay and "
             "Iberia &mdash; the Gironde, the Adour, the Loire, the Vilaine, the "
             "Minho. France's quota for the 2025&ndash;26 season is "
             "<strong>55&nbsp;tonnes</strong>. A kilogram is roughly 3,000 "
             "individual eels.",
             "Alongside it runs one of the largest wildlife crimes in Europe. "
             "Glass eels are flown to farms in East Asia, where a kilogram has "
             "reached &euro;6,000. Europol's Operation LAKE seized "
             "<strong>22 tonnes</strong> in the 2024&ndash;25 season alone, across "
             "21 countries.",
             "<em>The dots removed here mark where the fishery sits in the "
             "journey. Their number is not an exploitation rate &mdash; no such "
             "figure is drawn from this animation.</em>",
         ]),
    dict(key="rivers", title="Up the rivers",
         m0=31.0, m1=37.0, seconds=12.0, stage="elver",
         cam=dict(lat=48.0, lng=4.0, alt=0.86),
         lead="Pigmented now, and climbing.",
         body=[
             "The glass eel darkens into an elver and starts inland. Eels are "
             "extraordinary at this: they climb wet walls, wriggle through grass, "
             "and have been recorded ascending vertical weirs. The Rhine takes them "
             "800 river kilometres to Basel; the Loire once carried them to its "
             "headwaters; the Ebro to Zaragoza.",
             "Most of that is now blocked. Weirs, hydropower intakes, sluices and "
             "pumping stations divide almost every European catchment, and the same "
             "structures kill the adults on the way back down through the turbines. "
             "The dots that stop short here are stopping at real barriers.",
         ]),
    dict(key="growth", title="The yellow years",
         m0=37.0, m1=165.0, seconds=15.0, stage="yellow",
         cam=dict(lat=49.0, lng=6.0, alt=1.05),
         lead="Six to twenty years, in one stretch of water.",
         body=[
             "As a yellow eel it stays put, often in a few hundred metres of river "
             "or a single lake, hunting at night. This is the long middle of the "
             "life and it is why the animation has to compress: males spend about "
             "6 to 12 years here, females 9 to 20, and some far longer.",
             "Sex is not fixed at birth. It is settled during these years, and "
             "crowding pushes the balance toward males &mdash; so a population's "
             "own density helps decide how many egg-carrying females it will "
             "eventually send back to the Atlantic.",
         ]),
    dict(key="escape", title="Silver eels leave",
         m0=165.0, m1=170.0, seconds=10.0, stage="silver",
         cam=dict(lat=50.0, lng=0.0, alt=1.15),
         lead="An autumn night, on a rising river.",
         body=[
             "The eel remakes itself for the ocean: the eyes roughly double in "
             "area, the flanks turn silver-and-bronze, the gut shuts down. It will "
             "not feed again. Then it goes, usually on a dark night with the river "
             "in flood.",
             "Across twenty European catchments the peak of this run falls between "
             "<strong>10 August and 20 December</strong>, averaging 14 October. The "
             "same nights, the same rivers, and the turbines are still turning.",
         ]),
    dict(key="ret", title="The road back",
         m0=170.0, m1=190.0, seconds=19.0, stage="silver",
         cam=dict(lat=38.0, lng=-38.0, alt=1.8),
         lead="Five to ten thousand kilometres, without eating.",
         body=[
             "Of 707 eels tagged from four European regions, 87 got far enough out "
             "to reconstruct a route. Whether they left Sweden, Ireland, France or "
             "the western Mediterranean, <strong>the routes converge on the "
             "Azores</strong>. Baltic eels went north into the Norwegian Sea first; "
             "Mediterranean eels went out through Gibraltar.",
             "Every one of them rose and sank with the day &mdash; deep by daylight, "
             "shallower at night, working between about 200 and 1,000 m and a daily "
             "temperature swing from 0 to 11&nbsp;&deg;C.",
             "They travelled at 3 to 47 km a day, averaging 19. That is too slow "
             "for the spring after they left, which upends a century-old "
             "assumption: an eel leaving Europe this autumn is mostly not spawning "
             "next spring but the one after. In 2022 satellite tags from the Azores "
             "finally reached the breeding area itself &mdash; the first direct "
             "evidence, a hundred years after Schmidt.",
         ]),
]

FATE_THROUGH, FATE_FISHED, FATE_BARRIER, FATE_LOST = 0, 1, 2, 3


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def resample(pts: list[tuple[float, float]], n: int) -> list[list[float]]:
    """Even-arc-length resample of a polyline, so a dot moving at constant
    parameter moves at roughly constant speed rather than sprinting through
    the leg with the fewest control points."""
    if len(pts) < 2:
        return [[round(pts[0][0], 4), round(pts[0][1], 4)]] * n
    seg = []
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], (b[1] - a[1]) * math.cos(math.radians((a[0] + b[0]) / 2)))
        seg.append(d)
        total += d
    out = []
    for i in range(n):
        want = total * i / (n - 1)
        acc = 0.0
        for j, d in enumerate(seg):
            if acc + d >= want or j == len(seg) - 1:
                f = (want - acc) / d if d > 0 else 0.0
                f = min(1.0, max(0.0, f))
                a, b = pts[j], pts[j + 1]
                out.append([round(a[0] + (b[0] - a[0]) * f, 4),
                            round(a[1] + (b[1] - a[1]) * f, 4)])
                break
            acc += d
    return out


def truncated_normal(rng: random.Random, lo: float, hi: float,
                     mu: float, sigma: float) -> float:
    for _ in range(24):
        v = rng.gauss(mu, sigma)
        if lo <= v <= hi:
            return v
    return min(hi, max(lo, mu))


def build_routes() -> dict:
    """The drawn corridor, resampled so the page can walk it by parameter."""
    north = TRUNK_COMMON + TRUNK_NORTH
    south = TRUNK_COMMON + TRUNK_SOUTH
    return {
        "north": resample(north, 60),
        "south": resample(south, 60),
        "back": resample(RETURN_TRUNK, 40),
    }


def build_regions() -> list[dict]:
    out = []
    total = sum(r["share"] for r in REGIONS)
    for r in REGIONS:
        trunk = BRANCH[r["group"]]
        tail = TRUNK_NORTH[-1] if trunk == "north" else TRUNK_SOUTH[-1]
        approach = resample([tail, r["mouth"]], 12)
        river = resample(r["river"], 28)
        back = resample([tuple(r["mouth"])] + EXITS[r["group"]] + [AZORES], 30)
        out.append({
            "key": r["key"], "label": r["label"], "country": r["country"],
            "group": r["group"], "trunk": trunk,
            "share": round(r["share"] / total, 5),
            "arrive": r["arrive"], "note": r["note"],
            "mouth": [round(r["mouth"][0], 4), round(r["mouth"][1], 4)],
            "approach": approach, "river": river, "back": back,
        })
    return out


def build_particles(regions: list[dict], n: int, rng: random.Random) -> list[list]:
    """One record per drawn eel. Every field is a schedule, not a position:
    the page computes where a dot is from these numbers and the polylines
    above, which keeps the payload small and scrubbing exact."""
    weights = [r["share"] for r in regions]
    out = []
    for _ in range(n):
        ri = rng.choices(range(len(regions)), weights=weights, k=1)[0]
        reg = regions[ri]

        # Hatching spread over the spawning season, peaked on February.
        hatch = truncated_normal(rng, 0.0, 3.2, 0.9, 0.7)

        # Drift duration, derived from where this particle is going. `arrive`
        # is the region's peak glass eel month counted from January of the year
        # after spawning (10.8 = late October, 16.4 = late April), so
        # `arrive - SPAWN_PEAK_MONTH + 12` is the drift that lands it there. A
        # larva spawned late in the season gets less of it: the season is a
        # funnel and they arrive together regardless.
        target = reg["arrive"] - SPAWN_PEAK_MONTH + 12.0
        drift = max(11.0, target - hatch + rng.gauss(0.0, DRIFT_JITTER))

        linger = truncated_normal(rng, 0.6, 4.0, 1.7, 0.8)   # in the estuary
        ascent = truncated_normal(rng, 1.0, 6.0, 2.6, 1.1)   # climbing inland
        growth = truncated_normal(rng, GROWTH_MONTHS[0], GROWTH_MONTHS[1],
                                  128.0, 34.0)
        descent = truncated_normal(rng, 0.4, 1.6, 0.8, 0.3)  # back down
        ret = truncated_normal(rng, 6.0, 26.0, 15.0, 4.5)    # ocean crossing

        # How far up the catchment it settles. Most eels stop low down; a few
        # go the whole way. Barriers cut the tail off this distribution, which
        # is the point the rivers phase makes.
        up = min(1.0, max(0.06, rng.betavariate(1.5, 2.4)))

        # Fate. Fishing is placed where the fishery is -- the Biscay and
        # Iberian estuaries -- and barrier losses where the catchments are
        # most fragmented. These are positional, not rates.
        fate = FATE_THROUGH
        roll = rng.random()
        fished_p = {"biscay": 0.30, "south": 0.22, "med": 0.06,
                    "isles": 0.08, "northsea": 0.03, "baltic": 0.01}[reg["group"]]
        barrier_p = {"biscay": 0.16, "south": 0.14, "med": 0.24,
                     "isles": 0.13, "northsea": 0.22, "baltic": 0.15}[reg["group"]]
        if roll < fished_p:
            fate = FATE_FISHED
        elif roll < fished_p + barrier_p:
            fate = FATE_BARRIER
        elif roll < fished_p + barrier_p + 0.10:
            fate = FATE_LOST

        out.append([
            ri,
            round(hatch, 2), round(drift, 2), round(linger, 2), round(ascent, 2),
            round(growth, 1), round(descent, 2), round(ret, 2),
            round(up, 3), fate,
            round(rng.uniform(-1, 1), 3), round(rng.uniform(-1, 1), 3),
            round(rng.random(), 3),
        ])
    return out


def time_phases(particles: list[list], phases: list[dict]) -> None:
    """Set each chapter's start and end from the schedules actually drawn.

    Hand-picked boundaries were the first attempt and they were wrong in a way
    the page's own stage key made obvious: at the top of the "Glass eels"
    chapter the swarm was already 442 yellow eels sitting in rivers against 78
    glass eels, because the chapter had been placed most of a year behind the
    median particle. Reading the boundaries off the particle distribution
    instead keeps each chapter's own stage the dominant one on screen, while
    leaving the spread -- which is the disputed drift duration, and is the
    point -- entirely alone.
    """
    def q(vals, p):
        v = sorted(vals)
        return v[min(len(v) - 1, int(p * len(v)))]

    tA, tL, tR, tE, tM, tS = [], [], [], [], [], []
    for (_ri, hatch, drift, linger, ascent, growth,
         descent, ret, _up, _f, _jx, _jy, _sd) in particles:
        a = hatch + drift
        l = a + linger
        r = l + ascent
        e = r + growth
        m = e + descent
        tA.append(a); tL.append(l); tR.append(r)
        tE.append(e); tM.append(m); tS.append(m + ret)

    a50, l50, r50, e50 = q(tA, 0.5), q(tL, 0.5), q(tR, 0.5), q(tE, 0.5)
    # The estuary window is shared: arriving and being fished happen in the
    # same water, so landfall takes the first part of it and the fishery the
    # rest, and the ascent gets a chapter of its own rather than being folded
    # in with them. Without that split the "Up the rivers" chapter opened on
    # 675 yellow eels already settled and 84 elvers still climbing.
    estuary = max(0.4, l50 - a50)
    edges = {
        "spawn":    (0.0,        q(tA, 0.10) * 0.30),
        "drift":    (q(tA, 0.10) * 0.30, a50),
        "landfall": (a50,        a50 + estuary * 0.45),
        "fishery":  (a50 + estuary * 0.45, l50),
        "rivers":   (l50,        r50),
        "growth":   (r50,        e50),
        "escape":   (e50,        q(tM, 0.55)),
        "ret":      (q(tM, 0.55), q(tS, 0.80)),
    }
    for p in phases:
        p["m0"], p["m1"] = (round(v, 2) for v in edges[p["key"]])


def build_callouts() -> list[dict]:
    """Labels pinned to real places, shown while their phase is running."""
    return [
        dict(phase="spawn", lat=27.5, lng=-60.0, title="Presumed breeding area",
             text="24&ndash;31&deg;N, 50&ndash;70&deg;W"),
        dict(phase="drift", lat=35.0, lng=-74.5, title="Cape Hatteras",
             text="the Gulf Stream leaves the coast"),
        dict(phase="drift", lat=34.5, lng=-33.0, title="Azores Current",
             text="the southern arm, toward Iberia"),
        dict(phase="landfall", lat=38.68, lng=-9.32, title="Tagus",
             text="first arrivals, October"),
        dict(phase="landfall", lat=54.35, lng=18.95, title="Vistula",
             text="last arrivals, spring"),
        dict(phase="fishery", lat=45.58, lng=-1.06, title="Gironde",
             text="Europe's largest glass eel fishery"),
        dict(phase="fishery", lat=43.53, lng=-1.51, title="Adour",
             text="peak season December&ndash;January"),
        dict(phase="rivers", lat=47.55, lng=7.59, title="Basel",
             text="800 river km from the North Sea"),
        dict(phase="rivers", lat=41.65, lng=-0.88, title="Zaragoza",
             text="the Ebro, dammed below here"),
        dict(phase="escape", lat=52.66, lng=-8.63, title="Ardnacrusha",
             text="turbines on the Shannon"),
        dict(phase="ret", lat=38.5, lng=-28.0, title="The Azores",
             text="where every tracked route converges"),
        dict(phase="ret", lat=35.95, lng=-5.6, title="Gibraltar",
             text="the Mediterranean exit"),
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/processed/eel-migration.json")
    ap.add_argument("--particles", type=int, default=900)
    ap.add_argument("--seed", type=int, default=20260827)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    regions = build_regions()
    particles = build_particles(regions, args.particles, rng)
    time_phases(particles, PHASES)

    counts = {}
    for p in particles:
        counts[p[9]] = counts.get(p[9], 0) + 1

    payload = {
        "kind": "schematic",
        "key": "eel",
        "label": "European eel",
        "scientific": "Anguilla anguilla",
        "status": "Critically Endangered (IUCN)",
        "seed": args.seed,
        "spawnBox": SPAWN_BOX,
        "azores": [AZORES[0], AZORES[1]],
        "routes": build_routes(),
        "regions": regions,
        "particles": particles,
        "phases": PHASES,
        "callouts": build_callouts(),
        "recruitNow": RECRUIT_NOW,
        "measured": {
            "speedKmd": SPEED_KMD,
            "driftMonths": DRIFT_MONTHS,
            "driftDrawn": [round(min(p[2] for p in particles), 1),
                           round(max(p[2] for p in particles), 1)],
            "growthMonths": GROWTH_MONTHS,
            "escapeDayRange": ESCAPE_DAY_RANGE,
            "escapeDayMean": ESCAPE_DAY_MEAN,
            "spawnMonths": [SPAWN_FIRST_MONTH, SPAWN_PEAK_MONTH, SPAWN_LAST_MONTH],
            "depthM": [200, 1000],
            "tempC": [0, 11],
            "tagged": {"righton": 707, "reconstructed": 87, "azores": 26},
            "distanceKm": [5000, 10000],
        },
        "sources": SOURCES,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, separators=(",", ":")))

    total_months = PHASES[-1]["m1"]
    secs = sum(p["seconds"] for p in PHASES)
    print(f"regions   {len(regions)}")
    print(f"particles {len(particles)}  "
          f"through {counts.get(0,0)}  fished {counts.get(1,0)}  "
          f"barrier {counts.get(2,0)}  lost {counts.get(3,0)}")
    print(f"timeline  {total_months:.0f} months ({total_months/12:.1f} years) "
          f"in {secs:.0f} s over {len(PHASES)} phases")
    for p in PHASES:
        print(f"  {p['key']:<9} {p['m0']:7.1f} -> {p['m1']:7.1f} mo  {p['seconds']:4.0f} s"
              f"  {(p['m1']-p['m0'])/p['seconds']:6.2f} mo/s")
    print(f"-> {out}  ({out.stat().st_size/1024:.0f} kB)")


if __name__ == "__main__":
    main()
