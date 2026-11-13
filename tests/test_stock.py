"""Stock market: shares, price movement, trading, dividends, metrics."""

import pytest

from capitalism.rng import Rng
from capitalism.scenario import bread_town, build_bread_chain
from capitalism.stock import (
    MAX_CORPS,
    MAX_PERSONS,
    Stock,
    ai_buyback,
    ai_invest,
    buy_shares,
    check_sec_violation,
    compute_ai_dividend,
    daily_price_update,
    issue_shares,
    mark_to_market,
    pay_dividend,
    price_impact,
    sell_shares,
    stock_monthly,
    stock_yearly,
    tender_cooldown_days,
    tender_offer_price,
)


class TestStockInit:
    def test_basic_creation(self):
        s = Stock(0, 100_000.0, 10.0)
        assert s.corp_id == 0
        assert s.price == 10.0
        assert s.total_shares == 10_000
        assert s.public_float == 10_000
        assert s.insider_held == 0

    def test_min_price(self):
        s = Stock(0, 100.0, 0.001)
        assert s.price >= 0.01

    def test_min_shares(self):
        s = Stock(0, 0.5, 10.0)
        assert s.total_shares >= 1

    def test_holdings_arrays(self):
        s = Stock(0, 100_000.0, 10.0)
        assert len(s.holdings_corps) == MAX_CORPS
        assert len(s.holdings_persons) == MAX_PERSONS
        assert all(h == 0 for h in s.holdings_corps)


class TestMetrics:
    def test_equity_per_share(self):
        s = Stock(0, 100_000.0, 10.0)
        assert s.equity_per_share(50_000.0) == pytest.approx(5.0)

    def test_earnings_per_share(self):
        s = Stock(0, 100_000.0, 10.0)
        assert s.earnings_per_share(20_000.0) == pytest.approx(2.0)

    def test_pe_ratio(self):
        s = Stock(0, 100_000.0, 10.0)
        assert s.pe_ratio(20_000.0) == pytest.approx(5.0)

    def test_pe_ratio_no_earnings(self):
        s = Stock(0, 100_000.0, 10.0)
        assert s.pe_ratio(0.0) == 0.0
        assert s.pe_ratio(-1000.0) == 0.0

    def test_dividend_yield(self):
        s = Stock(0, 100_000.0, 10.0)
        assert s.dividend_yield(10_000.0) == pytest.approx(1000.0)

    def test_stock_return(self):
        s = Stock(0, 100_000.0, 10.0)
        s.daily_prices = [8.0, 9.0, 10.0]
        assert s.stock_return() == pytest.approx(0.25)

    def test_stock_return_no_history(self):
        s = Stock(0, 100_000.0, 10.0)
        assert s.stock_return() == 0.0


class TestDailyPriceMovement:
    def test_price_changes(self):
        s = Stock(0, 100_000.0, 10.0)
        rng = Rng(42)
        old_price = s.price
        daily_price_update(s, rng, 1000.0)
        assert s.price != old_price
        assert s.price > 0

    def test_negative_earnings_push_down(self):
        rng = Rng(42)
        prices_down = []
        for _ in range(50):
            s = Stock(0, 100_000.0, 10.0)
            r = Rng(rng.randint(0, 999999))
            for _ in range(30):
                daily_price_update(s, r, -10000.0)
            prices_down.append(s.price)
        avg = sum(prices_down) / len(prices_down)
        assert avg < 10.0  # negative earnings should tend to push price down

    def test_price_floor_zero(self):
        s = Stock(0, 100.0, 0.01)
        rng = Rng(42)
        for _ in range(100):
            daily_price_update(s, rng, -100000.0, climate=4)
        assert s.price >= 0.0

    def test_daily_history_capped_at_30(self):
        s = Stock(0, 100_000.0, 10.0)
        rng = Rng(42)
        for _ in range(50):
            daily_price_update(s, rng, 0.0)
        assert len(s.daily_prices) == 30

    def test_climate_affects_volatility(self):
        rng1 = Rng(42)
        rng2 = Rng(42)
        s1 = Stock(0, 100_000.0, 10.0)
        s2 = Stock(0, 100_000.0, 10.0)
        for _ in range(30):
            daily_price_update(s1, rng1, 0.0, climate=0)  # excellent
            daily_price_update(s2, rng2, 0.0, climate=4)  # very bad
        # Very bad climate should have more price movement
        var1 = max(s1.daily_prices) - min(s1.daily_prices)
        var2 = max(s2.daily_prices) - min(s2.daily_prices)
        assert var2 > var1

    def test_deterministic(self):
        def run(seed):
            s = Stock(0, 100_000.0, 10.0)
            rng = Rng(seed)
            for _ in range(30):
                daily_price_update(s, rng, 1000.0)
            return s.price
        assert run(42) == run(42)


