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
        sim.economy.market.consumer_pass(tm, 0, 1)
        assert link.quantity > 0

    def test_single_seller_stalls_when_below_reference(self):
        """One seller below reference gets no increase from N5."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=0, price=3.0)
        tm = link.buyer
        link.quantity = 0.0
        sim.economy.market.consumer_pass(tm, 0, 1)
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
        sim.economy.market.consumer_pass(tm, 0, 1)
        assert good.quantity > 0
        assert bad.quantity < 100.0

    def test_oversupply_trim(self):
        """Each link loses q/50 only when supply exceeds demand."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=50)
        tm = link.buyer
        link.quantity = tm.demand_per_day * 10
        before = link.quantity
        sim.economy.market.consumer_pass(tm, 0, 1)
        assert link.quantity < before

    def test_unmet_demand_accumulated(self):
        """K2: unmet demand accumulates when supply < demand."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=0, price=3.0)
        tm = link.buyer
        link.quantity = 0.0
        tm.unmet_demand_sum = 0.0
        sim.economy.market.consumer_pass(tm, 0, 1)
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
        eco._compute_market_shares(31)
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
        eco._compute_market_shares(31)
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
        eco._compute_market_shares(31)
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


# --- R11: per-factor clamping in gap functions --------------------------------


class TestPerFactorClamping:
    def test_reduce_gap_no_cross_factor_offset(self):
        """Being better on score shouldn't offset being worse on price (R11)."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=80, price=2.0)
        tm = link.buyer
        tm.ref_score = 0.0
        tm.ref_price = 0.5
        gap = _reduce_gap(link, tm)
        assert gap > 0

    def test_increase_gap_no_cross_factor_offset(self):
        """Being worse on score shouldn't offset being better on price (R11)."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=0, price=0.1)
        tm = link.buyer
        tm.ref_score = 100.0
        tm.ref_price = 2.0
        gap = _increase_gap(link, tm)
        assert gap > 0


# --- R12: price denominator uses ref_price in reduce -------------------------


class TestPriceDenominator:
    def test_reduce_uses_ref_price_in_denominator(self):
        """N4 denominator is ref_price + 0.1, not link.price + 0.1."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link_cheap = _link_in_town(sim, town, corp, quality=50, price=0.5)
        link_expensive = _link_in_town(sim, town, corp, quality=50, price=5.0)
        tm = link_cheap.buyer
        tm.ref_price = 1.0
        link_cheap.price = 2.0
        link_expensive.price = 2.0
        link_cheap.score = link_cheap.compute_score()
        link_expensive.score = link_expensive.compute_score()
        gap_c = _reduce_gap(link_cheap, tm)
        gap_e = _reduce_gap(link_expensive, tm)
        assert gap_c == pytest.approx(gap_e)


# --- R15: even-day supply sum ------------------------------------------------


class TestEvenDaySupply:
    def test_supply_updated_on_even_day(self):
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=80, price=0.5)
        tm = link.buyer
        link.quantity = 10.0
        tm.supply_today = 0.0
        sim.economy.market.consumer_pass(tm, 100, 1)  # even day_serial
        assert tm.supply_today > 0

    def test_supply_not_updated_on_odd_day(self):
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=80, price=0.5)
        tm = link.buyer
        link.quantity = 10.0
        tm.supply_today = 0.0
        sim.economy.market.consumer_pass(tm, 101, 1)  # odd day_serial
        assert tm.supply_today == 0.0


# --- R11: oversupply trim only when supply > demand --------------------------


