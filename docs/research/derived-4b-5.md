# 4b/5 corrections from the 4,192-line reference

The separate [native-evidence audit and artifact request](native-evidence-gaps.md)
records the provisional `20000`/`60000` split and a later **reported**, not
independently verified header finding. It does not close the capacity gap or
authorize any fill-rule, db, runtime or golden change.

`docs/reference/gamelogic.md` byte-for-byte. References below are line ranges
in that committed file. Relative to the earlier repo reference, its substantive
additions are rating/capacity (558–585), media (608–713), and training
(730–794). This is a **docs-only correction**: it changes neither runtime code
nor tests, and any follow-up experiment must be measured by the Programmer.

## Rating, production, and storage

- For ratings 1..9, put the **efficiency/fixed-credit multipliers**
  `100,130,160,200,250,300,360,430,500%` and **storage multipliers**
  `8,10,14,16,20,24,30,35,40` in db tables (558–585). Replace the provisional
  `50+5*rating` production efficiency; do not apply its labor-quality clamp
  again. M1 applies this rating table to its explicitly provisional daily
  normalized production bases.
- Native stock capacity is stated as
  `base_capacity × type_factor × rating_multiplier`, but the native base and
  type factor are not supplied. **Do not multiply the provisional
  product×size×job-capacity stock buffer by 8..40.** At rating1, naively
  adding ×8 would inflate three days of stock to24 days. Register the new
  storage lookup but leave the old M1 buffer untouched until native inputs
  are extracted. Do not confuse this storage multiplier with throughput.
- Rating loss may charge excess stock as an expense (584–585); no valuation
  or posting account is provided, so this is still a gap. The `36,500`
  livestock conversion and extraction zero-denominator guards remain marked
  provisional interpretations, not a recovered full growth equation.
- Software Production stays literally `min(room, efficiency×capacity)`
  **without `/100`** (988–994), unlike production modes that include it.
  PR #20's provisional copy result 76.8 neither establishes native units nor
  balanced software behavior. It may not be cited as an original target;
  real unit base and normalization remain unknown awaiting later research.

## Training

### Credits and the weekly check

- Award credits on actual work days. Evaluate on **weekday2**; a step passes
  when `train_acc > current_rating×900` **strictly**. One check may complete
  exactly one step, resetting credits to0 without subtracting the threshold
  or preserving overflow (730–786). Staff-count steps gain1 rating, capped
  at9; then reset the step counter. At9, do not gather a further upgrade.
- Steps per rating: Inventory/Advertising1, Purchasing/SoftwareProduction4,
  PrivateLabelling6, Sales/SoftwareDevelopment8, R&D12, Crop/Livestock16,
  Manufacturing/Logging/Mining/Oil24. Staff1 does **not** itself imply a
  passive credit each day; no credit rule for Inventory or Advertising was
  supplied. Manufacturing needs `24×1×900=21,600` for1→2 and
  `24×8×900=172,800` for8→9. A neutral theoretical100 credits/day for ten
  weeks gives7,000, not that first level. Equality at900 must fail; excess
  credit cannot cause multiple weekly steps.
- The reference calls downgrades theoretical (788–793); it gives neither a
  complete rewind algorithm nor an exact negative-credit boundary. Under
  positive settings the outlined work credits increase. Don't restore the
  obsolete30% demotion rule,90% promotion gate,30/60 rating thresholds or
  monthly `job_types.training_factor` scalar as native mechanics.

### Credit bases: supported and unresolved

- Fixed credits are Crop **20**, Livestock **10**, R&D **14**, multiplied by
  the rating percentage **once** (739–747). R&D and SoftwareDevelopment use
  this shared visit procedure (963–970), separate from project completion.
- Livestock Raising additionally says **10 per visit** at849. M1 provisionally
  gives that specific operation literal10 per actual worked visit, with no
  second multiplication of that same10. The operation-specific statement's
  relationship to the general rating-scaled base remains an open source
  precedence question; it must not produce two independent base pools.
