"""Product links and the market service (design.md slice 5).

A `Link` connects a seller job to a buyer: another firm's Purchasing job
(B2B) or a `TownMarket` (consumers). Consumer quantity only moves on
live-inventory links (department stores in 4a).
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from .catalog import Product, TownMarket
from .tables import LINK_RULES

BRAND_CORPORATE = 0
BRAND_RANGE = 1
BRAND_UNIQUE = 2

if TYPE_CHECKING:
    from .economy import Corporation, Economy
    from .jobs import Job

MONTHS = 12

# Weekly ratings constants (FUN_00075988, observed from binary)
RATING_TARGET = 30.0
RATING_GATE = RATING_TARGET / 200.0  # 0.15
DEMAND_DIVISOR = 20.0  # DAT_000aa0e3
SUPPLY_DECAY_CAP = 0.05  # DAT_000aa0e7 (double)
_IMPORTER_DECAY = {0: 0.025, 1: 0.05}  # corporate, range
_IMPORTER_DECAY_DEFAULT = 0.1  # unique / other

# Brand build-up constants (FUN_0006d0cd, decomp:78835-78920)
_BRAND_RAW_DIVISOR = 50.0  # DAT_000a9644
_BRAND_STEP = 0.1  # DAT_000a9648
_BRAND_DILUTION_PER = 3  # penalty = (count - 1) * 3
_BRAND_HIGH_FLOOR = 50  # max(50, published_high)


def brand_key(corp: Corporation, product: Product, catalog: object) -> int:
    """FUN_0006f435: brand record key by strategy (decomp:80647-80665)."""
    if corp.brand_strategy == BRAND_CORPORATE:
        return 1
    if corp.brand_strategy == BRAND_RANGE:
        return catalog.class_first_product[product.row.class_id]  # type: ignore[union-attr]
    return product.id


class BrandRecord:
    """Per-(town, brand_key) brand data with per-corp arrays (decomp:78870-78874)."""

    __slots__ = ("awareness", "cell", "rating_cell")

    def __init__(self) -> None:
        self.awareness: dict[int, float] = {}
        self.cell: dict[int, float] = {}
        self.rating_cell: dict[int, float] = {}


def link_score(
    product: Product, price: float, quality: float, brand: float, jitter: int = 0
) -> float:
    """Legacy score used for B2B links (consumer links use native_link_score)."""
    r = LINK_RULES
    row = product.row
    base = max(0.0, r.price_base - r.price_slope * price / row.base_price)
    s = base + brand * row.w_brand / r.score_div + quality * row.w_quality / r.score_div + jitter
    return max(0.0, s)


def native_link_score(tm: TownMarket, price: float, quality: float, brand: float) -> float:
    """Native score formula (N3, FPU recovery FUN_0006cc92).

    Brand path: round(pw × 2 × (base − price) / base) + brand × bw / 60 + quality × sw / 60
    No-brand path: round((base − price) × 100 / base + quality / 2)
    """
    row = tm.product.row
    if row.w_brand > 0:
        base = round(tm.price_weight * 2.0 * (row.base_price - price) / row.base_price)
        s = base + brand * tm.brand_weight / 60.0 + quality * tm.score_in_weight / 60.0
    else:
        s = round((row.base_price - price) * 100.0 / row.base_price + quality / 2.0)
    return max(0.0, float(s))


class Link:
    __slots__ = (
        "awareness",
        "brand",
        "buyer",
        "flow_prev",
        "id",
        "margin_month",
        "money_month",
        "prev_score",
        "price",
        "product",
        "quantity",
        "quantity_prev",
        "quantity_sum",
        "score",
        "seller",
        "units_month",
        "weight",
    )

    def __init__(
        self, link_id: int, seller: Job, buyer: Job | TownMarket, price: float | None = None
    ) -> None:
        assert seller.product is not None
        self.id = link_id
        self.seller = seller
        self.buyer = buyer
        self.product: Product = seller.product
        self.price = seller.price if price is None else price
        self.quantity = 0.0
        self.quantity_prev = 0.0
        self.quantity_sum = 0.0
        self.flow_prev = 0.0
        self.awareness = 0.0
        self.brand = LINK_RULES.brand_start
        self.score = 0.0
        self.prev_score = 0.0
        self.weight = 0.0
        self.money_month = [0.0] * MONTHS
        self.units_month = [0.0] * MONTHS
        self.margin_month = [0.0] * MONTHS
        self.update_weight()
        self.score = self.compute_score()
        self.prev_score = self.score

    def __repr__(self) -> str:
        return f"Link(id={self.id}, {self.product.name!r}, q={self.quantity:.1f})"

    @property
    def consumer(self) -> bool:
        return isinstance(self.buyer, TownMarket)

    @property
    def live(self) -> bool:
        return self.consumer and (
            self.seller.firm.row.live_inventory or self.product.row.kind == "software"
        )

    def compute_score(self) -> float:
        if self.consumer:
            return native_link_score(self.buyer, self.price, self.seller.quality, self.brand)
        return link_score(
            self.product,
            self.price,
            self.seller.quality,
            self.brand,
            self.product.state.score_jitter,
        )

    def update_weight(self) -> None:
        r = LINK_RULES
        bonus = 0.0 if self.seller.firm.is_farm else r.weight_nonfarm
        self.weight = min(r.weight_max, self.seller.firm.weight_rate * r.weight_rate_mult + bonus)

    def record_sale(self, qty: float) -> None:
        """Item-sell accounting on the link's monthly series."""
        m = self.month_index
        self.money_month[m] += qty * self.price
        self.units_month[m] += qty
        self.margin_month[m] += (self.price - self.seller.unit_cost) * qty

    month_index = 0  # set per day by the market (class-level default)

    def adjust_score(self) -> None:
        """Daily step 1: recompute; a drop penalises quantity (N11: qty × (1 − drop/100))."""
        new = self.compute_score()
        if self.live and new < self.score:
            drop = self.score - new
            self.quantity *= max(0.0, 1.0 - drop / 100.0)
        self.prev_score = self.score
        self.score = new

    def read_brand(self, market: Market) -> float:
        """FUN_0006d67d mode 1: round(awareness) + round(cell) (decomp:79090-79094)."""
        if not self.consumer:
            return self.brand
        corp = self.seller.firm.owner
        if corp is None or self.product.row.w_brand == 0:
            return 0.0
        bk = brand_key(corp, self.product, market.catalog)
        rec = market.brand_records.get((self.buyer.town.id, bk))
        if rec is None:
            return 0.0
        return float(round(rec.awareness.get(corp.id, 0.0)) + round(rec.cell.get(corp.id, 0.0)))


