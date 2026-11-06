# Capitalism++ — Design spec

The rules reference is `docs/reference/gamelogic.md`, and the build order is in
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

## Slice 3: product catalog and demand

### Classes

- `ProductClass` (pydantic, read-only, from `product_classes`): id, name,
  `durable`, `quality_decay_base`, grouping flags.
- `Product` base (pydantic for the static row) plus runtime `ProductState`
  (plain class, per game): `tech_level`, `discovered_on`, `obsolete`,
  `score`, `available`. Subclasses only where behaviour differs:
  `RawMaterial`, `Crop`, `Livestock`, `SemiProduct`, `ConsumerProduct`,
  `Software`. `Product.make(row)` picks the subclass from `kind`.
- `TownMarket` (plain class): one per (town, consumer product) with
  `demand_per_day`, the link list, `max_score_in`, `supply_today`.

### Tables (all numbers live in the db)

- `product_classes(id, name, durable, quality_decay_base, group_flags, ref, provisional)`: the 20 classes.
- `products(id, code, name, class_id, kind, unit, base_price, base_cost,
  demand_per_1000, luxury, necessity, tech_importance, w_price, w_quality,
  w_brand, base_tech_level, base_capacity, plant_month, grow_months,
  importable, spending_usd, ref, provisional)`: the 84 products. `spending_usd`
  is SET SPENDING, the product's base consumer price used by freight, not a
  store's selling price or the simulated import/resource cost. Wheat 0.30,
  Flour 0.50, Bread 1.50 are confirmed by the decompiler review. The current
  simulated Wheat import/resource `base_price` of 0.10 may stay a separately
  flagged baseline; never substitute it for SPENDING 0.30 in freight. CHECK
  `w_price + w_quality + w_brand = 100` and luxury, necessity in 0..9.
- `recipes(product_id, output_qty, speed_pct, ref)`: 54 rows from
  `docs/recipes.md` (the standard set). `output_qty` is units per
  production cycle; `speed_pct` is a throughput multiplier: 200 processes
  twice the units per work cycle of 100 (Esteban, 2026-11-05). The high
  values (Engine, Wheel & Tire, Desktop Computer, Motorcycle 200; Car 300;
  Electronic Components 400) offset the low unit capacity of expensive goods.
- `recipe_inputs(product_id, input_id, qty, quality_weight, ref)`: 1 to 5
  inputs per recipe, `qty` per cycle, `quality_weight` in %. CHECK
  `sum(quality_weight) < 100` per recipe; the rest is the manufacturing
  skill weight, derived, not stored.
- `rnd_prereqs(product_id, requires_id, ref)`: the 8 R&D prerequisites
  (e.g. Desktop Computer needs Television first). Not inputs.
  All recipe data is `ref`, so these tables carry no `provisional` column.

Filling rule: every value printed in gamelogic.md's catalog goes in as
`provisional=0`. Missing values are filled by these provisional rules
(and flagged `provisional=1`), so nothing is hand-typed twice:

| Column | Provisional fill |
|---|---|
| `base_cost` | 0.6 × `base_price` |
| `base_capacity` (units/day for one job at efficiency 100) | `max(1, round(20000 / base_price))`, about $20k of goods a day per job |
| `tech_importance` | 3 food, drink, raw, crop, livestock; 6 chemicals, apparel, furniture, toys; 10 electronics and computers; 12 jewelry, watches; 15 cars (15 is ref) |
| `base_tech_level` | 0 for raw, crop, livestock, food, drink; 20 otherwise |
| `w_*`, `demand_per_1000`, L/N | non-consumer products: 0 / 0 / 0 and 0 |
| `plant_month`, `grow_months` | crops: plant 3 (April), grow 5 |

Recipes are reference data (see `docs/recipes.md`), not provisional.

### Calls

1. **Demand unit.** `demand_per_1000` is units per 1000 people **per day**
   (bread 10.0, so a 640k city wants 6,400 loaves a day; cars 0.005, 3.2 a day).
2. **Daily town demand** (provisional formula, ref gives only the inputs):
   `demand = demand_per_1000 × pop / 1000 × (spending / 100) × nec_lux × age`
   - `nec_lux = 0.6 + 0.05 × necessity + 0.05 × luxury × (gnp_pc_index − 1)`, clamped 0.3..1.5
   - `age = 1.0` until the product is obsolete, then 0.8.
   Recomputed in the month pass, stored on `TownMarket`.
3. **Price is a column, not "constant ÷ cost".** The ref's "price =
   constant ÷ cost" has no constant; we use `base_price` from the table,
   and seaport and default sell prices start there.
4. **Initial jitter.** `tech_level = base_tech_level + randint(-4, 4)` and
   initial link score `+ randint(-4, 4)`, both clamped at 0, drawn from
   the game RNG in product-id order at setup.
5. **Tech diffusion.** Yearly pass: a product becomes generally available
   when `corps_with_it × 8 + years_since_discovery > 50` (ref), and is
   marked obsolete (stops quality decay) at the same test.
6. **Quality decay.** Month pass: every job's stock quality ×
   `quality_decay_base` of the class, unless the product is obsolete or the
   class is durable (decay base 1.0).
