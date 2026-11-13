"""#303: native town tile sets, drawn at 64 px with a 32 px fallback (same palette and style as town64/town).

Native kinds (docs/research/techspec.md "Town spread", gap audit T4; names corrected by Esteban, #311):
- town_urban_0..4  = kinds 0x3008..0x300c: the solid core inside the level radius and the 1-in-10
  corner tiles. Towers, mid-rise and shops on pavement.
- town_rural_0..7  = kinds 0x3000..0x3007: the ring scattered from level to level + 4, so rural always
  rings urban. Houses, gardens, farms and orchards on grass.
Variant index v = kind - 0x3008 (urban) or kind - 0x3000 (rural). Each tile stands alone (no road
autotiling), since native towns scatter single tiles over grass. Frames are appended after the existing
ones in both terrain atlases, so earlier frames keep their place."""

import random
from PIL import Image, ImageDraw
from terrain import H
import town64 as T64

C = T64.C


class Tile:
    def __init__(s, n, base):
        s.n = n
        s.k = n / 64
        s.im = Image.new("RGBA", (n, n), H(C[base]) + (255,))
        s.d = ImageDraw.Draw(s.im)

    def c(s, v):
        return int(v * s.k)

    def R(s, b, col, o=None):
        x0, y0, x1, y1 = [s.c(v) for v in b]
        s.d.rectangle(
            [x0, y0, max(x0, x1), max(y0, y1)], fill=H(C[col]), outline=H(C[o]) if o else None
        )

    def E(s, b, col, o=None):
        s.d.ellipse([s.c(v) for v in b], fill=H(C[col]), outline=H(C[o]) if o else None)

    def P(s, x, y, col):
        x, y = s.c(x), s.c(y)
        if 0 <= x < s.n and 0 <= y < s.n:
            s.im.putpixel((x, y), H(C[col]) + (255,))

    def grain(s, seed, col, count, hi=None):
        r = random.Random(seed)
        for _ in range(int(count * s.k)):
            x, y = r.randrange(s.n), r.randrange(s.n)
            s.im.putpixel((x, y), H(C[col]) + (255,))
            if hi and r.random() < 0.3 and y:
                s.im.putpixel((x, y - 1), H(C[hi]) + (255,))

    def pave_grid(s):
        step = 8 if s.n == 64 else 8
        for i in range(0, s.n, step):
            s.d.line([(i, 0), (i, s.n - 1)], fill=H(C["PAVED"]))
            s.d.line([(0, i), (s.n - 1, i)], fill=H(C["PAVED"]))


