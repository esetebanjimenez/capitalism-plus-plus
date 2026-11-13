"""Idempotent migration: create and populate the job_products table (audit D1).

Maps each producing job type to the products it can make. Trading jobs
(Purchasing, Inventory, Private Labelling, Sales, Import, Advertising)
are excluded — they take whatever product their source supplies.

Sources:
- Crop Growing: products with kind='crop' (gamelogic.md product catalog)
- Livestock Raising: products with kind='livestock'
- Livestock Processing: Leather, Milk, Wool + Eggs, Frozen Beef/Chicken/Pork/Lamb
- Logging: Timber (the only wood raw material)
- Mining: raw materials that are not Timber or Oil
- Oil Extraction: Oil
- Manufacturing: every product with a recipe
- R&D: every product with a recipe (tech levels apply to manufactured goods)
- Software Development: Software
- Software Production: Software
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

LIVESTOCK_PROCESSING_IDS = [23, 24, 25, 46, 47, 48, 49, 50]


def migrate(con: sqlite3.Connection) -> None:
    con.execute(
        "CREATE TABLE IF NOT EXISTS job_products ("
        " job_type INTEGER NOT NULL REFERENCES job_types(id),"
        " product_id INTEGER NOT NULL REFERENCES products(id),"
        " ref TEXT NOT NULL DEFAULT '',"
        " provisional INTEGER NOT NULL DEFAULT 0,"
        " PRIMARY KEY (job_type, product_id))"
    )

    rows: list[tuple[int, int, str, int]] = []

    # 1. Crop Growing (1): kind='crop'
    for (pid,) in con.execute("SELECT id FROM products WHERE kind='crop' ORDER BY id"):
        rows.append((1, pid, "gamelogic.md product catalog; kind=crop", 0))

    # 2. Livestock Raising (2): kind='livestock'
    for (pid,) in con.execute("SELECT id FROM products WHERE kind='livestock' ORDER BY id"):
        rows.append((2, pid, "gamelogic.md; kind=livestock", 0))

    # 3. Livestock Processing (3): semi-products + consumer meat/eggs
    for pid in LIVESTOCK_PROCESSING_IDS:
        rows.append((3, pid, "gamelogic.md livestock processing outputs", 0))

    # 4. Logging (4): Timber only
    rows.append((4, 8, "Timber is the only wood raw material", 0))

    # 8. Mining (8): raw materials except Timber (8) and Oil (6)
    for (pid,) in con.execute(
        "SELECT id FROM products WHERE kind='raw' AND id NOT IN (6, 8) ORDER BY id"
    ):
        rows.append((8, pid, "raw materials excluding Timber and Oil", 0))

    # 9. Oil Extraction (9): Oil only
    rows.append((9, 6, "Oil is the only petroleum raw material", 0))

    # 7. Manufacturing (7): every product with a recipe
    for (pid,) in con.execute("SELECT DISTINCT product_id FROM recipes ORDER BY product_id"):
        rows.append((7, pid, "recipes table; Manufacturing needs a recipe", 0))

    # 11. R&D (11): same as Manufacturing
    for (pid,) in con.execute("SELECT DISTINCT product_id FROM recipes ORDER BY product_id"):
        rows.append((11, pid, "R&D raises tech for manufactured products", 0))

    # 13. Software Development (13): Software only
    rows.append((13, 85, "Software (M1)", 0))

    # 14. Software Production (14): Software only
    rows.append((14, 85, "Software (M1)", 0))

    # Clear and repopulate
    con.execute("DELETE FROM job_products")
    con.executemany(
        "INSERT INTO job_products (job_type, product_id, ref, provisional) VALUES (?, ?, ?, ?)",
        rows,
    )
    con.commit()
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "src/capitalism/data/capitalism.db")
    con.execute("PRAGMA foreign_keys=ON")
    migrate(con)
    migrate(con)
    print(
        f"job_products migration ok ({con.execute('SELECT count(*) FROM job_products').fetchone()[0]} rows, idempotent)"
    )
