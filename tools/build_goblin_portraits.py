"""Culture-selected goblin portrait features, using the native portrait rig.

Geometry is authored here; portrait_bindings contains only attachment rig metadata.
No vanilla mesh, texture, or animation is redistributed. Engine testing is pending.
"""
import json, math, struct
from pathlib import Path
import numpy as np
from PIL import Image
from pdx_binary import node, write, read

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/models/goblins'
REL='in_game/gfx/models/portraits/ashborn'
TYPES=['male','female','boy','girl','adolescent_boy','adolescent_girl','infant']
SKIN_OPACITY = 0.94

# Gathering artwork: hooded eyes, lean cheeks, a hooked nose and a restrained
# mouth. Avoid stacking extreme morphs: that made the previous faces caricatures.
FACE = {
    'gene_nose_length': (.73,.86), 'gene_nose_tip_forward': (.69,.83),
    'gene_nose_tip_angle': (.16,.29), 'gene_nose_width': (.30,.44),
    'gene_nose_ridge_def': (.65,.82),
    'gene_jaw_width': (.38,.50), 'gene_jaw_height': (.32,.44),
    'gene_chin_size': (.36,.48), 'gene_head_height': (.30,.42),
    'gene_head_width': (.51,.62),
    'gene_forehead_height': (.22,.36), 'gene_forehead_roundness': (.22,.38),
    'gene_forehead_angle': (.39,.50),
    'gene_eye_size': (.30,.43), 'gene_eye_open': (.34,.46),
    'gene_eye_forward': (.30,.43), 'gene_eye_socket': (.62,.78),
    'gene_forehead_brow_forward': (.72,.87),
    'gene_forehead_brow_height': (.30,.43),
    'gene_cheek_forward': (.61,.77), 'gene_cheek_width': (.39,.53),
    'gene_cheek_def': (.75,.89), 'gene_cheek_fat': (.19,.32),
    'gene_mouth_width': (.47,.61), 'gene_mouth_upper_lip_size': (.23,.37),
    'gene_mouth_lower_lip_size': (.26,.40),
    'gene_mouth_corner_height': (.32,.44),
    'gene_neck_length': (.24,.38),
}

# Per-culture offsets from FACE, so heirs, consorts and courtiers of each crown
# read as one people at a glance. Shifts stay inside FACE's restrained limits.
CLAN_FACE = {
    # Forge crews: heavy brow, sturdy jaw. The reference profile.
    'cindermaw': {},
    # Marsh houses: broad flat heads, fleshy cheeks, wide noses, short necks.
    'brackmaw': {'gene_head_width': .07, 'gene_head_height': -.05, 'gene_cheek_fat': .12,
                 'gene_nose_width': .08, 'gene_nose_length': -.06, 'gene_neck_length': -.06,
                 'gene_jaw_width': .06},
    # Reef pilots: narrow heads, pointed chins, sharp noses, livelier eyes.
    'reefhook': {'gene_head_width': -.07, 'gene_jaw_width': -.07, 'gene_chin_size': -.06,
                 'gene_nose_tip_forward': .06, 'gene_eye_open': .03, 'gene_cheek_fat': -.05},
    # Stormfang: long faces, high cheekbones, strong jaws, narrow eyes.
    'shatterfin': {'gene_head_height': .08, 'gene_cheek_forward': .06, 'gene_cheek_def': .04,
                   'gene_jaw_height': .06, 'gene_eye_open': -.05, 'gene_neck_length': .05},
    # Forest wardens: gaunt, deep-set eyes under jutting brows, narrow jaws.
    'sootwake': {'gene_cheek_fat': -.08, 'gene_eye_socket': .08, 'gene_forehead_brow_forward': .05,
                 'gene_jaw_width': -.05, 'gene_head_width': -.04, 'gene_mouth_width': -.05},
    # Counting-house merchants: rounder, softer faces, long noses, small chins.
    'giltfang': {'gene_cheek_fat': .09, 'gene_cheek_def': -.10, 'gene_chin_size': -.05,
                 'gene_nose_length': .05, 'gene_forehead_roundness': .08},
}

