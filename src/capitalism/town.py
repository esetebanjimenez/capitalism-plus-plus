"""Towns and cities — plain classes on the hot path (design.md slice 2)."""

from __future__ import annotations

from enum import IntEnum

from .rng import Rng
from .tables import (
    CLIMATE_SPEND,
    CLIMATE_THRESHOLDS,
    LEVEL_RULES,
    SIMPLE_CITY,
    TIER_GNP,
    TOWN_GROWTH,
    UNEMPLOYMENT_DRIFT,
)


class Climate(IntEnum):
    PANIC = 0
    RECESSION = 1
    NORMAL = 2
    PROSPEROUS = 3
    BOOM = 4


def population_for_level(level: int) -> int:
    """Population needed to reach `level`: (level − 1)² × pop_per_level_sq."""
    return (level - 1) * (level - 1) * LEVEL_RULES.pop_per_level_sq


def level_for_population(population: float) -> int:
    """Level from population, capped at max_level."""
    level = 1
    while level < LEVEL_RULES.max_level and population >= population_for_level(level + 1):
        level += 1
    return level


def level_up_population(level: int) -> int:
    """Population needed to leave `level` (become level+1)."""
    return population_for_level(level + 1)


class Town:
    """A city on the map with living economic indicators."""

    __slots__ = (
        "climate",
        "consumer_spending",
        "env_factors",
        "gnp_growth_ring",
        "id",
        "labor_cost",
        "labor_quality",
        "last_month_gnp_growth",
        "last_month_population",
        "level",
        "name",
        "per_capita_gnp",
        "pop_ring",
        "population",
        "ring_index",
        "rolling_gnp_growth",
        "stagger_slot",
        "tier",
        "unemployment",
        "x",
        "y",
    )

    def __init__(
        self,
        *,
        id: int,
        name: str,
        tier: int,
        x: int,
        y: int,
        stagger_slot: int,
        population: float,
        per_capita_gnp: float,
        level: int = 1,
        unemployment: float | None = None,
        labor_cost: float | None = None,
        labor_quality: float | None = None,
        consumer_spending: float | None = None,
        climate: Climate = Climate.NORMAL,
        env_factors: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> None:
        self.id = id
        self.name = name
        self.tier = tier
        self.x = x
        self.y = y
        self.stagger_slot = stagger_slot
        self.population = population
        self.per_capita_gnp = per_capita_gnp
        self.level = level
        self.unemployment = SIMPLE_CITY.unemployment if unemployment is None else unemployment
        self.labor_cost = SIMPLE_CITY.labor_cost if labor_cost is None else labor_cost
        self.labor_quality = SIMPLE_CITY.labor_quality if labor_quality is None else labor_quality
        self.consumer_spending = (
            SIMPLE_CITY.spending if consumer_spending is None else consumer_spending
        )
        self.climate = climate
        self.env_factors = env_factors
        self.pop_ring: list[float] = [0.0] * 12
        self.gnp_growth_ring: list[float] = [0.0] * 12
        self.ring_index = 0
        self.last_month_population = population
        self.last_month_gnp_growth = 0.0
        self.rolling_gnp_growth = 0.0

    @property
    def gnp(self) -> float:
        return self.per_capita_gnp * self.population

    @classmethod
    def create(
        cls,
        town_id: int,
        name: str,
        tier: int,
        x: int,
        y: int,
        rng: Rng,
        *,
        detailed: bool,
    ) -> Town:
        lo, hi = TIER_GNP[tier].lo, TIER_GNP[tier].hi
        gnp = float(rng.randint(lo, hi))
        pop = float(tier * 300_000 + rng.randint(0, 30_000))
        slot = town_id % 30
        env = (
            float(rng.randint(-3, 3)),
            float(rng.randint(-3, 3)),
            float(rng.randint(-3, 3)),
        )
        if not detailed:
            return cls(
                id=town_id,
                name=name,
                tier=tier,
                x=x,
                y=y,
                stagger_slot=slot,
                population=pop,
                per_capita_gnp=float(SIMPLE_CITY.per_capita_gnp),
                level=SIMPLE_CITY.level,
                unemployment=SIMPLE_CITY.unemployment,
                labor_cost=SIMPLE_CITY.labor_cost,
                labor_quality=SIMPLE_CITY.labor_quality,
                consumer_spending=SIMPLE_CITY.spending,
                climate=Climate.NORMAL,
                env_factors=env,
            )
        return cls(
            id=town_id,
            name=name,
            tier=tier,
            x=x,
            y=y,
            stagger_slot=slot,
            population=pop,
            per_capita_gnp=gnp,
            level=level_for_population(pop),
            env_factors=env,
        )

    def monthly_tick(self, rng: Rng, *, detailed: bool) -> None:
        """City monthly tick (design.md). Order: pop, GNP, climate, unemp, labor, spend, quality, env."""
        if not detailed:
            return
        g = TOWN_GROWTH
        prev_pop = self.population
        prev_gnp = self.per_capita_gnp
        rolling = self.rolling_gnp_growth

        growth = (
            rng.uniform(g.pop_growth_lo, g.pop_growth_hi)
            + g.rolling_gnp_weight * rolling
            - g.unemp_weight * ((self.unemployment - g.unemp_baseline) / 100.0)
        )
        if growth < 0 and self.population < g.small_pop:
            growth *= 0.5
        if growth > 0 and self.population > g.large_pop:
            growth *= 0.5
        self.population = max(1.0, self.population * (1.0 + growth))
        self.level = level_for_population(self.population)

        self.per_capita_gnp *= rng.uniform(g.gnp_factor_lo, g.gnp_factor_hi)
        floor = TIER_GNP[self.tier].lo
        if self.per_capita_gnp < floor:
            self.per_capita_gnp = float(floor)
        while self.tier < 3 and self.per_capita_gnp > TIER_GNP[self.tier].hi:
            self.tier += 1

        gnp_growth = (self.per_capita_gnp - prev_gnp) / prev_gnp if prev_gnp else 0.0
        self.last_month_gnp_growth = gnp_growth
        self.gnp_growth_ring[self.ring_index] = gnp_growth
        self.rolling_gnp_growth = sum(self.gnp_growth_ring) / 12.0

        thr = CLIMATE_THRESHOLDS
        rg = self.rolling_gnp_growth
        if rg >= thr.boom:
            self.climate = Climate.BOOM
        elif rg >= thr.prosperous:
            self.climate = Climate.PROSPEROUS
        elif rg >= thr.normal:
            self.climate = Climate.NORMAL
        elif rg >= thr.recession:
            self.climate = Climate.RECESSION
        else:
            self.climate = Climate.PANIC

        drift, swing = UNEMPLOYMENT_DRIFT[int(self.climate)]
        self.unemployment += drift + rng.uniform(-swing, swing)
        self.unemployment = max(g.unemp_lo, min(g.unemp_hi, self.unemployment))

        env_a, env_b, env_c = self.env_factors
        target = self.per_capita_gnp / g.gnp_divisor * (1.0 + 0.01 * env_a)
        floor_lc = 0.5 * self.per_capita_gnp / g.gnp_divisor
        self.labor_cost += g.labor_step * (target - self.labor_cost)
        self.labor_cost = max(floor_lc, self.labor_cost)

        cf = CLIMATE_SPEND[int(self.climate)]
        spend_target = self.per_capita_gnp / g.gnp_divisor * cf * (1.0 + 0.01 * env_b)
        self.consumer_spending += g.labor_step * (spend_target - self.consumer_spending)
        self.consumer_spending = max(g.spend_floor, self.consumer_spending)

        q_target = max(
            g.labor_quality_lo,
            min(g.labor_quality_hi, self.per_capita_gnp / g.gnp_divisor * (1.0 + 0.01 * env_c)),
        )
        self.labor_quality += g.labor_step * (q_target - self.labor_quality)
        self.labor_quality = max(g.labor_quality_lo, min(g.labor_quality_hi, self.labor_quality))

        new_env = []
        for f in self.env_factors:
            if rng.chance(g.env_chance):
                f += 1.0 if rng.chance(0.5) else -1.0
            new_env.append(max(g.env_lo, min(g.env_hi, f)))
        self.env_factors = (new_env[0], new_env[1], new_env[2])

        self.pop_ring[self.ring_index] = self.population
        self.ring_index = (self.ring_index + 1) % 12
        self.last_month_population = prev_pop
