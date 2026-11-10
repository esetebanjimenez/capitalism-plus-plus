"""Capitalism++ M2 town tiles, concept B+ (32 px, 48-colour palette). Original art drawn in code.
Roads autotile on a 4-bit mask (N=1 E=2 S=4 W=8); blocks have a thin front edge like the firm sprites."""
import sys, os, random
from PIL import Image, ImageDraw
from terrain import PAL, H
C=dict(INK='#22262e',ASPH='#7a8088',ASPHD='#58605a',PAVE='#b8bcc0',PAVED='#9ba99c',CREAM='#f6ecd4',
       GRASS='#5f9e3a',GRASSD='#4a8030',TREE='#2f5e2a',GLASS='#3b6db3',GLASSD='#0d5199',GREY='#868a84',
       GREYD='#58605a',TAN='#d4b27f',TAND='#b08451',BROWN='#8a5a32',BROWND='#53341b',RED='#c8402e',REDD='#ad2816',
       WIN='#9fd3d8',SAND='#e8d6a0',WATER='#2a7f9e')
for v in C.values(): assert v in PAL, v
def new(c): return Image.new('RGBA',(32,32),H(C[c])+(255,))
def R(d,b,c,o=None): d.rectangle(b,fill=H(C[c]),outline=H(C[o]) if o else None)
def px(im,x,y,c):
    if 0<=x<32 and 0<=y<32: im.putpixel((x,y),H(C[c])+(255,))
def pavement(seed):
    im=new('PAVE'); r=random.Random(seed)
    for _ in range(6): px(im,r.randrange(32),r.randrange(32),'PAVED')
    return im
A0,A1=8,23  # asphalt band
def road(mask):
    im=pavement(mask); d=ImageDraw.Draw(im)
    R(d,[A0,A0,A1,A1],'ASPH')
    arms={1:[A0,0,A1,A0],2:[A1,A0,31,A1],4:[A0,A1,A1,31],8:[0,A0,A0,A1]}
    for b,box in arms.items():
        if mask&b: R(d,box,'ASPH')
    a=im.load(); ink=H(C['INK'])+(255,); asp=H(C['ASPH'])+(255,)
    for y in range(32):  # kerb: ink line on pavement pixels touching asphalt
        for x in range(32):
            if a[x,y]!=asp and any(0<=x+dx<32 and 0<=y+dy<32 and a[x+dx,y+dy]==asp for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))):
                a[x,y]=ink
    v=mask&5==5 and not mask&10; h=mask&10==10 and not mask&5
    if v:
        for y in range(2,32,8): R(d,[15,y,16,y+3],'CREAM')
    elif h:
        for x in range(2,32,8): R(d,[x,15,x+3,16],'CREAM')
    elif bin(mask).count('1')>=3:  # junction: zebra crossings on each arm
        for b,(x0,y0,hz) in {1:(A0+2,1,1),4:(A0+2,27,1),8:(1,A0+2,0),2:(27,A0+2,0)}.items():
            if mask&b:
                for i in range(0,13,3): R(d,[x0+i,y0,x0+i+1,y0+3] if hz else [x0,y0+i,x0+3,y0+i+1],'CREAM')
    else:  # corners and dead ends: centre dashes on each arm
        for b,box in {1:[15,1,16,5],4:[15,26,16,30],8:[1,15,5,16],2:[26,15,30,16]}.items():
            if mask&b: R(d,box,'CREAM')
    return im
ROOFS=[('GLASS','GLASSD'),('GREY','GREYD'),('TAN','TAND'),('BROWN','BROWND')]
def block(style,level):
    """level 0..2 = town size (small houses, mid-rise, towers). Thin front edge = building height."""
    im=pavement(style*3+level); d=ImageDraw.Draw(im); roof,edge=ROOFS[style]; r=random.Random(style*10+level)
    if level==0:  # two or three small houses with gardens
        R(d,[0,0,31,31],'GRASS')
        for _ in range(8): px(im,r.randrange(32),r.randrange(32),'GRASSD')
        lots=[(2,3,13,12),(17,2,29,11),(3,18,14,27),(18,17,28,26)]
        for i,(x0,y0,x1,y1) in enumerate(lots):
            if (style+i)%4==3: d.ellipse([x0+1,y0,x1-2,y1-1],fill=H(C['TREE']),outline=H(C['INK'])); continue
            R(d,[x0,y1-1,x1,y1+1],edge,'INK'); R(d,[x0,y0,x1,y1-1],'RED' if (style+i)%2 else roof,'INK')
            d.line([(x0+1,(y0+y1)//2-1),(x1-1,(y0+y1)//2-1)],fill=H(C['REDD' if (style+i)%2 else edge]))
            px(im,x0+3,y1+1,'WIN')
        return im
    e=2 if level==1 else 4  # front edge height
    x0,y0,x1,y1=(3,3,28,27-e) if level==1 else (5,2,26,26-e)
    R(d,[x0,y1,x1,y1+e],edge,'INK')
    for x in range(x0+2,x1-1,3): px(im,x,y1+e-1,'WIN') if e>=2 else None
    R(d,[x0,y0,x1,y1],roof,'INK')
    if roof=='GLASS':
        for y in range(y0+4,y1,5): d.line([(x0+1,y),(x1-1,y)],fill=H(C['GLASSD']))
        for x in range(x0+6,x1,8): d.line([(x,y0+1),(x,y1-1)],fill=H(C['GLASSD']))
    else:  # rooftop plant boxes
        R(d,[x0+3,y0+3,x0+8,y0+7],'PAVE','INK'); R(d,[x1-10,y1-8,x1-4,y1-3],'PAVE','INK'); px(im,x1-7,y1-6,'INK')
    if level==2:  # tower: helipad or antenna
        if style%2: d.ellipse([x0+7,y0+6,x0+15,y0+14],outline=H(C['CREAM'])); px(im,x0+11,y0+10,'CREAM')
        else: d.line([(x1-5,y0+3),(x1-5,y0+9)],fill=H(C['INK'])); px(im,x1-5,y0+2,'RED')
    return im
def park(v):
    im=new('GRASS'); d=ImageDraw.Draw(im); r=random.Random(70+v)
    for _ in range(10): px(im,r.randrange(32),r.randrange(32),'GRASSD')
    d.line([(0,16),(31,16)],fill=H(C['SAND']),width=3); d.line([(16,0),(16,31)],fill=H(C['SAND']),width=3)
    for x,y in [(3,3),(21,3),(3,21),(21,21)][: 4 if v==0 else 3]:
        d.ellipse([x+1,y+2,x+9,y+10],fill=H(C['GRASSD'])); d.ellipse([x,y,x+8,y+8],fill=H(C['TREE']),outline=H(C['INK']))
    if v==1: d.ellipse([20,20,29,29],fill=H(C['WATER']),outline=H(C['INK']))
    return im
def plaza():
    im=pavement(99); d=ImageDraw.Draw(im)
    for i in range(0,32,4): d.line([(i,0),(i,31)],fill=H(C['PAVED']))
    d.ellipse([9,9,22,22],fill=H(C['PAVE']),outline=H(C['INK'])); d.ellipse([12,12,19,19],fill=H(C['WATER']),outline=H(C['INK']))
    px(im,15,15,'WIN'); px(im,16,16,'WIN')
    return im
def build(save):
    for m in range(16): save(f'road_{m:02d}',road(m))
    for s in range(4):
        for l in range(3): save(f'block_s{s}_l{l}',block(s,l))
    for v in range(2): save(f'park_{v}',park(v))
    save('plaza',plaza())
