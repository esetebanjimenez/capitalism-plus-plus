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

These frames are legacy: since #249 the client draws town tiles only from the native kinds
(`town_rural_*` and `town_urban_*`, below).

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
- `tools/build64.py` writes `tiles64/{terrain,town,firms,flags}/*.png`, `atlas/terrain_atlas_64.png` + `.json` and `docs/art/m2-terrain-64-preview.png`.
  It fails if a 64 px frame has no 32 px frame of the same name.
- Each frame sits in a 68 px cell with its edge pixels repeated 2 px outward, so drawing straight from the
  atlas never picks up a neighbour's pixels. The JSON `x, y, w, h` give the 64 x 64 art only, not the padding.
- `tools/town64.py` draws the 64 px town tiles (roads, blocks, parks, plaza), same names as `town.py`, preview in `docs/art/m2-town-64-preview.png`.
- `tools/firms64.py` draws the 14 firms (64 x 64, transparent margins) and 12 owner flags (16 x 24, drawn at +48, -8 on the firm,
  twice the 32 px offset). Each flag has its own cell. Review sheet: `docs/art/m2-firms-64-sheet.png`.
- The 64 px sheet is now complete: 216 frames, every 32 px frame name has a 64 px twin.

## UI atlas

`python3 art/tools/ui_build.py` (run from `art/tools`) builds `art/atlas/ui_atlas.png`,
`ui_atlas_2x.png` and `ui_atlas.json` (34 frames: cards, sheet top, buttons with pressed
states, tab line, handle, slot cells, badge, rating chip, 16×16 status icons). JSON x/y/w/h
are 1x pixels; double them for the 2x sheet. Nine-slice frames list `slice` [l, t, r, b] in
points. Use the 2x sheet on 2x and 3x screens (3x draws it at 1.5×, nearest).

## Map markers

`python3 art/tools/marks.py` builds `art/atlas/marks_atlas.png/.json` (32 px) and
`marks_atlas_64.png/.json` (64 px), same frame names and the same 2 px padding rule:
`sel_tile` (selection), `sel_build_ok` / `sel_build_no` (build panel spot check),
`construction` (drawn in place of a firm while `build_firm` is pending), `link_sell`
(orange round) and `link_buy` (blue square) dots for supply-chain lines, spaced every
12 art units (12 px on the 32 px sheet) by the client, and `pending` (clock badge at the tile's
top-left, +2/+2 units). Frames that aren't full tiles keep their own w/h in the JSON and
are drawn at half size in map units on the 64 px sheet, like flags. Preview:
`docs/art/m2-map-marks-preview.png`.

