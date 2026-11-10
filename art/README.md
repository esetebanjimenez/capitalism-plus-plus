# Capitalism++ art (M2, concept B+)

Original art only, made for this project. Nothing here is taken from the original game.
Direction and the full asset list: `docs/art/visual-direction.md`.

- `tools/palette.json` is the shared 48-colour B+ palette. Every tile is checked against it on export.
- `tools/terrain.py` draws the terrain and coast tiles, and `tools/town.py` draws the town tiles, all at 32 px.
  `tools/preview.py` rebuilds `tiles/*/*.png`, the single atlas `atlas/terrain_atlas.png` + `.json` (all
  tiles, name kept so the renderer path stays stable; empty cells are transparent) and
  `docs/art/m2-tiles-preview.png`.
- Tiles are hard pixels. Scale them by whole numbers only, with nearest-neighbour filtering.

## Terrain tile names

| Name | Use |
|---|---|
| `deep_0..2`, `water_0..2` | DEEP_OCEAN and WATER variants |
| `grass_c{0-4}_{0-3}` | GRASSLAND, by tile climate (0 = poles, 4 = equator) |
| `forest_c{0-4}_{0-3}`, `hill_c{0-4}_{0-1}` | FOREST_HILL, mostly forest, with a few rocky hills |
| `grass_c{a}c{b}_{0-3}`, `forest_c{a}c{b}_{0-3}`, `hill_c{a}c{b}_{0-1}` | climate band edge: climate a at the top, dithered to climate b at the bottom (b = a±1). Use it on a tile whose climate is a when the tile to its south has climate b |
| `coast_01..15` | water tile with land on its sides, mask N=1 E=2 S=4 W=8 |
| `coast_corner_ne/se/sw/nw` | water tile with land only diagonally on that corner |
| `shelf_n/e/s/w` | deep ocean with shallow water on that side |

## Town tile names

| Name | Use |
|---|---|
| `road_00..15` | road, mask of road neighbours N=1 E=2 S=4 W=8 (00 = lone square, 05/10 = straights, 3+ bits = junction with zebra crossings) |
| `block_s{0-3}_l{0-2}` | city block, roof style 0-3 (glass, grey, tan, brick); l0 = houses and gardens, l1 = mid-rise, l2 = towers |
| `park_0`, `park_1`, `plaza` | open town tiles |

Which TOWN tiles are roads is a renderer choice; the preview uses every third column and every
second row of the town footprint, with taller blocks nearer the centre.

Variant pick: any stable hash of (x, y). When a water tile has land on its sides and also only diagonally
on a corner, use the side mask. A combined piece can follow later if it shows.
