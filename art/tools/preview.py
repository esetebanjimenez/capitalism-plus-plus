"""Rebuild every M2 tile into one atlas, kept as terrain_atlas.* so the renderer path does not change.
Rebuild every M2 tile PNG, the packed atlas + JSON, and docs/art/m2-tiles-preview.png."""
import os, sys, json, math
os.chdir(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,'.')
import terrain as T, town
from PIL import Image, ImageDraw, ImageFont
fr={}
def saver(sub):
    os.makedirs(f'../tiles/{sub}',exist_ok=True)
    def save(n,im):
        assert all(('#%02x%02x%02x'%c[1][:3]) in T.PAL for c in im.getcolors(4096) if c[1][3]), n
        im.save(f'../tiles/{sub}/{n}.png'); fr[n]=im
    return save
T.build('../tiles/terrain'); [fr.__setitem__(f[:-4],Image.open(f'../tiles/terrain/{f}').convert('RGBA')) for f in os.listdir('../tiles/terrain')]
town.build(saver('town'))
import firms
firms.build(saver('firms'),saver('flags'))
flags=sorted(n for n in fr if n.startswith('flag_'))
names=sorted(n for n in fr if n not in flags); cols=16; ncell=len(names)+math.ceil(len(flags)/8)
at=Image.new('RGBA',(cols*32,math.ceil(ncell/cols)*32),(0,0,0,0)); meta={}
for i,n in enumerate(names):
    x,y=(i%cols)*32,(i//cols)*32; at.paste(fr[n],(x,y)); meta[n]=dict(x=x,y=y,w=32,h=32)
for j,n in enumerate(flags):  # 8 x 12 flags, eight to a 32 px cell (4 x 2 grid)
    c=len(names)+j//8; k=j%8; x=(c%cols)*32+(k%4)*8; y=(c//cols)*32+(k//4)*12
    at.paste(fr[n],(x,y)); meta[n]=dict(x=x,y=y,w=8,h=12)
os.makedirs('../atlas',exist_ok=True)
at.save('../atlas/terrain_atlas.png'); json.dump(dict(tile=32,frames=meta),open('../atlas/terrain_atlas.json','w'),indent=1)
# ---- sample map ----
W,Hh=28,20
def hv(x,y):
    d=math.hypot((x-13.5)/11,(y-9.5)/8)+0.25*math.sin(x*.9)*math.cos(y*.7)
    return 'L' if d<0.75 else ('w' if d<1.0 else 'd')
G=[[hv(x,y) for x in range(W)] for y in range(Hh)]
TX,TY=9,10  # town origin, 7x5
for y in range(TY,TY+5):
    for x in range(TX,TX+7): G[y][x]='T'
land=lambda x,y: 0<=x<W and 0<=y<Hh and G[y][x] in 'LT'
isroad=lambda x,y: G[y][x]=='T' and ((x-TX)%3==0 or (y-TY)%2==0) if 0<=x<W and 0<=y<Hh else False
clim=lambda y: 4-min(4,abs(y-9)*5//10)
mp=Image.new('RGBA',(W*32,Hh*32))
for y in range(Hh):
    a=clim(y); b=clim(y+1) if y+1<Hh else a; sfx=f'c{a}' if a==b else f'c{a}c{b}'
    for x in range(W):
        c=G[y][x]; v=x*7+y*13
        if c=='T':
            if isroad(x,y): t=fr['road_%02d'%sum(bit for bit,(dx,dy) in ((1,(0,-1)),(2,(1,0)),(4,(0,1)),(8,(-1,0))) if isroad(x+dx,y+dy))]
            else:
                dist=max(abs(x-(TX+3)),abs(y-(TY+2))); lv=2 if dist<=1 else (1 if dist<=2 else 0)
                t=fr['park_0'] if (x,y)==(TX+5,TY+3) else fr[f'block_s{v%4}_l{lv}']
        elif c=='L':
            t=fr[f'forest_{sfx}_{v%4}'] if (x+y*3)%9<2 or (x>15 and y<8) else (fr[f'hill_{sfx}_{v%2}'] if (x*5+y)%23==0 else fr[f'grass_{sfx}_{v%4}'])
        else:
            m=sum(bit for bit,(dx,dy) in ((1,(0,-1)),(2,(1,0)),(4,(0,1)),(8,(-1,0))) if land(x+dx,y+dy))
            dg=[n for n,(dx,dy),(p,q) in (('ne',(1,-1),((0,-1),(1,0))),('se',(1,1),((1,0),(0,1))),('sw',(-1,1),((0,1),(-1,0))),('nw',(-1,-1),((-1,0),(0,-1))))
                if land(x+dx,y+dy) and not land(x+p[0],y+p[1]) and not land(x+q[0],y+q[1])]
            if c=='d':
                sh=[s for s,(dx,dy) in zip('nesw',((0,-1),(1,0),(0,1),(-1,0))) if 0<=x+dx<W and 0<=y+dy<Hh and G[y+dy][x+dx]=='w']
                t=fr[f'shelf_{sh[0]}'] if sh else fr[f'deep_{v%3}']
            elif m: t=fr['coast_%02d'%m]
            elif dg: t=fr['coast_corner_'+dg[0]]
            else: t=fr[f'water_{v%3}']
        mp.paste(t,(x*32,y*32))
FIRMS=[(5,6,'department_store',0),(7,8,'factory',1),(17,6,'rnd_center',2),(4,10,'farm',0),(18,4,'logging_camp',3),
       (19,9,'mine',1),(21,12,'oil_well',0),(17,11,'software_developer',2),(16,13,'software_publisher',0),
       (11,15,'restaurant',3),(8,8,'television_station',0),(14,6,'radio_station',1),(6,12,'newspaper_publisher',2)]
for x,y,n,o in FIRMS:
    f=fr['firm_'+n]; mp.paste(f,(x*32,y*32),f); g=fr[f'flag_{o:02d}']; mp.paste(g,(x*32+24,y*32-4),g)
for x in range(W):
    if G[16][x]=='w' and G[15][x]=='L': mp.paste(fr['firm_seaport'],(x*32,16*32),fr['firm_seaport']); g=fr['flag_00']; mp.paste(g,(x*32+24,16*32-4),g); break
FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; F=lambda n:ImageFont.truetype(FB,n)
cream=T.H('#f6ecd4')+(255,); ink=T.H('#22262e')
S=Image.new('RGBA',(W*64+60,Hh*64+at.height*2+180),cream); d=ImageDraw.Draw(S)
d.text((30,16),'Capitalism++ M2 production: terrain, coast, town, 14 firms and owner flags (B+, 32 px, 48 colours), shown at 2x',font=F(24),fill=ink)
S.paste(mp.resize((W*64,Hh*64),Image.NEAREST),(30,60))
d.text((30,Hh*64+80),f'Atlas: {len(names)} tiles, transparent where empty',font=F(20),fill=ink)
big=at.resize((at.width*2,at.height*2),Image.NEAREST); S.paste(big,(30,Hh*64+115),big)
S.convert('RGB').save('../../docs/art/m2-tiles-preview-2.png'); print(len(names),'tiles',at.size)
# ---- firm review sheet: each firm on grass at 4x, with its flag ----
FN='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
sh=Image.new('RGBA',(7*170+20,2*190+70),cream); d=ImageDraw.Draw(sh)
d.text((20,14),'Capitalism++ M2: 14 firm sprites, 32 px, shown at 4x on climate-2 grass with an owner flag',font=F(20),fill=ink)
for i,n in enumerate(firms.NAMES):
    g=fr['grass_c2_%d'%(i%4)].copy(); f=fr['firm_'+n]; g.paste(f,(0,0),f)
    c=Image.new('RGBA',(40,40),(0,0,0,0)); c.paste(g,(0,4)); fl=fr['flag_%02d'%(i%12)]; c.paste(fl,(24,0),fl)
    x,y=20+(i%7)*170,55+(i//7)*190; sh.paste(c.resize((160,160),Image.NEAREST),(x,y),c.resize((160,160),Image.NEAREST))
    d.text((x,y+162),n.replace('_',' ').replace('rnd','R&D').title().replace('R&D','R&D'),font=ImageFont.truetype(FN,15),fill=ink)
sh.convert('RGB').save('../../docs/art/m2-firms-sheet.png')
