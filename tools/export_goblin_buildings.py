"""Generate the goblin city set: ramshackle shacks, stacked plank towers,
a chieftain's hall, a stake palisade and a junk market.

Everything is procedural (seeded) and written as native EU5 static meshes with
the same minimal container as the unit exporter. No Paradox meshes or textures
are copied; the city-data script only names vanilla meshes for buildings that
still borrow the Iroquois wooden set (ports, later forts, workshops).

Engine space: metres-like units, Y up, left handed. A city "diorama" tile spans
about 2 x 2 units (vanilla peasant dioramas are 2.0 wide and 0.44 tall).
Front faces satisfy cross(b-a, c-a) . normal > 0, as in vanilla building meshes.
"""
import argparse,json,math,struct,zlib
from pathlib import Path
import numpy as np
from PIL import Image
from pdx_binary import node,write

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/buildings/goblins'
MODEL_REL=Path('in_game/gfx/models/buildings/ashborn_goblins')
CITY_DATA=Path('main_menu/gfx/map/city_data/cm_ashborn_goblins.txt')
ATLAS='cm_goblin_buildings_atlas'
GRID=4;TILE=128;SIZE=GRID*TILE
TILE_WORLD=0.32  # world units covered by one atlas tile before a face is squeezed

# ---------------------------------------------------------------- textures
MATERIALS=['planks','planks_dark','planks_patched','thatch',
           'rust','basalt','daub','bark',
           'cloth_green','cloth_ochre','bone','shingles',
           'rope','ember','ash','iron']
MAT={m:i for i,m in enumerate(MATERIALS)}
ROUGH={'rust':170,'iron':150,'bone':190,'ember':120}

def noise(rng,n,octaves=4):
    out=np.zeros((n,n))
    for o in range(octaves):
        cells=2**(o+2);g=rng.random((cells+1,cells+1))
        x=np.linspace(0,cells,n,endpoint=False);i=x.astype(int);f=x-i;f=f*f*(3-2*f)
        a=g[i][:,i];b=g[i][:,i+1];c=g[i+1][:,i];d=g[i+1][:,i+1]
        fy=f[:,None];fx=f[None,:]
        out+=((a*(1-fx)+b*fx)*(1-fy)+(c*(1-fx)+d*fx)*fy)/2**o
    return (out-out.min())/(np.ptp(out)+1e-9)

def tile_pixels(name,rng):
    n=TILE;y,x=np.mgrid[0:n,0:n]/n;nz=noise(rng,n);fine=rng.random((n,n))
    height=np.full((n,n),.5)
    def planks(base,count,var=.18,gap=.35):
        widths=rng.uniform(.7,1.3,count);edges=np.cumsum(widths)/widths.sum()
        idx=np.searchsorted(edges,x[0],side='right').clip(0,count-1)
        tint=1+rng.uniform(-var,var,count)[idx][None,:]
        grain=.85+.15*np.sin((y*40+nz*6)*math.pi)*noise(rng,n,2)
        seam=np.abs(((x*widths.sum()*0+x)[0][None,:]-edges[idx][None,:]))<.012
        col=np.array(base)[None,None,:]*(tint*grain)[...,None]*(.8+.3*nz)[...,None]
        col[np.broadcast_to(seam,(n,n))]*=gap
        h=.5+.3*grain-.4*np.broadcast_to(seam,(n,n))
        # nail heads
        for _ in range(count):
            cx,cy=rng.integers(4,n-4,2);col[cy-1:cy+2,cx-1:cx+2]=(60,55,50)
        return col,h
    if name=='planks':col,height=planks((178,150,112),6)
    elif name=='planks_dark':col,height=planks((116,94,74),5,.25,.3)
    elif name=='planks_patched':
        col,height=planks((160,134,100),7,.35)
        for _ in range(3):
            w,h=rng.integers(20,48,2);px,py=rng.integers(0,n-48,2)
            col[py:py+h,px:px+w]=col[py:py+h,px:px+w]*np.array([1.15,.9,.7])
    elif name=='thatch':
        s=np.sin((x*90+nz*12+fine*1.5)*math.pi)
        col=np.array((196,166,96))[None,None,:]*(.65+.25*s+.2*nz)[...,None]
        bands=(np.sin(y*math.pi*8)>.85)
        col[bands]*=.7;height=.5+.4*s*nz
    elif name=='rust':
        corr=.5+.5*np.sin(x*math.pi*16)
        rust=noise(rng,n,5)
        col=(np.array((120,110,100))*(1-rust[...,None])+np.array((140,70,35))*rust[...,None])*(.7+.35*corr)[...,None]
        height=corr
    elif name=='basalt':
        cells=noise(rng,n,3);cracks=np.abs(np.sin(cells*25))<.12
        col=np.array((84,80,82))[None,None,:]*(.7+.5*nz)[...,None];col[cracks]*=.5;height=1-cracks*.8
    elif name=='daub':
        col=np.array((150,124,90))[None,None,:]*(.75+.4*nz+.1*fine)[...,None]
        sticks=np.abs(np.sin((x+y*.2)*math.pi*10))<.08;col[sticks]*=.75
    elif name=='bark':
        rings=np.sin((y*30+nz*8)*math.pi)
        col=np.array((120,92,64))[None,None,:]*(.75+.2*rings+.2*fine)[...,None];height=.5+.4*rings
    elif name in('cloth_green','cloth_ochre'):
        base=(68,108,52) if name=='cloth_green' else (176,128,48)
        weave=.9+.1*np.sin(x*math.pi*128)*np.sin(y*math.pi*128)
        col=np.array(base)[None,None,:]*(weave*(.7+.45*nz))[...,None]
        holes=(noise(rng,n,5)>.86);col[holes]*=.45
    elif name=='bone':
        col=np.array((214,204,176))[None,None,:]*(.8+.25*nz)[...,None]
    elif name=='shingles':
        row=(y*8).astype(int);off=(row%2)*.5
        seam=(np.abs(((x*6+off)%1)-.5)>.46)|(((y*8)%1)>.9)
        col=np.array((98,86,78))[None,None,:]*(.7+.5*nz)[...,None]*(1+.15*rng.uniform(-1,1,9)[row][...,None])
        col[seam]*=.45;height=1-seam*.7
    elif name=='rope':
        s=np.sin((x+y)*math.pi*24)
        col=np.array((150,126,82))[None,None,:]*(.7+.3*s)[...,None]
    elif name=='ember':
        hot=noise(rng,n,4)
        col=np.array((255,120,30))*hot[...,None]+np.array((40,20,15))*(1-hot[...,None])
    elif name=='ash':
        col=np.array((96,92,88))[None,None,:]*(.7+.4*nz)[...,None]
    elif name=='iron':
        col=np.array((70,70,74))[None,None,:]*(.8+.3*nz)[...,None]
    return np.clip(col,0,255),np.clip(height,0,1)

