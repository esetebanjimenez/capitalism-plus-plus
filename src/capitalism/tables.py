"""Load static data tables from the shipped SQLite DB into Pydantic models."""

from __future__ import annotations

import sqlite3
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


class CityName(BaseModel):
    name: str
    tier: int = Field(ge=0, le=3)


class TierGnpRange(BaseModel):
    tier: int
    lo: int
    hi: int


class GnpIndexTuning(BaseModel):
    low_growth: float
    high_growth: float
    step_chance: float
    step: float
    floor: float


class ClimateSpend(BaseModel):
    climate: int
    factor: float


class UnemploymentDrift(BaseModel):
    climate: int
    drift: float
    swing: float


class ClimateThresholds(BaseModel):
    boom: float
    prosperous: float
    normal: float
    recession: float


class TownGrowth(BaseModel):
    pop_growth_lo: float
    pop_growth_hi: float
    rolling_gnp_weight: float
    unemp_weight: float
    unemp_baseline: float
    small_pop: float
    large_pop: float
    gnp_factor_lo: float
    gnp_factor_hi: float
    unemp_lo: float
    unemp_hi: float
    labor_step: float
    gnp_divisor: float
    env_chance: float
    env_lo: float
    env_hi: float
    labor_quality_lo: float
    labor_quality_hi: float
    spend_floor: float


class LandValueRules(BaseModel):
    floor: int
    bonus_cap: int
    base_mult: float
    small_town_factor: float
    small_town_level_max: int


class LevelRules(BaseModel):
    max_level: int
    pop_per_level_sq: int


class MapRules(BaseModel):
    width: int
    height: int
    min_land_fraction: float
    city_border: int
    city_min_dist: int
    max_cities: int
    default_cities: int
    spawn_chance: float
    spawn_min_days: int


class SimpleCity(BaseModel):
    level: int
    per_capita_gnp: float
    labor_cost: float
    spending: float
    labor_quality: float
    unemployment: float


class SetupOptions(BaseModel):
    """New-game setup options (Pydantic; not hot-path)."""

    seed: int = 0
    start_year: int = 1990
    detailed_cities: bool = True
    target_cities: int = Field(default=5, ge=0, le=12)


def _db_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "tables.sqlite"


@lru_cache(maxsize=1)
def _connect() -> sqlite3.Connection:
    path = _db_path()
    if not path.exists():
        raise FileNotFoundError(f"tables database missing: {path}")
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _rows(sql: str) -> list[sqlite3.Row]:
    return list(_connect().execute(sql))


def _one(sql: str) -> sqlite3.Row:
    row = _connect().execute(sql).fetchone()
    if row is None:
        raise RuntimeError(f"expected a row for: {sql}")
    return row


@lru_cache(maxsize=1)
def load_city_names() -> tuple[CityName, ...]:
    return tuple(
        CityName(name=r["name"], tier=r["tier"])
        for r in _rows("SELECT name, tier FROM city_names ORDER BY tier DESC, name")
    )


@lru_cache(maxsize=1)
def load_tier_gnp() -> dict[int, TierGnpRange]:
    return {
        int(r["tier"]): TierGnpRange(tier=r["tier"], lo=r["lo"], hi=r["hi"])
        for r in _rows("SELECT tier, lo, hi FROM tier_gnp")
    }


@lru_cache(maxsize=1)
def load_gnp_index() -> GnpIndexTuning:
    r = _one("SELECT low_growth, high_growth, step_chance, step, floor FROM gnp_index WHERE id = 1")
    return GnpIndexTuning(**dict(r))


@lru_cache(maxsize=1)
def load_climate_spend() -> dict[int, float]:
    return {
        int(r["climate"]): float(r["factor"])
        for r in _rows("SELECT climate, factor FROM climate_spend")
    }


@lru_cache(maxsize=1)
def load_unemployment_drift() -> dict[int, tuple[float, float]]:
    return {
        int(r["climate"]): (float(r["drift"]), float(r["swing"]))
        for r in _rows("SELECT climate, drift, swing FROM unemployment_drift")
    }


@lru_cache(maxsize=1)
def load_climate_thresholds() -> ClimateThresholds:
    r = _one("SELECT boom, prosperous, normal, recession FROM climate_thresholds WHERE id = 1")
    return ClimateThresholds(**dict(r))


@lru_cache(maxsize=1)
def load_town_growth() -> TownGrowth:
    r = _one("SELECT * FROM town_growth WHERE id = 1")
    data = {k: v for k, v in dict(r).items() if k != "id"}
    return TownGrowth(**data)


@lru_cache(maxsize=1)
def load_land_value() -> LandValueRules:
    r = _one(
        "SELECT floor, bonus_cap, base_mult, small_town_factor, small_town_level_max FROM land_value WHERE id = 1"
    )
    return LandValueRules(**dict(r))


@lru_cache(maxsize=1)
def load_level_rules() -> LevelRules:
    r = _one("SELECT max_level, pop_per_level_sq FROM level_rules WHERE id = 1")
    return LevelRules(**dict(r))


@lru_cache(maxsize=1)
def load_map_rules() -> MapRules:
    r = _one(
        "SELECT width, height, min_land_fraction, city_border, city_min_dist, "
        "max_cities, default_cities, spawn_chance, spawn_min_days FROM map_rules WHERE id = 1"
    )
    return MapRules(**dict(r))


@lru_cache(maxsize=1)
def load_simple_city() -> SimpleCity:
    r = _one(
        "SELECT level, per_capita_gnp, labor_cost, spending, labor_quality, unemployment "
        "FROM simple_city WHERE id = 1"
    )
    return SimpleCity(**dict(r))


# Eager module-level aliases used by the sim (loaded once from SQLite).
CITY_NAME_POOL: list[CityName] = list(load_city_names())
TIER_GNP: dict[int, TierGnpRange] = load_tier_gnp()
GNP_INDEX: GnpIndexTuning = load_gnp_index()
CLIMATE_SPEND: dict[int, float] = load_climate_spend()
UNEMPLOYMENT_DRIFT: dict[int, tuple[float, float]] = load_unemployment_drift()
CLIMATE_THRESHOLDS: ClimateThresholds = load_climate_thresholds()
TOWN_GROWTH: TownGrowth = load_town_growth()
LAND_VALUE: LandValueRules = load_land_value()
LEVEL_RULES: LevelRules = load_level_rules()
MAP_RULES: MapRules = load_map_rules()
SIMPLE_CITY: SimpleCity = load_simple_city()
