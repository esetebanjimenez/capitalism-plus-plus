# Capitalism++ web client (M2)

Map renderer for the M2 frontend plan (`docs/m2-frontend-plan.md`): Vite, TypeScript and PixiJS v8.
This first step draws terrain and towns from `art/atlas/terrain_atlas.*` on a sample map. The sim
worker, firms, overlays and panels come later.

```bash
npm install --prefix client
npm run --prefix client dev          # http://localhost:5173/ (live game), ?map=sample&x=147&y=39 for the sample map
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
  edges. Town tiles draw from the sim's native kind alone: `town_rural_N` for 0x3000-0x3007 and
  `town_urban_N` for 0x3008-0x300c (art/README.md). A firm tile draws the town tile (or grass)
  under its sprite.
- **Sim and Pyodide (#247).** `npm run build` (and `dev`) first writes `public/capitalism.zip`
  (`scripts/pyodide_bundle.py`) and `public/pyodide/` (`scripts/fetch-pyodide.mjs`: the core
  files from the pinned `pyodide` npm package plus the pydantic wheels named in its lock file,
  sha256-checked), so the site loads nothing from a CDN. `npm run boot-check` opens the built
  site in headless Chrome and fails unless the sim boots and 10 in-game days pass; CI runs it in
  the `client` job and before every Pages deploy.
- **Download size** (live game, first visit, measured 2026-11-14): Pyodide 14.7 MB (7.9 MB
  gzipped; the 9.6 MB `pyodide.asm.wasm` is most of it), sim bundle 0.14 MB, client code and art
  0.8 MB (0.4 MB gzipped). About 15.7 MB raw, 8.4 MB over gzip. The sample map (0.6 MB) loads
  only with `?map=sample`.
- **Live map (#249).** By default the map is the running sim's (`map` query). When a tick's
  `map_rev` moves, the client asks `map_objects` with `since`, applies the changed tiles and firm
  list, and rebuilds only the chunks those tiles touch (`chunksForTiles`) and the firm sprites
  that changed (`FirmLayer.setFirms`). The tile card reads the `tile` query.
- **Sample map.** `?map=sample` draws `public/sample-map.bin` instead (tests, bench, screenshots).
  It comes from `python scripts/export_sample_map.py` (seed 1, 240 x 198): `CPPM`, u16 width,
  u16 height, kind and climate bytes per tile, firms, towns (u16 x, u16 y, u8 id, u8 level), i16
  ref and u16 town kind per tile, then the TINF section.
- URL parameters: `map=sample`, `x`, `y` (top-left tile; default the first town), `margin` (tiles kept around the screen).

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

`src/sim/worker.ts` boots the pinned Pyodide (314.0.7, self-hosted under `pyodide/`), loads
pydantic, unpacks `public/capitalism.zip` (written by `npm run bundle`, which `dev` and
`build` run first) and creates `capitalism.api.Api.new_game(**DEFAULT_SETUP)`
(`src/sim/setup.ts`). `src/sim/engine.ts` owns the clock and command queue, and
`src/sim/client.ts` is the main-thread `SimClient` (`query`, `command -> id`, `onTick`,
`onCmdResult`). Speeds are target days per second in `src/sim/clock.ts` (provisional:
1, 3, 8, max). Space pauses and 1–4 set the speed. `web/worker-smoke.mjs` runs the
engine under Node + Pyodide in the `pyodide-smoke` CI job.
