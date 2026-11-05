"""Firms: buildings with nine job slots on a 3 × 3 grid (design.md slice 4).

Plain classes. One subclass per firm type; a subclass only overrides its
daily hook. Systems 4a implements Farm, LoggingCamp, Mine, OilWell, Factory,
DepartmentStore and Seaport. The other firm types are 4b.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .jobs import CAT_OVERHEAD, CAT_SALES, JOB_CLASSES, Job
from .tables import FIRM_JOB_ALLOWED, FIRM_RULES, FIRM_TYPES, FirmTypeRow

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

    __slots__ = ("cash", "month", "total", "year")

    def __init__(self) -> None:
        self.cash = 0.0
        self.month = [0.0] * N_CATEGORIES
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
        self.month = [0.0] * N_CATEGORIES

    def roll_year(self) -> None:
        self.year = [0.0] * N_CATEGORIES


class Firm:
    type_id = 0
    posts_purchase_cost = False

    __slots__ = (
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
        self.row: FirmTypeRow = FIRM_TYPES[self.type_id]
        self.owner = owner
        self.x = x
        self.y = y
        self.tile = tile
        self.town = town
        self.size = FIRM_RULES.size
        self.slots: list[Job | None] = [None] * FIRM_RULES.slots
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
        if not 0 <= slot < self.row.max_slots or self.slots[slot] is not None:
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

    def post(self, cat: int, amount: float) -> None:
        if self.owner is None or amount == 0:
            return
        self.ledger.post(cat, amount)
        self.owner.ledger.post(cat, amount)

    # --- cycles ------------------------------------------------------------

    def on_daily(self, eco: Economy) -> None:
        """Per-type daily hook (firm daily step 1). Default: nothing."""

    def daily(self, eco: Economy) -> None:
        """Firm pass: type hook, then slots 0..8 run work() then pull()."""
        self.on_daily(eco)
        for job in self.slots:
            if job is not None and job.work(eco):
                job.pull(eco)

    def post_overhead(self, fraction: float = 1.0) -> None:
        self.post(CAT_OVERHEAD, self.row.overhead_month * FIRM_RULES.cost_scale * fraction)

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


class Seaport(Firm):
    """Imports at base price. The ref's supply projection is a 4b refinement."""

    type_id = 14
    __slots__ = ()


FIRM_CLASSES: dict[int, type[Firm]] = {
    cls.type_id: cls
    for cls in (DepartmentStore, Factory, Farm, LoggingCamp, Mine, OilWell, Seaport)
}
