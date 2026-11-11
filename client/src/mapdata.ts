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
  const count = buf.byteLength >= fo + 2 ? view.getUint16(fo, true) : 0;
  if (buf.byteLength !== fo + 2 + 6 * count) throw new Error("CPPM map size mismatch");
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
  return {
    width,
    height,
    kind: new Uint8Array(buf, 8, n),
    climate: new Uint8Array(buf, 8 + n, n),
    firms,
  };
}
