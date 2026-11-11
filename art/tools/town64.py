"""Capitalism++ M2 town tiles at 64 px: the high-density set (B+, same 48-colour palette).
Drawn natively at 64 px, same frame names as town.py. Roads autotile on a 4-bit mask (N=1 E=2 S=4 W=8);
blocks keep the thin front edge (4 px mid-rise, 8 px towers, twice the 32 px heights)."""
import random
from PIL import Image, ImageDraw
from terrain import PAL, H
import town as T32
N=64
C=dict(T32.C); C.update(HI='#58a822',DARK='#313944',ORANGE='#e8742a',AMBER='#e0862f',MAROON='#712b19')
for v in C.values(): assert v in PAL, v
def new(c): return Image.new('RGBA',(N,N),H(C[c])+(255,))
def R(d,b,c,o=None): d.rectangle(b,fill=H(C[c]),outline=H(C[o]) if o else None)
def E(d,b,c,o=None): d.ellipse(b,fill=H(C[c]),outline=H(C[o]) if o else None)
def px(im,x,y,c):
    if 0<=x<N and 0<=y<N: im.putpixel((x,y),H(C[c])+(255,))
def pavement(seed):
    im=new('PAVE'); d=ImageDraw.Draw(im); r=random.Random(seed)
    for i in range(0,N,8): d.line([(i,0),(i,N-1)],fill=H(C['PAVED'])); d.line([(0,i),(N-1,i)],fill=H(C['PAVED']))
    for _ in range(10): px(im,r.randrange(N),r.randrange(N),'PAVED')
    return im
A0,A1=16,47
def road(mask):
    im=pavement(mask); d=ImageDraw.Draw(im); r=random.Random(40+mask)
    R(d,[A0,A0,A1,A1],'ASPH')
    arms={1:[A0,0,A1,A0],2:[A1,A0,N-1,A1],4:[A0,A1,A1,N-1],8:[0,A0,A0,A1]}
    for b,box in arms.items():
        if mask&b: R(d,box,'ASPH')
    a=im.load(); ink=H(C['INK'])+(255,); asp=H(C['ASPH'])+(255,); grey=H(C['GREY'])+(255,)
    near=lambda x,y,c: any(0<=x+dx<N and 0<=y+dy<N and a[x+dx,y+dy]==c for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))
    for y in range(N):  # kerb: ink line, then a grey kerbstone row on the pavement side
        for x in range(N):
            if a[x,y]!=asp and near(x,y,asp): a[x,y]=ink
    for y in range(N):
        for x in range(N):
            if a[x,y] not in (asp,ink) and near(x,y,ink): a[x,y]=grey
    for _ in range(40):  # asphalt grain
        x,y=r.randrange(N),r.randrange(N)
        if a[x,y]==asp: a[x,y]=H(C['ASPHD'])+(255,)
    v=mask&5==5 and not mask&10; h=mask&10==10 and not mask&5
    if v:
        for y in range(4,N,16): R(d,[31,y,32,y+6],'CREAM')
    elif h:
        for x in range(4,N,16): R(d,[x,31,x+6,32],'CREAM')
    elif bin(mask).count('1')>=3:  # junction: zebra crossings on each arm, stop lines
        for b,(x0,y0,hz) in {1:(A0+3,2,1),4:(A0+3,N-9,1),8:(2,A0+3,0),2:(N-9,A0+3,0)}.items():
            if mask&b:
                for i in range(0,26,4): R(d,[x0+i,y0,x0+i+1,y0+6] if hz else [x0,y0+i,x0+6,y0+i+1],'CREAM')
        E(d,[29,29,34,34],'ASPHD','INK')   # manhole
    else:
        for b,box in {1:[31,2,32,10],4:[31,N-11,32,N-3],8:[2,31,10,32],2:[N-11,31,N-3,32]}.items():
            if mask&b: R(d,box,'CREAM')
    if mask:  # street lamps on the pavement corners next to the road
        for cx,cy in ((A0-5,A0-5),(A1+3,A1+3)):
            if a[cx,cy] not in (asp,): E(d,[cx,cy,cx+2,cy+2],'INK'); px(im,cx+1,cy+1,'AMBER')
    return im
