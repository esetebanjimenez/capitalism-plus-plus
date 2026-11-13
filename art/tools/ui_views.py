"""M2 view art from docs/m2-view-briefs.md sections 2 to 5 (#175, #177, #178), on the same 1 pt grid as
ui_concept: palette colours only, text is live. ui_build.py appends frames() to ui_atlas; running this file
writes docs/art/m2-views-preview.png.

- #175 town-name plate: the plate is the existing `card` nine-slice sized for 12 characters at 12 pt bold
  (136x24 pt). The level is live text in `plate_level`, an ink badge that stretches for 7, 8, 10 and up.
  `plate_pulse` is an orange ring drawn 3 pt outside the plate for the optional level-up pulse.
- #177 news: `icon_nws_normal` (shopfront), `icon_nws_financial` (coins), `icon_nws_tech` (bulb),
  `icon_nws_special` (red burst). Profit arrows `icon_arr_up` (green) and `icon_arr_down` (red) sit beside the
  corporation's operating and other profit only.
- #178 charts: style in art/charts.json; `chart_dot` and `chart_dot_sel` for the last and tapped points,
  value tip in `card_float`.
- #178 win/loss card: one `card` layout; the headline band `end_band_<outcome>` and emblem `icon_end_<outcome>`
  (shown at 2x, 32 pt) change per outcome. Goal rows use `icon_goal` and `icon_goal_miss`.
  New game is `btn_primary`; Keep playing is an optional `btn_secondary` the client can hide."""

import json
import math

from PIL import Image, ImageDraw
from ui_concept import KEY, C, P, button, card, font, icon, scene, up

