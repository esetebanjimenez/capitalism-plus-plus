"""The product economy: catalog, corporations, firms, jobs and links.

`Economy` is owned by `Sim` and called from the slice-1 day order:
firms layer, jobs layer, links layer, then month/year passes and the
daily product stagger.
"""

from __future__ import annotations

import hashlib
import struct
from typing import TYPE_CHECKING

from .catalog import Catalog, Product, TownMarket
from .firms import FIRM_CLASSES, N_CATEGORIES, OPERATING_CATEGORIES, Firm, Ledger, MediaFirm
from .jobs import CAT_LOAN_INTEREST, CAT_SALES
from .links import Market
from .rng import Rng
from .tables import CORPORATION_RULES, JOB_RULES, PRODUCT_RULES
from .world import TileCategory

if TYPE_CHECKING:
    from .calendar import Calendar
    from .jobs import Job
    from .links import Link
    from .town import Town
    from .world import World

CORP_PLAYER = 1
CORP_HIRED = 2
CORP_AI = 3
CORP_GOVERNMENT = 4

BRAND_CORPORATE = 0
BRAND_RANGE = 1
BRAND_UNIQUE = 2

_CR = CORPORATION_RULES


class Corporation:
    """Corporation: owner of firms with full financial system (gamelogic.md Corporation internals)."""

    __slots__ = (
        "brand_strategy",
        "corp_type",
        "dividend_auto",
        "dividend_ratio",
        "id",
        "ledger",
        "liabilities",
        "manufacturing_skill",
        "month_history",
        "name",
        "peak_revenue",
        "technology",
        "training_budget",
        "year_history",
    )

    def __init__(self, corp_id: int, name: str, corp_type: int = CORP_PLAYER) -> None:
        self.id = corp_id
        self.name = name
        self.corp_type = corp_type
        self.ledger = Ledger()
        self.technology: dict[int, int] = {}
        self.manufacturing_skill = 0
        self.training_budget = JOB_RULES.corp_training_budget_default
        self.liabilities = 0.0
        self.brand_strategy = BRAND_CORPORATE
        self.dividend_ratio = 0
        self.dividend_auto = True
        self.peak_revenue = 0.0
        self.month_history: dict[str, list[float]] = {
            "revenue": [],
            "operating_profit": [],
            "other_profit": [],
            "expenses": [],
            "net_worth": [],
        }
        self.year_history: dict[str, list[float]] = {
            "revenue": [],
            "operating_profit": [],
            "other_profit": [],
            "expenses": [],
            "net_worth": [],
        }

    # --- technology ---------------------------------------------------------

    def technology_level(self, product: Product) -> int:
        return self.technology.get(product.id, 0)

    def has_technology(self, product: Product | int) -> bool:
        key = product if isinstance(product, int) else product.id
        return self.technology.get(key, 0) > 0

    def add_technology(self, product: Product, level: int | None = None) -> None:
        self.technology[product.id] = self.technology_level(product) + 1 if level is None else level

    # --- income statement ---------------------------------------------------

    @property
    def revenue(self) -> float:
        return self.ledger.month[CAT_SALES]

    @property
    def operating_expenses(self) -> float:
        return sum(self.ledger.month[i] for i in range(1, OPERATING_CATEGORIES))

    @property
    def operating_profit(self) -> float:
        return self.revenue - self.operating_expenses

    @property
    def other_profit(self) -> float:
        return sum(self.ledger.month[i] for i in range(OPERATING_CATEGORIES, N_CATEGORIES))

    @property
    def net_profit(self) -> float:
        return self.operating_profit + self.other_profit

    @property
    def cost_of_sales(self) -> float:
        """Purchase Cost + Freight Cost + Raw Material Reserve (cats 4+5+8)."""
        m = self.ledger.month
        return m[4] + m[5] + m[8]

    # --- balance sheet ------------------------------------------------------

    def total_assets(self, firms: list[Firm | None]) -> float:
        cash = self.ledger.cash
        inventory = sum(
            j.stock * j.unit_cost
            for f in firms
            if f is not None and f.owner is self
            for j in f.jobs()
            if j.stock > 0
        )
        business = sum(f.row.overhead_month * 12 for f in firms if f is not None and f.owner is self)
        land = sum(f.land_value for f in firms if f is not None and f.owner is self)
        return cash + inventory + business + land

    def net_worth(self, firms: list[Firm | None]) -> float:
        return self.total_assets(firms) - self.liabilities

    # --- bank loans ---------------------------------------------------------

    def credit_limit(self, firms: list[Firm | None]) -> float:
        return max(0.0, self.total_assets(firms) - self.liabilities)

    def borrow(self, amount: float) -> None:
        if amount <= 0:
            return
        self.ledger.cash += amount
        self.liabilities += amount

    def repay(self, amount: float) -> None:
        if amount <= 0:
            return
        actual = min(amount, self.liabilities, max(0.0, self.ledger.cash))
        self.ledger.cash -= actual
        self.liabilities -= actual

    # --- daily finance ------------------------------------------------------

    def daily_finance(self, interest_rate: float) -> None:
        """Overdraft and debt interest (gamelogic.md Cash flow and daily finance)."""
        cash = self.ledger.cash
        if cash < 0:
            daily_rate = (interest_rate + _CR.overdraft_spread) / 100.0 / 365.0
            charge = abs(cash) * daily_rate
            self.ledger.post(CAT_LOAN_INTEREST, charge)
            self.liabilities += charge
        if self.liabilities > 0:
            daily_rate = interest_rate / 100.0 / 365.0
            charge = self.liabilities * daily_rate
            self.ledger.post(CAT_LOAN_INTEREST, charge)

    # --- monthly/yearly processing ------------------------------------------

    def monthly(self, firms: list[Firm | None]) -> None:
        """Corporation monthly (gamelogic.md Monthly and yearly processing)."""
        rev = self.ledger.month[CAT_SALES]
        self.peak_revenue = max(self.peak_revenue, rev)
        nw = self.net_worth(firms)
        self._push_history(
            self.month_history,
            12,
            rev,
            self.operating_profit,
            self.other_profit,
            self.operating_expenses,
            nw,
        )
        self.ledger.roll_month()

    def yearly(self, firms: list[Firm | None]) -> None:
        """Corporation yearly (gamelogic.md Monthly and yearly processing)."""
        rev = self.ledger.year[CAT_SALES]
        expenses = sum(self.ledger.year[i] for i in range(1, OPERATING_CATEGORIES))
        op_profit = rev - expenses
        other = sum(self.ledger.year[i] for i in range(OPERATING_CATEGORIES, N_CATEGORIES))
        nw = self.net_worth(firms)
        self._push_history(self.year_history, 30, rev, op_profit, other, expenses, nw)
        self.ledger.roll_year()

    @staticmethod
    def _push_history(
        store: dict[str, list[float]],
        cap: int,
        revenue: float,
        op_profit: float,
        other_profit: float,
        expenses: float,
        net_worth: float,
    ) -> None:
        vals = {
            "revenue": revenue,
            "operating_profit": op_profit,
            "other_profit": other_profit,
            "expenses": expenses,
            "net_worth": net_worth,
        }
        for key, val in vals.items():
            arr = store[key]
            arr.append(val)
            if len(arr) > cap:
                arr.pop(0)

    @property
    def is_bankrupt(self) -> bool:
        return self.ledger.cash < 0


