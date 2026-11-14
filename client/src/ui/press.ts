/**
 * What a long press (or right click) on the map does (#338 rule, Esteban on #336/#337):
 * on a town plate's pixels it opens that town's card; anywhere else on empty land it opens
 * the build panel for the tile; on a firm or town tile it does nothing.
 */
import { TownInfo } from "../mapdata";
import { Pick } from "./layout";

export type LongPress = { kind: "town"; town: TownInfo } | { kind: "build"; x: number; y: number } | null;

export function longPressAction(plateTown: TownInfo | null, pick: Pick): LongPress {
  if (plateTown) return { kind: "town", town: plateTown };
  if (pick.kind === "tile") return { kind: "build", x: pick.x, y: pick.y };
  return null;
}