VIEW_ICON = {  # 16x16, same keys as ui_concept.ICON plus 'm' = MGREY
    "nws_normal": [
        "................",
        "................",
        ".##############.",
        ".#owwoowwoowwo#.",
        ".#owwoowwoowwo#.",
        ".##############.",
        "..############..",
        "..#wwwwwwwwww#..",
        "..#w###w####w#..",
        "..#w#l#w#nn#w#..",
        "..#w###w#nn#w#..",
        "..#wwwww#nn#w#..",
        "..#wwwww#nn#w#..",
        "..############..",
        "................",
        "................",
    ],
    "nws_financial": [
        "................",
        "..........##....",
        "........##oo##..",
        ".......#oowwoo#.",
        "......#oowwwwoo#",
        "......#oowwoooo#",
        ".....#oooowwoooo",
        ".....#ooooowwooo",
        "..#####oowwwwoo#",
        "..#ssssssowwooo#",
        "..#oooo#oooooo#.",
        "..########oo##..",
        "..#ssssss###....",
        "..########......",
        "..########......",
        "................",
    ],
    "nws_tech": [
        "................",
        "......####......",
        ".....#wwoo#.....",
        "....#wwwooo#....",
        "...#wwwwoooo#...",
        "...#wwwwoooo#...",
        "...#wwwwoooo#...",
        "...#oooooooo#...",
        "....#oooooo#....",
        ".....#oooo#.....",
        ".....######.....",
        ".....#ssss#.....",
        ".....######.....",
        ".....#ssss#.....",
        "......####......",
        "................",
    ],
    "nws_special": [
        "................",
        ".......##.......",
        "...##.#rr#.##...",
        "..#rr#rwwr#rr#..",
        "..#rrrrwwrrrr#..",
        "...#rrrwwrrr#...",
        "..#rrrrwwrrrr#..",
        ".#rrrrrwwrrrrr#.",
        ".#rrrrrwwrrrrr#.",
        "..#rrrrwwrrrr#..",
        "...#rrrrrrrr#...",
        "..#rrrrwwrrrr#..",
        "..#rr#rwwr#rr#..",
        "...##.#rr#.##...",
        ".......##.......",
        "................",
    ],
    "arr_up": [
        "................",
        ".......##.......",
        "......#gg#......",
        ".....#gggg#.....",
        "....#gggggg#....",
        "...#gggggggg#...",
        "..#gggggggggg#..",
        ".#gggggggggggg#.",
        "..###gggggg###..",
        "....#gggggg#....",
        "....#gggggg#....",
        "....#gggggg#....",
        "....#gggggg#....",
        "....#gggggg#....",
        ".....######.....",
        "................",
    ],
    "arr_down": [
        "................",
        ".....######.....",
        "....#rrrrrr#....",
        "....#rrrrrr#....",
        "....#rrrrrr#....",
        "....#rrrrrr#....",
        "....#rrrrrr#....",
        "..###rrrrrr###..",
        ".#rrrrrrrrrrrr#.",
        "..#rrrrrrrrrr#..",
        "...#rrrrrrrr#...",
        "....#rrrrrr#....",
        ".....#rrrr#.....",
        "......#rr#......",
        ".......##.......",
        "................",
    ],
    "goal_miss": [
        "................",
        "....########....",
        "...##mmmmmm##...",
        "..##mmmmmmmm##..",
        ".##mwwmmmmwwm##.",
        ".#mmmwwmmwwmmm#.",
        ".#mmmmwwwwmmmm#.",
        ".#mmmmmwwmmmmm#.",
        ".#mmmmwwwwmmmm#.",
        ".#mmmwwmmwwmmm#.",
        ".#mmmmmmmmmmmm#.",
        ".##mmmmmmmmmm##.",
        "..##mmmmmmmm##..",
        "...##mmmmmm##...",
        "....########....",
        "................",
    ],
    "end_win": [
        "................",
        "...##########...",
        ".###wwoooooo###.",
        ".#.#wwoooooo#.#.",
        ".#.#wwoooooo#.#.",
        ".###wwoooooo###.",
        "...#wwoooooo#...",
        "...#oooooooo#...",
        "....#o####o#....",
        "......#oo#......",
        "......#oo#......",
        "....########....",
        "....#nnnnnn#....",
        "....#nnnnnn#....",
        "....########....",
        "................",
    ],
    "end_time": [
        "................",
        "...##########...",
        "...##########...",
        "....#llllll#....",
        ".....#wwww#.....",
        "......#ww#......",
        ".......##.......",
        "................",
        ".......##.......",
        ".......##.......",
        "......#ss#......",
        ".....#ssss#.....",
        "....#ssssss#....",
        "...##########...",
        "...##########...",
        "................",
    ],
    "end_rival": [
        "................",
        "...##...........",
        "...###########..",
        "...##wwwwrrrr#..",
        "...##wwwwrrrr#..",
        "...##wwwwrrrr#..",
        "...##rrrrwwww#..",
        "...##rrrrwwww#..",
        "...##rrrrwwww#..",
        "...###########..",
        "...##...........",
        "...##...........",
        "...##...........",
        "..#####.........",
        "..#####.........",
        "................",
    ],
}
OUTCOMES = {  # result_name: (key, band colour, headline)
    "VICTORY": ("win", "GREEN", "Goals achieved"),
    "DEFEAT_DEADLINE": ("time", "AMBER", "Out of time"),
    "DEFEAT_AI_WON": ("rival", "RED", "A rival got there first"),
}
KEYS = dict(KEY, m="MGREY")


def rgb(k, a=255):
    return tuple(int(C[k][i : i + 2], 16) for i in (1, 3, 5)) + (a,)


def vicon(name):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    a = im.load()
    for y, row in enumerate(VIEW_ICON[name]):
        for x, ch in enumerate(row):
            if ch in KEYS:
                a[x, y] = rgb(KEYS[ch])
    return im


def level_badge():
    """Ink badge for the town level, 16 pt tall when sliced; cream live number, 10 pt bold."""
    return card(12, 12, "INK", "INK", shadow=False)


def pulse_ring():
    """2 pt orange ring with stepped corners, transparent inside; nine-slice [6,6,6,6]."""
    im = card(20, 20, "ORANGE", "ORANGE", shadow=False)
    a = im.load()
    for y in range(2, 18):
        for x in range(2, 18):
            if not ((x in (2, 17)) and (y in (2, 17))):
                a[x, y] = (0, 0, 0, 0)
    return im


