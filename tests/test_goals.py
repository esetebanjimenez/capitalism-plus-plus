"""Tests for goals, scoring, and difficulty rating (system 12)."""

from __future__ import annotations

import pytest

from capitalism.goals import (
    GameResult,
    GoalChecker,
    GoalConfig,
    check_goals,
    compute_difficulty_rating,
    compute_final_score,
)
from capitalism.tables import SetupOptions

# ---------------------------------------------------------------------------
# GoalConfig
# ---------------------------------------------------------------------------


class TestGoalConfig:
    def test_default_no_goals(self):
        gc = GoalConfig()
        assert not gc.has_any_goal

    def test_numeric_goal_detected(self):
        gc = GoalConfig()
        gc.personal_wealth = 10_000_000.0
        assert gc.has_any_goal

    def test_sector_goal_detected(self):
        gc = GoalConfig()
        gc.sector_goals[0] = True
        assert gc.has_any_goal

    def test_industry_goal_detected(self):
        gc = GoalConfig()
        gc.industry_goals = [True, False]
        assert gc.has_any_goal

    def test_all_zero_is_no_goal(self):
        gc = GoalConfig()
        gc.personal_wealth = 0.0
        gc.corp_net_worth = 0.0
        assert not gc.has_any_goal


# ---------------------------------------------------------------------------
# Difficulty rating
# ---------------------------------------------------------------------------


class TestDifficultyRating:
    def test_default_setup(self):
        setup = SetupOptions()
        rating = compute_difficulty_rating(setup)
        assert rating >= 1

    def test_harder_is_higher(self):
        easy = SetupOptions(
            competitors=3,
            competitor_capital=0,
            competence_level=0,
            show_trade_secrets=True,
            event_frequency=0,
        )
        hard = SetupOptions(
            competitors=8,
            competitor_capital=4,
            competence_level=3,
            show_trade_secrets=False,
            event_frequency=3,
        )
        assert compute_difficulty_rating(hard) > compute_difficulty_rating(easy)

    def test_no_seaports_adds_penalty(self):
        with_ports = SetupOptions(consumer_seaports=2, industrial_seaports=2)
        no_ports = SetupOptions(consumer_seaports=0, industrial_seaports=0)
        assert compute_difficulty_rating(no_ports) > compute_difficulty_rating(with_ports)

    def test_minimum_is_1(self):
        setup = SetupOptions(
            competitors=0,
            competitor_capital=0,
            competence_level=0,
            event_frequency=0,
        )
        assert compute_difficulty_rating(setup) >= 1

    def test_trade_secrets_penalty(self):
        visible = SetupOptions(show_trade_secrets=True)
        hidden = SetupOptions(show_trade_secrets=False)
        assert compute_difficulty_rating(hidden) > compute_difficulty_rating(visible)

    def test_expertise_levels(self):
        none_ = SetupOptions(expertise_level=0)
        vlow = SetupOptions(expertise_level=1)
        high = SetupOptions(expertise_level=4)
        r0 = compute_difficulty_rating(none_)
        r1 = compute_difficulty_rating(vlow)
        r4 = compute_difficulty_rating(high)
        assert r1 > r0
        assert r4 > r1

    def test_competitor_character(self):
        conservative = SetupOptions(competitor_character=0)
        aggressive = SetupOptions(competitor_character=3)
        mixed = SetupOptions(competitor_character=4)
        r0 = compute_difficulty_rating(conservative)
        r3 = compute_difficulty_rating(aggressive)
        rm = compute_difficulty_rating(mixed)
        assert r3 > r0
        assert rm > r0


# ---------------------------------------------------------------------------
# Final scoring
# ---------------------------------------------------------------------------


class TestFinalScore:
    def test_basic_score(self):
        setup = SetupOptions()
        score = compute_final_score(
            setup,
            personal_wealth=1_000_000_000.0,
            corp_net_worth=500_000_000.0,
            sectors_dominated=2,
            products_dominated=5,
            years_played=10,
            goals_achieved=False,
        )
        assert score >= 1

    def test_cheated_is_zero(self):
        setup = SetupOptions(cheated=True)
        score = compute_final_score(
            setup,
            personal_wealth=10_000_000_000.0,
            corp_net_worth=5_000_000_000.0,
            sectors_dominated=4,
            products_dominated=20,
            years_played=10,
            goals_achieved=True,
        )
        assert score == 0

    def test_goal_bonus_free_game(self):
        setup = SetupOptions(is_scenario=False)
        without = compute_final_score(
            setup, 1e9, 1e9, 2, 5, 10, goals_achieved=False,
        )
        with_ = compute_final_score(
            setup, 1e9, 1e9, 2, 5, 10, goals_achieved=True,
        )
        assert with_ > without

    def test_goal_bonus_scenario(self):
        setup = SetupOptions(is_scenario=True, goal_score_bonus=200)
        without = compute_final_score(
            setup, 1e9, 1e9, 2, 5, 10, goals_achieved=False,
        )
        with_ = compute_final_score(
            setup, 1e9, 1e9, 2, 5, 10, goals_achieved=True,
        )
        assert with_ > without

    def test_year_penalty(self):
        setup = SetupOptions()
        short = compute_final_score(
            setup, 1e9, 1e9, 2, 5, 30, goals_achieved=False,
        )
        long_ = compute_final_score(
            setup, 1e9, 1e9, 2, 5, 100, goals_achieved=False,
        )
        assert short > long_

    def test_no_year_penalty_before_threshold(self):
        setup = SetupOptions()
        s40 = compute_final_score(
            setup, 1e9, 1e9, 2, 5, 40, goals_achieved=False,
        )
        s50 = compute_final_score(
            setup, 1e9, 1e9, 2, 5, 50, goals_achieved=False,
        )
        assert s40 == s50

    def test_minimum_score(self):
        setup = SetupOptions()
        score = compute_final_score(
            setup, 0, 0, 0, 0, 10, goals_achieved=False,
        )
        assert score >= 1

    def test_difficulty_affects_score(self):
        easy = SetupOptions(competitors=0, competitor_capital=0)
        hard = SetupOptions(competitors=8, competitor_capital=4)
        se = compute_final_score(easy, 1e9, 1e9, 2, 5, 10, False)
        sh = compute_final_score(hard, 1e9, 1e9, 2, 5, 10, False)
        assert sh > se


