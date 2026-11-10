"""Employee and product-count goals read the player's own firms (owner, not corp_id)."""

import pytest

from capitalism.goals import GameResult, GoalConfig, check_goals
from capitalism.scenario import bread_town, build_bread_chain
from capitalism.tables import JOB_TYPES


@pytest.fixture(scope="module")
def chain_sim():
    sim, town = bread_town(1)
    build_bread_chain(sim, town)
    sim.advance_days(40)
    return sim


def _player_counts(sim):
    corp = sim.economy.corps[0]
    jobs = [j for f in sim.economy.firms if f is not None and f.owner is corp for j in f.jobs()]
    products = {
        j.product for j in jobs if j.product is not None and JOB_TYPES[j.type_id].counts_as_produced
    }
    return (
        corp.id,
        sum(j.staff for j in jobs),
        len({p.id for p in products}),
        len({p.cls.id for p in products}),
    )


@pytest.mark.parametrize("goal", ["num_employees", "num_product_types", "num_product_classes"])
def test_count_goal_met_at_actual_value_and_not_above(chain_sim, goal):
    corp_id, employees, types, classes = _player_counts(chain_sim)
    actual = {
        "num_employees": employees,
        "num_product_types": types,
        "num_product_classes": classes,
    }[goal]
    assert actual > 0
    g = GoalConfig()
    setattr(g, goal, float(actual))
    met, results = check_goals(g, chain_sim.economy, corp_id)
    assert met
    assert results[goal] == (float(actual), float(actual), True)
    setattr(g, goal, float(actual + 1))
    assert not check_goals(g, chain_sim.economy, corp_id)[0]


def test_other_corps_firms_are_not_counted(chain_sim):
    g = GoalConfig()
    g.num_employees = 1.0
    met, results = check_goals(g, chain_sim.economy, 99)
    assert not met
    assert results["num_employees"][1] == 0.0


def test_count_goals_scenario_is_won():
    sim, town = bread_town(1)
    build_bread_chain(sim, town)
    corp_id, employees, types, classes = _player_counts(sim)
    sim.goal_config.num_employees = float(employees)
    sim.goal_config.num_product_types = float(types)
    sim.goal_config.num_product_classes = float(classes)
    sim.goal_checker.player_corp_id = corp_id
    sim.advance_days(10)
    assert sim.goal_checker.result == GameResult.VICTORY


def test_bought_or_resold_products_do_not_count():
    """The chain imports Wheat (bought only) and resells Bread: only Flour and Bread count."""
    sim, town = bread_town(1)
    build_bread_chain(sim, town)
    eco = sim.economy
    corp = eco.corps[0]
    jobs = [j for f in eco.firms if f is not None and f.owner is corp for j in f.jobs()]
    assert {j.product.name for j in jobs if j.product is not None} == {"Wheat", "Flour", "Bread"}
    g = GoalConfig()
    g.num_product_types = 3.0
    met, results = check_goals(g, eco, corp.id)
    assert not met
    assert results["num_product_types"][1] == 2.0  # Flour, Bread (manufactured)
    g.num_product_types = 2.0
    assert check_goals(g, eco, corp.id)[0]


def test_store_reselling_imports_counts_nothing():
    sim, town = bread_town(1)
    build_bread_chain(sim, town)
    eco = sim.economy
    corp = eco.corps[0]
    for f in eco.firms:
        if f is not None and f.owner is corp and f.type_id != 1:  # keep the department store
            f.owner = None
    g = GoalConfig()
    g.num_product_types = 1.0
    g.num_product_classes = 1.0
    _, results = check_goals(g, eco, corp.id)
    assert results["num_product_types"][1] == 0.0
    assert results["num_product_classes"][1] == 0.0


def test_only_production_jobs_count():
    names = {r.name for r in JOB_TYPES.values() if r.counts_as_produced}
    assert names == {
        "Crop Growing",
        "Livestock Raising",
        "Logging",
        "Manufacturing",
        "Mining",
        "Oil Extraction",
        "Software Development",
        "Software Production",
    }