def build_textures():
    rng=np.random.default_rng(1337)
    diffuse=np.zeros((SIZE,SIZE,4));height=np.zeros((SIZE,SIZE));props=np.zeros((SIZE,SIZE,4))
    for i,name in enumerate(MATERIALS):
        r,c=divmod(i,GRID);col,h=tile_pixels(name,rng)
        sl=(slice(r*TILE,(r+1)*TILE),slice(c*TILE,(c+1)*TILE))
        diffuse[sl+(slice(0,3),)]=col;diffuse[sl+(3,)]=255;height[sl]=h
        props[sl+(3,)]=ROUGH.get(name,235)+np.zeros((TILE,TILE))
    # Tangent-space normal from the tile heights. Native building normals are
    # DXT5nm-like (X in alpha, Y in green); store Y in red as well.
    gy,gx=np.gradient(height*3.0)
    nx,ny=-gx,-gy;nz=np.ones_like(nx);l=np.sqrt(nx*nx+ny*ny+nz*nz)
    normal=np.zeros((SIZE,SIZE,4))
    normal[...,0]=normal[...,1]=(ny/l*.5+.5)*255;normal[...,3]=(nx/l*.5+.5)*255
    return [Image.fromarray(a.round().astype(np.uint8),'RGBA') for a in (diffuse,normal,props)]

# ---------------------------------------------------------------- geometry
def rot(yaw=0,tx=0,tz=0):
    cy,sy=math.cos(yaw),math.sin(yaw);cx,sx=math.cos(tx),math.sin(tx);cz,sz=math.cos(tz),math.sin(tz)
    Ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]);Rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);Rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    return Ry@Rx@Rz

class Mesh:
    def __init__(self):self.faces=[]
    def poly(self,pts,mat,inside=None):
        """Add a planar convex polygon. If inside is given, orient away from it."""
        pts=[np.asarray(p,float) for p in pts]
        n=np.cross(pts[1]-pts[0],pts[2]-pts[0])
        if np.linalg.norm(n)<1e-10:return
        if inside is not None and np.dot(n,np.mean(pts,0)-inside)<0:pts=pts[::-1]
        self.faces.append((pts,MAT[mat]))
    def solid(self,verts,faces,mat,face_mats=None):
        c=np.mean(verts,0)
        for i,f in enumerate(faces):self.poly([verts[j] for j in f],(face_mats or {}).get(i,mat),c)
    def box(self,center,size,mat,yaw=0,tilt=(0,0),shear=(0,0),top=None,bottom=False):
        w,h,d=np.asarray(size)/2;R=rot(yaw,*tilt)
        local=np.array([[x,y,z] for y in(-h,h) for z in(-d,d) for x in(-w,w)])
        local[4:,0]+=shear[0];local[4:,2]+=shear[1]
        v=(R@local.T).T+np.asarray(center,float)+np.array([0,h,0])
        faces=[[0,1,5,4],[2,3,7,6],[0,2,6,4],[1,3,7,5],[4,5,7,6]]+([[0,1,3,2]] if bottom else [])
        self.solid(v,faces,mat,{4:top} if top else None)
        return v
    def cylinder(self,base,radius,height,mat,sides=6,yaw=0,tilt=(0,0),cap=None,taper=1.0):
        R=rot(yaw,*tilt);ring=[(math.cos(a)*radius,math.sin(a)*radius) for a in np.linspace(0,2*math.pi,sides,endpoint=False)]
        lo=[R@np.array([x,0,z]) for x,z in ring];hi=[R@np.array([x*taper,height,z*taper]) for x,z in ring]
        v=np.array(lo+hi)+np.asarray(base,float)
        faces=[[i,(i+1)%sides,sides+(i+1)%sides,sides+i] for i in range(sides)]+[list(range(sides,2*sides))]
        self.solid(v,faces,mat,{sides:cap} if cap else None)
        return v[sides:].mean(0)
    def cone(self,base,radius,height,mat,sides=6,yaw=0,tilt=(0,0)):
        R=rot(yaw,*tilt);ring=[R@np.array([math.cos(a)*radius,0,math.sin(a)*radius]) for a in np.linspace(0,2*math.pi,sides,endpoint=False)]
        tip=R@np.array([0,height,0]);b=np.asarray(base,float);c=b+tip*.3
        for i in range(sides):self.poly([b+ring[i],b+ring[(i+1)%sides],b+tip],mat,c)
    def gable(self,center,w,d,h,mat,yaw=0,overhang=.03,end_mat=None,droop=0.0):
        """Ridge along local x at height h above center; eaves at center height."""
        R=rot(yaw);c=np.asarray(center,float);w=w/2+overhang;d=d/2+overhang
        p=lambda x,y,z:R@np.array([x,y,z])+c
        a,b=p(-w,0,-d),p(w,0,-d);e,f=p(-w,0,d),p(w,0,d)
        r0,r1=p(-w*.98,h,droop),p(w*.98,h,-droop)
        inside=c+R@np.array([0,h*.3,0])
        self.poly([a,b,r1,r0],mat,inside);self.poly([e,f,r1,r0],mat,inside)
        self.poly([a,e,r0],end_mat or mat,inside);self.poly([b,f,r1],end_mat or mat,inside)
        # underside so the roof never looks hollow from low camera angles
        self.poly([a,b,f,e],'planks_dark',inside+np.array([0,1,0]))
    def slab(self,p0,p1,width,thick,mat):
        """A plank/beam from p0 to p1 (centre line), width horizontal."""
        p0,p1=np.asarray(p0,float),np.asarray(p1,float);axis=p1-p0;L=np.linalg.norm(axis)
        side=np.cross(axis,[0,1,0]);side=side/np.linalg.norm(side) if np.linalg.norm(side)>1e-6 else np.array([1.,0,0])
        up=np.cross(side,axis);up/=np.linalg.norm(up)
        corners=[p+s*side*width/2+u*up*thick/2 for p in(p0,p1) for s in(-1,1) for u in(-1,1)]
        faces=[[0,1,3,2],[4,5,7,6],[0,1,5,4],[2,3,7,6],[0,2,6,4],[1,3,7,5]]
        self.solid(np.array(corners),faces,mat)

    def arrays(self):
        P=[];N=[];T=[];U=[];I=[]
        for pts,m in self.faces:
            pts=np.array(pts);n=np.cross(pts[1]-pts[0],pts[2]-pts[0]);n/=np.linalg.norm(n)
            u=pts[1]-pts[0];u/=np.linalg.norm(u);v=np.cross(n,u)
            lu=(pts-pts[0])@u;lv=(pts-pts[0])@v;lu-=lu.min();lv-=lv.min()
            span=max(lu.max(),lv.max(),1e-6);k=1/TILE_WORLD if span<=TILE_WORLD else 1/span
            r,c=divmod(m,GRID);inset=3/SIZE;cell=1/GRID-2*inset
            uv=np.c_[c/GRID+inset+lu*k*cell,r/GRID+inset+lv*k*cell]
            base=len(P);P.extend(pts);N.extend([n]*len(pts));T.extend([np.r_[u,1.0]]*len(pts));U.extend(uv)
            for i in range(1,len(pts)-1):I.append([base,base+i,base+i+1])
        return np.array(P),np.array(N),np.array(T),np.array(U),np.array(I,dtype=np.int64)

