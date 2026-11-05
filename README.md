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
