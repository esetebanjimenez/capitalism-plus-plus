"""News log and random events (system 11).

The news log is a circular buffer of up to ``NEWS_RULES.buffer_capacity``
items.  Random events fire during the daily batch when the frequency
setting is non-zero; each has an optional internal probability gate.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from enum import IntEnum
from typing import TYPE_CHECKING

from .tables import EVENT_RULES, FIRM_TYPES, JOB_TYPES, NEWS_RULES

if TYPE_CHECKING:
    from .rng import Rng

_ER = EVENT_RULES


# ---------------------------------------------------------------------------
# News categories (filter buckets for the News Report panel)
# ---------------------------------------------------------------------------


class NewsCategory(IntEnum):
    NORMAL = 0
    FINANCIAL = 1
    TECHNOLOGY = 2
    SPECIAL = 3


# ---------------------------------------------------------------------------
# News event types (28 distinct types)
# ---------------------------------------------------------------------------


class NewsType(IntEnum):
    FIRM_OPENED = 1
    FIRM_CLOSED = 2
    BANK_LOAN = 3
    LOAN_REPAID = 4
    SHARES_ISSUED = 5
    SHARE_TRADE = 6
    ANNUAL_DIVIDEND = 7
    TENDER_OFFER = 8
    NEW_COMPETITOR = 9
    BANKRUPTCY = 10
    CONTROL_CHANGE = 11
    MERGER = 12
    PRICE_WAR = 13
    INDUSTRY_DOMINANCE = 14
    CEO_RETIREMENT = 15
    CEO_SUCCESSION = 16
    RND_INVENTION = 17
    PRODUCT_MADE_PUBLIC = 18
    RESOURCE_EXHAUSTED = 19
    RESOURCE_DISCOVERED = 20
    RESOURCE_ON_SITE = 21
    CITY_FOUNDED = 22
    LIVESTOCK_DISEASE = 23
    BUILDING_DESTROYED = 24
    CROP_FAILURE = 25
    RND_BREAKTHROUGH = 26
    INVENTORY_LOSS = 27
    ECONOMIC_DOWNTURN = 28


_NEWS_CATEGORY: dict[NewsType, NewsCategory] = {
    NewsType.FIRM_OPENED: NewsCategory.NORMAL,
    NewsType.FIRM_CLOSED: NewsCategory.NORMAL,
    NewsType.BANK_LOAN: NewsCategory.FINANCIAL,
    NewsType.LOAN_REPAID: NewsCategory.FINANCIAL,
    NewsType.SHARES_ISSUED: NewsCategory.FINANCIAL,
    NewsType.SHARE_TRADE: NewsCategory.FINANCIAL,
    NewsType.ANNUAL_DIVIDEND: NewsCategory.FINANCIAL,
    NewsType.TENDER_OFFER: NewsCategory.FINANCIAL,
    NewsType.NEW_COMPETITOR: NewsCategory.SPECIAL,
    NewsType.BANKRUPTCY: NewsCategory.SPECIAL,
    NewsType.CONTROL_CHANGE: NewsCategory.SPECIAL,
    NewsType.MERGER: NewsCategory.SPECIAL,
    NewsType.PRICE_WAR: NewsCategory.SPECIAL,
    NewsType.INDUSTRY_DOMINANCE: NewsCategory.SPECIAL,
    NewsType.CEO_RETIREMENT: NewsCategory.SPECIAL,
    NewsType.CEO_SUCCESSION: NewsCategory.SPECIAL,
    NewsType.RND_INVENTION: NewsCategory.TECHNOLOGY,
    NewsType.PRODUCT_MADE_PUBLIC: NewsCategory.TECHNOLOGY,
    NewsType.RESOURCE_EXHAUSTED: NewsCategory.SPECIAL,
    NewsType.RESOURCE_DISCOVERED: NewsCategory.SPECIAL,
    NewsType.RESOURCE_ON_SITE: NewsCategory.SPECIAL,
    NewsType.CITY_FOUNDED: NewsCategory.SPECIAL,
    NewsType.LIVESTOCK_DISEASE: NewsCategory.SPECIAL,
    NewsType.BUILDING_DESTROYED: NewsCategory.SPECIAL,
    NewsType.CROP_FAILURE: NewsCategory.SPECIAL,
    NewsType.RND_BREAKTHROUGH: NewsCategory.TECHNOLOGY,
    NewsType.INVENTORY_LOSS: NewsCategory.SPECIAL,
    NewsType.ECONOMIC_DOWNTURN: NewsCategory.SPECIAL,
}

_UNIMPORTANT: frozenset[NewsType] = frozenset(
    {
        NewsType.FIRM_OPENED,
        NewsType.FIRM_CLOSED,
        NewsType.NEW_COMPETITOR,
        NewsType.BANKRUPTCY,
        NewsType.BANK_LOAN,
        NewsType.LOAN_REPAID,
        NewsType.SHARES_ISSUED,
    }
)


# ---------------------------------------------------------------------------
# NewsItem
# ---------------------------------------------------------------------------


class NewsItem:
    __slots__ = (
        "category",
        "corp_id",
        "day_serial",
        "details",
        "important",
        "news_type",
    )

    def __init__(
        self,
        news_type: NewsType,
        day_serial: int,
        corp_id: int = -1,
        details: dict[str, object] | None = None,
    ) -> None:
        self.news_type = news_type
        self.day_serial = day_serial
        self.corp_id = corp_id
        self.category = _NEWS_CATEGORY[news_type]
        self.important = news_type not in _UNIMPORTANT
        self.details: dict[str, object] = details or {}


# ---------------------------------------------------------------------------
# NewsLog — circular buffer
# ---------------------------------------------------------------------------


class NewsLog:
    __slots__ = ("_buffer", "_capacity")

    def __init__(self, capacity: int | None = None) -> None:
        self._capacity = capacity or int(NEWS_RULES.buffer_capacity)
        self._buffer: deque[NewsItem] = deque(maxlen=self._capacity)

    def post(self, item: NewsItem) -> None:
        self._buffer.append(item)

    def __len__(self) -> int:
        return len(self._buffer)

    def __iter__(self):
        return iter(self._buffer)

    @property
    def items(self) -> list[NewsItem]:
        return list(self._buffer)

    def by_category(self, category: NewsCategory) -> list[NewsItem]:
        return [it for it in self._buffer if it.category == category]

    def by_corp(self, corp_id: int) -> list[NewsItem]:
        return [it for it in self._buffer if it.corp_id == corp_id]

    def important_items(self) -> list[NewsItem]:
        return [it for it in self._buffer if it.important]


# ---------------------------------------------------------------------------
# Event frequency
# ---------------------------------------------------------------------------

FREQ_NONE = 0
FREQ_LOW = 1
FREQ_MEDIUM = 2
FREQ_HIGH = 3

_FREQ_DENOMINATORS: dict[int, int] = {
    FREQ_LOW: int(_ER.freq_low_denominator),
    FREQ_MEDIUM: int(_ER.freq_medium_denominator),
    FREQ_HIGH: int(_ER.freq_high_denominator),
}


def _should_fire(rng: Rng, frequency: int) -> bool:
    if frequency == FREQ_NONE:
        return False
    denom = _FREQ_DENOMINATORS[frequency]
    return rng.randint(1, denom) == 1


# ---------------------------------------------------------------------------
# Random event dispatch
# ---------------------------------------------------------------------------

# Firm and job type ids from the DB (firm_types, job_types), looked up by name.
_FIRM = {r.name: r.id for r in FIRM_TYPES.values()}
_JOB = {r.name: r.id for r in JOB_TYPES.values()}
FARM, RND_CENTER, DEPT_STORE = _FIRM["Farm"], _FIRM["R&D Center"], _FIRM["Department Store"]
CROP_GROWING, LIVESTOCK_RAISING = _JOB["Crop Growing"], _JOB["Livestock Raising"]
RESEARCH = _JOB["Research & Development"]


def _owned(firms: list, corp: object, firm_type: int) -> list:
    return [f for f in firms if f is not None and f.owner is corp and f.row.id == firm_type]


def _jobs_of(firm: object, job_type: int) -> list:
    return [j for j in firm.jobs() if j.row.id == job_type]  # type: ignore[attr-defined]


def _corp_id(firm: object) -> int:
    owner = getattr(firm, "owner", None)
    return owner.id if owner is not None else -1


EVENT_LIVESTOCK_DISEASE = 0
EVENT_BUILDING_DESTROYED = 1
EVENT_CROP_FAILURE = 2
EVENT_RND_BREAKTHROUGH = 3
EVENT_INVENTORY_LOSS = 4
EVENT_ECONOMIC_DOWNTURN = 5


def random_events_daily(
    rng: Rng,
    frequency: int,
    day_serial: int,
    news_log: NewsLog,
    corps: list,
    firms: list,
    remove_firm: Callable[[object], None] | None = None,
) -> NewsItem | None:
    """Roll for a random event. Returns the news item if one fired, else None.

    `remove_firm` takes a destroyed firm off the map (Economy.demolish_firm); without one the
    firm's slot in `firms` is cleared, which is only enough for bare test lists."""
    if not _should_fire(rng, frequency):
        return None

    event_id = rng.randint(0, int(_ER.event_type_count) - 1)

    if event_id == EVENT_LIVESTOCK_DISEASE:
        return _event_livestock_disease(rng, day_serial, news_log, corps, firms)
    if event_id == EVENT_BUILDING_DESTROYED:
        return _event_building_destroyed(rng, day_serial, news_log, firms, remove_firm)
    if event_id == EVENT_CROP_FAILURE:
        return _event_crop_failure(rng, day_serial, news_log, corps, firms)
    if event_id == EVENT_RND_BREAKTHROUGH:
        return _event_rnd_breakthrough(rng, day_serial, news_log, corps, firms)
    if event_id == EVENT_INVENTORY_LOSS:
        return _event_inventory_loss(rng, day_serial, news_log, corps, firms)
    return _event_economic_downturn(rng, day_serial, news_log, corps, firms)


