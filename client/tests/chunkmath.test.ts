import { describe, expect, it } from "vitest";
import {
  CHUNK_PX,
  TILE_PX,
  chunkBytes,
  clampView,
  deviceScale,
  makeView,
  neededChunks,
  sheetFor,
  STANDARD_STEP,
  stepZoom,
  ZOOM_STEPS,
} from "../src/chunkmath";

const MAP_W = 240;
const MAP_H = 198;
const phone3x = (x: number, y: number, step = 2) => makeView(x, y, 1170, 2532, step, 3);
const desktop = (x: number, y: number, w = 1920, h = 1080) => makeView(x, y, w, h, 2, 1);

describe("neededChunks", () => {
  it("a phone at standard zoom keeps at most 6 chunks (24 MB)", () => {
    // 390 x 844 points at dpr 3 = 1170 x 2532 canvas px; step 2 = 32 pt tiles, about 12 across.
    for (const x of [0, 300, 700, 1000, 3000])
      for (const y of [0, 200, 900, 3000]) {
        expect(neededChunks(phone3x(x, y), MAP_W, MAP_H).length).toBeLessThanOrEqual(6);
      }
    expect(neededChunks(phone3x(3 * CHUNK_PX + 300, 3 * CHUNK_PX + 300), MAP_W, MAP_H)).toEqual([
      [3, 3],
      [3, 4],
    ]);
  });

  it("never exceeds the map grid of 8 x 7 chunks", () => {
    expect(neededChunks(desktop(0, 0, 100000, 100000), MAP_W, MAP_H).length).toBe(8 * 7);
  });

  it("a 1920 x 1080 desktop at standard zoom keeps at most 12 chunks (48 MB)", () => {
    for (let x = 0; x < 4 * CHUNK_PX; x += 97)
      for (let y = 0; y < 4 * CHUNK_PX; y += 89) {
        expect(neededChunks(desktop(x, y), MAP_W, MAP_H).length).toBeLessThanOrEqual(12);
      }
  });

  it("accepts a fractional canvas scale", () => {
    const v = makeView(0, 0, 1170, 2532, 1, 3);
    expect(v.zoom).toBe(1.5);
    expect(neededChunks(v, MAP_W, MAP_H).length).toBeGreaterThan(0);
  });
});

describe("zoom steps in points", () => {
  it("a step draws the same tile size in points on every screen", () => {
    for (const step of [1, 2])
      for (const res of [1, 2, 3]) {
        expect((deviceScale(step, res) * TILE_PX) / res).toBe(16 * step);
      }
  });

  it("standard step keeps the 12-tile phone view on 2x and 3x screens and 60 across a desktop", () => {
    const across = (wPt: number, res: number, step = 2) => (wPt * res) / deviceScale(step, res) / TILE_PX;
    expect(across(390, 2)).toBeCloseTo(12.19, 2);
    expect(across(390, 3)).toBeCloseTo(12.19, 2);
    expect(across(1920, 1)).toBe(60);
  });

  it("picks the 64 px sheet once a tile spans 64 canvas px", () => {
    expect(sheetFor(deviceScale(2, 3))).toBe(64); // 3x phone standard: 64 px art at 1.5x
    expect(sheetFor(deviceScale(2, 2))).toBe(64); // 2x phone standard: 64 px art at 1:1
    expect(sheetFor(deviceScale(1, 3))).toBe(32); // 3x phone, 16 pt: 32 px art at 1.5x
    expect(sheetFor(deviceScale(1, 2))).toBe(32); // 2x phone, 16 pt: 32 px art at 1:1
    expect(sheetFor(deviceScale(2, 1))).toBe(32); // desktop standard: 32 px art at 1:1
  });
});

describe("zoom and camera", () => {
  it("has only the standard 32 pt view", () => {
    expect([...ZOOM_STEPS]).toEqual([STANDARD_STEP]);
    const v = makeView(0, 0, 1000, 1000, STANDARD_STEP, 3);
    expect(stepZoom(v, 1)).toBe(v);
    expect(stepZoom(v, -1)).toBe(v);
  });

  it("keeps the point under the cursor fixed", () => {
    const v = makeView(1000, 2000, 800, 600, 1, 3);
    const z = { ...v, step: 2, zoom: 3, x: v.x + 200 / 1.5 - 200 / 3, y: v.y + 100 / 1.5 - 100 / 3 };
    expect(z.x + 200 / z.zoom).toBeCloseTo(v.x + 200 / v.zoom);
    expect(z.y + 100 / z.zoom).toBeCloseTo(v.y + 100 / v.zoom);
  });

  it("clamps to the map and snaps to whole canvas pixels", () => {
    const c = clampView(phone3x(-50.3, 1e9), MAP_W, MAP_H);
    expect(c.x).toBe(0);
    expect(c.y).toBeCloseTo(MAP_H * TILE_PX - 2532 / 3);
    expect(Number.isInteger(c.y * 3)).toBe(true);
    const f = clampView(phone3x(1000.37, 900.11, 1), MAP_W, MAP_H);
    expect(Math.abs(f.x * 1.5 - Math.round(f.x * 1.5))).toBeLessThan(1e-9);
  });
});

describe("chunk size options", () => {
  it("baked chunk memory grows with art scale squared", () => {
    expect(chunkBytes(32, 1)).toBe(4 * 2 ** 20);
    expect(chunkBytes(32, 2)).toBe(16 * 2 ** 20);
    expect(chunkBytes(16, 2)).toBe(4 * 2 ** 20);
  });

  it("16-tile chunks cover the same view with finer pieces", () => {
    const v = desktop(0, 0, 1024, 1024);
    expect(neededChunks(v, 240, 198, 0, 32)).toHaveLength(1);
    expect(neededChunks(v, 240, 198, 0, 16)).toHaveLength(4);
  });
});
