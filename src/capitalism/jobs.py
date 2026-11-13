"""Jobs: plain daily work units in firm slots, research and import supplies."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .catalog import Crop, Product, Software
from .projects import Project, ProjectEngine
from .tables import (
    ADVERTISING_RULES,
    FIXED_TRAINING_CREDITS,
    JOB_RULES,
    JOB_TYPES,
    LINK_RULES,
    LIVESTOCK_HERD_RATES,
    LIVESTOCK_YIELDS,
    RATING_THROUGHPUT,
    RAW_RESOURCE_TYPES,
    RESEARCH_RULES,
    SOFTWARE_RULES,
    JobTypeRow,
    RecipeRow,
)

if TYPE_CHECKING:
    from .economy import Economy
    from .firms import Firm, MediaFirm
    from .links import Link

CAT_SALES, CAT_SALARIES, CAT_OVERHEAD, CAT_TRAINING = 0, 1, 2, 3
CAT_PURCHASE, CAT_FREIGHT, CAT_ADVERTISING, CAT_WRITEOFFS = 4, 5, 6, 7
CAT_RAW_MATERIAL, CAT_LOAN_INTEREST, CAT_STOCK_RETURN, CAT_LAND_VALUE = 8, 9, 10, 11


def job_wage_day(staff: int, labor_cost: float, days_in_month: int) -> int:
    """Reference wage posted once per job per day, not once per worker."""
    labor = round(labor_cost)
    return ((staff * JOB_RULES.wage_per_worker_month) // days_in_month * labor) // 100


def efficiency(rating: int, labor_quality: float) -> float:
    """Reference rating percent; staff quality is not applied again."""
    return RATING_THROUGHPUT[max(1, min(9, rating))].efficiency_pct


class Job:
    type_id = 0
    rank = 0
    __slots__ = (
        "brand",
        "firm",
        "param1",
        "param2",
        "price",
        "product",
        "quality",
        "rating",
        "row",
        "slot",
        "staff",
        "stock",
        "train_credits",
        "train_progress",
        "unit_cost",
    )

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        self.firm, self.slot = firm, slot
        self.row: JobTypeRow = JOB_TYPES[self.type_id]
        self.product, self.rating = product, rating
        self.staff = self.row.staff
        self.stock = self.quality = self.unit_cost = 0.0
        self.price = product.row.base_price if product is not None else 0.0
        self.brand = -1
        self.train_credits = 0.0
        self.train_progress = 0
        self.param1 = self.param2 = 0

    def __repr__(self) -> str:
        p = self.product.name if self.product else None
        return f"{type(self).__name__}(slot={self.slot}, product={p!r}, stock={self.stock:.1f})"

    @property
    def capacity(self) -> float:
        if self.product is None:
            return 0.0
        return self.product.row.base_capacity * self.firm.size * self.row.cap_mult

    @property
    def ceiling(self) -> float:
        """Storage ceiling = capacity × storage_mult (decomp:61852-61856)."""
        return self.capacity * RATING_THROUGHPUT[max(1, min(9, self.rating))].storage_mult

    @property
    def room(self) -> float:
        return max(0.0, self.ceiling - self.stock)

    @property
    def efficiency(self) -> float:
        return efficiency(self.rating, self.firm.town.labor_quality)

    def available_stock(self) -> float:
        return self.stock

    def produced_quality(self) -> float:
        return (self.rating - 1) * JOB_RULES.quality_per_rating + JOB_RULES.quality_base

    def receive(self, qty: float, quality: float, unit_cost: float) -> None:
        if qty <= 0:
            return
        total = self.stock + qty
        self.quality = (self.quality * self.stock + quality * qty) / total
        self.unit_cost = (self.unit_cost * self.stock + unit_cost * qty) / total
        self.stock = total

    def take(self, qty: float) -> float:
        qty = max(0.0, min(qty, self.stock))
        self.stock -= qty
        return qty

    def feeds(self, other: Job) -> bool:
        return self.product is not None and self.product is other.product and self.rank < other.rank

    def sources(self) -> list[Job]:
        return [j for j in self.firm.linked_jobs(self.slot) if j.feeds(self)]

    def post_wages(self, eco: Economy) -> None:
        if self.staff:
            wage = job_wage_day(self.staff, self.firm.town.labor_cost, eco.calendar.real_month_days)
            self.firm.post(CAT_SALARIES, wage)
            training_budget = (
                self.firm.owner.training_budget
                if self.firm.owner is not None
                else JOB_RULES.corp_training_budget_default
            )
            self.firm.post(
                CAT_TRAINING, training_budget * wage / JOB_RULES.training_expense_divisor
            )
        if eco.calendar.weekday == JOB_RULES.train_weekday:
            self.train()

    def _credit(self, raw: float) -> None:
        """Scale raw points by budget/100 × education/100, then accumulate (decomp:60780)."""
        if raw <= 0.0:
            return
        budget = (
            JOB_RULES.corp_training_budget_default
            if self.firm.owner is None
            else self.firm.owner.training_budget
        )
        education = JOB_RULES.training_education_default
        self.train_credits += (raw * budget // 100) * education // 100

    def fixed_visit_credit(self) -> None:
        """Only database-listed fixed-credit job types enter here."""
        row = FIXED_TRAINING_CREDITS.get(self.type_id)
        if row is not None:
            self._credit(row.base_daily * self.efficiency / 100.0)

    def train(self) -> None:
        """Weekday 2: one staff-count step on strict credits > rating×900; clear to 0."""
        r = JOB_RULES
        if self.train_credits > max(1, self.rating) * 900:
            self.train_credits = 0.0
            self.train_progress += 1
            if self.train_progress >= self.staff:
                self.train_progress = 0
                if self.rating < r.rating_max:
                    self.rating += 1

    def work(self, eco: Economy) -> bool:
        return False

    def pull(self, eco: Economy) -> None:
        for src in self.sources():
            room = self.room
            if room <= 0:
                break
            moved = src.take(min(room, src.available_stock()))
            if moved > 0:
                self.receive(moved, src.quality, src.unit_cost)
                self.on_moved(src, moved)

    def on_moved(self, src: Job, moved: float) -> None:
        pass

    def monthly(self, eco: Economy) -> None:
        if self.product is not None and self.product.decays and self.stock > 0:
            self.quality *= self.product.cls.quality_decay_base
        # J2: write-off when ceiling shrinks below stock (decomp:61857-61861)
        ceil = self.ceiling
        if self.stock > ceil >= 0:
            excess = self.stock - ceil
            self.firm.post(CAT_WRITEOFFS, excess * self.unit_cost)
            self.stock = ceil


class CropGrowing(Job):
    type_id = 1
    __slots__ = ()

    def yield_factor(self) -> float:
        r, tile = JOB_RULES, self.firm.tile
        row = self.product.row if self.product else None
        if row is None or row.suit_climate is None or row.suit_moisture is None:
            return 0.0
        cd, md = (
            abs(tile.climate - row.suit_climate),
            abs(tile.moisture - row.suit_moisture) / r.crop_moisture_step,
        )
        return max(
            0,
            cd * r.crop_climate_slope
            + r.crop_yield_base
            + md * r.crop_moisture_slope
            + r.crop_yield_base
            + tile.soil / r.crop_soil_div,
        )

    def daily_growth(self) -> float:
        return self.efficiency * self.capacity * self.yield_factor() / 10_000

    def work(self, eco: Economy) -> bool:
        p = self.product
        if not isinstance(p, Crop) or not p.in_season(eco.calendar.month - 1):
            return False
        step = self.daily_growth()
        added = min(self.room, step)
        if added > 0:
            self.fixed_visit_credit()
        self.receive(added, self.produced_quality(), p.row.base_cost)
        return self.stock >= self.ceiling


class LivestockRaising(Job):
    """Two-pool herd model (native FUN_000528ec, decomp:52303-52339).

    Per-livestock GROW and REPRODUCE rates from 1STD.SET FARMLIVE table.
    Formula divisors: 36500.0 (``livestock_scalar``, EXE 0xa768e) and
    100.0 (EXE 0xa7692).  Stock = round(young).
    """

    type_id = 2
    __slots__ = ("grown", "young")

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        self.young = 0.0
        self.grown = 0.0

    def work(self, eco: Economy) -> bool:
        if self.product is None:
            return False
        herd = LIVESTOCK_HERD_RATES.get(self.product.id)
        if herd is None:
            return False
        scalar = JOB_RULES.livestock_scalar
        eff = self.efficiency
        ceil = self.ceiling
        matured = herd.grow_rate * self.young / scalar * eff / 100.0
        if self.grown + matured > ceil:
            matured = ceil - self.grown
        self.young -= matured
        self.grown += matured
        born = herd.reproduce_rate * self.grown / scalar * eff / 100.0
        self.young += born
        self.young = min(self.young, ceil)
        self.stock = round(self.young)
        if self.young > 0 and self.stock > 0:
            self.quality = self.produced_quality()
            self.unit_cost = self.product.row.base_cost
            self.fixed_visit_credit()
        return False

    def available_stock(self) -> float:
        return self.grown

    def take(self, qty: float) -> float:
        qty = max(0.0, min(qty, self.grown))
        self.grown -= qty
        return qty


class Extraction(Job):
    type_id = 8
    __slots__ = ("rate",)

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        if product is not None and product.id in RAW_RESOURCE_TYPES:
            self.rate: float = float(RAW_RESOURCE_TYPES[product.id].speed)
        else:
            self.rate: float = JOB_RULES.extraction_rate

    def work(self, eco: Economy) -> bool:
        if self.product is None:
            return False
        firm = self.firm
        if hasattr(firm, "reserve") and firm.reserve <= 0:
            return False
        step = self.efficiency * self.rate * self.capacity / 100
        added = min(self.room, step)
        if added > 0 and step > 0:
            self._credit(added * 100.0 / step)
        self.receive(added, self.produced_quality(), self.product.row.base_cost)
        if hasattr(firm, "reserve") and firm.reserve > 0 and added > 0:
            draw = added / self.capacity / self.rate / 100.0
            draw = min(draw, firm.reserve)
            firm.reserve -= draw
            if firm.reserve <= 0:
                firm.reserve = 0.0
                return True
        return self.stock >= self.ceiling


class Logging(Extraction):
    type_id = 4
    __slots__ = ()


class Mining(Extraction):
    type_id = 8
    __slots__ = ()


class OilExtraction(Extraction):
    type_id = 9
    __slots__ = ()


def cycle_quality(recipe: RecipeRow, input_quality: dict[int, float], skill: float) -> float:
    weighted = sum(input_quality.get(i.input_id, 0.0) * i.quality_weight for i in recipe.inputs)
    return (weighted + skill * recipe.skill_weight) / 100.0


class Manufacturing(Job):
    type_id = 7
    __slots__ = ("inputs", "job_tech")

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        self.inputs: dict[int, list[float]] = {}
        self.job_tech: int = 0

    def skill(self) -> float:
        """Per-job tech (catching up weekly to corp level), plus manager skill."""
        if self.product is None or self.firm.owner is None:
            return 0.0
        manager = self.firm.owner.manufacturing_skill
        skill = manager / RESEARCH_RULES.manager_skill_divisor + self.job_tech
        return min(JOB_RULES.mfg_skill_max, skill)

    def _weekly_tech_upgrade(self, eco: Economy) -> None:
        """decomp:54813-54864: once per week, job tech catches up to corp tech."""
        if eco.calendar.day_serial % 7 != self.firm.id % 7:
            return
        if self.product is None or self.firm.owner is None:
            return
        corp_tech = self.firm.owner.technology_level(self.product)
        if self.job_tech < corp_tech:
            self.job_tech += 1

    def cycles_per_day(self, recipe: RecipeRow) -> int:
        return int(
            (self.capacity * self.efficiency / 100 * recipe.speed_pct / 100) // recipe.output_qty
        )

    def work(self, eco: Economy) -> bool:
        self._weekly_tech_upgrade(eco)
        p = self.product
        if p is None or self.room <= 0 or (recipe := eco.catalog.recipe(p)) is None:
            return False
        cycles = min(self.cycles_per_day(recipe), int(self.room // recipe.output_qty))
        done = _consume_cycles(self.inputs, recipe.inputs, cycles)
        if done:
            quals = {i.input_id: self.inputs[i.input_id][1] for i in recipe.inputs}
            material = sum(i.qty * self.inputs[i.input_id][2] for i in recipe.inputs) * done
            wages = job_wage_day(
                self.staff, self.firm.town.labor_cost, eco.calendar.real_month_days
            )
            units = done * recipe.output_qty
            self.receive(
                units, cycle_quality(recipe, quals, self.skill()), (material + wages) / units
            )
            nominal = self.efficiency * self.capacity * recipe.speed_pct / 10000.0
            self._credit(units * 100.0 / nominal)
        return True

    def pull(self, eco: Economy) -> None:
        p = self.product
        recipe = eco.catalog.recipe(p) if p is not None else None
        if recipe is None:
            return
        cycles, weekday0 = self.cycles_per_day(recipe), eco.calendar.weekday == 0
        for i in recipe.inputs:
            buf = self.inputs.setdefault(i.input_id, [0.0, 0.0, 0.0])
            for src in self.firm.linked_jobs(self.slot):
                if isinstance(src, Sales) or src.product is None or src.product.id != i.input_id:
                    continue
                need = i.qty * cycles - buf[0]
                if need <= 0:
                    break
                if not (src.stock >= src.capacity or weekday0):
                    continue
                moved = src.take(min(src.available_stock(), need))
                if moved > 0:
                    total = buf[0] + moved
                    buf[1] = (buf[1] * buf[0] + src.quality * moved) / total
                    buf[2] = (buf[2] * buf[0] + src.unit_cost * moved) / total
                    buf[0] = total


class LivestockProcessing(Job):
    """Continuous livestock conversion; yields and conversion ratio are provisional db rows."""

    type_id = 3
    __slots__ = ("month_output",)

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        self.month_output = 0.0

    def source_jobs(self) -> list[Job]:
        if self.product is None:
            return []
        return [j for j in self.firm.linked_jobs(self.slot) if isinstance(j, LivestockRaising)]

    def yield_for(self, src: LivestockRaising):
        if self.product is None or src.product is None:
            return None
        row = LIVESTOCK_YIELDS.get(src.product.id)
        return row if row is not None and row.product_id == self.product.id else None

    def work(self, eco: Economy) -> bool:
        src = next((j for j in self.source_jobs() if self.yield_for(j) is not None), None)
        if src is None:
            return False
        row = self.yield_for(src)
        assert row is not None
        wanted = self.efficiency * self.capacity * row.yield_factor / 10_000
        raw = min(src.available_stock(), wanted, self.room)
        if raw > 0:
            self.take_from(src, raw)
            self.month_output += raw
            self._credit(round(raw * 17.0 / self.capacity))
        return False

    def take_from(self, src: Job, raw: float) -> None:
        src.take(raw)
        quality = min(src.quality + (src.rating - 1) * 4, 100)
        self.receive(raw, quality, src.unit_cost)

    def monthly(self, eco: Economy) -> None:
        super().monthly(eco)
        self.month_output = 0.0


def product_freight_rate(product: Product, seller: Firm, buyer: Firm) -> float:
    """Decompiled FUN_000785f1: coefficient × distance × value / 100² × 0.5.

    Only a zero raw rate uses the $0.01/unit floor. Positive sub-cent rates stay exact.
    """
    r = JOB_RULES
    dx, dy = seller.x - buyer.x, seller.y - buyer.y
    distance = math.isqrt(dx * dx + dy * dy)
    raw = (
        product.row.freight
        * distance
        * product.row.spending_usd
        / r.freight_distance_value_divisor**2
        * r.freight_multiplier
    )
    return r.freight_floor_usd_per_unit if raw == 0 else raw


class Purchasing(Job):
    type_id = 10
    __slots__ = ("freight_month", "received_month", "supply")

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        self.supply: Link | None = None
        self.received_month = [0.0] * 12
        self.freight_month = [0.0] * 12

    def work(self, eco: Economy) -> bool:
        r, link = JOB_RULES, self.supply
        if (
            self.product is None
            or link is None
            or self.slot % r.purchase_every_days != eco.calendar.day_serial % r.purchase_every_days
            or self.stock >= self.ceiling
        ):
            return False
        order = self.efficiency * self.capacity * r.purchase_order_mult / 100
        link.quantity = order
        seller = link.seller
        receipt = min(order, self.room, seller.available_stock())
        if receipt <= 0:
            return False
        price, quality = link.price, seller.quality
        seller.sell_to(receipt, link)
        self.receive(receipt, quality, price)
        rate = product_freight_rate(self.product, seller.firm, self.firm)
        charge = rate * receipt
        self.firm.post(CAT_FREIGHT, charge)
        month = eco.calendar.month - 1
        self.received_month[month] += receipt
        self.freight_month[month] += charge
        self._credit(receipt * 80.0 / order)
        return False


class ImportJob(Job):
    """A numbered supply link, not occupancy of a nine-slot building grid."""

    type_id = 16
    __slots__ = ()

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        self.quality, self.unit_cost = JOB_RULES.import_quality, product.row.base_price

    def available_stock(self) -> float:
        return math.inf if self.product is not None else 0.0

    def take(self, qty: float) -> float:
        return max(0.0, qty)

    def sell_to(self, qty: float, link: Link) -> None:
        link.record_sale(qty)


class Inventory(Job):
    type_id = 5
    rank = 1
    __slots__ = ()

    def work(self, eco: Economy) -> bool:
        return True


class PrivateLabelling(Job):
    type_id = 6
    rank = 2
    __slots__ = ()

    def work(self, eco: Economy) -> bool:
        return True

    def on_moved(self, src: Job, moved: float) -> None:
        if self.capacity > 0:
            self._credit(moved * 18.0 / self.capacity)
        if self.firm.owner is not None:
            self.brand = self.firm.owner.id


class Sales(Job):
    type_id = 12
    rank = 3
    __slots__ = ("sell_left",)

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        self.sell_left = 0.0

    def daily_cap(self) -> float:
        mult = (
            JOB_RULES.sales_mult_store
            if self.firm.row.live_inventory
            else JOB_RULES.sales_mult_other
        )
        return self.efficiency * mult * self.capacity / 100

    def work(self, eco: Economy) -> bool:
        if self.product is None:
            return True
        self.sell_left = self.daily_cap()
        return self.stock < self.ceiling

    def sell_to(self, qty: float, link: Link) -> None:
        qty = self.take(qty)
        if qty <= 0:
            return
        self.sell_left = max(0.0, self.sell_left - qty)
        if self.daily_cap() > 0:
            self._credit(qty * 100.0 / self.daily_cap())
        self.firm.post(CAT_SALES, qty * link.price)
        if self.firm.posts_purchase_cost:
            self.firm.post(CAT_PURCHASE, qty * self.unit_cost)
        link.record_sale(qty)

    def consumer_cap(self) -> float:
        return min(self.sell_left, self.stock)


class ProjectJob(Job):
    """Shared one active project per research/software-development slot."""

    software_project = False
    __slots__ = ("completed_count", "paused", "project")

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        if product is None or (self.software_project and not isinstance(product, Software)):
            raise ValueError(f"{self.row.name} requires a valid target product")
        self.paused = False
        self.project: Project | None = None
        self.completed_count = 0

    def configure(
        self,
        product: Product | None = None,
        *,
        repeat: bool = False,
        funded: bool = True,
        serial: int = 0,
    ) -> Project:
        target = self.product if product is None else product
        if self.project is not None:
            raise ValueError("one active project per slot")
        if target is None or (self.software_project and not isinstance(target, Software)):
            raise ValueError(f"{self.row.name} requires a valid target product")
        self.product = target
        self.paused = False
        self.param1, self.param2 = int(repeat), int(funded)
        self.project = Project(target)
        self.project.repeat, self.project.funded = int(repeat), funded
        return self.project

    def repeat(self) -> Project:
        """Clear a completed one-shot and explicitly start the next level."""
        if self.project is None or self.project.started:
            raise ValueError("only a completed project can repeat")
        self.project = None
        return self.configure(repeat=True)

    def work(self, eco: Economy) -> bool:
        if self.project is None:
            return False
        self.project.funded = bool(self.param2)
        self.project.paused = self.paused
        ProjectEngine.work(self, eco)
        self.fixed_visit_credit()
        return False


class Research(ProjectJob):
    type_id = 11
    __slots__ = ()


class SoftwareDevelopment(ProjectJob):
    """M1 provisional: one generic catalog `Software` title; no per-title choice yet."""

    type_id = 13
    software_project = True
    __slots__ = ()

    def complete_project(self, product: Product, eco: Economy) -> None:
        assert self.firm.owner is not None
        self.firm.owner.add_technology(product)
        self.receive(1, SOFTWARE_RULES.software_copy_quality, self.unit_cost)


class SoftwareProduction(Job):
    """Binary FUN_0005bf73 (produce) + FUN_0005c06f (gate)."""

    type_id = 14
    rank = 1
    __slots__ = ("has_master", "production_started_serial", "revenue_months")

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        self.has_master = False
        self.production_started_serial = 0
        self.revenue_months: list[float] = [0.0] * 12

    def add_master(self, development: SoftwareDevelopment) -> None:
        if development.product is not self.product:
            raise ValueError("development and production targets differ")
        if (
            development.stock >= 1
            and self.firm.owner is not None
            and self.firm.owner.has_technology(development.product)
        ):
            self.quality, self.unit_cost = development.quality, development.unit_cost
            if not self.has_master:
                self.has_master = True

    def _gate_check(self, eco: Economy) -> None:
        """Binary FUN_0005c06f: every 15 days, drop stale products."""
        r = SOFTWARE_RULES
        if (eco.calendar.day_serial + self.firm.id) % r.software_gate_every_days != 0:
            return
        if not self.has_master or self.product is None:
            return
        age = eco.calendar.day_serial - self.production_started_serial
        if age <= r.software_gate_max_age_days:
            return
        window = r.software_gate_no_revenue_months
        recent_revenue = (
            sum(self.revenue_months[-window:])
            if window <= len(self.revenue_months)
            else sum(self.revenue_months)
        )
        if recent_revenue > 0:
            return
        new_product = self._select_new_product(eco)
        if new_product is not None:
            self.product = new_product
            self.has_master = False
            self.stock = 0.0
            self.production_started_serial = eco.calendar.day_serial
            self.revenue_months = [0.0] * 12

    def _select_new_product(self, eco: Economy) -> Product | None:
        """Binary FUN_0005c121: pick a software-eligible product where demand > supply."""
        best = None
        best_gap = 0.0
        for p in eco.catalog.products:
            if not isinstance(p, Software):
                continue
            if p is self.product:
                continue
            demand = sum(tm.demand_per_day for tm in eco.market.towns.values() if tm.product is p)
            supply = sum(
                j.stock
                for f in eco.firms
                if f is not None
                for j in f.jobs()
                if j.product is p and isinstance(j, Sales)
            )
            gap = demand - supply
            if gap > best_gap:
                best_gap = gap
                best = p
        return best

    def work(self, eco: Economy) -> bool:
        self._gate_check(eco)
        if (
            not self.has_master
            or self.product is None
            or self.firm.owner is None
            or not self.firm.owner.has_technology(self.product)
        ):
            return False
        if self.production_started_serial == 0:
            self.production_started_serial = eco.calendar.day_serial
        nominal = self.efficiency * self.capacity
        added = min(self.room, nominal)
        if added > 0 and nominal > 0:
            self._credit(added * 100.0 / nominal)
        self.receive(added, self.quality, self.product.row.base_cost)
        return self.stock < self.ceiling

    def pull(self, eco: Economy) -> None:
        for job in self.firm.linked_jobs(self.slot):
            if (
                isinstance(job, SoftwareDevelopment)
                and job.product is self.product
                and job.stock >= 1
            ):
                self.add_master(job)
                return

    def monthly(self, eco: Economy) -> None:
        super().monthly(eco)
        month_revenue = self.firm.ledger.last_month[0] if self.firm else 0.0
        self.revenue_months = self.revenue_months[1:] + [month_revenue]


def qualifies_media(media: MediaFirm) -> bool:
    """Binary FUN_0005116d: audience > 5.0 (_DAT_000a7518)."""
    return media.audience > ADVERTISING_RULES.media_min_audience


class Advertising(Job):
    type_id = 15
    rank = 4
    __slots__ = ("budget", "media", "targets")

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        self.budget, self.media = 0.0, None
        self.targets: dict[int, float] = {}

    def attach_media(self, media: MediaFirm) -> None:
        if media.town.id != self.firm.town.id:
            raise ValueError("advertising partner must be in the same town")
        self.media = media

    def specify_media(self, media: MediaFirm, budget: float) -> None:
        """Commit a financed campaign to a media firm already meeting the threshold."""
        if not qualifies_media(media):
            raise ValueError("media partner has not passed the audience threshold")
        self.attach_media(media)
        self.budget = max(0.0, budget)

    def commit_campaign(self, eco: Economy) -> None:
        if self.media is None or self.firm.town.id != self.media.town.id:
            raise ValueError("campaign needs a media partner in the same town")
        if self.budget <= 0:
            return
        self.firm.post(CAT_ADVERTISING, self.budget)
        self.media.post(CAT_SALES, self.budget, direct=True)
        self.media.advertisers.add(self.firm.id)
        product = next(
            (s.product for s in self.firm.jobs() if isinstance(s, Sales) and self.qualifying(s)),
            None,
        )
        if product is not None:
            self.product = product
            self.targets[product.id] = self.budget
            # Sim-specific: native FUN_0005136e selects products/budgets but does
            # NOT directly increment awareness; the sim adds a per-campaign gain.
            corp = self.firm.owner
            if corp is not None:
                from .links import BrandRecord, brand_key

                bk = brand_key(corp, product, eco.catalog)
                gain = LINK_RULES.ad_brand_per_100k * self.budget / 100_000
                for link in eco.market.live_links():
                    if (
                        link.live
                        and link.seller.firm is self.firm
                        and link.product is product
                        and link.seller.stock > 0
                    ):
                        key = (link.buyer.town.id, bk)
                        rec = eco.market.brand_records.get(key)
                        if rec is None:
                            rec = BrandRecord()
                            eco.market.brand_records[key] = rec
                        aw = rec.awareness.get(corp.id, 0.0)
                        rec.awareness[corp.id] = min(100.0, aw + gain)

    def qualifying(self, sales: Sales) -> bool:
        return (
            sales.product is not None
            and sales.product.state.tech_level > ADVERTISING_RULES.ad_tech_min_exclusive
        )

    def work(self, eco: Economy) -> bool:
        if (eco.calendar.day_serial + self.firm.id) % ADVERTISING_RULES.ad_campaign_every_days == 0:
            eligible = [s for s in self.firm.jobs() if isinstance(s, Sales) and self.qualifying(s)]
            if not eligible:
                self.budget = 0.0
                return False
            if self.media is None or not qualifies_media(self.media):
                candidates = [f for f in eco.media_firms(self.firm.town) if qualifies_media(f)]
                self.media = candidates[0] if candidates else None
            if self.media is None:
                self.budget = 0.0
                return False
            self.budget = min(
                JOB_RULES.ad_budget_max,
                max(
                    JOB_RULES.ad_budget_min,
                    ADVERTISING_RULES.ad_revenue_fraction * self.firm.ledger.last_month[CAT_SALES],
                ),
            )
            self.commit_campaign(eco)
        return False


JOB_CLASSES: dict[int, type[Job]] = {
    c.type_id: c
    for c in (
        CropGrowing,
        LivestockRaising,
        LivestockProcessing,
        Logging,
        Inventory,
        PrivateLabelling,
        Manufacturing,
        Mining,
        OilExtraction,
        Purchasing,
        Research,
        Sales,
        SoftwareDevelopment,
        SoftwareProduction,
        Advertising,
        ImportJob,
    )
}

__all__ = [
    "CAT_ADVERTISING",
    "JOB_CLASSES",
    "Advertising",
    "CropGrowing",
    "Extraction",
    "ImportJob",
    "Inventory",
    "Job",
    "LivestockProcessing",
    "LivestockRaising",
    "Logging",
    "Manufacturing",
    "Mining",
    "OilExtraction",
    "PrivateLabelling",
    "Purchasing",
    "Research",
    "Sales",
    "SoftwareDevelopment",
    "SoftwareProduction",
    "cycle_quality",
    "efficiency",
    "job_wage_day",
]


def _consume_cycles(stock: dict, inputs, cycles: int) -> int:
    """Run up to ``cycles`` production cycles, taking each input's ``qty`` per cycle.

    Same result as checking and subtracting one cycle at a time. When every
    stock and qty is a whole number (exact in float), the count and the
    remaining stock are computed in one step; otherwise it falls back to the
    per-cycle loop so float results match bit for bit.
    """
    if cycles <= 0:
        return 0
    exact = True
    done = cycles
    for i in inputs:
        entry = stock.get(i.input_id)
        have = entry[0] if entry is not None else 0.0
        q = i.qty
        if not (
            q > 0
            and float(have).is_integer()
            and float(q).is_integer()
            and abs(have) < 2**52
            and q < 2**52
        ):
            exact = False
            break
        n = int(have // q) if have >= q else 0
        done = min(done, n)
    if exact:
        if done:
            for i in inputs:
                stock[i.input_id][0] -= i.qty * done
        return done
    done = 0
    for _ in range(cycles):
        if any(stock.get(i.input_id, (0.0,))[0] < i.qty for i in inputs):
            break
        done += 1
        for i in inputs:
            stock[i.input_id][0] -= i.qty
    return done
