/** Pure panel-layout and tap maths for the clear-map layout (docs/m2-ux-spec.md). No DOM. */

import { TILE_PX } from "../chunkmath";
import { FIRM, FirmInfo, MapData, TownInfo, WATER } from "../mapdata";

/** Screens at least this many points wide use the desktop side panel. */
export const DESKTOP_MIN_PT = 720;
export const SIDE_PANEL_PT = 400;
/** Sheet heights as a share of the screen. 390 x 844: peek leaves 19 rows of 32 pt, half 13. */
export const SHEET_SHARE = { peek: 0.28, half: 0.5, full: 1 } as const;
export type SheetHeight = keyof typeof SHEET_SHARE;
/** A tap within this many points of a firm's or town's tile centre selects it (spec: 24 px). */
export const SNAP_PT = 24;

export const isDesktop = (widthPt: number) => widthPt >= DESKTOP_MIN_PT;

export const sheetPt = (h: SheetHeight, screenHPt: number) => Math.round(SHEET_SHARE[h] * screenHPt);

/** The part of the screen the map still shows with a panel open, in points. */
export function visibleMapRect(
  screenW: number,
  screenH: number,
  panel: SheetHeight | null,
): { x: number; y: number; w: number; h: number } {
  if (!panel) return { x: 0, y: 0, w: screenW, h: screenH };
  if (isDesktop(screenW)) return { x: 0, y: 0, w: screenW - SIDE_PANEL_PT, h: screenH };
  return { x: 0, y: 0, w: screenW, h: screenH - sheetPt(panel, screenH) };
}

/** Whole tiles visible (spec "Tiles visible" table), with `ptPerTile` points per tile. */
export function tilesVisible(screenW: number, screenH: number, panel: SheetHeight | null, ptPerTile = 32) {
  const r = visibleMapRect(screenW, screenH, panel);
  return { across: Math.floor(r.w / ptPerTile), down: Math.floor(r.h / ptPerTile) };
}

export type Pick =
  | { kind: "firm"; firm: FirmInfo }
  | { kind: "town"; town: TownInfo }
  | { kind: "tile"; x: number; y: number }
  | { kind: "none" };

/**
 * What a tap at world point (wx, wy) selects. A firm within SNAP_PT points of its tile centre
 * wins, then a town's own tile; otherwise the land tile (ring tiles of a town footprint
 * included), or nothing on water. `ptPerWorld` is points per world unit at the current zoom.
 */
export function pickAt(m: MapData, wx: number, wy: number, ptPerWorld: number): Pick {
  const snap = SNAP_PT / ptPerWorld;
  const dist = (x: number, y: number) => Math.hypot(wx - (x + 0.5) * TILE_PX, wy - (y + 0.5) * TILE_PX);
  const tx = Math.floor(wx / TILE_PX);
  const ty = Math.floor(wy / TILE_PX);
  let firm: FirmInfo | null = null;
  let best = Infinity;
  for (const f of m.firms) {
    const d = f.x === tx && f.y === ty ? 0 : dist(f.x, f.y);
    if (d <= snap && d < best) [firm, best] = [f, d];
  }
  if (firm) return { kind: "firm", firm };
  for (const t of m.towns) if (t.x === tx && t.y === ty) return { kind: "town", town: t };
  if (tx < 0 || ty < 0 || tx >= m.width || ty >= m.height) return { kind: "none" };
  const k = m.kind[ty * m.width + tx];
  if (k <= WATER || k === FIRM) return { kind: "none" };
  return { kind: "tile", x: tx, y: ty };
}

/**
 * Camera shift (world units) that brings tile (tx, ty) inside the visible map rect with a
 * one-tile margin, or [0, 0] when it is already there. `ptPerWorld` as in pickAt.
 */
export function panToShow(
  view: { x: number; y: number },
  tx: number,
  ty: number,
  rect: { x: number; y: number; w: number; h: number },
  ptPerWorld: number,
): [number, number] {
  const sx = (tx * TILE_PX - view.x) * ptPerWorld;
  const sy = (ty * TILE_PX - view.y) * ptPerWorld;
  const tile = TILE_PX * ptPerWorld;
  const inside =
    sx >= rect.x + tile && sy >= rect.y + tile && sx + tile <= rect.x + rect.w - tile && sy + tile <= rect.y + rect.h - tile;
  if (inside) return [0, 0];
  const cx = rect.x + rect.w / 2 - tile / 2;
  const cy = rect.y + rect.h / 2 - tile / 2;
  return [(sx - cx) / ptPerWorld, (sy - cy) / ptPerWorld];
}

/** Money with a sign and unit (spec "Numbers"): +$12,340 under a million, else +$4.1M. */
export function money(v: number): string {
  const sign = v < 0 ? "\u2212" : "+";
  const a = Math.abs(v);
  if (a >= 1e9) return `${sign}$${(a / 1e9).toFixed(1)}B`;
  if (a >= 1e6) return `${sign}$${(a / 1e6).toFixed(1)}M`;
  return `${sign}$${Math.round(a).toLocaleString("en-US")}`;
}

/** CSS for a nine-slice atlas frame: slice is [l, t, r, b] in points; `scale` sheet px per point. */
export function nineSliceCss(url: string, slice: readonly number[], scale: number): string {
  const [l, t, r, b] = slice;
  const px = [t, r, b, l].map((v) => v * scale).join(" ");
  const pt = [t, r, b, l].map((v) => `${v}px`).join(" ");
  return `border-style:solid;border-width:${pt};border-image:url(${url}) ${px} fill / ${pt} stretch;`;
}
