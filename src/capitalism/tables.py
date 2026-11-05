"""Static data tables as Pydantic models (see docs/code-style.md)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CityName(BaseModel):
    name: str
    tier: int = Field(ge=0, le=3)


class TierGnpRange(BaseModel):
    tier: int
    lo: int
    hi: int


class GnpIndexTuning(BaseModel):
    """Provisional GNP index thresholds (design.md slice 1)."""

    low_growth: float = 0.0
    high_growth: float = 0.06
    step_chance: float = 0.10
    step: float = 0.01
    floor: float = 0.5


class SetupOptions(BaseModel):
    """New-game setup options (Pydantic; not hot-path)."""

    seed: int = 0
    start_year: int = 1990
    detailed_cities: bool = True
    target_cities: int = Field(default=5, ge=0, le=12)


# Placeholder pool: 6 names per tier (design.md slice 2).
CITY_NAME_POOL: list[CityName] = [
    CityName(name=n, tier=t)
    for t, names in {
        3: ["Newhaven", "Portsmouth", "Metropole", "Westgate", "Goldcrest", "Harborview"],
        2: ["Riverside", "Oakridge", "Fairview", "Milltown", "Southpoint", "Stonebridge"],
        1: ["Cedar Falls", "Ironwood", "Bayshore", "Hillcrest", "Eastbrook", "Maplewood"],
        0: ["Dustfield", "Redrock", "Pine Hollow", "Northfield", "Greenfield", "Ashvale"],
    }.items()
    for n in names
]

TIER_GNP: dict[int, TierGnpRange] = {
    t: TierGnpRange(tier=t, lo=lo, hi=hi)
    for t, (lo, hi) in {
        0: (200, 2000),
        1: (2200, 7000),
        2: (7200, 14000),
        3: (14200, 20000),
    }.items()
}

GNP_INDEX = GnpIndexTuning()

CLIMATE_SPEND = {
    4: 1.10,  # Boom
    3: 1.05,  # Prosperous
    2: 1.00,  # Normal
    1: 0.95,  # Recession
    0: 0.90,  # Panic
}

# (drift, swing) percentage points — design.md unemployment table
UNEMPLOYMENT_DRIFT = {
    4: (-0.15, 0.30),
    3: (-0.10, 0.20),
    2: (0.0, 0.10),
    1: (0.10, 0.20),
    0: (0.15, 0.30),
}
