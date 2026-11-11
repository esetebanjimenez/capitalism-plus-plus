"""Production UI parts for the clear-map layout (concept approved by Esteban 2026-11-11, PR #65).
Builds art/atlas/ui_atlas.png (1 px per point, for 1x screens) and ui_atlas_2x.png (same layout,
nearest x2, for 2x and 3x screens) plus ui_atlas.json. Frames are on a 1 pt grid; JSON x/y/w/h are
in 1x pixels (multiply by 2 for the 2x sheet). Nine-slice frames carry `slice` [left, top, right, bottom]
in points for CSS border-image or a canvas nine-slice. Text, counts and numbers are drawn live."""
import json, os
from PIL import Image
from ui_concept import card, button, slot, handle, badge, icon, ICON, cream, P

def frames():
    f = {}
    f['card'] = (card(16, 16), [6, 6, 6, 7])                      # panels, side panel, report window, cards
    f['card_float'] = (card(16, 16, alpha=232), [6, 6, 6, 7])     # pill, menu button, toast
    f['sheet_top'] = (card(16, 16, top_only=True), [6, 6, 6, 1])  # phone bottom sheet, bottom open
    for k in ('primary', 'secondary', 'danger', 'disabled'):
        f['btn_' + k] = (button(16, 16, k), [6, 6, 6, 8])
        f['btn_' + k + '_down'] = (pressed(k), [6, 8, 6, 6])
    f['tab_line'] = (Image.new('RGBA', (4, 3), (232, 116, 42, 255)), [1, 0, 1, 0])
    f['handle'] = (handle(), None)
    for k in ('empty', 'filled', 'selected'): f['slot_' + k] = (slot(k), None)  # 72 pt cells
    f['badge'] = (badge(0), None)
    f['chip'] = (card(20, 20, 'INK', 'INK', shadow=False), None)  # rating chip in a slot
    for k in ICON: f['icon_' + k] = (icon(k), None)
    for k in ('play', 'ff', 'pause'): f['icon_' + k + '_on'] = (cream(icon(k)), None)  # on orange buttons
    return f

def pressed(k):
    """Pressed state: face drops 2 pt onto its lip."""
    b = button(16, 16, k); out = Image.new('RGBA', b.size, (0, 0, 0, 0))
    out.alpha_composite(b.crop((0, 0, 16, 16)), (0, 2)); return out

def build():
    fr = frames(); gap = 2; W = 256; x = y = gap; rowh = 0; place = {}
    for name, (im, sl) in fr.items():
        if x + im.width + gap > W: x = gap; y += rowh + gap; rowh = 0
        place[name] = (x, y, im, sl); x += im.width + gap; rowh = max(rowh, im.height)
    H = y + rowh + gap
    sheet = Image.new('RGBA', (W, H), (0, 0, 0, 0)); meta = {'scale': 1, 'frames': {}}
    for name, (x, y, im, sl) in place.items():
        sheet.alpha_composite(im, (x, y))
        meta['frames'][name] = dict(x=x, y=y, w=im.width, h=im.height, **({'slice': sl} if sl else {}))
    os.makedirs(P('art', 'atlas'), exist_ok=True)
    sheet.save(P('art', 'atlas', 'ui_atlas.png'), optimize=True)
    sheet.resize((W * 2, H * 2), Image.NEAREST).save(P('art', 'atlas', 'ui_atlas_2x.png'), optimize=True)
    json.dump(meta, open(P('art', 'atlas', 'ui_atlas.json'), 'w'), indent=1)
    # preview at 4x on dark
    pv = Image.new('RGBA', (W * 4, H * 4), (49, 57, 68, 255)); pv.alpha_composite(sheet.resize((W * 4, H * 4), Image.NEAREST))
    pv.convert('RGB').save(P('docs', 'art', 'm2-ui-atlas-preview.png'), optimize=True)
    return sheet, meta

if __name__ == '__main__':
    s, m = build()
    pal = {tuple(int(h[i:i+2], 16) for i in (1, 3, 5)) for h in json.load(open(P('art', 'tools', 'palette.json')))}
    bad = {px[:3] for px in s.getdata() if px[3] and px[:3] not in pal}
    assert not bad, bad
    print(len(m['frames']), 'frames', s.size)
