"""Extraction rate (J4), reserve depletion (J5), and exhaustion guard."""

import pytest

from capitalism.scenario import bread_town, find_site
from capitalism.tables import JOB_RULES

MINE = 6
MINING = 8


def _mine_with_reserve(sim, town, reserve=10.0):
    """Build a mine with one Mining job and a finite reserve."""
    eco = sim.economy
    corp = eco.add_corp("MiningCorp")
    x, y = find_site(sim, town)
    mine = eco.build_firm(MINE, corp, x, y, town)
    product = eco.catalog.by_id[5]  # Iron Ore
    corp.technology[product.id] = product.state.tech_level
    job = mine.add_job(0, MINING, product)
    mine.reserve = reserve
    return mine, job


def test_rate_field_from_rules():
    """J4: Extraction.rate is set from JOB_RULES.extraction_rate on init."""
    sim, town = bread_town()
    _mine, job = _mine_with_reserve(sim, town)
    assert job.rate == JOB_RULES.extraction_rate


def test_throughput_formula():
    """J4: step = efficiency × rate × capacity / 100."""
    sim, town = bread_town()
    mine, job = _mine_with_reserve(sim, town, reserve=100.0)
    expected_step = job.efficiency * job.rate * job.capacity / 100
    job.work(sim.economy)
    assert job.stock == pytest.approx(min(expected_step, job.room))


def test_reserve_decreases():
    """J5: reserve drops after extraction work."""
    sim, town = bread_town()
    mine, job = _mine_with_reserve(sim, town, reserve=10.0)
    before = mine.reserve
    job.work(sim.economy)
    assert mine.reserve < before


def test_reserve_depletion_formula():
    """J5: draw = added / capacity / rate / 100."""
    sim, town = bread_town()
    mine, job = _mine_with_reserve(sim, town, reserve=10.0)
    job.work(sim.economy)
    step = job.efficiency * job.rate * job.capacity / 100
    added = min(job.room, step)
    expected_draw = added / job.capacity / job.rate / 100.0
    assert mine.reserve == pytest.approx(10.0 - expected_draw)


def test_exhaustion_stops_extraction():
    """J5: when reserve hits 0, work returns False (no output)."""
    sim, town = bread_town()
    mine, job = _mine_with_reserve(sim, town, reserve=0.0)
    result = job.work(sim.economy)
    assert result is False
    assert job.stock == 0.0


def test_exhaustion_zeroes_reserve():
    """J5: reserve is clamped to exactly 0.0, not negative."""
    sim, town = bread_town()
    mine, job = _mine_with_reserve(sim, town, reserve=1e-20)
    job.work(sim.economy)
    assert mine.reserve == 0.0


def test_no_product_returns_false():
    """Extraction with no product does nothing."""
    sim, town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("MiningCorp2")
    x, y = find_site(sim, town)
    mine = eco.build_firm(MINE, corp, x, y, town)
    job = mine.add_job(0, MINING, None)
    mine.reserve = 10.0
    result = job.work(sim.economy)
    assert result is False
