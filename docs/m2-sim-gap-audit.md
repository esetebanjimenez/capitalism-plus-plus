# Milestone 2: sim gap audit (sim vs. original game)

This lists sim rules that are missing or wrong compared with the original
game. It's docs only. Each gap gets its own sim PR later, one rule at a time.

**Compared:** `main` at `29a1828`. The sim code hasn't changed since
`54b8508`, because #77 only changed docs.

**Sources**
- Native: the Ghidra export of `CAPPLUS.EXE` (`capplus_decompiled.c`, cited
  as `decomp:LINE`) and the RE notes (`techspec.md`, `gameloop.md`,
  `save_format.md`, cited as `techspec:LINE` and so on). Constants were
  decoded read-only from the EXE's data object (LE object 2, base `0xa0000`).
  The decoding was checked against two known values: `0xa6e8e` = 20000 and
  `0xa6eca` = 300. A constant listed as "f64" is an 8-byte double. Nothing
  was run, and no original files are in this repo.
- Reference: `docs/reference/gamelogic.md` (cited as `ref:LINE`).
- Sim: `src/capitalism/*.py` and `src/capitalism/data/capitalism.db` (cited
  as `file:LINE` or `db:table`).

**Status**
- **Observed**: read directly in the decompile or an EXE constant this pass,
  with the sim side read too.
- **Inferred**: the native side is shown by structure or field use, but
  part of it rests on a field meaning or a note not re-read this pass.
- **Unknown**: the native value or formula isn't recoverable yet. These
  rows can't be fixed until that changes.

"Fix PR" groups the rows into suggested sim PRs. Each PR should cite its
rows and include a `compare_saves.py` before-and-after where the goldens
move.

## 1. Towns

