"""Build goblin infantry on EU5's native modular soldier rig.

Goblin soldiers use the installed native soldier skeleton, animations, weapons,
shields and back items, exactly like human infantry. The mod adds its own
sculpted goblin body (one mesh, 51 native bones, a clan skin texture each),
two outfits (light rags and leather, heavy scrap iron) and two caps, all
authored by tools/goblin_sculpt.py (Blender) into art/models/goblins/soldier,
plus a shorter copy of the native soldier graph. Native meshes and textures are
referenced by name, not copied; the native skeleton bind data and soldier graph
are read from the installed game at build time.
"""
import argparse,json,re,struct
from pathlib import Path
import numpy as np
from PIL import Image
from pdx_binary import node,read,write
import goblin_paint

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/models/goblins'
SOLDIER=ART/'soldier'
MODEL_REL=Path('in_game/gfx/models/units/ashborn_goblins')
TEXTURE_REGISTRATION=Path('main_menu/gfx/unit_graphics/texture_variations/zz_ashborn_goblins.txt')
NATIVE_SKELETON=Path('in_game/gfx/models/units/unit_skeleton.mesh')
NATIVE_SCHEMATIC=Path('in_game/gfx/models/schematics/unit_skeleton_schematic.schematic')
SCHEMATIC='cm_goblin_unit_skeleton_schematic'
HEAD_JOINT='Unit_Base_Rig_Head'
# Fantasy-goblin proportions: native soldiers render at 0.08; goblins at 0.05
# (62.5%, roughly 1.1 m beside a 1.8 m human) with an oversized head.
UNIT_SCALE=0.05
BODY='cm_goblin_soldier_body'
OUTFITS={'army_light_infantry':'cm_goblin_soldier_outfit_light','army_heavy_infantry':'cm_goblin_soldier_outfit_heavy'}
CAPS={'leather':'cm_goblin_soldier_cap_leather','iron':'cm_goblin_soldier_cap_iron'}
HEADGEAR={'army_light_infantry':{'none':45,'leather':40,'iron':15},
          'army_heavy_infantry':{'none':10,'leather':30,'iron':60}}
# Native lists the goblin constructors keep (torsos/legs are replaced by the goblin body and outfits).
NATIVE_ATTACH=['weapons','shields','back','offhand']
SOURCES={BODY:'body',OUTFITS['army_light_infantry']:'outfit_light',OUTFITS['army_heavy_infantry']:'outfit_heavy',CAPS['leather']:'cap_leather',CAPS['iron']:'cap_iron'}

def prop(typ,a):return (typ,np.asarray(a).ravel().tolist())
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

def bone_table(game):
    """Bind-pose bone positions for the sculpt tool: [{name,parent,position}]."""
    skeleton,names=native_skeleton(game);out=[]
    for i,b in enumerate(skeleton['children']):
        tx=np.array(b['props']['tx'][1]);M=np.eye(4);M[:3,:3]=tx[:9].reshape(3,3).T;M[:3,3]=tx[9:12]
        pa=b['props']['pa'][1][0] if 'pa' in b['props'] else -1
        out.append({'name':names[i],'parent':int(pa),'position':np.round(np.linalg.inv(M)[:3,3],3).tolist()})
    return out

def skinned_mesh(name,source,skeleton,names):
    """pdx mesh tree for a sculpted part (world-space cm, 4 bone weights per vertex, native bone order)."""
    d=np.load(SOLDIER/f'{source}.npz');p,n,uv,tri,ix,w=d['pos'],d['nor'],d['uv'],d['tri'],d['ix'],d['w']
    assert ix.max()<len(names) and np.allclose(w.sum(1),1,atol=1e-3)
    length=np.linalg.norm(n,axis=1);n=np.where(length[:,None]>1e-6,n/np.maximum(length,1e-6)[:,None],[[0,1,0]])
    tangent=np.cross(np.where(np.abs(n[:,[0]])>.9,[[0,1,0]],[[1,0,0]]),n);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-6)
    low,high=p.min(0),p.max(0);center=(low+high)/2
    mesh=node('mesh',{'p':prop('f',p),'n':prop('f',n),'ta':prop('f',np.c_[tangent,np.ones(len(p))]),
         'u0':prop('f',uv),'u1':prop('f',uv),'tri':prop('i',tri),
         'boundingsphere':prop('f',np.r_[center,np.linalg.norm(p-center,axis=1).max()])},[
         node('aabb',{'min':prop('f',low),'max':prop('f',high)}),
         node('material',{'shader':('s','standard')}),
         node('skin',{'bones':('i',[4]),'ix':prop('i',ix),'w':prop('f',w)})])
    shape=node(name+'Shape',children=[mesh,skeleton])
    tree=node('root',{'pdxasset':('i',[1,0])},[node('object',children=[shape]),node('locator')])
    return tree,{'triangles':int(len(tri)),'vertices':int(len(p)),'bones_used':int(len(np.unique(ix[ix>=0])))}

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

def pdxmesh_entry(mesh_name,file_stem,diffuse,normal,mask):
    return f'''pdxmesh = {{
 name = "{mesh_name}"
 file = "{file_stem}.mesh"
 meshsettings = {{ name = "{file_stem}Shape" index = 0
  texture_diffuse = "{diffuse}"
  texture_normal = "{normal}"
  texture = {{ index = 3 srgb = no file = "{mask}" }}
  shader = "unit_material_repaint" shader_file = "gfx/FX/units.shader"
 }}
}}
'''

