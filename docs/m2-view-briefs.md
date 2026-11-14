# M2 view briefs

One short brief per view, written before the art is drawn. Each says what the
view shows and how the rules under it work, so the art doesn't promise
something the sim doesn't do. Layout and interactions stay in
`docs/m2-ux-spec.md`; look and palette stay in `docs/art/visual-direction.md`.

## 1. Job links (Firm detail, Layout tab)

### What it shows

The firm's 3 × 3 slot grid and the internal links between neighbouring slots.
It answers two questions for the player: which jobs are connected, and is
anything starved or backed up?

### How the rules work

- **A link is undirected.** `Firm.links` is a bitmask over the 20 neighbour
  edges (`SLOT_EDGES`; horizontal, vertical and both diagonals). Each edge is
  stored as `(min, max)` and `link_slots(a, b)` equals `link_slots(b, a)`
  (`src/capitalism/firms.py`). Nothing on the link records a direction.
- **The job type decides who pulls.** Each day, when a job's work step
  returns nonzero, the job runs its take-linked step against every linked job
  (gamelogic.md, "Step 6: Supply chain pull"):
  - Inventory, Private Labelling and Sales pull stock of their product from a
    linked job and blend quality.
  - Manufacturing pulls recipe ingredients that are below need, when the
    source is full or on day-of-week 0.
  - Two linked Inventory jobs equalize: whichever holds less pulls from the
    other. Stock can cross the same link in either direction on different
    days.
  - Crops, Livestock Raising and Advertising never pull. Advertising uses its
    links only to pick what to advertise: the last linked job with a product
    (gamelogic.md, "Advertising").
