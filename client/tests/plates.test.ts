// @vitest-environment happy-dom
import { describe, expect, it } from "vitest";
import ui from "../../art/atlas/ui_atlas.json";
import { TILE_PX, makeView } from "../src/chunkmath";
import { TownInfo } from "../src/mapdata";
import { PLATE_H, PLATE_W, TownPlates, badgeWidth, levelText, levelUps, plateRect } from "../src/ui/plates";

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

  it("lets taps through but answers long presses on the plate with its town (#336 review)", () => {
    const plates = new TownPlates();
    plates.setTowns([town(1, 2)]);
    const view = makeView(0, 0, 1280, 800, 1, 1);
    plates.update(view, 1, { x: 0, y: 0, w: 1280, h: 800 });
    const r = plateRect(town(1, 2), view, 1);
    expect(plates.townAt(r.x + 5, r.y + 5)?.id).toBe(1);
    expect(plates.townAt(r.x + r.w - 1, r.y + r.h - 1)?.id).toBe(1);
    expect(plates.townAt(r.x - 1, r.y + 5)).toBeNull();
    expect(plates.townAt(r.x + 5, r.y + r.h + 1)).toBeNull();
    const el = plates.layer.querySelector<HTMLElement>(".plate")!;
    expect(getComputedStyle(el).pointerEvents === "none" || el.onclick === null).toBe(true);
    plates.update(view, 1, { x: 0, y: 0, w: 10, h: 10 }); // plate hidden by a panel
    expect(plates.townAt(r.x + 5, r.y + 5)).toBeNull();
  });

  it("goes see-through while the tile under it is selected", () => {
    const plates = new TownPlates();
    plates.setTowns([town(1, 2)]);
    const view = makeView(0, 0, 1280, 800, 1, 1);
    const area = { x: 0, y: 0, w: 1280, h: 800 };
    const el = plates.layer.querySelector<HTMLElement>(".plate")!;
    const r = plateRect(town(1, 2), view, 1);
    const s = view.zoom;
    const under = { x: Math.floor((r.x / s + view.x) / TILE_PX), y: Math.floor(((r.y + r.h / 2) / s + view.y) / TILE_PX) };
    plates.selected = under;
    plates.update(view, 1, area);
    expect(el.classList.contains("dim")).toBe(true);
    plates.selected = { x: under.x, y: under.y + 6 };
    plates.update(view, 1, area);
    expect(el.classList.contains("dim")).toBe(false);
    plates.selected = null;
    plates.update(view, 1, area);
    expect(el.classList.contains("dim")).toBe(false);
  });

  it("is highlighted, never faded, while its town card is open", () => {
    const plates = new TownPlates();
    plates.setTowns([town(1, 2), { ...town(2, 1), x: 30 }]);
    const view = makeView(0, 0, 1280, 800, 1, 1);
    const area = { x: 0, y: 0, w: 1280, h: 800 };
    const [a, b] = Array.from(plates.layer.querySelectorAll<HTMLElement>(".plate"));
    plates.selected = { x: 10, y: 20 };
    plates.highlight = 1;
    plates.update(view, 1, area);
    expect(a.classList.contains("hl")).toBe(true);
    expect(a.classList.contains("dim")).toBe(false);
    expect(b.classList.contains("hl")).toBe(false);
    plates.highlight = null;
    plates.update(view, 1, area);
    expect(a.classList.contains("hl")).toBe(false);
  });
});
