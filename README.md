# Capitalism++

A modern take on the 90s business sim *Capitalism*. Milestone 1 is a headless Python simulation with no graphics.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Headless runner

```bash
python -m capitalism --days 30 --seed 1
capitalism --days 365
```

## Tests

```bash
pytest
```

CI runs the `build` check (lint + tests) on every PR.

## Docs

- [`docs/design.md`](docs/design.md) — slice specs and design calls
- [`docs/code-style.md`](docs/code-style.md) — OOP + Pydantic rules
- [`docs/synopsis.md`](docs/synopsis.md) — simulation overview
- [`docs/gamelogic.md`](docs/gamelogic.md) — full rules breakdown
- [`docs/milestone-1.md`](docs/milestone-1.md) — build order for milestone 1

Workflow: push to a branch, open a PR, merge only after `build` is green. No direct pushes to `main`.

## Code style

See [`docs/code-style.md`](docs/code-style.md). Short version: OOP for `Game` / `Sim` / firm·job·product hierarchies; tunable numbers live in `src/capitalism/data/capitalism.db` (see `docs/rules.md`) and load through Pydantic; plain classes for daily hot-path entities.

## Milestone 1 progress

1. **Clock and passes** — Gregorian calendar (day display clamped at 30), day-serial stagger, month/year passes, hook order, state hash.
2. **World data** — 240×198 map, city placement (default 5), town indicators, land-value floor.

```bash
python -m capitalism --days 365 --seed 42 --cities 5
```