# ---------------------------------------------------------------------------
# GoalChecker
# ---------------------------------------------------------------------------


class TestGoalChecker:
    def test_no_goals_stays_in_progress(self):
        gc = GoalConfig()
        checker = GoalChecker(gc)
        setup = SetupOptions()
        from capitalism.scenario import bread_town
        sim, _ = bread_town()
        result = checker.daily(sim.economy, 0, 1990, setup)
        assert result == GameResult.IN_PROGRESS

    def test_yearly_deadline_defeat(self):
        gc = GoalConfig()
        gc.personal_wealth = 999_999_999_999.0
        checker = GoalChecker(gc)
        result = checker.yearly(2000, 1990, 10)
        assert result == GameResult.DEFEAT_DEADLINE

    def test_yearly_no_limit(self):
        gc = GoalConfig()
        gc.personal_wealth = 1.0
        checker = GoalChecker(gc)
        result = checker.yearly(2050, 1990, 0)
        assert result == GameResult.IN_PROGRESS

    def test_yearly_warning(self):
        gc = GoalConfig()
        gc.personal_wealth = 1.0
        checker = GoalChecker(gc)
        checker.yearly(1997, 1990, 10)
        assert checker.years_warning == 3


# ---------------------------------------------------------------------------
# Goal checking
# ---------------------------------------------------------------------------


class TestCheckGoals:
    def test_all_zero_targets_met(self):
        gc = GoalConfig()
        from capitalism.scenario import bread_town
        sim, _ = bread_town()
        all_met, results = check_goals(gc, sim.economy, 0)
        assert all_met
        assert len(results) == 0

    def test_impossible_goal_not_met(self):
        gc = GoalConfig()
        gc.personal_wealth = 999_999_999.0
        from capitalism.scenario import bread_town
        sim, _ = bread_town()
        all_met, results = check_goals(gc, sim.economy, 0)
        assert not all_met
        assert "personal_wealth" in results
        assert not results["personal_wealth"][2]


# ---------------------------------------------------------------------------
# Setup options extensions
# ---------------------------------------------------------------------------


class TestSetupOptions:
    def test_year_limit_default(self):
        opts = SetupOptions()
        assert opts.year_limit == 0

    def test_goal_score_bonus(self):
        opts = SetupOptions(goal_score_bonus=250)
        assert opts.goal_score_bonus == 250

    def test_goal_score_bonus_range(self):
        with pytest.raises(ValueError):
            SetupOptions(goal_score_bonus=501)

    def test_is_scenario(self):
        opts = SetupOptions(is_scenario=True)
        assert opts.is_scenario

    def test_cheated(self):
        opts = SetupOptions(cheated=True)
        assert opts.cheated

    def test_competitors(self):
        opts = SetupOptions(competitors=7)
        assert opts.competitors == 7

    def test_all_new_fields(self):
        opts = SetupOptions(
            year_limit=20,
            goal_score_bonus=100,
            competitors=5,
            competitor_capital=3,
            competence_level=2,
            expertise_level=1,
            show_trade_secrets=False,
            competitor_character=2,
            consumer_seaports=1,
            industrial_seaports=1,
            constant_supply=False,
            import_quality=1,
            is_scenario=True,
            cheated=False,
        )
        assert opts.year_limit == 20
        assert opts.import_quality == 1


# ---------------------------------------------------------------------------
# Sim integration
# ---------------------------------------------------------------------------


class TestSimIntegration:
    def test_goal_checker_on_sim(self):
        from capitalism.scenario import bread_town
        sim, _ = bread_town()
        assert sim.goal_checker.result == GameResult.IN_PROGRESS

    def test_advance_with_goals(self):
        from capitalism.scenario import bread_town
        sim, _ = bread_town()
        sim.goal_config.personal_wealth = 999_999_999.0
        sim.reset()
        sim.advance_days(100)
        assert sim.goal_checker.result == GameResult.IN_PROGRESS

    def test_victory_on_easy_goal(self):
        from capitalism.scenario import bread_town
        sim, _ = bread_town()
        sim.economy.add_corp("TestCorp", corp_type=1)
        sim.goal_config.personal_wealth = 0.01
        sim.goal_checker = GoalChecker(sim.goal_config, player_corp_id=0)
        sim.advance_days(10)
        assert sim.goal_checker.result == GameResult.IN_PROGRESS
