"""Idempotent migration: starting capital and setup-cost rules (gap audit C1-C4).

- corporations.player_initial_capital: default 10,000,000 at g_app+0x196
  (float 0x4b189680, decomp:4518), edited as "Initial Capital of Your
  Corporation" (decomp:7758); ref:19 agrees. Where native credits it to the
  corp is not traced, so the sim credits it as corp cash on creation.
- competitor_capital: v by Competitor Capital setting, FUN_0007916c
  (decomp:87774-87776), table 0xae090. Starting money =
  (v/2 + random(v/2)) * ai.capital_unit, with ai.capital_unit = 6,000,000/10.
  Native writes it to the CEO's wealth (+0x2c); the hand-off to corp cash is
  not traced, so the sim puts it in corp cash (provisional).
- Replaces ai.starting_capital_low.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CC_REF = "FUN_0007916c decomp:87774-87776, v table 0xae090 (setting DAT_000b1ecd); ref:199-210"
# setting: (name, v)
COMPETITOR_CAPITAL = {
    0: ("Low", 10),
    1: ("Moderate", 15),
    2: ("High", 20),
    3: ("Very High", 30),
    4: ("Extremely High", 60),
}
RULES = [
    (
        "corporations",
        "player_initial_capital",
        10_000_000.0,
        "dollars",
        (
            "g_app+0x196 default 0x4b189680 (decomp:4518), setup dialog decomp:7758; ref:19. "
            "Credited as corp cash on creation (native hand-off not traced)"
        ),
        1,
    ),
    (
        "ai",
        "capital_unit",
        600_000.0,
        "dollars per v",
        (
            "FUN_0007916c decomp:87774-87776: (v/2 + random(v/2)) * 6,000,000 / 10. "
            "Native credits the CEO's wealth; sim credits corp cash (hand-off not traced)"
        ),
        1,
    ),
    (
        "ai",
        "ai_cash_reset",
        1_000_000_000.0,
        "dollars",
        (
            "Government corp only: FUN_00030ffc decomp:27691-27693, vtable 0x3553c (audit A1). "
            "Competitors keep real cash; the sim has no Government corp, so this is unused"
        ),
        0,
    ),
]


def migrate(con: sqlite3.Connection) -> None:
    con.execute(
        "CREATE TABLE IF NOT EXISTS competitor_capital ("
        " setting INTEGER PRIMARY KEY CHECK(setting >= 0),"
        " name TEXT NOT NULL,"
        " v INTEGER NOT NULL CHECK(v > 0),"
        " ref TEXT NOT NULL, provisional TEXT NOT NULL DEFAULT '')"
    )
    marks = ",".join("?" * len(COMPETITOR_CAPITAL))
    con.execute(
        f"DELETE FROM competitor_capital WHERE setting NOT IN ({marks})", list(COMPETITOR_CAPITAL)
    )
    for setting, (name, v) in COMPETITOR_CAPITAL.items():
        con.execute(
            "INSERT INTO competitor_capital VALUES(?,?,?,?,'') "
            "ON CONFLICT(setting) DO UPDATE SET name=excluded.name, v=excluded.v, "
            "ref=excluded.ref, provisional=excluded.provisional",
            (setting, name, v, CC_REF),
        )
    for row in RULES:
        con.execute(
            "INSERT INTO rules VALUES(?,?,?,?,?,?) ON CONFLICT(system, key) DO UPDATE SET "
            "value=excluded.value, units=excluded.units, ref=excluded.ref, "
            "provisional=excluded.provisional",
            row,
        )
    con.execute(
        "DELETE FROM rules WHERE system='ai' AND key IN ('starting_capital_low', 'template_cost_estimate', 'asset_sale_rounds')"
    )
    con.commit()
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "src/capitalism/data/capitalism.db")
    con.execute("PRAGMA foreign_keys=ON")
    migrate(con)
    migrate(con)
    print("money setup SQLite migration ok (idempotent)")
