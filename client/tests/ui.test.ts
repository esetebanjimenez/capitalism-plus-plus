import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import ui from "../../art/atlas/ui_atlas.json";
import { TILE_PX } from "../src/chunkmath";
import { FIRM, MapData, WATER, parseMap } from "../src/mapdata";
import { money, nineSliceCss, panToShow, pickAt, tilesVisible, visibleMapRect } from "../src/ui/layout";

const sample = (): MapData => {
  const buf = readFileSync(new URL("../public/sample-map.bin", import.meta.url));
  return parseMap(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
};

describe("clear-map layout (docs/m2-ux-spec.md)", () => {
  it("phone portrait 390x844 shows 12x19 tiles at peek and 12x13 at half", () => {
    expect(tilesVisible(390, 844, "peek")).toEqual({ across: 12, down: 19 });
    expect(tilesVisible(390, 844, "half")).toEqual({ across: 12, down: 13 });
    expect(tilesVisible(390, 844, null)).toEqual({ across: 12, down: 26 });
  });

  it("desktop with the 400 pt side panel shows 47x30 tiles", () => {
    expect(tilesVisible(1920, 960, "peek")).toEqual({ across: 47, down: 30 });
    expect(visibleMapRect(1920, 960, "full").w).toBe(1520);
  });

  it("formats money with sign and unit", () => {
    expect(money(12340)).toBe("+$12,340");
    expect(money(-4_100_000)).toBe("\u2212$4.1M");
    expect(money(2.5e9)).toBe("+$2.5B");
  });

  it("builds nine-slice CSS in top right bottom left order", () => {
    const css = nineSliceCss("u", [6, 4, 8, 10], 2);
    expect(css).toContain("border-width:4px 8px 10px 6px");
    expect(css).toContain("url(u) 8 16 20 12 fill / 4px 8px 10px 6px");
  });

  it("ui atlas has every frame the shell uses", () => {
    for (const f of ["card", "card_float", "btn_primary", "btn_secondary", "handle", "badge", "icon_menu", "icon_close", "icon_cal", "icon_cash", "icon_pause_on", "icon_play_on"])
      expect(Object.keys(ui.frames)).toContain(f);
  });
});

describe("tap picking", () => {
  const m = sample();
  const pt = 1; // 32 pt tiles: one point per world unit
  const centre = (x: number, y: number): [number, number] => [(x + 0.5) * TILE_PX, (y + 0.5) * TILE_PX];

  it("snaps to a firm within 24 pt of its tile centre", () => {
    const f = m.firms[0];
    const one = { ...m, firms: [f] }; // a lone firm, so the snap is unambiguous
    const [cx, cy] = centre(f.x, f.y);
    expect(pickAt(one, cx + 23, cy, pt)).toEqual({ kind: "firm", firm: f });
    expect(pickAt(one, cx + 16, cy + 16, pt)).toEqual({ kind: "firm", firm: f });
    expect(pickAt(one, cx + 40, cy, pt).kind).not.toBe("firm");
  });

  it("picks the nearer of two neighbouring firms", () => {
    const a = m.firms[0];
    const b = { ...a, x: a.x + 1 };
    const two = { ...m, firms: [a, b] };
    const [cx, cy] = centre(a.x, a.y);
    expect(pickAt(two, cx + 10, cy, pt)).toEqual({ kind: "firm", firm: a });
    expect(pickAt(two, cx + 22, cy, pt)).toEqual({ kind: "firm", firm: b });
  });

  it("opens the town card from the town's own tile and the tile card from ring tiles", () => {
    const t = m.towns.find((t) => t.level >= 5)!;
    expect(pickAt(m, ...centre(t.x, t.y), pt)).toEqual({ kind: "town", town: t });
    expect(pickAt(m, ...centre(t.x + 1, t.y), pt)).toEqual({ kind: "tile", x: t.x + 1, y: t.y });
  });

  it("selects nothing on water or off the map", () => {
    const i = Array.from(m.kind).findIndex((k) => k <= WATER);
    expect(pickAt(m, ...centre(i % m.width, Math.floor(i / m.width)), pt)).toEqual({ kind: "none" });
    expect(pickAt(m, -50, -50, pt)).toEqual({ kind: "none" });
    expect(m.kind.includes(FIRM)).toBe(true);
  });

  it("pans a tile hidden under the sheet into the visible map", () => {
    const view = { x: 0, y: 0 };
    const rect = visibleMapRect(390, 844, "half");
    expect(panToShow(view, 5, 5, rect, pt)).toEqual([0, 0]);
    const [dx, dy] = panToShow(view, 5, 20, rect, pt);
    const sy = (20 * TILE_PX - dy) * pt;
    expect(dx).not.toBe(0);
    expect(sy).toBeGreaterThan(TILE_PX);
    expect(sy + 2 * TILE_PX).toBeLessThanOrEqual(rect.h);
  });
});

describe("TINF section", () => {
  const m = sample();
  it("carries the date, player cash and per-tile values", () => {
    const info = m.info!;
    expect(info).toBeDefined();
    expect(info.year).toBeGreaterThan(1900);
    expect(info.month).toBeGreaterThanOrEqual(1);
    expect(info.month).toBeLessThanOrEqual(12);
    expect(Number.isFinite(info.cash)).toBe(true); // the sample player has built firms, so it can be negative
    const n = m.width * m.height;
    for (const a of [info.soil, info.rainfall, info.buildable, info.landValue]) expect(a.length).toBe(n);
    expect(Math.max(...info.soil)).toBeLessThanOrEqual(3);
    expect(Math.max(...info.rainfall)).toBeLessThanOrEqual(4);
    // Nothing is buildable on water.
    for (let i = 0; i < n; i++) if (m.kind[i] <= WATER) expect(info.buildable[i]).toBe(0);
    expect(info.buildable.includes(1)).toBe(true);
  });
});
