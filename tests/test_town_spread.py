"""T4: town spread on level-up (native FUN_0004c334, #302)."""

from capitalism.rng import Rng
from capitalism.tables import TOWN_SPREAD
from capitalism.town import Town, level_up_population
from capitalism.world import (
    GRASS_PLACE,
    RURAL_KINDS,
    URBAN_KINDS,
    Tile,
    TileCategory,
    World,
    round_dist,
)

N = 30
C = 15


def _world(level: int = 1) -> tuple[World, Town]:
    """30x30 grassland with one town at the centre."""
    world = World(width=N, height=N)
    world.tiles = [Tile(kind=TileCategory.GRASSLAND) for _ in range(N * N)]
    town = Town(
        id=0,
        name="Test",
        tier=0,
        x=C,
        y=C,
        stagger_slot=0,
        population=0.0,
        per_capita_gnp=10.0,
        level=level,
    )
    world.towns = [town]
    centre = world.tile_at(C, C)
    centre.kind, centre.town_kind, centre.ref = TileCategory.TOWN, min(URBAN_KINDS), 0
    return world, town


def _cheb(x: int, y: int) -> int:
    return max(abs(x - C), abs(y - C))


def test_round_dist_rounds():
    assert [round_dist(1, 1), round_dist(1, 2), round_dist(2, 2), round_dist(3, 0)] == [1, 2, 3, 3]


def test_db_constants():
    assert (TOWN_SPREAD.spread_fringe, TOWN_SPREAD.spread_overlap_odds) == (4, 10)
    assert list(RURAL_KINDS) == list(range(0x3000, 0x3008))
    assert list(URBAN_KINDS) == list(range(0x3008, 0x300D))


def test_three_zones_seed_42():
    world, town = _world(level=3)
    world.spread_town(town, Rng(42))
    lv, reach = 3, 3 + 4
    overlap_urban = 0
    for y in range(N):
        for x in range(N):
            t = world.tile_at(x, y)
            d, c = round_dist(x - C, y - C), _cheb(x, y)
            if c > reach:
                assert t.kind == TileCategory.GRASSLAND  # outside the scan square
            elif c > lv:
                assert t.kind == TileCategory.TOWN and t.town_kind in RURAL_KINDS  # outer fringe
            elif d < lv:
                assert t.kind == TileCategory.TOWN and t.town_kind in URBAN_KINDS  # core
            else:
                assert t.kind in (TileCategory.TOWN, TileCategory.GRASSLAND)  # overlap
                if t.kind == TileCategory.TOWN:
                    assert t.town_kind in URBAN_KINDS
                    overlap_urban += 1
            if t.kind == TileCategory.TOWN:
                assert t.ref == town.id
    overlap = sum(
        1
        for y in range(N)
        for x in range(N)
        if _cheb(x, y) <= lv and round_dist(x - C, y - C) >= lv
    )
    assert overlap_urban < overlap  # 1-in-10, not all


def test_core_absorbs_rural_and_fringe_keeps_rural():
    world, town = _world(level=2)
    rng = Rng(7)
    world.spread_town(town, rng)
    ring = world.tile_at(C + 3, C)  # Chebyshev 3 > 2: rural
    assert ring.town_kind in RURAL_KINDS
    kept = world.tile_at(C + 5, C).town_kind  # stays fringe at level 3
    town.level = 3
    world.spread_town(town, rng)
    assert world.tile_at(C + 2, C).town_kind in URBAN_KINDS  # core at level 3 (d=2<3)
    assert world.tile_at(C + 5, C).town_kind == kept  # rural not re-converted


def test_forest_and_water_never_convert():
    world, town = _world(level=3)
    world.tile_at(C + 1, C).kind = TileCategory.FOREST_HILL
    world.tile_at(C + 5, C).kind = TileCategory.FOREST_HILL
    world.tile_at(C, C + 1).kind = TileCategory.WATER
    world.tile_at(C, C + 5).kind = TileCategory.DEEP_OCEAN
    world.spread_town(town, Rng(42))
    assert world.tile_at(C + 1, C).kind == TileCategory.FOREST_HILL
    assert world.tile_at(C + 5, C).kind == TileCategory.FOREST_HILL
    assert world.tile_at(C, C + 1).kind == TileCategory.WATER
    assert world.tile_at(C, C + 5).kind == TileCategory.DEEP_OCEAN


def test_other_town_sets_abort_flag_and_blocks_level_up():
    world, town = _world(level=2)
    other = world.tile_at(C + 4, C + 4)  # inside the scan square, last rows
    other.kind, other.town_kind, other.ref = TileCategory.TOWN, min(RURAL_KINDS), 5
    world.spread_town(town, Rng(42))
    assert town.spread_blocked
    assert other.ref == 5
    # The scan stopped on that tile: nothing after it (row order) was painted.
    assert world.tile_at(C + 5, C + 4).kind == TileCategory.GRASSLAND
    assert world.tile_at(C, C + 5).kind == TileCategory.GRASSLAND
    # Later spreads do nothing, and the monthly level-up is skipped.
    before = [t.kind for t in world.tiles]
    town.level = 3
    world.spread_town(town, Rng(1))
    assert [t.kind for t in world.tiles] == before
    town.level = 1
    town.population = float(level_up_population(1)) + 1000.0
    assert town.monthly_tick(Rng(1), detailed=False) is False and town.level == 1


class _Firm:
    def __init__(self, workforce: int) -> None:
        self.workforce = workforce
        self.place_kind = GRASS_PLACE
        self.place_town = -1


def test_firm_place_kind_follows_spread_only_without_workforce():
    world, town = _world(level=3)
    idle, busy = _Firm(0), _Firm(5)
    for i, (x, f) in enumerate(((C + 1, idle), (C - 1, busy))):
        t = world.tile_at(x, C)
        t.kind, t.ref = TileCategory.FIRM, i
    world.spread_town(town, Rng(42), [idle, busy])
    assert idle.place_kind in URBAN_KINDS and idle.place_town == town.id
    assert busy.place_kind == GRASS_PLACE and busy.place_town == -1
    assert world.tile_at(C + 1, C).kind == TileCategory.FIRM  # the firm stays on top


def test_town_tiles_are_buildable():
    world, town = _world(level=3)
    world.spread_town(town, Rng(42))
    assert world.can_build(C, C) and world.can_build(C + 6, C)


def test_monthly_tick_returns_true_on_level_up():
    town = Town(
        id=0,
        name="Big",
        tier=0,
        x=5,
        y=5,
        stagger_slot=0,
        population=float(level_up_population(1)) + 1000.0,
        per_capita_gnp=10.0,
        level=1,
    )
    assert town.monthly_tick(Rng(1), detailed=False) is True
    assert town.level == 2