class TestOversupplyGate:
    def test_no_trim_when_undersupplied(self):
        """Trim shouldn't run when supply < demand."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=80, price=0.5)
        tm = link.buyer
        link.quantity = tm.demand_per_day * 0.1
        before = link.quantity
        sim.economy.market.consumer_pass(tm, 0, 1)
        assert link.quantity >= before


# --- R11: projection gate for increase/take ----------------------------------


class TestProjectionGate:
    def test_high_projection_blocks_growth(self):
        """A link whose projected quantity >= 2 × projected flow skips increase/take."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=80, price=0.5)
        tm = link.buyer
        link.quantity = 0.0
        link.quantity_prev = 1000.0
        link.flow_prev = 1.0
        before = link.quantity
        sim.economy.market.consumer_pass(tm, 0, 15)
        assert link.quantity == before

    def test_new_link_still_grows(self):
        """A link with no flow history can still get increase/take."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=80, price=0.5)
        tm = link.buyer
        link.quantity = 0.0
        link.quantity_prev = 0.0
        link.flow_prev = 0.0
        sim.economy.market.consumer_pass(tm, 0, 1)
        assert link.quantity > 0


# --- R16: score drop uses (1 − drop/100) -----------------------------------


class TestScoreDropNative:
    def test_score_drop_keeps_proportional_quantity(self):
        """A score drop on a live link uses q × (1 − drop/100) (N11)."""
        sim, town = bread_town()
        corp = sim.economy.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=50, price=0.5)
        link.quantity = 100.0
        old_score = link.score
        link.price = link.product.row.base_price * 1.5
        link.adjust_score()
        new_score = link.score
        if new_score < old_score:
            drop = old_score - new_score
            expected = 100.0 * max(0.0, 1.0 - drop / 100.0)
            assert link.quantity == pytest.approx(expected)


# --- Link monthly roll saves prev fields -----------------------------------


class TestMonthlyRoll:
    def test_quantity_prev_saved(self):
        sim, town = bread_town()
        eco = sim.economy
        corp = eco.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=50)
        link.quantity_sum = 42.0
        eco.market.monthly(0, eco)
        assert link.quantity_prev == 42.0
        assert link.quantity_sum == 0.0

    def test_flow_prev_saved(self):
        sim, town = bread_town()
        eco = sim.economy
        corp = eco.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=50)
        link.units_month[0] = 99.0
        eco.market.monthly(0, eco)
        assert link.flow_prev == 99.0
        assert link.units_month[0] == 0.0


# ---------------------------------------------------------------------------
# N10 price swap between cross-owned links
# ---------------------------------------------------------------------------


class TestN10PriceSwap:
    """N10: when two consumer links share corp_id but differ on owner_corp_id,
    the cross-owned link adopts the native owner's price."""

    @staticmethod
    def _setup(sim, town):
        eco = sim.economy
        corp_a = eco.add_corp("A")
        corp_b = eco.add_corp("B")
        link_a = _link_in_town(sim, town, corp_a, quality=50, price=10.0)
        link_b = _link_in_town(sim, town, corp_b, quality=50, price=20.0)
        return eco, link_a, link_b

    def test_swap_fires_on_cross_ownership(self):
        sim, town = bread_town()
        eco, link_a, link_b = self._setup(sim, town)
        tm = eco.town_market(town, "Bread")
        # Simulate cross-ownership: both grouped under corp_b,
        # but link_a is owned by corp_a (the cross-owned one).
        link_a.corp_id = link_b.seller.firm.owner.id
        link_b.corp_id = link_b.seller.firm.owner.id
        link_b.owner_corp_id = link_b.seller.firm.owner.id
        # link_a.owner_corp_id stays as corp_a's id (different from corp_id)
        eco.market._sum_supply(tm)
        assert link_a.price == pytest.approx(20.0)
        assert link_b.price == pytest.approx(20.0)

    def test_no_swap_when_same_owner(self):
        sim, town = bread_town()
        eco, link_a, link_b = self._setup(sim, town)
        tm = eco.town_market(town, "Bread")
        # Same corp group and same owner — no swap.
        link_a.corp_id = link_a.seller.firm.owner.id
        link_b.corp_id = link_b.seller.firm.owner.id
        eco.market._sum_supply(tm)
        assert link_a.price == pytest.approx(10.0)
        assert link_b.price == pytest.approx(20.0)

    def test_supply_total_unaffected(self):
        sim, town = bread_town()
        eco, link_a, link_b = self._setup(sim, town)
        tm = eco.town_market(town, "Bread")
        link_a.quantity = 5.0
        link_b.quantity = 7.0
        eco.market._sum_supply(tm)
        assert tm.supply_today == pytest.approx(12.0)


# ---------------------------------------------------------------------------
# K1 prorated market-share projection
# ---------------------------------------------------------------------------


class TestK1Prorate:
    """K1: market share uses prorated projection from native formula."""

    def test_31_day_month_no_proration(self):
        """For a 31-day month, proration factor is 0 — no last-month boost."""
        sim, town = bread_town()
        eco = sim.economy
        corp = eco.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=50)
        link.quantity_sum = 100.0
        link.quantity_prev = 200.0
        eco._compute_market_shares(31)
        assert corp.market_share[link.product.id] == 100

    def test_28_day_month_adds_proration(self):
        """For a 28-day month, (31-28)/31 of last month is added."""
        sim, town = bread_town()
        eco = sim.economy
        corp_a = eco.add_corp("A")
        corp_b = eco.add_corp("B")
        link_a = _link_in_town(sim, town, corp_a, quality=50)
        link_b = _link_in_town(sim, town, corp_b, quality=50)
        link_a.quantity_sum = 100.0
        link_a.quantity_prev = 0.0
        link_b.quantity_sum = 100.0
        link_b.quantity_prev = 310.0
        # With 28-day month: prorate = 3/31
        # projected_a = 100 + 3/31 * 0 = 100
        # projected_b = 100 + 3/31 * 310 = 130
        # total = 230, a = round(100/230*100) = 43, b = round(130/230*100) = 57
        eco._compute_market_shares(28)
        assert corp_a.market_share[link_a.product.id] == 43
        assert corp_b.market_share[link_b.product.id] == 57

    def test_unmet_demand_prorated_in_denominator(self):
        """Unmet demand in the K1 denominator is also prorated."""
        sim, town = bread_town()
        eco = sim.economy
        corp = eco.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=50)
        link.quantity_sum = 100.0
        link.quantity_prev = 0.0
        tm = eco.town_market(town, "Bread")
        tm.unmet_demand_sum = 100.0
        tm.last_month_unmet_demand_sum = 0.0
        eco._compute_market_shares(31)
        assert corp.market_share[link.product.id] == 50
        # With last-month unmet demand and shorter month, denominator grows
        tm.unmet_demand_sum = 100.0
        tm.last_month_unmet_demand_sum = 310.0
        eco._compute_market_shares(28)
        # projected_link = 100, projected_unmet = 100 + 3/31*310 = 130
        # total = 230, share = round(100/230*100) = 43
        assert corp.market_share[link.product.id] == 43


