"""Product links and the market service (design.md slice 5).

A `Link` connects a seller job to a buyer: another firm's Purchasing job
(B2B) or a `TownMarket` (consumers). Consumer quantity only moves on
live-inventory links (department stores in 4a).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .catalog import Product, TownMarket
from .tables import LINK_RULES

if TYPE_CHECKING:
    from .economy import Economy
    from .jobs import Job

MONTHS = 12


def link_score(
    product: Product, price: float, quality: float, brand: float, jitter: int = 0
) -> float:
    """`base + brand × w_brand / 60 + quality × w_quality / 60` with a price base."""
    r = LINK_RULES
    row = product.row
    base = max(0.0, r.price_base - r.price_slope * price / row.base_price)
    s = base + brand * row.w_brand / r.score_div + quality * row.w_quality / r.score_div + jitter
    return max(0.0, s)


def score_shares(demand: float, scores: list[float]) -> list[float]:
    """Split `demand` by score^exponent (design.md slice 5 call 5)."""
    e = LINK_RULES.share_exponent
    powered = [max(0.0, s) ** e for s in scores]
    total = sum(powered)
    if total <= 0:
        return [0.0] * len(scores)
    return [demand * p / total for p in powered]


class Link:
    __slots__ = (
        "brand",
        "buyer",
        "id",
        "margin_month",
        "money_month",
        "prev_score",
        "price",
        "product",
        "quantity",
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
        self.quantity_sum = 0.0
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
        return self.consumer and self.seller.firm.row.live_inventory

    def compute_score(self) -> float:
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
        """Daily step 1: recompute; a drop scales quantity by new/old on live links."""
        new = self.compute_score()
        if self.live and new < self.score and self.score > 0:
            self.quantity *= new / self.score
        self.prev_score = self.score
        self.score = new

    def nudge_brand(self) -> None:
        r = LINK_RULES
        target = self.seller.quality
        if self.brand < target:
            self.brand = min(target, self.brand + r.brand_nudge)
        elif self.brand > target:
            self.brand = max(target, self.brand - r.brand_nudge)
        self.brand = max(0.0, min(r.brand_max, self.brand))


class Market:
    """Owns every link and the (town, product) consumer markets."""

    def __init__(self) -> None:
        self.links: list[Link | None] = []
        self.towns: dict[tuple[int, int], TownMarket] = {}

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
        for link in self.links:
            if link is not None:
                link.adjust_score()
        for key in sorted(self.towns):
            tm = self.towns[key]
            if tm.links:
                self.consumer_pass(tm)

    def consumer_pass(self, tm: TownMarket) -> None:
        """design.md slice 5 calls 5 and 6, then sales and brand."""
        r = LINK_RULES
        live = [x for x in tm.links if x.live]
        if not live:
            return
        demand = tm.demand_per_day
        supply = sum(x.quantity for x in live)
        if supply > demand:
            for x in live:
                x.quantity -= x.quantity / r.oversupply_div
        else:
            shares = score_shares(demand, [x.score for x in live])
            for x, share in zip(live, shares, strict=True):
                x.quantity += (share - x.quantity) * (r.weight_max - x.weight) / r.weight_max
        for x in live:
            x.quantity_sum += x.quantity
            seller = x.seller
            cap = seller.consumer_cap()  # type: ignore[attr-defined]
            sold = min(cap, x.quantity)
            if sold > 0:
                seller.sell_to(sold, x)  # type: ignore[attr-defined]
                x.nudge_brand()
        tm.supply_today = sum(x.quantity for x in live)

    def monthly(self, month0: int) -> None:
        """Monthly roll (ref): zero the new month's buckets, reset sums, recompute weight."""
        for link in self.links:
            if link is None:
                continue
            link.money_month[month0] = 0.0
            link.units_month[month0] = 0.0
            link.margin_month[month0] = 0.0
            link.update_weight()
            link.quantity_sum = 0.0
        for tm in self.towns.values():
            tm.max_score_in = max((x.score for x in tm.links), default=0.0)
