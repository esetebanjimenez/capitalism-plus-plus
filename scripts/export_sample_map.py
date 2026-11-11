"""Write the client's sample map: terrain, climate and firms from a seeded bread-chain scenario.

Format (little-endian): b"CPPM", u16 width, u16 height, then width*height bytes of
TileCategory, width*height bytes of climate (0 = poles .. 4 = equator), then u16 firm
count and per firm u16 x, u16 y, u8 firm type id, u8 owner corp id (255 = no owner),
then u16 town count and per town u16 x, u16 y, u8 town id, u8 level, u8 footprint radius,
u8 block level (radius and block level from the town_footprints table).
Then a b"TINF" section for the panels until the client runs the sim: u16 year, u8 month,
u8 day, f64 player cash, then per tile (row-major) width*height bytes each of soil,
rainfall and World.can_build (0/1), and width*height u32 World.land_value in dollars.
The firms are the player's bread chain plus one of every other firm type, split between
the player and two AI corporations, so every firm sprite and a few flags show. The
second town is raised to level 5 so the sample shows a 5x5 footprint as well as 3x3.
"""

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from capitalism.economy import CORP_AI
from capitalism.firms import FIRM_CLASSES
from capitalism.scenario import bread_town, build_bread_chain, find_site
from capitalism.tables import TOWN_FOOTPRINTS
from capitalism.town import population_for_level

SEED = 1


def tile_info(sim, player) -> bytes:
    world = sim.world
    cal = sim.calendar
    xy = [(x, y) for y in range(world.height) for x in range(world.width)]
    return (
        b"TINF"
        + struct.pack("<HBBd", cal.year, cal.month, cal.day, player.ledger.cash)
        + bytes(t.soil for t in world.tiles)
        + bytes(t.rainfall for t in world.tiles)
        + bytes(int(world.can_build(x, y)) for x, y in xy)
        + struct.pack(f"<{len(xy)}I", *(world.land_value(x, y) for x, y in xy))
    )


def main() -> None:
    sim, town = bread_town(SEED)
    big = sim.towns[1]
    big.population = population_for_level(5)
    big.level = 5
    build_bread_chain(sim, town)
    eco = sim.economy
    corps = [eco.corps[0], eco.add_corp("Rival A", CORP_AI), eco.add_corp("Rival B", CORP_AI)]
    have = {f.type_id for f in eco.firms if f is not None}
    for i, t in enumerate(sorted(set(FIRM_CLASSES) - have)):
        x, y = find_site(sim, town, town.level + 3)
        eco.build_firm(t, corps[i % len(corps)], x, y, town)
    world = sim.world
    kinds = bytes(int(t.kind) for t in world.tiles)
    climate = bytes(int(t.climate) for t in world.tiles)
    firms = [f for f in eco.firms if f is not None]
    body = b"".join(
        struct.pack("<HHBB", f.x, f.y, f.type_id, 255 if f.owner is None else f.owner.id)
        for f in firms
    )
    out = ROOT / "client/public/sample-map.bin"
    out.write_bytes(
        b"CPPM"
        + struct.pack("<HH", world.width, world.height)
        + kinds
        + climate
        + struct.pack("<H", len(firms))
        + body
        + struct.pack("<H", len(sim.towns))
        + b"".join(
            struct.pack(
                "<HHBBBB",
                t.x,
                t.y,
                t.id,
                t.level,
                TOWN_FOOTPRINTS[t.level].radius,
                TOWN_FOOTPRINTS[t.level].block_level,
            )
            for t in sim.towns
        )
        + tile_info(sim, corps[0])
    )
    print(f"wrote {out} ({world.width}x{world.height}, seed {SEED}, {len(firms)} firms)")
    for t in sim.towns:
        print(f"town {t.id} at {t.x},{t.y} level {t.level}")


if __name__ == "__main__":
    main()
