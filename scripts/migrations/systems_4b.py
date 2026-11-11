"""Idempotent systems-4b SQLite migration from the pristine 4a schema."""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MIGRATION_SQL = """
PRAGMA foreign_keys = OFF;
PRAGMA legacy_alter_table = ON;
-- Rebuild products with an explicit provisional research-year field.
ALTER TABLE products RENAME TO products_4a;
CREATE TABLE products (
 id INTEGER PRIMARY KEY,code TEXT NOT NULL UNIQUE,name TEXT NOT NULL UNIQUE,
 class_id INTEGER NOT NULL REFERENCES product_classes(id),kind TEXT NOT NULL,unit TEXT NOT NULL,
 base_price REAL NOT NULL CHECK(base_price>0),base_cost REAL NOT NULL CHECK(base_cost>=0),freight REAL NOT NULL DEFAULT 0 CHECK(freight>=0),spending_usd REAL NOT NULL DEFAULT 1 CHECK(spending_usd>0),
 demand_per_1000 REAL NOT NULL CHECK(demand_per_1000>=0),luxury INTEGER NOT NULL,necessity INTEGER NOT NULL,
 tech_importance INTEGER NOT NULL,w_price INTEGER NOT NULL,w_quality INTEGER NOT NULL,w_brand INTEGER NOT NULL,
 base_tech_level INTEGER NOT NULL,base_capacity REAL NOT NULL CHECK(base_capacity>=1),
 importable INTEGER NOT NULL CHECK(importable IN(0,1)),plant_month INTEGER,grow_months INTEGER,
 suit_climate INTEGER,suit_moisture INTEGER,ref TEXT NOT NULL,provisional TEXT NOT NULL DEFAULT '',
 tech_year INTEGER NOT NULL DEFAULT 0 CHECK(tech_year BETWEEN 0 AND 100));
INSERT INTO products(id,code,name,class_id,kind,unit,base_price,base_cost,freight,spending_usd,demand_per_1000,
 luxury,necessity,tech_importance,w_price,w_quality,w_brand,base_tech_level,base_capacity,importable,
 plant_month,grow_months,suit_climate,suit_moisture,ref,provisional,tech_year)
SELECT id,code,name,class_id,kind,unit,base_price,base_cost,0,base_price,demand_per_1000,luxury,necessity,
 tech_importance,w_price,w_quality,w_brand,base_tech_level,base_capacity,importable,plant_month,
 grow_months,suit_climate,suit_moisture,ref,provisional,0 FROM products_4a;
DROP TABLE products_4a;
ALTER TABLE firm_types ADD COLUMN government INTEGER NOT NULL DEFAULT 0 CHECK(government IN(0,1));
UPDATE firm_types SET max_slots=0 WHERE name='Seaport';
UPDATE firm_types SET provisional=CASE WHEN provisional='' THEN 'max_slots' ELSE provisional||',max_slots' END WHERE name='Seaport';
UPDATE products SET tech_year=CASE tech_importance WHEN 3 THEN 0 WHEN 6 THEN 15 WHEN 10 THEN 30
 WHEN 12 THEN 45 WHEN 15 THEN 60 WHEN 20 THEN 75 ELSE 0 END;
UPDATE products SET provisional=CASE WHEN provisional='' THEN 'tech_year' ELSE provisional||',tech_year' END;
UPDATE products SET freight=70 WHERE name IN('Wheat','Flour');
UPDATE products SET freight=50 WHERE name='Bread';
UPDATE products SET spending_usd=0.30 WHERE name='Wheat';
UPDATE products SET provisional=CASE WHEN provisional='' THEN 'freight' ELSE provisional||',freight' END WHERE name NOT IN ('Wheat','Flour','Bread');
INSERT INTO products(id,code,name,class_id,kind,unit,base_price,base_cost,freight,spending_usd,demand_per_1000,
 luxury,necessity,tech_importance,w_price,w_quality,w_brand,base_tech_level,base_capacity,importable,
 ref,provisional,tech_year) VALUES(85,'SOFTWARE','Software',18,'software','copy',100,5,0,100,0.1,
 0,0,0,30,40,30,0,1000,0,'design.md slice 4b — provisional M1 software content',
 'name,class_id,unit,base_price,base_cost,freight,spending_usd,demand_per_1000,luxury,necessity,tech_importance,w_price,w_quality,w_brand,base_tech_level,base_capacity,importable,tech_year',0);
CREATE TABLE livestock_yields(livestock_id INTEGER PRIMARY KEY REFERENCES products(id),
 product_id INTEGER NOT NULL REFERENCES products(id),yield_factor REAL NOT NULL CHECK(yield_factor>0),
 input_ratio REAL NOT NULL CHECK(input_ratio>0),units TEXT NOT NULL,ref TEXT NOT NULL,
 provisional INTEGER NOT NULL CHECK(provisional IN(0,1)));
INSERT INTO livestock_yields VALUES
 (19,23,20,1,'output units / input unit / day','M1 provisional livestock yield and conversion; source yield missing',1),
 (20,24,1,1,'output units / input unit / day','M1 provisional livestock yield and conversion; source yield missing',1),
 (22,25,40,1,'output units / input unit / day','M1 provisional livestock yield and conversion; source yield missing',1);
CREATE TABLE research_durations(tech_year_bucket INTEGER PRIMARY KEY CHECK(tech_year_bucket BETWEEN 0 AND 6),
 months INTEGER NOT NULL CHECK(months>=0),units TEXT NOT NULL,ref TEXT NOT NULL,
 provisional INTEGER NOT NULL CHECK(provisional IN(0,1)));
INSERT INTO research_durations VALUES
 (0,0,'months','design.md slice 4b R&D duration table',0),
 (1,6,'months','design.md slice 4b R&D duration table',0),
 (2,12,'months','design.md slice 4b R&D duration table',0),
 (3,24,'months','design.md slice 4b R&D duration table',0),
 (4,36,'months','design.md slice 4b R&D duration table',0),
 (5,60,'months','design.md slice 4b R&D duration table',0),
 (6,120,'months','design.md slice 4b R&D duration table',0);
CREATE TABLE advertisements(id INTEGER PRIMARY KEY AUTOINCREMENT,firm_id INTEGER NOT NULL,
 slot INTEGER NOT NULL,product_id INTEGER NOT NULL REFERENCES products(id),budget REAL NOT NULL CHECK(budget>=0),
 brand REAL NOT NULL CHECK(brand>=0),media_type INTEGER NOT NULL DEFAULT 11,targets TEXT NOT NULL DEFAULT '',
 month INTEGER NOT NULL DEFAULT 0,provisional INTEGER NOT NULL DEFAULT 1 CHECK(provisional IN(0,1)));
-- Repair the previous migration's stale firm_types_old foreign key.
CREATE TABLE firm_job_allowed_4b (firm_type INTEGER NOT NULL REFERENCES firm_types(id),
 job_type INTEGER NOT NULL REFERENCES job_types(id),ref TEXT NOT NULL,
 provisional INTEGER NOT NULL CHECK(provisional IN(0,1)),PRIMARY KEY(firm_type,job_type));
INSERT INTO firm_job_allowed_4b SELECT * FROM firm_job_allowed;
DROP TABLE firm_job_allowed;
ALTER TABLE firm_job_allowed_4b RENAME TO firm_job_allowed;
DELETE FROM rules WHERE system IN ('research','advertising','software');
INSERT OR IGNORE INTO rules VALUES('jobs','freight_distance_value_divisor',100,'currency-distance divisor','decompiled FUN_000785f1 review (Esteban 2026-11-06)',0);
INSERT OR IGNORE INTO rules VALUES('jobs','freight_multiplier',0.5,'multiplier','decompiled FUN_000785f1 review (Esteban 2026-11-06)',0);
INSERT OR IGNORE INTO rules VALUES('jobs','freight_floor_usd_per_unit',0.01,'USD per unit only if raw rate == 0','decompiled FUN_000785f1 review (Esteban 2026-11-06)',0);
INSERT OR IGNORE INTO rules VALUES('jobs','corp_training_budget_default',10,'training budget','decompiled training review (2026-11-06)',0);
INSERT OR IGNORE INTO rules VALUES('jobs','training_expense_divisor',100,'USD divisor','decompiled training review (2026-11-06)',0);
UPDATE rules SET ref='decompiled FUN_000785f1 review (Esteban 2026-11-06)', provisional=0 WHERE system='jobs' AND key IN('freight_distance_value_divisor','freight_multiplier','freight_floor_usd_per_unit','corp_training_budget_default','training_expense_divisor');
"""


