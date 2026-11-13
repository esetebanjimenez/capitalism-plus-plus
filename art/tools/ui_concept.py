"""UI concept for the clear-map layout (spec docs/m2-ux-spec.md, PR #57).
Frames, buttons, handle, slot cells, badge and status icons are pixel art drawn on a
1-point grid with palette colours only; they are scaled by the screen density
(nearest). Text in the mocks is live browser text (DejaVu here), not baked art.
Outputs: docs/art/concept-ui-phone.png, concept-ui-desktop.png, concept-ui-parts.png
Mock numbers and names are example data."""

import json, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
P = lambda *a: os.path.join(ROOT, *a)
C = dict(
    CREAM="#f6ecd4",
    SAND="#e8d6a0",
    TAN="#d4b27f",
    INK="#22262e",
    ORANGE="#e8742a",
    GREEN="#3aa05a",
    RED="#c8402e",
    GREY="#b8bcc0",
    MGREY="#868a84",
    BLUE="#3b6db3",
    DGREY="#313944",
    WHITE="#f6ecd4",
    AMBER="#e0862f",
    DKGREEN="#306f46",
    LBLUE="#9fd3d8",
    BROWN="#8a5a32",
)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONTR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(pt, s, bold=True):
    return ImageFont.truetype(FONT if bold else FONTR, int(pt * s))


