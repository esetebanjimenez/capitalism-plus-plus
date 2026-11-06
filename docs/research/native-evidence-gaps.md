# Capitalism++ provisional-space research (2026-11-06, Asia/Jerusalem)

Executor read-only inspection for Producer handoff. **No runtime code edited.**
No native game binaries, decompilations, traces, or Ghidra/IDA projects found
under `/workspace` (or `/home/box` outside package caches). Evidence is
document/db only.

## Sources inspected (versions)

| Artifact | Path | Notes |
|---|---|---|
| Merged reference (canonical) | `/workspace/capitalism-plus-plus/docs/reference/gamelogic.md` | **4192 lines**, md5 `761169ca0a22df093f80a6cdac6d9bd0`. Byte-identical in `cpp-repo` and `cpp-rating-training`. Esteban attachment per older-research / derived-4b-5. |
| Older repo reference | `/workspace/cpp/gamelogic.md`, `docs/gamelogic.md` (~4024–4028) | Pre-merge; lacks rating/media/training expansions. |
| Research backlog | `/workspace/older-research.md` (= `research-backup-draft.md`) | 2026-11-06 backlog of open gaps. |
| Derived corrections | `/workspace/cpp-repo/docs/research/derived-4b-5.md` (213 lines, newer than capitalism-plus-plus copy at 192) | Strongest synthesis of gaps + 20k-vs-60k policy. |
| Design / rules | `docs/design.md`, `docs/rules.md` in repos | Label provisional vs ref. |
| Live DB | `src/capitalism/data/capitalism.db` | Provisional fill values; **not** native tables. |
| `cpp-agent-work/` | empty before this report | — |
| Native binary / decomp | **ABSENT** | Only named decomp citation locally: freight `FUN_000785f1` (already verified; out of scope). **No SET_* software symbols present anywhere.** |

## Evidence status key

- **DOCUMENTED**: stated in 4192-line reference with line cites; still may lack native field values.
- **PROVISIONAL (M1/db)**: labeled provisional in design/rules/db; must not be promoted to native.
- **GAP**: needed native value/func/field not recoverable from local materials.
- **CONTRADICTION**: two documented statements conflict; unresolved without binary.

---

## 1. Native base_capacity / type-factor (20k vs 60k) — FIRST PRIORITY

### Documented
- Stock formula name only: `base-capacity × type-factor × capacity-multiplier`
  with rating multipliers **8,10,14,16,20,24,30,35,40** at ratings 1..9
  (ref **580–585**; efficiency table **564–574**).
- Native **base-capacity table** and **type-factor** values: **not supplied**
  (older-research; derived-4b-5 §Rating; design.md ~462–465).

### Provisional conflict (NOT a user choice; both non-native)
- `design.md` fill rule: `base_capacity = max(1, round(20000 / base_price))`.
- Live DB `rules.products.capacity_value_per_day = 60000` with explicit note:
  *"design.md says 20000, raised ×3 so the bread chain can meet town demand (PR #11)"*, `provisional=1`.
- All 85 product rows satisfy `round(base_price * base_capacity) ≈ 60000`
  (e.g. Wheat 0.1→600000, Tobacco 1→60000, Cattle 500→120).
- derived-4b-5: **"Do not prescribe silent 20k rollback or 60k retention"**;
  keep gap open until native extraction + alternate measured scenarios.

