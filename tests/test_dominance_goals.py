"""Sector and industry dominance goals can be met (gamelogic.md Goals)."""

import pytest

from capitalism.goals import (
    GameResult,
    check_goals,
    industry_led,
    leads,
    product_shares,
    sector_shares,
    share_row,
)
from capitalism.scenario import bread_town, build_bread_chain
from capitalism.tables import FIRM_SECTORS, FIRM_TYPES, PRODUCT_CLASSES


def _chain(days: int = 70):
    sim, town = bread_town(1)
    build_bread_chain(sim, town)
    sim.advance_days(days)
    return sim


def test_sectors_match_native_mapping():
    by_sector: dict[int, set[str]] = {}
    for t, r in FIRM_SECTORS.items():
        by_sector.setdefault(r.sector, set()).add(FIRM_TYPES[t].name)
    assert by_sector == {
        0: {"Department Store"},
        1: {"Factory"},
        2: {"Farm"},
        3: {"Logging Camp", "Mine", "Oil Well"},
    }
    assert sorted(FIRM_SECTORS) == [1, 2, 4, 5, 6, 7]  # native type codes


def test_tie_goes_to_lowest_corp_slot():
    assert leads({0: 2.0, 1: 1.0}, 0)
    assert leads({0: 1.0, 1: 1.0}, 0)
    assert not leads({0: 1.0, 1: 1.0}, 1)
    assert leads({1: 1.0, 2: 1.0}, 1)
    assert not leads({0: 1.0, 1: 2.0}, 0)
    assert not leads({0: 0.0, 1: 0.0}, 0)
    assert not leads({1: 1.0}, 0)
    assert not leads({}, 0)


def test_sector_dominance_scenario_is_won():
    sim = _chain(0)
    corp = sim.economy.corps[0].id
    sim.goal_config.sector_goals[0] = True  # sector 1: department stores
    sim.goal_checker.player_corp_id = corp
    sim.advance_days(70)
    assert leads(sector_shares(sim.economy)[0], corp)
    assert sim.goal_checker.result == GameResult.VICTORY


def test_sector_without_player_revenue_is_not_met():
    sim = _chain()
    corp = sim.economy.corps[0].id
    goals = sim.goal_config
    goals.sector_goals[3] = True  # sector 4: the player owns no logging camp, mine or oil well
    all_met, results = check_goals(goals, sim.economy, corp)
    assert not all_met
    assert results["sector_3"] == (0.0, 0.0, False)


def test_sector_row_shows_player_and_leader_share():
    sim = _chain()
    corp = sim.economy.corps[0].id
    goals = sim.goal_config
    goals.sector_goals[0] = True
    _, results = check_goals(goals, sim.economy, corp)
    leader, player, met = results["sector_0"]
    assert leader == pytest.approx(0.0)
    assert player == pytest.approx(100.0)
    assert met is True
    assert share_row({corp: 30.0, corp + 1: 70.0}, corp) == (70.0, 30.0, False)


def test_industry_dominance_needs_every_product_in_class():
    sim = _chain()
    eco = sim.economy
    corp = eco.corps[0].id
    food = eco.catalog.by_name["Bread"].cls.id
    shares = product_shares(eco)
    assert leads(shares[eco.catalog.by_name["Bread"].id], corp)
    # Bread alone is not enough: Food also has other products nobody sells.
    assert not industry_led(eco, shares, food, corp)
    goals = sim.goal_config
    goals.industry_goals = [cid == food for cid in sorted(PRODUCT_CLASSES)]
    assert not check_goals(goals, eco, corp)[0]
    # Leading every Food product meets it; one product led by a rival fails it.
    members = [p.id for p in eco.catalog.products if p.cls.id == food]
    won = dict(shares) | {pid: {corp: 10.0, corp + 1: 5.0} for pid in members}
    assert industry_led(eco, won, food, corp)
    lost = won | {members[-1]: {corp: 5.0, corp + 1: 10.0}}
    assert not industry_led(eco, lost, food, corp)


def test_dominance_off_leaves_results_unchanged():
    sim = _chain()
    goals = sim.goal_config
    goals.personal_wealth = 1.0
    _, results = check_goals(goals, sim.economy, sim.economy.corps[0].id)
    assert set(results) == {"personal_wealth"}
