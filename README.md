# Capitalism++

A modern take on the 90s business sim *Capitalism*. Milestone 1 is a headless Python simulation with no graphics.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Headless runner

Advance the sim N days and print a short report:

```bash
python -m capitalism --days 30 --seed 1
# or, after install:
capitalism --days 365
```

## Tests

```bash
pytest
```

CI runs the `build` check (lint + tests) on every PR.

## Docs

- [`docs/synopsis.md`](docs/synopsis.md) — simulation overview
- [`docs/gamelogic.md`](docs/gamelogic.md) — full rules breakdown
- [`docs/milestone-1.md`](docs/milestone-1.md) — build order for milestone 1

Workflow: push to a branch, open a PR, merge only after `build` is green. No direct pushes to `main`.

## Code style

- Prefer OOP: `Game` → `Sim` → firms, products, etc. (with subclasses where the original has types).
- Use **Pydantic** `BaseModel` for sim data (towns, tiles, calendar fields, later products/firms).

## Milestone 1 progress

Systems landed:

1. **Clock and passes** — seeded RNG, 30-day months, real month lengths for salary/overhead, weekday, month/year passes.
2. **World data** — 240×198 map (diamond-square terrain), city placement, town indicators with staggered monthly ticks, land-value floor.

```bash
python -m capitalism --days 365 --seed 42 --cities 8
```
