// @vitest-environment happy-dom
import { describe, expect, it, vi } from "vitest";
import { endCard, endWatcher, newGameUrl, showsEndCard } from "../src/ui/endcard";
import { demoEnd } from "../src/ui/enddemo";

const text = (e: Element, sel: string) => e.querySelector(sel)?.textContent;

describe("win/loss card", () => {
  it.each([
    ["win", "Goals achieved", "8,420"],
    ["time", "Out of time", "3,115"],
    ["rival", "A rival got there first", "4,960"],
  ] as const)("%s: band, icon, headline, score and goal rows", (kind, headline, score) => {
    const card = endCard(demoEnd(kind), () => {});
    expect(card.querySelector(`.end-band.ui-end_band_${kind}`)).not.toBeNull();
    expect(card.querySelector(`.end-icon.ui-icon_end_${kind}`)).not.toBeNull();
    expect(text(card, ".end-headline")).toBe(headline);
    expect(Array.from(card.querySelectorAll(".end-rows dt")).map((d) => d.textContent)).toEqual(["Final score", "Years played", "Difficulty"]);
    expect(text(card, ".end-rows dd")).toBe(score);
    const rows = card.querySelectorAll(".end-goals .goal-row");
    expect(rows).toHaveLength(6);
    expect(card.querySelectorAll(".end-goals .goal-row.met").length).toBe(kind === "win" ? 6 : 3);
  });
  it("bankrupt in a game with no goals: no score row, no goal list", () => {
    const card = endCard(demoEnd("bankrupt"), () => {});
    expect(text(card, ".end-headline")).toBe("Bankrupt");
    expect(card.querySelector(".ui-end_band_bankrupt")).not.toBeNull();
    expect(Array.from(card.querySelectorAll(".end-rows dt")).map((d) => d.textContent)).toEqual(["Years played", "Difficulty"]);
    expect(card.querySelector(".end-goals")).toBeNull();
  });
  it("shows a score of 0 when cheats were used", () => {
    const card = endCard({ ...demoEnd("win"), cheated: true }, () => {});
    expect(text(card, ".end-rows dd")).toBe("0");
  });
  it("has New game as its only button", () => {
    const onNew = vi.fn();
    const card = endCard(demoEnd("rival"), onNew);
    const buttons = card.querySelectorAll("button");
    expect(Array.from(buttons).map((b) => b.textContent)).toEqual(["New game"]);
    (buttons[0] as HTMLButtonElement).click();
    expect(onNew).toHaveBeenCalled();
    expect(card.textContent).not.toContain("Keep playing");
  });
  it("a goal-less game shows the card only for bankruptcy", () => {
    expect(showsEndCard(1, false)).toBe(false);
    expect(showsEndCard(4, false)).toBe(true);
    expect(showsEndCard(0, true)).toBe(false);
    expect(showsEndCard(3, true)).toBe(true);
  });
  it("new game keeps the options and drops the seed", () => {
    expect(newGameUrl("http://x/?seed=3&events=2")).toBe("http://x/?events=2");
  });
});

describe("end watcher", () => {
  it("pauses the sim on the first result and shows the card once", async () => {
    const pause = vi.fn();
    const show = vi.fn();
    const fetch = vi.fn(async () => demoEnd("rival"));
    const watch = endWatcher(pause, fetch, show);
    watch({ result: 0 });
    expect(pause).not.toHaveBeenCalled();
    watch({ result: 3 });
    watch({ result: 3 });
    expect(pause).toHaveBeenCalledTimes(1);
    await Promise.resolve();
    await Promise.resolve();
    expect(show).toHaveBeenCalledTimes(1);
  });
  it("pauses but shows nothing when a goal-less game reports a goal result", async () => {
    const show = vi.fn();
    const watch = endWatcher(() => {}, async () => ({ ...demoEnd("win"), has_goals: false, goals: [] }), show);
    watch({ result: 1 });
    await Promise.resolve();
    await Promise.resolve();
    expect(show).not.toHaveBeenCalled();
  });
});
