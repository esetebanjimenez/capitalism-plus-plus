"""Weekly rating decay (gap audit M2, FUN_00075988)."""

import pytest

from capitalism.links import BRAND_CORPORATE, BRAND_RANGE, BRAND_UNIQUE
from capitalism.links import (
    DEMAND_DIVISOR,
    RATING_GATE,
    SUPPLY_DECAY_CAP,
)
from capitalism.scenario import (
    DEPARTMENT_STORE,
    SALES,
    bread_town,
    find_site,
)


def _consumer_link(sim, town, corp, product_name="Bread"):
    """Build a dept store with a Sales job and link to consumer market."""
    eco = sim.economy
    x, y = find_site(sim, town)
    firm = eco.build_firm(DEPARTMENT_STORE, corp, x, y, town)
    product = eco.catalog[product_name]
    job = firm.add_job(0, SALES, product)
    link = eco.link_consumer(job, town)
    return firm, job, link


def _importer_link(sim, seller_town, buyer_town, corp, product_name="Bread"):
    """A firm in seller_town selling to buyer_town's market (importer)."""
    eco = sim.economy
    x, y = find_site(sim, seller_town)
    firm = eco.build_firm(DEPARTMENT_STORE, corp, x, y, seller_town)
    product = eco.catalog[product_name]
    job = firm.add_job(0, SALES, product)
    link = eco.link_consumer(job, buyer_town)
    return firm, job, link


def test_decay_gate_blocks_low_awareness():
    sim, town = bread_town()
    corp = sim.economy.add_corp("P")
    _firm, _job, link = _consumer_link(sim, town, corp)
    link.awareness = RATING_GATE - 0.01
    demand_before = link.buyer.demand_per_day
    sim.economy.market.weekly_ratings()
    assert link.awareness == pytest.approx(RATING_GATE - 0.01)
    assert link.buyer.demand_per_day == pytest.approx(demand_before)


def test_decay_local_producer():
    sim, town = bread_town()
    corp = sim.economy.add_corp("P")
    _firm, _job, link = _consumer_link(sim, town, corp)
    link.awareness = 1.0
    tm = link.buyer
    demand = tm.demand_per_day
    expected_decay = min(RATING_GATE, demand / DEMAND_DIVISOR)
    sim.economy.market.weekly_ratings()
    assert link.awareness == pytest.approx(1.0 - expected_decay)


def test_decay_importer_corporate():
    sim, town = bread_town()
    eco = sim.economy
    towns = sim.world.towns
    if len(towns) < 2:
        pytest.skip("need at least 2 towns")
    other = towns[1] if towns[0] is town else towns[0]
    corp = eco.add_corp("P")
    corp.brand_strategy = BRAND_CORPORATE
    _firm, _job, link = _importer_link(sim, other, town, corp)
    link.awareness = 1.0
    sim.economy.market.weekly_ratings()
    assert link.awareness == pytest.approx(1.0 - 0.025)


def test_decay_importer_range():
    sim, town = bread_town()
    eco = sim.economy
    towns = sim.world.towns
    if len(towns) < 2:
        pytest.skip("need at least 2 towns")
    other = towns[1] if towns[0] is town else towns[0]
    corp = eco.add_corp("P")
    corp.brand_strategy = BRAND_RANGE
    _firm, _job, link = _importer_link(sim, other, town, corp)
    link.awareness = 1.0
    sim.economy.market.weekly_ratings()
    assert link.awareness == pytest.approx(1.0 - 0.05)


def test_decay_importer_unique():
    sim, town = bread_town()
    eco = sim.economy
    towns = sim.world.towns
    if len(towns) < 2:
        pytest.skip("need at least 2 towns")
    other = towns[1] if towns[0] is town else towns[0]
    corp = eco.add_corp("P")
    corp.brand_strategy = BRAND_UNIQUE
    _firm, _job, link = _importer_link(sim, other, town, corp)
    link.awareness = 1.0
    sim.economy.market.weekly_ratings()
    assert link.awareness == pytest.approx(1.0 - 0.1)


def test_demand_reduced_by_decay():
    sim, town = bread_town()
    corp = sim.economy.add_corp("P")
    _firm, _job, link = _consumer_link(sim, town, corp)
    link.awareness = 1.0
    tm = link.buyer
    demand_before = tm.demand_per_day
    expected_decay = min(RATING_GATE, demand_before / DEMAND_DIVISOR)
    sim.economy.market.weekly_ratings()
    assert tm.demand_per_day == pytest.approx(max(0.0, demand_before - expected_decay))


def test_supply_decays():
    sim, town = bread_town()
    corp = sim.economy.add_corp("P")
    _firm, _job, link = _consumer_link(sim, town, corp)
    tm = link.buyer
    tm.supply_today = 10.0
    link.awareness = 0.0  # below gate — no link-level decay
    sim.economy.market.weekly_ratings()
    expected = min(10.0 / 200.0, SUPPLY_DECAY_CAP)
    assert tm.supply_today == pytest.approx(10.0 - expected)


def test_supply_capped_at_demand():
    sim, town = bread_town()
    corp = sim.economy.add_corp("P")
    _firm, _job, link = _consumer_link(sim, town, corp)
    tm = link.buyer
    tm.demand_per_day = 0.5
    tm.supply_today = 10.0
    link.awareness = 0.0
    sim.economy.market.weekly_ratings()
    assert tm.supply_today <= tm.demand_per_day


def test_monthly_awareness_updates_brand_record():
    """FUN_00075aec: monthly awareness gain updates brand record, capped at 100."""
    from capitalism.links import brand_key

    sim, town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("P")
    _firm, _job, link = _consumer_link(sim, town, corp)
    market = eco.market
    tm = link.buyer
    tm.demand_per_day = 5.0
    link.units_month[(link.month_index - 1) % 12] = 10.0
    market._monthly_awareness(link, tm)
    bk = brand_key(corp, link.product, market.catalog)
    rec = market.brand_records.get((town.id, bk))
    assert rec is not None
    assert rec.awareness.get(corp.id, 0.0) > 0.0
    assert rec.rating_cell.get(corp.id, 0.0) > 0.0
    # Cap: set awareness near 100, gain should not exceed 100
    rec.awareness[corp.id] = 99.99
    rec.rating_cell[corp.id] = 0.0
    market._monthly_awareness(link, tm)
    assert rec.awareness[corp.id] <= 100.0


def test_weekly_ratings_runs_on_weekday5():
    """Integration: advance sim to weekday 5, verify decay fires."""
    sim, town = bread_town()
    corp = sim.economy.add_corp("P")
    _firm, _job, link = _consumer_link(sim, town, corp)
    # Advance until the NEXT advance_day() will land on weekday 5.
    # weekday = day_serial % 7; calendar.advance() runs before the check.
    while (sim.calendar.day_serial + 1) % 7 != 5:
        sim.advance_day()
    link.awareness = 25.0
    sim.advance_day()
    assert link.awareness < 25.0
