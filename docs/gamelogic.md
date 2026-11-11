# Capitalism Plus — Game Logic

How the simulation works. This document describes what the game does —
the rules, the timing, the coefficients — without referencing code.

## Starting a new game

### Setup dialog

The new-game dialog has multiple pages. The player configures the game
world, difficulty, competitors, and goals before the simulation begins.

**Default settings** (applied before the player changes anything):

| Setting | Default |
| --- | --- |
| Starting year | 1990 |
| Number of years and goals | 0 (no goal, no year limit) |
| Initial capital | $10,000,000 |
| Difficulty | Very Easy (rating 12) |
| Competitors | 3 |
| Character / capital / expertise | Conservative / Low / None |
| Strategy sliders | Diversified 2, Production 0, Retail 1, Stock 0 |
| Competitors may change strategy | on |
| Show competitor trade secrets | on |
| Random personality, random strategy | off |
| Cities at start | 5, new cities can appear |
| Local competitor competence | Low |
| Seaports, consumer / industrial | 2 / 2 |
| New seaports | off |
| Constant import supply | on |
| Import quality | High |
| Stock investment | on |
| Random events | None |
| Multiplayer | off |
| Product re-invention required | off |

### Difficulty levels

Seven difficulty options: Very Easy, Easy, Medium, Hard, Very Hard,
Hardest, and Custom. Selecting any preset (Very Easy through Hardest)
overwrites a fixed set of game fields. Custom leaves all fields at
their current values.

**Preset effects:**

| Setting | V.Easy | Easy | Medium | Hard | V.Hard | Hardest |
|---|---|---|---|---|---|---|
| Competitors | 3 | 5 | 7 | 8 | 8 | 10 |
| Competitor character | Conservative | Pre-defined | Pre-defined | Pre-defined | V. Aggressive | V. Aggressive |
| Competitor capital | Low | Low | Moderate | High | Very High | Extr. High |
| Expertise level | None | None | None | Moderate | Very Low | High |
| Show trade secrets | Yes | Yes | Yes | No | No | No |
| Consumer seaports | 2 | 1 | 1 | 1 | 1 | 0 |
| Industrial seaports | 2 | 2 | 1 | 1 | 1 | 0 |
| Constant supply | Yes | Yes | Yes | Yes | No | No |
| Import quality | High | High | Moderate | Low | Low | Low |
| Competitor competence | Low | Moderate | Moderate | Moderate | High | High |
| Random events | None | None | None | Low | Moderate | High |

The difficulty preset is applied last and overwrites any earlier copies
of the fields it owns.

### Difficulty rating

Each game configuration receives a computed difficulty rating (1–200+).
The formula combines multiple factors:

1. **Base score** starts at competitor capital level × 11, plus 15.
2. **Trade secrets penalty**: +15 if trade secrets are hidden.
3. **Character penalty**: if a specific type (0–3), adds type × 5;
   if mixed (Pre-defined/Random/Even), adds 7.
4. **Expertise penalty**: Very Low adds 40; higher levels add
   (level − 1) × 20.
5. **Import scarcity**: if no seaports at all, +30. Otherwise, the
   fewer seaports, the higher the penalty — scaled further by whether
   constant supply is off and by import quality (low quality adds more).
6. **Competitor multiplier**: the running score is increased by
   (competitors × score / 10 + 1).
7. **Competence bonus**: +10 per competence level.
8. **Random events bonus**: +4 per frequency level.

The final score is scaled to a 0–200 baseline (multiplied by 200/212),
with a minimum of 1.

### Setup pages

**Competitors page.** Sets the number of AI competitors (0–10),
their character type, starting capital level, expertise level, and
three toggles: show trade secrets, random personality, random strategy.

- **No. of Competitors**: slider 0–10. In multiplayer, the maximum is
  11 minus the number of human players.
