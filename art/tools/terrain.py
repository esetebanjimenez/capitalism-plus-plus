"""Capitalism++ M2 terrain and coast tiles, concept B+ (32 px, 48-colour palette).
Original art drawn in code. Run: python3 terrain.py OUTDIR"""

import sys, os, json, random
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PAL = json.load(open(os.path.join(HERE, "palette.json")))
H = lambda s: tuple(int(s[i : i + 2], 16) for i in (1, 3, 5))
assert len(PAL) == 48
C = dict(
    INK="#22262e",
    NAVY="#14234a",
    DEEP2="#133959",
    WATER="#2a7f9e",
    FOAM="#9fd3d8",
    SAND="#e8d6a0",
    SANDD="#d4b27f",
    FOREST="#2f5e2a",
    FOREST2="#20554b",
    CREAM="#f6ecd4",
    ROCK="#868a84",
    ROCKD="#58605a",
    SNOW="#f6ecd4",
)
# grass main / speckle / forest floor per climate (0 = poles .. 4 = equator, world.py)
CLIM = [
    ("#b6d0a8", "#9ba99c", "#9ba99c", "#306f46"),
    ("#4d8333", "#526e39", "#526e39", "#20554b"),
    ("#5f9e3a", "#4a8030", "#4a8030", "#2f5e2a"),
    ("#58a822", "#4ea026", "#4d8333", "#2f5e2a"),
    ("#3aa05a", "#1c8457", "#306f46", "#1c8457"),
]
for v in list(C.values()) + [c for t in CLIM for c in t]:
    assert v in PAL, v


def new(c):
    return Image.new("RGBA", (32, 32), H(c) + (255,))


def px(im, x, y, c):
    if 0 <= x < 32 and 0 <= y < 32:
        im.putpixel((x, y), H(c) + (255,))


def deep(v):
    im = new(C["NAVY"])
    r = random.Random(500 + v)
    for _ in range(3):
        x, y = r.randrange(2, 25), r.randrange(2, 30)
        for i in range(5):
            px(im, x + i, y, C["DEEP2"])
    return im


def water(v):
    im = new(C["WATER"])
    r = random.Random(900 + v)
    for _ in range(4):
        x, y = r.randrange(1, 24), r.randrange(2, 30)
        for i in range(4):
            px(im, x + i, y, C["FOAM"])
        px(im, x + 4, y - 1, C["FOAM"])
    return im


def grass(v, cl):
    g, s, _, _ = CLIM[cl]
    im = new(g)
    r = random.Random(v * 7 + cl)
    for _ in range(14):
        x, y = r.randrange(1, 31), r.randrange(2, 31)
        for dx, dy in ((0, 0), (-1, -1), (1, -1)):
            px(im, x + dx, y + dy, s)
    for _ in range(2):
        px(im, r.randrange(2, 30), r.randrange(2, 30), C["CREAM"] if cl else C["SAND"])
    if cl == 3:
        for _ in range(4):
            x, y = r.randrange(2, 28), r.randrange(2, 30)
            px(im, x, y, C["SANDD"])
            px(im, x + 1, y, C["SANDD"])
    return im


