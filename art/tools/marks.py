"""Map markers for M2, drawn natively at 32 px and 64 px (u = N/32), same frame names on both sheets:
sel_tile        orange selection outline (tile card, firm detail, town card)
sel_build_ok    green outline with corner ticks: the build panel's chosen tile, buildable
sel_build_no    red dashed outline with a no-entry mark: tapped tile can't be built on
construction    full tile shown in place of a firm while build_firm is pending
link_sell/link_buy  dots for supply-chain lines (8u): orange round = selling, blue square = buying,
                    so shape tells them apart as well as colour. The client spaces them along the line.
pending         12u clock badge, drawn at the tile's top-left (+2u, +2u) while a command is queued
Builds art/atlas/marks_atlas{,_64}.png + .json (2 px padding, full tiles edge-extruded) and
docs/art/m2-map-marks-preview.png."""

import os, json, math, random
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(HERE, "..", "..", *a)
C = dict(
    INK="#22262e",
    ORANGE="#e8742a",
    GREEN="#3aa05a",
    DKGREEN="#306f46",
    RED="#c8402e",
    CREAM="#f6ecd4",
    BLUE="#3b6db3",
    DIRT="#b08451",
    DIRT2="#8a5a32",
    SAND="#d4b27f",
    AMBER="#e0862f",
    STEEL="#7a8088",
    LSTEEL="#b8bcc0",
    CONC="#9ba99c",
    DKSTEEL="#58605a",
    WOOD="#a55922",
    WOOD2="#7f5226",
)


def ring(d, N, u, col, dash=None):
    """1u ink, 2u colour, 1u ink from the tile edge inward. dash=(on, off) in u: the colour band
    alternates col and cream, so a dashed outline still reads as one unbroken frame."""

    def sq(o, c):
        a, b = o, N - 1 - o
        d.rectangle([a, a, b, a], C[c])
        d.rectangle([a, b, b, b], C[c])
        d.rectangle([a, a, a, b], C[c])
        d.rectangle([b, a, b, b], C[c])

    for k in range(u):
        sq(k, "INK")
        sq(3 * u + k, "INK")
    for k in range(u, 3 * u):
        if dash is None:
            sq(k, col)
            continue
        a, b = k, N - 1 - k
        per = (dash[0] + dash[1]) * u
        for t in range(a, b + 1):
            c = C[col] if ((t - a) % per) < dash[0] * u else C["CREAM"]
            for xy in ((t, a), (t, b), (a, t), (b, t)):
                d.point(xy, c)


def brackets(im, N, u, col):
    """Thicker L-shaped corners (ink rim, colour core) so the outline reads at a glance."""
    q = Image.new("RGBA", (N, N))
    d = ImageDraw.Draw(q)
    d.rectangle([0, 0, 10 * u - 1, 5 * u - 1], C["INK"])
    d.rectangle([0, 0, 5 * u - 1, 10 * u - 1], C["INK"])
    d.rectangle([u, u, 9 * u - 1, 4 * u - 1], C[col])
    d.rectangle([u, u, 4 * u - 1, 9 * u - 1], C[col])
    for t in (None, Image.FLIP_LEFT_RIGHT, Image.FLIP_TOP_BOTTOM, Image.ROTATE_180):
        im.alpha_composite(q if t is None else q.transpose(t))
    return im


def sel_tile(N, u):
    im = Image.new("RGBA", (N, N))
    ring(ImageDraw.Draw(im), N, u, "ORANGE")
    return brackets(im, N, u, "ORANGE")


def sel_build_ok(N, u):
    im = Image.new("RGBA", (N, N))
    ring(ImageDraw.Draw(im), N, u, "GREEN")
    return brackets(im, N, u, "GREEN")


