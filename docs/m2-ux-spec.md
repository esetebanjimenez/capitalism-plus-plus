# Milestone 2: UX spec

Status: proposal for review. Docs only. It covers the screens M1 cut: the
map, firm detail with its 9-slot job grid and links, financial reports,
news, the stock market and goals. Each screen says what it shows, how touch
and mouse drive it, and which sim data it reads.

M1 is the baseline. Nothing here changes a sim rule. Every action below goes
through the command queue in `docs/m2-frontend-plan.md` (applied at the next
day boundary), and every screen reads through that plan's `query` /
`subscribe` views. Field names are the M1 attributes they come from, so the
`capitalism.api` facade can map them one to one. Look and feel (palette,
tile and icon sizes, the cream card panels) follow the Artist's
`docs/art/visual-direction.md`; this spec only sets layout and behavior.

## Shared rules

- **Targets.** Every tappable thing is at least 44 × 44 CSS px. On the map
  at any zoom a tap snaps to the nearest firm or town within 24 px, since a 32 px firm tile is below the 44 px minimum.
- **Mouse equivalents.** Tap is left click, long-press is right click, the
  sheet's drag handle is a resizable panel edge. Hover shows the same
  tooltip a long-press shows on touch. Keyboard: Space pauses, 1 to 4 set
  speed, Esc closes the top panel.
- **Numbers.** Money shows a sign and a unit (`+$12,340`, `−$4.1M`), never
  colour alone. Percentages show one decimal. Values the sim marks
  provisional are shown normally; this is a player UI, not a debug view.
- **Confirmations.** Anything that spends more than 10% of player cash,
  demolishes, or changes brand strategy (which resets brand ratings,
  reference "Corporation internals") asks once before it is queued.
- **Pending commands.** A queued command shows a small clock badge on the
  thing it changes until `cmd_result` arrives. An error result shows a
  toast with the sim's message and rolls the badge back.

## Screen layout: the map stays clear

Esteban's call (2026-11-11): no extra zoom level; instead nothing covers the
map permanently. The map always fills the whole screen, and panels appear
only while they are needed. Dismissing a panel returns the full map.

### Default state: minimal HUD

With nothing selected, only two small floating controls sit over the map.
Both are translucent cream with an ink border and do not reserve a strip of
screen.

- **Status pill**, top left, 40 points tall: date
  (`calendar.year/month/day`), player cash (`Corporation.ledger.cash`) and
  one speed button showing the current speed. Tapping the speed button
  pauses and resumes; long-press (or click its arrow on desktop) opens a
  small picker: pause, 1, 2, 3, max. Speed is a target days per second
  owned by the worker.
- **Menu button**, bottom right, 48 × 48 points. It opens the menu panel
  with Company, Stocks, News and Goals. A badge on it counts unread
  important news items.

Toasts (important news, command errors) slide in under the status pill for
4 seconds and never block taps on the map.

### Panels and what opens and closes them

Only one panel is open at a time; opening another replaces it. Every panel
closes on swipe down (phone), its close button, Esc, or a tap on empty map
outside it, except the build panel, which a map tap does not close (see
below).

| Panel | Opens when | Closes when | Phone height |
|---|---|---|---|
| Tile card | Tap empty land | Any of the above; Build swaps it for the build panel | Peek |
| Build panel | Build on the tile card, or long-press / right click on empty land | Build confirmed (then firm detail opens on the new firm), Cancel, Esc | Half |
| Town card | Tap a town | Any of the above | Peek, drag to half |
| Firm detail | Tap a firm, or a firm name in any list | Any of the above; tapping another firm swaps it in place | Peek, drag to half or full |
| Menu | Menu button | Picking an entry, or any of the above | Small, just the four entries |
| Company, Stocks, News, Goals | Picked from the menu (desktop also C, S, N, G) | Any of the above | Full |

