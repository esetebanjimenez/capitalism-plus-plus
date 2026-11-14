import { describe, expect, it } from "vitest";
import ui from "../../art/atlas/ui_atlas.json";
import { TILE_PX, makeView } from "../src/chunkmath";
import { TownInfo } from "../src/mapdata";
import { PLATE_H, PLATE_W, badgeWidth, levelText, levelUps, plateRect } from "../src/ui/plates";

const town = (id: number, level: number): TownInfo => ({ id, name: `Town ${id}`, x: 10, y: 20, level });

describe("town plates (#250, view brief section 2)", () => {
  it("shows the level as a number, so any level needs no new art", () => {
    expect([1, 9, 10, 123].map(levelText)).toEqual(["1", "9", "10", "123"]);
    expect(badgeWidth(9)).toBeLessThan(badgeWidth(10));
    expect(badgeWidth(10)).toBeLessThan(badgeWidth(123));
    expect(badgeWidth(1)).toBeGreaterThanOrEqual(16);
    const frames = ui.frames as Record<string, unknown>;
    expect(frames.plate_level && frames.plate_pulse && frames.card).toBeTruthy();
  });

  it("pulses once when a town's level goes up between two reads", () => {
    const levels = new Map<number, number>();
    expect(levelUps(levels, [town(1, 2), town(2, 3)])).toEqual([]); // first read: nothing to compare
    levels.set(1, 2).set(2, 3);
    expect(levelUps(levels, [town(1, 3), town(2, 3)])).toEqual([1]);
    levels.set(1, 3);
    expect(levelUps(levels, [town(1, 3), town(2, 3)])).toEqual([]); // not again on the next read
  });

  it("is 136x24 and centred over the town tile", () => {
    const view = makeView(0, 0, 1280, 800, 1, 1);
    const r = plateRect(town(1, 1), view, 1);
    const s = view.zoom;
    expect([r.w, r.h]).toEqual([PLATE_W, PLATE_H]);
    expect(r.x + r.w / 2).toBeCloseTo((10.5 * TILE_PX - view.x) * s, 0);
    expect(r.y + r.h).toBeLessThan((20.5 * TILE_PX - view.y) * s);
  });
});
