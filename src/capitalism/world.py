"""Map and terrain + city placement (gamelogic.md: Map and terrain, Towns and cities)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

from .city_names import CITY_NAMES
from .rng import Rng
from .town import Town

MAP_W = 240
MAP_H = 198
MAP_TILES = MAP_W * MAP_H  # 47_520
MIN_LAND_TILES = MAP_TILES // 3  # 15_840
CITY_BORDER = 5
CITY_MIN_DIST = 15
MAX_CITIES = 12
LAND_VALUE_FLOOR = 500_000


class TileCategory(IntEnum):
    DEEP_OCEAN = 0
    WATER = 1
    GRASSLAND = 2
    FOREST_HILL = 3
    TOWN = 4
    FIRM = 5


@dataclass
class Tile:
    category: TileCategory = TileCategory.GRASSLAND
    variant: int = 0
    data_id: int = -1  # town or firm id when applicable
    rainfall: int = 0  # 0-4
    soil: int = 0  # 0-3
    moisture: int = 0  # 0-100
    height: float = 0.0


@dataclass
class World:
    width: int = MAP_W
    height: int = MAP_H
    tiles: list[Tile] = field(default_factory=list)
    towns: list[Town] = field(default_factory=list)
    equator_row: int = 99
    centroid: tuple[float, float] = (0.0, 0.0)
    detailed_cities: bool = True
    target_cities: int = 8

    def tile_at(self, x: int, y: int) -> Tile:
        return self.tiles[y * self.width + x]

    def land_value(self, x: int, y: int) -> int:
        """Town-proximity land value with $500k floor. Building bonus lands later."""
        if not self.towns:
            return LAND_VALUE_FLOOR
        best = None
        best_d = 1e18
        for t in self.towns:
            d = ((t.x - x) ** 2 + (t.y - y) ** 2) ** 0.5
            if d < best_d:
                best_d = d
                best = t
        assert best is not None
        radius = best.level + 4
        if best_d >= radius:
            return LAND_VALUE_FLOOR
        # Base from level and population
        base = 500_000 + best.level * 200_000 + best.population * 0.5
        if best.level <= 2:
            base *= 0.75
        value = base * (1.0 - best_d / radius)
        return max(LAND_VALUE_FLOOR, int(value))


def _diamond_square(rng: Rng, size: int, levels: int = 5) -> list[list[float]]:
    """Generate a (2^levels)+1 square heightmap, then we'll sample into map size."""
    n = (1 << levels) + 1  # 33 for levels=5
    grid = [[0.0] * n for _ in range(n)]
    # Seed corners
    for y, x in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)):
        grid[y][x] = rng.uniform(0, 320)
    step = n - 1
    mag = 320.0
    while step > 1:
        half = step // 2
        # Diamond
        for y in range(0, n - 1, step):
            for x in range(0, n - 1, step):
                avg = (
                    grid[y][x]
                    + grid[y][x + step]
                    + grid[y + step][x]
                    + grid[y + step][x + step]
                ) / 4.0
                grid[y + half][x + half] = avg + rng.uniform(-mag, mag)
        # Square
        for y in range(0, n, half):
            for x in range((y + half) % step, n, step):
                vals = []
                if y - half >= 0:
                    vals.append(grid[y - half][x])
                if y + half < n:
                    vals.append(grid[y + half][x])
                if x - half >= 0:
                    vals.append(grid[y][x - half])
                if x + half < n:
                    vals.append(grid[y][x + half])
                grid[y][x] = sum(vals) / len(vals) + rng.uniform(-mag, mag)
        step = half
        mag *= 0.5
    return grid


def _sample_height(grid: list[list[float]], x: int, y: int, w: int, h: int) -> float:
    n = len(grid)
    gx = x / max(1, w - 1) * (n - 1)
    gy = y / max(1, h - 1) * (n - 1)
    x0, y0 = int(gx), int(gy)
    x1, y1 = min(n - 1, x0 + 1), min(n - 1, y0 + 1)
    tx, ty = gx - x0, gy - y0
    a = grid[y0][x0] * (1 - tx) + grid[y0][x1] * tx
    b = grid[y1][x0] * (1 - tx) + grid[y1][x1] * tx
    return a * (1 - ty) + b * ty


