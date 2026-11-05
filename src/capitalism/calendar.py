"""Gregorian calendar with day-of-month display clamped at 30 (design.md)."""

from __future__ import annotations

from datetime import date, timedelta

EPOCH = date(1900, 1, 1)
DEFAULT_START = date(1990, 1, 1)

_REAL_MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def real_days_in_month(year: int, month: int) -> int:
    """Real calendar length for salary/overhead. Month is 1-12."""
    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return 29 if leap else 28
    return _REAL_MONTH_DAYS[month - 1]


def day_serial_of(d: date) -> int:
    """Absolute day count from 1 January 1900."""
    return (d - EPOCH).days


class Calendar:
    """Real Gregorian advance; displayed day is min(real_day, 30)."""

    def __init__(self, start: date = DEFAULT_START) -> None:
        self._date = start
        self.years_elapsed = 0
        self._start_year = start.year

    @property
    def year(self) -> int:
        return self._date.year

    @property
    def month(self) -> int:
        return self._date.month

    @property
    def day(self) -> int:
        """Day-of-month, clamped at 30."""
        return min(self._date.day, 30)

    @property
    def real_day(self) -> int:
        return self._date.day

    @property
    def day_serial(self) -> int:
        return day_serial_of(self._date)

    @property
    def weekday(self) -> int:
        return self.day_serial % 7

    @property
    def real_month_days(self) -> int:
        return real_days_in_month(self.year, self.month)

    def advance(self) -> tuple[bool, bool]:
        """Advance one real calendar day. Returns (month_rolled, year_rolled)."""
        prev = self._date
        self._date = prev + timedelta(days=1)
        month_rolled = self._date.month != prev.month
        year_rolled = self._date.year != prev.year
        if year_rolled:
            self.years_elapsed = self._date.year - self._start_year
        return month_rolled, year_rolled
