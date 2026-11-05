# Code style

## OOP

Prefer objects where the domain has types:

- `Game` owns a `Sim` (and later save/load, UI hooks).
- `Sim` owns the world, calendar, RNG and entity arrays.
- `Firm` base class with one subclass per firm type.
- `Job` base class with one subclass per job type.
- `Product` base class with subclasses by product class where useful.

Hot-path entities that update every day (firms, jobs, product links, and
similar) are **plain Python classes**. Do not re-validate them with
Pydantic on every tick.

## Pydantic

Use Pydantic `BaseModel` for:

- **Rows loaded from data tables** (catalog rows, name pools, coefficients,
  provisional tuning constants).
- **Setup options** (new-game dialog, difficulty, toggles).
- **Save state** (serialize/deserialize the full game).

Do not wrap every daily-updating field in a Pydantic model. Validating
thousands of jobs and links once per day would hurt mobile/Pyodide
performance.

## Data tables (SQLite)

Anything that can live in a table **must** live in SQLite, shipped next to
the code as `capitalism/data/tables.sqlite`. Do not hardcode catalogs,
name pools, tier bands, climate factors, provisional coefficients or map
rules as Python literals.

- Edit the database (or a rebuild script) when tuning numbers.
- Load through `capitalism.tables`, which validates each row with Pydantic.
- Schema grows with new systems; keep one DB file for milestone 1.

## Sim rules (from `docs/design.md`)

- One seeded RNG owned by the world; no unseeded `random` calls.
- Fixed array/slot iteration order; deleted slots leave gaps.
- No I/O inside the sim package beyond reading the shipped tables DB —
  the runner prints and saves.
- Expose a stable state hash for determinism tests.
