"""Idempotent migration: native town spread constants (gap audit T4, #302).

`FUN_0004c334` (decomp:47131, body 47149-47292; techspec "Town spread"): on
each level-up a town scans a square of side 2 x (level + 4) + 1. Core tiles
(rounded Euclidean distance < level) become rural town tiles
(cfg_random(5) + 0x3008), the Chebyshev overlap gets a 1-in-10 roll for the
same, and the outer fringe (Chebyshev level+1 .. level+4) turns grassland into
urban town tiles (cfg_random(8) + 0x3000).
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REF = "FUN_0004c334 (decomp:47149-47292), techspec 'Town spread'"

RULES = [
    ("towns", "spread_fringe", 4.0, "tiles", f"{REF}: scan side 2 x (level + 4) + 1", 0),
    ("towns", "spread_overlap_odds", 10.0, "1 in n", f"{REF}: cfg_random(10) == 0", 0),
    ("towns", "rural_kind_base", float(0x3008), "tile kind", f"{REF}: cfg_random(5) + 0x3008", 0),
    ("towns", "rural_variants", 5.0, "count", f"{REF}: rural 0x3008-0x300c", 0),
    ("towns", "urban_kind_base", float(0x3000), "tile kind", f"{REF}: cfg_random(8) + 0x3000", 0),
    ("towns", "urban_variants", 8.0, "count", f"{REF}: urban 0x3000-0x3007", 0),
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
    print("town spread SQLite migration ok (idempotent)")
