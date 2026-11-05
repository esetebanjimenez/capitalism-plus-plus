"""Jobs: the work units inside a firm's nine slots (design.md slice 4).

Plain classes on the hot path. One subclass per job type; each overrides
`work()` (returns True when the supply-chain pull should run) and `pull()`.
Systems 4a ships the job types used by farms, extraction firms, factories,
department stores and seaports. R&D, software and media jobs are 4b.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .catalog import Crop, Product
from .tables import JOB_RULES, JOB_TYPES, JobTypeRow, RecipeRow

if TYPE_CHECKING:
    from .economy import Economy
    from .firms import Firm
    from .links import Link

# Ledger categories (gamelogic.md *Financial accounting*).
CAT_SALES = 0
CAT_SALARIES = 1
CAT_OVERHEAD = 2
CAT_TRAINING = 3
CAT_PURCHASE = 4
CAT_FREIGHT = 5


def wage_per_staff_day(labor_cost: float, days_in_month: int) -> int:
    """Ref integer formula: ((target × 2000) / days-in-month × labor) / 100."""
    r = JOB_RULES
    target = round(labor_cost)
    return ((target * r.wage_hours) // days_in_month * r.labor_factor) // 100


def efficiency(rating: int, labor_quality: float) -> float:
    """design.md slice 4 call 3 (provisional)."""
    r = JOB_RULES
    e = (r.eff_base + r.eff_per_rating * rating) * labor_quality / 100.0
    return max(r.eff_min, min(r.eff_max, e))


class Job:
    """Base job. `rank` orders stock flow: lower-rank jobs feed higher-rank ones."""

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
        self.firm = firm
        self.slot = slot
        self.row: JobTypeRow = JOB_TYPES[self.type_id]
        self.product = product
        self.staff = self.row.staff
        self.stock = 0.0
        self.quality = 0.0
        self.unit_cost = 0.0
        self.price = product.row.base_price if product is not None else 0.0
        self.brand = -1  # owner corp id whose brand the goods carry; -1 = none
        self.rating = rating
        self.train_acc = 0.0
        self.week_work = 0.0
        self.week_cap = 0.0
        self.param1 = 0
        self.param2 = 0

    def __repr__(self) -> str:
        p = self.product.name if self.product else None
        return f"{type(self).__name__}(slot={self.slot}, product={p!r}, stock={self.stock:.1f})"

    # --- derived -----------------------------------------------------------

    @property
    def capacity(self) -> float:
        if self.product is None:
            return 0.0
        return self.product.row.base_capacity * self.firm.size * self.row.cap_mult

    @property
    def room(self) -> float:
        return max(0.0, self.capacity - self.stock)

    @property
    def efficiency(self) -> float:
        return efficiency(self.rating, self.firm.town.labor_quality)

    def available_stock(self) -> float:
        return self.stock

    def produced_quality(self) -> float:
        r = JOB_RULES
        return (self.rating - 1) * r.quality_per_rating + r.quality_base

    # --- stock movement ----------------------------------------------------

    def receive(self, qty: float, quality: float, unit_cost: float) -> None:
        """Add stock, blending quality and unit cost by quantity."""
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
        """True when `self` is a stock source for `other` (same product, lower rank)."""
        return self.product is not None and self.product is other.product and self.rank < other.rank

    def sources(self) -> list[Job]:
        return [j for j in self.firm.linked_jobs(self.slot) if j.feeds(self)]

    # --- daily cycle -------------------------------------------------------

    def post_wages(self, eco: Economy) -> None:
        """Job daily step 1 (wages) and step 2 (training on the train weekday)."""
        if self.staff:
            wage = wage_per_staff_day(self.firm.town.labor_cost, eco.calendar.real_month_days)
            salary = wage * self.staff
            self.firm.post(CAT_SALARIES, salary)
            self.firm.post(CAT_TRAINING, salary * self.row.training_factor / 100.0)
        if eco.calendar.weekday == JOB_RULES.train_weekday:
            self.train()

    def train(self) -> None:
        """design.md slice 4 call 6: weekly rating credit from capacity use."""
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
        self.week_work = 0.0
        self.week_cap = 0.0

    def work(self, eco: Economy) -> bool:
        return False

    def pull(self, eco: Economy) -> None:
        """Default take-linked: move stock from linked source jobs, blending quality."""
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
        """Quality decay (design.md slice 3 call 6)."""
        if self.product is not None and self.product.decays and self.stock > 0:
            self.quality *= self.product.cls.quality_decay_base


# --- producers (rank 0) ---------------------------------------------------------


class CropGrowing(Job):
    type_id = 1
    __slots__ = ()

    def yield_factor(self) -> float:
        r = JOB_RULES
        row = self.product.row if self.product else None
        if row is None or row.suit_climate is None or row.suit_moisture is None:
            return 0.0
        tile = self.firm.tile
        cd = abs(tile.climate - row.suit_climate)
        md = abs(tile.moisture - row.suit_moisture) / r.crop_moisture_step
        y = (
            (cd * r.crop_climate_slope + r.crop_yield_base)
            + (md * r.crop_moisture_slope + r.crop_yield_base)
            + tile.soil / r.crop_soil_div
        )
        return max(0.0, y)

    def daily_growth(self) -> float:
        return (self.efficiency * self.capacity / 100.0 * self.yield_factor()) / 100.0

    def work(self, eco: Economy) -> bool:
        p = self.product
        if not isinstance(p, Crop) or not p.in_season(eco.calendar.month - 1):
            return False
        step = self.daily_growth()
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
        cap = self.capacity
        rate = cap / JOB_RULES.livestock_scalar
        step = rate * self.efficiency * cap / 100.0
        added = min(self.room, step)
        self.week_cap += step
        self.week_work += added
        self.receive(added, self.produced_quality(), self.product.row.base_cost)
        return False


class Extraction(Job):
    """Logging, Mining and Oil Extraction share this rule (reserve draw is 4b/slice 7)."""

    type_id = 8
    __slots__ = ()

    def work(self, eco: Economy) -> bool:
        if self.product is None:
            return False
        step = JOB_RULES.extraction_rate * self.efficiency * self.capacity / 100.0
        added = min(self.room, step)
        self.week_cap += step
        self.week_work += added
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
    """`Σ(q_i × w_i) / 100 + skill × (100 − Σw_i) / 100` (docs/recipes.md weights)."""
    q = sum(input_quality.get(i.input_id, 0.0) * i.quality_weight for i in recipe.inputs)
    return (q + skill * recipe.skill_weight) / 100.0


class Manufacturing(Job):
    """Runs whole recipe cycles from the db `recipes` / `recipe_inputs` tables.

    Daily output `(capacity × efficiency / 100) × 100 / speed_pct`, rounded
    down to whole cycles of `output_qty`. Each cycle needs `qty` of every
    input and stops at the first missing input (no partial cycles).
    """

    type_id = 7
    __slots__ = ("inputs",)

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        # input product id -> [qty, quality, unit_cost]
        self.inputs: dict[int, list[float]] = {}

    def skill(self) -> float:
        """Provisional until R&D: the product's tech level, capped (rules `mfg_skill_max`)."""
        if self.product is None:
            return 0.0
        return min(JOB_RULES.mfg_skill_max, float(self.product.state.tech_level))

    def cycles_per_day(self, recipe: RecipeRow) -> int:
        units = self.capacity * self.efficiency / 100.0 * 100.0 / recipe.speed_pct
        return int(units // recipe.output_qty)

    def work(self, eco: Economy) -> bool:
        p = self.product
        if p is None or self.room <= 0:
            return False
        recipe = eco.catalog.recipe(p)
        if recipe is None:
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
            wages = (
                wage_per_staff_day(self.firm.town.labor_cost, eco.calendar.real_month_days)
                * self.staff
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
        cycles = self.cycles_per_day(recipe)
        weekday0 = eco.calendar.weekday == 0
        linked = self.firm.linked_jobs(self.slot)
        for i in recipe.inputs:
            buf = self.inputs.setdefault(i.input_id, [0.0, 0.0, 0.0])
            for src in linked:
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
    """Holds its slot in 4a: the livestock yield table is not in the reference set yet."""

    type_id = 3
    __slots__ = ()


class Purchasing(Job):
    """Buys from a supplier link every few days (design.md slice 4 call 7)."""

    type_id = 10
    __slots__ = ("supply",)

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        self.supply: Link | None = None

    def work(self, eco: Economy) -> bool:
        r = JOB_RULES
        link = self.supply
        if self.product is None or link is None:
            return False
        if (eco.calendar.day_serial + self.firm.id) % r.purchase_every_days != 0:
            return False
        if self.stock >= self.capacity:
            return False
        order = self.efficiency * self.capacity * r.purchase_order_mult / 100.0
        link.quantity = order
        self.week_cap += order
        seller = link.seller
        receipt = min(order, self.room, seller.available_stock())
        if receipt <= 0:
            return False
        price = link.price
        quality = seller.quality
        seller.sell_to(receipt, link)
        self.receive(receipt, quality, price)
        self.firm.post(CAT_FREIGHT, r.freight_rate * price * receipt)
        self.week_work += receipt
        return False


class ImportJob(Job):
    """Seaport import: unlimited stock at base price (design.md slice 4 call 7)."""

    type_id = 16
    __slots__ = ()

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        self.quality = JOB_RULES.import_quality
        if product is not None:
            self.unit_cost = product.row.base_price

    def available_stock(self) -> float:
        return math.inf if self.product is not None else 0.0

    def take(self, qty: float) -> float:
        return max(0.0, qty)

    def sell_to(self, qty: float, link: Link) -> None:
        link.record_sale(qty)


# --- pass-through (rank 1, 2) and sales (rank 3) -------------------------------------


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
    """Sells to consumers (through the market) or to other firms' Purchasing jobs."""

    type_id = 12
    rank = 3
    __slots__ = ("sell_left",)

    def __init__(self, firm: Firm, slot: int, product: Product | None, rating: int = 1) -> None:
        super().__init__(firm, slot, product, rating)
        self.sell_left = 0.0

    def daily_cap(self) -> float:
        r = JOB_RULES
        mult = r.sales_mult_store if self.firm.row.live_inventory else r.sales_mult_other
        return self.efficiency * mult * self.capacity / 100.0

    def work(self, eco: Economy) -> bool:
        if self.product is None:
            return True
        self.sell_left = self.daily_cap()
        self.week_cap += self.sell_left
        return self.stock < self.capacity

    def sell_to(self, qty: float, link: Link) -> None:
        """B2B sale to a Purchasing job or a consumer sale from the market."""
        qty = self.take(qty)
        if qty <= 0:
            return
        self.sell_left = max(0.0, self.sell_left - qty)
        self.week_work += qty
        self.firm.post(CAT_SALES, qty * link.price)
        if self.firm.posts_purchase_cost:
            self.firm.post(CAT_PURCHASE, qty * self.unit_cost)
        link.record_sale(qty)

    def consumer_cap(self) -> float:
        return min(self.sell_left, self.stock)


class Advertising(Job):
    """Needs a media partner firm (4b); holds its slot and does nothing in 4a."""

    type_id = 15
    rank = 4
    __slots__ = ()


JOB_CLASSES: dict[int, type[Job]] = {
    cls.type_id: cls
    for cls in (
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
        Sales,
        Advertising,
        ImportJob,
    )
}

__all__ = [
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
    "Sales",
    "cycle_quality",
    "efficiency",
    "wage_per_staff_day",
]
