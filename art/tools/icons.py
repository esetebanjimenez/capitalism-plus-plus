"""Capitalism++ M2 job icons, concept B+ (48 px, 48-colour palette). Original art drawn pixel by pixel in
code with hard edges; a 1 px ink outline is added around every shape. Transparent background."""
from PIL import Image, ImageDraw
from terrain import PAL, H
from firms import C
C=dict(C, PINK='#f6d9a8', GOLD='#e0862f', LIGHT='#b6d0a8')
for v in C.values(): assert v in PAL, v
class I:
    def __init__(s): s.im=Image.new('RGBA',(48,48),(0,0,0,0)); s.d=ImageDraw.Draw(s.im)
    def R(s,b,c,o=None): s.d.rectangle(b,fill=H(C[c]),outline=H(C[o]) if o else None)
    def E(s,b,c,o=None): s.d.ellipse(b,fill=H(C[c]),outline=H(C[o]) if o else None)
    def L(s,p,c,w=1): s.d.line(p,fill=H(C[c]),width=w)
    def G(s,p,c,o=None): s.d.polygon(p,fill=H(C[c]),outline=H(C[o]) if o else None)
    def P(s,x,y,c): s.im.putpixel((x,y),H(C[c])+(255,))
    def done(s):
        a=s.im.load(); ink=H(C['INK'])+(255,); add=[]
        for y in range(48):
            for x in range(48):
                if a[x,y][3]==0 and any(0<=x+dx<48 and 0<=y+dy<48 and a[x+dx,y+dy][3] and a[x+dx,y+dy]!=ink
                                       for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))): add.append((x,y))
        for p in add: a[p]=ink
        return s.im
def crop():
    s=I()
    for xt,yt in ((10,10),(24,5),(38,10)):
        s.L([(24,44),(xt,yt+14)],'TAND',2)
        for k in range(5):
            y=yt+k*3
            s.R([xt-4,y,xt-1,y+2],'GOLD'); s.R([xt+1,y+1,xt+4,y+3],'AMBER')
        s.L([(xt,yt-3),(xt,yt)],'TAN')
    s.R([16,30,32,34],'BROWN'); s.L([(17,32),(31,32)],'BROWND')
    s.G([(24,40),(12,46),(20,46)],'CROP'); s.G([(24,40),(36,46),(28,46)],'CROPD')
    return s.done()
def livestock():
    s=I(); s.G([(8,10),(2,6),(4,14)],'CREAM'); s.G([(40,10),(46,6),(44,14)],'CREAM')  # horns
    s.E([4,14,14,22],'WHITE'); s.E([34,14,44,22],'WHITE'); s.E([6,16,12,20],'PINK'); s.E([36,16,42,20],'PINK')
    s.E([10,8,38,40],'WHITE'); s.E([12,10,22,22],'BROWND'); s.E([30,24,38,34],'BROWND')
    s.E([14,28,34,44],'PINK'); s.E([18,34,21,37],'BROWND'); s.E([27,34,30,37],'BROWND')
    s.R([17,20,19,23],'INK'); s.R([29,20,31,23],'INK')
    return s.done()
def processing():
    s=I(); s.E([4,10,40,40],'CREAM'); s.E([7,13,37,37],'RED'); s.E([16,20,24,28],'CREAM')
    s.L([(10,22),(18,32)],'REDD'); s.L([(26,16),(32,26)],'REDD')
    s.E([4,34,10,40],'TREE'); s.L([(4,38),(12,44)],'CROP',2)
    return s.done()
def logging():
    s=I(); s.R([4,24,36,40],'BROWN'); s.L([(5,28),(35,28)],'BROWND'); s.L([(5,34),(35,34)],'BROWND')
    s.E([30,22,44,42],'TAN'); s.E([33,26,41,38],'TAND'); s.E([36,30,38,34],'BROWND')
    s.L([(10,6),(22,26)],'BROWN',3)  # axe handle
    s.G([(4,4),(14,0),(16,10),(8,14)],'PAVE'); s.L([(4,5),(8,13)],'WHITE')
    return s.done()
