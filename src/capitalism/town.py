"""Towns and cities (gamelogic.md: Towns and cities)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

from .rng import Rng

# Per-capita GNP ranges by tier at creation.
TIER_GNP: dict[int, tuple[int, int]] = {
    0: (200, 2000),
    1: (2200, 7000),
    2: (7200, 14000),
    3: (14200, 20000),
}

# Tier floors (minimum per-capita GNP once at that tier).
TIER_FLOOR: dict[int, int] = {0: 200, 1: 2200, 2: 7200, 3: 14200}

# Detailed-mode-off fixed indicators.
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


def level_up_population(level: int) -> int:
    """Population needed to leave `level` (become level+1): level² × 160,000."""
    return level * level * 160_000


@dataclass
class Town:
    id: int
    name: str
    tier: int
    x: int
    y: int
    stagger_slot: int  # day-of-month 1-30 when this town runs its monthly tick
    population: float
    per_capita_gnp: float
    level: int = 1
    unemployment: float = 2.0
    labor_cost: float = 100.0
    labor_quality: float = 100.0
    consumer_spending: float = 100.0
    climate: Climate = Climate.NORMAL
    env_factors: tuple[float, float, float] = (0.0, 0.0, 0.0)
    # 12-month rings for charts
    pop_ring: list[float] = field(default_factory=lambda: [0.0] * 12)
    gnp_growth_ring: list[float] = field(default_factory=lambda: [0.0] * 12)
    ring_index: int = 0
    last_month_population: float = 0.0
    last_month_gnp_growth: float = 0.0

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
        lo, hi = TIER_GNP[tier]
        gnp = float(rng.randint(lo, hi))
        pop = float(tier * 300_000 + rng.randint(0, 30_000))
        slot = rng.randint(1, 30)
        env = (float(rng.randint(-3, 3)), float(rng.randint(-3, 3)), float(rng.randint(-3, 3)))
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
                last_month_population=pop,
            )
        t = cls(
            id=town_id,
            name=name,
            tier=tier,
            x=x,
            y=y,
            stagger_slot=slot,
            population=pop,
            per_capita_gnp=gnp,
            env_factors=env,
            last_month_population=pop,
        )
        # Raise level to match starting population.
        while t.level < 6 and t.population >= level_up_population(t.level):
            t.level += 1
        return t

    def monthly_tick(self, rng: Rng, *, detailed: bool) -> None:
        if not detailed:
            return
        prev_pop = self.population
        prev_gnp = self.per_capita_gnp

        # 1. Population growth
        econ = self.last_month_gnp_growth
        random_part = rng.uniform(-0.005, 0.005)
        econ_part = max(-0.01, min(0.02, econ * 0.5))
        unemp_part = -(self.unemployment - 5.0) * 0.001
        growth = random_part + econ_part + unemp_part
        # Dampen at extremes
        if self.population < 50_000:
            growth = max(growth, -0.002)
        if self.population > 3_000_000:
            growth = min(growth, 0.005)
        self.population = max(1.0, self.population * (1.0 + growth))
        while self.level < 6 and self.population >= level_up_population(self.level):
            self.level += 1

        # 2. Per-capita GNP ±1.7%
        self.per_capita_gnp *= rng.uniform(0.983, 1.013)
        floor = TIER_FLOOR[self.tier]
        if self.per_capita_gnp < floor:
            self.per_capita_gnp = float(floor)
        # Tier upgrade when past ceiling
        while self.tier < 3:
            _lo, hi = TIER_GNP[self.tier]
            if self.per_capita_gnp > hi:
                self.tier += 1
            else:
                break

        gnp_growth = (self.per_capita_gnp - prev_gnp) / prev_gnp if prev_gnp else 0.0
        self.last_month_gnp_growth = gnp_growth

        # 3. Economic climate
        if gnp_growth >= 0.08:
            self.climate = Climate.BOOM
        elif gnp_growth >= 0.04:
            self.climate = Climate.PROSPEROUS
        elif gnp_growth >= -0.01:
            self.climate = Climate.NORMAL
        elif gnp_growth >= -0.06:
            self.climate = Climate.RECESSION
        else:
            self.climate = Climate.PANIC

        # 4. Unemployment
        # Doc: ±0.30% etc as absolute percentage points on the unemployment rate.
        swing_map = {
            Climate.BOOM: 0.30,
            Climate.PROSPEROUS: 0.20,
            Climate.NORMAL: 0.10,
            Climate.RECESSION: 0.20,
            Climate.PANIC: 0.30,
        }
        bias = {
            Climate.BOOM: -0.20,
            Climate.PROSPEROUS: -0.10,
            Climate.NORMAL: 0.0,
            Climate.RECESSION: 0.10,
            Climate.PANIC: 0.20,
        }
        s = swing_map[self.climate]
        self.unemployment += bias[self.climate] + rng.uniform(-s, s)
        self.unemployment = max(2.0, min(10.0, self.unemployment))

        # 5-7. Smooth convergence (20% toward target)
        gnp_scale = self.per_capita_gnp / 10_000.0
        labor_target = max(50.0, 80.0 + gnp_scale * 40.0)
        spend_target = max(1.0, 60.0 + gnp_scale * 50.0)
        quality_target = max(1.0, min(100.0, 40.0 + gnp_scale * 30.0))
        self.labor_cost += 0.2 * (labor_target - self.labor_cost)
        self.consumer_spending = max(1.0, self.consumer_spending + 0.2 * (spend_target - self.consumer_spending))
        self.labor_quality = max(1.0, min(100.0, self.labor_quality + 0.2 * (quality_target - self.labor_quality)))

        # 8. Env factors drift slightly
        self.env_factors = tuple(
            max(-5.0, min(5.0, f + rng.uniform(-0.2, 0.2))) for f in self.env_factors
        )

        # Rings
        self.pop_ring[self.ring_index] = self.population
        self.gnp_growth_ring[self.ring_index] = gnp_growth
        self.ring_index = (self.ring_index + 1) % 12
        self.last_month_population = prev_pop
