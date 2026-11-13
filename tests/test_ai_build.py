"""AI firm build and configuration (R18, R19, R20, R21, R23)."""

from capitalism.ai import (
    FIRM_TYPE_SKILL,
    MODE_DORMANT,
    MODE_ESTABLISH,
    MODE_FIRM_TYPES,
    MODE_MANUFACTURE,
    MODE_RETAIL,
    RANDOM_BUILD_CAP,
    RETRY_COOLDOWN,
    AIState,
    _configure_new_firm,
    _random_firm_type,
    _skill_based_pick,
)
from capitalism.person import (
    SKILL_FARMING,
    SKILL_MANUFACTURING,
    SKILL_RAW_MATERIAL,
    SKILL_RETAILING,
    SKILL_RND,
)
from capitalism.rng import Rng
from capitalism.scenario import bread_town, find_site


def _ai_corp(sim, town, *, mode=MODE_ESTABLISH):
    """Create an AI corporation with an AIState in the given mode."""
    from capitalism.economy import CORP_AI

    eco = sim.economy
    corp = eco.add_corp("AI Corp", CORP_AI)
    corp.ledger.cash = 50_000_000
    ai = AIState(corp.id, eco.calendar.day_serial, eco.rng)
    ai.mode = mode
    eco.ai_states[corp.id] = ai
    return corp, ai


# --- R19: mode firm-type lists ---


def test_establish_has_10_types():
    assert len(MODE_FIRM_TYPES[MODE_ESTABLISH]) == 10


def test_manufacture_has_6_types():
    assert len(MODE_FIRM_TYPES[MODE_MANUFACTURE]) == 6


def test_retail_has_2_types():
    assert len(MODE_FIRM_TYPES[MODE_RETAIL]) == 2


def test_dormant_is_empty():
    assert MODE_FIRM_TYPES[MODE_DORMANT] == ()


def test_establish_includes_all_firm_types():
    expected = (1, 2, 3, 4, 5, 6, 7, 10, 8, 9)
    assert MODE_FIRM_TYPES[MODE_ESTABLISH] == expected


# --- R20: skill mapping (cross-wired) ---


def test_store_uses_manufacturing_skill():
    assert FIRM_TYPE_SKILL[1] == SKILL_MANUFACTURING


def test_factory_uses_retailing_skill():
    assert FIRM_TYPE_SKILL[2] == SKILL_RETAILING


def test_rnd_uses_rnd_skill():
    assert FIRM_TYPE_SKILL[3] == SKILL_RND


def test_farm_uses_farming_skill():
    assert FIRM_TYPE_SKILL[4] == SKILL_FARMING


def test_extraction_uses_raw_material_skill():
    for ft in (5, 6, 7):
        assert FIRM_TYPE_SKILL[ft] == SKILL_RAW_MATERIAL


def test_skill_based_pick_prefers_highest():
    """The 80% path picks the firm type whose mapped skill is highest."""
    sim, town = bread_town()
    eco = sim.economy
    corp, ai = _ai_corp(sim, town)

    ceo = eco.add_person("TestCEO")
    ceo.link_to_corp(corp.id, as_ceo=True)
    ceo.skills[SKILL_RETAILING] = 99.0
    for i in range(7):
        if i != SKILL_RETAILING:
            ceo.skills[i] = 1.0

    result = _skill_based_pick(eco, corp, ceo, ai)
    assert result == 2  # Factory, because factory maps to retailing skill


# --- R21: retry cooldowns ---


def test_retry_cooldown_blocks_pick():
    """A firm type with an active retry cooldown is skipped."""
    sim, town = bread_town()
    eco = sim.economy
    _corp, ai = _ai_corp(sim, town)
    ai.retry_cooldowns[1] = eco.calendar.day_serial + 100
    ai.retry_cooldowns[2] = eco.calendar.day_serial + 100

    rng = Rng(42)
    for _ in range(50):
        ft = _random_firm_type(rng, ai)
        if ft is not None:
            assert ft not in (1, 2)