def clan_face(ident):
    face = dict(FACE)
    for gene, shift in CLAN_FACE[ident].items():
        a, b = face[gene]
        face[gene] = (round(min(max(a + shift, 0), 1), 2), round(min(max(b + shift, 0), 1), 2))
    return face

# Each 1337 crown ruler gets a deliberate signature look, rather than another
# global species retune. Setup IDs are stable, so the modifiers reach saves.
# Regalia follows LORE.md: Drogg's war hall, Murgash's sluices, Skrezz's shell
# clasp, Snikh's charcoal forest, Vrekk's counting house, Jaimzha's maternal
# house. Accessories use native templates: a single-entry template is selected
# by range, a multi-entry one by name (EU5 resolves names only in male lists).
KINGS = {
    'drogg': {
        'character': 'cm_cdm_ruler', 'clan': 'cindermaw',
        'face': {
            'gene_head_height': .38, 'gene_head_width': .62,
            'gene_forehead_height': .34, 'gene_forehead_roundness': .27,
            'gene_forehead_brow_forward': .91, 'gene_forehead_brow_height': .25,
            'gene_eye_open': .24, 'gene_eye_size': .32,
            'gene_jaw_width': .60, 'gene_jaw_height': .52, 'gene_chin_size': .54,
            'gene_cheek_fat': .17, 'gene_cheek_def': .87, 'gene_cheek_forward': .73,
            'gene_nose_length': .69, 'gene_nose_tip_forward': .69,
            'gene_nose_width': .43, 'gene_nose_ridge_def': .73,
            'gene_mouth_width': .50, 'gene_mouth_corner_height': .43,
            'gene_mouth_upper_lip_size': .25, 'gene_mouth_lower_lip_size': .29,
            'gene_body_weight': .70,
        },
        'weathering': 1.0,
        'hair': 'male_hair_short_straight_pomp',
        'clothing': 'cm_warchief_clothing',
        'headwear': ('iroquois_royalty', None),
        'neckware_neck': ('european_war', 'male_neckwear_german_neck_gorget_black'),
        'marks': [('cm_drogg_scar', 'cm_battle_scar')],
    },
    'murgash': {
        'character': 'cm_qbr_ruler', 'clan': 'brackmaw',
        'face': {
            'gene_head_height': .30, 'gene_head_width': .70,
            'gene_forehead_height': .26, 'gene_forehead_roundness': .45,
            'gene_forehead_brow_forward': .74, 'gene_forehead_brow_height': .36,
            'gene_eye_open': .30, 'gene_eye_size': .28,
            'gene_jaw_width': .64, 'gene_jaw_height': .38, 'gene_chin_size': .44,
            'gene_cheek_fat': .62, 'gene_cheek_def': .48, 'gene_cheek_forward': .64,
            'gene_nose_length': .60, 'gene_nose_tip_forward': .62,
            'gene_nose_width': .58, 'gene_nose_ridge_def': .60,
            'gene_mouth_width': .60, 'gene_mouth_corner_height': .34,
            'gene_mouth_upper_lip_size': .40, 'gene_mouth_lower_lip_size': .46,
            'gene_neck_length': .18, 'gene_body_weight': .90,
        },
        'weathering': .9,
        'hair': 'male_german_hair_balding_forehead',
        'clothing': 'cm_sluice_clothing',
        'neckware_neck': ('european_low_nobility', 'male_ger_cloth_set_a_scarf'),
        'marks': [],
    },
    'skrezz': {
        'character': 'cm_rhk_ruler', 'clan': 'reefhook',
        'face': {
            'gene_head_height': .36, 'gene_head_width': .44,
            'gene_forehead_height': .30, 'gene_forehead_roundness': .30,
            'gene_forehead_brow_forward': .66, 'gene_forehead_brow_height': .44,
            'gene_eye_open': .48, 'gene_eye_size': .40,
            'gene_jaw_width': .32, 'gene_jaw_height': .36, 'gene_chin_size': .30,
            'gene_cheek_fat': .14, 'gene_cheek_def': .84, 'gene_cheek_forward': .70,
            'gene_nose_length': .84, 'gene_nose_tip_forward': .90,
            'gene_nose_width': .30, 'gene_nose_ridge_def': .80,
            'gene_mouth_width': .62, 'gene_mouth_corner_height': .62,
            'gene_mouth_upper_lip_size': .26, 'gene_mouth_lower_lip_size': .30,
            'gene_body_weight': .35,
        },
        'weathering': .2,
        'hair': 'male_iroquois_hair_mohawk_regular',
        'clothing': 'cm_wreck_clothing',
        'headwear': ('ashanti_high_nobility', None),
        'neckware_outer': ('ashanti_high_nobility', None),
        'marks': [],
    },
    'snikh': {
        'character': 'cm_swk_ruler', 'clan': 'sootwake',
        'face': {
            'gene_head_height': .44, 'gene_head_width': .40,
            'gene_forehead_height': .38, 'gene_forehead_roundness': .20,
            'gene_forehead_brow_forward': .90, 'gene_forehead_brow_height': .22,
            'gene_eye_open': .22, 'gene_eye_size': .30, 'gene_eye_socket': .86,
            'gene_jaw_width': .30, 'gene_jaw_height': .48, 'gene_chin_size': .46,
            'gene_cheek_fat': .06, 'gene_cheek_def': .92, 'gene_cheek_forward': .58,
            'gene_nose_length': .78, 'gene_nose_tip_forward': .70,
            'gene_nose_width': .28, 'gene_nose_ridge_def': .86,
            'gene_mouth_width': .40, 'gene_mouth_corner_height': .30,
            'gene_mouth_upper_lip_size': .18, 'gene_mouth_lower_lip_size': .22,
            'gene_neck_length': .40, 'gene_body_weight': .12,
        },
        'weathering': .55,
        'hair': 'male_hair_aztec_hair_bob_long',
        'clothing': 'cm_warden_clothing',
        'headwear': ('iroquois_low_nobility', 'male_headwear_iroquois_low_headband'),
        'marks': [],
    },
    'vrekk': {
        'character': 'cm_gtf_ruler', 'clan': 'giltfang',
        'face': {
            'gene_head_height': .34, 'gene_head_width': .56,
            'gene_forehead_height': .40, 'gene_forehead_roundness': .48,
            'gene_forehead_brow_forward': .70, 'gene_forehead_brow_height': .40,
            'gene_eye_open': .28, 'gene_eye_size': .34,
            'gene_jaw_width': .42, 'gene_jaw_height': .30, 'gene_chin_size': .26,
            'gene_cheek_fat': .44, 'gene_cheek_def': .60, 'gene_cheek_forward': .62,
            'gene_nose_length': .92, 'gene_nose_tip_forward': .80,
            'gene_nose_width': .36, 'gene_nose_ridge_def': .90,
            'gene_mouth_width': .44, 'gene_mouth_corner_height': .52,
            'gene_mouth_upper_lip_size': .16, 'gene_mouth_lower_lip_size': .20,
            'gene_body_weight': .62,
        },
        'weathering': .8,
        'hair': 'male_german_hair_balding_top',
        'clothing': 'cm_merchant_clothing',
        'headwear': ('syrian_low_nobility', 'male_headwear_syrian_low_fur_hat'),
        'neckware_outer': ('european_high_nobility', 'male_ger_cloth_set_a_chain_jewellery'),
        'marks': [('cm_ashborn_king_marks', 'cm_jaw_scar')],
    },
    'jaimzha': {
        'character': 'cm_sfk_maarka', 'clan': 'shatterfin', 'female': True,
        'face': {
            'gene_head_height': .48, 'gene_head_width': .50,
            'gene_forehead_height': .36, 'gene_forehead_roundness': .34,
            'gene_forehead_brow_forward': .72, 'gene_forehead_brow_height': .38,
            'gene_eye_open': .30, 'gene_eye_size': .36,
            'gene_jaw_width': .50, 'gene_jaw_height': .50, 'gene_chin_size': .52,
            'gene_cheek_fat': .16, 'gene_cheek_def': .90, 'gene_cheek_forward': .80,
            'gene_nose_length': .74, 'gene_nose_tip_forward': .66,
            'gene_nose_width': .34, 'gene_nose_ridge_def': .70,
            'gene_mouth_width': .48, 'gene_mouth_corner_height': .40,
            'gene_mouth_upper_lip_size': .28, 'gene_mouth_lower_lip_size': .32,
            'gene_neck_length': .44, 'gene_body_weight': .48,
        },
        'weathering': .85,
        'hair': 'female_aztec_horn_braid_hair',
        'clothing': 'cm_tidemother_clothing',
        'headwear': ('aztec_high_nobility', None),
        'neckware_outer': ('ashanti_high_nobility', None),
        'marks': [],
    },
}
KING_ACCESSORY_GENES = ['headwear', 'neckware_neck', 'neckware_outer']

