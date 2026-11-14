"""Idempotent migration: AI location finder tile ranges and radii (#315).

FUN_0002dc7c (techspec "Location (FUN_0002dc7c)", gamelogic "Location selection"):
radius = town base for one branch and base + 4 for the other, capped at 4, random
offsets clamped to the map, retried 20 times with radius + 1. The base-radius
branch checks tile kinds 0x3008..0x300c (town core), the base + 4 branch
0x3000..0x3007 (outer ring). The techspec calls them rural and urban, which is the
pre-#311 naming: under Esteban's correction the core is urban, the ring rural.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REF = "FUN_0002dc7c (techspec 'Location (FUN_0002dc7c)')"

RULES = [
    ("ai", "site_core_kind_min", float(0x3008), "tile kind", f"{REF}: base-radius branch", 0),
    ("ai", "site_core_kind_max", float(0x300C), "tile kind", f"{REF}: base-radius branch", 0),
    ("ai", "site_ring_kind_min", float(0x3000), "tile kind", f"{REF}: base + 4 branch", 0),
    ("ai", "site_ring_kind_max", float(0x3007), "tile kind", f"{REF}: base + 4 branch", 0),
    ("ai", "site_ring_radius_extra", 4.0, "tiles", f"{REF}: urban = base + 4", 0),
    ("ai", "site_radius_cap", 4.0, "tiles", f"{REF}: cap at 4", 0),
    ("ai", "site_retries", 20.0, "tries", f"{REF}: retry 20 times, radius += 1", 0),
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
    print("AI town sites SQLite migration ok (idempotent)")
