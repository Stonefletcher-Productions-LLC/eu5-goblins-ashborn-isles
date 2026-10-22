"""Sculpt the goblin soldier body in Blender (bpy) around the native EU5 soldier skeleton.

Kitbash sculpting: ellipsoids, tapered capsules and cones are placed on the
native bone positions (cm, bind pose, face toward -z), merged with a voxel
remesh into one watertight skin, smoothed, then decimated to the game budget.
Everything is parametric so proportions can be tuned from the constants below.
"""
import json,math,sys
from pathlib import Path
import bpy,bmesh
from mathutils import Vector,Euler,Matrix

def short(name):return name[len('Unit_Base_Rig_'):] if name.startswith('Unit_Base_Rig_') else name

def load_bones(path):
    """Native skeleton as a list of {name,parent,position} in bind pose (cm)."""
    return json.loads(Path(path).read_text())

def bone_positions(bones):
    return {short(b['name']):Vector(b['position']) for b in bones}

def build_armature(bones):
    arm=bpy.data.armatures.new('unit_skeleton');ob=bpy.data.objects.new('unit_skeleton',arm);bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.mode_set(mode='EDIT')
    children={i:[j for j,b in enumerate(bones) if b['parent']==i] for i in range(len(bones))}
    edit=[]
    for i,b in enumerate(bones):
        eb=arm.edit_bones.new(b['name']);head=Vector(b['position'])
        kids=[Vector(bones[j]['position']) for j in children[i] if (Vector(bones[j]['position'])-head).length>0.5]
        if kids:tail=sum(kids,Vector())/len(kids)
        elif b['parent']>=0:d=head-Vector(bones[b['parent']]['position']);tail=head+(d.normalized()*3 if d.length>0.5 else Vector((0,3,0)))
        else:tail=head+Vector((0,3,0))
        eb.head=head;eb.tail=tail;edit.append(eb)
    for i,b in enumerate(bones):
        if b['parent']>=0:edit[i].parent=edit[b['parent']]
    bpy.ops.object.mode_set(mode='OBJECT');return ob

def skin_to(ob,armature):
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);armature.select_set(True)
    bpy.context.view_layer.objects.active=armature
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    # Vertices that heat weighting missed fall back to the nearest bone.
    bones=[(b.name,b.head_local,b.tail_local) for b in armature.data.bones]
    missing=[v for v in ob.data.vertices if sum(g.weight for g in v.groups)<1e-6]
    for v in missing:
        best=min(bones,key=lambda b:(v.co-_closest(v.co,b[1],b[2])).length)
        ob.vertex_groups[best[0]].add([v.index],1.0,'REPLACE')
    # The native head joint sits at the crown, so heat weighting hands the skull to the neck bone.
    # Bind the skull to the head joint like vanilla heads, blending through the neck.
    head=ob.vertex_groups['Unit_Base_Rig_Head'];neck=ob.vertex_groups['Unit_Base_Rig_Neck']
    for v in ob.data.vertices:
        t=(v.co.y-HEAD_BLEND[0])/(HEAD_BLEND[1]-HEAD_BLEND[0])
        if t<=0:continue
        t=min(t,1);rest=1-t;total=sum(g.weight for g in v.groups) or 1
        for g in list(v.groups):ob.vertex_groups[g.group].add([v.index],g.weight/total*rest,'REPLACE')
        head.add([v.index],t,'ADD')
    return len(missing)
HEAD_BLEND=(150,158)

def _closest(p,a,b):
    d=b-a;t=max(0,min(1,(p-a).dot(d)/max(d.length_squared,1e-9)));return a+d*t

def unwrap(ob,margin=0.02):
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(88),island_margin=margin,area_weight=0.0);bpy.ops.object.mode_set(mode='OBJECT')

def export_mesh(ob,armature,path,weights_from=None):
    """Triangulated world-space mesh with up to 4 bone weights per vertex, bone indices in native order.
    weights_from=(pos,ix,w) copies the nearest body vertex's weights (clothing)."""
    import numpy as np
    if weights_from is not None:
        bp,bix,bw=weights_from;co=np.array([v.co for v in ob.data.vertices],np.float32)
        nearest=np.concatenate([np.argmin(((co[i:i+512,None,:]-bp[None])**2).sum(-1),axis=1) for i in range(0,len(co),512)])
        ob.vertex_groups.clear();groups={}
        names=[b.name for b in armature.data.bones]
        for vi,bi in enumerate(nearest):
            for k in range(4):
                if bix[bi,k]<0 or bw[bi,k]<=0:continue
                g=groups.get(bix[bi,k]) or groups.setdefault(bix[bi,k],ob.vertex_groups.new(name=names[bix[bi,k]]))
                g.add([vi],float(bw[bi,k]),'REPLACE')
    me=ob.data.copy();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    for poly in me.polygons:poly.use_smooth=True   # shared vertices across faces; hard edges come from the normal map and silhouette
    uv=me.uv_layers.active.data;names=[b.name for b in armature.data.bones];index={g.index:names.index(g.name) for g in ob.vertex_groups}
    pos=[];nor=[];uvs=[];tri=[];ix=[];w=[];cache={}
    me.calc_normals_split() if hasattr(me,'calc_normals_split') else None
    for poly in me.polygons:
        face=[]
        for li in poly.loop_indices:
            loop=me.loops[li];v=me.vertices[loop.vertex_index];key=(loop.vertex_index,tuple(round(c,4) for c in uv[li].uv),tuple(round(c,3) for c in loop.normal))
            if key not in cache:
                cache[key]=len(pos);pos.append(tuple(v.co));nor.append(tuple(loop.normal));uvs.append((uv[li].uv.x,1-uv[li].uv.y))
                groups=sorted(((index[g.group],g.weight) for g in v.groups if g.weight>0),key=lambda t:-t[1])[:4]
                total=sum(wt for _,wt in groups) or 1
                ix.append([g[0] for g in groups]+[-1]*(4-len(groups)));w.append([g[1]/total for g in groups]+[0]*(4-len(groups)))
            face.append(cache[key])
        tri.append(face)
    np.savez_compressed(path,pos=np.array(pos,np.float32),nor=np.array(nor,np.float32),uv=np.array(uvs,np.float32),tri=np.array(tri,np.int32),ix=np.array(ix,np.int32),w=np.array(w,np.float32))
    bpy.data.meshes.remove(me);return len(pos),len(tri)

