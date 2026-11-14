/**
 * Win/loss card (#263, view brief section 5, art/README "Win/loss card", docs/art/m2-views-preview.png):
 * a full-screen card when `goals.result` is no longer IN_PROGRESS. One layout, four outcomes,
 * each with its own band and 2x icon. New game is the only button (the native game has no
 * Keep playing, #243). Bankruptcy can end a game with no goals, so the score row and the goal
 * list hide when the game has no goals.
 */
import { GoalsJson, goalRow } from "./goals";

export type EndKind = "win" | "time" | "rival" | "bankrupt";

/** GameResult (goals.py) to the card's art and headline. */
export const OUTCOMES: Record<number, { kind: EndKind; name: string; headline: string }> = {
  1: { kind: "win", name: "VICTORY", headline: "Goals achieved" },
  2: { kind: "time", name: "DEFEAT_DEADLINE", headline: "Out of time" },
  3: { kind: "rival", name: "DEFEAT_AI_WON", headline: "A rival got there first" },
  4: { kind: "bankrupt", name: "DEFEAT_BANKRUPT", headline: "Bankrupt" },
};

/** Whether a tick's result ends the game with a card. A goal-less game only ends by bankruptcy. */
export function showsEndCard(result: number, hasGoals: boolean): boolean {
  const o = OUTCOMES[result];
  return o !== undefined && (hasGoals || o.kind === "bankrupt");
}

const el = <K extends keyof HTMLElementTagNameMap>(tag: K, cls = "", text = ""): HTMLElementTagNameMap[K] => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
};

/** The summary rows: final score (only with goals; 0 when cheated, still shown), years, difficulty. */
export function endSummary(g: GoalsJson): [string, string][] {
  const out: [string, string][] = [];
  if (g.has_goals) out.push(["Final score", g.cheated ? "0" : g.score.toLocaleString("en-US")]);
  out.push(["Years played", String(g.years_played)], ["Difficulty", String(g.difficulty)]);
  return out;
}

/** The card as a full-screen overlay element; the caller appends it to the page. */
export function endCard(g: GoalsJson, onNewGame: () => void): HTMLElement {
  const o = OUTCOMES[g.result];
  if (!o) throw new Error(`no end card for result ${g.result}`);
  const shade = el("div", "end-shade");
  shade.dataset.result = o.name;
  const card = el("div", "end-card ui-card");
  card.setAttribute("role", "dialog");
  card.setAttribute("aria-label", o.headline);
  const band = el("div", `end-band ui-end_band_${o.kind}`);
  band.append(el("span", `end-icon ui-icon_end_${o.kind}`), el("h2", "end-headline", o.headline));
  const dl = el("dl", g.has_goals && g.goals.length ? "rows end-rows" : "rows end-rows last");
  for (const [k, v] of endSummary(g)) dl.append(el("dt", "", k), el("dd", "", v));
  card.append(band, dl);
  if (g.has_goals && g.goals.length) {
    const list = el("div", "end-goals");
    list.append(el("h3", "end-goals-head", "Goals"));
    for (const row of g.goals) list.append(goalRow(row));
    card.append(list);
  }
  const btn = el("button", "btn ui-btn_primary end-new", "New game");
  btn.dataset.kind = "primary";
  btn.onclick = onNewGame;
  card.append(btn);
  shade.append(card);
  return shade;
}

/** The URL for a new game: the same setup options, without a fixed seed, so devSetup picks a new one. */
export function newGameUrl(href: string): string {
  const u = new URL(href);
  for (const k of ["seed", "end"]) u.searchParams.delete(k);
  return u.toString();
}

/**
 * A tick handler that, the first time a tick's result is not IN_PROGRESS, pauses the sim, asks
 * `goals` for the final numbers and shows the card (unless a goal-less game ended otherwise).
 */
export function endWatcher(pause: () => void, fetchGoals: () => Promise<GoalsJson>, show: (g: GoalsJson) => void): (t: { result: number }) => void {
  let done = false;
  return (t) => {
    if (done || !t.result) return;
    done = true;
    pause();
    void fetchGoals().then((g) => {
      if (showsEndCard(g.result, g.has_goals)) show(g);
    });
  };
}
