"""Map and terrain + city placement — plain classes (design.md slice 2)."""

from __future__ import annotations

from enum import IntEnum
from math import floor

from .rng import Rng
from .tables import CITY_NAME_POOL, LAND_VALUE, MAP_RULES
from .town import Town

MAP_W = MAP_RULES.width
MAP_H = MAP_RULES.height
MAP_TILES = MAP_W * MAP_H
MIN_LAND_TILES = int(MAP_TILES * MAP_RULES.min_land_fraction)
CITY_BORDER = MAP_RULES.city_border
CITY_MIN_DIST = MAP_RULES.city_min_dist
MAX_CITIES = MAP_RULES.max_cities
LAND_VALUE_FLOOR = LAND_VALUE.floor


class TileCategory(IntEnum):
    DEEP_OCEAN = 0
    WATER = 1
    GRASSLAND = 2
    FOREST_HILL = 3
    TOWN = 4
    FIRM = 5


class Tile:
    __slots__ = ("climate", "height", "kind", "moisture", "rainfall", "ref", "soil")

    def __init__(
        self,
        *,
        kind: TileCategory = TileCategory.GRASSLAND,
        ref: int = -1,
        rainfall: int = 0,
        soil: int = 0,
        moisture: int = 0,
        climate: int = 0,
        height: float = 0.0,
    ) -> None:
        self.kind = kind
        self.ref = ref
        self.rainfall = rainfall
        self.soil = soil
        self.moisture = moisture
        self.climate = climate
        self.height = height

    # Aliases used by older call sites / tests
    @property
    def category(self) -> TileCategory:
        return self.kind

    @property
    def data_id(self) -> int:
        return self.ref


