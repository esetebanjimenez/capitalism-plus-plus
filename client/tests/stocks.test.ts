// @vitest-environment happy-dom
import { describe, expect, it, vi } from "vitest";
import { DEMO_STOCK, DEMO_STOCKS } from "../src/ui/stocksdemo";
import { StockJson, pe, priceSeries, sharePrice, stockPage, stocksList } from "../src/ui/stocks";

const today = { year: 1993, month: 3, day_serial: (Date.UTC(1993, 2, 1) - Date.UTC(1900, 0, 1)) / 86_400_000 };
const hooks = (over = {}) => ({
  range: "day" as const,
  today,
  chartWidth: 300,
  onRange: vi.fn(),
  onList: vi.fn(),
  onReport: vi.fn(),
  ...over,
});

describe("stocks list", () => {
  it("shows every corporation with price, P/E, owned % and holding", () => {
    const p = stocksList(DEMO_STOCKS, () => {});
    const rows = Array.from(p.body.querySelectorAll(".stock-row"));
    expect(rows).toHaveLength(4);
    const cells = Array.from(rows[0].querySelectorAll("td")).map((c) => c.textContent);
    expect(cells).toEqual(["Esteban Holdings", "$18.25", "14.2", "62.0%", "$11,315,000"]);
    expect(rows[2].querySelectorAll("td")[2].textContent).toBe("n/a");
  });
  it("opens a corporation on tap", () => {
    const onCorp = vi.fn();
    const p = stocksList(DEMO_STOCKS, onCorp);
    (p.body.querySelectorAll(".stock-row")[3] as HTMLElement).click();
    expect(onCorp).toHaveBeenCalledWith(3);
  });
});

describe("stock page", () => {
  it("labels daily prices with the day of month, ending today", () => {
    const pts = priceSeries(DEMO_STOCK, "day", today);
    expect(pts).toHaveLength(30);
    expect(pts[29].label).toBe("1");
    expect(pts[28].label).toBe("28"); // 28 Feb 1993
  });
  it("labels months up to last month and years up to last year", () => {
    expect(priceSeries(DEMO_STOCK, "month", today).at(-1)?.label).toBe("Feb");
    expect(priceSeries(DEMO_STOCK, "year", today).map((p) => p.label)).toEqual(["1991", "1992"]);
  });
  it("draws a single-day series and shows n/a for a null P/E and dividend yield", () => {
    const s: StockJson = { ...DEMO_STOCK, daily_prices: [5], monthly_prices: [], yearly_prices: [], pe_ratio: null, dividend_yield: null };
    const p = stockPage("Northwind Foods", s, hooks());
    expect(p.body.querySelectorAll(".chart")).toHaveLength(1);
    const dd = Array.from(p.body.querySelectorAll("dd")).map((d) => d.textContent);
    expect(dd).toEqual(["$24.60", "10,000,000", "3,550,000", "n/a", "n/a"]);
  });
  it("says when there is no monthly series yet", () => {
    const s: StockJson = { ...DEMO_STOCK, monthly_prices: [] };
    const p = stockPage("Atlas", s, hooks({ range: "month" }));
    expect(p.body.querySelector(".chart")).toBeNull();
    expect(p.body.querySelector(".note")?.textContent).toContain("after the first month");
  });
  it("lists shareholders largest first with shares, % and value", () => {
    const p = stockPage("Atlas", DEMO_STOCK, hooks());
    const rows = Array.from(p.body.querySelectorAll(".holders tr")).slice(1);
    expect(rows.map((r) => r.querySelector("td")?.textContent)).toEqual(["Founder", "Esteban Holdings"]);
    expect(Array.from(rows[1].querySelectorAll("td")).map((c) => c.textContent)).toEqual(["Esteban Holdings", "450,000", "4.5%", "$11,070,000"]);
  });
  it("switches range and opens the read-only report", () => {
    const h = hooks();
    const p = stockPage("Atlas", DEMO_STOCK, h);
    (Array.from(p.body.querySelectorAll(".range .tab"))[2] as HTMLElement).click();
    expect(h.onRange).toHaveBeenCalledWith("year");
    expect(p.key).toBe("stock:1");
    expect(p.actions).toHaveLength(3);
  });
  it("formats prices and P/E", () => {
    expect(sharePrice(7.1)).toBe("$7.10");
    expect(pe(null)).toBe("n/a");
    expect(pe(9.84)).toBe("9.8");
    expect(pe(0)).toBe("n/a");
  });
});

describe("rival report", () => {
  it("shows only Income and Charts under its own key", async () => {
    const { companyReport } = await import("../src/ui/company");
    const { DEMO_CORP } = await import("../src/ui/companydemo");
    const p = companyReport(DEMO_CORP, { tab: "Income", byFirm: false }, {
      firmLabel: String,
      onFirm: () => {},
      onState: () => {},
      tabs: ["Income", "Charts"],
      key: "company:2",
    });
    expect(Array.from(p.body.querySelectorAll(".tabs .tab")).map((t) => t.textContent)).toEqual(["Income", "Charts"]);
    expect(p.key).toBe("company:2");
  });
});
