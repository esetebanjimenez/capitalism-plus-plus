"""Product catalog and town demand (design.md slice 3).

Static rows come from the db through `capitalism.tables`; the per-game state
(`ProductState`, `TownMarket`) is plain classes because it changes daily.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from .rng import Rng
from .tables import (
    PRODUCT_RULES,
    ProductClassRow,
    ProductRow,
    RecipeRow,
    RndPrereqRow,
    load_product_classes,
    load_products,
    load_recipes,
    load_rnd_prereqs,
)

if TYPE_CHECKING:
    from .links import Link
    from .town import Town


class Product:
    """A catalog product: the static row plus its per-game state."""

    kind = ""

    __slots__ = ("cls", "row", "slot", "state")

    def __init__(self, row: ProductRow, cls: ProductClassRow, slot: int) -> None:
        self.row = row
        self.cls = cls
        self.slot = slot
        self.state = ProductState(row.base_tech_level)

    @property
    def id(self) -> int:
        return self.row.id

    @property
    def name(self) -> str:
        return self.row.name

    @property
    def is_consumer(self) -> bool:
        return self.row.demand_per_1000 > 0

    @property
    def is_root(self) -> bool:
        """Raw, crop and livestock products need no inputs."""
        return False

    @property
    def decays(self) -> bool:
        return not self.cls.durable and not self.state.obsolete

    @staticmethod
    def make(row: ProductRow, cls: ProductClassRow, slot: int) -> Product:
        return PRODUCT_KINDS[row.kind](row, cls, slot)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.row.name!r})"


class RawMaterial(Product):
    kind = "raw"
    __slots__ = ()

    @property
    def is_root(self) -> bool:
        return True


class Crop(Product):
    kind = "crop"
    __slots__ = ()

    @property
    def is_root(self) -> bool:
        return True

    def in_season(self, month0: int) -> bool:
        """`month0` is 0 = January. Grows for `grow_months` from `plant_month`."""
        pm = self.row.plant_month or 0
        gm = self.row.grow_months or 0
        return (month0 - pm) % 12 < gm


class Livestock(Product):
    kind = "livestock"
    __slots__ = ()

    @property
    def is_root(self) -> bool:
        return True


class SemiProduct(Product):
    kind = "semi"
    __slots__ = ()


class ConsumerProduct(Product):
    kind = "consumer"
    __slots__ = ()


class Software(Product):
    kind = "software"
    __slots__ = ()


PRODUCT_KINDS: dict[str, type[Product]] = {
    k.kind: k for k in (RawMaterial, Crop, Livestock, SemiProduct, ConsumerProduct, Software)
}


class ProductState:
    """Per-game product state (plain class, design.md slice 3)."""

    __slots__ = (
        "available",
        "discovered_year",
        "max_score_in",
        "obsolete",
        "score",
        "score_jitter",
        "tech_level",
    )

    def __init__(self, tech_level: int) -> None:
        self.tech_level = tech_level
        self.discovered_year: int | None = None
        self.obsolete = False
        self.score = PRODUCT_RULES.score_no_links
        self.score_jitter = 0
        self.max_score_in = 0.0
        self.available = True


def nec_lux(row: ProductRow, gnp_pc_index: float) -> float:
    r = PRODUCT_RULES
    v = (
        r.nec_lux_base
        + r.nec_lux_necessity * row.necessity
        + r.nec_lux_luxury * row.luxury * (gnp_pc_index - 1.0)
    )
    return max(r.nec_lux_lo, min(r.nec_lux_hi, v))


def daily_demand(product: Product, town: Town) -> float:
    """Consumer units per day for `product` in `town` (design.md slice 3 call 2)."""
    row = product.row
    if row.demand_per_1000 <= 0:
        return 0.0
    r = PRODUCT_RULES
    idx = town.per_capita_gnp / r.gnp_pc_ref
    age = r.obsolete_demand_factor if product.state.obsolete else 1.0
    return (
        row.demand_per_1000
        * town.population
        / r.demand_per_people
        * (town.consumer_spending / 100.0)
        * nec_lux(row, idx)
        * age
    )


class TownMarket:
    """One per (town, consumer product): demand and the consumer links selling there."""

    __slots__ = ("demand_per_day", "links", "max_score_in", "product", "supply_today", "town")

    def __init__(self, town: Town, product: Product) -> None:
        self.town = town
        self.product = product
        self.demand_per_day = 0.0
        self.links: list[Link] = []
        self.max_score_in = 0.0
        self.supply_today = 0.0

    def recompute(self) -> None:
        self.demand_per_day = daily_demand(self.product, self.town)


class Catalog:
    """All products for one game, in product-id order."""

    def __init__(self) -> None:
        classes = load_product_classes()
        self.products: list[Product] = [
            Product.make(row, classes[row.class_id], i) for i, row in enumerate(load_products())
        ]
        self.by_id: dict[int, Product] = {p.id: p for p in self.products}
        self.by_name: dict[str, Product] = {p.name: p for p in self.products}
        self.recipes: dict[int, RecipeRow] = dict(load_recipes())
        self.rnd_prereqs: dict[int, list[RndPrereqRow]] = {}
        for pre in load_rnd_prereqs():
            self.rnd_prereqs.setdefault(pre.product_id, []).append(pre)
        self.refresh_availability()

    def __getitem__(self, name: str) -> Product:
        return self.by_name[name]

    def __len__(self) -> int:
        return len(self.products)

    def recipe(self, product: Product) -> RecipeRow | None:
        return self.recipes.get(product.id)

    def jitter(self, rng: Rng) -> None:
        """Setup jitter, drawn in product-id order (design.md slice 3 call 4)."""
        tj = PRODUCT_RULES.tech_jitter
        sj = PRODUCT_RULES.score_jitter
        for p in self.products:
            p.state.tech_level = max(0, p.row.base_tech_level + rng.randint(-tj, tj))
            p.state.score_jitter = rng.randint(-sj, sj)

    def refresh_availability(self, disabled: Iterable[int] = ()) -> None:
        avail = compute_availability(self.products, self.recipes, frozenset(disabled))
        for p in self.products:
            p.state.available = avail[p.id]

    def slot_products(self, slot: int) -> list[Product]:
        return [p for p in self.products if p.slot % 30 == slot]


def compute_availability(
    products: Iterable[Product],
    recipes: dict[int, RecipeRow],
    disabled: frozenset[int] = frozenset(),
) -> dict[int, bool]:
    """Recursive availability with a cycle guard (design.md slice 3 call 8).

    A product is available when it is raw/crop/livestock or importable, or
    it has a recipe whose every input is available. R&D prerequisites
    (`rnd_prereqs`) gate discovery, which lands with R&D. `disabled` ids are never available
    (used by tests and, later, by discovery).
    """
    by_id = {p.id: p for p in products}
    memo: dict[int, bool] = {}

    def visit(pid: int, stack: frozenset[int]) -> bool:
        if pid in memo:
            return memo[pid]
        if pid in disabled:
            memo[pid] = False
            return False
        p = by_id[pid]
        if p.is_root or p.row.importable:
            memo[pid] = True
            return True
        rec = recipes.get(pid)
        if rec is None or not rec.inputs or pid in stack:
            return False
        ok = all(visit(i.input_id, stack | {pid}) for i in rec.inputs)
        memo[pid] = ok
        return ok

    return {pid: visit(pid, frozenset()) for pid in by_id}
