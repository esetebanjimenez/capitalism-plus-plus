"""Headless day-advance sim stub. Real systems land slice by slice in later PRs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Sim:
    """A seeded simulation. Same seed must produce the same run once systems exist."""

    seed: int = 0
    day: int = 0
    month: int = 1
    year: int = 1
    history: list[dict[str, int]] = field(default_factory=list)

    def advance_day(self) -> None:
        """Run one day of the sim. Stub: only advances the calendar."""
        self.day += 1
        if self.day > 30:
            self.day = 1
            self.month += 1
            if self.month > 12:
                self.month = 1
                self.year += 1
        self.history.append({"year": self.year, "month": self.month, "day": self.day})

    def advance_days(self, n: int) -> None:
        if n < 0:
            raise ValueError("n must be >= 0")
        for _ in range(n):
            self.advance_day()

    def report(self) -> str:
        return (
            f"Capitalism++ sim\n"
            f"  seed:  {self.seed}\n"
            f"  date:  Y{self.year} M{self.month} D{self.day}\n"
            f"  days:  {len(self.history)}\n"
        )