def _reduce_gap(link: Link, tm: TownMarket) -> float:
    """N4: how far below reference (positive → gets reduced). Per-factor clamping."""
    score_term = max(0.0, (tm.ref_score - link.score) / 100.0)
    price_term = max(0.0, tm.price_weight * (link.price - tm.ref_price) / (tm.ref_price + 0.1) / 300.0)
    quality_term = max(0.0, tm.score_in_weight * (tm.ref_score_in - link.seller.quality) / 30000.0)
    brand_term = max(0.0, tm.brand_weight * (tm.ref_brand - link.brand) / 30000.0)
    return score_term + price_term + quality_term + brand_term


def _increase_gap(link: Link, tm: TownMarket) -> float:
    """N5: how far above reference (positive → gets to grow). Per-factor clamping."""
    score_term = max(0.0, (link.score - tm.ref_score) / 100.0)
    price_term = max(0.0, tm.price_weight * (tm.ref_price - link.price) / (link.price + 0.1) / 300.0)
    quality_term = max(0.0, tm.score_in_weight * (link.seller.quality - tm.ref_score_in) / 30000.0)
    brand_term = max(0.0, tm.brand_weight * (link.brand - tm.ref_brand) / 30000.0)
    return score_term + price_term + quality_term + brand_term


def _take_gap(me: Link, them: Link, tm: TownMarket) -> float:
    """N6: advantage of `me` over `them` (positive → me takes). Per-factor clamping."""
    score_term = max(0.0, (me.score - them.score + 1) / 100.0)
    price_term = max(0.0, tm.price_weight * (them.price - me.price) / (me.price + 0.1) / 300.0)
    quality_term = max(0.0, tm.score_in_weight * (me.seller.quality - them.seller.quality) / 30000.0)
    brand_term = max(0.0, tm.brand_weight * (me.brand - them.brand) / 30000.0)
    return score_term + price_term + quality_term + brand_term


