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
  /** Sim values for the panels, from the TINF section (until the client runs the sim). */
  info?: TileInfo;
}

export interface TileInfo {
  year: number;
  month: number;
  day: number;
  /** Player corporation cash in dollars. */
  cash: number;
  /** Per tile, row-major: Tile.soil (0-3), Tile.rainfall (0-4), World.can_build (0/1). */
  soil: Uint8Array;
  rainfall: Uint8Array;
  buildable: Uint8Array;
  /** World.land_value per tile, in dollars. */
  landValue: Uint32Array;
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
  const io = to + 2 + 8 * nTowns;
  const hasInfo = buf.byteLength === io + 16 + 7 * n;
  if (buf.byteLength !== io && !hasInfo) throw new Error("CPPM map size mismatch");
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
  let info: TileInfo | undefined;
  if (hasInfo) {
    if (String.fromCharCode(...new Uint8Array(buf, io, 4)) !== "TINF") throw new Error("bad TINF section");
    const t = io + 16;
    const lv = buf.slice(t + 3 * n, t + 7 * n); // copy: Uint32Array needs 4-byte alignment
    info = {
      year: view.getUint16(io + 4, true),
      month: view.getUint8(io + 6),
      day: view.getUint8(io + 7),
      cash: view.getFloat64(io + 8, true),
      soil: new Uint8Array(buf, t, n),
      rainfall: new Uint8Array(buf, t + n, n),
      buildable: new Uint8Array(buf, t + 2 * n, n),
      landValue: new Uint32Array(lv),
    };
  }
  return {
    info,
    width,
    height,
    kind,
    climate: new Uint8Array(buf, 8 + n, n),
    firms,
    towns,
    townAt: townFootprint(width, height, kind, towns),
  };
}