# ---------------------------------------------------------------------------
# Individual event implementations
# ---------------------------------------------------------------------------


def _event_livestock_disease(
    rng: Rng,
    day_serial: int,
    news_log: NewsLog,
    corps: list,
    firms: list,
) -> NewsItem | None:
    if not corps:
        return None
    corp = rng.choice(corps)
    farm_firms = _owned(firms, corp, FARM)
    if not farm_firms:
        return None
    divisor = rng.randint(int(_ER.disease_divisor_lo), int(_ER.disease_divisor_hi))
    affected = 0
    for farm in farm_firms:
        for job in _jobs_of(farm, LIVESTOCK_RAISING):
            # The herd (young and grown pools) is divided by the rolled divisor.
            if job.young + job.grown > 0:
                job.young /= divisor
                job.grown /= divisor
                job.stock = round(job.young)
                affected += 1
    if affected == 0:
        return None
    item = NewsItem(
        NewsType.LIVESTOCK_DISEASE,
        day_serial,
        corp_id=corp.id,
        details={"divisor": divisor, "farms_affected": affected},
    )
    news_log.post(item)
    return item


def _event_building_destroyed(
    rng: Rng,
    day_serial: int,
    news_log: NewsLog,
    firms: list,
    remove_firm: Callable[[object], None] | None,
) -> NewsItem | None:
    if rng.random() >= _ER.destruction_gate:
        return None
    live_firms = [f for f in firms if f is not None]
    if not live_firms:
        return None
    firm = rng.choice(live_firms)
    corp_id = _corp_id(firm)
    firm_idx = firms.index(firm)
    if remove_firm is not None:
        remove_firm(firm)  # same path as demolish: assets, tile, links
    else:
        firms[firm_idx] = None
    item = NewsItem(
        NewsType.BUILDING_DESTROYED,
        day_serial,
        corp_id=corp_id,
        details={
            "firm_id": getattr(firm, "id", firm_idx),
            # The firm is gone once the item is read, so keep its type for the headline.
            "firm_type": getattr(getattr(firm, "row", None), "id", None),
        },
    )
    news_log.post(item)
    return item