class TestTrading:
    def test_buy_from_float(self):
        s = Stock(0, 100_000.0, 10.0)
        cost = buy_shares(s, "corp", 1, 100)
        assert cost > 0
        assert s.holdings_corps[1] == 100
        assert s.public_float == s.total_shares - 100

    def test_buy_person(self):
        s = Stock(0, 100_000.0, 10.0)
        cost = buy_shares(s, "person", 0, 50)
        assert cost > 0
        assert s.holdings_persons[0] == 50

    def test_buy_increases_price(self):
        s = Stock(0, 100_000.0, 10.0)
        old_price = s.price
        buy_shares(s, "corp", 1, 500)
        assert s.price > old_price

    def test_sell_shares(self):
        s = Stock(0, 100_000.0, 10.0)
        s.holdings_corps[1] = 500
        proceeds = sell_shares(s, "corp", 1, 200)
        assert proceeds > 0
        assert s.holdings_corps[1] == 300

    def test_sell_decreases_price(self):
        s = Stock(0, 100_000.0, 10.0)
        s.holdings_corps[1] = 500
        old_price = s.price
        sell_shares(s, "corp", 1, 500)
        assert s.price < old_price

    def test_sell_more_than_held(self):
        s = Stock(0, 100_000.0, 10.0)
        s.holdings_corps[1] = 100
        sell_shares(s, "corp", 1, 500)
        assert s.holdings_corps[1] == 0

    def test_buy_zero(self):
        s = Stock(0, 100_000.0, 10.0)
        cost = buy_shares(s, "corp", 1, 0)
        assert cost == 0.0

    def test_price_impact_large_trade(self):
        s = Stock(0, 10_000.0, 10.0)
        impact = price_impact(500, s.total_shares, s.price)
        assert impact > 0
        small_impact = price_impact(10, s.total_shares, s.price)
        assert impact > small_impact

    def test_price_floor_ten_cents(self):
        s = Stock(0, 1000.0, 1.0)
        s.holdings_corps[1] = s.total_shares
        sell_shares(s, "corp", 1, s.total_shares)
        assert s.price >= 0.10


class TestShareIssuance:
    def test_issue_increases_total(self):
        s = Stock(0, 100_000.0, 10.0)
        old_total = s.total_shares
        issue_shares(s, 1000)
        assert s.total_shares == old_total + 1000

    def test_issue_dilutes_price(self):
        s = Stock(0, 100_000.0, 10.0)
        old_price = s.price
        issue_shares(s, 5000)
        assert s.price < old_price

    def test_issue_returns_proceeds(self):
        s = Stock(0, 100_000.0, 10.0)
        proceeds = issue_shares(s, 100)
        assert proceeds > 0

    def test_issue_zero(self):
        s = Stock(0, 100_000.0, 10.0)
        proceeds = issue_shares(s, 0)
        assert proceeds == 0.0