- **Competitor Character**: Conservative, Moderate, Aggressive, Very
  Aggressive, Pre-defined (keeps each person's existing type), Random,
  or Even Distribution (cycles through the four types).
- **Competitor Capital**: Low, Moderate, High, Very High, Extremely
  High. Controls the starting cash each AI corporation receives.
- **Competitor Expertise Level**: None, Very Low, Low, Moderate, High.
  Higher levels give AI CEOs random product-class expertise skills.
- **Show Competitor Trade Secrets**: reveals competitor firm internals
  (product quality, prices, linked products) in the player's UI.
- **Random Personality / Strategy**: when on, each competitor gets
  randomized personality traits or strategy assignments.

**Competitor Strategies page.** Four sliders distribute AI competitors
among strategy modes: Diversified, Production Focused, Retail Focused,
and Stock Focused. The sliders set quotas — as corporations are
created, each one fills the next unfilled slot. An "Enable Strategy
Changes" toggle allows AI competitors to switch strategies during play.

**Cities page.** Sets the initial number of cities (1–12), whether new
cities can emerge during play, and the competence level of local
competitors (Low, Moderate, High).

**Imports page.** Sets consumer and industrial seaport counts (0–10
each), whether new seaports can emerge, whether import supply is
constant (unlimited stock each month) or variable, and import quality
(Low, Moderate, High).

**Stock Market page.** Toggles whether stock investment is allowed. In
multiplayer, this is forced off for all corporations.

**Random Events page.** Sets the frequency of random events: None, Low,
Moderate, or High. Higher frequencies increase the daily probability of
livestock disease, building destruction, crop failure, R&D
breakthroughs, inventory loss, and economic downturns.

**Starting Year page.** Picks the game's start date from a list. Also
has a "Product Re-invention Required" checkbox — when on, products
must be re-discovered even if the starting year is past their normal
introduction date.

**Player Configuration page.** Sets the player's corporation name
(default "21st Century Capital"), player name (default
"Mr. Capitalist"), portrait (1–14), corporate color, and initial
capital ($3M–$1B). In multiplayer, also sets a password.

**Multiplayer Options page.** Enables multiplayer mode (Hot Seat or
Play-By-Email), sets a game description, number of human players
(2–11), turn duration (years and months), and a late-playing technology
bonus for players who join after the game has been running.

### Game initialization sequence

After the player clicks OK:

1. A Government corporation is created (type Government).
2. The game date is set to 1 January of the starting year.
3. All simulation modules are initialized (map, firms, products,
   economy, persons, corporations, stock market, news).
4. The player's corporation is created (type Player) with the
   configured initial capital, name, portrait, and color.

### NPC corporation spawning

AI competitor corporations are not all created at game start. Instead,
the person system periodically checks whether more corporations should
exist:

**Spawning conditions** (all must be true):
1. A person record is active and available (not already running a corp).
2. The total number of active corporations is below the competitor count
   setting.
3. A random 1-in-3 chance passes.
4. The total corporation count has not reached the hard cap of 12.

**Corporation creation process:**
1. **Person selection**: the system tries up to 20 times to find a
   random available person who is not already assigned and not on a
   cooldown timer.
2. **Color assignment**: cycles through 14 colors and picks the first
   one not used by any existing corporation.
3. **Strategy mode**: if the game has been running for more than 10
   years, there is a 50% chance the new corp enters dormant mode
   (otherwise Stock mode). Normally, the system uses the strategy quota
   sliders: it picks a random strategy and checks whether that quota
   still has room. If all quotas are zero (no distribution set), it
   auto-distributes: roughly half get Diversified, a third get Retail,
   an eighth get Production, and a seventh get Stock. As a fallback, it
   picks the first mode with remaining capacity (skipping Stock if the
   person has been active for fewer than 60 days).
4. **Character type**: depends on the Competitor Character setting:
   - *Pre-defined*: the person keeps their existing personality type.
   - *Random*: assigned a random type (Conservative through Very
     Aggressive).
   - *Even Distribution*: cycles through the four types by corporation
     index.
   - *Specific type (0–3)*: assigns that type, with random variation
     and a correction toward the average to prevent clustering.
5. **Personality traits**: if Random Personality is enabled, all traits
   are randomized. If this is a human player's person record, traits
   default to 50 (with salary preference 3 and skill level 7).
6. **Expertise skills**: depends on the expertise setting:
   - None: no skills assigned.
   - Very Low: skill level 40 in one area.
   - Low through High: assigns random product-class expertise from a
     fixed table of three product classes, with increasing skill levels.
7. **Starting capital**: determined by the Competitor Capital setting:

   | Setting | Capital range |
   |---|---|
   | Low | $3M – $6M |
   | Moderate | $4.2M – $8.4M |
   | High | $6M – $12M |
   | Very High | $9M – $18M |
   | Extremely High | $18M – $36M |

   The exact amount is random within the range: half the base value
   plus a random portion of the other half, multiplied by 600,000.

8. The corporation is created as type Competitor.

### Multiplayer specifics

- **Hard cap**: maximum 12 total players (AI + human combined).
- **Stock investment**: forced off in multiplayer.
- **Turn duration**: measured in game years and months.
- **Late playing bonus**: a technology catch-up bonus for players who
  join an in-progress game.
- **Hot Seat / PBEM**: two multiplayer modes — same computer or file
  exchange.

## Time and the game clock

The simulation has five speed settings:

| Speed | Real time per day |
| --- | --- |
| 0 (paused) | held indefinitely |
| 1 | 6 seconds |
| 2 | 3 seconds |
| 3 | 1 second |
| 4 | 0.5 seconds |
| 5 | instant (next frame after all work finishes) |

A "day" is the fundamental economic tick. The game does not advance the
date until all three simulation layers (firms, jobs, product links) have
each completed a full pass over their arrays. At that point the day
advances and a batch of daily events runs.

The calendar month is 30 days in most respects: day-of-month increments
and is clamped at 30, so on a 31-day month the 30th and 31st share
day-of-month 30. However, salary and overhead calculations use the real
calendar length for that month, not 30.

## The three simulation layers

The game spreads its per-day simulation across multiple frames. Each
layer has a cursor that walks through its array, visiting a fixed number
of records per frame. Once the cursor has passed every record, that
layer is "idle" and waits for the other two to finish.

| Layer | Records per frame | What it simulates |
| --- | --- | --- |
| Firms | 5 | Buildings on the map — drawing, AI decisions, shutdown checks |
| Jobs | 10 | Work inside firms — production, purchasing, sales, research, advertising |
| Product links | 15 | Market connections between firms — score, price, quantity, competition |

Empty slots still cost one visit — a deleted firm leaves a gap that
persists until something is allocated there.

Within a single frame, the order is firms → jobs → product links. A job
can therefore be visited on an earlier frame of the same day than the
firm that owns it. Both still see the same date.

## Day, month, and year

Once all three layers are idle and the clock has elapsed, the day
advances. The daily batch runs in this order:

1. **Day advance.** Weekday = day-serial mod 7. On a calendar-month
   boundary, day-of-month resets to 1 and the month pass runs before
   anything else. On a year boundary, the year pass runs immediately
   after the month pass.
2. **Corporations.** Each corporation runs its daily method. Each live
   job posts quantity × price into the owning corporation's cash and
   running totals. If a player corporation's cash goes negative, the
   game opens the crisis dialog (Borrow / Issue Shares / Sell Stocks /
   Close Firms / Declare Bankruptcy). An AI competitor is adjusted from
   last month's figures and can be removed if cash stays negative.
3. **People.** Each active person runs three updates.
4. **Towns.** Every town is visited. Population steps only on the day
   matching that town's index: population increases, and city level
   rises when population passes level × 80,000 × level × 2. On the
   same day, each live town-product link with a price gap adds the gap
   into the product's monthly demand and the link's own monthly buckets.
   The charts use Population Growth and GNP Growth.
5. **Goals.** With no goal set and multiplayer off, this does nothing.
   With a goal, player goals are checked every 2 days; AI goals every
   7 days (untimed games only). Timed games check annually instead.
6. **Weekly ratings** (weekday 5 only). Each rating entry tracks a
   firm's share of a product in a town. If the rating is still at or
   above target / 200, it is reduced. The reduction amount depends on
   whether the firm is an importer or a local producer: importers lose
   0.025 (corporate brand), 0.05 (range brand), or 0.1 (unique brand)
   per tick, while local producers lose up to their proportional share
   of the town-product demand cell. The matching town-product supply
   cell also decays (capped at 0.05 per tick).
7. **Random events.** Skipped when the frequency setting is 0 (the
   default for new games). Otherwise, each day has a probability of
   triggering based on the frequency — lower frequency means rarer
   events. When triggered, one of six event types is chosen at random
   and dispatched.
8. **Products.** One thirtieth of the catalog runs each day, so each
   product is visited once every 30 days. The visit converts current and
   previous demand into a 12-byte distribution capped at 100.
9. **Natural resource discovery.** After the first year of the game,
   new deposits of natural resources (mines, oil wells, forests) can
   appear on the map. After each discovery, the system waits at least
   365 days before another can occur. The discovery system ensures a
   minimum of 2 deposits per resource type exist at all times (placed
   immediately if below 2). For resources at their maximum count,
   there is only a 1-in-500 chance per attempt (up to 20 tries). A
   global safety net also has a 1-in-500 chance of placing a resource
   if the total across all types is below three times the number of
   resource types. New deposits are placed randomly on grassland or
   undeveloped terrain (never on existing towns), with randomized
   rainfall and soil quality. A news event announces each discovery.

### Month pass

The month pass runs inside the day-advance step, before corporations
and towns see the new day:

1. **GNP index adjustment.** The game averages GNP Growth across all
   towns. If the average is below a low threshold, there is a random
   chance that the global GNP index ticks upward (economic stimulus).
   If the average exceeds a high threshold and the GNP index is above
   1.0, there is a random chance it ticks downward (cooling).

2. **Product catalog maintenance.** For each product type:
   - Monthly sales buckets reset to zero for the current month
   - Current-month accumulators rotate to previous-month, then zero out
   - **Technology obsolescence check:** products that have been available
     for a long time (availability months × 8 plus years since invention
     exceeding 50) are marked as obsolete, disabling further quality decay
   - **Cigarette demand decline:** if the Cigarette class exists, its
     base demand shrinks by about 0.4% per month during the first 50
     years, and by 0.1% per month after that — modeling long-term
     decline in tobacco consumption

3. **Town monthly processing.** For each town:
   - **Population and growth statistics:** records current population
     into the monthly ring, computes month-over-month population growth
     rate, and calculates a 12-month rolling GNP growth figure from
     the population-weighted economic series (this feeds into step 1)
   - **Town spawning** (if enabled): after 700 days since the last
     town spawn, with fewer than 12 cities and the map not too crowded
     (towns < map area / 30), a 1-in-10 daily chance creates a new
     city. The new city is associated with corporation 1 and announced
     via a news event.
   - **Demand recalculation for each product in town:** each
     town-product entry updates:
     - *Supply/demand adjustment:* when demand exceeds supply, random
       chance of demand increase or quality/price improvement; when
       supply exceeds demand, random chance of the opposite.
       Difficulty level affects the probability (harder difficulties
       mean markets adjust faster).
     - *Base demand recalculation:* demand is recomputed from the
       product's inherent demand value, the town's population, the
       product's necessity factor, and a technology-age decay that
       reduces demand for aging products.
     - Monthly accumulators reset for the new period.
   - **Town centroid update:** the game averages the x/y coordinates
     of all active towns, maintaining a "center of the world" reference.

4. **Corporations monthly.** (See Corporation internals.)

5. **Array walks.** All firms, jobs, and product links run their monthly
   methods in bulk.

6. **Autosave.** On months 3, 6, 9, and 12, if autosave is enabled and
   the player corporation exists, the game writes AUTOSAVE.SAV.

### Year pass

Runs on the day the year changes, after the month pass:

1. **Calendar update.** Years-elapsed increments. The 30-year and
   10-year ring indices advance (wrapping at their limits).

2. **GNP history.** The current GNP index is stored in a 10-year
   history ring for the yearly GNP chart.

3. **Goal deadline check.** If a year limit was set for the scenario:
   - Fewer than 6 years remaining triggers a warning dialog
     ("N years left to achieve the goal. Hurry Up!").
   - At 0 years remaining the game ends — victory if goals are met,
     defeat otherwise.
   - A limit of 0 (free play) skips both checks entirely.

4. **Corporations yearly.** Each corporation runs its yearly method
   (financial resets, annual reporting).

5. **Firms yearly.** Each firm runs its yearly method via its type's
   virtual table.

## Firm types

14 building types the player or AI can place on the map.

Setup cost is a one-time cash payment when the building is placed.
The full price of a placement is the setup cost **plus the land value
of the tile** (see "Building, rebuilding and demolishing" below).
Overhead is a monthly operating expense (prorated by remaining days
when the firm is built mid-month). Both are in dollars.

| Type | Name | Setup cost ($) | Overhead ($/month) |
| --- | --- | --- | --- |
| 1 | Department Store | 1,000,000 | 100,000 |
| 2 | Factory | 1,500,000 | 100,000 |
| 3 | R&D Center | 1,500,000 | 100,000 |
| 4 | Farm | 1,000,000 | 100,000 |
| 5 | Logging Camp | 1,500,000 | 100,000 |
| 6 | Mine | 5,000,000 | 300,000 |
| 7 | Oil Well | 5,000,000 | 300,000 |
| 8 | Software Developer | 100,000 | 10,000 |
| 9 | Software Publisher | 1,000,000 | 100,000 |
| 10 | Restaurant | 2,000,000 | 100,000 |
| 11 | Television Station | 20,000,000 | 350,000 |
| 12 | Radio Station | 10,000,000 | 200,000 |
| 13 | Newspaper Publisher | 10,000,000 | 200,000 |
| 14 | Seaport | 0 | 0 |

### Building, rebuilding and demolishing

**What a placement books.** When a firm is created, the game stores the
tile's current land value on the firm and pays two amounts out of cash:
the setup cost goes into the Business Assets account and the land value
goes into the Land & Resource account. The placement step itself does
not check cash.

**Player build panel.** The panel shows Construction Cost, Land Cost and
Total Cost. The Build button is enabled only when the site can be built
on **and** the corporation's cash is at least setup cost + land value.
The check is re-run, and the button redrawn, whenever cash changes. Only
cash counts: the bank credit limit is not considered. (The check sets
the button's enabled state; how a disabled button is drawn was not
traced.) For an existing firm the panel shows the Firm Rebuild Cost
instead, with Rebuild and Close Down buttons. Rebuild is disabled when
cash is below the rebuild cost or the cost is zero. When the site can't
be used, the panel says "Cannot be built here".

**AI builds** use the same price (land value + the firm type's setup
cost). If cash is short, the AI runs the asset-sale sequence and checks
again, and it cancels the build only if it is still short (see "Firm
creation" and "Asset sale" under AI corporation strategy).

**Demolish** ("Destruct the firm and sell the land"). The setup cost is
moved from Business Assets back to cash and then posted as a Write-off
expense (category 7), so it is lost. The land is sold back to cash at
the land value currently stored on the firm (which is revalued monthly,
see Firm monthly). Both asset accounts are floored at zero.

## Firm daily cycle

Every day, each occupied firm runs through a sequence of steps. The
first step (drawing the map icon) runs for all owners. The remaining
AI steps run only for firms not owned by the player.

### Step 1: Draw (all owners)

Most firm types simply draw their icon on the map.

Exceptions:
- **Farm** and **Restaurant**: draw icon, then return.
- **Media firms (TV, Radio, Newspaper)**: draw icon, then post a payroll
  expense. The media salary formula is
  `(firm.salary × 2,000 / days-in-month × labor-factor) / 100`, using
  integer division. There is no Training post for media payroll.
- **Seaport**: draws icon, then runs a supply calculation. For each
  product link, the seaport caps quantity using a projection:
  `((30 − day-of-month) × previous-quantity / scalar + quantity-sum) / scalar`,
  raised to a floor from the product's base capacity. The capped amount
  is added to the link's flow and the product's daily total. A third
  routine runs every 3 days when a config flag is set (default off): it
  walks links to apply import scores and link/unlink firms.

### Step 2: AI daily (AI firms only)

Each firm type's AI runs periodically (typically every 15 or 30 days,
staggered by record number):

- **Department Store**: staffs Purchasing, Sales, and Advertising jobs
  into free slots. Shuts down after 180 days if the last 6 months of
  revenue are all zero or negative.
- **Factory**: runs a sub-check every 15 days. On a 30-day cycle,
  checks day-stamp for shutdown (> 30 or > 365 days).
- **R&D Center**: every 60 days, considers shutdown. The only outcome is
  shutdown = yes.
- **Farm**: every 30 days, checks age against a threshold for shutdown.
- **Logging Camp / Mine / Oil Well** (shared logic): every 15 days or
  when the first job slot is empty. Creates the matching extraction job
  plus Inventory and Sales. Shuts down when the reserve reaches 0 or
  after 364 days with no profitable linked product and no linked firm
  of the same owner.
- **Software Developer**: return immediately. All work happens through
  the Software Development job (type 13). The firm is a simple
  container for one R&D-style job slot.
- **Software Publisher**: return immediately. Uses Sales, Software
  Production, and Advertising job slots.
- **Restaurant**: return immediately. Works as a Department Store
  variant with no extra AI logic. Uses Purchasing and Sales
  with the live-inventory sales multiplier (2× instead of 4×).
- **Media (TV, Radio, Newspaper)**: return immediately (the firm's
  own daily method posts payroll as described above).
- **Seaport**: may open product links; runs a link walk on day 28.

All AI firms that have revenue check `projected-net ≥ 0` to recover
from shutdown.

### Step 3: Training factor (AI firms only)

Runs every 30 days (staggered by record number). Only applies to firms
whose firm-type byte is 0.

For **R&D Center**: the training factor is
`random(60) + (short1 × short2) / 100 − 30`, or 0 if last month's
corporation total is zero or negative. The random function is the
config-local LCG, range [0, bound).

For **all other types**: the factor is
`count-of-jobs-rated-above-89 × record-scaling-short`. The qualifying
job types are Purchasing, Sales, Manufacturing, and Livestock Processing.

The new value is clamped to 0..200 and stored only when it differs from
the current value by more than 9.

### Step 4: Action dispatch (AI firms only, when pending)

Runs when the firm has a pending action. Department Store is the only
type with meaningful dispatch: action value 2 routes a command to a job.
All other types clear the action field without doing work.

### Shutdown and deletion

- A firm whose shutdown flag reaches 1 posts a "firm closed" news event
  and is deleted.
- Any other nonzero shutdown flag decrements by 1 every 30 days
  (staggered by array cursor).

A player-owned firm has no AI steps — only drawing runs. Its jobs still
execute on the job sweep and still post wages.

### Firm monthly

At the month boundary:
- Monthly revenue, expense, and net for the starting month are zeroed.
- The nine category floats roll into the previous-category series.
- Overhead is posted as category 2 from the firm-type record. On day 1
  (the normal boundary), the full value is posted. When a newly created
  firm posts its first partial month, the value is scaled by
  `(days-in-month − day-of-month + 1) / days-in-month`.
- Land value is re-read from the map. The delta goes to the corporation
  as category 11 (Increase in Land Value). A balance transfer moves it
  from bucket 0 to bucket 3, leaving cash unchanged.

Media firms (TV, Radio, Newspaper) run additional monthly work: they
copy 12 floats from a current series to an archive, zero the current
series, and sum the archive.

### Firm yearly

Zeros the nine year-category floats. No job or product-link yearly
walk.

## Job types

15 work types that occupy slots inside firms:

| Type | Name | Setup cost | Staff |
| --- | --- | --- | --- |
| 1 | Crop Growing | 100 | 16 |
| 2 | Livestock Raising | 100 | 16 |
| 3 | Livestock Processing | 100 | 16 |
| 4 | Logging | 100 | 24 |
| 5 | Inventory | 50 | 1 |
| 6 | Private Labelling | 100 | 6 |
| 7 | Manufacturing | 300 | 24 |
| 8 | Mining | 1,000 | 24 |
| 9 | Oil Extraction | 1,000 | 24 |
| 10 | Purchasing | 50 | 4 |
| 11 | Research & Development | 500 | 12 |
| 12 | Sales | 100 | 8 |
| 13 | Software Development | 50 | 8 |
| 14 | Software Production | 100 | 4 |
| 15 | Advertising | 5 | 1 |

### Rating and throughput

Each job has a **rating** (1–9) representing its skill level. Rating
determines both production efficiency and storage capacity through two
lookup tables:

| Rating | Efficiency | Capacity multiplier |
|--------|-----------|-------------------|
| 1 | 100% | 8 |
| 2 | 130% | 10 |
| 3 | 160% | 14 |
| 4 | 200% | 16 |
| 5 | 250% | 20 |
| 6 | 300% | 24 |
| 7 | 360% | 30 |
| 8 | 430% | 35 |
| 9 | 500% | 40 |

**Efficiency** scales production throughput. For manufacturing:
`(recipe-output × recipe-speed × efficiency) / 100`. At rating 1,
a factory produces at base rate; at rating 9, it produces at 5× base.

**Capacity multiplier** scales how much stock the job can hold:
`base-capacity × type-factor × capacity-multiplier`. At rating 1 a job
can hold 8× its base; at rating 9 it can hold 40×.

When capacity shrinks (after a rating change that shouldn't happen
normally), excess stock is written off as an expense.

### Firm-to-job mapping

Each firm type carries a fixed template of job slots:

| Firm | Jobs |
| --- | --- |
| Department Store | Inventory, Private Labelling, Purchasing, Sales, Advertising |
| Factory | Inventory, Private Labelling, Manufacturing, Purchasing, Sales, Advertising |
| Farm | Crop Growing, Livestock Raising, Livestock Processing, Inventory, Sales, Advertising |
| Logging Camp | Logging, Inventory, Sales |
| Mine | Inventory, Mining, Sales |
| Oil Well | Inventory, Oil Extraction, Sales |
| R&D Center | R&D |
| Software Developer | Software Development |
| Software Publisher | Sales, Software Production, Advertising |

Media firms (TV, Radio, Newspaper), Restaurant, and Seaport have no
discrete job slots. Media firms use a payroll formula directly.
Restaurant daily/AI methods return immediately — it behaves as a
Department Store variant (Purchasing and Sales with the live-inventory
multiplier of 2). Seaport daily methods handle their own import work.

**Media firm economics:** Media firms (TV Station, Radio Station,
Newspaper Publisher) operate differently from production firms. They
have no job slots and no direct production cycle. Instead they generate
audience through a reputation-driven model, and earn revenue from
advertisers.

#### Daily cycle

The firm redraws its icon, then posts a payroll expense:
`(salary × 2,000 / days-in-month × labor) / 100`, using the firm's
salary field and the town's labor factor. There is no training post.

#### Monthly cycle

The base firm monthly method runs (clearing buckets, posting overhead
and land value changes). Then two media-specific calculations execute
in order:

1. **Audience update** — adjusts the firm's audience rating.
2. **Revenue calculation** — computes monthly revenue from audience and
   town economics.

After both calculations, the firm rolls its 12-month revenue series:
current-month data shifts to the previous-year archive, current month
resets, and the archive sums into an annual total for financial charts.

#### Audience initialization

Government-owned media (corporation type 4) in a town where the
product slot is established receive an initial audience of 10–39
(random). All other media firms start with audience 0 and a reputation
of 100 (the maximum). The 12-month audience history is backfilled with
the initial audience ± up to 10% random variation per month.

#### Audience model

Each media firm has two key values: an **audience rating** (how many
people watch/read/listen) and a **reputation** (a momentum value that
drives audience growth or decline over time). Reputation ranges from
-100 to +100.

**Monthly reputation drift:** Each month, reputation shifts randomly by
up to ±30. Low-audience firms (below 15) get an additional random
reputation boost, helping struggling media recover. High-audience firms
(above 40) get a random reputation penalty, dampening monopolistic
dominance. Reputation is then clamped to [-100, +100].

**Monthly audience change:**
```
audience_delta = (random(0..100) + reputation − 50) / 200
audience += audience_delta
```
With positive reputation, audience tends to grow (the random baseline
is centered at 50, so positive reputation tips the average above zero).
With negative reputation, audience shrinks. The divisor of 200 makes
the change gradual — at the extreme (reputation ±100), the maximum
monthly audience shift is about ±0.75 points.

If audience drops below zero it is floored at zero.

**Competition (zero-sum redistribution):** When a media firm gains
audience, each competitor of the same type in the same town loses a
share of the gain, proportional to the number of competitors and scaled
by 50%. This makes audience partially zero-sum: growth of one station
directly hurts its rivals.

**Market saturation:** If the total audience of all media firms of the
same type in a town exceeds 90, the current firm's audience is reduced
by the excess. This soft-caps the total audience market per media type
per town at approximately 90.

#### Revenue formula

Revenue depends on four factors: the firm's staff, its audience, the
town's economic characteristics, and a seasonal component.

1. **Reach** = staff × audience / 100
2. **Ad base** = (town economic stat / 200) × reach / 100
3. **Revenue base** = town purchasing power × ad base / 100
4. **Revenue** = ad rate × (revenue base / 1,000) × ((seasonal component
   + town stat / 200) × (audience / 100 + 2) / 100) / 100

Revenue is floored at 100 — a media firm always earns at least 100 per
month even with zero audience.

The town's monthly economic time series provides a seasonal component
that makes revenue fluctuate with the local economy. Larger, wealthier
towns generate substantially more media revenue.

The **CPM** (cost per mille — revenue per 1,000 units of reach) is
displayed as: `revenue × 1,000 / revenue_base`.

#### Advertising interaction

Media firms earn revenue from Advertising jobs in the same town. An
Advertising job selects a media partner by scanning for TV stations or
newspapers with audience above a minimum threshold of 5. Once linked,
the ad budget (clamped between 50,000 and 500,000) flows as revenue to
the media firm and as marketing expense to the advertiser's corporation.

The campaign cycle runs every 60 days (partner selection) and every
30 days (product targeting). The monthly cycle checks which of the
advertiser's products need more market visibility and directs ad spend
toward them, based on technology level and current brand rating versus
target. If no products need advertising, the budget drops to zero.

## Job daily cycle

Every job executes the same daily sequence, 10 jobs per frame:

### Step 1: Post wages (every visit)

The salary formula (integer arithmetic):
`((target × 2,000) / days-in-month × labor-factor) / 100`

This is posted as category 1 (Salaries Expense). Training & Equipment
(category 3) is `salary × training-factor / 100`.

The labor factor comes from the town the firm is placed in. Outside
a valid town range, a global default is used.

### Step 2: Train (weekday 2 only)

Rating ranges from 1 to 9. Every working day, each job earns training
credits toward a weekly skill check.

#### Daily credit accumulation

Credits are added each day in one of two modes:

**Fixed-credit mode** (farming, livestock, R&D): the job earns a
constant number of base credits per day, scaled upward by a rating
multiplier. Higher ratings earn proportionally more credits:

| Rating | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|--------|---|---|---|---|---|---|---|---|---|
| Multiplier | 100% | 130% | 160% | 200% | 250% | 300% | 360% | 430% | 500% |

Daily base credits: Crop Growing = 20, Livestock = 10, R&D = 14.

**Work-based mode** (manufacturing, sales, purchasing, extraction,
labelling): credits are proportional to work output as a percentage
of maximum capacity. If a factory produced 60 of a possible 100 units,
it earns 60 credits. No rating multiplier applies.

All credits are then scaled by two factors:
- **Training budget** (player-adjustable, default 10%): the same
  setting that controls Training & Equipment expense. Higher budget
  means faster skill gain but higher costs.
- **City education level**: location-dependent modifier. Retail-type
  firms use the town's education stat; other firms use a global default.

#### Weekly upgrade check

Once per week, the accumulated credits are checked against a threshold:

- **Upgrade threshold**: `current_rating × 900` credits per step
- **Steps per rating level**: equals the job's staff count from the
  game data. Jobs with larger crews need more steps:

| Job type | Steps per level |
|----------|----------------|
| Inventory, Advertising | 1 |
| Purchasing, Software Production | 4 |
| Private Labelling | 6 |
| Sales, Software Development | 8 |
| R&D | 12 |
| Crop Growing, Livestock | 16 |
| Manufacturing, Logging, Mining, Oil | 24 |

When accumulated credits exceed the threshold, one step is completed
and the accumulator resets. After all steps are completed, the rating
increases by 1 and the step counter resets.

Total credits needed for one full rating upgrade from level N to N+1
= steps × N × 900. Going from rating 1 to 2 in Manufacturing requires
24 × 1 × 900 = 21,600 credits; from rating 8 to 9 requires
24 × 8 × 900 = 172,800 credits.

#### Downgrade (theoretical)

A symmetric downgrade path exists if the accumulator ever reaches
−(rating × 900). Under normal gameplay conditions (positive training
budget, working jobs), credits only accumulate positively, so
downgrades do not occur in practice.

### Step 3: Gate (AI firms and operational player firms)

Player firms skip the gate when the firm is non-operational. AI firms
always run the gate. The gate is a per-type check (step 4 in the
dispatch) and an optional secondary check gated on an operational byte.

### Step 4: Corporation type 2 check

When the owning corporation is type Hired, a per-type check runs
(Purchasing and Sales only).

### Step 5: Work (every visit)

The core of each job type — production, purchasing, selling, research,
or advertising. Each type's behavior is described below.

### Step 6: Supply chain pull

When the work step returns a nonzero value, the firm's linked jobs are
walked. For each linked job, the take-linked function runs — this is
how inventory, private labelling, manufacturing, and sales pull output
from production jobs.

## Per-type job behavior

### Crop Growing

Four-stage seasonal growth cycle:
- **Stage 0 (dormant):** waits until the game-date month matches the
  product's planting month (from the demand table).
- **Stage 1 (growing):** a counter increments each day. After 30 days
  enters stage 2.
- **Stage 2 (mature):** continues counting.
- **Stage 3 (harvest):** when the counter reaches the product's growth
  duration, harvest runs. Yield depends on climate distance (× −10 + 20),
  moisture distance (× −10 + 20), soil quality (÷ 5), plus a training
  bonus. After harvest + 30 more days, the cycle resets to stage 0.

Returns true when stock reaches capacity. No supply chain pull (empty
take-linked slot).

### Livestock Raising

Does not trigger the supply chain pull (returns 0). When the product
is set, the quality target becomes `(rating − 1) × 5 + 30`. Then
two sub-routines run:

1. Moves a slice from the growth float onto the stock float. The slice
   scales with the record's growth rate, the stock-to-capacity ratio,
   and two scaling constants: 36,500 (100 years in days, converting a
   long-term yield rate to a daily increment) and 100 (percentage
   divisor). Caps stock at capacity.
2. Feeds back: the new stock produces more growth, also capped.

Adds 10 training credits per visit.

### Livestock Processing

Converts raw livestock into processed goods. The daily output is
`(efficiency × capacity / 100 × product-yield-factor) / 100`,
where the product-yield-factor comes from the livestock record for the
assigned product. The result is stored as the processing total; monthly,
the current total rolls to previous and resets.

Always returns 0 — processing is continuous with no completion signal
and no supply chain pull.

### Extraction (Logging / Mining / Oil)

Shared across all three. While stock is below capacity, adds
`min(remaining-room, rate × efficiency × capacity / 100)` units. The
reserve draw is
`(units / capacity / efficiency) / reserve-scalar`,
capped by the remaining reserve. The reserve decreases. A portion of
land value is extracted as category 8 (Consumption of Raw Material
Reserve), with a balance transfer that replaces the cash effect. When
the reserve reaches zero, a news item is posted. Returns true when
stock reaches capacity. Each visit adds a training credit of
`units × 100 / maximum units`.

### Inventory

A pass-through type. The work function returns 1 immediately. The real
work is in the take-linked step: it moves
stock from the linked job to this job, blending quality values. When
both jobs are Inventory, the transfer equalizes their stocks (only moves
when this job holds less than the other).

The gate checks the operational byte, ensuring the job only runs when
the firm is operational or AI-controlled.

### Private Labelling

Another pass-through. The work function returns 1 immediately (triggers
the supply chain pull). The take-linked step moves stock from the linked
job, adds training credits proportional to the moved count (moved × 18
/ capacity), and copies the brand identity from the source — essentially
relabelling the product under the firm's own brand. This is how
Department Stores and Factories apply their own branding to goods they
purchased or manufactured.

### Manufacturing

When the product is set and the owning corporation has the upgrade flag,
technology upgrade is checked. Then a sub-routine runs. If the product
is unset or stock is at capacity, returns 0 (no supply pull).

Otherwise, if the input buffer is empty, it refills from ingredient
stocks. The production step is
`(recipe-scaling × recipe-capacity × job-efficiency) / 100`.
An abort fires when that is below 1. Units added are the minimum of
room under capacity, the step, and the remaining input. Input decreases,
stock increases, and training credits are `(units × 100) / step`.
Returns 1, triggering the supply pull.

The take-linked step (for Manufacturing) moves recipe ingredients:
it matches each linked job's product against recipe ingredients. When
an ingredient slot is below its recipe requirement and the other job
has stock at capacity or it's day-of-week 0, it transfers the minimum
of the other job's stock and the remaining need. Copies quality and
price data from the source.

The gate runs weekly (every 7 days, staggered by firm index) and may
trigger technology upgrade.

### Purchasing

Returns 0 (no supply pull). On a 5-day cycle, runs a purchase routine.
When the product is set and stock is below capacity, computes order
size: `(efficiency × capacity × 4) / 100`.

Goods are received from the linked supplier. The receipt is capped by
the link's unit quantity, by room under capacity, and when the link's
projected quantity is below its projected flow, by a further scalar.
A positive receipt:
- Adds the order size into the link's quantity-sum and the product total
- Adds the receipt into quantity-carry
- Blends unit price and quality with the link
- Adds receipt to stock
- Posts Freight Cost (category 5) as `unit-price-at-source × receipt`

The game's freight-rate routine measures the distance between two
points as straight-line (Euclidean) distance rounded to the nearest
whole number. It is not Manhattan distance. The rate is
`product factor × distance × product value / 100 / 100 × 0.5`, with a
minimum of 0.01. Which product fields the two factors are hasn't been
confirmed.
- Training credits are `(receipt × 80) / order-size`

When the supplier firm type is nonzero, the receipt also flows through
the sales accounting path, recording revenue for the supplier.

### Sales

The cap is `(efficiency × multiplier × capacity) / 100`, where the
multiplier is 2 for live-inventory firms (Department Store, Restaurant)
and 4 for others. The sold count is capped by stock.

A positive sale:
- Subtracts from stock
- Runs item-sell on the product link (recording money, units, margin)
- Subtracts from quantity-carry
- Training credits: `(count × 100) / cap`
- Posts Sales Revenue (category 0) as `count × unit-price`
- For Department Store and Factory: posts Purchase Cost (category 4)
  as `count × unit-cost`

A secondary quantity, reduced by quantity-carry for live-inventory firms,
flows into the link's flow field and the product daily total.

Returns true when stock is still below capacity (triggering the supply
pull to restock). A product-ID of 0 also returns true.

The take-linked step moves stock from the linked job using the same
stock-move and quality-blend as Inventory and Private Labelling.

### R&D and Software R&D

Shared behavior. Product research (R&D) and software research
(Software R&D) differ only in dialog text. Returns 0 (no supply pull).

When the research-flag short is 0 and the firm is non-operational,
stores 1 in a pause flag. Otherwise, with a valid product set, adds
14 training credits per visit. When
`(day-serial − start-date) / 30` reaches a duration threshold,
the research completes. The duration is read from a 7-entry lookup
table indexed by the product's technology-year rating:

| Tech years | R&D duration |
|-----------|-------------|
| 0 | Instant (0 months) |
| 1 | 6 months |
| 2 | 12 months (1 year) |
| 3 | 24 months (2 years) |
| 4 | 36 months (3 years) |
| 5 | 60 months (5 years) |
| 6 | 120 months (10 years) |

A tech-year value of 100 is a sentinel meaning the product is already
fully researched, with an effective duration of 0.

### Software Production

Produces software units. Each day adds
`min(remaining-room, efficiency × capacity)` to stock. Training credits
are the production ratio. Returns true when stock reaches capacity
(no reserve draw, unlike extraction). Monthly rolls production:
copies current to previous, zeros current. Has its own gate function.

### Advertising

Returns 0 (no supply pull). The daily work step walks the firm's linked
jobs to find which product to advertise: the last linked job with a
valid product becomes the ad target. If the target product changes
(switches from none to active, or vice versa), the ad rating is
refreshed.

The gate function drives two periodic cycles:

1. **Campaign management (every 60 days, staggered by firm index):**
   Searches the town for a media partner — a TV station or newspaper
   in the same town with revenue above a minimum threshold. Once found,
   computes an advertising budget based on the firm's financials,
   clamped between 50,000 and 500,000. This links the advertising job
   to the media firm.

2. **Monthly rating calculation (every 30 days, staggered):**
   Requires an active media partner. Walks the firm's Sales job slots,
   and for each Sales job with a live product: checks whether the
   product has sufficient technology level (above 14) and whether the
   ad rating needs filling. If a product's current rating is below
   its target (plus a threshold), the advertising is linked to that
   product's rating entry. If no products need advertising, the budget
   drops to zero.

In effect, Advertising jobs need a media firm in the same town to
function. The 60-day cycle finds the media partner; the 30-day cycle
directs ad spend toward products that need more market visibility.

## Financial accounting

Every financial transaction in the game flows through a categorized
posting system. When a firm earns revenue or incurs an expense, the
amount is posted both to the firm's own ledger and to the owning
corporation's ledger under a specific expense category.

There are 12 expense categories (numbered 0–11). Categories 0–8 apply
at both the firm and corporation level. Categories 9–11 are
corporation-only entries that cover interest, stock returns and land
revaluation:

| Category | Label                      | Typical source                  |
|----------|----------------------------|---------------------------------|
| 0        | Sales Revenue              | Department stores, shops        |
| 1        | Salaries Expense           | Employee wages, president pay   |
| 2        | Operating Overhead         | Monthly fixed cost per firm     |
| 3        | Training and New Equipment | Worker training program         |
| 4        | Purchase Cost              | Cost of goods in Sales jobs     |
| 5        | Freight Cost               | Transport cost in Purchase jobs |
| 6        | Advertising Spending       | Advertising campaign budgets    |
| 7        | Write-offs                 | Depreciation, spoilage, losses  |
| 8        | Raw Material Reserve       | Raw material consumption        |
| 9        | Loan Interest              | Daily interest charges          |
| 10       | Stock Return               | Stock/share transactions        |
| 11       | Increase in Land Value     | Monthly land revaluation        |

Categories below 9 are classified as "operating" — they count toward
operating profit. Categories 9 and above are "other profit" items.

Revenue posts add to monthly revenue, monthly net profit, operating
profit (if operating), and three expense-detail series (current month,
current year, lifetime), plus cash.

Expense posts subtract from monthly net profit and operating profit
(if operating), add to monthly expenses, add to the three
expense-detail series, and subtract cash.

Category 11 (land value) is posted directly to the corporation, not
through the firm. The accompanying balance transfer moves the delta
between the Cash and Land & Resource balance sheet accounts, leaving
actual cash unchanged.

The stock revalue (stock-count × unit-price) runs in the corporation
daily batch, after the job sweep — it is not part of the per-visit
job cycle.

## Product links

Product links are the supply chain connections between firms. They
carry quantity, price, and score data that drives the market simulation.
There is no per-type dispatch — every product link runs the same daily
logic.

### Link fields

Each link is 228 bytes with these key fields:

- **product-id**: index into the product catalog
- **next**: next link for this product (circular list, 0 = end)
- **firm-index**: owning firm
- **town-id**: town this link belongs to
- **score-in**: monthly pass publishes the max onto the product
- **score**: recomputed each visit
- **unit-cost, extra-cost, unit-price**: pricing
- **quantity**: current stock flowing through this link
- **units**: sold units
- **quantity-carry, flow-prev, flow, quantity-prev, quantity-sum**: flow tracking
- **month-money[12], month-units[12], month-margin[12]**: 12-month rolling history

### Link daily cycle

Called once per link visit (15 per frame). The logic:

**Gate:** if the product is inactive, return.

**1. Adjust score.** Always runs.

When the product is not placed in a town: score is a simple rounded
value.

When the product is placed: the score combines a base value with two
weighted town-product factors:
`score = base + (brand × town-brand-weight) / 60 + (score-in × town-score-in-weight) / 60`
The base value is a rounded figure whose formula was lost in the
decompile. The two weights are described under Market competition.

If the new score is lower than the old score and the firm has live
inventory, a slice of quantity is removed:
`slice = (old score − new score) × quantity / 100`. Each point of score
lost removes 1% of the quantity, and the quantity can't go below zero.
The same slice comes off the town's supply total. This penalizes links
whose score worsens.

**Gate 2:** if the firm doesn't have live inventory, return.

**2. Move quantity.** Only runs for live-inventory firms in valid towns.

- **2a. Shrink oversupply:** when the town-product supply exceeds demand
  and the link has positive quantity, removes `quantity / scalar`.

- **2b. Compute weight (0..100):** the firm's weight short × 5, plus
  50 for non-farmland tiles, clamped to 100.

- **2c. Reduce quantity:** compares this link's score, unit-price,
  score-in, and brand against the town-product **reference levels**.
  These are values the town keeps and lets drift at random; they are
  not averages of the competing sellers. When this link is *worse*
  than the reference, removes
  quantity. The removed amount is quadratic in the gap and proportional
  to `(100 − weight)`. Worse links lose more, and farmland locations
  (lower weight) lose more.

- **2d. Conditional increase:** when the link's projected quantity-sum
  is below 2 × its projected flow. Both are projected to month end as
  `previous-month value × (30 − day-of-month) / 30 + this month's value`:
  - **Increase quantity:** when this link is *better* than the town reference levels,
    adds quantity. Same four-factor comparison, reversed direction. The
    added amount is quadratic in the gap.
  - **Take quantity:** walks the product's circular list. Steals
    quantity from other same-town links whose metrics are worse. The
    stolen amount is quadratic in the gap between the competing links.

**3. Accumulate.** Updates the link's flow tracking:
- When quantity ≥ 1.0 or quantity-carry ≥ 1.0: quantity-carry is replaced
  by the current quantity.
- Otherwise: quantity-carry accumulates the current quantity.
- quantity-sum and the product total both increase by quantity.

**4. Town sum (every other day, even days only).** Zeros the
town-product supply total, then walks the circular list summing
quantity for the links in the same town. The walk stops when it gets
back to the visiting link, so that link's own quantity isn't added in
this walk. The walk also applies a price swap: if another link has the
same field-12 as this link, that link's field-0a equals this link's
field-12, and that link's field-12 differs from this link's field-0a,
this link copies the other link's unit price. (Field-12 is used as the
owning corporation's index elsewhere.)

### Score calculation (quality + brand)

A link's score is the core measure of competitiveness. It is a base
value plus two terms weighted by the town-product weights:

`score = base_score + (brand_rating × brand_weight / 60) + (score_in × score_in_weight / 60)`

Where:
- **base_score** is a rounded value whose formula was lost in the
  decompile. It is believed to come from the job's manufacturing or
  purchasing quality, but that hasn't been confirmed.
- **brand_rating** is the corporation's brand value in this town for
  this product. It is looked up in a record chosen by the brand
  strategy: corporate, range (product class) or unique (product). How
  the stored brand value is turned into this rating was lost in the
  decompile.
- **score_in** is the link's score-in field. The decompile doesn't show
  whether it holds the product's quality.
- **score_in_weight** and **brand_weight** are the town-product weights
  (see Market competition). They start from the product's
  consumer-decision percentages plus a per-town adjustment.

When the score drops between visits on a live-inventory link, the
quantity loses `(old − new) × quantity / 100`, floored at zero. Each
point of score lost costs 1% of the quantity. This is not the ratio
new_score / old_score: a drop from 60 to 30 keeps 70% of the quantity,
not 50%.

### Price determination

Prices flow through the supply chain:
- **Purchasing** sets unit_price from the supplier's pricing
- **Manufacturing** builds up unit_cost from ingredient costs
- **Sales** sells at the link's unit_price, posting revenue and computing
  margin as (unit_price − unit_cost − extra_cost) × count
- **Importing (Seaport)** prices are set from the product catalog's
  base price

Prices are not set by any explicit pricing algorithm — they emerge from
the supply chain. A firm's purchase price becomes its cost of goods,
and its sales price is the link's stored unit_price. The price
comparison in market competition measures each link's price against the
town's reference price and against each rival's price, rewarding lower
prices.

### Market competition

The market simulation is driven by **four-factor comparative scoring**.
There is no score-power split of demand. Each town-product keeps
**reference levels** that the links are measured against:

1. **Reference score**. It is rebuilt from the other references with the
   same formula as a link's score.
2. **Reference price**. It starts at the product's base price.
3. **Reference score-in**. It starts at 5–15.
4. **Reference brand**. It starts at 0.

These are not averages of the competing sellers. They drift at random
in a periodic town-product update, which also clears the month buckets
and is believed to run monthly. Price moves in 1% steps, and score-in
and brand move by ±1. The roll odds depend on a game setting and on how
supply compares with demand.

**Weights.** Each town-product has three weights that sum to 100:
- **Price weight** = one of the product's consumer-decision
  percentages + a town adjustment, clamped to 20–90.
- **Score-in weight** = another of the product's percentages + a town
  adjustment. It is at least 10 and at most 100 − price weight.
- **Brand weight** = 100 − price weight − score-in weight.

**Gap.** For a link compared with a reference (or with a rival), each
factor where the link is better (or worse) adds to a gap:
- score: `difference / 100` (against a rival: `(my_score − their_score + 1) / 100`)
- price: `price_weight × (price difference / (lower-side price + 0.1)) / 300`
- score-in: `score_in_weight × difference / 30,000`
- brand: `brand_weight × difference / 30,000`

The **link weight** w (0..100) is the firm's weight short × 5, plus 50
for non-farmland tiles, clamped to 100. It is recomputed on every visit.
A higher w moves less quantity. D is the town's demand figure and S its
supply total (reading these two fields as demand and supply is inferred
from how they are used).

**Three moves**, run in this order on each visit:

1. **Lose to the reference.** This only runs when a reference price,
   score-in or brand is non-zero. It uses the factors where the link is
   worse than the reference:
   `cut = (100 − w) × q × gap² × (q / D)² / 100`
   The cut is capped at q and comes off both q and S.
2. **Beat the reference.** This only runs when free demand
   `f = D − S ≥ 0`, using the factors where the link is better:
   `add = (100 − w) × f × gap² × (f / D)² / 100`
   The add is capped at f and goes onto both q and S.
3. **Take from weaker rivals.** For each other link of the product whose
   firm is in the same town, it uses the factors where this link beats
   that rival:
   `take = (100 − w) × (their_q × gap² × (their_q / D)² × 120 / 100) / 100`
   The take is capped at their_q and moves from the rival to this link.
   w is the taker's weight, not the rival's.

Moves 2 and 3 only run when the projected quantity-sum is below 2 ×
the projected flow (see Link daily cycle, step 2d). Before any move, an
oversupplied town (D < S) trims each link by `q / 50`.

The transfer amounts are **quadratic in the gap** and in the share term,
so links that are far from the reference or a rival move much more
quantity than links that are close. This creates a winner-takes-most
dynamic.

### Brand perception

After each sale, the game adjusts the corporation's brand value in the
town. The brand record is chosen by the brand strategy: corporate,
range (product class) or unique (product). Each corporation has two
numbers there: a brand value and an **awareness** A (0–100, built by
the monthly cycle below). There is no update while A is below 1.

1. Expected level:
   `raw = 2·P × score_in / max(50, top_score_in) + (100 − 2·P) × score / max(50, top_score)`
   P is one of the product's consumer-decision percentages. The top
   score-in and top score are the product's highest values, published
   each month.
2. Per-town penalties: raw loses 3 × (count − 1) for one per-town count
   under corporate branding, and for a second per-town count under
   corporate and range branding. What the two counts measure wasn't
   identified. raw is floored at 0.
3. Target: `A × raw / 50 − A`, so the target runs from −A to +A.
4. Step: if the target is at or below the current value, the step is
   −0.1. Otherwise it is +0.1 under unique branding, or 0.1 divided by
   the second per-town count under the other strategies.
   `step × units_sold / max(units_sold, D)` is added, and the brand
   value is clamped to ±A.

The value always moves in the direction of the target; it doesn't stop
at the target. Consistently high scores therefore raise brand, and low
scores lower it. How the brand value feeds back into the link score was
lost in the decompile.

### AI firm type preferences by strategy mode

Each strategy mode has a preferred list of firm types the AI considers
building. The strategy dispatcher selects from this mode-specific list:

- For each firm type in the current mode's list that the corporation
  hasn't already built, scores it using the CEO's relevant expertise
  (retailing skill for stores, manufacturing for factories, R&D for
  research centers, farming for farms, raw material for resource firms)
- With 80% probability: picks the highest-scoring unbuilt firm type
- With 20% probability: picks a random firm type from the list
- 20-day cooldown between build attempts

**Establish mode** (10 types): Department Store, Factory, R&D Center,
Farm, Logging Camp, Mine, Oil Well, Restaurant, Software Developer,
Software Publisher — every non-media firm type.

**Manufacture mode** (6 types): Factory, R&D Center, Farm, Restaurant,
Software Developer, Software Publisher — production and technology
firms, excluding basic retail and raw resource extraction.

**Retail mode** (2 types): Department Store, Restaurant — retail
outlets only.

**Dormant mode** (0 types): no preferred list. If forced to build,
picks randomly from all available types.

### Sales accounting (item-sell)

Called by Sales jobs and Purchasing (when the supplier type is nonzero).
For a positive sale count:

- link.units decreases by the count
- Monthly series update: money += unit-price × count, units += count,
  margin += (unit-price − unit-cost − extra-cost) × count
- When the product is placed and the firm is live: updates town-product
  monthly series and nudges a per-corporation town cell
- When the firm is live or the product is unplaced: updates product
  catalog monthly series (money and count)

### Monthly cycle

At each month boundary, for every occupied link:

- Zeroes the starting month's money, units, and margin buckets
- Snapshots: quantity-prev ← quantity-sum, flow-prev ← flow
- Resets: quantity-sum ← 0, flow ← 0
- For live-inventory firms: looks up a rating row for the (town,
  corporation, brand record) triple and stores 30.0 at row offset +6.
  It then computes
  `δ = ((30 − row value) × u / max(u, D)) / 100`,
  where u is last month's units + 1 and D is the town's demand figure.
  δ is ×0.25 under corporate branding, ×0.5 under range branding and
  ×1 under unique branding. It is added to the row value and to the
  corporation's brand awareness A in the town. A is set to 100.0 when
  it passes 100. So the row value converges on 30, and awareness grows
  with sales relative to town demand.

After all links, the catalog publishes the maximum score-in and score
across all links onto each product's high-score fields.

## AI corporation strategy

The competitor AI is a scheduled state machine that runs inside the
corporation daily method, after the three-layer sweep. Each competitor's
decisions are staggered by a per-corporation schedule offset to avoid
all competitors acting on the same frame.

### Strategy modes

The AI operates in one of four modes:

| Mode | Name | Behaviour |
| --- | --- | --- |
| 0 | Establish | Build retail chains, vertical integration |
| 1 | Manufacture | Focus on factories, supply for existing products |
| 2 | Retail | Focus on stores and distribution |
| 3 | Dormant | No expansion; waits for capital / market conditions |

Mode transitions happen every 200 days, driven by the CEO's personality
traits (not the game difficulty setting):
- Mode 1 → 0: when factory count exceeds a salary-trait-derived
  threshold AND time in mode exceeds a salary-trait-derived duration
  (typically 10–16 years)
- Mode 2 → 0: when store count exceeds the same trait-derived threshold
- Any non-3 → 3: when no subsidiaries AND enough years since mode start
  (scales inversely with CEO aggressiveness)

### Decision schedule

All AI decisions are staggered by a per-corporation offset:

| Interval | Action |
| --- | --- |
| Every 15 days | Strategy dispatcher — pick a product, build or expand |
| Every 15 days | Link supply chain for pending builds |
| Every 30 days | Financial analysis |
| Every 30 days | Market survey and pricing |
| Every 60 days | Vertical integration — build retail chain |
| Every 365 days | Expand into new products |
| Variable (CEO aggressiveness-scaled) | Market dominance — expand if #1 in revenue and profit |
| Every 200 days | Strategy mode transition check |
| Every 200 days | Bankruptcy check |

### Strategy dispatcher (every 15 days)

The algorithm for choosing what to build:

**1. Product selection.** The current mode's product list is read from a
table (10 bytes per mode: count + pointer to product-ID array).

- **80% chance:** score each product using the CEO's expertise skills.
  Scores come from category-dependent skills:
  | Product category | CEO skill used |
  | --- | --- |
  | Factory | Retailing skill |
  | Store | Manufacturing skill |
  | Vertical | R&D skill |
  | Farm | Farming skill |
  | Other (5–7) | Raw Material skill |

  Note: the mapping is cross-wired — the factory category uses the
  retailing skill, and the store category uses the manufacturing skill.
  A CEO with strong retailing expertise tends to build factories (to
  supply retail), while one strong in manufacturing tends to open stores.
  Only products the corporation doesn't already operate are considered.
  The highest-scoring product is picked.
- **20% chance:** picks a random product from the list.

**2. Feasibility check.** Before building:
- For vertical integration: cash must exceed
  `(threshold − last-month-revenue) × scale1 × scale2`
- For other categories with existing subsidiaries: cash must exceed
  `land-value + template-cost`, scaled by
  `(4 − CEO_aggressiveness − 1) × subsidiary-count × 50,000`
- For the first build of its type: always feasible

A 20-day cooldown prevents the same product from being retried.

**3. Build dispatch** by category:

| Category | Action |
| --- | --- |
| Factory | Build a factory |
| Store | Build a store |
| Vertical | Evaluate catalog, invest based on revenue vs. position |
| Farm | Build a farm/plantation |
| Media/Ads | Find the city with best demand, build there |
| (empty) | No-op |

Dormant mode skips the product table. Instead it checks if enough years
have passed (salary-trait-derived + random 0–5) since entering dormant.
If so, triggers vertical supply chain evaluation.

### Profitability gating

Before each build, the AI checks whether existing firms of this type
are profitable. It walks all owned firms of the target type, counts
total vs. profitable (last month's revenue > 0). Build proceeds if:
- No existing firms of this type (always build the first one), OR
- Profitable ratio exceeds the character-type threshold:

| Character Type | Minimum Profitable % |
|----------------|---------------------|
| Conservative | 80 % |
| Moderate | 60 % |
| Aggressive | 45 % |
| Very Aggressive | 30 % |

A Conservative CEO will not expand unless 4 out of 5 existing firms of
that type turned a profit last month. A Very Aggressive CEO only needs
1 in 3. This is one of the largest behavioral differences between
character types — it directly controls how fast AI corporations expand.

### Location selection

The shared location finder:
1. Gets the target city center coordinates and base radius
2. For rural: uses base radius. For urban: base radius + 4
3. Caps search radius at 4
4. Generates random offsets within the radius, clamped to map bounds
   (240 × 198 tiles)
5. Checks tile type: rural needs farmland tiles, urban needs city tiles
6. Checks that no existing firm occupies the tile
7. Retries up to 20 times, expanding radius by 1 each failure

### Firm creation

The shared AI build path:
1. Check map tile availability
2. Look up the firm template
3. Read land value for the tile
4. Compare `land-value + setup cost` (the firm type's real setup cost)
   against corporation cash. Competitors use their real cash here
5. If too expensive: attempt to sell assets / adjust debt
6. Re-check affordability — if still too expensive, fail
7. Create and initialize the firm

Each build type has a **30-day cooldown** to prevent spam-building.

### Supply chain linking

After building a firm, the AI configures what it produces and sets up
the supply chain. This happens in two phases:

**Phase 1: Plan.** Analyzes the product group's 9 job slots. For each
purchasing/selling slot that references a product with no current
supply, classifies inputs into three lists:
- **Raw materials:** need farms (source type 3 or 5)
- **Manufactured goods:** need factory links
- **Local inputs:** need local production

If raw materials require farms that don't exist yet, the plan is saved
as a deferred link — the AI remembers what it needs and checks back
later.

**Phase 2: Link** (immediate or deferred). Processes the three lists:

1. **Raw materials:** first tries to find an existing owned farm. If
   none, builds a new farm near the product's preferred city. Assigns
   raw material products to the farm's job slots, defaulting to 1 unit
   if no demand data exists.
2. **Manufactured goods:** finds the best matching product group (most
   overlap with needed products). Finds a location, builds a Department
   Store, and binds the product group.
3. **Local inputs:** finds a suitable local production site and builds
   the appropriate firm type.

**Deferred linking** (same 15-day gate): when a pending build exists,
checks that all input farms have nonzero output. Once all farms are
producing, completes the wiring and clears the pending state.

### Vertical integration (every 60 days)

In Establish or Manufacture mode, when no build is pending:

1. **Build retail outlet:** finds an unsold product (worst
   demand/supply ratio that the corporation doesn't already sell), plans
   the supply chain, builds a store and links it.
2. **Build supplier:** finds the product with the highest demand surplus
   (doubled if currently zero supply), builds a supplier firm.
3. In Establish or Retail mode: adjusts pricing/marketing.
4. If any build succeeds while dormant: transitions to Establish mode.

### Market dominance (variable interval)

Fires at an interval determined by the CEO's aggressiveness: a
Conservative CEO checks every 160 days, Moderate every 120 days,
Aggressive every 80 days, and Very Aggressive every 40 days.

Only acts when all conditions are met:
- Hired manager is active
- Corporation age > 5 years
- No current investment target
- Corporation is #1 in both revenue and profit

Triggers an escalating cascade — each step is tried in order, stopping
on the first success:

**Step 1: Build a store** for the best-scoring product.

**Step 2: Build a farm** for raw material supply.

**Step 3: Enter new markets.** Scans all product types for ones where:
the technology is available, demand exists, and the corporation has
zero market share and no existing presence. For each qualifying
product, the AI builds a store (for retail products) or farm (for raw
materials). The number of builds per call is limited by the CEO's
aggressiveness level plus one — a Conservative CEO builds at most 1
new business, while a Very Aggressive CEO builds up to 4.

**Step 4: Last-resort diversification.** If the corporation is #1 but
still has untapped markets, scans all products where the corporation is
not the dominant player. For each, finds towns where the corporation
has zero market share and builds there. Same build limit: CEO
aggressiveness + 1 per call.

**Step 5: Intensity follow-up.** After diversification, if the CEO is
Aggressive or Very Aggressive and the expansion intensity is high:
checks whether the corporation is still #1 in revenue and profit. If
it has lost its lead, the expansion intensity resets. Sets a cooldown
based on aggressiveness (the most aggressive CEOs cycle back fastest).

### Asset sale (cash shortfall)

When the AI needs cash for a build but doesn't have enough, it tries
an escalating sequence to raise it. Some steps depend on a setting on
the corporation's chairman whose meaning is not known.

1. Sell shares it holds in other corporations, apparently the cheapest
   stock first (only if the chairman setting is on, and only when stock
   investment is allowed in the game).
2. Take a bank loan of at least $100,000, limited by the credit limit.
3. If it is still short, the chairman setting is off and its cash is
   still positive, it gives up here.
4. Issue new shares of its own stock (only for a listed corporation,
   and only if at least 10,000 shares can be issued).
5. Sell holdings in other corporations again.
6. Issue new shares again, up to 10 more times.
7. Only if cash is still below zero, close firms one at a time: an
   R&D Center, apparently the least profitable, unless one of its firms
   carries a flag (meaning not known) that sends it first. Whether a
   closed firm returns any cash is not known.

The process stops as soon as the corporation has enough cash for the
planned build. If it is still short, the build is cancelled. This path
is live in normal play, because competitors build with their real cash.
Only the Government corporation skips it: its cash is reset to $1
billion just before each of its own placements (see Cash management).

### Bankruptcy check (every 200 days)

Runs on the same 200-day schedule as mode transitions. Conditions:

- Corporation age exceeds 10 years
- No subsidiary companies
- Combined cash plus investment value falls below a fixed threshold

When all conditions are met, the corporation is liquidated.

### Annual expansion (yearly)

Once per year (365-day interval), the AI evaluates whether to expand
into new product categories. The CEO's expansion trait controls the
aggressiveness threshold: a higher trait value (range 20–99) means the
AI enters new markets more readily. The threshold is the trait value
plus 25, compared against a market opportunity score.

### Market survey (every 30 days)

The 30-day market survey runs different logic depending on hired
manager state:

- **No active hired manager:** pricing adjustment only
- **Active hired manager + stock market enabled:**
  1. Evaluate potential investment targets
  2. Adjust pricing or invest surplus cash
  3. Analyze market positions
  4. Execute stock trades based on analysis

### Pricing and investment (30-day cycle)

For non-investor corporations (investment budget is zero or negative),
the AI computes a cash reserve based on a personality trait:
- Hired managers use their salary trait
- CEOs use a different personality trait
- Reserve = `(200 − trait) × cash_needs / constant`

Cash above the reserve is available for stock purchases. The AI finds
the most attractive stock target and invests the surplus.

### Financial analysis (every 30 days)

Two activities run on the 30-day financial cycle:

1. **Surplus investment:** If the corporation has an investment budget,
   surplus cash above operating needs is invested into stocks.
2. **Share buyback:** If the corporation's P/E ratio is high enough AND
   all 12 months were profitable, the AI buys back its own shares.
   The buyback amount depends on CEO aggressiveness and a personality
   trait: more aggressive CEOs with lower trait values buy back more.

### Stock and investment tracking (daily)

Every day, the shared AI routine calculates the unrealized profit or
loss from the corporation's stock holdings. It sums up the current
market value of all held shares, compares to the previous day's total,
and posts the difference as investment revenue. This is mark-to-market
accounting — gains and losses appear in the income statement as they
occur, not when shares are sold.

### Portfolio management (daily)

Corporations with an active portfolio run daily portfolio maintenance:
1. Evaluate current portfolio performance
2. Rebalance holdings if needed
3. Record the current portfolio value in a 30-day rolling history

### Hired corporation behavior (daily)

When a CEO retires (the player selects "Retire" from the dialog), their
corporation transitions to a hired-manager-run entity. These
corporations have a very simple daily behavior: the cash reserve
threshold is set to twice the previous month's revenue. Any cash above
that threshold is invested into the stock market, up to the investment
budget. There is no expansion planning, no building, and no strategic
decision-making — the hired corporation is purely a passive investor.
The Purchasing and Sales jobs also have no special behavior for this
corporation type (the type-specific check slot is a no-op), so these
operations continue normally under their common processing path.

### Strategy parameter change (1/1,000 daily)

On any given day, there is a 1 in 1,000 chance that the AI randomly
adds a new business in a random town. This roll is part of the
**Government corporation's** daily routine, not the competitors'. The business type is drawn from
a small set (department stores or similar). The maximum number of
businesses per type is capped based on the town's level — smaller towns
support fewer businesses (2 per type for the smallest, up to 4 for the
largest).

### Cash management

The $1 billion cash reset applies to the **Government corporation
(type 4) only**. Its daily routine runs the shared AI daily (financial
posts, stock/investment, portfolio, per-city product census) and then
sets its cash to $1 billion. Its seaport and media placements also set
cash to $1 billion just before building. The Government corporation
therefore never runs short.

Competitor corporations (type 3) are **never** reset. They pay for
builds from real cash, use the asset-sale sequence when short, and can
go bankrupt.

The Government daily also rolls:
- 1/1,000 chance per day: the placement roll above
- 1/10,000 chance per day, only when a configuration flag is set and
  more than 3,650 days have passed since its initial placements: a new
  **seaport** (not a new competitor corporation)

## Plan system

A **plan** is a firm layout template — a saved configuration of up to
9 job slots that can be applied to build or reconfigure a firm in a
single action. Plans store everything needed to replicate a firm layout:
what each slot produces, what products it works with, the parameters for
each job, and the connection wiring between slots.

### What a plan contains

Each plan record holds:

- **Description** — a text name for the plan (up to 28 characters)
- **Firm type** — which kind of firm this plan applies to (factory,
  store, farm, etc.), organizing plans into folders
- **Valid flag** — whether the plan represents a usable layout
- **Connection bitmask** — a 20-bit mask encoding which of the 20
  possible links in the 4-column × 5-row grid layout are active. These
  connections represent the physical wiring between job slots in the firm
- **9 job slots** — each slot stores:
  - Job type (purchasing, manufacturing, sales, R&D, etc.)
  - Product (which product this slot works with)
  - Parameter 1 (job-type-specific: ad target, trade product, etc.)
  - Parameter 2 (used by certain job types like livestock processing)
- **Demand products** — up to 4 unique products derived from any Sales
  job slots in the plan, used for scoring market opportunity

Plans are stored in memory at 127 bytes each but serialize to just
72 bytes on disk (9 slots × 8-character product codes), with the full
record reconstructed at load time by looking up each product code.

### Plan folders

Plans are organized into **folders** by firm type. Up to 10 plan folders
can exist, each corresponding to a category of firm. When browsing plans,
the player navigates between folders to find plans for the type of firm
they want to build or reconfigure.

Two distinct plan collections serve different purposes:

- **Factory/manufacturing plans** — used when building factories and
  supply chain firms
- **Store/retail plans** — used when building retail outlets and
  distribution firms

### Plan editor (player interface)

The plan editor is a dialog accessible to the player for managing their
library of firm layout templates.

**Browsing.** Plans are shown one at a time, with a layout preview
displaying the 4×5 grid with connection lines and 9 labeled job
rectangles. The player navigates by record number within the current
folder. The display shows the plan's firm type, description, and a
visual representation of the connection wiring.

**Capturing a layout.** The player can save any firm's current
configuration as a plan:

1. Select a firm on the map
2. The editor reads the firm's current job configuration — all occupied
   slots with their types, products, and parameters
3. The captured plan is stored in the folder matching the firm's type

Restrictions:
- A firm must be selected on the map
- The firm must have an active layout (at least one configured slot)
- The firm's type must match the current plan folder being viewed

**Applying a plan.** To build from a plan, the player selects a target
firm on the map and applies the plan. This:

1. Verifies the player owns the target firm
2. Verifies the firm has an existing layout
3. Verifies the firm type matches the plan's type
4. After a confirmation prompt ("The plan will replace the existing
   layout of the highlighted firm, proceed?"), creates all 9 job slots
   from the plan's template

**Other operations:**
- **Delete** — remove a plan from the folder
- **Replace** — overwrite a plan with a new captured layout
- **Sort** — reorder plans within a folder

### Plan scoring

Plans can be evaluated for market opportunity based on their demand
products (the products sold through Sales-type job slots):

- An invalid plan (no layout data) scores −1,000
- If any demand product faces zero competition, the plan scores 10,000
  (maximum opportunity — an uncontested market)
- Otherwise, the score is derived from a competition-weighted analysis
  of the demand products' market data

Revenue estimates are also available, computed from the market size data
for each demand product.

### How the AI uses plans

The AI competitor corporations rely heavily on the plan system for their
long-term building strategy. The plan library is the bridge between the
AI's strategic goals and the concrete act of constructing firms.

**Plan selection.** When the AI decides to build, it evaluates plans from
the appropriate folder:

- For **factory builds**, the AI iterates plans (in random order for
  undirected builds, or filtered by a specific product), checking:
  - Product availability (technology discovered, product in season)
  - Purchasing capability (supply chain exists or can be built)
  - Supply gaps for each Sales-type slot (total demand minus the
    corporation's current share)
  - A seasonal check ensures demand products are plantable within ±1
    month of the current planting window
  - The final score combines market opportunity minus average supply gap
- For **store builds**, a simpler selection samples random plans and
  picks the one with the best market opportunity score (minimum 100)

**Two-phase execution.** The AI's plan execution can be immediate or
deferred:

1. **Immediate:** If all input products are already available in the
   market (farms producing, factories running), the AI builds the firm
   and wires up the supply chain right away.
2. **Deferred:** If the plan requires products that don't exist yet
   (e.g., raw materials that need a farm), the AI:
   - Saves the plan as "pending" with three lists of needed products:
     raw materials (need new farms), manufactured goods (need factory
     links), and local inputs (need local production)
   - Every 15 days, checks whether all pending farms have started
     producing (nonzero revenue plus cost)
   - Once all inputs are available, completes the build and wiring

This two-phase approach is why the AI appears to plan ahead — it commits
to a production chain, builds the supporting farms first, then builds
the main facility once supply is guaranteed.

**Plan-based firm creation.** When a plan is applied to a firm (whether
by the player or the AI), all 9 job slots are created from the template.
The connection bitmask is copied to establish the physical wiring.
Job-type-specific configuration is applied per slot (factory production
settings, store product assignments, advertising targets, etc.). The
firm then begins operating immediately in the next daily cycle.

## Person system

Behind every corporation is a **person** — the CEO or hired manager who
runs it. The game tracks up to 15 persons in a global array. Person
records carry identity, personality, expertise, satisfaction, and the
link to the corporation they control.

### Person lifecycle

Every person has a lifecycle state:

| State | Meaning |
|-------|---------|
| Empty | Slot is unused |
| Active | Initialized, waiting to act |
| Linked | Employed at a subsidiary |
| Retired | Former CEO, no longer active |

At game start the player person is created first, then the remaining
slots (up to 14, minus the starting competitor count minus 1) are
filled with random persons. Each random person begins as an
**Independent Investor** — active but not yet running a corporation.

### Competitor spawning

Independent investors can spontaneously create new competitor
corporations. Each day, every active independent investor has a **1 in
3** chance to found a new company, subject to:

- A per-person cooldown timer
- The global competitor count being below the configured cap (and below 12)
- On the very first game day, an additional 1/100 gate applies

After 10 game-years (3,650 days), there is a 50 % chance that a
new competitor enters **Dormant** strategy mode instead of the
normal distribution across the four modes.

### Character types

Each person has a character type that reflects their overall
aggressiveness:

| Index | Label | Description |
|-------|-------|-------------|
| 0 | Conservative | Least aggressive |
| 1 | Moderate | Balanced |
| 2 | Aggressive | Expansion-oriented |
| 3 | Very Aggressive | Maximum aggression |

The game-start setting "Competitor Character" controls how character
types are assigned. When set to a specific type, new persons cluster
around that value but may drift based on the current average across
all active persons. The "Random" setting assigns a uniform random type.
The "Pre-defined" setting uses built-in defaults.

### Expertise skills

Every person has seven expertise areas, each rated 0 to 100:

| Skill | Performance Weight |
|-------|-------------------|
| Manufacturing | 25.0 % (highest) |
| Research & Development | 17.5 % |
| Farming | 15.0 % |
| Advertising | 15.0 % |
| Training | 15.0 % |
| Retailing | 7.5 % |
| Raw Material Production | 5.0 % (lowest) |

These skills are combined into a weighted **performance score** that
drives salary expectations and management competence. Manufacturing
expertise dominates at a quarter of the total weight.

The "Competitor Expertise Level" game-start setting controls how
expertise is distributed. Higher settings give competitors stronger
starting skills.

### Person-corporation link

Persons are linked to corporations by matching the person's ID against
three slots in each corporation record:

- **CEO slot**: person becomes the corporation's chief executive
- **Hired manager slot**: person is employed as a manager hired by the player
- **Employee slot**: person is confirmed as working at a subsidiary

When the player retires (via the in-game dialog), their corporation's
type changes from Player (1) to Hired (2), meaning a hired manager now
runs it.

### Role titles

Each person displays a role title based on their current position.
There are six role titles plus two special labels:

| Role | When shown |
|------|------------|
| Human Player | The player character (role state 0) |
| CEO | Running a corporation as chief executive |
| Chairman | Confirmed employee at a subsidiary |
| CEO & Chairman | CEO who also holds the chairman position |
| President | Hired manager running a corporation |
| President & Chairman | Hired manager who also holds chairman |
| Independent Investor | Not linked to any corporation |
| Retired | Former CEO, no longer active |

The "CEO" and "President" roles are assigned when the person is first
linked to a corporation. The "& Chairman" suffix is added when the
person is also registered in a second corporation's employee slot,
confirming a dual role.

### Satisfaction

Each person tracks a satisfaction value labeled **"Attitude Towards You"**
in the game's UI:

| Range | Label |
|-------|-------|
| Below −50 | Very Bad |
| −50 to −1 | Bad |
| Exactly 0 | Neutral |
| 1 to 49 | Good |
| 50 and above | Very Good |

**Monthly drift.** Every 30 days (staggered so one person is checked
per day), satisfaction adjusts:

- If satisfaction is negative, it drifts toward zero by 1 point per
  check (unhappy managers gradually forgive).
- If the person's current wealth is at or below their stored reference
  salary, satisfaction gains 0 or 1 points (small random drift).
- If current wealth exceeds the stored salary, satisfaction gains 1 or
  2 points (the manager is earning well and becoming happier).

Over time, a well-paid manager's satisfaction climbs steadily, while
an underpaid one stalls near neutral.

**Salary raise penalties.** When a raise dialog fires and the player
declines, or when the manager accepts a salary offer, satisfaction
drops sharply by 30 to 60 points (random within that range). This
single penalty can push a "Very Good" manager down to "Bad" in one
event.

**Rejection disappointment.** If the player refuses a January raise
request, the game computes a wealth ratio — how much the manager's
wealth has grown relative to their stored salary. If their
satisfaction is already low enough relative to this ratio plus a
threshold of 50, the manager escalates to the "let go or offer raise"
dialog instead of merely complaining. Otherwise the manager shows
"is disappointed by your rejection" and takes a satisfaction hit
proportional to the wealth gap.

### Salary and retention

After the first 30 game-days, each person runs a salary retention
check on a staggered schedule (one person per day cycle). The
probability of a salary demand firing on any given check is:

> probability = 1 / (10 − salary_trait / 10)

A higher salary trait makes demands more frequent. For example, a
salary trait of 50 gives probability 1/5 (20 % per check), while a
trait of 90 gives 1/1 (100 % — demand every check).

The salary retention chain has two stages:

1. **Salary demand.** Only fires if the person's wealth is at least
   $1,000,000 and they hold a CEO role. The person evaluates whether
   they want to stay at their current corporation by computing a
   loyalty threshold based on their personality traits. If their years
   of service fall below this threshold, they look for opportunities in
   other towns instead. Higher salary trait and higher "trait 7" values
   reduce the threshold, making the person more willing to stay.

2. **Job seeking.** After the salary demand, the person looks for a
   better position elsewhere. They find a candidate town, check whether
   any firms there would take them, and compute the available salary as
   a fraction of that town's corporate revenue (5 % of revenue, then a
   random 20–100 % of that). If the available salary exceeds their
   current pay, they switch corporations.

**January wealth comparison.** In addition to the daily retention
cycle, every January a separate check fires for hired managers of the
player's corporation. The manager compares their current wealth to
their stored reference salary. If wealth has grown by more than 10 %
(i.e., current wealth > stored salary × 1.1), the manager requests a
raise:

- Dialog: "[Name] asked for a raise in salary from [old] to [new].
  Do you agree?"
- If the player agrees, the stored salary updates to the current
  wealth (resetting the comparison baseline).
- If the player refuses, the outcome depends on the manager's current
  satisfaction relative to the wealth gap. If satisfaction is low
  enough, the manager escalates to the "let go or offer raise" dialog.
  Otherwise they show disappointment and take a satisfaction penalty.

**Random salary trigger.** During each monthly periodic check, hired
managers also have a random chance of requesting a raise, with
probability 1 / (150 − performance_score). A high-performing manager
triggers this more often. If the player declines, satisfaction drops
by 30 to 60 points.

**Salary negotiation.** When the "offer a salary raise" path is taken,
the player enters a salary amount. The game computes a target salary
based on the manager's weekly pay, years of service, and annual base.
Longer service increases the demand. If the player's offer meets or
exceeds this target (adjusted by a random tolerance factor), the
manager accepts and stays. If the offer is too low, the manager
rejects it and resigns immediately.

### Hired manager system

**Hiring is player-only.** There is no AI hiring code — AI
corporations receive their CEOs exclusively through the competitor
spawning system. Only the player can recruit a person as a hired
manager.

**Acceptance check.** Whether a person accepts depends on their
current satisfaction:

> acceptance threshold = acceptance_trait / 2 − 100

With the default acceptance trait of 0, the threshold is −100 (the
person will accept unless satisfaction is catastrophically low). Even
with a maximum random acceptance trait of 99, the threshold only
reaches −51, meaning the person rejects only if satisfaction is "Very
Bad". In practice, most recruitment offers are accepted.

If accepted, the person announces their requested annual salary and
the player can agree or decline.

**Displacement.** Hiring a new manager displaces any existing one:
- If the player's corporation already has a hired manager, that person
  is fired first.
- If the target person is CEO of another corporation, they are removed
  from that role first.

**Firing.** When a hired manager is terminated (by player choice or
because they resigned after a salary negotiation failure), all firms
they personally managed are reassigned to the corporation's CEO. The
hired manager slot is cleared and the person returns to the
independent investor pool.

**President Policies.** The player can also set policies for the hired
manager:

- **Pricing Policy**: Normal, Aggressive, or Very Aggressive
- **Change Internal Sale**: toggle
- **Look for Better Supplies**: Don't look / From Own Firms Only / From Any Firms
- **Look for Better Products**: toggle for department store supply

### Gender

Persons have a gender flag (male or female). It affects only the
pronouns used in dialogs: "him"/"her", "he"/"she".

### Personality traits

Each person carries 13 internal personality values. When the
"Random Competitor Personality" game-start option is enabled, these are
randomized within individual ranges; otherwise they default to
moderate baseline values (50 for most traits). The player's own
person always uses the moderate defaults regardless of this setting.

**Only 5 of the 13 traits have any effect on gameplay.** The remaining
8 traits are initialized and stored but never read by any game logic.
They appear to be vestigial — designed for a more complex personality
system that was never completed or was removed before release.

The five active traits are:

**Character type** (the aggressiveness level: Conservative through Very
Aggressive). This is the single most influential personality parameter:
- Controls market dominance check frequency (40–160 days between checks)
- Sets the profitability threshold for building (looked up from a
  4-entry table; aggressive CEOs tolerate lower profitability)
- Limits builds per expansion call (aggressiveness + 1, so 1–4 builds)
- Sets cooldown after dominance actions (shorter for aggressive CEOs)
- Controls share buyback amounts (more aggressive = larger buybacks)
- Scales feasibility requirements for new builds
- Influences mode transition timing

**Salary trait** (range 20–99). The most multi-purpose trait beyond
character type:
- Controls salary demand probability (higher = more frequent demands)
- Determines how many years the AI stays in dormant mode before waking
- Sets factory and store count thresholds for mode transitions
- Controls how long the AI stays in Manufacturing mode before switching
- Determines cash reserve calculations for hired managers
- Gates access to Stock strategy mode: only persons with salary trait
  above 59 can enter the Stock-focused strategy. This acts as a
  personality filter — roughly 50 % of randomly generated persons
  (with trait range 20–99) qualify.

**Trait 7** (range 0–99). Affects financial decisions:
- Modifies the share buyback threshold (subtracts from the aggressiveness-
  based buyback amount, so higher values reduce buybacks)
- Controls the CEO's cash reserve in pricing decisions (higher values
  mean a smaller reserve and more aggressive investing)
- Contributes to the salary demand loyalty threshold (combined with
  salary trait, divided by 4, and subtracted from a base of 25 years)

**Expansion trait** (range 20–99). Controls the annual expansion cycle:
- The AI expands into new product categories when a market opportunity
  score exceeds this trait value plus 25. Lower values mean the AI
  enters new markets more readily.

**Acceptance trait** (range 0–99). Controls whether a person accepts
a job offer from the player. The acceptance threshold is computed as
half this trait minus 100. With the default value of 0 (used for
player characters), the threshold is −100, meaning the person accepts
virtually any offer. Even at the maximum random value of 99, the
threshold is −51, requiring only moderately positive satisfaction.
This trait matters only for hiring — it has no effect on AI behavior,
salary negotiations, or any other system.

**Vestigial traits.** The following 8 traits are initialized with
random ranges when "Random Competitor Personality" is enabled but are
never read by any traced game logic:

| Trait | Random Range | Notes |
|-------|-------------|-------|
| Trait 0 | 30–99 | Unused |
| Trait 1 | 40–59 | Narrow range, unused |
| Trait 2 | 0–99 | Unused |
| Trait 3 | 20–89 | Unused |
| Trait 4 | 0–99 | Unused |
| Trait 6 | 0–99 (biased by salary trait) | Generated based on salary trait but never read |
| Trait 8 | 1–5 | Tiny range, unused |
| Trait 11 | 3–12 | Tiny range, unused |

**Strategy weights** — two values summing to at most 150, randomized at
creation. Like the vestigial traits, these are not referenced in any
traced AI decision code. They may have been intended for a weight-based
strategy selection system that was replaced by the current mode-based
AI before release.

## Towns and cities

The game world contains up to 12 named cities.  Each city is a living
economic entity with its own population, labor market, and consumer
economy.

### Simplified vs detailed mode

The new-game setting "Detailed City Development" controls whether towns
simulate their own economies.  When off, every city is frozen at a
middle tier with fixed indicators:

| Indicator             | Fixed value |
|-----------------------|-------------|
| City level            | 3           |
| Per-capita GNP        | 20,000      |
| Economic climate      | Middle      |
| Labor cost index      | 100         |
| Consumer spending     | 100         |
| Labor quality index   | 100         |
| Unemployment rate     | 2.0 %       |

When detailed mode is on, all seven indicators update monthly and
cities can grow, level up, and spawn new ones. Population growth (with
its level-up check) and the yearly GNP-change record run for every town
in **both** modes; only the seven indicator updates are skipped when
detailed mode is off. Level-up is also blocked by a per-town frozen
flag, and whether simple mode sets that flag was not traced.

### City indicators

Every city tracks eight indicators, visible in the city info panel:

1. **City Population** — the total population (float).
2. **GNP** — equals per-capita GNP multiplied by population.
3. **Per Capita** — GNP per person, the core economic measure.
4. **Unemployment Rate** — percentage of idle labor.
5. **Labor Cost Index** — how expensive it is to hire workers.
6. **Labor Quality Index** — how skilled the available labor is.
7. **Consumer Spending Index** — local consumer purchasing power.
8. **Economic Climate** — an overall rating derived from GNP growth.

Two 12-month charts show population growth and GNP growth over the
past year.

### Monthly update cycle

Each city is assigned a stagger slot at creation.  On the day of the
month matching that slot, the city runs its full monthly tick.  This
spreads the load so all 12 cities do not update on the same day.

The monthly tick runs these steps in order:

1. **Population growth**:
   `growth = random(0–299) + 100 × GNP-term + 100 × (4 − unemployment) − 150`
   The **GNP term** is 50 × the yearly relative change in the city's
   total GNP: (this year's 12-month sum of population × per-capita GNP
   − last year's sum) / last year's sum. So it follows population as
   well as per-capita GNP, and a 1% yearly rise gives 0.5.
   Dampening: when growth ≤ 0 and population < 750,000, growth is scaled
   by population / 750,000. When growth > 0 and population > 1,500,000,
   it is scaled by 1,500,000 / population. Population is floored at 0.
   **Level-up**: when population ≥ 160,000 × level² and the town isn't
   frozen, the level rises by 1 per monthly tick. There is no cap, and
   the level never goes down.

2. **Per-capita GNP update**: each month, GNP is multiplied by
   `(295 + random(0–9)) / 300`. That is one of ten discrete steps from
   0.983 to 1.013 (roughly ±1.7%). It is clamped to the minimum for the
   city's current tier. If GNP exceeds the tier ceiling, the tier
   upgrades (at most one tier per month). The units of the tier floor
   and ceiling comparison are not settled: read literally, the
   decompiled comparison would never fire, which may be a decompiler
   misreading.

3. **Economic climate**: this month's **GNP term** (the same 50 × the
   yearly relative change in total GNP that drives population growth)
   is compared against the climate threshold table. The first threshold
   the term reaches wins. If none matches, the climate stays as it was
   (the last threshold is −100,000, so in practice one always matches):

   | Climate | GNP term | Label |
   |---------|-----------|-------|
   | Boom | >= 8 | Best economy |
   | Prosperous | >= 4 | Good |
   | Normal | >= -1 | Baseline |
   | Recession | >= -6 | Declining |
   | Panic | < -6 | Worst economy |

   The thresholds are in GNP-term units, not percent. Read through the
   GNP term, Boom needs roughly a 16% yearly rise in total GNP.

   In the UI, the bar is inverted so Boom shows the tallest bar.

4. **Unemployment rate** — adjusts randomly, biased by the economic
   climate:

   | Climate | Tendency | Random swing |
   |---------|----------|-------------|
   | Boom | Strong decrease | ±0.30% |
   | Prosperous | Moderate decrease | ±0.20% |
   | Normal | Balanced | ±0.10% |
   | Recession | Moderate increase | ±0.20% |
   | Panic | Strong increase | ±0.30% |

   Unemployment is floored at 2% and capped at 10%.

5. **Labor cost** — smoothly converges toward a target derived from
   per-capita GNP and a global scale factor. Each update moves 20%
   of the way toward the target. It will not drop below a minimum
   set by the city's per-capita GNP.

6. **Consumer spending** — smoothly converges toward a computed
   target (20% per update). Floored at 1.0.

7. **Labor quality** — smoothly converges toward a computed target
   (20% per update). Clamped between 1.0 and 100.0.

8. **Environmental factors** — three abstract economic factors (set
   randomly at city creation in the range -3 to +3) are adjusted.
   These feed into other indicator calculations.

### City levels and population thresholds

A city's level determines the size of its footprint on the map.  The
level-up formula is:

> population ≥ level² × 160,000

| Level | Population needed |
|-------|-------------------|
| 2     | 160,000           |
| 3     | 640,000           |
| 4     | 1,440,000         |
| 5     | 2,560,000         |
| 6     | 4,000,000         |

When a city levels up, every map tile within a distance of the new
level from the centre has a 1-in-10 chance of becoming a town tile, so
the footprint grows irregularly. The `level + 4` radius is the
**land-value** decay radius (see Land value). It is not the footprint,
and it is not a demand radius: no separate town demand radius was found.

### City tiers and starting GNP

Each city name in the database has a tier (0-3) that determines the
starting per-capita GNP range:

| Tier | GNP range | Character |
|------|-----------|-----------|
| 0 | $200 – $2,000 | Undeveloped |
| 1 | $2,200 – $7,000 | Developing |
| 2 | $7,200 – $14,000 | Established |
| 3 | $14,200 – $20,000 | Wealthy |

At creation, the actual GNP is chosen randomly within the tier's range.
During the game, if GNP grows past the tier ceiling, the city upgrades
to the next tier (its GNP minimum also rises). Tiers affect the GNP
floor — a tier-2 city can never drop below $7,200 per capita.

### Initial population

When a city is placed during map generation, its starting population
is derived from the city's tier in the name database: tier × 300,000
plus a small random offset (up to 30,000).

### City spawning

During a game (in detailed mode), new cities can appear.  The spawning
algorithm:

1. Tries up to 4,752 random positions on the 240 × 198 tile map.
2. Each candidate must fall on valid land (specific terrain codes).
3. A 5 × 5 tile area around the candidate must be entirely valid.
4. The candidate must be at least 15 tiles from every existing city.
5. The city name must not duplicate an existing one.
6. If a valid site is found, a new city is created with population
   derived from its name-database tier.

### Map terrain

The game map is a grid of 240 × 198 tiles.  Each tile stores:

- **Climate** — a value from 0 to 4, representing temperature zone.
- **Rainfall** — a value from 0 to 3.
- **Soil fertility** — a value from 0 to 100.

These tile properties are used by farming firms to determine crop
suitability.  Crop products define a "Suitable Climate" and
"Suitable Rainfall"; the tile where the farm is placed must match
for the crop to grow well.

### Town demand tracking

Each city maintains demand-tracking records for the products available
there.  When a firm type becomes active in or near a city, the city
creates a demand entry for it.  These entries are updated daily and
accumulate monthly revenue and quantity figures, feeding the consumer
side of the product link system. Each day, when an entry's demand
figure exceeds its supply total, the gap (and the gap × the reference
price) is booked into the entry's monthly quantity and revenue and into
the product's totals. Unmet demand therefore counts in the product's
market total, which is the denominator of market share. (Reading the
two fields as demand and supply is inferred from how they are used.)

## Stock market

The stock market is one of the game's core financial systems. Every
corporation (except government-type corporations) has a publicly
tradeable stock. The stock market can be toggled on or off in the
new-game settings ("Stock investment: on/off").

### Share creation and ownership

When a corporation is founded, its initial share count equals the
corporation's starting value divided by an initial price per share.
All shares are initially held by the corporation's CEO, and the cost
is deducted from the CEO's personal wealth.

Ownership is tracked separately for up to 12 corporations and 15
persons (the maximum counts of each in the game). The total of all
holdings equals the total shares outstanding. Shares not held by any
insider are considered "public float" — available for purchase on the
open market.

### Daily price movement

Stock prices update every game day using a random-walk model with
three components:

1. **Base random walk** — a small random price change whose range
   depends on the current economic climate:

   | Economic climate | Volatility |
   |-----------------|------------|
   | Excellent       | Very low   |
   | Good            | Low        |
   | Normal          | Moderate   |
   | Bad             | High       |
   | Very bad        | Very high  |

2. **Earnings momentum** — an accumulator that drifts the price based
   on the corporation's profitability. Positive earnings push prices
   up over time; losses push them down. The accumulator is clamped to
   prevent runaway drift.

3. **Random spikes and crashes** — on any given day there is roughly
   a 1 in 200 chance of a large random price shock, either up or
   down. This creates the occasional dramatic price movement.

The price can never go below zero.

Two decay factors reduce over time: the dilution effect from new share
issuances and the accumulated trading volume. This means the impact of
past events gradually fades.

### Stock metrics

The game tracks several financial metrics for each stock, updated
daily:

- **Equity per share** — the corporation's total equity divided by
  total shares outstanding.
- **Earnings per share** — the corporation's earnings divided by total
  shares.
- **Price-to-earnings ratio (P/E)** — current share price divided by
  earnings per share.
- **Stock return** — a momentum-based measure of price performance.
- **Dividend yield** — annual dividend as a percentage of share price.

For AI competitor corporations in certain states, the earnings figure
used for these calculations is scaled by constants to reflect their
different accounting treatment.

### Buying and selling stock

Players can buy and sell stocks through the Stock Market screen. The
interface shows:

- A list of all corporations with columns for Price, P/E ratio,
  Owned percentage, and Stock Value.
- A list of shareholders for the selected stock with Owned Quantity,
  Owned percentage, and Stock Value.
- Price history charts with Day, Month, and Year tabs.
- Buy and Sell sliders for entering trade quantities.

**Price impact**: large trades move the market price. Buying a large
quantity pushes the price up; selling pushes it down. The magnitude of
the impact is dampened by the total shares outstanding (larger
companies are more liquid). The price floor from impact is ten cents
per share.

The game includes a solver that accounts for price impact when you
enter a dollar amount — it iteratively calculates how many shares you
can actually afford, since each share purchased raises the price of
the next one.

When a large trade is entered, the game shows a dialog: "Your large
quantity stock sale/purchase puts pressure on the stock price,"
displaying the average purchase price and total cost.

**Where the money goes.** The trade price is the average of the old and
new prices. When a person trades, their personal wealth falls by the
cost on a buy and rises by the proceeds on a sell. When a corporation
trades another corporation's stock, money moves between its Cash and
Stock Assets accounts. The corporation whose stock is traded receives
nothing, and the public float moves opposite to the trade. When a
corporation buys back its own stock, cash falls by the cost, equity
falls, and total shares fall: bought-back shares are retired. The exact
amount posted to equity was lost in the decompile.

### Securities regulation (SEC rules)

The game enforces insider trading restrictions. Three situations are
blocked:

1. A player cannot use a corporation they control to buy stock in a
   company where they personally own shares.
2. A player cannot use a controlled corporation to buy stock in a
   company where their main corporation already has ownership.
3. A corporation cannot buy stock in a company where the player
   personally holds shares.

Attempting any of these displays a message from the "Securities and
Exchange Commission."

### Share issuance

Corporations can issue new shares to raise capital. Issuing shares:

- Increases the total shares outstanding.
- Dilutes the share price proportionally (more shares means each is
  worth less).
- Reduces price momentum (dampens recent upward pressure).
- Generates a news announcement: "New Shares at $X Per Share."
- Raises both cash and equity by new shares × issue price. Total shares
  and the public float both rise by the new shares.

### Dividends

At the end of each game year, profitable corporations pay dividends to
their shareholders.

**Player corporations**: The game shows a dialog asking "How much
dividend would your corporation pay this year?" with a slider for the
payout ratio. The player can also set the dividend to automatic mode
("Auto Dividend Payout") so it is calculated without asking each year.

**AI competitor corporations**: Dividends are calculated automatically.
The payout considers:

- The CEO's personality (specifically their leadership trait index),
  which influences generosity.
- The corporation's cash position relative to its debt — companies
  with comfortable cash reserves pay more.
- A random factor that adds variance to the decision.
- A minimum payout threshold below which no dividend is paid.
- A cap to prevent paying more than the stock is worth.
- If zero dividend would result, there is a small personality-dependent
  chance of paying a random amount anyway.

Dividends are distributed proportionally to all shareholders:
corporation holders receive the payment through the financial
accounting system, while person holders receive a direct addition to
their personal wealth.

The game tracks dividend history in two yearly arrays: total dividend
paid and dividend yield.

### Tender offers

When stock is not available on the open market (public float is zero
or very low), players can make "tender offers" — direct proposals to
buy shares from specific holders.

The target holder's willingness to sell depends on a valuation
calculation that considers:

- The relationship between buyer and the target company (CEO, board
  member, or unrelated).
- The corporation's financial health and competitive position.
- A random factor.
- Premium pricing: a CEO selling shares in their own company demands
  a significantly higher price (roughly double the market rate plus a
  personality-based premium). Board members also command a premium.

When a tender offer is made, the game shows a "Tender Offer" dialog
with the proposed price per share, number of shares, and the current
market price. The target can accept or reject.

If an offer is rejected, a cooldown period prevents repeated offers:
- If the target is the player's own CEO: approximately one year plus
  a random period up to six months.
- Otherwise: approximately six months plus a random period up to six
  months.

After a successful tender offer where shares were bought from a
non-public holder, a longer cooldown of roughly two years plus up to
six months applies.

### Corporate mergers and acquisitions

When a corporation (or person) acquires enough stock in another
corporation, a merger can occur. The Stock Market screen shows a
"Merger" button when the conditions are met.

The merger dialog presents three choices:

1. **Paying Cash** — the acquiring entity pays the remaining
   shareholders in cash at the current share price. This option is
   disabled if the acquirer lacks sufficient funds.
2. **Issuing Shares** — the acquiring corporation issues new shares
   of its own stock to exchange for the target's remaining shares,
   at the ratio of the two companies' share prices.
3. **Cancel** — abort the merger.

After a merger, the target corporation's shares are either cashed out
(mode 1) or converted to the acquirer's stock (mode 2). The target
corporation then transfers control to the acquirer.

### AI stock trading

AI competitor corporations participate in the stock market with two
behaviors:

1. **Buyback** — if the public float is too high relative to total
   shares, the AI buys back its own stock to concentrate ownership.
2. **Investment** — the AI evaluates other corporations' stocks based
   on net worth versus debt, buying shares in companies with
   favorable valuations.

### Stock-related news

The news system generates announcements for stock events:

- Dividend payouts: "Pays an Annual Stock Dividend of $X Per Share
  (Y% of the Stock Price)"
- Share issuance: "New Shares at $X Per Share"
- Stock buybacks: "[Corp] Shares of its Own Stock at $X Per Share"
- Tender offer outcomes (accepted or rejected)
- SEC violation notices

### Monthly and yearly history

The stock system maintains rolling history for charting:

- **Daily prices** — last 30 days, used for the "Day" chart tab.
- **Monthly average prices** — last 30 months, for the "Month" tab.
- **Yearly prices** — last 30 years, for the "Year" tab.
- **Yearly earnings** — tracks annual earnings for P/E history.

## Corporation internals

A corporation is the player's (or AI's) central entity. The game
supports up to 12 corporations simultaneously. Each tracks its own
finances, personnel, firms, stock, and brand strategy.

### Corporation types

| Type | Description       | Who controls it                           |
|------|-------------------|-------------------------------------------|
| 1    | Player            | Human-controlled through the UI           |
| 2    | Hired / Retired   | A hired manager runs day-to-day operations|
| 3    | Competitor (AI)   | AI-controlled, has a personality profile   |
| 4    | Government        | System corporation, minimal behavior       |

A type 2 corporation arises when the original CEO retires but the
company continues under hired management. Type 3 competitors each
have a personality index that determines their strategic behavior.

### Roles and leadership

Each corporation tracks three key personnel roles:

- **President** — The operational leader. Draws a salary charged daily
  against the corporation's cash. This is the person who runs the
  business.
- **Chairman** — The representative of the controlling shareholder.
  When a single shareholder (person or corporation) accumulates enough
  stock, they install their own Chairman.
- **CEO** — May or may not be the same person as the President. In the
  UI, a person holding multiple roles shows combined titles like
  "CEO & Chairman" or "President & Chairman".

The **Owner** field tracks whether the corporation is a subsidiary. If
set, it points to the parent corporation. A subsidiary chain can be
followed up to 12 levels deep to detect indirect ownership.

When the controlling shareholder changes (detected by checking who holds
the most stock), the game automatically transfers the CEO and owner
references and records the date of the ownership change. A news event
announces the change.

### Financial system

Each corporation maintains a 7-account balance sheet ledger tracked
across three time periods: current running balance, year-to-date
changes, and previous year's changes.

The accounts break down into three balance sheet groups:

**Assets** (accounts 0–4):

| Account | Label            | Notes                           |
|---------|------------------|---------------------------------|
| 0       | Cash             | Also drives the cash display    |
| 1       | Inventory        | Stock of goods on hand          |
| 2       | Business Assets  | Physical business property      |
| 3       | Land & Resource  | Updated monthly by land values  |
| 4       | Stock Assets     | Equity investments held         |

**Liabilities** (account 5):
- Tracks total outstanding debt, including bank loans.

**Shareholders' Equity** (accounts 6–7):
- Account 6 is stored equity.
- Account 7 is computed rather than stored, derived from asset and
  liability totals.

**Net income** is calculated as the sum of all Asset accounts (0–4)
minus the Liabilities account (5).

### Income statement

The income statement breaks financial activity into three groups with
10 line items total:

**Revenue** (1 item):
- Operating Revenue — all sales and business income

**Operating Expenses** (6 items):
- Cost of Sales — the combined cost of raw materials, purchased goods
  and freight
- Salaries Expense — all employee wages plus president salary
- Operating Overhead — monthly fixed costs per firm (varies by firm
  type)
- Advertising Spending — advertising campaign budgets
- Training and New Equipment — worker training programs
- Write-offs — depreciation, spoilage, and other asset losses

**Other Profit** (3 items):
- Stock Return — gains or losses from stock transactions
- Increase in Land Value — unrealized gains from monthly land
  revaluation
- Loan Interest — daily interest charges on debt (shown as negative)

The key computed lines:
- **Operating Profit** = Operating Revenue − Operating Expenses
- **Net Profit** = Operating Profit + Other Profit

There are no tax mechanics in the game. Net Profit is the final
bottom line.

### Expense tracking

The game tracks all 12 expense categories across four time periods:

- **Current month** — reset at the start of each month
- **Last month** — the previous month's totals (copied from current
  month at rollover)
- **Current year** — accumulates all year, reset at year end
- **Lifetime** — never reset, tracks the corporation's all-time totals

"Cost of Sales" on the income statement is a composite that sums three
underlying categories: Purchase Cost (cost of goods at point of sale),
Freight Cost (transport charges), and Raw Material Reserve
(consumption of stored raw materials).

### Interest rates

The game has a single global interest rate that applies to all
corporations equally. It starts at 10% and changes monthly based on
the economy.

**Monthly rate adjustment:**
- The game computes the average monthly GNP across all towns.
- In a weak economy (average GNP ≤ 5.0), the rate always rises by
  0.5 percentage points.
- In a stronger economy, the rate still rises but only with a 1-in-10
  random chance per month.
- Separately, the rate may fall by 0.5 points with a 1-in-50 chance
  per month, but never below 1.0%.

The rate history for the past 10 years is tracked and displayed in the
Bank Loans panel chart.

### Cash flow and daily finance

Every game day, each corporation processes its financial obligations:

1. **Overdraft interest**: If the corporation's cash is negative, a
   daily interest charge is applied. The charge uses the global
   interest rate plus a 2-percentage-point spread, divided across 365
   days. For example, at a 10% global rate, a corporation $1M in
   overdraft pays roughly $329 per day (12% / 365 × $1M). The charge
   is posted as a Loan Interest expense and added to the liabilities
   balance.

2. **Debt interest**: If the corporation has outstanding liabilities
   (from previous borrowing), interest accrues daily at the global
   rate (no spread), divided across 365 days.

3. **President salary**: If the corporation has a president, their
   annual salary is divided by 365 and paid daily. The salary comes
   from the corporation's cash (posted as a Salaries expense) and goes
   to the president's personal wealth: `salary / 365` per day.

4. **Net income update**: After daily charges, the net income figure
   is recalculated.

The monthly interest shown in the Bank Loans panel equals the annual
liabilities-based interest divided by 12.

### Bank loans

The loan system uses a simple credit-limit model:

- **Credit limit** = Total Assets − Outstanding Debt (minimum zero).
  The corporation cannot borrow beyond its asset backing.
- **Borrowing** increases both cash and debt by the same amount.
- **Repayment** is capped at the lesser of available cash or
  outstanding debt. It reduces both cash and debt equally.

The loan panel shows: Total Loan, Monthly Interest, Credit Limit, and
Interest Rate. Two 10-year history charts display the Interest Rate
(a global rate shared by all corporations) and the corporation's Loan
Amount over time.

Interest is charged daily when cash is negative — there is no grace
period. The rate comes from a global interest rate value.

### Share issuance

A corporation can issue new shares to raise capital:

- The **maximum issuable shares** is calculated from the stock object.
- The **issuing price** can range from a fraction of the current stock
  price up to the full stock price. The exact lower bound is set by a
  global factor.
- The panel shows: current number of shares outstanding, current stock
  price, maximum issuable shares, and the expected gross receipt.
- Pressing "Issue Now" creates the new shares and adds the proceeds
  to the corporation's cash.

Issuing shares dilutes existing shareholders proportionally.

### Dividend policy

Each corporation's dividend policy has two settings:

1. **Payout ratio** (0–100%): What percentage of earnings to
   distribute as dividends.
2. **Payout mode**:
   - **Auto Dividend Payout** — Dividends are paid automatically based
     on the ratio.
   - **Ask Dividend Payout** — The player is prompted each time a
     dividend decision comes up.

The actual dividend mechanics (how much per share, when paid, effect
on stock price) are handled by the stock system.

### Monthly and yearly processing

**Monthly**:
1. Checks for peak revenue — if current revenue exceeds the all-time
   peak, updates the record.
2. Recomputes annual sums for revenue and profit.
3. Rotates data into 12-month history arrays for five categories:
   revenue, operating profit, secondary revenue, expenses, and net
   worth snapshots.
4. Calls the stock system's monthly processing.
5. **Bankruptcy check**: If cash is still negative after monthly
   processing, the bankruptcy handler fires.

**Yearly**:
1. Archives current-year figures into 30-year rolling history arrays
   for revenue, operating profit, secondary revenue, expenses, and
   net worth.
2. Archives into 10-year history arrays for: account balances, stock
   return, salaries, advertising, training, write-offs, loan amount,
   total shares, dividend paid, and dividend yield.
3. Resets current-year counters.
4. Calls the stock system's yearly processing.

### Bankruptcy

Bankruptcy is triggered when a corporation's cash remains negative at
the monthly check. The process differs by corporation type.

**Player bankruptcy** (5 options):
A sound effect plays and the player chooses one of:
1. **Borrow Bank Loan** — Opens the loan dialog to borrow against
   remaining credit.
2. **Issue New Shares** — Opens the share issuance dialog to raise
   capital by diluting equity.
3. **Sell Stocks** — Opens the stock selling UI to liquidate
   investments in other companies.
4. **Close Down Firms** — An interactive mode where the player
   selects firms to close. The mode continues until cash reaches
   zero or above.
5. **Declare Bankruptcy** — After a confirmation dialog ("ARE YOU
   SURE?"), the corporation is dissolved. A bankruptcy sound plays,
   all firms are deleted, remaining cash is distributed, and the
   game ends for that player.

**AI bankruptcy** (4-step escalation):
The AI computes its deficit and attempts to recover through
progressively more drastic measures:
1. Sell stocks held in other companies
2. Sell individual firms
3. Sell more assets (up to 10 repeated rounds)
4. Close remaining firms

If still in deficit after all four steps, the AI declares bankruptcy.

**Dissolution cleanup**:
When a corporation is fully dissolved:
- All persons (CEO, board members) are released and given retirement
  dates.
- Owner and subsidiary links are cleared.
- The corporation is marked for deletion at the end of the tick.

### Corporate mergers

When one corporation acquires another (through the stock/tender offer
system), a full merger executes:

1. **Financial merge** — The target's firm counts, cash, firm arrays,
   and all seven financial accounts (across all three time periods)
   are added to the acquirer's totals.
2. **Asset transfer** — All of the target's firms, jobs, items, town
   demand entries, and stock holdings are reassigned to the acquirer.
3. **Firm integration** — Firm ownership references are updated and
   job slots are merged into the acquirer's pool.
4. **Excess firm sale** (AI only) — After acquisition, AI corporations
   sell approximately one-ninth of excess firms to stay manageable.
5. A news event announces the merger.

### Corporation creation

New corporations are allocated with 2,188 bytes of data. The
allocation process installs a type-specific strategy object based on
the corporation type (player, hired, competitor, or government).

When a new corporation's first firm is placed, the game tries up to
2,000 random positions on the map grid, checking each for valid tile
patterns before settling on a location.

### Brand strategy

Each corporation chooses one of three branding approaches:

- **Corporate Brand** — A single brand name covers all products.
- **Range Brand** — A brand covers a range of related products.
- **Unique Brand** — Each product gets its own brand name.

Changing brand strategy is significant: all existing brand ratings
are reset to zero. The game warns the player with a confirmation
dialog before applying the change.

### Detail panels

The corporation detail screen provides several specialized views:

1. **Shareholders** — Shows who owns this corporation's stock (both
   corporate and individual shareholders with their quantities,
   percentages, and values) and what stocks this corporation owns
   in others (with subsidiary status indicated).

2. **R&D / Technology** — Lists the corporation's products with
   current technology level, top available technology, target
   technology being researched, and R&D progress (shown as a
   progress bar). If the viewer is not the CEO or Chairman, this
   panel shows "Confidential" instead. A toggle switches between
   "Has R&D and Production" and "Has R&D Only" modes.

3. **Advertising** — Shows brand data per product: brand name,
   product, quality level, brand rating, monthly advertising spend,
   daily ad frequency, and rating points. Sortable by product name
   or city name.

4. **Brand / Market** — Shows brand performance metrics: brand
   awareness, brand loyalty, and brand rating. Also contains the
   brand strategy selector (Corporate / Range / Unique).

5. **Market Share** — Shows competitive position: product class,
   product name, leader's market share, this corporation's market
   share, and ranking position among all corporations.

### Summary panel

The corporation summary panel provides a quick overview:

- Corporation name, abbreviation, and color icon
- Portrait of the CEO
- For AI competitors (in design/debug mode): the AI personality name
- **Financial overview tab**: Cash, Annual Revenue, Annual Profit,
  Net Worth — each shown with a value and a horizontal bar chart.
  Also includes a "Past 12 Months" operating profit line chart.
- Additional tabs show other financial and operational details.

### Financial charts

The corporation tracks historical data for charting across three time
scales:

**12-month rolling charts** (Past 12 Months):
- Operating Profit, Net Profit, Revenue, Expenses, Net Worth, Stock
  Price

**30-year rolling charts** (Past 30 Years):
- Operating Profit, Net Profit, Revenue, Expenses, Net Worth, Stock
  Price

**10-year rolling charts** (Past 10 Years):
- Balance sheet: Cash, Inventory, Business Assets, Land & Resource,
  Stock Assets
- Expenses: Salaries, Advertising, Training, Write-offs
- Other: Stock Return, Total Loans, Stock Price, Dividend Paid
- Loan Interest Rate (global, same for all corporations)

At year end, balance sheet account balances and yearly expense totals
are copied into the 10-year history arrays. The 30-year arrays
aggregate all 12 monthly values into a single annual figure.

---

## Product catalog and demand

The game models a complete economy of products, from raw materials to
consumer goods. Every product belongs to a product class, has intrinsic
properties loaded from the scenario data files, and enters the economy
through item links that connect producers to retailers in specific towns.

### Product classes

Products are organized into 20 classes. Each class has:

- A **name** (up to 30 characters)
- A **group index** (1–12), used for UI grouping and filtering
- A **durable flag** — true for long-lasting goods (cars, furniture,
  electronics), false for consumables (food, raw materials)
- A **quality decay base** — a float that controls how quickly products
  in this class lose their appeal after technology matures. When zero,
  quality does not decay (effectively 100% retention).
- A **demand grouping flag** — controls whether the class is treated as
  a single unit for demand calculations or if individual products are
  tracked separately
- A **group class flag** — when true, the class contains sub-products
  that are checked as a group for availability

Each class keeps a chain of all products that belong to it.

The 20 product classes in the standard game set:

| Class                    | Code     | Durable | Group | Products |
|--------------------------|----------|---------|-------|----------|
| Raw Material             | RAW      | No      |  8    |  8       |
| Plant                    | PLANT    | No      |  2    |  2       |
| Plant Products           | PSEMI    | No      |  8    |  8       |
| Livestock                | LSTOCK   | No      |  4    |  4       |
| Livestock Semi-products  | LSEMI    | No      |  3    |  3       |
| Semi-products            | SEMI     | Yes     | 12    | 12       |
| Food                     | FOOD     | No      |  4    |  4       |
| Beverage                 | BEVERAGE | No      |  4    |  4       |
| Livestock Products       | LPRODUCT | No      |  5    |  5       |
| Chemical Products        | CHEMGOOD | No      |  4    |  4       |
| Cosmetics                | COSMETIC | No      |  2    |  2       |
| Cigarette                | CIGAR    | No      |  1    |  1       |
| Apparel, Footwear & Bag  | WEAR     | Yes     |  7    |  7       |
| Furniture                | FURN     | Yes     |  2    |  2       |
| Jewelry                  | JEWELRY  | Yes     |  1    |  1       |
| Watch                    | WATCH    | Yes     |  1    |  1       |
| Toy                      | TOY      | Yes     |  2    |  2       |
| Electronic Products      | ELEAPP   | Yes     |  7    |  7       |
| Computer                 | COMPUTER | Yes     |  5    |  5       |
| Automobile               | AUTO     | Yes     |  2    |  2       |
| **Total**                |          |         |       | **84**   |

### Individual products

Each product has these properties loaded from the scenario data:

- **Name** (up to 21 characters) and **code** (8-character abbreviation)
- **Unit name** (up to 6 characters, e.g. "unit", "kg", "box")
- **Sub-category** (8-character label for further grouping)
- **Class membership** — which product class it belongs to
- **Base cost** and **base price** — the price is computed as a constant
  divided by the cost, so cheaper products have higher prices relative
  to their cost (the constant represents a market-clearing price point)
- **Demand value** — the base consumer demand for this product (per 1000
  population). Products with zero demand are intermediate goods (raw
  materials, components) that have no direct consumer market but are
  consumed by production chains. The **has demand** flag is true when
  this value is positive.
- **Luxury index** — a single-digit value (0–9) measuring how luxurious
  the product is. Jewelry = 9, VR Computer = 9, Bread = 1, Cola = 1.
- **Necessity index** — a single-digit value (0–9) measuring how essential
  the product is. Detergent = 9, Toothpaste = 9, Bread = 7, Jewelry = 1.
  These two indices are independent: a product can be both luxurious and
  necessary (e.g. Car: luxury 8, necessity 2), or neither.
- **Technology importance** — how much technological advancement affects
  product quality. Cars have the highest value (15), electronics are
  high (10–12), food is low (3). Products with higher tech importance
  benefit more from R&D investment.

#### Demand weight triplet

Every product has three percentages that must sum to 100:

- **Quality weight** — how much product quality matters to consumers
- **Price weight** — how much price matters to consumers
- **Brand weight** — how much brand reputation matters to consumers

A product with high quality weight (say 60/20/20) will see market share
shift strongly toward the highest-quality producer. A product with high
price weight will be more price-sensitive. These weights flow into every
demand calculation: competition, growth, and decline.

#### Consumer flag

Products with category codes 2 through 6 are flagged as consumer
products. These are the products that appear on store shelves and
generate direct consumer demand. Other categories represent intermediate
goods, raw materials, or services.

#### Technology

Products can require technology to be produced:

- **Technology level** — a value loaded from the scenario data (with
  random jitter of ±4). Products with a zero technology level are always
  available.
- **Discovery mask** — tracks which corporations have discovered this
  product. Initially empty.
- **Year available** — set to the current game year when the product is
  first discovered by any corporation.
- **Technology diffusion** — technology spreads over time. The diffusion
  rule is: if `(number of corps knowing × 8) + (years since game start)
  exceeds 50`, the product becomes universally known to all corporations.
  This means that even without direct research, technologies eventually
  become common knowledge.
- **Quality decay** — after a product's technology matures (discovery
  date is recorded), the quality multiplier from the product class
  decays over time: `base − days_since_discovery / constant`. This
  represents technology becoming commoditized and less of a competitive
  advantage.
- **Technology upgrade** — when a corporation upgrades its technology
  level for a product, the town demand records are adjusted using a
  blend between old and new ratios, weighted by a brand factor. This
  prevents sudden market disruptions from technology jumps.

#### Initial score

When products are loaded, each receives an initial score that is the
base value plus or minus a random value in the range of 0 to 8, minus 4
(so effectively ±4 jitter). This gives each game session slight
variation in starting product attractiveness.

### Complete product catalog (standard game set)

The standard scenario ships 84 products organized into a supply chain
from raw materials through manufacturing to retail consumer goods.

#### Raw materials (8 products)

Extracted from the ground by mines, oil wells, and logging camps. No
consumer demand — these are purely industrial inputs.

| Product            | Price   | Unit   |
|--------------------|---------|--------|
| Aluminum           | $1.30   | lb     |
| Chemical Minerals  | $2.00   | lb     |
| Coal               | $0.20   | lb     |
| Gold               | $300    | oz     |
| Iron Ore           | $0.30   | lb     |
| Oil                | $20     | barrel |
| Silica             | $0.20   | lb     |
| Timber             | $0.20   | lb     |

#### Agricultural products (14 products)

Grown on farms. Most are industrial inputs, but Grapes have direct
consumer demand.

**Plants** (2): Rubber Plant ($0.30/lb), Sugar Cane ($0.30/lb)

**Crops** (8): Barley, Cocoa, Cotton, Grapes, Rubber, Sugar, Tobacco,
Wheat. Grapes are unusual — they are the only crop with direct consumer
demand (demand 7.0, P45/Q45/B10), meaning they can be sold directly
to consumers without processing.

**Livestock** (4): Cattle ($500), Chicken ($5), Pig ($150), Sheep ($150).
Raised on farms, then processed into consumer-grade meat products.

#### Livestock semi-products (3 products)

Intermediate goods from livestock processing: Leather ($10/lb), Milk
($1/quart), Wool ($20/lb). Milk is processed into Bottled Milk for
consumer sale; Leather feeds the apparel chain (shoes, jackets, bags);
Wool feeds textile manufacturing.

#### Semi-products (12 products)

Manufactured intermediate goods. Some are simple (Glass, Paper, Plastic,
Steel — all $1/lb), some are complex high-value components:

| Product                | Price   | Notes                          |
|------------------------|---------|--------------------------------|
| Car Body               | $5,000  | Auto assembly component        |
| CPU                    | $200    | Computer component             |
| Electronic Components  | $10/lb  | Used in all electronics        |
| Engine                 | $3,000  | Auto assembly component        |
| Flour                  | $0.50/lb| Food manufacturing input       |
| Glass                  | $1/lb   | General manufacturing          |
| Paper                  | $1/lb   | General manufacturing          |
| Plastic                | $1/lb   | General manufacturing          |
| Silicon                | $1/lb   | Electronics manufacturing      |
| Steel                  | $1/lb   | Auto, appliance manufacturing  |
| Textiles               | $10/lb  | Apparel manufacturing          |
| Wheel & Tire           | $1,000  | Auto assembly component        |

#### Consumer products (47 products)

These are the products with direct consumer demand. Each has a demand
value (units per 1000 population), luxury and necessity indices (L/N,
each 0–9), and consumer decision weights (Price/Quality/Brand percentages
summing to 100).

**Food** (4 products)

| Product        | Price  | Demand | L/N | P/Q/B%     |
|----------------|--------|--------|-----|------------|
| Bread          | $1.50  | 10.0   | 1/7 | 35/35/30   |
| Chocolate Bar  | $1.50  |  8.0   | 1/6 | 35/35/30   |
| Cookies        | $4.00  |  3.0   | 1/5 | 35/35/30   |
| Ice Cream      | $1.50  | 10.0   | 1/5 | 35/35/30   |

Food products are high-necessity, low-luxury, with balanced consumer
weights. Brand matters slightly less than price or quality.

**Beverages** (4 products)

| Product        | Price  | Demand | L/N | P/Q/B%     |
|----------------|--------|--------|-----|------------|
| Beer           | $2.00  | 10.0   | 1/5 | 30/30/40   |
| Bottled Milk   | $2.00  | 10.0   | 1/5 | 35/35/30   |
| Cola           | $1.00  | 30.0   | 1/5 | 30/20/50   |
| Wine           | $20.00 |  1.0   | 1/3 | 20/30/50   |

Cola has the highest demand of any product in the game (30.0) and is
strongly brand-driven (50%). Wine is also brand-driven but at much
lower volume and higher price.

**Livestock products** (5 products)

| Product        | Price  | Demand | L/N | P/Q/B%     |
|----------------|--------|--------|-----|------------|
| Eggs           | $2.00  |  3.5   | 1/6 | 45/45/10   |
| Frozen Beef    | $3.00  |  5.0   | 1/6 | 45/45/10   |
| Frozen Chicken | $3.00  |  5.0   | 1/6 | 45/45/10   |
| Frozen Pork    | $3.00  |  3.5   | 1/6 | 45/45/10   |
| Frozen Lamb    | $3.00  |  1.0   | 1/6 | 45/45/10   |

Meat products are highly price/quality sensitive (45/45) with almost no
brand loyalty (10%). Consumers buy the cheapest quality meat available.

**Chemical products** (4 products)

| Product        | Price  | Demand | L/N | P/Q/B%     |
|----------------|--------|--------|-----|------------|
| Detergent      | $4.00  |  3.0   | 1/9 | 40/30/30   |
| Diaper         | $6.00  |  2.0   | 2/8 | 33/33/34   |
| Shampoo        | $4.00  |  6.0   | 1/8 | 30/30/40   |
| Toothpaste     | $3.00  |  6.0   | 1/9 | 25/25/50   |

These are the highest-necessity consumer products in the game (N8–9).
Toothpaste is 50% brand-driven — real-world brand loyalty is reflected.

**Cosmetics** (2 products)

| Product        | Price   | Demand | L/N | P/Q/B%     |
|----------------|---------|--------|-----|------------|
| Eye Shadow     | $30.00  |  0.5   | 7/1 | 20/30/50   |
| Perfume        | $30.00  |  0.5   | 7/1 | 20/30/50   |

High luxury, low necessity, heavily brand-driven. Low demand volume
but high margins.

**Cigarettes** (1 product)

| Product        | Price  | Demand | L/N | P/Q/B%     |
|----------------|--------|--------|-----|------------|
| Cigarettes     | $3.00  |  7.0   | 5/5 | 25/15/60   |

The most brand-driven product in the game (60%). Quality barely matters
(15%) — consumers buy their favorite brand regardless.

**Apparel, footwear & bags** (7 products)

| Product           | Price   | Demand | L/N | P/Q/B%     |
|-------------------|---------|--------|-----|------------|
| Leather Briefcase | $200    | 0.04   | 7/4 | 30/35/35   |
| Leather Jacket    | $250    | 0.03   | 7/3 | 30/35/35   |
| Jeans             | $30     | 0.50   | 2/4 | 25/25/50   |
| Leather Shoes     | $50     | 0.25   | 2/4 | 30/30/40   |
| Socks             | $5      | 2.00   | 3/4 | 35/35/30   |
| Sweater           | $80     | 0.15   | 3/4 | 30/35/35   |
| Sport Shoes       | $50     | 0.30   | 3/4 | 25/25/50   |

Socks have the highest demand in this class. Leather goods are luxury
items with very low demand. Jeans and sport shoes are 50% brand-driven.

**Furniture** (2 products)

| Product | Price  | Demand | L/N | P/Q/B%     |
|---------|--------|--------|-----|------------|
| Bed     | $350   | 0.05   | 3/5 | 35/40/25   |
| Sofa    | $250   | 0.02   | 5/5 | 35/40/25   |

Quality-weighted — consumers prefer well-made furniture over cheap.

**Jewelry** (1 product)

| Product | Price  | Demand | L/N | P/Q/B%     |
|---------|--------|--------|-----|------------|
| Jewelry | $600   | 0.05   | 9/1 | 45/45/10   |

The most luxurious product (L9) and least necessary (N1). Brand is
nearly irrelevant — price and quality dominate equally.

**Watch** (1 product)

| Product | Price  | Demand | L/N | P/Q/B%     |
|---------|--------|--------|-----|------------|
| Watch   | $60    | 0.30   | 4/4 | 30/35/35   |

**Toys** (2 products)

| Product    | Price  | Demand | L/N | P/Q/B%     |
|------------|--------|--------|-----|------------|
| Toy Train  | $20    | 0.50   | 5/2 | 35/40/25   |
| Toy Bear   | $20    | 0.50   | 5/2 | 35/40/25   |

**Electronic products** (7 products)

| Product        | Price  | Demand | L/N | P/Q/B%  | Available | Requires     |
|----------------|--------|--------|-----|---------|-----------|--------------|
| Air Conditioner| $400   | 0.05   | 6/3 | 30/40/30|  Always   |              |
| Camera         | $150   | 0.10   | 5/3 | 30/40/30|  Always   |              |
| DVD Player     | $500   | 0.05   | 5/3 | 30/40/30|  1994     | Computer     |
| Hi-fi          | $400   | 0.05   | 6/3 | 30/40/30|  Always   |              |
| Television     | $400   | 0.05   | 4/3 | 30/40/30|  Always   |              |
| Video Camera   | $800   | 0.025  | 8/1 | 30/40/30|  Always   | Camera + TV  |
| Video Recorder | $400   | 0.05   | 6/3 | 30/40/30|  Always   | TV           |

All electronics share identical consumer weights (P30/Q40/B30) — quality
matters most. Video Camera is the most luxurious electronic product.
DVD Player is the only one requiring an invention year.

**Computers** (5 products)

| Product          | Price   | Demand | L/N | P/Q/B%  | Available | Requires   |
|------------------|---------|--------|-----|---------|-----------|------------|
| Desktop Computer | $1,500  | 0.05   | 7/2 | 35/35/30|  Always   | TV         |
| Internet-TV      | $600    | 0.06   | 5/4 | 35/35/30|  1995     | Computer   |
| PDA              | $320    | 0.05   | 7/1 | 30/40/30|  1992     | Computer   |
| VR Computer      | $1,800  | 0.025  | 9/1 | 25/45/30|  1997     | Computer   |
| Wrist Computer   | $900    | 0.03   | 9/1 | 25/45/30|  1996     | Computer   |

The most technology-driven class. Desktop Computer requires TV as a
component (the monitor). Four products unlock during gameplay through
R&D. VR Computer and Wrist Computer are the most quality-sensitive
products in the game (Q45) and among the most luxurious (L9).

Desktop Computer, along with cars and motorcycles, can be imported
through a seaport rather than manufactured locally.

**Automobiles** (2 products)

| Product    | Price    | Demand | L/N | P/Q/B%  |
|------------|----------|--------|-----|---------|
| Car        | $20,000  | 0.005  | 8/2 | 30/35/35|
| Motorcycle | $10,000  | 0.002  | 7/2 | 30/35/35|

The most expensive consumer products. Very low demand per capita but
high revenue per unit. Both can be imported via seaport. Cars have the
highest technology importance value of any product, meaning R&D
investment yields the greatest quality improvement for automobiles.

#### Consumer decision weight patterns

Across all products, three distinct consumer behavior patterns emerge:

- **Brand-dominant** (brand weight ≥ 50%): Cola, Wine, Toothpaste,
  Cigarettes, Jeans, Sport Shoes, Eye Shadow, Perfume. These products
  reward heavy advertising investment and brand-building strategies.

- **Quality-dominant** (quality weight ≥ 40%): All electronics, all
  computers, furniture, toys, jewelry, livestock products. These reward
  R&D investment and high-quality manufacturing.

- **Balanced** (no single weight above 40%): Cars, most food, most
  apparel, watches. Success requires a balanced strategy across all
  three dimensions.

#### Supply chain relationships

Some products require other products as manufacturing inputs (parent
products). The key chains are:

- **Automobile chain**: Raw materials → Steel, Car Body, Engine, Wheel
  & Tire → Car/Motorcycle
- **Computer chain**: Silicon → CPU + Electronic Components → Desktop
  Computer → PDA, Internet-TV, Wrist Computer, VR Computer
- **Electronics chain**: Electronic Components → Television → Video
  Recorder, Video Camera; Camera + TV → Video Camera
- **Food chain**: Wheat → Flour → Bread, Cookies; Cocoa → Chocolate;
  Milk → Bottled Milk; Barley → Beer; Grapes → Wine
- **Apparel chain**: Cotton → Textiles → Clothing; Leather → Shoes,
  Jackets, Bags; Wool → Textiles


### Item links — product instances in the economy

An item link represents a specific product being sold by a specific
retailer in a specific town. It is the fundamental unit of the product
economy. Each link tracks:

- Which **product type** it represents
- The **producer** and **retailer** firms involved
- The **town** where it is sold
- The **corporation** that owns it (used for market share grouping)
- Current **quality** and **score** ratings
- The current **price** set by the retailer
- The **quantity** — a float representing current consumer demand volume
- Two **cost components** that together form the per-unit production cost
- **Stock units** — integer count of physical inventory
- **Previous quantity** — smoothed demand tracking for trend detection
- Monthly tracking arrays (12 slots, one per calendar month):
  - **Revenue** — price × units sold
  - **Units sold** — count of units moved
  - **Margin** — revenue minus total cost (both cost components × units)

#### Circular linked lists

Products maintain two circular linked lists of their item links:

- **Global list** — all links for this product across all towns
- **Town list** — all links for this product within a specific town

These lists enable efficient iteration when computing market share,
updating town totals, or processing competition between retailers
selling the same product.

### The demand model

Demand processing is the heart of the product economy. It runs daily
but does not process every link each day — instead, **15 item links are
processed per game day**, cycling through all links over time. This
staggered approach prevents performance spikes and creates natural
market momentum.

#### Daily processing per link

For each link visited on a given day:

1. **Score adjustment**: the product's score is recalculated:
   `score = base_score + (brand_rating × brand_weight / 60) +
   (score_in × score_in_weight / 60)`, using the town-product weights.
   If the new score is lower than the old score, the quantity loses
   `(old_score − new_score) × quantity / 100`, floored at zero. This is
   1% per point lost, not new_score / old_score. Score increases don't
   immediately boost quantity (that happens through the growth mechanism
   below).

2. **Demand movement** — only for products with consumer demand, and
   only for retail firms. The system determines whether demand should
   grow, shrink, or shift between competitors:

   a. **Oversupply decay** — if the town's total supply for this product
      exceeds demand and this link has positive quantity, a fraction is
      removed (quantity divided by a constant). This prevents unlimited
      accumulation.

   b. **Decay factor**: a per-link factor is computed from the firm's
      properties: the firm's adjustment rate × 5, plus 50 unless the
      firm stands on the farmland (rural) tile range, capped at 100. It
      depends on the tile the firm stands on, not on the firm type.

   c. **Demand reduction**: if the link's quantity is positive, it may
      be reduced based on how the link's score, price, score-in and
      brand compare to the town's reference levels (not an average of
      sellers). Links that are worse than the reference lose quantity
      (see Market competition for the formula).

   d. **Supply-demand check** — the system projects whether supply will
      meet demand by the end of the month. If the projected quantity-sum
      is below 2 × the projected flow, two growth mechanisms activate:

      - **Demand growth**: the link gains quantity from free town
        demand f = demand − supply:
        `(100 − decay) × f × gap² × (f / demand)² / 100`, where gap sums
        the factors in which the link beats the town reference levels.

      - **Competition**: the link takes quantity from each weaker
        competitor in the same town:
        `(100 − decay) × (competitor_qty × gap² × (competitor_qty / demand)² × 120 / 100) / 100`,
        where gap sums the score, price (weighted by the price weight),
        score-in and brand advantages over that competitor. The
        quadratic terms mean that even small advantages compound into
        significant market share shifts over time.

