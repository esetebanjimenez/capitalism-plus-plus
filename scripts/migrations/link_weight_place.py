"""Idempotent migration: link weight bonus by place kind, not farm/non-farm (#351, #344 §5).

Native N7 (techspec 'Weight', lines 1307-1310) adds 50 to a link's weight unless the selling
firm sits on a town-core place kind (0x3008..0x300c, the urban range already in
towns.urban_kind_base/urban_variants). The old `weight_nonfarm` key read it as "non-farm".
Same value, new key and reference; no new scalars.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REF = "N7 techspec 'Weight' (lines 1307-1310): +50 unless place_kind in 0x3008..0x300c"


def migrate(con: sqlite3.Connection) -> None:
    con.execute("DELETE FROM rules WHERE system='links' AND key='weight_nonfarm'")
    con.execute(
        "INSERT INTO rules VALUES(?,?,?,?,?,?) ON CONFLICT(system, key) DO UPDATE SET "
        "value=excluded.value, units=excluded.units, ref=excluded.ref, "
        "provisional=excluded.provisional",
        ("links", "weight_off_core", 50.0, "weight", REF, 0),
    )
    con.commit()
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "src/capitalism/data/capitalism.db")
    con.execute("PRAGMA foreign_keys=ON")
    migrate(con)
    migrate(con)
    print("Link weight place-kind SQLite migration ok (idempotent)")
