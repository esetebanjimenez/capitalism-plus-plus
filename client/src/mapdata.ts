/** Terrain kinds, matching capitalism.world.TileCategory. */
export const DEEP_OCEAN = 0;
export const WATER = 1;
export const GRASSLAND = 2;
export const FOREST_HILL = 3;
export const TOWN = 4;
export const FIRM = 5;

/** Native town tile kinds (art/README.md, #311): rural rings urban. */
export const RURAL_MIN = 0x3000;
export const RURAL_MAX = 0x3007;
export const URBAN_MIN = 0x3008;
export const URBAN_MAX = 0x300c;

export interface MapData {
  width: number;
  height: number;
  /** TileCategory per tile, row-major. */
  kind: Uint8Array;
  /** Climate band per tile, 0 = poles .. 4 = equator. */
  climate: Uint8Array;
  /** Tile.ref per tile: the owning town id on a town tile, the firm id on a firm tile, else -1. */
  ref: Int16Array;
  /** Native town tile kind per tile (rural 0x3000-0x3007, urban 0x3008-0x300c), else 0.
   * A firm tile carries the town kind it stands on. */
  townKind: Uint16Array;
  firms: FirmInfo[];
  towns: TownInfo[];
  /** `map_rev` these arrays match (-1 for the sample map). */
  rev: number;
  /** Sim values for the panels, from the sample map's TINF section only. */
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
  /** Sim town id. */
  id: number;
  name: string;
  x: number;
  y: number;
  level: number;
}

export interface FirmInfo {
  /** Sim firm id (-1 in the sample map, which has none). */
  id: number;
  x: number;
  y: number;
  /** firm_types.id */
  type: number;
  /** Owning corporation id, or null for none (the seaport). */
  owner: number | null;
}

/** "rural", "urban" or null for a native town tile kind. */
export function townBand(k: number): "rural" | "urban" | null {
  if (k >= RURAL_MIN && k <= RURAL_MAX) return "rural";
  if (k >= URBAN_MIN && k <= URBAN_MAX) return "urban";
  return null;
}

/** The town drawn on tile index `i` (town tiles only), or null. */
export function townOfTile(m: MapData, i: number): TownInfo | null {
  if (m.kind[i] !== TOWN) return null;
  return m.towns.find((t) => t.id === m.ref[i]) ?? null;
}

// --- live map from the sim facade (docs/m2-facade-contract.md, `map` / `map_objects`) ---

export interface MapTownJson {
  id: number;
  name: string;
  x: number;
  y: number;
  level: number;
}

export interface MapFirmJson {
  id: number;
  x: number;
  y: number;
  type_id: number;
  owner: number | null;
}

export interface MapObjectsJson {
  map_rev: number;
  towns: MapTownJson[];
  firms: MapFirmJson[];
  /** [[index, kind, ref, town_kind], ...] since the asked rev, or null with full arrays. */
  changes?: [number, number, number, number][] | null;
  kind?: number[];
  ref?: number[];
  town_kind?: number[];
}

export interface MapJson extends MapObjectsJson {
  width: number;
  height: number;
  kind: number[];
  ref: number[];
  town_kind: number[];
  climate: number[];
}

const townsFrom = (towns: MapTownJson[]): TownInfo[] =>
  towns.map((t) => ({ id: t.id, name: t.name, x: t.x, y: t.y, level: t.level }));

const firmsFrom = (firms: MapFirmJson[]): FirmInfo[] =>
  firms.map((f) => ({ id: f.id, x: f.x, y: f.y, type: f.type_id, owner: f.owner }));

/** Build MapData from the `map` query. */
export function mapFromJson(j: MapJson): MapData {
  const n = j.width * j.height;
  for (const a of [j.kind, j.ref, j.town_kind, j.climate])
    if (a.length !== n) throw new Error("map query size mismatch");
  return {
    width: j.width,
    height: j.height,
    kind: Uint8Array.from(j.kind),
    climate: Uint8Array.from(j.climate),
    ref: Int16Array.from(j.ref),
    townKind: Uint16Array.from(j.town_kind),
    towns: townsFrom(j.towns),
    firms: firmsFrom(j.firms),
    rev: j.map_rev,
  };
}