3. **Supply tracking** — after demand movement, the link's supply data
   is updated. If quantity is at least 1 (or was at least 1 previously),
   the previous quantity tracker is set to current; otherwise the values
   accumulate (smoothing for very low-demand products). The quantity is
   added to the monthly supply bucket and to the product type's demand
   accumulator. Every other day, town-wide totals are recalculated by
   summing all links in that town.

#### Monthly processing

At the start of each month:
- The current month's revenue, units, and margin buckets are zeroed
  for each link
- Running totals are shifted to make room for the new month
- Market share percentages are recomputed by summing quantities across
  all links for each product, grouped by corporation. Each corporation's
  sum (this month plus the unexpired part of last month, prorated over
  31 days) is divided by the product's market total, which includes
  unmet demand. The result is rounded and capped at 100. This table is
  used for display and goals; it doesn't drive the split between
  sellers

### Sales

When a retail firm sells units of a product:

- Physical stock is decremented
- Revenue (price × units) is added to the monthly revenue bucket
- Units are added to the monthly units bucket
- Margin (revenue minus total production cost × units) is added to the
  monthly margin bucket
- For consumer products:
  - The town-product record's revenue and quantity counters are updated
  - **Brand perception adjustment**: the system computes an expected
    level from the link's score-in and score, compared with the
    product's top values, and turns it into a target between −A and
    +A, where A is the corporation's brand awareness in that town. The
    brand value then steps toward the target by 0.1 (or 0.1 / a
    per-town count for corporate and range brands) × units sold /
    max(units sold, town demand), clamped to ±A. See Brand perception
    for the formula.
