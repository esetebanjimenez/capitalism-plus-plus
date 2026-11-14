/**
 * Build panel (#252, ux-spec section 1 "Build menu", art/README #176): the firm types the
 * player can build on a tile from the `build_options` query, each with its map sprite, build
 * cost (setup plus land) and monthly overhead. A type the player can't afford draws its sprite
 * at 50% opacity with the shortfall in red and is a disabled button.
 */
import { FIRM_SPRITES } from "../firms";
import { shortMoney } from "./chart";
import { dollars } from "./company";
import { PanelSpec, button } from "./shell";

/** One row of the `build_options` query (docs/m2-facade-contract.md). */
export interface BuildOption {
  type_id: number;
  name: string;
  setup_cost: number;
  land_value: number;
  build_cost: number;
  overhead_month: number;
  affordable: boolean;
  shortfall: number;
}

export interface BuildOptionsJson {
  x: number;
  y: number;
  can_build: boolean;
  options: BuildOption[];
}

/** Short money label for rows: $1.5M, $600k. */
export const cost = (v: number) => `$${shortMoney(v)}`;

/** ux-spec "Confirmations": anything that spends more than 10% of player cash asks first. */
export const needsConfirm = (spend: number, cash: number) => spend > 0.1 * cash;

/** A row can be chosen only on a buildable tile the player can afford. */
export const canChoose = (o: BuildOption, canBuild: boolean) => canBuild && o.affordable;

const span = (cls: string, text = "") => {
  const s = document.createElement("span");
  s.className = cls;
  s.textContent = text;
  return s;
};

export function buildRow(o: BuildOption, canBuild: boolean, onPick: (o: BuildOption) => void): HTMLButtonElement {
  const b = document.createElement("button");
  b.className = `build-row${o.affordable ? "" : " unaffordable"}`;
  b.disabled = !canChoose(o, canBuild);
  b.dataset.type = String(o.type_id);
  const icon = span(`firm-icon firm-${FIRM_SPRITES[o.type_id] ?? "unknown"}`);
  const text = span("build-text");
  text.append(span("build-name", o.name), span("build-overhead", `${cost(o.overhead_month)}/month`));
  const right = span("build-cost-col");
  right.append(span("build-cost", cost(o.build_cost)));
  if (!o.affordable) right.append(span("build-short", `short ${cost(o.shortfall)}`));
  b.append(icon, text, right);
  b.setAttribute(
    "aria-label",
    `${o.name}, ${cost(o.build_cost)}, ${cost(o.overhead_month)} a month${o.affordable ? "" : `, short ${cost(o.shortfall)}`}`,
  );
  if (!b.disabled) b.onclick = () => onPick(o);
  return b;
}

/** The build panel for one tile; `cash` is the player's cash for the header. */
export function buildPanel(b: BuildOptionsJson, cash: number, onPick: (o: BuildOption) => void): PanelSpec {
  const body = document.createElement("div");
  body.className = "card-body build";
  const head = span("sub build-sub", `Tile ${b.x}, ${b.y} \u00b7 Cash ${dollars(cash)}`);
  body.append(head);
  if (!b.can_build) body.append(span("build-note", "You can't build on this tile. Tap another tile."));
  const list = document.createElement("div");
  list.className = "build-list";
  for (const o of b.options) list.append(buildRow(o, b.can_build, onPick));
  body.append(list);
  return { key: "build", title: "Build here", body, height: "half", heights: ["half", "full"] };
}

/** Confirmation before a build that spends more than 10% of cash. */
export function buildConfirm(o: BuildOption, cash: number, onOk: () => void, onCancel: () => void): PanelSpec {
  const body = document.createElement("div");
  body.className = "card-body build-confirm";
  const pct = cash > 0 ? Math.round((o.build_cost / cash) * 100) : 100;
  body.append(
    span("build-confirm-text", `Building a ${o.name} costs ${dollars(o.build_cost)}, ${pct}% of your cash.`),
    span("sub", `Overhead ${cost(o.overhead_month)} a month.`),
  );
  return {
    key: "build-confirm",
    title: `Build a ${o.name}?`,
    body,
    actions: [button("Build", "primary", onOk), button("Cancel", "secondary", onCancel)],
    height: "peek",
    heights: ["peek"],
  };
}
