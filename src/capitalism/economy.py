"""The product economy: catalog, corporations, firms, jobs and links.

`Economy` is owned by `Sim` and called from the slice-1 day order:
firms layer, jobs layer, links layer, then month/year passes and the
daily product stagger.
"""

from __future__ import annotations

import hashlib
import struct
from typing import TYPE_CHECKING

from .catalog import Catalog, TownMarket
from .firms import FIRM_CLASSES, Firm, Ledger
from .links import Market
from .tables import PRODUCT_RULES
from .world import TileCategory

if TYPE_CHECKING:
    from .calendar import Calendar
    from .jobs import Job
    from .links import Link
    from .rng import Rng
    from .town import Town
    from .world import World


class Corporation:
    """Minimal owner for slices 4–5: a scripted test corp with cash and books."""

    __slots__ = ("id", "ledger", "name")

    def __init__(self, corp_id: int, name: str) -> None:
        self.id = corp_id
        self.name = name
        self.ledger = Ledger()


class Economy:
    def __init__(self, calendar: Calendar, world: World, rng: Rng) -> None:
        self.calendar = calendar
        self.world = world
        self.catalog = Catalog()
        self.catalog.jitter(rng)
        self.corps: list[Corporation] = []
        self.firms: list[Firm | None] = []
        self.market = Market()
        self.ensure_markets()

    # --- setup -------------------------------------------------------------

    def ensure_markets(self) -> None:
        """One TownMarket per (town, consumer product); new towns get theirs here."""
        for town in self.world.towns:
            for p in self.catalog.products:
                key = (town.id, p.id)
                if p.is_consumer and key not in self.market.towns:
                    tm = TownMarket(town, p)
                    tm.recompute()
                    self.market.towns[key] = tm

    def town_market(self, town: Town, product_name: str) -> TownMarket:
        return self.market.towns[(town.id, self.catalog[product_name].id)]

    def add_corp(self, name: str) -> Corporation:
        corp = Corporation(len(self.corps), name)
        self.corps.append(corp)
        return corp

    def build_firm(
        self, firm_type: int, owner: Corporation | None, x: int, y: int, town: Town
    ) -> Firm:
        if firm_type not in FIRM_CLASSES:
            raise NotImplementedError(f"firm type {firm_type} lands in systems 4b")
        tile = self.world.tile_at(x, y)
        if tile.kind in (
            TileCategory.TOWN,
            TileCategory.FIRM,
            TileCategory.WATER,
            TileCategory.DEEP_OCEAN,
        ):
            raise ValueError(f"tile ({x},{y}) is not free land")
        slot = next((i for i, f in enumerate(self.firms) if f is None), len(self.firms))
        firm = FIRM_CLASSES[firm_type](
            slot, owner, x, y, tile, town, self.world.land_value(x, y), self.calendar.day_serial
        )
        tile.kind = TileCategory.FIRM
        tile.ref = slot
        if slot == len(self.firms):
            self.firms.append(firm)
        else:
            self.firms[slot] = firm
        # First partial month of overhead (ref: (dim − day + 1) / dim).
        cal = self.calendar
        dim = cal.real_month_days
        firm.post_overhead((dim - cal.real_day + 1) / dim)
        return firm

    def link_b2b(self, seller: Job, buyer: Job) -> Link:
        return self.market.add_link(seller, buyer)

    def link_consumer(self, seller: Job, town: Town | None = None) -> Link:
        assert seller.product is not None
        t = town or seller.firm.town
        return self.market.add_link(seller, self.market.towns[(t.id, seller.product.id)])

    # --- daily layers --------------------------------------------------------

    def firms_daily(self) -> None:
        for firm in self.firms:
            if firm is not None:
                firm.daily(self)

    def jobs_daily(self) -> None:
        for firm in self.firms:
            if firm is not None:
                for job in firm.slots:
                    if job is not None:
                        job.post_wages(self)

    def links_daily(self) -> None:
        self.market.daily(self)

    def products_daily(self, slot: int) -> None:
        """1/30 of the catalog per day: publish the product score (design.md call 7)."""
        by_product: dict[int, list[TownMarket]] = {}
        for tm in self.market.towns.values():
            by_product.setdefault(tm.product.id, []).append(tm)
        has_links = {x.product.id for x in self.market.live_links()}
        for p in self.catalog.slot_products(slot):
            st = p.state
            if p.id not in has_links:
                st.score = PRODUCT_RULES.score_no_links
            elif sum(tm.demand_per_day for tm in by_product.get(p.id, [])) <= 0:
                st.score = 0.0
            else:
                st.score = st.max_score_in

    # --- passes ----------------------------------------------------------------

    def recompute_demand(self) -> None:
        self.ensure_markets()
        for key in sorted(self.market.towns):
            self.market.towns[key].recompute()

    def monthly(self) -> None:
        for firm in self.firms:
            if firm is not None:
                firm.monthly(self)
        self.market.monthly(self.calendar.month - 1)
        best: dict[int, float] = {}
        for link in self.market.live_links():
            pid = link.product.id
            best[pid] = max(best.get(pid, 0.0), link.score)
        for p in self.catalog.products:
            p.state.max_score_in = best.get(p.id, 0.0)

    def yearly(self) -> None:
        for firm in self.firms:
            if firm is not None:
                firm.yearly(self)
        self.diffuse_tech()

    def diffuse_tech(self) -> None:
        """design.md slice 3 call 5: generally available and obsolete at the same test."""
        r = PRODUCT_RULES
        year = self.calendar.year
        owners: dict[int, set[int]] = {}
        for firm in self.firms:
            if firm is None or firm.owner is None:
                continue
            for job in firm.jobs():
                if job.product is not None:
                    owners.setdefault(job.product.id, set()).add(firm.owner.id)
        for p in self.catalog.products:
            st = p.state
            if p.id in owners and st.discovered_year is None:
                st.discovered_year = year
            if st.discovered_year is None or st.obsolete:
                continue
            n = len(owners.get(p.id, ()))
            if n * r.diffusion_corp_weight + (year - st.discovered_year) > r.diffusion_threshold:
                st.obsolete = True

    # --- hashing -----------------------------------------------------------------

    def hash_into(self, h: hashlib._Hash) -> None:
        for p in self.catalog.products:
            st = p.state
            h.update(struct.pack("<iid?", st.tech_level, st.score_jitter, st.score, st.obsolete))
        for firm in self.firms:
            if firm is None:
                h.update(b"-")
                continue
            h.update(struct.pack("<iiiiQ", firm.id, firm.type_id, firm.x, firm.y, firm.links))
            h.update(struct.pack("<d", firm.ledger.cash))
            for job in firm.slots:
                if job is None:
                    h.update(b".")
                    continue
                h.update(
                    struct.pack(
                        "<iiddddd",
                        job.type_id,
                        job.rating,
                        job.stock,
                        job.quality,
                        job.unit_cost,
                        job.train_acc,
                        job.price,
                    )
                )
        for link in self.market.links:
            if link is None:
                h.update(b"-")
                continue
            h.update(
                struct.pack(
                    "<idddd", link.id, link.quantity, link.score, link.brand, sum(link.money_month)
                )
            )