- Product-level monthly revenue and demand quantity accumulators are
  updated

### Brand strategy interaction

The product system interacts with the corporation brand strategy:

- **Corporate brand** — all products share a single brand identity.
  Brand perception changes for any one product affect the perception
  of all products from that corporation.
- **Range brand** — products within the same class share a brand.
  A strong brand in one product lifts the perception of other products
  in the same class from the same corporation.
- **Unique brand** — each product has its own independent brand. Brand
  perception changes are isolated to the individual product.

The brand-aware lookup maps each product to the appropriate brand scope
depending on the corporation's chosen strategy.

### Product score evaluation

A product's overall score (used for AI decision-making and UI display)
follows these rules:

- **400** — returned when the product has no item links with demand yet
  (not on the market). This high default encourages AI to enter new
  markets.
- **Computed score** — when supply and demand both exist, a dynamic
  score is calculated from market conditions.
- **0** — when there is supply but no demand activity at all, the
  product is rated as unattractive.

### Product availability

A product is considered "available" through a recursive check:

- If the product class tracks individual products: the product must
  have item links and positive demand totals.
- If the product class groups products: at least one product in the
  class must have supply.
- If the product has prerequisites (input materials or components):
  all prerequisites must themselves be available, checked recursively.

This means a manufactured product is not available until its entire
supply chain is active.

