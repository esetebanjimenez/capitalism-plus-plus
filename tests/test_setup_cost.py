"""Setup costs and starting capital (gap audit C1-C4)."""

import pytest

from capitalism.ai import ai_build_firm, ai_starting_capital
from capitalism.economy import CORP_AI
from capitalism.firms import InsufficientFunds
from capitalism.rng import Rng
from capitalism.scenario import bread_town, find_site
from capitalism.sim import Sim
from capitalism.tables import (
    AI_RULES,
    COMPETITOR_CAPITAL,
    CORPORATION_RULES,
    FIRM_TYPES,
    JOB_TYPES,
)
from capitalism.world import TileCategory

DEPT_STORE = 1
PURCHASING = 10


def test_player_starts_with_initial_capital():
    sim, _ = bread_town()
    corp = sim.economy.add_corp("P")
    assert CORPORATION_RULES.player_initial_capital == 10_000_000
    assert corp.ledger.cash == 10_000_000
    assert sim.economy.add_corp("AI", CORP_AI).ledger.cash == 0


def test_initial_capital_setup_option_overrides_db():
    sim = Sim(seed=1, detailed_cities=False)
    sim.setup.initial_capital = 2_500_000
    sim.reset()
    assert sim.economy.add_corp("P").ledger.cash == 2_500_000


def test_build_moves_setup_and_land_into_assets():
    sim, town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("P")
    x, y = find_site(sim, town)
    land = sim.world.land_value(x, y)
    assets_before = corp.total_assets(eco.firms)
    firm = eco.build_firm(DEPT_STORE, corp, x, y, town)
    cost = FIRM_TYPES[DEPT_STORE].setup_cost
    assert cost == 1_000_000
    assert corp.business_assets == cost
    assert corp.land_assets == land
    # The firm ledger only carries the first partial month of overhead (a P&L post);
    # setup and land are asset moves, so total assets drop by that overhead only.
    assert firm.ledger.cash < 0
    assert corp.ledger.cash == pytest.approx(10_000_000 - cost - land + firm.ledger.cash)
    assert corp.total_assets(eco.firms) == pytest.approx(assets_before + firm.ledger.cash)


def test_demolish_unbooks_assets_and_writes_off_setup():
    """B4: demolish reverses build_firm's asset bookings.

    Decomp FUN_00063f28: BizAssets→Cash, write-off setup as CAT_WRITEOFFS,
    floor BizAssets, LandAssets→Cash, floor LandAssets.
    Net cash change = +land_value (setup is a wash).
    """
    from capitalism.jobs import CAT_WRITEOFFS

    sim, town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("P")
    x, y = find_site(sim, town)
    land = sim.world.land_value(x, y)
    firm = eco.build_firm(DEPT_STORE, corp, x, y, town)
    setup = FIRM_TYPES[DEPT_STORE].setup_cost
    cash_after_build = corp.ledger.cash

    eco.demolish_firm(firm)

    assert corp.business_assets == 0.0
    assert corp.land_assets == 0.0
    assert corp.ledger.cash == pytest.approx(cash_after_build + land)
    assert corp.ledger.month[CAT_WRITEOFFS] == pytest.approx(setup)
    assert eco.firms[firm.id] is None
    tile = sim.world.tile_at(x, y)
    assert tile.kind == TileCategory.GRASSLAND
    assert tile.ref == -1


def test_build_refused_below_setup_plus_land():
    sim, town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("P")
    x, y = find_site(sim, town)
    cost = FIRM_TYPES[DEPT_STORE].setup_cost + sim.world.land_value(x, y)
    corp.ledger.cash = cost - 1
    n = len(eco.firms)
    with pytest.raises(InsufficientFunds):
        eco.build_firm(DEPT_STORE, corp, x, y, town)
    assert corp.ledger.cash == cost - 1 and corp.business_assets == 0
    assert len(eco.firms) == n
    assert sim.world.tile_at(x, y).kind != TileCategory.FIRM
    corp.liabilities = -1e9  # a huge credit line doesn't help: cash only
    with pytest.raises(InsufficientFunds):
        eco.build_firm(DEPT_STORE, corp, x, y, town)
    corp.ledger.cash = cost
    eco.build_firm(DEPT_STORE, corp, x, y, town)
    assert corp.ledger.cash < 0.0  # only the first partial month of overhead


def test_add_job_moves_setup_into_business_assets():
    sim, town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("P")
    x, y = find_site(sim, town)
    firm = eco.build_firm(DEPT_STORE, corp, x, y, town)
    bread = eco.catalog["Bread"]
    cost = JOB_TYPES[PURCHASING].setup_cost
    cash, business = corp.ledger.cash, corp.business_assets
    firm.add_job(0, PURCHASING, bread)
    assert corp.ledger.cash == pytest.approx(cash - cost)
    assert corp.business_assets == pytest.approx(business + cost)
    corp.ledger.cash = 0.0
    firm.add_job(1, PURCHASING, bread)  # never refused
    assert corp.ledger.cash == -cost


def test_government_firm_is_free():
    sim, town = bread_town()
    x, y = find_site(sim, town)
    sim.economy.build_firm(DEPT_STORE, None, x, y, town)  # no owner, nothing to book


