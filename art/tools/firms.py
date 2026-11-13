"""Capitalism++ M2 firm sprites, concept B+ (32 px, 48-colour palette). Original art, drawn pixel by pixel
in code: roof seen from above plus a thin front edge (south wall). Transparent around the lot so the
terrain tile shows through. Owner flags are separate overlays (flag_00..11), drawn at the top-right."""

import random
from PIL import Image, ImageDraw
from terrain import PAL, H

C = dict(
    INK="#22262e",
    PAVE="#b8bcc0",
    PAVED="#9ba99c",
    ASPH="#7a8088",
    ASPHD="#58605a",
    GREY="#868a84",
    CREAM="#f6ecd4",
    WHITE="#f6ecd4",
    SAND="#e8d6a0",
    TAN="#d4b27f",
    TAND="#b08451",
    BROWN="#8a5a32",
    BROWND="#53341b",
    DIRT="#7f5226",
    RUST="#a55922",
    RED="#c8402e",
    REDD="#ad2816",
    MAROON="#712b19",
    ORANGE="#e8742a",
    AMBER="#e0862f",
    GREEN="#3aa05a",
    GRASS="#5f9e3a",
    GRASSD="#4a8030",
    TREE="#2f5e2a",
    CROP="#58a822",
    CROPD="#4d8333",
    GLASS="#3b6db3",
    GLASSD="#0d5199",
    WIN="#9fd3d8",
    WATER="#2a7f9e",
    DEEP="#133959",
    NAVY="#14234a",
    DARK="#313944",
    SMOKE="#9ba99c",
)
for v in C.values():
    assert v in PAL, v
FLAGS = [
    "#e8742a",
    "#c8402e",
    "#3b6db3",
    "#3aa05a",
    "#f6ecd4",
    "#14234a",
    "#e8d6a0",
    "#712b19",
    "#9fd3d8",
    "#58a822",
    "#868a84",
    "#0d5199",
]
for v in FLAGS:
    assert v in PAL, v


