"""Static checks for goblin infantry built on the native soldier rig."""
import json,re,struct
from pathlib import Path
import numpy as np
from PIL import Image
from pdx_binary import read,write
from export_goblin_models import (ART,MODEL_REL,ROOT,TEXTURE_REGISTRATION,SCHEMATIC,HEAD_MESH,HEAD_JOINT,
                                  NATIVE_SKELETON,NATIVE_SCHEMATIC,NATIVE_ATTACH,UNIT_SCALE,hex_rgb)

def verify_texture_registration(out,clans,game=None):
    """Heads keep authored clan skin: register them in the native fixed-texture list."""
    from verify_055 import parse
    path=out/TEXTURE_REGISTRATION
    assert path.is_file(),'Goblin heads are missing texture-variation registration'
    rows=parse(path.read_text(encoding='utf-8-sig'))
    assert len(rows)==1 and rows[0][:2]==('assets_without_texture_variation','='),'Use the native fixed-texture registry'
    names=[name for name,op,value in rows[0][2] if op is None and value is None]
    expected={f'cm_goblin_{c["id"]}_unit_head_mesh' for c in clans}
    assert set(names)==expected and len(names)==len(expected),'Every clan head must be registered exactly once'
    assert not (out/'main_menu/gfx/unit_graphics/texture_variations/assets_without_texture_variations.txt').exists(),'Do not replace the native registry'
    if game:
        native=parse((Path(game)/'main_menu/gfx/unit_graphics/texture_variations/assets_without_texture_variations.txt').read_text(encoding='utf-8-sig'))
        assert native[0][:2]==rows[0][:2]
    return {'registered_fixed_palette_heads':len(names),'native_contract_checked':bool(game)}

def dds_levels(path):
    raw=Path(path).read_bytes();assert raw[:4]==b'DDS ' and raw[84:88]==b'DXT5',path
    height,width=struct.unpack_from('<II',raw,12);mips=struct.unpack_from('<I',raw,28)[0]
    return width,height,mips