ROOFS=[('GLASS','GLASSD'),('GREY','GREYD'),('TAN','TAND'),('BROWN','BROWND')]
def house(im,d,x0,y0,x1,y1,roof,edge,red,r):
    R(d,[x0,y1-2,x1,y1+3],edge,'INK')                                  # front wall
    for x in range(x0+3,x1-3,5): R(d,[x,y1,x+1,y1+1],'WIN')
    R(d,[x0+(x1-x0)//2-1,y1,x0+(x1-x0)//2+1,y1+2],'BROWND')            # door
    rc,rd=('RED','REDD') if red else (roof,edge); mid=(y0+y1)//2-1
    R(d,[x0,y0,x1,mid],rc,'INK'); R(d,[x0,mid,x1,y1-2],rd,'INK')       # pitched roof, lit and shaded halves
    for y in range(y0+2,mid,2): d.line([(x0+1,y),(x1-1,y)],fill=H(C[rd]))
    R(d,[x1-6,y0+2,x1-4,y0+5],'GREYD','INK')                            # chimney
def block(style,level):
    im=pavement(style*3+level); d=ImageDraw.Draw(im); roof,edge=ROOFS[style]; r=random.Random(style*10+level)
    if level==0:
        R(d,[0,0,N-1,N-1],'GRASS')
        for _ in range(30):
            x,y=r.randrange(N),r.randrange(N); px(im,x,y,'GRASSD')
            if r.random()<.3: px(im,x,y-1,'HI')
        lots=[(4,5,27,23),(35,4,59,22),(6,36,28,54),(36,34,57,52)]
        for i,(x0,y0,x1,y1) in enumerate(lots):
            if (style+i)%4==3:
                E(d,[x0+5,y0+4,x1-1,y1+3],'GRASSD'); E(d,[x0+2,y0,x1-4,y1-1],'TREE','INK')
                E(d,[x0+5,y0+3,x0+12,y0+10],'GRASS'); continue
            for x in range(x0-2,x1+3,3): px(im,x,y1+6,'CREAM')          # picket fence
            house(im,d,x0,y0,x1,y1,roof,edge,(style+i)%2,r)
        R(d,[30,0,33,N-1],'SAND')                                       # footpath between the lots
        return im
    e=4 if level==1 else 8
    x0,y0,x1,y1=(6,6,57,55-e) if level==1 else (10,4,53,53-e)
    R(d,[x0+3,y0+3,x1+3,y1+e+3],'PAVED')                               # ground shadow
    R(d,[x0,y1,x1,y1+e],edge,'INK')                                     # front edge = height
    for yy in range(y1+2,y1+e,3):
        for x in range(x0+3,x1-2,4): R(d,[x,yy,x+1,yy],'WIN')
    if level==2: R(d,[(x0+x1)//2-3,y1+e-3,(x0+x1)//2+3,y1+e],'DARK','INK')   # lobby door
    R(d,[x0,y0,x1,y1],roof,'INK')
    d.line([(x0+1,y0+1),(x1-1,y0+1)],fill=H(C['PAVE' if roof!='GLASS' else 'WIN']))   # roof parapet highlight
    if roof=='GLASS':
        for y in range(y0+6,y1,8): d.line([(x0+1,y),(x1-1,y)],fill=H(C['GLASSD']))
        for x in range(x0+10,x1,12): d.line([(x,y0+1),(x,y1-1)],fill=H(C['GLASSD']))
        for x in range(x0+3,x1-3,12): px(im,x,y0+3,'WIN'); px(im,x+1,y0+3,'WIN'); px(im,x,y0+4,'WIN')
    else:
        R(d,[x0+5,y0+5,x0+15,y0+13],'PAVE','INK'); R(d,[x0+7,y0+7,x0+13,y0+11],'GREY')   # plant box
        for k in range(3): R(d,[x1-18+k*5,y1-10,x1-15+k*5,y1-6],'PAVE','INK'); px(im,x1-17+k*5,y1-8,'INK')  # AC units
        R(d,[x0+5,y1-8,x0+10,y1-4],'GREYD','INK')                         # stair hatch
    if level==2:
        if style%2:
            E(d,[x0+14,y0+12,x0+30,y0+28],'GREYD','CREAM')
            d.line([(x0+19,y0+16),(x0+19,y0+24)],fill=H(C['CREAM'])); d.line([(x0+25,y0+16),(x0+25,y0+24)],fill=H(C['CREAM']))
            d.line([(x0+19,y0+20),(x0+25,y0+20)],fill=H(C['CREAM']))      # helipad H
        else:
            d.line([(x1-10,y0+4),(x1-10,y0+18)],fill=H(C['INK'])); d.line([(x1-13,y0+10),(x1-7,y0+10)],fill=H(C['INK']))
            px(im,x1-10,y0+3,'RED'); px(im,x1-10,y0+2,'RED')
    return im
def tree(im,d,x,y,s):
    E(d,[x+3,y+4,x+s+3,y+s+4],'GRASSD'); E(d,[x,y,x+s,y+s],'TREE','INK')
    E(d,[x+3,y+3,x+s*.55,y+s*.55],'GRASS'); px(im,x+5,y+5,'HI'); px(im,x+6,y+5,'HI')
def park(v):
    im=new('GRASS'); d=ImageDraw.Draw(im); r=random.Random(70+v)
    for _ in range(40):
        x,y=r.randrange(N),r.randrange(N); px(im,x,y,'GRASSD')
        if r.random()<.3: px(im,x,y-1,'HI')
    R(d,[0,29,N-1,34],'SAND'); R(d,[29,0,34,N-1],'SAND')
    for i in range(0,N,6): px(im,i,30,'TAN'); px(im,31,i,'TAN')
    for x,y in [(5,5),(41,5),(5,41),(41,41)][: 4 if v==0 else 3]: tree(im,d,x,y,17)
    for bx,by in ((22,22),(38,38)):  # benches by the path
        R(d,[bx,by,bx+5,by+2],'BROWN','INK')
    if v==1:
        E(d,[40,40,59,59],'WATER','INK'); d.arc([43,43,56,56],200,260,fill=H(C['WIN'])); px(im,52,48,'WIN')
    return im
def plaza():
    im=pavement(99); d=ImageDraw.Draw(im)
    for i in range(0,N,8):
        for j in range(0,N,8):
            if (i//8+j//8)%2: R(d,[i+1,j+1,i+7,j+7],'PAVED')
    E(d,[16,16,47,47],'PAVE','INK'); E(d,[20,20,43,43],'GREY','INK'); E(d,[23,23,40,40],'WATER','INK')
    E(d,[29,29,34,34],'PAVE','INK'); px(im,31,27,'WIN'); px(im,32,26,'WIN'); px(im,26,32,'WIN'); px(im,37,31,'WIN')
    d.arc([25,25,38,38],200,250,fill=H(C['WIN']))
    for bx,by,hz in ((6,30,0),(55,30,0),(30,6,1),(30,55,1)):
        R(d,[bx,by,bx+2,by+5] if not hz else [bx,by,bx+5,by+2],'BROWN','INK')
    for x,y in ((4,4),(54,4),(4,54),(54,54)): E(d,[x,y,x+6,y+6],'TREE','INK'); px(im,x+2,y+2,'GRASS')
    return im
def build():
    fr={}
    for m in range(16): fr[f'road_{m:02d}']=road(m)
    for s in range(4):
        for l in range(3): fr[f'block_s{s}_l{l}']=block(s,l)
    for v in range(2): fr[f'park_{v}']=park(v)
    fr['plaza']=plaza()
    return fr
