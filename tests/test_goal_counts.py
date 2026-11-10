"""Employee and product-count goals read the player's own firms (owner, not corp_id)."""

import pytest

from capitalism.goals import GameResult, GoalConfig, check_goals
from capitalism.scenario import bread_town, build_bread_chain


@pytest.fixture(scope="module")
def chain_sim():
    sim, town = bread_town(1)
    build_bread_chain(sim, town)
    sim.advance_days(40)
    return sim


def _player_counts(sim):
    corp = sim.economy.corps[0]
    jobs = [j for f in sim.economy.firms if f is not None and f.owner is corp for j in f.jobs()]
    products = {j.product for j in jobs if j.product is not None}
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
