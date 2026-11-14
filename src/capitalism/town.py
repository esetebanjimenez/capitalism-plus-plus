"""Towns and cities — plain classes on the hot path (design.md slice 2)."""

from __future__ import annotations

from enum import IntEnum

from .rng import Rng
from .tables import (
    CLIMATE_SPEND,
    CLIMATE_THRESHOLDS,
    LEVEL_RULES,
    SIMPLE_CITY,
    STAGGER_MOD,
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
        "gnp_growth_pct",
        "gnp_level_ring",
        "gnp_month_ring",
        "gnp_prev_year",
        "gnp_this_year",
        "id",
        "labor_cost",
        "labor_quality",
        "last_month_gnp_growth",
        "last_month_population",
        "level",
        "months_recorded",
        "name",
        "per_capita_gnp",
        "pop_ring",
        "population",
        "ring_index",
        "rolling_gnp_growth",
        "spread_blocked",
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
        # Native abort flag town+0x1d: set when spread meets another town's tile; it
        # stops all later spread and level-ups (FUN_0004c334, decomp:46538).
        self.spread_blocked = False
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
        self.gnp_level_ring: list[float] = [per_capita_gnp] * 12
        self.ring_index = 0
        # Bookkeeping for the town card charts (#255), not native state: how many months
        # the rings hold (capped at 12), and per-capita GNP at each month end. The native
        # gnp_level_ring is written only in detailed months, so it can hold stale slots.
        self.months_recorded = 0
        self.gnp_month_ring: list[float] = [0.0] * 12
        self.last_month_population = population
        self.last_month_gnp_growth = 0.0
        self.rolling_gnp_growth = 0.0
        # Native monthly stats (FUN_0004b377): total GNP per month this year and last,
        # and the 12-month total-GNP change that population growth reads.
        # Seeded from the first month's total on first use (new-game init not traced).
        self.gnp_this_year: list[float] = [0.0] * 12
        self.gnp_prev_year: list[float] = [0.0] * 12
        self.gnp_growth_pct: list[float] = [0.0] * 12

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
        g0 = TOWN_GROWTH
        pop = float(tier * g0.pop_per_tier + rng.randint(0, int(g0.pop_tier_noise)))
        slot = town_id % STAGGER_MOD
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

    def monthly_tick(self, rng: Rng, *, detailed: bool) -> bool:
        """City monthly tick — pop always, rest only when detailed.

        Returns True when the town levelled up this tick.
        """
        g = TOWN_GROWTH
        prev_pop = self.population
        levelled_up = False

        # --- Population growth (always runs, even simple-mode) ---
        growth = (
            float(rng.randint(0, g.pop_random_range - 1))
            + self.gnp_growth_pct[(self.ring_index - 1) % 12] * g.pop_gnp_scale
            + (g.pop_unemp_target - self.unemployment) * g.pop_unemp_scale
            + g.pop_base_offset
        )
        if growth <= 0.0 and self.population < g.small_pop:
            growth = growth * self.population / g.small_pop
        elif growth > 0.0 and self.population > g.large_pop:
            growth = growth * g.large_pop / self.population

        new_pop = self.population + growth
        if new_pop > 0.0:
            unemp_people = self.population * self.unemployment / g.pop_unemp_scale + growth
            self.unemployment = unemp_people * g.pop_unemp_scale / new_pop
        self.population = max(0.0, new_pop)
        # Native: +1 level per tick once pop >= level_pop_per_sq x L^2; never down, no cap.
        # The abort flag (town+0x1d) is checked first (decomp:46538).
        if not self.spread_blocked and self.population >= level_up_population(self.level):
            self.level += 1
            levelled_up = True

        if not detailed:
            self.monthly_stats()
            self.pop_ring[self.ring_index] = self.population
            self._advance_ring()
            self.last_month_population = prev_pop
            return levelled_up

        # --- GNP update (detailed only) ---
        prev_gnp = self.per_capita_gnp
        self.per_capita_gnp *= (
            rng.randint(0, g.gnp_walk_steps - 1) + g.gnp_walk_base
        ) / g.gnp_walk_divisor
        floor = TIER_GNP[self.tier].lo
        if self.per_capita_gnp < floor:
            self.per_capita_gnp = float(floor)
        # Native bug: guard reads `gnp < 3.0` instead of `tier < 3`, making upgrade dead code.
        while self.tier < 3 and self.per_capita_gnp > TIER_GNP[self.tier].hi:
            self.tier += 1

        month_delta = (self.per_capita_gnp - prev_gnp) / prev_gnp if prev_gnp else 0.0
        self.last_month_gnp_growth = month_delta
        # True 12-month change: current / value from 12 months ago − 1.
        # gnp_level_ring[ring_index] still holds the value we're about to overwrite.
        year_ago = self.gnp_level_ring[self.ring_index]
        if year_ago > 0:
            self.rolling_gnp_growth = self.per_capita_gnp / year_ago - 1.0
        else:
            self.rolling_gnp_growth = 0.0
        self.gnp_level_ring[self.ring_index] = self.per_capita_gnp

        # FUN_0004b68e reads this month's town+0x113 entry, the same total-GNP term
        # FUN_0004b377 stores for pop growth, so compute it before the climate check.
        self.monthly_stats()
        self.update_climate(self.gnp_growth_pct[self.ring_index])

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
        self._advance_ring()
        self.last_month_population = prev_pop
        return levelled_up

    def _advance_ring(self) -> None:
        self.gnp_month_ring[self.ring_index] = self.per_capita_gnp
        self.ring_index = (self.ring_index + 1) % 12
        self.months_recorded = min(12, self.months_recorded + 1)

    def history_slots(self) -> list[int]:
        """Ring slots of the recorded months, oldest first (at most 12)."""
        n = self.months_recorded
        return [(self.ring_index - n + k) % 12 for k in range(n)]

    def update_climate(self, gnp_growth: float) -> None:
        """FUN_0004b68e (decomp:46590-46598): the first DAT_000adad0 threshold that is
        <= the GNP term sets the climate (0 Boom .. 4 Panic); none matching keeps it."""
        thr = CLIMATE_THRESHOLDS
        for climate, limit in enumerate(
            (thr.boom, thr.prosperous, thr.normal, thr.recession, thr.panic)
        ):
            if gnp_growth >= limit:
                self.climate = Climate(climate)
                return

    def monthly_stats(self) -> None:
        """FUN_0004b377, run for every town in both modes: roll this month's total GNP
        into last year's slot, then store gnp_growth_scale x the 12-month total change."""
        m = self.ring_index
        if not any(self.gnp_this_year):
            total = self.per_capita_gnp * self.population
            self.gnp_this_year = [total] * 12
            self.gnp_prev_year = [total] * 12
        self.gnp_prev_year[m] = self.gnp_this_year[m]
        self.gnp_this_year[m] = self.per_capita_gnp * self.population
        prev = sum(self.gnp_prev_year)
        cur = sum(self.gnp_this_year)
        scale = TOWN_GROWTH.gnp_growth_scale
        self.gnp_growth_pct[m] = (cur - prev) * scale / prev if prev > 0 else 0.0
