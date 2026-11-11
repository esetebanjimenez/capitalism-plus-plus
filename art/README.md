# Capitalism++ art (M2, concept B+)

Original art only, made for this project. Nothing here is taken from the original game.
Direction and the full asset list: `docs/art/visual-direction.md`.

- `tools/palette.json` is the shared 48-colour B+ palette. Every tile is checked against it on export.
- `tools/firms.py` draws the 14 firm sprites and 12 owner flags.
- `tools/terrain.py` draws the terrain and coast tiles, and `tools/town.py` draws the town tiles, all at 32 px.
  `tools/preview.py` rebuilds `tiles/*/*.png`, the single atlas `atlas/terrain_atlas.png` + `.json` (all
  tiles, name kept so the renderer path stays stable; empty cells are transparent) and
  `docs/art/m2-tiles-preview-2.png`, plus `docs/art/m2-firms-sheet.png`.
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

## Firm sprites and owner flags

| Name | Use |
|---|---|
| `firm_<type>` | one per `firm_types` row: department_store, factory, rnd_center, farm, logging_camp, mine, oil_well, software_developer, software_publisher, restaurant, television_station, radio_station, newspaper_publisher, seaport |
| `flag_00..11` | 8 × 12 owner flag, one colour per corporation (00 = orange = player) |

Firms are 32 px with transparent margins: draw the terrain tile first, then the firm on top, then the flag
at (+24, −4) from the tile's top-left (it pokes 4 px above the tile, so draw flags after the row above).
The seaport sprite carries its own quay and water and should sit on a coast tile.

## High-density 64 px set

Screens at 2x density or more use a second sheet drawn natively at 64 px; ordinary screens keep the 32 px set.
The tile stays the same size on screen (32 points), so the map shows the same number of tiles.

- `tools/terrain64.py` draws the 64 px terrain and coast tiles, same palette and the same frame names as `terrain.py`.
- `tools/build64.py` writes `tiles64/terrain/*.png`, `atlas/terrain_atlas_64.png` + `.json` and `docs/art/m2-terrain-64-preview.png`.
  It fails if a 64 px frame has no 32 px frame of the same name.
- Each frame sits in a 68 px cell with its edge pixels repeated 2 px outward, so drawing straight from the
  atlas never picks up a neighbour's pixels. The JSON `x, y, w, h` give the 64 x 64 art only, not the padding.
- So far the 64 px sheet has terrain and coast (159 frames). Town, firms and flags follow in separate PRs.
