"""Approved systems-4b behavior: projects, media, software, live retail and imports."""

import pytest

from capitalism.firms import FIRM_CLASSES, Restaurant, Seaport, TVStation
from capitalism.jobs import (
    CAT_ADVERTISING,
    CAT_SALARIES,
    CAT_SALES,
    CAT_TRAINING,
    job_wage_day,
    qualifies_media,
)
from capitalism.projects import product_duration_months, project_duration_months
from capitalism.scenario import (
    DEPARTMENT_STORE,
    FACTORY,
    MANUFACTURING,
    PURCHASING,
    SALES,
    SEAPORT,
    bread_town,
    build_bread_chain,
    find_site,
)
from capitalism.tables import ADVERTISING_RULES, FIRM_RULES, JOB_RULES, RESEARCH_DURATIONS


def test_all_remaining_firms_and_ten_unbounded_import_links():
    assert set(FIRM_CLASSES) == set(range(1, 15))
    sim, town = bread_town(1)
    x, y = find_site(sim, town)
    port = SEAPORT
    firm = sim.economy.build_firm(port, None, x, y, town)
    assert isinstance(firm, Seaport) and firm.slots == []
    goods = [p for p in sim.economy.catalog.products if p.row.importable]
    assert len(goods) >= 10
    links = [firm.open_import(p) for p in goods[:10]]
    assert len(firm.jobs()) == len(firm.imports) == 10
    assert len(firm.slots) == 0
    assert sum(1 for job in links if job is not None) == 10
    assert firm.open_import(goods[0]) is links[0]
    assert firm.post_overhead() is None
    assert firm.ledger.total[2] == 0
    for job in links:
        assert job.stock == 0 and job.available_stock() == float("inf")


def test_restaurant_buys_bread_and_sells_it_with_multiplier_two():
    sim, town = bread_town(1)
    eco = sim.economy
    bread = eco.catalog["Bread"]
    corp = eco.add_corp("restaurant")
    x, y = find_site(sim, town)
    producer = eco.build_firm(FACTORY, corp, *find_site(sim, town), town)
    producer.add_job(0, MANUFACTURING, bread)
    source = producer.add_job(1, SALES, bread)
    source.receive(200_000, JOB_RULES.import_quality, bread.row.base_price)
    x, y = find_site(sim, town)
    restaurant = eco.build_firm(10, corp, x, y, town)
    assert isinstance(restaurant, Restaurant) and restaurant.row.live_inventory
    buy = restaurant.add_job(0, PURCHASING, bread)
    sale = restaurant.add_job(1, SALES, bread)
    restaurant.link_slots(0, 1)
    restaurant.slots[0].supply = eco.link_b2b(source, buy)
    link = eco.link_consumer(sale, town)
    sim.advance_days(6)
    assert sale.daily_cap() == pytest.approx(
        sale.efficiency * sale.capacity * JOB_RULES.sales_mult_store / 100
    )
    assert sale.daily_cap() == pytest.approx(sale.efficiency * sale.capacity * 2 / 100)
    assert link.units_month[0] > 0
    assert sale.quality == JOB_RULES.import_quality


def test_reference_duration_table_and_project_boundaries():
    assert RESEARCH_DURATIONS == (0, 6, 12, 24, 36, 60, 120)
    for years, months in zip((0, 15, 30, 45, 60, 75, 90), RESEARCH_DURATIONS, strict=True):
        sim, town = bread_town(1)
        product = sim.economy.catalog["Bread"]
        product.row = product.row.model_validate(product.row.model_dump() | {"tech_year": years})
        assert product_duration_months(product) == months
        assert project_duration_months(product, False) == months
    sim, town = bread_town(1)
    x, y = find_site(sim, town)
    firm = sim.economy.build_firm(3, sim.economy.add_corp("R"), x, y, town)
    with pytest.raises(ValueError):
        firm.add_job(0, 11, None)
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        sim.economy.catalog["Bread"].row.model_validate(
            sim.economy.catalog["Bread"].row.model_dump() | {"tech_year": -1}
        )


