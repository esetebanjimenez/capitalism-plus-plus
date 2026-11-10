"""Idempotent migration: firm type to sector mapping for sector dominance goals.

gamelogic.md *Sector dominance* groups firms into four sectors by business type
but does not list them. The mapping below is the Reverse Engineering
Researcher's report from CAPPLUS.EXE (1995-97 build): FUN_00026f10 tests the
firm type code at firm+0. Native sector slots 1-4 are stored here as 0-3.
Firm type ids match the native type codes. The other seven types (R&D Center,
both software firms, Restaurant, the three media firms) and Seaport have no
sector. Native sector names were not found, so the names are provisional.

Ties (FUN_00026e8c per sector, FUN_00027085 per product type): corporation
slots are scanned in order and the leader is replaced only by a strictly
higher share, so a tie goes to the lowest slot; a share of 0 has no leader.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REF = (
    "Researcher report: CAPPLUS.EXE FUN_00026f10 (type code at firm+0); "
    "native sector N stored as N-1; names provisional"
)
SECTORS = {
    0: ("Department stores", ("Department Store",)),
    1: ("Factories", ("Factory",)),
    2: ("Farms", ("Farm",)),
    3: ("Natural resources", ("Logging Camp", "Mine", "Oil Well")),
}
TIE_REF = (
    "Researcher report: CAPPLUS.EXE FUN_00026e8c (sector) and FUN_00027085 (product type) "
    "scan corp slots in order, replace the leader only on a strictly higher share; "
    "share 0 has no leader. FUN_0002713c: industry needs the lead in every product type. "
    "Native player slot is a variable (DAT_000b1aab, set by FUN_000214eb, the hot-seat "
    "picker); the single-player slot is unconfirmed. Here the player is corp 0, created "
    "before any AI corp, so in this build the player wins ties"
)


def migrate(con: sqlite3.Connection) -> None:
    con.execute(
        "CREATE TABLE IF NOT EXISTS firm_sectors ("
        " firm_type INTEGER PRIMARY KEY REFERENCES firm_types(id),"
        " sector INTEGER NOT NULL CHECK(sector BETWEEN 0 AND 3),"
        " sector_name TEXT NOT NULL, ref TEXT NOT NULL, provisional TEXT NOT NULL DEFAULT '')"
    )
    keep = [t for _, types in SECTORS.values() for t in types]
    marks = ",".join("?" * len(keep))
    con.execute(
        "DELETE FROM firm_sectors WHERE firm_type NOT IN "
        f"(SELECT id FROM firm_types WHERE name IN ({marks}))",
        keep,
    )
    for sector, (name, types) in SECTORS.items():
        for t in types:
            (tid,) = con.execute("SELECT id FROM firm_types WHERE name=?", (t,)).fetchone()
            con.execute(
                "INSERT INTO firm_sectors VALUES(?,?,?,?,'sector_name') ON CONFLICT(firm_type) DO UPDATE "
                "SET sector=excluded.sector, sector_name=excluded.sector_name, ref=excluded.ref, "
                "provisional=excluded.provisional",
                (tid, sector, name, REF),
            )
    con.execute("DELETE FROM rules WHERE system='scoring' AND key='dominance_tie_is_lead'")
    con.execute(
        "INSERT INTO rules VALUES('scoring','dominance_tie_lowest_slot',1,'flag (0 or 1)',?,0) "
        "ON CONFLICT(system,key) DO UPDATE SET value=excluded.value,units=excluded.units,"
        "ref=excluded.ref,provisional=0",
        (TIE_REF,),
    )
    con.execute(
        "INSERT INTO rules VALUES('scoring','sector_share_window_months',1,'months',?,1) "
        "ON CONFLICT(system,key) DO UPDATE SET value=excluded.value,units=excluded.units,"
        "ref=excluded.ref,provisional=1",
        (
            (
                "Researcher report: native sums 12 floats per firm from firm+0x8c (read as a "
                "12-month history, unconfirmed) and rounds the share to a whole percent capped "
                "at 100 with an unknown formula; we use last month's sales revenue, unrounded"
            ),
        ),
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