def king_modifiers(clans):
    from build_goblin_outfits import hair_selection
    cultures = {c['id']: c['culture'] for c in clans}
    rows = ['cm_ashborn_kings = { usage = game selection_behavior = max priority = 140']
    for king, spec in KINGS.items():
        dna = [f'morph = {{ mode = replace gene = {g} template = template_1 value = {v} }}'
               for g, v in spec['face'].items()]
        dna.append(f"morph = {{ mode = replace gene = cm_ashborn_weathering template = cm_weathered value = {spec['weathering']} }}")
        template, selection = hair_selection('female' if spec.get('female') else 'male', spec['hair'])
        dna.append(f'accessory = {{ mode = replace gene = hair_styles template = {template} {selection} }}')
        dna.append(f"accessory = {{ mode = replace gene = cm_ashborn_clothing template = {spec['clothing']} range = {{ 0 1 }} }}")
        for gene in KING_ACCESSORY_GENES:
            if gene in spec:
                template, name = spec[gene]
                selection = f'accessory = {name}' if name else 'range = { 0 1 }'
                dna.append(f'accessory = {{ mode = add gene = {gene} template = {template} {selection} }}')
        for gene, template in spec['marks']:
            dna.append(f'morph = {{ mode = add gene = {gene} template = {template} value = 1 }}')
        character = spec['character']
        rows.append(f'cm_{king}_signature = {{ ignore_outfit_tags = yes\n dna_modifiers = {{\n '
                    + '\n '.join(dna) +
                    f'\n }}\n weight = {{ base = 0 modifier = {{ add = 1000 exists = this exists = character:{character}'
                    f' this = character:{character} gfx_culture_applicable = {cultures[spec["clan"]]}_gfx }} }}\n }}')
    return '\n'.join(rows + ['}'])