def _event_crop_failure(
    rng: Rng,
    day_serial: int,
    news_log: NewsLog,
    corps: list,
    firms: list,
) -> NewsItem | None:
    if not corps:
        return None
    corp = rng.choice(corps)
    farm_firms = _owned(firms, corp, FARM)
    if not farm_firms:
        return None
    affected = 0
    for farm in farm_firms:
        for job in _jobs_of(farm, CROP_GROWING):
            # The growing crop (its stock) is lost.
            if job.stock > 0:
                job.stock = 0.0
                affected += 1
    if affected == 0:
        return None
    item = NewsItem(
        NewsType.CROP_FAILURE,
        day_serial,
        corp_id=corp.id,
        details={"farms_affected": affected},
    )
    news_log.post(item)
    return item


def _event_rnd_breakthrough(
    rng: Rng,
    day_serial: int,
    news_log: NewsLog,
    corps: list,
    firms: list,
) -> NewsItem | None:
    def active_jobs(firm: object) -> list:
        return [j for j in _jobs_of(firm, RESEARCH) if j.project is not None and j.project.started]

    active = [f for f in firms if f is not None and f.row.id == RND_CENTER and active_jobs(f)]
    if not active:
        return None
    firm = rng.choice(active)
    job = rng.choice(active_jobs(firm))
    progress = rng.randint(int(_ER.breakthrough_progress_lo), int(_ER.breakthrough_progress_hi))
    job.project.elapsed_days += progress  # days of project progress
    corp_id = _corp_id(firm)
    item = NewsItem(
        NewsType.RND_BREAKTHROUGH,
        day_serial,
        corp_id=corp_id,
        details={
            "progress_added": progress,
            "product": getattr(job.product, "name", "unknown"),
        },
    )
    news_log.post(item)
    return item