# ---------------------------------------------------------------- recipes
WALLS=['planks','planks','planks_patched','planks_dark','daub']
def shack(m,rng,pos,yaw,s=1.0,stilts=None,tall=1.0):
    x,z=pos;w,d=rng.uniform(.2,.32)*s,rng.uniform(.16,.25)*s;h=rng.uniform(.11,.16)*s*tall
    y0=0.0
    if stilts is None:stilts=rng.random()<.25
    if stilts:
        y0=rng.uniform(.04,.07)*s;R=rot(yaw)
        for sx in(-1,1):
            for sz in(-1,1):
                off=R@np.array([sx*w*.42,0,sz*d*.42])
                m.cylinder((x+off[0],-.02,z+off[2]),.008*s,y0+.03,'bark',4,tilt=(rng.normal(0,.08),rng.normal(0,.08)))
        # ladder
        f=R@np.array([0,0,d/2+.03*s]);m.slab((x+f[0],-.01,z+f[2]),(x+f[0]*.7,y0,z+f[2]*.7),.025*s,.006*s,'planks_dark')
    lean=(rng.normal(0,.035),rng.normal(0,.035))
    sh=(rng.normal(0,.012)*s,rng.normal(0,.012)*s)
    wall=rng.choice(WALLS)
    m.box((x,y0,z),(w,h,d),wall,yaw,lean,sh)
    R=rot(yaw,*lean);top=np.array([x,y0+h,z])+R@np.array([sh[0],0,sh[1]])-np.array([0,h*(1-math.cos(max(abs(lean[0]),abs(lean[1])))),0])
    # door and patches
    front=R@np.array([0,0,d/2+.002])
    m.box((x+front[0],y0,z+front[2]),(w*.28,h*.7,.006),'planks_dark',yaw)
    for _ in range(rng.integers(0,3)):
        side=rng.choice([-1,1]);o=R@np.array([side*(w/2+.003),0,rng.uniform(-d/3,d/3)])
        m.box((x+o[0],y0+rng.uniform(.01,h*.5),z+o[2]),(.004,rng.uniform(.03,.06)*s,rng.uniform(.03,.06)*s),rng.choice(['rust','planks_patched','cloth_ochre']),yaw)
    roof=rng.random()
    if roof<.45:
        # sagging lean-to of planks or corrugated scrap
        mat=rng.choice(['rust','rust','planks_dark','shingles'])
        hi=R@np.array([0,0,-d/2-.02*s]);lo=R@np.array([0,0,d/2+.035*s])
        rise=rng.uniform(.03,.06)*s
        m.slab(top+hi+np.array([0,rise,0]),top+lo,w+.04*s,.008*s,mat)
        if rng.random()<.5:  # a second, skewed sheet patching the first
            m.slab(top+hi*.4+np.array([rng.uniform(-w/3,w/3),rise*.85,0]),top+lo*.6+np.array([0,.01,0]),w*.45,.006*s,rng.choice(['rust','planks_patched']))
    else:
        mat=rng.choice(['thatch','thatch','shingles','planks_dark'])
        m.gable(top,w,d,rng.uniform(.05,.09)*s,mat,yaw+rng.normal(0,.04),.025*s,end_mat=rng.choice(['planks','daub','planks_patched']),droop=rng.normal(0,.01)*s)
    if rng.random()<.55:  # crooked chimney pipe or stone stack
        o=R@np.array([rng.uniform(-w/3,w/3),0,rng.uniform(-d/3,d/3)])
        if rng.random()<.6:m.cylinder(top+o,.012*s,rng.uniform(.06,.11)*s,'rust',5,tilt=(rng.normal(0,.2),rng.normal(0,.2)),cap='iron')
        else:m.box(top+o-np.array([0,.02*s,0]),(.03*s,rng.uniform(.07,.1)*s,.03*s),'basalt',yaw+rng.normal(0,.3),(rng.normal(0,.08),rng.normal(0,.08)),top='ember')
    return max(w,d)*.65