class Market:
    """Owns every link and the (town, product) consumer markets."""

    def __init__(self) -> None:
        self.links: list[Link | None] = []
        self.towns: dict[tuple[int, int], TownMarket] = {}
        self.brand_records: dict[tuple[int, int], BrandRecord] = {}
        self.catalog: object = None  # set by Economy after construction

    def add_link(self, seller: Job, buyer: Job | TownMarket, price: float | None = None) -> Link:
        slot = next((i for i, x in enumerate(self.links) if x is None), len(self.links))
        link = Link(slot, seller, buyer, price)
        if slot == len(self.links):
            self.links.append(link)
        else:
            self.links[slot] = link
        if isinstance(buyer, TownMarket):
            buyer.links.append(link)
        else:
            buyer.supply = link  # type: ignore[attr-defined]
        return link

    def live_links(self) -> list[Link]:
        return [x for x in self.links if x is not None]

    def daily(self, eco: Economy) -> None:
        Link.month_index = eco.calendar.month - 1
        day_serial = eco.calendar.day_serial
        day = eco.calendar.day
        for link in self.links:
            if link is not None:
                if link.consumer:
                    link.brand = link.read_brand(self)
                link.adjust_score()
        for key in sorted(self.towns):
            tm = self.towns[key]
            if tm.links:
                self.consumer_pass(tm, day_serial, day)

    def consumer_pass(self, tm: TownMarket, day_serial: int, day: int) -> None:
        """Native N7 transfer system: oversupply trim, reduce (N4), increase (N5), take (N6)."""
        live = [x for x in tm.links if x.live]
        if not live:
            return
        demand = tm.demand_per_day
        if demand <= 0:
            return
        supply = sum(x.quantity for x in live)
        if supply > demand:
            for x in live:
                if x.quantity > 0:
                    x.quantity -= x.quantity / 50.0
        for x in live:
            x.update_weight()
            gap = _reduce_gap(x, tm)
            if gap > 0 and demand > 0:
                cut = (100.0 - x.weight) * x.quantity * gap * gap * (x.quantity / demand) ** 2 / 100.0
                cut = min(cut, x.quantity)
                x.quantity -= cut
        proj_day = min(day, 30)
        for x in live:
            proj_qty = x.quantity_prev * (30 - proj_day) / 30.0 + x.quantity_sum
            m = Link.month_index
            flow_this = x.units_month[m]
            proj_flow = x.flow_prev * (30 - proj_day) / 30.0 + flow_this
            if proj_flow > 0.0 and proj_qty >= 2.0 * proj_flow:
                continue
            supply = sum(lk.quantity for lk in live)
            free = max(0.0, demand - supply)
            if free > 0:
                gap = _increase_gap(x, tm)
                if gap > 0:
                    add = (100.0 - x.weight) * free * gap * gap * (free / demand) ** 2 / 100.0
                    add = min(add, free)
                    x.quantity += add
            for them in live:
                if them is x:
                    continue
                gap = _take_gap(x, them, tm)
                if gap > 0 and demand > 0:
                    take = (
                        (100.0 - x.weight)
                        * them.quantity
                        * gap
                        * gap
                        * (them.quantity / demand) ** 2
                        * 120.0
                        / 100.0
                        / 100.0
                    )
                    take = min(take, them.quantity)
                    x.quantity += take
                    them.quantity -= take
        for x in live:
            x.quantity_sum += x.quantity
            seller = x.seller
            cap = seller.consumer_cap()  # type: ignore[attr-defined]
            sold = min(cap, x.quantity)
            if sold > 0:
                seller.sell_to(sold, x)  # type: ignore[attr-defined]
                self._brand_buildup(x, sold, tm)
        if day_serial % 2 == 0:
            self._sum_supply(tm)
        unmet = max(0.0, demand - sum(x.quantity for x in live))
        tm.unmet_demand_sum += unmet

    @staticmethod
    def _sum_supply(tm: TownMarket) -> None:
        """N10: recompute supply on even day_serial; each link sees others only."""
        live = [x for x in tm.links if x.live]
        total = sum(x.quantity for x in live)
        tm.supply_today = max(0.0, total)

    def _brand_buildup(self, link: Link, count: float, tm: TownMarket) -> None:
        """FUN_0006d0cd: brand perception update on each sale (decomp:78835-78920)."""
        corp = link.seller.firm.owner
        if corp is None or count <= 0:
            return
        if link.product.row.w_brand == 0:
            return
        bk = brand_key(corp, link.product, self.catalog)
        key = (tm.town.id, bk)
        rec = self.brand_records.get(key)
        if rec is None:
            rec = BrandRecord()
            self.brand_records[key] = rec
        awareness = rec.awareness.get(corp.id, 0.0)
        if awareness < 1.0:
            return
        cell = rec.cell.get(corp.id, 0.0)
        ps = link.product.state
        max_si = max(_BRAND_HIGH_FLOOR, ps.max_score_in)
        max_sc = max(_BRAND_HIGH_FLOOR, ps.max_score)
        p = link.product.row.w_quality
        si = int(link.seller.quality)
        sc = int(link.score)
        raw = float((p * 2 * si) // max_si + ((100 - p * 2) * sc) // max_sc)
        town_id = tm.town.id
        if corp.brand_strategy == BRAND_CORPORATE:
            raw -= (corp.products_per_town.get(town_id, 1) - 1) * _BRAND_DILUTION_PER
        if corp.brand_strategy in (BRAND_CORPORATE, BRAND_RANGE):
            raw -= (corp.classes_per_town.get(town_id, 1) - 1) * _BRAND_DILUTION_PER
        raw = max(0.0, raw)
        target = awareness * raw / _BRAND_RAW_DIVISOR - awareness
        if target == cell:
            return
        if target <= cell:
            step = -_BRAND_STEP
        elif corp.brand_strategy == BRAND_UNIQUE:
            step = _BRAND_STEP
        else:
            classes = max(1, corp.classes_per_town.get(town_id, 1))
            step = _BRAND_STEP / classes
        demand = max(count, tm.demand_per_day)
        cell += count * step / demand
        cell = max(-awareness, min(awareness, cell))
        rec.cell[corp.id] = cell

    def _monthly_awareness(self, link: Link, tm: TownMarket) -> None:
        """FUN_00075aec: monthly awareness gain per live link (decomp:85363-85426)."""
        corp = link.seller.firm.owner
        if corp is None:
            return
        if link.product.row.w_brand == 0:
            return
        bk = brand_key(corp, link.product, self.catalog)
        key = (tm.town.id, bk)
        rec = self.brand_records.get(key)
        if rec is None:
            rec = BrandRecord()
            self.brand_records[key] = rec
        prev_month = (Link.month_index - 1) % MONTHS
        units = link.units_month[prev_month] + 1.0
        demand = max(units, tm.demand_per_day)
        rating = rec.rating_cell.get(corp.id, 0.0)
        gain = (RATING_TARGET - rating) * units / demand / 100.0
        if corp.brand_strategy == BRAND_CORPORATE:
            gain *= 0.25
        elif corp.brand_strategy == BRAND_RANGE:
            gain *= 0.5
        rec.rating_cell[corp.id] = rating + gain
        awareness = rec.awareness.get(corp.id, 0.0) + gain
        awareness = min(awareness, 100.0)
        rec.awareness[corp.id] = awareness

    def weekly_ratings(self) -> None:
        """Weekday 5: decay oversupplied ratings (FUN_00075988).

        Each consumer link with awareness >= RATING_GATE is decayed.
        Importers (seller town != buyer town) lose a fixed amount by brand
        strategy; local producers lose min(RATING_GATE, demand / 20).
        Demand and supply cells also decay.
        """
        for tm in self.towns.values():
            for link in tm.links:
                if link.awareness < RATING_GATE:
                    continue
                owner = link.seller.firm.owner
                if link.seller.firm.town.id != tm.town.id:
                    strategy = owner.brand_strategy if owner else 0
                    decay = _IMPORTER_DECAY.get(strategy, _IMPORTER_DECAY_DEFAULT)
                else:
                    decay = min(RATING_GATE, tm.demand_per_day / DEMAND_DIVISOR)
                link.awareness -= decay
                tm.demand_per_day = max(0.0, tm.demand_per_day - decay)
            if tm.supply_today > 0:
                s_decay = min(tm.supply_today / 200.0, SUPPLY_DECAY_CAP)
                tm.supply_today -= s_decay
            tm.supply_today = max(-tm.demand_per_day, min(tm.supply_today, tm.demand_per_day))

    def _recount_corp_brands(self, eco: Economy) -> None:
        """FUN_00032733: recount distinct products and classes per (corp, town)."""
        for c in eco.corps:
            c.products_per_town.clear()
            c.classes_per_town.clear()
        seen_products: dict[tuple[int, int], set[int]] = defaultdict(set)
        seen_classes: dict[tuple[int, int], set[int]] = defaultdict(set)
        for link in self.links:
            if link is None or not link.consumer:
                continue
            corp = link.seller.firm.owner
            if corp is None:
                continue
            town_id = link.buyer.town.id
            seen_products[(corp.id, town_id)].add(link.product.id)
            seen_classes[(corp.id, town_id)].add(link.product.row.class_id)
        for (corp_id, town_id), prods in seen_products.items():
            if corp_id < len(eco.corps):
                eco.corps[corp_id].products_per_town[town_id] = len(prods)
        for (corp_id, town_id), cls in seen_classes.items():
            if corp_id < len(eco.corps):
                eco.corps[corp_id].classes_per_town[town_id] = len(cls)

    def monthly(self, month0: int, eco: Economy) -> None:
        """Monthly roll: save prev, zero buckets, publish highs, awareness (N9)."""
        product_max_si: dict[int, int] = defaultdict(int)
        product_max_sc: dict[int, int] = defaultdict(int)
        for link in self.links:
            if link is None:
                continue
            link.quantity_prev = link.quantity_sum
            link.flow_prev = link.units_month[month0]
            link.money_month[month0] = 0.0
            link.units_month[month0] = 0.0
            link.margin_month[month0] = 0.0
            link.update_weight()
            link.quantity_sum = 0.0
            pid = link.product.id
            si = int(link.seller.quality)
            sc = int(link.score)
            product_max_si[pid] = max(product_max_si[pid], si)
            product_max_sc[pid] = max(product_max_sc[pid], sc)
        for pid, v in product_max_si.items():
            eco.catalog.by_id[pid].state.max_score_in = v
        for pid, v in product_max_sc.items():
            eco.catalog.by_id[pid].state.max_score = v
        for tm in self.towns.values():
            tm.max_score_in = max((x.score for x in tm.links), default=0.0)
            for link in tm.links:
                if link.live:
                    self._monthly_awareness(link, tm)
                    rec = self.brand_records.get(
                        (tm.town.id, brand_key(link.seller.firm.owner, link.product, self.catalog))
                    )
                    if rec is not None and link.seller.firm.owner is not None:
                        rec.rating_cell.setdefault(link.seller.firm.owner.id, 0.0)
        self._recount_corp_brands(eco)
