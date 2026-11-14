// @vitest-environment happy-dom
import { describe, expect, it } from "vitest";
import style from "../../art/charts.json";
import { PALETTE, chartLayout } from "../src/ui/chart";
import { CorpJson, companyReport } from "../src/ui/company";
import { CHART_SERIES, chartSeries, chartsTab, monthLabels, yearLabels } from "../src/ui/companycharts";

const hist = (n: number, f: (i: number) => number) => Object.fromEntries(CHART_SERIES.map(([k]) => [k, Array.from({ length: n }, (_, i) => f(i))]));
const today = { year: 1991, month: 3 };

describe("Company charts labels (#258)", () => {
  it("labels months from the month before today", () => {
    expect(monthLabels(1, today)).toEqual(["Feb"]);
    expect(monthLabels(5, today)).toEqual(["Oct", "Nov", "Dec", "Jan", "Feb"]);
    expect(monthLabels(12, today)).toEqual(["Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb"]);
    expect(monthLabels(1, { year: 1991, month: 1 })).toEqual(["Dec"]);
  });
  it("labels years ending with last year", () => {
    expect(yearLabels(1, today)).toEqual(["1990"]);
    expect(yearLabels(3, today)).toEqual(["1988", "1989", "1990"]);
  });
  it("gives five charts, one series each, for 1, 5 and 12 months", () => {
    for (const n of [1, 5, 12]) {
      const s = chartSeries({ month_history: hist(n, (i) => i * 10) }, "months", today);
      expect(s.map((x) => x.title)).toEqual(["Revenue", "Operating profit", "Other profit", "Expenses", "Net worth"]);
      for (const x of s) {
        expect(x.points.map((p) => p.value)).toEqual(Array.from({ length: n }, (_, i) => i * 10));
        expect(x.points.map((p) => p.label)).toEqual(monthLabels(n, today));
      }
    }
  });
  it("reads year_history for Past years", () => {
    const s = chartSeries({ month_history: {}, year_history: { revenue: [5, 7] } }, "years", today);
    expect(s[0].points).toEqual([
      { label: "1989", value: 5 },
      { label: "1990", value: 7 },
    ]);
    expect(s[1].points).toEqual([]);
  });
});

describe("Company charts tab (#258)", () => {
  const zeroLines = (el: HTMLElement) =>
    Array.from(el.querySelectorAll("line")).filter((l) => l.getAttribute("stroke") === PALETTE[style.zero_line.colour]).length;

  it("draws the zero line only on a profit that crosses zero", () => {
    const h = hist(5, (i) => 100 + i);
    h.operating_profit = [-300, -100, 50, 200, 120];
    const el = chartsTab({ month_history: h }, "months", today, 360, () => {});
    const cards = Array.from(el.querySelectorAll(".chart"));
    expect(cards.length).toBe(5);
    expect(cards.map((c) => zeroLines(c as HTMLElement))).toEqual([0, 1, 0, 0, 0]);
    expect(chartLayout(h.operating_profit.map((value) => ({ label: "", value })), 360, 170).zeroY).not.toBeNull();
  });
  it("switches range and says when there is no complete month yet", () => {
    const picked: string[] = [];
    const el = chartsTab({ month_history: hist(0, () => 0) }, "months", today, 360, (r) => picked.push(r));
    expect(el.querySelector(".note")?.textContent).toMatch(/first complete month/);
    const [months, years] = Array.from(el.querySelectorAll<HTMLButtonElement>(".range .tab"));
    expect(months.className).toBe("tab on");
    years.click();
    expect(picked).toEqual(["years"]);
  });
  it("fills the Charts tab of the Company report", () => {
    const c: CorpJson = {
      id: 0,
      name: "P",
      revenue: 0,
      operating_expenses: 0,
      operating_profit: 0,
      other_profit: 0,
      net_profit: 0,
      ledger: { cash: 0, month: [], last_month: [], year: [] },
      by_firm: [],
      month_history: hist(12, (i) => i),
    };
    const spec = companyReport(c, { tab: "Charts", byFirm: false }, { firmLabel: String, onFirm: () => {}, onState: () => {}, today });
    expect(spec.body.querySelectorAll(".chart").length).toBe(5);
    expect(spec.body.querySelector(".coming")).toBeNull();
  });
});