# ---------------------------------------------------------------- primitives
def _obj(name,bm):
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free()
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);return ob

def ellipsoid(name,center,radii,rot=(0,0,0),segments=24,parts=None):
    bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=segments,v_segments=segments//2,radius=1)
    M=Matrix.Translation(Vector(center))@Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()@Matrix.Diagonal((*radii,1))
    bmesh.ops.transform(bm,matrix=M,verts=bm.verts);ob=_obj(name,bm)
    if parts is not None:parts.append(ob)
    return ob

def capsule(name,a,b,ra,rb,parts=None,segments=20):
    """Tapered capsule from a (radius ra) to b (radius rb)."""
    a,b=Vector(a),Vector(b);d=b-a;L=d.length
    bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=segments,radius1=ra,radius2=rb,depth=L)
    rot=Vector((0,0,1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm,matrix=Matrix.Translation((a+b)/2)@rot,verts=bm.verts)
    bmesh.ops.create_uvsphere(bm,u_segments=segments,v_segments=segments//2,radius=ra,matrix=Matrix.Translation(a))
    bmesh.ops.create_uvsphere(bm,u_segments=segments,v_segments=segments//2,radius=rb,matrix=Matrix.Translation(b))
    ob=_obj(name,bm)
    if parts is not None:parts.append(ob)
    return ob

def cone(name,base,tip,radii,parts=None,segments=16):
    """Pointed cone from base (elliptical radii) to tip."""
    base,tip=Vector(base),Vector(tip);d=tip-base;L=d.length
    bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,segments=segments,radius1=1,radius2=0.05,depth=L)
    rot=Vector((0,0,1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm,matrix=Matrix.Translation((base+tip)/2)@rot@Matrix.Diagonal((radii[0],radii[1],1,1)),verts=bm.verts)
    ob=_obj(name,bm)
    if parts is not None:parts.append(ob)
    return ob

def join(parts,name):
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:p.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join()
    ob=bpy.context.object;ob.name=name;ob.data.name=name;return ob

def remesh(ob,voxel,smooth_iterations=6):
    m=ob.modifiers.new('remesh','REMESH');m.mode='VOXEL';m.voxel_size=voxel;m.use_smooth_shade=True
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier='remesh')
    if smooth_iterations:
        s=ob.modifiers.new('smooth','SMOOTH');s.iterations=smooth_iterations;s.factor=0.5
        bpy.ops.object.modifier_apply(modifier='smooth')
    return ob

def decimate(ob,target_tris):
    tris=sum(len(p.vertices)-2 for p in ob.data.polygons)
    d=ob.modifiers.new('dec','DECIMATE');d.ratio=min(1,target_tris/max(tris,1));d.use_collapse_triangulate=True
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier='dec');return ob

def mirror(fn,*args,**kw):
    """Call fn for the left side and the mirrored right side."""
    out=[fn(*args,**kw)]
    def flip(v):return (-v[0],v[1],v[2])
    args2=[flip(a) if isinstance(a,(tuple,list,Vector)) and len(a)==3 and not isinstance(a[0],(tuple,list)) else a for a in args]
    kw2={k:((-v[0],v[1],v[2]) if k=='rot' else v) for k,v in kw.items()}
    if 'rot' in kw2:kw2['rot']=(kw['rot'][0],-kw['rot'][1],-kw['rot'][2])
    out.append(fn(*args2,**kw2));return out

# ------------------------------------------------------------- the goblin
P=dict(
    # trunk loft: (y, half-width x, half-depth z, centre z); hunched, pot-bellied, narrow pelvis
    trunk=[(96,11.5,8.5,1.5),(101,13,9,1),(107,13.5,11,-1),(113,13.5,13,-2.5),(119,13,12.5,-2),(125,13,11,-0.5),
           (131,14,10.5,1),(137,15.5,10.5,3),(142,17,10,5),(146,15,9.5,7),(150,10,7.5,7)],
    # head loft (y, rx, rz, cz): big cranium, long back of skull, narrow jaw
    head=[(149,3.5,3,-10),(152,6,5.5,-9),(155,8,7,-7),(158,9.5,9,-5.5),(161,11,11,-4),(164,12.5,12.5,-3),(167,13.2,13.8,-2.5),
          (170,13.2,14.5,-2),(173,12.6,14.2,-1.5),(176,11.3,13,-1),(179,9,11,-0.5),(182,5.5,7,0)],
    brow=(5.6,169,-13.8),brow_r=(5.4,2.6,3.6),brow_rot=(0,0,-10),
    eye=(5.4,166,-14.6),eye_r=2.9,
    cheek=(8.5,161,-10),cheek_r=(3.5,3,3.5),
    nose=[((0,165,-16),2.8),((0,161,-20.5),2.5),((0,157,-23),2.0)],
    ear_base=(10,167,0),ear_tip=(37,181,8),ear_r=(5,1.6),
    mouth=(0,154.5,-13),mouth_w=5.5,mouth_depth=1.6,
    neck=((0,146,0),(0,158,-6),6.5,6.8),
    hump=(0,146,11),hump_r=(11,9,8),
    shoulder_r=6.6,upper_arm=(4.8,3.9),forearm=(4.3,3.5),
    palm_center=(37,95.5,2),palm_r=(2.2,6,4.8),finger_r=1.5,thumb_r=1.6,claw=3.5,
    thigh=(6.3,4.6),knee_r=5.2,calf=(4.6,3.2),
    ankle_r=3.6,foot_center=(15.5,6.5,-3),foot_r=(6.2,5,12),toe_len=6,toe_r=(1.9,1.4),
)

def loft(name,rows,ry,parts,segments=32):
    """Closed lofted surface through elliptical rings (y, rx, rz, cz); ry is unused (kept for the parameter table)."""
    bm=bmesh.new();rings=[]
    for y,rx,rz,cz in rows:
        ring=[bm.verts.new((rx*math.cos(2*math.pi*i/segments),y,cz+rz*math.sin(2*math.pi*i/segments))) for i in range(segments)]
        rings.append(ring)
    for r0,r1 in zip(rings,rings[1:]):
        for i in range(segments):bm.faces.new((r0[i],r0[(i+1)%segments],r1[(i+1)%segments],r1[i]))
    for ring,y in ((rings[0],rows[0][0]),(rings[-1],rows[-1][0])):
        c=bm.verts.new((0,y,sum(v.co.z for v in ring)/segments))
        for i in range(segments):bm.faces.new((ring[i],ring[(i+1)%segments],c))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);parts.append(_obj(name,bm))

