// @vitest-environment happy-dom
import { describe, expect, it } from "vitest";
import { goalRow, goalView, goalsScreen, goalsSummary, yearsWarning } from "../src/ui/goals";
import { DEMO_GOALS } from "../src/ui/goalsdemo";

describe("goals screen", () => {
  it("labels named, sector and industry goals with their values", () => {
    const v = DEMO_GOALS.goals.map(goalView);
    expect(v.map((x) => x.label)).toEqual([
      "Net worth",
      "Annual revenue",
      "Products made",
      "Share price",
      "Lead sector: Department stores",
      "Lead industry: Food",
    ]);
    expect(v[0].value).toBe("$62.4M of $50.0M");
    expect(v[2].value).toBe("3 of 3");
    expect(v[3].value).toBe("$18.25 of $40.00");
    expect(v[4].value).toBe("44.8% vs best rival 31.2%");
    expect(v.map((x) => x.screen)).toEqual(["company", "company", "products", "stocks", "company", "products"]);
    expect(v[0].fill).toBe(1);
    expect(v[1].fill).toBeCloseTo(7.3 / 20);
  });

  it("falls back to a numbered sector when the sim sends no name", () => {
    expect(goalView({ name: "sector_2", target: 10, current: 0, met: false }).label).toBe("Lead sector: sector 3");
  });

  it("renders met and unmet marks and bars", () => {
    const panel = goalsScreen(DEMO_GOALS, () => {});
    const rowsEl = Array.from(panel.body.querySelectorAll(".goal-row"));
    expect(rowsEl).toHaveLength(6);
    const marks = rowsEl.map((r) => (r.querySelector(".goal-mark")!.classList.contains("ui-icon_goal") ? "met" : "miss"));
    expect(marks).toEqual(["met", "miss", "met", "miss", "met", "miss"]);
    expect(rowsEl[0].querySelector(".goal-fill")!.className).toContain("ui-bar_fill_good");
    expect(rowsEl[1].querySelector(".goal-fill")!.classList.contains("ui-bar_fill")).toBe(true);
    expect(rowsEl.every((r) => r.querySelector(".ui-bar_track"))).toBe(true);
  });

  it("shows no limit, a plain difficulty and the score", () => {
    expect(goalsSummary(DEMO_GOALS)).toEqual([
      ["Years played", "3 (no limit)"],
      ["Difficulty", "18"],
      ["Score estimate", "1,240"],
    ]);
    expect(goalsSummary({ ...DEMO_GOALS, year_limit: 20 })[0][1]).toBe("3 of 20");
  });

  it("opens the screen that moves a tapped goal", () => {
    const seen: string[] = [];
    const row = goalRow(DEMO_GOALS.goals[3], (s) => seen.push(s));
    (row as HTMLButtonElement).click();
    expect(seen).toEqual(["stocks"]);
  });

  it("warns only when years are running out", () => {
    expect(yearsWarning(DEMO_GOALS)).toBeNull();
    expect(yearsWarning({ ...DEMO_GOALS, years_warning: 1 })).toBe("1 year left to meet your goals.");
    expect(yearsWarning({ ...DEMO_GOALS, years_warning: 3 })).toBe("3 years left to meet your goals.");
  });

  it("says so when the game has no goals", () => {
    const panel = goalsScreen({ ...DEMO_GOALS, goals: [], has_goals: false }, () => {});
    expect(panel.body.querySelector(".goal-none")?.textContent).toContain("no goals");
  });
});