7. **Product score.** 400 when the product has no links; 0 when it has
   supply but no demand (ref); else `max_score_in` of its links.
8. **Availability** is recursive: a product is available when it is
   raw/crop/livestock/importable, or it has a recipe whose every input
   is available. Discovery also needs every `rnd_prereqs` row researched.
   Computed once at setup and on discovery, with a cycle guard.

### Golden tests

- The db passes the CHECKs; 84 products, 20 classes; 54 recipes whose
  outputs and inputs all exist in `products`; every recipe's quality
  weights sum below 100.
- Bread quality: one cycle from 9 flour at quality 80 with skill 50
  gives 10 loaves at `80 × 0.40 + 50 × 0.60 = 62`.
- Bread in a 640k town at spending 100: demand 6,400 × `nec_lux` (to 1 dp).
- Availability: bread is available iff wheat is; removing the
  flour recipe makes bread unavailable.
- Jitter is reproducible for seed 1 (store a hash of the tech levels).

## Slice 4: firms and jobs

### Classes

- `Firm` base (plain class): id, type, owner corp, tile, town, `size`
  (1 in M1), `slots: list[Job | None]` (9), `links` bitmask (20 bits),
  `ledger`, `land_value`. One subclass per firm type (14):
  `Farm, Factory, DepartmentStore, Restaurant, Mine, OilWell,
  LoggingCamp, ResearchCentre, SoftwareCompany, TVStation, RadioStation,
  Newspaper, Seaport, Headquarters` (names follow `firm_types`).
  A subclass only overrides `daily()` hooks and `allowed_jobs`.
- `Job` base (plain class): `type`, `product`, `stock`, `quality`,
  `unit_cost`, `rating` (1..9), `train_acc`, `staff`, `param1`, `param2`.
  One subclass per job type (15): `CropGrowing, LivestockRaising,
  LivestockProcessing, Extraction, Inventory, PrivateLabelling,
  Manufacturing, Purchasing, Sales, RAndD, SoftwareProduction,
  Advertising, Training`, plus `MediaJob` and `ImportJob`. Each overrides
  `work(day)` and `pull(day)`.
- `Ledger` (plain): 12 categories (0..11, ref); `operating = cat < 9`.
  Slice 4 posts to firm and owner-corp cash; full books are slice 7.

### Tables

- `firm_types(id, name, setup_cost, overhead_month, max_slots, live_inventory, ref, provisional)`
- `job_types(id, name, staff, setup_cost, training_factor, ref, provisional)`.
  The role of this field in daily credit scaling remains unresolved; it isn't
  declared a direct monthly skill-growth rate. Posted training expense remains
  `corp_training_budget × daily_wage / 100.0`, separately confirmed.
- `products` gains `freight_rate` (transport difficulty from SET: Wheat 70,
  Flour 70, Bread 50). It is a coefficient, **not** dollars or a percentage;
  freight uses the separately table-backed `spending_usd` for its price term.
- `firm_job_allowed(firm_type, job_type)`
- `rules` rows (system `jobs`): `sales_mult_store=2`, `sales_mult_other=4`,
  `purchase_every_days=5`, `purchase_order_mult=4`, `train_weekday=2`,
  `train_step=900`, `livestock_scalar=36500`, `wage_per_worker_month=2000`,
  `training_expense_divisor=100.0`, `corp_training_budget_default=10`,
  `freight_distance_value_divisor=100.0`, `freight_multiplier=0.5`,
  `freight_floor_usd_per_unit=0.01`, `ad_budget_min=50000`,
  `ad_budget_max=500000`. The decompiled review supplies the training and
  freight values; the others above are ref except for explicit provisional
  flags. Freight divides the coefficient × distance × unit price by the
  divisor **squared**, then multiplies by 0.5; `0.5` is not the numerator of
  the quotient.

### Calls

