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

- **Rows loaded from data tables** (catalogs, coefficients, tuning).
- **Setup options** (new-game dialog, difficulty, toggles).
- **Save state** (serialize/deserialize the full game).

Do not wrap every daily-updating field in a Pydantic model. Validating
thousands of jobs and links once per day would hurt mobile/Pyodide
performance.

## Data tables (SQLite)

Anything that can live in a table **must** live in the committed database
`src/capitalism/data/capitalism.db`. Do not hardcode catalogs, name pools,
tier bands, climate factors, provisional coefficients or map rules as
Python literals.

Each stored value carries:

- **units**
- **reference** — the `gamelogic.md` (or design.md) section it comes from
- **provisional** — set when the number is ours, not the original game's

Load through `capitalism.tables`, which validates rows with Pydantic.
Pyodide ships `sqlite3`, so the same DB works in the browser.

### Companion rules doc

`docs/rules.md` is generated from the DB by
`scripts/generate_rules_md.py`. Never edit `rules.md` by hand. After
changing the DB:

```bash
python scripts/generate_rules_md.py
```

`build` runs `python scripts/generate_rules_md.py --check` and fails when
the committed doc is stale. That keeps every number change visible as a
readable diff next to the binary DB change.

## Sim rules (from `docs/design.md`)

- One seeded RNG owned by the world; no unseeded `random` calls.
- Fixed array/slot iteration order; deleted slots leave gaps.
- No I/O inside the sim package beyond reading the shipped DB —
  the runner prints and saves.
- Expose a stable state hash for determinism tests.
