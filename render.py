import math, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W,H,FPS=1920,1080,24
D=Path("dist"); A=Path("assets")
D.mkdir(exist_ok=True); A.mkdir(exist_ok=True)
rng=np.random.default_rng(2026)

def sky(seed, blobs):
    r=np.random.default_rng(seed); y,x=np.mgrid[0:H,0:W]; xx=x/W; yy=y/H
    a=np.zeros((H,W,3),dtype=np.float32); a[:]=[2,4,17]
    for cx,cy,sx,sy,c,k in blobs:
        g=np.exp(-2*(((xx-cx)/sx)**2+((yy-cy)/sy)**2))
        a+=g[...,None]*np.array(c)[None,None,:]*k
    a+=r.normal(0,1.5,(H,W,1)); im=Image.fromarray(np.uint8(np.clip(a,0,255))).filter(ImageFilter.GaussianBlur(1))
    d=ImageDraw.Draw(im,"RGBA")
    for _ in range(1900):
        px,py=int(r.integers(W)),int(r.integers(H)); q=int(r.choice([1,1,1,2,2,3]))
        d.ellipse((px-q,py-q,px+q,py+q),fill=(210,225,255,int(r.integers(100,230))))
    return im

def planet(im,xy,r,col,ring=False):
    cx,cy=xy; glow=Image.new("RGBA",(W,H)); gd=ImageDraw.Draw(glow)
    gd.ellipse((cx-r*1.4,cy-r*1.4,cx+r*1.4,cy+r*1.4),fill=(*col[0],75))
    im=Image.alpha_composite(im.convert("RGBA"),glow.filter(ImageFilter.GaussianBlur(r*.3)))
    lay=Image.new("RGBA",(W,H)); d=ImageDraw.Draw(lay)
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(*col[1],255))
    if ring:
        rr=Image.new("RGBA",(W,H)); q=ImageDraw.Draw(rr)
        q.ellipse((cx-r*1.85,cy-r*.42,cx+r*1.85,cy+r*.42),outline=(*col[2],200),width=max(8,int(r*.07)))
        im=Image.alpha_composite(im,rr.rotate(-13,resample=Image.Resampling.BICUBIC,center=xy))
    return Image.alpha_composite(im,lay).convert("RGB")

pal=[
[(.25,.45,.25,.45,(70,20,140),1.3),(.7,.55,.3,.4,(10,95,150),1.2),(.5,.2,.25,.25,(110,30,90),.9)],
[(.25,.45,.35,.5,(20,60,130),.8),(.8,.3,.3,.3,(90,20,120),.8)],
[(.4,.55,.5,.5,(100,35,20),1),(.8,.35,.3,.4,(20,60,140),.7)],
[(.5,.6,.35,.4,(30,45,85),.6),(.2,.3,.3,.4,(20,80,130),.5)],
[(.4,.5,.35,.4,(15,65,140),.9),(.8,.3,.3,.3,(70,25,100),.7)],
[(.5,.5,.5,.5,(50,20,120),1.1),(.2,.3,.3,.4,(10,80,130),.8)]]
for i,p in enumerate(pal):
    im=sky(90+i,p)
    if i==1: im=planet(im,(1280,550),310,((30,100,210),(160,115,85),(220,195,145)),True)
    if i==2: im=planet(im,(1050,520),360,((70,30,20),(180,115,65),(220,170,110)))
    if i==3:
        d=ImageDraw.Draw(im); d.ellipse((-300,690,1700,1800),fill=(43,52,73)); d.arc((-300,660,1700,1760),185,355,fill=(160,185,220),width=9)
    if i==4: im=planet(im,(1000,980),470,((10,80,180),(20,80,145),(80,170,240)))
    if i==5:
        ov=Image.new("RGBA",(W,H)); d=ImageDraw.Draw(ov)
        for arm in range(3):
            pts=[]
            for t in np.linspace(0,5.5,500):
                rr=12+24*t; ang=t+arm*2*math.pi/3; pts.append((960+rr*math.cos(ang),520+rr*.52*math.sin(ang)))
            d.line(pts,fill=(190,160,255,150),width=22)
        im=Image.alpha_composite(im.convert("RGBA"),ov.filter(ImageFilter.GaussianBlur(24))).convert("RGB")
    im.save(A/f"scene_{i+1}.jpg",quality=94)

sr=48000; t=np.arange(sr*60)/sr; audio=np.zeros_like(t)
for f,amp,ph in [(55,.12,0),(82.41,.075,.8),(110,.055,1.7),(164.81,.035,2.4),(220,.022,3.1)]:
    audio+=amp*(.65+.35*np.sin(2*np.pi*.035*t+ph))*np.sin(2*np.pi*f*t+ph)
audio+=.018*np.sin(2*np.pi*(220+2*np.sin(2*np.pi*.04*t))*t)
audio=np.tanh(audio*2.1)*np.minimum(1,t/3)*np.minimum(1,(60-t)/4)
st=np.column_stack([audio,np.roll(audio,137)])
with wave.open(str(D/"score.wav"),"wb") as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(sr); f.writeframes((np.clip(st,-1,1)*32767).astype("<i2").tobytes())

seg=65/6; tr=5/6; args=[]; filters=[]
for i in range(6): args+=["-loop","1","-t",f"{seg:.6f}","-i",str(A/f"scene_{i+1}.jpg")]
args+=["-i",str(D/"score.wav")]
for i in range(6): filters.append(f"[{i}:v]scale=2200:1238,zoompan=z='min(zoom+0.00045,1.12)':d=260:s=1920x1080:fps=24,setsar=1,format=yuv420p[v{i}]")
last="v0"
for i in range(1,6):
    nxt=f"x{i}"; filters.append(f"[{last}][v{i}]xfade=transition=fade:duration={tr:.6f}:offset={i*(seg-tr):.6f}[{nxt}]"); last=nxt
filters.append(f"[{last}]trim=duration=60,setpts=PTS-STARTPTS[vout]")
cmd=["ffmpeg","-y",*args,"-filter_complex",";".join(filters),"-map","[vout]","-map","6:a","-t","60","-r","24","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",str(D/"cosmos-60s.mp4")]
subprocess.run(cmd,check=True)
print("Created dist/cosmos-60s.mp4")