While a peek or half panel is open, the rest of the map stays live: pan,
pinch and tap work as normal, and tapping another firm or town swaps the
panel's contents. When a selection opens a panel, the map pans so the
selected tile sits in the visible area above (phone) or beside (desktop)
the panel. Jumping to a firm from a full report closes the report, centres
the map on the firm and opens its firm detail at peek.

While the build panel is open, the chosen tile stays outlined and a map
tap moves that outline to the tapped tile if it is buildable, so the
player can compare spots without reopening the panel.

### Phone versus desktop

- **Phone** (under 720 points wide): panels are a bottom sheet with a drag
  handle and three heights: peek (about a quarter of the screen: title, key
  numbers, main actions), half, and full. Full-height reports cover the map
  until dismissed.
- **Phone menu button**: while a sheet is open at peek or half height, the
  menu button sits just above the sheet's top edge, still on the right; at
  full height it hides until the sheet is lowered or closed.
- **Desktop** (720 points and wider): panels slide in as a right-hand side
  panel 400 points wide over the map; the map does not resize, it only pans
  so the selection stays clear of the panel. Company, Stocks, News and Goals
  open as a centred window up to 960 points wide, closed with Esc or its
  close button. The panel edge can be dragged wider.
- **Desktop menu button**: while the side panel is open, the menu button
  moves to sit just left of the panel's edge, still at the bottom, so the
  panel never covers it (approved with the UI concept, PR #65).

### Tiles visible

Tiles are 32 points on screen at standard zoom on every device (the 64 px
art for high-density screens draws in the same 32 points, so counts do not
change). Counts are whole tiles, rounded down. Floating HUD controls sit over the map and are not subtracted.
Reference viewports: phone 390 × 844 points portrait, desktop browser
viewport 1920 × 960.

| View | No panel | Peek panel | Half panel | Full panel / report |
|---|---|---|---|---|
| Phone, portrait | 12 × 26 | 12 × 19 | 12 × 13 | Map hidden |
| Phone, landscape | 26 × 12 | 26 × 9 | Not offered | Map hidden |
| Desktop | 60 × 30 | 47 × 30 (side panel) | Same as peek | Report window over the map |

Phone landscape has only peek and full, since a half sheet would leave six
rows of map. The optional zoomed-out "survey" step discussed on 2026-11-11
is out of scope for M2; the far overview zoom below stays as specified.

## 1. Map view

The home screen.

**Shows.** The 240 × 198 tile map: tile kind (`Tile.kind`: deep ocean,
water, grassland, forest/hill, town, firm), towns with name labels, firms as
one tile each with an owner-colour flag (`Firm.owner`), and the player's
selection outline.

**Zoom.** Zoom is counted in points, so a step looks the same on every
screen. The standard view draws a tile in 32 points, which is about 12
tiles across a 390-point phone. The art is B+ (decided 2026-11-10), drawn
at 64 px with the 32 px set kept (decided 2026-11-11):

| Screen density | Art sheet | Art pixel to screen pixel |
|---|---|---|
| 1× | 32 px | 1:1, exact |
| 2× | 64 px | 1:1, exact |
| 3× | 64 px | 1:1.5, nearest-neighbour (slightly uneven pixels, accepted by Esteban) |

Two levels: far (1 px per tile overview, no sprites) and standard. There is
no closer zoom, and no zoomed-out viewing step for now. Pinch or mouse
wheel switches between them. Pan by one-finger drag or mouse drag.

**Town footprint (visual only).** The sim stores a town as one tile, so the
footprint is drawn by the client and changes no rule. By `Town.level`:
levels 1 to 2 draw the town tile only, levels 3 to 4 a 3 × 3 area centred on
it, levels 5 to 6 a 5 × 5 area. At 3 × 3, roads form a plus through the
centre. At 5 × 5, roads run along rows and columns 1 and 3 (a # shape)
and the town's own centre tile is a plaza. City blocks fill the rest; roof style is chosen per tile
from the town id so a town keeps its look, and the block level steps up at
levels 3 and 5. The radius per level lives in a small DB table so it can be
retuned. Firms always win: ring tiles stay buildable, a firm tile never gets
a block drawn on it, and tapping a ring tile opens the real tile card with
Build. This is a design call; the reference draws a town as one tile in 13
variants (`docs/reference/gamelogic.md`, tile categories) and shows a
town's reach through land value.

**Overlays** (a toggle in the map's corner, one at a time, drawn on the standard zoom): none, land value
(`World.land_value(x, y)`), soil, rainfall, climate (`Tile.soil`,
`Tile.rainfall`, `Tile.climate`), and ownership (tints firms by owner).
Overlays show a legend with the value range.

**Interactions.**

| Input | Result |
|---|---|
| Tap a firm | Opens firm detail at peek height |
| Tap a town | Opens the town card (below) |
| Tap empty land | Shows the tile card: kind, land value, soil, rainfall, and a Build button when `World.can_build(x, y)` |
| Long-press empty land / right click | Opens the build menu directly |
| Two-finger drag / middle drag | Pans without selecting |

**Build menu.** Lists the firm types the player can build on that tile
(the 14 rows of `firm_types` minus Seaport and the government-only media
rows the sim rejects), each with its build cost (setup cost plus the tile's
land value) and monthly overhead (`firm_types.setup_cost`, `overhead_month`).
A type the player can't afford (cash below setup cost plus land value; credit
doesn't count) is shown greyed with the shortfall in red and can't be chosen, as in
the original (audit #87: `FUN_000698e0` clears the Build button's enable
flag). Choosing a type queues `build_firm`.
After a successful build, firm detail opens on the new firm.

**Town card.** The eight city indicators from the reference "City
indicators": population, GNP, per capita GNP, unemployment, labor cost,
labor quality, consumer spending and economic climate (`Town.population`,
`Town.gnp`, `per_capita_gnp`, `unemployment`, `labor_cost`, `labor_quality`,
`consumer_spending`, `climate`), plus the two 12-month charts for
population growth and GNP growth (`Town.pop_ring`, `Town.gnp_level_ring`).
A Market tab lists products sold in the town with each consumer link's
price, quality, brand and share, from the town market's live links.

## 2. Firm detail

Opens from the map or any firm name (see the panel table above). Phone: bottom sheet. Desktop: side
panel. Three tabs: Layout, Firm, Links.

### Layout tab: the 9-slot job grid

**Shows.** A 3 × 3 grid of slots (`Firm.slots`, slot = row × 3 + column).
Each filled slot shows its job type icon, its product (`Job.product.name`),
its rating (`Job.rating`, 1 to 9) and a small stock bar (`Job.stock` over
`Job.capacity`). Empty slots show a plus. Lines between slots show the
internal connections decoded from `Firm.links` over the 20 neighbour edges
(`SLOT_EDGES`: horizontal, vertical and both diagonals). Links are
undirected: draw a plain line with no arrowhead. Which way stock moves is
decided by the job types at each end, not by the link (see
`docs/m2-view-briefs.md`).

Media firms (`max_slots = 0`) have no grid; the Layout tab is replaced by a
Media tab showing audience, reputation and monthly revenue. Seaport shows
its import jobs as a list, not a grid.

**Interactions.**

| Input | Result |
|---|---|
| Tap an empty slot | Job picker: only `Firm.allowed_jobs` for this firm type, each with staff and setup cost, then a product picker filtered to products that job can handle |
| Tap a filled slot | Slot card (below) |
| Drag from one slot to a neighbour | Queues a connection between them (`link_slots`). Non-neighbour drops are refused with a short shake |
| Tap a connection line | Offers Remove connection |
| Long-press a filled slot / right click | Remove job, with confirmation |

Desktop also accepts click one slot then click a neighbour to connect.

**Slot card.** Job type, product, rating and training progress toward the
next level (`Job.train_credits` against the weekly threshold, shown as a
bar, plus `Job.train_progress` steps), staff (`Job.staff`), stock and
capacity, quality (`Job.quality`), unit cost (`Job.unit_cost`) and, for
selling jobs, price (`Job.price`) with a price field. Changing the price
queues a price command. Manufacturing also shows its recipe inputs and
whether each is in stock. R&D and Software Development show project
progress.

**Plans.** A Plans button on the Layout tab offers Save layout as plan
(`plans.capture`) and Apply plan (`plans.apply_plan`), browsing the plan
folder for this firm type (`PlanLibrary.folder_for`). The browse view
shows the plan's grid preview, not a separate editor dialog.

### Firm tab

Firm type, town, owner, land value (`Firm.land_value`), opening date
(`Firm.created_serial`), and this month, last month and year to date
revenue, expenses and profit from `Firm.ledger` (`month`, `last_month`,
`year`), broken down by the 12 posting categories (below). Buttons:
Demolish (confirmation) and, for the player's own firms, Advertising
partners where the firm type allows it.

### Links tab

Every product link touching this firm. Two lists: Buying (links where one
of this firm's jobs is the buyer) and Selling (links where it is the
seller, including consumer links to the town).

Each row: product, the other end (firm name and town, or "Consumers in
<town>"), price (`Link.price`), quantity (`Link.quantity`), score
(`Link.score`), brand (`Link.brand`) and this month's units and money
(`Link.units_month`, `Link.money_month`).

| Input | Result |
|---|---|
| Tap a row | Opens the other firm's detail |
| Add supplier (on a buying job) | Supplier picker: firms selling that product, sorted by delivered cost (price plus freight estimate) then quality; picking one queues `link_b2b` |
| Sell to consumers (on a Sales job in a store) | Queues `link_consumer` for the firm's town |
| Swipe a row left / right click | Remove link, with confirmation |

On the map, while a firm is selected, its links draw as lines to the other
firms so the supply chain is visible.

## 3. Financial reports (Company)

The player corporation's books. Tabs: Income, Balance, Loans, Charts,
Corporation.

- **Income.** Revenue, operating expenses, operating profit, other profit
  and net profit (`Corporation.revenue`, `operating_expenses`,
  `operating_profit`, `other_profit`, `net_profit`), with a per-category
  table for this month, last month and this year. Category names are fixed
  by the ledger: 0 Sales revenue, 1 Salaries, 2 Overhead, 3 Training,
  4 Purchases, 5 Freight, 6 Advertising, 7 Write-offs, 8 Raw material,
  9 Loan interest, 10 Stock return, 11 Land value. A By firm toggle
  shows the same table per firm (`Firm.ledger`), tap a firm to open it.
- **Balance.** Cash, total assets, liabilities and net worth
  (`ledger.cash`, `total_assets`, `liabilities`, `net_worth`).
- **Loans.** Total loan, monthly interest, credit limit (`credit_limit`)
  and the global interest rate, with Borrow and Repay sliders that queue
  `borrow` / `repay`. The reference "Bank loans" panel layout.
- **Charts.** Line charts for revenue, operating profit, other profit,
  expenses and net worth, with Past 12 months (`month_history`) and Past
  years (`year_history`) tabs. Tap or hover a point for its value.
- **Corporation.** Technology per product (`Corporation.technology`),
  training budget (`training_budget`) with an editor, brand strategy
  (`brand_strategy`, with the reset warning), dividend ratio and auto
  dividend (`dividend_ratio`, `dividend_auto`).

Rivals' Income and Charts tabs are viewable from the stock market; their
technology stays hidden, as the reference marks it confidential.

## 4. News

A feed plus filters, after the reference "News Report panel".

**Shows.** Items from `NewsLog.items`, newest first. Each row: date
(`NewsItem.day_serial`), a category icon (Normal, Financial, Technology,
Special from `NewsItem.category`), the corporation if any (`corp_id`) and a
one-line headline built from `news_type` and `details`. Important items
(`NewsItem.important`) are bold and drive the badge on the menu button.

**Filters.** Corporation (all or one), category (all or one) and time
(this month, this year, all). On phone the filters are chips above the
list; on desktop, three columns as in the reference.

**Interactions.** Tap an item to jump to what it names: the firm on the map,
the corporation's stock, or the product's market. An important item also
shows as a toast for 4 seconds when it arrives; tapping the toast opens it.
Opening News marks items read; read state is UI-only and lives in the save
file, not the sim.

## 5. Stock market

After the reference "Stock Market screen".

**Shows.** A list of all corporations with price (`Stock.price`), P/E
(`Stock.pe_ratio`), the player's owned percentage and stock value. Tap one
for its page: price chart with Day, Month, Year tabs (`daily_prices`,
`monthly_prices`, `yearly_prices`), shares outstanding (`total_shares`),
public float (`public_float`), dividend yield, and the shareholder list
(corporations and persons from `holdings_corps` / `holdings_persons`) with
quantity, percentage and value.

**Trading.** Buy and Sell sliders in whole shares, bounded by the public
float for buys and the player's holding for sells. While dragging, show
the estimated cost including price impact (`stock.price_impact`) and the
resulting ownership percentage. Confirm queues `buy_shares` / `sell_shares`.
If the sim reports a SEC rule refusal, the toast shows its reason.

**Own company.** On the player's own stock page, an Issue shares action
shows shares outstanding, price, maximum issuable and expected receipt
before queueing `issue_shares`.

## 6. Goals

**Shows.** The scenario's active goals from `check_goals`: each row is a
goal name, its target, the current value and a met flag, as a progress
bar. Only goals with a target above zero appear. Below the list: years
played against the year limit, the difficulty rating
(`compute_difficulty_rating`) and the current score estimate
(`compute_final_score`).

**Interactions.** Tap a goal to open the screen that moves it: net worth and
revenue goals open Company, stock price and ownership open Stocks, product
class and type counts open the product list in Company. When the game ends
(`GameResult` win or loss) a full-screen result card shows the outcome and
final score, with New game and Keep playing where the rules allow it.

## Data the facade must expose

The full contract, with inputs and return fields for every query and
command, is `docs/m2-facade-contract.md`. In short, the `query` kinds
this spec needs, for `capitalism.api`:

| Query | Reads |
|---|---|
| `tile {x, y}` | `Tile` fields, `land_value`, `can_build` |
| `town {id}` | `Town` indicators and rings, town market links |
| `firm {id}` | `Firm` fields, slots and decoded links, ledger, links in and out |
| `job {firm, slot}` | `Job` fields and recipe stock state |
| `suppliers {firm, slot}` | Selling links and jobs for that product |
| `corp {id}` | Corporation statement, histories, technology (own corp only) |
| `stocks` / `stock {corp}` | `Stock` fields and histories |
| `news {corp, category, since}` | Filtered `NewsLog` items |
| `goals` | `check_goals` results, difficulty, score estimate |
| `plans {firm_type}` | Plan folder contents |

Commands: `build_firm`, `demolish_firm`, `add_job`, `remove_job`,
`link_slots`, `unlink_slots`, `set_price`, `link_b2b`, `link_consumer`,
`remove_link`, `borrow`, `repay`, `buy_shares`, `sell_shares`,
`issue_shares`, `set_training_budget`, `set_brand_strategy`,
`set_dividend`, `capture_plan`, `apply_plan`. Where M1 has no player entry
point for one of these yet (for example demolish or remove link), the
facade adds a thin wrapper over existing state changes, and any rule it
would need goes to its own PR, not this milestone.

## Out of scope for this spec

Main menu, new game setup screen, save and load UI, settings, tutorial and
sound. They get their own short spec once these screens are agreed.
