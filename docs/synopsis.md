# Capitalism Plus — Simulation Synopsis

A design reference for clean-room development of a similar business
simulation game. Describes the game's architecture and design
decisions without implementation details. Numbers, thresholds, and
formulas are omitted — the emphasis is on *how the systems interact*
and *why the design works*.

---

## The big picture

The player builds a business empire in a world of competing
corporations. The game is a layered economic simulation: a physical
world of cities and terrain, an economy of supply chains and consumer
demand, and a financial layer of stock markets and corporate finance.
Everything runs on a shared daily clock.

The player does not micromanage individual operations. Instead they
design firm layouts (which products to make, how to connect jobs
inside a building), hire people, set policies, and make financial
decisions. The AI competitors do the same things the player does —
they build firms, research technology, trade stocks — using the same
rules and the same economy.

Victory comes from achieving goals set at game start: personal wealth
targets, corporate financial milestones, market dominance, or some
combination. Free play with no goals is also supported.

---

## World and terrain

The game world is a tile-based map with procedurally generated terrain.
A fractal algorithm produces varied landscapes of grassland, forest,
and ocean, with climate properties (rainfall, soil quality, moisture)
assigned per tile based on latitude and noise. A minimum land-to-water
ratio is enforced to keep the map playable.

Cities are placed on grassland patches with minimum spacing between
them. Each city occupies a footprint that grows as the city levels up.
The map supports multiple zoom levels for strategic and tactical views.

A map editor allows manual terrain painting, city placement, and
import of saved maps. Terrain properties directly affect farming
output — fertile, rainy land produces better crops.

---

## Cities as living economies

Each city is an independent economic entity with its own population,
labor market, and consumer base. Cities track several indicators:
population, per-capita income, labor cost, labor quality, consumer
spending, unemployment, and economic climate.

These indicators are interconnected. A growing population attracts
businesses; businesses create employment; employment raises income;
income drives spending; spending generates demand for products. An
economic downturn raises unemployment, which lowers spending, which
can spiral if businesses pull out.

Cities have tiers based on their per-capita income, and levels based on
population. Higher-tier cities support more sophisticated industries
and higher land values. New cities can emerge during the game on
suitable terrain, expanding the economic map.

A simplified mode freezes all city indicators at moderate values,
removing the macroeconomic layer for players who want to focus purely
on business strategy.

---

## The three simulation layers

The simulation runs in three nested layers, each with its own update
cadence:

**Corporate layer.** Corporations, firms, and people. This is the
strategic level — who owns what, who runs what, what gets built where.

**Production layer.** The daily operation of firms: manufacturing,
farming, selling, advertising. Products flow through supply chains
from raw materials to consumer goods.

**Financial layer.** Money, stocks, loans, dividends. Corporations
have balance sheets and income statements that update continuously.
Stock prices react to earnings and market activity.

All three layers share the same clock and the same economy. A player
decision at the corporate level (build a new factory) creates activity
at the production level (jobs start running) which shows up at the
financial level (expenses hit the income statement, revenue follows
once goods are sold).

---

## The daily clock

Time advances in discrete days. Each day triggers a cascade of
updates:

1. Firms process their jobs (wages, training, production, sales).
2. Product links evaluate demand and competition.
3. AI corporations make strategic decisions.
4. People check their satisfaction and consider salary demands.
5. The stock market updates prices.
6. Random events may fire.

Monthly and yearly passes handle slower processes: city economic
updates, product catalog maintenance (new technologies appearing, old
ones becoming obsolete), financial statement archiving, and goal
deadline checks.

The daily cycle is deterministic given the same random seed — every
firm and every person processes in a fixed order. Staggered timers
spread expensive checks (monthly person reviews, city updates) across
different days so no single day has a processing spike.

---

## Firms and jobs

A firm is a physical building in a city that contains up to nine job
slots. Each job slot runs a specific operation: manufacturing, farming,
sales, purchasing, R&D, advertising, and so on. The power of the
system comes from how jobs are connected inside a firm.

