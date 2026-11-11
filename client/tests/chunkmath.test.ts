import { describe, expect, it } from "vitest";
import { CHUNK_PX, TILE_PX, chunkBytes, clampView, neededChunks, stepZoom } from "../src/chunkmath";

const MAP_W = 240;
const MAP_H = 198;

describe("neededChunks", () => {
  it("a phone at standard zoom keeps at most 6 chunks (24 MB)", () => {
    // 390 x 844 CSS px at dpr 3 = 1170 x 2532 device px; zoom 3 = 390 x 844 art px, about 12 tiles across.
    for (const x of [0, 300, 700, 1000, 3000])
      for (const y of [0, 200, 900, 3000]) {
        const n = neededChunks({ x, y, w: 1170, h: 2532, zoom: 3 }, MAP_W, MAP_H).length;
        expect(n).toBeLessThanOrEqual(6);
      }
    const got = neededChunks({ x: 3 * CHUNK_PX + 300, y: 3 * CHUNK_PX + 300, w: 1170, h: 2532, zoom: 3 }, MAP_W, MAP_H);
    expect(got).toEqual([
      [3, 3],
      [3, 4],
    ]);
  });

  it("never exceeds the map grid of 8 x 7 chunks", () => {
    const v = { x: 0, y: 0, w: 100000, h: 100000, zoom: 1 };
    expect(neededChunks(v, MAP_W, MAP_H).length).toBe(8 * 7);
  });

  it("a 1920 x 1080 desktop at zoom 1 keeps at most 12 chunks (48 MB)", () => {
    for (let x = 0; x < 4 * CHUNK_PX; x += 97)
      for (let y = 0; y < 4 * CHUNK_PX; y += 89) {
        const n = neededChunks({ x, y, w: 1920, h: 1080, zoom: 1 }, MAP_W, MAP_H).length;
        expect(n).toBeLessThanOrEqual(12);
      }
  });

  it("rejects fractional zoom", () => {
    expect(() => neededChunks({ x: 0, y: 0, w: 10, h: 10, zoom: 1.5 }, MAP_W, MAP_H)).toThrow();
  });
});

describe("zoom and camera", () => {
  it("steps through whole numbers only and stops at the ends", () => {
    let v = { x: 0, y: 0, w: 1000, h: 1000, zoom: 1 };
    v = stepZoom(v, 1);
    expect(v.zoom).toBe(2);
    v = stepZoom(stepZoom(v, 1), 1);
    expect(v.zoom).toBe(3);
    v = stepZoom(stepZoom(stepZoom(v, -1), -1), -1);
    expect(v.zoom).toBe(1);
  });

  it("keeps the point under the cursor fixed", () => {
    const v = { x: 1000, y: 2000, w: 800, h: 600, zoom: 1 };
    const z = stepZoom(v, 1, 200, 100);
    expect(z.x + 200 / z.zoom).toBeCloseTo(v.x + 200);
    expect(z.y + 100 / z.zoom).toBeCloseTo(v.y + 100);
  });

  it("clamps to the map and snaps to whole device pixels", () => {
    const c = clampView({ x: -50.3, y: 1e9, w: 1170, h: 2532, zoom: 3 }, MAP_W, MAP_H);
    expect(c.x).toBe(0);
    expect(c.y).toBeCloseTo(MAP_H * TILE_PX - 2532 / 3);
    expect(Number.isInteger(c.y * 3)).toBe(true);
  });
});

describe("chunk size options", () => {
  it("baked chunk memory grows with art scale squared", () => {
    expect(chunkBytes(32, 1)).toBe(4 * 2 ** 20);
    expect(chunkBytes(32, 2)).toBe(16 * 2 ** 20);
    expect(chunkBytes(16, 2)).toBe(4 * 2 ** 20);
  });

  it("16-tile chunks cover the same view with finer pieces", () => {
    const v = { x: 0, y: 0, w: 1024, h: 1024, zoom: 1 };
    expect(neededChunks(v, 240, 198, 0, 32)).toHaveLength(1);
    expect(neededChunks(v, 240, 198, 0, 16)).toHaveLength(4);
  });
});
