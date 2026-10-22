"""Paint diffuse textures for the sculpted goblin soldier from baked maps.

Inputs per mesh (from goblin_sculpt.py): <stem>_id.png (material colour),
<stem>_pos.npy (world position per texel, cm) and <stem>_ao.png. Everything is
painted procedurally in 3D space so seams never show: skin mottling, eyes,
mouth and claws on the body; weave, quilting, leather and rusty scrap iron on
the outfits. numpy only; no Blender needed at build time.
"""
import numpy as np
from pathlib import Path
from PIL import Image

MATERIALS={'skin':(1,0,0),'cloth':(0,1,0),'leather':(0,0,1),'iron':(1,1,0),'pad':(0,1,1),'mail':(1,0,1),'bone':(0.5,0,0),'fur':(0,0.5,0),'rope':(0,0,0.5)}
# Facial landmarks must match goblin_sculpt.P
EYE=(4.8,165,-13.4);EYE_R=2.2;MOUTH=(0,154.5,-13);MOUTH_W=5.5

def _hash(ix,iy,iz,seed):
    h=(ix*73856093)^(iy*19349663)^(iz*83492791)^(seed*2654435761)
    h=(h^(h>>13))*1274126177&0xffffffff;h=(h^(h>>16))&0xffffffff
    return (h&0xffff)/65535.0

def noise(p,scale,seed=0):
    """3D value noise in [0,1] evaluated at positions p (...,3) with the given feature size (cm)."""
    q=p/scale;i=np.floor(q).astype(np.int64);f=q-i;f=f*f*(3-2*f)
    out=np.zeros(p.shape[:-1])
    for dx in (0,1):
        for dy in (0,1):
            for dz in (0,1):
                w=(f[...,0] if dx else 1-f[...,0])*(f[...,1] if dy else 1-f[...,1])*(f[...,2] if dz else 1-f[...,2])
                out+=w*_hash(i[...,0]+dx,i[...,1]+dy,i[...,2]+dz,seed)
    return out

def fbm(p,scale,octaves=3,seed=0):
    total=np.zeros(p.shape[:-1]);amp=1;norm=0
    for o in range(octaves):
        total+=amp*noise(p,scale/(2**o),seed+o);norm+=amp;amp*=0.5
    return total/norm

def load_maps(stem):
    stem=str(stem)
    ident=np.asarray(Image.open(stem+'_id.png').convert('RGB'),np.float32)/255
    pos=np.load(stem+'_pos.npz')['pos'].astype(np.float32);ao=np.asarray(Image.open(stem+'_ao.png').convert('L'),np.float32)/255
    return ident,pos,ao

def masks(ident):
    return {k:(np.abs(ident-np.array(v,np.float32)).max(-1)<0.35) for k,v in MATERIALS.items()}

