/** Terrain kinds, matching capitalism.world.TileCategory. */
export const DEEP_OCEAN = 0;
export const WATER = 1;
export const GRASSLAND = 2;
export const FOREST_HILL = 3;
export const TOWN = 4;
export const FIRM = 5;

export interface MapData {
  width: number;
  height: number;
  /** TileCategory per tile, row-major. */
  kind: Uint8Array;
  /** Climate band per tile, 0 = poles .. 4 = equator. */
  climate: Uint8Array;
  firms: FirmInfo[];
  towns: TownInfo[];
  /** Per tile: index into `towns` whose drawn footprint covers it, or -1 (see townFootprint). */
  townAt: Int16Array;
}

export interface TownInfo {
  x: number;
  y: number;
  id: number;
  level: number;
  /** Footprint radius in tiles and block sprite level, from the town_footprints table. */
  radius: number;
  blockLevel: number;
}

/**
 * Which town's drawn footprint covers each tile (Designer rule, PR #50). Visual only:
 * the sim town is still one tile. Firm and water tiles are never covered, and where
 * footprints overlap, a town's own centre wins, then the earlier town.
 */
export function townFootprint(
  width: number,
  height: number,
  kind: Uint8Array,
  towns: TownInfo[],
): Int16Array {
  const at = new Int16Array(width * height).fill(-1);
  towns.forEach((t, i) => (at[t.y * width + t.x] = i));
  towns.forEach((t, i) => {
    for (let dy = -t.radius; dy <= t.radius; dy++)
      for (let dx = -t.radius; dx <= t.radius; dx++) {
        const x = t.x + dx;
        const y = t.y + dy;
        if (x < 0 || y < 0 || x >= width || y >= height) continue;
        const j = y * width + x;
        if (at[j] === -1 && kind[j] > WATER && kind[j] !== FIRM) at[j] = i;
      }
  });
  return at;
}

export interface FirmInfo {
  x: number;
  y: number;
  /** firm_types.id */
  type: number;
  /** Owning corporation id, or null for none (the seaport). */
  owner: number | null;
}

/** Parse the b"CPPM" sample-map payload written by scripts/export_sample_map.py. */
export function parseMap(buf: ArrayBuffer): MapData {
  const head = new Uint8Array(buf, 0, 4);
  if (String.fromCharCode(...head) !== "CPPM") throw new Error("not a CPPM map");
  const view = new DataView(buf);
  const width = view.getUint16(4, true);
  const height = view.getUint16(6, true);
  const n = width * height;
  const fo = 8 + 2 * n;
  const count = view.getUint16(fo, true);
  const to = fo + 2 + 6 * count;
  const nTowns = view.getUint16(to, true);
  if (buf.byteLength !== to + 2 + 8 * nTowns) throw new Error("CPPM map size mismatch");
  const firms: FirmInfo[] = [];
  for (let i = 0, o = fo + 2; i < count; i++, o += 6) {
    const owner = view.getUint8(o + 5);
    firms.push({
      x: view.getUint16(o, true),
      y: view.getUint16(o + 2, true),
      type: view.getUint8(o + 4),
      owner: owner === 255 ? null : owner,
    });
  }
  const towns: TownInfo[] = [];
  for (let i = 0, o = to + 2; i < nTowns; i++, o += 8) {
    towns.push({
      x: view.getUint16(o, true),
      y: view.getUint16(o + 2, true),
      id: view.getUint8(o + 4),
      level: view.getUint8(o + 5),
      radius: view.getUint8(o + 6),
      blockLevel: view.getUint8(o + 7),
    });
  }
  const kind = new Uint8Array(buf, 8, n);
  return {
    width,
    height,
    kind,
    climate: new Uint8Array(buf, 8 + n, n),
    firms,
    towns,
    townAt: townFootprint(width, height, kind, towns),
  };
}
