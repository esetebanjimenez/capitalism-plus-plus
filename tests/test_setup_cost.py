"""Setup costs and starting capital (gap audit C1-C4)."""

import pytest

from capitalism.ai import ai_starting_capital
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


def test_build_firm_charges_setup_cost():
    sim, town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("P")
    x, y = find_site(sim, town)
    firm = eco.build_firm(DEPT_STORE, corp, x, y, town)
    cost = FIRM_TYPES[DEPT_STORE].setup_cost
    assert cost == 1_000_000
    # Setup is a cash payment, not a P&L post; the firm's ledger only carries
    # the first partial month of overhead, which also hits the owner.
    assert firm.ledger.cash < 0
    assert corp.ledger.cash == pytest.approx(10_000_000 - cost + firm.ledger.cash)


def test_build_firm_refused_when_cash_short():
    sim, town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("P")
    corp.ledger.cash = FIRM_TYPES[DEPT_STORE].setup_cost - 1
    x, y = find_site(sim, town)
    n = len(eco.firms)
    with pytest.raises(InsufficientFunds):
        eco.build_firm(DEPT_STORE, corp, x, y, town)
    assert corp.ledger.cash == FIRM_TYPES[DEPT_STORE].setup_cost - 1
    assert len(eco.firms) == n
    assert sim.world.tile_at(x, y).kind != TileCategory.FIRM


def test_add_job_charges_and_refuses():
    sim, town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("P")
    x, y = find_site(sim, town)
    firm = eco.build_firm(DEPT_STORE, corp, x, y, town)
    bread = eco.catalog["Bread"]
    cost = JOB_TYPES[PURCHASING].setup_cost
    before = corp.ledger.cash
    firm.add_job(0, PURCHASING, bread)
    assert corp.ledger.cash == pytest.approx(before - cost)
    corp.ledger.cash = cost - 1
    with pytest.raises(InsufficientFunds):
        firm.add_job(1, PURCHASING, bread)
    assert firm.slots[1] is None
    assert corp.ledger.cash == cost - 1


def test_government_firm_is_free():
    sim, town = bread_town()
    x, y = find_site(sim, town)
    sim.economy.build_firm(DEPT_STORE, None, x, y, town)  # no owner, nothing to charge


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


def test_facade_reports_unaffordable_build():
    from capitalism.api import Api

    api = Api.new_game("Me", seed=1, detailed_cities=False)
    assert api.player.ledger.cash == 10_000_000
    town = api.sim.towns[0]
    x, y = find_site(api.sim, town)
    api.player.ledger.cash = 10.0
    api.command("build_firm", {"firm_type": DEPT_STORE, "x": x, "y": y})
    (res,) = api.tick(1)["results"]
    assert res["ok"] is False and "costs $1,000,000" in res["error"]
