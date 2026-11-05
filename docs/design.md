# Capitalism++ — Design spec

The rules reference is `docs/gamelogic.md`, and the build order is in
`docs/milestone-1.md`. This spec doesn't restate the reference. For each
slice it says what to build, where `gamelogic.md` contradicts itself or
leaves out a number, which call we made, and which golden tests prove the
slice. Any number marked **provisional** is ours, not the original's, and
belongs in a data table so it can be tuned.

General rules for the whole sim:

- **One RNG.** A single seeded generator is owned by the world and drawn
  from in a fixed order. No module makes its own unseeded random calls.
  The same seed and the same inputs must give the same state, byte for byte.
- **Fixed iteration order.** Corporations, people, towns, firms, jobs and
  links are processed in array (slot) order. A deleted entity leaves an
  empty slot, and that slot is reused before the array grows.
- **No I/O in the sim.** The sim never prints, saves or reads files. The
  runner does that. Autosave (month pass, step 6) is a runner hook.
- **State hash.** The sim exposes a stable hash of the full state, which
  the determinism tests use.

---

## Slice 1 — Clock and passes

Reference: *Time and the game clock*, *The three simulation layers*,
*Day, month, and year*, *Month pass*, *Year pass*.

### Calendar

- The game starts on 1 January of the starting year (default 1990).
- **day-serial** is an absolute day count from 1 January 1900 (call:
  the reference uses it as an absolute number, e.g. R&D's
  `(day-serial − start-date) / 30`, but never names an epoch).
  `weekday = day-serial mod 7`.
- Day-of-month follows the real Gregorian calendar but is **clamped at
  30**, so on a 31-day month the 30th and 31st both read 30.
  `days_in_month` gives the real length (28 to 31) and is what salary and
  overhead use.
- A month boundary is a real calendar boundary (31 Jan to 1 Feb), not a
  count of 30 days.

### One day

Headless, a whole day runs in one call (frame slicing is cut; see
milestone-1.md). Order:

1. **Firms layer:** every firm's daily method, in slot order.
2. **Jobs layer:** every job's daily method, in slot order.
3. **Links layer:** every product link's daily method, in slot order.
4. **Daily batch**, exactly as *Day, month, and year* lists it:
   1. Day advance. On a month boundary, the month pass runs first. On a
      year boundary, the year pass runs right after the month pass.
   2. Corporations daily.
   3. People daily.
   4. Towns daily.
   5. Goals: player every 2 days and AI every 7 days (untimed games
      only). Timed games check yearly instead.
   6. Weekly ratings, on weekday 5 only.
   7. Random events, skipped when frequency is 0.
   8. Products: 1/30 of the catalog.
   9. Natural resource discovery.

In slice 1, every system hook is an empty stub that records that it was
called and on which day. Later slices fill the stubs in.

**Call: staggered visits use `day-serial mod 30`, not day-of-month.**
The reference staggers products ("1/30 of the catalog per day"), the
town population step ("the day matching that town's index") and the city
monthly tick ("stagger slot"). Because of the clamp at 30, a
day-of-month stagger would visit slot 30 twice on a 31-day month and skip
slots 29 and 30 in February. With `day-serial mod 30 == slot`, every
staggered entity runs exactly once every 30 days. Slots are given at
creation: product slot = catalog index mod 30, and town slot = town index
mod 30.

### Month pass

This runs in this order, inside step 4.1, before corporations see the
new day. It follows the reference:

1. GNP index adjustment.
2. Product catalog maintenance, including obsolescence and cigarette
   decline.
3. Town monthly processing: stats ring, town spawning, town-product
   demand recalculation and the centroid.
4. Corporations monthly.
5. Monthly methods for firms, jobs and links.
6. Autosave hook on months 3, 6, 9 and 12 (runner only).

In slice 1, steps 1 to 5 are stubs. The pass itself, its order and its
timing are real.

**Call: town spawning is rolled once per month pass**, at 1 in 10. The
reference puts a "1-in-10 daily chance" inside the monthly pass, which
contradicts itself. The other gates are unchanged: detailed mode on,
700 or more days since the last spawn, fewer than 12 cities, and fewer
than map area / 30 towns.

