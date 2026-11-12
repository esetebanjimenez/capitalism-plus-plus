"""T4: Town spreads on level-up (native FUN_0004c334)."""

import pytest

from capitalism.rng import Rng
from capitalism.world import TileCategory, World


def _small_world(rng, *, level=1):
    """20×20 grassland world with one town at centre."""
    world = World(width=20, height=20)
    world.tiles = [
        World.__new__(World)  # dummy — overwritten below
        for _ in range(20 * 20)
    ]
    from capitalism.world import Tile

    world.tiles = [Tile(kind=TileCategory.GRASSLAND) for _ in range(20 * 20)]
    from capitalism.town import Town

    town = Town(
        id=0, name="Test", tier=0, x=10, y=10, stagger_slot=0,
        population=0.0, per_capita_gnp=10.0, level=level,
    )
    world.towns = [town]
    center = world.tile_at(10, 10)
    center.kind = TileCategory.TOWN
    center.ref = 0
    return world, town


def test_spread_paints_town_tiles():
    """After spread_town, some tiles near the centre become TOWN."""
    rng = Rng(42)
    world, town = _small_world(rng, level=3)
    world.spread_town(town, rng)
    town_count = sum(
        1 for y in range(20) for x in range(20)
        if world.tile_at(x, y).kind == TileCategory.TOWN
    )
    assert town_count > 1


def test_spread_respects_level_radius():
    """No tile beyond Chebyshev distance > level gets painted."""
    rng = Rng(42)
    world, town = _small_world(rng, level=2)
    world.spread_town(town, rng)
    cx, cy, lv = town.x, town.y, town.level
    for y in range(20):
        for x in range(20):
            if world.tile_at(x, y).kind == TileCategory.TOWN and (x, y) != (cx, cy):
                assert abs(x - cx) <= lv and abs(y - cy) <= lv


def test_spread_does_not_overwrite_firm():
    """FIRM tiles are never overwritten."""
    rng = Rng(42)
    world, town = _small_world(rng, level=3)
    firm_tile = world.tile_at(11, 10)
    firm_tile.kind = TileCategory.FIRM
    firm_tile.ref = 99
    world.spread_town(town, rng)
    assert world.tile_at(11, 10).kind == TileCategory.FIRM
    assert world.tile_at(11, 10).ref == 99


def test_spread_does_not_overwrite_existing_town():
    """Existing TOWN tiles keep their ref."""
    rng = Rng(42)
    world, town = _small_world(rng, level=3)
    other_tile = world.tile_at(9, 10)
    other_tile.kind = TileCategory.TOWN
    other_tile.ref = 5
    world.spread_town(town, rng)
    assert world.tile_at(9, 10).ref == 5


def test_monthly_tick_returns_true_on_level_up():
    """monthly_tick returns True when the town levels up."""
    from capitalism.town import Town, level_up_population

    rng = Rng(1)
    town = Town(
        id=0, name="Big", tier=0, x=5, y=5, stagger_slot=0,
        population=float(level_up_population(1)) + 1000.0,
        per_capita_gnp=10.0, level=1,
    )
    result = town.monthly_tick(rng, detailed=False)
    assert result is True
    assert town.level == 2


def test_monthly_tick_returns_false_no_level_up():
    """monthly_tick returns False when no level-up."""
    from capitalism.town import Town

    rng = Rng(1)
    town = Town(
        id=0, name="Small", tier=0, x=5, y=5, stagger_slot=0,
        population=100.0, per_capita_gnp=10.0, level=1,
    )
    result = town.monthly_tick(rng, detailed=False)
    assert result is False
    assert town.level == 1


def test_can_build_blocked_by_spread():
    """Tiles marked TOWN by spread_town block building."""
    rng = Rng(42)
    world, town = _small_world(rng, level=3)
    world.spread_town(town, rng)
    for y in range(20):
        for x in range(20):
            if world.tile_at(x, y).kind == TileCategory.TOWN:
                assert not world.can_build(x, y)
