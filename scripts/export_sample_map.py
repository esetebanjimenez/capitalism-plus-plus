"""Write the client's sample map: terrain, climate and firms from a seeded bread-chain scenario.

Format (little-endian): b"CPPM", u16 width, u16 height, then width*height bytes of
TileCategory, width*height bytes of climate (0 = poles .. 4 = equator), then u16 firm
count and per firm u16 x, u16 y, u8 firm type id, u8 owner corp id (255 = no owner).
The firms are the player's bread chain plus one of every other firm type, split between
the player and two AI corporations, so every firm sprite and a few flags show.
"""

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from capitalism.economy import CORP_AI
from capitalism.firms import FIRM_CLASSES
from capitalism.scenario import bread_town, build_bread_chain, find_site

SEED = 1


def main() -> None:
    sim, town = bread_town(SEED)
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
    )
    print(f"wrote {out} ({world.width}x{world.height}, seed {SEED}, {len(firms)} firms)")
    print(f"town at {town.x},{town.y}")


if __name__ == "__main__":
    main()
