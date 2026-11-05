"""Game calendar: 30-day months for the clock; real month lengths for salary/overhead."""

from __future__ import annotations

from pydantic import BaseModel, Field

_REAL_MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def real_days_in_month(year: int, month: int) -> int:
    """Real calendar length for salary/overhead. Month is 1-12."""
    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return 29 if leap else 28
    return _REAL_MONTH_DAYS[month - 1]


class Calendar(BaseModel):
    """Day-of-month is clamped at 30. day_serial counts days since game start (0-based)."""

    model_config = {"validate_assignment": True}

    year: int = 1
    month: int = Field(default=1, ge=1, le=12)
    day: int = Field(default=1, ge=1)
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
        if self.day >= 30:
            self.day = 1
            next_month = self.month + 1
            month_rolled = True
            if next_month > 12:
                self.month = 1
                self.year += 1
                self.years_elapsed += 1
                year_rolled = True
            else:
                self.month = next_month
        else:
            self.day += 1
        return month_rolled, year_rolled
