"""Headless simulation. Systems 1–2: clock/passes and world data."""

from __future__ import annotations

from .calendar import Calendar
from .rng import Rng
from .town import Town
from .world import World, generate_world


class Sim:
    """Seeded simulation. Same seed produces the same run.

    Owns the calendar, world and RNG. Later systems (firms, products, markets)
    attach here as object graphs with Pydantic models and subclasses.
    """

    def __init__(
        self,
        seed: int = 0,
        *,
        detailed_cities: bool = True,
        target_cities: int = 8,
    ) -> None:
        self.seed = seed
        self.detailed_cities = detailed_cities
        self.target_cities = target_cities
        self.rng: Rng
        self.calendar: Calendar
        self.world: World
        self.gnp_index: float = 1.0
        self.gnp_history: list[float] = []
        self.history: list[dict[str, int | float]] = []
        self.reset(seed)

    def reset(self, seed: int | None = None) -> None:
        if seed is not None:
            self.seed = seed
        self.rng = Rng(self.seed)
        self.calendar = Calendar()
        self.world = generate_world(
            self.rng,
            detailed_cities=self.detailed_cities,
            target_cities=self.target_cities,
        )
        self.gnp_index = 1.0
        self.gnp_history = []
        self.history = []

    @property
    def day(self) -> int:
        return self.calendar.day

    @property
    def month(self) -> int:
        return self.calendar.month

    @property
    def year(self) -> int:
        return self.calendar.year

    @property
    def towns(self) -> list[Town]:
        return self.world.towns

    def advance_day(self) -> None:
        """Advance one economic day. Month/year passes run on boundaries."""
        month_rolled, year_rolled = self.calendar.advance()
        if month_rolled:
            self._month_pass()
        if year_rolled:
            self._year_pass()
        self._daily_batch()
        self.history.append(
            {
                "year": self.calendar.year,
                "month": self.calendar.month,
                "day": self.calendar.day,
                "weekday": self.calendar.weekday,
                "towns": len(self.world.towns),
                "gnp_index": self.gnp_index,
            }
        )

    def advance_days(self, n: int) -> None:
        if n < 0:
            raise ValueError("n must be >= 0")
        for _ in range(n):
            self.advance_day()

    def _daily_batch(self) -> None:
        for town in self.world.towns:
            if town.stagger_slot == self.calendar.day:
                town.monthly_tick(self.rng, detailed=self.detailed_cities)

    def _month_pass(self) -> None:
        if self.world.towns:
            avg = sum(t.last_month_gnp_growth for t in self.world.towns) / len(self.world.towns)
            if avg < -0.02 and self.rng.chance(0.3):
                self.gnp_index = min(2.0, self.gnp_index + 0.01)
            elif avg > 0.05 and self.gnp_index > 1.0 and self.rng.chance(0.3):
                self.gnp_index = max(0.5, self.gnp_index - 0.01)

    def _year_pass(self) -> None:
        self.gnp_history.append(self.gnp_index)
        if len(self.gnp_history) > 10:
            self.gnp_history.pop(0)

    def report(self) -> str:
        cal = self.calendar
        lines = [
            "Capitalism++ sim",
            f"  seed:   {self.seed}",
            (
                f"  date:   Y{cal.year} M{cal.month} D{cal.day}"
                f" (weekday {cal.weekday}, serial {cal.day_serial})"
            ),
            f"  days:   {len(self.history)}",
            f"  salary month length: {cal.real_month_days} days",
            f"  GNP index: {self.gnp_index:.3f}",
            (
                f"  map:    {self.world.width}x{self.world.height},"
                f" {len(self.world.towns)} cities, centroid"
                f" ({self.world.centroid[0]:.0f},{self.world.centroid[1]:.0f})"
            ),
        ]
        for t in self.world.towns:
            lines.append(
                f"    - {t.name}: pop {t.population:,.0f}, level {t.level},"
                f" GNP/cap {t.per_capita_gnp:,.0f}, tier {t.tier},"
                f" stagger D{t.stagger_slot}"
            )
        return "\n".join(lines) + "\n"


class Game:
    """Top-level session: owns a Sim. Save/load and UI attach here later."""

    def __init__(
        self,
        seed: int = 0,
        *,
        detailed_cities: bool = True,
        target_cities: int = 8,
    ) -> None:
        self.sim = Sim(
            seed=seed,
            detailed_cities=detailed_cities,
            target_cities=target_cities,
        )

    def advance_days(self, n: int) -> None:
        self.sim.advance_days(n)

    def report(self) -> str:
        return self.sim.report()
