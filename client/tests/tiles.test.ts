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
  townFootprint,
} from "../src/mapdata";
import { FIRM_SPRITES, flagFrame } from "../src/firms";
import { frameFor } from "../src/tiles";

function tiny(rows: string[], level = 1): MapData {
  const codes: Record<string, number> = { "~": DEEP_OCEAN, w: WATER, g: GRASSLAND, t: TOWN, f: FIRM };
  const height = rows.length;
  const width = rows[0].length;
  const kind = new Uint8Array(width * height);
  rows.forEach((r, y) => [...r].forEach((ch, x) => (kind[y * width + x] = codes[ch])));
  const towns: TownInfo[] = [];
  kind.forEach((k, i) => {
    if (k !== TOWN) return;
    const radius = level >= 5 ? 2 : level >= 3 ? 1 : 0;
    towns.push({ x: i % width, y: Math.floor(i / width), id: 7, level, radius, blockLevel: radius });
  });
  const climate = new Uint8Array(width * height).fill(2);
  const townAt = townFootprint(width, height, kind, towns);
  return { width, height, kind, climate, firms: [], towns, townAt };
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

  it("draws a level 1-2 town as one block tile", () => {
    expect(frameFor(tiny(["ggg", "gtg", "ggg"], 2), 1, 1)).toMatch(/^block_s[0-3]_l0$/);
    expect(frameFor(tiny(["ggg", "gtg", "ggg"], 2), 0, 0)).toMatch(/^grass_/);
  });

  it("draws a level 3-4 town as 3x3 with a road plus", () => {
    const m = tiny(["ggggg", "ggggg", "ggtgg", "ggggg", "ggggg"], 3);
    expect(frameFor(m, 2, 2)).toBe("road_15");
    expect(frameFor(m, 2, 1)).toBe("road_04"); // north arm joins only to the centre
    expect(frameFor(m, 1, 1)).toMatch(/^block_s[0-3]_l1$/);
    expect(frameFor(m, 0, 0)).toMatch(/^grass_/);
  });

  it("draws level 5-6 as 5x5 with a # of roads and a plaza, and keeps a town's roofs stable", () => {
    const m = tiny(["ggggg", "ggggg", "ggtgg", "ggggg", "ggggg"], 5);
    expect(frameFor(m, 2, 2)).toBe("plaza");
    expect(frameFor(m, 1, 1)).toBe("road_15"); // the # crossings
    expect(frameFor(m, 3, 3)).toBe("road_15");
    expect(frameFor(m, 2, 1)).toBe("road_10"); // between crossings, beside the plaza
    expect(frameFor(m, 1, 0)).toBe("road_04"); // a road end at the footprint edge
    expect(frameFor(m, 0, 1)).toBe("road_02");
    for (const [x, y] of [[0, 0], [2, 0], [0, 2], [4, 2], [2, 4], [4, 4]])
      expect(frameFor(m, x, y)).toMatch(/^block_s[0-3]_l2$/);
    expect(frameFor(m, 4, 4)).toBe(frameFor(tiny(["ggggg", "ggggg", "ggtgg", "ggggg", "ggggg"], 5), 4, 4));
  });

  it("firms and water win over the footprint", () => {
    const m = tiny(["fgg", "gtg", "ggw"], 3);
    expect(m.townAt[0]).toBe(-1);
    expect(m.townAt[8]).toBe(-1);
    expect(frameFor(m, 0, 0)).toMatch(/^grass_/);
    expect(frameFor(m, 2, 0)).toMatch(/^block_/);
  });

  it("the sample map has a 5x5 and a 3x3 town", () => {
    const buf = readFileSync(new URL("../public/sample-map.bin", import.meta.url));
    const m = parseMap(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
    expect(new Set(m.towns.map((t) => t.radius))).toEqual(new Set([1, 2]));
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
