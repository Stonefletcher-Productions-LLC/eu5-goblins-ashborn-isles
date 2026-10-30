"""Culture-scoped native character longevity, independent of employer and dynasty."""
from datetime import date
import re

LOCALIZATION = {
    'AUTO_MODIFIER_NAME_ga_goblin_longevity': 'Goblin Longevity',
    'ga_goblin_longevity': 'Goblin Longevity',
    'ga_goblin_longevity_desc': 'Ashborn goblins have a natural life expectancy fifteen years longer than humans under otherwise equal conditions.',
}

def build(b, game, out):
    assert b.CFG['goblin_life_expectancy_bonus_years'] == 15
    definitions = b.read(game, 'main_menu/common/modifier_type_definitions/00_modifier_types.txt')
    a, z = b.block_span(definitions, 'character_life_expectancy')
    assert 'category=character' in definitions[a:z].replace(' ', '').replace('\t', '')
    schema = b.read(game, 'in_game/common/auto_modifiers/readme.txt')
    assert 'type: Scope type for potential_trigger' in schema
    cultures = ' '.join('culture = culture:' + c['culture'] for c in b.CFG['countries'])
    b.write(out, 'in_game/common/auto_modifiers/goblins_longevity.txt', f'''# Species follows character culture, including goblins employed by human countries.
# A conditional modifier prevents stacking and removes the benefit if culture changes.
ga_goblin_longevity = {{
    type = character
    category = character
    potential_trigger = {{ OR = {{ {cultures} }} }}
    character_life_expectancy = 15
}}
''')

def verify(b, out):
    s = (out/'in_game/common/auto_modifiers/goblins_longevity.txt').read_text(encoding='utf-8-sig')
    assert 'type = character' in s and 'category = character' in s
    assert s.count('character_life_expectancy = 15') == 1
    for c in b.CFG['countries']: assert 'culture = culture:' + c['culture'] in s
    assert 'tag =' not in s and 'global_life_expectancy' not in s
    chars = (out/'main_menu/setup/1337/05_characters.txt').read_text(encoding='utf-8-sig')
    import ashborn_names
    ages = {}
    now = date(1337, 11, 11)
    for c in b.CFG['countries']:
        a, z = b.block_span(chars, ashborn_names.ruler(c['tag']))
        born = date(*map(int, re.search(r'birth_date = ([\d.]+)', chars[a:z])[1].split('.')))
        age = now.year - born.year - ((now.month, now.day) < (born.month, born.day))
        assert age == b.CFG['starting_ruler_ages'][c['tag']]
        ages[c['tag']] = age
    assert len(set(ages.values())) >= 5 and all(20 <= age <= 39 for age in ages.values())
    assert sum(age < 30 for age in ages.values()) >= 2
    # All authored Ashborn children have chronological, plausible parent ages.
    rows = {}
    for ident in re.findall(r'(?m)^\s*(cm_\w+)\s*=\s*\{', chars):
        a, z = b.block_span(chars, ident)
        block = chars[a:z]
        born = re.search(r'birth_date = ([\d.]+)', block)
        if born: rows[ident] = (date(*map(int, born[1].split('.'))), block)
    for born, block in rows.values():
        for parent in re.findall(r'\b(?:mother|father) = (cm_\w+)', block):
            parent_born = rows[parent][0]
            assert (born - parent_born).days >= 16*365.25, parent
    for tag in ['CDM','QBR','RHK','SWK']:
        suffix='_brother' if tag in {'RHK','SWK'} else '_son'
        heir_born=rows['cm_'+tag.lower()+suffix][0]
        assert (now-heir_born).days >= 18*365.25
    for tag in ['RHK','SWK']:
        assert (now-rows['cm_'+tag.lower()+'_son'][0]).days < 18*365.25
    courts=[born for ident,(born,_) in rows.items() if '_court_' in ident]
    assert len(courts)==len(set(courts))==3*len(b.CFG['countries'])
    return {'starting_ruler_ages': ages, 'goblin_character_life_expectancy_bonus_years': 15,
            'culture_scoped': True, 'family_dates_checked': True, 'varied_court_birthdays': True, 'engine_tested': False}
