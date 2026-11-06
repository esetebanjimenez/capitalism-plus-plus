# Milestone 1 — Base sim, build order

Goal: a pure Python sim, detached from graphics, as close as possible to the
original. `gamelogic.md` is the reference for every rule and coefficient;
section names below point into it. Each system lands with golden tests
(seeded scenario, run N days, check the numbers against the doc).

## Systems in build order

1. **Clock and passes** — *Time and the game clock*, *Day, month, and year*
   (month pass, year pass). Seeded RNG, 30-day month with real-length
   salary/overhead, staggered timers. Same seed gives the same game.
2. **World data** — *Towns and cities* (levels, tiers, starting GNP,
   population, monthly update, town demand tracking), *Map and terrain*
   (tile types, terrain generation, city placement, land value).
3. **Product catalog and demand** — *Product catalog and demand* (classes,
   full standard catalog, item links, demand model, product availability).
4. **Firms and jobs (core loop)** — *Firm types*, *Firm daily cycle*,
   *Job types*, *Firm-to-job mapping*, *Job daily cycle*, *Per-type job
   behavior*, including media firms, restaurant and seaport.
5. **Product links and markets (core loop)** — *Product links*: link daily
   cycle, score (quality + brand), price determination, market competition,
   brand perception, item-sell accounting, monthly cycle.
6. **Plans** — *Plan system*: plans as reusable firm layouts.
7. **Financial accounting and corporations** — *Financial accounting*,
   *Corporation internals*: income statement, expenses, interest, cash
   flow, loans, share issuance, dividends, bankruptcy, creation, brand
   strategy.
8. **People** — *Person system*: lifecycle, expertise, satisfaction,
   salary and retention, hired managers, character types.
9. **AI corporations** — *AI corporation strategy*, *NPC corporation
   spawning*: strategy modes, decision schedule, dispatcher, location
   selection, supply chain linking, vertical integration, dominance,
   asset sale, bankruptcy check, cash management.
10. **Stock market** — *Stock market*: shares, daily price movement,
    trading, SEC rules, tender offers, M&A, AI trading.
11. **News and random events** — *News and random events* (event types
    and random events; the news feed is data only).
12. **Setup, goals and scoring** — *Starting a new game* (setup,
    difficulty levels and rating, initialization sequence), *Goals,
    victory conditions, and scoring* (goal types, dominance, timing,
    victory/defeat, scoring formula, scenarios).

Systems 1–5 are the core loop: after 5, a scripted player can build a
farm → factory → store chain and sell to a city.

## Cut or simplified for milestone 1

- **Frame-sliced processing (simplified).** The original walks firms,
  jobs and links a few records per frame. Headless, each day runs whole:
  all firms, then all jobs, then all links, in fixed array order. Small
  fidelity risk: a job can no longer run before its own firm on the same
  day. Deleted-slot gaps keep their position so order matches.
- **Speed settings (moved).** Real time per day is a frontend concern;
  the runner just advances N days.
- **Multiplayer (cut).** Hot seat, PBEM, the 12-player cap and late-join
  bonus. The sim keeps multiple corporations, so this stays possible.
- **UI panels (cut).** Detail and summary panels, financial charts,
  placement chart, News Report panel. The data they show is kept and
  exposed by the sim's report.
- **Map editor, map file format, zoom levels (cut).** Maps are generated
  from a seed.
- **Tutorial scenarios and Hall of Fame (cut).** The scenario system
  itself stays.
- **Vestigial personality traits (simplified).** Only the 5 of 13 traits
  the original reads (character type, salary trait, trait 7, expansion,
  acceptance) are implemented; the rest are stored, not used.

When something in the original turns out ambiguous, we add a note here
with the call we made.

## Canonical reference

Tracked reference copy: [`docs/reference/gamelogic.md`](reference/gamelogic.md)
(Esteban's expanded source dump, 4,192 lines). Prefer it over older working
notes when they disagree. It is a canonical **reference** for coefficients and
section text — not labeled as a verified original binary dump unless that
provenance is separately proven. Keep existing team docs (`docs/gamelogic.md`,
`docs/design.md`, `docs/recipes.md`, generated `docs/rules.md`) in place; do not
delete or replace them with this file.

**Known inconsistency (freight).** In `docs/reference/gamelogic.md` Purchasing /
Freight wording at line 933 still says Freight Cost posts as
`unit-price-at-source × receipt`. That stale line is **overridden** by the
validated, Esteban-corrected formula used in code and slice docs:

`FREIGHT × Manhattan distance × SPENDING / 20,000`, with a $0.01 floor **only**
when the raw rate is zero (positive sub-cent rates are kept). Do not reintroduce
the unit-price×receipt reading from the reference prose.
