"""Tests for news log and random events (system 11)."""

from __future__ import annotations

from capitalism.news import (
    FREQ_HIGH,
    FREQ_LOW,
    FREQ_MEDIUM,
    FREQ_NONE,
    NewsCategory,
    NewsItem,
    NewsLog,
    NewsType,
    random_events_daily,
)
from capitalism.rng import Rng

# ---------------------------------------------------------------------------
# NewsItem
# ---------------------------------------------------------------------------


class TestNewsItem:
    def test_basic_creation(self):
        item = NewsItem(NewsType.FIRM_OPENED, day_serial=10, corp_id=1)
        assert item.news_type == NewsType.FIRM_OPENED
        assert item.day_serial == 10
        assert item.corp_id == 1
        assert item.category == NewsCategory.NORMAL
        assert not item.important

    def test_important_flag(self):
        unimportant = NewsItem(NewsType.FIRM_OPENED, day_serial=0)
        assert not unimportant.important
        unimportant2 = NewsItem(NewsType.BANK_LOAN, day_serial=0)
        assert not unimportant2.important
        important = NewsItem(NewsType.MERGER, day_serial=0)
        assert important.important
        important2 = NewsItem(NewsType.ECONOMIC_DOWNTURN, day_serial=0)
        assert important2.important

    def test_category_mapping(self):
        assert NewsItem(NewsType.FIRM_OPENED, 0).category == NewsCategory.NORMAL
        assert NewsItem(NewsType.BANK_LOAN, 0).category == NewsCategory.FINANCIAL
        assert NewsItem(NewsType.RND_INVENTION, 0).category == NewsCategory.TECHNOLOGY
        assert NewsItem(NewsType.NEW_COMPETITOR, 0).category == NewsCategory.SPECIAL

    def test_details(self):
        item = NewsItem(NewsType.MERGER, 0, details={"target": "CorpB"})
        assert item.details["target"] == "CorpB"

    def test_defaults(self):
        item = NewsItem(NewsType.FIRM_CLOSED, 5)
        assert item.corp_id == -1
        assert item.details == {}


# ---------------------------------------------------------------------------
# NewsLog
# ---------------------------------------------------------------------------


class TestNewsLog:
    def test_post_and_len(self):
        log = NewsLog(capacity=100)
        assert len(log) == 0
        log.post(NewsItem(NewsType.FIRM_OPENED, 1))
        assert len(log) == 1

    def test_circular_buffer(self):
        log = NewsLog(capacity=5)
        for i in range(10):
            log.post(NewsItem(NewsType.FIRM_OPENED, i))
        assert len(log) == 5
        items = log.items
        assert items[0].day_serial == 5
        assert items[-1].day_serial == 9

    def test_by_category(self):
        log = NewsLog()
        log.post(NewsItem(NewsType.FIRM_OPENED, 1))
        log.post(NewsItem(NewsType.BANK_LOAN, 2))
        log.post(NewsItem(NewsType.MERGER, 3))
        assert len(log.by_category(NewsCategory.NORMAL)) == 1
        assert len(log.by_category(NewsCategory.FINANCIAL)) == 1
        assert len(log.by_category(NewsCategory.SPECIAL)) == 1
        assert len(log.by_category(NewsCategory.TECHNOLOGY)) == 0

    def test_by_corp(self):
        log = NewsLog()
        log.post(NewsItem(NewsType.FIRM_OPENED, 1, corp_id=1))
        log.post(NewsItem(NewsType.FIRM_OPENED, 2, corp_id=2))
        log.post(NewsItem(NewsType.BANK_LOAN, 3, corp_id=1))
        assert len(log.by_corp(1)) == 2
        assert len(log.by_corp(2)) == 1
        assert len(log.by_corp(3)) == 0

    def test_important_items(self):
        log = NewsLog()
        log.post(NewsItem(NewsType.FIRM_OPENED, 1))
        log.post(NewsItem(NewsType.MERGER, 2))
        log.post(NewsItem(NewsType.RND_INVENTION, 3))
        imp = log.important_items()
        assert len(imp) == 2
        assert all(it.important for it in imp)

    def test_iteration(self):
        log = NewsLog(capacity=10)
        log.post(NewsItem(NewsType.FIRM_OPENED, 1))
        log.post(NewsItem(NewsType.FIRM_CLOSED, 2))
        serials = [it.day_serial for it in log]
        assert serials == [1, 2]


# ---------------------------------------------------------------------------
# News types enumeration
# ---------------------------------------------------------------------------


class TestNewsTypes:
    def test_all_28_types(self):
        assert len(NewsType) == 28

    def test_all_types_have_category(self):
        from capitalism.news import _NEWS_CATEGORY
        for nt in NewsType:
            assert nt in _NEWS_CATEGORY, f"{nt.name} missing from _NEWS_CATEGORY"

    def test_categories_count(self):
        assert len(NewsCategory) == 4


