/** Pure chunk and camera maths, kept free of Pixi so it can be unit-tested. */

export const TILE_PX = 32;
export const CHUNK_TILES = 32;
export const CHUNK_PX = TILE_PX * CHUNK_TILES; // 1024
export const CHUNK_BYTES = CHUNK_PX * CHUNK_PX * 4; // RGBA8, about 4 MB
/**
 * Zoom is counted in points so it looks the same on every screen density. Step n draws a
 * tile at 16 x n points; the map has one view, step 2 = 32 pt tiles, about 12 across a phone
 * (docs/m2-ux-spec.md, Esteban 2026-11-11). The far overview comes later as its own mode.
 */
export const ZOOM_STEPS = [2] as const;
export const STANDARD_STEP = 2;
export const POINTS_PER_TILE_STEP = 16;

/** Canvas pixels per 32 px art pixel for a zoom step on a canvas at `resolution` px per point. */
export const deviceScale = (step: number, resolution: number) =>
  (step * POINTS_PER_TILE_STEP * resolution) / TILE_PX;

/**
 * Which art sheet to draw with: the 64 px sheet once a tile spans 64 or more canvas pixels
 * (64 px art at 1:1 or larger, e.g. 1.5x on a 3x phone at the standard step), else the
 * 32 px sheet, which is pixel-exact or larger there instead of dropping pixels.
 */
export const sheetFor = (scale: number): 32 | 64 => (scale * TILE_PX >= 64 ? 64 : 32);

export interface View {
  /** World pixel (at zoom 1) of the screen's top-left corner. */
  x: number;
  y: number;
  /** Screen size in device pixels. */
  w: number;
  h: number;
  /** Zoom step (ZOOM_STEPS), in points; see deviceScale. */
  step: number;
  /** Canvas pixels per point (the renderer resolution). */
  resolution: number;
  /** Canvas pixels per 32 px art pixel: deviceScale(step, resolution). May be fractional. */
  zoom: number;
}

export const chunkKey = (cx: number, cy: number) => `${cx},${cy}`;

export function chunkGrid(mapW: number, mapH: number, chunkTiles = CHUNK_TILES) {
  return { cols: Math.ceil(mapW / chunkTiles), rows: Math.ceil(mapH / chunkTiles) };
}

/** GPU bytes of one baked chunk: RGBA8 at `artScale` texels per art pixel. */
export const chunkBytes = (chunkTiles: number, artScale: number) =>
  (chunkTiles * TILE_PX * artScale) ** 2 * 4;

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
  chunkTiles = CHUNK_TILES,
): [number, number][] {
  if (!(v.zoom > 0)) throw new Error("zoom must be positive");
  const { cols, rows } = chunkGrid(mapW, mapH, chunkTiles);
  const CHUNK_PX = chunkTiles * TILE_PX;
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

/** Keep the camera inside the map and on whole canvas pixels. */
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

/** A view at a zoom step; zoom follows from the step and the resolution. */
export function makeView(x: number, y: number, w: number, h: number, step: number, resolution: number): View {
  return { x, y, w, h, step, resolution, zoom: deviceScale(step, resolution) };
}

/** Next zoom step, keeping the world point under (sx, sy) fixed on screen. */
export function stepZoom(v: View, dir: 1 | -1, sx = v.w / 2, sy = v.h / 2): View {
  const i = ZOOM_STEPS.indexOf(v.step as (typeof ZOOM_STEPS)[number]);
  const step = ZOOM_STEPS[Math.min(ZOOM_STEPS.length - 1, Math.max(0, i + dir))];
  if (step === v.step) return v;
  const next = deviceScale(step, v.resolution);
  const px = v.x + sx / v.zoom;
  const py = v.y + sy / v.zoom;
  return { ...v, step, zoom: next, x: px - sx / next, y: py - sy / next };
}
