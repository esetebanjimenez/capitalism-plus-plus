"""Sector and industry dominance goals can be met (gamelogic.md Goals)."""

from capitalism.goals import (
    GameResult,
    check_goals,
    industry_led,
    leads,
    product_shares,
    sector_shares,
)
from capitalism.scenario import bread_town, build_bread_chain
from capitalism.tables import FIRM_SECTORS, FIRM_TYPES, PRODUCT_CLASSES


def _chain(days: int = 70):
    sim, town = bread_town(1)
    build_bread_chain(sim, town)
    sim.advance_days(days)
    return sim


def test_every_firm_type_but_seaport_has_a_sector():
    names = {FIRM_TYPES[t].name for t in FIRM_TYPES if t not in FIRM_SECTORS}
    assert names == {"Seaport"}
    assert {r.sector for r in FIRM_SECTORS.values()} == {0, 1, 2, 3}


def test_leads_needs_strict_positive_lead():
    assert leads({0: 2.0, 1: 1.0}, 0)
    assert not leads({0: 1.0, 1: 1.0}, 0)
    assert not leads({1: 1.0}, 0)
    assert not leads({}, 0)


def test_sector_dominance_scenario_is_won():
    sim = _chain(0)
    corp = sim.economy.corps[0].id
    sim.goal_config.sector_goals[0] = True  # retail: the department store
    sim.goal_checker.player_corp_id = corp
    sim.advance_days(70)
    assert leads(sector_shares(sim.economy)[0], corp)
    assert sim.goal_checker.result == GameResult.VICTORY


def test_sector_without_player_revenue_is_not_met():
    sim = _chain()
    corp = sim.economy.corps[0].id
    goals = sim.goal_config
    goals.sector_goals[3] = True  # media: the player owns none
    all_met, results = check_goals(goals, sim.economy, corp)
    assert not all_met
    assert results["sector_3"] == (1.0, 0.0, False)


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
