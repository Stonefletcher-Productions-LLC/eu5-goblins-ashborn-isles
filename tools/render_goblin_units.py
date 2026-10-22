"""Software preview of the exported goblin soldiers beside a native soldier (bind pose).

Reads native torso/leg/headgear meshes from the installed game and the built
goblin head. Diffuse only, simple lighting; for fit and silhouette review, not
a substitute for an in-engine render.
"""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
from pdx_binary import read

def shapes(path,skip_lods=True):
    tree=read(path);out=[]
    for obj in tree['children']:
        if obj['name']!='object':continue
        for shape in obj['children']:
            if skip_lods and 'lod' in shape['name'].lower() and 'lod0' not in shape['name'].lower():continue
            for m in shape['children']:
                if m['name']!='mesh':continue
                p=np.array(m['props']['p'][1]).reshape(-1,3);uv=np.array(m['props']['u0'][1]).reshape(-1,2)
                t=np.array(m['props']['tri'][1]).reshape(-1,3);out.append((p,uv,t))
    return out

def texture(path):
    return np.asarray(Image.open(path).convert('RGB'),float)/255

def render(parts,yaw,size=420,center=(0,118,0),extent=118):
    a=np.radians(yaw);R=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
    img=np.full((size,size,3),.86);z=np.full((size,size),np.inf);light=np.array([-.4,.7,-.6]);light/=np.linalg.norm(light)
    for p,uv,t,tex in parts:
        q=(p-center)@R.T;sx=(q[:,0]/extent*.5+.5)*size;sy=(.5-q[:,1]/extent*.5)*size;depth=q[:,2]
        for tri in t:
            # engine meshes face -z; camera looks along +z
            x,y,d=sx[tri],sy[tri],depth[tri]
            area=(x[1]-x[0])*(y[2]-y[0])-(x[2]-x[0])*(y[1]-y[0])
            if area<=0:continue
            n=np.cross(q[tri[1]]-q[tri[0]],q[tri[2]]-q[tri[0]]);n/=np.linalg.norm(n)+1e-12
            shade=.45+.6*max(0,-(n@(light@R.T)))
            x0,x1=int(max(0,np.floor(x.min()))),int(min(size-1,np.ceil(x.max())));y0,y1=int(max(0,np.floor(y.min()))),int(min(size-1,np.ceil(y.max())))
            if x1<x0 or y1<y0:continue
            X,Y=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
            den=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
            w0=((y[1]-y[2])*(X-x[2])+(x[2]-x[1])*(Y-y[2]))/den;w1=((y[2]-y[0])*(X-x[2])+(x[0]-x[2])*(Y-y[2]))/den;w2=1-w0-w1
            inside=(w0>=0)&(w1>=0)&(w2>=0)
            if not inside.any():continue
            D=w0*d[0]+w1*d[1]+w2*d[2];iy,ix=np.nonzero(inside);iy+=y0;ix+=x0;D=D[inside]
            closer=D<z[iy,ix];iy,ix,D=iy[closer],ix[closer],D[closer]
            W=np.stack([w0[inside][closer],w1[inside][closer],w2[inside][closer]],1);U=W@uv[tri]
            h,w,_=tex.shape;col=tex[np.clip((U[:,1]%1)*h,0,h-1).astype(int),np.clip((U[:,0]%1)*w,0,w-1).astype(int)]
            img[iy,ix]=np.clip(col*shade,0,1);z[iy,ix]=D
    return img

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--game',type=Path,required=True);ap.add_argument('--built',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    U=args.game/'in_game/gfx/models/units';H=args.built/'in_game/gfx/models/units/ashborn_goblins'
    def load(mesh,diffuse):return [(p,uv,t,texture(diffuse)) for p,uv,t in shapes(mesh)]
    human_body=load(U/'torso/unit_torso_armor_linen_tunic_rope/unit_torso_linen_tunic_rope.mesh',U/'torso/unit_torso_armor_linen_tunic_rope/unit_torso_linen_tunic_rope_diffuse.dds')+\
         load(U/'legs/unit_legs_woven_trousers_leather_shoes/unit_legs_woven_trousers_leather_shoes.mesh',U/'legs/unit_legs_woven_trousers_leather_shoes/unit_legs_woven_trousers_leather_shoes_diffuse.dds')
    human=load(U/'head/unit_head_north_german_male_adult_a/unit_head_german_a.mesh',U/'head/unit_head_north_german_male_adult_a/unit_head_01_diffuse.dds')
    from export_goblin_models import UNIT_SCALE
    body=lambda clan:load(H/'cm_goblin_soldier_body.mesh',H/f'cm_goblin_{clan}_soldier_body_diffuse.dds')
    outfit=lambda kind:load(H/f'cm_goblin_soldier_outfit_{kind}.mesh',H/f'cm_goblin_soldier_outfit_{kind}_diffuse.dds')
    cap=lambda kind:load(H/f'cm_goblin_soldier_cap_{kind}.mesh',H/f'cm_goblin_soldier_cap_{kind}_diffuse.dds')
    # Schematic scale applies to the whole unit: show goblins at their size next to the native soldier.
    def scaled(parts,s=UNIT_SCALE/.08):return [(p*s,uv,t,tex) for p,uv,t,tex in parts]
    soldiers=[human_body+human,scaled(body('cindermaw')+outfit('light')+cap('leather')),scaled(body('brackmaw')+outfit('heavy')+cap('iron')),scaled(body('giltfang')+outfit('light'))]
    row=[render(parts,-25,center=(0,100,0),extent=112) for parts in soldiers]+[render(soldiers[2],90,center=(0,100,0),extent=112)]
    close=[render(body('cindermaw')+outfit('light')+cap('leather'),-25,center=(0,140,0),extent=60),render(body('sootwake')+outfit('heavy')+cap('iron'),-25,center=(0,140,0),extent=60),
           render(body('reefhook')+outfit('heavy'),90,center=(0,140,0),extent=60),render(body('shatterfin'),0,center=(0,160,0),extent=35),render(body('giltfang')+cap('iron'),90,center=(0,160,0),extent=35)]
    Image.fromarray((np.concatenate([np.concatenate(row,1),np.concatenate(close,1)],0)*255).astype(np.uint8)).save(args.out)