- **Livestock Processing does not expose a numeric credit base or work
  ratio.** Its continuous production returns0 and has no completion signal or
  supply pull (851–860), but that does not identify training credits. Hold
  credit/progress path at0/pending research in this M1 correction as a safe
  explicit implementation gate, not a claim that the original never trains.
  Extraction and SoftwareProduction refer to a `production ratio`, but give
  no numeric coefficient or divisor (864–871,988–994). Only scientific R&D,
  not production progress, has the explicitly shared14/visit mapping; supply
  no fabricated manufacturing-style equivalent for these other modes.
- The supplied work-credit numerators/denominators are:
  - Manufacturing `actual_units×100/nominal_step` (906): half of a nominal
    100-unit step earns50 raw credits, not zero at the old90% production
    threshold. Use actual output as numerator and the nominal computed step,
    as distinguished from actual output, as denominator.
  - Purchasing `receipt×80/order_size` (934).
  - Sales `sold_count×100/cap` (949).
  - PrivateLabelling `moved×18/capacity` (890).
  Do not apply a rating multiplier a second time to these work-based credits.
  Guard a zero denominator and no-work day as0 credits defensively, without
  treating an idle visit as a successfully processed batch.
- The source explicitly also credits company training budget (default10%)
  and city education for retail vs a global default otherwise (754–759), but
  its exact scalar/divisor mapping is absent. Current town data has eight
  indicators, no proven education field. Any neutral-at-budget10 mapping is
  **provisional db content**, not proof city's education equals100%; keep
  credit gating visible pending the missing native inputs. `job_types.training_factor`
  isn't established as a direct monthly growth factor; the AI-firm30-day
  skill formula (481–496) is not the source's Job `train_acc` rule.
- Confirmed expense remains independent of rawcredit scale:
  `corp_training_budget × daily_wage / training_expense_divisor` posted
  daily tocat3. Budget10/divisor100.0 gives10% of actual wages and
  **$16,791 on April wages of $167,910**. Don't change this confirmed golden.

## Media audience, revenue, and advertising

### Initialization and monthly sequence (603–713)

- Eligible Government corporation4 established-town/product media receives
  random audience10..39 inclusive. Other commercial media begin audience
  **0**, reputation **100**. Generate twelve historical months by
  independently varying initial audience up to±10%; do not fabricate their
  prior paid-ad revenue (635–641).
- In this order (621–679): (1)update reputation, (2)update audience including
  rival transfer and saturation, (3)compute revenue, (4)roll history.
  Reputation random range is±30; low audience<15 gets an additional boost
  while high audience>40 gets an additional penalty, then clamp−100..100.
  Exact extra boost/penalty bounds are missing, so don't reuse±30 as if
  their native formulas had also been recovered.
- `audience += (random(0..100)+reputation−50)/200`; floor at0, retaining
  fractional audience month-to-month. Positive gains take share from same-type
  same-town rivals with aggregate0.5 transfer share (not net extra audience);
  exact allocation is not completely specified. A stable, nonnegative
  proportional M1 allocation is necessarily provisional. When the same-type
  town total is above90, the **currently updated firm** loses the excess,
  floored at0. This is sequential deterministic firm-walk behavior, not proof
  every same-type firm is synchronously clipped at month end.
- Keep the literal revenue equation and source order (680–699):
  ```
  reach = staff * audience / 100
  ad_base = (town_economic_stat / 200) * reach / 100
  revenue_base = town_purchasing_power * ad_base / 100
  seasonal = (seasonal_component + town_stat / 200) * (audience / 100 + 2) / 100
  revenue = max(100, ad_rate * (revenue_base / 1000) * seasonal / 100)
  ```
  Don't silently reverse `/200`. Native revenue `staff`, `ad_rate`, both town
  economic fields and the season mapping remain unavailable. Put any
  necessary temporary fixture in the db and label it provisional rather than
  assigning these to unrelated existing town indicators. CPM is
  `revenue×1000/revenue_base`, guarded at zero denominator and **not** another
  payable demand multiplier.
- Media payroll uses `firm.salary` through the common wage formula, with no
  training post (615–620). It does not establish `media_staff=20`. The native
  initial salary, connection of `firm.salary` to revenue `staff`, and direct
  min100 revenue ledger category are still missing. Do not double-post a paid
  category0 contract receipt and unclear direct min100 revenue as if both were
  proven separate revenue channels.