A firm layout (called a "plan") defines which job types occupy the
nine slots and how they are wired together. A farm might have crop
growing slots feeding into an inventory slot, which feeds a sales
slot. A factory might have purchasing slots bringing in raw materials,
manufacturing slots producing goods, and sales slots selling them.

The player designs these layouts in a plan editor, then applies them
to firms. The AI uses the same plan system — it scores available
layouts against market conditions and picks the best one.

Each job has a rating (skill level) that improves through training
credits earned during daily work. Higher ratings mean better output
quality, faster production, and more efficient operations. Training
is gradual — it takes sustained operation to reach peak performance.

---

## Products and supply chains

The game has a large catalog of products organized into classes
(food, beverages, electronics, clothing, etc.). Each product has
intrinsic properties: base manufacturing cost, consumer price,
necessity level (how much people need it versus want it), and
technology requirements.

Products exist in the economy as "links" — instances that connect a
specific firm's output to a specific city's demand. Each link tracks
its own quality score, price, quantity in the market, and brand
perception. Competition happens at the link level: when two firms sell
the same product in the same city, the better score wins a
disproportionate share of demand.

The competition model uses a quadratic advantage curve — a product
with a slightly better score doesn't just win slightly more customers,
it wins *significantly* more. This creates winner-takes-most dynamics
where being second-best in a market is much worse than being first.

Consumer decisions are weighted by three factors: quality, price, and
brand. Each product class has its own weight balance — luxury goods
weight brand heavily, commodity goods weight price heavily. The
weights sum to a fixed total, making product positioning a tradeoff.

Demand grows over time when products are unavailable (pent-up demand)
and shrinks when markets are oversaturated. The growth uses the same
quadratic advantage model as competition, so unmet demand accumulates
faster for products that are better than what's currently available.

---

## Technology and R&D

Products have technology year ratings that determine when they become
available to manufacture. A product with a higher technology year
requires R&D investment before a corporation can produce it. R&D jobs
in R&D Center firms research specific products; the time to complete
scales steeply with the technology year — near-future products take
months, far-future products take years.

Technology also gates product quality. Products slowly lose quality
over time as the market moves on, creating pressure to research the
next generation. This drives a natural innovation cycle: researching
new products provides a competitive advantage, but the R&D investment
is substantial and the advantage is temporary.

---

## AI competitors

AI corporations are full participants in the economy. They build
firms, research products, trade stocks, and respond to market
conditions using the same rules as the player.

Each AI corporation operates in one of four strategy modes:

**Establishment mode.** The default starting mode. The AI builds a
diversified portfolio of businesses — department stores, factories,
farms, R&D centers. This is the broadest mode, touching all firm
types.

**Manufacturing mode.** Focuses on factories and production. The AI
narrows its building choices to production-oriented firms.

**Retail mode.** Focuses on department stores. The AI builds retail
outlets to sell products that others manufacture.

**Dormant mode.** The AI stops building and waits. New competitors
that enter after the initial wave of founding have a chance to start
in this mode, simulating late entrants who wait for opportunities.

Mode transitions are personality-driven. An AI stays in a mode for a
period determined by its personality traits, then evaluates whether to
switch based on how many factories and stores it operates.

### Decision-making

The AI makes decisions on staggered schedules. Every fifteen days it
checks whether to build something. Every thirty days it surveys
markets, adjusts pricing, and analyzes its financial position. Every
sixty days it looks for vertical integration opportunities. At
variable intervals (driven by aggressiveness) it checks whether it
dominates any market.

Each decision follows the same pattern: evaluate the opportunity,
score it, check whether resources are available, and if everything
passes, act. The AI uses the same plan scoring system as the plan
editor — it evaluates how well a firm layout matches the current
market conditions.

### Personality

AI behavior is shaped by a small number of personality traits, the
most important being aggressiveness (character type). Conservative
CEOs build slowly, tolerate lower returns, and wait longer between
expansion checks. Aggressive CEOs build fast, accept lower
profitability, and check for opportunities frequently.