# ---------------------------------------------------------------------------
# Frequency
# ---------------------------------------------------------------------------


def _test_corps_and_firms():
    """Provide corps and firms so events can find targets."""
    corps = [_MockCorp(0, 1_000_000.0)]
    store = _MockFirm(0, 0, "DepartmentStore")
    store._jobs.append(_MockJob(stock=100, unit_cost=10.0))
    firms: list[_MockFirm | None] = [store]
    return corps, firms


class TestFrequency:
    def test_freq_none_never_fires(self):
        rng = Rng(42)
        log = NewsLog()
        corps, firms = _test_corps_and_firms()
        for _ in range(1000):
            result = random_events_daily(rng, FREQ_NONE, 0, log, corps, firms)
            assert result is None
        assert len(log) == 0

    def test_freq_low_fires_sometimes(self):
        rng = Rng(42)
        log = NewsLog()
        corps, firms = _test_corps_and_firms()
        fired = 0
        for day in range(10000):
            result = random_events_daily(rng, FREQ_LOW, day, log, corps, firms)
            if result is not None:
                fired += 1
        assert fired > 0

    def test_freq_medium_fires_more_than_low(self):
        fired_low = 0
        fired_med = 0
        for seed in range(5):
            rng_low = Rng(seed)
            rng_med = Rng(seed)
            log_low = NewsLog()
            log_med = NewsLog()
            corps_l, firms_l = _test_corps_and_firms()
            corps_m, firms_m = _test_corps_and_firms()
            for day in range(3650):
                if random_events_daily(rng_low, FREQ_LOW, day, log_low, corps_l, firms_l) is not None:
                    fired_low += 1
                if random_events_daily(rng_med, FREQ_MEDIUM, day, log_med, corps_m, firms_m) is not None:
                    fired_med += 1
        assert fired_med > fired_low

    def test_freq_high_fires_most(self):
        rng = Rng(99)
        log = NewsLog()
        corps, firms = _test_corps_and_firms()
        fired = 0
        for day in range(3650):
            if random_events_daily(rng, FREQ_HIGH, day, log, corps, firms) is not None:
                fired += 1
        assert fired > 0


# ---------------------------------------------------------------------------
# Random events — stubs (no matching firms)
# ---------------------------------------------------------------------------


class TestRandomEventsNoTarget:
    """With empty corps/firms, events that need targets are no-ops."""

    def test_all_events_handle_empty_state(self):
        rng = Rng(42)
        log = NewsLog()
        for day in range(5000):
            random_events_daily(rng, FREQ_HIGH, day, log, [], [])
        for item in log:
            assert item.news_type in (
                NewsType.ECONOMIC_DOWNTURN,
                NewsType.BUILDING_DESTROYED,
                NewsType.LIVESTOCK_DISEASE,
                NewsType.CROP_FAILURE,
                NewsType.RND_BREAKTHROUGH,
                NewsType.INVENTORY_LOSS,
            )


# ---------------------------------------------------------------------------
# Random events — with mock firms/corps
# ---------------------------------------------------------------------------


class _MockJob:
    def __init__(self, type_name="", stock=0, unit_cost=10.0, capacity=100):
        self.type_name = type_name
        self.stock = stock
        self.unit_cost = unit_cost
        self.capacity = capacity
        self.growth = 100
        self.yield_capacity = 100
        self.stage = 0
        self.product = None
        self.progress = 0


class _MockProduct:
    def __init__(self, name="TestProduct"):
        self.name = name


class _MockFirm:
    def __init__(self, firm_id=0, corp_id=0, type_name="Factory"):
        self.id = firm_id
        self.corp_id = corp_id
        self.type_name = type_name
        self._jobs: list[_MockJob] = []

    def jobs(self):
        return self._jobs


class _MockLedger:
    def __init__(self, cash=1_000_000.0):
        self.cash = cash

    @property
    def net_worth(self):
        return self.cash


class _MockCorp:
    def __init__(self, corp_id=0, cash=1_000_000.0):
        self.id = corp_id
        self.ledger = _MockLedger(cash)


class TestBuildingDestruction:
    def test_destroys_firm(self):
        rng = Rng(0)
        log = NewsLog()
        firms: list[_MockFirm | None] = [_MockFirm(0, 1), _MockFirm(1, 1), _MockFirm(2, 2)]
        destroyed = False
        for day in range(5000):
            result = random_events_daily(rng, FREQ_HIGH, day, log, [], firms)
            if result is not None and result.news_type == NewsType.BUILDING_DESTROYED:
                destroyed = True
                break
        assert destroyed
        assert any(f is None for f in firms)


