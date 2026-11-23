import math, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W,H,FPS=1920,1080,24
D=Path("dist"); A=Path("assets")
D.mkdir(exist_ok=True); A.mkdir(exist_ok=True)
rng=np.random.default_rng(731)

def font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]:
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def background(seed, nebula):
    r=np.random.default_rng(seed); y,x=np.mgrid[0:H,0:W]; xx=x/W; yy=y/H
    a=np.zeros((H,W,3),dtype=np.float32); a[:]=[1,3,13]
    for cx,cy,sx,sy,c,k in nebula:
        g=np.exp(-2.2*(((xx-cx)/sx)**2+((yy-cy)/sy)**2))
        a+=g[...,None]*np.array(c)[None,None,:]*k
    a+=r.normal(0,1.8,(H,W,1))
    im=Image.fromarray(np.uint8(np.clip(a,0,255))).filter(ImageFilter.GaussianBlur(1.4))
    d=ImageDraw.Draw(im,"RGBA")
    for _ in range(2600):
        px,py=int(r.integers(W)),int(r.integers(H)); q=int(r.choice([1,1,1,2,2,3]))
        d.ellipse((px-q,py-q,px+q,py+q),fill=(205,222,255,int(r.integers(95,245))))
    return im

def planet(im,cx,cy,r,base,ring=False,texture=1):
    glow=Image.new("RGBA",(W,H)); gd=ImageDraw.Draw(glow)
    gd.ellipse((cx-r*1.5,cy-r*1.5,cx+r*1.5,cy+r*1.5),fill=(*base,100))
    im=Image.alpha_composite(im.convert("RGBA"),glow.filter(ImageFilter.GaussianBlur(r*.38)))
    p=Image.new("RGBA",(W,H)); d=ImageDraw.Draw(p)
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(*base,255))
    # Curved atmospheric bands, clipped by the circular silhouette.
    bands=Image.new("RGBA",(W,H)); bd=ImageDraw.Draw(bands)
    for j in range(-8,9):
        yy=cy+j*r*.19
        bd.arc((cx-r*1.04,yy-r*.5,cx+r*1.04,yy+r*.5),185,355,fill=(255,220,180,35+texture*7),width=max(3,int(r*.035)))
    mask=Image.new("L",(W,H)); ImageDraw.Draw(mask).ellipse((cx-r,cy-r,cx+r,cy+r),fill=255)
    bands.putalpha(Image.composite(bands.getchannel("A"),Image.new("L",(W,H)),mask))
    p=Image.alpha_composite(p,bands)
    # Dark night-side shading
    shade=Image.new("RGBA",(W,H)); sd=ImageDraw.Draw(shade)
    sd.ellipse((cx-r*.05,cy-r*1.1,cx+r*1.5,cy+r*1.1),fill=(0,0,8,175))
    shade.putalpha(Image.composite(shade.getchannel("A"),Image.new("L",(W,H)),mask))
    p=Image.alpha_composite(p,shade)
    if ring:
        rr=Image.new("RGBA",(W,H)); q=ImageDraw.Draw(rr)
        for k in range(7):
            rad=r*(1.35+k*.12)
            q.ellipse((cx-rad*1.7,cy-rad*.35,cx+rad*1.7,cy+rad*.35),outline=(205,183,150,75+k*12),width=max(3,int(r*.018)))
        im=Image.alpha_composite(im,rr.rotate(-16,resample=Image.Resampling.BICUBIC,center=(cx,cy)))
    return Image.alpha_composite(im,p).convert("RGB")

def caption(im,small,big):
    layer=Image.new("RGBA",(W,H)); d=ImageDraw.Draw(layer)
    d.rounded_rectangle((100,820,920,1015),radius=18,fill=(0,0,0,90))
    d.text((145,850),small.upper(),font=font(25),fill=(125,195,255,230),stroke_width=0)
    d.text((140,892),big,font=font(58),fill=(245,248,255,255),stroke_width=1,stroke_fill=(5,10,25,160))
    return Image.alpha_composite(im.convert("RGBA"),layer).convert("RGB")

