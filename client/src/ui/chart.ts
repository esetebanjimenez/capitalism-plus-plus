/**
 * Line chart for the Company, Stock and Town views (#178, view brief section 4). One series per
 * chart, drawn live as SVG with style from art/charts.json; dots and the tip use ui_atlas frames
 * (.ui-chart_dot, .ui-chart_dot_sel, .ui-card_float), so call loadUiAtlas first.
 */
import style from "../../../art/charts.json";
import "./chart.css";

/** Palette names used by art/charts.json, from art/tools/ui_concept.py C. */
export const PALETTE: Record<string, string> = {
  INK: "#22262e",
  ORANGE: "#e8742a",
  GREEN: "#3aa05a",
  RED: "#c8402e",
  SAND: "#e8d6a0",
  MGREY: "#868a84",
};

export interface ChartPoint {
  label: string;
  value: number;
}

const MINUS = "\u2212";

/** Short money label: 950, 12.5k, 3.2M, 1.1B, with a minus sign for negatives. */
export function shortMoney(v: number): string {
  const sign = v < 0 ? MINUS : "";
  const a = Math.abs(v);
  const fmt = (x: number) => (Math.round(x * 10) / 10).toFixed(1).replace(/\.0$/, "");
  const units: [number, string][] = [
    [1, ""],
    [1e3, "k"],
    [1e6, "M"],
    [1e9, "B"],
  ];
  let i = 0;
  while (i < units.length - 1 && Math.round((a / units[i][0]) * 10) / 10 >= 1000) i++; // 999,960 -> 1M
  return sign + fmt(a / units[i][0]) + units[i][1];
}

/** True when the value range strictly crosses zero, so the ink zero line is drawn. */
export const crossesZero = (min: number, max: number) => min < 0 && max > 0;

/** Tip colour: green for 0 and up, red below 0. */
export const tipColour = (v: number) => (v >= 0 ? PALETTE.GREEN : PALETTE.RED);

/** Axis range with exactly `lines` evenly spaced round ticks (1, 2, 2.5 or 5 times a power of ten)
 * covering every value. A flat series is widened to include 0. */
export function axisRange(values: number[], lines = style.grid.lines): { min: number; max: number; ticks: number[] } {
  let lo = values.length ? Math.min(...values) : 0;
  let hi = values.length ? Math.max(...values) : 1;
  if (lo === hi) {
    lo = Math.min(0, lo);
    hi = Math.max(0, hi);
    if (lo === hi) hi = 1;
  }
  const intervals = Math.max(1, lines - 1);
  const raw = (hi - lo) / intervals;
  const mag = 10 ** Math.floor(Math.log10(raw));
  for (const m of [1, 2, 2.5, 5, 10, 20]) {
    const step = m * mag;
    const start = Math.floor(lo / step + 1e-9) * step;
    if (start + intervals * step >= hi - 1e-9 * step) {
      const ticks = Array.from({ length: intervals + 1 }, (_, k) => +(start + k * step).toPrecision(12));
      return { min: ticks[0], max: ticks[intervals], ticks };
    }
  }
  throw new Error("unreachable");
}

export interface ChartLayout {
  /** Plot area inside the card, in points. */
  plot: { x: number; y: number; w: number; h: number };
  ticks: { value: number; y: number; label: string; zero: boolean }[];
  points: { x: number; y: number; value: number; label: string }[];
  zeroY: number | null;
}

/** The card frame's border (ui_atlas card slice 6 + 6): the SVG sits inside it, so the card's
 * inner right edge is at x = w - CARD_BORDER. */
const CARD_BORDER = 12;
/** Half the widest x label ("1990" at 10 pt, about 22 pt wide) and the tapped dot's radius. */
const LABEL_HALF = 11;
const DOT_R = 5;
/** Right padding keeps the last dot and its x label inside the border, plus 4 pt (Artist, #341).
 * The same for every chart so the cards line up. */
const PAD = { left: 40, right: CARD_BORDER + Math.max(LABEL_HALF, DOT_R) + 4, top: 30, bottom: 28 };

/** Pure layout: where each tick, grid line and point goes in a w x h chart. */
export function chartLayout(series: ChartPoint[], w: number, h: number): ChartLayout {
  const plot = { x: PAD.left, y: PAD.top, w: w - PAD.left - PAD.right, h: h - PAD.top - PAD.bottom };
  const { min, max, ticks } = axisRange(series.map((p) => p.value));
  const yOf = (v: number) => plot.y + plot.h - ((v - min) / (max - min)) * plot.h;
  const n = series.length;
  const xOf = (i: number) => (n <= 1 ? plot.x + plot.w / 2 : plot.x + (i / (n - 1)) * plot.w);
  const zero = crossesZero(min, max);
  return {
    plot,
    ticks: ticks.map((v) => ({ value: v, y: yOf(v), label: shortMoney(v), zero: zero && v === 0 })),
    points: series.map((p, i) => ({ x: xOf(i), y: yOf(p.value), value: p.value, label: p.label })),
    zeroY: zero ? yOf(0) : null,
  };
}

