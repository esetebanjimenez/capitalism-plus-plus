"""Golden tests for systems 3, 4a and 5 (docs/design.md slices 3–5)."""

from __future__ import annotations

import hashlib
import math
import re
import sqlite3
from pathlib import Path

import pytest

from capitalism import Sim
from capitalism.catalog import Catalog, compute_availability, daily_demand, nec_lux
from capitalism.firms import Farm, decode_links, encode_links
from capitalism.jobs import (
    CropGrowing,
    Extraction,
    Manufacturing,
    cycle_quality,
    job_wage_day,
)
from capitalism.links import link_score, score_shares
from capitalism.scenario import (
    CROP,
    DEPARTMENT_STORE,
    FACTORY,
    FARM,
    IMPORT,
    MANUFACTURING,
    PURCHASING,
    SALES,
    SEAPORT,
    bread_town,
    build_bread_chain,
    chain_month_profit,
    find_site,
)
from capitalism.tables import JOB_RULES, LINK_RULES, PRODUCT_RULES, db_path

ROOT = Path(__file__).resolve().parents[1]


def _db() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db_path()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


# --- schema --------------------------------------------------------------------------


def test_schema_uses_rules_table_and_ref_columns():
    con = _db()
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "rules" in tables and "rule_values" not in tables
    for t in tables:
        cols = {r[1] for r in con.execute(f"PRAGMA table_info({t})")}
        assert "reference" not in cols, t
    rule_cols = [r[1] for r in con.execute("PRAGMA table_info(rules)")]
    assert rule_cols == ["system", "key", "value", "units", "ref", "provisional"]


def test_unemployment_drift_is_provisional_and_swing_is_reference():
    con = _db()
    for r in con.execute("SELECT drift_provisional, swing_provisional FROM unemployment_drift"):
        assert (r[0], r[1]) == (1, 0)
    text = (ROOT / "docs" / "rules.md").read_text(encoding="utf-8")
    section = text.split("## Unemployment drift by climate")[1].split("\n## ")[0]
    rows = [ln for ln in section.splitlines() if ln.startswith("| ") and ln[2].isdigit()]
    assert len(rows) == 5
    for ln in rows:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        assert cells[2].endswith("**provisional**"), ln  # drift
        assert "provisional" not in cells[3], ln  # swing


# --- slice 3: catalog ------------------------------------------------------------------


def test_catalog_counts_and_checks():
    con = _db()
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 84
    assert con.execute("SELECT COUNT(*) FROM product_classes").fetchone()[0] == 20
    for r in con.execute("SELECT * FROM products"):
        s = r["w_price"] + r["w_quality"] + r["w_brand"]
        assert s == 100 or (s == 0 and r["demand_per_1000"] == 0), r["name"]
        assert 0 <= r["luxury"] <= 9 and 0 <= r["necessity"] <= 9
    assert con.execute("SELECT COUNT(*) FROM recipes").fetchone()[0] == 54
    assert con.execute("SELECT COUNT(*) FROM rnd_prereqs").fetchone()[0] == 9
    orphans = con.execute(
        "SELECT COUNT(*) FROM recipe_inputs WHERE input_id NOT IN (SELECT id FROM products) "
        "OR product_id NOT IN (SELECT product_id FROM recipes)"
    ).fetchone()[0]
    assert orphans == 0
    over = con.execute(
        "SELECT product_id FROM recipe_inputs GROUP BY product_id HAVING SUM(quality_weight) >= 100"
    ).fetchall()
    assert over == []
    assert (
        con.execute(
            "SELECT COUNT(*) FROM recipes WHERE product_id NOT IN (SELECT product_id FROM recipe_inputs)"
        ).fetchone()[0]
        == 0
    )
    # Class counts match the reference table.
    counts = dict(
        con.execute(
            "SELECT c.code, COUNT(*) FROM products p JOIN product_classes c "
            "ON c.id = p.class_id GROUP BY c.code"
        ).fetchall()
    )
    assert counts["RAW"] == 8 and counts["SEMI"] == 12 and counts["ELEAPP"] == 7
    # Printed reference values are not flagged; fills are.
    bread = con.execute("SELECT * FROM products WHERE name = 'Bread'").fetchone()
    assert (bread["base_price"], bread["demand_per_1000"]) == (1.5, 10.0)
    assert "base_price" not in bread["provisional"].split(",")
    assert "base_capacity" in bread["provisional"].split(",")


