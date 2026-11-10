"""Goals, victory conditions, scoring, and difficulty rating (system 12).

Covers goal configuration, periodic goal checks (player every 2 days,
AI every 7 in untimed games), difficulty rating computation, and the
final scoring formula.
"""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from .tables import SCORING_RULES, SetupOptions

if TYPE_CHECKING:
    from .economy import Economy

_SR = SCORING_RULES

N_SECTORS = 4


# ---------------------------------------------------------------------------
# Goal result
# ---------------------------------------------------------------------------

class GameResult(IntEnum):
    IN_PROGRESS = 0
    VICTORY = 1
    DEFEAT_DEADLINE = 2
    DEFEAT_AI_WON = 3


# ---------------------------------------------------------------------------
# Goal configuration
# ---------------------------------------------------------------------------

class GoalConfig:
    """All 17 numeric targets + dominance toggles."""

    __slots__ = (
        "controlled_annual_op_profit",
        "controlled_annual_revenue",
        "controlled_market_value",
        "controlled_net_worth",
        "corp_annual_op_profit",
        "corp_annual_revenue",
        "corp_market_value",
        "corp_net_worth",
        "industry_goals",
        "num_companies_controlled",
        "num_employees",
        "num_product_classes",
        "num_product_types",
        "op_profit_margin",
        "ownership_pct",
        "personal_wealth",
        "return_on_equity",
        "sector_goals",
        "stock_price",
    )

    def __init__(self) -> None:
        self.personal_wealth: float = 0.0
        self.corp_net_worth: float = 0.0
        self.corp_market_value: float = 0.0
        self.corp_annual_revenue: float = 0.0
        self.corp_annual_op_profit: float = 0.0
        self.controlled_net_worth: float = 0.0
        self.controlled_market_value: float = 0.0
        self.controlled_annual_revenue: float = 0.0
        self.controlled_annual_op_profit: float = 0.0
        self.num_companies_controlled: int = 0
        self.num_employees: int = 0
        self.op_profit_margin: float = 0.0
        self.return_on_equity: float = 0.0
        self.stock_price: float = 0.0
        self.ownership_pct: float = 0.0
        self.num_product_classes: int = 0
        self.num_product_types: int = 0
        self.sector_goals: list[bool] = [False] * N_SECTORS
        self.industry_goals: list[bool] = []

    @property
    def has_any_goal(self) -> bool:
        numeric = (
            self.personal_wealth,
            self.corp_net_worth,
            self.corp_market_value,
            self.corp_annual_revenue,
            self.corp_annual_op_profit,
            self.controlled_net_worth,
            self.controlled_market_value,
            self.controlled_annual_revenue,
            self.controlled_annual_op_profit,
            self.num_companies_controlled,
            self.num_employees,
            self.op_profit_margin,
            self.return_on_equity,
            self.stock_price,
            self.ownership_pct,
            self.num_product_classes,
            self.num_product_types,
        )
        if any(v > 0 for v in numeric):
            return True
        if any(self.sector_goals):
            return True
        return any(self.industry_goals)


# ---------------------------------------------------------------------------
# Goal evaluation
# ---------------------------------------------------------------------------

