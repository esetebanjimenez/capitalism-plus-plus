"""Person system: lifecycle, expertise, satisfaction, salary, traits."""

import pytest

from capitalism.economy import CORP_AI, CORP_PLAYER
from capitalism.person import (
    CHAR_AGGRESSIVE,
    CHAR_CONSERVATIVE,
    CHAR_VERY_AGGRESSIVE,
    N_SKILLS,
    ROLE_CEO,
    ROLE_HUMAN_PLAYER,
    ROLE_INDEPENDENT,
    ROLE_PRESIDENT,
    ROLE_RETIRED,
    SKILL_WEIGHTS,
    STATE_ACTIVE,
    STATE_LINKED,
    STATE_RETIRED,
    Person,
)
from capitalism.rng import Rng
from capitalism.scenario import bread_town
from capitalism.tables import PERSON_RULES


class TestPersonInit:
    def test_defaults(self):
        p = Person(0, "Alice")
        assert p.state == STATE_ACTIVE
        assert p.role == ROLE_INDEPENDENT
        assert p.corp_id is None
        assert p.satisfaction == 0
        assert p.salary == 0.0
        assert p.wealth == 0.0
        assert len(p.skills) == N_SKILLS
        assert p.character_type == CHAR_CONSERVATIVE

    def test_player_person(self):
        p = Person(0, "Player", is_player=True)
        assert p.role == ROLE_HUMAN_PLAYER
        assert p.acceptance_trait == 0


class TestExpertise:
    def test_performance_score_zero_skills(self):
        p = Person(0, "Test")
        assert p.performance_score == 0.0

    def test_performance_score_max_skills(self):
        p = Person(0, "Test")
        p.skills = [100.0] * N_SKILLS
        assert p.performance_score == pytest.approx(100.0)

    def test_performance_score_weights(self):
        p = Person(0, "Test")
        p.skills = [100.0] + [0.0] * (N_SKILLS - 1)
        assert p.performance_score == pytest.approx(SKILL_WEIGHTS[0])

    def test_randomize_skills(self):
        rng = Rng(42)
        p = Person(0, "Test")
        p.randomize_skills(rng, 2)
        for s in p.skills:
            assert 40 <= s <= 80


class TestCharacterType:
    def test_randomize_character_random(self):
        rng = Rng(1)
        types = set()
        for i in range(20):
            p = Person(i, f"P{i}")
            p.randomize_character(rng)
            types.add(p.character_type)
        assert len(types) >= 2

    def test_randomize_character_specific(self):
        rng = Rng(1)
        p = Person(0, "Test")
        p.randomize_character(rng, setting=CHAR_AGGRESSIVE)
        assert p.character_type == CHAR_AGGRESSIVE

    def test_randomize_character_clamped(self):
        rng = Rng(1)
        p = Person(0, "Test")
        p.randomize_character(rng, setting=99)
        assert p.character_type == CHAR_VERY_AGGRESSIVE


class TestSatisfaction:
    def test_label_ranges(self):
        p = Person(0, "Test")
        p.satisfaction = -60
        assert p.satisfaction_label == "Very Bad"
        p.satisfaction = -10
        assert p.satisfaction_label == "Bad"
        p.satisfaction = 0
        assert p.satisfaction_label == "Neutral"
        p.satisfaction = 30
        assert p.satisfaction_label == "Good"
        p.satisfaction = 50
        assert p.satisfaction_label == "Very Good"

    def test_monthly_drift_negative(self):
        rng = Rng(1)
        p = Person(0, "Test")
        p.satisfaction = -10
        p.monthly_satisfaction_drift(rng)
        assert p.satisfaction == -9

    def test_monthly_drift_underpaid(self):
        rng = Rng(1)
        p = Person(0, "Test")
        p.satisfaction = 5
        p.salary = 100000.0
        p.wealth = 50000.0
        old = p.satisfaction
        p.monthly_satisfaction_drift(rng)
        assert p.satisfaction in (old, old + 1)

    def test_monthly_drift_well_paid(self):
        rng = Rng(1)
        p = Person(0, "Test")
        p.satisfaction = 5
        p.salary = 100000.0
        p.wealth = 200000.0
        old = p.satisfaction
        p.monthly_satisfaction_drift(rng)
        assert p.satisfaction in (old + 1, old + 2)

    def test_raise_penalty(self):
        rng = Rng(1)
        p = Person(0, "Test")
        p.satisfaction = 50
        p.salary_raise_penalty(rng)
        assert 50 - 60 <= p.satisfaction <= 50 - 30


class TestSalary:
    def test_demand_probability_default(self):
        p = Person(0, "Test")
        p.salary_trait = 50
        assert p.salary_demand_probability() == pytest.approx(1.0 / 5.0)

    def test_demand_probability_high(self):
        p = Person(0, "Test")
        p.salary_trait = 90
        assert p.salary_demand_probability() == pytest.approx(1.0)

    def test_demand_probability_low(self):
        p = Person(0, "Test")
        p.salary_trait = 20
        assert p.salary_demand_probability() == pytest.approx(1.0 / 8.0)

    def test_loyalty_threshold(self):
        p = Person(0, "Test")
        p.salary_trait = 50
        p.trait7 = 50
        assert p.loyalty_threshold() == 0.0

    def test_loyalty_threshold_low_traits(self):
        p = Person(0, "Test")
        p.salary_trait = 20
        p.trait7 = 0
        assert p.loyalty_threshold() == pytest.approx(20.0)

    def test_wants_raise(self):
        p = Person(0, "Test")
        p.salary = 100000.0
        p.wealth = 110001.0
        assert p.wants_raise()
        p.wealth = 100000.0
        assert not p.wants_raise()

    def test_compute_target_salary(self):
        p = Person(0, "Test")
        p.salary = 100000.0
        p.years_of_service = 5
        assert p.compute_target_salary() == pytest.approx(150000.0)

    def test_random_raise_probability(self):
        p = Person(0, "Test")
        p.skills = [50.0] * N_SKILLS
        score = p.performance_score
        expected = 1.0 / (150.0 - score)
        assert p.random_raise_probability() == pytest.approx(expected)


