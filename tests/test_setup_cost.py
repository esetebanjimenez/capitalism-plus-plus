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
    ("setting", "mode", "lo", "hi"),
    [
        (0, 0, 55e6, 100e6),    # Low / Establish
        (0, 2, 55e6, 65e6),     # Low / Retail
        (1, 0, 220e6, 400e6),   # Moderate / Establish
        (2, 0, 390e6, 700e6),   # High / Establish
        (3, 0, 550e6, 1000e6),  # Very High / Establish
        (4, 0, 710e6, 1300e6),  # Extreme / Establish
        (4, 2, 710e6, 840e6),   # Extreme / Retail
    ],
)
def test_ai_starting_capital_by_setting(setting, mode, lo, hi):
    rng = Rng(7)
    values = {ai_starting_capital(setting, mode, rng) for _ in range(2000)}
    assert min(values) == lo
    assert max(values) == hi


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


# --- B2: own-share issue in raise-cash (FUN_00030d97) ----------------------


def _ai_with_own_stock(sim, cash):
    """Set up a corp that owns its own stock and can issue shares."""
    from capitalism.stock import Stock

    eco = sim.economy
    corp = eco.add_corp("AI", CORP_AI)
    corp.ledger.cash = cash
    stock = Stock(corp.id, 1e8, 50.0)  # $100M company at $50/share
    eco.stocks[corp.id] = stock
    return eco, corp, stock


def test_raise_cash_issues_own_shares_when_loan_insufficient():
    from capitalism.ai import ai_raise_cash

    sim, _town = bread_town()
    eco, corp, stock = _ai_with_own_stock(sim, 0.0)
    corp.business_assets = 0.0
    corp.liabilities = 0.0
    old_shares = stock.total_shares
    # No holdings to sell, no credit for a loan — share issue is the only way
    assert ai_raise_cash(eco, corp, 100_000.0)
    assert corp.ledger.cash >= 100_000.0
    assert stock.total_shares > old_shares


def test_raise_cash_skips_issue_when_price_below_one():
    from capitalism.ai import ai_raise_cash

    sim, _town = bread_town()
    eco, corp, stock = _ai_with_own_stock(sim, 0.0)
    stock.price = 0.50
    old_shares = stock.total_shares
    assert not ai_raise_cash(eco, corp, 1e9)
    assert stock.total_shares == old_shares


def test_raise_cash_retries_issues_up_to_10():
    from capitalism.ai import ai_raise_cash

    sim, _town = bread_town()
    eco, corp, stock = _ai_with_own_stock(sim, 0.0)
    corp.business_assets = 0.0
    corp.liabilities = 0.0
    old_shares = stock.total_shares
    min_issue = AI_RULES.share_issue_min
    # Target is huge — it will take many issues
    ai_raise_cash(eco, corp, 1e12)
    # Step 4 + up to 10 retries = at most 11 issues
    issued = stock.total_shares - old_shares
    assert issued <= 11 * min_issue
    assert issued >= min_issue


def test_raise_cash_second_holdings_sale():
    """After a share issue, a second holdings sale runs (step 5)."""
    from capitalism.ai import ai_raise_cash
    from capitalism.stock import Stock

    sim, _town = bread_town()
    eco, corp, stock = _ai_with_own_stock(sim, 0.0)
    corp.business_assets = 0.0
    corp.liabilities = 0.0
    # Also hold shares in another corp — step 1 won't sell enough, step 5 will
    other = eco.add_corp("Other", CORP_AI)
    other_stock = Stock(other.id, 1e9, 100.0)
    eco.stocks[other.id] = other_stock
    other_stock.holdings_corps[corp.id] = 100
    # Set stock price very low so issuing barely helps, forcing step 5
    stock.price = 1.0
    target = 1e6
    ai_raise_cash(eco, corp, target)
    # The second holdings sale should have sold some of those 100 shares
    assert other_stock.holdings_corps[corp.id] < 100
