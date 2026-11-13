"""#176: firm-type icons for the build menu and panels, plus the goal-met tick.
Decision: firm-type icons reuse the map sprites (`firm_*` in terrain_atlas / terrain_atlas_64), shown in a
32 pt cell, so each type looks the same in menus as on the map and stays pixel-native on every screen
(32 px sheet at 1x, 64 px sheet at 2x, 64 px at 1.5x nearest on 3x, as on the map). No separate 48 px set.
Unaffordable rows draw the sprite at 50% opacity and the shortfall in RED; the goal tick is icon_goal in ui_atlas.
Writes docs/art/m2-build-menu-preview.png (example cash $4.8M and land value $500k, read from capitalism.db)."""

import json, os, sqlite3
from PIL import Image, ImageDraw
from ui_concept import card, button, icon, C, P, font
from ui_controls import nine


def rgb(k):
    return tuple(int(C[k][i : i + 2], 16) for i in (1, 3, 5)) + (255,)


def money(v):
    return f"${v / 1e6:.1f}M" if v >= 1e6 else f"${v / 1e3:,.0f}k"


if __name__ == "__main__":
    meta = json.load(open(P("art", "atlas", "terrain_atlas_64.json")))["frames"]
    sheet = Image.open(P("art", "atlas", "terrain_atlas_64.png")).convert("RGBA")
    spr = lambda k: sheet.crop((meta[k]["x"], meta[k]["y"], meta[k]["x"] + 64, meta[k]["y"] + 64))
    db = sqlite3.connect(P("src", "capitalism", "data", "capitalism.db"))
    rows = [
        r
        for r in db.execute(
            'select name, setup_cost, overhead_month from firm_types where government = 0 and name != "Seaport" order by id'
        )
    ]
    keys = {
        "Department Store": "department_store",
        "R&D Center": "rnd_center",
        "Television Station": "television_station",
    }
    cash, land = 4_812_300, 500_000
    S = 2
    W = 360
    RH = 44
    H = 64 + RH * len(rows) + 40
    im = Image.new("RGBA", (W * S, H * S), rgb("DGREY"))
    d = ImageDraw.Draw(im)

    def put(part, x, y):
        im.alpha_composite(
            part.resize((part.width * S, part.height * S), Image.NEAREST), (x * S, y * S)
        )

    def txt(x, y, s, col="INK", pt=13, bold=True, anchor="la"):
        d.text((x * S, y * S), s, font=font(pt, S, bold), fill=rgb(col), anchor=anchor)

    put(nine(card(16, 16), [6, 6, 6, 7], W - 20, H - 20), 10, 10)
    txt(24, 22, "Build here", pt=15)
    txt(W - 24, 24, "Cash " + f"${cash:,}", "MGREY", 12, False, "ra")
    for i, (name, setup, ovh) in enumerate(rows):
        y = 52 + i * RH
        cost = setup + land
        ok = cash >= cost
        k = "firm_" + keys.get(name, name.lower().replace(" ", "_"))
        s = spr(k)
        if not ok:
            a = s.getchannel("A").point(lambda v: v // 2)
            s.putalpha(a)
        im.alpha_composite(s, ((24) * S, (y + 4) * S))  # 32 pt cell = 64 px at 2x, native
        txt(64, y + 6, name, "INK" if ok else "MGREY")
        txt(64, y + 24, f"{money(ovh)}/month", "MGREY", 11, False)
        txt(W - 24, y + 6, money(cost), "INK" if ok else "MGREY", 13, True, "ra")
        if not ok:
            txt(W - 24, y + 24, f"short {money(cost - cash)}", "RED", 11, True, "ra")
        if i:
            d.line([(24 * S, (y - 1) * S), ((W - 24) * S, (y - 1) * S)], fill=rgb("SAND"), width=S)
    gy = 52 + RH * len(rows) + 6
    put(icon("goal"), 24, gy)
    txt(46, gy + 1, "Goal met: reach $10M cash (example)", "GREEN", 12)
    im.convert("RGB").save(P("docs", "art", "m2-build-menu-preview.png"), optimize=True)
