"""The product economy: catalog, corporations, firms, jobs and links.

`Economy` is owned by `Sim` and called from the slice-1 day order:
firms layer, jobs layer, links layer, then month/year passes and the
daily product stagger.
"""

from __future__ import annotations

import hashlib
import struct
from typing import TYPE_CHECKING

from .calendar import real_days_in_month
from .catalog import Catalog, Product, TownMarket
from .firms import (
    FIRM_CLASSES,
    N_CATEGORIES,
    OPERATING_CATEGORIES,
    Firm,
    InsufficientFunds,
    Ledger,
    MediaFirm,
    book_asset,
)
from .jobs import CAT_LOAN_INTEREST, CAT_SALARIES, CAT_SALES, CAT_STOCK_RETURN, CAT_WRITEOFFS
from .links import BRAND_CORPORATE, Market
from .news import NewsLog, random_events_daily
from .person import (
    STATE_ACTIVE,
    STATE_LINKED,
    Person,
)
from .rng import Rng
from .stock import (
    MAX_CORPS,
    Stock,
    buy_back_shares,
    buy_cost,
    buy_shares,
    compute_ai_dividend,
    daily_price_update,
    issue_shares,
    pay_dividend,
    sell_shares,
    stock_monthly,
    stock_yearly,
)
from .tables import (
    CORPORATION_RULES,
    FIRM_TYPES,
    JOB_RULES,
    PERSON_RULES,
    PRODUCT_RULES,
    STOCK_RULES,
)
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


_CR = CORPORATION_RULES
_PR = PERSON_RULES