def _event_inventory_loss(
    rng: Rng,
    day_serial: int,
    news_log: NewsLog,
    corps: list,
    firms: list,
) -> NewsItem | None:
    if rng.random() >= _ER.blackout_gate:
        return None
    if not corps:
        return None
    corp = rng.choice(corps)
    stores = _owned(firms, corp, DEPT_STORE)
    if not stores:
        return None
    total_loss = 0.0
    for store in stores:
        for job in store.jobs():
            loss_units = rng.randint(0, int(_ER.blackout_max_loss))
            actual_loss = min(loss_units, job.stock)
            if actual_loss > 0:
                job.stock -= actual_loss
                total_loss += actual_loss * job.unit_cost
    item = NewsItem(
        NewsType.INVENTORY_LOSS,
        day_serial,
        corp_id=corp.id,
        details={"total_loss": total_loss},
    )
    news_log.post(item)
    return item


def _event_economic_downturn(
    rng: Rng,
    day_serial: int,
    news_log: NewsLog,
    corps: list,
    firms: list,
) -> NewsItem | None:
    if rng.random() >= _ER.downturn_gate:
        return None
    if not corps:
        return None
    loss_frac = rng.uniform(_ER.downturn_loss_lo, _ER.downturn_loss_hi)
    total_loss = 0.0
    for corp in corps:
        net_worth = corp.net_worth(firms)
        if net_worth > 0:
            loss = net_worth * loss_frac
            corp.ledger.cash -= loss
            total_loss += loss
    item = NewsItem(
        NewsType.ECONOMIC_DOWNTURN,
        day_serial,
        details={"loss_fraction": loss_frac, "total_loss": total_loss},
    )
    news_log.post(item)
    return item