scenes=[]
# 1 — Nebula: luminous clouds, dense stars and a bright stellar nursery.
im=background(11,[(.25,.42,.32,.48,(100,20,155),1.9),(.58,.55,.3,.42,(15,105,180),1.8),(.78,.25,.2,.3,(170,45,80),1.4)])
cloud=Image.new("RGBA",(W,H)); cd=ImageDraw.Draw(cloud)
for i in range(18):
    x=int(300+i*64); y=int(330+150*math.sin(i*.55))
    cd.ellipse((x-170,y-110,x+170,y+110),fill=(110,45,190,25))
cloud=cloud.filter(ImageFilter.GaussianBlur(75)); im=Image.alpha_composite(im.convert("RGBA"),cloud).convert("RGB")
im=caption(im,"Deep space • 00:00","THE STELLAR CRADLE"); scenes.append(im)

# 2 — Saturn-like ringed world, moon and asteroid foreground.
im=background(22,[(.2,.4,.25,.4,(15,55,130),.9),(.8,.5,.35,.4,(80,20,110),.8)])
im=planet(im,1230,500,330,(188,132,86),True,2)
d=ImageDraw.Draw(im,"RGBA")
d.ellipse((260,210,430,380),fill=(95,110,140,255),outline=(210,220,240,170),width=5)
for _ in range(180):
    x=int(rng.integers(0,W)); y=int(rng.integers(720,1100)); rad=int(rng.integers(2,10))
    d.ellipse((x-rad,y-rad,x+rad,y+rad),fill=(125,130,150,180))
im=caption(im,"Outer worlds • 00:10","THE RINGS OF A GIANT"); scenes.append(im)

