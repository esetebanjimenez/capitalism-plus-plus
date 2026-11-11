/** Pure chunk and camera maths, kept free of Pixi so it can be unit-tested. */

export const TILE_PX = 32;
export const CHUNK_TILES = 32;
export const CHUNK_PX = TILE_PX * CHUNK_TILES; // 1024
export const CHUNK_BYTES = CHUNK_PX * CHUNK_PX * 4; // RGBA8, about 4 MB
export const ZOOM_STEPS = [1, 2, 3] as const;

export interface View {
  /** World pixel (at zoom 1) of the screen's top-left corner. */
  x: number;
  y: number;
  /** Screen size in device pixels. */
  w: number;
  h: number;
  /** Whole-number zoom: device pixels per art pixel. */
  zoom: number;
}

export const chunkKey = (cx: number, cy: number) => `${cx},${cy}`;

export function chunkGrid(mapW: number, mapH: number) {
  return { cols: Math.ceil(mapW / CHUNK_TILES), rows: Math.ceil(mapH / CHUNK_TILES) };
}

/** Default keep-alive margin around the screen, in art pixels (8 tiles). */
export const MARGIN_PX = 8 * TILE_PX;

/**
 * Chunks overlapping the view grown by `marginPx` art pixels on every side,
 * clamped to the map. Chunks outside this set are evicted.
 */
export function neededChunks(
  v: View,
  mapW: number,
  mapH: number,
  marginPx = MARGIN_PX,
): [number, number][] {
  if (!Number.isInteger(v.zoom) || v.zoom < 1) throw new Error("zoom must be a whole number >= 1");
  const { cols, rows } = chunkGrid(mapW, mapH);
  const wx = v.w / v.zoom;
  const wy = v.h / v.zoom;
  const x0 = Math.max(0, Math.floor((v.x - marginPx) / CHUNK_PX));
  const y0 = Math.max(0, Math.floor((v.y - marginPx) / CHUNK_PX));
  const x1 = Math.min(cols - 1, Math.floor((v.x + wx + marginPx - 1) / CHUNK_PX));
  const y1 = Math.min(rows - 1, Math.floor((v.y + wy + marginPx - 1) / CHUNK_PX));
  const out: [number, number][] = [];
  for (let cy = y0; cy <= y1; cy++) for (let cx = x0; cx <= x1; cx++) out.push([cx, cy]);
  return out;
}

/** Keep the camera inside the map and on whole device pixels. */
export function clampView(v: View, mapW: number, mapH: number): View {
  const worldW = mapW * TILE_PX;
  const worldH = mapH * TILE_PX;
  const viewW = v.w / v.zoom;
  const viewH = v.h / v.zoom;
  const clamp = (p: number, span: number, world: number) =>
    span >= world ? (world - span) / 2 : Math.min(Math.max(p, 0), world - span);
  const snap = (p: number) => Math.round(p * v.zoom) / v.zoom;
  return { ...v, x: snap(clamp(v.x, viewW, worldW)), y: snap(clamp(v.y, viewH, worldH)) };
}

/** Next whole-number zoom step, keeping the world point under (sx, sy) fixed on screen. */
export function stepZoom(v: View, dir: 1 | -1, sx = v.w / 2, sy = v.h / 2): View {
  const i = ZOOM_STEPS.indexOf(v.zoom as (typeof ZOOM_STEPS)[number]);
  const next = ZOOM_STEPS[Math.min(ZOOM_STEPS.length - 1, Math.max(0, i + dir))];
  if (next === v.zoom) return v;
  const px = v.x + sx / v.zoom;
  const py = v.y + sy / v.zoom;
  return { ...v, zoom: next, x: px - sx / next, y: py - sy / next };
}