def king_marks_gene():
    """Native scar map, applied after the clan tint like the weathering."""
    def decal(stem, blend, alpha, normal):
        textures = f'diffuse = "{stem}_diffuse.dds"' + (f' normal = "{stem}_normal.dds"' if normal else '')
        blends = f'diffuse = {blend}' + (' normal = overlay' if normal else '')
        return (f'decal = {{ body_part = head\n textures = {{ {textures} }}\n blend_modes = {{ {blends} }}\n'
                f' alpha_curve = {{ {{ 0 0 }} {{ 1 {alpha} }} }}\n decal_apply_order = post_skin_color priority = 115\n }}')
    scar = decal('gfx/models/portraits/decals/visual_traits/male_head_decal_traits_scars_01', 'overlay', .85, True)
    rest = 'boy = { } girl = { } adolescent_boy = { } adolescent_girl = { } infant = { }'
    return ('cm_ashborn_king_marks = { inheritable = no\n'
            f' cm_jaw_scar = {{ index = 0 male = {{ {scar} }} female = {{ }} {rest} }}\n}}')

def drogg_scar_gene():
    return '''cm_drogg_scar = { inheritable = no cm_battle_scar = { index = 0
 male = { decal = { body_part = head
 textures = {
 diffuse = "gfx/models/portraits/decals/visual_traits/male_head_decal_traits_scars_02_diffuse.dds"
 normal = "gfx/models/portraits/decals/visual_traits/male_head_decal_traits_scars_02_normal.dds"
 }
 blend_modes = { diffuse = overlay normal = overlay }
 alpha_curve = { { 0 0 } { 1 0.85 } }
 decal_apply_order = post_skin_color priority = 115
 } }
 female = { } boy = { } girl = { } adolescent_boy = { } adolescent_girl = { } infant = { }
 } }'''