def crease(ob,center,width,depth,height=1.2):
    """Push vertices near a horizontal line inward (mouth slit)."""
    cx,cy,cz=center
    for v in ob.data.vertices:
        dx=abs(v.co.x-cx)/width;dy=abs(v.co.y-cy)/height
        if dx<1 and dy<1 and v.co.z<cz+6:
            w=(1-dx*dx)*(1-dy*dy);v.co.z+=depth*w

def sculpt_body(B,voxel=0.6,target_tris=6000):
    parts=[]
    E=lambda n,c,r,rot=(0,0,0):ellipsoid(n,c,r,rot,parts=parts)
    C=lambda n,a,b,ra,rb:capsule(n,a,b,ra,rb,parts=parts)
    K=lambda n,a,b,r:cone(n,a,b,r,parts=parts)
    # head
    loft('head',P['head'],4,parts)
    mirror(E,'brow',P['brow'],P['brow_r'],rot=P['brow_rot'])
    mirror(E,'eye',P['eye'],(P['eye_r'],)*3)
    mirror(E,'cheek',P['cheek'],P['cheek_r'])
    for i,(c,r) in enumerate(P['nose']):E(f'nose{i}',c,(r,r,r*1.2))
    mirror(K,'ear',P['ear_base'],P['ear_tip'],P['ear_r'])
    a,b,ra,rb=P['neck'];C('neck',a,b,ra,rb)
    # trunk
    loft('trunk',P['trunk'],4.5,parts);E('hump',P['hump'],P['hump_r'])
    for side in 'LR':
        s=1 if side=='L' else -1
        g=lambda n:B[side.replace('L','Left').replace('R','Right')+n]
        E(f'shoulder{side}',g('Arm'),(P['shoulder_r'],)*3)
        C(f'upperarm{side}',g('Arm'),g('ForeArm'),*P['upper_arm']);C(f'forearm{side}',g('ForeArm'),g('Hand'),*P['forearm'])
        pc=P['palm_center'];E(f'palm{side}',(s*pc[0],pc[1],pc[2]),P['palm_r'])
        for finger,r in [('Thumb',P['thumb_r']),('Index',P['finger_r']),('Ring',P['finger_r'])]:
            chain=[g(f'Hand{finger}{i}') for i in range(1,5)]
            for i in range(3):C(f'{finger}{side}{i}',chain[i],chain[i+1],r,r*0.85)
            tip=chain[3]+(chain[3]-chain[2]).normalized()*P['claw'];K(f'claw{finger}{side}',chain[3],tip,(r*0.8,r*0.6))
        C(f'thigh{side}',g('UpLeg'),g('Leg'),*P['thigh']);E(f'knee{side}',g('Leg'),(P['knee_r'],)*3)
        C(f'calf{side}',g('Leg'),g('Foot'),*P['calf'])
        fc=P['foot_center'];E(f'foot{side}',(s*fc[0],fc[1],fc[2]),P['foot_r']);C(f'ankle{side}',g('Foot'),(s*fc[0],fc[1],fc[2]),P['ankle_r'],P['ankle_r'])
        for j,(dx,dz) in enumerate([(-4.5,-1),(0,0),(4.5,-1)]):
            base=(s*(fc[0]+dx),3.2,fc[2]-P['foot_r'][2]+3+dz);tip=(s*(fc[0]+dx*1.3),2.4,base[2]-P['toe_len'])
            K(f'toe{side}{j}',base,tip,P['toe_r'])
    ob=join(parts,'goblin_body_hi');remesh(ob,voxel)
    crease(ob,P['mouth'],P['mouth_w'],P['mouth_depth'])
    hi=ob;lo=hi.copy();lo.data=hi.data.copy();lo.name='goblin_body';bpy.context.collection.objects.link(lo)
    decimate(lo,target_tris);return hi,lo

