import { describe, expect, it } from "vitest";
import ui from "../../art/atlas/ui_atlas.json";
import { ARROW_FIELDS, CATEGORIES, CorpJson, TABS, incomeSummary, profitArrow } from "../src/ui/company";

const corp = (history: Record<string, number[]>, over: Partial<CorpJson> = {}): CorpJson => ({
  id: 0,
  name: "You Corp",
  revenue: 500,
  operating_expenses: 700,
  operating_profit: -200,
  other_profit: 30,
  net_profit: -170,
  ledger: { cash: 0, month: Array(12).fill(0), last_month: Array(12).fill(0), year: Array(12).fill(0) },
  by_firm: [],
  month_history: history,
  ...over,
});

describe("profit arrows (view brief section 3)", () => {
  it("points up, down or nowhere from the last two months", () => {
    expect(profitArrow([1, 5, 9])).toBe("up");
    expect(profitArrow([9, 4])).toBe("down");
    expect(profitArrow([3, 3])).toBeNull();
  });
  it("shows nothing with fewer than two months", () => {
    expect(profitArrow([])).toBeNull();
    expect(profitArrow([42])).toBeNull();
    expect(profitArrow(undefined)).toBeNull();
  });
  it("a shrinking loss is a red figure with a green up arrow", () => {
    const row = incomeSummary(corp({ operating_profit: [-500, -200] })).find((r) => r.label === "Operating profit")!;
    expect(row.tone).toBe("neg");
    expect(row.arrow).toBe("up");
  });
  it("never puts an arrow on revenue, expenses or net profit", () => {
    const up = [1, 2];
    const rows = incomeSummary(corp({ revenue: up, expenses: up, operating_profit: up, other_profit: [5, 1], net_worth: up }));
    const arrows = Object.fromEntries(rows.map((r) => [r.label, r.arrow]));
    expect(arrows).toEqual({
      Revenue: null,
      "Operating expenses": null,
      "Operating profit": "up",
      "Other profit": "down",
      "Net profit": null,
    });
    expect(ARROW_FIELDS).toEqual(["operating_profit", "other_profit"]);
  });
});

describe("report layout", () => {
  it("has the five tabs and the twelve ledger categories from ux-spec section 3", () => {
    expect(TABS).toEqual(["Income", "Balance", "Loans", "Charts", "Corporation"]);
    expect(CATEGORIES).toHaveLength(12);
    expect(CATEGORIES[0]).toBe("Sales revenue");
    expect(CATEGORIES[11]).toBe("Land value");
  });
  it("uses arrow frames that exist in the UI atlas", () => {
    const frames = ui.frames as Record<string, unknown>;
    expect(frames.icon_arr_up).toBeDefined();
    expect(frames.icon_arr_down).toBeDefined();
  });
});
