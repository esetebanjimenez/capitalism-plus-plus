"""Person system: CEOs, hired managers, expertise, satisfaction, salary (gamelogic.md Person system)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .tables import PERSON_RULES

if TYPE_CHECKING:
    from .rng import Rng

# Lifecycle states
STATE_EMPTY = 0
STATE_ACTIVE = 1
STATE_LINKED = 2
STATE_RETIRED = 3

# Character types (aggressiveness)
CHAR_CONSERVATIVE = 0
CHAR_MODERATE = 1
CHAR_AGGRESSIVE = 2
CHAR_VERY_AGGRESSIVE = 3

# Role titles
ROLE_HUMAN_PLAYER = 0
ROLE_CEO = 1
ROLE_CHAIRMAN = 2
ROLE_CEO_CHAIRMAN = 3
ROLE_PRESIDENT = 4
ROLE_PRESIDENT_CHAIRMAN = 5
ROLE_INDEPENDENT = 6
ROLE_RETIRED = 7

ROLE_LABELS = {
    ROLE_HUMAN_PLAYER: "Human Player",
    ROLE_CEO: "CEO",
    ROLE_CHAIRMAN: "Chairman",
    ROLE_CEO_CHAIRMAN: "CEO & Chairman",
    ROLE_PRESIDENT: "President",
    ROLE_PRESIDENT_CHAIRMAN: "President & Chairman",
    ROLE_INDEPENDENT: "Independent Investor",
    ROLE_RETIRED: "Retired",
}

# Satisfaction labels
_SATISFACTION_LABELS = [
    (-50, "Very Bad"),
    (0, "Bad"),
    (1, "Neutral"),
    (50, "Good"),
]

# Expertise skill indices and weights (gamelogic.md Expertise skills)
SKILL_MANUFACTURING = 0
SKILL_RND = 1
SKILL_FARMING = 2
SKILL_ADVERTISING = 3
SKILL_TRAINING = 4
SKILL_RETAILING = 5
SKILL_RAW_MATERIAL = 6
N_SKILLS = 7

SKILL_WEIGHTS = (25.0, 17.5, 15.0, 15.0, 15.0, 7.5, 5.0)

_PR = PERSON_RULES


class Person:
    """A CEO, hired manager, or independent investor."""

    __slots__ = (
        "acceptance_trait",
        "character_type",
        "cooldown",
        "corp_id",
        "expansion_trait",
        "gender",
        "id",
        "name",
        "role",
        "salary",
        "salary_trait",
        "satisfaction",
        "skills",
        "state",
        "trait7",
        "wealth",
        "years_of_service",
    )

    def __init__(self, person_id: int, name: str, *, is_player: bool = False) -> None:
        self.id = person_id
        self.name = name
        self.state = STATE_ACTIVE
        self.role = ROLE_HUMAN_PLAYER if is_player else ROLE_INDEPENDENT
        self.corp_id: int | None = None
        self.gender = 0  # 0=male, 1=female
        self.character_type = CHAR_CONSERVATIVE
        self.skills = [0.0] * N_SKILLS
        self.satisfaction = 0
        self.salary = 0.0
        self.wealth = 0.0
        self.years_of_service = 0
        self.cooldown = 0
        # Active personality traits
        self.salary_trait = 50
        self.trait7 = 50
        self.expansion_trait = 50
        self.acceptance_trait = 0
        # Player defaults: moderate baselines, acceptance trait 0

    # --- expertise -----------------------------------------------------------

    @property
    def performance_score(self) -> float:
        return sum(s * w for s, w in zip(self.skills, SKILL_WEIGHTS)) / 100.0

    def randomize_skills(self, rng: Rng, level: int) -> None:
        """Set expertise skills based on competitor expertise level setting.

        level: 0=None, 1=Low, 2=Medium, 3=High.
        Higher levels shift the random range upward.
        """
        base = level * int(_PR.skill_level_step)
        for i in range(N_SKILLS):
            lo = max(0, base)
            hi = min(100, base + int(_PR.skill_range))
            self.skills[i] = float(rng.randint(lo, hi))

    # --- satisfaction --------------------------------------------------------

    @property
    def satisfaction_label(self) -> str:
        s = self.satisfaction
        if s < -50:
            return "Very Bad"
        if s < 0:
            return "Bad"
        if s == 0:
            return "Neutral"
        if s < 50:
            return "Good"
        return "Very Good"

    def monthly_satisfaction_drift(self, rng: Rng) -> None:
        """Monthly drift toward contentment (gamelogic.md Satisfaction)."""
        if self.satisfaction < 0:
            self.satisfaction += 1
        elif self.wealth <= self.salary:
            self.satisfaction += rng.randint(0, 1)
        else:
            self.satisfaction += rng.randint(1, 2)

    def salary_raise_penalty(self, rng: Rng) -> None:
        """Satisfaction drop when a raise is declined (gamelogic.md Salary raise penalties)."""
        self.satisfaction -= rng.randint(int(_PR.raise_penalty_min), int(_PR.raise_penalty_max))

    # --- salary and retention ------------------------------------------------

    def salary_demand_probability(self) -> float:
        """Probability of a salary demand on each monthly check."""
        divisor = 10 - self.salary_trait / 10
        if divisor <= 0:
            return 1.0
        return 1.0 / divisor

    def loyalty_threshold(self) -> float:
        """Years of service needed before the person considers leaving."""
        return max(0.0, _PR.loyalty_base - (self.salary_trait + self.trait7) / 4.0)

    def wants_raise(self) -> bool:
        """January wealth comparison: wealth > salary * 1.1."""
        return self.wealth > self.salary * _PR.raise_wealth_ratio

    def compute_target_salary(self) -> float:
        """Target salary for negotiation based on years of service."""
        return self.salary * (1.0 + self.years_of_service * _PR.service_salary_factor)

    def random_raise_probability(self) -> float:
        """Monthly random raise trigger probability: 1 / (150 - performance_score)."""
        divisor = _PR.random_raise_base - self.performance_score
        if divisor <= 0:
            return 1.0
        return 1.0 / divisor

    # --- hiring acceptance ---------------------------------------------------

    def acceptance_threshold(self) -> int:
        """Threshold for accepting a job offer (gamelogic.md Acceptance check)."""
        return self.acceptance_trait // 2 - 100

    def would_accept_hire(self) -> bool:
        return self.satisfaction >= self.acceptance_threshold()

    # --- competitor spawning -------------------------------------------------

    def can_spawn_competitor(self, day_serial: int, competitor_count: int, cap: int) -> bool:
        """Whether this independent investor can found a company today."""
        if self.state != STATE_ACTIVE or self.role != ROLE_INDEPENDENT:
            return False
        if self.cooldown > 0:
            return False
        return competitor_count < cap and competitor_count < int(_PR.max_competitors)

    # --- lifecycle -----------------------------------------------------------

    def link_to_corp(self, corp_id: int, as_ceo: bool = True) -> None:
        self.corp_id = corp_id
        self.state = STATE_LINKED
        if as_ceo:
            self.role = ROLE_CEO
        else:
            self.role = ROLE_PRESIDENT

    def unlink(self) -> None:
        self.corp_id = None
        self.state = STATE_ACTIVE
        self.role = ROLE_INDEPENDENT
        self.years_of_service = 0

    def retire(self) -> None:
        self.state = STATE_RETIRED
        self.role = ROLE_RETIRED
        self.corp_id = None

    # --- traits randomization ------------------------------------------------

    def randomize_traits(self, rng: Rng) -> None:
        """Randomize the 5 active personality traits (gamelogic.md Personality traits)."""
        self.salary_trait = rng.randint(20, 99)
        self.trait7 = rng.randint(0, 99)
        self.expansion_trait = rng.randint(20, 99)
        self.acceptance_trait = rng.randint(0, 99)

    def randomize_character(self, rng: Rng, setting: int | None = None) -> None:
        """Set character type based on game setting.

        setting: None=random, 0-3=specific type, -1=pre-defined.
        """
        if setting is None or setting == -1:
            self.character_type = rng.randint(CHAR_CONSERVATIVE, CHAR_VERY_AGGRESSIVE)
        else:
            self.character_type = max(CHAR_CONSERVATIVE, min(CHAR_VERY_AGGRESSIVE, setting))

    def randomize_gender(self, rng: Rng) -> None:
        self.gender = rng.randint(0, 1)
