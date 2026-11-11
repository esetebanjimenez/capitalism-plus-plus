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