def junk(m,rng,pos,s=1.0):
    x,z=pos;k=rng.random()
    if k<.4:m.cylinder((x,0,z),.018*s,.035*s,'planks_dark',6,cap='planks')
    elif k<.7:m.box((x,0,z),(.03*s,.025*s,.03*s),rng.choice(['planks','planks_patched']),rng.uniform(0,6),(rng.normal(0,.1),0))
    elif k<.85:m.cone((x,0,z),.035*s,.03*s,rng.choice(['ash','basalt']),5,rng.uniform(0,6))
    else:  # bone pile
        for _ in range(3):m.slab((x+rng.normal(0,.015),.005,z+rng.normal(0,.015)),(x+rng.normal(0,.02),.012,z+rng.normal(0,.02)),.006*s,.006*s,'bone')

def fence(m,rng,a,b,s=1.0,mat='bark'):
    a,b=np.asarray(a,float),np.asarray(b,float);n=max(2,int(np.linalg.norm(b-a)/(.06*s)))
    tops=[]
    for t in np.linspace(0,1,n):
        p=a+(b-a)*t;h=rng.uniform(.035,.055)*s
        tops.append(m.cylinder((p[0],-.01,p[1]),.005*s,h,mat,4,tilt=(rng.normal(0,.12),rng.normal(0,.12))))
    for i in range(len(tops)-1):
        if rng.random()<.85:m.slab(tops[i]-[0,.012*s,0],tops[i+1]-[0,.015*s,0],.008*s,.004*s,'planks_dark')

def bonfire(m,rng,pos,s=1.0):
    x,z=pos
    for a in np.linspace(0,2*math.pi,7,endpoint=False):
        m.box((x+math.cos(a)*.03*s,0,z+math.sin(a)*.03*s),(.016*s,.012*s,.016*s),'basalt',a)
    m.cone((x,0,z),.022*s,.03*s,'ember',5)

def scatter(rng,count,radius,extent,placed=None,tries=400):
    placed=placed if placed is not None else []
    out=[]
    for _ in range(tries):
        if len(out)>=count:break
        p=rng.uniform(-extent,extent,2)
        if all(np.hypot(*(p-q))>radius+r for q,r in placed):
            placed.append((p,radius));out.append(p)
    return out

def peasant(seed):
    rng=np.random.default_rng(seed);m=Mesh();placed=[]
    for p in scatter(rng,rng.integers(7,10),.21,.74,placed):
        shack(m,rng,p,rng.uniform(0,2*math.pi),rng.uniform(.85,1.15))
    for _ in range(2):
        a=rng.uniform(-.75,.75,2);b=np.clip(a+rng.normal(0,.22,2),-.9,.9);fence(m,rng,a,b)
    for p in scatter(rng,rng.integers(4,8),.03,.85,placed):junk(m,rng,p)
    if rng.random()<.6:
        p=scatter(rng,1,.05,.5,placed)
        if p:bonfire(m,rng,p[0])
    return m

def burgher(seed):
    rng=np.random.default_rng(seed);m=Mesh();placed=[];tops=[]
    for p in scatter(rng,rng.integers(4,6),.3,.66,placed):
        yaw=rng.uniform(0,2*math.pi);w,d,h=rng.uniform(.28,.38),rng.uniform(.22,.3),rng.uniform(.15,.2)
        lean=(rng.normal(0,.03),rng.normal(0,.03))
        m.box((p[0],0,p[1]),(w,h,d),rng.choice(WALLS),yaw,lean,(rng.normal(0,.01),rng.normal(0,.01)))
        m.box((p[0],0,p[1]+d/2+.002),(w*.25,h*.6,.006),'planks_dark',yaw)
        y=h;cx,cz=p
        for level in range(rng.integers(1,3)):
            # each upper storey overhangs and twists a little more
            yaw2=yaw+rng.normal(0,.25);ox,oz=rng.normal(0,.035,2);w2,d2=w*rng.uniform(.75,1.05),d*rng.uniform(.8,1.1)
            h2=h*rng.uniform(.75,.95)
            m.box((cx+ox,y,cz+oz),(w2,h2,d2),rng.choice(WALLS),yaw2,(rng.normal(0,.04),rng.normal(0,.04)),(rng.normal(0,.012),rng.normal(0,.012)))
            R=rot(yaw2)
            for sx in(-1,1):  # props holding up the overhang
                q=R@np.array([sx*w2*.45,0,d2*.5])
                m.slab((cx+ox+q[0],y-.05,cz+oz+q[2]+.03),(cx+ox+q[0],y+.005,cz+oz+q[2]),.008,.008,'bark')
            cx+=ox;cz+=oz;y+=h2;w,d=w2,d2;yaw=yaw2
        top=np.array([cx,y,cz])
        if rng.random()<.5:m.gable(top,w,d,rng.uniform(.07,.11),rng.choice(['thatch','shingles']),yaw,.03,end_mat='planks_patched')
        else:
            R=rot(yaw);m.slab(top+R@np.array([0,0,-d/2-.02])+[0,.06,0],top+R@np.array([0,0,d/2+.04]),w+.05,.009,rng.choice(['rust','shingles']))
        if rng.random()<.7:m.cylinder(top+[rng.uniform(-.03,.03),0,0],.013,rng.uniform(.08,.14),'rust',5,tilt=(rng.normal(0,.2),rng.normal(0,.2)),cap='iron')
        if rng.random()<.5:  # banner pole
            pole=m.cylinder(top+[0,0,.02],.004,.16,'bark',4)
            m.box(pole-[0,.06,0],(.004,.05,.035),rng.choice(['cloth_green','cloth_ochre']),rng.uniform(0,6))
        tops.append(top)
    for i in range(len(tops)-1):  # rope-and-plank catwalks between stacks
        a,b=tops[i]-[0,.05,0],tops[i+1]-[0,.06,0]
        if np.linalg.norm(a-b)<.8:m.slab(a,b,.035,.006,'planks_patched')
    for p in scatter(rng,rng.integers(2,4),.15,.8,placed):shack(m,rng,p,rng.uniform(0,6.3),.9)
    for p in scatter(rng,rng.integers(4,8),.03,.85,placed):junk(m,rng,p)
    return m