- **A link does nothing by itself.** Two linked jobs that don't match
  (for example a pulling job whose product the other doesn't hold) move
  nothing. That's a useful thing to show, because it's the player's mistake.

### What the art should do

- Draw links as plain 2 px ink lines with no arrowheads; selected links are
  signal orange. This replaces "Link arrows" in `visual-direction.md` and the
  arrows in the `ui_concept.py` mockup.
- Mark an idle link (one that can't move any product) with a dashed line, and
  explain why when it's tapped. The client works this out from the two jobs'
  types and products. It's a display hint and doesn't change the sim.
- Don't show flow direction or amounts on the line in M2. The facade doesn't
  report per-link transfers yet, and guessing the direction from job types
  would be wrong for Inventory to Inventory. If we want animated flow later,
  the sim has to report it first, and that's a separate PR.
- Don't confuse these with the `link_sell` and `link_buy` dots. Those are for
  product links between firms on the map (the market layer, gamelogic.md
  "Product links"). They're a different system and get their own brief.

### Art already drawn that needs a change

| Asset | Today | Change |
|---|---|---|
| `docs/art/visual-direction.md` line 124 | "Link arrows between slots" | Plain lines, no arrowheads |
| `art/tools/ui_concept.py` `arrow()` | Draws arrowheads on slot links | Plain line, plus a dashed idle style |

## 2. Town-name plate (map) — art issue #175

### What it shows

One plate per town on the map: the town's name and its level. Both come from
the `map` query (`towns[].name`, `towns[].level`). Tapping the plate opens the
Town panel, where population, GNP and the charts live. The plate never shows
those figures.

### How the rules work

- Names come from the `city_names` table: 24 names today, the longest 11
  characters ("Cedar Falls", "Pine Hollow", "Stonebridge"). Size the plate
  for 12 characters so a slightly longer name still fits.
- The level is a whole number from 1. A town goes up one level when its
  population reaches 160,000 × L², where L is the current level (rule
  `towns.level_pop_per_sq`, from `FUN_0004b4de`). Levels never go down.
- The native game has no level cap. The `towns.level_max` value of 6 only
  limits the starting footprint table. Some towns can go past 6.

### What the art should do

- Draw the level as a number in a small badge on the plate, not as one
  picture per level, so 7, 8 or more need no new art.
- Leave owner colours off the plate. Towns aren't owned.
- Give the plate a short pulse to use when a town levels up. It's optional:
  the facade doesn't report level-up events yet, so the client can only spot
  one by comparing two `map` reads.

## 3. News-category icons and profit arrows — art issue #177

### News categories

The sim has exactly four categories (`NewsCategory` in `news.py`), and every
item has one. The category icon is the only per-row icon in the News feed.

| Category | News types in it |
|---|---|
| Normal | Firm opened, firm closed |
| Financial | Bank loan, loan repaid, shares issued, share trade, annual dividend, tender offer |
| Technology | R&D invention, product made public, R&D breakthrough |
| Special | New competitor, bankruptcy, control change, merger, price war, industry dominance, CEO retirement, CEO succession, resource exhausted, resource discovered, resource on site, city founded, livestock disease, building destroyed, crop failure, inventory loss, economic downturn |

- Draw four icons, one per category. There's no icon per news type: the
  headline text carries the type.
- "Important" is a flag on the item, not a category. It shows as a bold row,
  the menu-button badge and a toast. It doesn't need its own icon.

### Profit arrows

The sim keeps monthly history only for the corporation (`month_history`):
revenue, operating profit, other profit, expenses and net worth. A firm's
ledger keeps only this month so far, last month and this year, so there are
no two complete months to compare for a firm.

- Show an arrow only next to the corporation's operating profit and other
  profit in Company > Income. It compares the last complete month with the
  month before it, the last two entries of `month_history`.
- Up means profit grew and down means it fell. Draw no arrow when the two
  are equal or there are fewer than two months.
- The arrow sits beside the figure. The figure keeps its own sign and its
  green or red colour (visual-direction.md). Colour the arrow by direction:
  green for up, red for down. That way a loss that shrank shows a red figure
  with a green up arrow, which is correct.
- Don't put arrows on firm rows, revenue or expenses in M2.

## 4. Charts — art issue #178 (line style)

Not tied to sim rules beyond what the charts show:

- Company charts: revenue, operating profit, other profit, expenses and net
  worth, one series per chart, with a Past 12 months tab and a Past years tab.
- Stock page: share price with Day, Month and Year tabs.
- Town panel: two 12-month charts of month-on-month growth %, one for
  population and one for GNP (per-capita GNP until #299 says otherwise),
  decided on #280. The `town` query returns them in month order, only for
  months that happened, with no point for the first month (#255). Growth
  can be negative, so the zero line applies here too.

What the style must handle: profit series can go below zero, so draw a zero
line whenever the range crosses it. Money runs from a few thousand to
billions, so axis labels need short forms (12.5k, 3.2M, 1.1B). A series can
have a single point (the first month of a game). A tapped point shows its
value.

## 5. Win/loss card — art issue #178

### What it shows

A full-screen card when the game ends (`goals.result` from the `goals`
query). It shows the outcome, the final score, years played, the difficulty
rating, and the goal list with a met tick or an unmet mark on each row
(the same rows as the Goals screen, using the #176 goal tick).

### How the rules work

There are four ways the game can end (the four game-over paths in the #243
answer), and the card needs a version for each:

| `result_name` | When | Card headline idea |
|---|---|---|
| `VICTORY` | Checked every 2 game-days: every active goal is met | Goals achieved |
| `DEFEAT_DEADLINE` | Checked at year end, when a year limit is set: the years have run out and the goals weren't met | Out of time |
| `DEFEAT_AI_WON` | Checked every 7 game-days, only when there's no year limit: a competitor met every goal first | A rival got there first |
| `DEFEAT_BANKRUPT` (not in the sim yet, #287) | The player's cash is negative at the monthly check and the player chooses Declare bankruptcy | Bankrupt |

- The competitor check is in the sim since #241 (PR #244).
- Bankruptcy can end any game, with or without goals. In a game with no
  goals it's the only ending. The card then shows no goal list.
- Before bankruptcy, the player gets a five-choice prompt: borrow, issue
  shares, sell stocks, close firms, or declare bankruptcy (gamelogic.md
  "Bankruptcy"). The first four open existing screens. The prompt is a
  dialog, not this card, and is specified in #287.
- The score is 0 when the game was marked as cheated. The card still shows it.
- In timed games, when 1 to 5 years are left, the year end brings a warning
  ("X years left to achieve the goal"). That's a toast, not this card.

### What the art should do

- Use one card layout with four headline and colour treatments, not
  separate screens. Bankrupt needs its own band and emblem. Whether a score
  shows on it is open research in #287, so make the score row hideable.
- Draw a New game button only — **no Keep playing button**. The native
  game exits to the main menu after the result screen; the `else` branch
  in `FUN_0001cf40` that would clear goals and continue is dead code
  because `DAT_000b1f17` is always zero (see techspec "Game over handler").
