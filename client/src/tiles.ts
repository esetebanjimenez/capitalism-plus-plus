import { DEEP_OCEAN, FIRM, FOREST_HILL, MapData, TOWN, WATER } from "./mapdata";

/** Stable per-tile hash for variant picks (art/README.md: any stable hash of x, y). */
export function tileHash(x: number, y: number): number {
  let h = Math.imul(x, 73856093) ^ Math.imul(y, 19349663);
  h = Math.imul(h ^ (h >>> 13), 0x5bd1e995);
  return (h ^ (h >>> 15)) >>> 0;
}

function kindAt(m: MapData, x: number, y: number): number {
  if (x < 0 || y < 0 || x >= m.width || y >= m.height) return DEEP_OCEAN;
  return m.kind[y * m.width + x];
}

const isLand = (k: number) => k > WATER;

/**
 * Placeholder town layout until town data reaches the client: on TOWN tiles,
 * every third column and every second row is road (art/README.md preview rule).
 */
export function isRoad(m: MapData, x: number, y: number): boolean {
  return kindAt(m, x, y) === TOWN && (x % 3 === 0 || y % 2 === 0);
}

/** Climate suffix: `c{a}`, or `c{a}c{b}` on a band edge where the tile south has climate b = a±1. */
function climateKey(m: MapData, x: number, y: number): string {
  const a = m.climate[y * m.width + x];
  if (y + 1 < m.height) {
    const b = m.climate[(y + 1) * m.width + x];
    if (Math.abs(b - a) === 1) return `c${a}c${b}`;
  }
  return `c${a}`;
}

/**
 * Atlas frame name for one tile, following the naming in art/README.md.
 * Firm tiles draw as grassland here; the firm sprite goes on top (src/firms.ts).
 */
export function frameFor(m: MapData, x: number, y: number): string {
  const k = kindAt(m, x, y);
  const h = tileHash(x, y);
  if (k === DEEP_OCEAN) {
    if (kindAt(m, x, y - 1) === WATER) return "shelf_n";
    if (kindAt(m, x + 1, y) === WATER) return "shelf_e";
    if (kindAt(m, x, y + 1) === WATER) return "shelf_s";
    if (kindAt(m, x - 1, y) === WATER) return "shelf_w";
    return `deep_${h % 3}`;
  }
  if (k === WATER) {
    const mask =
      (isLand(kindAt(m, x, y - 1)) ? 1 : 0) |
      (isLand(kindAt(m, x + 1, y)) ? 2 : 0) |
      (isLand(kindAt(m, x, y + 1)) ? 4 : 0) |
      (isLand(kindAt(m, x - 1, y)) ? 8 : 0);
    if (mask) return `coast_${String(mask).padStart(2, "0")}`;
    if (isLand(kindAt(m, x + 1, y - 1))) return "coast_corner_ne";
    if (isLand(kindAt(m, x + 1, y + 1))) return "coast_corner_se";
    if (isLand(kindAt(m, x - 1, y + 1))) return "coast_corner_sw";
    if (isLand(kindAt(m, x - 1, y - 1))) return "coast_corner_nw";
    return `water_${h % 3}`;
  }
  if (k === TOWN) {
    // The sim marks a town as one tile today; draw a lone town tile as a tower block.
    const lone = ![
      [0, -1],
      [1, 0],
      [0, 1],
      [-1, 0],
    ].some(([dx, dy]) => kindAt(m, x + dx, y + dy) === TOWN);
    if (lone) return `block_s${h % 4}_l2`;
    if (isRoad(m, x, y)) {
      const mask =
        (isRoad(m, x, y - 1) ? 1 : 0) |
        (isRoad(m, x + 1, y) ? 2 : 0) |
        (isRoad(m, x, y + 1) ? 4 : 0) |
        (isRoad(m, x - 1, y) ? 8 : 0);
      return `road_${String(mask).padStart(2, "0")}`;
    }
    if (h % 11 === 0) return h % 2 ? "plaza" : `park_${(h >>> 1) % 2}`;
    return `block_s${h % 4}_l${(h >>> 2) % 3}`;
  }
  const c = climateKey(m, x, y);
  if (k === FOREST_HILL) {
    return h % 8 === 0 ? `hill_${c}_${(h >>> 3) % 2}` : `forest_${c}_${(h >>> 3) % 4}`;
  }
  void FIRM;
  return `grass_${c}_${h % 4}`;
}