A salary-related trait controls how quickly the AI transitions between
strategy modes and how demanding the CEO is about compensation. A
financial trait affects share buyback decisions and cash reserve
levels. An expansion trait sets the bar for entering new markets.

Many personality traits are initialized at creation but never actually
consulted during gameplay — the AI's decision-making is simpler than
the personality system suggests, relying on just a handful of key
traits.

### Cash management

AI competitors effectively have unlimited cash — their balance is
reset to a large amount each day. This is a deliberate design choice:
the AI is not meant to be constrained by cash flow. Its challenge to
the player comes from its strategic decisions and market presence, not
from financial limitations. This also means the AI never goes bankrupt
from cash starvation — only from having too few assets after years of
poor performance.

---

## People and hiring

Behind every corporation is a person — the CEO who runs it. The game
tracks a pool of persons, each with a name, portrait, gender, expertise
skills, personality traits, and a satisfaction level representing their
attitude toward the player.

### Expertise

Each person has seven expertise skills (manufacturing, R&D, farming,
advertising, training, retailing, raw materials) that combine into a
weighted performance score. The weights are not equal — manufacturing
expertise dominates, while raw material expertise barely matters. This
performance score drives salary expectations and is used by the AI
when scoring which products to pursue (the CEO's skills influence what
the corporation is good at building).

### Satisfaction and salary

Satisfaction drifts gradually over time. Well-paid managers become
happier; underpaid ones stagnate near neutral. Negative satisfaction
slowly heals on its own. But salary events cause sharp drops — a
declined raise request or an accepted-but-grudging salary offer can
plunge satisfaction from "Very Good" to "Bad" in a single event.

The salary system runs on two cycles. A daily retention cycle fires
with personality-dependent probability — more salary-oriented
personalities demand raises more often. When triggered, the CEO
evaluates whether their compensation matches their worth and may look
for opportunities elsewhere. A separate annual check in January
compares the manager's wealth to a stored reference and triggers a
formal raise request if wealth has grown significantly.

When a salary conflict escalates, the player faces a choice: offer
a raise or let the manager go. Salary negotiation has a formula-based
acceptance test — the manager computes a target salary based on
weekly pay, years of service, and an annual base. Longer service
increases the demand. If the player's offer falls short, the manager
resigns immediately.

### Hiring

Only the player can hire managers — AI corporations receive their
CEOs exclusively through the competitor spawning system at game start
and throughout the game. Whether a person accepts a job offer depends
on their satisfaction, but the threshold is generous: most offers
are accepted unless the person is deeply unhappy.

A hired manager takes over the day-to-day operations of the player's
corporation, with configurable policies for pricing aggressiveness
and supply chain management. When fired, all firms they managed
revert to the corporation's main CEO.

---

## Stock market

Every corporation (except the government) has publicly traded shares.
The stock market is a full simulation with daily price movement,
share issuance, dividends, insider trading rules, tender offers, and
corporate mergers.

### Price dynamics

Stock prices move daily based on a random walk biased by earnings
momentum. Positive earnings push prices up over time; negative
earnings push them down. Occasional spikes and crashes add volatility.
Trading activity also affects prices — buying pushes prices up,
selling pushes them down.

### Player participation

The player can buy and sell shares in any corporation, receive
dividends, launch tender offers to acquire other companies, and issue
new shares in their own corporation to raise capital. SEC-style
insider trading rules prevent selling shares in a company you're about
to acquire.

### Mergers and acquisitions

When a corporation acquires enough shares in another (through tender
offers or market buying), it can initiate a merger. The acquired
company's assets, firms, and employees transfer to the acquirer. The
merger can be funded by cash or by share swaps.

AI corporations also trade stocks — they invest surplus cash, buy back
their own shares when it makes financial sense, and manage portfolios
of holdings in other companies.

---

## Corporate finance

Each corporation maintains a balance sheet with asset categories
(cash, inventory, business assets, land, stock holdings) and a
liability side (loans and equity). An income statement tracks revenue,
six categories of expenses, and other income sources.

Interest rates fluctuate based on the global economic climate. Loans
accrue daily interest. Overdraft spending (negative cash) incurs
penalty interest. The president's salary is a daily expense.