class TestK2UnmetDemandValue:
    """K2: unmet demand accumulates gap * ref_price into value sum."""

    def test_value_sum_accumulates(self):
        sim, town = bread_town()
        eco = sim.economy
        corp = eco.add_corp("T")
        link = _link_in_town(sim, town, corp, quality=50)
        tm = eco.town_market(town, "Bread")
        tm.demand_per_day = 10.0
        link.quantity = 3.0
        tm.unmet_demand_value_sum = 0.0
        tm.unmet_demand_sum = 0.0
        eco.market.consumer_pass(tm, 2, 1)
        assert tm.unmet_demand_sum > 0
        assert tm.unmet_demand_value_sum == pytest.approx(
            tm.unmet_demand_sum * tm.ref_price
        )

    def test_value_sum_zero_when_no_demand(self):
        sim, town = bread_town()
        eco = sim.economy
        tm = eco.town_market(town, "Bread")
        tm.demand_per_day = 0.0
        tm.unmet_demand_value_sum = 0.0
        eco.market.consumer_pass(tm, 2, 1)
        assert tm.unmet_demand_value_sum == 0.0

    def test_value_sum_rolled_monthly(self):
        sim, town = bread_town()
        eco = sim.economy
        tm = eco.town_market(town, "Bread")
        tm.unmet_demand_value_sum = 42.0
        tm.last_month_unmet_demand_value_sum = 0.0
        eco.monthly()
        assert tm.last_month_unmet_demand_value_sum == 42.0
        assert tm.unmet_demand_value_sum == 0.0


class TestN2TownWeightAdj:
    """N2: per-town env factors adjust consumer-split weights."""

    def test_env_factors_shift_price_weight(self):
        sim, town = bread_town()
        eco = sim.economy
        tm = eco.town_market(town, "Bread")
        row = tm.product.row
        town.env_factors = (0.0, 0.0, 0.0)
        tm.recompute_weights()
        pw_zero = tm.price_weight
        assert pw_zero == max(20, min(90, row.w_price))
        town.env_factors = (3.0, 0.0, 0.0)
        tm.recompute_weights()
        assert tm.price_weight == max(20, min(90, row.w_price + 3))

    def test_env_factors_shift_score_in_weight(self):
        sim, town = bread_town()
        eco = sim.economy
        tm = eco.town_market(town, "Bread")
        row = tm.product.row
        town.env_factors = (0.0, 0.0, 0.0)
        tm.recompute_weights()
        sw_zero = tm.score_in_weight
        town.env_factors = (0.0, 3.0, 0.0)
        tm.recompute_weights()
        expected = max(10, min(100 - tm.price_weight, row.w_quality + 3))
        assert tm.score_in_weight == expected

    def test_price_weight_clamped_20_90(self):
        sim, town = bread_town()
        eco = sim.economy
        tm = eco.town_market(town, "Bread")
        town.env_factors = (-100.0, 0.0, 0.0)
        tm.recompute_weights()
        assert tm.price_weight == 20
        town.env_factors = (100.0, 0.0, 0.0)
        tm.recompute_weights()
        assert tm.price_weight == 90

    def test_weights_sum_to_100(self):
        sim, town = bread_town()
        eco = sim.economy
        tm = eco.town_market(town, "Bread")
        town.env_factors = (2.0, -1.0, 0.0)
        tm.recompute_weights()
        assert tm.price_weight + tm.score_in_weight + tm.brand_weight == 100

    def test_monthly_recomputes_weights(self):
        sim, town = bread_town()
        eco = sim.economy
        tm = eco.town_market(town, "Bread")
        town.env_factors = (3.0, 0.0, 0.0)
        old_pw = tm.price_weight
        eco.monthly()
        assert tm.price_weight != old_pw
