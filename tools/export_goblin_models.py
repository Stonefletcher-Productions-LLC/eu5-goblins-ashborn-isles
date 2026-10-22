"""Build goblin infantry on EU5's native modular soldier rig.

Goblin soldiers use the installed native soldier skeleton, animations, clothing,
armour, headgear, weapons and shields, exactly like human infantry. The mod adds
only a goblin head per clan (sculpted from the CC0 source GLB and bound to the
native head joint), a shorter copy of the native soldier graph, and per-culture
attachment lists. Native meshes and textures are referenced by name, not copied;
the native skeleton bind data and soldier graph are read from the installed game.

glTF metres/Y-up/RH become engine centimetres/Y-up/LH.
"""
import argparse,json,math,re,struct
from pathlib import Path
import numpy as np
from PIL import Image
from pdx_binary import node,read,write

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/models/goblins'
MODEL_REL=Path('in_game/gfx/models/units/ashborn_goblins')
TEXTURE_REGISTRATION=Path('main_menu/gfx/unit_graphics/texture_variations/zz_ashborn_goblins.txt')
FLIP=np.diag([100.,100.,-100.,1.]);UNFLIP=np.linalg.inv(FLIP)

def prop(typ,a):return (typ,np.asarray(a).ravel().tolist())
def quat_matrix(q):
    x,y,z,w=np.asarray(q)/np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def trs(t,q,s):
    m=np.eye(4);m[:3,:3]=quat_matrix(q)@np.diag(s);m[:3,3]=t;return m
def slerp(a,b,f):
    a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);dot=np.dot(a,b)
    if dot<0:b=-b;dot=-dot
    if dot>.9995:q=a+(b-a)*f
    else:
        theta=np.arccos(np.clip(dot,-1,1));q=(np.sin((1-f)*theta)*a+np.sin(f*theta)*b)/np.sin(theta)
    return q/np.linalg.norm(q)