Financial data is archived monthly and yearly, providing history
charts that help the player and the AI evaluate long-term performance.
No tax mechanics exist — all profit is pre-tax.

### Bankruptcy

When a corporation's performance deteriorates far enough, bankruptcy
triggers. The player gets options: take a loan, sell stock, sell a
subsidiary, sell another company's shares, or liquidate. AI
corporations follow a similar escalation — they try each remedy in
sequence before finally liquidating if nothing works.

### Dividends

Corporations pay dividends from profits. The player can set automatic
dividend distribution or be prompted each time. Dividends affect stock
attractiveness and share price.

---

## Goals and victory

The game supports two modes: free play (sandbox with no objectives)
and goal-driven play. Goals are configured at game start and can
combine any number of targets:

- Financial targets on the player or their controlled corporations
  (wealth, net worth, revenue, profit)
- Operational targets (employee count, profit margin, return on
  equity, stock price, ownership percentage, product diversity)
- Sector dominance (lead one of four economic sectors by revenue)
- Industry dominance (lead every product in a product class by
  market share)

Goals are checked frequently. Once all goals are met, victory is
immediate. An optional time limit adds pressure — if the deadline
passes with unmet goals, the player loses.

A scoring formula evaluates performance across multiple dimensions
(wealth, corporate worth, market presence, products, difficulty level)
and ranks the player in a hall of fame.

Scenarios provide pre-configured goal sets with bonus points, offering
structured challenges beyond free-form play.

---

## News and events

A news system reports significant events: new competitor entries,
technology breakthroughs, market shifts, financial milestones, and
random disasters. News items are timestamped and categorized, and
the player can filter them by corporation, category, and time period.

Random events add unpredictability: livestock diseases can destroy
farm output, buildings can be damaged, crops can fail, R&D
breakthroughs can accelerate technology, inventory losses can wipe out
stock, and economic downturns can depress entire regions. The frequency
of random events is configurable at game start.

---

## Game setup and difficulty

The new-game screen exposes a large number of configuration options,
grouped into pages covering competitors, the economy, trade, and
goals. Preset difficulty levels configure many options at once, but
every individual setting can be overridden.

Key difficulty levers include: number of competitors, competitor
aggressiveness, starting capital for competitors, city count, import
quality, competitor expertise level, and whether random events occur.

A difficulty rating formula combines these settings into a single
score that scales the final game score — harder settings produce
higher ratings. This makes scores comparable across different
configurations.

---

## Design principles for a similar game

Several design decisions make the simulation cohesive:

**Shared rules.** The AI uses the same economy, the same firms, the
same products, and the same stock market as the player. There are no
hidden advantages or separate rule sets. The AI's edge comes from
unlimited cash (a deliberate simplification) and tireless attention
to opportunities.

**Layered complexity.** Each system (firms, products, stocks, cities)
is individually simple — a firm is just nine job slots with
connections. Complexity emerges from interaction: a factory's output
becomes a store's inventory, which becomes a city's supply, which
drives demand, which attracts competitors, which pressures prices.

**Staggered processing.** Expensive checks (person salary reviews,
city economic updates, AI strategic decisions) are spread across
different days using modular arithmetic. This keeps each day's
processing cost roughly constant regardless of how many entities
exist.

**Personality as a small lever.** AI differentiation comes from a
handful of traits, not elaborate decision trees. Aggressiveness
controls timing and risk tolerance; a salary trait controls strategic
patience. Most of the "personality system" is vestigial — designed
for more complexity than the final AI actually uses.

**Winner-takes-most competition.** Quadratic advantage curves in the
demand model mean that small quality or price edges produce large
market share differences. This creates natural monopolies that the
player must actively challenge, and rewards focused excellence over
broad mediocrity.

**Plans as the unit of design.** Rather than placing individual
machines or workers, the player designs firm layouts as reusable
templates. This raises the abstraction level from micro-management
to strategic design — the interesting decision is *what combination
of jobs to build*, not how to operate each one.
