/** ?end=win|time|rival|bankrupt: the win/loss card with fixed example data, for review (#263). */
import { loadUiAtlas } from "./atlas";
import { endCard, EndKind } from "./endcard";
import { GoalsJson } from "./goals";
import { DEMO_GOALS } from "./goalsdemo";

const RESULT: Record<EndKind, number> = { win: 1, time: 2, rival: 3, bankrupt: 4 };

export function demoEnd(kind: EndKind): GoalsJson {
  const result = RESULT[kind];
  const goals = DEMO_GOALS.goals.map((g) => (kind === "win" ? { ...g, met: true, current: g.met ? g.current : Math.round(g.target * 110) / 100 } : g));
  if (kind === "bankrupt") return { ...DEMO_GOALS, result, result_name: "DEFEAT_BANKRUPT", goals: [], has_goals: false, years_played: 12, difficulty: 120 };
  return {
    ...DEMO_GOALS,
    result,
    result_name: ["", "VICTORY", "DEFEAT_DEADLINE", "DEFEAT_AI_WON"][result],
    goals,
    years_played: kind === "time" ? 20 : 12,
    year_limit: kind === "time" ? 20 : 0,
    difficulty: 120,
    score: { win: 8420, time: 3115, rival: 4960 }[kind],
  };
}

export async function showEndDemo(resolution: number, kind: EndKind): Promise<void> {
  await loadUiAtlas(resolution);
  document.body.style.background = "#9fbf8a";
  document.body.append(endCard(demoEnd(kind), () => (document.title = "new game")));
}