def build(out,game):
    out=Path(out);directory=out/MODEL_REL
    if not game:raise SystemExit('Goblin infantry needs --game: it is built on the installed native soldier rig')
    for old in list(directory.glob('*'))+list((out/'in_game/gfx/models/schematics').glob('cm_goblin_*_schematic.schematic')):
        old.unlink()
    old_machine=out/'main_menu/gfx/animation_state_machines/cm_goblin_infantry.animsm'
    if old_machine.exists():old_machine.unlink()
    directory.mkdir(parents=True,exist_ok=True)
    config=json.loads((ART/'clans.json').read_text());skeleton,names=native_skeleton(game)
    Image.new('RGBA',(4,4),(128,128,0,128)).save(directory/'cm_goblin_soldier_flat_normal.dds')
    Image.new('RGBA',(4,4),(0,0,0,255)).save(directory/'cm_goblin_soldier_mask.dds')
    report={'stage':'sculpted-goblin-soldier-on-native-rig','engine_tested':False,'unit_scale':UNIT_SCALE,'native_scale':0.08,'meshes':{},'clans':[]}
    asset='';lists=[];registered=[]
    for name,source in SOURCES.items():
        tree,info=skinned_mesh(name,source,skeleton,names);write(directory/(name+'.mesh'),tree);report['meshes'][name]=info
        size=goblin_paint.load_maps(SOLDIER/source)[2].shape[0]
        normal='cm_goblin_soldier_flat_normal.dds'
        if (SOLDIER/f'{source}_normal.png').exists():
            normal=name+'_normal.dds';(directory/normal).write_bytes(rgba_dds(goblin_paint.normal_rgba(SOLDIER/source,size)))
        if name==BODY:
            for clan in config['clans']:
                stem=f'cm_goblin_{clan["id"]}_soldier_body'
                (directory/(stem+'_diffuse.dds')).write_bytes(rgba_dds(goblin_paint.paint(SOLDIER/source,hex_rgb(clan['skin_srgb']))))
                asset+=pdxmesh_entry(stem+'_mesh',name,stem+'_diffuse.dds',normal,'cm_goblin_soldier_mask.dds');registered.append(stem+'_mesh')
                lists.append(f'cm_goblin_{clan["id"]}_body = {{\n 1 = {{ add_entity = {{ node = shared_pose_entity mesh_name = "{stem}_mesh" }} }}\n}}')
                report['clans'].append({'clan':clan['id'],'culture':clan['culture'],'gfx_tag':clan['culture']+'_gfx','body_mesh':stem+'_mesh'})
        else:
            (directory/(name+'_diffuse.dds')).write_bytes(rgba_dds(goblin_paint.paint(SOLDIER/source)))
            asset+=pdxmesh_entry(name+'_mesh',name,name+'_diffuse.dds',normal,'cm_goblin_soldier_mask.dds');registered.append(name+'_mesh')
    for category,outfit in OUTFITS.items():
        lists.append(f'cm_goblin_{category}_outfit = {{\n 1 = {{ add_entity = {{ node = shared_pose_entity mesh_name = "{outfit}_mesh" }} }}\n}}')
    for category,weights in HEADGEAR.items():
        options=''.join(f' {w} = {{ }}\n' if kind=='none' else
                        f' {w} = {{ add_entity = {{ node = shared_pose_entity mesh_name = "{CAPS[kind]}_mesh" }} }}\n'
                        for kind,w in weights.items())
        lists.append(f'cm_goblin_{category}_headgear = {{\n{options}}}')
    write_text(directory/'cm_goblin_soldier.asset',asset)
    write_text(out/'in_game/gfx/models/schematics'/(SCHEMATIC+'.schematic'),goblin_schematic(game))
    constructors=[]
    for clan in config['clans']:
        tag=clan['culture']+'_gfx'
        for category in OUTFITS:
            # Own list names, attached directly by the goblin constructors, so no
            # native tag/age list can take precedence over them.
            names_=[f'cm_goblin_{clan["id"]}_body use_uniformity = no',f'cm_goblin_{category}_outfit',f'cm_goblin_{category}_headgear']+NATIVE_ATTACH
            attach=''.join(f' attach = {{ 100 = {n} }}\n' for n in names_)
            constructors.append(f'''{tag}:{category} = {{
 schematic_name = {SCHEMATIC}
{attach} animation_state_machine_name = unit_skeleton_state_machine_one_handed_axe
}}''')
    write_text(out/'main_menu/gfx/unit_graphics/units/zz_ashborn_goblins.txt','\n'.join(constructors)+'\n')
    write_text(out/'main_menu/gfx/unit_graphics/attachments/zz_ashborn_goblins.txt','\n'.join(lists)+'\n')
    # Goblin meshes carry authored colours; keep them out of the human skin/uniform repaint.
    write_text(out/TEXTURE_REGISTRATION,'assets_without_texture_variation = {\n'+''.join(f' {m}\n' for m in registered)+'}\n')
    report['runtime_infantry']='native soldier rig, weapons, shields and animations; sculpted goblin body per clan, goblin outfits and caps; 62.5% native graph copy'
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'build/goblin_models');ap.add_argument('--game',type=Path,required=True)
    ap.add_argument('--bones',type=Path,help='write the native bone table for goblin_sculpt.py and exit');args=ap.parse_args()
    if args.bones:args.bones.write_text(json.dumps(bone_table(args.game)));raise SystemExit
    result=build(args.out,args.game);write_text(args.out/'model_export.json',json.dumps(result,indent=2));print(json.dumps(result,indent=2))
