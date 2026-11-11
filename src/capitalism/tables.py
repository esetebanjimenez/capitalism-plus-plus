"""Load static data tables from the committed capitalism.db into Pydantic models."""

from __future__ import annotations

import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field


class StaticModel(BaseModel):
    """Static db content shared by every Sim: frozen, so runtime state lives elsewhere."""

    model_config = ConfigDict(frozen=True)


class CityName(StaticModel):
    name: str
    tier: int = Field(ge=0, le=3)


class TierGnpRange(StaticModel):
    tier: int
    lo: int
    hi: int


class GnpIndexTuning(StaticModel):
    low_growth: float
    high_growth: float
    step_chance: float
    step: float
    floor: float


class ClimateThresholds(StaticModel):
    boom: float
    prosperous: float
    normal: float
    recession: float
    panic: float


class TownGrowth(StaticModel):
    pop_random_range: int
    pop_base_offset: float
    pop_gnp_scale: float
    gnp_growth_scale: float
    pop_unemp_target: float
    pop_unemp_scale: float
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


class LandValueRules(StaticModel):
    floor: int
    bonus_cap: int
    base_mult: float
    small_town_factor: float
    small_town_level_max: int


class LevelRules(StaticModel):
    max_level: int
    pop_per_level_sq: int


class MapRules(StaticModel):
    width: int
    height: int
    min_land_fraction: float
    city_border: int
    city_min_dist: int
    max_cities: int
    default_cities: int
    spawn_chance: float
    spawn_min_days: int


class SimpleCity(StaticModel):
    level: int
    per_capita_gnp: float
    labor_cost: float
    spending: float
    labor_quality: float
    unemployment: float


# --- Slice 3: product catalog -------------------------------------------------


def _prov_cols(raw: str) -> frozenset[str]:
    return frozenset(c for c in raw.split(",") if c)


class ProductClassRow(StaticModel):
    id: int
    code: str
    name: str
    durable: bool
    quality_decay_base: float = Field(gt=0, le=1)
    group_flags: int
    ref: str
    provisional: frozenset[str] = frozenset()


class ProductRow(StaticModel):
    id: int
    code: str
    name: str
    class_id: int
    kind: str
    unit: str
    base_price: float = Field(gt=0)
    base_cost: float = Field(ge=0)
    freight: float = Field(ge=0)
    spending_usd: float = Field(gt=0)
    demand_per_1000: float = Field(ge=0)
    luxury: int = Field(ge=0, le=9)
    necessity: int = Field(ge=0, le=9)
    tech_importance: int
    w_price: int
    w_quality: int
    w_brand: int
    base_tech_level: int = Field(ge=0)
    tech_year: int = Field(ge=0, le=100)
    base_capacity: float = Field(ge=1)
    plant_month: int | None = None
    grow_months: int | None = None
    suit_climate: int | None = None
    suit_moisture: int | None = None
    importable: bool
    ref: str
    provisional: frozenset[str] = frozenset()

    @property
    def is_consumer(self) -> bool:
        return self.demand_per_1000 > 0


class RecipeInputRow(StaticModel):
    input_id: int
    qty: int = Field(ge=1)
    quality_weight: int = Field(ge=0, lt=100)


class RecipeRow(StaticModel):
    """One manufacturing recipe (docs/recipes.md, reference data)."""

    product_id: int
    output_qty: int = Field(ge=1)
    speed_pct: int
    ref: str
    inputs: tuple[RecipeInputRow, ...]

    @property
    def input_weight(self) -> int:
        return sum(i.quality_weight for i in self.inputs)

    @property
    def skill_weight(self) -> int:
        """Manufacturing skill share of output quality: the rest of 100."""
        return 100 - self.input_weight


class RndPrereqRow(StaticModel):
    product_id: int
    requires_id: int
    ref: str


class ProductRules(StaticModel):
    nec_lux_base: float
    nec_lux_necessity: float
    nec_lux_luxury: float
    nec_lux_lo: float
    nec_lux_hi: float
    obsolete_demand_factor: float
    gnp_pc_ref: float
    demand_per_people: float
    tech_jitter: int
    score_jitter: int
    score_no_links: float
    diffusion_corp_weight: float
    diffusion_threshold: float
    capacity_value_per_day: float


# --- Slice 4: firms and jobs ----------------------------------------------------


class FirmTypeRow(StaticModel):
    id: int
    name: str
    setup_cost: float
    overhead_month: float
    max_slots: int = Field(ge=0, le=9)
    live_inventory: bool
    government: bool
    ref: str
    provisional: frozenset[str] = frozenset()


