"""Livestock Raising herd model (J8): two-pool young/grown with observed rates."""

import pytest

from capitalism.scenario import FARM, bread_town, find_site
from capitalism.tables import LIVESTOCK_HERD_RATES, LIVESTOCK_YIELDS

LIVESTOCK_RAISING = 2


def _raising(sim, town, livestock_id=None):
    eco = sim.economy
    corp = eco.add_corp("Ranch")
    x, y = find_site(sim, town)
    farm = eco.build_firm(FARM, corp, x, y, town)
    if livestock_id is None:
        livestock_id = next(iter(LIVESTOCK_YIELDS))
    product = eco.catalog.by_id[livestock_id]
    raising = farm.add_job(0, LIVESTOCK_RAISING, product)
    return raising


def test_maturation_flow():
    """Young matures into grown at grow_rate / (scalar × 100)."""
    sim, town = bread_town()
    raising = _raising(sim, town)
    herd = LIVESTOCK_HERD_RATES[raising.product.id]
    raising.young = 100.0
    raising.grown = 0.0
    raising.work(sim.economy)
    scalar = 36500.0
    eff = raising.efficiency
    expected_matured = herd.grow_rate * 100.0 / scalar * eff / 100.0
    assert raising.grown == pytest.approx(expected_matured, rel=1e-6)
    assert raising.young == pytest.approx(100.0 - expected_matured, rel=1e-4)


def test_reproduction_flow():
    """Grown reproduces into young at reproduce_rate / (scalar × 100)."""
    sim, town = bread_town()
    raising = _raising(sim, town)
    herd = LIVESTOCK_HERD_RATES[raising.product.id]
    raising.young = 0.0
    raising.grown = 100.0
    raising.work(sim.economy)
    scalar = 36500.0
    eff = raising.efficiency
    expected_born = herd.reproduce_rate * 100.0 / scalar * eff / 100.0
    assert raising.young == pytest.approx(expected_born, rel=1e-6)


def test_stock_is_round_young():
    """stock = round(young), matching native __CHP behaviour."""
    sim, town = bread_town()
    raising = _raising(sim, town)
    raising.young = 50.0
    raising.grown = 0.0
    raising.work(sim.economy)
    assert raising.stock == round(raising.young)


def test_available_stock_is_grown():
    """Processing takes from the grown pool."""
    sim, town = bread_town()
    raising = _raising(sim, town)
    raising.grown = 42.0
    assert raising.available_stock() == 42.0


def test_take_deducts_from_grown():
    """take() reduces the grown pool."""
    sim, town = bread_town()
    raising = _raising(sim, town)
    raising.grown = 100.0
    taken = raising.take(30.0)
    assert taken == pytest.approx(30.0)
    assert raising.grown == pytest.approx(70.0)


def test_take_clamped_to_grown():
    """Cannot take more than grown pool."""
    sim, town = bread_town()
    raising = _raising(sim, town)
    raising.grown = 10.0
    taken = raising.take(50.0)
    assert taken == pytest.approx(10.0)
    assert raising.grown == pytest.approx(0.0)


def test_maturation_ceiling_allows_negative():
    """When grown > ceiling, matured can go negative (native behaviour)."""
    sim, town = bread_town()
    raising = _raising(sim, town)
    ceil = raising.ceiling
    raising.grown = ceil + 10.0
    raising.young = 50.0
    raising.work(sim.economy)
    # matured = ceil - grown = -10, so young increases and grown decreases
    assert raising.grown < ceil + 10.0


def test_young_ceiling_cap():
    """Young is capped at ceiling after reproduction."""
    sim, town = bread_town()
    raising = _raising(sim, town)
    ceil = raising.ceiling
    raising.young = ceil - 1.0
    raising.grown = ceil  # large grown → large born → young should hit ceiling
    raising.work(sim.economy)
    assert raising.young <= ceil


def test_no_product_returns_false():
    """work() returns False and does nothing with no product."""
    sim, town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("Ranch")
    x, y = find_site(sim, town)
    farm = eco.build_firm(FARM, corp, x, y, town)
    raising = farm.add_job(0, LIVESTOCK_RAISING, None)
    result = raising.work(eco)
    assert result is False
