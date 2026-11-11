"""Far overview colours, overlay colour scales and legend preview (M2 missing-art item 2).
Writes art/overlays.json (the client reads colours from it; every colour is in palette.json) and
docs/art/m2-overlays-preview.png, drawn from the real sim world of the sample-map seed.
Overlay toggle icons (icon_ov_*) live in ui_concept.ICON and ship in ui_atlas."""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'src'))
import terrain as T
from firms import FLAGS

FAR = {  # 1 px per tile overview, by TileCategory
    'deep_ocean': '#14234a', 'water': '#2a7f9e',
    'grassland': [c[0] for c in T.CLIM],      # by climate 0 (poles) .. 4 (equator), same base as the tiles
    'forest_hill': [c[3] for c in T.CLIM],
    'town': '#b8bcc0', 'town_centre': '#22262e', 'firm_unowned': '#f6ecd4',
    'firm_owner': FLAGS,                       # owner corp colour, same order as flag_00..11 (00 = player)
}
OVERLAYS = {
    'land_value': {'label': 'Land value', 'steps': ['#f6ecd4', '#f6d9a8', '#d4b27f', '#e0862f', '#c8402e', '#712b19'],
                   'bins': 'see rules.land_value_bins; legend shows bin edges as money'},
    'soil': {'label': 'Soil', 'steps': ['#e8d6a0', '#b08451', '#8a5a32', '#53341b'], 'values': [0, 1, 2, 3],
             'names': ['Poor', 'Fair', 'Good', 'Rich']},
    'rainfall': {'label': 'Rainfall', 'steps': ['#e8d6a0', '#9fd3d8', '#3b6db3', '#0d5199', '#122234'], 'values': [0, 1, 2, 3, 4],
                 'names': ['Dry', 'Low', 'Medium', 'High', 'Wet']},
    'climate': {'label': 'Climate', 'steps': ['#f6ecd4', '#9fd3d8', '#b6d0a8', '#e0862f', '#c8402e'], 'values': [0, 1, 2, 3, 4],
                'names': ['Polar', 'Cold', 'Mild', 'Warm', 'Tropical']},
    'ownership': {'label': 'Ownership', 'steps': FLAGS, 'note': 'firm tiles only, by owner corp; unowned and other tiles untinted'},
}
RULES = {'alpha_standard': 0.7, 'alpha_far': 1.0,
         'water_in_overlay_far': {'deep_ocean': '#313944', 'water': '#58605a'},
         'land_value_bins': 'step 0 = the floor value; steps 1-5 = equal-count bins over tiles above the floor', 'applies_to': 'land tiles (grassland, forest/hill, town); water and deep ocean are never tinted',
         'firms': 'firm sprites stay untinted on value overlays so the map stays readable; ownership tints only firm tiles',
         'legend': 'card frame from ui_atlas at the bottom-left above the safe area; one swatch (16 pt, 2 pt ink rim) per step plus live text'}

def check():
    pal = set(json.load(open(os.path.join(HERE, 'palette.json'))))
    cols = [v for v in FAR.values() for v in (v if isinstance(v, list) else [v])] + [c for o in OVERLAYS.values() for c in o['steps']]
    bad = [c for c in cols if c not in pal]; assert not bad, bad

def world():
    from capitalism.scenario import bread_town, build_bread_chain, find_site
    from capitalism.economy import CORP_AI
    from capitalism.firms import FIRM_CLASSES
    from capitalism.town import population_for_level
    sim, town = bread_town(1); big = sim.towns[1]; big.population = population_for_level(5); big.level = 5
    build_bread_chain(sim, town); eco = sim.economy
    corps = [eco.corps[0], eco.add_corp('Rival A', CORP_AI), eco.add_corp('Rival B', CORP_AI)]
    have = {f.type_id for f in eco.firms if f is not None}
    for i, t in enumerate(sorted(set(FIRM_CLASSES) - have)):
        x, y = find_site(sim, town, town.level + 3); eco.build_firm(t, corps[i % 3], x, y, town)
    return sim

def rgb(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
def mix(a, b, t): return tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))