| # | Rule | Sim now | Native / reference | Status | Fix PR |
|---|---|---|---|---|---|
| T1 | The GNP term in population growth | `town.py:212-221` sets `rolling_gnp_growth` to the year-on-year change in per-capita GNP (a fraction), and `town.py:181` multiplies it by 100 | `decomp:46520` reads `town+0x113[month]` × 100 (`0xa6eb6`). `FUN_0004b377` (`decomp:46454-46467`) writes it as 50 × (this year's 12-month total of pop × per-capita GNP − last year's total) ÷ last year's total. The 50 is `0xa6e9e`, f64. So the term uses total GNP, follows pop, and is about 50× larger | Observed | sim-town-gnp |
| T2 | The GNP term in simple mode | `town.py:197-201` returns before the GNP block, so the term stays 0 | `FUN_0004b377` runs for every town from `FUN_0004daa3` (`decomp:48270-48278`), and that loop doesn't check the detailed flag. Pop growth (`FUN_0004b490`, `decomp:46484`) is also unconditional. Per-capita GNP is constant in simple mode, so the term tracks pop growth | Observed (that the caller is the month pass is Inferred) | sim-town-gnp |
| T3 | Level-up | `town.py:33-38` and `town.py:195`: `level_for_population` can skip levels, can go down, and is capped at `level_max` = 6 (`db:rules towns.level_max`) | `decomp:46538-46542`: +1 per tick only when the frozen flag `+0x1d` == 0 and pop ≥ `L × 80000 × L × 2` (= 160,000·L²). It never goes down and has no cap | Observed | sim-town-level |
| T4 | The town spreads on level-up | Nothing: footprints are a fixed 3×3 or 5×5 (`db:town_footprints`) | `FUN_0004c334` (`decomp:47131`, body 47149-47201): each tile within distance ≤ level of the centre has a 1-in-10 chance per level-up of becoming a town tile. The tile kind affects land value (T10) and where firms can be built | Observed | sim-town-level (sim effect). How it looks is a separate UX call |
| T5 | Pop-growth constants | `db:rules towns.pop_*`, `small_pop`, `large_pop` | `0xa6ea6`=4, `0xa6eae`=100, `0xa6eb6`=100, `0xa6eba`=−150, `0xa6ec2`=750,000, `0xa6ec6`=1,500,000. The formula shape matches `decomp:46516-46537` | Observed: **matches, no change** | — |
| T6 | Monthly per-capita GNP walk | `town.py:205`: `uniform(0.983, 1.013)`, continuous | `FUN_0004b609` (`decomp:46562-46564`): `gnp × (random(10) + 295) / 300` (`0x127` = 295, `0xa6eca` = 300). That gives 10 discrete steps from 295/300 to 304/300 | Observed | sim-town-gnp |
| T7 | Tier floor and tier upgrade | `town.py:206-210`: floor at `tier_gnp.lo` in dollars. The tier keeps rising while GNP > `tier_gnp.hi`, up to tier 3 | `decomp:46565-46572` compares dollar GNP with raw shorts: the floor is `DAT_000adae4` = {0, 10, 35, 70}, and the upgrade happens when GNP ≥ {10, 35, 70, 100}[tier] **and** GNP < `0xa6ece` = 3.0 (f32). It moves at most one tier per month. Read literally, the floor never applies and the upgrade never fires. `techspec:2319-2336` reads these values as tier bounds in $200 units. The decompiler may be misreading an x87 compare, for example `tier < 3` | Unknown (needs a disassembly check) | Hold until resolved |
| T8 | Climate input and scale | `town.py:223-234` compares the per-capita year-on-year change (a fraction) with 0.08 / 0.04 / −0.01 / −0.06 | `FUN_0004b68e` (`decomp:46590-46598`) compares `town+0x113[month]`, the same total-GNP term as T1, with `DAT_000adad0` = {8, 4, −1, −6, −100000} (f32, decoded). The first threshold that's ≤ the value sets index 0 = Boom … 4 = Panic (`techspec:2345-2350`). So Boom needs 50·Δ ≥ 8, which is about a 16% year-on-year rise in total GNP. If nothing matches, the climate stays as it was | Observed (the 16% reading is Inferred from T1) | sim-town-gnp |
| T9 | Land-value base | `world.py:119-122`: `level × per-capita GNP × 50 × small`. `land_value_base_mult` is provisional | `map_land_value` (`decomp:43436-43437`): `(per-capita GNP × 100 / 20000) × pop × 2.5 / 100`, using `0xa6a36`=100, `0xa6a3e`=20000 and `0xa6a2e`=2.5, all f64. That's per-capita GNP × pop ÷ 8000, so it uses **pop**, not level | Observed | sim-land-value |
| T10 | Small-town discount | `world.py:119-121`: ×0.6 when level ≤ 2 (provisional) | `decomp:43397`, `43414` and `43443-43444`: ×0.5 (`0xa6a4e`, f32) when the town's tile is the small-town range `0x3008-0x300c` | Observed | sim-land-value |
| T11 | Land-value cap and floor | `world.py:127` clamps at `land_value_bonus_cap` = 50M (provisional), then floors at 500k | `decomp:43440-43441`: 1e9 (`0xa6a46`, f64) is an **assert** (abort), not a clamp. The floor is 500,000 (`0xa6a52`, `decomp:43446-43447`) | Observed (cap differs, floor matches) | sim-land-value |
| T12 | Land-value decay radius | `world.py:118`: `level + 4` | `decomp:43438-43439`: `level + 4` (`town+0x1e`). This is the **land-value** decay at `techspec:4914`, not town demand. With T3 fixed, the radius grows past 10 | Observed: **matches** | — |

## 2. Stock market and corporate cash