class GLB:
    def __init__(self,path):
        raw=Path(path).read_bytes();magic,version,size=struct.unpack_from('<III',raw)
        assert magic==0x46546c67 and version==2 and size==len(raw)
        length,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
        self.g=json.loads(raw[20:20+length]);offset=20+length
        length,kind=struct.unpack_from('<II',raw,offset);assert kind==0x004e4942
        self.data=raw[offset+8:offset+8+length];self.cache={}
        self.parents={c:i for i,n in enumerate(self.g['nodes']) for c in n.get('children',[])}
        self.mesh_node=next(i for i,n in enumerate(self.g['nodes']) if 'mesh' in n)
        self.skin=self.g['skins'][self.g['nodes'][self.mesh_node]['skin']]
        needed=set(self.skin['joints'])
        for joint in list(needed):
            while joint in self.parents:joint=self.parents[joint];needed.add(joint)
        self.bones=[]
        def visit(j):
            if j in needed:self.bones.append(j)
            for c in self.g['nodes'][j].get('children',[]):visit(c)
        for j in self.g['scenes'][self.g.get('scene',0)]['nodes']:visit(j)
        self.indices={j:i for i,j in enumerate(self.bones)}
        self.names=[self.g['nodes'][j]['name'] for j in self.bones]
        assert len(set(self.names))==len(self.names)
        self.rest=self.pose()
        self.mesh_world=self.rest[self.mesh_node]
        self.ibm=self.access(self.skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    def access(self,index):
        if index in self.cache:return self.cache[index]
        a=self.g['accessors'][index];assert 'sparse' not in a
        v=self.g['bufferViews'][a['bufferView']]
        dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
        width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',width*dtype.itemsize)
        x=np.ndarray((a['count'],width),dtype=dtype,buffer=self.data,offset=offset,strides=(stride,dtype.itemsize)).copy()
        if a.get('normalized'):x=x.astype(float)/np.iinfo(dtype).max
        self.cache[index]=x;return x
    def locals(self,animation=None,time=0):
        values=[{'translation':np.array(n.get('translation',[0,0,0]),float),
                 'rotation':np.array(n.get('rotation',[0,0,0,1]),float),
                 'scale':np.array(n.get('scale',[1,1,1]),float)} for n in self.g['nodes']]
        if animation is not None:
            for c in animation['channels']:
                sampler=animation['samplers'][c['sampler']];times=self.access(sampler['input']).ravel();vs=self.access(sampler['output'])
                assert sampler.get('interpolation','LINEAR') in ('LINEAR','STEP')
                hi=int(np.searchsorted(times,time,side='right'));lo=max(hi-1,0);hi=min(hi,len(times)-1)
                f=0 if lo==hi or sampler.get('interpolation')=='STEP' else (time-times[lo])/(times[hi]-times[lo])
                key=c['target']['path'];a,b=vs[lo].astype(float),vs[hi].astype(float)
                values[c['target']['node']][key]=slerp(a,b,f) if key=='rotation' else a+(b-a)*f
        return values
    def pose(self,animation=None,time=0):
        local=self.locals(animation,time);result={}
        def world(i):
            if i not in result:
                v=local[i];m=trs(v['translation'],v['rotation'],v['scale'])
                result[i]=world(self.parents[i])@m if i in self.parents else m
            return result[i]
        for i in range(len(local)):world(i)
        return result
    def primitives(self):return self.g['meshes'][self.g['nodes'][self.mesh_node]['mesh']]['primitives']


NATIVE_SKELETON=Path('in_game/gfx/models/units/unit_skeleton.mesh')
NATIVE_SCHEMATIC=Path('in_game/gfx/models/schematics/unit_skeleton_schematic.schematic')
SCHEMATIC='cm_goblin_unit_skeleton_schematic'
HEAD_MESH='cm_goblin_unit_head'
HEAD_JOINT='Unit_Base_Rig_Head'
# Fantasy-goblin proportions: native soldiers render at 0.08; goblins at 0.05
# (62.5%, roughly 1.1 m beside a 1.8 m human) with an oversized head.
UNIT_SCALE=0.05
# Fit of the source head into native head-joint space (cm): uniform scale,
# source jaw base -> native neck top, pushed slightly forward for a stoop.
HEAD_SCALE=1.05;SOURCE_NECK=63.6;NATIVE_NECK=153.0;HEAD_Z=1.0
NECK_SIDES=16;NECK_BOTTOM=147.0;NECK_TOP=158.0;NECK_RADIUS=(6.2,9.2,3.6);NECK_THROAT=3.0;NECK_LEAN=-2.0
ATLAS=256;CELL=ATLAS//4
EYE=(74,52,20);MOUTH=(46,22,18);TEETH=(214,198,150)
# Crude goblin caps shaped on the goblin skull, because native helmets are
# sized for human heads. Source-space heights: caps start above the eyes at the
# front and lower at the back; ears stay bare.
CAP_FRONT=83.0;CAP_BACK=69.0;CAP_EAR=14.0
CAPS={'leather':{'thickness':.55,'color':(96,66,40),'rim':(62,42,26)},
      'iron':{'thickness':.8,'color':(112,114,118),'rim':(70,66,60)}}
HEADGEAR={'army_light_infantry':{'none':45,'leather':40,'iron':15},
          'army_heavy_infantry':{'none':10,'leather':30,'iron':60}}
# Native unit attachment lists that soldiers combine. Gear below the neck comes
# from the native lists, so clothing, armour and weapons follow age and unit
# type exactly as for human armies. Native hair, beards and helmets are left
# out: they are sized for human heads.
NATIVE_ATTACH=['torsos','legs','weapons','shields','back','offhand']

def write_text(path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8-sig')
def hex_rgb(value):return np.array([int(value[i:i+2],16) for i in (1,3,5)],float)

def native_skeleton(game):
    """Native soldier skeleton nodes (bone names, parents, inverse binds)."""
    tree=read(Path(game)/NATIVE_SKELETON)
    shape=tree['children'][0]['children'][0]
    skeleton=next(n for n in shape['children'] if n['name']=='skeleton')
    names=[b['name'] for b in skeleton['children']]
    assert HEAD_JOINT in names and 'Unit_Base_Rig_Neck' in names
    return skeleton,names

def head_geometry(g):
    """Head, ears, nose, eyes, mouth and teeth from the shared clan sculpt, in native cm."""
    joints=[g.g['nodes'][j]['name'] for j in g.skin['joints']]
    head,neck=joints.index('Head'),joints.index('Neck')
    convert=FLIP@g.mesh_world;normal_matrix=np.linalg.inv(convert[:3,:3]).T
    positions,normals,tris,kinds=[],[],[],[]
    for p in g.primitives():
        a=p['attributes'];material=g.g['materials'][p['material']]['name']
        if material=='Pants':continue
        kind='skin' if material.startswith('goblin_skin') else material.lower()
        pos=g.access(a['POSITION']).astype(float);pos=(convert@np.c_[pos,np.ones(len(pos))].T).T[:,:3]
        nor=(normal_matrix@g.access(a['NORMAL']).T).T;nor/=np.linalg.norm(nor,axis=1)[:,None]
        J=g.access(a['JOINTS_0']).astype(int);W=g.access(a['WEIGHTS_0']).astype(float);W/=W.sum(1)[:,None]
        keep=(((J==head)|(J==neck))*W).sum(1)>.5
        t=g.access(p['indices']).reshape(-1,3)[:,[0,2,1]];t=t[keep[t].all(1)]
        used=np.unique(t);remap=-np.ones(len(pos),int);remap[used]=np.arange(len(used))+sum(len(x) for x in positions)
        positions.append(pos[used]);normals.append(nor[used]);tris.append(remap[t]);kinds+= [kind]*len(t)
    pos=np.concatenate(positions);nor=np.concatenate(normals);tri=np.concatenate(tris)
    out=pos*HEAD_SCALE;out[:,1]=NATIVE_NECK+(pos[:,1]-SOURCE_NECK)*HEAD_SCALE;out[:,2]+=HEAD_Z
    # The source neck is a short ring inside the jaw. Add a native-sized neck
    # column so the native torso's neck skin stays hidden inside green skin.
    ring=np.linspace(0,2*np.pi,NECK_SIDES,endpoint=False)
    rx,rz,cz=NECK_RADIUS;rows=[NECK_BOTTOM,NECK_TOP]
    # The native torso's throat skin slopes forward up to the chin, so the top
    # ring rises and leans forward at the front.
    cyl=np.array([[rx*np.sin(a),y+(NECK_THROAT*max(0,np.cos(a)) if y==NECK_TOP else 0),
                   cz-rz*np.cos(a)+(NECK_LEAN*(1+np.cos(a))/2 if y==NECK_TOP else 0)] for y in rows for a in ring])
    cn=np.array([[np.sin(a),0,-np.cos(a)] for y in rows for a in ring])
    base=len(out);cyl_tri=[]
    for i in range(NECK_SIDES):
        j=(i+1)%NECK_SIDES;a0,a1,b0,b1=base+i,base+j,base+NECK_SIDES+i,base+NECK_SIDES+j
        cyl_tri+=[[a0,b0,a1],[a1,b0,b1]]
    cyl_tri=np.array(cyl_tri)
    # Match the winding of the converted source mesh (outward normals).
    f=np.cross(cyl[cyl_tri[0,1]-base]-cyl[cyl_tri[0,0]-base],cyl[cyl_tri[0,2]-base]-cyl[cyl_tri[0,0]-base])
    g_=np.cross(out[tri[:,1]]-out[tri[:,0]],out[tri[:,2]]-out[tri[:,0]])
    source_sign=np.sign(np.einsum('ij,ij->i',g_,nor[tri].mean(1)).sum())
    if source_sign*np.dot(f,cn[cyl_tri[0,0]-base])<0:cyl_tri=cyl_tri[:,[0,2,1]]
    source_y=np.r_[pos[:,1],np.full(len(cyl),-1e9)]  # neck column never joins a cap
    out=np.r_[out,cyl];nor=np.r_[nor,cn];tri=np.r_[tri,cyl_tri];kinds=list(kinds)+['skin']*len(cyl_tri)
    return out,nor,tri,np.array(kinds),source_y

def ambient_occlusion(pos,nor,tri,rays=48,seed=7):
    """Per-vertex hemisphere occlusion against the head itself (Moller-Trumbore)."""
    rng=np.random.default_rng(seed);v0,v1,v2=pos[tri[:,0]],pos[tri[:,1]],pos[tri[:,2]];e1,e2=v1-v0,v2-v0
    dirs=rng.normal(size=(rays,3));dirs/=np.linalg.norm(dirs,axis=1)[:,None]
    result=np.zeros(len(pos))
    for i,(o,n) in enumerate(zip(pos,nor)):
        d=dirs*np.sign(dirs@n)[:,None];o=o+n*.05
        pv=np.cross(d[:,None,:],e2[None]);det=np.einsum('tk,rtk->rt',e1,pv)
        ok=np.abs(det)>1e-9;inv=np.where(ok,1/np.where(ok,det,1),0);tv=o-v0
        u=np.einsum('tk,rtk->rt',tv,pv)*inv;qv=np.cross(tv,e1);w=np.einsum('rk,tk->rt',d,qv)*inv
        t=np.einsum('tk,tk->t',e2,qv)[None]*inv
        hit=ok&(u>=0)&(w>=0)&(u+w<=1)&(t>1e-3)&(t<12)
        result[i]=1-hit.any(1).mean()
    return result

def unwrap(pos,nor,tri):
    """Box-projected charts with padding; seams split vertices per chart."""
    face=np.cross(pos[tri[:,1]]-pos[tri[:,0]],pos[tri[:,2]]-pos[tri[:,0]])
    axis=np.abs(face).argmax(1);sign=np.sign(face[np.arange(len(face)),axis]).astype(int)
    chart=axis*2+(sign>0)
    plane={0:(2,1),1:(0,1),2:(0,1)}
    low,high=pos.min(0),pos.max(0);span=(high-low).max()
    corners={}
    for c in range(6):
        cells=[(0,0),(1,0),(2,0),(3,0),(0,1),(1,1)][c];corners[c]=np.array(cells,float)*CELL
    vertices={};new_index=[];uv=[];source=[]
    for t,c in zip(tri,chart):
        row=[]
        for v in t:
            key=(int(v),int(c))
            if key not in vertices:
                a,b=plane[c//2];vertices[key]=len(source);source.append(v)
                pu=(pos[v,a]-low[a])/span;pv=1-(pos[v,b]-low[b])/span
                if c%2==0:pu=1-pu  # mirror back-facing charts so texels are not flipped
                uv.append(corners[c]+np.array([pu,pv])*(CELL-6)+3)
            row.append(vertices[key])
        new_index.append(row)
    return np.array(source),np.array(new_index),np.array(uv)/ATLAS,chart

def rasterize(uv,tri,colors,size=ATLAS,pad=4):
    image=np.zeros((size,size,3));filled=np.zeros((size,size),bool);px=uv*size
    for t in tri:
        a,b,c=px[t];lo=np.floor(np.minimum(np.minimum(a,b),c)).astype(int);hi=np.ceil(np.maximum(np.maximum(a,b),c)).astype(int)
        xs,ys=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));p=np.stack([xs.ravel()+.5,ys.ravel()+.5],1)
        m=np.array([b-a,c-a]).T
        if abs(np.linalg.det(m))<1e-9:continue
        l=np.linalg.solve(m,(p-a).T).T;w=np.c_[1-l.sum(1),l];inside=(w>=-.02).all(1)
        p=p[inside].astype(int);w=np.clip(w[inside],0,1);w/=w.sum(1)[:,None]
        ok=(p>=0).all(1)&(p<size).all(1);p=p[ok];w=w[ok]
        image[p[:,1],p[:,0]]=w@colors[t];filled[p[:,1],p[:,0]]=True
    for _ in range(pad):  # dilate so mips do not pull in background
        grown=image.copy();count=np.zeros((size,size))
        acc=np.zeros_like(image)
        for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
            sh=np.roll(np.roll(image*filled[...,None],dy,0),dx,1);sf=np.roll(np.roll(filled,dy,0),dx,1)
            acc+=sh;count+=sf
        edge=(~filled)&(count>0);grown[edge]=acc[edge]/count[edge][:,None];image=grown;filled=filled|edge
    image[~filled]=colors.mean(0)
    return image

def skin_colors(pos,nor,kinds_per_vertex,occlusion,clan):
    base=hex_rgb(clan['skin_srgb'])/255
    # Clan palettes are authored dark for portraits; units read from far away,
    # so lift them toward native soldier skin brightness while keeping hue.
    base=np.clip(base*1.32,0,1)
    light=.72+.28*np.clip(occlusion,0,1)**1.4+.06*nor[:,1]
    rng=np.random.default_rng(int(clan['skin_srgb'][1:],16));mottle=1+.05*rng.standard_normal(len(pos))
    color=base[None]*(light*mottle)[:,None]
    # Warmer, thinner skin at ear tips and nose.
    warm=np.clip((np.abs(pos[:,0])-CAP_EAR*HEAD_SCALE)/8,0,1)+np.clip((-pos[:,2]-11)/3,0,1)
    color=color*(1-.25*warm[:,None])+np.array([.62,.42,.33])*base.mean()*1.6*.25*warm[:,None]
    return np.clip(color,0,1)

def head_bound_mesh(name,pos,nor,tri,skeleton,names):
    """Native-skeleton mesh rigidly bound to the head joint, with unwrapped UVs."""
    source,index,uv,chart=unwrap(pos,nor,tri)
    p,n=pos[source],nor[source]
    tangent=np.cross(np.where(np.abs(n[:,[0]])>.9,[[0,1,0]],[[1,0,0]]),n);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    ids=np.full((len(p),4),-1);ids[:,0]=names.index(HEAD_JOINT);weights=np.zeros((len(p),4));weights[:,0]=1
    low,high=p.min(0),p.max(0);center=(low+high)/2
    mesh=node('mesh',{'p':prop('f',p),'n':prop('f',n),'ta':prop('f',np.c_[tangent,np.ones(len(p))]),
         'u0':prop('f',uv),'u1':prop('f',uv),'tri':prop('i',index),
         'boundingsphere':prop('f',np.r_[center,np.linalg.norm(p-center,axis=1).max()])},[
         node('aabb',{'min':prop('f',low),'max':prop('f',high)}),
         node('material',{'shader':('s','standard')}),
         node('skin',{'bones':('i',[4]),'ix':prop('i',ids),'w':prop('f',weights)})])
    shape=node(name+'Shape',children=[mesh,skeleton])
    tree=node('root',{'pdxasset':('i',[1,0])},[node('object',children=[shape]),node('locator')])
    return tree,{'pos':p,'nor':n,'tri':index,'uv':uv,'source':source}

def head_mesh(g,skeleton,names):
    pos,nor,tri,kinds,source_y=head_geometry(g)
    occlusion=ambient_occlusion(pos,nor,tri)
    tree,data=head_bound_mesh(HEAD_MESH,pos,nor,tri,skeleton,names)
    data.update({'occlusion':occlusion,'kinds':kinds,'base_pos':pos,'base_tri':tri,'base_nor':nor,'source_y':source_y})
    return tree,data

def cap_mesh(head,kind,skeleton,names):
    """A thin shell over the skull above the eyes (ears and face excluded)."""
    pos,nor,tri,kinds,sy=head['base_pos'],head['base_nor'],head['base_tri'],head['kinds'],head['source_y']
    back=np.clip((pos[:,2]-pos[:,2].min())/np.ptp(pos[:,2]),0,1)  # 0 at the face, 1 at the back
    threshold=CAP_FRONT+(CAP_BACK-CAP_FRONT)*np.clip((back-.3)/.5,0,1)
    inside=(sy>=threshold)&(np.abs(pos[:,0])<CAP_EAR*HEAD_SCALE)
    keep=(kinds=='skin')&inside[tri].all(1)
    t=tri[keep];used=np.unique(t);remap=-np.ones(len(pos),int);remap[used]=np.arange(len(used))
    spec=CAPS[kind];p=pos[used]+nor[used]*spec['thickness']*HEAD_SCALE/.68
    tree,data=head_bound_mesh(f'cm_goblin_unit_cap_{kind}',p,nor[used],remap[t],skeleton,names)
    occ=ambient_occlusion(p,nor[used],remap[t],rays=24)
    rim=np.clip(1-(sy[used]-threshold[used])/2.5,0,1)  # darker band along the lower edge
    base=np.array(spec['color'])/255;edge=np.array(spec['rim'])/255
    colors=(base*(1-rim[:,None])+edge*rim[:,None])*(.7+.3*occ)[:,None]
    rng=np.random.default_rng(len(kind));colors*=1+.06*rng.standard_normal(len(colors))[:,None]
    image=rasterize(data['uv'],data['tri'],np.clip(colors[data['source']],0,1))
    return tree,Image.fromarray((np.clip(image,0,1)*255).round().astype(np.uint8),'RGB').convert('RGBA'),len(t)

def head_textures(data,clan):
    occ,kinds=data['occlusion'],data['kinds']
    nor=data['nor'];source=data['source']
    skin=skin_colors(data['pos'],nor,None,occ[source],clan)
    colors=skin.copy()
    # Paint features per triangle: eyes amber with dark centre, mouth, teeth.
    feature=np.zeros(len(data['pos']),dtype=object);feature[:]='skin'
    for t_new,k in zip(data['tri'],kinds):
        if k!='skin':feature[t_new]=k
    for i,k in enumerate(feature):
        p=data['pos'][i]
        if k=='teeth':colors[i]=np.array(TEETH)/255*(.75+.25*occ[source[i]])
        elif k=='face':
            if data['source_y'][source[i]]>74:  # eyes sit above the mouth
                colors[i]=np.array(EYE)/255
            else:colors[i]=np.array(MOUTH)/255
    image=rasterize(data['uv'],data['tri'],colors)
    return Image.fromarray((np.clip(image,0,1)*255).round().astype(np.uint8),'RGB').convert('RGBA')

def rgba_dds(image):
    import io
    width,height=image.size;levels=[]
    while True:
        buffer=io.BytesIO();image.save(buffer,format='DDS',pixel_format='DXT5');raw=buffer.getvalue()
        assert raw[84:88]==b'DXT5';levels.append(raw[128:])
        if image.size==(1,1):break
        image=image.resize((max(1,image.width//2),max(1,image.height//2)),Image.Resampling.LANCZOS)
    header=[124,0xA1007,height,width,len(levels[0]),0,len(levels)]+[0]*11
    header+=[32,4,int.from_bytes(b'DXT5','little'),0,0,0,0,0]
    header+=[0x401008,0,0,0,0]
    return b'DDS '+struct.pack('<31I',*header)+b''.join(levels)

def goblin_schematic(game):
    """Native soldier graph with only its name and world scale changed."""
    text=(Path(game)/NATIVE_SCHEMATIC).read_text(encoding='utf-8-sig')
    assert text.count('name="unit_skeleton_schematic"')==1 and text.count('value=unit_skeleton_schematic')==1
    assert len(re.findall(r'value=0\.080000',text))==1,'Native unit scale moved; update the goblin copy'
    text=text.replace('name="unit_skeleton_schematic"',f'name="{SCHEMATIC}"').replace('value=unit_skeleton_schematic',f'value={SCHEMATIC}')
    return text.replace('value=0.080000',f'value={UNIT_SCALE:.6f}')

def build(out,game):
    out=Path(out);directory=out/MODEL_REL
    if not game:raise SystemExit('Goblin infantry needs --game: it is built on the installed native soldier rig')
    for old in list(directory.glob('*'))+list((out/'in_game/gfx/models/schematics').glob('cm_goblin_*_schematic.schematic')):
        old.unlink()
    old_machine=out/'main_menu/gfx/animation_state_machines/cm_goblin_infantry.animsm'
    if old_machine.exists():old_machine.unlink()
    directory.mkdir(parents=True,exist_ok=True)
    config=json.loads((ART/'clans.json').read_text())
    g=GLB(ART/'variants/cindermaw.glb');skeleton,names=native_skeleton(game)
    tree,data=head_mesh(g,skeleton,names);write(directory/(HEAD_MESH+'.mesh'),tree)
    Image.new('RGBA',(4,4),(128,128,0,128)).save(directory/(HEAD_MESH+'_normal.dds'))
    Image.new('RGBA',(4,4),(0,76,0,140)).save(directory/(HEAD_MESH+'_properties.dds'))
    Image.new('RGBA',(4,4),(0,0,0,255)).save(directory/(HEAD_MESH+'_mask.dds'))
    asset='';heads=[];report={'stage':'native-rig-goblin-heads-and-caps','engine_tested':False,'unit_scale':UNIT_SCALE,
        'native_scale':0.08,'head_triangles':len(data['tri']),'head_vertices':len(data['pos']),'clans':[]}
    for clan in config['clans']:
        stem=f'cm_goblin_{clan["id"]}_unit_head'
        (directory/(stem+'_diffuse.dds')).write_bytes(rgba_dds(head_textures(data,clan)))
        asset+=f'''pdxmesh = {{
 name = "{stem}_mesh"
 file = "{HEAD_MESH}.mesh"
 meshsettings = {{ name = "{HEAD_MESH}Shape" index = 0
  texture_diffuse = "{stem}_diffuse.dds"
  texture_normal = "{HEAD_MESH}_normal.dds"
  texture_specular = "{HEAD_MESH}_properties.dds"
  texture = {{ index = 3 srgb = no file = "{HEAD_MESH}_mask.dds" }}
  shader = "unit_material_repaint" shader_file = "gfx/FX/units.shader"
 }}
}}
'''
        tag=clan['culture']+'_gfx'
        # Own list names, attached directly by the goblin constructors, so no
        # native tag/age list can take precedence over them.
        heads.append(f'''cm_goblin_{clan["id"]}_heads = {{
 1 = {{ add_entity = {{ node = shared_pose_entity mesh_name = "{stem}_mesh" }} }}
}}''')
        report['clans'].append({'clan':clan['id'],'culture':clan['culture'],'gfx_tag':tag,'head_mesh':stem+'_mesh'})
    for kind in CAPS:
        name=f'cm_goblin_unit_cap_{kind}';cap,image,count=cap_mesh(data,kind,skeleton,names)
        write(directory/(name+'.mesh'),cap);(directory/(name+'_diffuse.dds')).write_bytes(rgba_dds(image))
        asset+=f'''pdxmesh = {{
 name = "{name}_mesh"
 file = "{name}.mesh"
 meshsettings = {{ name = "{name}Shape" index = 0
  texture_diffuse = "{name}_diffuse.dds"
  texture_normal = "{HEAD_MESH}_normal.dds"
  texture_specular = "{HEAD_MESH}_properties.dds"
  texture = {{ index = 3 srgb = no file = "{HEAD_MESH}_mask.dds" }}
  shader = "unit_material_repaint" shader_file = "gfx/FX/units.shader"
 }}
}}
'''
        report[f'cap_{kind}_triangles']=count
    for category,weights in HEADGEAR.items():
        options=''.join(f' {w} = {{ }}\n' if kind=='none' else
                        f' {w} = {{ add_entity = {{ node = shared_pose_entity mesh_name = "cm_goblin_unit_cap_{kind}_mesh" }} }}\n'
                        for kind,w in weights.items())
        heads.append(f'cm_goblin_{category}_headgear = {{\n{options}}}')
    write_text(directory/(HEAD_MESH+'.asset'),asset)
    write_text(out/'in_game/gfx/models/schematics'/(SCHEMATIC+'.schematic'),goblin_schematic(game))
    constructors=[]
    for clan in config['clans']:
        tag=clan['culture']+'_gfx'
        for category in ['army_light_infantry','army_heavy_infantry']:
            lists=[f'cm_goblin_{clan["id"]}_heads use_uniformity = no']+NATIVE_ATTACH[:2]+[f'cm_goblin_{category}_headgear']+NATIVE_ATTACH[2:]
            attach=''.join(f' attach = {{ 100 = {name} }}\n' for name in lists)
            constructors.append(f'''{tag}:{category} = {{
 schematic_name = {SCHEMATIC}
{attach} animation_state_machine_name = unit_skeleton_state_machine_one_handed_axe
}}''')
    write_text(out/'main_menu/gfx/unit_graphics/units/zz_ashborn_goblins.txt','\n'.join(constructors)+'\n')
    write_text(out/'main_menu/gfx/unit_graphics/attachments/zz_ashborn_goblins.txt','\n'.join(heads)+'\n')
    # Heads carry authored clan skin; keep them out of the human skin repaint.
    write_text(out/TEXTURE_REGISTRATION,'assets_without_texture_variation = {\n'+
               ''.join(f' cm_goblin_{clan["id"]}_unit_head_mesh\n' for clan in config['clans'])+
               ''.join(f' cm_goblin_unit_cap_{kind}_mesh\n' for kind in CAPS)+'}\n')
    report['runtime_infantry']='native soldier rig, body gear and animations; goblin head per clan and goblin caps; 62.5% native graph copy'
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'build/goblin_models');ap.add_argument('--game',type=Path,required=True);args=ap.parse_args()
    result=build(args.out,args.game);write_text(args.out/'model_export.json',json.dumps(result,indent=2));print(json.dumps(result,indent=2))