def render(sim, mode):
    w = sim.world; W, H = w.width, w.height; im = Image.new('RGB', (W, H)); a = im.load()
    firms = {(f.x, f.y): f for f in sim.economy.firms if f is not None}
    towns = {(t.x, t.y) for t in sim.towns}
    lv = None
    if mode == 'land_value':
        vals = sorted(w.land_value(x, y) for y in range(H) for x in range(W) if int(w.tiles[y * W + x].kind) in (2, 3, 4))
        fl = vals[0]; up = [v for v in vals if v > fl]
        edges = [fl + 1] + [up[len(up) * k // 5] for k in range(1, 5)]
    for y in range(H):
        for x in range(W):
            t = w.tiles[y * W + x]; k = int(t.kind)
            if k == 0: c = RULES['water_in_overlay_far']['deep_ocean'] if mode else FAR['deep_ocean']
            elif k == 1: c = RULES['water_in_overlay_far']['water'] if mode else FAR['water']
            elif k == 2: c = FAR['grassland'][t.climate]
            elif k == 3: c = FAR['forest_hill'][t.climate]
            elif k == 5:
                f = firms.get((x, y)); c = FAR['firm_owner'][f.owner.id % 12] if f and f.owner is not None else FAR['firm_unowned']
            else: c = FAR['town_centre'] if (x, y) in towns else FAR['town']
            px = rgb(c)
            if mode and k in (2, 3, 4) and mode != 'ownership':
                if mode == 'land_value':
                    v = w.land_value(x, y); i = sum(v >= e for e in edges); o = OVERLAYS['land_value']['steps'][i]
                else: o = OVERLAYS[mode]['steps'][getattr(t, mode)]
                px = rgb(o)  # far view: solid (alpha_far 1.0)
            a[x, y] = px
    return im

if __name__ == '__main__':
    check()
    json.dump({'far': FAR, 'overlays': OVERLAYS, 'rules': RULES}, open(os.path.join(ROOT, 'art', 'overlays.json'), 'w'), indent=1)
    sim = world(); S = 2; F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
    Fr = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    modes = [(None, 'Far overview, 1 px per tile')] + [(k, v['label'] + ' overlay') for k, v in OVERLAYS.items() if k != 'ownership']
    mw, mh = sim.world.width * S, sim.world.height * S; pad = 16; cols = 3
    sheet = Image.new('RGB', (cols * (mw + pad) + pad, 2 * (mh + 120) + pad), rgb('#313944')); d = ImageDraw.Draw(sheet)
    for i, (m, lab) in enumerate(modes):
        x = pad + (i % cols) * (mw + pad); y = pad + (i // cols) * (mh + 120)
        sheet.paste(render(sim, m).resize((mw, mh), Image.NEAREST), (x, y + 22)); d.text((x, y), lab, font=F, fill=rgb('#f6ecd4'))
        steps = OVERLAYS[m]['steps'] if m else None
        names = (OVERLAYS[m].get('names') or ['low', '', '', '', '', 'high']) if m else None
        if m:
            for j, c in enumerate(steps):
                sx = x + j * 74; sy = y + mh + 32
                d.rectangle([sx, sy, sx + 19, sy + 19], fill=rgb('#22262e')); d.rectangle([sx + 2, sy + 2, sx + 17, sy + 17], fill=rgb(c))
                d.text((sx + 24, sy + 2), names[j], font=Fr, fill=rgb('#e8d6a0'))
        else:
            d.text((x, y + mh + 32), 'Towns grey with a dark centre, firms in owner colour', font=Fr, fill=rgb('#e8d6a0'))
    from ui_concept import icon
    x0 = pad + 2 * (mw + pad); y0 = pad + mh + 120; d.text((x0, y0), 'Overlay toggle icons (ui_atlas icon_ov_*), 3x', font=F, fill=rgb('#f6ecd4'))
    for j, (k, lab) in enumerate([('ov_none', 'None'), ('ov_land', 'Land value'), ('ov_soil', 'Soil'), ('ov_rain', 'Rainfall'), ('ov_climate', 'Climate'), ('ov_owner', 'Ownership')]):
        cx = x0 + (j % 3) * 150; cy = y0 + 40 + (j // 3) * 110
        d.rectangle([cx, cy, cx + 59, cy + 59], fill=rgb('#e8d6a0'))
        sheet.paste(icon(k).resize((48, 48), Image.NEAREST), (cx + 6, cy + 6), icon(k).resize((48, 48), Image.NEAREST))
        d.text((cx, cy + 66), lab, font=Fr, fill=rgb('#e8d6a0'))
    sheet.save(os.path.join(ROOT, 'docs', 'art', 'm2-overlays-preview.png'))
    print('ok', sim.world.width, sim.world.height)