def test_retry_cooldown_value():
    assert RETRY_COOLDOWN == 20


# --- R23: random build cap ---


def test_random_build_cap_values():
    assert RANDOM_BUILD_CAP == {0: 2, 1: 2, 2: 3, 3: 3, 4: 4, 5: 4}


# --- R18: firm configuration ---


def test_configure_store():
    """A Dept Store gets Purchasing + Sales with a consumer product."""
    sim, town = bread_town()
    eco = sim.economy
    corp, _ = _ai_corp(sim, town)
    x, y = find_site(sim, town)
    firm = eco.build_firm(1, corp, x, y, town)
    rng = Rng(42)
    _configure_new_firm(eco, corp, firm, rng)

    jobs = firm.jobs()
    assert len(jobs) == 2
    types = {j.type_id for j in jobs}
    assert 10 in types  # Purchasing
    assert 12 in types  # Sales
    assert firm.links != 0


def test_configure_factory():
    """A Factory gets Purchasing + Manufacturing + Sales."""
    sim, town = bread_town()
    eco = sim.economy
    corp, _ = _ai_corp(sim, town)
    x, y = find_site(sim, town)
    firm = eco.build_firm(2, corp, x, y, town)
    rng = Rng(7)
    _configure_new_firm(eco, corp, firm, rng)

    jobs = firm.jobs()
    types = {j.type_id for j in jobs}
    assert 7 in types  # Manufacturing
    assert 12 in types  # Sales
    assert 10 in types  # Purchasing
    assert len(jobs) >= 3  # at least 1 purchase + mfg + sales
    assert firm.links != 0


def test_configure_farm_crop():
    """A Farm configured with a crop gets CropGrowing + Sales."""
    sim, town = bread_town()
    eco = sim.economy
    corp, _ = _ai_corp(sim, town)
    x, y = find_site(sim, town)
    firm = eco.build_firm(4, corp, x, y, town)

    from capitalism.catalog import Crop, Livestock

    cat = eco.catalog
    rng = Rng(42)
    while True:
        test_rng = Rng(rng.randint(0, 10000))
        all_farm = [
            p for p in cat.products if isinstance(p, (Crop, Livestock)) and p.state.available
        ]
        pick = test_rng.choice(all_farm)
        if isinstance(pick, Crop):
            _configure_new_firm(eco, corp, firm, test_rng)
            break

    jobs = firm.jobs()
    types = {j.type_id for j in jobs}
    assert 1 in types  # CropGrowing
    assert 12 in types  # Sales


def test_configure_mine():
    """A Mine gets Mining + Sales with a mineral product."""
    sim, town = bread_town()
    eco = sim.economy
    corp, _ = _ai_corp(sim, town)
    x, y = find_site(sim, town)
    firm = eco.build_firm(6, corp, x, y, town)
    rng = Rng(42)
    _configure_new_firm(eco, corp, firm, rng)

    jobs = firm.jobs()
    assert len(jobs) == 2
    types = {j.type_id for j in jobs}
    assert 8 in types  # Mining
    assert 12 in types  # Sales
    assert firm.reserve == 100.0
    assert jobs[0].product.id in (1, 2, 3, 4, 5, 7)


def test_configure_oil_well():
    """An Oil Well gets OilExtraction + Sales for Oil."""
    sim, town = bread_town()
    eco = sim.economy
    corp, _ = _ai_corp(sim, town)
    x, y = find_site(sim, town)
    firm = eco.build_firm(7, corp, x, y, town)
    rng = Rng(42)
    _configure_new_firm(eco, corp, firm, rng)

    jobs = firm.jobs()
    assert len(jobs) == 2
    assert jobs[0].type_id == 9  # OilExtraction
    assert jobs[0].product.id == 6  # Oil
    assert firm.reserve == 100.0