### Advertising and cold-start policy (701–713,1004–1024)

- Re-target products every30days; select a partner every60days. Technology
  must be **strictly >14**. Eligibility is current rating below target plus
  an **unspecified threshold**. No needy product gives0 budget; don't apply
  a minimum when no ad is needed. Current last-sales10% budget and
  `budget/100000` brand increment capped at100 remain provisional. Nonzero
  budgets are bounded **$50,000..$500,000**. A genuine paid campaign posts
  advertiser category6 expense and exact equal category0 media revenue once,
  with no CPM-based multiplier.
- Newer source701–713 calls for **same-town TV/Newspaper with strictly
  audience>5**, not Radio. But older advertising1004–1011 still checks media
  revenue over a threshold: this is an unresolved source contradiction.
  M1 **provisionally chooses the newer audience>5 check** to allow cold start;
  it does not assert native equivalence or an original revenue-field mapping.
  Radio still runs media audience/revenue; it simply isn't an ad type in this
  selector. New commercial audience0 grows normally past5, so the first paid
  partnership must not require an artificial prior category0 receipt.
- Follow-up tests should use ordinary deterministic game-RNG audience growth,
  strict boundary5 rejected/above5 eligible, and same-town TV/Newspaper
  selection. Replace the intentional cold-start xfail only once the
  implementation actually passes. **This docs PR itself does not alter or
  pass any test.** Native threshold, media-stat fields and precise allocation
  details remain tracked gaps, not data hidden in a db table.

## Citation boundaries

The requested operative line ranges all point to the same committed reference:
livestock quality **839**; manufacturing production/input **895–917**;
purchasing **919–935**; sales **939–961**; software **988–994**; media
**603–713**; advertising **996–1024**. Treat generic unit-price freight line
933 as overridden by the confirmed freight mechanic, not released validation.
The **3408+ sales/category** concern belongs in a separate code-and-ledger
audit, not an invented ongoing watcher. Non-farmland against nondepartment
`+50` at 1119–1124 versus 3356–3362 is also unresolved: current M1 selects
non-farmland but cannot promote it as fact on the strength of a majority vote.

## Deliberate boundaries and preserved goldens

1. Native product/type capacity, new livestock input/output mapping and
   software units remain unknown. Production and current three-day buffer
   stay distinct. After implementation, measure a full new dense-scenario
   P&L under rating efficiency; positive consolidated profit remains its
   goal, but previous P&L predictions cannot be claimed as measured now.
2. **`20000/base_price` in slice 3 and live `60000` db capacity global are not
   consistent.** The latter is PR #11's provisional scale; neither the new
   rating table nor media adds a universal factor3 measurement of base units.
   Do not prescribe silent 20k rollback or 60k retention for more revenue.
   Update the fill rule/reuse value explicitly after native extraction and
   separately measured alternate-scaling scenarios; keep research gap open.
3. Budget/education credit conversion, `training_factor`, Processing ratio,
   Extraction/SoftwareProduction ratio, and passive credit paths are unknown.
   R&D manager/2+own-tech duration/progress formulas remain existing
   provisional model, **not** `progress += skill − current technology`
   validated by this source. Software's price/cost/demand/capacity content
   and CPM calculations likewise need real product/media inputs first.
4. Current `score²`, `/20` oversupply, brand and star normalizers stay
   provisional. **Do not cite** market `7.5%/2.5%` loss/recovery,
   `(100+status)/100` passive or `(400+status)/100` active multiplier, or
   `30/60` brand/techthresholds: none is supported by this reference.
5. Independently confirmed freight remains
   `FREIGHT × firm Manhattan distance × product SPENDING / 20,000`,
   with the $0.01/unit floor only when the rawrate is0. Positive fractional
   sub-cent rates must not round to that floor. April fixture receipts are
   Wheat **$187.11**, Flour **$311.85**, Bread **$757.50**, total
   **$1,256.46**; holding other prior April categories fixed gives
   **−$230,200.20**. This isolated fixture is not a predicted new rating
   economy outcome. Duration/demand/recipe rules and dense-economy goldens
   outside the explicit 4b/5 amendments remain unchanged.
