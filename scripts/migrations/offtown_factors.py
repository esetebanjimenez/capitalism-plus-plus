"""Idempotent migration: labor and education factors for firms off town tiles (audit W2, #285).

`firm_labor_factor` (decomp:70631-70655): a firm whose place kind (firm+0x4a) is in
0x3000..0x300c (a town tile) gets round(town labor cost); every other firm gets
DAT_000b1b26, which is BSS and never written, so 0. The education factor
FUN_00066a2f (decomp:70663-70687) has the same shape with DAT_000b1b28 (also 0).
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LABOR = "firm_labor_factor (decomp:70631-70655)"
EDU = "FUN_00066a2f (decomp:70663-70687)"

RULES = [
    ("jobs", "town_place_min", float(0x3000), "tile kind", f"{LABOR}: town tile range low end", 0),
    ("jobs", "town_place_max", float(0x300C), "tile kind", f"{LABOR}: town tile range high end", 0),
    ("jobs", "offtown_labor_factor", 0.0, "percent", f"{LABOR}: DAT_000b1b26, BSS-zero", 0),
    ("jobs", "offtown_education", 0.0, "percent", f"{EDU}: DAT_000b1b28, BSS-zero", 0),
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
    print("off-town factors SQLite migration ok (idempotent)")