def test_wheat_flour_bread_chain_rows():
    cat = Catalog()
    wheat, flour, bread = cat["Wheat"], cat["Flour"], cat["Bread"]
    assert wheat.kind == "crop" and wheat.row.importable
    fr, br = cat.recipe(flour), cat.recipe(bread)
    assert fr is not None and br is not None
    assert (fr.output_qty, fr.speed_pct, fr.skill_weight) == (1, 100, 30)
    assert [(i.input_id, i.qty, i.quality_weight) for i in fr.inputs] == [(wheat.id, 1, 70)]
    assert (br.output_qty, br.speed_pct, br.skill_weight) == (10, 100, 60)
    assert [(i.input_id, i.qty, i.quality_weight) for i in br.inputs] == [(flour.id, 9, 40)]


def _parse_recipes_md() -> dict[str, tuple[int, int, list[tuple[str, int, int]]]]:
    text = (ROOT / "docs" / "recipes.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    out = {}
    pat = r"\*\*(.+?)\*\* \((\d+) units\)(?:\s+\(speed: (\d+)%\))?\n\n\|.*\n\|.*\n((?:\|.*\n)+)"
    for m in re.finditer(pat, text):
        ins = []
        for row in m.group(4).strip().splitlines():
            cells = [c.strip() for c in row.strip("|").split("|")]
            if not cells[0].startswith("*"):
                ins.append((cells[0], int(cells[1]), int(cells[2].rstrip("%"))))
        out[m.group(1)] = (int(m.group(2)), int(m.group(3) or 100), sorted(ins))
    return out


def test_db_recipes_match_docs_recipes_md():
    doc = _parse_recipes_md()
    assert len(doc) == 54
    cat = Catalog()
    db = {}
    for pid, rec in cat.recipes.items():
        ins = sorted((cat.by_id[i.input_id].name, i.qty, i.quality_weight) for i in rec.inputs)
        db[cat.by_id[pid].name] = (rec.output_qty, rec.speed_pct, ins)
    assert db == doc


def test_bread_cycle_quality_flour_80_skill_50_is_62():
    cat = Catalog()
    bread = cat["Bread"]
    rec = cat.recipe(bread)
    assert rec is not None
    assert cycle_quality(rec, {cat["Flour"].id: 80.0}, 50.0) == pytest.approx(62.0)


def test_bread_demand_in_640k_town():
    sim, town = bread_town(1, 640_000)
    bread = sim.economy.catalog["Bread"]
    assert town.consumer_spending == 100
    nl = nec_lux(bread.row, town.per_capita_gnp / 20_000)
    assert round(daily_demand(bread, town), 1) == round(6_400 * nl, 1)
    assert round(sim.economy.town_market(town, "Bread").demand_per_day, 1) == 6080.0


def test_availability_is_recursive():
    cat = Catalog()
    wheat, flour, bread = cat["Wheat"], cat["Flour"], cat["Bread"]
    assert bread.state.available
    off = compute_availability(cat.products, cat.recipes, frozenset({wheat.id}))
    assert not off[bread.id] and not off[flour.id]
    no_flour = {k: v for k, v in cat.recipes.items() if k != flour.id}
    assert bread.id in no_flour
    assert not compute_availability(cat.products, no_flour)[bread.id]


def test_setup_jitter_is_reproducible_seed_1():
    sim = Sim(seed=1)
    blob = ",".join(
        f"{p.state.tech_level}:{p.state.score_jitter}" for p in sim.economy.catalog.products
    )
    assert hashlib.sha256(blob.encode()).hexdigest() == (
        "5abce68c0dd2a0ba8301e8ee5fa5e14c2f2c83064dd0d2ece76fe62cad0c8a79"
    )
    for p in sim.economy.catalog.products:
        assert p.state.tech_level >= 0
        assert abs(p.state.tech_level - p.row.base_tech_level) <= 4 or p.state.tech_level == 0


# --- slice 4: firms and jobs -------------------------------------------------------------


def test_wages_per_job_at_labor_100_thirty_days():
    # design.md golden: Manufacturing (24) $1,600, Purchasing (4) $266, Sales (8) $533.
    assert job_wage_day(24, 100, 30) == 1600
    assert job_wage_day(4, 100, 30) == 266
    assert job_wage_day(8, 100, 30) == 533


def test_wages_training_and_overhead_post_to_their_categories():
    sim, town = bread_town(1)
    eco = sim.economy
    x, y = find_site(sim, town)
    f = eco.build_firm(FACTORY, eco.add_corp("T"), x, y, town)
    f.add_job(1, MANUFACTURING, eco.catalog["Flour"])
    # January: first partial month of overhead posted at build, all 31 days.
    assert f.ledger.month[2] == pytest.approx(100000 / 12)
    sim.advance_day()
    wage = job_wage_day(24, 100, 31)
    assert f.ledger.month[1] == wage
    assert f.ledger.month[3] == pytest.approx(wage * 10 / 100)  # training_factor 10
    while sim.calendar.month == 1:
        sim.advance_day()
    assert f.ledger.month[2] == pytest.approx(100000 / 12)  # Feb overhead, ÷ 12


def test_base_capacity_is_value_per_day_over_price():
    k = PRODUCT_RULES.capacity_value_per_day
    for p in Catalog().products:
        assert p.row.base_capacity == max(1, round(k / p.row.base_price)), p.name


def test_slot_bitmask_decodes():
    mask = encode_links([(0, 1), (1, 2), (4, 7)])
    assert mask == 0b1000000011
    assert decode_links(mask) == [(0, 1), (1, 2), (4, 7)]
    assert len(decode_links((1 << 20) - 1)) == 20


def test_firm_rejects_jobs_it_cannot_hold():
    sim, town = bread_town(1)
    eco = sim.economy
    x, y = find_site(sim, town)
    farm = eco.build_firm(FARM, eco.add_corp("T"), x, y, town)
    assert isinstance(farm, Farm)
    with pytest.raises(ValueError):
        farm.add_job(0, MANUFACTURING, eco.catalog["Flour"])
    x, y = find_site(sim, town)
    with pytest.raises(NotImplementedError):
        eco.build_firm(11, None, x, y, town)  # Television Station is 4b


def test_wheat_farm_fills_in_season():
    sim, town = bread_town(1)
    eco = sim.economy
    x, y = find_site(sim, town)
    farm = eco.build_firm(FARM, eco.add_corp("T"), x, y, town)
    job = farm.add_job(0, CROP, eco.catalog["Wheat"])
    assert isinstance(job, CropGrowing)
    while sim.calendar.month != 4:  # out of season Jan–Mar: nothing grows
        sim.advance_day()
    assert job.stock == 0
    daily = job.daily_growth()
    assert daily > 0
    days = 0
    while job.stock < job.capacity:
        sim.advance_day()
        days += 1
    assert days == math.ceil(job.capacity / daily)


def test_flour_factory_fed_by_seaport_30_days_seed_1():
    sim, town = bread_town(1)
    eco = sim.economy
    cat = eco.catalog
    x, y = find_site(sim, town)
    imp = eco.build_firm(SEAPORT, None, x, y, town).add_job(0, IMPORT, cat["Wheat"])
    x, y = find_site(sim, town)
    f = eco.build_firm(FACTORY, eco.add_corp("T"), x, y, town)
    buy = f.add_job(0, PURCHASING, cat["Wheat"])
    mfg = f.add_job(1, MANUFACTURING, cat["Flour"])
    f.link_slots(0, 1)
    eco.link_b2b(imp, buy)
    sim.advance_days(30)
    assert mfg.stock == pytest.approx(120000.0)  # filled to capacity (60k $/day)
    # Wheat at $0.10 plus each day's wages spread over that day's output.
    assert mfg.unit_cost == pytest.approx(0.1258, abs=1e-4)
    assert mfg.quality == pytest.approx(41.6)  # 50 import × 70% + skill 22 × 30%
    assert buy.stock == pytest.approx(600000.0)


def _engine_output(speed_pct: int) -> tuple[int, float]:
    """Cycles per day and one day's units for an Engine line with plentiful inputs."""
    sim, town = bread_town(1)
    town.labor_quality = 50  # efficiency 27.5, so a 2× day still fits under capacity
    eco = sim.economy
    engine = eco.catalog["Engine"]
    rec = eco.catalog.recipes[engine.id]
    assert rec.speed_pct == 200  # docs/recipes.md
    eco.catalog.recipes[engine.id] = rec.model_copy(update={"speed_pct": speed_pct})
    x, y = find_site(sim, town)
    f = eco.build_firm(FACTORY, eco.add_corp("T"), x, y, town)
    job = f.add_job(1, MANUFACTURING, engine)
    assert isinstance(job, Manufacturing)
    for i in rec.inputs:
        job.inputs[i.input_id] = [1e9, 50.0, 1.0]
    job.work(eco)
    return job.cycles_per_day(eco.catalog.recipes[engine.id]), job.stock


def test_speed_pct_multiplies_throughput():
    cycles_200, units_200 = _engine_output(200)
    cycles_100, units_100 = _engine_output(100)
    assert cycles_100 > 0 and units_100 > 0
    assert cycles_200 in (2 * cycles_100, 2 * cycles_100 + 1)  # whole cycles only
    assert units_200 == pytest.approx(2 * units_100, abs=1)
    assert (units_200, units_100) == (cycles_200, cycles_100)  # Engine output_qty is 1


def test_training_full_capacity_ten_weeks_rating_1_to_2():
    sim, town = bread_town(1)
    eco = sim.economy
    x, y = find_site(sim, town)
    mine = eco.build_firm(6, eco.add_corp("T"), x, y, town)
    job = mine.add_job(1, 8, eco.catalog["Coal"])
    assert isinstance(job, Extraction) and job.rating == 1
    trains = 0
    while trains < 10:
        job.stock = 0.0  # drained daily: the job works at full capacity
        if sim.calendar.weekday == JOB_RULES.train_weekday:
            trains += 1
            assert job.rating == 1
        sim.advance_day()
    assert job.rating == 2 and job.train_acc == 0


# --- slice 5: links and markets ---------------------------------------------------------


def _two_stores(q1: float, q2: float):
    sim, town = bread_town(1)
    eco = sim.economy
    bread = eco.catalog["Bread"]
    corp = eco.add_corp("T")
    sales = []
    for q in (q1, q2):
        x, y = find_site(sim, town)
        store = eco.build_firm(DEPARTMENT_STORE, corp, x, y, town)
        s = store.add_job(0, SALES, bread)
        s.quality = q
        sales.append(s)
    links = [eco.link_consumer(s, town) for s in sales]
    return sim, town, links


def test_two_stores_score_squared_shares():
    sim, town, links = _two_stores(60, 40)
    tm = sim.economy.town_market(town, "Bread")
    scores = [lk.compute_score() for lk in links]
    assert scores[0] > scores[1]
    shares = score_shares(tm.demand_per_day, scores)
    assert sum(shares) == pytest.approx(tm.demand_per_day, abs=1)
    assert shares[0] / shares[1] == pytest.approx((scores[0] / scores[1]) ** 2)


def test_halving_price_adds_25_to_score():
    sim, _, _ = _two_stores(50, 50)
    bread = sim.economy.catalog["Bread"]
    full = link_score(bread, bread.row.base_price, 50, 10)
    half = link_score(bread, bread.row.base_price / 2, 50, 10)
    assert half - full == pytest.approx(25)
    scores = [full, half]
    shares = score_shares(100, scores)
    assert shares[1] > shares[0]


def test_oversupply_drains_five_percent_a_day():
    sim, town, links = _two_stores(50, 50)
    eco = sim.economy
    tm = eco.town_market(town, "Bread")
    for lk in links:
        lk.quantity = tm.demand_per_day  # supply = 2 × demand
    before = [lk.quantity for lk in links]
    eco.market.consumer_pass(tm)
    for b, lk in zip(before, links, strict=True):
        assert lk.quantity == pytest.approx(b * (1 - 1 / LINK_RULES.oversupply_div))
        assert lk.quantity == pytest.approx(b * 0.95)


def _run_chain(seed: int = 1, days: int = 120):
    sim, town = bread_town(seed)
    chain = build_bread_chain(sim, town)
    sim.advance_days(days)
    return sim, chain


def test_bread_chain_end_to_end_seed_1():
    sim, chain = _run_chain()
    link = chain.store_link
    assert sim.state_hash() == ("ec138cc754db7b84e6d2782685208973e22a3ee82b523b4d49e4b191761801bd")
    assert sum(link.money_month) == pytest.approx(952730.4030324987, abs=1e-3)
    assert chain.store_sales.unit_cost == pytest.approx(1.5)
    assert link.brand == pytest.approx(10.6, abs=1e-6)
    assert chain.store_sales.quality == pytest.approx(17.903092, abs=1e-5)
    # Bread actually reached the shelf and sold every month after the first.
    assert all(link.units_month[m] > 0 for m in (1, 2, 3))


def test_bread_chain_monthly_profit():
    """After a two-month warm-up, every month March–June closes with a profit.

    Profit (scenario.chain_month_profit) = consumers' money at the store minus
    what leaves the corporation: seaport wheat, wages, training, overhead and
    freight. Sales between the chain's own firms cancel out.
    """
    sim, town = bread_town(1)
    chain = build_bread_chain(sim, town)
    results = {}
    for month in range(1, 7):
        while not (sim.calendar.month == month + 1 and sim.calendar.real_day == 1):
            sim.advance_day()
        results[month] = chain_month_profit(chain, month - 1)
    for month in (3, 4, 5, 6):
        r = results[month]
        assert r["profit"] > 0, (month, r)
        assert r["revenue"] > r["wages"] + r["overhead"]


def test_bread_chain_is_deterministic():
    a, _ = _run_chain(1, 60)
    b, _ = _run_chain(1, 60)
    assert a.state_hash() == b.state_hash()