class CompetitorCapitalRow(StaticModel):
    """AI starting-capital factor v per Competitor Capital setting (FUN_0007916c)."""

    setting: int = Field(ge=0)
    name: str
    v: int = Field(gt=0)
    ref: str
    provisional: frozenset[str] = frozenset()


class TownFootprintRow(StaticModel):
    """Visual town footprint per town level (client map only; the sim town stays one tile)."""

    level: int = Field(ge=1)
    radius: int = Field(ge=0)
    block_level: int = Field(ge=0, le=2)
    ref: str
    provisional: frozenset[str] = frozenset()


class FirmSectorRow(StaticModel):
    """Sector of a firm type for sector dominance goals (native mapping; names provisional)."""

    firm_type: int
    sector: int = Field(ge=0, le=3)
    sector_name: str
    ref: str
    provisional: frozenset[str] = frozenset()


class RatingThroughputRow(StaticModel):
    rating: int = Field(ge=1, le=9)
    efficiency_pct: float = Field(gt=0)
    storage_mult: float = Field(gt=0)
    ref: str


class FixedTrainingCreditRow(StaticModel):
    job_type: int
    base_daily: float = Field(gt=0)
    ref: str
    provisional: bool = False


class JobTypeRow(StaticModel):
    id: int
    name: str
    staff: int = Field(ge=0)
    setup_cost: float
    training_factor: float
    cap_mult: float = Field(gt=0)
    counts_as_produced: bool
    ref: str
    provisional: frozenset[str] = frozenset()


class FirmRules(StaticModel):
    slots: int
    link_bits: int
    size: int
    media_staff: int
    media_wage_mult: float


class JobRules(StaticModel):
    sales_mult_store: float
    sales_mult_other: float
    purchase_every_days: int
    purchase_order_mult: float
    train_weekday: int
    training_credit_budget_divisor: float = Field(gt=0)
    training_credit_education: float = Field(ge=0)
    training_credit_education_divisor: float = Field(gt=0)
    rating_min: int
    rating_max: int
    livestock_scalar: float
    wage_per_worker_month: int
    ad_budget_min: float
    ad_budget_max: float
    crop_climate_slope: float
    crop_moisture_slope: float
    crop_yield_base: float
    crop_soil_div: float
    crop_moisture_step: float
    extraction_rate: float
    mfg_skill_max: float
    freight_distance_value_divisor: float = Field(gt=0)
    freight_multiplier: float = Field(gt=0)
    freight_floor_usd_per_unit: float = Field(gt=0)
    training_expense_divisor: float = Field(gt=0)
    corp_training_budget_default: float = Field(ge=0)
    import_quality: float
    quality_base: float
    quality_per_rating: float


# --- Slice 5: links and markets -------------------------------------------------


class LinkRules(StaticModel):
    price_base: float
    price_slope: float
    score_div: float
    oversupply_div: float
    share_exponent: float
    ad_brand_per_100k: float
    weight_nonfarm: float
    weight_rate_mult: float
    weight_max: float
    brand_nudge: float
    brand_max: float
    brand_start: float


class SetupOptions(BaseModel):
    seed: int = 0
    start_year: int = 1990
    detailed_cities: bool = True
    target_cities: int = Field(default=5, ge=0, le=12)
    event_frequency: int = Field(default=0, ge=0, le=3)
    year_limit: int = Field(default=0, ge=0)
    goal_score_bonus: int = Field(default=0, ge=0, le=500)
    competitors: int = Field(default=3, ge=0, le=10)
    competitor_capital: int = Field(default=0, ge=0, le=4)
    # None: corporations.player_initial_capital from the DB.
    initial_capital: float | None = Field(default=None, ge=0)
    competence_level: int = Field(default=0, ge=0, le=5)
    expertise_level: int = Field(default=0, ge=0, le=5)
    show_trade_secrets: bool = True
    competitor_character: int = Field(default=-1, ge=-1, le=6)
    consumer_seaports: int = Field(default=2, ge=0)
    industrial_seaports: int = Field(default=2, ge=0)
    constant_supply: bool = True
    import_quality: int = Field(default=3, ge=0, le=3)
    is_scenario: bool = False
    cheated: bool = False


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
        panic=_rule("towns", "climate_panic"),
    )