MALE_PROFILES = {
    'gaunt': {'gene_head_width': .40, 'gene_jaw_width': .29, 'gene_cheek_fat': .12, 'gene_nose_length': .91, 'gene_nose_width': .27},
    'square': {'gene_head_width': .67, 'gene_jaw_width': .58, 'gene_chin_size': .57, 'gene_nose_length': .62, 'gene_nose_width': .49},
    'heavy': {'gene_head_width': .63, 'gene_jaw_width': .48, 'gene_cheek_fat': .50, 'gene_cheek_def': .53, 'gene_nose_width': .55},
    'sharp': {'gene_head_width': .48, 'gene_jaw_width': .35, 'gene_chin_size': .31, 'gene_cheek_def': .91, 'gene_nose_tip_forward': .91},
}

def male_variation(clans):
    cultures='OR = { '+' '.join('gfx_culture_applicable = '+c['culture']+'_gfx' for c in clans)+' }'
    rows=['cm_ashborn_male_variation = { usage = game selection_behavior = weighted_random priority = 135']
    for name,genes in MALE_PROFILES.items():
        dna='\n'.join(f'morph = {{ mode = replace gene = {g} template = template_1 range = {{ {round(v-.04,2)} {round(v+.04,2)} }} }}' for g,v in genes.items())
        rows.append(f'cm_male_{name} = {{ dna_modifiers = {{ {dna} }} weight = {{ base = 0 modifier = {{ add = 1 is_female = no age_in_years >= 18 {cultures} }} }} }}')
    return '\n'.join(rows+['}'])

def weathering_gene():
    """Restore restrained adult creases AFTER the opaque clan tint.

    Reference installed native maps; do not redistribute textures or assign
    health/scar traits. Separate sex maps preserve their fitted facial UVs.
    Children and infants receive no weathering; normal ageing stays active.
    """
    lines=['cm_ashborn_weathering = { inheritable = no cm_weathered = { index = 0']
    for sex in ['male','female']:
        lines.append(sex+' = {')
        for region in ['forehead','eyes','mouth']:
            stem=f'gfx/models/portraits/decals/{sex}_head/{sex}_head_old_{region}_1_early'
            lines.append(f'''decal = {{ body_part = head
 textures = {{ diffuse = "{stem}_diffuse.dds" normal = "{stem}_normal.dds" }}
 blend_modes = {{ diffuse = multiply normal = overlay }}
 alpha_curve = {{ {{ 0 0 }} {{ 1 0.42 }} }}
 age = {{ mode = multiply curve = {{ {{ 0 0 }} {{ 0.18 0 }} {{ 0.30 1 }} {{ 1 1 }} }} }}
 decal_apply_order = post_skin_color priority = 110
 }}''')
        lines.append('}')
    lines.append('boy = { } girl = { } adolescent_boy = { } adolescent_girl = { } infant = { } } }')
    return '\n'.join(lines)

