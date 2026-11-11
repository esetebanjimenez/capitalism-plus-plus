import { FIRM_NAMES } from "../firms";
import { DEEP_OCEAN, FOREST_HILL, FirmInfo, GRASSLAND, MapData, TOWN, TownInfo, WATER } from "../mapdata";
import { money } from "./layout";
import { PanelSpec, button, rows } from "./shell";

const KIND_NAMES: Record<number, string> = {
  [DEEP_OCEAN]: "Deep ocean",
  [WATER]: "Water",
  [GRASSLAND]: "Grassland",
  [FOREST_HILL]: "Forest / hill",
  [TOWN]: "Town",
};

const div = (cls: string, ...kids: (Node | string)[]) => {
  const d = document.createElement("div");
  d.className = cls;
  d.append(...kids);
  return d;
};

/**
 * Tile card (spec: tap empty land): kind, land value, soil, rainfall, and Build when
 * World.can_build. Values come from the sample map's TINF section until the facade lands.
 */
export function tileCard(m: MapData, x: number, y: number, onBuild: () => void): PanelSpec {
  const i = y * m.width + x;
  const ring = m.townAt[i] >= 0;
  const info = m.info;
  const kind = ring ? "Town outskirts" : (KIND_NAMES[m.kind[i]] ?? "Land");
  const pairs: [string, string][] = info
    ? [
        ["Land value", money(info.landValue[i]).replace(/^\+/, "")],
        ["Soil", `${info.soil[i]} of 3`],
        ["Rainfall", `${info.rainfall[i]} of 4`],
      ]
    : [["Land value", "not loaded"]];
  const buildable = info ? info.buildable[i] === 1 : false;
  return {
    key: `tile:${x},${y}`,
    title: kind,
    body: div("card-body", div("sub", `Tile ${x}, ${y}`), rows(pairs)),
    actions: buildable ? [button("Build", "primary", onBuild)] : [],
    height: "peek",
    heights: ["peek"],
  };
}

const ownerText = (owner: number | null, player = 0) =>
  owner === null ? "No owner" : owner === player ? "You" : `Corporation ${owner}`;

/** Firm detail header only; slots, links and numbers come with the capitalism.api facade. */
export function firmCard(f: FirmInfo): PanelSpec {
  return {
    key: `firm:${f.x},${f.y}`,
    title: FIRM_NAMES[f.type] ?? "Firm",
    body: div("card-body", div("sub", `${ownerText(f.owner)} \u00b7 tile ${f.x}, ${f.y}`), div("note", "Slots and links arrive with the sim facade.")),
    height: "peek",
    heights: ["peek", "half", "full"],
  };
}

/** Town card header only; the indicators come with the capitalism.api facade. */
export function townCard(t: TownInfo): PanelSpec {
  return {
    key: `town:${t.id}`,
    title: `Town ${t.id}`,
    body: div("card-body", div("sub", `Level ${t.level} \u00b7 tile ${t.x}, ${t.y}`), div("note", "City indicators arrive with the sim facade.")),
    height: "peek",
    heights: ["peek", "half"],
  };
}

/** The menu: Company, Stocks, News, Goals. Their reports are later PRs. */
export function menuPanel(onPick: (entry: string) => void): PanelSpec {
  const list = div("menu-list");
  for (const name of ["Company", "Stocks", "News", "Goals"]) list.append(button(name, "secondary", () => onPick(name)));
  return { key: "menu", title: "Menu", body: list, height: "peek", heights: ["peek"] };
}
