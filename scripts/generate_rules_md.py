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
    ("products", "3 — Product catalog and demand"),
    ("firms", "4 — Firms"),
    ("jobs", "4 — Jobs"),
    ("links", "5 — Product links and markets"),
    ("research", "4b — Research and projects"),
    ("software", "4b — Software"),
    ("advertising", "4b — Advertising and media"),
    ("corporations", "7 — Corporation financials"),
    ("persons", "8 — Persons"),
    ("ai", "9 — AI corporations"),
    ("stock", "10 — Stock market"),
    ("news", "11 — News system"),
    ("events", "11 — Random events"),
    ("scoring", "12 — Scoring and difficulty"),
]

P = " **provisional**"
P_SHORT = " **p**"


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _prov(flag: int) -> str:
    return P if flag else ""


def _num(val: float | None) -> str:
    if val is None:
        return "—"
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    if isinstance(val, float):
        return f"{val:g}"
    return str(val)


def _cell(row: sqlite3.Row, col: str, prov_cols: set[str]) -> str:
    """One value of a wide catalog row, marked when its column is provisional."""
    return _num(row[col]) + (P_SHORT if col in prov_cols else "")


def _prov_set(raw: str) -> set[str]:
    return {c for c in raw.split(",") if c}


def _table(lines: list[str], title: str, header: list[str], rows: list[list[str]]) -> None:
    lines.append(f"## {title}")
    lines.append("")
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    lines.append("")