def paint_skin(pos,ao,clan_rgb,seed=1):
    base=(np.array(clan_rgb,np.float32)/255)**2.2*2.1  # clan sRGB -> linear, brightened for map distance
    col=np.broadcast_to(base,pos.shape).copy()
    mottle=1+0.22*(fbm(pos,7,3,seed)-0.5)+0.10*(fbm(pos,1.6,2,seed+7)-0.5)
    col*=mottle[...,None]
    # Paler belly and throat, darker back
    front=np.clip((-pos[...,2]-2)/10,0,1)*np.clip((pos[...,1]-95)/10,0,1)*np.clip((150-pos[...,1])/10,0,1)
    col=col*(1-0.18*front[...,None])+np.array((0.78,0.72,0.42))*0.18*front[...,None]*col.mean(-1,keepdims=True)*2
    back=np.clip((pos[...,2]-4)/8,0,1);col*=(1-0.15*back)[...,None]
    # Warm, bruised tint on the nose, ears, knuckles and toes
    warm=np.zeros(pos.shape[:-1])
    warm+=np.clip((-pos[...,2]-15)/4,0,1)*np.clip((7-np.abs(pos[...,1]-162))/3,0,1)*(np.abs(pos[...,0])<4.5)
    warm+=np.clip((np.abs(pos[...,0])-15)/8,0,1)*(pos[...,1]>158)
    warm+=np.clip((np.abs(pos[...,0])-30)/4,0,1)*(pos[...,1]<98)
    warm+=np.clip((-pos[...,2]-12)/5,0,1)*(pos[...,1]<9)
    warm=np.clip(warm,0,1)*0.4;col=col*(1-warm[...,None])+np.array((0.3,0.17,0.12))*warm[...,None]
    # Brow shadow and sunken cheeks
    brow=(np.abs(pos[...,1]-168.5)<2.2)*(pos[...,2]<-10.5)*(np.abs(pos[...,0])<11);col*=(1-0.18*brow)[...,None]
    # Eyes: amber with a black slit pupil, dark rim
    for sx in (1,-1):
        c=np.array((sx*EYE[0],EYE[1],EYE[2]));d=np.linalg.norm(pos-c,axis=-1)
        rim=(d<EYE_R+1.6)&(d>=EYE_R+0.5);col[rim]=col[rim]*0.4
        eye=d<EYE_R+0.5;col[eye]=np.array((1.0,0.8,0.2))
        front=np.linalg.norm(pos-(c+np.array((0,0,-EYE_R))),axis=-1)
        glint=(front<2.2)&(np.abs(pos[...,0]-c[0])<0.5);col[glint&eye]=np.array((0.03,0.02,0.02))
        edge=(d<EYE_R+0.5)&(d>EYE_R-0.4);col[edge]=col[edge]*0.7
    # Mouth slit and jagged lower teeth
    mouth=(np.abs(pos[...,1]-MOUTH[1])<0.75)*(np.abs(pos[...,0])<MOUTH_W)*(pos[...,2]<MOUTH[2]+5.5)
    col[mouth>0]=np.array((0.16,0.07,0.06))
    for tx in (-3.6,-1.2,1.2,3.6):
        tooth=(np.abs(pos[...,0]-tx)<0.5)*(pos[...,1]>MOUTH[1]-1.9)*(pos[...,1]<MOUTH[1]+0.3)*(pos[...,2]<MOUTH[2]+5.5)
        col[tooth>0]=np.array((0.85,0.8,0.62))
    # Nostrils
    for sx in (1,-1):
        d=np.linalg.norm(pos-np.array((sx*1.7,158.6,-21.4)),axis=-1);col[d<1.1]*=0.45
    # Horn-coloured claws
    claw=np.clip((85.5-pos[...,1])/2.5,0,1)*(np.abs(pos[...,0])>30)+np.clip((-pos[...,2]-17.5)/2,0,1)*(pos[...,1]<6)
    claw=np.clip(claw,0,1);col=col*(1-claw[...,None])+np.array((0.32,0.3,0.22))*claw[...,None]
    # Ivory tusks (cones from the lower jaw past the lip)
    for sx in (1,-1):
        a=np.array((sx*3.4,152.5,-14.6));b=np.array((sx*4.2,159.5,-18));ab=b-a;t=np.clip(((pos-a)*ab).sum(-1)/(ab*ab).sum(),0,1)
        d=np.linalg.norm(pos-(a+t[...,None]*ab),axis=-1);tusk=(d<1.5)&(t>0.35);col[tusk]=np.array((0.78,0.7,0.52))*(0.7+0.3*ao[tusk])[...,None]
    # Shadowed sockets, darker knuckles, lighter palms, mud on shins and feet, a few pale scars
    for sx in (1,-1):
        d=np.linalg.norm(pos-np.array((sx*EYE[0],EYE[1],EYE[2]-2)),axis=-1);socket=np.clip((EYE_R+4.5-d)/3,0,1)*(d>EYE_R+0.5);col*=(1-0.3*socket)[...,None]
    knuckle=np.clip((np.abs(pos[...,0])-33)/4,0,1)*(pos[...,1]<96)*(pos[...,2]<2.5);col*=(1-0.2*knuckle)[...,None]
    palm=np.clip((np.abs(pos[...,0])-33)/4,0,1)*(pos[...,1]<98)*(pos[...,2]>3.5);col=col*(1-0.25*palm[...,None])+np.array((0.5,0.36,0.26))*0.25*palm[...,None]
    mud=np.clip((32-pos[...,1])/26,0,1)**1.5*(0.6+0.4*fbm(pos,3,2,seed+11));col=col*(1-0.55*mud[...,None])+np.array((0.11,0.08,0.05))*0.55*mud[...,None]
    for (a,b) in [((-9,118,-13),(-4,126,-12)),((11,136,2),(16,141,6)),((-6,170,-11),(-2,176,-8))]:
        a=np.array(a,float);b=np.array(b,float);ab=b-a;t=np.clip(((pos-a)*ab).sum(-1)/(ab*ab).sum(),0,1)
        d=np.linalg.norm(pos-(a+t[...,None]*ab),axis=-1);scar=np.clip((0.9-d)/0.5,0,1);col=col*(1-0.5*scar[...,None])+np.array((0.5,0.42,0.3))*0.5*scar[...,None]*col.mean(-1,keepdims=True)*3
    # Mottled darker patches across the shoulders and back, pinker inner ears
    spots=np.clip((fbm(pos,2.2,2,seed+13)-0.56)*5,0,1)*np.clip((pos[...,2]+2)/8,0,1)*(pos[...,1]>100);col*=(1-0.35*spots)[...,None]
    inner=np.clip((np.abs(pos[...,0])-14)/6,0,1)*(pos[...,1]>160)*(pos[...,2]<2);col=col*(1-0.3*inner[...,None])+np.array((0.3,0.15,0.12))*0.3*inner[...,None]
    col*=(0.52+0.48*ao)[...,None]
    return col