# ---------- pixel parts on a 1 pt grid ----------
def card(w, h, fill="CREAM", border="INK", alpha=255, shadow=True, r=2, top_only=False):
    """Cream card: 2 pt ink border, stepped 4 pt corner, 1 pt tan drop shadow."""
    im = Image.new("RGBA", (w, h + (1 if shadow else 0)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def body(dx, dy, col, a=255):
        c = Image.new("RGBA", im.size, (0, 0, 0, 0))
        e = ImageDraw.Draw(c)
        rgb = tuple(int(C[col][i : i + 2], 16) for i in (1, 3, 5)) + (a,)
        e.rectangle([dx + r, dy, dx + w - 1 - r, dy + h - 1], rgb)
        e.rectangle([dx, dy + r, dx + w - 1, dy + h - 1 - (0 if top_only else r)], rgb)
        e.rectangle([dx + 1, dy + 1, dx + w - 2, dy + h - 2 + (1 if top_only else 0)], rgb)
        if top_only:
            e.rectangle([dx, dy + r, dx + w - 1, dy + h - 1], rgb)
        return c

    if shadow:
        im.alpha_composite(body(0, 1, "TAN"))
    im.alpha_composite(body(0, 0, border))
    inner = body(0, 0, fill, alpha).crop((0, 0, w - 4, h - 4)) if False else None
    c = Image.new("RGBA", im.size, (0, 0, 0, 0))
    e = ImageDraw.Draw(c)
    rgb = tuple(int(C[fill][i : i + 2], 16) for i in (1, 3, 5)) + (alpha,)
    e.rectangle([2 + 1, 2, w - 4, h - 3 + (2 if top_only else 0)], rgb)
    e.rectangle([2, 3, w - 3, h - 4 + (3 if top_only else 0)], rgb)
    # clear border area under fill first so translucency shows map
    a = im.load()
    b = c.load()
    for y in range(im.size[1]):
        for x in range(w):
            if b[x, y][3]:
                a[x, y] = b[x, y]
    return im


ICON = {  # 16x16 status icons, '#'=ink, 'o'=orange, 'w'=cream, 'g'=green, 'r'=red
    "pause": [
        "................",
        "................",
        "...####..####...",
        "...#ww#..#ww#...",
        "...#ww#..#ww#...",
        "...#ww#..#ww#...",
        "...#ww#..#ww#...",
        "...#ww#..#ww#...",
        "...#ww#..#ww#...",
        "...#ww#..#ww#...",
        "...#ww#..#ww#...",
        "...#ww#..#ww#...",
        "...#ww#..#ww#...",
        "...####..####...",
        "................",
        "................",
    ],
    "play": [
        "................",
        "....#...........",
        "....##..........",
        "....#o#.........",
        "....#oo#........",
        "....#ooo#.......",
        "....#oooo#......",
        "....#ooooo#.....",
        "....#ooooo#.....",
        "....#oooo#......",
        "....#ooo#.......",
        "....#oo#........",
        "....#o#.........",
        "....##..........",
        "....#...........",
        "................",
    ],
    "ff": [
        "................",
        "................",
        "..#......#......",
        "..##.....##.....",
        "..#o#....#o#....",
        "..#oo#...#oo#...",
        "..#ooo#..#ooo#..",
        "..#oooo#.#oooo#.",
        "..#oooo#.#oooo#.",
        "..#ooo#..#ooo#..",
        "..#oo#...#oo#...",
        "..#o#....#o#....",
        "..##.....##.....",
        "..#......#......",
        "................",
        "................",
    ],
    "cal": [
        "................",
        "...#......#.....",
        "..############..",
        "..#oooooooooo#..",
        "..#oooooooooo#..",
        "..############..",
        "..#wwwwwwwwww#..",
        "..#w##w##w##w#..",
        "..#wwwwwwwwww#..",
        "..#w##w##w##w#..",
        "..#wwwwwwwwww#..",
        "..#w##w##wwww#..",
        "..#wwwwwwwwww#..",
        "..############..",
        "................",
        "................",
    ],
    "cash": [
        "................",
        "................",
        ".##############.",
        ".#gggggggggggg#.",
        ".#g#gggggggg#g#.",
        ".#gggg####gggg#.",
        ".#ggg#gggg#ggg#.",
        ".#ggg#gggg#ggg#.",
        ".#ggg#gggg#ggg#.",
        ".#gggg####gggg#.",
        ".#g#gggggggg#g#.",
        ".#gggggggggggg#.",
        ".##############.",
        "................",
        "................",
        "................",
    ],
    "clock": [
        "................",
        ".....######.....",
        "....#wwwwww#....",
        "...#www#www#w...",
        "..#wwww#wwwww#..",
        "..#wwww#wwwww#..",
        "..#wwww#wwwww#..",
        "..#wwww####ww#..",
        "..#wwwwwwwwww#..",
        "..#wwwwwwwwww#..",
        "...#wwwwwwww#...",
        "....#wwwwww#....",
        ".....######.....",
        "................",
        "................",
        "................",
    ],
    "news": [
        "................",
        "................",
        ".############...",
        ".#wwwwwwwwww##..",
        ".#w####wwwww#w#.",
        ".#w####w###w#w#.",
        ".#w####wwwww#w#.",
        ".#wwwwww###w#w#.",
        ".#w########w#w#.",
        ".#wwwwwwwwww#w#.",
        ".#w########w#w#.",
        ".#wwwwwwwwww#w#.",
        ".#############..",
        "................",
        "................",
        "................",
    ],
    "close": [
        "................",
        "................",
        "................",
        "...##......##...",
        "...###....###...",
        "....###..###....",
        ".....######.....",
        "......####......",
        "......####......",
        ".....######.....",
        "....###..###....",
        "...###....###...",
        "...##......##...",
        "................",
        "................",
        "................",
    ],
    "menu": [
        "................",
        "................",
        "................",
        "..############..",
        "..############..",
        "................",
        "................",
        "..############..",
        "..############..",
        "................",
        "................",
        "..############..",
        "..############..",
        "................",
        "................",
        "................",
    ],
    "warn": [
        "................",
        ".......##.......",
        "......#oo#......",
        "......#oo#......",
        ".....#oooo#.....",
        ".....#o##o#.....",
        "....#oo##oo#....",
        "....#oo##oo#....",
        "...#ooo##ooo#...",
        "...#ooo##ooo#...",
        "..#oooooooooo#..",
        "..#oooo##oooo#..",
        ".#ooooooooooooo#",
        ".################",
        "................",
        "................",
    ],
    "down": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "....########....",
        ".....######.....",
        "......####......",
        ".......##.......",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    "plus": [
        "................",
        "................",
        "................",
        "................",
        ".......##.......",
        ".......##.......",
        ".......##.......",
        "....########....",
        "....########....",
        ".......##.......",
        ".......##.......",
        ".......##.......",
        "................",
        "................",
        "................",
        "................",
    ],
    "ov_none": [
        "................",
        "................",
        "..############..",
        "..#wwwwwwww###..",
        "..#wwwwwww##w#..",
        "..#wwwwww##ww#..",
        "..#wwwww##www#..",
        "..#wwww##wwww#..",
        "..#www##wwwww#..",
        "..#ww##wwwwww#..",
        "..#w##wwwwwww#..",
        "..###wwwwwwww#..",
        "..##wwwwwwwww#..",
        "..############..",
        "................",
        "................",
    ],
    "ov_land": [
        "................",
        "................",
        ".############...",
        ".#gggggggggg#...",
        ".#gggggggggg#...",
        ".#gggggggggg#...",
        ".#gggggggggg#...",
        ".#gggggg######..",
        ".#ggggg##wwoo##.",
        ".#ggggg#owoooo#.",
        ".#ggggg#oooooo#.",
        ".#ggggg#oooooo#.",
        ".#######oooooo#.",
        ".......##oooo##.",
        "........######..",
        "................",
    ],
    "ov_soil": [
        "................",
        "................",
        "..############..",
        "..#gggggggggg#..",
        "..#gggggggggg#..",
        "..############..",
        "..#ssssssssss#..",
        "..#ss#sss#sss#..",
        "..#ssssssssss#..",
        "..#nnnnnnnnnn#..",
        "..#n#nnnnnn#n#..",
        "..#nnnn#nnnnn#..",
        "..#nnnnnnnnnn#..",
        "..############..",
        "................",
        "................",
    ],
    "ov_rain": [
        "................",
        ".......##.......",
        ".......##.......",
        "......#bb#......",
        "......#bb#......",
        ".....#bbbb#.....",
        ".....#bbbb#.....",
        "....#bbbbbb#....",
        "...#bbbbbbbb#...",
        "...#blbbbbbb#...",
        "...#blbbbbbb#...",
        "...#bllbbbbb#...",
        "....#bbbbbb#....",
        ".....######.....",
        "................",
        "................",
    ],
    "ov_climate": [
        "................",
        "......####......",
        "......#ww#......",
        "......#ww###....",
        "......#rr#......",
        "......#rr###....",
        "......#rr#......",
        "......#rr###....",
        "......#rr#......",
        ".....#rrrr#.....",
        "....#rrrrrr#....",
        "....#rwrrrr#....",
        "....#rrrrrr#....",
        ".....#rrrr#.....",
        "......####......",
        "................",
    ],
    "ov_owner": [
        "................",
        "...##...........",
        "...###########..",
        "...###ooooooo#..",
        "...###ooooooo#..",
        "...###ooooooo#..",
        "...###ooooooo#..",
        "...###ooooooo#..",
        "...###########..",
        "...##...........",
        "...##...........",
        "...##...........",
        "...##...........",
        "...##...........",
        "..####..........",
        "................",
    ],
    "build": [
        "................",
        "................",
        ".......#........",
        "......#o#.......",
        ".....#ooo#......",
        "....#ooooo#.....",
        "...#ooooooo#....",
        "..###########...",
        "...#wwwwwww#....",
        "...#w##w##w#....",
        "...#w##w##w#....",
        "...#wwwww#w#....",
        "...#wwwww#w#....",
        "...#########....",
        "................",
        "................",
    ],
}
KEY = {
    "#": "INK",
    "o": "ORANGE",
    "w": "CREAM",
    "g": "GREEN",
    "r": "RED",
    "b": "BLUE",
    "l": "LBLUE",
    "s": "SAND",
    "n": "BROWN",
}


def icon(name, tint=None):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    a = im.load()
    for y, row in enumerate(ICON[name]):
        for x, ch in enumerate(row[:16]):
            if ch in KEY:
                col = C[tint if (tint and ch == "#") else KEY[ch]]
                a[x, y] = tuple(int(col[i : i + 2], 16) for i in (1, 3, 5)) + (255,)
    return im


def cream(im):
    a = im.load()
    o = tuple(int(C["ORANGE"][i : i + 2], 16) for i in (1, 3, 5)) + (255,)
    cr = tuple(int(C["CREAM"][i : i + 2], 16) for i in (1, 3, 5)) + (255,)
    for y in range(im.height):
        for x in range(im.width):
            if a[x, y] == o:
                a[x, y] = cr
    return im


def badge(n):
    im = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, 17, 17], C["CREAM"])
    d.ellipse([1, 1, 16, 16], C["RED"])
    return im


