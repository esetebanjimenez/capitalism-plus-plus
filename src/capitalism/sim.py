"""Headless simulation. Systems 1–2: clock/passes and world data."""

from __future__ import annotations

import hashlib
import struct
from datetime import date

from .calendar import DEFAULT_START, Calendar
from .rng import Rng
from .tables import GNP_INDEX, SetupOptions
from .town import Town
from .world import World, generate_world, try_spawn_town


class Sim:
    """Seeded simulation. Same seed produces the same run."""

    def __init__(
        self,
        seed: int = 0,
        *,
        detailed_cities: bool = True,
        target_cities: int = 5,
        start_year: int = 1990,
        record_hooks: bool = False,
    ) -> None:
        self.setup = SetupOptions(
            seed=seed,
            start_year=start_year,
            detailed_cities=detailed_cities,
            target_cities=target_cities,
        )
        self.seed = seed
        self.detailed_cities = detailed_cities
        self.target_cities = target_cities
        self.start_year = start_year
        self.record_hooks = record_hooks
        self.rng: Rng
        self.calendar: Calendar
        self.world: World
        self.gnp_index: float = 1.0
        self.gnp_history: list[float] = []
        self.avg_gnp_growth_12m: float = 0.0
        self.history: list[dict[str, int | float]] = []
        self.hooks: list[str] = []
        self.reset(seed)

    def reset(self, seed: int | None = None) -> None:
        if seed is not None:
            self.seed = seed
            self.setup.seed = seed
        self.rng = Rng(self.seed)
        start = date(self.start_year, 1, 1) if self.start_year != 1990 else DEFAULT_START
        self.calendar = Calendar(start)
        self.world = generate_world(
            self.rng,
            detailed_cities=self.detailed_cities,
            target_cities=self.target_cities,
        )
        self.gnp_index = 1.0
        self.gnp_history = []
        self.avg_gnp_growth_12m = 0.0
        self.history = []
        self.hooks = []

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

    def _hook(self, name: str) -> None:
        if self.record_hooks:
            self.hooks.append(name)

    def advance_day(self) -> None:
        """One economic day (design.md slice 1 order)."""
        # 1–3: firms, jobs, links (stubs in slice 1)
        self._hook("firms")
        self._hook("jobs")
        self._hook("links")

        # 4. Daily batch
        # 4.1 Day advance (+ month/year passes on boundaries)
        month_rolled, year_rolled = self.calendar.advance()
        if month_rolled:
            self._month_pass()
        if year_rolled:
            self._year_pass()

        self._hook("corporations")
        self._hook("people")
        self._towns_daily()
        self._hook("goals")
        if self.calendar.weekday == 5:
            self._hook("weekly_ratings")
        self._hook("random_events")
        self._hook("products")
        self._hook("natural_resources")

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
            raise ValueError("n must be >= 0")  # typo guard — fix below
        for _ in range(n):
            self.advance_day()

    def _towns_daily(self) -> None:
        self._hook("towns")
        slot = self.calendar.day_serial % 30
        for town in self.world.towns:
            if town.stagger_slot == slot:
                town.monthly_tick(self.rng, detailed=self.detailed_cities)

    def _month_pass(self) -> None:
        # 1. GNP index adjustment
        self._hook("month_gnp_index")
        t = GNP_INDEX
        avg = self.avg_gnp_growth_12m
        if self.rng.chance(t.step_chance):
            if avg > t.high_growth:
                delta = t.step
            elif avg < t.low_growth:
                delta = -t.step
            else:
                delta = t.step if self.rng.chance(0.5) else -t.step
            self.gnp_index = max(t.floor, self.gnp_index + delta)

        # 2. Product catalog maintenance (stub)
        self._hook("month_products")

        # 3. Town monthly: stats ring, spawn, demand, centroid
        self._hook("month_towns")
        if self.world.towns:
            self.avg_gnp_growth_12m = sum(t.rolling_gnp_growth for t in self.world.towns) / len(
                self.world.towns
            )
        try_spawn_town(self.world, self.rng, self.calendar.day_serial)

        # 4–5. Corporations / firms / jobs / links monthly (stubs)
        self._hook("month_corporations")
        self._hook("month_firms_jobs_links")

    def _year_pass(self) -> None:
        self._hook("year_pass")
        self.gnp_history.append(self.gnp_index)
        if len(self.gnp_history) > 10:
            self.gnp_history.pop(0)

    def state_hash(self) -> str:
        """Stable hash of full sim state for determinism tests."""
        h = hashlib.sha256()
        cal = self.calendar
        h.update(struct.pack("<iiii", cal.year, cal.month, cal.real_day, cal.day_serial))
        h.update(struct.pack("<d", self.gnp_index))
        h.update(struct.pack("<i", len(self.world.towns)))
        for t in self.world.towns:
            h.update(t.name.encode())
            h.update(
                struct.pack(
                    "<iiiddddddi",
                    t.id,
                    t.x,
                    t.y,
                    t.population,
                    t.per_capita_gnp,
                    t.unemployment,
                    t.labor_cost,
                    t.labor_quality,
                    t.consumer_spending,
                    int(t.climate),
                )
            )
        # Sample a few tile heights for map identity
        tiles = self.world.tiles
        step = max(1, len(tiles) // 64)
        for i in range(0, len(tiles), step):
            tile = tiles[i]
            h.update(struct.pack("<BBd", int(tile.kind), tile.climate, tile.height))
        return h.hexdigest()

    def report(self) -> str:
        cal = self.calendar
        lines = [
            "Capitalism++ sim",
            f"  seed:   {self.seed}",
            (
                f"  date:   {cal.year}-{cal.month:02d}-{cal.day:02d}"
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
                f" stagger {t.stagger_slot}"
            )
        return "\n".join(lines) + "\n"


class Game:
    """Top-level session: owns a Sim. Save/load and UI attach here later."""

    def __init__(
        self,
        seed: int = 0,
        *,
        detailed_cities: bool = True,
        target_cities: int = 5,
        start_year: int = 1990,
    ) -> None:
        self.sim = Sim(
            seed=seed,
            detailed_cities=detailed_cities,
            target_cities=target_cities,
            start_year=start_year,
        )

    def advance_days(self, n: int) -> None:
        self.sim.advance_days(n)

    def report(self) -> str:
        return self.sim.report()

    def state_hash(self) -> str:
        return self.sim.state_hash()