@lru_cache(maxsize=1)
def load_town_growth() -> TownGrowth:
    keys = (
        "pop_random_range",
        "pop_base_offset",
        "pop_gnp_scale",
        "gnp_growth_scale",
        "pop_unemp_target",
        "pop_unemp_scale",
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


M = TypeVar("M", bound=BaseModel)


def _rules_model(model: type[M], system: str) -> M:
    """Build a rules model from every `rules` row of `system` named by its fields."""
    return model(**{k: _rule(system, k) for k in model.model_fields})


@lru_cache(maxsize=1)
def load_product_classes() -> dict[int, ProductClassRow]:
    out: dict[int, ProductClassRow] = {}
    for r in _rows("SELECT * FROM product_classes ORDER BY id"):
        d = dict(r)
        d["provisional"] = _prov_cols(d["provisional"])
        out[d["id"]] = ProductClassRow(**d)
    return out


@lru_cache(maxsize=1)
def load_products() -> tuple[ProductRow, ...]:
    rows = []
    for r in _rows("SELECT * FROM products ORDER BY id"):
        d = dict(r)
        d["provisional"] = _prov_cols(d["provisional"])
        rows.append(ProductRow(**d))
    return tuple(rows)


@lru_cache(maxsize=1)
def load_recipes() -> dict[int, RecipeRow]:
    inputs: dict[int, list[RecipeInputRow]] = {}
    for r in _rows(
        "SELECT product_id, input_id, qty, quality_weight FROM recipe_inputs "
        "ORDER BY product_id, input_id"
    ):
        d = dict(r)
        inputs.setdefault(d.pop("product_id"), []).append(RecipeInputRow(**d))
    return {
        int(r["product_id"]): RecipeRow(
            product_id=r["product_id"],
            output_qty=r["output_qty"],
            speed_pct=r["speed_pct"],
            ref=r["ref"],
            inputs=tuple(inputs.get(int(r["product_id"]), ())),
        )
        for r in _rows("SELECT product_id, output_qty, speed_pct, ref FROM recipes ORDER BY 1")
    }


@lru_cache(maxsize=1)
def load_rnd_prereqs() -> tuple[RndPrereqRow, ...]:
    return tuple(
        RndPrereqRow(**dict(r))
        for r in _rows("SELECT product_id, requires_id, ref FROM rnd_prereqs ORDER BY 1, 2")
    )


@lru_cache(maxsize=1)
def load_firm_types() -> dict[int, FirmTypeRow]:
    out: dict[int, FirmTypeRow] = {}
    for r in _rows(
        "SELECT id, name, setup_cost, overhead_month, max_slots, live_inventory, government, ref, provisional "
        "FROM firm_types ORDER BY id"
    ):
        d = dict(r)
        d["provisional"] = _prov_cols(d["provisional"])
        out[d["id"]] = FirmTypeRow(**d)
    return out


@lru_cache(maxsize=1)
def load_town_footprints() -> dict[int, TownFootprintRow]:
    out: dict[int, TownFootprintRow] = {}
    for r in _rows(
        "SELECT level, radius, block_level, ref, provisional FROM town_footprints ORDER BY level"
    ):
        d = dict(r)
        d["provisional"] = _prov_cols(d["provisional"])
        out[d["level"]] = TownFootprintRow(**d)
    return out


@lru_cache(maxsize=1)
def load_competitor_capital() -> dict[int, CompetitorCapitalRow]:
    out: dict[int, CompetitorCapitalRow] = {}
    for r in _rows(
        "SELECT setting, name, v, ref, provisional FROM competitor_capital ORDER BY setting"
    ):
        d = dict(r)
        d["provisional"] = _prov_cols(d["provisional"])
        out[d["setting"]] = CompetitorCapitalRow(**d)
    return out


@lru_cache(maxsize=1)
def load_firm_sectors() -> dict[int, FirmSectorRow]:
    out: dict[int, FirmSectorRow] = {}
    for r in _rows(
        "SELECT firm_type, sector, sector_name, ref, provisional FROM firm_sectors ORDER BY firm_type"
    ):
        d = dict(r)
        d["provisional"] = _prov_cols(d["provisional"])
        out[d["firm_type"]] = FirmSectorRow(**d)
    return out


@lru_cache(maxsize=1)
def load_job_types() -> dict[int, JobTypeRow]:
    out: dict[int, JobTypeRow] = {}
    for r in _rows(
        "SELECT id, name, staff, setup_cost, training_factor, cap_mult, counts_as_produced, ref, "
        "provisional "
        "FROM job_types ORDER BY id"
    ):
        d = dict(r)
        d["provisional"] = _prov_cols(d["provisional"])
        out[d["id"]] = JobTypeRow(**d)
    return out


@lru_cache(maxsize=1)
def load_firm_job_allowed() -> dict[int, frozenset[int]]:
    out: dict[int, set[int]] = {}
    for r in _rows("SELECT firm_type, job_type FROM firm_job_allowed ORDER BY firm_type, job_type"):
        out.setdefault(int(r["firm_type"]), set()).add(int(r["job_type"]))
    return {k: frozenset(v) for k, v in out.items()}


@lru_cache(maxsize=1)
def load_rating_throughput() -> dict[int, RatingThroughputRow]:
    return {
        int(r["rating"]): RatingThroughputRow(**dict(r))
        for r in _rows(
            "SELECT rating, efficiency_pct, storage_mult, ref "
            "FROM rating_throughput ORDER BY rating"
        )
    }


@lru_cache(maxsize=1)
def load_fixed_training_credits() -> dict[int, FixedTrainingCreditRow]:
    return {
        int(r["job_type"]): FixedTrainingCreditRow(
            job_type=int(r["job_type"]),
            base_daily=float(r["base_daily"]),
            ref=r["ref"],
            provisional=bool(r["provisional"]),
        )
        for r in _rows(
            "SELECT job_type, base_daily, ref, provisional "
            "FROM fixed_training_credits ORDER BY job_type"
        )
    }


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
PRODUCT_RULES: ProductRules = _rules_model(ProductRules, "products")
FIRM_RULES: FirmRules = _rules_model(FirmRules, "firms")
JOB_RULES: JobRules = _rules_model(JobRules, "jobs")
LINK_RULES: LinkRules = _rules_model(LinkRules, "links")
PRODUCT_CLASSES: dict[int, ProductClassRow] = load_product_classes()
FIRM_TYPES: dict[int, FirmTypeRow] = load_firm_types()
FIRM_SECTORS: dict[int, FirmSectorRow] = load_firm_sectors()
TOWN_FOOTPRINTS: dict[int, TownFootprintRow] = load_town_footprints()
COMPETITOR_CAPITAL: dict[int, CompetitorCapitalRow] = load_competitor_capital()
JOB_TYPES: dict[int, JobTypeRow] = load_job_types()
FIRM_JOB_ALLOWED: dict[int, frozenset[int]] = load_firm_job_allowed()
RATING_THROUGHPUT: dict[int, RatingThroughputRow] = load_rating_throughput()
FIXED_TRAINING_CREDITS: dict[int, FixedTrainingCreditRow] = load_fixed_training_credits()


class LivestockYieldRow(StaticModel):
    livestock_id: int
    product_id: int
    yield_factor: float = Field(gt=0)
    input_ratio: float = Field(gt=0)
    ref: str


class ResearchRules(StaticModel):
    days_per_project_month: int
    manager_skill_divisor: float
    max_technology: int
    tech_year_divisor: int


class AdvertisingRules(StaticModel):
    ad_revenue_fraction: float
    ad_campaign_every_days: int
    ad_tech_min_exclusive: int
    media_min_revenue: float
    media_min_audience: float
    media_audience_min: float
    media_government_max: int
    media_audience_population_div: float
    media_audience_cap: float
    media_audience_adjust_rate: float
    # Binary FUN_000604d2: reputation-driven audience model
    media_reputation_drift_range: int
    media_reputation_drift_offset: int
    media_low_audience_threshold: float
    media_high_audience_threshold: float
    media_reputation_boost_range: int
    media_reputation_min: float
    media_reputation_max: float
    media_audience_delta_range: int
    media_audience_delta_offset: float
    media_audience_delta_divisor: float
    media_competition_steal_factor: float
    media_market_cap: float
    # Binary FUN_0006073c: organic media revenue
    media_revenue_town_divisor: float
    media_revenue_audience_addend: float
    media_revenue_base_divisor: float
    media_revenue_floor: float
    media_revenue_seasonal_neutral: float


class SoftwareRules(StaticModel):
    software_project_months: int
    software_copy_quality: float
    software_copy_cost_per_day: float
    # Binary FUN_0005c06f: production gate
    software_gate_every_days: int
    software_gate_max_age_days: int
    software_gate_no_revenue_months: int


class PersonRules(StaticModel):
    max_persons: int
    spawn_chance: float
    spawn_first_day_gate: float
    dormant_year_threshold: int
    dormant_chance: float
    skill_level_step: float
    skill_range: float
    raise_penalty_min: int
    raise_penalty_max: int
    loyalty_base: float
    raise_wealth_ratio: float
    service_salary_factor: float
    random_raise_base: float
    max_competitors: int
    wealth_floor: float


class AIRules(StaticModel):
    strategy_interval: int
    link_interval: int
    finance_interval: int
    survey_interval: int
    vertical_interval: int
    mode_transition_interval: int
    build_cooldown: int
    ai_cash_reset: float
    spawn_chance: float
    spawn_first_day_gate: float
    dormant_year_threshold: float
    dormant_chance: float
    competitor_cap: int
    max_competitors: int
    capital_unit: float
    loan_minimum: float
    random_build_chance: float
    bankruptcy_age_threshold: float
    bankruptcy_value_threshold: float


class NewsRules(StaticModel):
    buffer_capacity: int


class EventRules(StaticModel):
    freq_low_denominator: int
    freq_medium_denominator: int
    freq_high_denominator: int
    event_type_count: int
    disease_divisor_lo: int
    disease_divisor_hi: int
    destruction_gate: float
    breakthrough_progress_lo: int
    breakthrough_progress_hi: int
    blackout_gate: float
    blackout_max_loss: int
    downturn_gate: float
    downturn_loss_lo: float
    downturn_loss_hi: float


class StockRules(StaticModel):
    initial_price_per_share: float
    momentum_up_step: float
    momentum_down_step: float
    momentum_clamp: float
    spike_chance: float
    spike_magnitude: float
    dilution_decay_rate: float
    volume_decay_rate: float
    impact_factor: float
    volume_trade_factor: float
    dilution_issue_factor: float
    issuance_momentum_factor: float
    dividend_min_payout: float
    dividend_max_ratio: float
    buyback_float_threshold: float
    buyback_fraction: float
    invest_max_fraction: float


class ScoringRules(StaticModel):
    difficulty_capital_mult: int
    difficulty_base_offset: int
    difficulty_secrets_penalty: int
    difficulty_char_mixed_penalty: int
    difficulty_char_per_type: int
    difficulty_expertise_vlow: int
    difficulty_expertise_per_level: int
    difficulty_no_seaports: int
    difficulty_competence_per_level: int
    difficulty_events_per_level: int
    difficulty_scale_numerator: int
    difficulty_scale_denominator: int
    wealth_per_billion: int
    corpworth_per_billion: int
    sector_points: int
    product_points: int
    year_penalty_threshold: int
    free_goal_multiplier: int
    player_goal_check_interval: int
    ai_goal_check_interval: int
    warning_years_threshold: int
    goal_bonus_max: int
    dominance_tie_lowest_slot: int = Field(ge=0, le=1)
    sector_share_window_months: int = Field(ge=1, le=1)
    product_goals_count_own_output: int = Field(ge=1, le=1)


class CorporationRules(StaticModel):
    interest_rate_default: float
    interest_rate_floor: float
    interest_rate_step: float
    overdraft_spread: float
    weak_gnp_threshold: float
    player_initial_capital: float
    interest_rise_chance: float
    interest_fall_chance: float


@lru_cache(maxsize=1)
def load_livestock_yields() -> dict[int, LivestockYieldRow]:
    rows = _rows(
        "SELECT livestock_id, product_id, yield_factor, input_ratio, ref FROM livestock_yields"
    )
    return {int(r["livestock_id"]): LivestockYieldRow(**dict(r)) for r in rows}


@lru_cache(maxsize=1)
def load_research_durations() -> tuple[int, ...]:
    return tuple(
        int(r["months"])
        for r in _rows("SELECT months FROM research_durations ORDER BY tech_year_bucket")
    )


LIVESTOCK_YIELDS = load_livestock_yields()
RESEARCH_DURATIONS = load_research_durations()
RESEARCH_RULES = _rules_model(ResearchRules, "research")
ADVERTISING_RULES = _rules_model(AdvertisingRules, "advertising")
SOFTWARE_RULES = _rules_model(SoftwareRules, "software")
PERSON_RULES = _rules_model(PersonRules, "persons")
AI_RULES = _rules_model(AIRules, "ai")
STOCK_RULES = _rules_model(StockRules, "stock")
CORPORATION_RULES = _rules_model(CorporationRules, "corporations")
NEWS_RULES = _rules_model(NewsRules, "news")
EVENT_RULES = _rules_model(EventRules, "events")
SCORING_RULES = _rules_model(ScoringRules, "scoring")