**GNP index thresholds (provisional):** these are in the reference but
have no numbers. Use a low threshold of 0% average 12-month GNP growth,
a high threshold of 6%, a 10% chance per month of a ±0.01 step, and an
index floor of 0.5.

### Year pass

Runs in this order: calendar update (years elapsed, and the 30-year and
10-year rings advance), GNP history ring, goal deadline check,
corporations yearly, firms yearly. In slice 1, the goal check and the two
yearly methods are stubs.

### Golden tests, slice 1

1. **Determinism:** two worlds with seed 42 run for 3,650 days have the
   same state hash. Seed 43 gives a different hash.
2. **Order:** for the day that advances into 1 Feb 1990, the hook log reads firms, jobs, links, then
   month pass (steps 1 to 5 in order), then corporations, people, towns
   and so on. For the day that advances into 1 Jan 1991, the year pass
   comes right after the month pass.
3. **Clamp:** 30 Jan and 31 Jan both read day-of-month 30, and
   `days_in_month` is 31. In February 1992, `days_in_month` is 29.
4. **Stagger:** over any 30 consecutive days, every product slot and
   every town slot is visited exactly once.
5. **Weekly:** weekly ratings run on exactly the days where
   `day-serial mod 7 == 5`.
6. **Counts:** across 10 years from 1990, there are 120 month passes and
   10 year passes.

---

## Slice 2 — World data (map, terrain, towns)

Reference: *Map and terrain*, *Towns and cities*, *Game initialization
sequence*.

### Map

The map is 240 × 198 = 47,520 tiles. Each tile holds:

- `kind`: deep ocean, water, grassland, hills/forest, town or firm.
- `ref`: the town or firm id.
- `rainfall` (0–4), `soil` (0–3), `moisture` (0–100) and `climate` (0–4).

Visual-only bytes (terrain shade and variant offsets) are cut until
milestone 2.

**Call on tile attributes.** *Towns and cities* says climate 0–4,
rainfall 0–3 and soil fertility 0–100. *Map and terrain* says rainfall
0–4, soil type 0–3 and moisture 0–100. We store all four:

- `rainfall`, `soil` and `moisture` follow *Map and terrain*.
- `climate` is the latitude band, from 4 at the equator row down to 0 at
  the poles.
- Moisture is the 0–100 "fertility" that farming reads.

This is provisional and gets re-checked when we build the farming jobs
in slice 4.

### Terrain generation

The pipeline follows the reference:

1. Diamond-square heightmap with 5 levels and displacements of 320, 160,
   80, 40 and 20, with random orientation.
2. Water-level normalization.
3. Jitter.
4. Classification.
5. Coast pass.
6. Climate.

The grid isn't a power of two plus one. Any approach that keeps the five
displacement levels and passes the tests below is fine, for example
generating 257 × 257 and cropping.

**Call on classification.** The normalization step counts "land" as
height above 99, but the conversion step only names thresholds at 1 and
215. Combined:

| Height | Tile |
|---|---|
| below 1 | deep ocean |
| 1 to 99 | water |
| 100 to 214 | grassland |
| 215 and above | hills/forest |

Land is anything at 100 or above, which keeps normalization consistent.

**Climate:** the equator row is random in 34 to 164. Let
`d = |row − equator|` and `dmax = max(equator, 197 − equator)`. Then
`climate = rainfall = 4 − floor(5 × d / (dmax + 1))`. Rainfall and
climate share the latitude curve because the reference derives both from
latitude. Soil and moisture each come from their own neighbour-averaging
noise pass.

### Towns

- **Placement (setup):** default 5 cities, maximum 12, up to 1,000
  attempts, abort after 10 failures in a row. Each attempt tries up to
  4,752 sites with a 5-tile border, and the site needs a 5 × 5 area of
  all grassland.
- **Call on spacing:** "15 tiles in both axes independently" means a site
  is rejected when `|dx| < 15` and `|dy| < 15` for any existing city. That
  is, the Chebyshev distance must be 15 or more.
- **Name pool:** each name has a tier from 0 to 3. Building the pool is a
  content task. Slice 2 ships a 24-name placeholder pool with 6 names per
  tier.
- **Initial values:**
  - Population is `tier × 300,000 + rand(0, 30,000)`.
  - Per-capita GNP is uniform within the tier's range.
  - The three environmental factors are each a random integer from −3
    to +3.