def text(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    # CRLF on every platform, matching the checked-in Windows builds.
    path.write_text(value,encoding='utf-8-sig',newline='\r\n')

def skin_decal(path, rgb):
    """Constant-color BC3 decal matching native 1024px / 11-mip arrays."""
    width, mip_count = 1024, 11
    header = [124, 0xA1007, width, width, width * width, 0, mip_count]
    header += [0] * 11
    header += [32, 4, int.from_bytes(b'DXT5', 'little'), 0, 0, 0, 0, 0]
    header += [0x401008, 0, 0, 0, 0]
    r, g, b = rgb
    color = (round(r * 31 / 255) << 11) | (round(g * 63 / 255) << 5) | round(b * 31 / 255)
    block = bytes([255, 255]) + bytes(6) + struct.pack('<HHI', color, color, 0)
    payload = b''.join(block * (max(1, (width >> level) // 4) ** 2) for level in range(mip_count))
    path.write_bytes(b'DDS ' + struct.pack('<31I', *header) + payload)


def geometry(sex,bones):
    """Closed cupped pinnae with rounded rims; face points toward -Z.

    Concentric anatomical folds replace the flat five-triangle fan. Matching
    boundary vertices close the front/back shell; normals are area averaged.
    """
    parts=[[]]
    names={b['name']:i for i,b in enumerate(bones)}
    def tri(part,a,b,c,j):parts[part].append((np.array([a,b,c],float),j))
    young=sex=='infant'; female=sex=='female'
    x=5.8 if not female else 5.5
    y=15.7 if not female else 15.3
    if young:x,y=5.9,9.2
    for sign in [-1,1]:
        length=6.3 if not young else 3.2
        # Swept, slightly unequal ears, with a thick root and tapered tip.
        length *= 1.0 if sign > 0 else .96
        scale=.62 if young else 1.0
        outline=np.array([[x-.25,y-1.7*scale,-1.45],
            [x+1.2,y-1.95*scale,-1.2], [x+3.6*scale,y-.35*scale,-.65],
            [x+length,y+2.8*scale,.20], [x+4.0*scale,y+2.15*scale,-.45],
            [x+1.8*scale,y+1.9*scale,-1.1], [x-.3,y+.9*scale,-1.65]])
        # Rounded root/lobe with a cusp at the tip, rather than polygon corners.
        tangents=(np.roll(outline,-1,axis=0)-np.roll(outline,1,axis=0))*.4
        tangents[3]=0
        rim=[]
        for i,a in enumerate(outline):
            j=(i+1)%len(outline);b=outline[j]
            for t in np.arange(4)/4:
                rim.append((2*t**3-3*t*t+1)*a+(t**3-2*t*t+t)*tangents[i]
                           +(-2*t**3+3*t*t)*b+(t**3-t*t)*tangents[j])
        rim=np.array(rim)
        center=np.array([x+1.45*scale,y+.10*scale,-1.15])
        joint=names['Head_B'] if young else names['bn_ear_L_main' if sign>0 else 'bn_ear_R_main']
        def eartri(a,b,c,back=False):
            verts=np.array([a,b,c]);verts[:,0]*=sign
            if (sign<0) != back:verts=verts[[0,2,1]]
            tri(0,*verts,joint)
        for back in (False,True):
            rings=[]
            for radius,depth in [(0.22,.0),(.48,-.18),(.76,-.72),(.91,-.58),(1.,0.)]:
                ring=center+(rim-center)*radius
                ring[:,2] += ((.75*(1-radius)) if back else depth)*scale
                rings.append(ring)
            cap=center+np.array([0,0,.75*scale if back else 0])
            for i in range(len(rim)):
                j=(i+1)%len(rim)
                eartri(cap,rings[0][j],rings[0][i],back)
                for inner,outer in zip(rings,rings[1:]):
                    eartri(inner[i],inner[j],outer[j],back)
                    eartri(inner[i],outer[j],outer[i],back)
        # Native teeth stay inside the animated mouth. Fixed external fangs
        # appeared as detached white studs beside narrower lips in screenshots.
    meshes=[]
    for part_index,faces in enumerate(parts):
        if not faces:continue
        p=[];n=[];ix=[]
        smooth={}
        for verts,j in faces:
            normal=np.cross(verts[1]-verts[0],verts[2]-verts[0])
            for v in verts:
                key=(j,*np.round(v,6));smooth[key]=smooth.get(key,np.zeros(3))+normal
        for verts,j in faces:
            p.extend(verts)
            for v in verts:
                normal=smooth[(j,*np.round(v,6))];n.append(normal/np.linalg.norm(normal))
            ix.extend([[j,0,0,0]]*3)
        p=np.array(p);n=np.array(n);axis=np.tile([0.,1,0],(len(n),1));axis[np.abs(n[:,1])>.9]=[1,0,0]
        tangent=np.cross(axis,n);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
        prop=lambda t,v:(t,np.asarray(v).ravel().tolist())
        low,high=p.min(0),p.max(0);center=(low+high)/2
        meshes.append(node('mesh',{'p':prop('f',p),'n':prop('f',n),'ta':prop('f',np.c_[tangent,np.ones(len(n))]),
            # Sample a blank corner of facial detail maps, not the mouth crease.
            # The constant clan tint still covers the whole head/ear UV space.
            'u0':prop('f',np.full((len(p),2),.01)),'tri':prop('i',np.arange(len(p))),
            'boundingsphere':prop('f',np.r_[center,np.linalg.norm(p-center,axis=1).max()])},[
            node('aabb',{'min':prop('f',low),'max':prop('f',high)}),
            node('material',{'shader':('s','portrait_skin' if part_index==0 else 'portrait_attachment')}),
            node('skin',{'bones':('i',[4]),'ix':prop('i',ix),'w':prop('f',np.tile([1.,0,0,0],(len(p),1)))})]))
    return node('root',{'pdxasset':('i',[1,0])},[node('object',children=[node('ashborn_features',children=meshes+[node('skeleton',children=bones)])])])

def build(out):
    out=Path(out);dest=out/REL;dest.mkdir(parents=True,exist_ok=True)
    clans=json.loads((ART/'clans.json').read_text())['clans']
    bindings=json.loads((ART/'portrait_bindings.json').read_text())
    for sex,bones in bindings.items():write(dest/f'cm_{sex}_features.mesh',geometry(sex,bones))
    # RRxG normal decoding uses G and A, not the usual RGB tangent packing.
    # Ear skin follows PS_skin: palette + head decals + skin scattering.
    for name,color in [('normal',(128,128,255,128)),('properties',(120,64,0,210)),
                       ('ivory',(222,210,164,255)),('ear_base',(128,128,128,255)),
                       ('ssao',(0,0,0,255))]:
        Image.new('RGBA',(4,4),color).save(dest/f'{name}.dds')
    # Opt-in visual effects, never ordinary DNA: zero-strength defaults can render globally.
    genes=['special_genes = {\nmorph_genes = {'];accessories=[];assets=[];modifiers=['cm_ashborn_appearance = {\n usage = game selection_behavior = max priority = 110'];ethnicities=[]
    # Kept within supported native gene ranges. Individuals retain all other DNA.
    genes.append(weathering_gene())
    genes.append(drogg_scar_gene())
    genes.append(king_marks_gene())
    # Reuse the supported torso-only proportion and posture attributes on BOTH
    # sexes. Do not enable the disabled female height animation or infant face.
    # Fade in after childhood so native child/infant growth is not compounded.
    genes.append('''cm_ashborn_stature = { inheritable = no
 cm_compact_body = { index = 0
  male = {
   setting = { attribute = "body_infant_proportions" value = { min = 0 max = 0.42 }
    age = { mode = multiply curve = { { 0 0 } { 0.12 0 } { 0.18 1 } { 1 1 } } } }
   setting = { attribute = "body_hunchback" value = { min = 0 max = 0.24 }
    age = { mode = multiply curve = { { 0 0 } { 0.12 0 } { 0.18 1 } { 1 1 } } } }
  }
  female = male boy = male girl = male adolescent_boy = male adolescent_girl = male
  infant = { }
 }
}''')
    for clan in clans:
        ident=clan['id'];culture=clan['culture'];tag=culture+'_gfx'
        rgb=tuple(bytes.fromhex(clan['skin_srgb'].lstrip('#')))
        skin_decal(dest/f'{ident}_skin.dds', rgb)
        gene='cm_'+ident+'_skin'
        decals=''
        for part in ['head','torso']:
            decals+=f'''decal = {{ body_part = {part}
 textures = {{ diffuse = "gfx/models/portraits/ashborn/{ident}_skin.dds" }}
 blend_modes = {{ diffuse = replace }}
 alpha_curve = {{ {{ 0 {SKIN_OPACITY} }} {{ 1 {SKIN_OPACITY} }} }}
 decal_apply_order = post_skin_color priority = 100
 }}\n'''
        genes.append(f'{gene} = {{ inheritable = no {gene} = {{ index = 0 male = {{ {decals} }} '+
                     ' '.join(f'{t} = male' for t in TYPES if t!='male')+' } }')
        for sex in ['male','female','infant']:
            name=f'cm_{ident}_{sex}_features'
            settings=''
            for i,texture in enumerate(['ear_base']):
                shader='portrait_skin' if i==0 else 'portrait_attachment'
                settings+=f'''meshsettings = {{ name = "ashborn_features" index = {i}
 texture_diffuse = "{texture}.dds" texture_normal = "normal.dds" texture_specular = "properties.dds"
 texture = {{ file = "ssao.dds" index = 3 }}
 shader = "{shader}" shader_file = "gfx/FX/jomini/portrait.shader" }}\n'''
            assets.append(f'pdxmesh = {{ name = "{name}_mesh" file = "cm_{sex}_features.mesh" {settings} }}\nentity = {{ name = "{name}_entity" pdxmesh = "{name}_mesh" game_data = {{ portrait_entity_user_data = {{ color_mask_remap_interval = {{ interval = {{ 0 1 }} }} portrait_decal = {{ body_part = head }} }} }} }}')
            accessories.append(f'{name} = {{ entity = {{ required_tags = "" shared_pose_entity = head entity = {name}_entity }} }}')
        dna=f'morph = {{ mode = add gene = {gene} template = {gene} value = 1 }}\naccessory = {{ mode = add gene = cm_ashborn_features template = cm_{ident}_features value = 1 }}\n'
        dna+='morph = { mode = add gene = cm_ashborn_stature template = cm_compact_body value = 1 }\n'
        dna+='morph = { mode = add gene = cm_ashborn_weathering template = cm_weathered range = { 0.7 1 } }\n'
        face=clan_face(ident)
        dna+='\n'.join(f'morph = {{ mode = replace gene = {g} template = template_1 range = {{ {a} {b} }} }}' for g,(a,b) in face.items())
        modifiers.append(f'cm_{ident}_appearance = {{ ignore_outfit_tags = yes dna_modifiers = {{ {dna} }} weight = {{ base = 0 modifier = {{ add = 100 gfx_culture_applicable = {tag} }} }} }}')
        ethnicities.append(f'cm_{ident}_ethnicity = {{ template = "ethnicity_template"\n'+
            '\n'.join(f'{g} = {{ 100 = {{ name = template_1 range = {{ {a} {b} }} }} }}' for g,(a,b) in face.items())+
            '\n}')
    genes.append('}\naccessory_genes = { cm_ashborn_features = { inheritable = no')
    for i,clan in enumerate(clans):
        ident=clan['id'];genes.append(f'cm_{ident}_features = {{ index = {i}\n'+
            '\n'.join(f'{t} = {{ 1 = "cm_{ident}_{"infant" if t=="infant" else "female" if t in ["female","girl","adolescent_girl"] else "male"}_features" }}' for t in TYPES)+'\n}')
    genes.append('} }\n}');modifiers.append('}')
    modifiers.append(king_modifiers(clans))
    text(dest/'ashborn_features.asset','\n'.join(assets)+'\n')
    text(out/'in_game/common/genes/zz_ashborn_portraits.txt','\n'.join(genes)+'\n')
    text(out/'in_game/common/ethnicities/ashborn.txt','\n'.join(ethnicities)+'\n')
    text(out/'main_menu/gfx/portraits/accessories/ashborn.txt','\n'.join(accessories)+'\n')
    text(out/'main_menu/gfx/portraits/portrait_modifiers/zz_ashborn.txt','\n'.join(modifiers)+'\n')
    text(out/'main_menu/gfx/portraits/portrait_modifiers/zz_ashborn_male_variation.txt',male_variation(clans)+'\n')
    from build_goblin_outfits import build as build_outfits
    outfits = build_outfits(out, clans)
    return {'engine_tested':False,'cultures':len(clans),'portrait_types':TYPES,'method':'shorter swept cupped ears using native skin shader and shared head decal; lower flatter forehead, sturdier jaw, restrained hooked nose, adult weathering and cropped/braided hair; 94% shared clan tint retained','skin_opacity':SKIN_OPACITY,'ear_material':'portrait_skin with head decal routing and skin palette','teeth':'native animated mouth teeth only; detached external fangs removed','infants':'skin and smaller pointed ears; no tusks or extra stature modifier','outfits':outfits,'portrait_stature':'culture-only compact torso 0.42 and stoop 0.24 on both sexes, shorter neck; native child growth preserved; framing and clothing fit need engine review'}

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'mod');a=ap.parse_args()
    print(json.dumps(build(a.out),indent=2))
