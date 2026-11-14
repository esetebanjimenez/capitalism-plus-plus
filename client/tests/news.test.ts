// @vitest-environment happy-dom
import { describe, expect, it } from "vitest";
import ui from "../../art/atlas/ui_atlas.json";
import { ALL_NEWS, CATEGORY_ICONS, NewsItem, filterNews, newsDate, newsReport, serialDate, unreadImportant } from "../src/ui/news";

const serial = (y: number, m: number, d: number) => Math.round((Date.UTC(y, m - 1, d) - Date.UTC(1900, 0, 1)) / 86_400_000);
const item = (over: Partial<NewsItem>): NewsItem => ({
  day_serial: serial(1990, 3, 12),
  category: 0,
  corp_id: 1,
  corp_name: "Rival Inc",
  news_type: 0,
  important: false,
  headline: "Something happened",
  corp: 1,
  firm: null,
  product: null,
  ...over,
});
const today = { year: 1990, month: 3 };
const feed = [
  item({ day_serial: serial(1990, 3, 20), category: 1, important: true, headline: "Crash", corp_id: 2, corp_name: "Other" }),
  item({ day_serial: serial(1990, 3, 5), category: 2 }),
  item({ day_serial: serial(1990, 1, 9), category: 3, important: true }),
  item({ day_serial: serial(1989, 12, 31), category: 0 }),
];
const hooks = { today, onState: () => {}, onItem: () => {} };

describe("news dates", () => {
  it("counts days from 1 Jan 1900 and caps the shown day at 30", () => {
    expect(serialDate(0)).toEqual({ year: 1900, month: 1, day: 1 });
    expect(serialDate(serial(1990, 3, 12))).toEqual({ year: 1990, month: 3, day: 12 });
    expect(newsDate(serial(1990, 1, 31))).toBe("30 Jan 1990");
  });
});

describe("news rows (view brief section 3)", () => {
  it("has one atlas icon per category", () => {
    expect(CATEGORY_ICONS).toEqual(["icon_nws_normal", "icon_nws_financial", "icon_nws_tech", "icon_nws_special"]);
    for (const k of CATEGORY_ICONS) expect((ui.frames as Record<string, unknown>)[k]).toBeTruthy();
    const rows = Array.from(newsReport(feed, ALL_NEWS, hooks).body.querySelectorAll(".news-row"));
    expect(rows.map((r) => r.querySelector(".news-icon")!.className)).toEqual(
      ["financial", "tech", "special", "normal"].map((c) => `news-icon ui-icon_nws_${c}`),
    );
  });
  it("lists newest first with important items bold", () => {
    const rows = Array.from(newsReport(feed, ALL_NEWS, hooks).body.querySelectorAll<HTMLElement>(".news-row"));
    expect(rows[0].querySelector(".news-headline")!.textContent).toBe("Crash");
    expect(rows[0].querySelector(".news-meta")!.textContent).toBe("20 Mar 1990 \u00b7 Other");
    expect(rows.map((r) => r.classList.contains("important"))).toEqual([true, false, true, false]);
  });
  it("taps through to the item", () => {
    let got: NewsItem | null = null;
    const body = newsReport(feed, ALL_NEWS, { ...hooks, onItem: (n) => (got = n) }).body;
    body.querySelectorAll<HTMLElement>(".news-row")[1].click();
    expect(got).toBe(feed[1]);
  });
});

describe("news filters", () => {
  it("filters by corporation, category and time", () => {
    expect(filterNews(feed, { ...ALL_NEWS, corp: 2 }, today)).toEqual([feed[0]]);
    expect(filterNews(feed, { ...ALL_NEWS, category: 2 }, today)).toEqual([feed[1]]);
    expect(filterNews(feed, { ...ALL_NEWS, time: "month" }, today)).toEqual([feed[0], feed[1]]);
    expect(filterNews(feed, { ...ALL_NEWS, time: "year" }, today)).toEqual(feed.slice(0, 3));
  });
  it("draws chips with the picked one on, and reports picks", () => {
    let state = ALL_NEWS;
    const body = newsReport(feed, { ...ALL_NEWS, category: 1 }, { ...hooks, onState: (f) => (state = f) }).body;
    const groups = Array.from(body.querySelectorAll(".news-filter"));
    expect(groups.map((g) => g.querySelector(".news-filter-label")!.textContent)).toEqual(["Corporation", "Category", "Time"]);
    const on = Array.from(groups[1].querySelectorAll(".chip.on")).map((c) => c.textContent);
    expect(on).toEqual(["Financial"]);
    expect(groups[1].querySelectorAll(".ui-chip_off").length).toBe(4);
    (groups[0].querySelectorAll(".chip")[2] as HTMLElement).click();
    expect(state).toEqual({ corp: 2, category: 1, time: "all" });
    expect(body.querySelectorAll(".news-row").length).toBe(1);
  });
  it("leaves items with no corporation out of the corporation chips", () => {
    const body = newsReport([...feed, item({ corp_id: -1, corp_name: null })], ALL_NEWS, hooks).body;
    const chips = Array.from(body.querySelector(".news-filter")!.querySelectorAll(".chip")).map((c) => c.textContent);
    expect(chips).toEqual(["All", "Rival Inc", "Other"]);
  });
  it("says so when nothing matches", () => {
    expect(newsReport(feed, { ...ALL_NEWS, corp: 9 }, hooks).body.querySelector(".news-empty")!.textContent).toMatch(/No news matches/);
  });
});

describe("news badge", () => {
  it("counts important items after the read mark", () => {
    expect(unreadImportant(feed, -1)).toBe(2);
    expect(unreadImportant(feed, serial(1990, 2, 1))).toBe(1);
    expect(unreadImportant(feed, serial(1990, 3, 20))).toBe(0);
  });
});