### Product detail panel

The product detail screen shows comprehensive data for a single product,
filterable by town:

- **Header** — product name, bitmap icon, product class name, and the
  necessity index (displayed as the raw value × 10)
- **Revenue or Quantity Sold graph** — toggleable, showing the city
  total and optionally one selected link's contribution
- **Market share** — two pie charts: one for production market share
  and one for retail market share
- **Price and demand chart** — only for consumer products; shows price
  and demand relationships by firm
- **Link list** — a scrollable table with columns: Producer, Retailer,
  Price, Quality, Brand, Overall
- **Town averages** — displayed when a town is selected: average
  quality, average price, and average brand rating for this product in
  the selected town
- **Competitor comparison** — detailed breakdown for the selected link
- **Demand breakdown** — analysis of supply vs demand for the link
- **Market position** — ranking chart

Navigation arrows skip to the next product that has known technology,
has consumer demand, and has active item links.

### Product summary panel

The summary panel lists all products with filtering:

- **Firm filter** — show all cities or one specific town
- **Product class filter** — narrow to a specific class
- **Category filter** — narrow to a specific category

Each row shows the product name, "(Tech. unknown to you)" if the
player has not discovered it, the class name, a bitmap icon, and
mini charts showing revenue/demand and market share.

The list supports searching for products owned by a specific
corporation or present in a specific town, with buttons for "Close"
and "Product Detail" to drill into a specific product.