class TestHiring:
    def test_acceptance_default(self):
        p = Person(0, "Test")
        assert p.acceptance_threshold() == -100
        assert p.would_accept_hire()

    def test_acceptance_max_trait(self):
        p = Person(0, "Test")
        p.acceptance_trait = 99
        assert p.acceptance_threshold() == -51
        p.satisfaction = -52
        assert not p.would_accept_hire()
        p.satisfaction = -51
        assert p.would_accept_hire()


class TestLifecycle:
    def test_link_as_ceo(self):
        p = Person(0, "Test")
        p.link_to_corp(1, as_ceo=True)
        assert p.state == STATE_LINKED
        assert p.role == ROLE_CEO
        assert p.corp_id == 1

    def test_link_as_president(self):
        p = Person(0, "Test")
        p.link_to_corp(2, as_ceo=False)
        assert p.role == ROLE_PRESIDENT

    def test_unlink(self):
        p = Person(0, "Test")
        p.link_to_corp(1)
        p.years_of_service = 5
        p.unlink()
        assert p.state == STATE_ACTIVE
        assert p.role == ROLE_INDEPENDENT
        assert p.corp_id is None
        assert p.years_of_service == 0

    def test_retire(self):
        p = Person(0, "Test")
        p.link_to_corp(1)
        p.retire()
        assert p.state == STATE_RETIRED
        assert p.role == ROLE_RETIRED
        assert p.corp_id is None


class TestTraits:
    def test_randomize_traits(self):
        rng = Rng(42)
        p = Person(0, "Test")
        p.randomize_traits(rng)
        assert 20 <= p.salary_trait <= 99
        assert 0 <= p.trait7 <= 99
        assert 20 <= p.expansion_trait <= 99
        assert 0 <= p.acceptance_trait <= 99

    def test_randomize_gender(self):
        rng = Rng(1)
        genders = set()
        for i in range(20):
            p = Person(i, f"P{i}")
            p.randomize_gender(rng)
            genders.add(p.gender)
        assert genders == {0, 1}


class TestCompetitorSpawning:
    def test_can_spawn_basic(self):
        p = Person(0, "Test")
        assert p.can_spawn_competitor(100, 3, 10)

    def test_cannot_spawn_linked(self):
        p = Person(0, "Test")
        p.link_to_corp(1)
        assert not p.can_spawn_competitor(100, 3, 10)

    def test_cannot_spawn_cooldown(self):
        p = Person(0, "Test")
        p.cooldown = 5
        assert not p.can_spawn_competitor(100, 3, 10)

    def test_cannot_spawn_cap_reached(self):
        p = Person(0, "Test")
        assert not p.can_spawn_competitor(100, 10, 10)

    def test_cannot_spawn_max_competitors(self):
        p = Person(0, "Test")
        assert not p.can_spawn_competitor(100, 12, 20)


class TestEconomyIntegration:
    def test_add_person(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        p = eco.add_person("Alice")
        assert p.id == 0
        assert eco.person_count() == 1
        assert eco.persons[0] is p

    def test_add_person_randomized(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        p = eco.add_person("Bob", randomize=True)
        assert p.gender in (0, 1)
        assert any(s > 0 for s in p.skills)

    def test_person_slots_limited(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        for i in range(int(PERSON_RULES.max_persons)):
            eco.add_person(f"P{i}")
        with pytest.raises(RuntimeError, match="person array full"):
            eco.add_person("Overflow")

    def test_active_persons(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        p1 = eco.add_person("Active")
        p2 = eco.add_person("Linked")
        p2.link_to_corp(0)
        assert p1 in eco.active_persons()
        assert p2 not in eco.active_persons()

    def test_competitor_count(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        eco.add_corp("Player", CORP_PLAYER)
        eco.add_corp("AI1", CORP_AI)
        eco.add_corp("AI2", CORP_AI)
        assert eco.competitor_count() == 2

    def test_persons_monthly_drift(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        p = eco.add_person("Test")
        p.satisfaction = -20
        eco.persons_monthly()
        assert p.satisfaction == -19

    def test_persons_yearly_service(self):
        sim, _ = bread_town(1)
        eco = sim.economy
        p = eco.add_person("Test")
        p.link_to_corp(0)
        assert p.years_of_service == 0
        eco.persons_yearly()
        assert p.years_of_service == 1

    def test_person_hash_deterministic(self):
        sim1, _ = bread_town(1)
        p1 = sim1.economy.add_person("Alice", randomize=True)
        p1.satisfaction = 42
        sim1.advance_days(60)

        sim2, _ = bread_town(1)
        p2 = sim2.economy.add_person("Alice", randomize=True)
        p2.satisfaction = 42
        sim2.advance_days(60)

        assert sim1.state_hash() == sim2.state_hash()

    def test_advance_with_persons_no_crash(self):
        sim, _town = bread_town(1)
        for i in range(5):
            p = sim.economy.add_person(f"Person{i}", randomize=True)
            if i < 3:
                corp = sim.economy.add_corp(f"Corp{i}", CORP_AI)
                p.link_to_corp(corp.id)
        sim.advance_days(120)
        assert sim.economy.person_count() == 5
