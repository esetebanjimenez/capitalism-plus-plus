/**
 * ?goals=demo: the Goals screen with fixed example data, for PR screenshots and tests (#262):
 * met and unmet goals, a sector goal, a product-class goal and no year limit.
 */
import { loadUiAtlas } from "./atlas";
import { GoalsJson, goalsScreen } from "./goals";
import { Shell } from "./shell";

export const DEMO_GOALS: GoalsJson = {
  result: 0,
  result_name: "IN_PROGRESS",
  goals: [
    { name: "corp_net_worth", target: 50, current: 62.4, met: true },
    { name: "corp_annual_revenue", target: 20, current: 7.3, met: false },
    { name: "num_product_types", target: 3, current: 3, met: true },
    { name: "stock_price", target: 40, current: 18.25, met: false },
    { name: "sector_0", target: 31.2, current: 44.8, met: true, label: "Department stores" },
    { name: "industry_6", target: 52.0, current: 21.5, met: false, label: "Food" },
  ],
  years_played: 3,
  year_limit: 0,
  difficulty: 18,
  score: 1240,
  years_warning: 0,
  cheated: false,
  has_goals: true,
};

export async function showGoalsDemo(resolution: number): Promise<void> {
  await loadUiAtlas(resolution);
  document.body.style.background = "#9fbf8a";
  const shell = new Shell(document.body);
  shell.open(goalsScreen(DEMO_GOALS, (screen) => shell.toast(`Opens ${screen}.`)));
}
