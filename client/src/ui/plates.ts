/**
 * Town-name plates (#250, view brief section 2, art/README "Town plate (#175)"): a DOM layer
 * over the canvas with one `card` plate per town showing its name and level. Plates sit above
 * the map and below panels and toasts; a plate outside the part of the map a panel leaves
 * visible is hidden. Plates don't take taps (Esteban, PR #336): a tap goes to the tile
 * underneath, a long press or right click on a plate opens its town card (`townAt`), and a
 * plate goes see-through while the tile under it is selected. While its town card is open the
 * plate stays opaque and is drawn highlighted.
 */
import { TILE_PX, View } from "../chunkmath";
import { TownInfo } from "../mapdata";

/** Plate size in CSS px (points): 136 x 24, fits 12 characters at 12 pt bold. */
export const PLATE_W = 136;
export const PLATE_H = 24;
/** How long the level-up ring shows. */
export const PULSE_MS = 1500;

/** The badge text: the level as a plain number, so 7, 10 or 123 need no new art. */
export const levelText = (level: number) => String(Math.max(1, Math.floor(level)));

/** Badge width in points: the 12 pt `plate_level` nine-slice stretched for its digits. */
export const badgeWidth = (level: number) => Math.max(16, 8 + 7 * levelText(level).length);

/** Town ids whose level went up between two reads (none on the first read). */
export function levelUps(prev: ReadonlyMap<number, number>, towns: readonly TownInfo[]): number[] {
  return towns.filter((t) => prev.has(t.id) && t.level > prev.get(t.id)!).map((t) => t.id);
}

/** Where a town's plate goes, in CSS px: centred on the town tile, just above its middle. */
export function plateRect(t: TownInfo, view: View, resolution: number) {
  const s = view.zoom / resolution;
  const cx = ((t.x + 0.5) * TILE_PX - view.x) * s;
  const cy = ((t.y + 0.5) * TILE_PX - view.y) * s;
  return { x: Math.round(cx - PLATE_W / 2), y: Math.round(cy - PLATE_H - 4), w: PLATE_W, h: PLATE_H };
}

type Rect = { x: number; y: number; w: number; h: number };
const inside = (r: Rect, area: Rect) =>
  r.x >= area.x && r.y >= area.y && r.x + r.w <= area.x + area.w && r.y + r.h <= area.y + area.h;
const overlaps = (a: Rect, b: Rect) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;

/** A tile's square on screen, in CSS px. */
export function tileRect(x: number, y: number, view: View, resolution: number): Rect {
  const s = view.zoom / resolution;
  return { x: (x * TILE_PX - view.x) * s, y: (y * TILE_PX - view.y) * s, w: TILE_PX * s, h: TILE_PX * s };
}

export class TownPlates {
  readonly layer = document.createElement("div");
  private plates = new Map<number, { el: HTMLDivElement; name: HTMLSpanElement; badge: HTMLSpanElement }>();
  private levels = new Map<number, number>();
  private towns: TownInfo[] = [];
  /** Where each shown plate is on screen, for `townAt`. */
  private shown = new Map<number, Rect>();
  /** The selected tile; plates over it go see-through. */
  selected: { x: number; y: number } | null = null;
  /** The town whose card is open; its plate is highlighted and never faded. */
  highlight: number | null = null;

  constructor() {
    this.layer.className = "plates";
  }

  /** New towns or levels from a map read; a level that went up pulses once. */
  setTowns(towns: TownInfo[]): number[] {
    const ups = levelUps(this.levels, towns);
    this.towns = towns;
    const seen = new Set<number>();
    for (const t of towns) {
      seen.add(t.id);
      let p = this.plates.get(t.id);
      if (!p) {
        const el = document.createElement("div");
        el.className = "plate ui-card";
        const name = document.createElement("span");
        name.className = "plate-name";
        const badge = document.createElement("span");
        badge.className = "plate-level ui-plate_level";
        el.append(name, badge);
        this.layer.append(el);
        p = { el, name, badge };
        this.plates.set(t.id, p);
      }
      p.name.textContent = t.name;
      p.badge.textContent = levelText(t.level);
      p.badge.style.minWidth = `${badgeWidth(t.level)}px`;
      p.el.setAttribute("aria-label", `${t.name}, level ${levelText(t.level)}`);
      this.levels.set(t.id, t.level);
    }
    for (const [id, p] of this.plates) {
      if (!seen.has(id)) (p.el.remove(), this.plates.delete(id), this.levels.delete(id));
    }
    for (const id of ups) this.pulse(id);
    return ups;
  }

  private pulse(id: number): void {
    const el = this.plates.get(id)?.el;
    if (!el) return;
    el.classList.remove("pulse");
    const ring = document.createElement("span");
    ring.className = "plate-pulse ui-plate_pulse";
    el.append(ring);
    el.classList.add("pulse");
    setTimeout(() => (ring.remove(), el.classList.remove("pulse")), PULSE_MS);
  }

  /** Position plates for the view; hide those outside `area` (the map a panel leaves). */
  update(view: View, resolution: number, area: Rect): void {
    this.shown.clear();
    const sel = this.selected && tileRect(this.selected.x, this.selected.y, view, resolution);
    for (const t of this.towns) {
      const p = this.plates.get(t.id);
      if (!p) continue;
      const r = plateRect(t, view, resolution);
      const show = inside(r, area);
      p.el.hidden = !show;
      if (!show) continue;
      this.shown.set(t.id, r);
      p.el.style.transform = `translate(${r.x}px, ${r.y}px)`;
      const hl = t.id === this.highlight;
      p.el.classList.toggle("hl", hl);
      p.el.classList.toggle("dim", !hl && Boolean(sel && overlaps(sel, r)));
    }
  }

  /** The town whose shown plate is under a screen point (the top one if plates overlap). */
  townAt(cx: number, cy: number): TownInfo | null {
    for (let i = this.towns.length - 1; i >= 0; i--) {
      const r = this.shown.get(this.towns[i].id);
      if (r && cx >= r.x && cx < r.x + r.w && cy >= r.y && cy < r.y + r.h) return this.towns[i];
    }
    return null;
  }
}