class Corporation:
    """Corporation: owner of firms with full financial system (gamelogic.md Corporation internals)."""

    __slots__ = (
        "brand_strategy",
        "business_assets",
        "classes_per_town",
        "corp_type",
        "dividend_auto",
        "dividend_ratio",
        "id",
        "land_assets",
        "ledger",
        "liabilities",
        "manufacturing_skill",
        "market_share",
        "month_history",
        "name",
        "peak_revenue",
        "products_per_town",
        "stock_assets",
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
        # Balance-sheet accounts 2 and 3 (B1): setup costs paid and land bought.
        self.business_assets = 0.0
        self.land_assets = 0.0
        # Account 4 (S1): money moved in and out by trades in other corps' stock.
        self.stock_assets = 0.0
        self.brand_strategy = BRAND_CORPORATE
        self.products_per_town: dict[int, int] = {}
        self.classes_per_town: dict[int, int] = {}
        self.dividend_ratio = 0
        self.dividend_auto = True
        self.peak_revenue = 0.0
        self.market_share: dict[int, int] = {}
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
        return cash + inventory + self.business_assets + self.land_assets + self.stock_assets

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
        self.persons: list[Person | None] = [None] * int(_PR.max_persons)
        self.ai_states: dict[int, object] = {}
        self.stocks: list[Stock | None] = [None] * MAX_CORPS
        self.stock_enabled = True
        self.news_log = NewsLog()
        self.event_frequency = 0
        # Setup options (Sim.reset copies them from SetupOptions).
        self.initial_capital = _CR.player_initial_capital
        self.competitor_capital = 0
        self.firms: list[Firm | None] = []
        self.market = Market()
        self.market.catalog = self.catalog
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
                    tm.init_weights(self.rng)
                    self.market.towns[key] = tm

    def town_market(self, town: Town, product_name: str) -> TownMarket:
        return self.market.towns[(town.id, self.catalog[product_name].id)]

    def add_person(self, name: str, *, is_player: bool = False, randomize: bool = False) -> Person:
        slot = next((i for i, p in enumerate(self.persons) if p is None), None)
        if slot is None:
            raise RuntimeError("person array full")
        person = Person(slot, name, is_player=is_player)
        if randomize:
            person.randomize_traits(self.rng)
            person.randomize_gender(self.rng)
            person.randomize_skills(self.rng, 1)
        self.persons[slot] = person
        return person

    def active_persons(self) -> list[Person]:
        return [p for p in self.persons if p is not None and p.state in (STATE_ACTIVE,)]

    def linked_persons(self) -> list[Person]:
        from .person import STATE_LINKED

        return [p for p in self.persons if p is not None and p.state == STATE_LINKED]

    def all_persons(self) -> list[Person]:
        return [p for p in self.persons if p is not None]

    def person_count(self) -> int:
        return sum(1 for p in self.persons if p is not None)

    def competitor_count(self) -> int:
        return sum(1 for c in self.corps if c.corp_type in (CORP_AI, CORP_HIRED))

    def add_corp(self, name: str, corp_type: int = CORP_PLAYER) -> Corporation:
        corp = Corporation(len(self.corps), name, corp_type)
        self.corps.append(corp)
        if corp_type == CORP_PLAYER:
            # Initial Capital of Your Corporation (C3); native hand-off not traced.
            corp.ledger.cash = self.initial_capital
        if corp_type != CORP_GOVERNMENT and self.stock_enabled:
            initial_value = max(1.0, corp.ledger.cash)
            stock = Stock(corp.id, initial_value, STOCK_RULES.initial_price_per_share)
            if corp.id < len(self.stocks):
                self.stocks[corp.id] = stock
        return corp

    # --- share trades (audit S1, S3, S4; FUN_0003f240, FUN_0004021e) -------

    def buy_stock(self, corp: Corporation, target: int, shares: int) -> float:
        """corp buys shares of corp `target`; returns the cost.

        Another corp's stock: Cash -> Stock Assets (decomp:38407-38417); the
        target's cash isn't touched. Own stock: a buyback that retires the
        shares and lowers equity (S3, decomp:38425-38431). Refused when cash is
        short, like the stock dialogs' "Sorry, you don't have enough cash."
        (decomp:41281, 41659).
        """
        stock = self.stocks[target]
        if stock is None:
            raise ValueError("that corporation has no stock")
        if target == corp.id:
            est = buy_cost(stock, min(shares, stock.total_shares - 1))
        else:
            est = buy_cost(stock, shares)
        if corp.ledger.cash < est:
            raise InsufficientFunds(
                f"{shares:,} shares cost ${est:,.0f}; {corp.name} has ${corp.ledger.cash:,.0f}"
            )
        if target == corp.id:
            cost = buy_back_shares(stock, shares)
        else:
            cost = buy_shares(stock, "corp", corp.id, shares)
            corp.stock_assets += cost
        corp.ledger.cash -= cost
        return cost

    def sell_stock(self, corp: Corporation, target: int, shares: int) -> float:
        """corp sells shares it holds in corp `target`: Stock Assets -> Cash (S1)."""
        stock = self.stocks[target]
        if stock is None:
            raise ValueError("that corporation has no stock")
        got = sell_shares(stock, "corp", corp.id, shares)
        corp.stock_assets -= got
        corp.ledger.cash += got
        return got

    def issue_stock(self, corp: Corporation, shares: int) -> float:
        """New shares of corp's own stock: cash and equity rise by the proceeds,
        total_shares and the float by the shares (S4, FUN_0004021e decomp:38851-38885)."""
        stock = self.stocks[corp.id]
        if stock is None:
            raise ValueError("that corporation has no stock")
        got = issue_shares(stock, shares)
        corp.ledger.cash += got
        return got

    def build_firm(
        self, firm_type: int, owner: Corporation | None, x: int, y: int, town: Town
    ) -> Firm:
        if firm_type not in FIRM_CLASSES:
            raise NotImplementedError(f"firm type {firm_type} lands in systems 4b")
        if not self.world.can_build(x, y):
            raise ValueError(f"tile ({x},{y}) is not free land")
        row = FIRM_TYPES[firm_type]
        if owner is not None and not row.government:
            # FUN_000698e0 (decomp:76662-76690): Build is disabled when cash is below
            # setup cost + land value; no credit line (audit B3, corrected in #87).
            cost = row.setup_cost + self.world.land_value(x, y)
            if owner.ledger.cash < cost:
                raise InsufficientFunds(
                    f"{row.name} costs ${cost:,.0f} with land; {owner.name} has "
                    f"${owner.ledger.cash:,.0f}"
                )
        tile = self.world.tile_at(x, y)
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
        if not FIRM_TYPES[firm_type].government:
            book_asset(owner, firm.row.setup_cost, firm.land_value)
        if hasattr(firm, "initialize_audience"):
            firm.initialize_audience(self)
        # First partial month of overhead (ref: (dim − day + 1) / dim).
        cal = self.calendar
        dim = cal.real_month_days
        firm.post_overhead((dim - cal.real_day + 1) / dim)
        return firm

    def demolish_firm(self, firm: Firm) -> None:
        """Remove a firm and unbook its assets (gap audit B4).

        FUN_00063f28 (decomp:68490-68540): move setup from BizAssets to Cash,
        write it off as CAT_WRITEOFFS, floor BizAssets at 0, move land from
        LandAssets to Cash, floor LandAssets at 0.  Net cash = +land_value.
        """
        owner = firm.owner
        if owner is not None:
            setup = firm.row.setup_cost
            land = firm.land_value
            owner.business_assets -= setup
            owner.ledger.cash += setup
            owner.ledger.post(CAT_WRITEOFFS, setup)
            owner.business_assets = max(0.0, owner.business_assets)
            owner.land_assets -= land
            owner.ledger.cash += land
            owner.land_assets = max(0.0, owner.land_assets)
        self.firms[firm.id] = None
        tile = self.world.tile_at(firm.x, firm.y)
        tile.kind = TileCategory.GRASSLAND
        tile.ref = -1

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
        # W4: president/CEO salary (decomp 28817-28823)
        for person in self.persons:
            if person is not None and person.state == STATE_LINKED and person.salary > 0:
                corp = self.corps[person.corp_id]
                daily_pay = person.salary / 365.0
                corp.ledger.post(CAT_SALARIES, daily_pay)
                person.wealth += daily_pay

    def persons_daily(self, day_serial: int) -> None:
        """Staggered person processing: one person per day on a 30-day cycle."""
        from .person import STATE_LINKED

        slot = day_serial % int(_PR.max_persons)
        person = self.persons[slot] if slot < len(self.persons) else None
        if person is None:
            return
        if person.state == STATE_LINKED:
            person.years_of_service += 1 if day_serial % 365 == 0 else 0
        if person.cooldown > 0:
            person.cooldown -= 1

    def ai_daily(self, day_serial: int) -> None:
        """AI corporation decisions for all competitor corps."""
        from .ai import ai_daily, try_spawn_competitor

        try_spawn_competitor(self, day_serial)
        for corp in self.corps:
            if corp.corp_type == CORP_AI:
                ai_daily(self, corp, day_serial)

    def stocks_daily(self) -> None:
        """Daily stock price updates for all corporations."""
        if not self.stock_enabled:
            return
        for i, stock in enumerate(self.stocks):
            if stock is None:
                continue
            if i < len(self.corps):
                earnings = self.corps[i].net_profit
            else:
                earnings = 0.0
            daily_price_update(stock, self.rng, earnings)

    def events_daily(self, day_serial: int) -> None:
        """Roll for a random event (system 11)."""
        random_events_daily(
            self.rng,
            self.event_frequency,
            day_serial,
            self.news_log,
            self.corps,
            self.firms,
        )

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

    def persons_monthly(self) -> None:
        """Monthly satisfaction drift for all active/linked persons."""
        for person in self.all_persons():
            person.monthly_satisfaction_drift(self.rng)

    def persons_yearly(self) -> None:
        """Yearly service increment for linked persons."""
        from .person import STATE_LINKED

        for person in self.all_persons():
            if person.state == STATE_LINKED:
                person.years_of_service += 1

    def corps_monthly(self) -> None:
        """Corporation monthly pass — runs before firms monthly."""
        for corp in self.corps:
            corp.monthly(self.firms)
        self.adjust_interest_rate()

    def monthly(self) -> None:
        for firm in self.firms:
            if firm is not None:
                firm.monthly(self)
        prev_m = self.calendar.month - 1 if self.calendar.month > 1 else 12
        prev_y = self.calendar.year if self.calendar.month > 1 else self.calendar.year - 1
        self._compute_market_shares(real_days_in_month(prev_y, prev_m))
        self.market.monthly(self.calendar.month - 1, self)
        for tm in self.market.towns.values():
            tm.recompute_weights()
            tm.random_walk_refs(self.rng)
            tm.last_month_unmet_demand_sum = tm.unmet_demand_sum
            tm.unmet_demand_sum = 0.0
            tm.last_month_unmet_demand_value_sum = tm.unmet_demand_value_sum
            tm.unmet_demand_value_sum = 0.0

    def _compute_market_shares(self, days_in_month: int) -> None:
        """K1: prorated market share (native 0xa96b4/0xa99ed = 31).

        projected = this_month_sum + (31 - days_in_month) * last_month_sum / 31.
        For 31-day months the proration factor is 0; shorter months get a boost
        from last month's data to normalize to a 31-day equivalent.
        """
        prorate = (31 - days_in_month) / 31.0
        corp_sums: dict[int, dict[int, float]] = {}
        product_totals: dict[int, float] = {}
        for link in self.market.live_links():
            if not link.consumer:
                continue
            pid = link.product.id
            owner = link.seller.firm.owner
            if owner is None:
                continue
            cid = owner.id
            projected = link.quantity_sum + prorate * link.quantity_prev
            corp_sums.setdefault(cid, {})
            corp_sums[cid][pid] = corp_sums[cid].get(pid, 0.0) + projected
            product_totals[pid] = product_totals.get(pid, 0.0) + projected
        for tm in self.market.towns.values():
            pid = tm.product.id
            projected_unmet = tm.unmet_demand_sum + prorate * tm.last_month_unmet_demand_sum
            product_totals[pid] = product_totals.get(pid, 0.0) + projected_unmet
        for corp in self.corps:
            corp.market_share.clear()
            sums = corp_sums.get(corp.id, {})
            for pid, corp_sum in sums.items():
                total = product_totals.get(pid, 0.0)
                if total > 0:
                    corp.market_share[pid] = min(100, round(corp_sum * 100.0 / total))

    def stocks_monthly(self) -> None:
        if not self.stock_enabled:
            return
        for stock in self.stocks:
            if stock is not None:
                stock_monthly(stock)

    def corps_yearly(self) -> None:
        """Corporation yearly pass — runs before firms yearly."""
        # R4: pay dividends before roll_year() wipes year accumulators
        if self.stock_enabled:
            self._pay_dividends()
        for corp in self.corps:
            corp.yearly(self.firms)
        self.interest_rate_history.append(self.interest_rate)
        if len(self.interest_rate_history) > 10:
            self.interest_rate_history.pop(0)

    def _pay_dividends(self) -> None:
        """Year-end dividend distribution for all corps with stocks."""
        person_for_corp: dict[int, Person] = {}
        for p in self.persons:
            if p is not None and p.state == STATE_LINKED and p.corp_id is not None:
                person_for_corp[p.corp_id] = p
        for i, stock in enumerate(self.stocks):
            if stock is None or i >= len(self.corps):
                continue
            corp = self.corps[i]
            earnings = corp.net_profit
            person = person_for_corp.get(i)
            if corp.dividend_auto:
                leadership = person.trait7 if person else 50
                payout = compute_ai_dividend(
                    stock,
                    corp.total_assets(self.firms),
                    corp.ledger.cash,
                    corp.stock_assets,
                    earnings,
                    leadership,
                    self.rng,
                )
            else:
                payout = earnings * corp.dividend_ratio / 100.0
            if payout <= 0:
                continue
            dist = pay_dividend(stock, payout)
            for cid, amount in dist["corps"]:
                if cid < len(self.corps):
                    # Dividend income: record in CAT_STOCK_RETURN and add cash
                    # (Ledger.post would subtract cash for non-SALES cats).
                    rcorp = self.corps[cid]
                    for arr in (rcorp.ledger.month, rcorp.ledger.year, rcorp.ledger.total):
                        arr[CAT_STOCK_RETURN] += amount
                    rcorp.ledger.cash += amount
            for pid, amount in dist["persons"]:
                if pid < len(self.persons) and self.persons[pid] is not None:
                    self.persons[pid].wealth += amount
            corp.ledger.cash -= payout

    def stocks_yearly(self) -> None:
        if not self.stock_enabled:
            return
        for i, stock in enumerate(self.stocks):
            if stock is None:
                continue
            earnings = 0.0
            if i < len(self.corps):
                earnings = self.corps[i].net_profit
            stock_yearly(stock, earnings)

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
            self.interest_rate = max(
                _CR.interest_rate_floor, self.interest_rate - _CR.interest_rate_step
            )

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
            if hasattr(firm, "reserve"):
                h.update(struct.pack("<d", firm.reserve))

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
        for person in self.persons:
            if person is None:
                h.update(b"_")
                continue
            h.update(struct.pack("<iii", person.id, person.state, person.satisfaction))
        for stock in self.stocks:
            if stock is None:
                h.update(b"~")
                continue
            h.update(struct.pack("<id", stock.total_shares, stock.price))
        h.update(struct.pack("<i", len(self.news_log)))
        h.update(struct.pack("<i", self.event_frequency))
        for link in self.market.links:
            if link is None:
                h.update(b"-")
                continue
            h.update(
                struct.pack(
                    "<iddddd",
                    link.id,
                    link.quantity,
                    link.score,
                    link.brand,
                    link.awareness,
                    sum(link.money_month),
                )
            )
