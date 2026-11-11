"""Idempotent migration: visual town footprint per town level (client map only).

Game Designer rule (PR #50, m2-ux-spec.md): the sim keeps a town as one tile,
but the map draws a square of radius r around it, with roads in a plus through
the centre and city blocks elsewhere. Firms and water always win over the
footprint, and ring tiles stay buildable. The reference draws a town as one
tile in 13 variants (gamelogic.md ~4181), so radius and block level are design
values, provisional and retunable here.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REF = (
    "Game Designer, PR #50 (m2-ux-spec.md): visual only, sim town stays one tile; "
    "reference draws a town as one tile (gamelogic.md ~4181)"
)
# level: (radius in tiles, block sprite level 0-2)
FOOTPRINT = {1: (0, 0), 2: (0, 0), 3: (1, 1), 4: (1, 1), 5: (2, 2), 6: (2, 2)}


def migrate(con: sqlite3.Connection) -> None:
    con.execute(
        "CREATE TABLE IF NOT EXISTS town_footprints ("
        " level INTEGER PRIMARY KEY CHECK(level >= 1),"
        " radius INTEGER NOT NULL CHECK(radius >= 0),"
        " block_level INTEGER NOT NULL CHECK(block_level BETWEEN 0 AND 2),"
        " ref TEXT NOT NULL, provisional TEXT NOT NULL DEFAULT '')"
    )
    marks = ",".join("?" * len(FOOTPRINT))
    con.execute(f"DELETE FROM town_footprints WHERE level NOT IN ({marks})", list(FOOTPRINT))
    for level, (radius, block) in FOOTPRINT.items():
        con.execute(
            "INSERT INTO town_footprints VALUES(?,?,?,?,'radius,block_level') "
            "ON CONFLICT(level) DO UPDATE SET radius=excluded.radius, "
            "block_level=excluded.block_level, ref=excluded.ref, provisional=excluded.provisional",
            (level, radius, block, REF),
        )
    con.commit()
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "src/capitalism/data/capitalism.db")
    con.execute("PRAGMA foreign_keys=ON")
    migrate(con)
    migrate(con)
    print("town footprint SQLite migration ok (idempotent)")
