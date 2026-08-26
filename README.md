# Data from: Predator-prey space-use and landscape features influence movement behaviors in a large-mammal community

[https://doi.org/10.5061/dryad.kh1893292](https://doi.org/10.5061/dryad.kh1893292)

**Recommended citation for this dataset:**

Bassing, S. B., L. Satterfield, T. R. Ganz, M. DeVivo, B. N. Kertson, T. Roussin, A. J. Wirsing, and B. Gardner. 2024. Data for: Predator-prey interactions and landscape features influence movement behaviors in a large-mammal community. Dryad, Dataset. [https://doi.org/10.5061/dryad.kh1893292](https://doi.org/10.5061/dryad.kh1893292)

## Description of the data and file structure

This repository contains movement data from collected from GPS-collared elk, mule deer, white-tailed deer, cougars, and wolves in eastern Washington, USA, from 2017 - 2021. The provided data are formatted for conducting resource selection function (RSF) analyses and hidden Markov models (HMM) for movement analysis. Formatted data are provided for several stages of the analysis.

**Date of data collection:** 2017-01-01 to 2021-03-31

**Geographic location of data collection:** Northeast study area centered around Chewelah, Washington, USA (117.7193° W, 48.28302° N); Okanogan study area centered around Winthrop, Washington, USA (120.1096° W, 48.42966° N)

**Information about funding sources that supported the collection of the data:** Funding was provided by the Washington Department of Fish and Wildlife, the Washington State Legislature, Federal Aid in Wildlife Restoration Grant no. F16AF00910, WDFW Aquatic Lands Enhancement Accounts, Seattle City Light Wildlife Research Grant no. 2015-04, NASA FINESST grant 80NSSC19K1334, and National Geographic grant EC-51129R-19.

## Data & File Overview

**Use-Available Data:** Contains species and season-specific "used" and "available" data included in resource selection function (RSF) analyses. GPS-collar relocation data from each collared animal were classified as "used" locations and used to define the region within a study area that was "available" to it (i.e., its seasonal home-range). A ratio of 1:20 used:available locations were randomly sampled within this spatial extent. "Used" locations were labeled (1) and "available" locations were labeled (0). Covariate data were extracted at each used and available location and included here with its used or available classification. The coordinates of each observation are excluded due to sensitivity of the information. Contact information for complete data provided below. Files are RData files that can be read into R with the load() function. Start of file names relate to each species (coug = cougar, elk = elk, md = mule deer, wtd = white-tailed deer, wolf = wolf).

*Files included:*

1. coug_dat_all_for_pub.RData
2. elk_dat_all_for_pub.RData
3. md_dat_all_for_pub.RData
4. wtd_dat_all_for_pub.RData
5. wolf_dat_all_for_pub.RData

*Data description:*

* ID: Individual animal identification number
* Season: Indicates season and year when each observation was made (Summer18 = summer 2018; Winter1819 = winter 2018-2019; 			Summer19 = summer 2019; Winter1920 = winter 2019-2020, Summer20 = summer 2020; Winter2021 = winter 2020-2021)
* Year (Year1, Year2, Year3): Year of study each observation was made (Year1 = 2018-2019; Year2 = 2019-2020; Year3 = 2020-2021).
* Elev: Elevation (m) of observation location
* Slope: Slope (degrees) of terrain at observation location
* RoadDen: Total road length/1 km-sq at observation location
* Dist2Water: Distance (m) to nearest water
* HumanMod: Percentage of human modification to the landscape
* CanopyCover: Percentage of tree cover
* Dist2Edge: Distance (m) to nearest forested to non-forested habitat edge
* PercForestMix: Percentage of forested habitat within 250 m of observation location
* PercXGrass: Percentage of xeric grassland habitat within 250 m of observation location
* PercXShrub: Percentage of xeric shrubland habitat within 250 m of observation location
* Landcover: Numerical value representing landcover classification from Cascadia Partner Forum TerrAdapt:Cascadia tool (30m 			resolution)
* Landcover_type: Landcover classification label
* obs: Unique value for each observation
* Area (NE, OK): Indicates which study area (Northeast or Okanogan) each observation was associated with
* Used: Indicates whether observation was "used" (1) or "available" (0) to an individual
* w: The weight of each observation ("available" = 5000, "used" = 1)

**Movement Data:** Contains movement data used in hidden Markov model analyses, derived from telemetry relocations for each species. The coordinates of each observation are excluded due to sensitivity of the information. Contact information for complete data provided above. File is an RData file that can be read into R containing a list of 14 data frames, one per species, season, and study area. Start of each named list indicates the species (e.g., md = Mule Deer, wtd = White-tailed Deer); season is indicated by smr = Summer or wtr = Winter; study area is indicated by NE = Northeast or OK = Okanogan. Mule deer data were only collected in the OK, elk and white-tailed deer data were only collected in the NE study area.

*Files  included:*

1. crwOut_ALL_wCovs_for_pub.RData

*Data description:*

* ID: Unique animal ID and burst number
* step: Step length
* angle: Turning angle
* FullID: Unique animal ID and year of observation
* time: Date and time of telemetry relocation, time floored to nearest hour
* burst: Numerical indicator for which burst of sequential locations each observation belongs to.
* AnimalID: Unique animal ID
* speed: Movement speed calculated based on time step and step length
* obs: Observation number
* Date: Date of observation
* month: Month of observation
* Dist2Road: Distance (m) to nearest road based on Cascadia Partner Forum TerrAdapt:Cascadia tool roads layer
* PercOpen: Percentage of open habitat within 250m of observation
* SnowCover: Binary indicator of whether snow cover was present at the animal location on day of observation
* TRI: Measure of landscape variability (Terrain ruggedness index) 30m resolution, values have been centered and scaled
* \[species code]_RSF: Predicted relative probability of selection by each species of interest [ELK = elk, MD = mule deer, WTD = white-tailed deer, COUG = cougar, WOLF = wolf] based on species, season, and year specific resource selection functions (RSF), values have been centered and scaled
* hour: Hour of each observation
* hour_fix: Hour of each observation
* hour3: Hour of each observation transformed to categorical variable representing the number of relocations in a day
* daytime: Binary variable indicating whether observation occurred during daylight (0) or nighttime (1)
* Sex: Sex of collared animal
* StudyArea (NE, OK): Indicates which study area (Northeast or Okanogan) each observation was associated with
* Season: Indicates season and year when each observation was made (Summer18 = summer 2018; Winter1819 = winter 2018-2019; Summer19 		= summer 2019; Winter1920 = winter 2019-2020, Summer20 = summer 2020; Winter2021 = winter 2020-2021)

**Covariate Data:** CSV files containing covariate values extracted at every 30-sq-m or 1-sq-km pixel across the Northeast and Okanogan study areas and their corresponding TIF files, each containing a single raster that matches the spatial location and resolution of the covariate data. Raster pixels can be converted to points, representing the location of each pixel centroid, and paired with each row of the covariate data. The covariates and rasters were used to predict and map the relative probability of selection for each RSF analysis.  CSV file columns and units of measurement for each variable are described below. Waterways were masked in the raster data so no predictions can be made to pixels that overlap waterbodies or rivers.

*Files included:*

1. NE_covariates_30m.csv
2. OK_covariates_30m.csv
3. NE_covariates_1km.csv
4. OK_covariates_1km.csv
5. NE_30m_grid_mask.tif
6. OK_30m_grid_mask.tif
7. NE_1km_grid_mask.tif
8. OK_1km_grid_mask.tif

*Data description:*

* ID: unique identifier for covariate data extracted at each location, corresponding with the raster's grid index number 
* Elev: Elevation (m) of camera site
* Slope: Slope (degrees) of terrain at camera site
* RoadDen: Total road length/km-sq at observation location
* Dist2Water: Distance (m) to nearest water
* HumanMod: Percentage (%) of human modification to the landscape (1 km resolution)
* CanopyCover: Percentage (%) of tree cover per year of study
* Dist2Edge: Distance (m) to nearest forested to non-forested habitat edge per year of study

- Landcover_type: Landcover classification from Cascadia Partner Forum TerrAdapt:Cascadia tool (30m resolution) per year of study

## Sharing/Access information

The coordinates of telemetry re-locations from GPS-collared animals analyzed during the current study are not publicly available due to sensitive location information but are available to qualified researchers from the Wildlife Chief Scientist of the Washington Department of Fish and Wildlife by contacting (306) 902-2515.

Query details: Data collected Jan 2017 – Mar 2021 in Game Management Units 117, 121, 203, 218, 224, 231, 233, and 239, including animal ID, date, time, and coordinates of telemetry relocations for all cougars, elk, mule deer, white-tailed deer, and wolves GPS-collared as part of the Washington Predator-Prey Project. Anonymized data are available here. Detailed data collection, processing, and formatting methods described in manuscript.

The code used to analyze the datasets during the current study are available in the GitHub repository, [https://github.com/SarahBassing/Bassing_et_al_Predator-Prey_Movement](https://github.com/SarahBassing/Bassing_et_al_Predator-Prey_Movement) and is permanently archived with Zenodo to ensure permanency and versioning, [https://zenodo.org/records/13381998](https://zenodo.org/records/13381998) (DOI: 10.5281/zenodo.13381998).

#### **Author Information**

* Name: Sarah B. Bassing
* ORCID: 0000-0001-6295-6372
* Institution: University of Washington
* Address: 107 Anderson Hall, University of Washington, Seattle WA
* Email: [sarah.bassing@gmail.com](mailto:sarah.bassing@gmail.com)

#### **Author/Principal Investigator Information**

* Name: Beth Gardner
* ORCID: 0000-0002-9624-2981
* Institution: University of Washington
* Address: 107 Anderson Hall, University of Washington, Seattle WA
* Email: [bg43@uw.edu](mailto:bg43@uw.edu)