def _get_player_values(economy: Economy, player_corp_id: int) -> dict[str, float]:
    """Gather current values for all goal metrics."""
    corps = economy.corps
    player_corp = None
    for c in corps:
        if c.id == player_corp_id:
            player_corp = c
            break

    result: dict[str, float] = {}

    if player_corp is None:
        return {k: 0.0 for k in (
            "personal_wealth", "corp_net_worth", "corp_market_value",
            "corp_annual_revenue", "corp_annual_op_profit",
            "controlled_net_worth", "controlled_market_value",
            "controlled_annual_revenue", "controlled_annual_op_profit",
            "num_companies_controlled", "num_employees",
            "op_profit_margin", "return_on_equity",
            "stock_price", "ownership_pct",
            "num_product_classes", "num_product_types",
        )}

    nw = player_corp.net_worth(economy.firms)
    result["personal_wealth"] = nw
    result["corp_net_worth"] = nw / 1_000_000.0
    stock = economy.stocks[player_corp_id] if player_corp_id < len(economy.stocks) else None
    if stock is not None:
        result["corp_market_value"] = (stock.price * stock.total_shares) / 1_000_000.0
        result["stock_price"] = stock.price
        total = stock.total_shares
        if total > 0:
            held = sum(stock.holdings_persons)
            result["ownership_pct"] = held / total * 100.0
        else:
            result["ownership_pct"] = 100.0
    else:
        result["corp_market_value"] = result["corp_net_worth"]
        result["stock_price"] = 0.0
        result["ownership_pct"] = 100.0

    rev = player_corp.month_history.get("revenue", [])
    annual_rev = sum(rev[-12:]) if rev else 0.0
    result["corp_annual_revenue"] = annual_rev / 1_000_000.0
    op = player_corp.month_history.get("operating_profit", [])
    annual_op = sum(op[-12:]) if op else 0.0
    result["corp_annual_op_profit"] = annual_op / 1_000_000.0

    result["controlled_net_worth"] = result["corp_net_worth"]
    result["controlled_market_value"] = result["corp_market_value"]
    result["controlled_annual_revenue"] = result["corp_annual_revenue"]
    result["controlled_annual_op_profit"] = result["corp_annual_op_profit"]
    result["num_companies_controlled"] = 1

    employees = 0
    product_classes: set[int] = set()
    product_types: set[int] = set()
    for firm in economy.firms:
        if firm is None:
            continue
        if getattr(firm, "corp_id", None) != player_corp_id:
            continue
        for job in firm.jobs():
            employees += getattr(job, "staff", 0)
            p = getattr(job, "product", None)
            if p is not None:
                product_types.add(p.id)
                product_classes.add(p.class_id)
    result["num_employees"] = float(employees)
    result["num_product_classes"] = float(len(product_classes))
    result["num_product_types"] = float(len(product_types))

    if annual_rev > 0:
        result["op_profit_margin"] = (annual_op / annual_rev) * 100.0
    else:
        result["op_profit_margin"] = 0.0
    equity = player_corp.net_worth(economy.firms)
    if equity > 0:
        result["return_on_equity"] = (annual_op / equity) * 100.0
    else:
        result["return_on_equity"] = 0.0

    return result


def check_goals(
    goals: GoalConfig,
    economy: Economy,
    player_corp_id: int,
) -> tuple[bool, dict[str, tuple[float, float, bool]]]:
    """Check all goals. Returns (all_met, {goal_name: (target, current, met)})."""
    values = _get_player_values(economy, player_corp_id)
    results: dict[str, tuple[float, float, bool]] = {}

    checks = [
        ("personal_wealth", goals.personal_wealth),
        ("corp_net_worth", goals.corp_net_worth),
        ("corp_market_value", goals.corp_market_value),
        ("corp_annual_revenue", goals.corp_annual_revenue),
        ("corp_annual_op_profit", goals.corp_annual_op_profit),
        ("controlled_net_worth", goals.controlled_net_worth),
        ("controlled_market_value", goals.controlled_market_value),
        ("controlled_annual_revenue", goals.controlled_annual_revenue),
        ("controlled_annual_op_profit", goals.controlled_annual_op_profit),
        ("num_companies_controlled", goals.num_companies_controlled),
        ("num_employees", goals.num_employees),
        ("op_profit_margin", goals.op_profit_margin),
        ("return_on_equity", goals.return_on_equity),
        ("stock_price", goals.stock_price),
        ("ownership_pct", goals.ownership_pct),
        ("num_product_classes", goals.num_product_classes),
        ("num_product_types", goals.num_product_types),
    ]

    all_met = True
    for name, target in checks:
        if target <= 0:
            continue
        current = values.get(name, 0.0)
        met = current >= target
        results[name] = (target, current, met)
        if not met:
            all_met = False

    for i, enabled in enumerate(goals.sector_goals):
        if not enabled:
            continue
        results[f"sector_{i}"] = (1.0, 0.0, False)
        all_met = False

    for i, enabled in enumerate(goals.industry_goals):
        if not enabled:
            continue
        results[f"industry_{i}"] = (1.0, 0.0, False)
        all_met = False

    return all_met, results


# ---------------------------------------------------------------------------
# Goal checker (called from sim)
# ---------------------------------------------------------------------------