export interface MapDelta {
  /** Tile indices whose kind, ref or town kind changed. */
  tiles: number[];
  /** True when firms were added, removed or moved. */
  firms: boolean;
}

/**
 * Apply a `map_objects` result to `m` in place: changed tiles (or the full arrays when
 * `changes` is null), towns and firms. Returns what changed so the caller rebuilds only that.
 */
export function applyMapObjects(m: MapData, o: MapObjectsJson): MapDelta {
  const tiles: number[] = [];
  if (o.changes) {
    for (const [i, k, r, tk] of o.changes) {
      m.kind[i] = k;
      m.ref[i] = r;
      m.townKind[i] = tk;
      tiles.push(i);
    }
  } else if (o.kind && o.ref && o.town_kind) {
    for (let i = 0; i < m.kind.length; i++) {
      if (m.kind[i] === o.kind[i] && m.ref[i] === o.ref[i] && m.townKind[i] === o.town_kind[i]) continue;
      m.kind[i] = o.kind[i];
      m.ref[i] = o.ref[i];
      m.townKind[i] = o.town_kind[i];
      tiles.push(i);
    }
  }
  const firms = firmsFrom(o.firms);
  const key = (f: FirmInfo) => `${f.id}:${f.x}:${f.y}:${f.type}:${f.owner}`;
  const changed = firms.length !== m.firms.length || firms.some((f, i) => key(f) !== key(m.firms[i]));
  m.firms = firms;
  m.towns = townsFrom(o.towns);
  m.rev = o.map_rev;
  return { tiles, firms: changed };
}

// --- sample map (tests and `npm run bench`) ---

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
  const ro = to + 2 + 6 * nTowns;
  const io = ro + 4 * n;
  const hasInfo = buf.byteLength === io + 16 + 7 * n;
  if (buf.byteLength !== io && !hasInfo) throw new Error("CPPM map size mismatch");
  const firms: FirmInfo[] = [];
  for (let i = 0, o = fo + 2; i < count; i++, o += 6) {
    const owner = view.getUint8(o + 5);
    firms.push({
      id: -1,
      x: view.getUint16(o, true),
      y: view.getUint16(o + 2, true),
      type: view.getUint8(o + 4),
      owner: owner === 255 ? null : owner,
    });
  }
  const towns: TownInfo[] = [];
  for (let i = 0, o = to + 2; i < nTowns; i++, o += 6) {
    const id = view.getUint8(o + 4);
    towns.push({
      id,
      name: `Town ${id}`,
      x: view.getUint16(o, true),
      y: view.getUint16(o + 2, true),
      level: view.getUint8(o + 5),
    });
  }
  // copies: typed arrays wider than a byte need aligned offsets
  const ref = new Int16Array(buf.slice(ro, ro + 2 * n));
  const townKind = new Uint16Array(buf.slice(ro + 2 * n, ro + 4 * n));
  let info: TileInfo | undefined;
  if (hasInfo) {
    if (String.fromCharCode(...new Uint8Array(buf, io, 4)) !== "TINF") throw new Error("bad TINF section");
    const t = io + 16;
    info = {
      year: view.getUint16(io + 4, true),
      month: view.getUint8(io + 6),
      day: view.getUint8(io + 7),
      cash: view.getFloat64(io + 8, true),
      soil: new Uint8Array(buf, t, n),
      rainfall: new Uint8Array(buf, t + n, n),
      buildable: new Uint8Array(buf, t + 2 * n, n),
      landValue: new Uint32Array(buf.slice(t + 3 * n, t + 7 * n)),
    };
  }
  return {
    info,
    width,
    height,
    kind: new Uint8Array(buf, 8, n),
    climate: new Uint8Array(buf, 8 + n, n),
    ref,
    townKind,
    firms,
    towns,
    rev: -1,
  };
}
