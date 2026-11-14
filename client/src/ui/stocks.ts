/**
 * Stock market (#260, docs/m2-ux-spec.md section 5, view brief section 4): the list of every
 * corporation from `stocks`, and one corporation's page from `stock` with a share price chart
 * (Day, Month and Year tabs), the share facts and the shareholder list. Trading is #26.
 */
import { lineChart } from "./chart";
import { monthLabels, Today, yearLabels } from "./companycharts";
import { serialDate } from "./news";
import { PanelSpec, button, rows } from "./shell";

/** One row of the `stocks` query (docs/m2-facade-contract.md). */
export interface StockRowJson {
  corp: number;
  name: string;
  price: number;
  pe_ratio: number | null;
  owned_pct: number;
  holding_value: number;
}

export interface ShareholderJson {
  kind: "corp" | "person";
  id: number;
  name: string;
  shares: number;
  pct: number;
  value: number;
}

/** The `stock` query result. */
export interface StockJson {
  corp: number;
  price: number;
  pe_ratio: number | null;
  daily_prices: number[];
  monthly_prices: number[];
  yearly_prices: number[];
  total_shares: number;
  public_float: number;
  /** A fraction (0.024 is 2.4%). */
  dividend_yield: number | null;
  shareholders: ShareholderJson[];
}

export type PriceRange = "day" | "month" | "year";
export const PRICE_RANGES: Record<PriceRange, string> = { day: "Day", month: "Month", year: "Year" };

const h = <K extends keyof HTMLElementTagNameMap>(tag: K, cls = "", text = ""): HTMLElementTagNameMap[K] => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
};

/** Share price with cents: "$18.25". */
export const sharePrice = (v: number) => `${v < 0 ? "\u2212" : ""}$${Math.abs(v).toFixed(2)}`;
/** Whole dollars without a sign: "$1,250,000". */
export const value = (v: number) => `$${Math.round(v).toLocaleString("en-US")}`;
export const count = (v: number) => Math.round(v).toLocaleString("en-US");
/** The sim returns 0 when earnings per share are not positive (stock.py pe_ratio), so 0 reads n/a too. */
export const pe = (v: number | null) => (v === null || v <= 0 ? "n/a" : v.toFixed(1));
const pct = (v: number) => `${v.toFixed(1)}%`;

export interface StockToday extends Today {
  /** Day serial of today (days since 1 Jan 1900); the daily series ends today. */
  day_serial: number;
}

/**
 * Chart points for one range. Daily prices are recorded each day up to and including today
 * (the last 30); monthly averages at each month end (last 30 months); yearly at each year end.
 */
export function priceSeries(s: StockJson, range: PriceRange, today: StockToday): { label: string; value: number }[] {
  if (range === "day") {
    const n = s.daily_prices.length;
    return s.daily_prices.map((v, i) => {
      const d = serialDate(today.day_serial - (n - 1 - i));
      return { label: String(Math.min(d.day, 30)), value: v };
    });
  }
  const values = range === "month" ? s.monthly_prices : s.yearly_prices;
  const labels = range === "month" ? monthLabels(values.length, today) : yearLabels(values.length, today);
  return values.map((v, i) => ({ label: labels[i], value: v }));
}

/** The Stocks list: every corporation with price, P/E, owned % and holding value. */
export function stocksList(list: StockRowJson[], onCorp: (corp: number) => void): PanelSpec {
  const body = h("div", "card-body stocks");
  const t = h("table", "stock-table");
  const head = h("tr");
  for (const c of ["Corporation", "Price", "P/E", "Owned", "Holding"]) head.append(h("th", "", c));
  t.append(head);
  for (const r of list) {
    const tr = h("tr", "stock-row");
    tr.dataset.corp = String(r.corp);
    tr.tabIndex = 0;
    tr.onclick = () => onCorp(r.corp);
    tr.onkeydown = (e) => e.key === "Enter" && onCorp(r.corp);
    tr.append(
      h("td", "corp-name", r.name),
      h("td", "num", sharePrice(r.price)),
      h("td", "num", pe(r.pe_ratio)),
      h("td", "num", pct(r.owned_pct)),
      h("td", "num", value(r.holding_value)),
    );
    t.append(tr);
  }
  body.append(t);
  return { key: "stocks", title: "Stocks", body, height: "full", heights: ["half", "full"] };
}

export interface StockPageHooks {
  range: PriceRange;
  today: StockToday;
  chartWidth: number;
  onRange: (r: PriceRange) => void;
  /** Back to the list. */
  onList: () => void;
  /** The corporation's Income and Charts: read-only for a rival, the Company report for yours. */
  onReport: (tab: "Income" | "Charts") => void;
}

/** One corporation's page. */
export function stockPage(name: string, s: StockJson, hooks: StockPageHooks): PanelSpec {
  const body = h("div", "card-body stock-page");
  const sw = h("div", "range");
  for (const r of ["day", "month", "year"] as const) {
    const b = h("button", r === hooks.range ? "tab on" : "tab", PRICE_RANGES[r]);
    b.setAttribute("aria-pressed", String(r === hooks.range));
    b.onclick = () => hooks.onRange(r);
    sw.append(b);
  }
  body.append(sw);
  const points = priceSeries(s, hooks.range, hooks.today);
  if (points.length) body.append(lineChart(points, { title: "Share price", width: hooks.chartWidth, height: 170, format: sharePrice }));
  else body.append(h("div", "note", hooks.range === "month" ? "Monthly prices start after the first month." : "Yearly prices start after the first year."));
  body.append(
    rows([
      ["Share price", sharePrice(s.price)],
      ["Shares outstanding", count(s.total_shares)],
      ["Public float", count(s.public_float)],
      ["Dividend yield", s.dividend_yield === null ? "n/a" : pct(s.dividend_yield * 100)],
      ["P/E", pe(s.pe_ratio)],
    ]),
  );
  body.append(h("div", "stock-head", "Shareholders"));
  if (!s.shareholders.length) body.append(h("div", "note", "No shareholders."));
  else {
    const t = h("table", "stock-table holders");
    const head = h("tr");
    for (const c of ["Holder", "Shares", "%", "Value"]) head.append(h("th", "", c));
    t.append(head);
    for (const x of [...s.shareholders].sort((a, b) => b.shares - a.shares)) {
      const tr = h("tr");
      tr.append(h("td", "corp-name", x.name || (x.kind === "person" ? `Investor ${x.id + 1}` : `Corporation ${x.id + 1}`)), h("td", "num", count(x.shares)), h("td", "num", pct(x.pct)), h("td", "num", value(x.value)));
      t.append(tr);
    }
    body.append(t);
  }
  const actions = [button("Income", "secondary", () => hooks.onReport("Income")), button("Charts", "secondary", () => hooks.onReport("Charts")), button("All stocks", "secondary", hooks.onList)];
  return { key: `stock:${s.corp}`, title: name, body, actions, height: "full", heights: ["half", "full"] };
}
