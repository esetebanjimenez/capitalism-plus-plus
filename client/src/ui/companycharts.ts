/**
 * Company report Charts tab (#258, ux-spec section 3, view brief section 4): five one-series
 * charts from the corp's `month_history` (Past 12 months) or `year_history` (Past years).
 * The sim pushes a history entry when a month or year ends, so the last entry is the month
 * (or year) before the current one.
 */
import { ChartPoint, lineChart } from "./chart";

export const CHART_SERIES = [
  ["revenue", "Revenue"],
  ["operating_profit", "Operating profit"],
  ["other_profit", "Other profit"],
  ["expenses", "Expenses"],
  ["net_worth", "Net worth"],
] as const;

export type ChartRange = "months" | "years";
export const RANGE_NAMES: Record<ChartRange, string> = { months: "Past 12 months", years: "Past years" };

export interface Today {
  year: number;
  /** 1 to 12. */
  month: number;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** Labels for `n` complete months ending with the month before `today`: "Jan" .. "Dec". */
export function monthLabels(n: number, today: Today): string[] {
  const last = today.year * 12 + (today.month - 1) - 1; // month index of the last complete month
  return Array.from({ length: n }, (_, i) => MONTHS[(((last - (n - 1 - i)) % 12) + 12) % 12]);
}

/** Labels for `n` complete years ending with the year before `today`. */
export function yearLabels(n: number, today: Today): string[] {
  return Array.from({ length: n }, (_, i) => String(today.year - n + i));
}

export interface HistoryJson {
  month_history: Record<string, number[]>;
  year_history?: Record<string, number[]>;
}

/** The five charts' titles and points for one range. */
export function chartSeries(c: HistoryJson, range: ChartRange, today: Today): { key: string; title: string; points: ChartPoint[] }[] {
  const hist = (range === "months" ? c.month_history : c.year_history) ?? {};
  return CHART_SERIES.map(([key, title]) => {
    const values = hist[key] ?? [];
    const labels = range === "months" ? monthLabels(values.length, today) : yearLabels(values.length, today);
    return { key, title, points: values.map((value, i) => ({ label: labels[i], value })) };
  });
}

const h = <K extends keyof HTMLElementTagNameMap>(tag: K, cls = "", text = ""): HTMLElementTagNameMap[K] => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
};

/** The tab body: a Past 12 months / Past years switch and the five chart cards. */
export function chartsTab(c: HistoryJson, range: ChartRange, today: Today, width: number, onRange: (r: ChartRange) => void): HTMLElement {
  const box = h("div", "charts");
  const sw = h("div", "range");
  for (const r of ["months", "years"] as const) {
    const b = h("button", r === range ? "tab on" : "tab", RANGE_NAMES[r]);
    b.setAttribute("aria-pressed", String(r === range));
    b.onclick = () => onRange(r);
    sw.append(b);
  }
  box.append(sw);
  const series = chartSeries(c, range, today);
  if (series.every((s) => !s.points.length)) {
    box.append(h("div", "note", range === "months" ? "Charts start after your first complete month." : "Charts start after your first complete year."));
    return box;
  }
  for (const s of series) box.append(lineChart(s.points, { title: s.title, width, height: 170 }));
  return box;
}
