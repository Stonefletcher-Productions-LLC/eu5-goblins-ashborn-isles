"""Check portrait references and native attachment compatibility; not a render test."""
import json,re,struct
from pathlib import Path
import numpy as np
from collections import Counter
from PIL import Image
from pdx_binary import read
from build_goblin_portraits import ROOT,ART,REL,TYPES

def verify(out,game=None):
    out=Path(out);folder=out/REL
    clans=json.loads((ART/'clans.json').read_text())['clans']
    genes=(out/'in_game/common/genes/zz_ashborn_portraits.txt').read_text(encoding='utf-8-sig')
    modifiers=(out/'main_menu/gfx/portraits/portrait_modifiers/zz_ashborn.txt').read_text(encoding='utf-8-sig')
    variants=(out/'main_menu/gfx/portraits/portrait_modifiers/zz_ashborn_male_variation.txt').read_text(encoding='utf-8-sig')
    assert variants.count('{')==variants.count('}')
    assert variants.count('is_female = no age_in_years >= 18')==4
    assert 'selection_behavior = weighted_random priority = 135' in variants
    ethnicity=(out/'in_game/common/ethnicities/ashborn.txt').read_text(encoding='utf-8-sig')
    gfx=(out/'in_game/gfx/graphical_culture_types/ashborn_goblins.txt').read_text(encoding='utf-8-sig')
    accessories=(out/'main_menu/gfx/portraits/accessories/ashborn.txt').read_text(encoding='utf-8-sig')
    asset=(folder/'ashborn_features.asset').read_text(encoding='utf-8-sig')
    # Regression: attachments bypass skin palette, decal and scattering stages.
    assert asset.count('shader = "portrait_skin"')==3*len(clans)
    assert 'shader = "portrait_attachment"' not in asset, 'Ear material must use skin lighting'
    assert asset.count('portrait_decal = { body_part = head }')==3*len(clans)
    assert asset.count('texture_diffuse = "ear_base.dds"')==3*len(clans)
    assert Image.open(folder/'ear_base.dds').getpixel((0,0))[3]==255
    normal=Image.open(folder/'normal.dds').getpixel((0,0))
    assert normal[1]==normal[3]==128, 'RRxG normals use green and alpha'
    properties=Image.open(folder/'properties.dds').getpixel((0,0))
    assert properties[2]==0 and properties[3]>=180, 'Skin must remain non-metallic and rough'
    from build_goblin_portraits import SKIN_OPACITY
    assert SKIN_OPACITY>=.9
    # Shader equation: residual pre-decal face/ear colour difference is <=6%.
    assert (1-SKIN_OPACITY)*255 <= 15.31
    assert genes.count(f'{{ 0 {SKIN_OPACITY} }} {{ 1 {SKIN_OPACITY} }}')==2*len(clans)
    for path in re.findall(r'"([^"\n]+\.(?:mesh|dds))"',asset):assert (folder/path).is_file(),path
    for path in re.findall(r'"(gfx/[^"\n]+\.dds)"',genes):
        if '/ashborn/' in path:
            assert (out/'in_game'/path).is_file(),path
        else:
            assert (re.fullmatch(r'gfx/models/portraits/decals/(male|female)_head/\1_head_old_(forehead|eyes|mouth)_1_early_(diffuse|normal)\.dds',path)
                    or re.fullmatch(r'gfx/models/portraits/decals/visual_traits/male_head_decal_traits_scars_0[12]_(diffuse|normal)\.dds',path)),path
            if game:
                native_texture=Path(game)/'in_game'/path
                assert native_texture.is_file(),path
                if path.endswith('_diffuse.dds'):
                    with Image.open(native_texture) as im:
                        assert im.getpixel((int(im.width*.01),int(im.height*.01)))[3]==0, 'Ear UV must avoid facial weathering'
    for entity in re.findall(r'entity = (cm_\w+)',accessories):assert f'name = "{entity}"' in asset,entity
    for name in re.findall(r'1 = "(cm_\w+)"',genes):assert name+' = {' in accessories,name
    assert genes.lstrip().startswith('special_genes = {'), 'Goblin visuals must not be ordinary DNA'
    assert modifiers.count('mode = add gene = cm_ashborn_stature template = cm_compact_body value = 1')==len(clans)
    assert 'cm_ashborn_stature' not in ethnicity
    assert 'cm_ashborn_weathering' not in ethnicity
    # One per culture, plus one age-appropriate override per crown ruler.
    assert modifiers.split('cm_ashborn_kings =')[0].count('gene = cm_ashborn_weathering')==len(clans)
    from build_goblin_portraits import weathering_gene
    weathering=weathering_gene()
    assert weathering.count('post_skin_color priority = 110')==6, 'Weathering must survive the clan tint'
    for typ in TYPES[2:]: assert typ+' = { }' in weathering, 'No adult weathering on children'
    assert 'attribute = "body_infant_proportions"' in genes and 'attribute = "body_hunchback"' in genes
    assert 'male_body_height' not in genes, 'Do not depend on the disabled female height attribute'
    assert not re.search(r'cm_\w+_(?:skin|features)\s*=', ethnicity), 'Special genes must only be applied by scoped modifiers'
    clans=json.loads((ART/'clans.json').read_text())['clans']
    generic_modifiers=modifiers.split('cm_ashborn_kings =')[0]
    kings=modifiers.split('cm_ashborn_kings =')[1]
    assert 'priority = 140' in kings and 'selection_behavior = max' in kings
    from build_goblin_portraits import KINGS, KING_ACCESSORY_GENES, clan_face
    from build_goblin_outfits import KING_CLOTHING
    culture_of={c['id']:c['culture'] for c in clans}
    # Every crown's 1337 ruler has a distinct signature, not only Drogg.
    assert {k['clan'] for k in KINGS.values()}=={c['id'] for c in clans}
    for name,spec in KINGS.items():
        block=kings.split(f'cm_{name}_signature =')[1].split('_signature =')[0]
        character=spec['character']
        assert f'exists = character:{character} this = character:{character} gfx_culture_applicable = {culture_of[spec["clan"]]}_gfx' in block,name
        assert re.search(r'(?m)^'+character+r' = \{',(out/'main_menu/setup/1337/05_characters.txt').read_text(encoding='utf-8-sig')),character
        assert f"template = {spec['clothing']} range" in block and spec['clothing'] in KING_CLOTHING
        assert all(0<v<=1 for v in spec['face'].values()) and 0<=spec['weathering']<=1
        for gene,template in spec['marks']:assert f'{gene} = {{' in genes and f'{template} = {{' in genes
    signatures=[tuple(sorted(k['face'].items())) for k in KINGS.values()]
    assert len(set(signatures))==len(signatures), 'Two kings share a face'
    looks=[(k['hair'],k['clothing'],k.get('headwear')) for k in KINGS.values()]
    assert len(set(looks))==len(looks), 'Two kings share a costume'
    faces=[tuple(sorted(clan_face(c['id']).items())) for c in clans]
    assert len(set(faces))==len(faces), 'Two cultures share a face recipe'
    assert 'gene = cm_drogg_scar' in kings and 'gene = cm_drogg_scar' not in generic_modifiers
    assert 'gene = cm_ashborn_clothing template = cm_warchief_clothing' in kings
    assert 'mode = replace gene = hair_styles template = all_hair accessory = male_hair_short_straight_pomp' in kings
    for clan in clans:
        ident=clan['id'];tag=clan['culture']+'_gfx'
        assert generic_modifiers.count('gfx_culture_applicable = '+tag)==1
        assert f'100 = cm_{ident}_ethnicity' in gfx
        assert f'cm_{ident}_ethnicity = ' in ethnicity
        texture = folder/f'{ident}_skin.dds'
        raw = texture.read_bytes()
        assert raw[:4] == b'DDS ' and raw[84:88] == b'DXT5', texture
        assert struct.unpack_from('<II', raw, 12) == (1024, 1024), texture
        assert struct.unpack_from('<I', raw, 28)[0] == 11, texture
        assert len(raw) == 1398256, texture
        pixel = Image.open(texture).getpixel((0,0))
        target = bytes.fromhex(clan['skin_srgb'].lstrip('#'))
        assert all(abs(a-b) <= 4 for a,b in zip(pixel[:3], target)), texture
        assert pixel[3] == 255, texture
        if game:
            native_decal = Path(game)/'in_game/gfx/models/portraits/decals/male_body/decal_male_body_old_01_diffuse.dds'
            native_raw = native_decal.read_bytes()
            for start,end in [(12,20),(28,32),(76,108)]:
                assert raw[start:end] == native_raw[start:end], (texture, 'native texture array mismatch')
    for typ in TYPES:assert genes.count(typ+' = ')>=10,typ
    assert 'employer' not in modifiers and 'is_ruler' not in modifiers and 'is_female' not in modifiers
    triangles=0
    for sex in ['male','female','infant']:
        shape=read(folder/f'cm_{sex}_features.mesh')['children'][0]['children'][0]
        assert sum(c['name']=='mesh' for c in shape['children'])==1, 'External tusks must not return'
        bones=next(c['children'] for c in shape['children'] if c['name']=='skeleton')
        if game:
            native=Path(game)/'in_game/gfx/models/portraits'
            native=native/(sex+'_head')/(sex+'_head.mesh') if sex!='infant' else native/'infant/infant_head_base.mesh'
            ns=read(native)['children'][0]['children'][0]
            nb={b['name']:b for b in next(c['children'] for c in ns['children'] if c['name']=='skeleton')}
            for bone in bones:assert np.allclose(bone['props']['tx'][1],nb[bone['name']]['props']['tx'][1]),bone['name']
        for mesh_index,mesh in enumerate(c for c in shape['children'] if c['name']=='mesh'):
            p=np.array(mesh['props']['p'][1]).reshape(-1,3);t=np.array(mesh['props']['tri'][1]).reshape(-1,3)
            assert np.allclose(mesh['props']['u0'][1],.01), 'Ear UV must sample outside the facial crease masks'
            skin=next(c['props'] for c in mesh['children'] if c['name']=='skin')
            assert np.isfinite(p).all() and t.min()>=0 and t.max()<len(p)
            area=np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]])
            assert (np.linalg.norm(area,axis=1)>1e-8).all(), (sex,'degenerate triangle')
            if mesh_index==0:
                # Ears must be watertight with opposite winding on shared edges.
                edges=Counter()
                for face in t:
                    verts=[tuple(np.round(p[v],5)) for v in face]
                    for a,b in zip(verts,verts[1:]+verts[:1]):edges[(a,b)]+=1
                assert all(n==1 and edges[(b,a)]==1 for (a,b),n in edges.items()), (sex,'open or reversed ear shell')
                assert len(t)>=1000, (sex,'old flat ear geometry')
                for sign in [-1,1]:
                    side=t[p[t].mean(axis=1)[:,0]*sign>0]
                    volume=np.einsum('ij,ij->i',p[side[:,0]],np.cross(p[side[:,1]],p[side[:,2]])).sum()/6
                    assert volume>0, (sex,'inside-out ear')
            assert np.allclose(np.linalg.norm(np.array(mesh['props']['n'][1]).reshape(-1,3),axis=1),1)
            assert min(skin['ix'][1])>=0 and max(skin['ix'][1])<len(bones)
            assert np.allclose(np.array(skin['w'][1]).reshape(-1,4).sum(axis=1),1)
            triangles+=len(t)
    for script in [genes,modifiers,accessories,asset,ethnicity]:assert script.count('{')==script.count('}')
    from build_goblin_outfits import OUTFITS, RESET, HAIR
    outfit_genes=(out/'in_game/common/genes/zz_ashborn_outfits.txt').read_text(encoding='utf-8-sig')
    outfit_mods=(out/'main_menu/gfx/portraits/portrait_modifiers/zzz_ashborn_outfits.txt').read_text(encoding='utf-8-sig')
    for script in [outfit_genes,outfit_mods]:assert script.count('{')==script.count('}')
    assert outfit_genes.lstrip().startswith('special_genes = {'), 'Goblin clothes must not be ordinary DNA'
    assert 'mode = add gene = cm_ashborn_clothing' in outfit_mods
    assert 'priority = 120' in outfit_mods and 'selection_behavior = max' in outfit_mods
    clothing_mods=outfit_mods.split('cm_ashborn_native_hair =')[0]
    assert all(clothing_mods.count('gfx_culture_applicable = '+c['culture']+'_gfx')==1 for c in clans)
    assert all(outfit_mods.count('mode = add gene = '+g+' template = '+t+' range = { 0 1 }')==len(clans) for g,t in RESET.items())
    assert 'value = 0' not in outfit_mods, 'Zero-strength replacements failed to clear noble outfits'
    assert OUTFITS['infant']==[(1,'empty')], 'Do not layer clothing over the native infant swaddle'
    assert HAIR['infant']==[(1,'empty')]
    assert 'cm_ashborn_hair' not in outfit_mods+outfit_genes, 'Separate accessory gene layered two hairstyles'
    assert 'gene = hair_styles template = no_hair' not in clothing_mods
    assert outfit_mods.count('mode = replace gene = hair_styles')==sum(len(HAIR[t]) for t in ['male','female','boy','girl'])
    assert 'selection_behavior = weighted_random priority = 130' in outfit_mods
    # 0.6.4.1: a named hair accessory plus a range logged "Both value and
    # accessory are set"; named female/child styles logged "Can't find accessory".
    hair_lines=[l for l in outfit_mods.splitlines() if 'gene = hair_styles' in l]
    assert not [l for l in hair_lines if 'accessory = ' in l.split('gene = hair_styles',1)[1] and 'range' in l], 'Hair modifier sets both a name and a range'
    assert not re.search(r'gene = hair_styles template = all_hair accessory = (?!male_)', outfit_mods), 'Only male hair may be selected by name'
    from build_goblin_outfits import NATIVE_ALL_HAIR, hair_selection
    for sex in ['female','girl','boy']:
        for _,name in HAIR[sex]:
            low,high=map(float,re.search(r'range = \{ ([\d.]+) ([\d.]+) \}',hair_selection(sex,name)[1]).groups())
            n=len(NATIVE_ALL_HAIR[sex])
            assert int(low*n)==int(high*n)==NATIVE_ALL_HAIR[sex].index(name),(sex,name)
    for sex,minimum in [('male',6),('female',5)]:
        assert len(HAIR[sex])>=minimum and len({name for _,name in HAIR[sex]})==len(HAIR[sex])
        assert max(w for w,_ in HAIR[sex])/sum(w for w,_ in HAIR[sex])<=.2
    assert not any(token in name for _,name in HAIR['male'] for token in ['bald','long','bob','wig'])
    for sex in ['male','female']:
        assert all('iroquois' in name for _,name in OUTFITS[sex]), 'Adults must select the inspected hide/leather wardrobe'
    assert not any('chinese' in name for choices in OUTFITS.values() for _,name in choices)
    if game:
        native_accessories=(Path(game)/'main_menu/gfx/portraits/accessories/clothes.txt').read_text(encoding='utf-8-sig')
        native_genes='\n'.join(p.read_text(encoding='utf-8-sig') for p in (Path(game)/'in_game/common/genes').glob('*.txt'))
        for choices in OUTFITS.values():
            for _,name in choices:
                assert name=='empty' or re.search(r'(?m)^'+re.escape(name)+r'\s*=\s*\{',native_accessories),name
        for template in RESET.values():assert re.search(r'\b'+template+r'\s*=\s*\{',native_genes),template
        native_hair=(Path(game)/'main_menu/gfx/portraits/accessories/hair.txt').read_text(encoding='utf-8-sig')
        for choices in HAIR.values():
            for _,name in choices:
                assert name=='empty' or re.search(r'(?m)^\s*'+re.escape(name)+r'\s*=\s*\{',native_hair),name
        # Range slices assume the native all_hair order and equal weights.
        hair_genes=(Path(game)/'in_game/common/genes/07_genes_accessories_hair.txt').read_text(encoding='utf-8-sig')
        all_hair=hair_genes[hair_genes.index('all_hair = {'):]
        all_hair=all_hair[:all_hair.index('german_hair = {')]
        for sex in ['female','girl','boy']:
            block=re.search(r'\b'+sex+r'\s*=\s*\{([^}]*)\}',all_hair)[1]
            entries=re.findall(r'(\d+)\s*=\s*(\w+)',block)
            assert [name for _,name in entries]==NATIVE_ALL_HAIR[sex],('native all_hair order changed',sex)
            assert {w for w,_ in entries}=={'1'},('native all_hair weights changed',sex)
        for _,(male,female) in KING_CLOTHING.items():
            for name in (male,female):
                assert name=='empty' or re.search(r'(?m)^'+re.escape(name)+r'\s*=\s*\{',native_accessories),name
        for spec in KINGS.values():
            for gene in KING_ACCESSORY_GENES:
                if gene not in spec:continue
                template,name=spec[gene]
                block=re.search(r'\n\t'+gene+r' = \{(.*?)\n\t\}',native_genes,re.S)[1]
                body=re.search(r'\n\t\t'+template+r' = \{(.*?)\n\t\t\}',block,re.S)[1]
                sex='female' if spec.get('female') else 'male'
                entries=re.findall(r'\d+\s*=\s*(\w+)',re.sub(r'#[^\n]*','',re.search(r'\b'+sex+r' = \{([^}]*)\}',body)[1]))
                # A name resolves only in male lists; a range must hit one item.
                assert (name in entries and sex=='male') if name else len(entries)==1,(gene,template,entries)

            assert re.search(r'\b'+gene+r'\s*=\s*\{',native_genes),gene
        from build_goblin_portraits import FACE
        assert FACE['gene_eye_size'][1] < .5, 'Avoid the previous enlarged cartoon eyes'
        assert FACE['gene_mouth_width'][1] < .65, 'Avoid the previous broad grin'
        assert FACE['gene_forehead_height'][1]<.5, 'Avoid the tall rounded forehead seen on Drogg'
        assert RESET.get('beards') == 'no_beard'
        for sex in ['male','female']:
            body=(Path(game)/f'in_game/gfx/models/portraits/{sex}_body/{sex}_body.asset').read_text(encoding='utf-8-sig')
            for attribute in ['body_infant_proportions','body_hunchback']:
                assert re.search(r'attribute\s*=\s*\{\s*name\s*=\s*"'+attribute+'"',body),(sex,attribute)
    return {'status':'static checks passed; in-game appearance unverified','cultures':len(clans),'portrait_types':7,'attachment_triangles':triangles,'native_rig_bindings_checked':bool(game),'native_outfit_references_checked':bool(game),'engine_tested':False}

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'mod');ap.add_argument('--game',type=Path);a=ap.parse_args()
    print(json.dumps(verify(a.out,a.game),indent=2))
