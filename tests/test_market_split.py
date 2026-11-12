"""Tests for Group 9: K1 market share, K2 unmet demand, K3 consumer split (N3-N7)."""

from __future__ import annotations

import pytest

from capitalism.links import (
    _increase_gap,
    _reduce_gap,
    _take_gap,
    native_link_score,
)
from capitalism.scenario import DEPARTMENT_STORE, SALES, bread_town, find_site


def _link_in_town(sim, town, corp, quality=50.0, price=None, product_name="Bread"):
    eco = sim.economy
    x, y = find_site(sim, town)
    store = eco.build_firm(DEPARTMENT_STORE, corp, x, y, town)
    product = eco.catalog[product_name]
    job = store.add_job(0, SALES, product)
    job.quality = quality
    link = eco.link_consumer(job, town)
    if price is not None:
        link.price = price
    link.score = link.compute_score()
    link.prev_score = link.score
    return link


# --- N3: native link score -------------------------------------------------


class TestNativeLinkScore:
    def test_price_at_base_gives_zero_base(self):
        sim, town = bread_town()
        tm = sim.economy.town_market(town, "Bread")
        s = native_link_score(tm, tm.product.row.base_price, 0, 0)
        assert s == 0.0

    def test_cheaper_than_base_gives_positive(self):
        sim, town = bread_town()
        tm = sim.economy.town_market(town, "Bread")
        s = native_link_score(tm, tm.product.row.base_price * 0.5, 0, 0)
        assert s > 0

    def test_more_expensive_gives_negative_clamped(self):
        sim, town = bread_town()
        tm = sim.economy.town_market(town, "Bread")
        s = native_link_score(tm, tm.product.row.base_price * 2, 0, 0)
        assert s == 0.0

    def test_quality_raises_score(self):
        sim, town = bread_town()
        tm = sim.economy.town_market(town, "Bread")
        low = native_link_score(tm, 1.0, 10, 0)
        high = native_link_score(tm, 1.0, 50, 0)
        assert high > low

    def test_brand_raises_score(self):
        sim, town = bread_town()
        tm = sim.economy.town_market(town, "Bread")
        low = native_link_score(tm, 1.0, 0, 10)
        high = native_link_score(tm, 1.0, 0, 50)
        assert high > low


# --- N11: score drop penalty ------------------------------------------------


class TestScoreDrop:
    def test_score_drop_reduces_quantity(self):
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=50)
        link.quantity = 100.0
        old_score = link.score
        link.seller.quality = 10.0
        link.adjust_score()
        assert link.score < old_score
        drop = old_score - link.score
        expected = 100.0 * max(0.0, 1.0 - drop / 100.0)
        assert link.quantity == pytest.approx(expected)

    def test_score_increase_does_not_reduce_quantity(self):
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=10)
        link.quantity = 100.0
        link.seller.quality = 80.0
        link.adjust_score()
        assert link.quantity == 100.0


# --- N4-N7: transfer system ------------------------------------------------


class TestGapFunctions:
    def test_reduce_gap_worse_link_positive(self):
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=0, price=3.0)
        tm = link.buyer
        gap = _reduce_gap(link, tm)
        assert gap > 0

    def test_reduce_gap_good_link_zero(self):
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=80, price=0.5)
        tm = link.buyer
        gap = _reduce_gap(link, tm)
        assert gap == 0.0

    def test_increase_gap_good_link_positive(self):
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=80, price=0.5)
        tm = link.buyer
        gap = _increase_gap(link, tm)
        assert gap > 0

    def test_take_gap_better_wins(self):
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        good = _link_in_town(sim, town, corp, quality=80, price=0.5)
        bad = _link_in_town(sim, town, corp, quality=10, price=2.0)
        tm = good.buyer
        assert _take_gap(good, bad, tm) > 0
        assert _take_gap(bad, good, tm) == 0.0