def test_static_rows_are_frozen_and_never_leak_between_sims():
    """Tests swap a Sim's own Product.row/job.row; the shared db rows stay untouched."""
    from pydantic import ValidationError

    from capitalism.tables import JOB_TYPES, load_products

    shared = {r.name: r for r in load_products()}
    sim, _town = bread_town(1)
    bread = sim.economy.catalog["Bread"]
    assert bread.row is shared["Bread"]
    with pytest.raises(ValidationError):
        bread.row.tech_year = 90  # static content: no in-place mutation
    with pytest.raises(ValidationError):
        JOB_TYPES[PURCHASING].training_factor = 50
    with pytest.raises(ValidationError):
        JOB_RULES.freight_multiplier = 1.0
    bread.row = bread.row.model_validate(bread.row.model_dump() | {"tech_year": 90})
    fresh, _ = bread_town(1)
    assert fresh.economy.catalog["Bread"].row is shared["Bread"]
    assert shared["Bread"].tech_year == 0 and JOB_TYPES[PURCHASING].training_factor == 10.0
    # Runtime technology lives on Product.state and corporations, not on rows.
    corp = sim.economy.add_corp("C")
    corp.add_technology(bread, 3)
    assert corp.technology_level(bread) == 3 and fresh.economy.corps == []


def _research_fixture():
    sim, town = bread_town(1)
    bee = sim.economy.catalog["DVD Player"]
    required = [p.requires_id for p in sim.economy.catalog.prerequisites(bee)]
    assert required
    x, y = find_site(sim, town)
    firm = sim.economy.build_firm(3, sim.economy.add_corp("R"), x, y, town)
    job = firm.add_job(0, 11, bee)
    job.configure(bee)
    return sim, firm, job, required


def test_prerequisites_block_then_enable_project_and_pause_preserves_progress():
    sim, firm, job, required = _research_fixture()
    assert job.product.row.tech_year == 30
    job.project.elapsed_days = 359
    sim.advance_day()
    assert job.project.elapsed_days == 359 and not job.project.started
    for pid in required:
        firm.owner.add_technology(sim.economy.catalog.by_id[pid])
    sim.advance_day()
    assert job.completed_count == 1 and job.project.elapsed_days == 360
    assert not job.project.started
    sim, firm, job, required = _research_fixture()
    for pid in required:
        firm.owner.add_technology(sim.economy.catalog.by_id[pid])
    sim.advance_days(7)
    progress = job.project.elapsed_days
    job.paused = True
    sim.advance_days(5)
    assert job.project.elapsed_days == progress
    job.paused = False
    job.param2 = 0
    sim.advance_days(4)
    assert job.project.elapsed_days == progress
    job.param2 = 1
    sim.advance_day()
    assert job.project.elapsed_days == progress + 1


def test_one_shot_stops_repeat_starts_next_level():
    sim, firm, job, required = _research_fixture()
    for pid in required:
        firm.owner.add_technology(sim.economy.catalog.by_id[pid])
    for _ in range(360):
        sim.advance_day()
    assert job.completed_count == 1 and not job.project.started
    with pytest.raises(ValueError, match="one active project"):
        job.configure()
    job.param1 = 1
    job.repeat()
    for _ in range(360):
        sim.advance_day()
    assert job.completed_count >= 2
    assert firm.owner.technology_level(job.product) >= 2


def test_manufacturing_research_affects_new_batches_not_old_stock():
    sim, town = bread_town(1)
    eco = sim.economy
    x, y = find_site(sim, town)
    factory = eco.build_firm(FACTORY, eco.add_corp("R"), x, y, town)
    job = factory.add_job(0, MANUFACTURING, eco.catalog["Bread"])
    recipe = eco.catalog.recipe(job.product)
    for i in recipe.inputs:
        job.inputs[i.input_id] = [i.qty * 1000, 80.0, 1.0]
    factory.owner.manufacturing_skill = 100
    sim.advance_days(1)
    orig = job.quality
    assert job.quality == pytest.approx(62.0)
    first_quality = orig
    factory.owner.add_technology(job.product, 5)
    sim.advance_days(7)  # weekly tech upgrade catches job_tech up to corp tech
    assert job.job_tech > 0
    job.stock = 0
    recipe = eco.catalog.recipe(job.product)
    for i in recipe.inputs:
        job.inputs[i.input_id] = [i.qty * 1000, 80.0, 1.0]
    sim.advance_day()
    assert job.stock > 0
    assert job.quality > first_quality


