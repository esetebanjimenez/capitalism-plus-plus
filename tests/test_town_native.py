"""Town growth vs the native binary (FUN_0004b4de pop/level, FUN_0004b377 GNP term)."""

from __future__ import annotations

import pytest

from capitalism.rng import Rng
from capitalism.tables import load_level_rules, load_town_growth
from capitalism.town import Town

G = load_town_growth()
SQ = load_level_rules().pop_per_level_sq


def town(pop: float, level: int, gnp: float = 20_000.0) -> Town:
    return Town(
        id=0, name="T", tier=1, x=0, y=0, stagger_slot=0,
        population=pop, per_capita_gnp=gnp, level=level, env_factors=(0.0, 0.0, 0.0),
    )  # fmt: skip


def test_gnp_term_is_scaled_twelve_month_total_change():
    t = town(1_000_000.0, 7)
    t.gnp_this_year = [100.0] * 12
    t.gnp_prev_year = [0.0] * 12
    t.ring_index = 3
    t.monthly_stats()  # month 3: prev[3] = 100, this[3] = pop × gnp
    cur = 100.0 * 11 + 20_000.0 * 1_000_000.0
    assert t.gnp_prev_year[3] == 100.0
    assert t.gnp_growth_pct[3] == pytest.approx((cur - 100.0) * G.gnp_growth_scale / 100.0)


def test_gnp_term_feeds_population_growth_in_simple_mode():
    a, b = town(640_000.0, 3), town(640_000.0, 3)
    b.gnp_growth_pct[11] = 2.0  # read at ring_index 0 (previous month)
    a.monthly_tick(Rng(5), detailed=False)
    b.monthly_tick(Rng(5), detailed=False)
    assert b.population - a.population == pytest.approx(2.0 * G.pop_gnp_scale)
    assert b.gnp_this_year[0] == pytest.approx(b.population * b.per_capita_gnp)


def test_level_rises_one_step_per_tick_without_cap():
    t = town(SQ * 8 * 8 + 1_000_000.0, 6)  # far past the level-7 and level-8 thresholds
    t.monthly_tick(Rng(1), detailed=False)
    assert t.level == 7
    t.monthly_tick(Rng(1), detailed=False)
    assert t.level == 8


def test_level_never_drops():
    t = town(1_000.0, 5)
    t.monthly_tick(Rng(1), detailed=False)
    assert t.level == 5
