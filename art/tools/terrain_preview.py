import sys,json,random,math
import os; os.chdir(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,'.'); import terrain as T
from PIL import Image,ImageDraw,ImageFont
fr=T.build('../tiles/terrain')
# atlas + json
names=sorted(fr); cols=16; at=Image.new('RGBA',(cols*32,math.ceil(len(names)/cols)*32))
meta={}
for i,n in enumerate(names):
    x,y=(i%cols)*32,(i//cols)*32; at.paste(fr[n],(x,y)); meta[n]=dict(x=x,y=y,w=32,h=32)
at.save('../atlas/terrain_atlas.png'); json.dump(dict(tile=32,frames=meta),open('../atlas/terrain_atlas.json','w'),indent=1)
# sample map: island, 28x20, climate by row
W,Hh=28,20; r=random.Random(3)
def hv(x,y):
    d=math.hypot((x-13.5)/11,(y-9.5)/8)+0.25*math.sin(x*.9)*math.cos(y*.7)
    return 'L' if d<0.75 else ('w' if d<1.0 else 'd')
G=[[hv(x,y) for x in range(W)] for y in range(Hh)]
for x,y in [(6,8),(7,8),(6,9)]: G[y][x]='f'
land=lambda x,y: 0<=x<W and 0<=y<Hh and G[y][x] in 'Lf'
mp=Image.new('RGBA',(W*32,Hh*32))
for y in range(Hh):
    cl=4-min(4,abs(y-9)*5//10)
    for x in range(W):
        c=G[y][x]; v=(x*7+y*13)
        if c=='L': t=fr[f'forest_c{cl}_{v%4}'] if (x+y*3)%9<2 or (x>15 and y<8) else (fr[f'hill_c{cl}_{v%2}'] if (x*5+y)%23==0 else fr[f'grass_c{cl}_{v%4}'])
        elif c=='f': t=fr[f'forest_c{cl}_{v%4}']
        else:
            m=sum(b for b,(dx,dy) in ((1,(0,-1)),(2,(1,0)),(4,(0,1)),(8,(-1,0))) if land(x+dx,y+dy))
            dg=sum(b for b,(dx,dy),(ax,ay) in ((1,(1,-1),((0,-1),(1,0))),(2,(1,1),((1,0),(0,1))),(4,(-1,1),((0,1),(-1,0))),(8,(-1,-1),((-1,0),(0,-1))))
                   if land(x+dx,y+dy) and not land(x+ax[0],y+ax[1]) and not land(x+ay[0],y+ay[1]))
            if c=='d':
                sh=[s for s,(dx,dy) in zip('nesw',((0,-1),(1,0),(0,1),(-1,0))) if 0<=x+dx<W and 0<=y+dy<Hh and G[y+dy][x+dx]=='w']
                t=fr[f'shelf_{sh[0]}'] if sh else fr[f'deep_{v%3}']
            elif m: t=fr[f'coast_{m:02d}']
            elif dg: t=T.coast(0,dg)
            else: t=fr[f'water_{v%3}']
        mp.paste(t,(x*32,y*32))
FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; F=lambda n:ImageFont.truetype(FB,n)
cream=T.H('#f6ecd4'); ink=T.H('#22262e')
S=Image.new('RGB',(W*64+60,Hh*64+at.height*2+180),cream); d=ImageDraw.Draw(S)
d.text((30,16),'Capitalism++ M2 production: terrain and coast (B+, 32 px, 48 colours), sample map and atlas at 2x',font=F(24),fill=ink)
S.paste(mp.resize((W*64,Hh*64),Image.NEAREST),(30,60))
d.text((30,Hh*64+80),f'Atlas: {len(names)} tiles (climate 0 = poles at top rows of each group, 4 = equator)',font=F(20),fill=ink)
S.paste(at.resize((at.width*2,at.height*2),Image.NEAREST),(30,Hh*64+115))
S.save('../../docs/art/terrain-preview.png'); print(S.size,len(names))
