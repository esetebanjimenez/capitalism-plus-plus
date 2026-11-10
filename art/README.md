# Capitalism++ art (M2, concept B+)

Original art only, made for this project. Nothing here is taken from the original game.
Direction and the full asset list: `docs/art/visual-direction.md`.

- `tools/palette.json` is the shared 48-colour B+ palette. Every tile is checked against it on export.
- `tools/terrain.py` draws the terrain and coast tiles at 32 px. `tools/terrain_preview.py` rebuilds
  `tiles/terrain/*.png`, `atlas/terrain_atlas.png` + `.json` and `docs/art/terrain-preview.png`.
- Tiles are hard pixels. Scale them by whole numbers only, with nearest-neighbour filtering.

## Terrain tile names

| Name | Use |
|---|---|
| `deep_0..2`, `water_0..2` | DEEP_OCEAN and WATER variants |
| `grass_c{0-4}_{0-3}` | GRASSLAND, by tile climate (0 = poles, 4 = equator) |
| `forest_c{0-4}_{0-3}`, `hill_c{0-4}_{0-1}` | FOREST_HILL, mostly forest, with a few rocky hills |
| `coast_01..15` | water tile with land on its sides, mask N=1 E=2 S=4 W=8 |
| `coast_corner_ne/se/sw/nw` | water tile with land only diagonally on that corner |
| `shelf_n/e/s/w` | deep ocean with shallow water on that side |

Variant pick: any stable hash of (x, y). When a water tile has land on its sides and also only diagonally
on a corner, use the side mask. A combined piece can follow later if it shows.