class Economy:
    def __init__(self, calendar: Calendar, world: World, rng: Rng) -> None:
        self.calendar = calendar
        self.world = world
        self.rng = rng
        self.catalog = Catalog()
        self.catalog.jitter(rng)
        self.corps: list[Corporation] = []
        self.firms: list[Firm | None] = []
        self.market = Market()
        self.interest_rate = _CR.interest_rate_default
        self.interest_rate_history: list[float] = [_CR.interest_rate_default]
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

    def add_corp(self, name: str, corp_type: int = CORP_PLAYER) -> Corporation:
        corp = Corporation(len(self.corps), name, corp_type)
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
        if hasattr(firm, "initialize_audience"):
            firm.initialize_audience(self)
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

    def media_firms(self, town: Town) -> list[Firm]:
        """Same-town payroll-only television, radio and newspaper firms."""
        return [
            f
            for f in self.firms
            if f is not None and f.town.id == town.id and isinstance(f, MediaFirm)
        ]

    def media_firm(self, town: Town) -> Firm:
        candidates = self.media_firms(town)
        if not candidates:
            raise LookupError("no media firm in town")
        return candidates[0]

    # --- daily layers --------------------------------------------------------

    def firms_daily(self) -> None:
        for firm in self.firms:
            if firm is not None:
                firm.daily(self)

    def jobs_daily(self) -> None:
        for firm in self.firms:
            if firm is not None:
                for job in firm.jobs():
                    if job is not None:
                        job.post_wages(self)

    def links_daily(self) -> None:
        self.market.daily(self)

    def corps_daily(self) -> None:
        for corp in self.corps:
            corp.daily_finance(self.interest_rate)

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

    def corps_monthly(self) -> None:
        """Corporation monthly pass — runs before firms monthly."""
        for corp in self.corps:
            corp.monthly(self.firms)
        self.adjust_interest_rate()

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

    def corps_yearly(self) -> None:
        """Corporation yearly pass — runs before firms yearly."""
        for corp in self.corps:
            corp.yearly(self.firms)
        self.interest_rate_history.append(self.interest_rate)
        if len(self.interest_rate_history) > 10:
            self.interest_rate_history.pop(0)

    def yearly(self) -> None:
        for firm in self.firms:
            if firm is not None:
                firm.yearly(self)
        self.diffuse_tech()

    def adjust_interest_rate(self) -> None:
        """Monthly interest rate adjustment (gamelogic.md Interest rates)."""
        towns = self.world.towns
        if not towns:
            return
        avg_gnp = sum(t.per_capita_gnp for t in towns) / len(towns) / 1000.0
        if avg_gnp <= _CR.weak_gnp_threshold or self.rng.chance(1.0 / _CR.interest_rise_chance):
            self.interest_rate += _CR.interest_rate_step
        if self.rng.chance(1.0 / _CR.interest_fall_chance):
            self.interest_rate = max(_CR.interest_rate_floor, self.interest_rate - _CR.interest_rate_step)

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
            h.update(struct.pack("<id", firm.owner.id if firm.owner else -1, firm.ledger.cash))

            for job in firm.jobs():
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
                        job.train_credits,
                        job.price,
                    )
                )
                h.update(struct.pack("<i", job.train_progress))
        for corp in self.corps:
            h.update(struct.pack("<i", corp.id))
            for product_id, level in corp.technology.items():
                h.update(struct.pack("<ii", product_id, level))
        for link in self.market.links:
            if link is None:
                h.update(b"-")
                continue
            h.update(
                struct.pack(
                    "<idddd", link.id, link.quantity, link.score, link.brand, sum(link.money_month)
                )
            )