class TestDividends:
    def test_pay_dividend_proportional(self):
        s = Stock(0, 100_000.0, 10.0)
        s.holdings_corps[1] = 5000  # 50%
        s.holdings_persons[0] = 2000  # 20%
        result = pay_dividend(s, 10_000.0)
        corp_payouts = dict(result["corps"])
        person_payouts = dict(result["persons"])
        assert corp_payouts[1] == pytest.approx(5000.0)
        assert person_payouts[0] == pytest.approx(2000.0)

    def test_pay_zero_dividend(self):
        s = Stock(0, 100_000.0, 10.0)
        result = pay_dividend(s, 0.0)
        assert result["corps"] == []
        assert result["persons"] == []

    def test_dividend_history(self):
        s = Stock(0, 100_000.0, 10.0)
        pay_dividend(s, 5000.0)
        assert len(s.dividend_history) == 1
        assert s.dividend_history[0] == 5000.0

    def test_ai_dividend_profitable(self):
        """R4: native FUN_00040fd5 — surplus cash triggers payout."""
        s = Stock(0, 100_000.0, 10.0)
        rng = Rng(42)
        div = compute_ai_dividend(s, 200_000.0, 25_000_000.0, 0.0, 50_000.0, 50, rng)
        assert div > 0

    def test_ai_dividend_unprofitable(self):
        """Negative earnings + equity floor blocks payout."""
        s = Stock(0, 100_000.0, 10.0)
        rng = Rng(42)
        div = compute_ai_dividend(s, 100_000.0, 100_000.0, 0.0, -10_000.0, 50, rng)
        assert div == 0.0

    def test_ai_dividend_equity_cap(self):
        """Step 5: net_equity > cash → no dividend."""
        s = Stock(0, 100_000.0, 10.0)
        rng = Rng(42)
        div = compute_ai_dividend(s, 50_000_000.0, 1_000_000.0, 0.0, 100_000.0, 50, rng)
        assert div == 0.0  # net_equity(50M) > cash(1M)

    def test_ai_dividend_min_per_share(self):
        """Below 0.1 per share the payout is suppressed."""
        s = Stock(0, 100_000.0, 10.0)
        rng = Rng(99)
        div = compute_ai_dividend(s, 200_000.0, 200_010.0, 0.0, 1.0, 50, rng)
        assert div == 0.0  # tiny earnings → per-share < 0.1

    def test_ai_dividend_deterministic(self):
        """Same seed → same result."""
        def run(seed):
            s = Stock(0, 100_000.0, 10.0)
            return compute_ai_dividend(s, 200_000.0, 25_000_000.0, 0.0, 50_000.0, 50, Rng(seed))
        assert run(42) == run(42)


class TestMonthlyYearly:
    def test_monthly_records_average(self):
        s = Stock(0, 100_000.0, 10.0)
        rng = Rng(42)
        for _ in range(30):
            daily_price_update(s, rng, 0.0)
        stock_monthly(s)
        assert len(s.monthly_prices) == 1

    def test_monthly_caps_at_30(self):
        s = Stock(0, 100_000.0, 10.0)
        rng = Rng(42)
        for _ in range(35):
            daily_price_update(s, rng, 0.0)
            stock_monthly(s)
        assert len(s.monthly_prices) == 30

    def test_yearly_records(self):
        s = Stock(0, 100_000.0, 10.0)
        stock_yearly(s, 50_000.0)
        assert len(s.yearly_prices) == 1
        assert len(s.yearly_earnings) == 1


class TestAITrading:
    def test_buyback_when_float_high(self):
        s = Stock(0, 100_000.0, 10.0)
        # All shares are public float — should trigger buyback
        rng = Rng(42)
        total = s.total_shares
        cost = ai_buyback(s, 0, rng)
        assert cost > 0
        assert s.holdings_corps[0] == 0  # S3: bought-back shares are retired
        assert s.total_shares < total

    def test_buyback_skipped_when_float_low(self):
        s = Stock(0, 100_000.0, 10.0)
        s.holdings_corps[0] = s.total_shares  # all held
        rng = Rng(42)
        cost = ai_buyback(s, 0, rng)
        assert cost == 0.0

    def test_invest_in_other_corp(self):
        s = Stock(1, 100_000.0, 10.0)
        rng = Rng(42)
        cost = ai_invest(s, 0, 50_000.0, rng)
        assert cost > 0
        assert s.holdings_corps[0] > 0

    def test_invest_zero_surplus(self):
        s = Stock(1, 100_000.0, 10.0)
        rng = Rng(42)
        cost = ai_invest(s, 0, 0.0, rng)
        assert cost == 0.0