def noble(seed):
    rng=np.random.default_rng(seed);m=Mesh();yaw=rng.uniform(-.3,.3)
    # chieftain's hall: long, low, heavily roofed, bone horns on the ridge ends
    L,D,H=1.0,.5,.22
    m.box((0,0,0),(L,H,D),'planks_dark',yaw,(0,rng.normal(0,.02)),(0,0),top='planks_dark')
    m.box(rot(yaw)@np.array([0,0,D/2+.003]),(.14,.15,.01),'iron',yaw)
    for x in np.linspace(-L/2+.05,L/2-.05,6):
        q=rot(yaw)@np.array([x,0,D/2+.012]);m.cylinder(q,.013,H+.02,'bark',6)
    m.gable((0,H,0),L,D,.24,'thatch',yaw,.07,end_mat='planks_patched',droop=.01)
    for sx in(-1,1):
        q=rot(yaw)@np.array([sx*L*.5,H+.24,0])
        m.cone(q,.02,.14,'bone',5,tilt=(0,sx*.6));m.cone(q,.018,.12,'bone',5,tilt=(.5,sx*.4))
    # teetering watchtower
    tx,tz=L*.38,-D*.95
    top=.62
    for sx in(-1,1):
        for sz in(-1,1):
            m.slab((tx+sx*.08,0,tz+sz*.08),(tx+sx*.045,top,tz+sz*.045),.022,.022,'bark')
    for y in(.2,.42):
        m.slab((tx-.075,y,tz-.075),(tx+.07,y+.04,tz+.075),.012,.012,'planks_dark')
    m.box((tx,top,tz),(.2,.012,.2),'planks',.1)
    m.box((tx,top+.012,tz),(.15,.11,.15),'planks_patched',.15,(.03,-.04),(.012,0))
    m.cone((tx+.01,top+.125,tz),.13,.16,'shingles',4,.95)
    pole=m.cylinder((tx+.01,top+.25,tz),.005,.18,'bark',4)
    m.box(pole-[0,.075,-.03],(.004,.06,.06),'cloth_green',0)
    # palisade arc and a few retainers' shacks
    pts=[(math.cos(a)*.95,math.sin(a)*.9) for a in np.linspace(.5,2.6,9)]
    for a,b in zip(pts,pts[1:]):stakes(m,rng,a,b,.12)
    placed=[(np.array([0,0]),.6),(np.array([tx,tz]),.18)]
    for p in scatter(rng,3,.18,.85,placed):shack(m,rng,p,rng.uniform(0,6.3),1.0)
    bonfire(m,rng,(-.3,.45),1.4)
    for p in scatter(rng,6,.03,.85,placed):junk(m,rng,p)
    return m

def stakes(m,rng,a,b,h,s=1.0):
    a,b=np.asarray(a,float),np.asarray(b,float);n=max(2,int(np.linalg.norm(b-a)/(.032*s)))
    for t in np.linspace(0,1,n,endpoint=False):
        p=a+(b-a)*t;hh=h*rng.uniform(.8,1.15);tilt=(rng.normal(0,.05),rng.normal(0,.05))
        top=m.cylinder((p[0],-.02,p[1]),.016*s,hh,'bark',5,rng.uniform(0,6),tilt)
        m.cone(top,.016*s,.035*s,'planks',5,0,tilt)

def tower(m,rng,pos,h,s=1.0):
    x,z=pos
    for sx in(-1,1):
        for sz in(-1,1):m.slab((x+sx*.08*s,-.02,z+sz*.08*s),(x+sx*.06*s,h,z+sz*.06*s),.025*s,.025*s,'bark')
    m.slab((x-.07*s,h*.45,z-.07*s),(x+.07*s,h*.5,z+.07*s),.012*s,.012*s,'planks_dark')
    m.box((x,h,z),(.2*s,.012*s,.2*s),'planks',rng.uniform(0,.3))
    m.box((x,h+.012*s,z),(.17*s,.07*s,.17*s),'planks_patched',rng.uniform(0,.3),(rng.normal(0,.04),rng.normal(0,.04)))
    m.cone((x,h+.08*s,z),.15*s,.14*s,rng.choice(['thatch','shingles']),4,.78)

def stockade(seed,big=False):
    rng=np.random.default_rng(seed);m=Mesh();r=1.0 if not big else 1.15;h=.42 if not big else .55
    corners=[(r*math.cos(a)+rng.normal(0,.05),r*math.sin(a)+rng.normal(0,.05)) for a in np.linspace(math.pi/4,math.pi/4+2*math.pi,7)[:-1]]
    gate=0
    for i in range(len(corners)):
        a,b=np.array(corners[i]),np.array(corners[(i+1)%len(corners)])
        if i==gate:
            mid=(a+b)/2;dirv=(b-a)/np.linalg.norm(b-a)
            stakes(m,rng,a,mid-dirv*.16,h);stakes(m,rng,mid+dirv*.16,b,h)
            for g in(mid-dirv*.2,mid+dirv*.2):tower(m,rng,g,h+.3)
            gate_top=np.r_[mid[0],h+.12,mid[1]]
            m.slab(gate_top-np.r_[dirv[0],0,dirv[1]]*.2,gate_top+np.r_[dirv[0],0,dirv[1]]*.2,.04,.03,'planks_dark')
            for k in range(3):m.cone(gate_top+np.r_[dirv[0],0,dirv[1]]*(k-1)*.12+[0,.015,0],.012,.06,'bone',4)
        else:stakes(m,rng,a,b,h)
    for c in corners[2:5:2] if not big else corners[1:]:
        if not big or rng.random()<.8:tower(m,rng,c,h+.25)
    # keep: a fat crooked hut in the middle, plus clutter
    placed=[(np.array(c),.2) for c in corners]
    shack(m,rng,(rng.normal(0,.1),rng.normal(0,.1)),rng.uniform(0,6.3),2.2 if big else 1.8,stilts=False)
    placed.append((np.zeros(2),.35))
    for p in scatter(rng,3 if big else 2,.16,.6,placed):shack(m,rng,p,rng.uniform(0,6.3),1.1)
    for p in scatter(rng,8,.03,.65,placed):junk(m,rng,p)
    return m