class TestConsumerPass:
    def test_single_seller_grows_when_above_reference(self):
        """One seller with score above reference should gain quantity from N5."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=80, price=0.5)
        tm = link.buyer
        link.quantity = 0.0
        sim.economy.market.consumer_pass(tm)
        assert link.quantity > 0

    def test_single_seller_stalls_when_below_reference(self):
        """One seller below reference gets no increase from N5."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=0, price=3.0)
        tm = link.buyer
        link.quantity = 0.0
        sim.economy.market.consumer_pass(tm)
        assert link.quantity == 0.0

    def test_better_seller_takes_from_worse(self):
        """N6: better seller takes quantity from worse one."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        good = _link_in_town(sim, town, corp, quality=80, price=0.5)
        bad = _link_in_town(sim, town, corp, quality=10, price=2.0)
        tm = good.buyer
        bad.quantity = 100.0
        good.quantity = 0.0
        sim.economy.market.consumer_pass(tm)
        assert good.quantity > 0
        assert bad.quantity < 100.0

    def test_oversupply_trim(self):
        """Each link loses q/50 from the oversupply trim."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=50)
        tm = link.buyer
        link.quantity = tm.demand_per_day * 10
        before = link.quantity
        sim.economy.market.consumer_pass(tm)
        assert link.quantity < before

    def test_unmet_demand_accumulated(self):
        """K2: unmet demand accumulates when supply < demand."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=0, price=3.0)
        tm = link.buyer
        link.quantity = 0.0
        tm.unmet_demand_sum = 0.0
        sim.economy.market.consumer_pass(tm)
        assert tm.unmet_demand_sum > 0


# --- K1: market share -------------------------------------------------------


class TestMarketShare:
    def test_single_corp_gets_100(self):
        sim, town = bread_town()
        eco = sim.economy
        corp = eco.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=80, price=0.5)
        link.quantity_sum = 1000.0
        tm = link.buyer
        tm.unmet_demand_sum = 0.0
        eco._compute_market_shares()
        assert corp.market_share[link.product.id] == 100

    def test_two_corps_split(self):
        sim, town = bread_town()
        eco = sim.economy
        c1 = eco.add_corp("A")
        c2 = eco.add_corp("B")
        l1 = _link_in_town(sim, town, c1, quality=50)
        l2 = _link_in_town(sim, town, c2, quality=50)
        l1.quantity_sum = 600.0
        l2.quantity_sum = 400.0
        l1.buyer.unmet_demand_sum = 0.0
        eco._compute_market_shares()
        pid = l1.product.id
        assert c1.market_share[pid] == 60
        assert c2.market_share[pid] == 40

    def test_unmet_demand_dilutes_share(self):
        sim, town = bread_town()
        eco = sim.economy
        corp = eco.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=80, price=0.5)
        link.quantity_sum = 500.0
        tm = link.buyer
        tm.unmet_demand_sum = 500.0
        eco._compute_market_shares()
        assert corp.market_share[link.product.id] == 50


# --- TownMarket reference levels --------------------------------------------


class TestTownMarketWeights:
    def test_weights_sum_to_100(self):
        sim, town = bread_town()
        tm = sim.economy.town_market(town, "Bread")
        assert tm.price_weight + tm.score_in_weight + tm.brand_weight == 100

    def test_price_weight_clamped(self):
        sim, town = bread_town()
        tm = sim.economy.town_market(town, "Bread")
        assert 20 <= tm.price_weight <= 90

    def test_ref_score_positive(self):
        sim, town = bread_town()
        tm = sim.economy.town_market(town, "Bread")
        assert tm.ref_score >= 0

    def test_random_walk_changes_refs(self):
        sim, town = bread_town()
        tm = sim.economy.town_market(town, "Bread")
        before_price = tm.ref_price
        before_score = tm.ref_score
        for _ in range(100):
            tm.random_walk_refs(sim.rng)
        assert tm.ref_price != before_price or tm.ref_score != before_score