def render(con: sqlite3.Connection) -> str:
    lines: list[str] = [
        "# Capitalism++ rules tables",
        "",
        "Generated from `src/capitalism/data/capitalism.db` by",
        "`scripts/generate_rules_md.py`. Do not edit by hand — change the",
        "database, then regenerate. Numbers marked **provisional** (or **p** in",
        "the wide catalog tables) are ours, not the original game's.",
        "",
    ]

    _table(
        lines,
        "Research durations by tech-year bucket",
        ["Bucket", "Months", "Reference"],
        [
            [str(r["tech_year_bucket"]), f"{r['months']}{_prov(r['provisional'])}", r["ref"]]
            for r in con.execute("SELECT * FROM research_durations ORDER BY tech_year_bucket")
        ],
    )
    _table(
        lines,
        "Provisional livestock processing",
        ["Livestock", "Output", "Output / input", "Input ratio", "Reference"],
        [
            [
                str(r["livestock_id"]),
                str(r["product_id"]),
                f"{r['yield_factor']:g} **provisional**",
                f"{r['input_ratio']:g}",
                r["ref"],
            ]
            for r in con.execute("SELECT * FROM livestock_yields ORDER BY livestock_id")
        ],
    )

    _table(
        lines,
        "Rating efficiency and storage",
        ["Rating", "Efficiency %", "Storage multiplier", "Reference"],
        [
            [str(r["rating"]), f"{r['efficiency_pct']:g}", f"{r['storage_mult']:g}", r["ref"]]
            for r in con.execute("SELECT * FROM rating_throughput ORDER BY rating")
        ],
    )
    lines += [
        "The storage multiplier is registered but inactive: the native base capacity and",
        "type factor are missing, so M1 preserves the normalized product×size×3-day capacity.",
        "",
    ]
    # Per-system scalar rules
    for system, title in SYSTEM_ORDER:
        rows = con.execute(
            "SELECT key, value, units, ref, provisional FROM rules WHERE system = ? ORDER BY key",
            (system,),
        ).fetchall()
        if not rows:
            continue
        _table(
            lines,
            title,
            ["Key", "Value", "Units", "Reference"],
            [
                [
                    f"`{r['key']}`",
                    _num(float(r["value"])) + _prov(r["provisional"]),
                    r["units"],
                    r["ref"],
                ]
                for r in rows
            ],
        )

    _table(
        lines,
        "City name pool",
        ["Name", "Tier", "Reference"],
        [
            [r["name"], f"{r['tier']}{_prov(r['provisional'])}", r["ref"]]
            for r in con.execute(
                "SELECT name, tier, ref, provisional FROM city_names ORDER BY tier DESC, name"
            )
        ],
    )

    _table(
        lines,
        "Per-capita GNP by tier",
        ["Tier", "Low", "High", "Units", "Reference"],
        [
            [
                str(r["tier"]),
                str(r["lo"]),
                f"{r['hi']}{_prov(r['provisional'])}",
                r["units"],
                r["ref"],
            ]
            for r in con.execute(
                "SELECT tier, lo, hi, units, ref, provisional FROM tier_gnp ORDER BY tier"
            )
        ],
    )

    _table(
        lines,
        "Consumer spending climate factors",
        ["Climate", "Label", "Factor", "Units", "Reference"],
        [
            [
                str(r["climate"]),
                r["label"],
                f"{r['factor']:g}{_prov(r['provisional'])}",
                r["units"],
                r["ref"],
            ]
            for r in con.execute(
                "SELECT climate, label, factor, units, ref, provisional "
                "FROM climate_spend ORDER BY climate DESC"
            )
        ],
    )

    # Unemployment: drift and swing carry their own reference and flag.
    unemp = con.execute(
        "SELECT climate, label, drift, drift_ref, drift_provisional, swing, swing_ref, "
        "swing_provisional, units FROM unemployment_drift ORDER BY climate DESC"
    ).fetchall()
    _table(
        lines,
        "Unemployment drift by climate",
        ["Climate", "Label", "Drift", "Swing (±)", "Units"],
        [
            [
                str(r["climate"]),
                r["label"],
                f"{r['drift']:g}{_prov(r['drift_provisional'])}",
                f"{r['swing']:g}{_prov(r['swing_provisional'])}",
                r["units"],
            ]
            for r in unemp
        ],
    )
    if unemp:
        lines.append(f"Drift: {unemp[0]['drift_ref']}. Swing: {unemp[0]['swing_ref']}.")
        lines.append("")

    # Slice 3: product catalog
    _table(
        lines,
        "Product classes",
        ["Id", "Code", "Name", "Durable", "Quality decay base", "Group", "Reference"],
        [
            [
                str(r["id"]),
                r["code"],
                r["name"],
                "yes" if r["durable"] else "no",
                _cell(r, "quality_decay_base", _prov_set(r["provisional"])),
                _cell(r, "group_flags", _prov_set(r["provisional"])),
                r["ref"],
            ]
            for r in con.execute("SELECT * FROM product_classes ORDER BY id")
        ],
    )

    products = con.execute(
        "SELECT p.*, c.code AS class_code FROM products p "
        "JOIN product_classes c ON c.id = p.class_id ORDER BY p.id"
    ).fetchall()
    names = {r["id"]: r["name"] for r in products}
    ref_note = products[0]["ref"] if products else ""
    _table(
        lines,
        "Products — market",
        [
            "Id",
            "Name",
            "Class",
            "Kind",
            "Unit",
            "Price",
            "Demand / 1000 / day",
            "L",
            "N",
            "P%",
            "Q%",
            "B%",
            "Import",
        ],
        [
            [str(r["id"]), r["name"], r["class_code"], r["kind"]]
            + [
                _cell(r, c, _prov_set(r["provisional"]))
                for c in (
                    "unit",
                    "base_price",
                    "demand_per_1000",
                    "luxury",
                    "necessity",
                    "w_price",
                    "w_quality",
                    "w_brand",
                    "importable",
                )
            ]
            for r in products
        ],
    )
    lines.append(f"Reference: {ref_note}.")
    lines.append("")
    _table(
        lines,
        "Products — production",
        [
            "Id",
            "Code",
            "Name",
            "Base cost",
            "Capacity / day",
            "Tech importance",
            "Base tech",
            "Tech year (years)",
            "Freight coefficient",
            "SPENDING (freight $)",
            "Plant month (0 = Jan)",
            "Grow months",
            "Climate",
            "Moisture",
        ],
        [
            [str(r["id"]), _cell(r, "code", _prov_set(r["provisional"])), r["name"]]
            + [
                _cell(r, c, _prov_set(r["provisional"]))
                for c in (
                    "base_cost",
                    "base_capacity",
                    "tech_importance",
                    "base_tech_level",
                    "tech_year",
                    "freight",
                    "spending_usd",
                    "plant_month",
                    "grow_months",
                    "suit_climate",
                    "suit_moisture",
                )
            ]
            for r in products
        ],
    )

    recipes = con.execute(
        "SELECT product_id, output_qty, speed_pct, ref FROM recipes ORDER BY product_id"
    ).fetchall()
    inputs: dict[int, list[sqlite3.Row]] = {}
    for r in con.execute(
        "SELECT product_id, input_id, qty, quality_weight FROM recipe_inputs "
        "ORDER BY product_id, input_id"
    ):
        inputs.setdefault(r["product_id"], []).append(r)
    rows: list[list[str]] = []
    for rec in recipes:
        ins = inputs.get(rec["product_id"], [])
        skill = 100 - sum(i["quality_weight"] for i in ins)
        rows.append(
            [
                names[rec["product_id"]],
                str(rec["output_qty"]),
                f"{rec['speed_pct']}%",
                "; ".join(
                    f"{names[i['input_id']]} × {i['qty']} @ {i['quality_weight']}%" for i in ins
                ),
                f"{skill}%",
            ]
        )
    _table(
        lines,
        "Recipes",
        ["Product", "Output / cycle", "Speed", "Inputs (qty / cycle @ quality weight)", "Skill"],
        rows,
    )
    if recipes:
        lines.append(
            f"Reference: {recipes[0]['ref']}. Speed is a throughput multiplier (200% = twice the units per work cycle); skill is the "
            "share of output quality from manufacturing skill (100 − Σ input weights)."
        )
        lines.append("")
    _table(
        lines,
        "R&D prerequisites",
        ["Product", "Requires first", "Reference"],
        [
            [names[r["product_id"]], names[r["requires_id"]], r["ref"]]
            for r in con.execute(
                "SELECT product_id, requires_id, ref FROM rnd_prereqs ORDER BY product_id, requires_id"
            )
        ],
    )

    # Slice 4: firms and jobs
    _table(
        lines,
        "Firm types",
        [
            "Id",
            "Name",
            "Setup cost",
            "Overhead / month",
            "Max slots",
            "Live inventory",
            "Government",
            "Units",
            "Reference",
        ],
        [
            [str(r["id"]), r["name"]]
            + [
                _cell(r, c, _prov_set(r["provisional"]))
                for c in ("setup_cost", "overhead_month", "max_slots")
            ]
            + [
                "yes" if r["live_inventory"] else "no",
                ("yes" if r["government"] else "no")
                + (P_SHORT if "government" in _prov_set(r["provisional"]) else ""),
                r["units"],
                r["ref"],
            ]
            for r in con.execute("SELECT * FROM firm_types ORDER BY id")
        ],
    )
    _table(
        lines,
        "Firm sectors (sector dominance goals)",
        ["Firm type", "Name", "Sector", "Sector name", "Reference"],
        [
            [
                str(r["firm_type"]),
                r["name"],
                _num(r["sector"]) + (P_SHORT if "sector" in _prov_set(r["provisional"]) else ""),
                r["sector_name"],
                r["ref"],
            ]
            for r in con.execute(
                "SELECT s.*, f.name FROM firm_sectors s JOIN firm_types f ON f.id = s.firm_type "
                "ORDER BY s.firm_type"
            )
        ],
    )
    _table(
        lines,
        "Job types",
        [
            "Id",
            "Name",
            "Staff",
            "Setup cost",
            "Training factor",
            "Capacity mult",
            "Units",
            "Reference",
        ],
        [
            [str(r["id"]), r["name"]]
            + [
                _cell(r, c, _prov_set(r["provisional"]))
                for c in ("staff", "setup_cost", "training_factor", "cap_mult")
            ]
            + [r["units"], r["ref"]]
            for r in con.execute("SELECT * FROM job_types ORDER BY id")
        ],
    )
    _table(
        lines,
        "Jobs allowed per firm type",
        ["Firm type", "Job type", "Reference"],
        [
            [r["firm"], r["job"] + _prov(r["provisional"]), r["ref"]]
            for r in con.execute(
                "SELECT f.name AS firm, j.name AS job, a.ref, a.provisional "
                "FROM firm_job_allowed a JOIN firm_types f ON f.id = a.firm_type "
                "JOIN job_types j ON j.id = a.job_type ORDER BY a.firm_type, a.job_type"
            )
        ],
    )
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