| # | Rule | Sim now | Native / reference | Status | Fix PR |
|---|---|---|---|---|---|
| S1 | Share trades move cash | `stock.py:147-205` only returns the cost or proceeds. `api.py:738-743` (the facade) doesn't post anything. No cash moves | `FUN_0003f240` (`decomp:38300-38447`). A person's wealth `+0x2c` drops by the cost on a buy and rises on a sell (38391-38396). A corp trading another corp's stock moves money with `group_move_balance` between Cash (0) and Stock Assets (4) (38407-38417). The target corp's cash is never touched. The public float moves the opposite way to the trade (38436), and the control check `FUN_00032a14` runs | Observed | sim-share-cash |
| S2 | Trade price | `stock.py:159-160` and `190-191`: old price ± half the impact, which is the average of the old and new prices | Average of the old and new prices × 0.5 (`0xa5e34`); the new price comes from `FUN_0003f68c` (38342-38343) | Observed: **matches** | — |
| S3 | Own-stock buyback | `stock.py:324-336` `ai_buyback` calls `buy_shares` into `holdings_corps[own id]`, so the shares stay in issue | `decomp:38425-38431`: cash drops by the cost, equity (account 6) drops, and `total_shares` falls by the shares bought back, so they're **retired** | Observed (the amount posted to equity is lost to `__CHP`, see U2) | sim-share-cash |
| S4 | New share issue | `stock.py:208-221` returns the proceeds and lowers the price. `api.py:748` posts nothing | `FUN_0004021e` (`decomp:38851-38885`): cash and equity both rise by shares × price, and `total_shares` and the float rise by the new shares | Observed | sim-share-cash |
| C1 | Firm setup cost | `economy.py:318-342` `build_firm` doesn't charge `firm_types.setup_cost`. The facade only shows a shortfall (`api.py:236-239`) | `ref:403`: "Setup cost is a one-time cash payment when the building is placed". `ref:1515-1524`: the AI cancels a build or sells assets when it can't raise the cash. I haven't found the native code that charges it | Inferred (reference doc) | sim-setup-cost |
| C2 | Job setup cost | `firms.py:153-170` `add_job` doesn't charge `job_types.setup_cost` | `ref:540` lists a setup cost per job type. No native charging code found yet | Inferred (reference doc) | sim-setup-cost |
| C3 | Player initial capital | Every corp starts at cash 0 (`firms.py:69`, `economy.py:308-316`) | The default at `g_app+0x196` is float `0x4b189680` = 10,000,000 (`decomp:4518`). The setup dialog edits it as "Initial Capital of Your Corporation" (`decomp:7758`). `ref:19` agrees. I haven't traced where it's credited to the corp | Observed (default value). Where it's credited: Unknown | sim-setup-cost (needs a DB row) |
| C4 | AI starting capital | `ai.py:182-184`: `half + uniform(0, half) × 600000 / 3e6` with half = 1.5M, so $1.5M–$1.8M. It ignores the Competitor Capital setting | `FUN_0007916c` (`decomp:87774-87776`): `(v/2 + random(v/2)) × 6,000,000 / 10`, where v = {10, 15, 20, 30, 60}[Competitor Capital] (`0xae090`, `0xaa498`, `0xaa49c`, setting `DAT_000b1ecd`). That gives $3.0M–$5.4M at Low if `random(n)` returns 0…n−1 (`ref:199-210` says $3M–$6M). It's written to the **person's** wealth `+0x2c`. A non-AI person gets 6,000,000 (`decomp:87771`). Not traced: how that wealth becomes corp cash. Note that `ai.py:220` resets AI cash to $1B every day (`ref:1622-1626`), which hides this gap | Observed (formula). Hand-off to corp cash: Unknown | sim-setup-cost |

## 3. Jobs

