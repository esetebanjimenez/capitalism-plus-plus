"""Capitalism++ M2 terrain and coast tiles at 64 px: the high-density set (B+, same 48-colour palette).
Drawn natively at 64 px, not upscaled. Frame names match terrain.py exactly, so the renderer can swap
sheets by screen density. Original art drawn in code. Run via build64.py."""

import os, json, math, random
from PIL import Image, ImageDraw
import terrain as T

N = 64
PAL, H, C, CLIM = T.PAL, T.H, dict(T.C), T.CLIM
C.update(TROUGH="#122234", GLASS="#3b6db3")
HI = [
    "#f6ecd4",
    "#5f9e3a",
    "#58a327",
    "#51a724",
    "#51a724",
]  # light blade / leaf highlight per climate
for v in list(C.values()) + HI:
    assert v in PAL, v


def new(c):
    return Image.new("RGBA", (N, N), H(c) + (255,))


def px(im, x, y, c):
    if 0 <= x < N and 0 <= y < N:
        im.putpixel((x, y), H(c) + (255,))


def deep(v):
    im = new(C["NAVY"])
    r = random.Random(500 + v)
    for _ in range(6):  # long low swells with a dark trough under each
        x, y, L = r.randrange(2, 48), r.randrange(4, 60), r.randrange(7, 13)
        for i in range(L):
            dy = -1 if L // 3 <= i < 2 * L // 3 else 0
            px(im, x + i, y + dy, C["DEEP2"])
            px(im, x + i, y + dy + 1, C["TROUGH"])
    return im


def water(v):
    im = new(C["WATER"])
    r = random.Random(900 + v)
    for _ in range(9):  # wavelets: trough, foam crest, a lifted tip
        x, y, L = r.randrange(2, 52), r.randrange(3, 60), r.randrange(4, 8)
        for i in range(L):
            px(im, x + i, y + 1, C["DEEP2"])
            px(im, x + i, y, C["FOAM"])
        px(im, x + L, y - 1, C["FOAM"])
        px(im, x - 1, y + 1, C["DEEP2"])
    for _ in range(6):
        px(im, r.randrange(N), r.randrange(N), C["FOAM"])
    return im


def grass(v, cl):
    g, s, _, _ = CLIM[cl]
    im = new(g)
    r = random.Random(v * 7 + cl + 64)
    for _ in range(46):  # tufts: dark V with a light blade
        x, y = r.randrange(1, N - 1), r.randrange(2, N - 1)
        for dx, dy in ((0, 0), (-1, -1), (1, -1), (0, 1)):
            px(im, x + dx, y + dy, s)
        if r.random() < 0.4:
            px(im, x, y - 1, HI[cl])
    for _ in range(18):
        px(im, r.randrange(N), r.randrange(N), s)
    for _ in range(4):  # small flowers / pebbles
        x, y = r.randrange(2, N - 2), r.randrange(2, N - 2)
        c = C["CREAM"] if cl else C["SAND"]
        px(im, x, y, c)
        px(im, x + 1, y, C["SAND"] if cl else C["ROCK"])
    if cl == 3:  # dry patches
        for _ in range(6):
            x, y = r.randrange(2, 58), r.randrange(2, 60)
            for i in range(r.randrange(2, 5)):
                px(im, x + i, y, C["SANDD"])
            px(im, x + 1, y + 1, C["SANDD"])
    if cl == 0:  # snow drifts
        for _ in range(3):
            x, y = r.randrange(3, 54), r.randrange(3, 58)
            for i in range(6):
                px(im, x + i, y, C["SNOW"])
            for i in range(1, 4):
                px(im, x + i, y - 1, C["SNOW"])
    return im