/** Index of the point nearest to x (points), or -1 for an empty series. */
export function nearestPoint(layout: ChartLayout, x: number): number {
  let best = -1;
  let bestD = Infinity;
  layout.points.forEach((p, i) => {
    const d = Math.abs(p.x - x);
    if (d < bestD) {
      bestD = d;
      best = i;
    }
  });
  return best;
}

const SVG = "http://www.w3.org/2000/svg";
function svgEl(tag: string, attrs: Record<string, string | number>): SVGElement {
  const e = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  return e;
}

/** A chart card: title, grid, optional zero line, orange line, last-point dot, tap or hover tip. */
export function lineChart(series: ChartPoint[], opts: { title: string; width: number; height: number }): HTMLElement {
  const { width: w, height: h } = opts;
  const L = chartLayout(series, w, h);
  const card = document.createElement("div");
  card.className = "chart ui-card";
  card.style.width = `${w}px`;
  card.style.height = `${h}px`;
  const title = document.createElement("div");
  title.className = "chart-title";
  title.textContent = opts.title;
  card.append(title);

  const svg = svgEl("svg", { width: w, height: h, viewBox: `0 0 ${w} ${h}` });
  for (const t of L.ticks) {
    if (!t.zero)
      svg.append(svgEl("line", { x1: L.plot.x, x2: L.plot.x + L.plot.w, y1: t.y, y2: t.y, stroke: PALETTE[style.grid.colour], "stroke-width": style.grid.width }));
    const lab = svgEl("text", { x: L.plot.x - 6, y: t.y + 3.5, "text-anchor": "end", class: t.zero ? "chart-axis zero" : "chart-axis" });
    lab.textContent = t.label;
    svg.append(lab);
  }
  if (L.zeroY !== null)
    svg.append(svgEl("line", { x1: L.plot.x, x2: L.plot.x + L.plot.w, y1: L.zeroY, y2: L.zeroY, stroke: PALETTE[style.zero_line.colour], "stroke-width": style.zero_line.width }));
  // x labels: at most 12, evenly picked.
  const every = Math.max(1, Math.ceil(L.points.length / 12));
  L.points.forEach((p, i) => {
    if (i % every && i !== L.points.length - 1) return;
    const lab = svgEl("text", { x: p.x, y: L.plot.y + L.plot.h + 14, "text-anchor": "middle", class: "chart-axis" });
    lab.textContent = p.label;
    svg.append(lab);
  });
  if (L.points.length > 1)
    svg.append(
      svgEl("polyline", {
        points: L.points.map((p) => `${p.x},${p.y}`).join(" "),
        fill: "none",
        stroke: PALETTE[style.line.colour],
        "stroke-width": style.line.width,
        "stroke-linejoin": style.line.join,
        "stroke-linecap": "round",
      }),
    );
  card.append(svg);

  const dot = (cls: string, p: { x: number; y: number }) => {
    const d = document.createElement("div");
    d.className = `chart-dot ${cls}`;
    d.style.left = `${p.x}px`;
    d.style.top = `${p.y}px`;
    return d;
  };
  const last = L.points[L.points.length - 1];
  if (last) card.append(dot("ui-chart_dot", last));

  const sel = dot("ui-chart_dot_sel", { x: 0, y: 0 });
  const tip = document.createElement("div");
  tip.className = "chart-tip ui-card_float";
  sel.hidden = tip.hidden = true;
  card.append(sel, tip);
  const select = (i: number) => {
    const p = L.points[i];
    if (!p) return;
    sel.hidden = tip.hidden = false;
    sel.style.left = tip.style.left = `${p.x}px`;
    sel.style.top = `${p.y}px`;
    tip.style.top = `${p.y - style.tip.offset_above}px`;
    tip.style.color = tipColour(p.value);
    tip.textContent = shortMoney(p.value);
  };
  const at = (e: PointerEvent) => select(nearestPoint(L, e.clientX - card.getBoundingClientRect().left));
  card.addEventListener("pointermove", at);
  card.addEventListener("pointerdown", at);
  card.addEventListener("pointerleave", (e) => {
    if (e.pointerType === "mouse") sel.hidden = tip.hidden = true;
  });
  return card;
}
