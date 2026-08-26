# Vendored third-party assets

Nothing here is written by this project. It is checked in rather than fetched
from a CDN for the same reason the backdrop is baked into the map: the page
should work on a host that permits no outbound requests, and a build should not
depend on a CDN still serving the same bytes next year.

Extracted from the npm registry with `npm pack`, unmodified:

| File | From | Version | Licence |
|---|---|---|---|
| `globe.gl.min.js` | `globe.gl` | 2.46.2 | MIT |
| `earth-blue-marble.jpg` | `three-globe`, `example/img/` | 2.45.2 | see below |
| `earth-topology.png` | `three-globe`, `example/img/` | 2.45.2 | see below |

`globe.gl.min.js` bundles three.js (also MIT), so it is the only script the
globe page loads.

The two images are NASA imagery redistributed by `three-globe`:

- `earth-blue-marble.jpg` (4096x2048) is NASA's **Blue Marble Next
  Generation**, a cloud-free composite of MODIS observations, produced by NASA
  Earth Observatory. NASA imagery is generally not copyrighted and is free to
  use; see https://www.nasa.gov/nasa-brand-center/images-and-media/
- `earth-topology.png` (2048x1024, greyscale) is a global elevation map used as
  a bump map for surface relief.

To refresh them:

    npm pack globe.gl three-globe
    tar xzf globe.gl-*.tgz package/dist/globe.gl.min.js
    tar xzf three-globe-*.tgz package/example/img/earth-blue-marble.jpg \
                              package/example/img/earth-topology.png
