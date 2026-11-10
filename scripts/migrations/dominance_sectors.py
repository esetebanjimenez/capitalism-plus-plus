"""Idempotent migration: firm type to sector mapping for sector dominance goals.

gamelogic.md *Sector dominance* says firms are grouped into four sectors by
business type but does not list which type is in which sector. The mapping
below is provisional until the Reverse Engineering Researcher confirms it.
Seaport has no sector.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REF = "Goals, victory conditions, and scoring; Sector dominance (mapping not in reference)"
SECTORS = {
    0: ("Retail", ("Department Store", "Restaurant")),
    1: (
        "Manufacturing and technology",
        ("Factory", "R&D Center", "Software Developer", "Software Publisher"),
    ),
    2: ("Natural resources", ("Farm", "Logging Camp", "Mine", "Oil Well")),
    3: ("Media", ("Television Station", "Radio Station", "Newspaper Publisher")),
}


def migrate(con: sqlite3.Connection) -> None:
    con.execute(
        "CREATE TABLE IF NOT EXISTS firm_sectors ("
        " firm_type INTEGER PRIMARY KEY REFERENCES firm_types(id),"
        " sector INTEGER NOT NULL CHECK(sector BETWEEN 0 AND 3),"
        " sector_name TEXT NOT NULL, ref TEXT NOT NULL, provisional TEXT NOT NULL DEFAULT '')"
    )
    for sector, (name, types) in SECTORS.items():
        for t in types:
            (tid,) = con.execute("SELECT id FROM firm_types WHERE name=?", (t,)).fetchone()
            con.execute(
                "INSERT INTO firm_sectors VALUES(?,?,?,?,'sector') ON CONFLICT(firm_type) DO UPDATE "
                "SET sector=excluded.sector, sector_name=excluded.sector_name, ref=excluded.ref, "
                "provisional=excluded.provisional",
                (tid, sector, name, REF),
            )
    con.execute(
        "INSERT INTO rules VALUES('scoring','dominance_tie_is_lead',0,'flag (0 or 1)',?,1) "
        "ON CONFLICT(system,key) DO UPDATE SET value=excluded.value,units=excluded.units,"
        "ref=excluded.ref,provisional=1",
        ("Sector dominance / Industry dominance: tie rule not in reference",),
    )
    con.commit()
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "src/capitalism/data/capitalism.db")
    con.execute("PRAGMA foreign_keys=ON")
    migrate(con)
    migrate(con)
    print("dominance sectors SQLite migration ok (idempotent)")
