import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import atlas from "../../art/atlas/terrain_atlas.json";
import {
  DEEP_OCEAN,
  FIRM,
  GRASSLAND,
  MapData,
  TOWN,
  TownInfo,
  WATER,
  parseMap,
} from "../src/mapdata";
import { FIRM_SPRITES, flagFrame } from "../src/firms";
import { frameFor } from "../src/tiles";

/** Tiny map from rows: ~ deep, w water, g grass, f firm, r rural town tile, u urban town tile. */
function tiny(rows: string[]): MapData {
  const codes: Record<string, number> = { "~": DEEP_OCEAN, w: WATER, g: GRASSLAND, r: TOWN, u: TOWN, f: FIRM };
  const height = rows.length;
  const width = rows[0].length;
  const n = width * height;
  const kind = new Uint8Array(n);
  const ref = new Int16Array(n).fill(-1);
  const townKind = new Uint16Array(n);
  rows.forEach((r, y) =>
    [...r].forEach((ch, x) => {
      const i = y * width + x;
      kind[i] = codes[ch];
      if (ch === "r" || ch === "u") {
        ref[i] = 7;
        townKind[i] = ch === "r" ? 0x3000 + ((x + y) % 8) : 0x3008 + ((x + y) % 5);
      }
    }),
  );
  const towns: TownInfo[] = [{ id: 7, name: "Town 7", x: 0, y: 0, level: 1 }];
  const climate = new Uint8Array(n).fill(2);
  return { width, height, kind, climate, ref, townKind, firms: [], towns, rev: 0 };
}

describe("frameFor", () => {
  it("uses the coast mask N=1 E=2 S=4 W=8", () => {
    const m = tiny(["~g~", "gwg", "~w~"]);
    expect(frameFor(m, 1, 1)).toBe("coast_11"); // land N, E, W
  });

  it("uses a corner piece when land is only diagonal", () => {
    const m = tiny(["~~g", "~w~", "~~~"]);
    expect(frameFor(m, 1, 1)).toBe("coast_corner_ne");
  });

  it("picks a shelf for deep ocean next to shallow water", () => {
    const m = tiny(["~w~", "~~~", "~~~"]);
    expect(frameFor(m, 1, 1)).toBe("shelf_n");
  });

  it("uses a dithered band-edge tile where the climate changes to the south", () => {
    const m = tiny(["g", "g"]);
    m.climate[1] = 3;
    expect(frameFor(m, 0, 0)).toMatch(/^grass_c2c3_[0-3]$/);
    expect(frameFor(m, 0, 1)).toMatch(/^grass_c3_[0-3]$/);
  });

  it("draws town tiles from the native kind: rural 0x3000-7, urban 0x3008-c", () => {
    const m = tiny(["rrr", "rur", "rrr"]);
    expect(frameFor(m, 1, 1)).toBe(`town_urban_${(1 + 1) % 5}`);
    expect(frameFor(m, 0, 0)).toBe("town_rural_0");
    expect(frameFor(m, 2, 1)).toBe(`town_rural_${3 % 8}`);
    m.townKind[4] = 0x300c;
    expect(frameFor(m, 1, 1)).toBe("town_urban_4");
    m.townKind[0] = 0x3007;
    expect(frameFor(m, 0, 0)).toBe("town_rural_7");
  });

  it("a firm draws the town tile it stands on, or grass off town", () => {
    const m = tiny(["fgg", "gfg", "ggg"]);
    expect(frameFor(m, 0, 0)).toMatch(/^grass_/);
    m.townKind[4] = 0x3009;
    expect(frameFor(m, 1, 1)).toBe("town_urban_1");
  });

  it("the sample map has rural and urban tiles of every variant", () => {
    const buf = readFileSync(new URL("../public/sample-map.bin", import.meta.url));
    const m = parseMap(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
    const kinds = new Set(Array.from(m.townKind).filter((k) => k));
    for (let k = 0x3000; k <= 0x300c; k++) expect(kinds.has(k)).toBe(true);
    for (let i = 0; i < m.kind.length; i++) if (m.kind[i] === TOWN) expect(m.townKind[i]).not.toBe(0);
  });

  it("every tile of the sample map has an atlas frame", () => {
    const buf = readFileSync(new URL("../public/sample-map.bin", import.meta.url));
    const m = parseMap(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
    expect([m.width, m.height]).toEqual([240, 198]);
    const missing = new Set<string>();
    for (let y = 0; y < m.height; y++)
      for (let x = 0; x < m.width; x++) {
        const f = frameFor(m, x, y);
        if (!(f in atlas.frames)) missing.add(f);
      }
    expect([...missing]).toEqual([]);
  });
});

describe("firms", () => {
  const buf = readFileSync(new URL("../public/sample-map.bin", import.meta.url));
  const m = parseMap(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));

  it("the sample map has all 14 firm types, owned firms flagged", () => {
    expect(new Set(m.firms.map((f) => f.type)).size).toBe(14);
    expect(m.firms.find((f) => f.type === 14)?.owner).toBeNull();
    expect(new Set(m.firms.map((f) => f.owner))).toEqual(new Set([null, 0, 1, 2]));
  });

  it("every firm type and owner flag has an atlas frame", () => {
    for (const name of Object.values(FIRM_SPRITES)) expect(name in atlas.frames).toBe(true);
    for (let o = 0; o < 12; o++) expect(flagFrame(o) in atlas.frames).toBe(true);
  });
});