## Far overview and overlays
`python3 art/tools/overlays.py` (needs the sim's deps, e.g. pydantic) writes `art/overlays.json` and `docs/art/m2-overlays-preview.png` from the sample-map seed. The JSON holds the far overview colours (1 px per tile, by tile kind and climate; firms in owner flag colour), the colour steps for the land value, soil, rainfall, climate and ownership overlays, and the drawing rules: solid on the far view with water greyed, about 70% over land on the standard view, water never tinted. Every colour is from `palette.json`. The six toggle icons are `icon_ov_*` in the UI atlas (`ui_concept.ICON`, rebuilt with `ui_build.py`).

## UI controls (M2 item 3)
`art/tools/ui_controls.py` draws the extra controls and `ui_build.py` adds them to the UI atlas (53 frames, earlier frames keep their places): `bar_track`, `bar_fill`, `bar_fill_good` (slider and progress bar, nine-slice [4,4,4,4], 12 pt tall), `knob` (20 pt thumb with its lip), `chip_off`/`chip_on` and `field_normal`/`field_focus`/`field_error` (nine-slice [6,6,6,6]), `switch_off`/`switch_on` (44x24, give it a 44x44 tap area), `caret` and `toast_error` (nine-slice [10,6,6,7], red band on the left, icon_warn just right of it). Running `python3 ui_controls.py` writes `docs/art/m2-ui-controls-preview.png`; its labels are example text only. The town-name plate waits for its view brief.

## Firm-type icons and goal tick (#176)

Firm-type icons reuse the map sprites (`firm_*` in `terrain_atlas` / `terrain_atlas_64`) in a 32 pt cell,
so a type looks the same in the build menu and panels as on the map and stays pixel-native on every
screen. There is no separate 48 px set. A type the player can't afford draws its sprite at 50% opacity
with the shortfall in red. The goal-met tick is `icon_goal` (16×16) in `ui_atlas`. Preview:
`docs/art/m2-build-menu-preview.png`, made by `art/tools/build_menu.py` (cash and land value are example values;
costs come from `capitalism.db`).

## M2 views: town plate, news and profit icons, charts, win/loss card (#175, #177, #178)

Drawn from `docs/m2-view-briefs.md` sections 2 to 5 by `art/tools/ui_views.py`; `ui_build.py` appends its
frames to `ui_atlas` (now 71 frames, earlier frames unchanged). Preview: `docs/art/m2-views-preview.png`.

- **Town plate (#175):** the existing `card` nine-slice at 136×24 pt (12 characters at 12 pt bold), name and
  level as live text. The level sits in `plate_level`, an ink badge that stretches for any number. No owner
  colour. `plate_pulse` is an orange ring 3 pt outside the plate for the optional level-up pulse.
  States (#336, view brief §2): while a plain tap selects the tile under the plate, the whole plate (badge
  included) fades to 40% opacity over 120 ms. While the town card is open, the plate stays fully opaque and
  `plate_pulse` is drawn steady at 100% with no scale animation as the highlight; it is dropped with no fade
  when the card closes, and a level-up pulse still plays on top.
- **News (#177):** `icon_nws_normal`, `icon_nws_financial`, `icon_nws_tech`, `icon_nws_special`, one per
  category. Important items stay a bold row, not an icon.
- **Profit arrows (#177):** `icon_arr_up` (green) and `icon_arr_down` (red), beside the corporation's
  operating and other profit only; the figure keeps its own colour.
- **Charts (#178):** style in `art/charts.json`: one orange 2 pt line, sand grid, ink zero line when the
  range crosses 0, short money labels, `chart_dot` on the last point, `chart_dot_sel` and a `card_float`
  tip on the tapped point; a single point is a dot alone.
- **Win/loss card (#178, #289):** one `card` layout; `end_band_win|time|rival|bankrupt` (green, amber, red,
  grey) and `icon_end_win|time|rival|bankrupt` (shown at 2×) change per outcome (`VICTORY`, `DEFEAT_DEADLINE`,
  `DEFEAT_AI_WON`, `DEFEAT_BANKRUPT`). Goal rows use `icon_goal` and `icon_goal_miss`, with labels from `q_goals`;
  difficulty is a plain rating (no %). The score row and the goal list (divider, heading and rows) can each be hidden, since a game with no goals can still end in bankruptcy (#287). New game (`btn_primary`)
  is the only button: the native game has no Keep playing (#243).

## Native town tiles (#303)

`art/tools/towntiles.py` draws two stand-alone town sets (no road autotiling), at 64 px and a 32 px fallback.
`build64.py` and `preview.py` append them after every older frame in `terrain_atlas_64` and `terrain_atlas`.
Run `python3 towntiles.py` to rebuild `docs/art/m2-town-native-preview.png`.

| Frame | Native kind | Where it appears |
| --- | --- | --- |
| `town_rural_0` .. `town_rural_7` | `0x3000` .. `0x3007`, index = kind − `0x3000` | outer ring, from the level radius out to level + 4 (rural always rings urban) |
| `town_urban_0` .. `town_urban_4` | `0x3008` .. `0x300c`, index = kind − `0x3008` | solid core inside the level radius, plus the 1-in-10 corner tiles |

Rural: 0 four houses on crossing paths, 1 three houses and a tree, 2 two houses with gardens, 3 house, vegetable plot and shed,
4 farmstead, 5 cottage by an orchard, 6 two houses above a pond, 7 grain silos, shed and hay bales.
Urban: 0 glass tower, 1 tower with helipad, 2 brick mid-rise with mast, 3 shop row over a car park, 4 glass offices and brick annex.
Frames are in native kind order (rural, then urban). Names follow Esteban's correction in #311.
