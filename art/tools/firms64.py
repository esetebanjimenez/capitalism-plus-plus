"""Capitalism++ M2 firm sprites and owner flags at 64 px: the high-density set (B+, same 48-colour palette).
Same lots and layout as firms.py, redrawn at 64 px with 1 px ink outlines and the extra detail the size allows
(window rows, roof plant, vehicles, textures). Same frame names. Flags are 16 x 24, drawn at (+48, -8)."""
import random, math
from PIL import Image, ImageDraw
from terrain import PAL, H
import firms as F32
C=dict(F32.C); C.update(GREYD='#58605a',HI='#58a822',TROUGH='#122234')
for v in C.values(): assert v in PAL, v
N=64
class S:
    """Coordinates are on the 32 px grid (so lots line up with the 32 px set); lines and outlines stay 1 px."""
    def __init__(s): s.im=Image.new('RGBA',(N,N),(0,0,0,0)); s.d=ImageDraw.Draw(s.im)
    @staticmethod
    def b(b): return [b[0]*2,b[1]*2,b[2]*2+1,b[3]*2+1]
    def R(s,b,c,o=None): s.d.rectangle(s.b(b),fill=H(C[c]),outline=H(C[o]) if o else None)
    def E(s,b,c,o=None): s.d.ellipse(s.b(b),fill=H(C[c]),outline=H(C[o]) if o else None)
    def L(s,p,c,w=1): s.d.line([(x*2+.5,y*2+.5) for x,y in p],fill=H(C[c]),width=1 if c=='INK' and w==1 else 2*w)
    def P(s,x,y,c):  # native 64 px pixel
        if 0<=x<N and 0<=y<N: s.im.putpixel((x,y),H(C[c])+(255,))
    def r(s,b,c,o=None): s.d.rectangle(b,fill=H(C[c]),outline=H(C[o]) if o else None)   # native rect
    def e(s,b,c,o=None): s.d.ellipse(b,fill=H(C[c]),outline=H(C[o]) if o else None)     # native ellipse
    def l(s,p,c,w=1): s.d.line(p,fill=H(C[c]),width=w)                                   # native line
    def lot(s,c,b=(1,2,30,30),speck=None,seed=0,n=40):
        s.R(b,c); x0,y0,x1,y1=s.b(b)
        if speck:
            rr=random.Random(seed)
            for _ in range(n): s.P(rr.randrange(x0+1,x1),rr.randrange(y0+1,y1),speck)
    def bld(s,x0,y0,x1,y1,roof,wall,e=3,win='WIN',door=None,roofd=None):
        X0,Y0,X1,Y1=s.b((x0,y0,x1,y1)); E=e*2
        s.r([X0+2,Y0+2,X1+2,Y1+2],'DARK')                                   # shadow to the south-east
        s.r([X0,Y1-E,X1,Y1],wall,'INK'); s.r([X0,Y0,X1,Y1-E],roof,'INK')
        s.l([(X0+1,Y0+1),(X1-1,Y0+1)],'CREAM' if roof not in ('CREAM','TAN','SAND') else 'WHITE')  # lit parapet
        if roofd: s.l([(X0+1,Y1-E-1),(X1-1,Y1-E-1)],roofd); s.l([(X0+1,Y1-E-2),(X1-1,Y1-E-2)],roofd)
        if E>=6 and win:
            for yy in range(Y1-E+2,Y1-1,3):
                for x in range(X0+3,X1-2,4): s.r([x,yy,x+1,yy],win)
        if door is not None: s.r([door*2,Y1-E+2,door*2+5,Y1-1],'DARK','INK')
    def car(s,x,y,c,vert=False):
        if vert: s.r([x,y,x+4,y+8],c,'INK'); s.r([x+1,y+2,x+3,y+3],'WIN')
        else: s.r([x,y,x+8,y+4],c,'INK'); s.r([x+5,y+1,x+6,y+3],'WIN')
    def tree(s,x,y,d):
        s.e([x+2,y+3,x+d+2,y+d+3],'GRASSD'); s.e([x,y,x+d,y+d],'TREE','INK'); s.e([x+2,y+2,x+d//2+1,y+d//2+1],'GRASSD')
        s.P(x+3,y+3,'HI'); s.P(x+4,y+3,'HI')
    def smoke(s,pts):
        for x,y,k in pts: s.e([x-k,y-k,x+k,y+k],'SMOKE'); s.P(x-k//2,y-k//2,'CREAM')
def dept():
    s=S(); s.lot('ASPH',(1,1,30,30),'ASPHD',1)
    for x in range(8,60,10): s.l([(x,48),(x,60)],'PAVE')
    for i,(x,c) in enumerate(((10,'RED'),(30,'GLASS'),(40,'CREAM'),(50,'GREEN'))): s.car(x,50,c,True)
    s.bld(2,2,29,20,'TAN','CREAM',e=4,door=14,roofd='TAND')
    for x in range(6,58,4): s.r([x,33,x+1,35],'RED'); s.r([x+2,33,x+3,35],'CREAM')    # striped awning
    s.l([(5,32),(58,32)],'REDD'); s.l([(5,36),(58,36)],'INK')
    s.R([10,6,21,10],'RED','INK')
    for x in range(24,42,4): s.r([x,15,x+2,19],'CREAM')                                # rooftop sign letters
    for i,(x,y) in enumerate(((8,10),(48,22),(52,22))): s.r([x,y,x+5,y+4],'PAVE','INK'); s.P(x+2,y+2,'INK')  # AC units
    s.r([8,22,16,28],'PAVED','INK'); s.l([(9,25),(15,25)],'GREY')
    return s.im
def factory():
    import importlib.util, os
    s=S(); s.lot('PAVED',(1,1,30,30),'ASPH',2)
    s.r([10,34,103//2,55],'DARK')
    s.bld(2,8,25,27,'GREY','PAVE',e=4,door=11)
    X0,X1=5,51
    for y in (18,26,34):  # sawtooth roof: ink ridge, glazing with frames, lit slope, shaded slope
        s.l([(X0,y),(X1,y)],'INK'); s.r([X0,y+1,X1,y+2],'GLASS')
        for x in range(X0+2,X1,4): s.P(x,y+1,'WIN')
        s.l([(X0,y+3),(X1,y+3)],'PAVE'); s.l([(X0,y+5),(X1,y+5)],'GREY'); s.l([(X0,y+6),(X1,y+6)],'ASPH')
    s.r([10,42,15,45],'PAVE','INK'); s.r([36,40,42,43],'PAVE','INK')
    for x in (12,26,38): s.r([x,48,x+7,54],'GREY','INK'); [s.l([(x+1,yy),(x+6,yy)],'ASPHD') for yy in range(49,54,2)]  # loading bays
    s.r([52,8,59,55],'ASPHD','INK'); s.l([(53,9),(53,54)],'GREY')
    for y in (16,28,40): s.l([(52,y),(59,y)],'INK')
    s.r([53,4,58,8],'RUST','INK'); s.r([54,5,57,7],'DARK')
    s.smoke([(56,2,3),(50,2,3),(45,1,2)])
    s.r([6,56,24,61],'CREAM','INK'); s.r([18,56,24,61],'ORANGE','INK'); s.r([19,57,23,58],'WIN')  # truck
    s.e([8,59,11,62],'INK'); s.e([19,59,22,62],'INK')
    for x in (30,36): s.r([x,57,x+4,60],'TAND','INK'); s.l([(x+1,58),(x+3,58)],'BROWN')   # pallets
    return s.im
def rnd():
    s=S(); s.lot('GRASS',(1,1,30,30),'GRASSD',3,60)
    s.r([28,48,35,61],'PAVE'); s.l([(31,49),(31,61)],'PAVED')
    s.bld(2,4,22,24,'GLASS','PAVE',e=3,door=14)
    for y in range(14,42,8): s.l([(5,y),(43,y)],'GLASSD')
    for x in (17,31): s.l([(x,9),(x,41)],'GLASSD')
    for x,y in ((7,11),(19,11),(33,11),(7,19)): s.l([(x,y),(x+3,y)],'WIN'); s.P(x,y+1,'WIN')   # reflections
    s.e([42,6,61,25],'CREAM','INK'); s.e([46,10,57,21],'PAVE','INK'); s.e([49,13,54,18],'PAVED')
    s.l([(51,15),(58,8)],'INK'); s.l([(46,21),(51,15)],'GREY'); s.P(58,8,'RED'); s.P(59,7,'RED')   # dish and feed horn
    s.tree(47,40,11); s.tree(50,52,8)
    for x in (6,12): s.P(x,52,'CREAM'); s.P(x+1,52,'AMBER')                                  # flowers
    return s.im
def farm():
    s=S(); s.r([2,2,61,61],'DIRT')
    for y in range(3,61,5):
        s.l([(2,y),(61,y)],'BROWND')
        for x in range(3,61,3): s.P(x,y+2,'CROP'); s.P(x+1,y+2,'CROPD'); s.P(x,y+1,'CROPD')
    s.r([3,26,46,61],'TAN'); s.r([3,26,46,27],'TAND')
    for x in range(4,46,6): s.r([x,59,x+1,61],'BROWN')
    s.l([(3,60),(46,60)],'BROWN')
    s.r([7,31,34,59],'DARK')
    s.r([5,48,32,57],'MAROON','INK')
    s.r([13,49,24,56],'CREAM','INK'); s.l([(14,50),(23,55)],'INK'); s.l([(23,50),(14,55)],'INK'); s.l([(18,49),(18,56)],'INK')
    s.r([5,28,32,48],'RED','INK'); s.r([6,37,31,39],'REDD'); s.l([(6,38),(31,38)],'CREAM')
    s.r([6,29,31,32],'REDD'); s.r([14,30,23,33],'CREAM','INK'); s.r([16,31,21,32],'DARK')
    for x in range(8,31,4): s.l([(x,40),(x,47)],'REDD')
    s.e([36,26,48,38],'PAVE','INK'); s.e([39,29,45,35],'GREY'); s.e([40,30,42,32],'WHITE')
    s.r([36,32,48,52],'PAVED','INK'); s.l([(37,34),(47,34)],'GREY'); s.l([(37,42),(47,42)],'GREY')
    for y in range(34,52,2): s.P(46,y,'INK')
    s.l([(42,32),(42,52)],'PAVE')
    s.r([50,44,58,51],'GREEN','INK'); s.r([51,45,54,48],'WIN'); s.e([49,49,53,53],'INK'); s.e([55,48,60,53],'INK')
    s.l([(34,57),(61,57)],'TAND',3)
    return s.im
def logging():
    s=S(); s.lot('DIRT',(1,1,30,30),'BROWND',5,70)
    for x,y in ((4,4),(48,6),(52,44),(6,48),(40,2)):
        s.e([x,y,x+9,y+9],'TAN','BROWND'); s.e([x+2,y+2,x+7,y+7],'TAND'); s.e([x+4,y+4,x+5,y+5],'BROWN')   # stumps with rings
    s.bld(9,3,22,15,'BROWND','BROWN',e=3,door=14)
    for y in range(9,24,3): s.l([(19,y),(44,y)],'MAROON')                                     # plank roof
    for i,y in enumerate((38,44,50)):
        for x in range(16-i%2*4,48,8):
            s.e([x,y,x+7,y+7],'TAN','BROWND'); s.e([x+2,y+2,x+5,y+5],'TAND'); s.P(x+3,y+3,'BROWN')
    s.r([48,24,59,36],'ORANGE','INK'); s.r([50,26,57,30],'WIN'); s.r([50,32,57,35],'AMBER')   # skidder
    s.e([46,34,50,38],'INK'); s.e([57,34,61,38],'INK')
    return s.im
def mine():
    s=S(); s.lot('TAND',(1,1,30,30),'DIRT',6,70)
    s.E([3,10,21,28],'DIRT','INK'); s.e([10,24,39,53],'BROWN'); s.E([6,13,18,25],'BROWND'); s.e([17,31,32,46],'DIRT')
    s.E([9,16,15,22],'DARK','INK')
    for a in range(0,360,40):  # terrace steps
        x=28+math.cos(math.radians(a))*15; y=38+math.sin(math.radians(a))*15; s.P(int(x),int(y),'TAND')
    for x in (44,56): s.l([(x,6),(x,29)],'INK')
    for y in (6,16): s.l([(44,y),(56,y)],'INK')
    s.l([(44,6),(56,29)],'INK'); s.l([(56,6),(44,29)],'INK'); s.l([(44,16),(56,29)],'GREY'); s.l([(56,16),(44,29)],'GREY')
    s.e([46,2,54,10],'GREY','INK'); s.e([49,5,51,7],'INK')
    s.l([(34,44),(59,44)],'ASPHD'); s.l([(34,50),(59,50)],'ASPHD')
    for x in range(35,60,3): s.l([(x,44),(x,50)],'BROWND')
    s.r([46,40,57,48],'RUST','INK'); s.r([47,40,56,42],'GREY')
    for x,y in ((48,41),(51,40),(54,41)): s.P(x,y,'ASPHD')
    return s.im
def oil():
    s=S(); s.lot('TAND',(1,1,30,30),'DIRT',7,60)
    s.r([6,40,31,55],'PAVED','INK'); s.r([8,42,29,53],'PAVE')
    s.l([(11,53),(19,30)],'INK',2); s.l([(27,53),(19,30)],'INK',2); s.l([(14,44),(24,44)],'INK')  # A-frame
    s.l([(4,28),(35,24)],'ORANGE',4); s.l([(4,26),(35,22)],'INK')
    s.r([0,26,7,38],'ORANGE','INK'); s.r([1,27,6,29],'AMBER'); s.l([(4,37),(4,50)],'INK')        # horse head
    s.e([28,14,40,26],'DARK','INK'); s.e([31,17,37,23],'GREYD'); s.l([(34,20),(34,50)],'INK')     # counterweight
    s.e([38,30,59,51],'CREAM','INK'); s.e([42,34,55,47],'PAVE'); s.e([46,38,51,43],'PAVED'); s.l([(40,44),(57,44)],'INK')
    s.r([38,44,59,55],'PAVE','INK'); s.l([(39,48),(58,48)],'PAVED')
    for y in range(45,55,2): s.P(41,y,'INK')                                                       # tank ladder
    s.l([(10,58),(57,58)],'DARK'); s.l([(10,59),(57,59)],'GREYD')                                  # pipeline
    return s.im
def office(roof,roofd,sym):
    s=S(); s.lot('GRASS',(1,1,30,30),'GRASSD',8,60)
    s.r([28,50,35,61],'PAVE'); s.r([4,50,21,61],'ASPH')
    for x in (9,15): s.l([(x,51),(x,61)],'PAVE')
    s.car(5,53,'RED',True); s.car(16,53,'GLASS',True)
    s.bld(3,3,28,24,roof,'PAVE',e=3,door=14,roofd=roofd)
    s.r([10,10,17,17],'PAVE','INK'); s.r([12,12,15,15],'GREY'); s.r([48,10,53,14],'PAVE','INK'); s.P(50,12,'INK')
    s.tree(48,51,10)
    sym(s); return s.im
def sym_monitor(s):
    s.r([20,12,43,31],'DARK','INK'); s.r([22,14,41,29],'GLASS')
    for i,w in enumerate((8,12,6,10)): s.l([(24,17+i*3),(24+w,17+i*3)],'WIN')
    s.r([29,32,34,35],'INK'); s.l([(25,36),(38,36)],'INK')
def sym_disc(s):
    s.e([19,12,43,36],'PAVE','INK'); s.e([24,17,38,31],'WIN'); s.e([28,21,34,27],'GREY','INK'); s.e([30,23,32,25],'INK')
    s.l([(22,17),(25,14)],'CREAM'); s.P(21,20,'CREAM')
def restaurant():
    s=S(); s.lot('PAVE',(1,1,30,30),'PAVED',9)
    for i in range(0,64,8): s.l([(i,34),(i,61)],'PAVED')
    s.bld(2,2,29,16,'MAROON','CREAM',e=3,door=14,roofd='BROWND')
    for x in range(6,58,4): s.r([x,27,x+1,29],'RED'); s.r([x+2,27,x+3,29],'CREAM')
    s.r([12,8,21,19],'PAVE','INK'); s.r([14,10,19,17],'GREY')
    s.r([44,8,51,15],'GREY','INK'); s.r([46,10,49,13],'DARK'); s.smoke([(47,5,2),(50,2,2)])
    for cx,cy,c,c2 in ((14,47,'ORANGE','AMBER'),(32,51,'GREEN','TREE'),(50,45,'ORANGE','AMBER')):
        s.r([cx-6,cy+7,cx-4,cy+9],'BROWN'); s.r([cx+4,cy+7,cx+6,cy+9],'BROWN')                 # chairs
        s.e([cx-8,cy-8,cx+8,cy+8],c,'INK')
        for a in range(0,360,60): s.l([(cx,cy),(cx+math.cos(math.radians(a))*7,cy+math.sin(math.radians(a))*7)],c2)
        s.P(cx,cy,'CREAM')
    return s.im
def tv():
    s=S(); s.lot('PAVE',(1,1,30,30),'PAVED',10)
    s.bld(2,13,22,29,'GREY','PAVE',e=3,door=11,roofd='ASPHD')
    s.e([10,30,27,47],'CREAM','INK'); s.e([14,34,23,43],'PAVE'); s.e([17,37,20,40],'PAVED'); s.l([(18,38),(27,30)],'INK'); s.P(27,30,'RED')
    s.r([34,32,41,39],'PAVE','INK'); s.P(37,35,'INK')
    for y in range(4,52,6): s.l([(50,y),(57,y+6)],'INK'); s.l([(57,y),(50,y+6)],'INK')
    s.l([(50,4),(50,55)],'INK'); s.l([(57,4),(57,55)],'INK')
    for x,y in ((53,1),(54,1),(53,2),(54,2),(53,0)): s.P(x,y,'RED')
    for y in (16,32): s.P(48,y,'RED'); s.P(59,y,'RED')
    s.car(6,52,'CREAM'); s.r([12,52,14,56],'RED')                                                  # OB van
    return s.im
def radio():
    s=S(); s.lot('GRASS',(1,1,30,30),'GRASSD',11,60)
    for ax,ay in ((6,6),(57,8),(8,57)): s.l([(32,28),(ax,ay)],'DARK'); s.r([ax-2,ay-2,ax+2,ay+2],'ASPHD','INK')
    s.l([(30,4),(30,41)],'INK'); s.l([(34,4),(34,41)],'INK')
    for y in range(5,40,4): s.l([(30,y),(34,y+4)],'RED'); s.l([(31,y+2),(33,y+2)],'CREAM')
    for x,y in ((32,2),(32,1),(31,2),(33,2)): s.P(x,y,'RED')
    s.bld(19,19,29,29,'CREAM','PAVE',e=3,door=23,roofd='TAN'); s.r([42,42,47,47],'GREY','INK'); s.P(44,44,'INK')
    s.l([(34,40),(42,44)],'INK')                                                                    # feed line
    return s.im
def newspaper():
    s=S(); s.lot('PAVE',(1,1,30,30),'PAVED',12)
    s.bld(2,2,25,20,'BROWN','TAN',e=3,door=12,roofd='BROWND')
    s.r([10,10,41,27],'CREAM','INK')
    s.l([(13,13),(38,13)],'INK',2)
    for col in (13,27):
        for y in range(17,26,2): s.l([(col,y),(col+10,y)],'GREYD')
    s.r([28,17,38,21],'GREY')
    for y in (6,18,30): s.e([52,y,61,y+9],'CREAM','INK'); s.e([55,y+3,58,y+6],'TAN'); s.P(56,y+4,'BROWN')
    s.r([8,46,35,59],'CREAM','INK'); s.r([26,46,35,59],'GLASS','INK'); s.r([28,48,33,52],'WIN'); s.l([(10,52),(23,52)],'RED',2)
    s.e([10,57,14,61],'INK'); s.e([28,57,32,61],'INK')
    s.r([40,48,57,59],'TAND','INK'); s.l([(41,53),(56,53)],'BROWN'); s.l([(48,49),(48,58)],'BROWN')
    return s.im
def seaport():
    s=S(); s.r([0,0,63,63],'WATER'); s.r([0,0,63,27],'PAVED'); s.l([(0,27),(63,27)],'INK'); s.l([(0,26),(63,26)],'GREY')
    for i in range(0,64,8): s.l([(i,0),(i,25)],'PAVE')
    for x in range(4,60,12): s.r([x,28,x+3,30],'DARK','INK')
    for x,y,c in ((4,4,'RED'),(4,12,'GLASS'),(18,4,'GREEN'),(18,12,'ORANGE'),(32,8,'GLASSD'),(4,19,'CREAM')):
        s.r([x,y,x+11,y+6],c,'INK')
        for xx in range(x+2,x+10,2): s.l([(xx,y+1),(xx,y+5)],'INK' if c!='GLASSD' else 'NAVY')     # corrugated sides
    s.l([(46,2),(46,25)],'INK'); s.l([(54,2),(54,25)],'INK'); s.r([44,4,56,8],'ORANGE','INK')
    for y in range(10,24,4): s.l([(46,y),(54,y+4)],'ORANGE')
    s.r([48,8,52,43],'ORANGE','INK'); s.l([(50,43),(50,48)],'INK'); s.r([47,48,53,50],'GREYD','INK')   # crane boom and spreader
    s.d.polygon([(6,35),(40,35),(45,44),(40,55),(6,55)],fill=H(C['NAVY']),outline=H(C['INK']))
    s.l([(7,37),(40,37)],'TROUGH')
    for x,c in ((10,'RED'),(18,'GLASS'),(26,'CREAM')): s.r([x,39,x+6,51],c,'INK'); s.l([(x+3,40),(x+3,50)],'INK')
    s.r([34,40,39,50],'CREAM','INK'); s.r([35,42,38,44],'WIN')                                      # bridge
    for x in range(2,62,10): s.l([(x,59),(x+4,59)],'WIN'); s.l([(x+5,60),(x+7,60)],'TROUGH')
    return s.im
def flag(c):
    im=Image.new('RGBA',(16,24),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle([1,1,2,23],fill=H(C['GREYD'])); d.line([(1,1),(1,23)],fill=H(C['INK']))
    d.rectangle([3,1,14,12],fill=H(c),outline=H(C['INK']))
    shade=H(C['INK']) if c in ('#f6ecd4','#e8d6a0','#9fd3d8') else H('#22262e')
    for y in range(2,12):  # fold shadow down the middle
        if y%3: im.putpixel((9,y),shade)
    d.point([(2,0)],fill=H(C['AMBER']))
    return im
NAMES=F32.NAMES
DRAW=[dept,factory,rnd,farm,logging,mine,oil,lambda:office('CREAM','TAN',sym_monitor),
      lambda:office('GLASS','GLASSD',sym_disc),restaurant,tv,radio,newspaper,seaport]
def build():
    fr={'firm_'+n:f() for n,f in zip(NAMES,DRAW)}
    for i,c in enumerate(F32.FLAGS): fr[f'flag_{i:02d}']=flag(c)
    return fr