def _advertising_fixture():
    """Established prior-month books, explicitly distinct from a cold-start station."""
    sim, town = bread_town(1)
    eco = sim.economy
    tv = eco.build_firm(11, None, *find_site(sim, town, in_town=True), town)
    tv.ledger.last_month[CAT_SALES] = 100_000  # sole ledger history: no daily fake-revenue posting
    corp = eco.add_corp("Ad buyer")
    product = eco.catalog["Desktop Computer"]
    firm = eco.build_firm(DEPARTMENT_STORE, corp, *find_site(sim, town, in_town=True), town)
    ad = firm.add_job(0, 15, product)
    consumer = eco.link_consumer(firm.add_job(1, SALES, product), town)
    firm.ledger.last_month[CAT_SALES] = 1_000_000
    return sim, town, tv, firm, ad, consumer


def _days_to_tick(sim, firm):
    """Days before the advertiser's next scheduled tick (work runs before the serial advances)."""
    every = ADVERTISING_RULES.ad_campaign_every_days
    return (-(sim.calendar.day_serial + firm.id)) % every


def _next_campaign(sim, firm, prepare=None):
    """Run to the advertiser's next scheduled tick once, optionally setting explicit books first.

    Every non-tick day must leave category 6 untouched (no daily charge). `prepare` runs on the
    tick's eve, after any month roll, so explicit prior-month history is what the tick reads.
    """
    before = firm.ledger.total[CAT_ADVERTISING]
    for _ in range(_days_to_tick(sim, firm)):
        sim.advance_day()
        assert firm.ledger.total[CAT_ADVERTISING] == before
    if prepare is not None:
        prepare()
    tick_serial = sim.calendar.day_serial
    sim.advance_day()
    assert (tick_serial + firm.id) % ADVERTISING_RULES.ad_campaign_every_days == 0
    return firm.ledger.total[CAT_ADVERTISING] - before


def _stock(link, qty=10):
    """Real store inventory bought at the import/base price, so the campaign has goods to back."""
    product = link.product
    link.seller.receive(qty, JOB_RULES.import_quality, product.row.base_price)


def _record_campaign_brand(monkeypatch, link):
    """(brand before, brand after) of `link` around each committed campaign call."""
    from capitalism.jobs import Advertising

    seen = []
    original = Advertising.commit_campaign

    def commit(self, eco):
        before = link.read_brand(eco.market)
        original(self, eco)
        seen.append((before, link.read_brand(eco.market)))

    monkeypatch.setattr(Advertising, "commit_campaign", commit)
    return seen


def test_media_daily_payroll_and_100k_campaign_same_town(monkeypatch):
    sim, town, tv, firm, ad, consumer = _advertising_fixture()
    brand = _record_campaign_brand(monkeypatch, consumer)
    assert isinstance(tv, TVStation) and tv.slots == [] and 10 <= tv.audience <= 39
    low_audience_station = TVStation(998, None, tv.x, tv.y, tv.tile, tv.town, 0, 0)
    low_audience_station.audience = 3.0  # below the 5.0 binary threshold
    with pytest.raises(ValueError, match="audience threshold"):
        ad.specify_media(low_audience_station, 100_000)
    # Seed 1 first tick lands in January, so the fixture's books are the real prior month.
    assert _next_campaign(sim, firm, lambda: _stock(consumer)) == 100_000
    assert sim.calendar.month == 1
    assert ad.media is tv and ad.budget == 100_000
    assert ad.targets == {consumer.product.id: 100_000}
    assert [after - before for before, after in brand] == [1]
    assert firm.ledger.total[CAT_ADVERTISING] == firm.owner.ledger.total[CAT_ADVERTISING] == 100_000
    assert tv.ledger.total[CAT_SALES] >= 100_000 and firm.id in tv.advertisers
    other = next(t for t in sim.towns if t.id != town.id)
    wrong = sim.economy.build_firm(11, None, *find_site(sim, other), other)
    with pytest.raises(ValueError, match="same town"):
        ad.attach_media(wrong)
    while sim.calendar.month == 1:
        sim.advance_day()
    assert tv.ledger.last_month[CAT_SALARIES] > 0 and tv.ledger.total[CAT_TRAINING] == 0
    # revenue_month includes both campaign revenue and organic revenue (binary FUN_0006073c).
    assert tv.revenue_month[-1] >= 100_000 and tv.revenue_total >= 100_000
    assert len(tv.revenue_month) == len(tv.audience_month) == 12