def inventory():
    s=I()
    for x,y,w in ((4,24,20),(24,24,20),(14,6,20)):
        s.R([x,y,x+w-1,y+17],'TAN'); s.R([x,y,x+w-1,y+3],'TAND'); s.L([(x+w//2,y),(x+w//2,y+8)],'BROWN',2)
        s.R([x+3,y+11,x+8,y+14],'WHITE')
    s.L([(4,41),(43,41)],'BROWND',2)
    return s.done()
def label():
    s=I(); s.G([(12,6),(42,6),(42,38),(12,38),(4,22)],'CREAM'); s.E([10,19,15,24],'PAVE')
    s.L([(12,21),(2,10)],'BROWN')
    st=[(28,10),(31,18),(39,18),(33,23),(35,32),(28,27),(21,32),(23,23),(17,18),(25,18)]; s.G(st,'ORANGE')
    s.L([(18,40),(40,40)],'GLASS',3)
    return s.done()
def manufacturing():
    s=I(); import math
    pts=[]
    for k in range(16):
        r=20 if k%2==0 else 15; a=k*math.pi/8; pts.append((22+r*math.cos(a),22+r*math.sin(a)))
    s.G(pts,'GREY'); s.E([10,10,34,34],'GREY'); s.E([16,16,28,28],'PAVE'); s.E([19,19,25,25],'DARK')
    s.L([(30,30),(42,42)],'ORANGE',5); s.E([36,36,46,46],'ORANGE'); s.E([39,39,43,43],'DARK')
    return s.done()
def mining():
    s=I(); s.L([(8,42),(36,10)],'BROWN',3)
    s.G([(22,4),(36,6),(46,16),(44,18),(34,10),(24,8)],'PAVE'); s.L([(23,5),(35,7)],'WHITE')
    s.G([(4,40),(10,30),(22,28),(28,36),(24,46),(8,46)],'GREY'); s.G([(10,34),(16,32),(16,38)],'AMBER'); s.G([(18,38),(23,36),(21,42)],'WIN')
    return s.done()
def oil():
    s=I(); s.R([22,22,42,44],'GLASSD'); s.E([22,19,42,25],'GLASS'); s.L([(23,30),(41,30)],'NAVY'); s.L([(23,37),(41,37)],'NAVY')
    s.G([(14,4),(4,22),(6,30),(14,34),(22,30),(24,22)],'DARK'); s.E([4,16,24,34],'DARK'); s.L([(10,20),(8,26)],'GREY',2)
    return s.done()
def purchasing():
    s=I(); s.L([(2,8),(10,8),(16,32),(40,32)],'GREY',3)
    s.G([(10,12),(44,12),(40,28),(15,28)],'PAVE'); 
    for x in range(16,42,6): s.L([(x,13),(x+1,27)],'GREY')
    s.L([(13,20),(42,20)],'GREY'); s.E([14,36,22,44],'DARK'); s.E([32,36,40,44],'DARK')
    s.R([20,14,28,22],'ORANGE'); s.R([29,15,36,23],'GLASS')
    return s.done()
def rnd():
    s=I(); s.R([18,4,30,8],'PAVE'); s.R([20,8,28,20],'WIN'); s.G([(20,20),(28,20),(42,42),(6,42)],'WIN')
    s.G([(14,30),(34,30),(42,42),(6,42)],'GREEN'); s.L([(8,41),(40,41)],'TREE')
    for x,y,r in ((20,34,2),(28,36,1),(25,25,2),(22,14,1)): s.E([x-r,y-r,x+r,y+r],'WHITE')
    s.L([(23,9),(23,18)],'WHITE')
    return s.done()
def sales():
    s=I()
    for i in range(3): s.R([4+i*2,30-i*6,30+i*2,40-i*6],'GREEN'); s.L([(6+i*2,35-i*6),(28+i*2,35-i*6)],'TREE')
    s.E([14,19,24,25],'CROP'); 
    s.E([26,24,46,44],'GOLD'); s.E([29,27,43,41],'AMBER')
    s.d.arc([31,29,41,39],200,290,fill=H(C['CREAM'])); s.R([34,32,38,36],'GOLD')
    s.G([(32,2),(42,12),(36,12),(36,20),(28,20),(28,12),(22,12)],'GREEN')
    return s.done()
def softdev():
    s=I(); s.R([2,4,45,34],'DARK'); s.R([5,7,42,31],'NAVY')
    s.L([(14,13),(9,19),(14,25)],'GREEN',2); s.L([(33,13),(38,19),(33,25)],'GREEN',2); s.L([(26,11),(21,27)],'WIN',2)
    s.R([20,35,27,39],'GREY'); s.R([12,40,35,44],'GREY')
    return s.done()
def softprod():
    s=I(); s.R([4,4,30,44],'GLASS'); s.R([6,6,28,20],'ORANGE'); s.L([(8,10),(24,10)],'WHITE',2); s.L([(8,15),(18,15)],'CREAM')
    s.R([4,4,7,44],'GLASSD')
    s.E([18,16,46,44],'PAVE'); s.E([22,20,42,40],'WIN'); s.E([28,26,36,34],'PAVE'); s.E([30,28,34,32],'DARK')
    s.L([(24,24),(28,22)],'WHITE')
    return s.done()
def advertising():
    s=I(); s.G([(6,18),(30,6),(30,40),(6,28)],'ORANGE'); s.R([2,18,8,28],'RED')
    s.E([26,4,34,42],'AMBER'); s.E([28,18,32,28],'DARK'); s.L([(10,28),(14,40),(18,40),(16,30)],'GREY',2)
    for k,(a,b) in enumerate(((38,12),(40,23),(38,34))): s.L([(a,b),(a+6,b+(k-1)*4)],'GOLD',2)
    return s.done()
def imp():
    s=I(); s.R([2,14,34,40],'RED'); s.R([2,14,34,17],'REDD')
    for x in range(6,34,5): s.L([(x,18),(x,39)],'REDD')
    s.R([28,20,31,34],'PAVE')
    s.G([(46,27),(36,17),(36,23),(22,23),(22,31),(36,31),(36,37)],'GREEN')
    return s.done()
NAMES=['crop_growing','livestock_raising','livestock_processing','logging','inventory','private_labelling',
       'manufacturing','mining','oil_extraction','purchasing','research_development','sales',
       'software_development','software_production','advertising','import']
DRAW=[crop,livestock,processing,logging,inventory,label,manufacturing,mining,oil,purchasing,rnd,sales,softdev,softprod,advertising,imp]
def build(save):
    for n,f in zip(NAMES,DRAW): save('job_'+n,f())