def handle(w=36):
    im = Image.new("RGBA", (w, 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([1, 0, w - 2, 3], C["MGREY"])
    d.rectangle([0, 1, w - 1, 2], C["MGREY"])
    return im


def button(w, h, kind):
    fill, border = {
        "primary": ("ORANGE", "INK"),
        "secondary": ("CREAM", "INK"),
        "danger": ("RED", "INK"),
        "disabled": ("SAND", "MGREY"),
    }[kind]
    im = card(w, h, fill, border, shadow=False)
    out = Image.new("RGBA", (w, h + 2), (0, 0, 0, 0))
    lip = card(
        w,
        h,
        "INK" if kind != "disabled" else "MGREY",
        "INK" if kind != "disabled" else "MGREY",
        shadow=False,
    )
    out.alpha_composite(lip, (0, 2))
    out.alpha_composite(im, (0, 0))
    return out


def slot(state, w=72, h=72):
    if state == "empty":
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for i in range(0, w, 4):  # dashed ink border
            d.rectangle([i, 0, i + 1, 1], C["MGREY"])
            d.rectangle([i, h - 2, i + 1, h - 1], C["MGREY"])
        for j in range(0, h, 4):
            d.rectangle([0, j, 1, j + 1], C["MGREY"])
            d.rectangle([w - 2, j, w - 1, j + 1], C["MGREY"])
        im.alpha_composite(icon("plus", "MGREY"), (w // 2 - 8, h // 2 - 8))
        return im
    return card(
        w,
        h,
        "CREAM" if state == "filled" else "SAND",
        "INK" if state == "filled" else "ORANGE",
        shadow=False,
    )


def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


# ---------- map backdrop ----------
def atlas(n):
    meta = json.load(open(P("art", "atlas", f"terrain_atlas{'_64' if n == 64 else ''}.json")))
    sheet = Image.open(P("art", "atlas", f"terrain_atlas{'_64' if n == 64 else ''}.png")).convert(
        "RGBA"
    )
    return lambda k: sheet.crop(
        (
            meta["frames"][k]["x"],
            meta["frames"][k]["y"],
            meta["frames"][k]["x"] + meta["frames"][k]["w"],
            meta["frames"][k]["y"] + meta["frames"][k]["h"],
        )
    )


def scene(cols, rows, n, seed=3):
    """Hand-laid example map: sea on the west, a level 5 town, firms with flags."""
    import random

    r = random.Random(seed)
    F = atlas(n)
    im = Image.new("RGBA", (cols * n, rows * n))
    sea = lambda x, y: x < 2 or (x < 3 and y > rows - 7)
    for y in range(rows):
        for x in range(cols):
            if sea(x, y):
                k = f"water_{r.randint(0, 2)}" if x >= 1 else f"deep_{r.randint(0, 2)}"
                if x == 1 or (x == 2 and sea(x, y)):
                    k = f"water_{r.randint(0, 2)}"
                m = (2 if not sea(x + 1, y) else 0) | (1 if y > 0 and not sea(x, y - 1) else 0)
                if m:
                    k = f"coast_{m:02d}"
                elif not sea(x + 1, y - 1) and y > 0:
                    k = "coast_corner_ne"
            else:
                forest = (x - 9) ** 2 + (y - 3) ** 2 < 6 or (x - 10) ** 2 + (y - rows + 4) ** 2 < 7
                k = f"forest_c2_{r.randint(0, 3)}" if forest else f"grass_c2_{r.randint(0, 3)}"
            im.alpha_composite(F(k), (x * n, y * n))
    tx, ty = 4, rows // 2 - 6  # 5x5 town, roads on rows/cols 1 and 3
    for j in range(5):
        for i in range(5):
            if i == 2 and j == 2:
                k = "plaza"
            elif i in (1, 3) or j in (1, 3):
                m = 0
                if i in (1, 3):
                    m |= (1 if j > 0 else 0) | (4 if j < 4 else 0)
                if j in (1, 3):
                    m |= (8 if i > 0 else 0) | (2 if i < 4 else 0)
                k = f"road_{m:02d}"
            else:
                k = r.choice(["block_s0_l2", "block_s1_l2", "block_s2_l1", "block_s3_l2", "park_0"])
            im.alpha_composite(F(k), ((tx + i) * n, (ty + j) * n))
    firms = [
        (10, ty + 1, "factory", 0),
        (10, ty + 3, "department_store", 3),
        (3, ty + 7, "farm", 0),
        (7, ty + 8, "rnd_center", 5),
        (11, ty + 9, "oil_well", 3),
        (6, ty - 3, "restaurant", 0),
        (2, ty - 1, "seaport", 5),
        (8, ty + 12, "software_developer", 0),
        (4, ty + 13, "mine", 7),
    ]
    for x, y, t, fl in firms:
        if 0 <= y < rows:
            im.alpha_composite(F("firm_" + t), (x * n, y * n))
            im.alpha_composite(F(f"flag_{fl:02d}"), (x * n + 3 * n // 4, y * n - n // 8))
    return im, firms, (tx, ty)


def outline(im, x, y, n, s):
    d = ImageDraw.Draw(im)
    w = 3 if s == 1 else 2 * s
    for i in range(w):
        d.rectangle(
            [x * n + i, y * n + i, x * n + n - 1 - i, y * n + n - 1 - i], outline=C["ORANGE"]
        )


# ---------- text helper ----------
def text(d, xy, t, pt, s, col="INK", bold=True, anchor="la"):
    d.text((xy[0] * s, xy[1] * s), t, font=font(pt, s, bold), fill=C[col], anchor=anchor)


def tw(t, pt, s, bold=True):
    return font(pt, s, bold).getlength(t) / s


def paste(base, part, x, y, s):
    base.alpha_composite(up(part, s), (int(x * s), int(y * s)))


def pill(base, x, y, s, date, cash, speed):
    d = ImageDraw.Draw(base)
    w1, w2 = tw(date, 16, s), tw(cash, 16, s)
    W = 8 + 16 + 6 + w1 + 14 + 16 + 6 + w2 + 12 + 64
    W = int(W)
    paste(base, card(W, 40, alpha=232), x, y, s)
    cx = x + 8
    paste(base, icon("cal"), cx, y + 12, s)
    text(d, (cx + 22, y + 11), date, 16, s)
    cx += 22 + w1 + 12
    d.rectangle([cx * s, (y + 9) * s, (cx + 1) * s - 1, (y + 31) * s - 1], C["TAN"])
    cx += 6
    paste(base, icon("cash"), cx, y + 12, s)
    text(d, (cx + 22, y + 11), cash, 16, s, "INK")
    bx = x + W - 64 - 4
    paste(base, button(60, 30, "primary"), bx, y + 4, s)
    paste(base, cream(icon("ff" if speed else "pause")), bx + 6, y + 11, s)
    text(d, (bx + 26, y + 10), str(speed) if speed else "", 16, s, "INK")
    paste(base, icon("down"), bx + 40, y + 11, s)
    return W


def menu_btn(base, x, y, s, n):
    paste(base, card(48, 48, alpha=232), x, y, s)
    paste(base, icon("menu"), x + 16, y + 16, s)
    if n:
        paste(base, badge(n), x + 36, y - 6, s)
        text(ImageDraw.Draw(base), (x + 45, y + 3), str(n), 12, s, "CREAM", anchor="mm")


def toast(base, x, y, w, s, msg):
    paste(base, card(w, 40, alpha=240), x, y, s)
    paste(base, icon("news"), x + 10, y + 12, s)
    text(ImageDraw.Draw(base), (x + 34, y + 11), msg, 16, s, bold=False)


def phone_frame(img, s, label):
    W, H = img.size
    pad = 14 * s
    out = Image.new("RGBA", (W + 2 * pad, H + 2 * pad + 30 * s), C["DGREY"])
    d = ImageDraw.Draw(out)
    d.rounded_rectangle([0, 0, out.width - 1, out.height - 30 * s - 1], 44 * s, C["INK"])
    out.alpha_composite(img, (pad, pad))
    d.text(
        (out.width // 2, out.height - 15 * s), label, font=font(13, s), fill=C["CREAM"], anchor="mm"
    )
    return out


def phone_default(s=2):
    n = 32 * s
    W, H = 390, 844
    m, firms, (tx, ty) = scene(13, 27, 64 if s >= 2 else 32)
    base = m.crop((0, 0, W * s, H * s)).convert("RGBA")
    pill(base, 8, 54, s, "14 Mar 1991", "$4,812,300", 2)
    toast(base, 8, 102, 300, s, "New rival factory in Hanford")
    menu_btn(base, W - 16 - 48, H - 34 - 48, s, 3)
    return base


def sheet_firm(s=2):
    n = 32 * s
    W, H = 390, 844
    m, firms, (tx, ty) = scene(13, 27, 64)
    # pan so the factory sits above the half sheet
    fx, fy = 10, ty + 1
    off = (fy - 6) * n
    base = m.crop((0, off, W * s, off + H * s)).convert("RGBA")
    outline(base, fx, fy - off // n, n, s)
    pill(base, 8, 54, s, "14 Mar 1991", "$4,812,300", 0)
    d = ImageDraw.Draw(base)
    top = 410
    paste(base, card(W, H - top + 4, top_only=True), 0, top, s)
    paste(base, handle(), W // 2 - 18, top + 8, s)
    F = atlas(64)
    base.alpha_composite(F("firm_factory"), (16 * s, (top + 22) * s))
    base.alpha_composite(F("flag_00"), (16 * s + 48, (top + 22) * s - 8))
    text(d, (60, top + 22), "Factory", 20, s)
    text(d, (60, top + 46), "Hanford · you", 14, s, "MGREY", bold=False)
    text(d, (W - 60, top + 22), "+$38,200", 16, s, "DKGREEN", anchor="ra")
    text(d, (W - 60, top + 44), "this month", 14, s, "MGREY", False, "ra")
    paste(base, button(36, 36, "secondary"), W - 50, top + 20, s)
    paste(base, icon("close"), W - 40, top + 30, s)
    # tabs
    ty0 = top + 72
    for i, t in enumerate(["Layout", "Firm", "Links"]):
        x = 16 + i * 120
        if i == 0:
            d.rectangle([x * s, (ty0 + 30) * s, (x + 110) * s - 1, (ty0 + 33) * s - 1], C["ORANGE"])
        text(d, (x + 55, ty0 + 6), t, 16, s, "INK" if i == 0 else "MGREY", anchor="ma")
    d.rectangle([0, (ty0 + 34) * s, W * s, (ty0 + 35) * s - 1], C["TAN"])
    # 3x3 grid
    I = json.load(open(P("art", "atlas", "icons_atlas.json")))["frames"]
    IS = Image.open(P("art", "atlas", "icons_atlas.png")).convert("RGBA")
    ic = lambda k: IS.crop((I[k]["x"], I[k]["y"], I[k]["x"] + I[k]["w"], I[k]["y"] + I[k]["h"]))
    jobs = {
        0: ("purchasing", 6, 0.7),
        1: ("manufacturing", 7, 0.4),
        2: ("inventory", 5, 0.9),
        4: ("manufacturing", 3, 0.2),
        5: ("sales", 4, 0.6),
    }
    gx, gy, cw, gap = 59, ty0 + 48, 72, 16
    pos = lambda i: (gx + (i % 3) * (cw + gap), gy + (i // 3) * (cw + gap))
    for i in range(9):
        x, y = pos(i)
        st = "selected" if i == 1 else ("filled" if i in jobs else "empty")
        paste(base, slot(st), x, y, s)
        if i in jobs:
            j, rt, st_ = jobs[i]
            base.alpha_composite(ic("job_" + j), (int((x + 12) * s), int((y + 8) * s)))
            chip = card(20, 20, "INK", "INK", shadow=False)
            paste(base, chip, x + 46, y + 6, s)
            text(d, (x + 56, y + 16), str(rt), 13, s, "CREAM", anchor="mm")
            d.rectangle([(x + 8) * s, (y + 58) * s, (x + 64) * s - 1, (y + 64) * s - 1], C["INK"])
            d.rectangle(
                [(x + 9) * s, (y + 59) * s, (x + 9 + 54 * st_) * s - 1, (y + 63) * s - 1],
                C["GREEN"],
            )

    def link(a, b, col, dashed=False):
        """Slot links have no direction (brief PR #77): plain line, no arrowhead; dashed = can't move anything."""
        (x1, y1), (x2, y2) = pos(a), pos(b)
        x1 += cw / 2
        y1 += cw / 2
        x2 += cw / 2
        y2 += cw / 2
        import math

        L = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        sx, sy = x1 + ux * 38, y1 + uy * 38
        ex, ey = x2 - ux * 38, y2 - uy * 38
        if not dashed:
            d.line([sx * s, sy * s, ex * s, ey * s], C[col], width=3 * s)
            return
        n = math.hypot(ex - sx, ey - sy)
        t = 0
        while t < n:
            t2 = min(t + 4, n)
            d.line(
                [(sx + ux * t) * s, (sy + uy * t) * s, (sx + ux * t2) * s, (sy + uy * t2) * s],
                C[col],
                width=3 * s,
            )
            t += 7

    link(0, 1, "INK")
    link(1, 2, "ORANGE")
    link(0, 4, "INK")
    link(4, 5, "INK")
    link(2, 5, "INK", dashed=True)
    by = gy + 3 * cw + 2 * gap + 18
    paste(base, button(170, 44, "secondary"), 16, by, s)
    text(d, (101, by + 12), "Plans", 16, s, anchor="ma")
    paste(base, button(170, 44, "primary"), W - 186, by, s)
    text(d, (W - 101, by + 12), "Slot details", 16, s, anchor="ma")
    return base


def desktop(s=1):
    W, H = 1280, 720
    n = 32
    m, firms, (tx, ty) = scene(40, 23, 32)
    base = m.crop((0, 0, W, H)).convert("RGBA")
    pill(base, 12, 12, s, "14 Mar 1991", "$4,812,300", 2)
    menu_btn(
        base, W - 400 - 16 - 48, H - 64, s, 3
    )  # bottom right, shifted left of the open side panel
    fx, fy = 10, ty + 3
    outline(base, fx, fy, n, 1)
    d = ImageDraw.Draw(base)
    px = W - 400
    paste(base, card(404, H + 8), px, -4, s)
    F = atlas(32)
    base.alpha_composite(up(F("firm_department_store"), 1), (px + 16, 20))
    text(d, (px + 58, 18), "Department Store", 20, s)
    text(d, (px + 58, 42), "Hanford · you", 14, s, "MGREY", False)
    paste(base, button(36, 36, "secondary"), W - 50, 16, s)
    paste(base, icon("close"), W - 40, 26, s)
    for i, t in enumerate(["Layout", "Firm", "Links"]):
        x = px + 16 + i * 124
        if i == 1:
            d.rectangle([x, 98, x + 114, 101], C["ORANGE"])
        text(d, (x + 57, 72), t, 16, s, "INK" if i == 1 else "MGREY", anchor="ma")
    d.rectangle([px + 2, 102, W, 103], C["TAN"])
    rows = [
        ("Sales", "+$212,400"),
        ("Purchases", "−$141,900"),
        ("Wages", "−$18,300"),
        ("Overhead", "−$100,000"),
        ("Advertising", "−$6,000"),
        ("Training", "−$1,200"),
        ("Profit", "−$55,000"),
    ]
    y = 120
    text(d, (px + 16, y), "This month", 14, s, "MGREY", False)
    y += 28
    for k, v in rows:
        last = k == "Profit"
        if last:
            d.rectangle([px + 16, y - 6, W - 16, y - 5], C["INK"])
        text(d, (px + 16, y), k, 16, s, bold=last)
        text(
            d,
            (W - 16, y),
            v,
            14 if not last else 16,
            s,
            ("DKGREEN" if v[0] == "+" else "RED"),
            bold=True,
            anchor="ra",
        )
        y += 30
    paste(base, button(180, 44, "danger"), px + 16, H - 70, s)
    text(d, (px + 106, H - 58), "Demolish", 16, s, "CREAM", anchor="ma")
    paste(base, button(180, 44, "secondary"), W - 196, H - 70, s)
    text(d, (W - 106, H - 58), "Partners", 16, s, anchor="ma")
    return base


def parts_sheet(s=4):
    items = [
        ("Panel card: 2 pt ink, stepped corner, 1 pt tan shadow", card(48, 32)),
        ("Floating card, translucent (pill, menu button, toast)", card(48, 32, alpha=232)),
        ("Bottom sheet top, open bottom", card(64, 24, top_only=True)),
        ("Drag handle", handle()),
        ("Primary button with 2 pt pressed lip", button(48, 22, "primary")),
        ("Secondary button", button(48, 22, "secondary")),
        ("Danger button (Demolish)", button(48, 22, "danger")),
        ("Disabled button (cannot afford)", button(48, 22, "disabled")),
        ("Slot cells: empty, filled, selected", "slots"),
        ("News badge (count drawn live)", badge(3)),
    ]
    icons = [
        "pause",
        "play",
        "ff",
        "down",
        "cal",
        "cash",
        "clock",
        "news",
        "warn",
        "menu",
        "close",
        "plus",
        "build",
    ]
    W = 1180
    colw = W // 2
    out = Image.new("RGBA", (W, 1400), C["DGREY"])
    d = ImageDraw.Draw(out)
    d.text(
        (24, 18),
        "UI parts at 4× (one art pixel per point). Palette colours only; all text is live, not baked.",
        font=font(16, 1),
        fill=C["CREAM"],
    )
    ys = [60, 60]
    for i, (lab, im) in enumerate(items):
        c = i % 2
        x = 24 + c * colw
        y = ys[c]
        d.text((x, y), lab, font=font(14, 1, False), fill=C["SAND"])
        if im == "slots":
            for k, st in enumerate(["empty", "filled", "selected"]):
                out.alpha_composite(up(slot(st, 24, 24), s // 2 * 2), (x + k * 120, y + 24))
            h = 24 * s
        else:
            out.alpha_composite(up(im, s), (x, y + 24))
            h = im.height * s
        ys[c] = y + 24 + h + 28
    y = max(ys) + 4
    d.text(
        (24, y),
        "Status icons, 16 × 16: pause, play, speed, picker arrow, date, cash, pending clock, news, warning, menu, close, empty slot, build",
        font=font(14, 1, False),
        fill=C["SAND"],
    )
    for i, k in enumerate(icons):
        out.alpha_composite(up(icon(k), s), (24 + i * 88, y + 28))
    return out.crop((0, 0, W, y + 28 + 64 + 24))


if __name__ == "__main__":
    a = phone_frame(phone_default(), 2, "Map, nothing open: pill, toast, menu + badge")
    b = phone_frame(sheet_firm(), 2, "Firm detail, half sheet: 3×3 slots, links")
    sheet = Image.new("RGBA", (a.width + b.width + 60, a.height + 40), C["DGREY"])
    sheet.alpha_composite(a, (20, 20))
    sheet.alpha_composite(b, (a.width + 40, 20))
    sheet.convert("RGB").save(P("docs", "art", "concept-ui-phone.png"), optimize=True)
    desktop().convert("RGB").save(P("docs", "art", "concept-ui-desktop.png"), optimize=True)
    parts_sheet().convert("RGB").save(P("docs", "art", "concept-ui-parts.png"), optimize=True)
    print("ok")
