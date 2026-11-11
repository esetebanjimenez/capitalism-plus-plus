import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import atlas from "../../art/atlas/terrain_atlas.json";
import { DEEP_OCEAN, GRASSLAND, MapData, TOWN, WATER, parseMap } from "../src/mapdata";
import { FIRM_SPRITES, flagFrame } from "../src/firms";
import { frameFor } from "../src/tiles";

function tiny(rows: string[]): MapData {
  const codes: Record<string, number> = { "~": DEEP_OCEAN, w: WATER, g: GRASSLAND, t: TOWN };
  const height = rows.length;
  const width = rows[0].length;
  const kind = new Uint8Array(width * height);
  rows.forEach((r, y) => [...r].forEach((ch, x) => (kind[y * width + x] = codes[ch])));
  return { width, height, kind, climate: new Uint8Array(width * height).fill(2), firms: [] };
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

  it("joins town roads by neighbour mask", () => {
    const m = tiny(["ttt", "ttt", "ttt"]);
    expect(frameFor(m, 0, 0)).toBe("road_06"); // E and S are roads
    expect(frameFor(m, 1, 1)).toMatch(/^(block_s[0-3]_l[0-2]|park_[01]|plaza)$/);
  });

  it("draws a lone town tile as a tower block", () => {
    expect(frameFor(tiny(["ggg", "gtg", "ggg"]), 1, 1)).toMatch(/^block_s[0-3]_l2$/);
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
