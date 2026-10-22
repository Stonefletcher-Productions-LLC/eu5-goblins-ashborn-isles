from ashborn_roster import TAGS
"""Check UI explanations and live progress against delivered gameplay predicates."""
import re
from verify_055 import parse, flatten, ownership_checks
from verify_harbor_bargains import World


def verify(read):
    definitions = {}
    for folder in ['scripted_triggers', 'script_values', 'generic_actions']:
        definitions.update({k: v for k, _, v in parse(read('in_game/common/'+folder+'/goblins_gathering.txt'))})
    count = definitions['ga_ui_homeland_count']
    ids = [k[9:] for k, _, _ in flatten(count) if k.startswith('location:')]
    actual = [k[9:] for k, _, _ in flatten(definitions['ga_controls_homeland']) if k.startswith('location:')]
    assert len(ids) == len(set(ids)) == 109 and ids == actual
    assert not any(k in {'set_variable','change_variable','every_country','every_location'} for k, _, _ in flatten(count))
    scenarios = ownership_checks(definitions, ids)
    action = definitions['ga_offer_compact']
    selector = next(v for k, _, v in action if k == 'select_trigger' and ('looking_for_a', '=', 'country') in v)
    fields = dict((k, v) for k, _, v in selector)
    assert fields['show_why_not_enabled'] == 'yes'
    assert [k for k, _, _ in fields['interaction_source_list']] == ['c:'+t for t in TAGS]
    w = World(definitions); scopes = dict(actor='CDM', target='QBR')
    assert w.condition(fields['visible'], 'QBR', scopes)
    assert not w.condition(fields['enabled'], 'QBR', scopes)
    reasons = {v for k, _, v in flatten(fields['enabled']) if k == 'text'}
    trust = {'ga_ui_bound_tt'} if 'ga_swear_pact' in definitions else {'ga_ui_bargain_tt','ga_ui_alliance_age_tt'}
    assert trust | {'ga_ui_opinion_tt','ga_ui_strength_tt','ga_ui_rank_tt','ga_ui_pair_wait_tt'} <= reasons
    for state in ['at_war','is_subject','is_junior_partner']:
        w.countries['QBR'][state] = True
        assert w.condition(fields['visible'], 'QBR', scopes)
        assert not w.condition(fields['enabled'], 'QBR', scopes)
        w.countries['QBR'][state] = False
    w.countries['QBR']['exists'] = False
    assert not w.condition(fields['visible'], 'QBR', scopes)
    assert not w.condition(fields['visible'], 'CDM', scopes)
    localization = read('main_menu/localization/english/goblins_gathering_l_english.yml')
    for rows in definitions.values():
        for k, _, v in flatten(rows):
            if k == 'text' and isinstance(v,str) and v.startswith('ga_ui_'):
                assert re.search(r'^ '+re.escape(v)+': "', localization, re.M), v
    for situation in ['ga_gathering_of_five','ga_eastern_hunger']:
        gui = read('in_game/gui/panels/situation/'+situation+'.gui')
        assert gui.count('text = "ga_ui_homeland_progress"') == 1
        assert 'GetEndConditions' in gui and 'blockoverride "panel_content"' not in gui
        for key in re.findall(r'text = "(ga_ui_\w+)"', gui): assert ' '+key+':' in localization
    assert "[GetPlayer.MakeScope.ScriptValue('ga_ui_homeland_count')|0]" in localization
    return {'ownership_and_progress_scenarios': len(scenarios), 'fixed_locations':len(ids),
            'disabled_crowns_remain_visible':True, 'extinct_and_self_hidden':True,
            'localized_requirement_checks':True, 'read_only_progress':True, 'engine_layout_tested':False}
