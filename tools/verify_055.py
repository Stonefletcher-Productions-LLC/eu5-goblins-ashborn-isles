from ashborn_roster import TAGS
"""Static references plus ownership regression scenarios for the 0.5.5 prototype.

These checks are deliberately not described as an engine parser or gameplay test.
"""
from pathlib import Path
import argparse
import json
import re

TOKEN = re.compile(r'#[^\n]*|"(?:\\.|[^"\\])*"|\?=|>=|<=|!=|[{}=]|[^\s{}=<>!]+|[<>]')

def parse(text):
    tokens = [m[0] for m in TOKEN.finditer(text) if not m[0].startswith('#')]
    index = 0
    def group(nested=False):
        nonlocal index
        rows = []
        while index < len(tokens):
            if tokens[index] == '}':
                assert nested, 'Unexpected closing brace'
                index += 1
                return rows
            key = tokens[index]; index += 1
            assert index < len(tokens), f'Incomplete entry: {key}'
            if tokens[index] not in ['=', '?=', '>=', '<=', '>', '<', '!=']:
                rows.append((key, None, None))
                continue
            operator = tokens[index]; index += 1
            assert index < len(tokens), f'Missing value: {key}'
            if tokens[index] == '{':
                index += 1; value = group(True)
            else:
                value = tokens[index]; index += 1
            rows.append((key, operator, value))
        assert not nested, 'Unclosed brace'
        return rows
    return group()

def flatten(rows):
    for key, operator, value in rows:
        yield key, operator, value
        if isinstance(value, list):
            yield from flatten(value)

def read(path):
    return path.read_text(encoding='utf-8-sig')

