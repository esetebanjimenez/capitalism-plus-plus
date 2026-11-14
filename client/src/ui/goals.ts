/**
 * Goals screen (#262, docs/m2-ux-spec.md section 6): one row per goal from the `goals` query
 * with its label, target, current value, a progress bar and the met tick (`icon_goal`) or
 * miss mark (`icon_goal_miss`), then years played, the difficulty rating and the score
 * estimate. `goalRow` is shared with the win/loss card (#263).
 */
import { money } from "./layout";
import { PanelSpec, rows } from "./shell";

/** One row of the `goals` query; `label` names the sector or product class of a dominance goal. */
export interface GoalRowJson {
  name: string;
  target: number;
  current: number;
  met: boolean;
  label?: string | null;
}

/** The `goals` query result (docs/m2-facade-contract.md), the fields the screen reads. */
export interface GoalsJson {
  result: number;
  result_name: string;
  goals: GoalRowJson[];
  years_played: number;
  year_limit: number;
  difficulty: number;
  score: number;
  years_warning: number;
  cheated: boolean;
  has_goals: boolean;
}

/** Which screen moves a goal (ux-spec section 6). Products open Company until its product list lands. */
export type GoalScreen = "company" | "stocks" | "products";

type Unit = "millions" | "dollars" | "price" | "count" | "pct" | "share";

/** Labels, units (goals.py `_get_player_values`) and target screens for the 17 named goals. */
export const GOALS: Record<string, { label: string; unit: Unit; screen: GoalScreen }> = {
  personal_wealth: { label: "Personal wealth", unit: "dollars", screen: "company" },
  corp_net_worth: { label: "Net worth", unit: "millions", screen: "company" },
  corp_market_value: { label: "Market value", unit: "millions", screen: "stocks" },
  corp_annual_revenue: { label: "Annual revenue", unit: "millions", screen: "company" },
  corp_annual_op_profit: { label: "Annual operating profit", unit: "millions", screen: "company" },
  controlled_net_worth: { label: "Net worth of companies you control", unit: "millions", screen: "company" },
  controlled_market_value: { label: "Market value of companies you control", unit: "millions", screen: "stocks" },
  controlled_annual_revenue: { label: "Revenue of companies you control", unit: "millions", screen: "company" },
  controlled_annual_op_profit: { label: "Operating profit of companies you control", unit: "millions", screen: "company" },
  num_companies_controlled: { label: "Companies controlled", unit: "count", screen: "stocks" },
  num_employees: { label: "Employees", unit: "count", screen: "company" },
  op_profit_margin: { label: "Operating profit margin", unit: "pct", screen: "company" },
  return_on_equity: { label: "Return on equity", unit: "pct", screen: "company" },
  stock_price: { label: "Share price", unit: "price", screen: "stocks" },
  ownership_pct: { label: "Your ownership", unit: "pct", screen: "stocks" },
  num_product_classes: { label: "Product classes made", unit: "count", screen: "products" },
  num_product_types: { label: "Products made", unit: "count", screen: "products" },
};

const el = <K extends keyof HTMLElementTagNameMap>(tag: K, cls = "", text = ""): HTMLElementTagNameMap[K] => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
};

const plain = (v: number) => money(v).replace(/^\+/, "");

function fmt(v: number, unit: Unit): string {
  switch (unit) {
    case "millions":
      return plain(v * 1e6);
    case "dollars":
      return plain(v);
    case "price":
      return `${v < 0 ? "\u2212" : ""}$${Math.abs(v).toFixed(2)}`;
    case "count":
      return Math.round(v).toLocaleString("en-US");
    case "pct":
    case "share":
      return `${v.toFixed(1)}%`;
  }
}

/** What a row shows: label, "current of target" text and the bar's fill fraction (0..1). */
export function goalView(g: GoalRowJson): { label: string; value: string; fill: number; screen: GoalScreen } {
  const dom = /^(sector|industry)_(\d+)$/.exec(g.name);
  if (dom) {
    // Dominance: lead the sector or product class. Target is the best rival's share.
    const what = g.label ?? `${dom[1] === "sector" ? "sector" : "industry"} ${Number(dom[2]) + 1}`;
    const fill = g.met ? 1 : g.target > 0 ? Math.min(1, g.current / g.target) : 0;
    return {
      label: `Lead ${dom[1] === "sector" ? "sector" : "industry"}: ${what}`,
      value: `${fmt(g.current, "share")} vs best rival ${fmt(g.target, "share")}`,
      fill,
      screen: dom[1] === "sector" ? "company" : "products",
    };
  }
  const def = GOALS[g.name] ?? { label: g.name.replace(/_/g, " "), unit: "count" as Unit, screen: "company" as GoalScreen };
  const fill = g.met ? 1 : g.target > 0 ? Math.max(0, Math.min(1, g.current / g.target)) : 0;
  return { label: def.label, value: `${fmt(g.current, def.unit)} of ${fmt(g.target, def.unit)}`, fill, screen: def.screen };
}

/** One goal row: mark, label, value text and progress bar. Shared with the win/loss card. */
export function goalRow(g: GoalRowJson, onTap?: (screen: GoalScreen) => void): HTMLElement {
  const v = goalView(g);
  const row = el(onTap ? "button" : "div", `goal-row${g.met ? " met" : ""}`);
  row.dataset.goal = g.name;
  const mark = el("span", `goal-mark ${g.met ? "ui-icon_goal" : "ui-icon_goal_miss"}`);
  mark.setAttribute("aria-label", g.met ? "Met" : "Not met");
  const text = el("span", "goal-text");
  text.append(el("span", "goal-label", v.label), el("span", "goal-value", v.value));
  const bar = el("span", "goal-bar");
  const fill = el("span", `goal-fill ${g.met ? "ui-bar_fill_good" : "ui-bar_fill"}`);
  fill.style.width = `${Math.round(v.fill * 100)}%`;
  if (v.fill <= 0) fill.hidden = true;
  bar.append(el("span", "goal-track ui-bar_track"), fill);
  row.append(mark, text, bar);
  if (onTap) (row as HTMLButtonElement).onclick = () => onTap(v.screen);
  return row;
}

/** Years played against the limit, the difficulty rating and the score estimate. */
export function goalsSummary(g: GoalsJson): [string, string][] {
  return [
    ["Years played", g.year_limit > 0 ? `${g.years_played} of ${g.year_limit}` : `${g.years_played} (no limit)`],
    ["Difficulty", String(g.difficulty)],
    ["Score estimate", g.cheated ? "0 (cheats used)" : g.score.toLocaleString("en-US")],
  ];
}

/** The toast for `years_warning` at year end, or null when there is none. */
export function yearsWarning(g: GoalsJson): string | null {
  const n = g.years_warning;
  if (n <= 0 || !g.has_goals) return null;
  return `${n} year${n === 1 ? "" : "s"} left to meet your goals.`;
}

export function goalsScreen(g: GoalsJson, onTap: (screen: GoalScreen) => void): PanelSpec {
  const body = el("div", "card-body goals");
  if (g.goals.length) {
    const list = el("div", "goal-list");
    for (const row of g.goals) list.append(goalRow(row, onTap));
    body.append(list);
  } else {
    body.append(el("p", "goal-none", "This game has no goals. Play as long as you like."));
  }
  body.append(rows(goalsSummary(g)));
  return { key: "goals", title: "Goals", body, height: "full", heights: ["half", "full"] };
}
