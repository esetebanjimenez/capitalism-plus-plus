"""Share trades move cash (gap audit S1, S3, S4)."""

import pytest

from capitalism.economy import CORP_AI
from capitalism.firms import InsufficientFunds
from capitalism.scenario import bread_town
from capitalism.stock import Stock


def _two_corps():
    sim, _town = bread_town()
    eco = sim.economy
    me = eco.add_corp("Me")
    other = eco.add_corp("Other", CORP_AI)
    eco.stocks[other.id] = Stock(other.id, 1e8, 10.0)
    eco.stocks[me.id] = Stock(me.id, 1e8, 10.0)
    me.ledger.cash = 5_000_000.0
    other.ledger.cash = 1_000_000.0
    return eco, me, other


def test_buy_and_sell_other_corp_moves_cash_and_stock_assets():
    eco, me, other = _two_corps()
    firms = eco.firms
    before = me.total_assets(firms)
    cost = eco.buy_stock(me, other.id, 10_000)
    assert cost > 0
    assert me.ledger.cash == pytest.approx(5_000_000.0 - cost)
    assert me.stock_assets == pytest.approx(cost)
    assert me.total_assets(firms) == pytest.approx(before)
    assert other.ledger.cash == 1_000_000.0  # the target's cash isn't touched
    assert eco.stocks[other.id].holdings_corps[me.id] == 10_000
    got = eco.sell_stock(me, other.id, 10_000)
    assert me.ledger.cash == pytest.approx(5_000_000.0 - cost + got)
    assert me.stock_assets == pytest.approx(cost - got)
    assert other.ledger.cash == 1_000_000.0


def test_buy_refused_when_cash_short():
    eco, me, other = _two_corps()
    me.ledger.cash = 100.0
    with pytest.raises(InsufficientFunds):
        eco.buy_stock(me, other.id, 10_000)
    assert me.ledger.cash == 100.0
    assert eco.stocks[other.id].holdings_corps[me.id] == 0


def test_own_stock_buyback_retires_shares():
    eco, me, _other = _two_corps()
    st = eco.stocks[me.id]
    total = st.total_shares
    worth = me.net_worth(eco.firms)
    cost = eco.buy_stock(me, me.id, 50_000)
    assert st.total_shares == total - 50_000
    assert st.holdings_corps[me.id] == 0
    assert me.ledger.cash == pytest.approx(5_000_000.0 - cost)
    assert me.net_worth(eco.firms) == pytest.approx(worth - cost)  # equity drops


def test_issue_raises_cash_and_shares():
    eco, me, _other = _two_corps()
    st = eco.stocks[me.id]
    total, price = st.total_shares, st.price
    got = eco.issue_stock(me, 100_000)
    assert got == pytest.approx(100_000 * price)
    assert me.ledger.cash == pytest.approx(5_000_000.0 + got)
    assert st.total_shares == total + 100_000


def test_facade_share_commands_post_cash():
    from capitalism.api import Api

    api = Api.new_game("Me", seed=1, detailed_cities=False)
    cash = api.player.ledger.cash
    api.command("issue_shares", {"shares": 10_000})
    (res,) = api.tick(1)["results"]
    assert res["ok"] is True
    assert api.player.ledger.cash > cash