- **Level:** the table means reaching level L needs population of at
  least `(L − 1)² × 160,000`. So level 2 needs 160,000 and level 3 needs
  640,000. The initial level is computed the same way. Call: the level is
  capped at 6, where the table ends. The footprint radius is level + 4.
- **Simplified mode** (Detailed City Development off): indicators are
  frozen at the reference's fixed table, with level 3, per-capita GNP
  20,000 and every index at 100. There is no growth and no spawning.

### City monthly tick (detailed mode)

This runs on the town's stagger slot, in the reference's order:
population, per-capita GNP, climate, unemployment, labor cost, consumer
spending, labor quality, environmental factors. The reference gives the
per-capita GNP factor (0.983 to 1.013), the tier floors and ceilings, the
climate table and the unemployment limits. Everything else is missing and
is **provisional**:

- **Climate input. Call: use the 12-month rolling GNP growth** that the
  month pass already computes. The table's thresholds (8% and −6%) can't
  be reached by a single month, which moves at most about ±1.7%.
- **Unemployment:** `Δ = drift + uniform(−swing, +swing)` in percentage
  points, clamped to the range 2% to 10%. Each climate sets the drift and
  the swing:

  | Climate | Drift | Swing |
  |---|---|---|
  | Boom | −0.15 | 0.30 |
  | Prosperous | −0.10 | 0.20 |
  | Normal | 0 | 0.10 |
  | Recession | +0.10 | 0.20 |
  | Panic | +0.15 | 0.30 |
- **Population:** the monthly growth rate is
  `uniform(−0.2%, +0.4%) + 0.05 × (12-month GNP growth) − 0.05 × (unemployment − 5%)`.
  Negative growth is halved below 50,000 people, and positive growth is
  halved above 4,000,000.
- **Labor cost:** the target is `per-capita GNP / 200 × (1 + 0.01 × envA)`.
  The value moves 20% of the way toward the target each month, with a
  floor of `0.5 × per-capita GNP / 200`. A per-capita GNP of 20,000 gives
  100, which matches simplified mode.
- **Consumer spending:** the target is
  `per-capita GNP / 200 × climate factor × (1 + 0.01 × envB)`, with a
  20% step and a floor of 1.0. The climate factors are Boom 1.10,
  Prosperous 1.05, Normal 1.00, Recession 0.95 and Panic 0.90.
- **Labor quality:** the target is
  `clamp(per-capita GNP / 200 × (1 + 0.01 × envC), 1, 100)`, with a 20%
  step.
- **Environmental factors:** each month, each factor has a 10% chance to
  move ±1, clamped to the range −3 to +3.

### Land value

Proximity value decays linearly to 0 at a distance of level + 4 from the
nearest relevant town. Small towns get a discount. The floor is
$500,000. The building bonus is `type value × level × size³ / 5`, and
the floor is applied again after the bonus is added. The base value and
the bonus cap are **provisional**:

- Base value at the town centre is
  `level × per-capita GNP × 50 × small-town factor`. The small-town
  factor is 0.6 for levels 1 and 2, and 1.0 otherwise.
- The bonus cap is $50,000,000.

Land value is only computed in slice 2. Firms start using it in slice 4.

### Golden tests, slice 2

1. **Map determinism:** seed 42 gives the same tile hash every run.
2. **Map shape:** over seeds 1 to 50, every map has land on at least a
   third of its tiles (15,840 or more), at least 10 land border tiles,
   and an equator row in 34 to 164.
3. **Placement:** with the defaults, every map from seeds 1 to 50 has
   5 cities. Each one sits on a 5 × 5 grassland area, every pair is at
   Chebyshev distance 15 or more, and no names repeat.
4. **Initial values:** every town's population, per-capita GNP and level
   match its tier formula.
5. **Simplified mode:** after 10 years, every indicator is unchanged.
6. **Detailed mode:** after 10 years, every indicator stays within its
   clamps. Unemployment stays in 2% to 10%, labor quality in 1 to 100,
   and per-capita GNP at or above its tier floor. A town that crosses
   640,000 people is level 3 or higher.
7. **Land value:** every tile is $500,000 or more. A town's centre tile is
   worth more than a tile at distance level + 4.

---

## Slices 3 and up

To follow, in milestone-1.md order. Next up: product catalog and demand,
then firms and jobs.
