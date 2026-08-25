# Okavango Delta predator–prey movement map

An animated map of predator and prey movement in the Okavango Delta, Botswana,
in the visual style of the [train maps](https://github.com/Chillchamp1/github.io).

Two views are planned:

- **Predator–prey encounters** — lion and African wild dog tracks animated
  against impala, tsessebe, wildebeest and zebra, with proximity events
  flaring when a predator closes on a prey animal.
- **Seasonal prey wandering** — herbivore movement across the 2014–2016 span,
  driven by the Delta's wet/dry flood pulse.

## Data

Bennitt, E. et al. (2024). *Proactive cursorial and ambush predation risk
avoidance in four African herbivore species.* Ecology and Evolution.
Dataset: <https://doi.org/10.5061/dryad.w0vt4b8zr>

GPS collar data collected in the Okavango Delta between the start of the 2014
rainy season and the end of the 2016 dry season: 4 African wild dogs, 6 lions,
5 impala, 8 tsessebe, 8 wildebeest and 14 zebra.

### Fetching the data

```sh
python3 scripts/fetch_dryad.py
```

Downloads every file in the Dryad deposit into `data/raw/` and unpacks any
archives. Requires outbound HTTPS access to `datadryad.org`; sandboxed
environments must allow that host in their egress policy first.
