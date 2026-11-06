"""Jobs: plain daily work units in firm slots, research and import supplies."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .catalog import Crop, Product, Software
from .projects import Project, ProjectEngine
from .tables import (
    ADVERTISING_RULES,
    JOB_RULES,
    JOB_TYPES,
    LINK_RULES,
    LIVESTOCK_YIELDS,
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
CAT_PURCHASE, CAT_FREIGHT, CAT_ADVERTISING = 4, 5, 6


def job_wage_day(staff: int, labor_cost: float, days_in_month: int) -> int:
    """Reference wage posted once per job per day, not once per worker."""
    labor = round(labor_cost)
    return ((staff * JOB_RULES.wage_per_worker_month) // days_in_month * labor) // 100


def efficiency(rating: int, labor_quality: float) -> float:
    r = JOB_RULES
    return max(
        r.eff_min, min(r.eff_max, (r.eff_base + r.eff_per_rating * rating) * labor_quality / 100)
    )


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
        "train_acc",
        "unit_cost",
        "week_cap",
        "week_work",
    )

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        self.firm, self.slot = firm, slot
        self.row: JobTypeRow = JOB_TYPES[self.type_id]
        self.product, self.rating = product, rating
        self.staff = self.row.staff
        self.stock = self.quality = self.unit_cost = 0.0
        self.price = product.row.base_price if product is not None else 0.0
        self.brand = -1
        self.train_acc = self.week_work = self.week_cap = 0.0
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
    def room(self) -> float:
        """4a stock ceiling. Slice 5 replaces this with the three-day buffer."""
        return max(0.0, self.capacity - self.stock)

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

    def train(self) -> None:
        r = JOB_RULES
        if self.week_cap > 0:
            use = self.week_work / self.week_cap
            delta = 1 if use >= r.train_hi else (-1 if use < r.train_lo else 0)
            self.train_acc += delta * r.train_step
        if self.train_acc >= r.train_threshold:
            if self.rating < r.rating_max:
                self.rating += 1
            self.train_acc = 0.0
        elif self.train_acc <= -r.train_threshold:
            if self.rating > r.rating_min:
                self.rating -= 1
            self.train_acc = 0.0
        self.week_work = self.week_cap = 0.0

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
        step, added = self.daily_growth(), 0.0
        added = min(self.room, step)
        self.week_cap += step
        self.week_work += added
        self.receive(added, self.produced_quality(), p.row.base_cost)
        return self.stock >= self.capacity


class LivestockRaising(Job):
    type_id = 2
    __slots__ = ()

    def work(self, eco: Economy) -> bool:
        if self.product is None:
            return False
        step = self.capacity / JOB_RULES.livestock_scalar * self.efficiency * self.capacity / 100
        added = min(self.room, step)
        self.week_cap, self.week_work = self.week_cap + step, self.week_work + added
        self.receive(added, self.produced_quality(), self.product.row.base_cost)
        return False


class Extraction(Job):
    type_id = 8
    __slots__ = ()

    def work(self, eco: Economy) -> bool:
        if self.product is None:
            return False
        step = JOB_RULES.extraction_rate * self.efficiency * self.capacity / 100
        added = min(self.room, step)
        self.week_cap, self.week_work = self.week_cap + step, self.week_work + added
        self.receive(added, self.produced_quality(), self.product.row.base_cost)
        return self.stock >= self.capacity


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
    __slots__ = ("inputs",)

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        self.inputs: dict[int, list[float]] = {}

    def skill(self) -> float:
        """Own technology, with a manager's manufacturing skill once people are available."""
        if self.product is None or self.firm.owner is None:
            return 0.0
        manager = self.firm.owner.manufacturing_skill
        tech = self.firm.owner.technology_level(self.product)
        skill = manager / RESEARCH_RULES.manager_skill_divisor + tech
        return min(JOB_RULES.mfg_skill_max, skill)

    def cycles_per_day(self, recipe: RecipeRow) -> int:
        return int(
            (self.capacity * self.efficiency / 100 * recipe.speed_pct / 100) // recipe.output_qty
        )

    def work(self, eco: Economy) -> bool:
        p = self.product
        if p is None or self.room <= 0 or (recipe := eco.catalog.recipe(p)) is None:
            return False
        cycles = min(self.cycles_per_day(recipe), int(self.room // recipe.output_qty))
        self.week_cap += self.cycles_per_day(recipe) * recipe.output_qty
        done = 0
        for _ in range(cycles):
            if any(self.inputs.get(i.input_id, (0.0,))[0] < i.qty for i in recipe.inputs):
                break
            done += 1
            for i in recipe.inputs:
                self.inputs[i.input_id][0] -= i.qty
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
            self.week_work += units
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
        wanted = self.efficiency * src.capacity * row.yield_factor / 10_000
        raw = min(
            src.stock, wanted * row.input_ratio, self.room * row.input_ratio / row.yield_factor
        )
        if raw > 0:
            self.take_from(src, raw, row.yield_factor)
            self.month_output += raw * row.yield_factor
        return False

    def take_from(self, src: Job, raw: float, factor: float) -> None:
        src.take(raw)
        self.receive(raw * factor, src.quality, src.unit_cost / factor)

    def monthly(self, eco: Economy) -> None:
        super().monthly(eco)
        self.month_output = 0.0


def product_freight_rate(product: Product, seller: Firm, buyer: Firm) -> float:
    """Decompiled FUN_000785f1: coefficient × distance × value / 100² × 0.5.

    Only a zero raw rate uses the $0.01/unit floor. Positive sub-cent rates stay exact.
    """
    r = JOB_RULES
    distance = abs(seller.x - buyer.x) + abs(seller.y - buyer.y)
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
            or (eco.calendar.day_serial + self.firm.id) % r.purchase_every_days
            or self.stock >= self.capacity
        ):
            return False
        order = self.efficiency * self.capacity * r.purchase_order_mult / 100
        link.quantity = order
        self.week_cap += order
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
        self.week_work += receipt
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
        self.week_cap += self.sell_left
        return self.stock < self.capacity

    def sell_to(self, qty: float, link: Link) -> None:
        qty = self.take(qty)
        if qty <= 0:
            return
        self.sell_left, self.week_work = max(0.0, self.sell_left - qty), self.week_work + qty
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
    type_id = 14
    rank = 1
    __slots__ = ("has_master",)

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        self.has_master = False

    def add_master(self, development: SoftwareDevelopment) -> None:
        if development.product is not self.product:
            raise ValueError("development and production targets differ")
        if (
            development.stock >= 1
            and self.firm.owner is not None
            and self.firm.owner.has_technology(development.product)
        ):
            self.quality, self.unit_cost = development.quality, development.unit_cost
            self.has_master = True

    def work(self, eco: Economy) -> bool:
        if (
            not self.has_master
            or self.product is None
            or self.firm.owner is None
            or not self.firm.owner.has_technology(self.product)
        ):
            return False
        # M1 interpretation: efficiency is the 10..100 percentage scale used by other jobs.
        added = min(self.room, self.efficiency / 100 * self.capacity)
        self.receive(added, self.quality, self.product.row.base_cost)
        self.week_cap += self.capacity
        self.week_work += added
        return self.stock < self.capacity

    def pull(self, eco: Economy) -> None:
        for job in self.firm.linked_jobs(self.slot):
            if (
                isinstance(job, SoftwareDevelopment)
                and job.product is self.product
                and job.stock >= 1
            ):
                self.add_master(job)
                return


def qualifies_media(media: MediaFirm) -> bool:
    """Only the station's own earned last-month revenue qualifies it."""
    return media.ledger.last_month[CAT_SALES] > ADVERTISING_RULES.media_min_revenue


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
            raise ValueError("media partner has not passed the monthly revenue threshold")
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
            # design.md slice 5: no stock, no sale, no brand gain, no ad effect. Only live
            # consumer links whose seller holds stock on the campaign tick gain brand.
            for link in eco.market.live_links():
                if (
                    link.live
                    and link.seller.firm is self.firm
                    and link.product is product
                    and link.seller.stock > 0
                ):
                    link.brand = min(
                        LINK_RULES.brand_max,
                        link.brand + LINK_RULES.ad_brand_per_100k * self.budget / 100_000,
                    )

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
