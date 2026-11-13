"""M2 item 3: extra UI controls on the same 1 pt grid as ui_concept (cream cards, 2 pt ink border,
stepped corners, palette colours only). ui_build.py adds these frames to ui_atlas. Text is live."""

from PIL import Image, ImageDraw
from ui_concept import card, button, icon, C


def rgb(k):
    return tuple(int(C[k][i : i + 2], 16) for i in (1, 3, 5)) + (255,)


def bar(fill):
    """Track or fill for sliders and progress bars, 12 pt tall, nine-slice [4,4,4,4]."""
    return card(12, 12, fill, "INK", shadow=False)


def knob():
    """Slider thumb: 20 pt cream button with its 2 pt lip (22 tall), centred on the value."""
    return button(20, 20, "secondary")


def chip(on):
    """Filter chip, 32 pt tall when sliced: cream when off, orange when on. nine-slice [6,6,6,6]."""
    return card(16, 16, "ORANGE" if on else "CREAM", "INK", shadow=False)


def switch(on):
    """On/off switch, 44x24 (tap area 44x44): ink track grey or green, cream knob on the left or right."""
    im = card(44, 24, "GREEN" if on else "MGREY", "INK", shadow=False)
    k = card(16, 16, "CREAM", "INK", shadow=False)
    im.alpha_composite(k, (24 if on else 4, 4))
    return im


def field(state):
    """Text field: cream with a 2 pt border, ink normally, orange when focused, red on error. nine-slice [6,6,6,6]."""
    return card(
        16, 16, "CREAM", {"normal": "INK", "focus": "ORANGE", "error": "RED"}[state], shadow=False
    )


def caret():
    im = Image.new("RGBA", (2, 16), rgb("INK"))
    return im


def toast_error():
    """Error toast: floating cream card with a 6 pt red band on the left for the warn icon area.
    nine-slice [10,6,6,7]; draw icon_warn 12 pt in from the left edge of the band, vertically centred."""
    im = card(24, 16, "CREAM", "INK", alpha=232)
    a = im.load()
    for y in range(2, 14):
        for x in range(2, 8):
            if a[x, y][3]:
                a[x, y] = rgb("RED")
    for y in range(0, 16):  # keep the stepped ink corner crisp
        for x in range(0, 4):
            if (x, y) in ((2, 2), (2, 13)):
                a[x, y] = rgb("INK")
    return im


def nine(im, sl, w, h):
    l, t, r, b = sl
    W, H = im.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    xs = [(0, l, 0, l), (l, W - r, l, w - r), (W - r, W, w - r, w)]
    ys = [(0, t, 0, t), (t, H - b, t, h - b), (H - b, H, h - b, h)]
    for sx0, sx1, dx0, dx1 in xs:
        for sy0, sy1, dy0, dy1 in ys:
            if dx1 > dx0 and dy1 > dy0 and sx1 > sx0 and sy1 > sy0:
                out.alpha_composite(
                    im.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST),
                    (dx0, dy0),
                )
    return out


if __name__ == "__main__":
    from ui_concept import P, font

    S = 3
    W, H = 360, 330
    im = Image.new("RGBA", (W * S, H * S), (49, 57, 68, 255))
    d = ImageDraw.Draw(im)

    def put(part, x, y):
        im.alpha_composite(
            part.resize((part.width * S, part.height * S), Image.NEAREST), (x * S, y * S)
        )

    def txt(x, y, s, col="INK", pt=12, bold=True):
        d.text((x * S, y * S), s, font=font(pt, S, bold), fill=rgb(col))

    put(nine(card(16, 16), [6, 6, 6, 7], 340, 252), 10, 10)
    txt(24, 22, "Bakery, Sales", pt=14)
    txt(24, 48, "Price  $4.20")
    put(nine(bar("SAND"), [4] * 4, 300, 12), 24, 70)
    put(nine(bar("ORANGE"), [4] * 4, 180, 12), 24, 70)
    put(knob(), 194, 66)
    txt(24, 94, "Show")
    for i, (lab, on) in enumerate((("All", False), ("Mine", True), ("Rivals", False))):
        w = 70
        put(nine(chip(on), [6] * 4, w, 32), 24 + i * (w + 8), 112)
        txt(
            24 + i * (w + 8) + (w - d.textlength(lab, font=font(12, S)) / S) // 2,
            120,
            lab,
            "CREAM" if on else "INK",
        )
    txt(24, 158, "Auto-restock")
    put(switch(True), 280, 152)
    txt(24, 186, "Advertise")
    put(switch(False), 280, 180)
    put(nine(field("focus"), [6] * 4, 300, 36), 24, 212)
    txt(36, 222, "Corner Bakery", bold=False)
    put(caret(), 132, 222)
    put(nine(bar("SAND"), [4] * 4, 160, 12), 10, 276)
    put(nine(bar("GREEN"), [4] * 4, 112, 12), 10, 276)
    txt(178, 274, "Building 70%", "CREAM")
    t = nine(toast_error(), [10, 6, 6, 7], 340, 30)
    put(t, 10, 296)
    put(icon("warn"), 22, 303)
    txt(46, 304, "Not enough cash to build", pt=12)
    im.convert("RGB").save(P("docs", "art", "m2-ui-controls-preview.png"), optimize=True)
