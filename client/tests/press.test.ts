import { describe, expect, it } from "vitest";
import { TownInfo } from "../src/mapdata";
import { longPressAction } from "../src/ui/press";

const town = { id: 0, name: "Cedar Falls", x: 212, y: 156, level: 2 } as TownInfo;

describe("long press on the map (#338 rule)", () => {
  it("opens the town card on plate pixels, even over buildable land", () => {
    expect(longPressAction(town, { kind: "tile", x: 212, y: 150 })).toEqual({ kind: "town", town });
  });
  it("opens the build panel anywhere else on empty land", () => {
    expect(longPressAction(null, { kind: "tile", x: 230, y: 160 })).toEqual({ kind: "build", x: 230, y: 160 });
  });
  it("does nothing on a firm or town tile off the plate", () => {
    expect(longPressAction(null, { kind: "town", town })).toBeNull();
    expect(longPressAction(null, { kind: "none" })).toBeNull();
  });
});