def verify(out,game=None):
    out=Path(out);folder=out/MODEL_REL
    clans=json.loads((ART/'clans.json').read_text())['clans']
    # Retired standalone body: its meshes, clips, graphs and state machine must be gone.
    assert not list(folder.glob('*.anim')) and not list(folder.glob('cm_goblin_*_0_*.dds'))
    assert not (out/'main_menu/gfx/animation_state_machines/cm_goblin_infantry.animsm').exists()
    assert not [p for p in (out/'in_game/gfx/models/schematics').glob('cm_goblin_*_schematic.schematic') if p.stem!=SCHEMATIC]

    tree=read(folder/(HEAD_MESH+'.mesh'));shape=tree['children'][0]['children'][0]
    assert shape['name']==HEAD_MESH+'Shape'
    mesh=next(n for n in shape['children'] if n['name']=='mesh')
    bones=next(n for n in shape['children'] if n['name']=='skeleton')['children'];names=[b['name'] for b in bones]
    if game:
        native=read(Path(game)/NATIVE_SKELETON)['children'][0]['children'][0]
        native_bones=next(n for n in native['children'] if n['name']=='skeleton')['children']
        assert bones==native_bones,'Head skeleton must match the native soldier skeleton exactly'
    p=np.array(mesh['props']['p'][1]).reshape(-1,3);n=np.array(mesh['props']['n'][1]).reshape(-1,3)
    uv=np.array(mesh['props']['u0'][1]).reshape(-1,2);tri=np.array(mesh['props']['tri'][1]).reshape(-1,3)
    assert np.isfinite(p).all() and np.allclose(np.linalg.norm(n,axis=1),1,atol=1e-5)
    assert tri.min()>=0 and tri.max()<len(p) and (uv>=0).all() and (uv<=1).all()
    skin=next(c for c in mesh['children'] if c['name']=='skin')['props']
    ids=np.array(skin['ix'][1]).reshape(-1,4);w=np.array(skin['w'][1]).reshape(-1,4)
    assert (ids[:,0]==names.index(HEAD_JOINT)).all() and (ids[:,1:]==-1).all() and np.allclose(w.sum(1),1)
    # Placement against the native head: neck into the collar, crown near native height, face toward -z.
    assert 145<p[:,1].min()<150 and 170<p[:,1].max()<180 and p[:,2].min()<-15
    if game:
        roundtrip=ROOT/'.local/pdx_roundtrip';roundtrip.mkdir(parents=True,exist_ok=True)
        original=Path(game)/NATIVE_SKELETON;target=roundtrip/original.name;write(target,read(original))
        assert target.read_bytes()==original.read_bytes(),'pdx parser/writer must round-trip native data'

    asset=(folder/(HEAD_MESH+'.asset')).read_text(encoding='utf-8-sig')
    assert asset.count('{')==asset.count('}')
    for texture in set(re.findall(r'"([^"\n]+\.dds)"',asset)):assert (folder/texture).is_file(),texture
    constructors=(out/'main_menu/gfx/unit_graphics/units/zz_ashborn_goblins.txt').read_text(encoding='utf-8-sig')
    attachments=(out/'main_menu/gfx/unit_graphics/attachments/zz_ashborn_goblins.txt').read_text(encoding='utf-8-sig')
    native_machine='unit_skeleton_state_machine_one_handed_axe'
    if game:
        army=(Path(game)/'main_menu/gfx/unit_graphics/units/01_army.txt').read_text(encoding='utf-8-sig')
        assert native_machine in army and 'schematic_name = unit_skeleton_schematic' in army
        lists=(Path(game)/'main_menu/gfx/unit_graphics/attachments/00_attachment_lists.txt').read_text(encoding='utf-8-sig')
        for name in NATIVE_ATTACH:assert re.search(rf'^\s*{name}\s*=\s*{{',lists,re.M) or name=='hairstyles',name
    skins={}
    for clan in clans:
        stem=f'cm_goblin_{clan["id"]}_unit_head';tag=clan['culture']+'_gfx'
        assert f'name = "{stem}_mesh"' in asset and f'texture_diffuse = "{stem}_diffuse.dds"' in asset
        width,height,mips=dds_levels(folder/(stem+'_diffuse.dds'));assert width==height==256 and mips==9
        image=np.asarray(Image.open(folder/(stem+'_diffuse.dds')).convert('RGB'),float)
        # Median skin stays near the brightened clan palette (green above blue).
        target=np.clip(hex_rgb(clan['skin_srgb'])*1.32,0,255);mean=np.median(image.reshape(-1,3),axis=0)
        assert mean[1]>mean[2] and np.abs(mean-target).max()<45,(clan["id"],mean,target)
        skins[clan['id']]=[round(float(x)) for x in mean]
        assert f'{tag}:heads = {{' in attachments and f'mesh_name = "{stem}_mesh"' in attachments
        assert f'{tag}:hairstyles = {{' in attachments and f'{tag}:beards = {{' in attachments
        for category in ['army_light_infantry','army_heavy_infantry']:
            block=re.search(rf'^{re.escape(tag)}:{category} = {{(.*?)^}}',constructors,re.S|re.M)[1]
            assert f'schematic_name = {SCHEMATIC}' in block and f'animation_state_machine_name = {native_machine}' in block
            attached=re.findall(r'attach = \{ 100 = (\w+)',block)
            assert attached==['heads']+NATIVE_ATTACH,attached
    schematic=(out/'in_game/gfx/models/schematics'/(SCHEMATIC+'.schematic')).read_text(encoding='utf-8-sig')
    assert f'name="{SCHEMATIC}"' in schematic and f'value={UNIT_SCALE:.6f}' in schematic
    if game:
        native=(Path(game)/NATIVE_SCHEMATIC).read_text(encoding='utf-8-sig')
        diff=[(a,b) for a,b in zip(native.splitlines(),schematic.splitlines()) if a!=b]
        assert len(native.splitlines())==len(schematic.splitlines()) and len(diff)==3,'Only name and scale may differ from the native soldier graph'
    registration=verify_texture_registration(out,clans,game)
    return {'status':'STATIC MODEL CHECKS PASSED; ENGINE PLAYTEST PENDING',
            'runtime_infantry':'native soldier rig, gear and animations with clan goblin heads',
            'clans':len(clans),'head_triangles':len(tri),'head_vertices':len(p),'skeleton_bones':len(bones),
            'unit_scale':UNIT_SCALE,'native_scale':0.08,'median_head_texel_srgb':skins,
            'native_skeleton_and_graph_compared':bool(game),'texture_registration':registration,'engine_tested':False}

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'build/goblin_models');ap.add_argument('--game',type=Path);args=ap.parse_args()
    report=verify(args.out,args.game);(args.out/'model_verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
