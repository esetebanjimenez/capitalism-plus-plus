"""Idempotent migration: AI town choice by firm type constants (#300, R24).

Techspec "Town choice": department stores score towns by demand
(FUN_0002e2d9, threshold (4 - character_type) * 2 + 3, minimum qualifying
(4 - character_type) // 2); R&D and software score education * 2.0 - labor_cost
(FUN_0002ee8d, constant 0xa46cc = 2.0, ties switch on cfg_random(3) == 0).
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEMAND = "FUN_0002e2d9 (techspec 'Demand scoring')"
EDU = "FUN_0002ee8d (techspec 'Education-labor scoring')"

RULES = [
    ("ai", "town_char_type_span", 4.0, "count", f"{DEMAND}: (4 - character_type)", 0),
    ("ai", "town_demand_step", 2.0, "per type", f"{DEMAND}: (4 - ct) * 2 + 3", 0),
    ("ai", "town_demand_base", 3.0, "demand", f"{DEMAND}: (4 - ct) * 2 + 3", 0),
    ("ai", "town_min_qual_divisor", 2.0, "count", f"{DEMAND}: min qualifying (4 - ct) / 2", 0),
    ("ai", "town_edu_weight", 2.0, "factor", f"{EDU}: education * 2.0 - labor_cost", 0),
    ("ai", "town_tie_switch_odds", 3.0, "1 in n", f"{EDU}: tie switches on cfg_random(3) == 0", 0),
]


def migrate(con: sqlite3.Connection) -> None:
    for row in RULES:
        con.execute(
            "INSERT INTO rules VALUES(?,?,?,?,?,?) ON CONFLICT(system, key) DO UPDATE SET "
            "value=excluded.value, units=excluded.units, ref=excluded.ref, "
            "provisional=excluded.provisional",
            row,
        )
    con.commit()
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "src/capitalism/data/capitalism.db")
    con.execute("PRAGMA foreign_keys=ON")
    migrate(con)
    migrate(con)
    print("AI town choice SQLite migration ok (idempotent)")
