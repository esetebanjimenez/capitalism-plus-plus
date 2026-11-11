"""Plans: reusable firm layout templates (gamelogic.md Plan system).

A plan stores a 9-slot job configuration with connection wiring that can
be captured from a firm and applied to build or reconfigure another firm
of the same type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .firms import Firm
from .jobs import JOB_CLASSES, Sales

if TYPE_CHECKING:
    from .economy import Economy

MAX_DESCRIPTION = 28
MAX_SLOTS = 9
MAX_DEMAND_PRODUCTS = 4
INVALID_SCORE = -1000
UNCONTESTED_SCORE = 10_000


class PlanSlot:
    """One of nine job slots in a plan template."""

    __slots__ = ("job_type", "param1", "param2", "product_id")

    def __init__(
        self,
        job_type: int = 0,
        product_id: int = 0,
        param1: int = 0,
        param2: int = 0,
    ) -> None:
        self.job_type = job_type
        self.product_id = product_id
        self.param1 = param1
        self.param2 = param2

    @property
    def empty(self) -> bool:
        return self.job_type == 0

    def __repr__(self) -> str:
        if self.empty:
            return "PlanSlot()"
        return f"PlanSlot(job={self.job_type}, prod={self.product_id})"


class Plan:
    """A firm layout template — 9 job slots plus connection wiring.

    In the binary the in-memory record is 127 bytes; on disk (in .PLA
    files) each plan serializes to 72 bytes (9 × 8-char product codes).
    """

    __slots__ = (
        "connection_mask",
        "demand_products",
        "description",
        "firm_type",
        "slots",
        "valid",
    )

    def __init__(
        self,
        description: str = "",
        firm_type: int = 0,
        valid: bool = False,
        connection_mask: int = 0,
    ) -> None:
        self.description = description[:MAX_DESCRIPTION]
        self.firm_type = firm_type
        self.valid = valid
        self.connection_mask = connection_mask
        self.slots: list[PlanSlot] = [PlanSlot() for _ in range(MAX_SLOTS)]
        self.demand_products: list[int] = []

    def __repr__(self) -> str:
        n_jobs = sum(1 for s in self.slots if not s.empty)
        return f"Plan({self.description!r}, type={self.firm_type}, jobs={n_jobs})"

    def recompute_demand(self) -> None:
        """Scan Sales-type slots and collect up to 4 unique product IDs."""
        seen: set[int] = set()
        products: list[int] = []
        for slot in self.slots:
            if (
                slot.job_type == Sales.type_id
                and slot.product_id != 0
                and slot.product_id not in seen
                and len(products) < MAX_DEMAND_PRODUCTS
            ):
                seen.add(slot.product_id)
                products.append(slot.product_id)
        self.demand_products = products

    def score(self, eco: Economy) -> int:
        """Evaluate market opportunity (gamelogic.md Plan scoring)."""
        if not self.valid:
            return INVALID_SCORE
        if not self.demand_products:
            return INVALID_SCORE

        total_score = 0
        for pid in self.demand_products:
            supply = 0.0
            for link in eco.market.live_links():
                if link.product.id == pid:
                    supply += link.quantity
            if supply == 0:
                return UNCONTESTED_SCORE
            total_score += int(supply)

        return max(0, UNCONTESTED_SCORE - total_score)

    def revenue_estimate(self, eco: Economy) -> float:
        """Estimate revenue from demand products' market data."""
        total = 0.0
        for pid in self.demand_products:
            for tm in eco.market.towns.values():
                if tm.product.id == pid:
                    total += tm.demand_per_day * 30
        return total


def capture(firm: Firm) -> Plan:
    """Read a firm's current job configuration into a plan (gamelogic.md Plan capture)."""
    plan = Plan(
        description=f"{firm.row.name}",
        firm_type=firm.type_id,
        valid=True,
        connection_mask=firm.links,
    )
    for i, job in enumerate(firm.slots[:MAX_SLOTS]):
        if job is None:
            continue
        slot = plan.slots[i]
        slot.job_type = job.type_id
        slot.product_id = job.product.id if job.product is not None else 0
        slot.param1 = 0
        slot.param2 = 0
    plan.recompute_demand()
    return plan


def apply_plan(plan: Plan, firm: Firm, eco: Economy) -> None:
    """Apply a plan to a firm, creating all 9 job slots (gamelogic.md Plan apply).

    Raises ValueError if the firm type does not match or the plan is invalid.
    """
    if not plan.valid:
        raise ValueError("cannot apply an invalid plan")
    if plan.firm_type != firm.type_id:
        raise ValueError(
            f"plan is for firm type {plan.firm_type}, "
            f"but firm is type {firm.type_id}"
        )

    firm.links = plan.connection_mask
    for i in range(MAX_SLOTS):
        firm.slots[i] = None

    catalog = eco.catalog
    for i, ps in enumerate(plan.slots):
        if ps.empty:
            continue
        if ps.job_type not in JOB_CLASSES:
            continue
        product = catalog.by_id.get(ps.product_id) if ps.product_id else None
        firm.add_job(i, ps.job_type, product)


class PlanFolder:
    """A named collection of plans for one firm-type category."""

    __slots__ = ("name", "plans")

    def __init__(self, name: str) -> None:
        self.name = name
        self.plans: list[Plan] = []

    def add(self, plan: Plan) -> int:
        self.plans.append(plan)
        return len(self.plans) - 1

    def delete(self, index: int) -> None:
        if 0 <= index < len(self.plans):
            del self.plans[index]

    def best(self, eco: Economy) -> Plan | None:
        """Return the plan with the highest market opportunity score."""
        best_plan = None
        best_score = INVALID_SCORE
        for plan in self.plans:
            s = plan.score(eco)
            if s > best_score:
                best_score = s
                best_plan = plan
        return best_plan


class PlanLibrary:
    """Two plan collections: factory/manufacturing and store/retail.

    The binary keeps these as two dynamic arrays on a global plan object
    (DAT_000b233b for factory, DAT_000b2366 for store).
    """

    __slots__ = ("factory", "store")

    def __init__(self) -> None:
        self.factory = PlanFolder("FACT")
        self.store = PlanFolder("RETA")

    def folder_for(self, firm_type: int) -> PlanFolder:
        """Return the appropriate folder based on firm type.

        Department stores (1) and restaurants (10) go to the store folder;
        everything else goes to the factory folder.
        """
        if firm_type in (1, 10):
            return self.store
        return self.factory