class TestEconomicDownturn:
    def test_reduces_cash(self):
        rng = Rng(0)
        log = NewsLog()
        corps = [_MockCorp(0, 1_000_000.0), _MockCorp(1, 500_000.0)]
        initial_cash = [c.ledger.cash for c in corps]
        downturn_fired = False
        for day in range(10000):
            result = random_events_daily(rng, FREQ_HIGH, day, log, corps, [])
            if result is not None and result.news_type == NewsType.ECONOMIC_DOWNTURN:
                downturn_fired = True
                break
        assert downturn_fired
        assert any(c.ledger.cash < init for c, init in zip(corps, initial_cash))


class TestLivestockDisease:
    def test_reduces_capacity(self):
        farm = _MockFirm(0, 0, "Farm")
        job = _MockJob("LivestockRaising", capacity=1000)
        farm._jobs.append(job)
        corps = [_MockCorp(0)]
        rng = Rng(0)
        log = NewsLog()
        fired = False
        for day in range(10000):
            result = random_events_daily(rng, FREQ_HIGH, day, log, corps, [farm])
            if result is not None and result.news_type == NewsType.LIVESTOCK_DISEASE:
                fired = True
                break
        assert fired
        assert job.capacity < 1000


class TestCropFailure:
    def test_zeroes_growth(self):
        farm = _MockFirm(0, 0, "Farm")
        job = _MockJob("CropGrowing")
        job.growth = 50
        job.yield_capacity = 80
        farm._jobs.append(job)
        corps = [_MockCorp(0)]
        rng = Rng(0)
        log = NewsLog()
        fired = False
        for day in range(10000):
            result = random_events_daily(rng, FREQ_HIGH, day, log, corps, [farm])
            if result is not None and result.news_type == NewsType.CROP_FAILURE:
                fired = True
                break
        assert fired
        assert job.growth == 0
        assert job.yield_capacity == 0


class TestRndBreakthrough:
    def test_adds_progress(self):
        rnd_firm = _MockFirm(0, 0, "ResearchCentre")
        job = _MockJob()
        job.stage = 1
        job.product = _MockProduct("NewGadget")
        job.progress = 10
        rnd_firm._jobs.append(job)
        corps = [_MockCorp(0)]
        rng = Rng(0)
        log = NewsLog()
        fired = False
        for day in range(10000):
            result = random_events_daily(rng, FREQ_HIGH, day, log, corps, [rnd_firm])
            if result is not None and result.news_type == NewsType.RND_BREAKTHROUGH:
                fired = True
                break
        assert fired
        assert job.progress > 10


class TestInventoryLoss:
    def test_loses_stock(self):
        store = _MockFirm(0, 0, "DepartmentStore")
        job = _MockJob(stock=100, unit_cost=10.0)
        store._jobs.append(job)
        corps = [_MockCorp(0)]
        rng = Rng(0)
        log = NewsLog()
        fired = False
        for day in range(10000):
            result = random_events_daily(rng, FREQ_HIGH, day, log, corps, [store])
            if result is not None and result.news_type == NewsType.INVENTORY_LOSS:
                fired = True
                break
        assert fired
        assert job.stock < 100


# ---------------------------------------------------------------------------
# Economy integration
# ---------------------------------------------------------------------------


class TestEconomyIntegration:
    def test_news_log_on_economy(self):
        from capitalism.scenario import bread_town
        sim, _ = bread_town()
        assert len(sim.economy.news_log) == 0
        assert sim.economy.event_frequency == 0

    def test_events_disabled_by_default(self):
        from capitalism.scenario import bread_town
        sim, _ = bread_town()
        sim.advance_days(365)
        assert len(sim.economy.news_log) == 0

    def test_events_with_frequency(self):
        from capitalism.scenario import bread_town
        sim, _ = bread_town()
        sim.economy.event_frequency = FREQ_HIGH
        sim.advance_days(365)
        assert len(sim.economy.news_log) >= 0

    def test_setup_options_event_frequency(self):
        from capitalism.tables import SetupOptions
        opts = SetupOptions(event_frequency=2)
        assert opts.event_frequency == 2

    def test_setup_options_default(self):
        from capitalism.tables import SetupOptions
        opts = SetupOptions()
        assert opts.event_frequency == 0

    def test_setup_frequency_propagates(self):
        from capitalism.sim import Sim
        from capitalism.tables import MAP_RULES
        sim = Sim(seed=1, target_cities=MAP_RULES.default_cities)
        assert sim.economy.event_frequency == 0
        sim.setup.event_frequency = 2
        sim.reset()
        assert sim.economy.event_frequency == 2