# ---------- rural (0x3000..0x3007, outer ring) ----------
def house(t, x0, y0, x1, y1, roof, edge):
    """Pitched-roof house seen from above with a short front wall (64 px coords)."""
    big = t.n == 64
    t.R([x0, y1 - 2, x1, y1 + 3], edge, "INK")
    if big:
        for x in range(x0 + 3, x1 - 3, 5):
            t.R([x, y1, x + 1, y1 + 1], "WIN")
        t.R([(x0 + x1) // 2 - 1, y1, (x0 + x1) // 2 + 1, y1 + 2], "BROWND")
    mid = (y0 + y1) // 2 - 1
    t.R([x0, y0, x1, mid], roof, "INK")
    t.R([x0, mid, x1, y1 - 2], edge, "INK")
    if big:
        for y in range(y0 + 2, mid, 2):
            t.d.line([(x0 + 1, y), (x1 - 1, y)], fill=H(C[edge]))
        t.R([x1 - 6, y0 + 2, x1 - 4, y0 + 5], "GREYD", "INK")
    else:
        t.P(x0 + 6, y1 + 2, "WIN")


def tree(t, x, y, s):
    t.E([x + 2, y + 3, x + s + 2, y + s + 3], "GRASSD")
    t.E([x, y, x + s, y + s], "TREE", "INK")
    if t.n == 64:
        t.E([x + 3, y + 3, x + s * 0.55, y + s * 0.55], "GRASS")
        t.P(x + 5, y + 5, "HI")


ROOF = [("RED", "REDD"), ("TAN", "TAND"), ("BROWN", "BROWND"), ("GREY", "GREYD")]


def rural(v):
    def make(n):
        t = Tile(n, "GRASS")
        t.grain(300 + v, "GRASSD", 34, "HI")
        if v == 0:  # four houses around a cross of footpaths
            t.R([30, 0, 33, 63], "SAND")
            t.R([0, 30, 63, 33], "SAND")
            for i, (x0, y0) in enumerate(((4, 4), (37, 5), (5, 38), (38, 37))):
                house(t, x0, y0, x0 + 21, y0 + 17, *ROOF[i % 4])
        elif v == 1:  # three houses and a garden tree, lane along the bottom
            t.R([0, 52, 63, 57], "SAND")
            house(t, 4, 4, 27, 22, *ROOF[1])
            house(t, 36, 6, 58, 23, *ROOF[0])
            house(t, 34, 30, 57, 46, *ROOF[2])
            tree(t, 6, 29, 18)
        elif v == 2:  # two big houses with fenced gardens, lane down the middle
            t.R([29, 0, 34, 63], "SAND")
            house(t, 3, 6, 26, 26, *ROOF[0])
            house(t, 38, 34, 60, 54, *ROOF[3])
            for x in range(2, 27, 3):
                t.P(x, 52, "CREAM")
            for x in range(37, 62, 3):
                t.P(x, 14, "CREAM")
            tree(t, 6, 36, 15)
            tree(t, 42, 4, 14)
        elif v == 3:  # house with a vegetable garden and a shed
            house(t, 6, 4, 30, 22, *ROOF[1])
            t.R([36, 6, 58, 26], "BROWN", "INK")
            for y in range(9, 25, 4 if t.n == 64 else 6):
                t.R([38, y, 56, y + 1], "HI")
            house(t, 8, 36, 24, 48, *ROOF[3])
            t.R([0, 56, 63, 60], "SAND")
            tree(t, 38, 34, 16)
        elif v == 4:  # farmstead: barn and crop rows
            t.R([4, 6, 28, 30], "RED", "INK")
            t.R([4, 18, 28, 30], "REDD", "INK")
            t.R([12, 26, 20, 30], "BROWND", "INK")
            t.R([34, 4, 60, 58], "TAND", "INK")
            for x in range(37, 59, 4 if t.n == 64 else 6):
                t.R([x, 6, x + 1, 56], "GRASSD")
            house(t, 6, 38, 26, 54, *ROOF[2])
        elif v == 5:  # cottage by an orchard
            house(t, 4, 4, 26, 21, *ROOF[0])
            t.R([0, 30, 30, 34], "SAND")
            for yy in (4, 22, 40):
                for xx in (34, 48):
                    tree(t, xx, yy, 12)
            tree(t, 6, 42, 12)
            tree(t, 18, 46, 10)
        elif v == 6:  # two houses above a farm pond
            house(t, 4, 4, 26, 21, *ROOF[2])
            house(t, 36, 4, 58, 21, *ROOF[1])
            t.R([0, 30, 63, 33], "SAND")
            t.E([14, 38, 54, 60], "WATER", "INK")
            t.d.arc([t.c(20), t.c(42), t.c(40), t.c(54)], 200, 260, fill=H(C["WIN"]))
            for x, y in ((12, 50), (10, 44), (54, 50)):
                t.R([x, y, x, y + 4], "TREE")
        else:  # grain silos, a shed and hay bales by a track
            t.R([0, 28, 63, 33], "SAND")
            for x in (6, 20):
                t.E([x + 2, 6, x + 14, 18], "GRASSD")
                t.E([x, 4, x + 12, 16], "GREY", "INK")
                t.E([x + 3, 7, x + 9, 13], "PAVE")
            t.R([36, 4, 60, 22], "GREYD", "INK")
            t.R([36, 18, 60, 22], "GREY", "INK")
            t.R([44, 19, 52, 22], "DARK", "INK")
            for x, y in ((6, 42), (20, 46), (34, 40), (48, 48)):
                t.E([x, y, x + 9, y + 9], "TAN", "INK")
                t.E([x + 3, y + 3, x + 6, y + 6], "TAND")
        return t.im

    return make


# ---------- urban (0x3008..0x300c, core) ----------
def building(t, x0, y0, x1, y1, roof, edge, h, kind="plain"):
    """Flat-roof building: roof rect, thin front edge h px tall (= height), window dots on the edge."""
    big = t.n == 64
    t.R([x0 + 3, y0 + 3, x1 + 3, y1 + h + 3], "PAVED")
    t.R([x0, y1, x1, y1 + h], edge, "INK")
    if big:
        for yy in range(y1 + 2, y1 + h, 3):
            for x in range(x0 + 3, x1 - 2, 4):
                t.R([x, yy, x + 1, yy], "WIN")
    t.R([x0, y0, x1, y1], roof, "INK")
    if roof == "GLASS":
        for y in range(y0 + 6, y1, 8):
            t.d.line([(t.c(x0) + 1, t.c(y)), (t.c(x1) - 1, t.c(y))], fill=H(C["GLASSD"]))
        for x in range(x0 + 10, x1, 12):
            t.d.line([(t.c(x), t.c(y0) + 1), (t.c(x), t.c(y1) - 1)], fill=H(C["GLASSD"]))
    elif big:
        t.R([x0 + 4, y0 + 4, x0 + 10, y0 + 9], "PAVE", "INK")
        t.R([x1 - 9, y1 - 8, x1 - 4, y1 - 4], "GREYD", "INK")
    if kind == "heli":
        t.E(
            [(x0 + x1) / 2 - 8, (y0 + y1) / 2 - 8, (x0 + x1) / 2 + 8, (y0 + y1) / 2 + 8],
            "GREYD",
            "CREAM",
        )
        if big:
            cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
            t.d.line([(cx - 3, cy - 4), (cx - 3, cy + 4)], fill=H(C["CREAM"]))
            t.d.line([(cx + 3, cy - 4), (cx + 3, cy + 4)], fill=H(C["CREAM"]))
            t.d.line([(cx - 3, cy), (cx + 3, cy)], fill=H(C["CREAM"]))
    if kind == "mast":
        t.R([x1 - 10, y0 + 3, x1 - 9, y0 + 16], "INK")
        t.P(x1 - 10, y0 + 2, "RED")


def parking(t, x0, y0, x1, y1):
    t.R([x0, y0, x1, y1], "ASPH", "INK")
    for x in range(x0 + 6, x1 - 2, 6):
        t.R([x, y0 + 2, x, y0 + 8], "CREAM")
        t.R([x, y1 - 8, x, y1 - 2], "CREAM")
    r = random.Random(x0 * 7 + y0)
    for x in range(x0 + 2, x1 - 5, 6):
        if r.random() < 0.5:
            t.R([x + 1, y0 + 3, x + 4, y0 + 7], r.choice(["RED", "GLASS", "CREAM", "GREY"]), "INK")


def urban(v):
    def make(n):
        t = Tile(n, "PAVE")
        t.pave_grid()
        if v == 0:  # glass tower
            building(t, 10, 4, 53, 45, "GLASS", "GLASSD", 8)
        elif v == 1:  # grey tower with helipad
            building(t, 10, 4, 53, 45, "GREY", "GREYD", 8, "heli")
        elif v == 2:  # brick mid-rise with a radio mast
            building(t, 6, 6, 57, 51, "BROWN", "BROWND", 4, "mast")
        elif v == 3:  # shop row with awnings over a car park
            building(t, 4, 4, 58, 24, "TAN", "TAND", 4)
            for x in range(6, 56, 8):
                t.R([x, 29, x + 6, 31], "RED" if (x // 8) % 2 else "CREAM", "INK")
            parking(t, 4, 38, 59, 59)
        else:  # glass offices and a brick annex
            building(t, 4, 4, 34, 52, "GLASS", "GLASSD", 8)
            building(t, 40, 20, 59, 48, "BROWN", "BROWND", 4)
        return t.im

    return make


RURAL = 8
URBAN = 5


def frames(n):
    """In native kind order: rural 0x3000..0x3007, then urban 0x3008..0x300c."""
    f = {}
    for v in range(RURAL):
        f[f"town_rural_{v}"] = rural(v)(n)
    for v in range(URBAN):
        f[f"town_urban_{v}"] = urban(v)(n)
    return f


def preview():
    """docs/art/m2-town-native-preview.png: both sets at 64 px and 32 px (2x), then a sample native spread."""
    from PIL import ImageFont
    import terrain64

    f = ImageFont.load_default()
    fr64, fr32 = frames(64), frames(32)
    names = list(fr64)
    W = 16 + len(names) * 68
    grid, gx, gy = 13, 11, 11
    S = Image.new("RGBA", (W, 200 + gy * 64 + 20), H("#313944") + (255,))
    d = ImageDraw.Draw(S)
    d.text(
        (8, 4),
        "Capitalism++ #303: rural 0x3000-7 (left, outer ring) and urban 0x3008-c (right, core)",
        fill="white",
        font=f,
    )
    for i, n in enumerate(names):
        x = 12 + i * 68
        S.alpha_composite(fr64[n], (x, 20))
        S.alpha_composite(fr32[n].resize((64, 64), 0), (x, 90))
        d.text((x, 158), n.replace("town_", ""), fill="white", font=f)
    d.text(
        (8, 176),
        "Sample spread, level 2: urban core within 2 tiles, rural scattered out to 6",
        fill="white",
        font=f,
    )
    r = random.Random(7)
    grass = terrain64.build()
    g = [k for k in grass if k.startswith("grass_c2_")] or [next(iter(grass))]
    cx, cy = gx // 2, gy // 2
    for y in range(gy):
        for x in range(gx):
            dist = max(abs(x - cx), abs(y - cy))
            if dist < 2:
                im = fr64[f"town_urban_{r.randrange(URBAN)}"]
            elif dist < 6 and r.random() < 0.45 - dist * 0.05:
                im = fr64[f"town_rural_{r.randrange(RURAL)}"]
            else:
                im = grass[g[r.randrange(len(g))]]
            S.alpha_composite(im, (12 + x * 64, 196 + y * 64))
    S.convert("RGB").save("../../docs/art/m2-town-native-preview.png")


if __name__ == "__main__":
    import os

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    preview()