def tree(im, x, y, s, cl):
    d = ImageDraw.Draw(im)
    _, _, fl, can = CLIM[cl]
    d.ellipse([x + 2, y + 3, x + s + 2, y + s + 3], fill=H(fl))
    d.ellipse([x, y, x + s, y + s], fill=H(can), outline=H(C["INK"]))
    hi = CLIM[cl][0]
    d.ellipse(
        [x + 2, y + 2, x + s // 2 + 1, y + s // 2 + 1], fill=H(CLIM[cl][1] if cl else "#9ba99c")
    )
    for p in ((3, 3), (4, 3), (3, 4)):
        px(im, x + p[0], y + p[1], hi)
    if cl == 0:
        px(im, x + s // 2, y + 2, C["SNOW"])


LAYS = [
    [(1, 1, 13), (16, 0, 14), (7, 13, 15), (0, 20, 10), (20, 17, 11)],
    [(0, 0, 12), (13, 3, 16), (2, 15, 14), (18, 20, 12)],
    [(2, 2, 12), (17, 1, 12), (9, 12, 13), (1, 19, 11), (20, 18, 11)],
    [(4, 0, 14), (1, 14, 12), (16, 10, 15), (10, 22, 9)],
]


def forest(v, cl):
    im = new(CLIM[cl][2])
    for x, y, s in LAYS[v]:
        tree(im, x, y, s, cl)
    return im


def hill(v, cl):  # rocky hill variant of FOREST_HILL
    im = grass(v + 20, cl)
    d = ImageDraw.Draw(im)
    r = random.Random(v + 40)
    for x, y, s in [(3, 6, 22), (12, 2, 16)] if v % 2 == 0 else [(2, 10, 20), (14, 6, 15)]:
        pts = [(x, y + s), (x + s // 2, y), (x + s, y + s)]
        d.polygon(pts, fill=H(C["ROCK"]), outline=H(C["INK"]))
        d.polygon([(x + s // 2, y), (x + s, y + s), (x + s // 2 + 2, y + s)], fill=H(C["ROCKD"]))
        if cl <= 1:
            d.polygon(
                [(x + s // 2, y), (x + s // 2 - 3, y + 5), (x + s // 2 + 3, y + 5)],
                fill=H(C["SNOW"]),
            )
    return im


# ---- coast: deterministic edge profile so neighbours always meet ----
PROF = [
    4,
    4,
    5,
    5,
    5,
    4,
    3,
    3,
    3,
    4,
    4,
    5,
    6,
    6,
    5,
    4,
    4,
    4,
    5,
    5,
    4,
    3,
    3,
    3,
    4,
    5,
    5,
    5,
    4,
    4,
    4,
    4,
]  # sand depth, symmetric ends = 4


def coast(mask, diag=0, deep_base=False):
    """mask bits N=1 E=2 S=4 W=8: land on that side. diag bits NE=1 SE=2 SW=4 NW=8: land only on that corner."""
    im = deep(0) if deep_base else water(0)
    a = im.load()

    def depth(x, y):
        ds = []
        if mask & 1:
            ds.append(PROF[x] - y)
        if mask & 4:
            ds.append(PROF[31 - x] - (31 - y))
        if mask & 8:
            ds.append(PROF[y] - x)
        if mask & 2:
            ds.append(PROF[31 - y] - (31 - x))
        for b, (cx, cy) in ((1, (31, 0)), (2, (31, 31)), (4, (0, 31)), (8, (0, 0))):
            if diag & b:
                ds.append(5 - max(abs(x - cx), abs(y - cy)))
        return max(ds) if ds else -99

    for y in range(32):
        for x in range(32):
            k = depth(x, y)
            if k > 0:
                a[x, y] = H(C["SAND"] if k > 1 else C["SANDD"]) + (255,)
            elif k > -2:
                a[x, y] = H(C["FOAM"]) + (255,)
    return im


def shelf(side):  # deep ocean with shallow water on one side
    im = deep(1)
    a = im.load()
    for y in range(32):
        for x in range(32):
            t = {"N": y, "E": 31 - x, "S": 31 - y, "W": x}[side]
            p = PROF[{"N": x, "E": y, "S": 31 - x, "W": 31 - y}[side]]
            if t < p + 1:
                a[x, y] = H(C["WATER"]) + (255,)
            elif t == p + 1:
                a[x, y] = H(C["DEEP2"]) + (255,)
    return im


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def climate_edge(im, a, b):
    """Dithered band edge: the tile is climate a at the top and fades to climate b at the bottom."""
    m = {H(ca): H(cb) for ca, cb in reversed(list(zip(CLIM[a], CLIM[b])))}
    if a == 0:
        m.update({H(C["SAND"]): H(C["CREAM"])})
    out = im.copy()
    px_ = out.load()
    import math

    k = 1 + (
        sum(im.convert("RGB").getpixel((x, x))[0] for x in range(32)) % 2
    )  # 1 or 2 waves, seamless at x=0/32
    for y in range(32):
        for x in range(32):
            t = min(1, max(0, (y - 6 - 4 * math.sin(2 * math.pi * k * x / 32)) / 20))
            if (BAYER[y % 4][x % 4] + 0.5) / 16 < t:
                c = px_[x, y][:3]
                if c in m:
                    px_[x, y] = m[c] + (255,)
    return out


def build(out):
    os.makedirs(out, exist_ok=True)
    frames = {}

    def save(name, im):
        assert all(("#%02x%02x%02x" % c[1][:3]) in PAL for c in im.getcolors(4096)), name
        im.save(os.path.join(out, name + ".png"))
        frames[name] = im

    for v in range(3):
        save(f"deep_{v}", deep(v))
        save(f"water_{v}", water(v))
    for cl in range(5):
        for v in range(4):
            save(f"grass_c{cl}_{v}", grass(v, cl))
            save(f"forest_c{cl}_{v}", forest(v, cl))
        for v in range(2):
            save(f"hill_c{cl}_{v}", hill(v, cl))
    for a in range(5):
        for b in (a - 1, a + 1):
            if 0 <= b < 5:
                for v in range(4):
                    save(f"grass_c{a}c{b}_{v}", climate_edge(grass(v, a), a, b))
                    save(f"forest_c{a}c{b}_{v}", climate_edge(forest(v, a), a, b))
                for v in range(2):
                    save(f"hill_c{a}c{b}_{v}", climate_edge(hill(v, a), a, b))
    for m in range(1, 16):
        save(f"coast_{m:02d}", coast(m))
    for d, n in ((1, "ne"), (2, "se"), (4, "sw"), (8, "nw")):
        save(f"coast_corner_{n}", coast(0, d))
    for s in "NESW":
        save(f"shelf_{s.lower()}", shelf(s))
    return frames


if __name__ == "__main__":
    print(len(build(sys.argv[1] if len(sys.argv) > 1 else "out")), "tiles")
