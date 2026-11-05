"""Back-compat: city name pool now lives in tables.py as Pydantic models."""

from __future__ import annotations

from .tables import CITY_NAME_POOL

CITY_NAMES: list[tuple[str, int]] = [(c.name, c.tier) for c in CITY_NAME_POOL]
