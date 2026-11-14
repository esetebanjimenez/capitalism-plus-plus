"""Idempotent migration: product FREIGHT bulk factors from 1STD.SET (audit F2, #283).

Product +0x37 is the SET ITEM FREIGHT field (techspec "Freight rate", FUN_000785f1,
confirmed in PR #281). The values are copied from the parsed SET in
src/capitalism/data/1std_set.db (ITEM.FREIGHT, matched by NAME) and agree with the
techspec table. Livestock, Rubber Plant and Sugar Cane have no FREIGHT field (they
aren't shipped between firms), so they stay 0, which is Observed too. Software isn't in
the SET's ITEM table and keeps its provisional value.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "src/capitalism/data"
NOTE = "freight: 1STD.SET ITEM.FREIGHT (techspec freight rate, FUN_000785f1)"


def migrate(con: sqlite3.Connection) -> None:
    sset = sqlite3.connect(DATA / "1std_set.db")
    freight = {name: f for name, f in sset.execute('SELECT NAME, FREIGHT FROM "ITEM"')}
    sset.close()
    rows = con.execute("SELECT id, name, ref, provisional FROM products").fetchall()
    for pid, name, ref, prov in rows:
        if name not in freight:
            continue
        value = float(freight[name] or 0)
        fields = [f for f in prov.split(",") if f and f != "freight"]
        if NOTE not in ref:
            ref = f"{ref}; {NOTE}" if ref else NOTE
        con.execute(
            "UPDATE products SET freight=?, ref=?, provisional=? WHERE id=?",
            (value, ref, ",".join(fields), pid),
        )
    con.commit()
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


if __name__ == "__main__":
    con = sqlite3.connect(DATA / "capitalism.db")
    migrate(con)
    migrate(con)
    print("product freight SQLite migration ok (idempotent)")