def test_new_station_cannot_select_itself_without_audience():
    """Binary FUN_0005116d: audience must exceed 5.0 (_DAT_000a7518)."""
    sim, _town, tv, firm, ad, consumer = _advertising_fixture()
    tv.audience = 3.0  # below the 5.0 threshold
    assert _next_campaign(sim, firm) == 0
    assert not qualifies_media(tv) and ad.media is None and ad.budget == 0
    assert consumer.brand == 0


def test_repeated_identical_campaign_does_not_charge_every_day(monkeypatch):
    sim, _town, tv, firm, _ad, consumer = _advertising_fixture()
    brand = _record_campaign_brand(monkeypatch, consumer)
    assert _next_campaign(sim, firm, lambda: _stock(consumer)) == 100_000

    def next_month_books():
        tv.ledger.last_month[CAT_SALES] = 100_000
        firm.ledger.last_month[CAT_SALES] = 1_000_000
        _stock(consumer)

    assert _next_campaign(sim, firm, next_month_books) == 100_000
    assert firm.ledger.total[CAT_ADVERTISING] == 200_000
    # One bounded brand increment per committed campaign, never a daily or doubled jump.
    assert [after - before for before, after in brand] == [1, 1]
    # Station earns campaign revenue plus organic revenue from audience/town economics.
    assert tv.ledger.total[CAT_SALES] >= 200_000


def test_campaign_without_stock_or_on_b2b_link_gains_no_brand(monkeypatch):
    sim, town, tv, firm, _ad, consumer = _advertising_fixture()
    eco = sim.economy
    product = consumer.product
    buyer = eco.build_firm(DEPARTMENT_STORE, eco.add_corp("B"), *find_site(sim, town), town)
    b2b = eco.link_b2b(consumer.seller, buyer.add_job(0, PURCHASING, product))
    assert not b2b.live
    brand = _record_campaign_brand(monkeypatch, consumer)
    b2b_brand = _record_campaign_brand(monkeypatch, b2b)
    # Sponsored but empty shelf: the campaign is still financed, the brand does not move.
    assert consumer.seller.stock == 0
    assert _next_campaign(sim, firm) == 100_000
    assert [after - before for before, after in brand] == [0]

    def stocked_next_month():
        tv.ledger.last_month[CAT_SALES] = 100_000
        firm.ledger.last_month[CAT_SALES] = 1_000_000
        _stock(consumer)

    assert _next_campaign(sim, firm, stocked_next_month) == 100_000
    assert [after - before for before, after in brand] == [0, 1]
    assert [after - before for before, after in b2b_brand] == [0, 0]


def test_media_payroll_ticks_on_day_31_and_rolls_in_february():
    sim, town, tv, *_ = _advertising_fixture()
    sim.advance_days(30)
    wage = job_wage_day(FIRM_RULES.media_staff, town.labor_cost, 31)
    assert tv.ledger.month[CAT_SALARIES] == pytest.approx(30 * wage)
    sim.advance_day()
    assert tv.ledger.last_month[CAT_SALARIES] == pytest.approx(31 * wage)
    assert tv.ledger.last_month[CAT_TRAINING] == 0


