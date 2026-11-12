"""AI corporation strategy: decision engine, spawning, expansion (gamelogic.md AI corporation strategy)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .person import (
    CHAR_CONSERVATIVE,
    CHAR_VERY_AGGRESSIVE,
    ROLE_INDEPENDENT,
    SKILL_FARMING,
    SKILL_MANUFACTURING,
    SKILL_RAW_MATERIAL,
    SKILL_RETAILING,
    SKILL_RND,
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

# Firm-type preference lists by strategy mode (techspec DAT_000ad7f0, decoded)
MODE_FIRM_TYPES: dict[int, tuple[int, ...]] = {
    MODE_ESTABLISH: (1, 2, 3, 4, 5, 6, 7, 10, 8, 9),
    MODE_MANUFACTURE: (2, 3, 4, 10, 8, 9),
    MODE_RETAIL: (1, 10),
    MODE_DORMANT: (),
}

# CEO skill used to score each firm type (techspec FUN_0007a2e4, cross-wired)
FIRM_TYPE_SKILL: dict[int, int] = {
    1: SKILL_MANUFACTURING,   # Store → manufacturing (cross-wired)
    2: SKILL_RETAILING,       # Factory → retailing (cross-wired)
    3: SKILL_RND,             # R&D Center → R&D
    4: SKILL_FARMING,         # Farm → farming
    5: SKILL_RAW_MATERIAL,    # Logging Camp → raw material
    6: SKILL_RAW_MATERIAL,    # Mine → raw material
    7: SKILL_RAW_MATERIAL,    # Oil Well → raw material
    8: SKILL_RND,             # Software Developer → R&D
    9: SKILL_RND,             # Software Publisher → R&D
    10: SKILL_MANUFACTURING,  # Restaurant → manufacturing (store category)
}

RETRY_COOLDOWN = 20

# Max businesses per type in random build, by town level (techspec FUN_000316b4)
RANDOM_BUILD_CAP = {0: 2, 1: 2, 2: 3, 3: 3, 4: 4, 5: 4}


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
        "retry_cooldowns",
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
        self.retry_cooldowns: dict[int, int] = {}
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
    # If short, raise cash with FUN_00030ae2 and re-check; cancel only if still short.
    cost = land_value + FIRM_TYPES[firm_type].setup_cost
    if corp.ledger.cash < cost and not ai_raise_cash(eco, corp, cost):
        return None
    try:
        return eco.build_firm(firm_type, corp, x, y, town)
    except (ValueError, NotImplementedError):
        return None


def _sell_holdings(eco: Economy, corp: Corporation, target: float) -> None:
    """Step 1/5: sell shares this corp holds in other corps (FUN_00030c6e)."""
    if not eco.stock_enabled:
        return
    for stock in eco.stocks:
        if corp.ledger.cash >= target:
            break
        if stock is None or stock.corp_id == corp.id:
            continue
        held = stock.holdings_corps[corp.id]
        while held > 0 and corp.ledger.cash < target:
            want = min(held, int((target - corp.ledger.cash) // max(stock.price, 0.10)) + 1)
            eco.sell_stock(corp, stock.corp_id, want)
            held = stock.holdings_corps[corp.id]


def _issue_own_shares(eco: Economy, corp: Corporation) -> bool:
    """One own-share issue (FUN_00030d97, decomp:27540-27566).

    Issues new shares of the corp's own stock. Minimum issue is
    ai.share_issue_min (DAT_000a4835 = 10,000). The issue size source is
    lost in the decompile; issuing share_issue_min shares is provisional.
    Returns True if shares were issued.
    """
    if not eco.stock_enabled:
        return False
    stock = eco.stocks[corp.id]
    if stock is None or stock.price < 1.0:
        return False
    if stock.total_shares < _AR.share_issue_min:
        return False
    eco.issue_stock(corp, _AR.share_issue_min)
    return True


def ai_raise_cash(eco: Economy, corp: Corporation, target: float) -> bool:
    """Raise cash toward *target* before a build is cancelled (FUN_00030ae2, audit B2).

    Researcher trace (decomp:27435-27473), seven steps:
    1. Sell holdings in other corps (FUN_00030c6e, decomp:27484-27530).
    2. Bank loan (FUN_00037a7e, decomp:33468-33495), capped at credit limit.
    3. Chairman-byte give-up gate — skipped (byte meaning is Unknown).
    4. Own share issue (FUN_00030d97, decomp:27540-27566).
    5. Second holdings sale.
    6. Retry loop: up to 10 more own-share issues (decomp:27455-27459).
    7. Firm closures while cash < 0 — not modelled (A3 Hold).
    Returns True once cash >= target.
    """
    if corp.ledger.cash >= target:
        return True
    # Step 1: sell holdings
    _sell_holdings(eco, corp, target)
    if corp.ledger.cash >= target:
        return True
    # Step 2: bank loan
    short = target - corp.ledger.cash
    if short > 0:
        amount = min(max(short, _AR.loan_minimum), corp.credit_limit(eco.firms))
        if amount >= _AR.loan_minimum:
            corp.borrow(amount)
    if corp.ledger.cash >= target:
        return True
    # Step 3: chairman-byte give-up gate — Unknown, skipped
    # Step 4: own share issue
    _issue_own_shares(eco, corp)
    if corp.ledger.cash >= target:
        return True
    # Step 5: second holdings sale
    _sell_holdings(eco, corp, target)
    if corp.ledger.cash >= target:
        return True
    # Step 6: retry own-share issues up to 10 times
    for _ in range(10):
        if corp.ledger.cash >= target:
            return True
        if not _issue_own_shares(eco, corp):
            break
    return corp.ledger.cash >= target


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
    expired = [k for k, v in ai.retry_cooldowns.items() if v <= day_serial]
    for k in expired:
        del ai.retry_cooldowns[k]

    # No cash reset here: native resets cash to $1B only for the Government corp
    # (FUN_00030ffc, vtable 0x3553c; audit A1). Competitors spend real cash.

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
        _configure_new_firm(eco, corp, firm, rng)
    else:
        ai.retry_cooldowns[firm_type] = day_serial + RETRY_COOLDOWN


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
    """Pick a firm type based on CEO's expertise skills (techspec FUN_0007a2e4)."""
    type_list = MODE_FIRM_TYPES.get(ai.mode, ())
    candidates: list[tuple[float, int]] = []
    for ft in type_list:
        if ft in ai.build_cooldowns or ft in ai.retry_cooldowns:
            continue
        skill_idx = FIRM_TYPE_SKILL.get(ft)
        if skill_idx is None:
            continue
        candidates.append((ceo.skills[skill_idx], ft))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def _random_firm_type(rng: Rng, ai: AIState) -> int | None:
    """Pick a random firm type from the mode's available types."""
    type_list = MODE_FIRM_TYPES.get(ai.mode, ())
    available = [t for t in type_list if t not in ai.build_cooldowns and t not in ai.retry_cooldowns]
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
    """1/1000 random build in a random town (techspec FUN_000316b4).

    Native builds type 0xb (TV) or 0xd (Newspaper) from the Government
    corp. The sim has no Government corp, so this runs for competitors
    building a Department Store, capped by town level.
    """
    rng = eco.rng
    towns = eco.world.towns
    if not towns:
        return
    town = rng.choice(towns)
    firm_type = 1  # Department Store
    cap = RANDOM_BUILD_CAP.get(town.level, 2)
    count = sum(
        1 for f in eco.firms
        if f is not None and f.type_id == firm_type and f.town is town
    )
    if count >= cap:
        return
    firm = ai_build_firm(eco, corp, firm_type, town, rng)
    if firm is not None:
        ai.build_cooldowns[firm_type] = day_serial + int(_AR.build_cooldown)
        _configure_new_firm(eco, corp, firm, rng)


