"""AI corporation strategy: decision engine, spawning, expansion (gamelogic.md AI corporation strategy)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .person import (
    CHAR_CONSERVATIVE,
    CHAR_VERY_AGGRESSIVE,
    ROLE_INDEPENDENT,
    STATE_ACTIVE,
)
from .tables import AI_RULES, COMPETITOR_CAPITAL, FIRM_TYPES

if TYPE_CHECKING:
    from .economy import Corporation, Economy
    from .person import Person
    from .rng import Rng
    from .town import Town

_AR = AI_RULES

# Strategy modes
MODE_ESTABLISH = 0
MODE_MANUFACTURE = 1
MODE_RETAIL = 2
MODE_DORMANT = 3

# Profitability thresholds by character type (gamelogic.md Profitability gating)
PROFITABILITY_THRESHOLDS = (0.80, 0.60, 0.45, 0.30)

# Dominance check intervals by character type (gamelogic.md Market dominance)
DOMINANCE_INTERVALS = (160, 120, 80, 40)


class AIState:
    """Per-corporation AI decision state."""

    __slots__ = (
        "build_cooldowns",
        "corp_id",
        "dormant_start_day",
        "expansion_intensity",
        "last_annual_day",
        "last_dominance_day",
        "last_finance_day",
        "last_link_day",
        "last_mode_day",
        "last_strategy_day",
        "last_survey_day",
        "last_vertical_day",
        "mode",
        "mode_start_day",
        "pending_build",
        "schedule_offset",
    )

    def __init__(self, corp_id: int, day_serial: int, rng: Rng) -> None:
        self.corp_id = corp_id
        self.mode = MODE_ESTABLISH
        self.mode_start_day = day_serial
        self.schedule_offset = rng.randint(0, 14)
        self.dormant_start_day = 0
        self.expansion_intensity = 0
        self.pending_build: int | None = None
        self.build_cooldowns: dict[int, int] = {}
        # Decision timers
        self.last_strategy_day = day_serial
        self.last_link_day = day_serial
        self.last_finance_day = day_serial
        self.last_survey_day = day_serial
        self.last_vertical_day = day_serial
        self.last_dominance_day = day_serial
        self.last_mode_day = day_serial
        self.last_annual_day = day_serial


def _owned_firms(eco: Economy, corp: Corporation) -> list:
    return [f for f in eco.firms if f is not None and f.owner is corp]


def _profitable_ratio(eco: Economy, corp: Corporation, firm_type: int) -> float:
    """Fraction of owned firms of this type that were profitable last month."""
    firms = [f for f in _owned_firms(eco, corp) if f.type_id == firm_type]
    if not firms:
        return 1.0
    profitable = sum(1 for f in firms if f.ledger.last_month[0] > 0)
    return profitable / len(firms)


def passes_profitability_gate(
    eco: Economy, corp: Corporation, firm_type: int, ceo: Person | None
) -> bool:
    """Check whether the AI should build more of this firm type (gamelogic.md Profitability gating)."""
    owned = [f for f in _owned_firms(eco, corp) if f.type_id == firm_type]
    if not owned:
        return True
    char_type = ceo.character_type if ceo else CHAR_CONSERVATIVE
    threshold = PROFITABILITY_THRESHOLDS[min(char_type, CHAR_VERY_AGGRESSIVE)]
    return _profitable_ratio(eco, corp, firm_type) >= threshold


def find_ai_site(
    eco: Economy, town: Town, rng: Rng, *, rural: bool = False, max_retries: int = 20
) -> tuple[int, int] | None:
    """AI location selection (gamelogic.md Location selection)."""
    from .world import TileCategory

    cx, cy = town.x, town.y
    base_radius = town.level + (0 if rural else 4)
    radius = min(base_radius, 4)

    for attempt in range(max_retries):
        r = radius + attempt
        dx = rng.randint(-r, r)
        dy = rng.randint(-r, r)
        x = max(0, min(eco.world.width - 1, cx + dx))
        y = max(0, min(eco.world.height - 1, cy + dy))
        tile = eco.world.tile_at(x, y)
        if rural:
            if tile.kind in (TileCategory.GRASSLAND, TileCategory.FOREST_HILL):
                return x, y
        else:
            if tile.kind not in (
                TileCategory.TOWN,
                TileCategory.FIRM,
                TileCategory.WATER,
                TileCategory.DEEP_OCEAN,
            ):
                return x, y
    return None


def ai_build_firm(
    eco: Economy, corp: Corporation, firm_type: int, town: Town, rng: Rng, *, rural: bool = False
) -> object | None:
    """Shared AI build path (gamelogic.md Firm creation)."""
    site = find_ai_site(eco, town, rng, rural=rural)
    if site is None:
        return None
    x, y = site
    land_value = eco.world.land_value(x, y)
    # FUN_0002e19a (decomp:25264-25281): cash vs land value + the type's setup cost.
    # Native then tries asset sales (FUN_00030ae2) before refusing; with the $1B
    # daily reset (A1) that branch rarely runs, so the sim just refuses.
    if corp.ledger.cash < land_value + FIRM_TYPES[firm_type].setup_cost:
        return None
    try:
        return eco.build_firm(firm_type, corp, x, y, town)
    except (ValueError, NotImplementedError):
        return None


# --- NPC spawning -----------------------------------------------------------

def ai_starting_capital(setting: int, rng: Rng) -> float:
    """AI starting money for a Competitor Capital setting (gap audit C4).

    FUN_0007916c: (v/2 + random(v/2)) * 6,000,000 / 10 with integer v/2 and
    random(n) in 0..n-1. Native credits the CEO's wealth; the hand-off to corp
    cash is not traced, so the sim puts it in corp cash.
    """
    half = COMPETITOR_CAPITAL[setting].v // 2
    return (half + rng.randint(0, half - 1)) * _AR.capital_unit


def try_spawn_competitor(eco: Economy, day_serial: int) -> Corporation | None:
    """Try to spawn a new AI competitor (gamelogic.md NPC corporation spawning)."""
    rng = eco.rng

    if day_serial == 0 and not rng.chance(_AR.spawn_first_day_gate):
        return None
    if not rng.chance(_AR.spawn_chance):
        return None

    available = [
        p for p in eco.all_persons()
        if p.state == STATE_ACTIVE and p.role == ROLE_INDEPENDENT and p.cooldown == 0
    ]
    if not available:
        return None

    competitor_cap = int(_AR.competitor_cap)
    if eco.competitor_count() >= competitor_cap:
        return None
    if eco.competitor_count() >= int(_AR.max_competitors):
        return None

    person = rng.choice(available)

    from .economy import CORP_AI
    corp = eco.add_corp(person.name, CORP_AI)
    person.link_to_corp(corp.id, as_ceo=True)

    # Starting capital
    corp.ledger.cash = ai_starting_capital(eco.competitor_capital, rng)

    # Determine strategy mode
    game_years = day_serial / 365.0
    if game_years > _AR.dormant_year_threshold and rng.chance(_AR.dormant_chance):
        mode = MODE_DORMANT
    else:
        mode = rng.randint(MODE_ESTABLISH, MODE_RETAIL)

    ai_state = AIState(corp.id, day_serial, rng)
    ai_state.mode = mode
    if mode == MODE_DORMANT:
        ai_state.dormant_start_day = day_serial
    eco.ai_states[corp.id] = ai_state

    return corp


# --- Daily AI dispatch -------------------------------------------------------

def ai_daily(eco: Economy, corp: Corporation, day_serial: int) -> None:
    """Run all AI decision checks for one corporation on one day."""
    ai = eco.ai_states.get(corp.id)
    if ai is None:
        return

    rng = eco.rng
    ceo = _find_ceo(eco, corp)
    offset_day = day_serial + ai.schedule_offset

    # Tick cooldowns
    expired = [k for k, v in ai.build_cooldowns.items() if v <= day_serial]
    for k in expired:
        del ai.build_cooldowns[k]

    # Cash management: reset AI cash to ~$1B (gamelogic.md Cash management)
    corp.ledger.cash = _AR.ai_cash_reset

    # Strategy dispatcher (every 15 days)
    if offset_day - ai.last_strategy_day >= int(_AR.strategy_interval):
        ai.last_strategy_day = offset_day
        _strategy_dispatch(eco, corp, ai, ceo, day_serial)

    # Supply chain linking (every 15 days, offset)
    if offset_day - ai.last_link_day >= int(_AR.link_interval):
        ai.last_link_day = offset_day

    # Financial analysis (every 30 days)
    if offset_day - ai.last_finance_day >= int(_AR.finance_interval):
        ai.last_finance_day = offset_day

    # Market survey (every 30 days)
    if offset_day - ai.last_survey_day >= int(_AR.survey_interval):
        ai.last_survey_day = offset_day

    # Vertical integration (every 60 days)
    if offset_day - ai.last_vertical_day >= int(_AR.vertical_interval):
        ai.last_vertical_day = offset_day
        if ai.mode in (MODE_ESTABLISH, MODE_MANUFACTURE) and ai.pending_build is None:
            _vertical_integration(eco, corp, ai, day_serial)

    # Market dominance (variable interval)
    char_type = ceo.character_type if ceo else CHAR_CONSERVATIVE
    dominance_interval = DOMINANCE_INTERVALS[min(char_type, CHAR_VERY_AGGRESSIVE)]
    if offset_day - ai.last_dominance_day >= dominance_interval:
        ai.last_dominance_day = offset_day

    # Mode transition (every 200 days)
    if offset_day - ai.last_mode_day >= int(_AR.mode_transition_interval):
        ai.last_mode_day = offset_day
        _check_mode_transition(eco, corp, ai, ceo, day_serial)
        _check_bankruptcy(eco, corp, ai, day_serial)

    # Annual expansion (every 365 days)
    if offset_day - ai.last_annual_day >= 365:
        ai.last_annual_day = offset_day

    # Random strategy parameter change (1/1000)
    if rng.chance(_AR.random_build_chance):
        _random_build(eco, corp, ai, day_serial)


def _find_ceo(eco: Economy, corp: Corporation) -> Person | None:
    """Find the person linked as CEO to this corporation."""
    from .person import ROLE_CEO, STATE_LINKED
    for p in eco.all_persons():
        if p.corp_id == corp.id and p.state == STATE_LINKED and p.role == ROLE_CEO:
            return p
    return None


def _strategy_dispatch(
    eco: Economy, corp: Corporation, ai: AIState, ceo: Person | None, day_serial: int
) -> None:
    """Strategy dispatcher: pick a product category and build (gamelogic.md Strategy dispatcher)."""
    if ai.mode == MODE_DORMANT:
        _dormant_check(eco, corp, ai, ceo, day_serial)
        return

    rng = eco.rng
    owned = _owned_firms(eco, corp)
    if not owned and not eco.world.towns:
        return

    town = _pick_town(eco, corp)
    if town is None:
        return

    # 80% skill-based, 20% random product selection
    if rng.chance(0.8) and ceo is not None:
        firm_type = _skill_based_pick(eco, corp, ceo, ai)
    else:
        firm_type = _random_firm_type(rng, ai)

    if firm_type is None:
        return

    # Profitability gate
    if not passes_profitability_gate(eco, corp, firm_type, ceo):
        return

    # Cooldown check
    if firm_type in ai.build_cooldowns:
        return

    # Build
    firm = ai_build_firm(eco, corp, firm_type, town, rng, rural=firm_type in (4, 5, 6, 7))
    if firm is not None:
        ai.build_cooldowns[firm_type] = day_serial + int(_AR.build_cooldown)


def _dormant_check(
    eco: Economy, corp: Corporation, ai: AIState, ceo: Person | None, day_serial: int
) -> None:
    """Dormant mode: check if enough years have passed to wake up."""
    rng = eco.rng
    salary_trait = ceo.salary_trait if ceo else 50
    wake_years = salary_trait / 10.0 + rng.randint(0, 5)
    days_dormant = day_serial - ai.dormant_start_day
    if days_dormant >= wake_years * 365:
        ai.mode = MODE_ESTABLISH
        ai.mode_start_day = day_serial


def _pick_town(eco: Economy, corp: Corporation) -> Town | None:
    """Pick the best town for AI expansion."""
    towns = eco.world.towns
    if not towns:
        return None
    # Prefer the town with highest population among those the corp doesn't dominate
    return max(towns, key=lambda t: t.population)


def _skill_based_pick(
    eco: Economy, corp: Corporation, ceo: Person, ai: AIState
) -> int | None:
    """Pick a firm type based on CEO's expertise skills (gamelogic.md cross-wired mapping)."""
    from .person import SKILL_FARMING, SKILL_MANUFACTURING, SKILL_RETAILING

    candidates: list[tuple[float, int]] = []
    # Factory (type 2) uses retailing skill
    if 2 not in ai.build_cooldowns:
        candidates.append((ceo.skills[SKILL_RETAILING], 2))
    # Store (type 1) uses manufacturing skill
    if 1 not in ai.build_cooldowns:
        candidates.append((ceo.skills[SKILL_MANUFACTURING], 1))
    # Farm (type 4) uses farming skill
    if 4 not in ai.build_cooldowns:
        candidates.append((ceo.skills[SKILL_FARMING], 4))

    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def _random_firm_type(rng: Rng, ai: AIState) -> int | None:
    """Pick a random firm type from the mode's available types."""
    options = [1, 2, 4]  # store, factory, farm
    available = [t for t in options if t not in ai.build_cooldowns]
    if not available:
        return None
    return rng.choice(available)


