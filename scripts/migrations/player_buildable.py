"""Idempotent migration: which firm types the player can build (#251).

Adds `firm_types.player_buildable`. The build menu lists the 14 firm types minus the
Seaport (docs/m2-ux-spec.md "Build menu"): seaports are placed by the world, not built.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOT_BUILDABLE = {14}  # Seaport


def migrate(con: sqlite3.Connection) -> None:
    cols = {r[1] for r in con.execute("PRAGMA table_info(firm_types)")}
    if "player_buildable" not in cols:
        con.execute(
            "ALTER TABLE firm_types ADD COLUMN player_buildable INTEGER NOT NULL DEFAULT 1 "
            "CHECK (player_buildable IN (0, 1))"
        )
    con.execute("UPDATE firm_types SET player_buildable = 1")
    con.executemany(
        "UPDATE firm_types SET player_buildable = 0 WHERE id = ?", [(i,) for i in NOT_BUILDABLE]
    )
    con.commit()
    got = {r[0] for r in con.execute("SELECT id FROM firm_types WHERE player_buildable = 0")}
    assert got == NOT_BUILDABLE, got
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "src/capitalism/data/capitalism.db")
    con.execute("PRAGMA foreign_keys=ON")
    migrate(con)
    migrate(con)
    print("player_buildable SQLite migration ok (idempotent)")
