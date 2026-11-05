#!/usr/bin/env python3
"""Generate docs/rules.md from the committed capitalism.db.

Usage:
  python scripts/generate_rules_md.py          # write docs/rules.md
  python scripts/generate_rules_md.py --check  # exit 1 if docs/rules.md is stale
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "src" / "capitalism" / "data" / "capitalism.db"
OUT = ROOT / "docs" / "rules.md"

# Build-order sections (milestone-1.md). Only systems with rows are printed.
SYSTEM_ORDER = [
    ("clock", "1 — Clock and passes"),
    ("world", "2 — World data (map, terrain, towns)"),
    ("towns", "2 — Town indicators and land value"),
    ("products", "3 — Product catalog"),
    ("firms", "4 — Firms"),
    ("jobs", "5 — Jobs"),
]


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _prov(flag: int) -> str:
    return " **provisional**" if flag else ""


def render(con: sqlite3.Connection) -> str:
    lines: list[str] = [
        "# Capitalism++ rules tables",
        "",
        "Generated from `src/capitalism/data/capitalism.db` by",
        "`scripts/generate_rules_md.py`. Do not edit by hand — change the",
        "database, then regenerate. Numbers marked **provisional** are ours,",
        "not the original game's.",
        "",
    ]

    # Per-system scalar rules
    for system, title in SYSTEM_ORDER:
        rows = con.execute(
            "SELECT key, value, units, reference, provisional FROM rule_values "
            "WHERE system = ? ORDER BY key",
            (system,),
        ).fetchall()
        if not rows:
            continue
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| Key | Value | Units | Reference |")
        lines.append("|---|---|---|---|")
        for r in rows:
            val = r["value"]
            if float(val).is_integer():
                shown = str(int(val))
            else:
                shown = f"{val:g}"
            lines.append(
                f"| `{r['key']}` | {shown}{_prov(r['provisional'])} | {r['units']} | {r['reference']} |"
            )
        lines.append("")

    # city_names
    lines.append("## City name pool")
    lines.append("")
    lines.append("| Name | Tier | Reference |")
    lines.append("|---|---|---|")
    for r in con.execute(
        "SELECT name, tier, reference, provisional FROM city_names ORDER BY tier DESC, name"
    ):
        lines.append(f"| {r['name']} | {r['tier']}{_prov(r['provisional'])} | {r['reference']} |")
    lines.append("")

    # tier_gnp
    lines.append("## Per-capita GNP by tier")
    lines.append("")
    lines.append("| Tier | Low | High | Units | Reference |")
    lines.append("|---|---|---|---|---|")
    for r in con.execute(
        "SELECT tier, lo, hi, units, reference, provisional FROM tier_gnp ORDER BY tier"
    ):
        lines.append(
            f"| {r['tier']} | {r['lo']} | {r['hi']}{_prov(r['provisional'])} | {r['units']} | {r['reference']} |"
        )
    lines.append("")

    # climate_spend
    lines.append("## Consumer spending climate factors")
    lines.append("")
    lines.append("| Climate | Label | Factor | Units | Reference |")
    lines.append("|---|---|---|---|---|")
    for r in con.execute(
        "SELECT climate, label, factor, units, reference, provisional "
        "FROM climate_spend ORDER BY climate DESC"
    ):
        lines.append(
            f"| {r['climate']} | {r['label']} | {r['factor']:g}{_prov(r['provisional'])} | "
            f"{r['units']} | {r['reference']} |"
        )
    lines.append("")

    # unemployment
    lines.append("## Unemployment drift by climate")
    lines.append("")
    lines.append("| Climate | Label | Drift | Swing | Units | Reference |")
    lines.append("|---|---|---|---|---|---|")
    for r in con.execute(
        "SELECT climate, label, drift, swing, units, reference, provisional "
        "FROM unemployment_drift ORDER BY climate DESC"
    ):
        lines.append(
            f"| {r['climate']} | {r['label']} | {r['drift']:g} | {r['swing']:g}"
            f"{_prov(r['provisional'])} | {r['units']} | {r['reference']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if docs/rules.md is stale")
    args = ap.parse_args(argv)
    if not DB.exists():
        print(f"missing database: {DB}", file=sys.stderr)
        return 2
    text = render(_con())
    if args.check:
        if not OUT.exists():
            print(f"missing {OUT}; run without --check to generate", file=sys.stderr)
            return 1
        current = OUT.read_text(encoding="utf-8")
        if current != text:
            print(
                f"{OUT} is out of date; run: python scripts/generate_rules_md.py", file=sys.stderr
            )
            return 1
        print(f"{OUT} is up to date")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
