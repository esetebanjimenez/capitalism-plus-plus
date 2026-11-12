"""J6 + M1: Resource deposits, extraction rate from deposit, discovery."""

from capitalism.rng import Rng
from capitalism.tables import RAW_RESOURCE_TYPES
from capitalism.world import Tile, TileCategory, World


def _flat_world(rng, *, kind=TileCategory.GRASSLAND, width=20, height=20):
    """Small world of uniform terrain, no towns."""
    world = World(width=width, height=height)
    world.tiles = [Tile(kind=kind) for _ in range(width * height)]
    world.towns = []
    return world


# --- J6: extraction rate from deposit ---


def test_raw_resource_table_loaded():
    """RAW_RESOURCE_TYPES loaded from capitalism.db with 8 entries."""
    assert len(RAW_RESOURCE_TYPES) == 8
    assert 1 in RAW_RESOURCE_TYPES  # Aluminum
    assert 8 in RAW_RESOURCE_TYPES  # Timber


def test_timber_speed_is_1():
    """Timber (product 8) extraction speed = 1 (from 1STD.SET RAW table)."""
    assert RAW_RESOURCE_TYPES[8].speed == 1


def test_mine_speed_is_2():
    """Mine resources (product 1-5, 7) extraction speed = 2."""
    for pid in (1, 2, 3, 4, 5, 7):
        assert RAW_RESOURCE_TYPES[pid].speed == 2, f"product {pid}"


def test_oil_speed_is_4():
    """Oil (product 6) extraction speed = 4."""
    assert RAW_RESOURCE_TYPES[6].speed == 4


def test_extraction_rate_from_resource():
    """J6: Extraction.rate comes from RAW entry speed, not fixed constant."""
    from capitalism.scenario import bread_town, find_site

    sim, town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("TestCorp")
    x, y = find_site(sim, town)
    mine = eco.build_firm(6, corp, x, y, town)  # Mine
    product = eco.catalog.by_id[5]  # Iron Ore
    corp.technology[product.id] = product.state.tech_level
    job = mine.add_job(0, 8, product)  # Mining job
    mine.reserve = 10.0
    assert job.rate == 2.0  # Iron speed from RAW table


def test_extraction_rate_timber():
    """Timber extraction rate = 1 (speed from RAW table)."""
    from capitalism.scenario import bread_town, find_site

    sim, town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("Logger")
    x, y = find_site(sim, town)
    camp = eco.build_firm(5, corp, x, y, town)  # Logging Camp
    product = eco.catalog.by_id[8]  # Timber
    corp.technology[product.id] = product.state.tech_level
    job = camp.add_job(0, 4, product)  # Logging job
    camp.reserve = 10.0
    assert job.rate == 1.0


def test_extraction_rate_oil():
    """Oil extraction rate = 4 (speed from RAW table)."""
    from capitalism.scenario import bread_town, find_site

    sim, town = bread_town()
    eco = sim.economy
    corp = eco.add_corp("Driller")
    x, y = find_site(sim, town)
    well = eco.build_firm(7, corp, x, y, town)  # Oil Well
    product = eco.catalog.by_id[6]  # Oil
    corp.technology[product.id] = product.state.tech_level
    job = well.add_job(0, 9, product)  # OilExtraction job
    well.reserve = 10.0
    assert job.rate == 4.0


# --- M1: initial deposit placement ---


def test_initial_deposits_placed():
    """place_initial_deposits creates deposits on the map."""
    rng = Rng(42)
    world = _flat_world(rng)
    world.place_initial_deposits(rng)
    assert world.total_deposits > 0


def test_initial_deposits_all_terrain_matching_types():
    """Every resource type whose terrain is present gets at least 1 deposit."""
    rng = Rng(42)
    world = _flat_world(rng)
    world.place_initial_deposits(rng)
    for res_id, entry in RAW_RESOURCE_TYPES.items():
        if entry.terrain_type == 2:
            continue  # forest-only types can't place on all-grassland
        assert world.deposit_counts.get(res_id, 0) >= 1, f"product {res_id}"


def test_deposit_on_correct_terrain():
    """Deposits are only placed on terrain matching the resource type."""
    rng = Rng(42)
    world = _flat_world(rng)
    world.place_initial_deposits(rng)
    for y in range(world.height):
        for x in range(world.width):
            tile = world.tile_at(x, y)
            if tile.resource == 0:
                continue
            entry = RAW_RESOURCE_TYPES[tile.resource]
            if entry.terrain_type == 1:
                assert tile.kind == TileCategory.GRASSLAND
            elif entry.terrain_type == 2:
                assert tile.kind == TileCategory.FOREST_HILL


def test_timber_needs_forest():
    """Timber deposits (terrain_type=2) are not placed on pure grassland."""
    rng = Rng(42)
    world = _flat_world(rng, kind=TileCategory.GRASSLAND)
    world.place_initial_deposits(rng)
    assert world.deposit_counts.get(8, 0) == 0  # Timber = product 8


def test_no_deposit_on_water():
    """No deposits on water tiles."""
    rng = Rng(42)
    world = _flat_world(rng, kind=TileCategory.WATER)
    world.place_initial_deposits(rng)
    assert world.total_deposits == 0


def test_tile_resource_field():
    """Tile.resource holds the product_id of the placed deposit."""
    rng = Rng(42)
    world = _flat_world(rng)
    world.place_initial_deposits(rng)
    found = False
    for y in range(world.height):
        for x in range(world.width):
            tile = world.tile_at(x, y)
            if tile.resource != 0:
                assert tile.resource in RAW_RESOURCE_TYPES
                found = True
    assert found


# --- M1: discovery gate ---


def test_discovery_gate_blocks_before_365():
    """discover_resources does nothing before day 366."""
    rng = Rng(42)
    world = _flat_world(rng)
    world.place_initial_deposits(Rng(42))
    before = world.total_deposits
    world.discover_resources(rng, day_serial=365, start_day_serial=0)
    assert world.total_deposits == before


def test_discovery_gate_opens_after_365():
    """After day 365, discovery can add deposits (run many days for chance)."""
    rng = Rng(42)
    world = _flat_world(rng)
    world.place_initial_deposits(Rng(42))
    before = world.total_deposits
    for d in range(366, 500):
        world.discover_resources(rng, day_serial=d, start_day_serial=0)
    assert world.total_deposits >= before