# --------------------------------------------------------------- outfit
def tube(name,rows,segments=32,ragged=0,seed=1,arc=None,parts=None):
    """Open lofted band through rings (y, rx, rz, cz). ragged lowers random hem vertices; arc=(a0,a1) keeps a sector (degrees, -90 = front)."""
    import random;rng=random.Random(seed)
    bm=bmesh.new();rings=[]
    angles=[2*math.pi*i/segments for i in range(segments)]
    if arc:angles=[math.radians(arc[0]+(arc[1]-arc[0])*i/(segments-1)) for i in range(segments)]
    for k,(y,rx,rz,cz) in enumerate(rows):
        ring=[]
        for i,a in enumerate(angles):
            yy=y-(rng.random()*ragged if (k==0 and i%2==0) else 0)
            ring.append(bm.verts.new((rx*math.cos(a),yy,cz+rz*math.sin(a))))
        rings.append(ring)
    closed=arc is None
    for r0,r1 in zip(rings,rings[1:]):
        for i in range(segments if closed else segments-1):bm.faces.new((r0[i],r0[(i+1)%segments],r1[(i+1)%segments],r1[i]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);ob=_obj(name,bm)
    if parts is not None:parts.append(ob)
    return ob

def tube_along(name,a,b,r0,r1,width=None,segments=16,parts=None):
    """Band around a bone segment from a to b (radii r0 to r1)."""
    a,b=Vector(a),Vector(b);d=b-a;L=d.length
    bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=False,segments=segments,radius1=r0,radius2=r1,depth=L)
    rot=Vector((0,0,1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm,matrix=Matrix.Translation((a+b)/2)@rot,verts=bm.verts);ob=_obj(name,bm)
    if parts is not None:parts.append(ob)
    return ob

def patch(name,center,radius,rot=(0,0,0),u=24,v=12,cut=0.0,parts=None):
    """Sphere portion (cap): keeps the part of a UV sphere above local z=cut."""
    bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=u,v_segments=v,radius=1)
    bmesh.ops.delete(bm,geom=[vv for vv in bm.verts if vv.co.z<cut],context='VERTS')
    # Sphere poles are on z; the model is y-up, so turn the cap to open downward before placing it.
    M=Matrix.Translation(Vector(center))@Euler([math.radians(x) for x in rot]).to_matrix().to_4x4()@Matrix.Diagonal((*radius,1))@Matrix.Rotation(math.radians(-90),4,'X')
    bmesh.ops.transform(bm,matrix=M,verts=bm.verts);ob=_obj(name,bm)
    if parts is not None:parts.append(ob)
    return ob

def fit(ob,body,offset,thickness,subdiv=1,wrap=True):
    bpy.context.view_layer.objects.active=ob
    if subdiv:
        m=ob.modifiers.new('sub','SUBSURF');m.levels=subdiv;m.subdivision_type='CATMULL_CLARK';bpy.ops.object.modifier_apply(modifier='sub')
    if wrap:
        m=ob.modifiers.new('wrap','SHRINKWRAP');m.target=body;m.wrap_method='NEAREST_SURFACEPOINT';m.offset=offset;bpy.ops.object.modifier_apply(modifier='wrap')
    if thickness:
        m=ob.modifiers.new('solid','SOLIDIFY');m.thickness=thickness;m.offset=1;bpy.ops.object.modifier_apply(modifier='solid')
    return ob

