"""Game calendar: 30-day months for the clock; real month lengths for salary/overhead."""

from __future__ import annotations

from dataclasses import dataclass

# Real calendar lengths used for salary and overhead (gamelogic.md: Time and the game clock).
# February uses 28; leap years use 29 when year % 4 == 0 (and not century unless % 400).
_REAL_MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def real_days_in_month(year: int, month: int) -> int:
    """Real calendar length for salary/overhead. Month is 1-12."""
    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return 29 if leap else 28
    return _REAL_MONTH_DAYS[month - 1]


@dataclass
class Calendar:
    """Day-of-month is clamped at 30. day_serial counts days since game start (0-based)."""

    year: int = 1
    month: int = 1
    day: int = 1
    day_serial: int = 0
    years_elapsed: int = 0

    @property
    def weekday(self) -> int:
        return self.day_serial % 7

    @property
    def real_month_days(self) -> int:
        return real_days_in_month(self.year, self.month)

    def advance(self) -> tuple[bool, bool]:
        """Advance one game day. Returns (month_rolled, year_rolled)."""
        self.day_serial += 1
        month_rolled = False
        year_rolled = False
        self.day += 1
        if self.day > 30:
            self.day = 1
            self.month += 1
            month_rolled = True
            if self.month > 12:
                self.month = 1
                self.year += 1
                self.years_elapsed += 1
                year_rolled = True
        return month_rolled, year_rolled
