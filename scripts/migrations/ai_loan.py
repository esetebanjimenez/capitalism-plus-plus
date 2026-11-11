"""Idempotent migration: AI raise-cash bank loan floor (gap audit B2/A3).

- ai.loan_minimum = 100,000: FUN_00037a7e (decomp:33468-33495) won't lend less
  than the constant at 0xa481c; the loan is capped at total assets minus debt.
  How the floor combines with the requested amount (lost in the decompile) is
  provisional: the sim asks for max(shortfall, floor) and skips the loan when
  the cap is below the floor.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ROW = (
    "ai",
    "loan_minimum",
    100_000.0,
    "dollars",
    (
        "FUN_00037a7e decomp:33468-33495, constant 0xa481c (Researcher trace, PR #94); "
        "cap = total assets - debt. Requested amount unknown: max(shortfall, floor) is provisional"
    ),
    1,
)


def migrate(con: sqlite3.Connection) -> None:
    con.execute(
        "INSERT INTO rules VALUES(?,?,?,?,?,?) ON CONFLICT(system, key) DO UPDATE SET "
        "value=excluded.value, units=excluded.units, ref=excluded.ref, "
        "provisional=excluded.provisional",
        ROW,
    )
    con.commit()
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "src/capitalism/data/capitalism.db")
    migrate(con)
    migrate(con)
    print("ai loan SQLite migration ok (idempotent)")
