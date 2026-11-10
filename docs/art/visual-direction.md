# M2 visual direction (proposal, waiting on Esteban's okay)

Concept sheet: [`concept-sheet-a.png`](concept-sheet-a.png). The art is all
original. Nothing in it is extracted or traced from the original game. No asset
production starts until this is approved.

## Look

Crisp top-down pixel art with a clean, modern flat UI on top of it. The tone is
bright and friendly, like a contemporary business tycoon game. There are no
fantasy or medieval elements.

## Sizes

- **Map tiles are 16×16 px.** They're drawn at integer scale only, so 2× (32 px)
  on a phone and 2× or 3× on desktop. Nearest-neighbour filtering, no blur.
- A phone at 360 px wide shows about 11 tiles across at 2×. The map is
  240 × 198, so it pans and zooms. Zoom steps are 1×, 2× and 3×.
- **A firm takes one tile** (the sim's `FIRM` tile). Its sprite is 16×16, with
  a 2 px owner-colour flag so you can tell corporations apart at a glance.
- **Icons are 24×24 px** with a 1 px ink outline. They're shown at 2× (48 px),
  which is a comfortable tap target.

## Palette

| Use | Hex |
|---|---|
| Deep ocean | `#14234a` |
| Water | `#2a7f9e` |
| Foam and sand (coast) | `#e8d6a0` |
| Grassland | `#5f9e3a` |
| Forest/hill | `#2f5e2a` |
| Asphalt (town roads) | `#7a8088` |
| Glass (town buildings) | `#3b6db3` |
| Panel cream | `#f6ecd4` |
| Ink (outlines, text) | `#22262e` |
| Signal orange (accent, selection) | `#e8742a` |
| Profit green | `#3aa05a` |
| Loss red | `#c8402e` |

Up to 12 corporation flag colours get picked later. They have to stay apart
from the terrain greens and blues.

## Terrain tiles (from `TileCategory`)

| Kind | Tiles |
|---|---|
| `DEEP_OCEAN` | 2 variants |
| `WATER` | 2 variants, plus a 16-piece coast autotile where water meets land (sand and foam edge) |
| `GRASSLAND` | 4 variants. A tint follows `climate` (0 poles to 4 equator), cooler and paler toward the poles |
| `FOREST_HILL` | 3 variants, trees on a darker base |
| `TOWN` | road and block tiles over the town's footprint (radius level + 4). Block height grows with town level, 3 building styles |
| `FIRM` | the firm's sprite on a paved pad |

Variants are picked from a hash of the tile position, so the map always draws
the same way for the same seed. That needs no new sim bytes.

## Firm types (14)

Each firm gets a map sprite (16×16) and a panel icon (24×24) drawn from the
same design:

1. Department Store: striped awning
2. Factory: sawtooth roof and two chimneys
3. R&D Center: glass lab with a dish
4. Farm: red barn, silo, crop rows
5. Logging Camp: cabin with a log stack
6. Mine: headframe over a pit
7. Oil Well: pumpjack and tank
8. Software Developer: small office with a laptop sign
9. Software Publisher: office with a disc sign
10. Restaurant: fork and knife sign
11. Television Station: tall mast
12. Radio Station: tower with waves
13. Newspaper Publisher: rolled-paper sign
14. Seaport: pier, crane and containers (always placed on the coast)

## Job types (16, from `job_types`)

Crop Growing (sprout), Livestock Raising (cow), Livestock Processing (cleaver
and steak), Logging (axe in a log), Inventory (box stack), Private Labelling
(star tag), Manufacturing (gear and wrench), Mining (pickaxe and ore), Oil
Extraction (pumpjack and drop), Purchasing (cart with an arrow), Research &
Development (flask and bulb), Sales (cash register), Software Development
(laptop with code brackets), Software Production (disc and box), Advertising
(megaphone), Import (container ship).

On the concept sheet the shopping bag is a spare, and Import's ship isn't drawn
yet. Both get settled in production.

Link arrows between slots use ink at 2 px, and signal orange when selected.

## UI panels

- The panels are cream cards with a 2 px ink border, a 4 px corner radius and
  a 1 px darker drop shadow.
- Text is 16 px minimum on a phone, 14 px only for table numbers. Money uses
  tabular figures. Profit is green and loss is red, always with a sign as well,
  so colour is never the only cue.
- On a phone the firm detail opens as a bottom sheet with the **3×3 job slot
  grid** (48 px cells). On desktop it's a side panel.
- Reports, news, stock and goals use the same card style. The layout follows
  the Game Designer's UX spec.
- The top bar shows cash and date. The bottom dock in the mock uses placeholder
  labels, and the real tabs come from the UX spec.

## Asset list for production (after okay)

- Terrain: about 30 tiles plus the 16 coast pieces
- Town: about 12 road and block tiles
- Firms: 14 sprites and 14 icons
- Jobs: 16 icons
- UI: panel nine-slice, buttons, dock icons, about 10 status icons

---

# Concept B: straight top-down with hard pixels (to compare with A)

Concept sheet: [`concept-sheet-b.png`](concept-sheet-b.png). The phone mock at
its real size (360 × 640) is [`concept-b-phone.png`](concept-b-phone.png).
B is drawn as real pixel art, not painted. Every tile and sprite is a native
16 × 16, every icon is a native 24 × 24, and the sheet only enlarges them by
whole numbers.

How B differs from A:

- **View.** Everything is seen from straight above, both terrain and
  buildings. You see roofs, yards and pads, with no walls and no 3/4 angle. A
  firm is told apart by its roof colour plus a roof symbol, such as the
  store's awning stripes, the factory's sawtooth roof and chimneys, the mine
  pit, the radio mast's guy wires or the port's containers.
- **Rendering.** Hard pixels and flat fills only, with no gradients,
  anti-aliasing or painted shading. Icons get a 1 px ink outline.
- **Palette.** 16 colours. That's A's 12 plus a foam, a dark grass, a light
  grey and a wood brown, and nothing off-palette.

| Name | Hex | Name | Hex |
|---|---|---|---|
| Ink | `#22262e` | Grass dark | `#4a8030` |
| Navy (deep ocean) | `#14234a` | Forest | `#2f5e2a` |
| Water | `#2a7f9e` | Asphalt | `#7a8088` |
| Foam | `#9fd3d8` | Light grey | `#b8bcc0` |
| Sand | `#e8d6a0` | Glass | `#3b6db3` |
| Grass | `#5f9e3a` | Cream (panels) | `#f6ecd4` |
| Orange (player, accent) | `#e8742a` | Green (profit) | `#3aa05a` |
| Red (loss) | `#c8402e` | Brown (wood, soil) | `#8a5a32` |

- **Map at zoom 1×** fits about 22 tiles across a phone screen. Zoom 2× and
  3× are the same pixels enlarged.
- **Owner flag.** A 3 × 3 px flag sits in the top-right corner of the firm
  tile. In the mock, orange is the player and red and blue are rivals.
  Production adds the rest of the 12 corp colours.
- **Coast.** Water tiles that touch land get a sand edge and a foam edge.
  Production adds the inner and outer corner pieces to make the full 16-piece
  set.
- **Panels.** Same cream cards as A. The dock is Map, Company, Stocks, News
  and Goals, following the Game Designer's UX spec. Firm detail opens as a
  bottom sheet with the 3 × 3 slot grid. Links are orange connectors between
  slots.
- **Coverage.** The same as A: terrain and coast, the town road grid, owner
  flags, all 14 firm types, all 16 job icons, the palette and a panel mock.
  Import's container ship is drawn in B.

Esteban picks A or B, or a mix, before any production starts.