def no_mark(d, x, y, s, u):
    d.ellipse([x, y, x + s - 1, y + s - 1], C["INK"])
    d.ellipse([x + u, y + u, x + s - 1 - u, y + s - 1 - u], C["RED"])
    d.rectangle([x + 2 * u, y + s // 2 - u, x + s - 1 - 2 * u, y + s // 2 + u - 1], C["CREAM"])


def sel_build_no(N, u):
    im = Image.new("RGBA", (N, N))
    d = ImageDraw.Draw(im)
    ring(d, N, u, "RED", dash=(4, 2))
    no_mark(d, N - 13 * u, 5 * u, 8 * u, u)
    return im


def construction(N, u):
    r = random.Random(N)
    im = Image.new("RGBA", (N, N))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, N - 1, N - 1], C["DIRT"])
    for _ in range(N * N // (12 * u)):  # dirt grain
        x, y = r.randrange(0, N, u), r.randrange(0, N, u)
        d.rectangle([x, y, x + u - 1, y + u - 1], C[r.choice(["DIRT2", "SAND"])])
    # foundation slab with rebar grid and thin front edge
    d.rectangle([6 * u, 8 * u, 25 * u - 1, 22 * u - 1], C["CONC"])
    d.rectangle([6 * u, 22 * u, 25 * u - 1, 23 * u - 1], C["DKSTEEL"])
    for gx in range(8, 25, 4):
        d.rectangle([gx * u, 9 * u, gx * u + (u // 2 or 1) - 1, 21 * u - 1], C["STEEL"])
    for gy in range(10, 22, 4):
        d.rectangle([7 * u, gy * u, 24 * u - 1, gy * u + (u // 2 or 1) - 1], C["STEEL"])
    # tower crane: mast, jib, counterweight, hook
    h = u // 2 if u > 1 else 0
    d.rectangle([22 * u, 4 * u, 24 * u - 1, 24 * u - 1], C["INK"])
    d.rectangle([22 * u + h, 4 * u, 24 * u - 1 - h, 24 * u - 1], C["AMBER"])
    if u > 1:
        for yy in range(5 * u, 24 * u, 3 * u):
            d.line([22 * u + 1, yy, 24 * u - 2, yy + 2 * u], C["INK"])
    d.rectangle([5 * u, 3 * u, 29 * u - 1, 5 * u - 1], C["INK"])
    d.rectangle([5 * u, 3 * u + (h or 1), 29 * u - 1, 5 * u - 1 - h], C["AMBER"])
    d.rectangle([26 * u, 5 * u, 29 * u - 1, 7 * u - 1], C["DKSTEEL"])
    d.rectangle([10 * u, 5 * u, 10 * u + (u // 2 or 1) - 1, 12 * u - 1], C["INK"])
    d.rectangle([9 * u, 12 * u, 12 * u - 1, 13 * u - 1], C["INK"])
    # stacked beams and timber
    d.rectangle([3 * u, 25 * u, 12 * u - 1, 27 * u - 1], C["INK"])
    d.rectangle([3 * u, 25 * u, 12 * u - 1, 26 * u - 1], C["STEEL"])
    d.rectangle([13 * u, 25 * u, 20 * u - 1, 28 * u - 1], C["WOOD2"])
    d.rectangle([13 * u, 25 * u, 20 * u - 1, 26 * u + (u // 2) - 1], C["WOOD"])

    # orange/cream striped barrier along the edge (with ink rim), cones at the gap
    def barrier(x0, y0, x1, y1, horiz):
        """Ink rim, then alternating 2u orange/cream stripes inside it."""
        d.rectangle([x0, y0, x1, y1], C["INK"])
        e = u // 2 if u > 1 else 0
        if horiz:
            ix0, ix1, iy0, iy1 = x0, x1, y0 + e, y1 - e
        else:
            ix0, ix1, iy0, iy1 = x0 + e, x1 - e, y0, y1
        for yy in range(iy0, iy1 + 1):
            for xx in range(ix0, ix1 + 1):
                t = (xx - x0) if horiz else (yy - y0)
                d.point((xx, yy), C["ORANGE" if (t // (2 * u)) % 2 == 0 else "CREAM"])

    barrier(u, u, N - u - 1, 2 * u - 1 + (u > 1) * u, True)
    barrier(u, N - 3 * u, N - 10 * u, N - 2 * u - 1 + (u > 1) * u, True)
    barrier(u, u, 2 * u - 1 + (u > 1) * u, N - 2 * u - 1, False)
    barrier(N - 2 * u - (u > 1) * u, u, N - u - 1, N - 2 * u - 1, False)
    for cx in (N - 8 * u, N - 5 * u):
        if u == 1:  # 2 px cone: orange tip on an ink base
            d.point((cx + 1, N - 4), C["ORANGE"])
            d.rectangle([cx, N - 3, cx + 2, N - 3], C["ORANGE"])
            d.rectangle([cx, N - 2, cx + 2, N - 2], C["INK"])
        else:
            d.polygon(
                [(cx, N - 2 * u), (cx + u, N - 5 * u), (cx + 2 * u, N - 2 * u)],
                C["ORANGE"],
                C["INK"],
            )
    return im


def link(N, u, buy):
    s = 8 * u
    im = Image.new("RGBA", (s, s))
    d = ImageDraw.Draw(im)
    if buy:
        d.rectangle([u, u, s - u - 1, s - u - 1], C["INK"])
        d.rectangle([2 * u, 2 * u, s - 2 * u - 1, s - 2 * u - 1], C["BLUE"])
    else:
        d.ellipse([0, 0, s - 1, s - 1], C["INK"])
        d.ellipse([u + (u > 1), u + (u > 1), s - u - 1 - (u > 1), s - u - 1 - (u > 1)], C["ORANGE"])
    return im


def pending(N, u):
    s = 12 * u
    im = Image.new("RGBA", (s, s))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, s - 1, s - 1], C["INK"])
    d.ellipse([u, u, s - u - 1, s - u - 1], C["CREAM"])
    m = s // 2
    d.rectangle([m - (u // 2 or 1), 2 * u + u // 2, m + u // 2 - (0 if u > 1 else 0), m], C["INK"])
    d.rectangle([m - (u // 2 or 1), m - (u // 2 or 1), s - 3 * u, m + u // 2], C["INK"])
    return im


def build(N):
    u = N // 32
    return {
        "sel_tile": sel_tile(N, u),
        "sel_build_ok": sel_build_ok(N, u),
        "sel_build_no": sel_build_no(N, u),
        "construction": construction(N, u),
        "link_sell": link(N, u, False),
        "link_buy": link(N, u, True),
        "pending": pending(N, u),
    }


def pack(fr, N, path):
    PAD = 2
    CELL = N + 2 * PAD
    names = sorted(fr)
    at = Image.new("RGBA", (len(names) * CELL, CELL))
    meta = {}
    for i, n in enumerate(names):
        im = fr[n]
        c = Image.new("RGBA", (CELL, CELL))
        c.paste(im, (PAD, PAD))
        if im.size == (N, N) and n == "construction":  # opaque tile: extrude edges
            for k in range(PAD):
                c.paste(im.crop((0, 0, N, 1)), (PAD, k))
                c.paste(im.crop((0, N - 1, N, N)), (PAD, PAD + N + k))
            for k in range(PAD):
                c.paste(c.crop((PAD, 0, PAD + 1, CELL)), (k, 0))
                c.paste(c.crop((PAD + N - 1, 0, PAD + N, CELL)), (PAD + N + k, 0))
        at.paste(c, (i * CELL, 0))
        meta[n] = dict(x=i * CELL + PAD, y=PAD, w=im.width, h=im.height)
    at.save(path + ".png")
    json.dump(dict(tile=N, padding=PAD, frames=meta), open(path + ".json", "w"), indent=1)


if __name__ == "__main__":
    pal = {
        tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))
        for h in json.load(open(os.path.join(HERE, "palette.json")))
    }
    sheets = {}
    for N, suf in ((32, ""), (64, "_64")):
        fr = build(N)
        sheets[N] = fr
        for n, im in fr.items():
            bad = {p[:3] for p in im.getdata() if p[3] and p[:3] not in pal}
            assert not bad, (n, N, bad)
            assert not any(0 < p[3] < 255 for p in im.getdata()), (n, "alpha must be 0 or 255")
        pack(fr, N, P("art", "atlas", "marks_atlas" + suf))
    assert set(sheets[32]) == set(sheets[64])
    # preview: each marker on a grass/town patch, 32 px at 2x beside 64 px at 1x, plus a supply line
    T = {}
    for N, suf in ((32, ""), (64, "_64")):
        m = json.load(open(P("art", "atlas", "terrain_atlas" + suf + ".json")))["frames"]
        sh = Image.open(P("art", "atlas", "terrain_atlas" + suf + ".png")).convert("RGBA")
        T[N] = lambda k, m=m, sh=sh: sh.crop(
            (m[k]["x"], m[k]["y"], m[k]["x"] + m[k]["w"], m[k]["y"] + m[k]["h"])
        )

    def scene(N):
        F = T[N]
        cols, rows = 9, 4
        im = Image.new("RGBA", (cols * N, rows * N))
        r = random.Random(5)
        for y in range(rows):
            for x in range(cols):
                im.alpha_composite(F(f"grass_c2_{r.randint(0, 3)}"), (x * N, y * N))
        mk = sheets[N]
        im.alpha_composite(F("firm_factory"), (1 * N, 1 * N))
        im.alpha_composite(mk["sel_tile"], (1 * N, 1 * N))
        im.alpha_composite(F("firm_farm"), (7 * N, 2 * N))
        im.alpha_composite(F("firm_department_store"), (4 * N, 3 * N))
        im.alpha_composite(mk["sel_build_ok"], (3 * N, 0))
        im.alpha_composite(F("forest_c2_1"), (5 * N, 0))
        im.alpha_composite(mk["sel_build_no"], (5 * N, 0))
        im.alpha_composite(mk["construction"], (7 * N, 0))
        im.alpha_composite(mk["pending"], (7 * N + N // 16, N // 16))

        def line(
            a, b, k
        ):  # dots every 12u from firm centre to firm centre, skipping the tiles themselves
            (ax, ay), (bx, by) = a, b
            L = math.hypot(bx - ax, by - ay)
            u = N // 32
            s = mk[k].width
            t = N * 0.6
            while t < L - N * 0.6:
                x = ax + (bx - ax) * t / L
                y = ay + (by - ay) * t / L
                im.alpha_composite(mk[k], (int(x - s / 2), int(y - s / 2)))
                t += 12 * u

        c = lambda tx, ty: (tx * N + N / 2, ty * N + N / 2)
        line(c(1, 1), c(7, 2), "link_buy")
        line(c(1, 1), c(4, 3), "link_sell")
        return im

    a = scene(32).resize((9 * 64, 4 * 64), Image.NEAREST)
    b = scene(64)
    pv = Image.new("RGBA", (a.width * 2 + 24, a.height + 16), (49, 57, 68, 255))
    pv.alpha_composite(a, (8, 8))
    pv.alpha_composite(b, (a.width + 16, 8))
    pv.convert("RGB").save(P("docs", "art", "m2-map-marks-preview.png"))
    print("ok", sorted(sheets[32]))