def dot(sel=False):
    """Chart point: 8 pt (orange 4 pt core) orange square with stepped ink edge; the tapped one is 10 pt with a cream centre."""
    if sel:
        im = card(10, 10, "ORANGE", "INK", shadow=False)
        ImageDraw.Draw(im).rectangle([4, 4, 5, 5], rgb("CREAM"))
        return im
    im = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([1, 0, 6, 7], rgb("INK"))
    d.rectangle([0, 1, 7, 6], rgb("INK"))
    d.rectangle([2, 2, 5, 5], rgb("ORANGE"))
    return im


def band(col):
    return card(16, 16, col, "INK", shadow=False)


def frames():
    f = {}
    f["plate_level"] = (level_badge(), [4, 4, 4, 4])
    f["plate_pulse"] = (pulse_ring(), [6, 6, 6, 6])
    for k in VIEW_ICON:
        f["icon_" + k] = (vicon(k), None)
    f["chart_dot"] = (dot(), None)
    f["chart_dot_sel"] = (dot(True), None)
    for k, col, _ in OUTCOMES.values():
        f["end_band_" + k] = (band(col), [6, 6, 6, 6])
    return f


def nine(im, sl, w, h):
    l, t, r, b = sl
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    W, H = im.size
    xs = [(0, l, 0, l), (l, W - r, l, w - r), (W - r, W, w - r, w)]
    ys = [(0, t, 0, t), (t, H - b, t, h - b), (H - b, H, h - b, h)]
    for sx0, sx1, dx0, dx1 in xs:
        for sy0, sy1, dy0, dy1 in ys:
            if dx1 > dx0 and dy1 > dy0:
                out.alpha_composite(
                    im.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), 0), (dx0, dy0)
                )
    return out


def nice(raw):
    """Round a tick step up to 1, 2, 2.5 or 5 times a power of ten."""
    e = 10 ** math.floor(math.log10(raw))
    return next(m * e for m in (1, 2, 2.5, 5, 10) if m * e >= raw)


def short(v):
    a = abs(v)
    for d, s in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if a >= d:
            t = f"{a / d:.1f}".rstrip("0").rstrip(".")
            return ("-" if v < 0 else "") + t + s
    return f"{v:.0f}"