def trunk_rows(y0,y1,grow,step=4,flare=0):
    """Rings following the sculpted trunk profile, grown outward by grow cm (flare adds toward the bottom)."""
    rows=[]
    ys=[r[0] for r in P['trunk']];y=y0
    while y<=y1+1e-6:
        import bisect
        i=max(1,min(len(ys)-1,bisect.bisect_left(ys,y)));t=(y-ys[i-1])/(ys[i]-ys[i-1]);t=max(0,min(1,t))
        a,b=P['trunk'][i-1],P['trunk'][i];rx,rz,cz=[a[k]+(b[k]-a[k])*t for k in (1,2,3)]
        f=flare*max(0,(y1-y)/(y1-y0))
        rows.append((y,rx+grow+f,rz+grow+f,cz));y+=step
    return rows

def build_outfit(B,body,kind):
    """Clothing pieces for 'light' (rags, leather) or 'heavy' (scrap iron over padding). Returns [(name, object)]."""
    pieces=[];R=lambda side:B[('Left' if side=='L' else 'Right')]
    g=lambda side,n:B[('Left' if side=='L' else 'Right')+n]
    # tunic: ragged hem below the hips, wide yoke over the shoulders, short sleeves
    rows=trunk_rows(82,134,1.6,step=4,flare=3.5 if kind=='light' else 2)+[(138,21,12.5,3.5),(142,23.5,12.5,4),(146,22,11.5,4.5),(150,10,8.5,3)]
    tun=tube('tunic',rows,ragged=7 if kind=='light' else 3,seed=3);fit(tun,body,0,1.0,subdiv=1,wrap=False);assign(tun,'cloth' if kind=='light' else 'pad');pieces.append(('tunic',tun))
    for side in 'LR':
        s=1 if side=='L' else -1
        ar,fa=g(side,'Arm'),g(side,'ForeArm');sl=tube_along(f'sleeve{side}',ar+(fa-ar)*0.05,ar+(fa-ar)*(0.55 if kind=='light' else 0.8),6.4,5.0);fit(sl,body,0,0.9,subdiv=1,wrap=False);assign(sl,'cloth' if kind=='light' else 'pad');pieces.append((f'sleeve{side}',sl))
        # bracers on the forearms, wraps on the shins
        fa,h=g(side,'ForeArm'),g(side,'Hand');br=tube_along(f'bracer{side}',fa+(h-fa)*0.25,fa+(h-fa)*0.9,5.2,4.4);fit(br,body,0,0.9,subdiv=1,wrap=False);assign(br,'leather');pieces.append((f'bracer{side}',br))
        lg,ft=g(side,'Leg'),g(side,'Foot');sh=tube_along(f'shin{side}',lg+(ft-lg)*0.2,lg+(ft-lg)*0.95,5.0,4.0);fit(sh,body,0,0.8,subdiv=1,wrap=False);assign(sh,'leather');pieces.append((f'shin{side}',sh))
    belt=tube('belt',trunk_rows(101,106,3.4,step=5));fit(belt,body,0,1.2,subdiv=0,wrap=False);assign(belt,'leather');pieces.append(('belt',belt))
    buckle=ellipsoid('buckle',(0,103.5,-12.6),(3.2,2.6,1.2));assign(buckle,'iron');pieces.append(('buckle',buckle))
    if kind=='heavy':
        # scrap breastplate: front sector of the trunk, thick and standing off the padding
        plate=tube('plate',trunk_rows(112,140,3.6,step=4),arc=(-165,-15),ragged=4,seed=5);fit(plate,body,0,1.6,subdiv=1,wrap=False);assign(plate,'iron');pieces.append(('plate',plate))
        for side,(rad,spikes) in (('R',(10.5,3)),('L',(8.5,0))):
            s=1 if side=='L' else -1;c=g(side,'Arm')+Vector((s*1.5,2.5,0))
            pa=patch(f'pauldron{side}',c,(rad,rad*0.8,rad),rot=(0,0,s*-25),cut=0.15);fit(pa,body,0,1.4,subdiv=1,wrap=False);assign(pa,'iron');pieces.append((f'pauldron{side}',pa))
            for k in range(spikes):
                a=math.radians(-40+40*k);base=c+Vector((s*rad*0.75*math.cos(a)*0.9,rad*0.7,rad*0.75*math.sin(a)));tip=base+(base-c).normalized()*7
                sp=cone(f'spike{side}{k}',base,tip,(1.6,1.6));assign(sp,'iron');pieces.append((f'spike{side}{k}',sp))
        # skirt of hanging iron strips over the hips
        for i in range(10):
            a=2*math.pi*i/10;rows=[(y,0,0,0) for y in (104,86)]
            strip=tube(f'tasset{i}',[(104,16.5,13.5,-0.5),(86,19.5,16.5,-0.5)],segments=4,arc=(math.degrees(a)-10,math.degrees(a)+10));fit(strip,body,0,0.9,subdiv=0,wrap=False);assign(strip,'iron');pieces.append((f'tasset{i}',strip))
    return pieces

