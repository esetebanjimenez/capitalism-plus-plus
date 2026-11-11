"""Rebuild the 48 px job icons: tiles/icons/*.png, atlas/icons_atlas.png + .json, docs/art/m2-job-icons-sheet.png."""
import os, sys, json
os.chdir(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,'.')
import icons, terrain as T
from PIL import Image, ImageDraw, ImageFont
os.makedirs('../tiles/icons',exist_ok=True); fr={}
def save(n,im):
    assert all(('#%02x%02x%02x'%c[1][:3]) in T.PAL for c in im.getcolors(4096) if c[1][3]), n
    im.save(f'../tiles/icons/{n}.png'); fr[n]=im
icons.build(save)
cols=8; at=Image.new('RGBA',(cols*48,2*48),(0,0,0,0)); meta={}
for i,n in enumerate(icons.NAMES):
    k='job_'+n; x,y=(i%cols)*48,(i//cols)*48; at.paste(fr[k],(x,y)); meta[k]=dict(x=x,y=y,w=48,h=48)
at.save('../atlas/icons_atlas.png'); json.dump(dict(tile=48,frames=meta),open('../atlas/icons_atlas.json','w'),indent=1)
FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; FN='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
ink=T.H('#22262e'); S=Image.new('RGBA',(8*150+20,2*200+130),T.H('#f6ecd4')+(255,)); d=ImageDraw.Draw(S)
d.text((20,14),'Capitalism++ M2: 16 job icons, 48 px, shown at 2x (left) and 1x (right)',font=ImageFont.truetype(FB,20),fill=ink)
LAB=['Crop Growing','Livestock Raising','Livestock Processing','Logging','Inventory','Private Labelling','Manufacturing','Mining',
     'Oil Extraction','Purchasing','Research & Dev.','Sales','Software Dev.','Software Prod.','Advertising','Import']
for i,n in enumerate(icons.NAMES):
    im=fr['job_'+n]; x,y=20+(i%8)*150,60+(i//8)*200; big=im.resize((96,96),Image.NEAREST)
    S.paste(big,(x,y),big); S.paste(im,(x+100,y+48),im); d.text((x,y+110),LAB[i],font=ImageFont.truetype(FN,14),fill=ink)
d.text((20,450),'Use at 1x in the 3×3 firm slot grid. The 1 px ink outline keeps them readable on the cream panel or the map.',font=ImageFont.truetype(FN,14),fill=ink)
S.convert('RGB').save('../../docs/art/m2-job-icons-sheet.png'); print('ok',len(meta))
