"""Livestock Processing throughput (J10) and quality (J12)."""

import pytest

from capitalism.scenario import FARM, bread_town, find_site
from capitalism.tables import LIVESTOCK_YIELDS

LIVESTOCK_RAISING = 2
LIVESTOCK_PROCESSING = 3


def _livestock_pair(sim, town):
    """Build a farm with a Livestock Raising + Processing pair, linked."""
    eco = sim.economy
    corp = eco.add_corp("Ranch")
    x, y = find_site(sim, town)
    farm = eco.build_firm(FARM, corp, x, y, town)
    # Pick first livestock that has a yield row
    livestock_id = next(iter(LIVESTOCK_YIELDS))
    row = LIVESTOCK_YIELDS[livestock_id]
    livestock_product = eco.catalog.by_id[livestock_id]
    output_product = eco.catalog.by_id[row.product_id]
    raising = farm.add_job(0, LIVESTOCK_RAISING, livestock_product)
    proc = farm.add_job(1, LIVESTOCK_PROCESSING, output_product)
    farm.link_slots(0, 1)
    return raising, proc, row


def test_throughput_uses_own_capacity():
    """J10: throughput = eff × self.capacity × yield / 10000."""
    sim, town = bread_town()
    raising, proc, row = _livestock_pair(sim, town)
    raising.stock = 1000.0
    expected = proc.efficiency * proc.capacity * row.yield_factor / 10_000
    proc.work(sim.economy)
    taken = 1000.0 - raising.stock
    assert taken == pytest.approx(min(expected, proc.room, 1000.0))


def test_throughput_limited_by_stock():
    """Take is min(stock, wanted, room)."""
    sim, town = bread_town()
    raising, proc, row = _livestock_pair(sim, town)
    raising.stock = 0.5  # very little stock
    proc.work(sim.economy)
    assert raising.stock == pytest.approx(0.0)
    assert proc.stock == pytest.approx(0.5)


def test_throughput_limited_by_room():
    """Take is min(stock, wanted, room)."""
    sim, town = bread_town()
    raising, proc, row = _livestock_pair(sim, town)
    raising.stock = 1000.0
    proc.stock = proc.ceiling - 0.1  # almost full, only 0.1 room
    proc.work(sim.economy)
    assert proc.stock == pytest.approx(proc.ceiling, abs=0.01)


def test_quality_bonus_from_raising_rating():
    """J12: proc.quality = src.quality + (src.rating - 1) × 4, capped at 100."""
    sim, town = bread_town()
    raising, proc, row = _livestock_pair(sim, town)
    raising.stock = 100.0
    raising.quality = 35.0
    raising.rating = 3
    proc.work(sim.economy)
    expected_quality = min(35.0 + (3 - 1) * 4, 100)
    assert proc.quality == pytest.approx(expected_quality)


def test_quality_bonus_rating_1():
    """Rating 1 adds 0 bonus."""
    sim, town = bread_town()
    raising, proc, row = _livestock_pair(sim, town)
    raising.stock = 100.0
    raising.quality = 40.0
    raising.rating = 1
    proc.work(sim.economy)
    assert proc.quality == pytest.approx(40.0)


def test_quality_capped_at_100():
    """Quality bonus cannot exceed 100."""
    sim, town = bread_town()
    raising, proc, row = _livestock_pair(sim, town)
    raising.stock = 100.0
    raising.quality = 95.0
    raising.rating = 9
    proc.work(sim.economy)
    assert proc.quality == pytest.approx(100.0)
