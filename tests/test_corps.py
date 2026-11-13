"""Corporation system: financial accounting, interest, loans, bankruptcy."""

import pytest

from capitalism.economy import (
    CORP_AI,
    CORP_PLAYER,
    Corporation,
)
from capitalism.jobs import CAT_LOAN_INTEREST, CAT_SALES
from capitalism.links import BRAND_CORPORATE, BRAND_UNIQUE
from capitalism.scenario import bread_town, build_bread_chain
from capitalism.tables import CORPORATION_RULES


class TestCorporationInit:
    def test_defaults(self):
        corp = Corporation(0, "TestCorp")
        assert corp.corp_type == CORP_PLAYER
        assert corp.liabilities == 0.0
        assert corp.brand_strategy == BRAND_CORPORATE
        assert corp.dividend_ratio == 0
        assert corp.dividend_auto is True
        assert corp.peak_revenue == 0.0
        assert corp.ledger.cash == 0.0
        assert len(corp.month_history["revenue"]) == 0

    def test_custom_type(self):
        corp = Corporation(1, "AI Corp", CORP_AI)
        assert corp.corp_type == CORP_AI


class TestIncomeStatement:
    def test_revenue_and_expenses(self):
        corp = Corporation(0, "Test")
        corp.ledger.post(CAT_SALES, 1000.0)
        corp.ledger.post(1, 200.0)  # salaries
        corp.ledger.post(2, 100.0)  # overhead
        assert corp.revenue == 1000.0
        assert corp.operating_expenses == 300.0
        assert corp.operating_profit == 700.0

    def test_net_profit_includes_other(self):
        corp = Corporation(0, "Test")
        corp.ledger.post(CAT_SALES, 1000.0)
        corp.ledger.post(1, 200.0)  # salaries
        corp.ledger.post(CAT_LOAN_INTEREST, 50.0)  # loan interest (other)
        assert corp.operating_profit == 800.0
        assert corp.other_profit == 50.0
        assert corp.net_profit == 850.0

    def test_cost_of_sales_composite(self):
        corp = Corporation(0, "Test")
        corp.ledger.post(4, 100.0)  # purchase cost
        corp.ledger.post(5, 30.0)  # freight cost
        corp.ledger.post(8, 20.0)  # raw material
        assert corp.cost_of_sales == 150.0


class TestBalanceSheet:
    def test_total_assets_with_no_firms(self):
        corp = Corporation(0, "Test")
        corp.ledger.cash = 5000.0
        assert corp.total_assets([]) == 5000.0

    def test_net_worth_subtracts_liabilities(self):
        corp = Corporation(0, "Test")
        corp.ledger.cash = 10000.0
        corp.liabilities = 3000.0
        assert corp.net_worth([]) == 7000.0

    def test_total_assets_includes_firm_values(self):
        sim, town = bread_town(1)
        build_bread_chain(sim, town)
        eco = sim.economy
        corp = eco.corps[0]
        assets = corp.total_assets(eco.firms)
        assert assets > corp.ledger.cash


class TestBankLoans:
    def test_borrow_increases_cash_and_debt(self):
        corp = Corporation(0, "Test")
        corp.ledger.cash = 1000.0
        corp.borrow(500.0)
        assert corp.ledger.cash == 1500.0
        assert corp.liabilities == 500.0

    def test_repay_decreases_both(self):
        corp = Corporation(0, "Test")
        corp.ledger.cash = 1000.0
        corp.liabilities = 800.0
        corp.repay(300.0)
        assert corp.ledger.cash == 700.0
        assert corp.liabilities == 500.0

    def test_repay_capped_at_debt(self):
        corp = Corporation(0, "Test")
        corp.ledger.cash = 1000.0
        corp.liabilities = 200.0
        corp.repay(500.0)
        assert corp.ledger.cash == 800.0
        assert corp.liabilities == 0.0

    def test_repay_capped_at_cash(self):
        corp = Corporation(0, "Test")
        corp.ledger.cash = 100.0
        corp.liabilities = 500.0
        corp.repay(300.0)
        assert corp.ledger.cash == 0.0
        assert corp.liabilities == 400.0

    def test_credit_limit(self):
        corp = Corporation(0, "Test")
        corp.ledger.cash = 5000.0
        corp.liabilities = 2000.0
        assert corp.credit_limit([]) == 3000.0

    def test_credit_limit_floor_zero(self):
        corp = Corporation(0, "Test")
        corp.ledger.cash = 1000.0
        corp.liabilities = 5000.0
        assert corp.credit_limit([]) == 0.0


class TestDailyFinance:
    def test_no_charges_when_solvent(self):
        corp = Corporation(0, "Test")
        corp.ledger.cash = 1000.0
        corp.daily_finance(10.0)
        assert corp.ledger.cash == 1000.0

    def test_overdraft_interest(self):
        corp = Corporation(0, "Test")
        corp.ledger.cash = -1_000_000.0
        corp.daily_finance(10.0)
        overdraft = 1_000_000.0 * (10.0 + CORPORATION_RULES.overdraft_spread) / 100.0 / 365.0
        debt_on_new = overdraft * 10.0 / 100.0 / 365.0
        assert corp.ledger.month[CAT_LOAN_INTEREST] == pytest.approx(
            overdraft + debt_on_new, rel=1e-6
        )
        assert corp.liabilities == pytest.approx(overdraft, rel=1e-6)

    def test_debt_interest(self):
        corp = Corporation(0, "Test")
        corp.ledger.cash = 5000.0
        corp.liabilities = 1_000_000.0
        corp.daily_finance(10.0)
        expected_daily = 1_000_000.0 * 10.0 / 100.0 / 365.0
        assert corp.ledger.month[CAT_LOAN_INTEREST] == pytest.approx(expected_daily, rel=1e-6)

    def test_overdraft_plus_debt(self):
        """When cash < 0 AND has liabilities, both charges apply."""
        corp = Corporation(0, "Test")
        corp.ledger.cash = -500_000.0
        corp.liabilities = 1_000_000.0
        corp.daily_finance(10.0)
        overdraft = 500_000.0 * 12.0 / 100.0 / 365.0
        new_liabilities = 1_000_000.0 + overdraft
        debt = new_liabilities * 10.0 / 100.0 / 365.0
        total = overdraft + debt
        assert corp.ledger.month[CAT_LOAN_INTEREST] == pytest.approx(total, rel=1e-4)


