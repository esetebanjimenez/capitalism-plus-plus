"""Golden tests for systems 3, 4a and 5 (docs/design.md slices 3–5)."""

from __future__ import annotations

import hashlib
import math
import re
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from capitalism import Sim
from capitalism.catalog import Catalog, Software, compute_availability, daily_demand, nec_lux
from capitalism.firms import Farm, TVStation, decode_links, encode_links
from capitalism.jobs import (
    Advertising,
    CropGrowing,
    Extraction,
    ImportJob,
    Inventory,
    LivestockProcessing,
    Manufacturing,
    PrivateLabelling,
    Sales,
    SoftwareProduction,
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
from capitalism.tables import (
    FIXED_TRAINING_CREDITS,
    JOB_RULES,
    LINK_RULES,
    PRODUCT_RULES,
    RATING_THROUGHPUT,
    db_path,
)

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
    assert con.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 85
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
    assert counts["RAW"] == 8 and counts["SEMI"] == 12 and counts["ELEAPP"] == 8
    # Software is provisional reference-price content for M1, not a baseline recipe.
    assert con.execute("SELECT tech_year FROM products WHERE name='Software'").fetchone()[0] == 0
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []
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
        "2f7c9ad14599229681a019e9e26a4f3fc656cc1e8862328c4f163a26e261ecb4"
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
    assert f.ledger.month[2] == pytest.approx(100000.0)
    sim.advance_day()
    wage = job_wage_day(24, 100, 31)
    assert f.ledger.month[1] == wage
    assert f.ledger.month[3] == pytest.approx(wage * 10 / 100)  # corporate training budget 10%
    while sim.calendar.month == 1:
        sim.advance_day()
    assert f.ledger.month[2] == pytest.approx(100000.0)  # Feb overhead, full month


def test_base_capacity_is_value_per_day_over_price():
    k = PRODUCT_RULES.capacity_value_per_day
    for p in Catalog().products:
        if not isinstance(
            p, Software
        ):  # explicit provisional capacity row, not generic $60k/day fill
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
    tv = eco.build_firm(11, None, x, y, town)
    assert isinstance(tv, TVStation) and tv.jobs() == []


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
    eco.add_corp("Test Corp")  # fixture identity matches canonical chain: public port has id 0 only
    corp = eco.add_corp("Manufacturer")
    corp.technology[cat["Flour"].id] = cat["Flour"].state.tech_level
    imp = eco.build_firm(SEAPORT, None, x, y, town).add_job(0, IMPORT, cat["Wheat"])
    x, y = find_site(sim, town)
    f = eco.build_firm(FACTORY, corp, x, y, town)
    buy = f.add_job(0, PURCHASING, cat["Wheat"])
    mfg = f.add_job(1, MANUFACTURING, cat["Flour"])
    f.link_slots(0, 1)
    eco.link_b2b(imp, buy)
    sim.advance_days(30)
    assert mfg.stock == pytest.approx(120000.0)  # filled to capacity (60k $/day)
    # Wheat at $0.10 plus each day's wages spread over that day's output.
    assert mfg.unit_cost == pytest.approx(0.1129, abs=1e-4)
    assert mfg.quality == pytest.approx(41.6)  # 50 import × 70% + skill 22 × 30%
    assert buy.stock == pytest.approx(600000.0)


def _engine_output(speed_pct: int) -> tuple[int, float]:
    """Cycles per day and one day's units for an Engine line with plentiful inputs."""
    sim, town = bread_town(1)
    town.labor_quality = 50  # labour quality does not lower efficiency a second time
    eco = sim.economy
    engine = eco.catalog["Engine"]
    rec = eco.catalog.recipes[engine.id]
    assert rec.speed_pct == 200  # docs/recipes.md
    eco.catalog.recipes[engine.id] = rec.model_copy(update={"speed_pct": speed_pct})
    # Rating-1 efficiency is now 100%: native Engine base (20) fills before 2× speed can show.
    # Local capacity override only — storage_mult stays inactive on the real capacity path.
    engine.row = engine.row.model_copy(update={"base_capacity": 100.0})
    x, y = find_site(sim, town)
    f = eco.build_firm(FACTORY, eco.add_corp("T"), x, y, town)
    job = f.add_job(1, MANUFACTURING, engine)
    assert isinstance(job, Manufacturing)
    for i in rec.inputs:
        job.inputs[i.input_id] = [1e9, 50.0, 1.0]
    job.work(eco)
    return job.cycles_per_day(eco.catalog.recipes[engine.id]), job.stock


def test_speed_pct_multiplies_throughput():
    # At rating-1 efficiency 100%, speed≥100% fills the whole capacity room in one day,
    # so 100→200 cannot show a 2× stock delta. 50→100 still fits under the room.
    cycles_100, units_100 = _engine_output(100)
    cycles_50, units_50 = _engine_output(50)
    assert cycles_50 > 0 and units_50 > 0
    assert cycles_100 in (2 * cycles_50, 2 * cycles_50 + 1)  # whole cycles only
    assert units_100 == pytest.approx(2 * units_50, abs=1e-9)
    assert (units_100, units_50) == (cycles_100, cycles_50)  # Engine output_qty is 1


def test_rating_efficiency_table_and_inactive_storage():
    assert [RATING_THROUGHPUT[i].efficiency_pct for i in range(1, 10)] == [
        100,
        130,
        160,
        200,
        250,
        300,
        360,
        430,
        500,
    ]
    assert [RATING_THROUGHPUT[i].storage_mult for i in range(1, 10)] == [
        8,
        10,
        14,
        16,
        20,
        24,
        30,
        35,
        40,
    ]
    sim, town = bread_town(1)
    job = sim.economy.build_firm(FACTORY, None, *find_site(sim, town), town).add_job(
        0, MANUFACTURING, sim.economy.catalog["Bread"]
    )
    # Storage multiplier is registered only; capacity stays product×size×cap_mult.
    assert job.capacity == job.product.row.base_capacity * job.firm.size * job.row.cap_mult
    assert job.capacity == pytest.approx(40000.0)


def test_fixed_and_work_mode_credit_ratios():
    """Half of a nominal-100 manufacturing step earns 50 raw credits (PR #22)."""
    sim, town = bread_town(1)
    eco = sim.economy
    engine = eco.catalog["Engine"]
    # capacity 50 × efficiency 100 × speed 200% / 10000 = nominal 100 units.
    engine.row = engine.row.model_copy(update={"base_capacity": 50.0})
    f = eco.build_firm(FACTORY, eco.add_corp("F"), *find_site(sim, town), town)
    job = f.add_job(0, MANUFACTURING, engine)
    recipe = eco.catalog.recipe(job.product)
    assert recipe is not None and recipe.output_qty == 1 and job.efficiency == 100
    for ingredient in recipe.inputs:
        job.inputs[ingredient.input_id] = [ingredient.qty * 50, 80.0, 1.0]
    nominal = job.efficiency * job.capacity * recipe.speed_pct / 10000.0
    assert (job.capacity, nominal) == (50.0, 100.0)
    assert job.work(eco) and job.stock == 50
    assert job.train_credits == pytest.approx(50.0)
    for ingredient in recipe.inputs:
        job.inputs[ingredient.input_id][0] = 0
    prior = job.train_credits
    job.stock = 0
    assert job.work(eco) and job.train_credits == prior  # idle visit earns nothing
    assert {k: v.base_daily for k, v in FIXED_TRAINING_CREDITS.items()} == {
        1: 20,
        2: 10,
        11: 14,
        13: 14,
    }


def test_weekly_training_strict_threshold_one_staff_step():
    sim, town = bread_town(1)
    f = sim.economy.build_firm(FACTORY, sim.economy.add_corp("T"), *find_site(sim, town), town)
    job = f.add_job(0, MANUFACTURING, sim.economy.catalog["Bread"])
    job.staff = 1
    job.rating = 1
    job.train_credits = 900.0  # exact threshold must not pass
    job.train()
    assert (job.rating, job.train_progress, job.train_credits) == (1, 0, 900.0)
    job.train_credits = 901.0
    job.train()
    assert (job.rating, job.train_progress, job.train_credits) == (2, 0, 0.0)
    job.rating = 9
    job.train_credits = 9 * 900 + 1
    job.train()
    assert (job.rating, job.train_progress, job.train_credits) == (9, 0, 0.0)


def test_low_stock_receipt_and_real_sale_credit_actual_units(monkeypatch):
    from capitalism.jobs import Purchasing

    sim, town = bread_town(1)
    eco = sim.economy
    corp = eco.add_corp("T")
    factory = eco.build_firm(FACTORY, corp, *find_site(sim, town), town)
    buy = factory.add_job(0, PURCHASING, eco.catalog["Wheat"])
    # Rating-1 efficiency 100% makes order=4×capacity; room then caps receipt at 25% of order.
    # Local 25% efficiency makes order==capacity so a full receipt scores the reference 80.
    monkeypatch.setattr(Purchasing, "efficiency", property(lambda self: 25.0))
    seller = ImportJob(factory, 0, buy.product)
    buy.stock = 0.0
    buy.supply = SimpleNamespace(
        seller=seller, price=0.1, firm=factory, quantity=0.0, record_sale=lambda qty: None
    )
    calendar = SimpleNamespace(day_serial=(-factory.id) % JOB_RULES.purchase_every_days, month=1)
    assert buy.work(SimpleNamespace(calendar=calendar)) is False
    assert buy.train_credits == pytest.approx(80.0)
    assert buy.stock == pytest.approx(buy.capacity)

    store = eco.build_firm(DEPARTMENT_STORE, corp, *find_site(sim, town), town)
    sale = store.add_job(0, SALES, eco.catalog["Bread"])
    assert isinstance(sale, Sales)
    cap = sale.daily_cap()
    sale.stock = cap
    sale.unit_cost = 1.5
    sold = cap / 2
    link = SimpleNamespace(price=1.5, record_sale=lambda qty: None)
    sale.sell_left = cap
    sale.sell_to(sold, link)
    assert sale.train_credits == pytest.approx(50.0)
    assert sale.stock == pytest.approx(cap - sold)


def test_no_passive_credit_for_inventory_advertising_or_uncertain_ratios():
    sim, town = bread_town(1)
    eco = sim.economy
    f = eco.build_firm(FACTORY, eco.add_corp("dummy"), *find_site(sim, town), town)
    farm = eco.build_firm(FARM, None, *find_site(sim, town), town)
    chicken = eco.catalog["Chicken"]
    for j in (
        Inventory(f, 0, eco.catalog["Bread"]),
        Advertising(f, 0, eco.catalog["Bread"]),
        SoftwareProduction(f, 0, eco.catalog["Software"]),
        Extraction(f, 0, eco.catalog["Coal"]),
        LivestockProcessing(farm, 0, chicken),
        PrivateLabelling(f, 0, eco.catalog["Bread"]),  # credit only on_moved, not idle work
    ):
        if isinstance(j, SoftwareProduction):
            j.has_master = False
        j.work(eco)
        assert j.train_credits == 0.0
        j.train()
        assert j.train_progress == 0


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


def test_bread_chain_end_to_end_seed_1():  # updated 4b hash also includes the Software catalog row
    sim, chain = _run_chain()
    link = chain.store_link
    assert sim.state_hash() == ("3ea47a3fa0b461a90165c77b5454d1d9f0e527b32dac79dd5345b5406e370cbc")
    assert sum(link.money_month) == pytest.approx(1003123.1072974899, abs=1e-3)
    assert chain.store_sales.unit_cost == pytest.approx(1.5)
    assert link.brand == pytest.approx(11.0, abs=1e-6)
    assert chain.store_sales.quality == pytest.approx(17.687896898428896, abs=1e-5)
    # Bread actually reached the shelf and sold every month after the first.
    assert all(link.units_month[m] > 0 for m in (1, 2, 3))


def test_bread_chain_monthly_accounting():
    """4a is accounting-correct, not profit-positive (Designer 2026-11-06).

    A single-product chain can't break even at full-dollar monthly overhead
    until the 4b/5 volume rebalance. This locks the postings instead:
    wages cat 1, TV-scale $100k/month cat 2 overhead, positive consumer revenue
    at reference prices. Don't tune capacity to force profit here.
    """
    sim, town = bread_town(1)
    chain = build_bread_chain(sim, town)
    results = {}
    for month in range(1, 7):
        while not (sim.calendar.month == month + 1 and sim.calendar.real_day == 1):
            sim.advance_day()
        results[month] = chain_month_profit(chain, month - 1)
    r = results[4]  # month after April closes; ledger index remains zero-based April = 3
    assert r["overhead"] == pytest.approx(300000.0)  # 2 factories + dept store, $100k/mo each
    assert r["revenue"] == pytest.approx(273_578.5119369011, abs=0.002)
    assert (r["wages"], r["overhead"], r["wheat"]) == (167_910, 300_000, 16_414.2)
    # Training is budget × daily wage / divisor accumulated in floats: equal to cents, not bits.
    assert r["training"] == pytest.approx(16_791, abs=1e-6)
    for job, qty, charge in zip(
        (chain.wheat_buy, chain.flour_buy, chain.bread_buy),
        (164_142, 164_142, 182_385.67462499382),
        (172.34910000000002, 287.2485, 683.9462798437269),
        strict=True,
    ):
        assert job.received_month[3] == pytest.approx(qty)
        assert job.freight_month[3] == pytest.approx(charge)
    assert r["freight"] == pytest.approx(1_143.543879843727)
    assert r["profit"] == pytest.approx(-228_680.23194294266, abs=0.002)
    assert r["profit"] == pytest.approx(
        r["revenue"] - r["wages"] - r["training"] - r["overhead"] - r["freight"] - r["wheat"]
    )


def test_bread_chain_is_deterministic():
    a, _ = _run_chain(1, 60)
    b, _ = _run_chain(1, 60)
    assert a.state_hash() == b.state_hash()