def test_ai_build_checks_land_plus_real_setup_cost():
    from capitalism.ai import ai_build_firm

    sim, town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("AI", CORP_AI)
    corp.ledger.cash = FIRM_TYPES[DEPT_STORE].setup_cost * 0.4  # too short even with a loan
    assert ai_build_firm(eco, corp, DEPT_STORE, town, Rng(1)) is None
    assert corp.business_assets == 0
    corp.ledger.cash = 1e9
    assert ai_build_firm(eco, corp, DEPT_STORE, town, Rng(1)) is not None
    assert corp.business_assets == FIRM_TYPES[DEPT_STORE].setup_cost


@pytest.mark.parametrize(
    ("setting", "lo", "hi"),
    [(0, 3.0e6, 5.4e6), (1, 4.2e6, 7.8e6), (2, 6.0e6, 11.4e6), (3, 9.0e6, 17.4e6),
     (4, 18.0e6, 35.4e6)],
)
def test_ai_starting_capital_by_setting(setting, lo, hi):
    assert AI_RULES.capital_unit == 600_000
    rng = Rng(7)
    values = {ai_starting_capital(setting, rng) for _ in range(2000)}
    half = COMPETITOR_CAPITAL[setting].v // 2
    assert min(values) == lo == half * 600_000
    assert max(values) == hi == (2 * half - 1) * 600_000


def test_facade_build_cost_and_refusal():
    from capitalism.api import Api

    api = Api.new_game("Me", seed=1, detailed_cities=False)
    assert api.player.ledger.cash == 10_000_000
    town = api.sim.towns[0]
    x, y = find_site(api.sim, town)
    api.player.ledger.cash = 10.0
    opt = next(
        o for o in api.query("build_options", {"x": x, "y": y})["options"]
        if o["type_id"] == DEPT_STORE
    )
    assert opt["land_value"] == api.sim.world.land_value(x, y)
    assert opt["build_cost"] == opt["setup_cost"] + opt["land_value"]
    assert opt["affordable"] is False and opt["shortfall"] == opt["build_cost"] - 10.0
    api.command("build_firm", {"firm_type": DEPT_STORE, "x": x, "y": y})
    (res,) = api.tick(1)["results"]
    assert res["ok"] is False and "with land" in res["error"]
    assert api.player.ledger.cash <= 10.0


def _ai_with_shares(sim, cash):
    eco = sim.economy
    other = eco.add_corp("Target", CORP_AI)
    corp = eco.add_corp("AI", CORP_AI)
    corp.ledger.cash = cash
    from capitalism.stock import Stock

    stock = Stock(other.id, 1e9, 10.0)  # a $1B company at $10 a share
    eco.stocks[other.id] = stock
    stock.holdings_corps[corp.id] = 1_000_000  # about $10M held
    return eco, corp, stock


def test_ai_raise_cash_sells_just_enough_shares():
    from capitalism.ai import ai_raise_cash

    sim, _town = bread_town()
    eco, corp, stock = _ai_with_shares(sim, 0.0)
    assert ai_raise_cash(eco, corp, 50_000.0)
    assert corp.ledger.cash >= 50_000.0
    assert 0 < 1_000_000 - stock.holdings_corps[corp.id] < 1_000_000


def test_ai_build_sells_assets_then_builds_or_cancels():
    sim, town = bread_town()
    eco, corp, stock = _ai_with_shares(sim, 0.0)
    firm = ai_build_firm(eco, corp, DEPT_STORE, town, eco.rng)
    assert firm is not None and stock.holdings_corps[corp.id] < 1_000_000
    assert corp.ledger.cash >= -FIRM_TYPES[DEPT_STORE].overhead_month
    stock.holdings_corps[corp.id] = 0
    corp.ledger.cash = 0.0
    corp.liabilities = corp.total_assets(eco.firms)  # no credit left either
    assert ai_build_firm(eco, corp, DEPT_STORE, town, eco.rng) is None


def test_ai_raise_cash_borrows_up_to_credit_limit():
    from capitalism.ai import ai_raise_cash

    sim, _town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("AI", CORP_AI)
    corp.ledger.cash = 1_000_000.0
    corp.business_assets = 3_000_000.0
    corp.liabilities = 1_000_000.0
    # total assets 4M - debt 1M: credit 3M, enough for a 2M target
    assert ai_raise_cash(eco, corp, 2_000_000.0)
    assert corp.ledger.cash == pytest.approx(2_000_000.0)
    assert corp.liabilities == pytest.approx(2_000_000.0)
    # now credit is 5M - 2M = 3M; a 10M target can only borrow 3M, then cancel
    assert not ai_raise_cash(eco, corp, 10_000_000.0)
    assert corp.ledger.cash == pytest.approx(5_000_000.0)
    assert corp.liabilities == pytest.approx(5_000_000.0)


def test_ai_loan_floor():
    from capitalism.ai import ai_raise_cash

    sim, _town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("AI", CORP_AI)
    corp.ledger.cash = 1_000_000.0
    corp.business_assets = 1_000_000.0
    # short by 10k: borrows the 100k floor
    assert ai_raise_cash(eco, corp, 1_010_000.0)
    assert corp.liabilities == pytest.approx(AI_RULES.loan_minimum)
    # credit below the floor: no loan at all
    corp.liabilities = corp.total_assets(eco.firms) - 50_000.0
    debt = corp.liabilities
    assert not ai_raise_cash(eco, corp, 10_000_000.0)
    assert corp.liabilities == debt