def generate_world(
    rng: Rng,
    *,
    detailed_cities: bool = True,
    target_cities: int = 8,
) -> World:
    """Procedural map + city placement. Visual shading/zoom cut for M1."""
    w, h = MAP_W, MAP_H
    heightmap = _diamond_square(rng, max(w, h), levels=5)
    # Sample and count land (height > 99 in doc's water-level check uses different scale;
    # we normalize after).
    raw = [_sample_height(heightmap, x, y, w, h) for y in range(h) for x in range(w)]
    # Shift so median-ish lands above water: raise if too little land above threshold.
    threshold = 99.0
    land_count = sum(1 for v in raw if v > threshold)
    if land_count < MIN_LAND_TILES:
        # Raise all heights proportionally toward more land
        deficit = MIN_LAND_TILES - land_count
        # Simple boost: add enough so more tiles clear threshold
        boost = 20.0 + deficit / MAP_TILES * 80.0
        raw = [v + boost for v in raw]

    equator = rng.randint(34, 164)
    tiles: list[Tile] = []
    for y in range(h):
        for x in range(w):
            hv = raw[y * w + x] + rng.uniform(-2, 2)  # jitter
            if hv < 1:
                cat = TileCategory.DEEP_OCEAN
            elif hv < 100:
                cat = TileCategory.WATER
            elif hv < 215:
                cat = TileCategory.GRASSLAND
            else:
                cat = TileCategory.FOREST_HILL
            dist = abs(y - equator)
            rainfall = max(0, 4 - dist // 33)
            soil = rng.randint(0, 3)
            moisture = 0 if cat in (TileCategory.DEEP_OCEAN, TileCategory.WATER) else rng.randint(0, 100)
            tiles.append(
                Tile(
                    category=cat,
                    variant=rng.randint(0, 4),
                    rainfall=rainfall,
                    soil=soil,
                    moisture=moisture,
                    height=hv,
                )
            )

    world = World(
        tiles=tiles,
        equator_row=equator,
        detailed_cities=detailed_cities,
        target_cities=target_cities,
    )
    _place_cities(world, rng)
    if world.towns:
        cx = sum(t.x for t in world.towns) / len(world.towns)
        cy = sum(t.y for t in world.towns) / len(world.towns)
        world.centroid = (cx, cy)
    return world


def _is_grass_block(world: World, cx: int, cy: int) -> bool:
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            x, y = cx + dx, cy + dy
            if not (0 <= x < world.width and 0 <= y < world.height):
                return False
            if world.tile_at(x, y).category != TileCategory.GRASSLAND:
                return False
    return True


def _far_enough(world: World, x: int, y: int) -> bool:
    # Chebyshev exclusion: both |dx| and |dy| must be < 15 to reject
    # (gamelogic.md: min 15 tiles in both axes independently).
    for t in world.towns:
        if abs(t.x - x) < CITY_MIN_DIST and abs(t.y - y) < CITY_MIN_DIST:
            return False
    return True


def _place_cities(world: World, rng: Rng) -> None:
    used_names: set[str] = set()
    pool = list(CITY_NAMES)
    attempts = 0
    consecutive_fail = 0
    target = min(world.target_cities, MAX_CITIES)
    while len(world.towns) < target and attempts < 1000 and consecutive_fail < 10:
        attempts += 1
        name, tier = rng.choice(pool)
        if name in used_names:
            consecutive_fail += 1
            continue
        placed = False
        for _ in range(200):
            x = rng.randint(CITY_BORDER, world.width - 1 - CITY_BORDER)
            y = rng.randint(CITY_BORDER, world.height - 1 - CITY_BORDER)
            if world.tile_at(x, y).category != TileCategory.GRASSLAND:
                continue
            if not _is_grass_block(world, x, y):
                continue
            if not _far_enough(world, x, y):
                continue
            town = Town.create(
                len(world.towns),
                name,
                tier,
                x,
                y,
                rng,
                detailed=world.detailed_cities,
            )
            world.towns.append(town)
            used_names.add(name)
            # Paint town tiles (footprint radius = level + 4, clipped)
            r = town.level + 4
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    tx, ty = x + dx, y + dy
                    if (
                        0 <= tx < world.width
                        and 0 <= ty < world.height
                        and dx * dx + dy * dy <= r * r
                    ):
                        tile = world.tile_at(tx, ty)
                        if tile.category in (TileCategory.GRASSLAND, TileCategory.FOREST_HILL):
                            tile.category = TileCategory.TOWN
                            tile.data_id = town.id
            placed = True
            consecutive_fail = 0
            break
        if not placed:
            consecutive_fail += 1