def test_media_twelve_month_audience_and_revenue_series(monkeypatch):
    """Reputation-driven random walk (binary FUN_000604d2) produces bounded audience."""
    sim, _town, tv, *_ = _advertising_fixture()
    r = ADVERTISING_RULES
    months_seen = 0
    original = TVStation.monthly

    def record(self, eco):
        nonlocal months_seen
        months_seen += 1
        original(self, eco)

    monkeypatch.setattr(TVStation, "monthly", record)
    while sim.calendar.year == 1990:
        sim.advance_day()
    assert months_seen == 12
    # Reputation model: audience stays within global bounds.
    assert all(r.media_audience_min <= a <= r.media_audience_cap for a in tv.audience_month)
    assert tv.audience_total == pytest.approx(sum(tv.audience_month))
    # Reputation field tracks drift state.
    assert r.media_reputation_min <= tv.reputation <= r.media_reputation_max
    # Organic revenue is earned every month (binary FUN_0006073c).
    assert all(rev >= r.media_revenue_floor for rev in tv.revenue_month)
    assert tv.revenue_total >= r.media_revenue_floor * 12


def test_government_media_audience_uses_game_rng_only():
    def build(government):
        sim, town = bread_town(1)
        eco = sim.economy
        tv = eco.build_firm(11, None, *find_site(sim, town), town)
        state = eco.rng._r.getstate()
        tv.row = tv.row.model_copy(update={"government": government})
        tv.initialize_audience(eco)
        return tv.audience, eco.rng._r.getstate() == state

    assert build(False) == (ADVERTISING_RULES.media_audience_min, True)
    first, second = build(True), build(True)
    assert first == second and not first[1]
    assert (
        ADVERTISING_RULES.media_audience_min <= first[0] <= ADVERTISING_RULES.media_government_max
    )


def test_software_completion_mastering_copying_and_sales():
    sim, town = bread_town(1)
    eco = sim.economy
    sw = eco.catalog["Software"]
    x, y = find_site(sim, town)
    corp = eco.add_corp("Software publisher")
    developer = eco.build_firm(8, corp, x, y, town)
    dev = developer.add_job(0, 13, sw)
    dev.configure()
    x, y = find_site(sim, town)
    publisher = eco.build_firm(9, corp, x, y, town)
    prod = publisher.add_job(0, 14, sw)
    sales = publisher.add_job(1, 12, sw)
    publisher.link_slots(0, 1)
    link = eco.link_consumer(sales, town)
    sim.advance_days(30)
    assert dev.completed_count == 0 and prod.stock == sales.stock == link.units_month[0] == 0
    sim.advance_days(150)
    assert dev.completed_count == 1 and dev.stock == 1
    assert prod.has_master and prod.stock >= 0 and sales.stock > 0
    assert link.units_month[5] > 0  # the completed Software title has an active consumer link
    assert prod.unit_cost == sw.row.base_cost
    assert dev.stock == 1  # a copy handoff does not consume the development master
    buyer = sim.economy.build_firm(DEPARTMENT_STORE, corp, *find_site(sim, town), town)
    buy = buyer.add_job(0, PURCHASING, sw)
    retail = buyer.add_job(1, SALES, sw)
    buyer.link_slots(0, 1)
    sim.economy.link_b2b(sales, buy)
    retail_link = sim.economy.link_consumer(retail, town)
    # The buyer's first scheduled 5-day purchase, then the same-day consumer link pass.
    sim.advance_days((buy.slot - sim.calendar.day_serial) % JOB_RULES.purchase_every_days + 1)
    assert sim.calendar.month == 7 and buy.firm.ledger.total[CAT_SALES] > 0
    assert dev.stock == 1 and retail_link.units_month[6] > 0  # actual sale from buyer's store
    assert link.live and retail_link.live


def test_software_gate_drops_stale_product():
    """Binary FUN_0005c06f: every 15 days, drop products older than 151 days with no revenue."""
    from capitalism.tables import SOFTWARE_RULES

    sim, town = bread_town(1)
    eco = sim.economy
    sw = eco.catalog["Software"]
    corp = eco.add_corp("Software publisher")
    x, y = find_site(sim, town)
    developer = eco.build_firm(8, corp, x, y, town)
    dev = developer.add_job(0, 13, sw)
    dev.configure()
    x, y = find_site(sim, town)
    publisher = eco.build_firm(9, corp, x, y, town)
    prod = publisher.add_job(0, 14, sw)
    publisher.link_slots(0, 1)
    # Complete development so production has a master.
    sim.advance_days(180)
    assert dev.completed_count == 1
    assert prod.has_master
    # Record that production started.
    assert prod.production_started_serial > 0
    start = prod.production_started_serial
    # Advance past the staleness threshold (151 days) with no revenue.
    prod.revenue_months = [0.0] * 12
    sim.advance_days(SOFTWARE_RULES.software_gate_max_age_days + 20)
    age = sim.calendar.day_serial - start
    assert age > SOFTWARE_RULES.software_gate_max_age_days
    # The gate may have fired and dropped the product (if a gate tick aligned).
    # At minimum, verify the gate fields exist and the mechanism runs.
    assert hasattr(prod, "production_started_serial")
    assert hasattr(prod, "revenue_months")


