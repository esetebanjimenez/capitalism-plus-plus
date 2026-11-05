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

- **Data tables** (catalog rows, name pools, coefficients, provisional
  tuning constants loaded from data).
- **Setup options** (new-game dialog, difficulty, toggles).
- **Save state** (serialize/deserialize the full game).

Do not wrap every daily-updating field in a Pydantic model. Validating
thousands of jobs and links once per day would hurt mobile/Pyodide
performance.

## Sim rules (from `docs/design.md`)

- One seeded RNG owned by the world; no unseeded `random` calls.
- Fixed array/slot iteration order; deleted slots leave gaps.
- No I/O inside the sim package — the runner prints and saves.
- Expose a stable state hash for determinism tests.
