/**
 * News feed (#254, ux-spec section 4, view brief section 3 "News categories"): the `news` query
 * newest first, each row with its date, category icon, corporation and headline. Important
 * items are bold rows (no icon of their own). Filters by corporation, category and time are
 * chips on phones and three columns on desktop.
 */
import { PanelSpec } from "./shell";

/** One row of the `news` query (docs/m2-facade-contract.md). */
export interface NewsItem {
  day_serial: number;
  category: number;
  category_name?: string;
  corp_id: number | null;
  corp_name: string | null;
  news_type: number;
  important: boolean;
  headline: string;
  /** Jump ids, null when the item names none or it is gone. */
  corp: number | null;
  firm: number | null;
  product: number | null;
}

/** NewsCategory in news.py: Normal, Financial, Technology, Special. */
export const CATEGORY_NAMES = ["Normal", "Financial", "Technology", "Special"] as const;
export const CATEGORY_ICONS = ["icon_nws_normal", "icon_nws_financial", "icon_nws_tech", "icon_nws_special"] as const;

export type NewsTime = "month" | "year" | "all";
export interface NewsFilter {
  corp: number | null;
  category: number | null;
  time: NewsTime;
}
export const ALL_NEWS: NewsFilter = { corp: null, category: null, time: "all" };

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const EPOCH_MS = Date.UTC(1900, 0, 1);

/** The calendar date of a day serial (days since 1 Jan 1900, calendar.py). */
export function serialDate(serial: number): { year: number; month: number; day: number } {
  const d = new Date(EPOCH_MS + serial * 86_400_000);
  return { year: d.getUTCFullYear(), month: d.getUTCMonth() + 1, day: d.getUTCDate() };
}

/** "12 Mar 1991"; the shown day is capped at 30 like the status pill (Calendar.day). */
export function newsDate(serial: number): string {
  const d = serialDate(serial);
  return `${Math.min(d.day, 30)} ${MONTHS[d.month - 1]} ${d.year}`;
}

/** Items that pass the filter; `today` is the game date for the time filter. */
export function filterNews(items: readonly NewsItem[], f: NewsFilter, today: { year: number; month: number }): NewsItem[] {
  return items.filter((n) => {
    if (f.corp !== null && n.corp_id !== f.corp) return false;
    if (f.category !== null && n.category !== f.category) return false;
    if (f.time === "all") return true;
    const d = serialDate(n.day_serial);
    return d.year === today.year && (f.time === "year" || d.month === today.month);
  });
}

/** The badge: important items newer than the read mark (Api.status `unread_important`). */
export const unreadImportant = (items: readonly NewsItem[], readSince: number) =>
  items.filter((n) => n.important && n.day_serial > readSince).length;

/** The corporations named in the feed, for the corporation filter (-1 is "no corporation"). */
export function newsCorps(items: readonly NewsItem[]): { id: number; name: string }[] {
  const seen = new Map<number, string>();
  for (const n of items) if (n.corp_id !== null && n.corp_id >= 0 && !seen.has(n.corp_id)) seen.set(n.corp_id, n.corp_name ?? `Corporation ${n.corp_id}`);
  return [...seen].map(([id, name]) => ({ id, name })).sort((a, b) => a.id - b.id);
}

const el = <K extends keyof HTMLElementTagNameMap>(tag: K, cls = "", text = ""): HTMLElementTagNameMap[K] => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
};

export function newsRow(n: NewsItem, onItem: (n: NewsItem) => void): HTMLButtonElement {
  const b = el("button", `news-row${n.important ? " important" : ""}`);
  b.dataset.category = String(n.category);
  const icon = el("span", `news-icon ui-${CATEGORY_ICONS[n.category] ?? CATEGORY_ICONS[0]}`);
  icon.setAttribute("aria-label", CATEGORY_NAMES[n.category] ?? "News");
  icon.setAttribute("role", "img");
  const text = el("span", "news-text");
  text.append(el("span", "news-headline", n.headline), el("span", "news-meta", [newsDate(n.day_serial), n.corp_name].filter(Boolean).join(" \u00b7 ")));
  b.append(icon, text);
  b.onclick = () => onItem(n);
  return b;
}

export interface NewsHooks {
  today: { year: number; month: number };
  onState: (f: NewsFilter) => void;
  onItem: (n: NewsItem) => void;
}

function filterGroup<T>(label: string, options: [string, T][], current: T, pick: (v: T) => void): HTMLElement {
  const g = el("div", "news-filter");
  g.append(el("span", "news-filter-label", label));
  const chips = el("div", "chips");
  for (const [name, v] of options) {
    const on = v === current;
    const c = el("button", `chip ${on ? "on ui-chip_on" : "ui-chip_off"}`, name);
    c.setAttribute("aria-pressed", String(on));
    c.onclick = () => pick(v);
    chips.append(c);
  }
  g.append(chips);
  return g;
}

/** The News report: filters, then the matching items newest first. */
export function newsReport(items: readonly NewsItem[], f: NewsFilter, hooks: NewsHooks): PanelSpec {
  const body = el("div", "card-body news");
  const filters = el("div", "news-filters");
  filters.append(
    filterGroup<number | null>("Corporation", [["All", null], ...newsCorps(items).map((c) => [c.name, c.id] as [string, number])], f.corp, (corp) =>
      hooks.onState({ ...f, corp }),
    ),
    filterGroup<number | null>("Category", [["All", null], ...CATEGORY_NAMES.map((n, i) => [n, i] as [string, number])], f.category, (category) =>
      hooks.onState({ ...f, category }),
    ),
    filterGroup<NewsTime>("Time", [["This month", "month"], ["This year", "year"], ["All", "all"]], f.time, (time) => hooks.onState({ ...f, time })),
  );
  const shown = filterNews(items, f, hooks.today);
  const list = el("div", "news-list");
  for (const n of shown) list.append(newsRow(n, hooks.onItem));
  if (!shown.length) list.append(el("div", "sub news-empty", items.length ? "No news matches these filters." : "No news yet."));
  body.append(filters, list);
  return { key: "news", title: "News", body, height: "full", heights: ["half", "full"] };
}