def paint_cloth(pos,ao,seed=2):
    col=np.broadcast_to(np.array((0.42,0.32,0.19),np.float32),pos.shape).copy()
    weave=1+0.14*(noise(pos,0.45,seed)-0.5);stain=1+0.3*(fbm(pos,9,3,seed+3)-0.5)
    col*=(weave*stain)[...,None]
    # sewn-on patches of other cloth
    for (x0,x1,y0,y1,c) in [(-12,-4,108,118,(0.42,0.34,0.22)),(3,11,120,128,(0.35,0.3,0.3)),(2,9,86,96,(0.45,0.3,0.2))]:
        m=(pos[...,0]>x0)&(pos[...,0]<x1)&(pos[...,1]>y0)&(pos[...,1]<y1)&(pos[...,2]<0);col[m]=np.array(c)*stain[m][...,None]
        border=m&((np.abs(pos[...,0]-x0)<0.5)|(np.abs(pos[...,0]-x1)<0.5)|(np.abs(pos[...,1]-y0)<0.5)|(np.abs(pos[...,1]-y1)<0.5));col[border]*=0.6
    hem=np.clip((95-pos[...,1])/10,0,1);col*=(1-0.4*hem)[...,None]
    dirt=np.clip((fbm(pos,2.5,2,seed+5)-0.5)*2.5,0,1)*0.3;col*=(1-dirt)[...,None]
    col*=(0.45+0.55*ao)[...,None];return col

def paint_pad(pos,ao,seed=3):
    col=np.broadcast_to(np.array((0.38,0.31,0.24),np.float32),pos.shape).copy()
    stain=1+0.25*(fbm(pos,8,3,seed)-0.5)+0.1*(noise(pos,0.5,seed+1)-0.5);col*=stain[...,None]
    quilt=(np.abs((pos[...,1]+2.5)%5-2.5)<0.35)|(np.abs((pos[...,0]+3)%6-3)<0.35);col[quilt]*=0.6
    puff=0.5+0.5*np.cos((pos[...,1])/5*2*np.pi)*np.cos(pos[...,0]/6*2*np.pi);col*=(0.92+0.12*puff)[...,None]
    col*=(0.45+0.55*ao)[...,None];return col

def paint_leather(pos,ao,seed=4):
    col=np.broadcast_to(np.array((0.34,0.21,0.11),np.float32),pos.shape).copy()
    grain=1+0.2*(fbm(pos,3,3,seed)-0.5)+0.08*(noise(pos,0.35,seed+2)-0.5);col*=grain[...,None]
    scratch=noise(pos*np.array((9,0.6,9)),1.0,seed+5)>0.78;col[scratch]*=1.35
    stitch=(np.abs((pos[...,1]+1)%4-2)<0.2)&(noise(pos,0.8,seed+9)>0.72);col[stitch]=np.array((0.5,0.4,0.25))
    col*=(0.4+0.6*ao)[...,None];return col

def paint_iron(pos,ao,seed=5):
    col=np.broadcast_to(np.array((0.3,0.31,0.34),np.float32),pos.shape).copy()
    dents=1+0.25*(fbm(pos,6,3,seed)-0.5);col*=dents[...,None]
    rust=np.clip((fbm(pos,4,3,seed+4)-0.55)*3.2,0,1);col=col*(1-rust[...,None])+np.array((0.42,0.22,0.1))*rust[...,None]
    scratch=noise(pos*np.array((0.5,8,8)),1.0,seed+6)>0.8;col[scratch]*=1.3
    col*=(0.4+0.6*ao)[...,None];return col

