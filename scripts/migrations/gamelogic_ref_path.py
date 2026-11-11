"""Idempotent migration: point `ref` citations at docs/gamelogic.md.

The reference doc moved from docs/reference/gamelogic.md to docs/gamelogic.md
(PR #91). Only the path prefix changes; the rest of each citation (line
ranges and notes) stays as it was.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

OLD = "docs/reference/gamelogic.md"
NEW = "docs/gamelogic.md"
TABLES = ("rating_throughput", "fixed_training_credits")


def migrate(con: sqlite3.Connection) -> None:
    for table in TABLES:
        con.execute(
            f"UPDATE {table} SET ref=replace(ref, ?, ?) WHERE instr(ref, ?) > 0", (OLD, NEW, OLD)
        )
    con.commit()
    for table in TABLES:
        n = con.execute(f"SELECT count(*) FROM {table} WHERE instr(ref, ?) > 0", (OLD,)).fetchone()[
            0
        ]
        assert n == 0, table
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "src/capitalism/data/capitalism.db")
    con.execute("PRAGMA foreign_keys=ON")
    migrate(con)
    migrate(con)
    print("gamelogic ref path SQLite migration ok (idempotent)")