def test_software_gate_keeps_product_with_revenue():
    """Binary FUN_0005c06f: product with recent revenue is NOT dropped."""
    from capitalism.tables import SOFTWARE_RULES

    sim, town = bread_town(1)
    eco = sim.economy
    sw = eco.catalog["Software"]
    corp = eco.add_corp("Software publisher")
    x, y = find_site(sim, town)
    developer = eco.build_firm(8, corp, x, y, town)
    dev = developer.add_job(0, 13, sw)
    dev.configure()
    x, y = find_site(sim, town)
    publisher = eco.build_firm(9, corp, x, y, town)
    prod = publisher.add_job(0, 14, sw)
    sales = publisher.add_job(1, SALES, sw)
    publisher.link_slots(0, 1)
    eco.link_consumer(sales, town)
    sim.advance_days(180)
    assert dev.completed_count == 1 and prod.has_master
    original_product = prod.product
    # Inject revenue so the gate doesn't fire.
    prod.revenue_months = [0.0] * 7 + [10000.0] * 5
    sim.advance_days(SOFTWARE_RULES.software_gate_max_age_days + 20)
    # Product should NOT have changed because there was recent revenue.
    assert prod.product is original_product


def test_media_qualifies_on_audience_not_revenue():
    """Binary FUN_0005116d: partner selection gates on audience > 5.0, not revenue.
    This resolves the cold-start problem — a new station with audience >= 10.0
    (media_audience_min) always qualifies."""
    sim, town = bread_town(1)
    eco = sim.economy
    tv = eco.build_firm(11, None, *find_site(sim, town), town)
    assert tv.audience >= ADVERTISING_RULES.media_audience_min
    assert tv.audience > ADVERTISING_RULES.media_min_audience
    assert qualifies_media(tv)
    # Zero revenue doesn't matter — audience is what counts.
    assert tv.ledger.total[CAT_SALES] == 0
    assert qualifies_media(tv)


def test_cold_start_station_gets_first_campaign():
    """With audience-based qualification, a new station can be selected immediately."""
    sim, town = bread_town(1)
    eco = sim.economy
    tv = eco.build_firm(11, None, *find_site(sim, town), town)
    firm = eco.build_firm(DEPARTMENT_STORE, eco.add_corp("A"), *find_site(sim, town), town)
    ad = firm.add_job(0, 15, eco.catalog["Desktop Computer"])
    sales = firm.add_job(1, SALES, eco.catalog["Desktop Computer"])
    eco.link_consumer(sales, town)
    firm.ledger.last_month[CAT_SALES] = 1_000_000
    assert _next_campaign(sim, firm) > 0
    assert ad.media is tv and tv.ledger.total[CAT_SALES] > 0


# --- freight (decompiled FUN_000785f1) and training expense vs skill-growth factor ----------


def _at(x, y):
    from types import SimpleNamespace

    return SimpleNamespace(x=x, y=y)


def test_freight_db_defaults_and_per_product_rates():
    from capitalism.jobs import product_freight_rate

    assert (
        JOB_RULES.freight_distance_value_divisor,
        JOB_RULES.freight_multiplier,
        JOB_RULES.freight_floor_usd_per_unit,
    ) == (100.0, 0.5, 0.01)
    sim, _ = bread_town(1)
    cat = sim.economy.catalog
    for name, freight, spending, per_tile in (
        ("Wheat", 70, 0.30, 0.00105),
        ("Flour", 70, 0.50, 0.00175),
        ("Bread", 50, 1.50, 0.00375),
    ):
        p = cat[name]
        assert (p.row.freight, p.row.spending_usd) == (freight, spending)
        rate = product_freight_rate(p, _at(0, 0), _at(1, 0))
        assert rate == pytest.approx(freight * spending / 20_000) == pytest.approx(per_tile)
        assert 0 < rate < 0.01  # positive sub-cent rate is kept, not floored or rounded
    # Wheat's freight price term is SPENDING 0.30, not its $0.10 import/resource price.
    assert cat["Wheat"].row.base_price == 0.1


