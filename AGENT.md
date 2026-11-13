# Agent Reference — Capitalism++

Quick-reference for agents working on this codebase. Points to every
research and development resource in the repo and nearby.

## Databases

### `src/capitalism/data/capitalism.db` — Sim Rules DB
SQLite database driving the simulation. Tables: `products`, `firm_types`,
`job_types`, `livestock_yields`, `rules`, `tech_tree`, etc. Many values
are **Observed** (decoded from the native EXE or 1STD.SET); some are still
**provisional** (placeholders awaiting native confirmation). The audit doc
tracks which is which.

- Query with: `.venv312\Scripts\python.exe -c "import sqlite3; ..."`
- Regenerate `docs/rules.md` after schema changes:
  `.venv312\Scripts\python.exe scripts/generate_rules_md.py`

### `src/capitalism/data/1std_set.db` — Parsed 1STD.SET
SQLite copy of the standard game-set file, 16 dBASE III tables, 738 rows.
Tables: RICH, ITEMCLAS, FIRMJOB, JOB, RAW, GROUP, PERSON, METHOD,
FARMPROD, HEADER, TOWN, FIRM, ITEMPAE, ITEM, FARMLIVE, FARMCROP.

Use this instead of re-parsing the binary SET file each time. Regenerate
with: `.venv312\Scripts\python.exe scripts/parse_set.py --sqlite`

## Research Documents

### `docs/gamelogic.md` — Game Rules Reference
~4200-line merged reference covering every game system: economy, firms,
jobs, consumers, stock market, AI, technology, advertising, etc. The
canonical source for how the native game works. When the sim diverges
from this doc, the audit tracks it.

### `docs/research/techspec.md` — Reverse-Engineering Binary Reference
Native evidence from the decompiled EXE: struct layouts, field offsets,
function addresses, constant values. Sections cover town-item market
structs, link structs, brand records, FARMLIVE format, save file
sections, and more. Cite `decomp:LINE` for decompile line references.

### `docs/m2-sim-gap-audit.md` — Sim-Gap Audit Tracker
Row-by-row comparison of the Python sim against native behaviour. Each
row has: ID, area, status (Fixed / Inferred / Unknown / Hold), native
reference, sim code reference, and fix PR. This is the main work tracker
for sim accuracy.

### `docs/rules.md` — Auto-Generated Rules Dump
Readable dump of every row in `capitalism.db`. **Do not edit by hand** —
regenerate with `scripts/generate_rules_md.py`.

### `docs/recipes.md` — Manufacturing Recipes
54 recipes from 1STD.SET METHOD section: inputs, outputs, quantities,
quality weights, production speeds.

### `docs/synopsis.md` — Simulation Synopsis
High-level design reference: how the game systems interact and why the
design works. No formulas or thresholds — architecture and intent only.

### `docs/research/save_format.md` — Save File Format
Reverse-engineered from `load_game_file` (decomp:0x1dbf6). Documents
file extensions (.SET, .II2, .II, .SAV), section tags, and the loader
chain.

### `docs/research/derived-4b-5.md` — Derived Corrections
Synthesis of open gaps and corrections (e.g., 20k-vs-60k policy thresholds).

### `docs/research/native-evidence-gaps.md` — Evidence Gap Analysis
Inventory of what native evidence exists and what is missing. Notes which
values are document-only vs. binary-confirmed.

### `docs/design.md` — Sim Design Document
Architecture decisions for the Python sim implementation.

### `docs/code-style.md` — Code Style Guide
Project conventions for Python code.

## Scripts

### `scripts/parse_set.py` — SET File Parser
Parses the Capitalism Plus `.SET` binary (dBASE III archive format).

```
--dump              Dump all sections to stdout
--compare           Compare SET products/firms against capitalism.db
--sqlite [OUT]      Export all sections to SQLite (default: 1std_set.db)
```

### `scripts/parse_sav.py` — Save File Parser
Parses `.SAV` / `.II` save-game streams.

### `scripts/compare_saves.py` — Save Comparison
Diffs two parsed save files to find what changed between game states.

### `scripts/generate_rules_md.py` — Rules Doc Generator
Reads `capitalism.db` and writes `docs/rules.md`. Run after any DB
schema or data change.

### `scripts/export_sample_map.py` — Map Exporter
Exports a sample game map for visualization or testing.

### `scripts/pyodide_bundle.py` — Pyodide Bundler
Bundles the sim for browser execution via Pyodide (used by the web client).

## External Resources (not in repo)

### Native EXE Binary
`D:\capitalism plus\CAPPLUS\CAPPLUS.EXE`

The original Win32 game executable. Use for decoding constants from the
data segment (addresses like `0xa622b` are offsets into EXE object 2,
base `0xa0000`). Read with Python `struct` from raw bytes.

### Decompiled Source
`D:\capplus-re\analysis\CAPPLUS\decomp\capplus_decompiled.c`

Ghidra decompilation of the EXE. Function names are `FUN_XXXXXXXX`;
reference by `decomp:LINE` in docs. Key functions:
- `FUN_00075aec` — brand awareness monthly update (N9)
- `FUN_0005136e` — advertising campaign (N10)
- `FUN_00040fd5` — AI dividend decision (R4)
- `FUN_000785f1` — freight calculation

### Game Data
`D:\capitalism plus\CAPPLUS\GAMESET\1STD.SET`

The standard game-set file (binary dBASE III archive). Already parsed
into `1std_set.db` — prefer the SQLite copy.

## Skills

### `.claude/skills/implement-group/SKILL.md`
Workflow for implementing a batch of sim-gap audit rows: research →
issue → branch → implement → tests → docs → PR → CI. Invoke with
`/implement-group <row-IDs or issue numbers>`.

## Development Environment

- **Python**: 3.12 via `.venv312\Scripts\python.exe`
- **PYTHONPATH**: `src`
- **Source**: `src/capitalism/`
- **Tests**: `tests/` — run with `.venv312\Scripts\python.exe -m pytest -q --tb=short`
- **Lint**: `ruff check` (enforced by CI)
- **CI checks**: `build` (lint + tests), `client`, `pyodide-smoke` — all three must pass
- **Branch protection**: `main` requires PRs; never push directly

## Key Conventions

- Every value in the sim DB should be **Observed** (decoded from the EXE
  or SET file). Provisional/placeholder values must be replaced with
  native-confirmed data before marking a row Fixed.
- Open a GitHub issue BEFORE creating a branch. Link it in the PR with
  `Closes #N`, not `Refs`.
- `MAX_CORPS = 12` throughout the sim.
- Watcom `__CHP` (float-to-int) maps to Python `round()`.
