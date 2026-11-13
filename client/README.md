# Capitalism++ web client (M2)

Map renderer for the M2 frontend plan (`docs/m2-frontend-plan.md`): Vite, TypeScript and PixiJS v8.
This first step draws terrain and towns from `art/atlas/terrain_atlas.*` on a sample map. The sim
worker, firms, overlays and panels come later.

```bash
npm install --prefix client
npm run --prefix client dev          # http://localhost:5173/?x=147&y=39
npm run --prefix client check        # typecheck, unit tests, production build
npm run --prefix client screenshot   # after build: docs/art/m2-map-desktop.png, m2-map-phone.png
```

- **Chunks.** Terrain is baked into 32 x 32-tile chunks (1024 px, about 4 MB each) on first view.
  Only chunks within 8 tiles of the screen are kept; the rest are destroyed. A 1920 x 1080 screen
  holds at most 12 chunks (48 MB), a phone at standard zoom at most 6. The full map would be 56.
- **Zoom.** Counted in points, so the view looks the same on every screen: one map view with
  32 pt tiles (about 12 across a phone, 60 across a 1920 px desktop; docs/m2-ux-spec.md). Canvas
  pixels per art pixel are `32 pt x resolution / 32`, so a 3x phone draws 64 px art at 1.5x
  nearest-neighbour (Esteban, 2026-11-11). Camera snapped to whole canvas pixels; one-finger or
  mouse drag pans. The far overview comes later.
- **Art sheet.** The 64 px sheet is used once a tile spans 64 or more canvas pixels, otherwise
  the 32 px sheet (`sheetFor`); frames missing from the 64 px sheet fall back to 32 px ones.
  Changing sheet rebuilds the visible chunks.
- **Tiles.** `src/tiles.ts` follows `art/README.md`: coast mask, corners, shelves, climate band
  edges, and road masks. Towns are one tile in the sim today, so a lone town tile draws as a tower
  block; the town footprint and road layout are placeholders until town data reaches the client.
  Firms draw as grass until the firm sprites land.
- **Sample map.** `public/sample-map.bin` comes from `python scripts/export_sample_map.py` (seed 1,
  240 x 198): `CPPM`, u16 width, u16 height, then kind and climate bytes per tile.
- URL parameters: `x`, `y` (top-left tile), `margin` (tiles kept around the screen).

## Terrain renderer options

URL parameters pick the terrain renderer, for comparison: `mode=baked|direct`, `art=32|64`,
`chunk=<tiles per chunk side>`. Default is direct mode with 16-tile chunks and the sheet picked
by zoom (about 4 MB of GPU memory for both sheets; baked 64 px chunks on a 3x phone take about
100 MB). `art=32|64` forces one sheet. `npm run bench` (after
`npm run build`) prints memory and frame time for each variant at phone and desktop sizes.
Chrome there renders WebGL on the CPU (SwiftShader), so frame times are only relative.

## Live build

`.github/workflows/pages.yml` deploys `client/` to GitHub Pages on every push to main:
https://esetebanjimenez.github.io/capitalism-plus-plus/ (same URL options, for example
`?mode=baked` or `?art=32`). The HUD's second line shows the average frame time, the
render call's CPU time and the screen's pixel density.

## Sim in a Web Worker (#246)

`src/sim/worker.ts` boots the pinned Pyodide (314.0.7, from the jsDelivr CDN), loads
pydantic, unpacks `public/capitalism.zip` (written by `npm run bundle`, which `dev` and
`build` run first) and creates `capitalism.api.Api.new_game(**DEFAULT_SETUP)`
(`src/sim/setup.ts`). `src/sim/engine.ts` owns the clock and command queue, and
`src/sim/client.ts` is the main-thread `SimClient` (`query`, `command -> id`, `onTick`,
`onCmdResult`). Speeds are target days per second in `src/sim/clock.ts` (provisional:
1, 3, 8, max). Space pauses and 1–4 set the speed. `web/worker-smoke.mjs` runs the
engine under Node + Pyodide in the `pyodide-smoke` CI job.