def tree(im, x, y, s, cl, r):
    d = ImageDraw.Draw(im)
    _, mid, fl, can = CLIM[cl]
    d.ellipse([x + 3, y + 5, x + s + 3, y + s + 5], fill=H(fl))  # cast shadow
    bl = [(x, y, x + s, y + s)]
    for _ in range(4):  # leaf clumps on the rim
        a = r.uniform(0, 2 * math.pi)
        cx, cy = x + s / 2 + math.cos(a) * s * 0.34, y + s / 2 + math.sin(a) * s * 0.34
        k = s * 0.24
        bl.append((round(cx - k), round(cy - k), round(cx + k), round(cy + k)))
    for b_ in bl:
        d.ellipse(b_, fill=H(C["INK"]))
    for b_ in bl:
        d.ellipse((b_[0] + 1, b_[1] + 1, b_[2] - 1, b_[3] - 1), fill=H(can))
    d.ellipse(
        [x + 3, y + 3, x + s * 0.55, y + s * 0.55], fill=H(mid if cl else "#9ba99c")
    )  # lit side
    d.ellipse([x + 5, y + 5, x + s * 0.35, y + s * 0.35], fill=H(HI[cl] if cl else "#b6d0a8"))
    for p in ((6, 6), (7, 6), (6, 7)):
        px(im, x + p[0], y + p[1], HI[cl])
    if cl == 0:
        for i in range(-2, 3):
            px(im, x + s // 2 + i, y + 3, C["SNOW"])
        px(im, x + s // 2, y + 2, C["SNOW"])


LAYS = [
    [(1, 1, 13), (16, 0, 14), (7, 13, 15), (0, 20, 10), (20, 17, 11)],
    [(0, 0, 12), (13, 3, 16), (2, 15, 14), (18, 20, 12)],
    [(2, 2, 12), (17, 1, 12), (9, 12, 13), (1, 19, 11), (20, 18, 11)],
    [(4, 0, 14), (1, 14, 12), (16, 10, 15), (10, 22, 9)],
]


def forest(v, cl):
    im = new(CLIM[cl][2])
    r = random.Random(300 + v * 5 + cl)
    d = ImageDraw.Draw(im)
    for _ in range(30):
        px(im, r.randrange(N), r.randrange(N), CLIM[cl][3])  # floor litter
    for x, y, s in LAYS[v]:
        tree(im, x * 2, y * 2, s * 2, cl, r)
    return im


def hill(v, cl):
    im = grass(v + 20, cl)
    d = ImageDraw.Draw(im)
    r = random.Random(v + 40)
    for x, y, s in [(6, 12, 44), (24, 4, 32)] if v % 2 == 0 else [(4, 20, 40), (28, 12, 30)]:
        top = (x + s // 2, y)
        pts = [(x, y + s), top, (x + s, y + s)]
        d.polygon(
            [(x + 4, y + s + 3), (top[0] + 4, y + 6), (x + s + 4, y + s + 3)], fill=H(CLIM[cl][3])
        )  # ground shadow
        d.polygon(pts, fill=H(C["ROCK"]), outline=H(C["INK"]))
        d.polygon([top, (x + s, y + s), (top[0] + 4, y + s)], fill=H(C["ROCKD"]))  # shaded face
        for i in range(3):  # ridge strata
            yy = y + s * (i + 2) // 5
            xx = x + (yy - y) // 2
            d.line([(xx + 2, yy), (top[0] - 2, yy + 2)], fill=H(C["ROCKD"]))
        for _ in range(6):
            px(im, r.randrange(x + 4, x + s - 4), r.randrange(y + s - 6, y + s - 1), C["ROCKD"])
        px(im, top[0] - 1, y + 3, C["PAVE"] if "PAVE" in C else "#b8bcc0")
        if cl <= 1:
            d.polygon(
                [
                    top,
                    (top[0] - 6, y + 10),
                    (top[0] - 2, y + 8),
                    (top[0] + 1, y + 11),
                    (top[0] + 6, y + 10),
                ],
                fill=H(C["SNOW"]),
            )
    return im


# ---- coast: smooth deterministic 64-sample profile, ends fixed at 8 so neighbours always meet ----
def _prof():
    p = []
    for x in range(N):
        t = x / 2
        i = int(t)
        f = t - i
        a = T.PROF[i]
        b = T.PROF[min(31, i + 1)]
        p.append(round(2 * (a + (b - a) * f)))
    p[0] = p[1] = p[-1] = p[-2] = 8
    return p


PROF = _prof()


def coast(mask, diag=0):
    """mask bits N=1 E=2 S=4 W=8: land on that side. diag bits NE=1 SE=2 SW=4 NW=8: land only on that corner."""
    im = water(0)
    a = im.load()
    r = random.Random(mask * 16 + diag)

    def depth(x, y):
        ds = []
        if mask & 1:
            ds.append(PROF[x] - y)
        if mask & 4:
            ds.append(PROF[N - 1 - x] - (N - 1 - y))
        if mask & 8:
            ds.append(PROF[y] - x)
        if mask & 2:
            ds.append(PROF[N - 1 - y] - (N - 1 - x))
        for b, (cx, cy) in ((1, (N - 1, 0)), (2, (N - 1, N - 1)), (4, (0, N - 1)), (8, (0, 0))):
            if diag & b:
                ds.append(10.5 - math.hypot(x - cx, y - cy))
        return max(ds) if ds else -99

    for y in range(N):
        for x in range(N):
            k = depth(x, y)
            if k > 3:
                a[x, y] = H(C["SAND"]) + (255,)
            elif k > 0:
                a[x, y] = H(C["SANDD"]) + (255,)  # wet sand
            elif k > -2:
                a[x, y] = H(C["FOAM"]) + (255,)  # surf line, 2 px
            elif k == -5 and (x + y) % 16 < 9:
                a[x, y] = H(C["FOAM"]) + (255,)  # second, broken wave
            elif k == -6 and (x + y) % 16 < 9:
                a[x, y] = H(C["DEEP2"]) + (255,)
    for _ in range(10):  # shells and pebbles on the dry sand
        x, y = r.randrange(N), r.randrange(N)
        if depth(x, y) > 5:
            a[x, y] = H(C["SANDD"] if r.random() < 0.6 else C["CREAM"]) + (255,)
    return im


def shelf(side):
    im = deep(1)
    a = im.load()
    for y in range(N):
        for x in range(N):
            t = {"N": y, "E": N - 1 - x, "S": N - 1 - y, "W": x}[side]
            p = PROF[{"N": x, "E": y, "S": N - 1 - x, "W": N - 1 - y}[side]]
            if t < p + 2:
                a[x, y] = H(C["WATER"]) + (255,)
            elif t < p + 4 and (x + y) % 2 == 0:
                a[x, y] = H(C["WATER"]) + (255,)  # dithered drop-off
            elif t < p + 5:
                a[x, y] = H(C["DEEP2"]) + (255,)
    return im


B8 = [
    [0, 32, 8, 40, 2, 34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37],
    [63, 31, 55, 23, 61, 29, 53, 21],
]


def climate_edge(im, a, b):
    """Dithered band edge: climate a at the top, fading to climate b at the bottom, along a wavy front."""
    m = {H(ca): H(cb) for ca, cb in reversed(list(zip(CLIM[a], CLIM[b])))}
    m.update({H(HI[a]): H(HI[b])})
    if a == 0:
        m.update({H(C["SAND"]): H(C["CREAM"]), H(C["SNOW"]): H(HI[b])})
    out = im.copy()
    p = out.load()
    k = 1 + (
        sum(im.convert("RGB").getpixel((x, x))[0] for x in range(N)) % 2
    )  # 1 or 2 waves, seamless across tiles
    for y in range(N):
        for x in range(N):
            t = min(1, max(0, (y - 12 - 8 * math.sin(2 * math.pi * k * x / N)) / 40))
            if (B8[y % 8][x % 8] + 0.5) / 64 < t:
                c = p[x, y][:3]
                if c in m:
                    p[x, y] = m[c] + (255,)
    return out


def build():
    fr = {}
    for v in range(3):
        fr[f"deep_{v}"] = deep(v)
        fr[f"water_{v}"] = water(v)
    for cl in range(5):
        for v in range(4):
            fr[f"grass_c{cl}_{v}"] = grass(v, cl)
            fr[f"forest_c{cl}_{v}"] = forest(v, cl)
        for v in range(2):
            fr[f"hill_c{cl}_{v}"] = hill(v, cl)
    for a in range(5):
        for b in (a - 1, a + 1):
            if 0 <= b < 5:
                for v in range(4):
                    fr[f"grass_c{a}c{b}_{v}"] = climate_edge(fr[f"grass_c{a}_{v}"], a, b)
                    fr[f"forest_c{a}c{b}_{v}"] = climate_edge(fr[f"forest_c{a}_{v}"], a, b)
                for v in range(2):
                    fr[f"hill_c{a}c{b}_{v}"] = climate_edge(fr[f"hill_c{a}_{v}"], a, b)
    for m in range(1, 16):
        fr[f"coast_{m:02d}"] = coast(m)
    for d, n in ((1, "ne"), (2, "se"), (4, "sw"), (8, "nw")):
        fr[f"coast_corner_{n}"] = coast(0, d)
    for s in "NESW":
        fr[f"shelf_{s.lower()}"] = shelf(s)
    return fr
