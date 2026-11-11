# Milestone 2: which products each job can make (`job_products`)

The job picker (`job_options` in `docs/m2-facade-contract.md`) needs to know
which products a job may be given. This spec defines a DB table for it, so
the rule is data rather than code. It adds no game rule: `Firm.add_job`
keeps its current checks, and the table only narrows what the picker
offers. Enforcing the table in the sim, if wanted, is a separate PR.

## Table

`job_products(job_type, product_id, ref, provisional)`, one row per
allowed pair, stored as final rows (no rule evaluated at load). It sits
next to `firm_job_allowed` and uses the same `ref` and `provisional`
columns. A build script fills it from the rules below so the rows can be
regenerated if the product table changes, and a test checks that the
stored rows match the rules.

## Producing jobs: listed in the table

| Job (id) | Products | Count | Source | Status |
|---|---|---|---|---|
| Crop Growing (1) | Every product with `kind = crop` (Rubber Plant, Sugar Cane, Barley, Cocoa, Cotton, Grapes, Rubber, Sugar, Tobacco, Wheat) | 10 | `gamelogic.md` product catalog, Plants and Crops (around line 3229); Crop Growing reads the product's planting month and growth duration (around 852) | Sourced |
| Livestock Raising (2) | Every product with `kind = livestock` (Cattle, Chicken, Pig, Sheep) | 4 | `gamelogic.md` "Livestock (4) ... Raised on farms" (around 3239) | Sourced |
| Livestock Processing (3) | Leather, Milk, Wool, Eggs, Frozen Beef, Frozen Chicken, Frozen Pork, Frozen Lamb | 8 | `gamelogic.md` "Livestock semi-products ... from livestock processing" (around 3242) and livestock "processed into consumer-grade meat products" (3240); the meat and egg rows are the five Livestock Products consumer goods with no recipe | Leather, Milk, Wool sourced; meat and eggs inferred |
| Logging (4) | Timber | 1 | Logging Camp creates "the matching extraction job" (`gamelogic.md` around 493); Timber is the only wood raw material | Inferred |
| Mining (8) | Aluminum, Chemical Minerals, Coal, Gold, Iron Ore, Silica | 6 | The raw materials that are neither Timber nor Oil | Inferred |
| Oil Extraction (9) | Oil | 1 | Same as Logging | Inferred |
| Manufacturing (7) | Every product with a row in `recipes` | 54 | `recipes` table (from `docs/recipes.md`); Manufacturing needs a recipe to run (`gamelogic.md` around 938) | Sourced |
| Research & Development (11) | Every product with a row in `recipes` | 54 | R&D raises a corporation's technology for a product, and technology only changes manufactured quality | Inferred |
| Software Development (13) | Software | 1 | `SoftwareDevelopment` requires the catalog `Software` product (M1 provisional, one title) | Sourced from M1 |
| Software Production (14) | Software | 1 | Same | Sourced from M1 |

Which livestock feeds which processed product stays in `livestock_yields`,
not in this table. This table lists only what a processing job may output.

## Trading jobs: not listed

Purchasing (10), Inventory (5), Private Labelling (6), Sales (12) and
Import (16) take whatever product their source supplies, so they get no
rows. The picker handles them like this:
- **Purchasing.** Any product some firm currently sells (the `suppliers`
  query), plus `importable = 1` products when a seaport exists.
- **Inventory, Private Labelling, Sales.** No product is picked. The job
  takes the product of the slot it is connected to, and the slot card
  shows "Connect to a job to choose its product" until then.
- **Import.** Seaport only: `importable = 1` products.
- **Advertising (15).** No product; it advertises the last connected job's
  product (`gamelogic.md` around 1040).

Selling to consumers (`link_consumer`) stays limited to products with
consumer demand. That is an existing check, not part of this table.

## Open questions for the Researcher

1. Is there a native table or check that ties each extraction job to its
   products, and how does a mine choose which mineral it extracts (for
   example a per-deposit resource)? Until that's known, Mining offers all
   six and the rows are `provisional`.
2. Which livestock produces which meat, egg or semi-product? This affects
   `livestock_yields`, which today has Chicken (20) yielding Milk (24).
   That looks like a typo for Cattle, and it should be checked in its own
   sim PR.
3. Does native R&D accept any product, or only manufactured ones?
