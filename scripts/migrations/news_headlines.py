"""Idempotent migration: one-line news headline templates, one per NewsType (#253).

docs/m2-ux-spec.md section 4: each news row shows a headline built from `news_type` and
`details`, naming the corporation when there is one. The wording is ours (plain English, no
figures); placeholders are filled by capitalism.news_text:
{corp}, {other_corp}, {firm_type}, {town}, {product}, {resource}.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REF = "docs/m2-ux-spec.md section 4 (our wording, #253)"

HEADLINES = [
    (1, "FIRM_OPENED", "{corp} opened a {firm_type} in {town}"),
    (2, "FIRM_CLOSED", "{corp} closed a {firm_type} in {town}"),
    (3, "BANK_LOAN", "{corp} took out a bank loan"),
    (4, "LOAN_REPAID", "{corp} repaid a bank loan"),
    (5, "SHARES_ISSUED", "{corp} issued new shares"),
    (6, "SHARE_TRADE", "{corp} traded shares of {other_corp}"),
    (7, "ANNUAL_DIVIDEND", "{corp} paid its annual dividend"),
    (8, "TENDER_OFFER", "{corp} made a tender offer for {other_corp}"),
    (9, "NEW_COMPETITOR", "{corp} entered the market"),
    (10, "BANKRUPTCY", "{corp} went bankrupt"),
    (11, "CONTROL_CHANGE", "{other_corp} took control of {corp}"),
    (12, "MERGER", "{corp} merged with {other_corp}"),
    (13, "PRICE_WAR", "{corp} started a price war on {product}"),
    (14, "INDUSTRY_DOMINANCE", "{corp} now dominates its industry"),
    (15, "CEO_RETIREMENT", "The CEO of {corp} retired"),
    (16, "CEO_SUCCESSION", "{corp} named a new CEO"),
    (17, "RND_INVENTION", "{corp} invented {product}"),
    (18, "PRODUCT_MADE_PUBLIC", "The technology for {product} is now public"),
    (19, "RESOURCE_EXHAUSTED", "A {resource} deposit near {town} ran out"),
    (20, "RESOURCE_DISCOVERED", "A {resource} deposit was found near {town}"),
    (21, "RESOURCE_ON_SITE", "{corp} found {resource} on its site"),
    (22, "CITY_FOUNDED", "{town} was founded"),
    (23, "LIVESTOCK_DISEASE", "Disease hit the livestock on {corp}'s farms"),
    (24, "BUILDING_DESTROYED", "A {firm_type} owned by {corp} was destroyed"),
    (25, "CROP_FAILURE", "Crops failed on {corp}'s farms"),
    (26, "RND_BREAKTHROUGH", "{corp} made a research breakthrough on {product}"),
    (27, "INVENTORY_LOSS", "A blackout spoiled stock at {corp}'s department stores"),
    (28, "ECONOMIC_DOWNTURN", "An economic downturn cut corporate cash"),
]


def migrate(con: sqlite3.Connection) -> None:
    con.execute(
        "CREATE TABLE IF NOT EXISTS news_headlines ("
        "news_type INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, template TEXT NOT NULL, "
        "ref TEXT NOT NULL, provisional TEXT NOT NULL DEFAULT '')"
    )
    con.executemany(
        "INSERT INTO news_headlines VALUES(?,?,?,?,'') ON CONFLICT(news_type) DO UPDATE SET "
        "name=excluded.name, template=excluded.template, ref=excluded.ref",
        [(i, n, t, REF) for i, n, t in HEADLINES],
    )
    con.execute(
        f"DELETE FROM news_headlines WHERE news_type NOT IN ({','.join('?' * len(HEADLINES))})",
        [i for i, _, _ in HEADLINES],
    )
    con.commit()
    assert con.execute("SELECT COUNT(*) FROM news_headlines").fetchone()[0] == len(HEADLINES)
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "src/capitalism/data/capitalism.db")
    con.execute("PRAGMA foreign_keys=ON")
    migrate(con)
    migrate(con)
    print("news headlines SQLite migration ok (idempotent)")
