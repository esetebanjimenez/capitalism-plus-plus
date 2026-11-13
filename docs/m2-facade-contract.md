# Milestone 2: `capitalism.api` facade contract

This is the fixed list of queries and commands the M2 panels need. Every
entry comes from a panel in `docs/m2-ux-spec.md`, and the field names are
the M1 model names on main (`src/capitalism/`). The facade only reads and
wraps existing state; it adds no game rule. Where M1 has no entry point
yet, the entry is marked **wrapper**: a thin function over existing state,
and any rule it turns out to need goes to its own sim PR.

## Conventions

- Calls cross the worker boundary as JSON. Every object is referred to by
  id: firm `Firm.id`, town `Town.id`, corporation `Corporation.id`
  (player is corp 0), product `Product.id`, link `Link.id`, slot 0 to 8
  (row × 3 + column).
- Money is full dollars, as stored in the DB. Dates are `day_serial`; the
  client formats them.
- `query(kind, args)` returns a plain snapshot. It never changes state and
  may run while the sim is paused.
- `command(kind, args)` returns `{id}` at once; the client shows the
  pending badge for that id. When the sim applies it at the next tick it
  posts `{id, ok: true, result}` or `{id, ok: false, error}`, where
  `error` is a short player-facing reason (shown in the toast).
- Each tick the worker posts `tick {day_serial, cash, speed,
  unread_important, map_rev}`, which is all the status pill and menu badge read.
  `map_rev` is a counter that moves when a firm is built or removed or a town
  changes level (which is when `spread_town` repaints tiles); when it moves the
  map view calls `map_objects` with the `map_rev` it last drew.
- Lists of 12 are month rings in M1 order; the client labels them.

## Queries