# --- AI firm configuration (R18) -------------------------------------------

_PURCHASE_SLOTS = (3, 1, 7, 0, 2, 6, 8)
_MFG_SLOT = 4
_SALES_SLOT = 5
_EXTRACT_JOB = {5: 4, 6: 8, 7: 9}
_EXTRACT_PRODUCTS: dict[int, tuple[int, ...]] = {
    5: (8,),
    6: (1, 2, 3, 4, 5, 7),
    7: (6,),
}
_DEFAULT_RESERVE = 100.0


def _grant_tech(corp: Corporation, product: object) -> None:
    if not corp.has_technology(product):
        corp.add_technology(product, product.state.tech_level)


def _configure_new_firm(
    eco: Economy, corp: Corporation, firm: object, rng: Rng
) -> None:
    """Configure a newly built AI firm with jobs (R18, techspec FUN_0002b895).

    The native AI selects a product group from the plan library and copies
    its 9-slot template into the new firm, then wires supplier links.  The
    sim's plan library starts empty, so this picks products directly from
    the catalog and adds the minimum set of jobs that make the firm
    functional.  Supply chain linking is not yet modelled (R22).
    """
    from .catalog import ConsumerProduct, Crop, Livestock
    from .tables import LIVESTOCK_YIELDS

    cat = eco.catalog
    ft = firm.type_id

    if ft in (1, 10):
        candidates = [
            p for p in cat.products
            if isinstance(p, ConsumerProduct) and p.state.available
            and p.row.demand_per_1000 > 0
        ]
        if not candidates:
            return
        product = rng.choice(candidates)
        _grant_tech(corp, product)
        firm.add_job(0, 10, product)
        firm.add_job(1, 12, product)
        firm.link_slots(0, 1)

    elif ft == 2:
        recipes = [
            (cat.by_id[pid], rec)
            for pid, rec in cat.recipes.items()
            if isinstance(cat.by_id[pid], ConsumerProduct)
            and cat.by_id[pid].state.available
        ]
        if not recipes:
            return
        product, recipe = rng.choice(recipes)
        _grant_tech(corp, product)
        for i, inp in enumerate(recipe.inputs):
            if i >= len(_PURCHASE_SLOTS):
                break
            inp_p = cat.by_id[inp.input_id]
            _grant_tech(corp, inp_p)
            firm.add_job(_PURCHASE_SLOTS[i], 10, inp_p)
            firm.link_slots(_PURCHASE_SLOTS[i], _MFG_SLOT)
        firm.add_job(_MFG_SLOT, 7, product)
        firm.add_job(_SALES_SLOT, 12, product)
        firm.link_slots(_MFG_SLOT, _SALES_SLOT)

    elif ft == 3:
        candidates = [
            p for p in cat.products
            if p.state.available and not corp.has_technology(p)
        ]
        if not candidates:
            candidates = [p for p in cat.products if p.state.available]
        if not candidates:
            return
        firm.add_job(0, 11, rng.choice(candidates))

    elif ft == 4:
        candidates = [
            p for p in cat.products
            if isinstance(p, (Crop, Livestock)) and p.state.available
        ]
        if not candidates:
            return
        product = rng.choice(candidates)
        _grant_tech(corp, product)
        if isinstance(product, Crop):
            firm.add_job(0, 1, product)
            firm.add_job(1, 12, product)
            firm.link_slots(0, 1)
        else:
            firm.add_job(0, 2, product)
            yield_row = LIVESTOCK_YIELDS.get(product.id)
            if yield_row is not None:
                out = cat.by_id[yield_row.product_id]
                _grant_tech(corp, out)
                firm.add_job(1, 3, out)
                firm.add_job(2, 12, out)
                firm.link_slots(0, 1)
                firm.link_slots(1, 2)
            else:
                firm.add_job(1, 12, product)
                firm.link_slots(0, 1)

    elif ft in _EXTRACT_JOB:
        products = _EXTRACT_PRODUCTS[ft]
        pid = rng.choice(products) if len(products) > 1 else products[0]
        product = cat.by_id[pid]
        _grant_tech(corp, product)
        firm.add_job(0, _EXTRACT_JOB[ft], product)
        firm.add_job(1, 12, product)
        firm.link_slots(0, 1)
        firm.reserve = _DEFAULT_RESERVE

    elif ft == 8:
        product = cat.by_id.get(85)
        if product is None:
            return
        firm.add_job(0, 13, product)

    elif ft == 9:
        product = cat.by_id.get(85)
        if product is None:
            return
        _grant_tech(corp, product)
        firm.add_job(0, 14, product)
        firm.add_job(1, 12, product)
        firm.link_slots(0, 1)