class GoalChecker:
    """Periodic goal evaluation integrated into the sim day order."""

    __slots__ = (
        "_goals_met",
        "goals",
        "player_corp_id",
        "result",
        "warning_shown_year",
        "years_warning",
    )

    def __init__(
        self,
        goals: GoalConfig,
        player_corp_id: int = 0,
    ) -> None:
        self.goals = goals
        self.player_corp_id = player_corp_id
        self.result = GameResult.IN_PROGRESS
        self._goals_met = False
        self.years_warning: int = 0
        self.warning_shown_year: int = 0

    def daily(
        self,
        economy: Economy,
        day_serial: int,
        year: int,
        setup: SetupOptions,
    ) -> GameResult:
        if self.result != GameResult.IN_PROGRESS:
            return self.result
        if not self.goals.has_any_goal:
            return GameResult.IN_PROGRESS

        if day_serial % int(_SR.player_goal_check_interval) == 0:
            all_met, _ = check_goals(self.goals, economy, self.player_corp_id)
            if all_met:
                self.result = GameResult.VICTORY
                self._goals_met = True
                return self.result

        if setup.year_limit == 0 and day_serial % int(_SR.ai_goal_check_interval) == 0:
            pass

        return GameResult.IN_PROGRESS

    def yearly(self, year: int, start_year: int, year_limit: int) -> GameResult:
        if self.result != GameResult.IN_PROGRESS:
            return self.result
        if year_limit <= 0:
            return GameResult.IN_PROGRESS
        years_played = year - start_year
        remaining = year_limit - years_played
        if remaining < 1:
            if not self._goals_met:
                self.result = GameResult.DEFEAT_DEADLINE
            return self.result
        if 1 <= remaining <= int(_SR.warning_years_threshold):
            self.years_warning = remaining
        return GameResult.IN_PROGRESS


# ---------------------------------------------------------------------------
# Difficulty rating
# ---------------------------------------------------------------------------

def compute_difficulty_rating(setup: SetupOptions) -> int:
    """Compute the 1–200+ difficulty rating from setup options."""
    s = _SR
    score = setup.competitor_capital * s.difficulty_capital_mult + s.difficulty_base_offset

    if not setup.show_trade_secrets:
        score += s.difficulty_secrets_penalty

    char = setup.competitor_character
    if 0 <= char <= 3:
        score += char * s.difficulty_char_per_type
    elif char >= 4:
        score += s.difficulty_char_mixed_penalty

    exp = setup.expertise_level
    if exp == 1:
        score += s.difficulty_expertise_vlow
    elif exp > 1:
        score += (exp - 1) * s.difficulty_expertise_per_level

    total_seaports = setup.consumer_seaports + setup.industrial_seaports
    if total_seaports == 0:
        score += s.difficulty_no_seaports

    score += score * setup.competitors // 10 + 1

    score += setup.competence_level * s.difficulty_competence_per_level

    score += setup.event_frequency * s.difficulty_events_per_level

    score = max(1, score * s.difficulty_scale_numerator // s.difficulty_scale_denominator)
    return score


# ---------------------------------------------------------------------------
# Final scoring
# ---------------------------------------------------------------------------

def compute_final_score(
    setup: SetupOptions,
    personal_wealth: float,
    corp_net_worth: float,
    sectors_dominated: int,
    products_dominated: int,
    years_played: int,
    goals_achieved: bool,
) -> int:
    """Compute the final score using the formula from gamelogic.md."""
    if setup.cheated:
        return 0

    s = _SR
    base = 0.0
    base += (personal_wealth / 1_000_000_000.0) * s.wealth_per_billion
    base += (corp_net_worth / 1_000_000_000.0) * s.corpworth_per_billion
    base += sectors_dominated * s.sector_points
    base += products_dominated * s.product_points

    difficulty = compute_difficulty_rating(setup)
    score = base * difficulty / 100.0

    if years_played > s.year_penalty_threshold:
        score = score * s.year_penalty_threshold / years_played

    if goals_achieved:
        if setup.is_scenario:
            score += setup.goal_score_bonus
        else:
            score *= s.free_goal_multiplier

    return max(1, int(score))