| # | Rule | Sim now | Native / reference | Status | Fix PR |
|---|---|---|---|---|---|
| J1 | Throughput base vs. storage ceiling | `jobs.py:83-91`: one `capacity` = `base_capacity × size × cap_mult`, used both for the rate formulas and as the stock ceiling (`room`). `rating_throughput.storage_mult` is loaded (`tables.py:241`) but never used | `FUN_0005dbb7` (`decomp:61852-61856`): efficiency `+0x3e` = `DAT_000add3a[rating]`, storage multiplier `+0x3c` = `DAT_000add4c[rating]` (8…40), ceiling `+0x28` = `+0x30 × vtbl[0x5c]() × +0x3c`. The rate formulas use the base `+0x30`: sales `decomp:58685`, purchasing `55170`, extraction `56367-56368`, software `60212`, livestock processing `52704`. Livestock caps use `+0x30 × +0x3c` (`52320`) | Observed (that `+0x30` = sim `base_capacity × size` is Inferred) | sim-job-capacity |
| J2 | Write-off when the ceiling shrinks | Nothing: `CAT_WRITEOFFS` (`jobs.py:30`) is never posted | `decomp:61857-61861`: when the ceiling drops below stock, (stock − ceiling) × unit cost `+0x34` is posted as expense 7 and stock is clipped | Observed | sim-job-capacity |
| J3 | Extraction training credit | `jobs.py:246-252` gives no credit for Logging, Mining or Oil | `job_extract` `decomp:56375`: `job_add_training(job, units × 100 / max_units, 1)` | Observed | sim-training-credits |
| J4 | Extraction rate | `jobs.py:249`: `extraction_rate` (1.0, provisional) × eff × capacity / 100 | `decomp:56367-56368`: `eff × +0x54 × +0x30 / 100`. `+0x54` is the rate from the resource-table entry, set in `FUN_00057149` (`decomp:56200`) | Observed (the table values are Unknown, see J6) | sim-extraction |
| J5 | Reserve depletion | No reserve. Extraction never runs out | `decomp:56378-56400`: each day the firm's reserve `+0x4e` drops by `units / +0x30 / +0x54 / 100` (`0xa7bd1` = 100). The land value `+0x52` is written down through `FUN_00046fc3`, posted as expense 8, and moved with `group_move_balance(corp, 0, 3)`. At 0 the job stops and a news item is raised (`FUN_00023c7a`, `FUN_00021f7e`) | Observed | sim-extraction |
| J6 | Mine, logging or oil product comes from the deposit | The product is picked freely (`db:job_products` pending, see D1) | `FUN_00057149` (`decomp:56178-56202`) takes the entry in `DAT_000b1c2f` whose short `+0` equals the firm's resource `+0x4c` and whose short `+3` equals the firm type. It sets the product from it, the rate `+0x54` from short `+5`, and `job+0x44` from tile byte `+6`. **Correction:** byte `+6` goes to `+0x44`, which is probably quality, not reserve. The reserve is firm `+0x4c`/`+0x4e`. `DAT_000b1c2f` is a save-game section (`save_format.md:156`), so its entries aren't EXE constants | Observed (lookup). The table's entries are Unknown | sim-extraction |
| J7 | Software Production training credit | `jobs.py:667-680` gives no credit | `FUN_0005bf73` `decomp:60218`: `job_add_training(job, units × 100 / (eff × +0x30), 1)`. Output is `min(room, eff × +0x30)` (60212-60216), with no /100, which matches the sim's form | Observed | sim-training-credits |
| J8 | Livestock Raising herd model | `jobs.py:234-238`: `capacity / 36500 × eff × capacity / 100` added to stock | `FUN_000528ec` (`decomp:52319-52337`) uses two pools. Each day `rec[6] × young / 36500 × f / 100` moves from young `+0x56` to grown `+0x5a`, capped at `+0x30 × +0x3c`. Then young grows by `rec[8] × grown / 36500 × f / 100`, where rec is the livestock record from `0xb1c1c` and f is `+0x5e`. Stock `+0x2c` = rounded (lost to `__CHP`) | Observed (structure; the per-livestock `rec` values are Unknown) | sim-livestock |
| J9 | Which livestock gives which product | `db:livestock_yields`: Cattle (19) gives Leather (23), **Chicken (20) gives Milk (24)**, Sheep (22) gives Wool (25). Pig has no row | `FUN_000529b8` (`decomp:52368-52386`) loops over a product list inside the livestock record (count at `rec+10`, ids at `rec+0xc…`), with month windows at product-record bytes `+4/+5`. The pairs are game data loaded at runtime, not in the decompile | Unknown (the pairs). Chicken gives Milk is **not confirmed and not refuted** | Hold. Don't change it on a guess |
| J10 | Livestock Processing throughput | `jobs.py:368`: `eff × source.capacity × yield / 10000`, with the yield keyed by livestock | `FUN_00052f0c` (`decomp:52704`): `(eff × own +0x30 / 100 × rec[1]) / 100`, where `rec` is the **output** product's record (`+0x16`). In `FUN_00052afc` (`52441-52450`), the amount taken is `min(raising.+0x5e[slot], +0x58, room)` | Observed | sim-livestock |
| J11 | Livestock Processing training credit | None | `decomp:52462`: `job_add_training(proc, ROUND(...), 0)`, fixed-daily mode. The amount is lost to `__CHP` | Observed (a credit exists). The amount is Unknown | sim-training-credits (after U3) |
| J12 | Livestock Processing quality | `jobs.py:377-379` passes the source quality through unchanged | `decomp:52456-52460`: `proc.+0x44 = raising.+0x44 + (proc.rating − 1) × 4`, capped at 100 | Inferred (`+0x44` = quality, the same field `job_livestock` sets as `(rating − 1) × 5 + 30`, `techspec:734`) | sim-livestock |
| J13 | Weekly per-job tech upgrade in Manufacturing | `jobs.py:283-290`: skill = manager ÷ 2 + the corp's tech level. There's no per-job tech | `job_manufacturing_daily` (`decomp:54813-54816`) runs `FUN_0005570e` when `day % 7 == firm % 7`. It compares job `+0x46` with the product's corp tech `+0x66[corp]` and calls `job_upgrade_technology` (`decomp:54841-54864`) | Inferred (that `+0x46` is per-job tech is read from use) | sim-mfg-tech |
| J14 | Purchasing 5-day stagger | `jobs.py:418`: `(day + firm.id) % 5` | `decomp:55155`: `job.+2 % 5 == day % 5` (per job, opposite phase) | Inferred (that `+2` is the job index) | sim-training-credits (small) |
| J15 | How the training credit is scaled | `jobs.py:146-160` scales at train time: credits × budget ÷ 10 × 100 ÷ 100 (provisional, `db:rules jobs.training_credit_*`) | `job_add_training` (`decomp:60774-60780`) scales at credit time: `credit × budget / 100 × education / 100`. Education comes from `FUN_00066a2f` (`decomp:70671-70686`): the town's value for firms on town tiles (lost to `__CHP`), otherwise the global `DAT_000b1b28` | Unknown (education value) | Hold |