def market(seed):
    rng=np.random.default_rng(seed);m=Mesh();placed=[(np.zeros(2),.22)]
    m.cylinder((0,0,0),.03,.32,'bark',6)  # totem
    for k in range(3):m.box((0,.08+k*.08,0),(.07,.05,.07),rng.choice(['bone','planks_patched','basalt']),rng.uniform(0,6))
    for p in scatter(rng,6,.15,.7,placed):
        yaw=rng.uniform(0,6.3);R=rot(yaw);hh=rng.uniform(.09,.12)
        for sx in(-1,1):
            for sz in(-1,1):
                q=R@np.array([sx*.07,0,sz*.05]);m.cylinder((p[0]+q[0],0,p[1]+q[2]),.005,hh+(.02 if sz<0 else 0),'bark',4)
        m.box((p[0],0,p[1]),(.13,.04,.08),'planks_patched',yaw)
        a=R@np.array([0,0,-.06]);b=R@np.array([0,0,.07])
        m.slab((p[0]+a[0],hh+.02,p[1]+a[2]),(p[0]+b[0],hh-.01,p[1]+b[2]),.17,.004,rng.choice(['cloth_green','cloth_ochre','rust']))
        for _ in range(2):junk(m,rng,p+rng.normal(0,.06,2),.8)
    return m

MODELS={
    'cm_goblin_peasant_a':lambda:peasant(11),'cm_goblin_peasant_b':lambda:peasant(23),
    'cm_goblin_peasant_c':lambda:peasant(37),'cm_goblin_peasant_d':lambda:peasant(41),
    'cm_goblin_burgher_a':lambda:burgher(101),'cm_goblin_burgher_b':lambda:burgher(131),'cm_goblin_burgher_c':lambda:burgher(151),
    'cm_goblin_noble_a':lambda:noble(201),'cm_goblin_noble_b':lambda:noble(227),
    'cm_goblin_stockade':lambda:stockade(301),'cm_goblin_fort':lambda:stockade(331,True),
    'cm_goblin_market':lambda:market(401),
}

# ---------------------------------------------------------------- export
def prop(t,a):return (t,np.asarray(a).ravel().tolist())
def export_mesh(mesh,name,path):
    P,N,T,U,I=mesh.arrays()
    low,high=P.min(0),P.max(0);center=(low+high)/2
    shape=node(name+'Shape',children=[node('mesh',{'p':prop('f',P),'n':prop('f',N),'ta':prop('f',T),'u0':prop('f',U),'tri':prop('i',I),
        'boundingsphere':prop('f',np.r_[center,np.linalg.norm(P-center,axis=1).max()])},[
        node('aabb',{'min':prop('f',low),'max':prop('f',high)}),
        node('material',{'shader':('s','standard'),'diff':('s',ATLAS+'_diffuse.dds'),'n':('s',ATLAS+'_normal.dds'),'spec':('s',ATLAS+'_properties.dds')})])])
    write(path,node('root',{'pdxasset':('i',[1,0])},[node('object',children=[shape]),node('locator')]))
    return {'name':name,'triangles':int(len(I)),'vertices':int(len(P)),'aabb_min':low.round(3).tolist(),'aabb_max':high.round(3).tolist()}

def asset_text(name):
    return f'''pdxmesh = {{
\tname = "{name}_mesh"
\tfile = "{name}.mesh"

\tmeshsettings = {{
\t\tname = "{name}Shape"
\t\tindex = 0
\t\ttexture_diffuse = "{ATLAS}_diffuse.dds"
\t\ttexture_normal = "{ATLAS}_normal.dds"
\t\ttexture_specular = "{ATLAS}_properties.dds"
\t\tshader = "standard_building"
\t\tshader_file = "gfx/FX/pdxmesh.shader"
\t}}
}}

entity = {{
\tname = "{name}_entity"
\tpdxmesh = "{name}_mesh"
}}
'''