class TestMonthlyYearly:
    def test_monthly_tracks_peak_revenue(self):
        corp = Corporation(0, "Test")
        corp.ledger.post(CAT_SALES, 5000.0)
        corp.monthly([])
        assert corp.peak_revenue == 5000.0
        corp.ledger.post(CAT_SALES, 3000.0)
        corp.monthly([])
        assert corp.peak_revenue == 5000.0
        corp.ledger.post(CAT_SALES, 8000.0)
        corp.monthly([])
        assert corp.peak_revenue == 8000.0

    def test_monthly_history_rotation(self):
        corp = Corporation(0, "Test")
        for i in range(15):
            corp.ledger.post(CAT_SALES, float(i * 100))
            corp.monthly([])
        assert len(corp.month_history["revenue"]) == 12

    def test_monthly_rolls_ledger(self):
        corp = Corporation(0, "Test")
        corp.ledger.post(CAT_SALES, 1000.0)
        assert corp.ledger.month[CAT_SALES] == 1000.0
        corp.monthly([])
        assert corp.ledger.month[CAT_SALES] == 0.0
        assert corp.ledger.last_month[CAT_SALES] == 1000.0

    def test_yearly_history(self):
        corp = Corporation(0, "Test")
        corp.ledger.post(CAT_SALES, 12000.0)
        corp.yearly([])
        assert len(corp.year_history["revenue"]) == 1
        assert corp.year_history["revenue"][0] == 12000.0

    def test_yearly_rolls_year_counters(self):
        corp = Corporation(0, "Test")
        corp.ledger.post(CAT_SALES, 5000.0)
        corp.yearly([])
        assert corp.ledger.year[CAT_SALES] == 0.0
        assert corp.ledger.total[CAT_SALES] == 5000.0


class TestBankruptcy:
    def test_not_bankrupt_with_positive_cash(self):
        corp = Corporation(0, "Test")
        corp.ledger.cash = 100.0
        assert not corp.is_bankrupt

    def test_bankrupt_with_negative_cash(self):
        corp = Corporation(0, "Test")
        corp.ledger.cash = -1.0
        assert corp.is_bankrupt


class TestInterestRate:
    def test_initial_rate(self):
        sim, _ = bread_town(1)
        assert sim.economy.interest_rate == CORPORATION_RULES.interest_rate_default

    def test_rate_history_starts_with_default(self):
        sim, _ = bread_town(1)
        assert sim.economy.interest_rate_history == [CORPORATION_RULES.interest_rate_default]

    def test_rate_adjustment_weak_economy(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        for town in sim.world.towns:
            town.per_capita_gnp = 2000.0
        old_rate = eco.interest_rate
        eco.adjust_interest_rate()
        assert eco.interest_rate == old_rate + CORPORATION_RULES.interest_rate_step

    def test_rate_never_below_floor(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        eco.interest_rate = CORPORATION_RULES.interest_rate_floor
        for town in sim.world.towns:
            town.per_capita_gnp = 20000.0
        for _ in range(200):
            eco.adjust_interest_rate()
        assert eco.interest_rate >= CORPORATION_RULES.interest_rate_floor


class TestBrandStrategy:
    def test_default_is_corporate(self):
        corp = Corporation(0, "Test")
        assert corp.brand_strategy == BRAND_CORPORATE

    def test_can_set_strategy(self):
        corp = Corporation(0, "Test")
        corp.brand_strategy = BRAND_UNIQUE
        assert corp.brand_strategy == BRAND_UNIQUE


class TestCorpIntegration:
    def test_bread_chain_corps_daily_no_crash(self):
        """Corps daily runs without error on the bread chain scenario."""
        sim, town = bread_town(1)
        build_bread_chain(sim, town)
        sim.advance_days(60)
        eco = sim.economy
        assert len(eco.corps) >= 1
        corp = eco.corps[0]
        assert corp.ledger.cash != 0.0

    def test_weak_economy_raises_rate(self):
        """In a weak economy, the interest rate rises every month."""
        sim, _ = bread_town(1)
        eco = sim.economy
        for t in sim.world.towns:
            t.per_capita_gnp = 2000.0
            t.tier = 0
        initial = eco.interest_rate
        eco.adjust_interest_rate()
        assert eco.interest_rate == initial + CORPORATION_RULES.interest_rate_step

    def test_corp_monthly_history_populated(self):
        """After several months, corporation history has data."""
        sim, town = bread_town(1)
        build_bread_chain(sim, town)
        sim.advance_days(120)
        corp = sim.economy.corps[0]
        assert len(corp.month_history["revenue"]) > 0

    def test_hash_deterministic(self):
        """Same seed produces same hash — corporation processing is deterministic."""
        sim1, town1 = bread_town(1)
        build_bread_chain(sim1, town1)
        sim1.advance_days(120)
        sim2, town2 = bread_town(1)
        build_bread_chain(sim2, town2)
        sim2.advance_days(120)
        assert sim1.state_hash() == sim2.state_hash()