### Placement chart

The placement view shows a pie chart of revenue distribution per
corporation for a product. Revenue is aggregated across all item links
(either globally or for a specific town) and displayed as market share
percentages. Corporations below a visibility threshold are omitted from
the chart.

## News and random events

### News system

The game tracks noteworthy events through a news system. Every
significant event — firm openings, financial transactions, personnel
changes, random disasters — generates a news item that the player can
browse in the News Report panel.

Each news item records:
- The date it occurred
- The corporations and nations involved
- The event type and category
- Type-specific details (amounts, names, locations)

News items are stored in a circular buffer holding up to 2000 items.
When full, the oldest item is silently dropped.

### News categories

Every news item belongs to one of four filter categories:

| Category | Content |
|----------|---------|
| Normal News | Firm openings and closures |
| Financial News | Loans, share trades, dividends, tender offers |
| Technology News | R&D inventions, products made public, R&D breakthroughs |
| Special News | New competitors, bankruptcies, resource events, control changes, mergers, CEO changes, city founding, price wars, industry dominance, random events |

### Complete news event types

The game generates 28 distinct types of news:

**Business operations (Normal News):**
1. **Firm opened** — "[Corp] Opens [Firm Type] near/in [City]." Records
   the firm type (Department Store, Factory, R&D Center, Farm, Logging
   Camp, Mine, Oil Well) and the nearest city.