class TestSECRules:
    def test_player_owns_shares_blocks_corp_buy(self):
        s = Stock(1, 100_000.0, 10.0)
        s.holdings_persons[0] = 100
        assert check_sec_violation(0, s, 0, [0]) is True

    def test_no_violation_when_no_personal_shares(self):
        s = Stock(1, 100_000.0, 10.0)
        assert check_sec_violation(0, s, 0, [0]) is False

    def test_main_corp_owns_blocks_other_corp(self):
        s = Stock(2, 100_000.0, 10.0)
        s.holdings_corps[0] = 100
        assert check_sec_violation(1, s, None, [0, 1]) is True


class TestTenderOffers:
    def test_ceo_demands_premium(self):
        s = Stock(0, 100_000.0, 10.0)
        rng = Rng(42)
        ceo_price = tender_offer_price(s, True, 50, rng)
        rng2 = Rng(42)
        regular_price = tender_offer_price(s, False, 50, rng2)
        assert ceo_price > regular_price

    def test_cooldown_longer_for_success(self):
        rng = Rng(42)
        success_cd = tender_cooldown_days(False, True, rng)
        rng2 = Rng(42)
        fail_cd = tender_cooldown_days(False, False, rng2)
        assert success_cd > fail_cd


class TestMarkToMarket:
    def test_portfolio_value(self):
        s1 = Stock(0, 100_000.0, 10.0)
        s2 = Stock(1, 100_000.0, 20.0)
        s1.holdings_corps[2] = 100  # corp 2 holds 100 shares of s1
        s2.holdings_corps[2] = 50   # corp 2 holds 50 shares of s2
        stocks: list[Stock | None] = [s1, s2]
        current, pnl = mark_to_market(stocks, 2, 0.0)
        assert current == pytest.approx(100 * 10.0 + 50 * 20.0)
        assert pnl == pytest.approx(current)

    def test_pnl_calculation(self):
        s1 = Stock(0, 100_000.0, 10.0)
        s1.holdings_corps[1] = 100
        prev = 900.0
        current, pnl = mark_to_market([s1], 1, prev)
        assert current == pytest.approx(1000.0)
        assert pnl == pytest.approx(100.0)


class TestEconomyIntegration:
    def test_stock_created_for_corp(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        from capitalism.economy import CORP_PLAYER
        corp = eco.add_corp("Test Corp", CORP_PLAYER)
        assert eco.stocks[corp.id] is not None
        assert eco.stocks[corp.id].corp_id == corp.id

    def test_no_stock_for_government(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        from capitalism.economy import CORP_GOVERNMENT
        corp = eco.add_corp("Gov", CORP_GOVERNMENT)
        assert eco.stocks[corp.id] is None

    def test_stocks_daily_runs(self):
        sim, town = bread_town(1)
        build_bread_chain(sim, town)
        sim.advance_days(30)
        # Stocks should have daily history
        for stock in sim.economy.stocks:
            if stock is not None:
                assert len(stock.daily_prices) > 0

    def test_determinism_with_stocks(self):
        def run(seed):
            sim, town = bread_town(seed)
            build_bread_chain(sim, town)
            sim.advance_days(60)
            return sim.state_hash()
        assert run(1) == run(1)

    def test_full_sim_120_days(self):
        sim, town = bread_town(1)
        build_bread_chain(sim, town)
        sim.advance_days(120)
        # Should not crash and stocks should have history
        corp_stock = sim.economy.stocks[0]
        assert corp_stock is not None
        assert len(corp_stock.daily_prices) == 30
        assert len(corp_stock.monthly_prices) > 0
