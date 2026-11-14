// @vitest-environment happy-dom
import { describe, expect, it } from "vitest";
import { CLIMATE_NAMES, TownJson, growthPct, growthSeries, pct, townCard, townIndicators } from "../src/ui/towncard";

/** A `town` result as the sim returns it about 13 months in (Api.new_game(seed=3), town 0). */
export const TOWN: TownJson = {
  id: 0,
  name: "Riverside",
  level: 2,
  population: 628504.35,
  gnp: 7030731200.49,
  per_capita_gnp: 11186.45,
  unemployment: 2,
  labor_cost: 59.825,
  labor_quality: 58.21,
  consumer_spending: 61.76,
  climate: 3,
  pop_history: [627972, 628007, 628310, 628488, 628486, 628456, 628372, 628503, 628407, 628418, 628404, 628504],
  gnp_level_history: [11808, 11808, 11611, 11418, 11265, 11078, 11188, 11300, 11112, 11186, 11223, 11186],
  pop_growth_pct: [0.0056, 0.0483, 0.0283, -0.0003, -0.0048, -0.0134, 0.0209, -0.0153, 0.0018, -0.0023, 0.0159],
  gnp_level_growth_pct: [0, -1.667, -1.667, -1.333, -1.667, 1, 1, -1.667, 0.667, 0.333, -0.333],
};

describe("town card", () => {
  it("formats the eight indicators per the Shared rules", () => {
    expect(townIndicators(TOWN)).toEqual([
      ["Population", "628,504"],
      ["GNP", "$7.0B"],
      ["Per capita GNP", "$11,186"],
      ["Unemployment", "2.0%"],
      ["Labor cost", "59.8"],
      ["Labor quality", "58.2"],
      ["Consumer spending", "61.8"],
      ["Economic climate", "Prosperous"],
    ]);
    expect(CLIMATE_NAMES).toHaveLength(5);
  });

  it("formats growth with a sign and enough digits to see small months", () => {
    expect(growthPct(1.234)).toBe("+1.2%");
    expect(growthPct(-1.667)).toBe("\u22121.7%");
    expect(growthPct(0.0483)).toBe("+0.05%");
    expect(growthPct(-0.0003)).toBe("0.00%");
    expect(growthPct(0)).toBe("0.0%");
    expect(pct(-0.25)).toBe("\u22120.3%");
  });

  it("labels growth months back from the last complete month and skips nulls", () => {
    const s = growthSeries([1, null, 3], { year: 1991, month: 2 });
    expect(s).toEqual([
      { label: "Nov", value: 1 },
      { label: "Jan", value: 3 },
    ]);
  });

  it("renders the title, badge, indicators and both charts", () => {
    const spec = townCard(TOWN, { year: 1991, month: 2 }, 352);
    expect(spec.key).toBe("town:0");
    expect(spec.title).toBe("Riverside");
    expect(spec.badge).toBe("2");
    expect(spec.heights).toEqual(["peek", "half"]);
    const titles = Array.from(spec.body.querySelectorAll(".chart-title")).map((e) => e.textContent);
    expect(titles).toEqual(["Population growth", "Per capita GNP growth"]);
    expect(spec.body.querySelector("dd")?.textContent).toBe("628,504");
  });

  it("explains empty charts in a new game", () => {
    const spec = townCard({ ...TOWN, pop_growth_pct: [], gnp_level_growth_pct: [] }, { year: 1990, month: 1 }, 352);
    expect(spec.body.querySelector(".chart")).toBeNull();
    expect(spec.body.textContent).toContain("Growth charts start");
  });
});