2. **Firm closed** — "[Corp] Closes Down its [Firm Type] near/in [City]
   after N Years of Operation." Records years active. Not posted for
   government-owned firms.

**Financial events (Financial News):**
3. **Bank loan** — "[Corp] Borrows [Amount] Bank Loan."
4. **Loan repaid** — "[Corp] Repays All of its Outstanding Bank Loans."
5. **Shares issued** — "[Corp] Issues [N] New Shares at [Price] Per Share."
6. **Share trade** — "[Corp/Person] Sells/Buys/Buys Back [N] Shares of
   [Corp] at [Price] Per Share." Distinguishes buybacks (buying own stock)
   from market purchases.
7. **Annual dividend** — "[Corp] Pays an Annual Stock Dividend of [Amount]
   Per Share." If the dividend yield is positive, also shows the yield
   as a percentage of stock price.
8. **Tender offer** — "[Person/Corp] Buys [N] Shares of [Corp] from
   [Person/Corp] at [Price] Per Share." Records both buyer and seller.

**Corporate events (Special News):**
9. **New competitor** — "[Corp] Joins the Competition." Posted when a new
   AI corporation enters the game. Not posted for government corps.
10. **Bankruptcy** — "[Corp] Goes Bankrupt after N Years of Operation."
    If shareholders receive a payout, shows the per-share amount.
11. **Control change** — "[Corp/Person] Takes Control of / Loses Control
    of [Corp]." Posted when majority ownership shifts.
12. **Merger** — "[Corp] Merges with [Corp]."
13. **Price war** — "[Corp] Declares a Price War with All of its
    Competitors!"
14. **Industry dominance** — "[Corp] Dominates All Industries!"

**Personnel events (Special News):**
15. **CEO retirement** — "[Person] Retires after N Years of Service as
    the CEO of [Corp]."
16. **CEO succession** — "[Person] Succeeds [Person] as the CEO of [Corp]."

**Technology events (Technology News):**
17. **R&D invention** — "[Corp]'s R&D Center Announce Invention.
    [Product] Unveiled at Press Conference." Posted when a corporation's
    R&D center completes development of a new product.
18. **Product made public** — "[Product] Made Public." Posted when a
    privately held technology becomes publicly available (tech diffusion).

**World events (Special News):**
19. **Resource exhausted** — "[Resource] Reserve near [City] Exhausted.
    Production at the [Firm Type] Owned by [Corp] Ceases." Natural
    resource deposits (minerals, oil, timber) eventually run out.
20. **Resource discovered** — "[Resource] Deposit Discovered near [City]."
    New resource deposits appear over time.
21. **Resource on construction site** — "[Resource] Deposit Discovered
    Accidentally on the Construction Site of [Corp]'s New [Firm Type]."
    A lucky find during building.
22. **City founded** — "[City] Founded." New cities appear after the
    initial map generation (700-day cooldown, then 1-in-10 chance each
    month).

### Random events

The game includes six random events that fire during the daily batch.
They can be toggled on/off and their frequency adjusted in the new-game
settings.

**Frequency settings:**

| Setting | Average events per year |
|---------|------------------------|
| Low | ~1.8 (1-in-200 chance each day) |
| Medium | ~3.6 (1-in-100 chance each day) |
| High | ~7.3 (1-in-50 chance each day) |

When the frequency check passes, one of the six events is chosen at
random with equal probability. Some events have an additional internal
probability gate, making them rarer than others.

