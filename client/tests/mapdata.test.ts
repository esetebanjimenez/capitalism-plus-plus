import { describe, expect, it } from "vitest";
import { chunkKey, chunksForTiles } from "../src/chunkmath";
import { FIRM, GRASSLAND, MapJson, TOWN, applyMapObjects, mapFromJson, townOfTile } from "../src/mapdata";
import { frameFor } from "../src/tiles";

/** A 4 x 3 `map` query result: one town of three tiles, one firm. */
function fixture(): MapJson {
  const g = GRASSLAND;
  return {
    width: 4,
    height: 3,
    kind: [g, TOWN, TOWN, g, g, TOWN, FIRM, g, g, g, g, g],
    ref: [-1, 0, 0, -1, -1, 0, 0, -1, -1, -1, -1, -1],
    town_kind: [0, 0x3001, 0x3008, 0, 0, 0x3002, 0x3009, 0, 0, 0, 0, 0],
    climate: Array(12).fill(2),
    map_rev: 3,
    towns: [{ id: 0, name: "Springfield", x: 2, y: 0, level: 1 }],
    firms: [{ id: 0, x: 2, y: 1, type_id: 1, owner: 0 }],
  };
}

describe("live map data (#249)", () => {
  it("builds MapData from the map query", () => {
    const m = mapFromJson(fixture());
    expect([m.width, m.height, m.rev]).toEqual([4, 3, 3]);
    expect(m.towns).toEqual([{ id: 0, name: "Springfield", x: 2, y: 0, level: 1 }]);
    expect(m.firms).toEqual([{ id: 0, x: 2, y: 1, type: 1, owner: 0 }]);
    expect(townOfTile(m, 1)?.name).toBe("Springfield");
    expect(townOfTile(m, 0)).toBeNull();
    expect(frameFor(m, 2, 0)).toBe("town_urban_0");
    expect(frameFor(m, 1, 0)).toBe("town_rural_1");
    expect(frameFor(m, 2, 1)).toBe("town_urban_1"); // the firm stands on an urban tile
  });

  it("rejects arrays that do not match the size", () => {
    expect(() => mapFromJson({ ...fixture(), climate: [2] })).toThrow();
  });

  it("applies map_objects changes and reports the changed tiles and firms", () => {
    const m = mapFromJson(fixture());
    const built = applyMapObjects(m, {
      map_rev: 4,
      towns: fixture().towns,
      firms: [...fixture().firms, { id: 1, x: 0, y: 2, type_id: 2, owner: 1 }],
      changes: [[8, FIRM, 1, 0]],
    });
    expect(built).toEqual({ tiles: [8], firms: true });
    expect([m.kind[8], m.ref[8], m.rev]).toEqual([FIRM, 1, 4]);
    expect(m.firms.map((f) => f.id)).toEqual([0, 1]);

    const spread = applyMapObjects(m, {
      map_rev: 5,
      towns: [{ ...fixture().towns[0], level: 2 }],
      firms: m.firms.map((f) => ({ id: f.id, x: f.x, y: f.y, type_id: f.type, owner: f.owner })),
      changes: [[3, TOWN, 0, 0x3004]],
    });
    expect(spread).toEqual({ tiles: [3], firms: false });
    expect(frameFor(m, 3, 0)).toBe("town_rural_4");
    expect(m.towns[0].level).toBe(2);
  });

  it("diffs full arrays when changes is null", () => {
    const m = mapFromJson(fixture());
    const j = fixture();
    j.kind[11] = TOWN;
    j.ref[11] = 0;
    j.town_kind[11] = 0x3005;
    const d = applyMapObjects(m, { ...j, map_rev: 9, changes: null });
    expect(d).toEqual({ tiles: [11], firms: false });
    expect(m.townKind[11]).toBe(0x3005);
  });
});

describe("chunk invalidation", () => {
  it("one changed tile rebuilds its chunk only, unless it borders another", () => {
    // 64 x 64 map, 16-tile chunks: tile (20, 20) is inside chunk (1, 1).
    expect(chunksForTiles([20 * 64 + 20], 64, 64, 16)).toEqual(new Set([chunkKey(1, 1)]));
    // Tile (16, 16) sits on a chunk corner, so its neighbours reach chunks (0..1, 0..1).
    expect(chunksForTiles([16 * 64 + 16], 64, 64, 16)).toEqual(
      new Set([chunkKey(0, 0), chunkKey(1, 0), chunkKey(0, 1), chunkKey(1, 1)]),
    );
    // The map edge clips neighbours.
    expect(chunksForTiles([0], 64, 64, 16)).toEqual(new Set([chunkKey(0, 0)]));
  });
});