1. **Slot grid.** The 9 slots are a 3 × 3 grid; the 20 possible links
   are 6 horizontal + 6 vertical + 8 diagonal neighbours (this is the
   only layout that gives exactly 20). Bit order: horizontals row by row,
   then verticals column by column, then diagonals `\` then `/`, each
   top-left first. A link is undirected; the direction comes from job
   types (an input job feeds a consuming job).
2. **Daily order.** Inside the firm pass (slice 1 order), each firm runs
   slots 0..8: `work()` then `pull()` for each. Daily overhead is not
   posted; overhead posts in the month pass (category 2), prorated
   `days_left / days_in_month` in the first month (ref).
3. **Efficiency** (`docs/reference/gamelogic.md` 558–578). Put the retrieved
   rating table into the db, not Python. At ratings 1..9 its efficiency and
   fixed-credit multipliers are `100,130,160,200,250,300,360,430,500%`
   (also 743–747). Replace the provisional `50 + 5×rating` throughput and
   quality-scaled clamp. For M1, apply this once to the existing provisional
   normalized production bases, not to quality a second time. Keep `/100`
   where a type's expression supplies it (e.g. manufacturing, extraction).
   Software Production instead stays literally
   `min(room, efficiency×capacity)`, **with no added `/100`** (988–994);
   The different equation does not recover native software copy units; the
   cited production-ratio/credit constant also remains unresolved. The
   provisional 76.8-unit result isn't proven original or balanced content.
4. **Storage-capacity inputs remain missing.** Add db lookup
   `rating_storage_multiplier = 8,10,14,16,20,24,30,35,40` and record native
   `base_capacity × type_factor × storage_multiplier` from 580–585, but do
   not apply it yet. Native base and type factors aren't supplied. **Don't**
   multiply the already-normalized provisional product×size×3-day buffer
   by 8..40: it would inflate rating-1 stock eightfold at unchanged input.
   Preserve the current M1 capacity mapping pending real product/type data.
   Livestock yield constants aren't recovered from this table; the `36,500`
   conversion is only a partial interpretation. A rating loss can cause an
   excess-stock write-off (584–585), but its account/cost value is unspecified.
   For extraction, if capacity or efficiency is0 produce0 and draw0 rather
   than divide by0; use efficiency/100 as M1's provisional percentage input.
5. **Wages.** Ref formula, posted once per **job** per day (not per staff):
   `((staff × 2000) / days_in_month × labor_cost) / 100`, integer division,
   **category 1** (Salaries Expense; category 0 is Sales Revenue).
   Our reading of the ref's unnamed `target`: it is the job type's staff
   count, 2000 is dollars per worker per month at labor cost index 100,
   and `labor_cost` is the town's labor cost index (slice 2, 100 at
   start). So a Manufacturing job (24 staff) costs $1,600 a day, or
   $48,000 a month. Media uses `firm.salary` in that payroll formula with
   no training post (615–620). The salary field's actual value and relation
   to the revenue formula's `staff` are unknown—not an original 20 staff.
   **Money units (Esteban, 2026-11-06):** the ref's setup, overhead and
   job setup numbers are in $1000s, but the db stores full dollars with a
   units column saying `usd` (a Department Store is 1,000,000, its setup
   job slots likewise). `overhead` is `usd_per_month` (Esteban,
   2026-11-06): a Department Store costs $1,000,000 to build and pays
   $100,000 a month, a TV Station $20,000,000 and $350,000 a month. It
   posts to category 2 in the month pass, prorated in the first month.
6. **Daily training credits and weekly progression** (730–794 replaces the
   provisional 90%/30%/9000 quota). On every **actual work day**, accrue raw
   credits; then weekly on **weekday2** check **strict** `credits >
   current_rating×900`. One successful check completes **one** staff-count
   step and resets credits exactly to0—never multiple steps or retained
   overflow. After staff-count steps, rating gains1 to max9 and step count
   resets. Staff count is steps per level (765–777), not automatic daily
   credits: Inventory and Advertising with1 step don't get a free credit/day.
   Manufacturing1→2 needs `24×1×900=21,600`;8→9 needs `24×8×900=172,800`.
   Neutral100/day for ten weeks (70 daily events) gives7,000, so no level-up;
   replace the invalid ten-week golden without adding hidden multipliers.
   Exact900 at rating1 doesn't advance. The reference calls negative rating
   loss theoretical (788–793) and provides neither full rewind boundary nor a
   negative credit source for positive working days; don't restore 30% gating.

   **Fixed credits** are Crop20, Livestock10, R&D14 multiplied once by the
   rating percent (739–747). Livestock Raising additionally says "adds10
   training credits per visit" (849). M1 explicitly chooses 10 per actual worked
   visit without multiplying that same10 twice, reserving the source-precedence
   question as provisional. R&D and SoftwareDevelopment share the R&D visit
   credit (963–970), separate from project completion. **Livestock Processing**
   has output at851–860 but no credit constant or numeric work ratio: hold its
   credit progress at0/gated pending research, never alias it to Manufacturing.
   Extraction (864–871) and SoftwareProduction (988–994) name only `production
   ratio` with no numeric coefficient. Hold that credit path too instead of
   borrowing Manufacturing's100/nominal-step proxy. This safe M1 gate isn't a
   claim the original never trains these modes.

   **Work-based raw credits** use actual units without a second rating
   multiplier (749–752):
   - Manufacturing: `actual_units×100 / nominal_step` (906). The denominator
     is computed production step before output/ingredient caps: half of a
     nominal 100 units earns 50 raw credits, not0 under obsolete90% quota.
   - Purchasing: `received×80 / order_size` (934). This credit denominator
     doesn't overwrite separately confirmed freight mechanics: freight is
     `FREIGHT×distance×SPENDING/20,000`, only raw-zero rate floors at
     $0.01/unit. Don't let older generic price text at933 undo that.
   - Sales: `count_sold×100 / cap` (949).
   - Private Labelling: `moved×18 / capacity` (890).
   If a denominator or actual work is0, guard credits at0 defensively; an idle
   visit isn't a successfully processed batch. Actual receipt and stock cycles
   stay separate from credit accumulation.

   **Both result scaling inputs are acknowledged:** the company training
   budget (default10%) and city education for retail-type firms vs a global
   default for others (754–759). Exact divisor/mapping and education field
   aren't supplied here; the current eight town indicators have no education
   field. If M1 uses neutral-at-budget10 or neutral-education interim values,
   make those **provisional db-backed mappings**, not proof the original city
   education is100%. Don't assert `job_types.training_factor` directly drives
   monthly growth; AI firm30-day factors (481–496) are separate. **Confirmed
   daily category3 expense does not change:**
   `corp_training_budget × daily_wage / training_expense_divisor` with db
   budget10/divisor100.0 gives10% actual wages, **$16,791 on April wages of
   $167,910**, independent of provisional credit scaling.
7. **Per-type work** (ref unless marked):
   - Crop: stock grows only in its season; yield factor
     `(climate_dist × −10 + 20) + (moisture_dist × −10 + 20) + soil / 5`,
     daily add `(efficiency × capacity / 100 × yield) / 100`.
   - Livestock raising: shared rule, `min(room, rate × efficiency × capacity / 100)`,
     `rate = 1 / 36500 × capacity` units per day (provisional reading of
     the 36,500 scalar).
   - Extraction: as livestock with rate 1.
   - Inventory, Private Labelling: move stock from the linked job,
     blending quality by quantity; Private Labelling copies the brand
     from its source.
   - Manufacturing (recipes from the ref): daily output units
     `step = (capacity × efficiency / 100) × speed_pct / 100`, rounded
     down to whole cycles of `output_qty`; each cycle consumes `qty` of
     every input, and stops at the first missing input (no partial cycles).
     Output quality per cycle:
     `Σ(input_quality_i × w_i) / 100 + skill × (100 − Σw_i) / 100`,
     where `skill = min(100, corp_tech_level[product])` (provisional until
     R&D lands; the ref names the term but not its source). The new
     batch blends into stock quality by quantity. Unit cost is the
     cycle's input cost plus that day's wages, divided by `output_qty`.
   - Purchasing: every 5 days, order `(efficiency × capacity × 4) / 100`,
     capped by room and by the supplier link quantity; freight is
     category 5 at `(0.01 if raw_rate == 0 else raw_rate) × received_qty`,
     where `distance = |source.x - buyer.x| + |source.y - buyer.y|` and
     `raw_rate = freight_rate × distance × product.spending_usd /
     freight_distance_value_divisor² × freight_multiplier`. The default
     divisor is 100, multiplier 0.5 and zero-only floor $0.01 per unit
     (decompiled review). With those constants,
     `raw_rate = FREIGHT × distance × SPENDING / 20,000`. Positive sub-cent
     rates remain fractional: do **not** use `max(0.01, raw_rate)` or round
     per unit. Calculate independently for each actual receipt using its
     product and each **firm's** stored map coordinate, not town center.
     In-firm slot transfers are not cross-firm purchasing receipts and are
     not charged freight a second time. Preserve full-precision rates until
     the posted expense; do not round individual unit rates. The 2%-of-price
     rule was a provisional fallback, not original mechanics.
   - Sales: daily cap `(efficiency × mult × capacity) / 100`, mult 2 for
     live-inventory firms and 4 otherwise.
   - R&D: raises `corp_tech_level[product]` by 1 per completed project;
     duration from the 0/6/12/24/36/60/120 month table by tech step (ref).
   - Advertising: budget 50k..500k per month; needs a media partner
     firm linked; brand effect lands in slice 5.
   - Seaport `ImportJob`: unlimited stock at `base_price`, quality 50
     (provisional; "High" import quality = 60, Moderate 50, Low 40).
8. **Cut for now.** Firm AI steps (shutdown, price changes, ownership
   moves) wait for slice 9. Firms in slices 4–5 belong to a scripted
   test corp.
9. **Delivery split** is allowed: 4a = Farm, Mine/Oil/Logging, Factory,
   Department Store, Seaport and the jobs they use; 4b = the rest.

### Golden tests

- Wages at labor cost 100 in a 30-day month: Manufacturing (24 staff)
  posts $1,600 a day to category 1; Purchasing (4) $266; Sales (8) $533.
- Slot links: the bitmask for "0–1, 1–2, 4–7" decodes to those edges.
- A wheat farm in season fills to capacity in `ceil(capacity / daily)` days.
- Flour factory fed by a seaport: after 30 days, stock, unit cost and
  quality match stored values for seed 1.
- Training: check strict `credits > rating×900` on weekday2, never `>=`.
  At rating 1, exactly 900 doesn't pass; 901 does one staff step only and
  clears to 0. Neutral 100/day over ten weeks totals 7,000, below the
  Manufacturing first-level 24×1×900 = 21,600; rating 8→9 costs 172,800.
  Half of nominal 100 manufacturing units earns 50 work credits, no old
  90% quota or extra hidden multiplier.

## Slice 5: product links and markets

### Classes

- `Link` (plain class): `seller_job`, `buyer` (a job or a `TownMarket`),
  `product`, `quantity` (units/day), `score`, `weight`, `price`.
- `Market` service: owns the link list per (town, product), runs the
  daily link pass after jobs (slice 1 order) and the monthly roll.

### Calls

1. **All links run daily.** The ref's "15 links per frame" is frame
   slicing, which M1 cut; headless we walk the whole array once per day
   in link-id order.
2. **Score formula.** The ref has two versions. We use the explicit one:
   `score = base + brand × w_brand / 60 + quality × w_quality / 60`,
   where `base = 100 − 50 × price / base_price` (provisional, gives the
   price weight a role), floored at 0. The other version's
   "factor1 / score-in" are taken as the same terms under other names.
3. **Score drop.** Two versions again. We use `quantity × new / old`
   (no unknown scalar), applied when a link's score falls day over day.
4. **Weight is source-contradicted and provisional** (1119–1124 vs
   3356–3362): one source places `+50` at non-farmland, another at
   nondepartment-store retailers. M1 currently chooses non-farmland:
   `weight = min(100, adjust_rate × 5 + (0 if seller is a Farm else 50))`.
   Keep it only as that explicit pending-research interpretation, not a
   resolved native mapping. Growth is proportional to `(100 − weight)`.
5. **Consumer demand moves only on live-inventory links** (department
   store, restaurant). Each day the town's `demand` is split across those
   links by `score²` share (provisional; squaring makes the best store
   win clearly without taking everything). A link's daily sales are
   `min(sales cap, stock, its demand share)`.
6. **Oversupply.** When a town's supply exceeds demand, each link's
   quantity falls by `excess / oversupply_div` per day,
   `oversupply_div = 20` (provisional, 5% a day).
7. **B2B links** (purchasing from another firm) have no consumer
   demand; quantity is the buyer's order, filled in seller-stock order.
8. **Brand.** Each sale nudges brand perception by ±0.1 toward the
   seller's quality (ref); advertising adds `budget / 100000` points a
   month (provisional), capped at 100.
9. **Monthly roll** (ref): links recompute weight, and each product
   publishes `max_score_in`.

Provisional scalars for slice 5 go in `rules` under system `links`:
`price_base=100`, `price_slope=50`, `oversupply_div=20`,
`share_exponent=2`, `ad_brand_per_100k=1`, `weight_nonfarm=50`.

### Golden tests

- Two bread stores in one town, equal price and brand, quality 60 vs 40:
  shares are `score²`-weighted and sum to town demand (to 1 unit).
- Halving one store's price raises its score by 25 (with base_price
  fixed) and its share accordingly.
- Oversupply of 2× demand drains link quantity by 5% a day.
- End-to-end, seed 1: seaport wheat → flour factory → bread factory →
  department store in a 640k town for 120 days; store a state hash and
  the store's revenue, unit cost and brand at day 120.

## Slice 4b: specialized firms and remaining jobs

### Firms and job mapping

Use the firm-to-job table in the reference verbatim. The corrected names
are `ResearchCentre`, `SoftwareDeveloper`, `SoftwarePublisher`, `TVStation`,
`RadioStation`, `NewspaperPublisher` and `Restaurant`; all fourteen types
are subclasses of `Firm`. 4b completes `LivestockRaising`,
`LivestockProcessing`, `PrivateLabelling`, `Research`, `SoftwareDevelopment`,
`SoftwareProduction` and `Advertising`.

**Seaport (reference clarified).** A seaport has **no nine-slot job grid**.
It opens numbered import links per product, with no link cap. The 4a
`ImportJob` objects are the implementation of a link's unlimited supply,
not buildings' consumed slots. Do not allocate ten resources across nine
job slots. Its stock has `quality = import_quality` and unit cost equal to
the catalog's `base_price`. Import supply is unlimited in standard mode;
`importable=0` products must be produced locally. A seaport costs and pays
nothing (`0 / 0`).

**Restaurant (reference).** Run the department-store variants of
`Purchasing` and `Sales` with `live_inventory=True`. It can earn consumer
demand just like a department store. Until prepared-food content exists,
it sells catalog consumer goods; that is simplification, not a new recipe.

### R&D

`Research` and `SoftwareDevelopment` share the same engine; only the
catalog target type differs.

- One active project per job. Parameters are project product, repeat mode
  (0 one-shot) and funded status. Unfunded or paused projects retain progress.
- Prerequisites: every `rnd_prereqs` row for the target must be discovered.
- Duration is **tech-year / 15 years rounded up**, then the reference table:
  `0 -> 0, 1 -> 6, 2 -> 12, 3 -> 24, 4 -> 36, 5 -> 60, 6 -> 120 months`.
  Software uses 0 years (one level per project, 6 months); tech-year 100 is
  a completed sentinel, not a further project (provisional).
- Progress is `(day_serial - start_day) / 30`; complete on crossing the
  duration threshold. A one-shot project then stops; repeat begins the next
  tech level if its prerequisites hold.
- On completion add 1 to the corporation's technology level for that product.
  Manufacturing skill is **no longer** simply catalog tech: it is
  `min(100, hired_manager_manufacturing_skill/2 + own_tech_level)` until people
  (slice 8); with no manager it is `min(100, own_tech_level)` (provisional).
  Current stock does not improve retroactively.
- Newly completed technology propagates from raw materials through recipes
  before consumer-goods projects in that year (matching the reference's
  dependency direction).

### Advertising and media

Media has no discrete nine-slot jobs (603–620). Its direct daily payroll
uses `(firm.salary×2000/days_in_month×town_labor_factor)/100`, with no
training post. The mapping between native `salary` and revenue `staff` is
unknown; the former staff20 is not recovered fact. An Advertising job lives
in a DepartmentStore/Factory and points at a **separate same-town media
firm**, not an invented MediaSales internal slot.

**Initialization (635–641).** Eligible Government corporation4 media gets
random audience10..39 inclusive for its established town/product slot. All
other commercial media start **audience0, reputation100**. Backfill twelve
months with independently random variation of up to±10% from initial audience,
not fabricated prior paid-ad-revenue history.

**Monthly behavior (621–679) in this prescribed order:**

1. Apply random reputation drift up to±30; audience<15 gets an extra boost,
   audience>40 an extra penalty, then clamp [-100,+100]. Extra amounts and
   bounds are **absent**, not simply another identical ±30. Mark any interim
   db fixture provisional and retain this explicit native-input gap.
2. `audience += (random(0..100)+reputation−50)/200`, floored at0, **retaining
   fractional audience**. Exact original random endpoint/type and rounding
   are not fully specified by the "about±0.75" narrative; use one game-RNG
   stream without claiming exact binary RNG equivalence.
3. Positive gains transfer from **same-type, same-town** rivals with aggregate
   share50%; they are not simply free extra audience. Until exact allocation
   is recovered, use a labelled-provisional stable, proportional, nonnegative
   allocator. No second compensation or global reallocation pass.
4. When same-type town total exceeds **90**, the **currently updated firm**
   loses the excess, floored at0. Preserve sequential firm-walk semantics;
   don't claim a synchronous month-end cap is already proven for every firm.
5. Compute **revenue after audience**, then roll twelve-month history and
   current series (621–633):
   ```
   reach = staff * audience / 100
   ad_base = (town_economic_stat / 200) * reach / 100
   revenue_base = town_purchasing_power * ad_base / 100
   seasonal = (seasonal_component + town_stat / 200) * (audience / 100 + 2) / 100
   revenue = max(100, ad_rate * (revenue_base / 1000) * seasonal / 100)
   ```
   Never invert `/200`. Native `staff`, `ad_rate`, economic-stat fields, season
   and purchasing-power mappings are unknown. Any required temporary fixture
   must be explicitly provisional and db-backed, not a guessed mapping to
   existing unrelated town indicators. The other town's economic-stat field
   is also missing in the expected denormalized input table. CPM is
   `revenue×1000/revenue_base`, guarded at denominator0, **not** a second
   revenue multiplier. Direct min100 formula even at audience0 is not already
   proof of a separate paid-ad receipt; don't double-post direct revenue with
   paid category0 without clarifying native ledger mapping.

**Advertising targets and cold start.** Product targeting runs every30 days
and campaign-partner selection every60 days (701–713, 996–1024). Technology is
**strictly >14**, not at least14; target eligibility also depends on rating
being below its target plus an **unspecified threshold**. Leave that amount
unresolved. If no product needs advertising, set0 budget, no $50,000 floor.
A real nonzero budget is bounded **$50,000..$500,000**. Existing last-sales
10% and brand increment `budget/100000` capped at100 remain provisional.
Exact paid campaign posts equal advertiser category6 expense and media
category0 revenue once, never multiplied by displayed CPM again.

For M1, replace provisional `media_min_revenue=10,000` with the newer
701–713 requirement **same-town TV or Newspaper, audience strictly >5**.
Radio still has media audience/revenue, but this selector doesn't include it;
don't silently substitute it. Older lines1004–1011 still mention media revenue
above threshold: a genuine unresolved source conflict. This **provisional M1
choice** uses newer audience eligibility for the cold-start fix, not proof of
native equivalence or complete mapping of older revenue. New commercial
audience0 grows normally past5, then its first paid partner needs no prior
advertising receipt. Follow-up golden should get above5 through deterministic
normal game-RNG growth, reject exactly5, permit only same-town TV/Newspaper,
and replace intentional cold-start xfail with success. Don't preserve it
through fabricated prior category0 income. **This docs PR neither alters
production code nor claims passing tests**; the Programmer reports that
follow-up. Unresolved native values stay explicit, not cleanly-labeled facts.
### Software

Software is an intentionally provisional M1 implementation pending real
content. It is not silently treated as another consumer can:

- A `SoftwareDevelopment` job yields one sellable software product per project.
- `SoftwareProduction` copies it at `min(room, efficiency * capacity)` units
  per day (ref), carrying current quality and consuming daily wages.
- Its catalog price is $100, stock capacity 1,000 units/day, variable copy
  cost $5, software tech 0, and consumer demand 0.1/1000/day (all provisional,
  table-backed). Development copies already completed projects only.
- `Sales` opens consumer links for it. These rules are modular content, easy
  to cut before M3 modern-products work.

## Slice 4b / 5 economy rebalance

### What was measured, and what changes

April (30 days), seed 1, with the earlier 4a postings: bread revenue
**273,577.26**, wages **167,910**, default-budget training **16,791**, overhead
**300,000**, **provisional-model** freight **8,198.40**, imported wheat
**17,820**, loss **−237,142.14**. These explain the old regression only. The
reported freight total does **not** validate reference mechanics: it came from
2% of purchase value, which gives wheat $356.40, flour $1,782 and bread $6,060.

The April receipt links use seaport (204,148) → flour factory (205,148) →
bread factory (206,148) → department store (207,148), each Manhattan distance
**1**. With SPENDING values $0.30/$0.50/$1.50, the raw per-unit freight rates are
respectively **$0.00105 / $0.00175 / $0.00375**, all positive. April freight is
therefore wheat **$187.11**, flour **$311.85**, bread **$757.50**, total
**$1,256.46**. Holding other old-chain quantities fixed gives rounded April loss
**−$230,200.20**. These are formula
results for the current fixture; no raw rate hits the zero floor. This supersedes
both the blanket-floor estimate $5,584 and the $1,131.72 result obtained by
using Wheat's simulated import/resource price $0.10 instead of SPENDING $0.30;
below $0.01 does not mean zero. Distance tests must
include two firms more than one tile apart and across tiles/towns; do not
pretend the three adjacencies validate long-haul costs.

Factory capacity is also wrong as a daily stock cap: it causes a
seaport/ factory to repeatedly over-order cheap bulk inputs.

1. **Keep reference demand and catalog prices.** `demand_per_1000` has the
   reference unit `units_per_1000_people_per_day`, with no multiplier buried
   in `nec_lux`. At index 100 bread is 6,080 units/day for 640,000 people.
   Do not change these rows to force profitability. The original strategy
   is to supply many consumer needs, not to sell increasingly more of one
   product to the same people.
2. **A firm is expensive and must be full.** Firms charge monthly overhead
   regardless of idle slots. A single-line factory and single-line store are
   valid startup fixtures but are not expected to be profitable by themselves.
   No wages or overhead discount for empty slots.
3. **Throughput and stock buffer are distinct.** `base_capacity`
   `base_capacity` is the provisional product-specific production scale,
   but is no longer a daily hard stock ceiling. Each job has:
   - `throughput_per_day = base_capacity * firm.size * job_cap_mult`
   - `stock_buffer = 3 * throughput_per_day`
   Purchasing room and inventory use `stock_buffer`; manufacturing efficiency
   and sales caps use `throughput_per_day`. A day can add a full batch even
   while carrying yesterday's inventory. Recipe inputs follow the same rule.
   This removes the 4a bulk-order feedback without inflating demand.
   Reconcile the db's live `capacity_value_per_day = 60,000` (provisional)
   against slice 3's stale fill-rule `round(20,000/base_price)` explicitly.
   Don't quietly change to20k to contract revenue or retain 60k to manufacture
   a profit. Neither is recovered by the source rating table. Whether the
   provisional coefficient remains 60k or is adjusted needs native input research
   and measured alternate-scaling scenarios, not another ad-hoc revenue scalar;
   mark the mismatch in this docs PR instead of pretending agreement now.
4. **Recipe cost is scale-correct.** Recipe `qty` is input units per **cycle**,
   `output_qty` output units per cycle. Raw-input cost for a cycle is
   `sum(qty * input.unit_cost)`; factory conversion cost is one daily
   manufacturing wage divided by actual units produced that day. Goods sold
   internally at market price cancel in consolidated corporation profit; they
   cannot create profit. Validate every recipe so total reference-priced
   input value per output is <=0.85 * base_price. Any offending recipe is a
   unit-scale issue to report, never silently rewrite reference quantities.
5. **Base-cost call.** Keep the ref's prices and make `base_cost` explicitly
   **default simulated resource cost**, not guaranteed margin. Missing values
   use 60% of `base_price` as now. All provisional quantities are content rows
   with their unit exposed in `rules.md`. There is no extra global
   cost/divisor; that earlier suggestion added an unexplained constant.
6. **Dense layouts.** Canonical plans (slice 6 will serialize these):
   - Food ingredient factories can hold several crops and process several
     different semi-products.
   - Consumer factories combine products sharing ingredients: Bread,
     Chocolate Bar, Cola or Beer can share factory and store overhead, using
     the reference recipes. One firm's up-to-9 slots may contain more than
     one product. A slot is not dedicated to the firm type's first product.
   - Stores buy each product once and allocate remaining slots to its Sales
     job. Six consumer products need twelve Purchasing/Sales slots, so use
     two stores or a selected three/four-product mix, not imaginary slots.
   - Internal supply links point to the job holding the requested product.
     Intermediate stock can be drawn from any valid linked source; the
     source need not be a separate Sales slot when it is a transfer between
     owned production jobs. An outside corporation's Purchasing needs a
     Seller's Sales slot so the seller can post revenue. This is the original
     supply-chain pull, with sales accounting only at actual ownership exits.
     This does not allow arbitrary non-adjacent slots to transfer stock.
7. **No profitability exemption for the old chain.** Keep the exact April
   numbers above in a regression. Add a **dense mixed-product
   corporation** on seed 1 using multiple products per firm, actual reference
   recipes, actual consumer demand, full monthly overhead, wages, freight,
   and intercompany postings eliminated. The golden records total consumer
   revenue, external input cost and all costs before requiring positive
   monthly profit by month 6. Tune only provisional capacity/buffer content
   if necessary and report the final P&L, never reduce reference prices,
   quantities, wages or overhead.

### Link and market fixes for 5

- Link `quantity` is today's intended demand, `quantity_sum` is this month's
  fulfilled daily quantity. Never treat quantity as cumulative stock.
- Consumer demand may only be claimed by live-inventory links. Several Sales
  jobs of the same product in one store split the same market; they do not
  each create a fresh market. No stock, no sale, no brand gain, no ad effect.
- Score uses the provisional price term:
  `price_score = 100 - 50 * link.price/base_price`,
  `score = max(0, price_score + brand*w_brand/60 + quality*w_quality/60)`
  (provisional price term). Do not apply the price weight a second time.
- Sales cap is a throughput cap; retail price can be set per link. For M1 scripted/test firms the default is
  `max(base_price, unit_cost*1.05)` (provisional); tests may set prices
  explicitly. Seaport has no
  markup; manufacturing is where value is created. This makes setting the
  wrong price a real choice, not free guaranteed margin.
- Weight starts at 0 and grows based on sales performance. Score-down
  quantity uses `quantity * new_score / old_score`; overflow supply drops
  by `quantity / 20` daily, matching the provisional oversupply rule.
- `max_score_in` publishes once each month to each product in product-id order.
- All links run each day in link-id order; deterministic floating-point
  accumulations and no `random` outside the game RNG.

## 4b / 5 golden tests

- Seaport opens ten product imports without consuming ten building slots.
- Restaurant buys and sells bread as live inventory with sales multiplier 2.
- A level-up research project: durations 0/6/12/24/36/60/120 from the table;
  prerequisite failure never starts a project; one-shot stops at completion.
- At skill 50, a new Bread batch from quality-80 flour is quality 62; old
  stock never retroactively changes after skill rises.
- Media payroll uses `firm.salary` with no training post; staff20 isn't
  proven. Prescribed direct revenue runs after monthly audience with
  literal divisions, and computed CPM guards0 denominator. Native staff,
  town stat and season mappings stay provisional db-backed fixtures.
  Actual paid $100,000 campaign has equal category6 sponsor expense and
  category0 media receipt once; CPM is never another payable multiplier.
- New commercial TV/Newspaper starts audience0/reputation100. Ordinary
  deterministic game-RNG growth past5 enables initial same-town partner
  without previous ad receipt; exactly5 fails; Radio isn't eligible under
  this newer M1 policy. Only after Programmer implements deterministic
  growth with passing test does this replace deliberate cold-start xfail.
  The docs branch alone doesn't modify code or tests; older1004–1011
  media-revenue threshold at 996–1024 remains a recognized source conflict.
- A software project completes, produces copies at a measured daily rate,
  and cannot sell before that project's completion.
- The April regression retains the old P&L only as evidence of the fallback.
  With actual firm positions and exact products, the corrected fixture posts
  freight **$1,256.46** and loss **−$230,200.20**. Assert all three products
  separately, with positive sub-cent rates preserved and full receipt-detail
  sums per job, not a single total applied arbitrarily.
- Independently test `raw_rate = FREIGHT × distance × spending_usd / 20,000`, a
  positive sub-cent rate that stays sub-cent, and a zero raw rate that becomes
  $0.01/unit. Move a source farther from the buyer to assert freight varies by
  Manhattan tile distance. Round no unit rate to cents. Valid product links
  must never produce negative freight.
- With corp training budget 10 and global divisor 100.0, training = 10% of
  daily wages ($26.60 on a Purchasing wage of $266): assert both db defaults.
  Raw work credits and strict weekday2 staff steps now govern progress;
  Don't assert that `job_types.training_factor` directly drives monthly
  growth. Budget/default10% and education raw mappings/divisors remain
  **explicitly provisional**, separate from this confirmed expense golden.
  Target each training boundary and formula gain by job; no blanket exception.
  Compare alternate efficiency scale tests separately from a rating promotion:
  do not loosen every expectation to rescue accumulated weak work credits.
  Adding Wheat $187.11, Flour $311.85 and Bread $757.50 gives $1,256.46;
  subtracting the April expense categories from its $273,577.25868064887
  revenue yields −$230,200.20131935113, reported to two decimals.
- The dense-mixed-product plan's month-6 P&L reports its consumer revenue,
  external ingredients, wages, training, freight and all overhead, then
  asserts a positive consolidated operating profit.
- Two stores competing for one fixed 6,080-unit/day bread market still sell
  no more than 6,080 units together. Repeated identical stores split demand.
- A factory manufacturing three products uses each reference recipe and
  consumes its declared ingredients exactly once per cycle.
- A one-year stock-flow check: no job has a stock of 3x buffer, reserved
  inputs are never sold twice, and no money is created by internal transfers.
- Full scenario hash for seed 1 at 120 days and repeated runs are equal;
  Pyodide smoke exercises the identical dense scenario and returns its P&L.

## Slices 6 and up

Plans canonicalize and save the dense layouts above; then finance and
corporations. Product/media audience and technology calibrations remain
explicit provisional content until we recover the original set's fields.