def ownership_checks(definitions, ids):
    # Evaluate the actual generated ownership trigger subset, rather than a
    # separate copy of the intended ownership algorithm.
    countries = {tag: {'tag': tag, 'subject': None, 'overlord': None, 'senior': None}
                 for tag in [*TAGS, 'POR']}
    owners = {x: 'CDM' for x in ids}
    locations = {x: {'continent': 'europe', 'coastal': True, 'area': 'cm_cindermaw_area'} for x in ids}
    locations['porto'] = {'continent': 'europe', 'coastal': True, 'area': 'porto_area'}
    owners['porto'] = 'POR'
    claimant = None
    def evaluate(rows, obj, kind='country', depth=0):
        nonlocal claimant
        assert depth < 64, 'Cyclic scripted subject evaluation'
        answers = []
        for key, op, value in rows:
            if key == 'OR': result = any(evaluate([row], obj, kind, depth + 1) for row in value)
            elif key == 'AND': result = evaluate(value, obj, kind, depth + 1)
            elif key == 'NOT': result = not evaluate(value, obj, kind, depth + 1)
            elif key == 'save_temporary_scope_as': claimant = obj; result = True
            elif key == 'this': result = obj == claimant
            elif key == 'tag': result = countries[obj]['tag'] == value
            elif key == 'is_subject': result = (countries[obj]['subject'] is not None) == (value == 'yes')
            elif key == 'is_junior_partner': result = (countries[obj]['senior'] is not None) == (value == 'yes')
            elif key == 'is_subject_type': result = countries[obj]['subject'] == value
            elif key == 'junior_union_with': result = countries[obj]['senior'] == claimant
            elif key == 'any_overlord_or_above':
                others = []
                other = countries[obj]['overlord']
                while other is not None:
                    assert other not in others, 'Cyclic subject graph'
                    others.append(other)
                    other = countries[other]['overlord']
                predicates = [row for row in value if row[0] != 'count']
                results = [evaluate(predicates, other, depth=depth + 1) for other in others]
                result = all(results) if ('count', '=', 'all') in value else any(results)
            elif key == 'overlord':
                other = countries[obj]['overlord']
                result = (op == '?=') if other is None else evaluate(value, other, depth=depth + 1)
            elif key.startswith('location:'): result = evaluate(value, key.split(':', 1)[1], 'location', depth + 1)
            elif key == 'exists': result = owners[obj] is not None
            elif key == 'any_country': result = any(evaluate(value, country, depth=depth + 1) for country in countries)
            elif key == 'any_owned_location':
                result = any(evaluate(value, location, 'location', depth + 1) for location, owner in owners.items() if owner == obj)
            elif key == 'continent': result = locations[obj]['continent'] == value.split(':', 1)[1]
            elif key == 'is_coastal': result = locations[obj]['coastal'] == (value == 'yes')
            elif key == 'area': result = locations[obj]['area'] == value.split(':', 1)[1]
            elif key == 'owner':
                other = owners[obj]
                result = (op == '?=') if other is None else evaluate(value, other, depth=depth + 1)
            elif key == 'owns': result = owners[value.split(':', 1)[1]] == obj
            elif key in definitions: result = evaluate(definitions[key], obj, kind, depth + 1)
            else: raise AssertionError(f'Uncovered ownership test token: {key}')
            answers.append(result)
        return all(answers)
    def complete(): return evaluate(definitions['ga_controls_homeland'], 'CDM')
    def progress(rows):
        nonlocal claimant
        total = 0
        for key, _, value in rows:
            if key == 'value': total = int(value)
            elif key == 'add': total += int(value)
            elif key == 'save_temporary_scope_as': claimant = 'CDM'
            elif key == 'if':
                limit = next(v for k, _, v in value if k == 'limit')
                if evaluate(limit, 'CDM'): total += progress([row for row in value if row[0] != 'limit'])
            else: raise AssertionError(('Unknown progress operation', key))
        return total
    scenarios = []
    def check(name, expected):
        assert complete() == expected, name
        count = progress(definitions['ga_ui_homeland_count'])
        assert 0 <= count <= len(ids) and (count == len(ids)) == expected, (name, count)
        scenarios.append(name)
    check('All homeland directly owned', True)
    assert evaluate(definitions['ga_owns_entire_homeland'], 'CDM')
    assert not evaluate(definitions['ga_has_european_foothold'], 'CDM'), 'Homeland must not count as Europe foothold'
    scenarios.append('European-classified Ashborn homeland is excluded from foothold completion')
    owners['porto'] = 'CDM'
    assert evaluate(definitions['ga_has_european_foothold'], 'CDM')
    scenarios.append('A genuinely foreign coastal foothold counts')
    owners['porto'] = 'POR'
    for tag in [t for t in TAGS if t != 'CDM']:
        countries[tag].update(subject='vassal', overlord='CDM')
    for n, x in enumerate(ids): owners[x] = TAGS[n % len(TAGS)]
    check('Mixed direct land and five vassals', True)
    countries['SFK'].update(subject=None, overlord=None, senior='CDM')
    check('Shatterfin junior union partner', True)
    countries['RHK'].update(overlord='SFK')
    check('Vassal beneath a junior union partner', True)
    countries['QBR'].update(overlord='RHK')
    countries['SWK'].update(overlord='QBR')
    check('Multiple nested vassal links', True)
    countries['QBR']['subject'] = 'ga_compact_autonomy'
    countries['SWK']['subject'] = 'ga_compact_protection'
    check('Nested autonomy and protection charters count toward unification', True)
    owners['porto'] = 'SFK'
    assert evaluate(definitions['ga_has_european_foothold'], 'CDM')
    scenarios.append('Foothold held by a qualifying junior partner counts')
    owners['porto'] = 'POR'
    countries['QBR']['subject'] = 'tributary'
    check('Tributary in the subject chain blocks completion', False)
    countries['QBR']['subject'] = 'vassal'
    owners[ids[-1]] = None
    check('An unowned homeland district blocks completion', False)
    assert progress(definitions['ga_ui_homeland_count']) == len(ids)-1
    owners[ids[-1]] = 'POR'
    check('One foreign-held district blocks completion', False)
    assert progress(definitions['ga_ui_homeland_count']) == len(ids)-1
    countries['POR'].update(subject='vassal', overlord='CDM')
    check('Foreign vassal legitimately holding homeland counts', True)
    countries['SFK']['senior'] = 'POR'
    check('Union under a different senior crown blocks completion', False)
    countries['SFK']['senior'] = 'CDM'
    countries['POR'].update(subject=None, overlord=None)
    countries['CDM'].update(subject='vassal', overlord='POR')
    check('A foreign-controlled claimant cannot win', False)
    assert progress(definitions['ga_ui_homeland_count']) == 0
    countries['CDM'].update(subject=None, overlord=None)
    countries['POR'].update(subject='vassal', overlord='CDM')
    check('Restored independence restores live progress', True)
    return scenarios