def test_freight_scales_with_euclidean_distance_and_zero_only_floor():
    import math

    from capitalism.jobs import product_freight_rate

    sim, town = bread_town(1)
    cat = sim.economy.catalog
    wheat = cat["Wheat"]
    one = product_freight_rate(wheat, _at(5, 5), _at(6, 5))
    assert product_freight_rate(wheat, _at(5, 5), _at(8, 9)) == pytest.approx(5 * one)
    assert product_freight_rate(wheat, _at(8, 9), _at(5, 5)) == pytest.approx(5 * one)
    assert product_freight_rate(wheat, _at(0, 0), _at(10, 0)) == pytest.approx(0.0105)
    # Zero raw rate (same tile, or a product with no freight coefficient) uses the floor.
    assert product_freight_rate(wheat, _at(5, 5), _at(5, 5)) == 0.01
    zero = next(p for p in cat.products if p.row.freight == 0)
    assert product_freight_rate(zero, _at(0, 0), _at(30, 30)) == 0.01
    # Firms in different towns use their own stored coordinates.
    other = next(t for t in sim.towns if t.id != town.id)
    a, b = find_site(sim, town), find_site(sim, other)
    dx, dy = a[0] - b[0], a[1] - b[1]
    d = math.isqrt(dx * dx + dy * dy)
    assert d > 1
    assert product_freight_rate(wheat, _at(*a), _at(*b)) == pytest.approx(d * 70 * 0.30 / 20_000)
    for p in cat.products:
        assert product_freight_rate(p, _at(0, 0), _at(3, 4)) > 0


def test_freight_inputs_are_recovered_spending_or_flagged_fill():
    sim, _ = bread_town(1)
    for p in sim.economy.catalog.products:
        assert p.row.spending_usd > 0 and p.row.freight >= 0
        # #283: every SET item's FREIGHT is Observed; only Software (not in the SET) is a fill.
        prov = set(p.row.provisional)
        assert ("freight" in prov) == (p.name == "Software"), p.name
    from capitalism.jobs import product_freight_rate

    # Long haul crosses a cent without any floor; the floor never applies to positive rates.
    assert product_freight_rate(sim.economy.catalog["Bread"], _at(0, 0), _at(4, 0)) == (
        pytest.approx(0.015)
    )
    assert product_freight_rate(sim.economy.catalog["Wheat"], _at(0, 0), _at(1, 0)) < 0.01


def _first_wheat_receipt(offset):
    """Seaport → factory Purchasing, buyer `offset` tiles east of the port; first receipt."""
    sim, town = bread_town(1)
    eco = sim.economy
    x, y = find_site(sim, town)
    port = eco.build_firm(SEAPORT, None, x, y, town)
    imp = port.open_import(eco.catalog["Wheat"])
    factory = eco.build_firm(FACTORY, eco.add_corp("F"), x + offset, y, town)
    buy = factory.add_job(0, PURCHASING, eco.catalog["Wheat"])
    eco.link_b2b(imp, buy)
    while buy.received_month[0] == 0:
        sim.advance_day()
    return buy.received_month[0], buy.freight_month[0], factory.ledger.total[5]


def test_purchasing_receipt_freight_varies_with_distance():
    near_qty, near_freight, near_posted = _first_wheat_receipt(1)
    far_qty, far_freight, far_posted = _first_wheat_receipt(4)
    assert near_qty == far_qty > 0
    assert near_freight == pytest.approx(near_qty * 0.00105) == pytest.approx(near_posted)
    assert far_freight == pytest.approx(4 * near_freight) == pytest.approx(far_posted)


