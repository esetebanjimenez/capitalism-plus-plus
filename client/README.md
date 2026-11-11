# Capitalism++ web client (M2)

Map renderer for the M2 frontend plan (`docs/m2-frontend-plan.md`): Vite, TypeScript and PixiJS v8.
This first step draws terrain and towns from `art/atlas/terrain_atlas.*` on a sample map. The sim
worker, firms, overlays and panels come later.

```bash
npm install --prefix client
npm run --prefix client dev          # http://localhost:5173/?x=147&y=39&zoom=1
npm run --prefix client check        # typecheck, unit tests, production build
npm run --prefix client screenshot   # after build: docs/art/m2-map-desktop.png, m2-map-phone.png
```

- **Chunks.** Terrain is baked into 32 x 32-tile chunks (1024 px, about 4 MB each) on first view.
  Only chunks within 8 tiles of the screen are kept; the rest are destroyed. A 1920 x 1080 screen
  holds at most 12 chunks (48 MB), a phone at standard zoom at most 6. The full map would be 56.
- **Zoom.** Whole-number steps only (1x, 2x, 3x device pixels per art pixel), nearest-neighbour,
  camera snapped to whole device pixels. Wheel, pinch, and the 44 px +/- buttons.
- **Tiles.** `src/tiles.ts` follows `art/README.md`: coast mask, corners, shelves, climate band
  edges, and road masks. Towns are one tile in the sim today, so a lone town tile draws as a tower
  block; the town footprint and road layout are placeholders until town data reaches the client.
  Firms draw as grass until the firm sprites land.
- **Sample map.** `public/sample-map.bin` comes from `python scripts/export_sample_map.py` (seed 1,
  240 x 198): `CPPM`, u16 width, u16 height, then kind and climate bytes per tile.
- URL parameters: `x`, `y` (top-left tile), `zoom` (1-3), `margin` (tiles kept around the screen).

## Terrain renderer options

URL parameters pick the terrain renderer, for comparison: `mode=baked|direct`, `art=32|64`,
`chunk=<tiles per chunk side>`. Default is `mode=baked&art=32&chunk=32`. `npm run bench` (after
`npm run build`) prints memory and frame time for each variant at phone and desktop sizes.
Chrome there renders WebGL on the CPU (SwiftShader), so frame times are only relative.