def verify(root, game, out):
    import archipelago
    cfg = archipelago.prepare(json.loads(read(root / 'data/island.json')))
    ids = [x['id'] for x in cfg['locations']]
    scripts = sorted(out.glob('in_game/common/**/goblins_gathering.txt'))
    scripts += [out / 'in_game/events/goblins_gathering.txt', out / 'main_menu/common/static_modifiers/goblins_gathering.txt']
    assert len(scripts) == 12, f'Expected 12 script files, got {len(scripts)}'
    ast = {}; declarations = {}; raw = ''
    for path in scripts:
        text = read(path); raw += text
        assert path.read_bytes().startswith(b'\xef\xbb\xbf'), path
        rows = parse(text); ast[path] = rows
        for key, op, value in rows:
            if key != 'namespace':
                assert key not in declarations, f'Duplicate declaration: {key}'
                declarations[key] = value
    # Verify all namespaced static references against either authored or native files.
    directories = {'casus_belli': 'in_game/common/casus_belli', 'subject_type': 'in_game/common/subject_types',
                   'relation_type': 'in_game/common/scripted_relations', 'price': 'in_game/common/prices',
                   'situation': 'in_game/common/situations', 'special_status': 'in_game/common/special_statuses'}
    native_refs = {}
    for kind, folder in directories.items():
        names = set()
        for path in (game / folder).glob('*.txt'):
            names.update(re.findall(r'(?m)^\s*(\w+)\s*=\s*\{', read(path)))
        native_refs[kind] = names
    for kind, ident in re.findall(r'\b(casus_belli|subject_type|relation_type|price|situation|special_status):(\w+)', raw):
        assert ident in declarations or ident in native_refs[kind], f'Missing {kind}: {ident}'
    for ident in re.findall(r'\bid\s*=\s*(ga_gathering\.\d+)|trigger_event_non_silently\s*=\s*(ga_gathering\.\d+)', raw):
        assert (ident[0] or ident[1]) in declarations, ident
    native_modifiers = '\n'.join(read(p) for p in (game / 'main_menu/common/modifier_type_definitions').glob('*.txt'))
    for key, op, modifiers in ast[out / 'main_menu/common/static_modifiers/goblins_gathering.txt']:
        for modifier, _, _ in modifiers:
            assert re.search(r'(?m)^\s*' + re.escape(modifier) + r'\s*=\s*\{', native_modifiers), modifier
    for _, _, body in ast[out / 'in_game/common/subject_types/goblins_gathering.txt']:
        for key, _, value in body:
            if key in ['subject_modifier', 'overlord_modifier']:
                for modifier, _, _ in value:
                    assert re.search(r'(?m)^\s*' + re.escape(modifier) + r'\s*=\s*\{', native_modifiers), modifier
    native_vassal = read(game / 'in_game/common/subject_types/vassal.txt')
    assert 'annexation_min_years_before = 10' in native_vassal and 'annexation_speed = 1' in native_vassal
    native_prices = '\n'.join(read(p) for p in (game / 'in_game/common/prices').glob('*.txt'))
    price_defs = {k: v for k, _, v in parse(native_prices)}
    assert ('scaled_gold', '=', '0.2') in price_defs['subject_pays_vassal'], 'Recheck half-base tribute against native game'
    for modifier in re.findall(r'\bmodifier\s*=\s*(ga_\w+)', raw):
        assert modifier in declarations, modifier
    locpath = out / 'main_menu/localization/english/goblins_gathering_l_english.yml'
    loctext = read(locpath)
    keys = re.findall(r'(?m)^ ([\w.]+):', loctext)
    assert len(keys) == len(set(keys)), 'Duplicate localization keys'
    assert locpath.read_bytes().startswith(b'\xef\xbb\xbf')
    # Native UI discovery requires one ID-matched layout per situation.
    native_panels = game / 'in_game/gui/panels/situation'
    assert 'type situation_panel = lateralview' in read(native_panels / 'common.gui')
    assert 'using = situations_actions' in read(native_panels / 'common.gui')
    for situation_id in ('ga_gathering_of_five', 'ga_eastern_hunger'):
        panel_path = out / 'in_game/gui/panels/situation' / (situation_id + '.gui')
        panel = read(panel_path)
        assert panel_path.read_bytes().startswith(b'\xef\xbb\xbf')
        assert panel.count('{') == panel.count('}'), panel_path
        assert panel.strip().startswith('situation_panel = {'), panel_path
        assert f'text = "{situation_id}_desc"' in panel, panel_path
        assert situation_id + '_desc' in keys
        assert '[SituationView.GetActiveSituation.GetSituation.GetEndConditions]' in panel
        assert 'blockoverride "panel_content"' not in panel, 'Must retain native actions and scrolling'
    for modifier, _, _ in ast[out / 'main_menu/common/static_modifiers/goblins_gathering.txt']:
        for prefix in ('STATIC_MODIFIER_NAME_', 'STATIC_MODIFIER_DESC_'):
            assert prefix + modifier in keys, f'Missing static modifier localization: {prefix}{modifier}'
    # UI wrappers must preserve the original completion conditions exactly.
    for situation_id, field, tooltip, conditions in [
        ('ga_gathering_of_five', 'can_end', 'ga_gathering_complete_tt', 'ga_controls_homeland = yes'),
        ('ga_eastern_hunger', 'can_start', 'ga_eastern_start_tt', 'has_variable = ga_unifier ga_controls_homeland = yes'),
        ('ga_eastern_hunger', 'can_end', 'ga_eastern_complete_tt', 'has_variable = ga_unifier ga_has_european_foothold = yes'),
    ]:
        actual = next(value for key, _, value in declarations[situation_id] if key == field)
        expected = parse('custom_tooltip = { text = ' + tooltip + ' any_country = { ' + conditions + ' } }')
        assert actual == expected, f'Changed situation rules or missing tooltip boundary: {situation_id}.{field}'
        assert tooltip in keys, f'Missing situation tooltip: {tooltip}'
    for field in ['title', 'desc', 'none_available_msg_key']:
        for key in re.findall(r'\b' + field + r'\s*=\s*(ga_[\w.]+)', raw):
            assert key in keys, f'Missing localization: {key}'
    for rows in ast.values():
        for parent, _, value in flatten(rows):
            if parent in ['option', 'select_trigger'] and isinstance(value, list):
                for field, _, key in value:
                    if field == 'name' and isinstance(key, str) and key.startswith('ga_'):
                        assert key in keys, f'Missing option/selector localization: {key}'
    # Full territorial checks: no culture shortcut, percentage threshold, or empty tile success.
    # Every crown must receive its own introduction; Shatterfin has a guarded follow-up.
    situation = declarations['ga_gathering_of_five']
    monthly = next(v for k, _, v in situation if k == 'on_monthly')
    assert {k for k, _, _ in monthly} == {'c:' + tag for tag in TAGS}
    assert all(op == '?=' for _, op, _ in monthly)
    assert not any(k == 'every_country' for k, _, _ in flatten(monthly))
    for tag, number in [('CDM', 10), ('QBR', 11), ('RHK', 12), ('SFK', 13), ('SWK', 14), ('GTF', 40)]:
        introduction = declarations[f'ga_gathering.{number}']
        assert ('trigger', '=', [('tag', '=', tag)]) in introduction
        assert any(k == 'if' and ('limit', '=', [('tag', '=', tag)]) in v
                   and ('trigger_event_non_silently', '=', f'ga_gathering.{number}') in v
                   for k, _, v in flatten(monthly) if isinstance(v, list)), tag
    after = next(v for k, _, v in declarations['ga_gathering.13'] if k == 'after')
    assert after == [('trigger_event_non_silently', '=', [('id', '=', 'ga_gathering.15'), ('days', '=', '30')])]
    followup = declarations['ga_gathering.15']
    assert ('trigger', '=', [('tag', '=', 'SFK'), ('NOT', '=', [('has_variable', '=', 'ga_tidemother_council_seen')])]) in followup
    assert ('immediate', '=', [('set_variable', '=', [('name', '=', 'ga_tidemother_council_seen'), ('value', '=', 'yes')])]) in followup
    assert len([k for k in declarations if k.startswith('ga_gathering.')]) == 30
    # Every diplomatic response must notify the sender before request cleanup.
    for number, outcomes in [(2, [17]), (3, [18])]:
        response = declarations[f'ga_gathering.{number}']
        options = [v for k, _, v in response if k == 'option']
        for body, outcome in zip(options, outcomes, strict=True):
            assert ('save_scope_as', '=', 'ga_offer_respondent') in body
            sender = next(v for k, op, v in body if k == 'var:ga_offer_sender' and op == '?=')
            assert ('trigger_event_non_silently', '=', f'ga_gathering.{outcome}') in sender
        after = next(v for k, _, v in response if k == 'after')
        assert ('remove_variable', '=', 'ga_offer_pending') in after
        assert ('remove_variable', '=', 'ga_offer_sender') in after
    ai_actions = next(v for k, _, v in declarations['ga_gathering_ai_list'] if k == 'actions')
    assert all(k != 'ga_offer_harbor_pact' for k, _, _ in ai_actions)
    harbor_ai = next(v for k, _, v in declarations['ga_harbor_bargains_ai_list'] if k == 'actions')
    assert {k for k, _, _ in harbor_ai} == {'ga_offer_harbor_pact', 'ga_seek_pilot_bargain'}
    ownership = declarations['ga_controls_homeland']
    locations = [key.split(':', 1)[1] for key, _, _ in flatten(ownership) if key.startswith('location:')]
    assert len(locations) == len(set(locations)) == 109
    assert set(locations) == set(ids)
    scenarios = ownership_checks(declarations, ids)
    forbidden = ['change_location_owner', 'annex_country', 'create_sub_unit', 'declare_war_with_cb', 'form_union', 'change_heir_selection']
    for name in forbidden:
        assert not re.search(r'\b' + name + r'\s*=', raw), f'Forbidden grant/forced operation: {name}'
    # The sole scripted subject grant must require explicit recipient consent.
    grants = [k for k, body in declarations.items() if any(key == 'make_subject_of' for key, _, _ in flatten(body))]
    assert grants == ['ga_gathering.33'], grants
    assert all('ga_cp_valid' in str(body) for k, _, body in declarations['ga_gathering.33'] if k == 'option' and 'make_subject_of' in str(body))
    cb = declarations['ga_cb_eastern_foothold']
    assert ('war_goal_type', '=', 'conquer_province') in cb
    assert any(key == 'province' for key, _, _ in cb)
    assert any(key == 'declare_enabled' and any(k == 'ga_controls_homeland' for k, _, _ in value) for key, _, value in cb)
    # No free aid: the payer price is exactly the recipient's 10-gold transfer.
    assert declarations['ga_gathering_aid_price'] == [('gold', '=', '10')]
    report = {'version': '0.5.5', 'script_files': len(scripts), 'situations': 2,
              'events': len([k for k in declarations if k.startswith('ga_gathering.')]),
              'homeland_locations': len(locations), 'localization_keys': len(keys),
              'ownership_scenarios': scenarios, 'native_references_checked': True,
              'no_free_foreign_land_units_or_wars': True, 'static_checks_passed': True,
              'all_five_introductions_routed': True, 'shatterfin_guarded_followup': True,
              'engine_parser_tested': False, 'gameplay_tested': False}
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = verify(root, args.game, args.out or root / 'mod')
    reports = root / 'build/reports'; reports.mkdir(parents=True, exist_ok=True)
    (reports / 'gathering_verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
