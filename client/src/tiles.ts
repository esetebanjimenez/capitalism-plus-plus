import { DEEP_OCEAN, FIRM, FOREST_HILL, MapData, WATER } from "./mapdata";

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

/** Index of the town whose footprint covers (x, y), or -1. */
function townIndex(m: MapData, x: number, y: number): number {
  if (x < 0 || y < 0 || x >= m.width || y >= m.height) return -1;
  return m.townAt[y * m.width + x];
}

/** Town roads form a plus through the centre of the footprint (Designer rule, PR #50). */
export function isRoad(m: MapData, x: number, y: number): boolean {
  const i = townIndex(m, x, y);
  if (i < 0) return false;
  const t = m.towns[i];
  return t.radius > 0 && (x === t.x || y === t.y);
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
  const ti = townIndex(m, x, y);
  if (ti >= 0) {
    const t = m.towns[ti];
    if (isRoad(m, x, y)) {
      const mask =
        (isRoad(m, x, y - 1) ? 1 : 0) |
        (isRoad(m, x + 1, y) ? 2 : 0) |
        (isRoad(m, x, y + 1) ? 4 : 0) |
        (isRoad(m, x - 1, y) ? 8 : 0);
      return `road_${String(mask).padStart(2, "0")}`;
    }
    // Roof style per tile from the town id and offset, so a town keeps its look.
    const roof = tileHash(t.id * 97 + (x - t.x), y - t.y) % 4;
    return `block_s${roof}_l${t.blockLevel}`;
  }
  const c = climateKey(m, x, y);
  if (k === FOREST_HILL) {
    return h % 8 === 0 ? `hill_${c}_${(h >>> 3) % 2}` : `forest_${c}_${(h >>> 3) % 4}`;
  }
  void FIRM;
  return `grass_${c}_${h % 4}`;
}
