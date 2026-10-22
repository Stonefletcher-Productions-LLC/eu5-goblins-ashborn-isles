"""Static checks for the sculpted goblin soldiers built on the native rig."""
import json,re,struct
from pathlib import Path
import numpy as np
from PIL import Image
from pdx_binary import read,write
from export_goblin_models import (ART,SOLDIER,MODEL_REL,ROOT,TEXTURE_REGISTRATION,SCHEMATIC,NATIVE_SKELETON,NATIVE_SCHEMATIC,
                                  NATIVE_ATTACH,UNIT_SCALE,BODY,OUTFITS,CAPS,HEADGEAR,SOURCES,hex_rgb)

def verify_texture_registration(out,clans,game=None):
    """Goblin meshes keep authored colours: register them in the native fixed-texture list."""
    from verify_055 import parse
    path=out/TEXTURE_REGISTRATION
    assert path.is_file(),'Goblin meshes are missing texture-variation registration'
    rows=parse(path.read_text(encoding='utf-8-sig'))
    assert len(rows)==1 and rows[0][:2]==('assets_without_texture_variation','='),'Use the native fixed-texture registry'
    names=[name for name,op,value in rows[0][2] if op is None and value is None]
    expected={f'cm_goblin_{c["id"]}_soldier_body_mesh' for c in clans}|{f'{m}_mesh' for m in SOURCES if m!=BODY}
    assert set(names)==expected and len(names)==len(expected),'Every goblin mesh must be registered exactly once'
    assert not (out/'main_menu/gfx/unit_graphics/texture_variations/assets_without_texture_variations.txt').exists(),'Do not replace the native registry'
    if game:
        native=parse((Path(game)/'main_menu/gfx/unit_graphics/texture_variations/assets_without_texture_variations.txt').read_text(encoding='utf-8-sig'))
        assert native[0][:2]==rows[0][:2]
    return {'registered_fixed_palette_meshes':len(names),'native_contract_checked':bool(game)}

def dds_levels(path):
    raw=Path(path).read_bytes();assert raw[:4]==b'DDS ' and raw[84:88]==b'DXT5',path
    height,width=struct.unpack_from('<II',raw,12);mips=struct.unpack_from('<I',raw,28)[0]
    return width,height,mips

def read_mesh(path):
    tree=read(path);shape=tree['children'][0]['children'][0]
    mesh=next(n for n in shape['children'] if n['name']=='mesh')
    bones=next(n for n in shape['children'] if n['name']=='skeleton')['children']
    p=np.array(mesh['props']['p'][1]).reshape(-1,3);n=np.array(mesh['props']['n'][1]).reshape(-1,3)
    uv=np.array(mesh['props']['u0'][1]).reshape(-1,2);tri=np.array(mesh['props']['tri'][1]).reshape(-1,3)
    skin=next(c for c in mesh['children'] if c['name']=='skin')['props']
    ix=np.array(skin['ix'][1]).reshape(-1,4);w=np.array(skin['w'][1]).reshape(-1,4)
    return shape['name'],p,n,uv,tri,ix,w,bones

