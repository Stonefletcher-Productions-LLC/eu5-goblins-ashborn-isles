"""Culture-only rough clothing selection; references installed native accessories.

Native hide, fringe and fur materials inspected against the installed assets.
No native art is copied. Children retain fitted plain clothes, infants swaddling.
"""
from pathlib import Path

OUTFITS = {
    'male': [(5, 'male_clothes_iroquois_low_beadwork_shirt'),
             (3, 'male_clothes_iroquois_low_beadwork'),
             (2, 'male_clothes_iroquois_royal_bear_hunter')],
    'female': [(7, 'female_clothes_iroquois_common_overcoat'),
               (3, 'female_clothes_iroquois_noble_overcoat')],
    'boy': [(1, 'ger_child_cloth_set_a')],
    'girl': [(1, 'child_cloth')],
    # The native no_clothes template already supplies infant swaddling.
    'infant': [(1, 'empty')],
}
RESET = {'clothes': 'no_clothes', 'headwear': 'no_headwear',
         'capes': 'no_cape', 'neckware_neck': 'no_neckware_neck',
         'beards': 'no_beard'}

# Equal weights: no dominant adult style. Drogg has a separate signature crest.
HAIR = {
    'male': [(1, 'male_german_hair_short_curly'),
             (1, 'male_hair_short_straight_pomp'),
             (1, 'male_syrian_hair_curly_regular'),
             (1, 'male_ashanti_hair_short_afro'),
             (1, 'male_german_hair_crown_short'), (1, 'empty')],
    'female': [(1, 'female_syrian_braided_back_hair'),
               (1, 'female_german_braid_hair_behind'),
               (1, 'female_iroquois_straight_parted_hair'),
               (1, 'female_aztec_horn_braid_hair'),
               (1, 'female_ashanti_hair_short_afro')],
    'boy': [(1, 'boy_short_hair_a'), (1, 'boy_german_hair_bob_short'),
            (1, 'male_syrian_hair_curly_regular')],
    'girl': [(1, 'female_hair_long_basic'), (1, 'female_ashanti_hair_short_afro')],
    'infant': [(1, 'empty')],
}

# Native all_hair entry order per portrait type (in_game/common/genes/
# 07_genes_accessories_hair.txt, EU5 1.3.11). All weights are 1 there.
# EU5 resolves a named `accessory =` only against the male list ("Can't find
# accessory 'female_...' in gene template all_hair" in 0.6.4 logs), and a
# `range` alongside a name counts as a second selector ("Both value and
# accessory are set"). So: male choices use the name alone, as native
# 01_hairstyles.txt does; female/child choices use a range slice that lands on
# the curated entry in their own list. verify_goblin_portraits checks this
# order against the installed game. In-game appearance is unverified.
NATIVE_ALL_HAIR = {
    'female': ['female_german_braid_hair_behind', 'female_ashanti_hair_short_afro',
               'female_iroquois_straight_parted_hair', 'female_hair_chinese_bun_loose',
               'female_syrian_braided_back_hair', 'female_aztec_horn_braid_hair',
               'female_deccan_straight_back_hair', 'female_hair_long_basic',
               'male_german_hair_bob_regular', 'female_german_hair_long_crown'],
    'girl': ['female_hair_long_basic', 'female_ashanti_hair_short_afro',
             'girl_han_chinese_hair_bon_sides'],
    'boy': ['boy_short_hair_a', 'boy_german_hair_bob_short', 'male_ashanti_hair_short_afro',
            'boy_han_chinese_hair_bun_front', 'male_syrian_hair_curly_regular',
            'boy_aztec_hair_bob_short'],
}

def hair_selection(sex, name):
    """DNA selector for one curated hairstyle; never both a name and a range."""
    if name == 'empty':
        return 'no_hair', 'range = { 0 1 }'
    if sex == 'male':
        return 'all_hair', 'accessory = ' + name
    entries = NATIVE_ALL_HAIR[sex]
    i, n = entries.index(name), len(entries)
    low, high = (i + 0.1) / n, (i + 0.9) / n
    return 'all_hair', f'range = {{ {low:.3f} {high:.3f} }}'

