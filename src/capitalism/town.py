"""Towns and cities — plain classes on the hot path (design.md slice 2)."""

from __future__ import annotations

from enum import IntEnum

from .rng import Rng
from .tables import (
    CLIMATE_SPEND,
    TIER_GNP,
    UNEMPLOYMENT_DRIFT,
)

SIMPLE_LEVEL = 3
SIMPLE_GNP = 20_000
SIMPLE_LABOR_COST = 100.0
SIMPLE_SPENDING = 100.0
SIMPLE_LABOR_QUALITY = 100.0
SIMPLE_UNEMPLOYMENT = 2.0


class Climate(IntEnum):
    PANIC = 0
    RECESSION = 1
    NORMAL = 2
    PROSPEROUS = 3
    BOOM = 4


def population_for_level(level: int) -> int:
    """Population needed to reach `level`: (level − 1)² × 160,000."""
    return (level - 1) * (level - 1) * 160_000


def level_for_population(population: float) -> int:
    """Level from population, capped at 6."""
    level = 1
    while level < 6 and population >= population_for_level(level + 1):
        level += 1
    return level


# Back-compat alias used by older tests / callers.
def level_up_population(level: int) -> int:
    """Population needed to leave `level` (become level+1): level² × 160,000."""
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
        unemployment: float = 2.0,
        labor_cost: float = 100.0,
        labor_quality: float = 100.0,
        consumer_spending: float = 100.0,
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
        self.unemployment = unemployment
        self.labor_cost = labor_cost
        self.labor_quality = labor_quality
        self.consumer_spending = consumer_spending
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
                per_capita_gnp=float(SIMPLE_GNP),
                level=SIMPLE_LEVEL,
                unemployment=SIMPLE_UNEMPLOYMENT,
                labor_cost=SIMPLE_LABOR_COST,
                labor_quality=SIMPLE_LABOR_QUALITY,
                consumer_spending=SIMPLE_SPENDING,
                climate=Climate.NORMAL,
                env_factors=env,
            )
        level = level_for_population(pop)
        return cls(
            id=town_id,
            name=name,
            tier=tier,
            x=x,
            y=y,
            stagger_slot=slot,
            population=pop,
            per_capita_gnp=gnp,
            level=level,
            env_factors=env,
        )

    def monthly_tick(self, rng: Rng, *, detailed: bool) -> None:
        """City monthly tick (design.md). Order: pop, GNP, climate, unemp, labor, spend, quality, env."""
        if not detailed:
            return
        prev_pop = self.population
        prev_gnp = self.per_capita_gnp
        rolling = self.rolling_gnp_growth

        # Population (design.md). Unemployment is stored as percentage points (2..10).
        growth = (
            rng.uniform(-0.002, 0.004) + 0.05 * rolling - 0.05 * ((self.unemployment - 5.0) / 100.0)
        )
        if growth < 0 and self.population < 50_000:
            growth *= 0.5
        if growth > 0 and self.population > 4_000_000:
            growth *= 0.5
        self.population = max(1.0, self.population * (1.0 + growth))
        self.level = level_for_population(self.population)

        # Per-capita GNP
        self.per_capita_gnp *= rng.uniform(0.983, 1.013)
        floor = TIER_GNP[self.tier].lo
        if self.per_capita_gnp < floor:
            self.per_capita_gnp = float(floor)
        while self.tier < 3 and self.per_capita_gnp > TIER_GNP[self.tier].hi:
            self.tier += 1

        gnp_growth = (self.per_capita_gnp - prev_gnp) / prev_gnp if prev_gnp else 0.0
        self.last_month_gnp_growth = gnp_growth
        self.gnp_growth_ring[self.ring_index] = gnp_growth
        self.rolling_gnp_growth = sum(self.gnp_growth_ring) / 12.0

        # Climate from 12-month rolling GNP growth (design call)
        g = self.rolling_gnp_growth
        if g >= 0.08:
            self.climate = Climate.BOOM
        elif g >= 0.04:
            self.climate = Climate.PROSPEROUS
        elif g >= -0.01:
            self.climate = Climate.NORMAL
        elif g >= -0.06:
            self.climate = Climate.RECESSION
        else:
            self.climate = Climate.PANIC

        # Unemployment
        drift, swing = UNEMPLOYMENT_DRIFT[int(self.climate)]
        self.unemployment += drift + rng.uniform(-swing, swing)
        self.unemployment = max(2.0, min(10.0, self.unemployment))

        env_a, env_b, env_c = self.env_factors
        # Labor cost
        target = self.per_capita_gnp / 200.0 * (1.0 + 0.01 * env_a)
        floor_lc = 0.5 * self.per_capita_gnp / 200.0
        self.labor_cost += 0.2 * (target - self.labor_cost)
        self.labor_cost = max(floor_lc, self.labor_cost)

        # Consumer spending
        cf = CLIMATE_SPEND[int(self.climate)]
        spend_target = self.per_capita_gnp / 200.0 * cf * (1.0 + 0.01 * env_b)
        self.consumer_spending += 0.2 * (spend_target - self.consumer_spending)
        self.consumer_spending = max(1.0, self.consumer_spending)

        # Labor quality
        q_target = max(1.0, min(100.0, self.per_capita_gnp / 200.0 * (1.0 + 0.01 * env_c)))
        self.labor_quality += 0.2 * (q_target - self.labor_quality)
        self.labor_quality = max(1.0, min(100.0, self.labor_quality))

        # Environmental factors: 10% chance each to move ±1, clamp −3..+3
        new_env = []
        for f in self.env_factors:
            if rng.chance(0.10):
                f += 1.0 if rng.chance(0.5) else -1.0
            new_env.append(max(-3.0, min(3.0, f)))
        self.env_factors = (new_env[0], new_env[1], new_env[2])

        self.pop_ring[self.ring_index] = self.population
        self.ring_index = (self.ring_index + 1) % 12
        self.last_month_population = prev_pop