def verify(out,game=None):
    out=Path(out);folder=out/MODEL_REL
    clans=json.loads((ART/'clans.json').read_text())['clans']
    # Retired standalone body and head-only build: their files must be gone.
    assert not list(folder.glob('*.anim')) and not list(folder.glob('cm_goblin_*_0_*.dds')) and not list(folder.glob('cm_goblin_unit_*'))
    assert not (out/'main_menu/gfx/animation_state_machines/cm_goblin_infantry.animsm').exists()
    assert not [p for p in (out/'in_game/gfx/models/schematics').glob('cm_goblin_*_schematic.schematic') if p.stem!=SCHEMATIC]
    for source in SOURCES.values():
        for suffix in ['.npz','_id.png','_ao.png','_pos.npz']:assert (SOLDIER/(source+suffix)).is_file(),source+suffix
    native_bones=None
    if game:
        native=read(Path(game)/NATIVE_SKELETON)['children'][0]['children'][0]
        native_bones=next(n for n in native['children'] if n['name']=='skeleton')['children']
    meshes={}
    for name in SOURCES:
        shape,p,n,uv,tri,ix,w,bones=read_mesh(folder/(name+'.mesh'));names=[b['name'] for b in bones]
        assert shape==name+'Shape' and len(bones)==51
        if native_bones is not None:assert bones==native_bones,f'{name}: skeleton must match the native soldier skeleton exactly'
        assert np.isfinite(p).all() and np.allclose(np.linalg.norm(n,axis=1),1,atol=1e-4)
        assert tri.min()>=0 and tri.max()<len(p) and (uv>=0).all() and (uv<=1).all()
        assert (ix<len(names)).all() and ((ix>=0)==(w>0)).all() and np.allclose(w.sum(1),1,atol=1e-3) and (ix[:,0]>=0).all()
        meshes[name]={'triangles':int(len(tri)),'vertices':int(len(p)),'bones_used':int(len(np.unique(ix[ix>=0]))),
                      'height_cm':[round(float(p[:,1].min()),1),round(float(p[:,1].max()),1)]}
        if name==BODY:
            # Whole body on the ground, skull above the native head joint, face toward -z, every limb bone used.
            assert -1<p[:,1].min()<2 and 178<p[:,1].max()<190 and p[:,2].min()<-20 and meshes[name]['bones_used']>=45
            head=names.index('Unit_Base_Rig_Head');assert (ix[p[:,1]>160]==head).any(1).mean()>0.95,'skull must follow the head joint'
    asset=(folder/'cm_goblin_soldier.asset').read_text(encoding='utf-8-sig')
    assert asset.count('{')==asset.count('}')
    for texture in set(re.findall(r'"([^"\n]+\.dds)"',asset)):assert (folder/texture).is_file(),texture
    constructors=(out/'main_menu/gfx/unit_graphics/units/zz_ashborn_goblins.txt').read_text(encoding='utf-8-sig')
    attachments=(out/'main_menu/gfx/unit_graphics/attachments/zz_ashborn_goblins.txt').read_text(encoding='utf-8-sig')
    native_machine='unit_skeleton_state_machine_one_handed_axe'
    if game:
        army=(Path(game)/'main_menu/gfx/unit_graphics/units/01_army.txt').read_text(encoding='utf-8-sig')
        assert native_machine in army and 'schematic_name = unit_skeleton_schematic' in army
        lists=(Path(game)/'main_menu/gfx/unit_graphics/attachments/00_attachment_lists.txt').read_text(encoding='utf-8-sig')
        for name in NATIVE_ATTACH:assert re.search(rf'^\s*{name}\s*=\s*{{',lists,re.M),name
        roundtrip=ROOT/'.local/pdx_roundtrip';roundtrip.mkdir(parents=True,exist_ok=True)
        original=Path(game)/NATIVE_SKELETON;target=roundtrip/original.name;write(target,read(original))
        assert target.read_bytes()==original.read_bytes(),'pdx parser/writer must round-trip native data'
    skins={}
    for clan in clans:
        stem=f'cm_goblin_{clan["id"]}_soldier_body';tag=clan['culture']+'_gfx'
        assert f'name = "{stem}_mesh"' in asset and f'texture_diffuse = "{stem}_diffuse.dds"' in asset
        width,height,mips=dds_levels(folder/(stem+'_diffuse.dds'));assert width==height==1024 and mips==11
        image=np.asarray(Image.open(folder/(stem+'_diffuse.dds')).convert('RGB'),float).reshape(-1,3)
        painted=image[image.sum(1)>30];median=np.median(painted,axis=0);target=hex_rgb(clan['skin_srgb'])
        # Skin stays a brightened version of the clan palette with the same hue ordering.
        assert median[1]>median[2] and 1.0<median.mean()/target.mean()<1.7 and np.argmax(median)==np.argmax(target),(clan['id'],median,target)
        skins[clan['id']]=[round(float(x)) for x in median]
        assert f'cm_goblin_{clan["id"]}_body = {{' in attachments and f'mesh_name = "{stem}_mesh"' in attachments
        for category in OUTFITS:
            block=re.search(rf'^{re.escape(tag)}:{category} = {{(.*?)^}}',constructors,re.S|re.M)[1]
            assert f'schematic_name = {SCHEMATIC}' in block and f'animation_state_machine_name = {native_machine}' in block
            attached=re.findall(r'attach = \{ 100 = (\w+)',block)
            assert attached==[f'cm_goblin_{clan["id"]}_body',f'cm_goblin_{category}_outfit',f'cm_goblin_{category}_headgear',*NATIVE_ATTACH],attached
            assert '= torsos' not in block and '= legs' not in block and '= headgear' not in block
    for name in [n for variants in OUTFITS.values() for n in variants]+list(CAPS.values()):
        width,height,mips=dds_levels(folder/(name+'_diffuse.dds'));assert width==height and mips==int(np.log2(width))+1
    # Native helmets, hair and beards do not fit the goblin skull: only goblin outfits and caps, no culture-tag overrides.
    assert ':' not in ''.join(re.findall(r'^(\S+) = \{',attachments,re.M))
    for category,weights in HEADGEAR.items():
        block=re.search(rf'^cm_goblin_{category}_headgear = {{(.*?)^}}',attachments,re.S|re.M)[1]
        assert sorted(re.findall(r'cm_goblin_soldier_cap_(\w+)_mesh',block))==sorted(k for k in weights if k!='none'),category
        outfit_block=re.search(rf'^cm_goblin_{category}_outfit = {{(.*?)^}}',attachments,re.S|re.M)[1]
        assert sorted(re.findall(r'mesh_name = "(\w+)_mesh"',outfit_block))==sorted(OUTFITS[category]),category
    schematic=(out/'in_game/gfx/models/schematics'/(SCHEMATIC+'.schematic')).read_text(encoding='utf-8-sig')
    assert f'name="{SCHEMATIC}"' in schematic and f'value={UNIT_SCALE:.6f}' in schematic
    if game:
        native=(Path(game)/NATIVE_SCHEMATIC).read_text(encoding='utf-8-sig')
        diff=[(a,b) for a,b in zip(native.splitlines(),schematic.splitlines()) if a!=b]
        assert len(native.splitlines())==len(schematic.splitlines()) and len(diff)==3,'Only name and scale may differ from the native soldier graph'
    registration=verify_texture_registration(out,clans,game)
    return {'status':'STATIC MODEL CHECKS PASSED; ENGINE PLAYTEST PENDING',
            'runtime_infantry':'native soldier rig, weapons, shields and animations at goblin scale; sculpted goblin body per clan with two outfit variants per category and three caps',
            'clans':len(clans),'meshes':meshes,'unit_scale':UNIT_SCALE,'native_scale':0.08,'median_skin_texel_srgb':skins,
            'native_skeleton_and_graph_compared':bool(game),'texture_registration':registration,'engine_tested':False}

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'build/goblin_models');ap.add_argument('--game',type=Path);args=ap.parse_args()
    report=verify(args.out,args.game);(args.out/'model_verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
