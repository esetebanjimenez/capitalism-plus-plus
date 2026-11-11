"""Idempotent migration: fix stale line numbers in `ref` citations of docs/gamelogic.md.

PR #89 inserted text above the cited passages, so the line numbers in these
citations went stale. Each new number was found by mapping the cited passage to
its current line (not a blanket offset):

- 558–585 Rating and throughput section -> 590–617
- 739–747 Fixed-credit mode -> 771–779
- 849 "Adds 10 training credits per visit." -> 881
- 963–970 R&D and Software R&D -> 1003–1010
- ~4008 Town tile row ("| Town | 13 |") -> ~4181

Only the numbers change; the rest of each citation stays as it was.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FOOTPRINT_REF = (
    "Game Designer, PR #50 (m2-ux-spec.md): visual only, sim town stays one tile; "
    "reference draws a town as one tile (gamelogic.md ~{line})"
)

# (table, old ref, new ref)
REFS = [
    (
        "rating_throughput",
        "docs/gamelogic.md 558–585 — rating efficiency and storage",
        "docs/gamelogic.md 590–617 — rating efficiency and storage",
    ),
    (
        "fixed_training_credits",
        "docs/gamelogic.md 739–747 — Crop Growing fixed credits",
        "docs/gamelogic.md 771–779 — Crop Growing fixed credits",
    ),
    (
        "fixed_training_credits",
        "docs/gamelogic.md 849 plus 739–747 — Raising visit reading, not Processing",
        "docs/gamelogic.md 881 plus 771–779 — Raising visit reading, not Processing",
    ),
    (
        "fixed_training_credits",
        "docs/gamelogic.md 739–747, 963–970 — shared R&D visit credits",
        "docs/gamelogic.md 771–779, 1003–1010 — shared R&D visit credits",
    ),
    (
        "fixed_training_credits",
        "docs/gamelogic.md 963–970 — shared Software Development visit credits",
        "docs/gamelogic.md 1003–1010 — shared Software Development visit credits",
    ),
    (
        "town_footprints",
        FOOTPRINT_REF.format(line=4008),
        FOOTPRINT_REF.format(line=4181),
    ),
]


def migrate(con: sqlite3.Connection) -> None:
    for table, old, new in REFS:
        con.execute(f"UPDATE {table} SET ref=? WHERE ref=?", (new, old))
    con.commit()
    for table, old, new in REFS:
        assert con.execute(f"SELECT count(*) FROM {table} WHERE ref=?", (old,)).fetchone()[0] == 0
        assert con.execute(f"SELECT count(*) FROM {table} WHERE ref=?", (new,)).fetchone()[0] > 0
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "src/capitalism/data/capitalism.db")
    con.execute("PRAGMA foreign_keys=ON")
    migrate(con)
    migrate(con)
    print("gamelogic ref lines SQLite migration ok (idempotent)")
