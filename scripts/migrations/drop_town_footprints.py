"""Idempotent migration: drop the legacy town_footprints table (#249).

The client draws towns from the native tile kinds (`town_kind`, rural 0x3000-0x3007 and
urban 0x3008-0x300c, art #307) that `spread_town` paints, so the per-level radius and
block-level footprint (Designer rule, PR #50) is no longer used anywhere.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def migrate(con: sqlite3.Connection) -> None:
    con.execute("DROP TABLE IF EXISTS town_footprints")
    con.commit()
    assert (
        con.execute("SELECT count(*) FROM sqlite_master WHERE name='town_footprints'").fetchone()[0]
        == 0
    )
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "src/capitalism/data/capitalism.db")
    migrate(con)
    migrate(con)
    con.execute("VACUUM")
    print("drop town_footprints SQLite migration ok (idempotent)")
