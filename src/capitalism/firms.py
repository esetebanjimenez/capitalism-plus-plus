"""Firms: buildings with nine job slots on a 3 × 3 grid (design.md slice 4).

Plain classes. One subclass per firm type; a subclass only overrides its
daily hook. Systems 4a implements Farm, LoggingCamp, Mine, OilWell, Factory,
DepartmentStore and Seaport. Media, research, software, restaurant and import supply complete slice 4b.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .jobs import (
    CAT_OVERHEAD,
    CAT_SALARIES,
    CAT_SALES,
    JOB_CLASSES,
    Job,
    SoftwareDevelopment,
    SoftwareProduction,
    job_wage_day,
)
from .tables import ADVERTISING_RULES, FIRM_JOB_ALLOWED, FIRM_RULES, FIRM_TYPES, FirmTypeRow

if TYPE_CHECKING:
    from .catalog import Product
    from .economy import Corporation, Economy
    from .town import Town
    from .world import Tile

N_CATEGORIES = 12
OPERATING_CATEGORIES = 9

# The 20 neighbour links on the 3 × 3 slot grid (design.md slice 4 call 1):
# horizontals row by row, verticals column by column, then diagonals "\"
# and "/", each top-left first. Slot = row × 3 + column.
SLOT_EDGES: tuple[tuple[int, int], ...] = (
    (0, 1), (1, 2), (3, 4), (4, 5), (6, 7), (7, 8),
    (0, 3), (3, 6), (1, 4), (4, 7), (2, 5), (5, 8),
    (0, 4), (1, 5), (3, 7), (4, 8),
    (1, 3), (2, 4), (4, 6), (5, 7),
)  # fmt: skip
EDGE_BIT: dict[tuple[int, int], int] = {e: i for i, e in enumerate(SLOT_EDGES)}


def edge_bit(a: int, b: int) -> int:
    key = (min(a, b), max(a, b))
    if key not in EDGE_BIT:
        raise ValueError(f"slots {a} and {b} are not neighbours on the 3x3 grid")
    return EDGE_BIT[key]


def encode_links(edges: list[tuple[int, int]]) -> int:
    mask = 0
    for a, b in edges:
        mask |= 1 << edge_bit(a, b)
    return mask


def decode_links(mask: int) -> list[tuple[int, int]]:
    return [e for i, e in enumerate(SLOT_EDGES) if mask >> i & 1]


class Ledger:
    """12 posting categories (ref). Revenue is category 0; everything else is a cost."""

    __slots__ = ("cash", "last_month", "month", "total", "year")

    def __init__(self) -> None:
        self.cash = 0.0
        self.month = [0.0] * N_CATEGORIES
        self.last_month = [0.0] * N_CATEGORIES
        self.year = [0.0] * N_CATEGORIES
        self.total = [0.0] * N_CATEGORIES

    def post(self, cat: int, amount: float) -> None:
        self.month[cat] += amount
        self.year[cat] += amount
        self.total[cat] += amount
        self.cash += amount if cat == CAT_SALES else -amount

    @staticmethod
    def operating(cat: int) -> bool:
        return cat < OPERATING_CATEGORIES

    def roll_month(self) -> None:
        self.last_month = self.month
        self.month = [0.0] * N_CATEGORIES

    def roll_year(self) -> None:
        self.year = [0.0] * N_CATEGORIES


class Firm:
    type_id = 0
    posts_purchase_cost = False

    __slots__ = (
        "advertisers",
        "created_serial",
        "id",
        "land_value",
        "ledger",
        "links",
        "owner",
        "row",
        "size",
        "slots",
        "tile",
        "town",
        "weight_rate",
        "x",
        "y",
    )

    def __init__(
        self,
        firm_id: int,
        owner: Corporation | None,
        x: int,
        y: int,
        tile: Tile,
        town: Town,
        land_value: int,
        created_serial: int,
    ) -> None:
        self.id = firm_id
        self.advertisers: set[int] = set()
        self.row: FirmTypeRow = FIRM_TYPES[self.type_id]
        self.owner = owner
        self.x = x
        self.y = y
        self.tile = tile
        self.town = town
        self.size = FIRM_RULES.size
        self.slots: list[Job | None] = [None] * self.row.max_slots
        self.links = 0
        self.ledger = Ledger()
        self.land_value = land_value
        self.created_serial = created_serial
        self.weight_rate = 0

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id}, town={self.town.name!r})"

    @property
    def allowed_jobs(self) -> frozenset[int]:
        return FIRM_JOB_ALLOWED.get(self.type_id, frozenset())

    @property
    def is_farm(self) -> bool:
        return False

    def add_job(self, slot: int, job_type: int, product: Product | None) -> Job:
        if job_type not in self.allowed_jobs:
            raise ValueError(f"{self.row.name} cannot hold job type {job_type}")
        if job_type not in JOB_CLASSES:
            raise NotImplementedError(f"job type {job_type} lands in systems 4b")
        if not 0 <= slot < self.row.max_slots:
            raise ValueError(
                "this firm uses numbered supply links, not a slot grid"
                if self.row.max_slots == 0
                else f"slot {slot} unavailable"
            )
        if slot >= len(self.slots):
            self.slots.extend([None] * (slot - len(self.slots) + 1))
        if self.slots[slot] is not None:
            raise ValueError(f"slot {slot} unavailable")
        job = JOB_CLASSES[job_type](self, slot, product)
        self.slots[slot] = job
        return job

    def link_slots(self, a: int, b: int) -> None:
        self.links |= 1 << edge_bit(a, b)

    def linked_jobs(self, slot: int) -> list[Job]:
        out: list[Job] = []
        for i, (a, b) in enumerate(SLOT_EDGES):
            if not self.links >> i & 1:
                continue
            other = b if a == slot else a if b == slot else -1
            if other >= 0:
                job = self.slots[other]
                if job is not None:
                    out.append(job)
        return out

    def jobs(self) -> list[Job]:
        return [j for j in self.slots if j is not None]

    def job_suppliers(self, eco: Economy, product: Product) -> list[Job]:
        firm = next(
            (
                f
                for f in eco.firms
                if f is not None
                and f.owner is self.owner
                and any(
                    isinstance(j, SoftwareDevelopment)
                    and j.product is product
                    and j.stock >= 1
                    and type(f) is SoftwareDeveloper
                    for j in f.jobs()
                )
            ),
            None,
        )
        return firm.jobs() if firm is not None else []

    def post(self, cat: int, amount: float, *, direct: bool = False) -> None:
        """Every firm keeps its own books. direct media receipts post only there."""
        if amount == 0:
            return
        self.ledger.post(cat, amount)
        if self.owner is not None and not direct:
            self.owner.ledger.post(cat, amount)

    # --- cycles ------------------------------------------------------------

    def on_daily(self, eco: Economy) -> None:
        """Per-type daily hook (firm daily step 1). Default: nothing."""

    def daily(self, eco: Economy) -> None:
        """Firm pass: type hook, then slots 0..8 run work() then pull()."""
        self.on_daily(eco)
        for job in self.slots:
            if job is not None:
                if isinstance(self, SoftwarePublisher) and isinstance(job, SoftwareProduction):
                    dev = next(
                        (
                            j
                            for j in self.job_suppliers(eco, job.product)
                            if isinstance(j, SoftwareDevelopment) and j.stock >= 1
                        ),
                        None,
                    )
                    if dev is not None:
                        job.add_master(dev)
                if job.work(eco):
                    job.pull(eco)

    def post_overhead(self, fraction: float = 1.0) -> None:
        """Overhead is full dollars per month (Esteban 2026-11-06); whole post on monthly."""
        self.post(CAT_OVERHEAD, self.row.overhead_month * fraction)

    def monthly(self, eco: Economy) -> None:
        self.ledger.roll_month()
        self.post_overhead()
        self.land_value = eco.world.land_value(self.x, self.y)
        for job in self.slots:
            if job is not None:
                job.monthly(eco)

    def yearly(self, eco: Economy) -> None:
        self.ledger.roll_year()


class DepartmentStore(Firm):
    type_id = 1
    posts_purchase_cost = True
    __slots__ = ()


class Factory(Firm):
    type_id = 2
    posts_purchase_cost = True
    __slots__ = ()


class Farm(Firm):
    type_id = 4
    __slots__ = ()

    @property
    def is_farm(self) -> bool:
        return True


class LoggingCamp(Firm):
    type_id = 5
    __slots__ = ()


class Mine(Firm):
    type_id = 6
    __slots__ = ()


class OilWell(Firm):
    type_id = 7
    __slots__ = ()


class Restaurant(DepartmentStore):
    type_id = 10
    __slots__ = ()


class ResearchCentre(Firm):
    type_id = 3
    __slots__ = ()


class SoftwareDeveloper(Firm):
    type_id = 8
    __slots__ = ()


class SoftwarePublisher(Firm):
    type_id = 9
    posts_purchase_cost = True
    __slots__ = ()


class MediaFirm(Firm):
    """No job slots: daily payroll, audience and twelve-month revenue history."""

    __slots__ = ("audience", "audience_month", "audience_total", "revenue_month", "revenue_total")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.audience = ADVERTISING_RULES.media_audience_min
        self.audience_month = [0.0] * 12
        self.audience_total = self.audience
        self.revenue_month = [0.0] * 12
        self.revenue_total = 0.0

    def on_daily(self, eco: Economy) -> None:
        wage = job_wage_day(
            FIRM_RULES.media_staff, self.town.labor_cost, eco.calendar.real_month_days
        )
        self.post(CAT_SALARIES, wage)  # media payroll: no training post (ref)

    def initialize_audience(self, eco: Economy) -> None:
        r = ADVERTISING_RULES
        if not self.row.government:
            return
        self.audience = float(
            eco.rng.randint(int(r.media_audience_min), int(r.media_government_max))
        )

    def monthly(self, eco: Economy) -> None:
        super().monthly(eco)
        r = ADVERTISING_RULES
        target = max(
            r.media_audience_min,
            min(r.media_audience_cap, self.town.population / r.media_audience_population_div),
        )
        self.audience += (target - self.audience) * r.media_audience_adjust_rate
        self.audience_month = self.audience_month[1:] + [self.audience]
        self.audience_total = sum(self.audience_month)
        self.revenue_month = self.revenue_month[1:] + [self.ledger.last_month[CAT_SALES]]
        self.revenue_total = sum(self.revenue_month)


class TVStation(MediaFirm):
    type_id = 11
    __slots__ = ()


class RadioStation(MediaFirm):
    type_id = 12
    __slots__ = ()


class NewspaperPublisher(MediaFirm):
    type_id = 13
    __slots__ = ()


class Seaport(Firm):
    """Unlimited numbered product supplies, independent of the nine-slot job grid."""

    type_id = 14
    __slots__ = ("imports",)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.imports: dict[int, Job] = {}

    def open_import(self, product: Product) -> Job:
        if not product.row.importable:
            raise ValueError(f"{product.name} must be produced locally")
        job = self.imports.get(product.id)
        if job is not None:
            return job
        job = JOB_CLASSES[16](self, len(self.imports), product)
        self.imports[product.id] = job
        return job

    def add_job(self, slot: int, job_type: int, product: Product | None) -> Job:
        """Compatibility for 4a scenarios; new callers use open_import(product)."""
        if job_type != 16 or product is None:
            raise ValueError("seaports only open import supplies")
        if product.id in self.imports:
            return self.imports[product.id]
        return self.open_import(product)

    def jobs(self) -> list[Job]:
        return list(self.imports.values())


FIRM_CLASSES: dict[int, type[Firm]] = {
    cls.type_id: cls
    for cls in (
        DepartmentStore,
        Factory,
        ResearchCentre,
        Farm,
        LoggingCamp,
        Mine,
        OilWell,
        SoftwareDeveloper,
        SoftwarePublisher,
        Restaurant,
        TVStation,
        RadioStation,
        NewspaperPublisher,
        Seaport,
    )
}
