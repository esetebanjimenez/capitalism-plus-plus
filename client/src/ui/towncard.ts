/**
 * Town card (#259, ux-spec "Town card"): the town name with its level badge, the eight city
 * indicators from the `town` query and the two 12-month growth charts (#280, #255). Peek shows
 * the indicators; half adds the charts. main.ts re-queries `town` while the card is open.
 */
import { ChartPoint, lineChart } from "./chart";
import { money } from "./layout";
import { PanelSpec, rows } from "./shell";

/** The `town` query result (src/capitalism/api.py `q_town`). */
export interface TownJson {
  id: number;
  name: string;
  level: number;
  population: number;
  gnp: number;
  per_capita_gnp: number;
  /** Percentage points. */
  unemployment: number;
  /** Indices, 100 = the simplified-city baseline (docs/rules.md). */
  labor_cost: number;
  labor_quality: number;
  consumer_spending: number;
  climate: number;
  pop_history: number[];
  gnp_level_history: number[];
  /** Month-on-month growth %, month order, last = the last complete month; null if unknown. */
  pop_growth_pct: (number | null)[];
  gnp_level_growth_pct: (number | null)[];
}

/** `Climate` in town.py: 0 Panic .. 4 Boom. */
export const CLIMATE_NAMES = ["Panic", "Recession", "Normal", "Prosperous", "Boom"];

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MINUS = "\u2212";

export interface Today {
  year: number;
  /** 1..12 */
  month: number;
}

/** Money without the "+" the Shared rules reserve for changes. */
const dollars = (v: number) => money(v).replace(/^\+/, "");

/** A level such as 2.0%: one decimal per the Shared rules. */
export const pct = (v: number) => `${v < 0 ? MINUS : ""}${Math.abs(v).toFixed(1)}%`;

/**
 * A growth change with its sign: +0.4%, \u22121.2%. Town growth is often a few hundredths of a
 * percent a month, which one decimal would show as 0.0%, so values under 0.1 keep two.
 */
export function growthPct(v: number): string {
  const a = Math.abs(v);
  const digits = a === 0 || a >= 0.095 ? 1 : 2;
  const s = a.toFixed(digits);
  if (Number(s) === 0) return `0${digits === 1 ? ".0" : ".00"}%`;
  return `${v < 0 ? MINUS : "+"}${s}%`;
}

/**
 * An axis tick for growth: every tick gets the fewest decimals (1 to 4) that show all of them
 * exactly, so a 0.025 step reads +0.025%, +0.050%, not +0.03%, +0.05%.
 */
export function growthTick(v: number, ticks: readonly number[]): string {
  let d = 1;
  while (d < 4 && ticks.some((t) => Math.abs(Math.round(t * 10 ** d) / 10 ** d - t) > 1e-9)) d++;
  const s = Math.abs(v).toFixed(d);
  if (Number(s) === 0) return `${(0).toFixed(d)}%`;
  return `${v < 0 ? MINUS : "+"}${s}%`;
}

/** The eight indicators in the reference's order, formatted per the Shared rules. */
export function townIndicators(t: TownJson): [string, string][] {
  return [
    ["Population", Math.round(t.population).toLocaleString("en-US")],
    ["GNP", dollars(t.gnp)],
    ["Per capita GNP", dollars(t.per_capita_gnp)],
    ["Unemployment", pct(t.unemployment)],
    ["Labor cost", t.labor_cost.toFixed(1)],
    ["Labor quality", t.labor_quality.toFixed(1)],
    ["Consumer spending", t.consumer_spending.toFixed(1)],
    ["Economic climate", CLIMATE_NAMES[t.climate] ?? "Unknown"],
  ];
}

/**
 * Chart points for a growth array: the last value belongs to the month before `today`, the one
 * before it to the month before that, and so on. Months with no value (null) are left out.
 */
export function growthSeries(values: readonly (number | null)[], today: Today): ChartPoint[] {
  const last = today.year * 12 + (today.month - 1) - 1;
  const out: ChartPoint[] = [];
  values.forEach((v, i) => {
    if (v === null || !Number.isFinite(v)) return;
    const m = last - (values.length - 1 - i);
    out.push({ label: MONTHS[((m % 12) + 12) % 12], value: v });
  });
  return out;
}

const div = (cls: string, ...kids: (Node | string)[]) => {
  const d = document.createElement("div");
  d.className = cls;
  d.append(...kids);
  return d;
};

/** The full town card. `chartWidth` is the chart card width in points. */
export function townCard(t: TownJson, today: Today, chartWidth: number): PanelSpec {
  const charts: HTMLElement[] = [];
  const pop = growthSeries(t.pop_growth_pct, today);
  const gnp = growthSeries(t.gnp_level_growth_pct, today);
  if (!pop.length && !gnp.length) charts.push(div("note", "Growth charts start after the town's second month."));
  else
    for (const [title, s] of [
      ["Population growth", pop],
      ["Per capita GNP growth", gnp],
    ] as const)
      if (s.length) charts.push(lineChart(s, { title, width: chartWidth, height: 170, format: growthPct, tickFormat: growthTick }));
  return {
    key: `town:${t.id}`,
    title: t.name,
    badge: String(Math.max(1, Math.floor(t.level))),
    body: div("card-body town-card", rows(townIndicators(t)), div("town-charts", ...charts)),
    height: "peek",
    heights: ["peek", "half"],
  };
}