def test_configure_logging_camp():
    """A Logging Camp gets Logging + Sales for Timber."""
    sim, town = bread_town()
    eco = sim.economy
    corp, _ = _ai_corp(sim, town)
    x, y = find_site(sim, town)
    firm = eco.build_firm(5, corp, x, y, town)
    rng = Rng(42)
    _configure_new_firm(eco, corp, firm, rng)

    jobs = firm.jobs()
    assert len(jobs) == 2
    assert jobs[0].type_id == 4  # Logging
    assert jobs[0].product.id == 8  # Timber
    assert firm.reserve == 100.0


def test_configure_rnd():
    """An R&D Center gets a Research job."""
    sim, town = bread_town()
    eco = sim.economy
    corp, _ = _ai_corp(sim, town)
    x, y = find_site(sim, town)
    firm = eco.build_firm(3, corp, x, y, town)
    rng = Rng(42)
    _configure_new_firm(eco, corp, firm, rng)

    jobs = firm.jobs()
    assert len(jobs) == 1
    assert jobs[0].type_id == 11  # Research


def test_configure_sw_dev():
    """A Software Developer gets a SoftwareDevelopment job."""
    sim, town = bread_town()
    eco = sim.economy
    corp, _ = _ai_corp(sim, town)
    x, y = find_site(sim, town)
    firm = eco.build_firm(8, corp, x, y, town)
    rng = Rng(42)
    _configure_new_firm(eco, corp, firm, rng)

    jobs = firm.jobs()
    assert len(jobs) == 1
    assert jobs[0].type_id == 13  # SoftwareDevelopment
    assert jobs[0].product.id == 85  # Software


def test_configure_sw_pub():
    """A Software Publisher gets SoftwareProduction + Sales."""
    sim, town = bread_town()
    eco = sim.economy
    corp, _ = _ai_corp(sim, town)
    x, y = find_site(sim, town)
    firm = eco.build_firm(9, corp, x, y, town)
    rng = Rng(42)
    _configure_new_firm(eco, corp, firm, rng)

    jobs = firm.jobs()
    assert len(jobs) == 2
    types = {j.type_id for j in jobs}
    assert 14 in types  # SoftwareProduction
    assert 12 in types  # Sales


def test_configure_restaurant():
    """A Restaurant gets Purchasing + Sales like a store."""
    sim, town = bread_town()
    eco = sim.economy
    corp, _ = _ai_corp(sim, town)
    x, y = find_site(sim, town)
    firm = eco.build_firm(10, corp, x, y, town)
    rng = Rng(42)
    _configure_new_firm(eco, corp, firm, rng)

    jobs = firm.jobs()
    assert len(jobs) == 2
    types = {j.type_id for j in jobs}
    assert 10 in types  # Purchasing
    assert 12 in types  # Sales


def test_configure_grants_technology():
    """_configure_new_firm grants the corp technology for the chosen products."""
    sim, town = bread_town()
    eco = sim.economy
    corp, _ = _ai_corp(sim, town)
    assert len(corp.technology) == 0

    x, y = find_site(sim, town)
    firm = eco.build_firm(1, corp, x, y, town)
    rng = Rng(42)
    _configure_new_firm(eco, corp, firm, rng)

    assert len(corp.technology) > 0
    product = firm.jobs()[0].product
    assert corp.has_technology(product)


def test_factory_links_inputs_to_manufacturing():
    """Factory purchasing slots are linked to the manufacturing slot."""
    sim, town = bread_town()
    eco = sim.economy
    corp, _ = _ai_corp(sim, town)
    x, y = find_site(sim, town)
    firm = eco.build_firm(2, corp, x, y, town)
    rng = Rng(7)
    _configure_new_firm(eco, corp, firm, rng)

    mfg = next(j for j in firm.jobs() if j.type_id == 7)
    linked = firm.linked_jobs(mfg.slot)
    purchase_jobs = [j for j in linked if j.type_id == 10]
    assert len(purchase_jobs) >= 1