def city_data(tags):
    """Mesh lists + one culture_data per clan graphical culture.

    Goblin cultures carry `european_gfx <clan>_gfx`; the clan tag (priority 600)
    wins over european_gfx, so each needs its own culture_data block.
    Ports, bastions and later forts, workshops and military buildings borrow the
    vanilla Iroquois wooden set until goblin versions exist.
    """
    t='''# Generated by tools/export_goblin_buildings.py - edit the generator, not this file.
# Goblin city set: crooked plank shacks, stacked shanty towers, a chieftain's hall,
# stake palisades and a junk market.

mesh_list = {
\tname = "cm_goblin_noble"
\tscale_settings_small = { bias = -0.5 min = 0.95 max = 1.05 }
\tcm_goblin_noble_a_mesh = 1
\tcm_goblin_noble_b_mesh = 1
\tmaterial_index = 1
\tspawn_count = { curve = "standard_pop_curve" }
}
mesh_list = {
\tname = "cm_goblin_burgher"
\tscale_settings_small = { bias = -0.5 min = 0.95 max = 1.1 }
\tcm_goblin_burgher_a_mesh = 1
\tcm_goblin_burgher_b_mesh = 1
\tcm_goblin_burgher_c_mesh = 1
\tmaterial_index = 1
\tspawn_count = { curve = "standard_pop_curve" }
}
mesh_list = {
\tname = "cm_goblin_peasant"
\tscale_settings_small = { bias = -0.5 min = 0.9 max = 1.05 }
\tcm_goblin_peasant_a_mesh = 100
\tcm_goblin_peasant_b_mesh = 100
\tcm_goblin_peasant_c_mesh = 100
\tcm_goblin_peasant_d_mesh = 100
\tmaterial_index = 0
\tspawn_count = { curve = "standard_pop_curve" }
}
mesh_list = {
\tname = "cm_goblin_peasant_rural"
\tscale_settings_small = { bias = 0 min = 0.8 max = 0.9 }
\tcm_goblin_peasant_a_mesh = 1
\tcm_goblin_peasant_b_mesh = 1
\tcm_goblin_peasant_c_mesh = 1
\tcm_goblin_peasant_d_mesh = 1
\tmaterial_index = 0
\tspawn_count = { curve = "standard_pop_peasants_curve" }
}
mesh_list = {
\tname = "cm_goblin_farming"
\tscale_settings_small = { bias = 0 min = 1.0 max = 1.0 }
\tspawn_count = { curve = "standard_rgo_curve" }
\tcm_goblin_peasant_a_mesh = 1
\tcm_goblin_peasant_c_mesh = 1
\tresource_farmlands_a_mesh = 2
\tresource_farmlands_b_mesh = 2
}
mesh_list = {
\tname = "cm_goblin_stockade"
\tscale_settings_large = { bias = 0 min = 1.5 max = 1.5 }
\tcm_goblin_stockade_mesh = 1
\tshould_spawn_flags = yes
\ttag = fort
}
mesh_list = {
\tname = "cm_goblin_stockade_no_flag"
\tscale_settings_large = { bias = 0 min = 1.5 max = 1.5 }
\tcm_goblin_stockade_mesh = 1
\ttag = fort
}
mesh_list = {
\tname = "cm_goblin_fort"
\tscale_settings_large = { bias = 0 min = 1.5 max = 1.5 }
\tcm_goblin_fort_mesh = 1
\tmaterial_index = 1
\tshould_spawn_flags = yes
\ttag = fort
}
mesh_list = {
\tname = "cm_goblin_market"
\tscale_settings_small = { bias = 0 min = 0.9 max = 1.0 }
\tcm_goblin_market_mesh = 1
\tshould_spawn_flags = no
\tmaterial_index = 1
}
mesh_list = {
\tname = "cm_goblin_small_burgher"
\tscale_settings_small = { bias = 0 min = 0.9 max = 1.0 }
\tcm_goblin_burgher_a_mesh = 1
\tcm_goblin_burgher_c_mesh = 1
\tshould_spawn_flags = no
\tmaterial_index = 1
}

@cm_goblin_noble_mesh_list = cm_goblin_noble
@cm_goblin_burgher_mesh_list = cm_goblin_burgher
@cm_goblin_peasant_mesh_list = cm_goblin_peasant
@cm_goblin_peasant_rural_mesh = cm_goblin_peasant_rural
@cm_goblin_farming_mesh_list = cm_goblin_farming
'''
    for tag in tags:
        t+=f'''
culture_data = {{
\tgraphical_culture = {tag}

\tload_template player_buildings {{
\t\tdefault_bridge_meshes = iroquois_bridges
\t\tdock_meshes = iroquois_dock
\t\tdry_dock_meshes = iroquois_dry_dock
\t\tshipyard_meshes = iroquois_shipyard
\t\tgrand_shipyard_meshes = iroquois_grand_shipyard
\t\tnaval_base_meshes = iroquois_naval_base

\t\tstockade_meshes = cm_goblin_stockade
\t\tstockade_no_flag_meshes = cm_goblin_stockade_no_flag
\t\tfort_meshes = cm_goblin_fort
\t\tbastion_meshes = iroquois_bastion
\t\tstarfort_meshes = iroquois_starfort
\t\tfortress_meshes = iroquois_fortress

\t\tfactory_meshes = iroquois_factory
\t\tmarket_meshes = cm_goblin_market
\t\tpeasants_gathering_meshes = iroquois_peasants_gathering
\t\tculture_meshes = iroquois_culture
\t\tsmall_burgher_meshes = cm_goblin_small_burgher
\t\tmedium_burgher_meshes = iroquois_medium_burgher
\t\trepublican_assembly_meshes = iroquois_republic_assembly

\t\tmedium_military_meshes = iroquois_medium_military
\t\tregimental_camp_meshes = iroquois_regimental_camp
\t\tnoble_military_meshes = iroquois_noble_military
\t\tarmory_meshes = iroquois_armory
\t\tbarracks_meshes = iroquois_barracks
\t\ttraining_fields_meshes = iroquois_training_fields
\t}}

\tload_template nobles {{ mesh_list = @cm_goblin_noble_mesh_list }}
\tload_template burghers {{ mesh_list = @cm_goblin_burgher_mesh_list }}
\tload_template peasants {{ mesh_list = @cm_goblin_peasant_mesh_list }}
\tload_template peasant_rural {{ mesh_list = @cm_goblin_peasant_rural_mesh }}

\tload_template rgo_all {{ farming_mesh_list = @cm_goblin_farming_mesh_list }}

\tload_template unique_buildings {{
\t\tfort_meshes = cm_goblin_fort
\t\tbastion_meshes = iroquois_bastion
\t}}
}}
'''
    return t