def paint_mail(pos,ao,seed=6):
    # riveted rings: hex-ish lattice of bright ring edges on dark backing
    col=np.broadcast_to(np.array((0.2,0.21,0.23),np.float32),pos.shape).copy()
    u=pos[...,0]*1.0+pos[...,2]*0.3;v=pos[...,1]*1.0
    ring=np.cos(u/1.1*2*np.pi)*np.cos(v/1.1*2*np.pi);col*=(0.75+0.5*np.clip(ring,0,1))[...,None]
    rust=np.clip((fbm(pos,5,3,seed+2)-0.58)*3,0,1);col=col*(1-rust[...,None])+np.array((0.38,0.2,0.1))*rust[...,None]
    col*=(0.35+0.65*ao)[...,None];return col

def paint_bone(pos,ao,seed=7):
    col=np.broadcast_to(np.array((0.72,0.64,0.5),np.float32),pos.shape).copy()
    grain=1+0.18*(fbm(pos*np.array((1,0.3,1)),2.5,3,seed)-0.5);col*=grain[...,None]
    crack=noise(pos*np.array((6,1,6)),1.2,seed+3)>0.82;col[crack]*=0.55
    col*=(0.5+0.5*ao)[...,None];return col

def paint_fur(pos,ao,seed=8):
    col=np.broadcast_to(np.array((0.17,0.12,0.08),np.float32),pos.shape).copy()
    strand=noise(pos*np.array((8,0.7,8)),1.0,seed);col*=(0.6+0.9*strand)[...,None]
    tips=np.clip((fbm(pos,3,2,seed+2)-0.5)*2,0,1);col=col*(1-tips[...,None])+np.array((0.36,0.28,0.18))*tips[...,None]*0.6
    col*=(0.45+0.55*ao)[...,None];return col

def paint_rope(pos,ao,seed=9):
    col=np.broadcast_to(np.array((0.5,0.4,0.24),np.float32),pos.shape).copy()
    twist=0.5+0.5*np.cos((pos[...,0]+pos[...,1]+pos[...,2])/1.2*2*np.pi);col*=(0.7+0.5*twist)[...,None]
    col*=(1+0.15*(noise(pos,0.4,seed)-0.5))[...,None]
    col*=(0.45+0.55*ao)[...,None];return col

def paint(stem,clan_rgb=None,seed=0):
    """Diffuse RGBA uint8 image for the mesh at stem (clan colour used for skin)."""
    ident,pos,ao=load_maps(stem);m=masks(ident);out=np.zeros(pos.shape,np.float32)
    painters={'skin':lambda:paint_skin(pos,ao,clan_rgb if clan_rgb is not None else (90,120,60),seed+1),'cloth':lambda:paint_cloth(pos,ao,seed+2),
              'pad':lambda:paint_pad(pos,ao,seed+3),'leather':lambda:paint_leather(pos,ao,seed+4),'iron':lambda:paint_iron(pos,ao,seed+5),
              'mail':lambda:paint_mail(pos,ao,seed+6),'bone':lambda:paint_bone(pos,ao,seed+7),'fur':lambda:paint_fur(pos,ao,seed+8),'rope':lambda:paint_rope(pos,ao,seed+9)}
    for k,fn in painters.items():
        if m[k].any():out[m[k]]=fn()[m[k]]
    painted=np.zeros(pos.shape[:2],bool)
    for k in painters:painted|=m[k]
    out=dilate(out,painted,8)
    rgb=(np.clip(out,0,1)**(1/2.2)*255).round().astype(np.uint8)
    return Image.fromarray(np.dstack([rgb,np.full(rgb.shape[:2],255,np.uint8)]),'RGBA')

def dilate(img,mask,steps):
    """Spread painted colour into unpainted texels so mip-maps and bilinear filtering do not pull in black."""
    img=img.copy();mask=mask.copy()
    for _ in range(steps):
        if mask.all():break
        acc=np.zeros_like(img);cnt=np.zeros(mask.shape,np.float32)
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            s=np.roll(mask,(dy,dx),(0,1));v=np.roll(img,(dy,dx),(0,1));acc+=v*s[...,None];cnt+=s
        fill=(~mask)&(cnt>0);img[fill]=acc[fill]/cnt[fill][...,None];mask|=fill
    return img

