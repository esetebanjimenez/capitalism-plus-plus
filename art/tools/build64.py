"""Build the 64 px high-density sheet: art/tiles64/{terrain,town}/*.png, art/atlas/terrain_atlas_64.png + .json,
docs/art/m2-terrain-64-preview.png and docs/art/m2-town-64-preview.png. Frame names match the 32 px atlas; each 64 px frame sits in a
68 px cell with its edge pixels repeated 2 px outward, and the JSON x, y, w, h point at the 64 px art only."""
import os, sys, json, math
os.chdir(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,'.')
import terrain64 as T, town64, firms64
from PIL import Image, ImageDraw, ImageFont
N,PAD=64,2; CELL=N+2*PAD
fr=T.build(); tw=town64.build(); fm=firms64.build()
sub={**{n:'terrain' for n in fr},**{n:'town' for n in tw},**{n:('flags' if n.startswith('flag_') else 'firms') for n in fm}}
fr.update(tw); fr.update(fm)
for d_ in set(sub.values()): os.makedirs(f'../tiles64/{d_}',exist_ok=True)
for n,im in fr.items():
    assert im.size==((16,24) if n.startswith('flag_') else (N,N)), n
    assert all(('#%02x%02x%02x'%c[1][:3]) in T.PAL for c in im.getcolors(1<<16) if c[1][3]), n
    im.save(f'../tiles64/{sub[n]}/{n}.png')
lo=json.load(open('../atlas/terrain_atlas.json'))['frames']
missing=[n for n in fr if n not in lo]; assert not missing, missing
def extrude(im):
    if im.size!=(N,N):  # flags: transparent overlay, own cell, top-left at the padding origin
        c=Image.new('RGBA',(CELL,CELL)); c.paste(im,(PAD,PAD)); return c
    c=Image.new('RGBA',(CELL,CELL)); c.paste(im,(PAD,PAD))
    for i in range(PAD):
        c.paste(im.crop((0,0,N,1)),(PAD,i)); c.paste(im.crop((0,N-1,N,N)),(PAD,PAD+N+i))
    for i in range(PAD):
        c.paste(c.crop((PAD,0,PAD+1,CELL)),(i,0)); c.paste(c.crop((PAD+N-1,0,PAD+N,CELL)),(PAD+N+i,0))
    return c
