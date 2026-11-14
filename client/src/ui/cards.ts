import { FIRM_NAMES } from "../firms";
import { DEEP_OCEAN, FOREST_HILL, FirmInfo, GRASSLAND, MapData, TOWN, TownInfo, WATER, townBand } from "../mapdata";
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

/** The `tile` query result (docs/m2-facade-contract.md). */
export interface TileJson {
  x: number;
  y: number;
  kind: number;
  town_kind: number;
  soil: number;
  rainfall: number;
  land_value: number;
  can_build: boolean;
  /** Nearest town id. */
  town: number;
}

/** A `tile` result from the sample map's TINF section, for tests and the bench page. */
export function sampleTile(m: MapData, x: number, y: number): TileJson {
  const i = y * m.width + x;
  const info = m.info;
  return {
    x,
    y,
    kind: m.kind[i],
    town_kind: m.townKind[i],
    soil: info ? info.soil[i] : 0,
    rainfall: info ? info.rainfall[i] : 0,
    land_value: info ? info.landValue[i] : 0,
    can_build: info ? info.buildable[i] === 1 : false,
    town: -1,
  };
}

/**
 * Tile card (spec: tap empty land): kind, land value, soil, rainfall, and Build when
 * World.can_build. Values come from the `tile` query.
 */
export function tileCard(t: TileJson, onBuild: () => void): PanelSpec {
  const band = townBand(t.town_kind);
  const kind = band === "urban" ? "Town (urban)" : band === "rural" ? "Town (rural)" : (KIND_NAMES[t.kind] ?? "Land");
  const pairs: [string, string][] = [
    ["Land value", money(t.land_value).replace(/^\+/, "")],
    ["Soil", `${t.soil} of 3`],
    ["Rainfall", `${t.rainfall} of 4`],
  ];
  return {
    key: `tile:${t.x},${t.y}`,
    title: kind,
    body: div("card-body", div("sub", `Tile ${t.x}, ${t.y}`), rows(pairs)),
    actions: t.can_build ? [button("Build", "primary", onBuild)] : [],
    height: "peek",
    heights: ["peek"],
  };
}

const ownerText = (owner: number | null, player = 0) =>
  owner === null ? "No owner" : owner === player ? "You" : `Corporation ${owner}`;

/** Firm detail header only; slots, links and numbers come with the capitalism.api facade. */
export function firmCard(f: FirmInfo): PanelSpec {
  return {
    key: f.id >= 0 ? `firm:${f.id}` : `firm:${f.x},${f.y}`,
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
    title: t.name,
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