def hair_modifiers(clans):
    lines=['cm_ashborn_native_hair = { usage = game selection_behavior = weighted_random priority = 130']
    cultures='OR = { '+' '.join('gfx_culture_applicable = '+c['culture']+'_gfx' for c in clans)+' }'
    for sex,choices in HAIR.items():
        if sex=='infant': continue
        female=sex in ['female','girl']
        age='age_in_years >= 18' if sex in ['male','female'] else 'age_in_years >= 3 age_in_years < 18'
        for index,(weight,name) in enumerate(choices):
            template,selection=hair_selection(sex,name)
            lines.append(f'''cm_hair_{sex}_{index} = {{ ignore_outfit_tags = yes
 dna_modifiers = {{ accessory = {{ mode = replace gene = hair_styles template = {template} {selection} }} }}
 weight = {{ base = 0 modifier = {{ add = {weight} {cultures} is_female = {'yes' if female else 'no'} {age} }} }}
 }}''')
    lines.append('}')
    return '\n'.join(lines)

def build(out, clans):
    from build_goblin_portraits import text
    out = Path(out)
    # Separate custom gene avoids replacing vanilla clothing template definitions.
    genes = ['special_genes = {\naccessory_genes = { cm_ashborn_clothing = { inheritable = no',
             'cm_rough_clothing = { index = 0']
    for sex, choices in OUTFITS.items():
        genes.append(sex + ' = { ' + ' '.join(f'{w} = "{a}"' for w, a in choices) + ' }')
    genes += ['adolescent_boy = boy adolescent_girl = girl',
              '} cm_warchief_clothing = { index = 1 male = { 1 = "male_clothes_iroquois_royal_bear_hunter" } female = { 1 = "empty" } boy = { 1 = "empty" } girl = { 1 = "empty" } adolescent_boy = boy adolescent_girl = girl infant = { 1 = "empty" } } } } }']
    text(out/'in_game/common/genes/zz_ashborn_outfits.txt', '\n'.join(genes)+'\n')
    mods = ['cm_ashborn_outfits = { usage = game selection_behavior = max priority = 120']
    for clan in clans:
        # Match native beard/headwear suppression: add the empty template with a
        # selection range. A zero-strength replace did not suppress noble outfits.
        dna = [f'accessory = {{ mode = add gene = {g} template = {t} range = {{ 0 1 }} }}'
               for g, t in RESET.items()]
        dna.append('accessory = { mode = add gene = cm_ashborn_clothing template = cm_rough_clothing range = { 0 1 } }')
        mods.append(f'cm_{clan["id"]}_rough_clothing = {{ ignore_outfit_tags = yes\n'
                    'dna_modifiers = {\n'+'\n'.join(dna)+'\n}\n'
                    f'weight = {{ base = 0 modifier = {{ add = 100 gfx_culture_applicable = {clan["culture"]}_gfx }} }} }}')
    mods.append('}')
    mods.append(hair_modifiers(clans))
    text(out/'main_menu/gfx/portraits/portrait_modifiers/zzz_ashborn_outfits.txt', '\n'.join(mods)+'\n')
    return {'method':'native hide tunics, fringed leather overcoats and fur-trimmed hunter garments; culture-scoped native add-template suppression, priority 120',
            'royal_clothes_and_crowns_suppression':'configured; in-game confirmation pending', 'engine_tested':False,
            'custom_rag_geometry':False, 'beards_removed':True,
            'adult_leather_garment_weight':1.0,
            'hair':'native replacement: six equal male and five equal female choices; no separate hair layer; fitted child choices',
            'children':'native fitted plain clothes; no adult meshes on child rigs'}