## 4. Data tables

| # | Rule | Sim now | Native / reference | Status | Fix PR |
|---|---|---|---|---|---|
| D1 | `job_products` table | Not in the DB, so the picker lists every product | Spec in `docs/m2-job-products.md` (#76). Mining, Logging and Oil pairs come from the deposit (J6) | Observed (missing) | db-job-products |
| D2 | Chicken gives Milk | `db:livestock_yields` row (20, 24) | See J9 | Unknown | Hold |

## 5. Missing daily systems

| # | Rule | Sim now | Native / reference | Status | Fix PR |
|---|---|---|---|---|---|
| M1 | Natural resource discovery | `sim.py:140`: only the `natural_resources` hook, no logic | Daily step 9: `FUN_0007433c` on `0xb1c2f` (`techspec:150`, `gameloop.md:229`). It's quiet until day 365 and then adds deposits (`techspec:198` news). `ref:308` agrees | Inferred (body not re-read this pass) | sim-extraction |
| M2 | Weekly rating decay | `sim.py:132-133`: only the `weekly_ratings` hook, no logic | Daily step 6: `FUN_00075988` on `0xb1c5c`, on weekday 5, decays oversupplied ratings (`techspec:147`, `techspec:152-155`) | Inferred (body not re-read this pass) | sim-ratings |

## 6. Unknown (native formula not recovered)

| # | What | Where | Blocks |
|---|---|---|---|
| U1 | The share-count rounding step in a trade | `decomp:38326` (`__CHP`) | S1 rounding only |
| U2 | The amount posted to equity on a buyback | `decomp:38425-38427` (`__CHP`) | S3 |
| U3 | The Livestock Processing training-credit amount | `decomp:52462` (`__CHP`) | J11 |
| U4 | Livestock stock rounding and the per-livestock record values (`rec[6]`, `rec[8]`, the product lists) | `decomp:52336-52337`, `52363-52386`. The records are runtime data | J8, J9, D2 |
| U5 | Tier floor and upgrade units, and `0xa6ece` = 3.0 | `decomp:46565-46572` | T7 |
| U6 | Town education for training | `decomp:70680` (`__CHP`), `DAT_000b1b28` | J15 |
| U7 | `DAT_000b1c2f` resource-table entries (product, firm type, rate) | Save-game section `0x1011` | J4, J6 |
| U8 | Where the initial capital and AI person wealth become corp cash | Not traced | C3, C4 |

## Not audited in this pass

Overhead and wages, freight (the sim already cites `FUN_000785f1`), market
share and consumer demand, goals, and the AI. They need their own pass.
Sales, purchasing and manufacturing rate formulas match in form. The only
gap found there is the capacity base (J1).

## Reference-doc rows (Game Designer)

_For the Game Designer: add the rules that come from
`docs/reference/gamelogic.md` and other reference docs here, in the same
table format._

| # | Rule | Sim now | Native / reference | Status | Fix PR |
|---|---|---|---|---|---|