**Event 1 — Livestock disease:**
Targets a random corporation's farms. Finds all Farm firms with
Livestock Raising jobs matching a randomly chosen product class.
Reduces the livestock capacity by dividing it by 2 to 5 (random).
This slashes ongoing livestock production until the animals recover.
News: "[Product] Population in [City] Area... [N Product] Are Destroyed."

**Event 2 — Building destruction:**
Has a 50% chance of actually triggering (effective frequency is half
the setting). Picks a random firm anywhere on the map and deletes it
entirely — the building, all jobs, and all inventory are lost.
News: "[Corp]'s [Firm Type] near/in [City] Destroyed."

**Event 3 — Crop failure:**
Targets a random corporation's farms. Finds all Farm firms with Crop
Growing jobs. Zeroes both the growth and yield capacities, wiping out
the current growing season entirely. Crops must regrow from scratch.
News: "[City] Area. Fields are Completely Stripped of Vegetation."

**Event 4 — R&D breakthrough:**
A beneficial event. Picks a random R&D Center that is actively
researching a product (stage 1 with an active product). Adds 20 to 60
progress points to the research, potentially completing it early.
News (if product stays in R&D): "[Corp]'s R&D Center Make a
Breakthrough in [Product]'s Production Technology."
News (if breakthrough completes the research): "[Corp]'s R&D Center
Make a Breakthrough. [Product] Unveiled at Press Conference."

**Event 5 — Inventory loss (Blackout):**
Has a 50% chance of actually triggering. Targets a random
corporation's Department Stores. Each store job loses up to 29 units of
inventory at random. The loss is posted as an expense.
News: "[City] Blacked Out for [N] Hours! Looters Steal [Amount] Worth
of Goods from City's Department Stores."

**Event 6 — Economic downturn:**
Has only a 1-in-5 chance of actually triggering (combined with the
frequency gate, this is the rarest event). Reduces corporate asset
values by roughly 4 to 25 percent, causing paper losses across the
affected portfolios.
News: "[Value]! Panic Selling Ensues!"

**Effective frequency comparison** (events per year at Medium setting):

| Event | Internal gate | Effective per year |
|-------|---------------|--------------------|
| Livestock disease | Always | ~0.6 |
| Building destruction | 50% | ~0.3 |
| Crop failure | Always | ~0.6 |
| R&D breakthrough | Always | ~0.6 |
| Inventory loss | 50% | ~0.3 |
| Economic downturn | 20% | ~0.12 |

### News Report panel

The News Report is a panel with three filter columns:
- **Corporation**: filter news by a specific corporation, or show all
- **Category**: Normal News, Financial News, Technology News, Special
  News, or All
- **Time period**: filter by recency

Each news item also has an importance flag. Routine events (firm
openings/closings, new competitors, bankruptcies, bank loans, loan
repayments, share issuances) are flagged as unimportant. All other
events (resource changes, share trades, control shifts, mergers,
dividends, personnel changes, technology events, random events) are
flagged as important.


## Resolved open questions

All items that were previously listed as open questions have been
resolved. Key resolutions:

- **Float values lost in disassembly**: All five resolved by context
  (town labor cost index, sales stock count, base product quality
  score, livestock stock integer, R&D duration sentinel for
  already-complete tech).

- **Livestock scalars**: 36,500.0 (100 years in days — converts per-100-
  year yield to daily rate) and 100.0 (percentage divisor).

- **Corporation type Hired (CEO retired)**: No special Purchasing/Sales
  behavior (the job check slot is a no-op). Daily AI is passive stock
  reinvestment only — invests surplus cash above twice last month's
  revenue into stocks. No building, expansion, or strategic planning.

- **Empty AI daily methods**: Software Developer, Software Publisher,
  and Restaurant firm types have empty firm-level AI. Their jobs run
  via common processing.

- **Missing source-file strings**: Decompiler artifact for 5 job types.
  All have work functions found via dispatch table analysis.

- **Unread function bodies**: All 8 classified — 2 dispatch trampolines,
  3 simple state handlers, 1 manufacturing quality computation, 1
  livestock processing switch, 1 livestock farm daily (512-byte
  function with product matching and stock transfer).

- **AI strategy functions**: All decoded in earlier sessions (B5/B6).
  Portfolio P&L function computes unrealized gain on 5 stock positions.

- **Personality traits**: 5 of 13 are active (character type, salary
  trait, trait 7, expansion trait, acceptance trait). The remaining 8
  plus both strategy weights are vestigial.

- **Person record fields**: All 7 unknowns resolved — portrait resource
  ID, start date, spawn cooldown, and 4 unused padding fields.


## Goals, victory conditions, and scoring

### Overview

The game supports two modes: **free play** (no goals) and **goal-driven
play**. When goals are active, the player must achieve every specified
target within an optional time limit. Goals are configured at game start
or predefined by a scenario.

### Goal types

There are three categories of goals, totaling up to 17 numeric targets
plus sector and industry dominance goals.

**Financial targets (goals on the player and their corporations):**

| Goal | Unit | Scope |
|------|------|-------|
| Personal Wealth | $ | Player's total wealth |
| Corporation Net Worth | $ million | Player's own corporation |
| Corporation Market Value | $ million | Player's own corporation |
| Corporation Annual Revenue | $ million | Player's own corporation |
| Corporation Annual Operating Profit | $ million | Player's own corporation |
| Controlled Corporations Net Worth | $ million | All corporations the player controls |
| Controlled Corporations Market Value | $ million | All controlled corporations |
| Controlled Corporations Annual Revenue | $ million | All controlled corporations |
| Controlled Corporations Annual Op Profit | $ million | All controlled corporations |

**Operational targets:**

| Goal | Unit |
|------|------|
| No. of Companies Controlled | count |
| Total No. of Employees in Your Corporation | count |
| Operating Profit Margin of Your Corporation | % |
| Return on Equity of Your Corporation | % |
| Stock Price of Your Corporation | $ |
| Your Ownership of Your Corporation | % |
| No. of Product Classes Being Produced | count |
| No. of Product Types Being Produced | count |

**Dominance goals:**

- **Sector dominance** (4 sectors): The player must lead a sector by
  having the highest combined monthly revenue among all firms of that
  sector's business category.

- **Industry dominance** (one per product class): The player must have
  the highest market share in **every** product type within a product
  class — not just the class overall.

For numeric targets, a goal is achieved when the player's current value
meets or exceeds the target. A target of zero means that goal is
inactive. Dominance goals are individually toggled on or off during
game setup.

### Sector dominance

The economy is divided into four sectors, each grouping firms by
business type. The game sums monthly revenue across all firms in a
sector for each of the 12 possible corporations, then converts to
market-share percentages (capped at 100%). The corporation with the
highest share leads the sector.

To achieve a sector dominance goal, the player must be the sector
leader. If the sector goal flag was not enabled at game setup, the
goal counts as automatically achieved.

### Industry dominance

An industry goal covers an entire product class. The player must
dominate **every product type** within that class — one product led
by a competitor causes the goal to fail.

For each product type, the game compares market-share values across all
12 corporation slots. The corporation with the highest share leads that
product. Only when the player leads all products in the class does the
industry goal succeed.

If the industry goal flag was not enabled at game setup, it counts as
automatically achieved.

### Goal checking timing

Goals are evaluated on three schedules:

- **Every 2 game-days**: The game checks whether the player has achieved
  all active goals. If every goal is met, the game triggers immediate
  victory.

- **Every 7 game-days** (only when no time limit is set): The game also
  checks whether any AI competitor corporation has achieved all goals.
  If any AI succeeds, the game ends — the player loses to the AI. This
  creates a race dynamic in open-ended games that does not exist in
  time-limited ones.

- **Annually** (year-end): If goals are active and a time limit is set,
  the game checks years remaining. If the deadline has expired (years
  remaining < 1), the game ends. If 1 to 5 years remain, a warning
  popup appears: "X years left to achieve the goal. Hurry Up!"

### Victory and defeat

When the game ends — whether by goal achievement, deadline expiry, or
the player choosing to end — the following sequence occurs:

1. **Goal result**: If goals are active, the game checks whether the
   player achieved all goals and plays either the victory sound or the
   defeat sound, then shows a goal status dialog listing every goal with
   its target, current value, and whether it was achieved.

2. **Performance chart**: A score breakdown is displayed, showing each
   scoring component and modifiers.

3. **Hall of Fame**: If the final score qualifies, the player enters
   the Hall of Fame.

### Scoring formula

The score is computed from base components plus sequential modifiers.

**Base components (added together):**

| Component | Formula | Points per unit |
|-----------|---------|-----------------|
| Personal Wealth | Total wealth in billions × 100 | 100 per billion |
| Corporation Worth | Corporation net worth in billions × 10 | 10 per billion |
| Dominated Sectors | Number of led sectors × 20 | 20 each |
| Dominated Product Types | Number of led products × 5 | 5 each |

**Modifiers (applied in order):**

1. **Difficulty scaling**: Multiply by the difficulty percentage,
   divide by 100. A harder difficulty setting gives a higher multiplier.

2. **Year penalty** (free play only, after 50 years): Multiply by 50,
   divide by years played. This reduces the score for long free-play
   games, discouraging indefinite play without goals.

3. **Goal bonus** (only when goals are active and all are achieved):
   - Free game (no scenario): the score is **doubled** (×2).
   - Scenario game: the scenario's **bonus points** are **added** to
     the score. This is why scenarios list a "Bonus Points" value.

4. **Cheat detection**: If the player used cheats at any point, the
   entire score is set to zero and "Cheated" is displayed instead.

### Goal Score Bonus setting

During new-game setup, a "Goal Score Bonus" value can be set from 0 to
500. This value is used as the additive bonus in scenario-style scoring.
In free games (no scenario), the bonus is always a flat ×2 multiplier
regardless of this setting.

### Hall of Fame

The Hall of Fame holds the top 5 scores across all games. Each entry
stores:

- Player name and corporation name
- Start year and end year
- Final score (used for ranking)
- Net worth (personal wealth plus corporation wealth)
- Whether all goals were achieved
- Scenario name (if the game was a scenario)

When a game ends, the score is compared against existing entries from
highest to lowest. If the new score beats any entry, the lower entries
shift down and the new entry is inserted at the appropriate rank.

### Scenario system

Scenarios are premade game setups stored as files with predefined maps,
economies, and goal configurations. The game scans for scenario files
and presents a selection screen.

**Scenario selection screen:**

Each scenario is listed with three columns:

| Column | Meaning |
|--------|---------|
| Title | Scenario name |
| Game Set | The product/economy data set used |
| Bonus Points | Points added to score if goals are achieved |

The detail panel shows the game set name, bonus point value, and a
descriptive text. Some scenarios include voice narration.

**Play options:**
- **Play the Scenario**: loads the predefined map, economy, and goal
  configuration exactly as designed.
- **Play in a New World**: uses the scenario's goals but generates a
  fresh random map and economy.
- **Detail**: shows the full scenario description.

Scenarios predefine the complete game state including all goal targets,
time limits, starting economic conditions, and available products. The
scenario's bonus points become the score bonus awarded for completing
all goals.

### Tutorial scenarios

Eight tutorial scenarios teach different aspects of gameplay. Each
tutorial uses a scripted instruction system that guides the player
through specific game mechanics step by step, with named lesson topics
such as retail operations, manufacturing, and corporate management.

### Ownership loss

If the player loses majority ownership of their corporation — through
hostile takeover, share dilution, or other means — a notification
dialog warns that they have lost control. This can effectively end a
goal-driven game since the player can no longer direct their
corporation toward the targets.

### New game goal configuration

The goal setup screen has two pages of settings:

**Page 1 — Time and financial goals:**
- Starting Year and No. of Years (time limit; 0 = unlimited)
- Goal Score Bonus (0–500)
- Player's Wealth target (in millions)
- Corporation targets: Annual Revenue, Annual Operating Profit, Net
  Worth, Market Value — all in millions
- Controlled corporations targets: Annual Revenue, Annual Operating
  Profit, No. of Controlled Companies, Net Worth, Market Value

**Page 2 — Operational and dominance goals:**
- Total No. of Employees
- Operating Profit Margin (0–100%)
- Return on Equity (0–100%)
- Stock Price
- Ownership (0–100%)
- No. of Product Classes Being Produced (0–100)
- No. of Product Types Being Produced (0–100)
- Sector dominance toggles (individual select/deselect per sector,
  plus select-all and deselect-all)
- Industry dominance toggles (individual select/deselect per product
  class, plus select-all and deselect-all)

Any numeric target set to zero is inactive. Dominance goals use
separate on/off toggles. In design mode, an additional "New Map
Scenario" option appears for creating scenarios.

## Map and terrain

### Overview

The game world is a 240 × 198 tile grid. Each tile stores its terrain
type, a data reference (firm or town ID), and four attribute bytes
controlling visual appearance and climate properties. Three separate
buffers hold the main map, an overlay for buildings and visual data,
and a compact minimap representation.

### Tile types

Tiles fall into five categories:

| Category | Variants | Description |
|---|---|---|
| Firm (building) | 16 | Built structures placed by players or AI. Data field holds the firm ID. |
| Grassland | 5 | Flat, walkable land. Cities can only be placed on grassland. |
| Forested/hilly land | 12 | Elevated terrain with trees or hills. |
| Deep ocean/water | 4 | Impassable water tiles. |
| Town | 13 | City tiles. Data field holds the town ID. Types split into "large town" (8 variants) and "small town" (5 variants). |

Each tile also stores four attribute bytes:

- **Terrain visual**: an index into a color lookup table, computed from
  height gradients and lighting. Determines how the tile appears on the
  minimap and world view.
- **Rainfall** (0–4): latitude-based, highest near the equator, falling
  with distance. On built tiles, this byte stores the building level.
- **Soil type** (0–3): noise-generated from neighbor averaging with random
  perturbation. On built tiles, this byte stores the building size.
- **Moisture** (0–100): noise-generated for land tiles, display-capped
  at 31 for the minimap moisture view.

### Terrain generation

When starting a new game, the map is generated procedurally. The game
shows "Generating Map, Please Wait..." during this process.

The generation pipeline runs in sequence:

1. **Fractal heightmap**: The terrain starts as a flat grid. Four random
   corner values are seeded, and a diamond-square (midpoint displacement)
   algorithm recursively subdivides the map to 5 levels of detail. At
   each level, midpoints are computed by averaging their neighbors and
   adding a random displacement. The displacement magnitude halves at
   each recursion level (320, 160, 80, 40, 20 units), producing
   large-scale continent shapes that gain finer detail at smaller scales.
   The algorithm is randomly oriented (horizontally or vertically) for
   variety.

2. **Water level normalization**: The game counts how many tiles qualify
   as land (height above 99). If land covers less than one-third of the
   map (fewer than 15,840 of 47,520 tiles), all tile heights are raised
   proportionally. A secondary check ensures at least 10 border tiles
   are land, preventing fully ocean-enclosed maps.

3. **Terrain jitter**: Small random displacements are added to break up
   flat, uniform areas.

4. **Height-to-type conversion**: Raw height values are classified:
   - Height below 1 → deep ocean
   - Height below 215 → water or grassland
   - Height 215 and above → land

5. **Coastline processing**: Each deep ocean tile checks its eight
   neighbors. Where ocean borders land, transitional coast tiles are
   placed to smooth the shoreline.

6. **Terrain variety**: Each tile's type receives a random offset within
   its category's variation range, creating visual diversity (multiple
   shades of grass, different tree types, etc.).

7. **Climate generation**: A random equator row is chosen (between
   rows 34 and 164). Climate attributes are then computed:
   - Rainfall decreases with distance from the equator (4 at the
     equator, down to 0 at the poles)
   - Soil type is generated via neighbor-averaging noise, producing
     smooth regional variation
   - Moisture uses a separate noise pass, with land tiles capped at
     a display maximum

8. **Terrain shading**: A lighting model computes surface gradients from
   neighboring tile heights and maps them to visual color indices. The
   result creates the illusion of sunlight on hills and shadows in
   valleys. Different height bands receive different color palettes:
   water, lowland, highland, and mountain.

### City placement

During new game setup, cities are placed on the generated terrain. The
process targets a specific number of cities (set by the game
configuration). The system makes up to 1,000 total attempts, aborting
early after 10 consecutive failures. A maximum of 12 cities can exist
on any map.

Each placement attempt:
1. Pick a random city name from the name pool
2. Try up to 4,752 random locations within the map (with a 5-tile
   border margin on all sides)
3. The candidate tile must be grassland
4. Validate: a 5×5 area around the candidate must be entirely grassland
5. Validate: minimum 15 tiles distance from any existing city (in both
   the horizontal and vertical axes independently)
6. Check that the city name is not already in use

If all validations pass, a town record is created with the assigned
name, position, and initial properties. After all cities are placed,
the system computes the centroid (average position) of all cities,
which is used to center the initial map view.

### Manual city placement (map editor)

The map editor's "Add City" button opens a dialog prompting for a city
name and population. The same validation rules apply: the 5×5 area must
be grassland, and the minimum 15-tile distance to other cities must be
respected. The "Delete City" button removes an existing city.

### Land value

Land value is computed per tile as the sum of two components.

**Town proximity value:**
1. Find the relevant town — either the town on the tile, the town
   assigned to the building on the tile, or the nearest town by
   Euclidean distance
2. Compute a base value from the town's per-capita GNP and
   population: `(per-capita GNP × 100 / 20,000) × population × 2.5 / 100`,
   which is per-capita GNP × population / 8,000. The town's level is not
   part of the base.
3. Apply linear distance decay: value drops to zero at a distance
   equal to the town's level plus 4. Higher-level towns project value
   over a larger radius.
4. Small towns (the small-town tile range) are multiplied by 0.5.
5. A $1 billion check on the value aborts the game rather than
   clamping.
6. Minimum floor: $500,000. No tile is worth less than this.

**Building bonus:**
If the tile's overlay has a building reference, a bonus is added:
- The bonus equals the building's type value multiplied by the
  building's level multiplied by the cube of the building's size,
  divided by 5
- This means large, high-level buildings dramatically increase land
  value (size has a cubic effect)
- A sanity cap prevents absurd values
- The $500,000 floor is re-applied after adding the bonus

The total land value (proximity + building bonus) is used by the
monthly firm processing and displayed in the sell-land dialog.

### Map editor

The map editor provides tools for manual terrain editing:

- **Generate**: regenerate the entire map from scratch
- **Terrain brushes**: Grassland, Mountain, and variant terrain types.
  "Keep Type" preserves the existing terrain category while editing.
- **Flood fill**: "All Sea" converts the entire map to water; "All
  Grassland" fills it with grass
- **City tools**: Add City (with name and population dialog) and
  Delete City
- **Import Map**: load a previously saved map file (available only in
  design/scenario mode)
- **Range and Strength sliders**: control the brush size and intensity

### Zoom levels

The world view supports multiple zoom levels:

| Level | View | Tile size | Description |
|---|---|---|---|
| Standard | Normal gameplay | Variable | Each tile rendered with its terrain sprite via the rendering pipeline. Result is cached for fast redraw. |
| Close-up | Attribute overlay | 2×2 pixels | Three sub-modes show different tile attributes as colored blocks: rainfall (5 colors by latitude), soil type (4 colors), or moisture (gradient from dry to wet). |
| Far | Strategic overview | 1×1 pixel | Shows the full map with building icons drawn for any tile containing a structure. |
| Detail | Firm inspection | N/A | Clicking a firm tile in this mode opens the firm's detail view. |

The close-up zoom centers on the cursor position. The far zoom shows
the entire map from origin (0, 0). Toggling between zoom levels
preserves the cursor position.

An animated selection highlight cycles through frames on a centisecond
timer, drawing a flashing rectangle around the currently selected area.
The animation bounces between two endpoints, reversing direction at
each extreme.

Firm icons are drawn on top of the terrain in all zoom levels (except
the detail mode), iterating through all active firms and calling their
icon-drawing routine.

### Map file format

Maps can be saved and loaded as files. The file contains:

1. **Header** (55 bytes): map metadata from the map file record
2. **Tile data** (optional, flagged): the full 380,160-byte tile buffer
   containing all 47,520 tiles
3. **App state** (optional, flagged): 737 bytes of game configuration
   from the application object, including goal settings

Two flags in the header control which optional sections are included.
When loading, if the file's city count exceeds the current target, the
city count is reset to a default value. After loading, the overlay
update runs across the entire map to recompute visual data.

Sound effects play when the cursor moves across different terrain:
grassland plays one of two grass sounds (randomly chosen), forested
land plays a terrain sound (50% chance), and ocean plays a water sound.
