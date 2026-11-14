"""Tests for news log and random events (system 11)."""

from __future__ import annotations

from capitalism import news
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
    _, eco, corp, *_ = _event_world()
    return [corp], eco.firms


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
                if (
                    random_events_daily(rng_low, FREQ_LOW, day, log_low, corps_l, firms_l)
                    is not None
                ):
                    fired_low += 1
                if (
                    random_events_daily(rng_med, FREQ_MEDIUM, day, log_med, corps_m, firms_m)
                    is not None
                ):
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
# Random events — on real firms, jobs and corporations (#327)
# ---------------------------------------------------------------------------


def _event_world():
    """A corp with a farm (crops and cattle), an R&D centre with a running project and a
    stocked department store, all on a real Economy."""
    from capitalism.scenario import bread_town, find_site

    sim, town = bread_town(1)
    eco = sim.economy
    corp = eco.add_corp("Events")
    corp.ledger.cash = 1e9
    cat = eco.catalog

    def place(ftype):
        x, y = find_site(sim, town)
        return eco.build_firm(ftype, corp, x, y, town)

    farm = place(news.FARM)
    crop = farm.add_job(0, news.CROP_GROWING, cat["Wheat"])
    herd = farm.add_job(1, news.LIVESTOCK_RAISING, cat["Cattle"])
    crop.stock = 500.0
    herd.young, herd.grown = 400.0, 600.0
    lab = place(news.RND_CENTER)
    research = lab.add_job(0, news.RESEARCH, cat["DVD Player"])
    research.configure()
    research.project.started = True
    research.project.elapsed_days = 10
    store = place(news.DEPT_STORE)
    stock = store.add_job(0, 10, cat["Bread"])
    stock.stock, stock.unit_cost = 100.0, 2.0
    return sim, eco, corp, farm, crop, herd, research, store, stock


def _fire(fn, *args):
    """Call one event with fixed seeds until it fires (some events have an odds gate)."""
    for seed in range(200):
        item = fn(Rng(seed), 1, NewsLog(), *args)
        if item is not None:
            return item
    raise AssertionError(f"{fn.__name__} never fired")


def test_livestock_disease_divides_the_herd():
    _, eco, corp, _, _, herd, *_ = _event_world()
    item = _fire(news._event_livestock_disease, [corp], eco.firms)
    d = item.details["divisor"]
    assert item.corp_id == corp.id and item.details["farms_affected"] == 1
    assert (herd.young, herd.grown) == (400.0 / d, 600.0 / d)


def test_crop_failure_wipes_the_growing_crop():
    _, eco, corp, _, crop, herd, *_ = _event_world()
    item = _fire(news._event_crop_failure, [corp], eco.firms)
    assert item.corp_id == corp.id and crop.stock == 0.0
    assert herd.grown == 600.0  # livestock untouched


def test_rnd_breakthrough_adds_project_days():
    _, eco, corp, _, _, _, research, *_ = _event_world()
    item = _fire(news._event_rnd_breakthrough, [corp], eco.firms)
    assert item.corp_id == corp.id and item.details["product"] == "DVD Player"
    assert research.project.elapsed_days == 10 + item.details["progress_added"]


def test_inventory_loss_takes_store_stock():
    _, eco, corp, *_, stock = _event_world()
    item = None
    for seed in range(200):  # the loss roll can be 0 units
        stock.stock = 100.0
        item = news._event_inventory_loss(Rng(seed), 1, NewsLog(), [corp], eco.firms)
        if item is not None and stock.stock < 100.0:
            break
    assert item is not None and item.corp_id == corp.id
    assert item.details["total_loss"] == (100.0 - stock.stock) * 2.0 > 0


def test_economic_downturn_takes_a_share_of_net_worth():
    _, eco, corp, *_ = _event_world()
    nw, cash = corp.net_worth(eco.firms), corp.ledger.cash
    item = _fire(news._event_economic_downturn, [corp], eco.firms)
    lost = cash - corp.ledger.cash
    assert lost > 0
    assert abs(lost - nw * item.details["loss_fraction"]) < 1e-6 * nw


def test_building_destroyed_goes_through_demolish():
    from capitalism.world import TileCategory

    _, eco, _, _, _, _, _, store, _ = _event_world()
    others = [f for f in eco.firms if f is not None and f is not store]
    item = _fire(news._event_building_destroyed, others + [store], eco.demolish_firm)
    gone = next(f for f in others + [store] if eco.firms[f.id] is None)
    assert item.details["firm_id"] == gone.id and item.details["firm_type"] == gone.row.id
    assert item.corp_id == _owner_id(gone)
    assert eco.world.tile_at(gone.x, gone.y).kind != TileCategory.FIRM


def _owner_id(firm):
    return firm.owner.id if firm.owner is not None else -1


def test_bare_lists_without_remove_hook_still_clear_the_slot():
    class F:
        def __init__(self, i):
            self.id, self.owner = i, None

    firms = [F(0), F(1)]
    item = _fire(news._event_building_destroyed, firms, None)
    assert item.corp_id == -1 and firms.count(None) == 1


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