names=sorted(fr); cols=16
at=Image.new('RGBA',(cols*CELL,math.ceil(len(names)/cols)*CELL),(0,0,0,0)); meta={}
for i,n in enumerate(names):
    x,y=(i%cols)*CELL,(i//cols)*CELL; at.paste(extrude(fr[n]),(x,y)); meta[n]=dict(x=x+PAD,y=y+PAD,w=fr[n].width,h=fr[n].height)
at.save('../atlas/terrain_atlas_64.png')
json.dump(dict(tile=64,padding=PAD,frames=meta),open('../atlas/terrain_atlas_64.json','w'),indent=1)
# ---- preview: same terrain map as the 32 px preview, 32 px art at 2x next to 64 px art at 1x ----
W,Hh=14,10
def hv(x,y):
    d=math.hypot((x-6.5)/5.5,(y-4.5)/4)+0.25*math.sin(x*1.8)*math.cos(y*1.4)
    return 'L' if d<0.75 else ('w' if d<1.0 else 'd')
G=[[hv(x,y) for x in range(W)] for y in range(Hh)]
land=lambda x,y: 0<=x<W and 0<=y<Hh and G[y][x]=='L'
clim=lambda y: max(0,min(4,1+y*4//(Hh-1)))
lo_im={n:Image.open(f'../tiles/{sub[n]}/{n}.png').convert('RGBA') for n in fr}
def pick(x,y):
    a=clim(y); b=clim(y+1) if y+1<Hh else a; sfx=f'c{a}' if a==b else f'c{a}c{b}'; c=G[y][x]; v=x*7+y*13
    if c=='L':
        return f'forest_{sfx}_{v%4}' if (x+y*3)%7<2 else (f'hill_{sfx}_{v%2}' if (x*5+y)%11==0 else f'grass_{sfx}_{v%4}')
    m=sum(bit for bit,(dx,dy) in ((1,(0,-1)),(2,(1,0)),(4,(0,1)),(8,(-1,0))) if land(x+dx,y+dy))
    dg=[n for n,(dx,dy),(p,q) in (('ne',(1,-1),((0,-1),(1,0))),('se',(1,1),((1,0),(0,1))),('sw',(-1,1),((0,1),(-1,0))),('nw',(-1,-1),((-1,0),(0,-1))))
        if land(x+dx,y+dy) and not land(x+p[0],y+p[1]) and not land(x+q[0],y+q[1])]
    if c=='d':
        sh=[s for s,(dx,dy) in zip('nesw',((0,-1),(1,0),(0,1),(-1,0))) if 0<=x+dx<W and 0<=y+dy<Hh and G[y+dy][x+dx]=='w']
        return f'shelf_{sh[0]}' if sh else f'deep_{v%3}'
    return 'coast_%02d'%m if m else ('coast_corner_'+dg[0] if dg else f'water_{v%3}')
def render(src,n,atlas=None):
    mp=Image.new('RGBA',(W*n,Hh*n))
    for y in range(Hh):
        for x in range(W):
            k=pick(x,y)
            if atlas:  # cut from the padded atlas exactly as the renderer would
                f=meta[k]; t=atlas.crop((f['x'],f['y'],f['x']+f['w'],f['y']+f['h']))
            else: t=src[k]
            mp.paste(t,(x*n,y*n))
    return mp
a32=render(lo_im,32).resize((W*64,Hh*64),Image.NEAREST); a64=render(None,64,at)
FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; F=lambda s:ImageFont.truetype(FB,s)
cream=T.H('#f6ecd4')+(255,); ink=T.H('#22262e')
S=Image.new('RGBA',(W*64*2+90,Hh*64+520),cream); d=ImageDraw.Draw(S)
d.text((30,14),'Capitalism++ M2: terrain and coast, 32 px set at 2x (left) vs native 64 px high-density set at 1x (right)',font=F(22),fill=ink)
d.text((30,48),'Same map, same size on screen. Right side is cut from the padded 64 px atlas using its JSON frames.',font=F(16),fill=ink)
S.paste(a32,(30,80)); S.paste(a64,(60+W*64,80))
y0=Hh*64+100; d.text((30,y0),'Close-up, enlarged 3x for viewing: coast corner and a climate band edge',font=F(18),fill=ink)
bx=(4*64,1*64,8*64,3*64)
S.paste(a32.crop(bx).resize((768,384),Image.NEAREST),(30,y0+30)); S.paste(a64.crop(bx).resize((768,384),Image.NEAREST),(60+W*64,y0+30))
S.convert('RGB').save('../../docs/art/m2-terrain-64-preview.png'); print(len(names),'frames',at.size)

# ---- town preview: a 7 x 5 town (# layout roads) on grass, 32 px at 2x vs 64 px at 1x ----
TW,TH=9,7; TX,TY=1,1
inT=lambda x,y: TX<=x<TX+7 and TY<=y<TY+5
isroad=lambda x,y: inT(x,y) and ((x-TX)%3==0 or (y-TY)%2==0)
def tpick(x,y):
    if not inT(x,y): return f'grass_c2_{(x*7+y*13)%4}'
    if isroad(x,y): return 'road_%02d'%sum(b for b,(dx,dy) in ((1,(0,-1)),(2,(1,0)),(4,(0,1)),(8,(-1,0))) if isroad(x+dx,y+dy))
    if (x,y)==(TX+4,TY+1): return 'plaza'
    if (x,y)==(TX+5,TY+3): return 'park_1'
    dist=max(abs(x-(TX+3)),abs(y-(TY+2))); lv=2 if dist<=1 else (1 if dist<=2 else 0)
    return f'block_s{(x*7+y*13)%4}_l{lv}'
def trender(n,atlas=None):
    mp=Image.new('RGBA',(TW*n,TH*n))
    for y in range(TH):
        for x in range(TW):
            k=tpick(x,y)
            if atlas: f=meta[k]; t=atlas.crop((f['x'],f['y'],f['x']+f['w'],f['y']+f['h']))
            else: t=lo_im[k]
            mp.paste(t,(x*n,y*n))
    return mp
t32=trender(32).resize((TW*64,TH*64),Image.NEAREST); t64=trender(64,at)
S=Image.new('RGBA',(TW*64*2+90,TH*64+110),cream); d=ImageDraw.Draw(S)
d.text((30,14),'Capitalism++ M2: town tiles, 32 px set at 2x (left) vs native 64 px high-density set at 1x (right)',font=F(22),fill=ink)
d.text((30,48),'Same town, same size on screen. Right side is cut from the padded 64 px atlas using its JSON frames.',font=F(16),fill=ink)
S.paste(t32,(30,80)); S.paste(t64,(60+TW*64,80))
S.convert('RGB').save('../../docs/art/m2-town-64-preview.png')

# ---- firm sheet: each firm on climate-2 grass with its flag, 32 px at 2x (left) vs 64 px at 1x (right), then 3x ----
import firms
lo_f={n:Image.open(f'../tiles/{"flags" if n.startswith("flag_") else "firms"}/{n}.png').convert('RGBA') for n in fm}
def onground(src,g,n,i,k):
    t=g.copy(); f=src['firm_'+n]; t.paste(f,(0,0),f)
    c=Image.new('RGBA',(t.width+k*8,t.height+k*4),(0,0,0,0)); c.paste(t,(0,k*4)); fl=src['flag_%02d'%(i%12)]; c.paste(fl,(k*24,0),fl); return c
S=Image.new("RGBA",(7*340+20,2*200+70),cream); d=ImageDraw.Draw(S)
d.text((20,14),'Capitalism++ M2: 14 firms with owner flags. Each pair: 32 px set (left) vs native 64 px set (right), same size, enlarged 2x for viewing',font=F(18),fill=ink)
FN=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
for i,n in enumerate(firms.NAMES):
    a=onground(lo_f,lo_im['grass_c2_%d'%(i%4)],n,i,1).resize((160,144),Image.NEAREST)
    b=onground(fr,fr['grass_c2_%d'%(i%4)],n,i,2).resize((160,144),Image.NEAREST)
    x,y=20+(i%7)*340,55+(i//7)*200; S.paste(a,(x,y),a); S.paste(b,(x+166,y),b)
    d.text((x,y+150),n.replace('_',' ').replace('rnd','R&D').title(),font=FN,fill=ink)
S.convert('RGB').save('../../docs/art/m2-firms-64-sheet.png')