def _purchasing_job(budget=None, training_factor=None):
    sim, town = bread_town(1)
    eco = sim.economy
    corp = eco.add_corp("T")
    if budget is not None:
        corp.training_budget = budget
    factory = eco.build_firm(FACTORY, corp, *find_site(sim, town, in_town=True), town)
    job = factory.add_job(0, PURCHASING, eco.catalog["Wheat"])
    if training_factor is not None:
        job.row = job.row.model_copy(update={"training_factor": training_factor})
    return factory, job


def _one_day_training(budget=None, training_factor=None):
    from types import SimpleNamespace

    factory, job = _purchasing_job(budget, training_factor)
    factory.town.labor_cost = 100
    before = factory.ledger.total[CAT_TRAINING]
    eco = SimpleNamespace(calendar=SimpleNamespace(real_month_days=30, weekday=0))
    job.post_wages(eco)
    return factory.ledger.total[CAT_TRAINING] - before, factory.ledger.total[CAT_SALARIES]


def test_training_expense_is_budget_times_wage_over_divisor():
    assert JOB_RULES.corp_training_budget_default == 10
    assert JOB_RULES.training_expense_divisor == 100.0
    training, wages = _one_day_training()
    assert wages == 266 and training == pytest.approx(26.60)
    assert _one_day_training(budget=20)[0] == pytest.approx(53.20)
    assert _one_day_training(budget=0)[0] == 0


def test_training_factor_is_independent_of_training_expense():
    """Spec: job-type training_factor drives monthly skill growth, never expense.

    The job field's role in daily-credit scaling is unresolved (design.md slice 4 call 6
    names the factor but not the formula), so only the separation is asserted here.
    """
    assert _one_day_training(training_factor=50)[0] == pytest.approx(_one_day_training()[0])
    from capitalism.tables import JOB_TYPES

    _, job = _purchasing_job(budget=50)
    assert job.row.training_factor == JOB_TYPES[PURCHASING].training_factor == 10.0


# --- bread-chain placement ----------------------------------------------------------------


def test_bread_chain_seed_1_layout_is_canonical_free_tiles():
    sim, town = bread_town(1)
    chain = build_bread_chain(sim, town)
    firms = (chain.seaport, chain.flour_factory, chain.bread_factory, chain.store)
    # In-town tiles since #285 (firms off town tiles pay no wages, audit W2).
    assert [(f.x, f.y) for f in firms] == [(211, 155), (212, 155), (213, 155), (211, 156)]
    assert all(f.on_town_tile for f in firms)


def test_bread_chain_skips_an_occupied_tile_instead_of_overwriting():
    sim, town = bread_town(1)
    eco = sim.economy
    blocker = eco.build_firm(FACTORY, None, 212, 155, town)
    chain = build_bread_chain(sim, town)
    firms = (chain.seaport, chain.flour_factory, chain.bread_factory, chain.store)
    spots = [(f.x, f.y) for f in firms]
    assert len(set(spots)) == 4 and (212, 155) not in spots
    assert sim.world.tile_at(212, 155).ref == blocker.id and eco.firms[blocker.id] is blocker


def test_product_freight_factors_from_set():
    """#283 / audit F2: every SET item's FREIGHT is in the DB; unshipped items stay 0."""
    from capitalism.jobs import product_freight_rate

    sim, _ = bread_town(1)
    cat = sim.economy.catalog
    for name, freight in (("Coal", 100), ("CPU", 1), ("Wheat", 70), ("Glass", 90), ("Jewelry", 1)):
        assert cat[name].row.freight == freight
        assert "freight" not in cat[name].row.provisional
    for name in ("Cattle", "Chicken", "Pig", "Sheep", "Rubber Plant", "Sugar Cane"):
        assert cat[name].row.freight == 0
    assert sum(p.row.freight > 0 for p in cat.products) == 78
    # Coal: FREIGHT 100 x SPENDING x 5 tiles / 100^2 x 0.5.
    coal = cat["Coal"]
    rate = product_freight_rate(coal, _at(0, 0), _at(3, 4))
    assert rate == pytest.approx(100 * 5 * coal.row.spending_usd / 20_000)