| Query | Inputs | Returns | Used by |
|---|---|---|---|
| `map` | none | `width`, `height`, `map_rev`, per tile `kind`, `ref`, `town_kind` (native town tile kind: urban 0x3000–0x3007, rural 0x3008–0x300c, else 0; a firm tile reports the town tile it stands on); towns `id`, `name`, `x`, `y`, `level` (`radius` and `block_level` from `town_footprints` are legacy; the client draws the urban and rural tile kinds from #302 instead); firms `id`, `x`, `y`, `type_id`, `owner` | Map view, town tiles |
| `map_objects` | `since` (a `map_rev`, default -1) | `map_rev`, towns and firms as in `map`, and `changes`: `[[index, kind, ref, town_kind], ...]` for tiles changed after `since`. When `since` is -1 or older than the last 64 revisions, `changes` is null and `kind`, `ref` and `town_kind` hold the whole map | Map view redraw |
| `overlay` | `layer`: `land_value`, `soil`, `rainfall`, `climate` or `ownership` | One value per tile (firm owner per firm for `ownership`), plus `min` and `max` for the legend | Map overlays |
| `tile` | `x`, `y` | `kind`, `soil`, `rainfall`, `moisture`, `climate`, `land_value` (`World.land_value`), `can_build` (`World.can_build`), nearest `town` id | Tile card |
| `build_options` | `x`, `y` | Per buildable firm type: `type_id`, `name`, `setup_cost`, `land_value`, `build_cost` (setup + land), `overhead_month`, `affordable`, `shortfall` (0 when affordable; when above 0 the type can't be built) | Build panel |
| `town` | `id` | `name`, `level`, `population`, `gnp`, `per_capita_gnp`, `unemployment`, `labor_cost`, `labor_quality`, `consumer_spending`, `climate`, `pop_ring[12]`, `gnp_level_ring[12]` | Town card |
| `town_market` | `id` | Per consumer link: `link`, `product`, seller `firm` and `corp`, `price`, quality, `brand`, share of demand | Town card, Market tab |
| `firm` | `id` | `type_id`, `name`, `town`, `owner`, `x`, `y`, `land_value`, `created_serial`, `max_slots`, `allowed_jobs`, `slots[9]` (each null or `job_type`, `product`, `rating`, `stock`, `capacity`), `edges` (decoded `Firm.links` as slot pairs), `ledger` (`cash`, `month[12]`, `last_month[12]`, `year[12]`); media firms add `audience`, `reputation`, `revenue_month[12]` | Firm detail, Layout and Firm tabs |
| `job` | `firm`, `slot` | `job_type`, `product`, `rating`, `train_credits`, `train_threshold` (the weekly threshold), `train_progress`, `staff`, `stock`, `capacity`, `quality`, `unit_cost`, `price`, `is_selling`; manufacturing adds `inputs` (product, needed, in stock); R&D and Software Development add project progress | Slot card |
| `job_options` | `firm`, `slot` | Per allowed job type: `job_type`, `name`, `staff`, setup cost, and the `products` that job can handle (from `job_products`, see `docs/m2-job-products.md`) | Job picker |
| `firm_links` | `id` | `buying` and `selling` lists; each row: `link`, `product`, other end (`firm` and `town`, or `consumers` with town id), `price`, `quantity`, `score`, `brand`, this month's `units` and `money` (`units_month`, `money_month`) | Links tab, map link lines |
| `suppliers` | `firm`, `slot` | Selling jobs for that job's product: `firm`, `slot`, `corp`, `town`, `price`, `freight` estimate, `delivered_cost`, `quality`; sorted by delivered cost then quality | Supplier picker |
| `corp` | `id` | `name`; `revenue`, `operating_expenses`, `operating_profit`, `other_profit`, `net_profit`; `ledger` (`cash`, `month`, `last_month`, `year`); `by_firm` (firm id with its ledger); `total_assets`, `liabilities`, `net_worth`, `credit_limit`; `interest_rate` (global); `month_history`, `year_history`. Own corp only: `technology`, `training_budget`, `brand_strategy`, `dividend_ratio`, `dividend_auto` | Company report |
| `stocks` | none | Per corporation: `corp`, `name`, `price`, `pe_ratio`, player's owned percent, value of the player's holding | Stock list |
| `stock` | `corp` | `price`, `pe_ratio`, `daily_prices`, `monthly_prices`, `yearly_prices`, `total_shares`, `public_float`, `dividend_yield`, shareholders (`kind` corp or person, `id`, `name`, `shares`, percent, value); for the player's own corp, maximum issuable shares | Stock page |
| `trade_quote` | `corp`, `side` (`buy`, `sell` or `issue`), `shares` | Estimated cost or receipt including `price_impact`, resulting ownership percent, and the allowed range of `shares` | Trade and Issue sliders |
| `news` | `corp` (optional), `category` (optional), `since` (day serial, optional) | Newest first: `day_serial`, `category`, `corp_id`, `news_type`, `details`, `important`, and the headline text | News |
| `goals` | none | `result` (`GameResult`), rows from `check_goals` (`name`, `target`, `current`, `met`, only targets above zero), years played, year limit, `difficulty` (`compute_difficulty_rating`), `score` (`compute_final_score`) | Goals, result card |
| `plans` | `firm_type` | Plans in `PlanLibrary.folder_for(firm_type)`: index, `description`, slot preview (`job_type`, `product_id`), `connection_mask` | Plans browser |

## Commands

| Command | Inputs | Result | Sim entry |
|---|---|---|---|
| `build_firm` | `firm_type`, `x`, `y` | New `firm` id | `Economy.build_firm` |
| `demolish_firm` | `firm` | none | **wrapper** |
| `add_job` | `firm`, `slot`, `job_type`, `product` | none | `Firm.add_job` |
| `remove_job` | `firm`, `slot` | none | **wrapper** |
| `link_slots` | `firm`, `a`, `b` (neighbours) | none | `Firm.link_slots` |
| `unlink_slots` | `firm`, `a`, `b` | none | **wrapper** |
| `set_price` | `firm`, `slot`, `price` | none | **wrapper** (sets `Job.price`) |
| `link_b2b` | seller `firm`, `slot`; buyer `firm`, `slot` | New `link` id | `Economy.link_b2b` |
| `link_consumer` | `firm`, `slot` | New `link` id | `Economy.link_consumer` (firm's own town) |
| `remove_link` | `link` | none | **wrapper** |
| `borrow` | `amount` | none | `Corporation.borrow` |
| `repay` | `amount` | Amount actually repaid | `Corporation.repay` |
| `buy_shares` | `corp`, `shares` | Total cost, taken from cash; refused when cash is short. Buying your own corp's shares is a buyback that retires them | `Economy.buy_stock` |
| `sell_shares` | `corp`, `shares` | Total proceeds, added to cash | `Economy.sell_stock` |
| `issue_shares` | `shares` | Amount received, added to cash | `Economy.issue_stock` |
| `set_training_budget` | `amount` | none | **wrapper** (sets `training_budget`) |
| `set_brand_strategy` | `strategy` | none | **wrapper** (sets `brand_strategy`) |
| `set_dividend` | `ratio`, `auto` | none | **wrapper** (sets `dividend_ratio`, `dividend_auto`) |
| `capture_plan` | `firm`, `description` | Plan index | `plans.capture`, then `PlanFolder.add` |
| `apply_plan` | `firm`, `plan` (index) | none | `plans.apply_plan` |
| `set_speed` | `speed`: pause, 1, 2, 3 or max | none | Worker only, not the sim |

All commands act as the player (corp 0). A command that fails a check the
sim already makes (for example `can_build`, `allowed_jobs`, an occupied
slot, a SEC refusal or not enough cash) returns `ok: false` with that
reason instead of throwing. For `build_firm`, not enough cash means cash below setup cost plus
land value, with credit not counted (audit #87).

## Not in this contract

Save and load, new game setup and settings (out of scope for the UX spec).
News read state is UI-only and lives in the client save, not the facade.