class World:
    """Map grid and the towns that live on it."""

    __slots__ = (
        "centroid",
        "days_since_spawn",
        "detailed_cities",
        "equator_row",
        "height",
        "last_spawn_day_serial",
        "target_cities",
        "tiles",
        "towns",
        "width",
    )

    def __init__(
        self,
        *,
        width: int = MAP_W,
        height: int = MAP_H,
        tiles: list[Tile] | None = None,
        towns: list[Town] | None = None,
        equator_row: int = 99,
        centroid: tuple[float, float] = (0.0, 0.0),
        detailed_cities: bool = True,
        target_cities: int = MAP_RULES.default_cities,
    ) -> None:
        self.width = width
        self.height = height
        self.tiles = tiles if tiles is not None else []
        self.towns = towns if towns is not None else []
        self.equator_row = equator_row
        self.centroid = centroid
        self.detailed_cities = detailed_cities
        self.target_cities = target_cities
        self.days_since_spawn = 0
        self.last_spawn_day_serial = 0

    def tile_at(self, x: int, y: int) -> Tile:
        return self.tiles[y * self.width + x]

    def land_value(self, x: int, y: int) -> int:
        """Proximity land value (decomp:43397-43447). Floor $500k."""
        if not self.towns:
            return LAND_VALUE_FLOOR
        best: Town | None = None
        best_d = 1e18
        for t in self.towns:
            d = ((t.x - x) ** 2 + (t.y - y) ** 2) ** 0.5
            if d < best_d:
                best_d = d
                best = t
        assert best is not None
        radius = best.level + 4
        small = (
            LAND_VALUE.small_town_factor if best.level <= LAND_VALUE.small_town_level_max else 1.0
        )
        base = best.per_capita_gnp * best.population / LAND_VALUE.base_divisor * small
        if best_d >= radius:
            value = 0.0
        else:
            value = base * (1.0 - best_d / radius)
        assert value < LAND_VALUE.assert_cap
        return max(LAND_VALUE_FLOOR, int(value))

    def can_build(self, x: int, y: int) -> bool:
        """True when a firm may be placed here. Subclasses override the rule."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.tile_at(x, y).kind in (TileCategory.GRASSLAND, TileCategory.FOREST_HILL)

    @classmethod
    def generate(
        cls,
        rng: Rng,
        *,
        detailed_cities: bool = True,
        target_cities: int = MAP_RULES.default_cities,
    ) -> World:
        """Procedural map + city placement. Constructs `cls`, not `World` by name."""
        world = cls(detailed_cities=detailed_cities, target_cities=target_cities)
        world._build_terrain(rng)
        world._place_cities(rng)
        world._update_centroid()
        return world

    def _build_terrain(self, rng: Rng) -> None:
        """Heightmap, waterline, and tile classification. Override for a new geology."""
        w, h = self.width, self.height
        n_tiles = w * h
        min_land = int(n_tiles * MAP_RULES.min_land_fraction)
        heightmap = _diamond_square(rng)
        raw = [
            _sample_height(heightmap, x, y, w, h) + rng.uniform(-2, 2)
            for y in range(h)
            for x in range(w)
        ]
        # Water-level normalization: shift so at least min_land tiles sit at 100+.
        sorted_h = sorted(raw)
        boundary = sorted_h[n_tiles - min_land]
        # Nudge past 100 so float noise can't leave a boundary tile as water.
        shift = (100.0 + 1e-6) - boundary
        raw = [v + shift for v in raw]

        equator = rng.randint(34, 164)
        dmax = max(equator, 197 - equator)
        soil_map = _neighbour_avg_noise(rng, w, h, 0, 3)
        moist_map = _neighbour_avg_noise(rng, w, h, 0, 100)

        tiles: list[Tile] = []
        for y in range(h):
            for x in range(w):
                hv = raw[y * w + x]
                if hv < 1:
                    kind = TileCategory.DEEP_OCEAN
                elif hv < 100:
                    kind = TileCategory.WATER
                elif hv < 215:
                    kind = TileCategory.GRASSLAND
                else:
                    kind = TileCategory.FOREST_HILL
                d = abs(y - equator)
                climate = rainfall = 4 - floor(5 * d / (dmax + 1))
                climate = max(0, min(4, climate))
                rainfall = max(0, min(4, rainfall))
                moisture = (
                    0
                    if kind in (TileCategory.DEEP_OCEAN, TileCategory.WATER)
                    else moist_map[y * w + x]
                )
                tiles.append(
                    Tile(
                        kind=kind,
                        rainfall=rainfall,
                        soil=soil_map[y * w + x],
                        moisture=moisture,
                        climate=climate,
                        height=hv,
                    )
                )
        self.tiles = tiles
        self.equator_row = equator

    def _update_centroid(self) -> None:
        if self.towns:
            cx = sum(t.x for t in self.towns) / len(self.towns)
            cy = sum(t.y for t in self.towns) / len(self.towns)
            self.centroid = (cx, cy)
        else:
            self.centroid = (0.0, 0.0)

    def _is_grass_block(self, cx: int, cy: int) -> bool:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                x, y = cx + dx, cy + dy
                if not (0 <= x < self.width and 0 <= y < self.height):
                    return False
                if self.tile_at(x, y).kind != TileCategory.GRASSLAND:
                    return False
        return True

    def _far_enough(self, x: int, y: int) -> bool:
        for t in self.towns:
            if abs(t.x - x) < CITY_MIN_DIST and abs(t.y - y) < CITY_MIN_DIST:
                return False
        return True

    def _place_cities(self, rng: Rng) -> None:
        used_names: set[str] = set()
        pool = list(CITY_NAME_POOL)
        attempts = 0
        consecutive_fail = 0
        target = min(self.target_cities, MAX_CITIES)
        while len(self.towns) < target and attempts < 1000 and consecutive_fail < 10:
            attempts += 1
            entry = rng.choice(pool)
            if entry.name in used_names:
                consecutive_fail += 1
                continue
            placed = False
            for _ in range(4_752):
                x = rng.randint(CITY_BORDER, self.width - 1 - CITY_BORDER)
                y = rng.randint(CITY_BORDER, self.height - 1 - CITY_BORDER)
                if self.tile_at(x, y).kind != TileCategory.GRASSLAND:
                    continue
                if not self._is_grass_block(x, y):
                    continue
                if not self._far_enough(x, y):
                    continue
                town = Town.create(
                    len(self.towns),
                    entry.name,
                    entry.tier,
                    x,
                    y,
                    rng,
                    detailed=self.detailed_cities,
                )
                self.towns.append(town)
                tile = self.tile_at(x, y)
                tile.kind = TileCategory.TOWN
                tile.ref = town.id
                used_names.add(entry.name)
                placed = True
                consecutive_fail = 0
                break
            if not placed:
                consecutive_fail += 1

    def try_spawn(self, rng: Rng, day_serial: int) -> bool:
        """Month-pass town spawn: 1-in-10, gates from design.md."""
        n_tiles = self.width * self.height
        if not self.detailed_cities:
            return False
        if len(self.towns) >= MAX_CITIES:
            return False
        if len(self.towns) >= n_tiles // 30:
            return False
        if day_serial - self.last_spawn_day_serial < MAP_RULES.spawn_min_days and self.towns:
            return False
        if not rng.chance(MAP_RULES.spawn_chance):
            return False
        before = len(self.towns)
        # one placement attempt burst
        old_target = self.target_cities
        self.target_cities = before + 1
        self._place_cities(rng)
        self.target_cities = old_target
        if len(self.towns) > before:
            self.last_spawn_day_serial = day_serial
            self._update_centroid()
            return True
        return False


def _diamond_square(rng: Rng, levels: int = 5) -> list[list[float]]:
    """257×257 heightmap (2^8+1) with displacements 320,160,80,40,20."""
    n = (1 << levels) + 1  # 33 for levels=5 — use 8 for 257
    # design: 5 levels; generating 257×257 and cropping is fine
    levels = 8
    n = (1 << levels) + 1
    grid = [[0.0] * n for _ in range(n)]
    for y, x in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)):
        grid[y][x] = rng.uniform(0, 320)
    step = n - 1
    mags = [320.0, 160.0, 80.0, 40.0, 20.0]
    mag_i = 0
    while step > 1:
        half = step // 2
        mag = mags[mag_i] if mag_i < len(mags) else mags[-1] / (2 ** (mag_i - len(mags) + 1))
        for y in range(0, n - 1, step):
            for x in range(0, n - 1, step):
                avg = (
                    grid[y][x] + grid[y][x + step] + grid[y + step][x] + grid[y + step][x + step]
                ) / 4.0
                grid[y + half][x + half] = avg + rng.uniform(-mag, mag)
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
        mag_i += 1
    return grid


def _sample_height(grid: list[list[float]], x: int, y: int, w: int, h: int) -> float:
    n = len(grid)
    # Crop centre of 257 into 240×198
    ox = (n - w) // 2
    oy = (n - h) // 2
    gx = min(n - 1, max(0, ox + x))
    gy = min(n - 1, max(0, oy + y))
    return grid[gy][gx]


def _neighbour_avg_noise(rng: Rng, w: int, h: int, lo: int, hi: int) -> list[int]:
    raw = [rng.randint(lo, hi) for _ in range(w * h)]
    out = [0] * (w * h)
    for y in range(h):
        for x in range(w):
            vals = [raw[y * w + x]]
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    vals.append(raw[ny * w + nx])
            out[y * w + x] = round(sum(vals) / len(vals))
    return out
