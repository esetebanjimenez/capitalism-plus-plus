"""Load static data tables from the committed capitalism.db into Pydantic models."""

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
    pop_per_tier: float
    pop_tier_noise: int


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
    seed: int = 0
    start_year: int = 1990
    detailed_cities: bool = True
    target_cities: int = Field(default=5, ge=0, le=12)


def db_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "capitalism.db"


@lru_cache(maxsize=1)
def _connect() -> sqlite3.Connection:
    path = db_path()
    if not path.exists():
        raise FileNotFoundError(f"tables database missing: {path}")
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _rows(sql: str, args: tuple = ()) -> list[sqlite3.Row]:
    return list(_connect().execute(sql, args))


def _rule(system: str, key: str) -> float:
    row = (
        _connect()
        .execute(
            "SELECT value FROM rules WHERE system = ? AND key = ?",
            (system, key),
        )
        .fetchone()
    )
    if row is None:
        raise KeyError(f"missing rules[{system}.{key}]")
    return float(row["value"])


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
    return GnpIndexTuning(
        low_growth=_rule("clock", "gnp_index_low_growth"),
        high_growth=_rule("clock", "gnp_index_high_growth"),
        step_chance=_rule("clock", "gnp_index_step_chance"),
        step=_rule("clock", "gnp_index_step"),
        floor=_rule("clock", "gnp_index_floor"),
    )


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
    return ClimateThresholds(
        boom=_rule("towns", "climate_boom"),
        prosperous=_rule("towns", "climate_prosperous"),
        normal=_rule("towns", "climate_normal"),
        recession=_rule("towns", "climate_recession"),
    )


@lru_cache(maxsize=1)
def load_town_growth() -> TownGrowth:
    keys = (
        "pop_growth_lo",
        "pop_growth_hi",
        "rolling_gnp_weight",
        "unemp_weight",
        "unemp_baseline",
        "small_pop",
        "large_pop",
        "gnp_factor_lo",
        "gnp_factor_hi",
        "unemp_lo",
        "unemp_hi",
        "labor_step",
        "gnp_divisor",
        "env_chance",
        "env_lo",
        "env_hi",
        "labor_quality_lo",
        "labor_quality_hi",
        "spend_floor",
        "pop_per_tier",
        "pop_tier_noise",
    )
    return TownGrowth(**{k: _rule("towns", k) for k in keys})


@lru_cache(maxsize=1)
def load_land_value() -> LandValueRules:
    return LandValueRules(
        floor=int(_rule("world", "land_value_floor")),
        bonus_cap=int(_rule("world", "land_value_bonus_cap")),
        base_mult=_rule("world", "land_value_base_mult"),
        small_town_factor=_rule("world", "land_value_small_town_factor"),
        small_town_level_max=int(_rule("world", "land_value_small_town_level_max")),
    )


@lru_cache(maxsize=1)
def load_level_rules() -> LevelRules:
    return LevelRules(
        max_level=int(_rule("towns", "level_max")),
        pop_per_level_sq=int(_rule("towns", "level_pop_per_sq")),
    )


@lru_cache(maxsize=1)
def load_map_rules() -> MapRules:
    return MapRules(
        width=int(_rule("world", "map_width")),
        height=int(_rule("world", "map_height")),
        min_land_fraction=_rule("world", "min_land_fraction"),
        city_border=int(_rule("world", "city_border")),
        city_min_dist=int(_rule("world", "city_min_dist")),
        max_cities=int(_rule("world", "max_cities")),
        default_cities=int(_rule("world", "default_cities")),
        spawn_chance=_rule("world", "spawn_chance"),
        spawn_min_days=int(_rule("world", "spawn_min_days")),
    )


@lru_cache(maxsize=1)
def load_simple_city() -> SimpleCity:
    return SimpleCity(
        level=int(_rule("towns", "simple_level")),
        per_capita_gnp=_rule("towns", "simple_per_capita_gnp"),
        labor_cost=_rule("towns", "simple_labor_cost"),
        spending=_rule("towns", "simple_spending"),
        labor_quality=_rule("towns", "simple_labor_quality"),
        unemployment=_rule("towns", "simple_unemployment"),
    )


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
STAGGER_MOD: int = int(_rule("clock", "stagger_mod"))
