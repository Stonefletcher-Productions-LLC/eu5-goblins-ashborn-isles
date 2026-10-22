"""Focused religion checks against installed EU5. Does not claim engine acceptance."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path
import ashen_covenant as ac
from verify_055 import parse

def clean(text):
    return re.sub(r'"(?:\\.|[^"\\])*"|#[^\r\n]*', '', text)

def verify(game, out):
    cfg = json.loads((ac.ROOT/'data/island.json').read_text())
    locations = {loc['id']: island['id'] for island in cfg['islands'] for loc in island['locations']}
    assert len({row[2] for row in ac.SITES}) == len(ac.SITES)
    assert len({row[0] for row in ac.SITES}) == len(ac.SITES)
    assert Counter(row[3] for row in ac.SITES) == {
        'cindermaw': 3, 'brackmaw': 2, 'reefhook': 1,
        'shatterfin': 1, 'knifeback': 1, 'sootwake': 1, 'giltfang': 1, 'tolltooth': 1, 'lantern_cay': 1}
    assert set(ac.SITE_IMPORTANCE) == {row[0] for row in ac.SITES}
    assert all(type(level) is int and 1 <= level <= 5 for level in ac.SITE_IMPORTANCE.values())
    assert set(ac.SITE_IMPORTANCE.values()) == {1, 2, 3, 4, 5}
    sites = (out/'in_game/common/holy_sites/ashen_covenant.txt').read_text(encoding='utf-8-sig')
    emitted = dict((key, int(level)) for key, level in re.findall(
        r'ac_(\w+) = \{ location = \w+ type = \w+ importance = (\d+)', sites))
    assert emitted == ac.SITE_IMPORTANCE
    assert {row[3] for row in ac.SITES} == {i['id'] for i in cfg['islands']}
    for row in ac.SITES:
        assert locations[row[2]] == row[3], row
    assert set(ac.STARTING) == {c['tag'] for c in cfg['countries']}
    assert all(len(set(pair)) == 2 and set(pair) <= ac.ASPECTS.keys() for pair in ac.STARTING.values())
    native_mods = '\n'.join(p.read_text(encoding='utf-8-sig') for p in (game/'main_menu/common/modifier_type_definitions').glob('*.txt'))
    mod_ids = set(re.findall(r'(?m)^\s*(\w+)\s*=\s*\{', native_mods))
    for _,_,body in parse((out/'main_menu/common/static_modifiers/ashen_covenant.txt').read_text(encoding='utf-8-sig')):
        for modifier,_,_ in body: assert modifier in mod_ids, modifier
    for modifier in {r[2] for r in ac.ASPECTS.values()} | {r[2] for r in ac.RITES.values()} | {s[4] for s in ac.SITES} | {'monthly_religious_influence', 'maximum_religious_influence', 'female_spouses'}:
        assert modifier in mod_ids, f'Unknown modifier {modifier}'
    files = [p for p in out.rglob('*') if p.is_file() and (p.stem == 'ashen_covenant' or p.name == 'ashen_covenant_l_english.yml')]
    files.append(out/'in_game/common/religions/goblins_ashborn_isles.txt')
    for path in files:
        assert path.read_bytes().startswith(b'\xef\xbb\xbf'), path
        depth = 0
        for ch in clean(path.read_text(encoding='utf-8-sig')):
            depth += (ch == '{') - (ch == '}')
            assert depth >= 0, path
        assert depth == 0, path
    text = (out/'main_menu/localization/english/ashen_covenant_l_english.yml').read_text(encoding='utf-8-sig')
    locs = re.findall(r'^ (\S+):', text, re.M)
    assert len(locs) == len(set(locs)), 'Duplicate localization'
    events = (out/'in_game/events/ashen_covenant.txt').read_text(encoding='utf-8-sig')
    ids = set(re.findall(r'^(ashen_covenant\.\d+) =', events, re.M))
    assert len(ids) == 13
    for key in re.findall(r'\b(?:title|desc|name) = (ashen_covenant\.\d+\.\w+)', events):
        assert key in locs, key
    for image in re.findall(r'image = "([^"]+)"', events):
        assert (ac.ROOT/'mod/main_menu'/image).is_file(), image
    hooks = (out/'in_game/common/on_action/ashen_covenant.txt').read_text(encoding='utf-8-sig')
    assert set(re.findall(r'\b10 = (ashen_covenant\.\d+)', hooks)) == ids - {'ashen_covenant.20'}
    assert hooks.index('name = ac_moot_held value = yes') < hooks.index('id = ashen_covenant.20')
    assert 'num_of_religious_aspects = 0' in hooks
    assert 'NOT = { has_variable = ac_initialized }' in hooks
    assert 'has_variable = ga_unifier NOT = { has_variable = ac_moot_held } ga_controls_homeland = yes' in hooks
    cleanup_branch = hooks.split('else = {', 1)[1].split('ac_covenant_stories', 1)[0]
    assert 'remove_variable = ac_initialized' in cleanup_branch
    actions = (out/'in_game/common/generic_actions/ashen_covenant.txt').read_text(encoding='utf-8-sig')
    for key in ac.RITES:
        assert f'remove_country_modifier = ac_{key}' in hooks
    assert actions.count('NOT = { has_variable = ac_rite_cooldown }') == 3
    assert actions.count('name = ac_rite_cooldown years = 5') == 3
    assert actions.count('price = price:ac_major_rite') == 3
    assert actions.count('years = 5 mode = replace') == 3
    types = (out/'in_game/common/holy_site_types/ashen_covenant.txt').read_text(encoding='utf-8-sig')
    assert 'country_modifier' not in types, 'Holy site national stacking'
    prices = (out/'in_game/common/prices/ashen_covenant.txt').read_text(encoding='utf-8-sig')
    assert 'scaled_gold = 2' in prices and 'religious_influence = 20' in prices
    religion = files[-1].read_text(encoding='utf-8-sig')
    assert 'religious_aspects = 2' in religion and 'has_religious_influence = yes' in religion
    # Verify the installed native action provides access to this faith's aspect pool.
    native_actions = (game/'in_game/common/generic_actions/general_religion.txt').read_text(encoding='utf-8-sig')
    assert 'source_object = scope:actor.religion' in native_actions
    assert 'add_religious_aspect = scope:target' in native_actions
    return {'checks': ['eleven unique sites with unequal island counts and importance 1-5', 'two valid traditions per starting crown',
        'all numeric modifier keys exist in installed EU5', 'script braces and UTF-8 BOM',
        'event localization and existing illustrations', 'event eligibility routing',
        'once-only initialization and Moot dispatch', 'shared rite cooldown and scaled price',
        'conversion cleanup', 'no national holy-site stacking', 'native aspect selection available'],
        'engine_tested': False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=ac.ROOT/'build/religion-check')
    args = parser.parse_args()
    report = ac.build(args.out)
    report['validation'] = verify(args.game, args.out)
    (args.out/'religion-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