def _rule(con: sqlite3.Connection, system: str, args: tuple[str, float, str, str]) -> None:
    con.execute("INSERT INTO rules VALUES(?,?,?,?,?,1)", (system, *args))


def migrate(con: sqlite3.Connection) -> None:
    """Apply exactly once to a pristine 4a database, then safely revalidate."""
    products = {r[1] for r in con.execute("PRAGMA table_info(products)")}
    firms = {r[1] for r in con.execute("PRAGMA table_info(firm_types)")}
    if "tech_year" not in products:
        if "government" in firms:
            raise RuntimeError("4b migration must start with a pristine 4a database")
        con.executescript(MIGRATION_SQL)
        for args in [
            (
                "media_min_revenue",
                10000,
                "usd / month",
                "design.md slice 4b media partner threshold",
            ),
            ("media_audience_min", 10, "audience", "design.md slice 4b provisional audience"),
            ("media_government_max", 39, "audience", "design.md slice 4b government audience"),
            (
                "media_audience_population_div",
                10000,
                "people / audience point",
                "design.md slice 4b provisional audience",
            ),
            ("media_audience_cap", 100, "audience", "design.md slice 4b provisional audience"),
            (
                "media_audience_adjust_rate",
                0.1,
                "fraction / month",
                "M1 provisional gradual audience adjustment",
            ),
            (
                "ad_revenue_fraction",
                0.1,
                "fraction of previous month revenue",
                "design.md slice 4b provisional budget rate",
            ),
            (
                "ad_campaign_every_days",
                60,
                "days",
                "design.md slice 4b advertising campaign stagger",
            ),
            ("ad_tech_min_exclusive", 14, "tech level", "design.md slice 4b no ads at tech <= 14"),
            (
                "software_project_months",
                6,
                "months",
                "design.md slice 4b software one level project",
            ),
            ("software_copy_quality", 50, "quality", "M1 provisional software initial quality"),
            (
                "software_copy_cost_per_day",
                0,
                "usd per copy-unit day",
                "M1 no additional daily copy cost; wages already posted once daily",
            ),
        ]:
            _rule(con, "advertising" if args[0].startswith(("ad_", "media_")) else "software", args)
        for args in [
            (
                "days_per_project_month",
                30,
                "days / month",
                "design.md slice 4b project elapsed time",
            ),
            (
                "manager_skill_divisor",
                2,
                "divisor",
                "design.md slice 4b manufacturing skill provisional",
            ),
            ("max_technology", 100, "technology", "design.md slice 4b completed sentinel"),
            (
                "tech_year_divisor",
                15,
                "tech years / duration bucket",
                "design.md slice 4b R&D duration formula",
            ),
        ]:
            _rule(con, "research", args)
    con.execute("DELETE FROM rules WHERE key='freight_rate'")
    con.execute("UPDATE rules SET key='freight_distance_value_divisor' WHERE key='freight_rate'")
    con.execute("UPDATE rules SET key='freight_multiplier' WHERE key='freight_rate'")
    con.execute("UPDATE rules SET key='freight_floor_usd_per_unit' WHERE key='freight_rate'")
    con.execute(
        "UPDATE rules SET key='freight_distance_value_divisor' WHERE key='freight_distance_divisor'"
    )
    con.execute("UPDATE rules SET key='training_expense_divisor' WHERE key='training_divisor'")
    con.execute("UPDATE rules SET key='training_expense_divisor' WHERE key='training_constant'")
    for key, value, units, ref in [
        (
            "freight_distance_value_divisor",
            100.0,
            "currency-distance divisor",
            "decompiled FUN_000785f1 review (Esteban 2026-11-06)",
        ),
        (
            "freight_multiplier",
            0.5,
            "multiplier",
            "decompiled FUN_000785f1 review (Esteban 2026-11-06)",
        ),
        (
            "freight_floor_usd_per_unit",
            0.01,
            "USD per unit only if raw rate == 0",
            "decompiled FUN_000785f1 review (Esteban 2026-11-06)",
        ),
        (
            "corp_training_budget_default",
            10.0,
            "training budget",
            "decompiled training review (2026-11-06)",
        ),
        (
            "training_expense_divisor",
            100.0,
            "USD divisor",
            "decompiled training review (2026-11-06)",
        ),
    ]:
        con.execute(
            "UPDATE rules SET value=?,units=?,ref=?,provisional=0 WHERE system='jobs' AND key=?",
            (value, units, ref, key),
        )
        assert con.execute("SELECT changes()").fetchone()[0] == 1, key
    con.execute("PRAGMA legacy_alter_table = OFF")
    # Repair a legacy mapping's stale parent left by the old 4a rename migration.
    schema = con.execute("SELECT sql FROM sqlite_master WHERE name='firm_job_allowed'")
    if next((r[0] for r in schema if "firm_types_old" in r[0]), None):
        con.execute("PRAGMA foreign_keys=OFF")
        cols = [r[1] for r in con.execute("PRAGMA table_info(firm_job_allowed)")]
        q = ",".join(cols)
        con.execute(
            "CREATE TABLE firm_job_allowed_fixed (firm_type INTEGER NOT NULL REFERENCES firm_types(id), job_type INTEGER NOT NULL REFERENCES job_types(id), ref TEXT NOT NULL, provisional INTEGER NOT NULL CHECK(provisional IN(0,1)), PRIMARY KEY(firm_type,job_type))"
        )
        con.execute(f"INSERT INTO firm_job_allowed_fixed({q}) SELECT {q} FROM firm_job_allowed")
        con.execute("DROP TABLE firm_job_allowed")
        con.execute("ALTER TABLE firm_job_allowed_fixed RENAME TO firm_job_allowed")
    # Only the bread chain's SPENDING values are recovered; the base_price fill is provisional.
    con.execute(
        "UPDATE products SET provisional=CASE WHEN provisional='' THEN 'spending_usd' "
        "ELSE provisional||',spending_usd' END WHERE name NOT IN ('Wheat','Flour','Bread') "
        "AND instr(provisional,'spending_usd')=0"
    )
    # Resolved expanded reference: job training_factor has no confirmed monthly-growth mapping;
    # the separate budget × wage / 100 expense remains authoritative.
    con.execute(
        "UPDATE job_types SET units=replace(units,'% of salary (training)',"
        "'monthly skill-growth factor (training)')"
    )
    # The one-off development draft marked Seaport a government firm; it is infrastructure.
    con.execute("UPDATE firm_types SET government=0 WHERE name='Seaport'")
    con.execute("UPDATE firm_types SET provisional='max_slots' WHERE name='Seaport'")
    con.execute(
        "UPDATE firm_types SET provisional=CASE WHEN provisional='' THEN 'government' ELSE provisional||',government' END WHERE name!='Seaport' AND instr(provisional,'government')=0"
    )
    # Expanded reference: rating lookup and genuine work-credit progression.
    con.execute(
        "CREATE TABLE IF NOT EXISTS rating_throughput("
        "rating INTEGER PRIMARY KEY CHECK(rating BETWEEN 1 AND 9),"
        "efficiency_pct REAL NOT NULL CHECK(efficiency_pct>0),"
        "storage_mult REAL NOT NULL CHECK(storage_mult>0),"
        "ref TEXT NOT NULL, provisional INTEGER NOT NULL CHECK(provisional IN(0,1)))"
    )
    con.executemany(
        "INSERT INTO rating_throughput VALUES(?,?,?,'docs/gamelogic.md 590–617 — rating efficiency and storage',0) "
        "ON CONFLICT(rating) DO UPDATE SET efficiency_pct=excluded.efficiency_pct,"
        "storage_mult=excluded.storage_mult,ref=excluded.ref,provisional=0",
        [
            (i, eff, cap)
            for i, (eff, cap) in enumerate(
                zip(
                    (100, 130, 160, 200, 250, 300, 360, 430, 500),
                    (8, 10, 14, 16, 20, 24, 30, 35, 40),
                    strict=True,
                ),
                1,
            )
        ],
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS fixed_training_credits("
        "job_type INTEGER PRIMARY KEY REFERENCES job_types(id),"
        "base_daily REAL NOT NULL CHECK(base_daily>0),"
        "ref TEXT NOT NULL, provisional INTEGER NOT NULL CHECK(provisional IN(0,1)))"
    )
    con.executemany(
        "INSERT INTO fixed_training_credits VALUES(?,?,?,?) "
        "ON CONFLICT(job_type) DO UPDATE SET base_daily=excluded.base_daily,"
        "ref=excluded.ref, provisional=excluded.provisional",
        [
            (1, 20, "docs/gamelogic.md 771–779 — Crop Growing fixed credits", 0),
            (
                2,
                10,
                "docs/gamelogic.md 881 plus 771–779 — Raising visit reading, not Processing",
                1,
            ),
            (11, 14, "docs/gamelogic.md 771–779, 1003–1010 — shared R&D visit credits", 0),
            (
                13,
                14,
                "docs/gamelogic.md 1003–1010 — shared Software Development visit credits",
                0,
            ),
        ],
    )
    # The missing original budget/education mapping is neutral for M1 at defaults.
    for key, value, units in [
        ("training_credit_budget_divisor", 10, "budget-value / divisor; budget10 neutral"),
        ("training_credit_education", 100, "global fallback education; no native field recovered"),
        ("training_credit_education_divisor", 100, "education / divisor; fallback100 neutral"),
    ]:
        con.execute(
            "INSERT INTO rules VALUES('jobs',?,?,?,?,1) "
            "ON CONFLICT(system,key) DO UPDATE SET value=excluded.value,units=excluded.units,"
            "ref=excluded.ref,provisional=1",
            (
                key,
                value,
                units,
                "docs/design.md slice 4 call 6 (PR22 d012404) — provisional neutral credit scaling",
            ),
        )
    con.execute(
        "DELETE FROM rules WHERE system='jobs' AND key IN "
        "('train_step','train_threshold','train_hi','train_lo','eff_base','eff_per_rating','eff_min','eff_max')"
    )
    con.execute(
        "UPDATE job_types SET units=replace(units,'monthly skill-growth factor (training)',"
        " 'daily-credit input (role unresolved)') WHERE instr(units,'monthly skill-growth factor')>0"
    )
    con.commit()
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "src/capitalism/data/capitalism.db")
    con.execute("PRAGMA foreign_keys=ON")
    migrate(con)
    migrate(con)
    print("systems 4b SQLite migration ok (idempotent)")