def build_cap(B,body,kind):
    """Skull cap wrapped to the head; iron gets a crest spike and rivets."""
    center=Vector((0,166,-2.5));cap=patch(f'cap_{kind}',center,(15,15,16),rot=(-12,0,0),cut=0.1 if kind=='iron' else 0.06,u=28,v=14)
    fit(cap,body,1.0 if kind=='leather' else 1.6,1.1 if kind=='leather' else 1.5,subdiv=1);assign(cap,'leather' if kind=='leather' else 'iron');pieces=[(f'cap_{kind}',cap)]
    if kind=='iron':
        extra=[('crest',cone('crest',center+Vector((0,14,-2)),center+Vector((0,25,-5)),(2.2,2.2)))]
        for i,a in enumerate(range(0,360,45)):
            r=math.radians(a);p=center+Vector((12.5*math.cos(r),6,12.8*math.sin(r)))
            extra.append((f'rivet{i}',ellipsoid(f'rivet{i}',p,(1.1,1.1,1.1))))
        extra.append(('nasal',tube_along('nasal',center+Vector((0,6,-16)),center+Vector((0,-8,-20)),1.4,1.0,segments=6)))
        for n,ob in extra:assign(ob,'iron')
        pieces+=extra
    return pieces

# ----------------------------------------------------------------- bake
MATERIALS={'skin':(1,0,0),'cloth':(0,1,0),'leather':(0,0,1),'iron':(1,1,0),'pad':(0,1,1),'horn':(1,0,1)}

def material(kind):
    name=f'id_{kind}'
    if name in bpy.data.materials:return bpy.data.materials[name]
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree
    for n in list(nt.nodes):nt.nodes.remove(n)
    out=nt.nodes.new('ShaderNodeOutputMaterial');em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(*MATERIALS[kind],1)
    nt.links.new(em.outputs[0],out.inputs[0]);tex=nt.nodes.new('ShaderNodeTexImage');nt.nodes.active=tex
    pos=nt.nodes.new('ShaderNodeNewGeometry');m['pos_node']=pos.name;m['emit_node']=em.name;m['tex_node']=tex.name
    return m

def assign(ob,kind):
    ob.data.materials.clear();ob.data.materials.append(material(kind))

def join_pieces(pieces,name):
    obs=[ob for _,ob in pieces];ob=join(obs,name);return ob

def _pixels(img,size):
    import numpy as np
    return np.array(img.pixels[:],np.float32).reshape(size,size,4)[::-1]

def bake_maps(ob,size,hi=None,occluders=(),samples=16):
    """Bake id (material colour), world position, ambient occlusion and (from hi) tangent normal into ob's UV space."""
    import numpy as np
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=samples;sc.render.bake.margin=6
    for o in bpy.context.scene.objects:o.hide_render=o not in (ob,*occluders)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    maps={}
    def target(float_buffer):
        img=bpy.data.images.new('bake',size,size,float_buffer=float_buffer);img.colorspace_settings.name='Non-Color'
        for m in ob.data.materials:
            nt=m.node_tree;nt.nodes[m['tex_node']].image=img;nt.nodes.active=nt.nodes[m['tex_node']]
        return img
    def wire(position):
        for m in ob.data.materials:
            nt=m.node_tree;em=nt.nodes[m['emit_node']];pos=nt.nodes[m['pos_node']]
            for l in list(em.inputs[0].links):nt.links.remove(l)
            if position:nt.links.new(pos.outputs['Position'],em.inputs[0])
    img=target(False);wire(False);bpy.ops.object.bake(type='EMIT');maps['id']=_pixels(img,size)[...,:3];bpy.data.images.remove(img)
    img=target(True);wire(True);bpy.ops.object.bake(type='EMIT');maps['pos']=_pixels(img,size)[...,:3];bpy.data.images.remove(img);wire(False)
    img=target(True);sc.cycles.samples=max(samples,32);bpy.ops.object.bake(type='AO');maps['ao']=_pixels(img,size)[...,0];bpy.data.images.remove(img)
    if hi is not None:
        img=target(True);hi.hide_render=False;hi.select_set(True);bpy.context.view_layer.objects.active=ob
        bpy.ops.object.bake(type='NORMAL',use_selected_to_active=True,cage_extrusion=2.5,max_ray_distance=8,normal_space='TANGENT')
        maps['normal']=_pixels(img,size)[...,:3];bpy.data.images.remove(img);hi.select_set(False)
    for o in bpy.context.scene.objects:o.hide_render=False
    return maps

def save_maps(maps,stem):
    import numpy as np
    from PIL import Image
    Image.fromarray((np.clip(maps['id'],0,1)*255).round().astype(np.uint8)).save(f'{stem}_id.png')
    Image.fromarray((np.clip(maps['ao'],0,1)*255).round().astype(np.uint8)).save(f'{stem}_ao.png')
    np.savez_compressed(f'{stem}_pos.npz',pos=maps['pos'].astype(np.float16))
    if 'normal' in maps:Image.fromarray((np.clip(maps['normal'],0,1)*255).round().astype(np.uint8)).save(f'{stem}_normal.png')