### Evidence status
**GAP** for native base/type. **PROVISIONAL** for both 20k (design text) and 60k (PR #11 db). Do not treat as user preference.

### Exact cites
- Ref: **558–585** (rating/capacity).
- derived-4b-5: deliberate boundary #2 (20k vs 60k).
- DB rule key `products.capacity_value_per_day`.
- No `FUN_*` / SET for capacity found.

---

## 2. Livestock processing input / yield coefficient

### Documented
- Daily output: `(efficiency × capacity / 100 × product-yield-factor) / 100`
  where yield-factor comes from **"the livestock record for the assigned product"**
  (ref **851–860**).
- Continuous; returns 0; no completion signal; no supply-chain pull.
- Plan slots mention **Parameter 2** used by livestock processing (ref **1655**)
  but do not define numeric meaning.
- Raising side scalars 36,500 and 100 (ref **3711–3712**, **842–846**) are
  growth conversion, not processing yield coefficients.
- Catalog lists livestock/semi/consumer meat prices (3068–3138) but **not**
  per-animal yield coefficients or input consumption rates.

### Provisional (must not cite as native)
- DB `livestock_yields` (provisional=1, ref *"source yield missing"*):
  - Cattle(19)→Leather(23) yield 20, input_ratio 1
  - Chicken(20)→Milk(24) yield 1, input_ratio 1  **(catalog-implausible pairing)**
  - Sheep(22)→Wool(25) yield 40, input_ratio 1
  - Pig→*missing*; Frozen meats→*missing*

### Evidence status
**DOCUMENTED formula skeleton**; **GAP** for native yield-factor table, input
draw rate, param2 semantics, and meat-product mapping. DB rows are provisional only.

---

## 3. Software units / prices / cost / demand and SET functions

### Documented
- Production: `min(remaining-room, efficiency × capacity)` **without `/100`**
  (ref **988–994**). Training credits = unspecified "production ratio".
- Firm/job setup/overhead/staff tables exist (416–417, 554–555, 600–601).
- R&D / Software R&D share visit credits 14 and duration table (963–986).

### Provisional
- Single DB product `SOFTWARE`: price **$100**, cost **$5**, demand **0.1**/1000,
  base_capacity **1000**, tech 0 — design.md Software section marks all provisional.
- PR #20 measured 76.8 copies/day: derived-4b-5 forbids citing as original target.

### SET functions
- **No `SET_*` symbols, setters, or decompiled software unit-setup functions**
  exist in local docs, migrations, or code comments.
- Only local decomp name: `FUN_000785f1` (freight; out of scope).

### Evidence status
**DOCUMENTED** production equation shape. **GAP** for native catalog economics,
capacity base, copy normalization, and all SET_* APIs. Native artifacts absent.

---

## 4. Media: staff / ad-rate / town econ / season / reputation / budget / ledger

### Documented (ref **603–713**, advertising **996–1024**, **1004–1020**)
- Payroll: `(salary × 2000 / days-in-month × labor) / 100` on `firm.salary`;
  no training post (**615–620**). Does **not** define revenue `staff`.
- Init: gov corp type4 established-town audience **10..39**; others audience **0**,
  reputation **100**; 12-mo history ±10% (**635–641**).
- Reputation monthly ±30; low audience &lt;15 extra boost; high &gt;40 extra penalty;
  clamp [−100,+100]. **Exact boost/penalty bounds GAP** (**650–654**).
- Audience: `(rand(0..100)+reputation−50)/200`; floor 0 (**656–667**).
- Rival transfer ~50% share; same-type town soft-cap ~90 (**669–678**);
  exact rival allocation formula incomplete.
- Revenue chain (**680–699**):
  ```
  reach = staff * audience / 100
  ad_base = (town_economic_stat / 200) * reach / 100
  revenue_base = town_purchasing_power * ad_base / 100
  seasonal = (seasonal_component + town_stat / 200) * (audience/100 + 2) / 100
  revenue = max(100, ad_rate * (revenue_base/1000) * seasonal / 100)
  ```
  CPM display `revenue×1000/revenue_base`.
- Town panel has **eight** indicators (**2142–2150**): Population, GNP,
  Per Capita, Unemployment, Labor Cost, Labor Quality, **Consumer Spending
  Index** (=purchasing power wording), Economic Climate. **No Education**
  field despite training text (**754–759**) referencing education for retail.
- Two unnamed "town economic / town_stat" inputs in revenue: **GAP** which of
  the eight (or other fields) map to them; season from "monthly economic time series".
- Campaign: partner every **60** days; product retarget **30** days; tech **>14**;
  budget clamp **50k..500k**; no-need → budget 0 (**701–713**, **1004–1020**).
- Paid campaign: advertiser **cat6** = media **cat0** equal amount once
  (derived-4b-5); direct floor-100 revenue ledger category **unresolved**.
- **CONTRADICTION**: newer **701–713** partner gate = TV/Newspaper audience **>5**;
  older **1004–1011** = media revenue above threshold. M1 provisionally picks audience>5.

### Provisional (not native)
- DB `firms.media_staff=20` provisional; design forbids treating as fact.
- `advertising.media_min_revenue=10000`, audience fixtures, ad_revenue_fraction=0.1,
  brand/100000 caps — provisional budget derivation.

### Evidence status
**DOCUMENTED** formulas/order/clamps. **GAP**: native staff init, ad_rate,
mapping of two town econ stats + purchasing power + season series, extra
reputation bounds, campaign budget from "firm financials", floor-100 ledger
category, salary↔revenue-staff link.

---

## 5. Market / capacity scalars and +50 classification; decay/restore

### Documented
- Live-inventory demand movement (**1118–1141**, restated **3351–3389**).
- Oversupply shrink: `quantity / scalar` — **scalar unnamed** (**1120–1121**, **3355–3358**).
- Weight: `firm.weight × 5`, **plus 50**, clamp 100 (**1123–1124**, **1221–1224**).
- Four-factor competition; transfer uses `(100 − decay) × … × factor² …`
  (**1203–1219**, **3376–3885**). **decay** here is the per-link weight-like
  factor, not a separate restore timer. Numeric divisors/constants mostly unnamed.
- Score drop quantity: proportional / "global scalar" (**1111–1114**).

### +50 classification CONTRADICTION
- **1119–1124 / 1221–1224**: "+50 for **non-farmland** tiles".
- **3356–3362**: "+50 base for **non-department-store** retailers".
- derived-4b-5 / older-research: unresolved; M1 currently uses non-farmland
  (`rules.links.weight_nonfarm=50`) but **must not promote as fact**.

### Explicitly NOT supported by this reference (do not cite)
- `score²` share, oversupply `/20`, brand/star normalizers (provisional M1).
- Market `7.5%/2.5%` loss/recovery; `(100+status)/100` / `(400+status)/100`;
  `30/60` brand/tech thresholds (derived-4b-5 boundary #4).

### Evidence status
**DOCUMENTED** qualitative mechanics + named +50 conflict. **GAP** for all
unnamed scalars/divisors and for resolving +50 class. No native restore% found.

---

## Out of scope (already sourced — not re-worked)
Wages, setup/overhead, recipes, freight (`FUN_000785f1`), training expense goldens.

## What would unblock (requires native artifacts not on box)
1. Product/job base_capacity + type_factor tables from binary/data files.
2. Livestock record yield/input/param2 fields.
3. Software product records + any SET_* / unit-init functions.
4. Media firm init (salary, staff, ad_rate) + town field indices used by revenue.
5. Named constants behind market scalars and definitive +50 predicate.

## Paths
- Detailed notes: this file.
- Canonical reference: `/workspace/capitalism-plus-plus/docs/reference/gamelogic.md`
- Best synthesis: `/workspace/cpp-repo/docs/research/derived-4b-5.md`
- Prior backlog: `/workspace/older-research.md`

---

## Native artifact request (remaining evidence gaps)

A purported `Game/Informations.h` with declared capacity constants was
mentioned in this handoff **without an actual file, accessible full path,
commit/hash, or verified provenance**. The Researcher states it did **not**
supply that artifact or its asserted definitions. This invalidates the
attribution in the handoff, not merely its implementation proof. The claim is
excluded as evidence, including its named fields, values, ranges and suggested
mode distinction. It must not steer native capacity changes or a new media
salary/staff formula. The first 199 lines above remain the original report
verbatim; this request is an appended, separately dated editorial section.

The Researcher is checking Esteban's designated reference folders read-only;
this document records no results from that inspection until exact artifacts
and evidence are independently available to the repo agents. No existing
provisional capacity value is changed or promoted, and no binary claim is
reconstructed from memory.

### What would settle the native gaps

1. An **authorized original game executable with its matching data files**, or
   the **authorized decompiler-exported data and symbol map**. Identify the
   matching game version/build, provide an accessible full path for the file
   or export and a cryptographic hash/commit for the artifact, and describe
   how it was extracted. A filename or prose declaration is not enough.
2. Exact **capacity/table declarations** for base capacity and type factor,
   including declared type, entries and units, plus every proposed
   capacity-derived `Firm` field. Identify stable source line anchors and
   address/field offsets when available.
3. **Call-site functions, identifiers/signatures and stable evidence anchors**
   showing reads, initialization, operating-mode selection, and the mapping
   among product, production type and firm record. A declaration alone is not
   evidence of its runtime use, scale or effect.
4. Native job capacity/minimum-efficiency and view-threshold evidence, with
   matching identifiers, paths and hashes. Also provide the listed livestock,
   software, media, market-scalar and `+50` records from §1–§4. No proportional
   salary-versus-linear-staff rule or `+$30` staff constant is introduced.
5. A symbol map or analysis identifying external/indirect calls not apparent
   in table declarations. Distinguish direct extraction from inference by the
   reverse-engineering tool.

### Acceptance standard

A value gains native evidence only when repo agents independently read an
artifact whose accessible path, hash/version and provenance support the cited
declaration, and its callers support the proposed behavior. Until then no
such value or formula belongs in `capitalism.db`, docs/rules.md, gameplay code
or existing goldens. This research note changes no runtime or tests.