def detail_height(pos,ident):
    """Material-dependent fine relief (cm) evaluated in world space: skin pores and wrinkles, weave, hammered iron, rings."""
    m=masks(ident);h=np.zeros(pos.shape[:2],np.float32)
    if m['skin'].any():
        h[m['skin']]=(0.25*(fbm(pos,1.2,3,21)-0.5)+0.12*(noise(pos,0.25,22)-0.5)+0.18*(noise(pos*np.array((1,6,1)),1.5,23)-0.5))[m['skin']]
        # forehead furrows and crow's feet
        brow=np.clip((pos[...,1]-167)/2,0,1)*np.clip((178-pos[...,1])/2,0,1)*np.clip((-pos[...,2]-7)/3,0,1)*np.clip((12-np.abs(pos[...,0]))/3,0,1)
        h+=0.4*brow*np.sin(pos[...,1]/2.2*2*np.pi+0.8*np.sin(pos[...,0]/4))
        feet=np.clip((np.abs(pos[...,0])-7)/2,0,1)*np.clip((12-np.abs(pos[...,0]))/2,0,1)*np.clip((168-np.abs(pos[...,1]-164)*2)/4,0,1)*np.clip((-pos[...,2]-8)/3,0,1)
        h+=0.3*feet*np.sin((pos[...,1]-np.abs(pos[...,0])*0.6)/1.6*2*np.pi)
    for k,amp,scale in [('cloth',0.12,0.3),('pad',0.2,0.6),('leather',0.15,0.5),('fur',0.35,0.3),('rope',0.3,0.4),('bone',0.12,0.8)]:
        if m[k].any():h[m[k]]=(amp*(noise(pos,scale,30+len(k))-0.5)+amp*0.6*(fbm(pos,4,2,40+len(k))-0.5))[m[k]]
    if m['iron'].any():h[m['iron']]=(0.3*(fbm(pos,5,3,51)-0.5))[m['iron']]
    if m['mail'].any():
        u=pos[...,0]+pos[...,2]*0.3;v=pos[...,1];h[m['mail']]=(0.35*np.clip(np.cos(u/1.1*2*np.pi)*np.cos(v/1.1*2*np.pi),0,1))[m['mail']]
    return h

def normal_rgba(stem,size):
    """Native-style normal map (R=X, G=Y, B=0, A=128): the baked sculpt normals with per-material surface detail layered on."""
    p=Path(str(stem)+'_normal.png')
    if not p.exists():return Image.new('RGBA',(size,size),(128,128,0,128))
    n=np.asarray(Image.open(p).convert('RGB'),np.float32)
    bad=np.abs(n[...,2]-255)>140;n[bad]=(128,128,255)   # unbaked texels
    n=n/127.5-1
    ident,pos,ao=load_maps(stem)
    if ident.shape[:2]==n.shape[:2]:
        h=detail_height(pos,ident)
        # Texel-space gradients; the texel's world-space tangent frame comes from the position map.
        dhx=np.roll(h,-1,1)-np.roll(h,1,1);dhy=np.roll(h,-1,0)-np.roll(h,1,0)
        tx=np.linalg.norm(np.roll(pos,-1,1)-np.roll(pos,1,1),axis=-1);ty=np.linalg.norm(np.roll(pos,-1,0)-np.roll(pos,1,0),axis=-1)
        valid=(tx>1e-3)&(tx<3)&(ty>1e-3)&(ty<3)&~bad
        sx=np.where(valid,-dhx/np.maximum(tx,1e-3),0);sy=np.where(valid,dhy/np.maximum(ty,1e-3),0)   # image y runs against uv v
        d=np.dstack([sx,sy,np.ones_like(sx)]);d/=np.linalg.norm(d,axis=-1,keepdims=True)
        # Whiteout-style blend of the detail normal onto the baked one.
        n=np.dstack([n[...,0]+d[...,0],n[...,1]+d[...,1],n[...,2]*d[...,2]]);n/=np.maximum(np.linalg.norm(n,axis=-1,keepdims=True),1e-6)
    n=np.clip((n+1)*127.5,0,255)
    return Image.fromarray(np.dstack([n[...,0].astype(np.uint8),n[...,1].astype(np.uint8),np.zeros(n.shape[:2],np.uint8),np.full(n.shape[:2],128,np.uint8)]),'RGBA')

if __name__=='__main__':
    import sys
    stem=sys.argv[1];out=sys.argv[2];clan=tuple(int(x) for x in sys.argv[3].split(',')) if len(sys.argv)>3 else None
    paint(stem,clan).save(out)