# --------------------------------------------------------------- render
def clay_render(objects,out,size=700,views=((-30,0),(90,0)),extent=None,center=None):
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.device='CPU';sc.cycles.use_denoising=False
    sc.render.resolution_x=size;sc.render.resolution_y=size;sc.render.film_transparent=False
    world=sc.world or bpy.data.worlds.new('w');sc.world=world;world.use_nodes=True
    bg=world.node_tree.nodes['Background'];bg.inputs[0].default_value=(0.82,0.82,0.84,1);bg.inputs[1].default_value=1.0
    mat=bpy.data.materials.new('clay');mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs[0].default_value=(0.55,0.57,0.5,1)
    for ob in objects:
        if not ob.data.materials:ob.data.materials.append(mat)
    cam=bpy.data.objects.new('cam',bpy.data.cameras.new('c'));bpy.context.collection.objects.link(cam);sc.camera=cam
    cam.data.type='ORTHO'
    sun=bpy.data.objects.new('sun',bpy.data.lights.new('s','SUN'));bpy.context.collection.objects.link(sun)
    # Lights point down their -Z; aim the key from the front-upper-left and a weak fill from the front-right.
    sun.matrix_world=Vector((-0.5,0.8,-0.6)).to_track_quat('Z','Y').to_matrix().to_4x4();sun.data.energy=4;sun.data.angle=0.25
    fill=bpy.data.objects.new('fill',bpy.data.lights.new('f','SUN'));bpy.context.collection.objects.link(fill)
    fill.matrix_world=Vector((0.7,0.2,-0.5)).to_track_quat('Z','Y').to_matrix().to_4x4();fill.data.energy=1.2
    bg.inputs[1].default_value=0.6
    paths=[]
    for i,(yaw,pitch) in enumerate(views):
        c=Vector(center);yaw_r,pitch_r=math.radians(yaw),math.radians(pitch)
        # The model faces -z, so the camera sits on the -z side and looks toward +z.
        back=Vector((-math.sin(yaw_r),math.sin(pitch_r),-math.cos(yaw_r)*math.cos(pitch_r))).normalized()  # from target to camera
        cam.location=c+back*400
        right=Vector((0,1,0)).cross(back).normalized();up=back.cross(right)
        cam.matrix_world=Matrix(((right.x,up.x,back.x,cam.location.x),(right.y,up.y,back.y,cam.location.y),(right.z,up.z,back.z,cam.location.z),(0,0,0,1)))
        cam.data.ortho_scale=extent*2
        sc.render.filepath=f'{out}_{i}.png';bpy.ops.render.render(write_still=True);paths.append(sc.render.filepath)
    return paths

def native_reference(game,offset=(95,0,0)):
    """Vanilla soldier (head, tunic, trousers) as an untextured reference beside the goblin."""
    sys.path.insert(0,str(Path(__file__).parent));from pdx_binary import read
    U=Path(game)/'in_game/gfx/models/units';parts=[]
    for f in ['head/unit_head_north_german_male_adult_a/unit_head_german_a.mesh','torso/unit_torso_armor_linen_tunic_rope/unit_torso_linen_tunic_rope.mesh','legs/unit_legs_woven_trousers_leather_shoes/unit_legs_woven_trousers_leather_shoes.mesh']:
        for obj in read(U/f)['children']:
            if obj['name']!='object':continue
            for shape in obj['children']:
                if 'lod' in shape['name'].lower() and 'lod0' not in shape['name'].lower():continue
                m=next(n for n in shape['children'] if n['name']=='mesh')
                p=m['props']['p'][1];tri=m['props']['tri'][1]
                me=bpy.data.meshes.new(shape['name']);me.from_pydata([(p[i]+offset[0],p[i+1]+offset[1],p[i+2]+offset[2]) for i in range(0,len(p),3)],[],[tuple(tri[i:i+3]) for i in range(0,len(tri),3)])
                ob=bpy.data.objects.new(shape['name'],me);bpy.context.collection.objects.link(ob);parts.append(ob)
    mat=bpy.data.materials.new('native');mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs[0].default_value=(0.75,0.6,0.5,1)
    for ob in parts:ob.data.materials.append(mat)
    return parts