def preview(S=2):
    W, H = 1180, 1180
    im = Image.new("RGBA", (W * S, H * S), rgb("DGREY"))
    d = ImageDraw.Draw(im)
    fr = {k: v for k, v in frames().items()}

    def put(part, x, y, k=1):
        im.alpha_composite(up(part, S * k), (int(x * S), int(y * S)))

    def txt(x, y, s, col="INK", pt=12, bold=True, anchor="la"):
        d.text((x * S, y * S), s, font=font(pt, S, bold), fill=rgb(col), anchor=anchor)

    def head(x, y, s):
        txt(x, y, s, "CREAM", 14)

    # --- #175 plates over the map
    head(20, 14, "#175 Town-name plate")
    mp, _, (tx, ty) = scene(11, 20, 32)
    top = max(0, min(13, ty - 2))
    mp = mp.crop((0, top * 32, 352, top * 32 + 224))
    im.alpha_composite(up(mp, S), (20 * S, 40 * S))

    def plate(x, y, name, lvl, pulse=False):
        wb = max(16, 8 + font(10, 1).getlength(str(lvl)))
        w = 136
        if pulse:
            put(nine(fr["plate_pulse"][0], [6, 6, 6, 6], w + 6, 30), x - 3, y - 3)
        put(nine(card(16, 16), [6, 6, 6, 7], w, 25), x, y)
        bx = x + w - 4 - wb
        put(nine(fr["plate_level"][0], [4, 4, 4, 4], int(wb), 16), bx, y + 4)
        txt(bx + wb / 2, y + 12, str(lvl), "CREAM", 10, True, "mm")
        txt(x + 7, y + 12, name, "INK", 12, True, "lm")

    plate(20 + tx * 32 + 8, 40 + (ty - top) * 32 - 34, "Cedar Falls", 5)
    plate(24, 278, "Stonebridge", 12, pulse=True)
    plate(184, 278, "Ash", 1)
    txt(20, 314, "136x24 pt for 12 characters. Left: level-up pulse.", "GREY", 11, False)

    # --- #177 news feed + income
    x0 = 420
    head(x0, 14, "#177 News categories and profit arrows")
    put(nine(card(16, 16), [6, 6, 6, 7], 360, 160), x0, 40)
    news = [
        ("nws_normal", "Day 412", "Northwind opened a factory in Cedar Falls", False),
        ("nws_financial", "Day 410", "Bank loan of $2M approved", False),
        ("nws_tech", "Day 405", "R&D breakthrough: Phone quality +12", False),
        ("nws_special", "Day 401", "Price war on Bread in Pine Hollow", True),
    ]
    for i, (k, day, h, imp) in enumerate(news):
        y = 52 + i * 34
        put(fr["icon_" + k][0], x0 + 12, y + 4)
        txt(x0 + 36, y, day, "MGREY", 10, False)
        txt(x0 + 36, y + 13, h, "INK", 11, imp)
    put(nine(card(16, 16), [6, 6, 6, 7], 360, 96), x0, 212)
    txt(x0 + 12, 222, "Company > Income, last full month", "MGREY", 10, False)
    rows = [
        ("Operating profit", "$1,204,500", "GREEN", "arr_up"),
        ("Other profit", "-$38,200", "RED", "arr_up"),
    ]
    for i, (lab, val, col, ar) in enumerate(rows):
        y = 242 + i * 26
        txt(x0 + 12, y, lab, "INK", 12, False)
        txt(x0 + 320, y, val, col, 12, True, "ra")
        put(fr["icon_" + ar][0], x0 + 328, y - 1)
    txt(
        x0,
        316,
        "A smaller loss: red figure, green up arrow. No arrow when equal or under two months.",
        "GREY",
        11,
        False,
    )

    # --- #178 charts
    y0 = 350
    head(20, y0, "#178 Chart style (art/charts.json)")
    with open(P("art", "charts.json")) as fh:
        style = json.load(fh)

    def chart(x, y, w, h, title, vals, labels, sel=None):
        put(nine(card(16, 16), [6, 6, 6, 7], w, h), x, y)
        txt(x + 12, y + 10, title, "INK", 12)
        px0, py0, px1, py1 = x + 52, y + 34, x + w - 16, y + h - 30
        lo, hi = min(vals), max(vals)
        if hi == lo:
            lo = 0 if hi > 0 else hi * 2
        step = nice((hi - lo) / 3)
        lo, hi = math.floor(lo / step) * step, math.ceil(hi / step) * step
        ticks = round((hi - lo) / step)
        Y = lambda v: py1 - (v - lo) / (hi - lo) * (py1 - py0)
        n = max(1, len(labels) - 1)
        X = lambda i: px0 + i * (px1 - px0) / n
        for j in range(ticks + 1):
            v = lo + step * j
            d.line(
                [(px0 * S, Y(v) * S), (px1 * S, Y(v) * S)],
                fill=rgb(style["grid"]["colour"]),
                width=S,
            )
            z = abs(v) < step / 2
            txt(
                px0 - 6,
                Y(v),
                "0" if z else short(v),
                "INK" if z else style["axis_label"]["colour"],
                10,
                z,
                "rm",
            )
        if lo < 0 < hi:
            d.line(
                [(px0 * S, Y(0) * S), (px1 * S, Y(0) * S)],
                fill=rgb(style["zero_line"]["colour"]),
                width=S,
            )
        for i, l in enumerate(labels):
            if l:
                txt(X(i), py1 + 8, l, style["axis_label"]["colour"], 10, False, "ma")
        pts = [(X(i) * S, Y(v) * S) for i, v in enumerate(vals)]
        if len(pts) > 1:
            d.line(
                pts,
                fill=rgb(style["line"]["colour"]),
                width=style["line"]["width"] * S,
                joint="curve",
            )
        last = len(vals) - 1
        for i in [last] if sel is None else [last, sel]:
            k = "chart_dot_sel" if i == sel else "chart_dot"
            dimg = fr[k][0]
            put(dimg, X(i) - dimg.width / 2, Y(vals[i]) - dimg.height / 2)
        if sel is not None:
            t = short(vals[sel]) if abs(vals[sel]) < 1e5 else "$" + short(vals[sel])
            tw = font(11, 1).getlength(t) + 16
            tx, ty = X(sel) - tw / 2, Y(vals[sel]) - 34
            put(nine(card(16, 16, alpha=232), [6, 6, 6, 7], int(tw), 24), tx, ty)
            txt(X(sel), ty + 11, t, "GREEN" if vals[sel] >= 0 else "RED", 11, True, "mm")

    m = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
    chart(
        20,
        y0 + 26,
        540,
        220,
        "Operating profit, past 12 months",
        [-420e3, -310e3, -150e3, -60e3, 40e3, 210e3, 180e3, 390e3, 640e3, 820e3, 1.1e6, 1.2e6],
        m,
        sel=3,
    )
    chart(580, y0 + 26, 280, 220, "Net worth, first month", [12.5e6], ["Jan"], sel=None)
    chart(
        880,
        y0 + 26,
        280,
        220,
        "Share price, day",
        [18.2, 18.6, 18.4, 19.1, 19.0, 19.7, 20.3],
        ["9", "", "11", "", "13", "", "15"],
        sel=None,
    )

    # --- #178 win/loss cards
    y1 = 640
    head(
        20,
        y1,
        "#178 Win/loss card: one layout, three outcomes; optional Keep playing shown hidden on the third",
    )
    goals = [
        ("Reach $50M net worth", True),
        ("Own 3 firm types", True),
        ("Market share 30% in Bread", None),
    ]
    for c, (res, (k, col, hl)) in enumerate(OUTCOMES.items()):
        x, y, w, h = 20 + c * 386, y1 + 28, 370, 500
        put(nine(card(16, 16), [6, 6, 6, 7], w, h), x, y)
        put(nine(fr["end_band_" + k][0], [6, 6, 6, 6], w - 24, 96), x + 12, y + 12)
        put(fr["icon_end_" + k][0], x + w / 2 - 16, y + 22, 2)
        txt(x + w / 2, y + 80, hl, "CREAM", 17, True, "mm")
        stats = [
            ("Final score", "8,420" if c == 0 else ("3,115" if c == 1 else "4,960")),
            ("Years played", "12" if c != 1 else "20"),
            ("Difficulty", "120"),
        ]
        for i, (a, b) in enumerate(stats):
            yy = y + 126 + i * 28
            txt(x + 24, yy, a, "MGREY", 12, False)
            txt(x + w - 24, yy, b, "INK", 14, True, "ra")
        d.line(
            [((x + 24) * S, (y + 214) * S), ((x + w - 24) * S, (y + 214) * S)],
            fill=rgb("SAND"),
            width=S,
        )
        txt(x + 24, y + 226, "Goals", "INK", 13)
        for i, (g, met) in enumerate(goals):
            met = met if met is not None else c == 0
            yy = y + 256 + i * 30
            put(
                icon("goal") if met else fr["icon_goal_miss"][0],
                x + 24,
                yy - 2,
            )
            txt(x + 48, yy, g, "INK" if met else "MGREY", 12, False)
        bw = w - 48
        put(nine(button(16, 16, "primary"), [6, 6, 6, 8], bw, 46), x + 24, y + h - 130)
        txt(x + w / 2, y + h - 107, "New game", "CREAM", 14, True, "mm")
        if c != 2:
            put(nine(button(16, 16, "secondary"), [6, 6, 6, 8], bw, 46), x + 24, y + h - 72)
            txt(x + w / 2, y + h - 49, "Keep playing (optional)", "INK", 14, True, "mm")
    im.convert("RGB").save(P("docs", "art", "m2-views-preview.png"), optimize=True)


if __name__ == "__main__":
    preview()
