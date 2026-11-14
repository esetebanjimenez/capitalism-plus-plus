/**
 * Company report (docs/m2-ux-spec.md section 3): tabs Income, Balance, Loans, Charts and
 * Corporation. Only Income is filled in so far (#257); the rest show a placeholder.
 * Profit arrows follow view brief section 3: operating and other profit only.
 */
import { money } from "./layout";
import { PanelSpec } from "./shell";

/** A ledger from the `corp` query: cash plus the 12 categories for three periods. */
export interface LedgerJson {
  cash: number;
  month: number[];
  last_month: number[];
  year: number[];
}

/** The `corp` query result (docs/m2-facade-contract.md), the fields the report reads. */
export interface CorpJson {
  id: number;
  name: string;
  revenue: number;
  operating_expenses: number;
  operating_profit: number;
  other_profit: number;
  net_profit: number;
  ledger: LedgerJson;
  by_firm: { firm: number; ledger: LedgerJson }[];
  month_history: Record<string, number[]>;
}

/** Ledger category names, fixed by the ledger (ux-spec section 3). 0 is revenue, the rest are costs. */
export const CATEGORIES = [
  "Sales revenue",
  "Salaries",
  "Overhead",
  "Training",
  "Purchases",
  "Freight",
  "Advertising",
  "Write-offs",
  "Raw material",
  "Loan interest",
  "Stock return",
  "Land value",
] as const;

export const TABS = ["Income", "Balance", "Loans", "Charts", "Corporation"] as const;
export type Tab = (typeof TABS)[number];

export type Arrow = "up" | "down" | null;

/** Compare the last two entries: up when the latest is larger, down when smaller, else none. */
export function profitArrow(history: readonly number[] | undefined): Arrow {
  if (!history || history.length < 2) return null;
  const [a, b] = history.slice(-2);
  return b > a ? "up" : b < a ? "down" : null;
}

/** The fields that may carry an arrow; never revenue, expenses or firm rows. */
export const ARROW_FIELDS = ["operating_profit", "other_profit"] as const;

export interface SummaryRow {
  label: string;
  value: number;
  /** Green or red figure, by its own sign. Expenses are shown as a cost, not coloured. */
  tone: "plain" | "pos" | "neg";
  arrow: Arrow;
}

const tone = (v: number): SummaryRow["tone"] => (v > 0 ? "pos" : v < 0 ? "neg" : "plain");

/** The five Income figures with their colour and arrow. */
export function incomeSummary(c: CorpJson): SummaryRow[] {
  const arrow = (k: (typeof ARROW_FIELDS)[number]) => profitArrow(c.month_history[k]);
  return [
    { label: "Revenue", value: c.revenue, tone: "plain", arrow: null },
    { label: "Operating expenses", value: c.operating_expenses, tone: "plain", arrow: null },
    { label: "Operating profit", value: c.operating_profit, tone: tone(c.operating_profit), arrow: arrow("operating_profit") },
    { label: "Other profit", value: c.other_profit, tone: tone(c.other_profit), arrow: arrow("other_profit") },
    { label: "Net profit", value: c.net_profit, tone: tone(c.net_profit), arrow: null },
  ];
}

/** Plain dollars for tables: $1,234 or −$1.2M. */
export const dollars = (v: number) => money(v).replace(/^\+/, "");

export interface ReportState {
  tab: Tab;
  byFirm: boolean;
}

export interface ReportHooks {
  /** A firm's label for the By firm view, e.g. "Factory #3". */
  firmLabel: (id: number) => string;
  onFirm: (id: number) => void;
  /** Re-render with a new tab or toggle. */
  onState: (s: ReportState) => void;
}

const h = <K extends keyof HTMLElementTagNameMap>(tag: K, cls = "", text = ""): HTMLElementTagNameMap[K] => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
};

function categoryTable(l: LedgerJson, skipZero = false): HTMLElement {
  const t = h("table", "ledger");
  const head = h("tr");
  for (const c of ["", "This month", "Last month", "This year"]) head.append(h("th", "", c));
  t.append(head);
  CATEGORIES.forEach((name, i) => {
    const vals = [l.month[i] ?? 0, l.last_month[i] ?? 0, l.year[i] ?? 0];
    if (skipZero && vals.every((v) => v === 0)) return;
    const tr = h("tr");
    tr.append(h("td", "", name), ...vals.map((v) => h("td", "num", dollars(v))));
    t.append(tr);
  });
  return t;
}

function incomeTab(c: CorpJson, s: ReportState, hooks: ReportHooks): HTMLElement {
  const box = h("div", "income");
  const dl = h("dl", "rows income-sum");
  for (const r of incomeSummary(c)) {
    const dd = h("dd", `tone-${r.tone}`, dollars(r.value));
    if (r.arrow) {
      const a = h("span", `arrow ui-icon_arr_${r.arrow}`);
      a.title = r.arrow === "up" ? "Up on the month before" : "Down on the month before";
      a.dataset.arrow = r.arrow;
      dd.append(a);
    }
    dl.append(h("dt", "", r.label), dd);
  }
  const toggle = h("label", "toggle");
  const cb = h("input");
  cb.type = "checkbox";
  cb.checked = s.byFirm;
  cb.onchange = () => hooks.onState({ ...s, byFirm: cb.checked });
  toggle.append(cb, document.createTextNode(" By firm"));
  box.append(dl, toggle);
  if (!s.byFirm) {
    box.append(categoryTable(c.ledger));
  } else if (!c.by_firm.length) {
    box.append(h("div", "note", "You don't own any firms yet."));
  } else {
    for (const f of c.by_firm) {
      const head = h("button", "firm-row", hooks.firmLabel(f.firm));
      head.onclick = () => hooks.onFirm(f.firm);
      box.append(head, categoryTable(f.ledger, true));
    }
  }
  return box;
}

/** The report panel for corp `c` (the player's, corp 0). */
export function companyReport(c: CorpJson, s: ReportState, hooks: ReportHooks): PanelSpec {
  const tabs = h("div", "tabs");
  for (const t of TABS) {
    const b = h("button", t === s.tab ? "tab on" : "tab", t);
    b.onclick = () => hooks.onState({ ...s, tab: t });
    tabs.append(b);
  }
  const body = h("div", "company");
  body.append(tabs, s.tab === "Income" ? incomeTab(c, s, hooks) : h("div", "note coming", `${s.tab} is coming in a later update.`));
  return { key: "company", title: c.name, body, height: "full", heights: ["half", "full"] };
}