def _vertical_integration(
    eco: Economy, corp: Corporation, ai: AIState, day_serial: int
) -> None:
    """Vertical integration: build retail for unsold products (gamelogic.md Vertical integration)."""
    rng = eco.rng
    town = _pick_town(eco, corp)
    if town is None:
        return

    # Build a department store if the corp has factories but no stores
    owned = _owned_firms(eco, corp)
    has_factory = any(f.type_id == 2 for f in owned)
    has_store = any(f.type_id == 1 for f in owned)
    if has_factory and not has_store:
        firm = ai_build_firm(eco, corp, 1, town, rng)
        if firm is not None:
            ai.build_cooldowns[1] = day_serial + int(_AR.build_cooldown)


def _check_mode_transition(
    eco: Economy, corp: Corporation, ai: AIState, ceo: Person | None, day_serial: int
) -> None:
    """Mode transition check (gamelogic.md Strategy modes)."""
    salary_trait = ceo.salary_trait if ceo else 50
    char_type = ceo.character_type if ceo else CHAR_CONSERVATIVE

    owned = _owned_firms(eco, corp)
    factory_count = sum(1 for f in owned if f.type_id == 2)
    store_count = sum(1 for f in owned if f.type_id == 1)

    threshold = max(1, salary_trait // 20 + 2)
    years_in_mode = (day_serial - ai.mode_start_day) / 365.0
    duration_threshold = max(1, 16 - salary_trait // 10)

    if ai.mode == MODE_MANUFACTURE:
        if factory_count >= threshold and years_in_mode >= duration_threshold:
            ai.mode = MODE_ESTABLISH
            ai.mode_start_day = day_serial
    elif ai.mode == MODE_RETAIL:
        if store_count >= threshold:
            ai.mode = MODE_ESTABLISH
            ai.mode_start_day = day_serial
    elif ai.mode in (MODE_ESTABLISH, MODE_MANUFACTURE, MODE_RETAIL) and not owned:
        dormant_years = max(1, (4 - char_type) * 2)
        if years_in_mode >= dormant_years:
            ai.mode = MODE_DORMANT
            ai.mode_start_day = day_serial
            ai.dormant_start_day = day_serial


def _check_bankruptcy(
    eco: Economy, corp: Corporation, ai: AIState, day_serial: int
) -> None:
    """Bankruptcy check (gamelogic.md Bankruptcy check)."""
    age_days = day_serial - ai.mode_start_day
    if age_days < _AR.bankruptcy_age_threshold * 365:
        return
    owned = _owned_firms(eco, corp)
    if owned:
        return
    total_value = corp.total_assets(eco.firms)
    if total_value < _AR.bankruptcy_value_threshold:
        corp.ledger.cash = 0.0
        # Mark as bankrupt — the corporation stays but is inactive


def _random_build(
    eco: Economy, corp: Corporation, ai: AIState, day_serial: int
) -> None:
    """1/1000 random build in a random town (gamelogic.md Strategy parameter change)."""
    rng = eco.rng
    towns = eco.world.towns
    if not towns:
        return
    town = rng.choice(towns)
    firm = ai_build_firm(eco, corp, 1, town, rng)  # department store
    if firm is not None:
        ai.build_cooldowns[1] = day_serial + int(_AR.build_cooldown)
