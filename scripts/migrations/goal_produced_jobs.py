"""Idempotent migration: which job types count toward the product goals.

The product types and product classes goals count products "being produced"
(gamelogic.md 3780-3781 gives only the labels). Game Designer call
(2026-11-10), confirmed by the Reverse Engineering Researcher's report on
CAPPLUS.EXE: a product type counts for a corp while at least one of its jobs is
set to make it; a class counts when any of its types does; buying, stocking and
reselling never count. Both goals read a per-corp counter at product+0x97+corp
(FUN_00033fe9 classes, FUN_00034056 types) changed only by job output setters.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PRODUCING = (
    "Crop Growing",
    "Livestock Raising",
    "Logging",
    "Manufacturing",
    "Mining",
    "Oil Extraction",
    "Software Development",
    "Software Production",
)

RULE_REF = (
    "Researcher report, CAPPLUS.EXE: product goals read a per-corp counter at "
    "product+0x97+corp (FUN_00033fe9 classes, FUN_00034056 types); only job output "
    "setters change it, each -1 for the old product. +1 observed in FUN_00054071 "
    "(manufacturing) and FUN_00057149 (raw-material extraction setup: product from the "
    "firm's natural resource via DAT_000b1c2f, reserve from the map tile; teardown "
    "FUN_000570e1 does the -1). Its callers FUN_0005e934/998/9fc read as Logging, Mine and "
    "Oil (inferred). +1 inferred, not observed, in FUN_00051ced (crop), FUN_000534b7 "
    "(livestock) and FUN_0005bdb8 (software). No writer found for livestock processing, "
    "so it does not count. Takeover moves counts to the buyer (FUN_000331fc); here counts "
    "follow firm ownership. No purchasing, sales or retail writer found"
)


def migrate(con: sqlite3.Connection) -> None:
    cols = {r[1] for r in con.execute("PRAGMA table_info(job_types)")}
    if "counts_as_produced" not in cols:
        con.execute(
            "ALTER TABLE job_types ADD COLUMN counts_as_produced INTEGER NOT NULL DEFAULT 0 "
            "CHECK(counts_as_produced IN(0,1))"
        )
    marks = ",".join("?" * len(PRODUCING))
    con.execute(f"UPDATE job_types SET counts_as_produced = (name IN ({marks}))", PRODUCING)
    con.execute(
        "UPDATE job_types SET provisional = CASE WHEN provisional='' THEN 'counts_as_produced' "
        "ELSE provisional||',counts_as_produced' END "
        "WHERE ','||provisional||',' NOT LIKE '%,counts_as_produced,%'"
    )
    con.execute(
        "INSERT INTO rules VALUES('scoring','product_goals_count_own_output',1,'flag (0 or 1)',?,1) "
        "ON CONFLICT(system,key) DO UPDATE SET value=excluded.value,units=excluded.units,"
        "ref=excluded.ref,provisional=1",
        (RULE_REF,),
    )
    n = con.execute("SELECT count(*) FROM job_types WHERE counts_as_produced=1").fetchone()[0]
    assert n == len(PRODUCING)
    con.commit()
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "src/capitalism/data/capitalism.db")
    con.execute("PRAGMA foreign_keys=ON")
    migrate(con)
    migrate(con)
    print("goal produced jobs SQLite migration ok (idempotent)")
