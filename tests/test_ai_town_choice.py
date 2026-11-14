"""AI town choice by firm type (R24, #300; techspec "Town choice")."""

from capitalism.ai import (
    _demand_threshold,
    _demand_town,
    _education_labor_town,
    _pick_town,
    _untapped_market_town,
)
from capitalism.economy import CORP_AI
from capitalism.person import CHAR_CONSERVATIVE, CHAR_VERY_AGGRESSIVE, Person
from capitalism.rng import Rng
from capitalism.scenario import bread_town, build_bread_chain
from capitalism.tables import AI_RULES


def _eco(seed: int = 1):
    sim, _town = bread_town(seed)
    eco = sim.economy
    for tm in eco.market.towns.values():
        tm.demand_per_day = 0.0
        tm.supply_today = 0.0
    return sim, eco


def _ceo(char_type: int) -> Person:
    p = Person(0, "CEO")
    p.character_type = char_type
    return p


def _set_demand(eco, town, n: int, demand: float) -> list:
    tms = [tm for (tid, _pid), tm in eco.market.towns.items() if tid == town.id]
    tms = [tm for tm in tms if tm.product.state.available][:n]
    for tm in tms:
        tm.demand_per_day = demand
    return tms


def test_town_choice_constants_from_db():
    assert AI_RULES.town_edu_weight == 2.0
    assert AI_RULES.town_tie_switch_odds == 3
    assert _demand_threshold(_ceo(CHAR_CONSERVATIVE)) == (11, 2)
    assert _demand_threshold(_ceo(1)) == (9, 1)
    assert _demand_threshold(_ceo(2)) == (7, 1)
    assert _demand_threshold(_ceo(CHAR_VERY_AGGRESSIVE)) == (5, 0)


class TestDemandTown:
    def test_most_qualifying_products_wins(self):
        _sim, eco = _eco()
        towns = eco.world.towns
        corp = eco.add_corp("AI", CORP_AI)
        _set_demand(eco, towns[1], 2, 50.0)
        _set_demand(eco, towns[3], 3, 50.0)
        assert _demand_town(eco, corp, _ceo(CHAR_CONSERVATIVE)) is towns[3]
        assert _pick_town(eco, corp, 1, _ceo(CHAR_CONSERVATIVE)) is towns[3]

    def test_ties_go_to_first_town(self):
        _sim, eco = _eco()
        towns = eco.world.towns
        corp = eco.add_corp("AI", CORP_AI)
        _set_demand(eco, towns[2], 2, 50.0)
        _set_demand(eco, towns[1], 2, 50.0)
        assert _demand_town(eco, corp, _ceo(CHAR_CONSERVATIVE)) is towns[1]

    def test_below_threshold_or_minimum_does_not_qualify(self):
        _sim, eco = _eco()
        towns = eco.world.towns
        corp = eco.add_corp("AI", CORP_AI)
        _set_demand(eco, towns[1], 5, 10.0)  # below conservative threshold 11
        _set_demand(eco, towns[2], 1, 50.0)  # one product, conservative needs 2
        assert _demand_town(eco, corp, _ceo(CHAR_CONSERVATIVE)) is None
        # Very aggressive: threshold 5, minimum 0, so town 1's five products count.
        assert _demand_town(eco, corp, _ceo(CHAR_VERY_AGGRESSIVE)) is towns[1]

    def test_oversupplied_product_does_not_qualify(self):
        _sim, eco = _eco()
        towns = eco.world.towns
        corp = eco.add_corp("AI", CORP_AI)
        for tm in _set_demand(eco, towns[1], 2, 50.0):
            tm.supply_today = 60.0
        assert _demand_town(eco, corp, _ceo(CHAR_CONSERVATIVE)) is None


class TestEducationLaborTown:
    def test_highest_score_wins(self):
        _sim, eco = _eco()
        towns = eco.world.towns
        towns[2].labor_quality = 120.0  # 240 - 100
        towns[4].labor_quality = 110.0
        towns[4].labor_cost = 50.0  # 220 - 50 = 170, beats 140
        assert _education_labor_town(towns, Rng(1)) is towns[4]
        corp = eco.add_corp("AI", CORP_AI)
        for ft in (3, 8, 9):
            assert _pick_town(eco, corp, ft, None) is towns[4]

    def test_ties_switch_with_seeded_rng(self):
        _sim, eco = _eco()
        towns = eco.world.towns  # all towns score 100 * 2 - 100
        picks = [_education_labor_town(towns, Rng(s)) for s in range(40)]
        assert picks == [_education_labor_town(towns, Rng(s)) for s in range(40)]
        assert len({t.id for t in picks}) > 1


class TestFactoryTown:
    def test_uniform_random_seeded(self):
        _sim, eco = _eco()
        corp = eco.add_corp("AI", CORP_AI)
        picks = []
        for s in range(40):
            eco.rng = Rng(s)
            picks.append(_pick_town(eco, corp, 2, None).id)
        again = []
        for s in range(40):
            eco.rng = Rng(s)
            again.append(_pick_town(eco, corp, 2, None).id)
        assert picks == again
        assert set(picks) == {t.id for t in eco.world.towns}


def test_extraction_skips_town_choice():
    _sim, eco = _eco()
    corp = eco.add_corp("AI", CORP_AI)
    biggest = max(eco.world.towns, key=lambda t: t.population)
    for ft in (5, 6, 7):
        assert _pick_town(eco, corp, ft, None) is biggest


class TestUntappedMarketFallback:
    def test_skips_towns_the_corp_already_sells_in(self):
        sim, eco = _eco()
        towns = eco.world.towns
        chain = build_bread_chain(sim, towns[0])
        bread = eco.catalog["Bread"]
        for t in towns[:2]:
            eco.market.towns[(t.id, bread.id)].demand_per_day = 30.0
        store_tm = eco.market.towns[(towns[0].id, bread.id)]
        corp_id = store_tm.links[0].corp_id
        corp = next(c for c in eco.corps if c.id == corp_id)
        assert chain is not None
        assert _untapped_market_town(eco, corp) is towns[1]
        newcomer = eco.add_corp("AI", CORP_AI)
        assert _untapped_market_town(eco, newcomer) is towns[0]

    def test_dept_store_falls_back_when_no_town_qualifies(self):
        _sim, eco = _eco()
        towns = eco.world.towns
        corp = eco.add_corp("AI", CORP_AI)
        _set_demand(eco, towns[3], 1, 4.0)  # demand, but below every threshold
        assert _demand_town(eco, corp, _ceo(CHAR_CONSERVATIVE)) is None
        assert _pick_town(eco, corp, 1, _ceo(CHAR_CONSERVATIVE)) is towns[3]