# 3 — Asteroid field and spacecraft silhouette.
im=background(33,[(.65,.4,.4,.4,(35,35,100),.8),(.2,.7,.3,.3,(85,35,20),.5)])
d=ImageDraw.Draw(im,"RGBA")
for i in range(260):
    x=int(rng.integers(-100,W+100)); y=int(rng.integers(80,1030)); rad=int(rng.integers(5,30))
    col=int(rng.integers(65,145)); d.polygon([(x-rad,y),(x-rad//2,y-rad),(x+rad,y-rad//2),(x+rad//2,y+rad),(x-rad//2,y+rad//2)],fill=(col,col-8,col-15,235))
# Ship body and solar arrays
ship=Image.new("RGBA",(W,H)); s=ImageDraw.Draw(ship)
s.polygon([(850,520),(1010,475),(1130,520),(1010,565)],fill=(190,205,220,255))
s.polygon([(965,520),(1010,430),(1055,520)],fill=(225,235,245,255))
s.rectangle((610,495,840,545),fill=(30,100,175,230),outline=(150,210,255,255),width=4)
s.rectangle((1140,495,1370,545),fill=(30,100,175,230),outline=(150,210,255,255),width=4)
for x in range(620,1370,35): s.line((x,495,x,545),fill=(130,190,255,130),width=2)
im=Image.alpha_composite(im.convert("RGBA"),ship).convert("RGB")
im=caption(im,"Beyond the asteroid belt • 00:20","A SHIP IN THE ABYSS"); scenes.append(im)

# 4 — Moon close-up with crater rims and sunrise.
im=background(44,[(.72,.6,.22,.3,(230,105,35),1.7),(.3,.3,.25,.3,(30,50,100),.5)])
d=ImageDraw.Draw(im,"RGBA")
d.ellipse((-300,420,1750,2050),fill=(50,58,76,255),outline=(160,175,195,210),width=10)
for x,y,r in [(250,800,100),(650,1000,150),(1080,770,80),(1360,1100,125),(900,1350,190),(300,1250,55)]:
    d.ellipse((x-r,y-r*.55,x+r,y+r*.55),fill=(28,34,49,190),outline=(120,130,150,210),width=9)
    d.arc((x-r*.8,y-r*.45,x+r*.8,y+r*.45),190,345,fill=(190,195,205,170),width=7)
im=caption(im,"Lunar frontier • 00:30","SILENCE ON THE MOON"); scenes.append(im)

# 5 — Earthrise: blue atmosphere, continents, cloud systems and sun flare.
im=background(55,[(.6,.25,.4,.3,(30,75,170),1.1),(.15,.35,.3,.3,(50,20,110),.6)])
im=planet(im,1000,1050,570,(24,100,175),False,2)
d=ImageDraw.Draw(im,"RGBA")
# broad stylized continents
for pts in [[(650,650),(760,580),(820,620),(800,710),(720,760),(670,700)],[(1030,720),(1140,650),(1240,690),(1200,800),(1110,850),(1040,800)],[(820,1030),(940,960),(1030,1010),(980,1110),(850,1120)]]:
    d.polygon(pts,fill=(65,135,105,180))
for _ in range(35):
    x=int(rng.integers(550,1450)); y=int(rng.integers(570,1030))
    d.arc((x-80,y-25,x+80,y+25),180,350,fill=(235,245,255,120),width=7)
d.ellipse((1340,130,1450,240),fill=(255,232,185,255))
im=caption(im,"Home • 00:40","ONE BLUE PLANET"); scenes.append(im)

# 6 — Grand spiral galaxy, bright core and sweeping arms.
im=background(66,[(.5,.5,.5,.5,(50,20,130),1.2),(.25,.35,.3,.3,(15,90,140),.8)])
gal=Image.new("RGBA",(W,H)); gd=ImageDraw.Draw(gal)
for arm in range(4):
    pts=[]
    for t in np.linspace(0,7.4,900):
        rr=12+31*t; a=t+arm*math.pi/2
        pts.append((960+rr*math.cos(a),520+rr*.58*math.sin(a)))
    gd.line(pts,fill=(130,145,255,95),width=44)
gal=gal.filter(ImageFilter.GaussianBlur(28))
im=Image.alpha_composite(im.convert("RGBA"),gal)
core=Image.new("RGBA",(W,H)); c=ImageDraw.Draw(core)
c.ellipse((875,435,1045,605),fill=(255,230,190,230))
im=Image.alpha_composite(im,core.filter(ImageFilter.GaussianBlur(48)))
d=ImageDraw.Draw(im,"RGBA")
d.ellipse((925,485,995,555),fill=(255,250,225,255))
im=caption(im.convert("RGB"),"Across the universe • 00:50","INFINITE HORIZONS"); scenes.append(im)

for i,im in enumerate(scenes): im.save(A/f"scene_{i+1}.jpg",quality=95)

# Original ambient score with a slow harmonic swell.
sr=48000; t=np.arange(sr*60)/sr; audio=np.zeros_like(t)
for f,amp,ph in [(55,.14,0),(82.41,.085,.8),(110,.06,1.7),(164.81,.04,2.4),(220,.025,3.1),(329.63,.018,1.1)]:
    audio+=amp*(.62+.38*np.sin(2*np.pi*.025*t+ph))*np.sin(2*np.pi*f*t+ph)
audio+=.025*np.sin(2*np.pi*(220+3*np.sin(2*np.pi*.035*t))*t)
audio=np.tanh(audio*1.8)*np.minimum(1,t/3)*np.minimum(1,(60-t)/4)
st=np.column_stack([audio,np.roll(audio,211)])
with wave.open(str(D/"score.wav"),"wb") as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(sr); f.writeframes((np.clip(st,-1,1)*32767).astype("<i2").tobytes())

# Six distinct compositions, with slow camera pushes and overlapping dissolves.
seg=65/6; tr=5/6; args=[]; filters=[]
for i in range(6): args+=["-loop","1","-t",f"{seg:.6f}","-i",str(A/f"scene_{i+1}.jpg")]
args+=["-i",str(D/"score.wav")]
for i in range(6):
    filters.append(f"[{i}:v]scale=2200:1238,zoompan=z='min(zoom+0.00038,1.10)':d=260:s=1920x1080:fps=24,setsar=1,format=yuv420p[v{i}]")
last="v0"
for i in range(1,6):
    nxt=f"x{i}"; filters.append(f"[{last}][v{i}]xfade=transition=fade:duration={tr:.6f}:offset={i*(seg-tr):.6f}[{nxt}]"); last=nxt
filters.append(f"[{last}]trim=duration=60,setpts=PTS-STARTPTS[vout]")
cmd=["ffmpeg","-y",*args,"-filter_complex",";".join(filters),"-map","[vout]","-map","6:a","-t","60","-r","24","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",str(D/"cosmos-60s.mp4")]
subprocess.run(cmd,check=True)
print("Created dist/cosmos-60s.mp4")
