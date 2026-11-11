"""Write the client's sample map: terrain kind and climate per tile from a seeded world.

Format (little-endian): b"CPPM", u16 width, u16 height, then width*height bytes of
TileCategory, then width*height bytes of climate (0 = poles .. 4 = equator).
"""

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from capitalism.rng import Rng
from capitalism.world import World

SEED = 1


def main() -> None:
    world = World.generate(Rng(SEED))
    kinds = bytes(int(t.kind) for t in world.tiles)
    climate = bytes(int(t.climate) for t in world.tiles)
    out = ROOT / "client/public/sample-map.bin"
    out.write_bytes(b"CPPM" + struct.pack("<HH", world.width, world.height) + kinds + climate)
    print(f"wrote {out} ({world.width}x{world.height}, seed {SEED})")


if __name__ == "__main__":
    main()
