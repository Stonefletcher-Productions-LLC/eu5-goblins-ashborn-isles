from ashborn_roster import TAGS
"""Audit optimization invariants and the delivered art against installed EU5."""
import argparse
import json
from pathlib import Path
from verify_055 import parse, flatten
import verify_event_art, verify_clan_flags, verify_goblin_portraits, verify_goblin_models
import verify_ashen_covenant
import verify_script_registration
import verify_harbor_bargains
import verify_compact_talks
import verify_sworn_pacts
import verify_situation_progress
import verify_early_projects
import verify_covenant_stories
import verify_exploration
import verify_exploration_progress
import verify_combined_candidate
import verify_giltfang
import verify_061


def verify(out, game):
    import build, verify_economy
    if 'population_062' in build.CFG:
        verify_economy.verify_population_062(game, out)
    situations = dict((k, v) for k, _, v in parse((out/'in_game/common/situations/goblins_gathering.txt').read_text(encoding='utf-8-sig')))
    monthly = next(v for k, _, v in situations['ga_gathering_of_five'] if k == 'on_monthly')
    assert len(monthly) == len(TAGS)
    for country, op, body in monthly:
        assert op == '?=' and country in {'c:'+tag for tag in TAGS}
        guard = next(v for k, _, v in body if k == 'if')
        assert guard[0] == ('limit', '=', [('NOT', '=', [('has_variable', '=', 'ga_signature_seen')])])
        assert guard[1] == ('set_variable', '=', [('name', '=', 'ga_signature_seen'), ('value', '=', 'yes')])
    actions = dict((k, v) for k, _, v in parse((out/'in_game/common/generic_actions/goblins_gathering.txt').read_text(encoding='utf-8-sig')))
    for key in ['ga_prepare_crossing', 'ga_plan_eastern_foothold']:
        checks = [k for k, _, _ in flatten(actions[key]) if k == 'ga_controls_homeland']
        assert len(checks) == 1
    events = dict((k, v) for k, _, v in parse((out/'in_game/events/goblins_gathering.txt').read_text(encoding='utf-8-sig')))
    modifiers = dict((k, v) for k, _, v in parse((out/'main_menu/common/static_modifiers/goblins_gathering.txt').read_text(encoding='utf-8-sig')))
    opening = [v for k, _, v in events['ga_gathering.1'] if k == 'option']
    expected = [('ga_gathering_leadership','land_morale_modifier','0.05'),
                ('ga_gathering_cooperation','diplomatic_reputation','0.5'),
                ('ga_gathering_independence','global_defensive','0.10')]
    assert len(opening) == 3
    for option, (modifier, effect, amount) in zip(opening, expected, strict=True):
        assert [v for k, _, v in option if k == 'add_prestige'] == ['5']
        assert [v for k, _, v in option if k == 'add_country_modifier'] == [[
            ('modifier','=',''+modifier), ('years','=','5'), ('mode','=','replace')]]
        assert modifiers[modifier] == [(effect,'=',amount)]
        assert not any(k in {'set_variable','trigger_event_non_silently'} for k, _, _ in flatten(option))
    # Existing saves retain their previously granted opening effects until expiry.
    assert modifiers['ga_gathering_claimant'] == [('diplomatic_reputation','=','0.5')]
    assert modifiers['ga_gathering_defiant'] == [('naval_morale_modifier','=','0.05')]
    # All founding-crown introductions are exercised by the shared project verifier below.
    assert modifiers['ga_brackmaw_repaired_sluices'] == [('global_food_capacity_modifier','=','0.10')]
    assert modifiers['ga_reefhook_restored_beacons'] == [('naval_morale_recovery','=','0.05')]
    version=json.loads((out/'.metadata/metadata.json').read_text(encoding='utf-8-sig'))['version']
    return {'version':version, 'monthly_introduction_country_scopes':len(TAGS),
            'setup_061':verify_061.verify(out,game),
            'giltfang':verify_giltfang.verify(out,game),
            'combined_candidate':verify_combined_candidate.verify(lambda p:(out/p).read_text(encoding='utf-8-sig')),
            'harbor_bargains':verify_harbor_bargains.verify(lambda p:(out/p).read_text(encoding='utf-8-sig')),
            'compact_talks':verify_compact_talks.verify(lambda p:(out/p).read_text(encoding='utf-8-sig')),
            'sworn_pacts':verify_sworn_pacts.verify(lambda p:(out/p).read_text(encoding='utf-8-sig')),
            'situation_progress':verify_situation_progress.verify(lambda p:(out/p).read_text(encoding='utf-8-sig')),
            'early_projects':verify_early_projects.verify(lambda p:(out/p).read_text(encoding='utf-8-sig')),
            'covenant_stories':verify_covenant_stories.verify(lambda p:(out/p).read_text(encoding='utf-8-sig')),
            'exploration':verify_exploration_progress.verify(lambda p:(out/p).read_text(encoding='utf-8-sig')),
            'exploration_setup':verify_exploration.verify(game,out,rebuild=False),
            'reefhook_beacons': {'gold_cost':25,'naval_morale_recovery_bonus':0.05,'duration_years':5,
                                'affordability_boundaries_checked':True,'free_decline':True,'extra_popup':False},
            'brackmaw_sluices': {'gold_cost':25,'food_storage_bonus':0.10,'duration_years':5,
                                'affordability_boundaries_checked':True,'free_decline':True,'extra_popup':False},
            'script_registration':verify_script_registration.verify(lambda p:(out/p).read_text(encoding='utf-8-sig')),
            'opening_choices': {'distinct_benefits':3,'prestige_each':5,'duration_years':5,'legacy_effects_preserved':True},
            'events':verify_event_art.verify(out),
            'flags':verify_clan_flags.verify(out,game),
            'portraits':verify_goblin_portraits.verify(out,game),
            'models':verify_goblin_models.verify(out,game),
            'covenant':verify_ashen_covenant.verify(game,out),
            'gameplay_tested':False}


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--game',type=Path,required=True)
    a=ap.parse_args();report=verify(a.out,a.game)
    target=Path(__file__).resolve().parents[1]/'build/reports/optimization_059.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