class S:
    def __init__(s):
        s.im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        s.d = ImageDraw.Draw(s.im)

    def R(s, b, c, o=None):
        s.d.rectangle(b, fill=H(C[c]), outline=H(C[o]) if o else None)

    def E(s, b, c, o=None):
        s.d.ellipse(b, fill=H(C[c]), outline=H(C[o]) if o else None)

    def L(s, p, c, w=1):
        s.d.line(p, fill=H(C[c]), width=w)

    def P(s, x, y, c):
        if 0 <= x < 32 and 0 <= y < 32:
            s.im.putpixel((x, y), H(C[c]) + (255,))

    def lot(s, c, b=(1, 2, 30, 30), speck=None, seed=0):
        s.R(b, c)
        if speck:
            r = random.Random(seed)
            for _ in range(12):
                s.P(r.randrange(b[0] + 1, b[2]), r.randrange(b[1] + 1, b[3]), speck)

    def bld(s, x0, y0, x1, y1, roof, wall, e=3, win="WIN", door=None, roofd=None):
        """Roof [x0..x1, y0..y1-e], front edge e px tall below it, ink outline."""
        s.R([x0 + 1, y0 + 1, x1 + 1, y1 + 1], "DARK")  # 1 px shadow to the south-east
        s.R([x0, y1 - e, x1, y1], wall, "INK")
        s.R([x0, y0, x1, y1 - e], roof, "INK")
        if roofd:
            s.L([(x0 + 1, y1 - e - 1), (x1 - 1, y1 - e - 1)], roofd)
        if e >= 3 and win:
            for x in range(x0 + 2, x1 - 1, 3):
                s.P(x, y1 - e + 1 + (e - 2) // 2, win)
        if door is not None:
            s.R([door, y1 - e + 1, door + 2, y1 - 1], "DARK")


def dept():
    s = S()
    s.lot("ASPH", (1, 1, 30, 30))
    for x in range(4, 30, 5):
        s.L([(x, 24), (x, 29)], "PAVE")
    s.bld(2, 2, 29, 20, "TAN", "CREAM", e=4, door=14, roofd="TAND")
    for x in range(3, 29, 2):
        s.P(x, 17, "RED")
        s.P(x + 1, 17, "CREAM")  # awning
    s.L([(3, 16), (28, 16)], "REDD")
    s.R([10, 6, 21, 10], "RED", "INK")
    s.L([(12, 8), (19, 8)], "CREAM")
    s.R([4, 5, 7, 8], "PAVE", "INK")
    s.R([24, 11, 27, 14], "PAVE", "INK")
    return s.im


def factory():
    s = S()
    s.lot("PAVED", (1, 1, 30, 30), "ASPH", 2)
    s.bld(2, 8, 25, 27, "GREY", "PAVE", e=4, door=11)
    for y in (9, 13, 17):  # sawtooth: dark glass strip under each ridge
        s.L([(3, y), (24, y)], "INK")
        s.L([(3, y + 1), (24, y + 1)], "GLASS")
        s.L([(3, y + 2), (24, y + 2)], "PAVE")
    s.R([26, 4, 29, 27], "ASPHD", "INK")
    s.R([27, 2, 28, 4], "RUST", "INK")  # chimney stack
    for x, y in ((26, 0), (28, 1), (24, 1)):
        s.P(x, y, "SMOKE")
    s.E([20, 1, 24, 5], "SMOKE")
    s.R([3, 28, 9, 30], "ORANGE", "INK")  # crate
    return s.im


def rnd():
    s = S()
    s.lot("GRASS", (1, 1, 30, 30), "GRASSD", 3)
    s.L([(15, 24), (15, 30)], "PAVE", 3)
    s.bld(2, 4, 22, 24, "GLASS", "PAVE", e=3, door=14)
    for y in range(7, 21, 4):
        s.L([(3, y), (21, y)], "GLASSD")
    for x in (9, 16):
        s.L([(x, 5), (x, 20)], "GLASSD")
    s.E([21, 3, 30, 12], "CREAM", "INK")
    s.E([23, 5, 28, 10], "PAVE")
    s.L([(25, 7), (28, 4)], "INK")
    s.P(28, 4, "RED")  # dish
    s.E([24, 20, 29, 25], "TREE", "INK")
    return s.im


def farm():
    s = S()
    s.lot("DIRT", (1, 1, 30, 30))
    for y in range(2, 30, 3):
        s.L([(1, y), (30, y)], "CROP")
        s.L([(1, y + 1), (30, y + 1)], "CROPD")
    s.R([2, 14, 22, 29], "TAN")
    s.bld(3, 15, 16, 28, "RED", "MAROON", e=4, win=None)
    s.L([(4, 19), (15, 19)], "REDD")
    s.L([(4, 20), (15, 20)], "CREAM")
    s.R([8, 25, 11, 28], "CREAM", "INK")
    s.L([(8, 25), (11, 28)], "INK")
    s.L([(11, 25), (8, 28)], "INK")
    s.E([18, 16, 24, 22], "PAVE", "INK")
    s.E([20, 18, 22, 20], "GREY")
    s.R([18, 20, 24, 27], "PAVED", "INK")  # silo
    s.R([19, 24, 23, 26], "PAVE")
    return s.im


def logging():
    s = S()
    s.lot("DIRT", (1, 1, 30, 30), "BROWND", 5)
    for x, y in ((2, 2), (24, 3), (26, 22), (3, 24)):
        s.E([x, y, x + 4, y + 4], "TAN", "BROWND")
        s.P(x + 2, y + 2, "BROWN")  # stumps
    s.bld(9, 3, 22, 15, "BROWND", "BROWN", e=3, door=14)
    s.L([(9, 8), (22, 8)], "MAROON")
    for i, y in enumerate((19, 22, 25)):  # log pile, cut ends showing
        for x in range(8 - i % 2 * 2, 24, 4):
            s.E([x, y, x + 3, y + 3], "TAN", "BROWND")
            s.P(x + 1, y + 1, "TAND")
    s.R([24, 12, 29, 18], "ORANGE", "INK")
    s.R([25, 13, 28, 15], "WIN")  # skidder
    return s.im


def mine():
    s = S()
    s.lot("TAND", (1, 1, 30, 30), "DIRT", 6)
    s.E([3, 10, 21, 28], "DIRT", "INK")
    s.E([6, 13, 18, 25], "BROWND")
    s.E([9, 16, 15, 22], "DARK", "INK")
    for x0, x1 in ((22, 22), (28, 28)):
        s.L([(x0, 3), (x0, 14)], "INK")  # headframe
    s.L([(22, 3), (28, 3)], "INK")
    s.L([(22, 8), (28, 8)], "INK")
    s.L([(22, 3), (28, 14)], "INK")
    s.L([(28, 3), (22, 14)], "INK")
    s.E([23, 1, 27, 5], "GREY", "INK")
    s.P(25, 3, "INK")
    s.L([(17, 22), (29, 22)], "ASPHD")
    s.L([(17, 25), (29, 25)], "ASPHD")
    for x in range(18, 30, 3):
        s.L([(x, 22), (x, 25)], "BROWND")
    s.R([23, 20, 28, 24], "RUST", "INK")
    s.R([24, 20, 27, 21], "GREY")  # ore cart
    return s.im


def oil():
    s = S()
    s.lot("TAND", (1, 1, 30, 30), "DIRT", 7)
    s.R([3, 20, 15, 27], "PAVED", "INK")
    s.L([(5, 26), (9, 15)], "INK", 2)
    s.L([(13, 26), (9, 15)], "INK", 2)  # pump jack A-frame
    s.L([(2, 14), (17, 12)], "ORANGE", 3)
    s.L([(2, 13), (17, 11)], "INK")
    s.R([0, 13, 3, 19], "ORANGE", "INK")
    s.L([(2, 18), (2, 25)], "INK")
    s.E([14, 7, 20, 13], "DARK", "INK")
    s.L([(17, 10), (17, 25)], "INK")
    s.E([19, 15, 29, 25], "CREAM", "INK")
    s.E([21, 17, 27, 23], "PAVE")
    s.L([(20, 22), (28, 22)], "INK")  # tank
    s.R([19, 22, 29, 27], "PAVE", "INK")
    s.L([(20, 24), (28, 24)], "PAVED")
    s.L([(5, 29), (28, 29)], "DARK")
    return s.im


def office(roof, roofd, sym):
    s = S()
    s.lot("GRASS", (1, 1, 30, 30), "GRASSD", 8)
    s.L([(15, 25), (15, 30)], "PAVE", 3)
    s.R([2, 25, 10, 30], "ASPH")
    s.L([(5, 26), (5, 30)], "PAVE")
    s.bld(3, 3, 28, 24, roof, "PAVE", e=3, door=14, roofd=roofd)
    s.R([5, 5, 8, 8], "PAVE", "INK")
    s.E([24, 26, 29, 30], "TREE", "INK")
    sym(s)
    return s.im


def sym_monitor(s):
    s.R([10, 6, 21, 15], "DARK", "INK")
    s.R([11, 7, 20, 14], "GLASS")
    s.L([(12, 9), (16, 9)], "WIN")
    s.L([(12, 11), (18, 11)], "WIN")
    s.R([14, 16, 17, 17], "INK")
    s.L([(12, 18), (19, 18)], "INK")


def sym_disc(s):
    s.E([9, 6, 21, 18], "PAVE", "INK")
    s.E([12, 9, 18, 15], "WIN")
    s.E([14, 11, 16, 13], "INK")
    s.P(11, 8, "CREAM")
    s.P(10, 10, "CREAM")


def restaurant():
    s = S()
    s.lot("PAVE", (1, 1, 30, 30), "PAVED", 9)
    s.bld(2, 2, 29, 16, "MAROON", "CREAM", e=3, door=14, roofd="BROWND")
    for x in range(3, 29, 2):
        s.P(x, 13, "RED")
        s.P(x + 1, 13, "CREAM")
    s.R([6, 4, 10, 9], "PAVE", "INK")
    s.R([22, 4, 25, 7], "GREY", "INK")
    s.P(23, 3, "SMOKE")
    for cx, cy, c in (
        (7, 23, "ORANGE"),
        (16, 25, "GREEN"),
        (25, 22, "ORANGE"),
    ):  # parasols over tables
        s.E([cx - 4, cy - 4, cx + 4, cy + 4], c, "INK")
        s.P(cx, cy, "CREAM")
        s.L([(cx - 3, cy), (cx + 3, cy)], "AMBER" if c == "ORANGE" else "TREE")
    return s.im


def tv():
    s = S()
    s.lot("PAVE", (1, 1, 30, 30), "PAVED", 10)
    s.bld(2, 13, 22, 29, "GREY", "PAVE", e=3, door=11, roofd="ASPHD")
    s.E([5, 15, 13, 23], "CREAM", "INK")
    s.E([7, 17, 11, 21], "PAVE")
    s.L([(9, 19), (13, 15)], "INK")  # dish
    s.R([17, 16, 20, 19], "PAVE", "INK")
    for y in range(2, 26, 3):
        s.L([(25, y), (28, y + 3)], "INK")
        s.L([(28, y), (25, y + 3)], "INK")
    s.L([(25, 2), (25, 27)], "INK")
    s.L([(28, 2), (28, 27)], "INK")
    s.P(26, 1, "RED")
    s.P(27, 1, "RED")
    s.P(26, 0, "RED")
    for y in (8, 16):
        s.P(24, y, "RED")
        s.P(29, y, "RED")
    return s.im


def radio():
    s = S()
    s.lot("GRASS", (1, 1, 30, 30), "GRASSD", 11)
    for ax, ay in ((3, 3), (28, 4), (4, 28)):
        s.L([(16, 14), (ax, ay)], "DARK")
        s.R([ax - 1, ay - 1, ax + 1, ay + 1], "ASPHD")  # guy wires
    s.L([(15, 2), (15, 20)], "INK")
    s.L([(17, 2), (17, 20)], "INK")
    for y in range(3, 20, 3):
        s.L([(15, y), (17, y + 2)], "RED")
        s.P(16, y + 1, "CREAM")
    s.P(16, 1, "RED")
    s.P(16, 0, "RED")
    s.bld(19, 19, 29, 29, "CREAM", "PAVE", e=3, door=23, roofd="TAN")
    s.R([21, 21, 23, 23], "GREY", "INK")
    return s.im


def newspaper():
    s = S()
    s.lot("PAVE", (1, 1, 30, 30), "PAVED", 12)
    s.bld(2, 2, 25, 20, "BROWN", "TAN", e=3, door=12, roofd="BROWND")
    s.R([5, 5, 20, 13], "CREAM", "INK")  # front page on the roof
    s.L([(7, 7), (18, 7)], "INK", 1)
    s.L([(7, 9), (12, 9)], "DARK")
    s.L([(7, 11), (12, 11)], "DARK")
    s.R([14, 9, 18, 11], "GREY")
    for x in (26, 26):
        pass
    for y in (3, 9, 15):
        s.E([26, y, 30, y + 4], "CREAM", "INK")
        s.P(28, y + 2, "TAN")  # paper rolls
    s.R([4, 23, 17, 29], "CREAM", "INK")
    s.R([13, 23, 17, 29], "GLASS", "INK")
    s.L([(5, 26), (11, 26)], "RED")  # van
    s.R([20, 24, 28, 29], "TAND", "INK")
    s.L([(21, 26), (27, 26)], "BROWN")  # bundles
    return s.im


def seaport():
    s = S()
    s.R([0, 0, 31, 31], "WATER")
    s.R([0, 0, 31, 13], "PAVED")
    s.L([(0, 13), (31, 13)], "INK")
    for x in range(2, 30, 6):
        s.R([x, 14, x + 1, 15], "DARK")  # bollards
    for i, (x, y, c) in enumerate(
        ((2, 2, "RED"), (2, 6, "GLASS"), (9, 2, "GREEN"), (9, 6, "ORANGE"), (16, 4, "GLASSD"))
    ):
        s.R([x, y, x + 5, y + 3], c, "INK")
        s.L([(x + 1, y + 1), (x + 4, y + 1)], "INK")
    s.L([(23, 1), (23, 12)], "INK")
    s.L([(27, 1), (27, 12)], "INK")
    s.R([22, 2, 28, 4], "ORANGE", "INK")  # crane
    s.R([24, 4, 26, 21], "ORANGE", "INK")
    s.L([(25, 21), (25, 24)], "INK")
    s.d.polygon(
        [(4, 18), (20, 18), (22, 22), (20, 27), (4, 27)], fill=H(C["NAVY"]), outline=H(C["INK"])
    )  # ship
    s.R([6, 20, 11, 25], "RED", "INK")
    s.R([12, 20, 16, 25], "GLASS", "INK")
    s.R([17, 20, 19, 25], "CREAM", "INK")
    for x in range(1, 31, 5):
        s.L([(x, 29), (x + 2, 29)], "WIN")
    return s.im


def flag(c):
    im = Image.new("RGBA", (8, 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line([(1, 1), (1, 11)], fill=H(C["INK"]))
    d.rectangle([1, 1, 7, 6], fill=H(c), outline=H(C["INK"]))
    return im


NAMES = [
    "department_store",
    "factory",
    "rnd_center",
    "farm",
    "logging_camp",
    "mine",
    "oil_well",
    "software_developer",
    "software_publisher",
    "restaurant",
    "television_station",
    "radio_station",
    "newspaper_publisher",
    "seaport",
]
DRAW = [
    dept,
    factory,
    rnd,
    farm,
    logging,
    mine,
    oil,
    lambda: office("CREAM", "TAN", sym_monitor),
    lambda: office("GLASS", "GLASSD", sym_disc),
    restaurant,
    tv,
    radio,
    newspaper,
    seaport,
]


def build(save, flags_save=None):
    for n, f in zip(NAMES, DRAW):
        save("firm_" + n, f())
    if flags_save:
        for i, c in enumerate(FLAGS):
            flags_save(f"flag_{i:02d}", flag(c))