def main(bones_path,outdir,game=None,render=True):
    import numpy as np
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    bones=load_bones(bones_path);bpy.ops.wm.read_factory_settings(use_empty=True);B=bone_positions(bones)
    hi,lo=sculpt_body(B);assign(lo,'skin');assign(hi,'skin')
    armature=build_armature(bones);print('unweighted',skin_to(lo,armature));unwrap(lo,margin=0.004)
    print('body',export_mesh(lo,armature,outdir/'body.npz'))
    maps=bake_maps(lo,512,hi=hi);save_maps(maps,str(outdir/'body'))
    body=np.load(outdir/'body.npz');weights=(body['pos'],body['ix'],body['w'])
    meshes={'outfit_light':join_pieces(build_outfit(B,hi,'light'),'outfit_light'),
            'outfit_heavy':join_pieces(build_outfit(B,hi,'heavy'),'outfit_heavy'),
            'cap_leather':join_pieces(build_cap(B,hi,'leather'),'cap_leather'),
            'cap_iron':join_pieces(build_cap(B,hi,'iron'),'cap_iron')}
    budget={'outfit_light':3000,'outfit_heavy':4500,'cap_leather':700,'cap_iron':1200}
    for name,ob in meshes.items():
        decimate(ob,budget[name]);unwrap(ob,margin=0.006);print(name,export_mesh(ob,armature,outdir/f'{name}.npz',weights_from=weights))
        maps=bake_maps(ob,512 if name.startswith('outfit') else 256,occluders=(lo,));save_maps(maps,str(outdir/name))
    hi.hide_render=True
    bpy.ops.wm.save_as_mainfile(filepath=str(outdir/'goblin_soldier.blend'))
    report={'body_tris':int(len(body['tri'])),'body_vertices':int(len(body['pos'])),
            **{name:{'tris':int(len(np.load(outdir/f'{name}.npz')['tri']))} for name in meshes}}
    (outdir/'sculpt_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)

def textured_material(name,diffuse,normal=None):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bsdf=nt.nodes['Principled BSDF'];bsdf.inputs['Roughness'].default_value=0.75
    img=nt.nodes.new('ShaderNodeTexImage');img.image=bpy.data.images.load(str(diffuse));nt.links.new(img.outputs['Color'],bsdf.inputs['Base Color'])
    if normal and Path(normal).exists():
        nimg=nt.nodes.new('ShaderNodeTexImage');nimg.image=bpy.data.images.load(str(normal));nimg.image.colorspace_settings.name='Non-Color'
        nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=0.8;nt.links.new(nimg.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bsdf.inputs['Normal'])
    return m

def preview(outdir,out,game=None,clan_rgb=(98,106,82)):
    """Render the textured soldier (bare, light, heavy) beside a textured vanilla soldier."""
    sys.path.insert(0,str(Path(__file__).parent));import goblin_paint
    outdir=Path(outdir);bpy.ops.wm.open_mainfile(filepath=str(outdir/'goblin_soldier.blend'))
    objs={o.name:o for o in bpy.data.objects};tex=Path(out).parent/'preview_textures';tex.mkdir(parents=True,exist_ok=True)
    for name in ['goblin_body','outfit_light','outfit_heavy','cap_leather','cap_iron']:
        ob=objs[name];stem=outdir/('body' if name=='goblin_body' else name)
        goblin_paint.paint(stem,clan_rgb if name=='goblin_body' else None).save(tex/f'{name}_diffuse.png')
        ob.data.materials.clear();ob.data.materials.append(textured_material(name,tex/f'{name}_diffuse.png',f'{stem}_normal.png'))
    for o in bpy.data.objects:o.hide_render=True
    def twin(name,dx):
        ob=objs[name].copy();ob.data=objs[name].data;bpy.context.collection.objects.link(ob);ob.location.x+=dx;ob.hide_render=False;return ob
    shown=[twin('goblin_body',70),twin('goblin_body',0),twin('outfit_light',0),twin('cap_leather',0),twin('goblin_body',-70),twin('outfit_heavy',-70),twin('cap_iron',-70)]
    if game:
        from PIL import Image
        U=Path(game)/'in_game/gfx/models/units';sys.path.insert(0,str(Path(__file__).parent));from pdx_binary import read
        for f,tex in [('head/unit_head_north_german_male_adult_a/unit_head_german_a.mesh','head/unit_head_north_german_male_adult_a/unit_head_01_diffuse.dds'),
                      ('torso/unit_torso_armor_linen_tunic_rope/unit_torso_linen_tunic_rope.mesh','torso/unit_torso_armor_linen_tunic_rope/unit_torso_linen_tunic_rope_diffuse.dds'),
                      ('legs/unit_legs_woven_trousers_leather_shoes/unit_legs_woven_trousers_leather_shoes.mesh','legs/unit_legs_woven_trousers_leather_shoes/unit_legs_woven_trousers_leather_shoes_diffuse.dds')]:
            png=Path(out).parent/'preview_textures'/(Path(tex).stem+'.png');Image.open(U/tex).convert('RGBA').save(png);mat=textured_material(Path(f).stem,png)
            for obj in read(U/f)['children']:
                if obj['name']!='object':continue
                for shape in obj['children']:
                    if 'lod' in shape['name'].lower() and 'lod0' not in shape['name'].lower():continue
                    m=next(n for n in shape['children'] if n['name']=='mesh');p=m['props']['p'][1];tri=m['props']['tri'][1];uv=m['props']['u0'][1]
                    me=bpy.data.meshes.new(shape['name']);me.from_pydata([(p[i]+150,p[i+1],p[i+2]) for i in range(0,len(p),3)],[],[tuple(tri[i:i+3]) for i in range(0,len(tri),3)])
                    layer=me.uv_layers.new();
                    for poly in me.polygons:
                        for li in poly.loop_indices:vi=me.loops[li].vertex_index;layer.data[li].uv=(uv[2*vi],1-uv[2*vi+1])
                    me.materials.append(mat);ob=bpy.data.objects.new(shape['name'],me);bpy.context.collection.objects.link(ob);shown.append(ob)
    clay_render(shown,out,size=900,views=((-30,0),(90,0),(-30,0)),extent=130 if game else 115,center=(40 if game else 0,92,0))
    # close-up of the heads
    clay_render(shown,out+'_head',size=700,views=((-30,0),(90,0),(0,0)),extent=40,center=(-35,165,0))

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if args[0]=='preview':preview(args[1],args[2],args[3] if len(args)>3 else None)
    else:main(args[0],args[1])