def write_text(path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8-sig')

def build(out,meshes=None):
    out=Path(out);directory=out/MODEL_REL;directory.mkdir(parents=True,exist_ok=True)
    meshes=meshes or {k:f() for k,f in MODELS.items()}
    for img,suffix in zip(build_textures(),('diffuse','normal','properties')):img.save(directory/f'{ATLAS}_{suffix}.dds')
    report={'stage':'procedural-city-set','engine_tested':False,'models':[]}
    for name,mesh in meshes.items():
        report['models'].append(export_mesh(mesh,name,directory/(name+'.mesh')))
        write_text(directory/(name+'.asset'),asset_text(name))
    clans=json.loads((ROOT/'art/models/goblins/clans.json').read_text())['clans']
    tags=[c['culture']+'_gfx' for c in clans]
    write_text(out/CITY_DATA,city_data(tags));report['graphical_cultures']=tags
    return report

def runtime_paths():
    return [MODEL_REL/f'{ATLAS}_{s}.dds' for s in ('diffuse','normal','properties')]+\
           [MODEL_REL/(n+e) for n in MODELS for e in ('.mesh','.asset')]+[CITY_DATA]

# ---------------------------------------------------------------- previews
def glb(mesh,atlas_png,path):
    """Self-contained glTF 2.0 for any desktop 3D viewer (Z flipped back to RH)."""
    P,N,T,U,I=mesh.arrays();P=P*[1,1,-1];N=N*[1,1,-1];I=I[:,[0,2,1]]
    blobs=[P.astype('<f4').tobytes(),N.astype('<f4').tobytes(),U.astype('<f4').tobytes(),I.astype('<u4').tobytes(),atlas_png]
    views=[];offset=0;data=b''
    for b in blobs:
        pad=(-len(data))%4;data+=b'\0'*pad;offset=len(data);views.append({'buffer':0,'byteOffset':offset,'byteLength':len(b)});data+=b
    data+=b'\0'*((-len(data))%4)
    g={'asset':{'version':'2.0','generator':'export_goblin_buildings.py'},'scene':0,'scenes':[{'nodes':[0]}],
       'nodes':[{'mesh':0,'name':path.stem}],
       'meshes':[{'primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2},'indices':3,'material':0}]}],
       'materials':[{'pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':.9}}],
       'textures':[{'source':0,'sampler':0}],'samplers':[{'magFilter':9729,'minFilter':9987}],
       'images':[{'bufferView':4,'mimeType':'image/png'}],
       'buffers':[{'byteLength':len(data)}],'bufferViews':views,
       'accessors':[{'bufferView':0,'componentType':5126,'count':len(P),'type':'VEC3','min':P.min(0).tolist(),'max':P.max(0).tolist()},
                    {'bufferView':1,'componentType':5126,'count':len(N),'type':'VEC3'},
                    {'bufferView':2,'componentType':5126,'count':len(U),'type':'VEC2'},
                    {'bufferView':3,'componentType':5125,'count':I.size,'type':'SCALAR'}]}
    js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
    path.write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(data))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(data),0x004e4942)+data)

def render(mesh,atlas,size=420,yaw=.65,pitch=.62,span=None):
    """Tiny z-buffered rasteriser: textured, lambert lit, 3/4 view."""
    P,N,T,U,I=mesh.arrays();tex=np.asarray(atlas.convert('RGB'),float)
    cam=np.array([math.sin(yaw)*math.cos(pitch),math.sin(pitch),-math.cos(yaw)*math.cos(pitch)])
    f=-cam;r=np.cross([0,1,0],f);r/=np.linalg.norm(r);u=np.cross(f,r)
    V=np.array([r,u,f])  # screen x, screen y, depth (left-handed engine space)
    Q=P@V.T;span=span or (np.ptp(Q[:,:2],0).max()*1.1)
    mid=(Q[:,:2].min(0)+Q[:,:2].max(0))/2
    sx=(Q[:,0]-mid[0])/span*size+size/2;sy_=size/2-(Q[:,1]-mid[1])/span*size;z=Q[:,2]
    img=np.zeros((size,size,3))+np.array([226,222,212]);zb=np.full((size,size),np.inf)
    light=np.array([.45,.8,-.4]);light/=np.linalg.norm(light)
    for a,b,c in I:
        if np.dot(N[a],V[2])>=0:continue  # back face
        xs=np.array([sx[a],sx[b],sx[c]]);ys=np.array([sy_[a],sy_[b],sy_[c]])
        x0,x1=max(int(xs.min()),0),min(int(xs.max())+1,size);y0,y1=max(int(ys.min()),0),min(int(ys.max())+1,size)
        if x0>=x1 or y0>=y1:continue
        gx,gy=np.meshgrid(np.arange(x0,x1)+.5,np.arange(y0,y1)+.5)
        d=(ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2])
        if abs(d)<1e-9:continue
        w0=((ys[1]-ys[2])*(gx-xs[2])+(xs[2]-xs[1])*(gy-ys[2]))/d;w1=((ys[2]-ys[0])*(gx-xs[2])+(xs[0]-xs[2])*(gy-ys[2]))/d;w2=1-w0-w1
        inside=(w0>=0)&(w1>=0)&(w2>=0)
        if not inside.any():continue
        zz=w0*z[a]+w1*z[b]+w2*z[c];sub=zb[y0:y1,x0:x1];vis=inside&(zz<sub)
        if not vis.any():continue
        uv=w0[...,None]*U[a]+w1[...,None]*U[b]+w2[...,None]*U[c]
        px=(uv[...,0]*SIZE).astype(int).clip(0,SIZE-1);py=(uv[...,1]*SIZE).astype(int).clip(0,SIZE-1)
        shade=.45+.65*max(np.dot(N[a],light),0)
        region=img[y0:y1,x0:x1];region[vis]=tex[py,px][vis]*shade;sub[vis]=zz[vis]
    return Image.fromarray(img.clip(0,255).astype(np.uint8))

def previews(meshes,atlas):
    import io
    pdir=ART/'preview';pdir.mkdir(parents=True,exist_ok=True)
    buf=io.BytesIO();atlas.convert('RGB').save(buf,'PNG');png=buf.getvalue()
    atlas.convert('RGB').save(pdir/'atlas.png')
    tiles=[]
    for name,mesh in meshes.items():
        glb(mesh,png,pdir/f'{name}.glb')
        im=render(mesh,atlas);im.save(pdir/f'{name}.png');tiles.append((name,im))
    cols=4;rows=math.ceil(len(tiles)/cols);sheet=Image.new('RGB',(cols*420,rows*420),(226,222,212))
    for i,(n,im) in enumerate(tiles):sheet.paste(im,((i%cols)*420,(i//cols)*420))
    sheet.save(pdir/'city_set_sheet.png')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'mod');ap.add_argument('--previews',action='store_true')
    args=ap.parse_args();meshes={k:f() for k,f in MODELS.items()}
    report=build(args.out,meshes)
    if args.previews:previews(meshes,build_textures()[0])
    write_text(ART/'export.json',json.dumps(report,indent=2));print(json.dumps(report,indent=2))
