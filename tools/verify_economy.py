"""Focused 0.5.6 setup build and economic regression checks; no terrain rebuild."""
import argparse
import json
import re
from decimal import Decimal
from pathlib import Path
import build as b
import economy
import economy_reference
import mixed_populations


def verify(game, out):
    out.mkdir(parents=True, exist_ok=True)
    b.build_setup(game, out)
    import goblin_estates
    goblin_estates.build(b, game, out)
    report = economy.build(b, game, out)
    audit = report['balance_audit']
    assert not audit['staffing_shortfalls'], audit['staffing_shortfalls']
    templates = dict(economy_reference.blocks((out/'in_game/common/town_setups/goblins_ashborn_isles.txt').read_text(encoding='utf-8-sig')))
    pops = dict(economy_reference.blocks(dict(economy_reference.blocks((out/'main_menu/setup/start/06_pops.txt').read_text()))['locations']))
    for loc in b.CFG['locations']:
        actual = {k:int(v) for k,v in re.findall(r'(\w+)\s*=\s*(\d+)', templates[loc['id']+'_settlement'])}
        assert actual == loc['buildings'], loc['id']
        total = sum((Decimal(v) for v in re.findall(r'\bsize\s*=\s*([\d.]+)', pops[loc['id']])), Decimal(0))
        assert total == Decimal(str(loc['pop'])) + mixed_populations.extra(loc['id'])
    countries = audit['countries']
    # Every crown can produce essential manufactured construction/maintenance
    # goods. Shared-market planning must also cover their raw input chains.
    balance = audit['construction_balance']['groups']
    essential = ['masonry', 'glass', 'tools', 'cloth', 'leather', 'paper', 'pottery', 'naval_supplies']
    for tag in countries:
        for good in essential:
            assert balance[tag]['goods'][good]['net_before_pops_and_construction'] > 0, (tag, good)
    for group in ['southern_crowns', 'northern_crown']:
        assert not balance[group]['inputs_requiring_external_supply'], (group, balance[group])
        for good in essential + ['coal', 'weaponry', 'jewelry']:
            assert balance[group]['goods'][good]['net_before_pops_and_construction'] > 0, (group, good)
    assert sum(c['population'] for c in countries.values()) == b.CFG['population_target'] + int(sum(mixed_populations.extra(l['id']) for l in b.CFG['locations'])*1000)
    if 'population_062' in b.CFG:
        verify_population_062(game, out)
    assert countries['CDM']['total_building_levels'] > countries['QBR']['total_building_levels'] > countries['SFK']['total_building_levels'] > countries['RHK']['total_building_levels']
    assert countries['CDM']['building_levels']['weapon_guild'] == 3
    assert countries['QBR']['building_levels']['naval_supplies_guild'] > countries['CDM']['building_levels']['naval_supplies_guild']
    assert countries['SWK']['building_levels']['charcoal_maker'] > countries['CDM']['building_levels']['charcoal_maker']
    assert len({tuple(sorted(next(l['buildings'] for l in b.CFG['locations'] if l['id']==c['capital']).items())) for c in b.CFG['countries']}) == len(b.CFG['countries'])
    # Three native markets and once-only, ownership-guarded investment remain intact.
    markets = (out/'main_menu/setup/start/03_markets.txt').read_text()
    assert 'add_market = cm_hooktooth' in markets
    assert 'add_market = cm_chainhaven' in markets
    assert 'add_market = cm_shatterfin' in markets
    actions = (out/'in_game/common/on_action/goblins_economy.txt').read_text(encoding='utf-8-sig')
    assert actions.count('NOT = { has_variable = ga_economy_initialized }') == 1
    assert actions.count('limit = { owns = location:') == len(b.CFG['locations'])
    report['checks'] = ['native building ranks/resources', 'generated settlement levels',
                        'configured population totals', 'production staffing and resource reserve',
                        'country specialization and scale', 'three markets and guarded initialization',
                        'essential goods in every crown and complete regional base-recipe input chains']
    (out/'economy-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def verify_population_062(game, out):
    """Check delivered classes, country balance, estate labels and tribal shares."""
    import goblin_estates
    from verify_055 import parse
    native_classes = set(re.findall(r'(?m)^(\w+)\s*=\s*\{', (game/'in_game/common/pop_types/00_default.txt').read_text(encoding='utf-8-sig')))
    populations = dict(economy_reference.blocks(dict(economy_reference.blocks((out/'main_menu/setup/start/06_pops.txt').read_text()))['locations']))
    policy = b.CFG['population_062']
    previous_totals = {tag:Decimal(0) for tag in policy['prior_country_population_targets']}
    # 0.6.7 settles the enlarged Shatter Maw from existing Shatterfin towns.
    # Check each donor's 0.6.2 history with its settlers added back.
    settled, departed = {}, {}
    for move in b.CFG.get('shatter_maw_067', {}).get('transfers', []):
        taken = {k:Decimal(str(v)) for k,v in move['taken'].items()}
        settled[move['to']] = (taken, Decimal(str(move['laborers_on_arrival'])))
        gone = departed.setdefault(move['from'], {})
        for k,v in taken.items():gone[k] = gone.get(k,Decimal(0))+v
    additions = {k:Decimal(str(v)) for k,v in b.CFG.get('shatter_maw_067', {}).get('additions', {}).items()}
    for loc in b.CFG['locations']:
        actual = {}
        for key,op,row in parse(populations[loc['id']]):
            assert key == 'define_pop'
            fields = {k:v for k,_,v in row}
            assert fields['type'] in native_classes
            ident=(fields['type'],fields['culture'],fields['religion'])
            actual[ident]=actual.get(ident,Decimal(0))+Decimal(fields['size'])
        expected = {(k,loc['culture'],'cm_hunger_below'):Decimal(str(v)) for k,v in loc['pop_classes'].items()}
        for pop in mixed_populations.additions().get(loc['id'],[]):
            ident=(pop['type'],pop['culture'],'cm_hunger_below')
            expected[ident]=expected.get(ident,Decimal(0))+Decimal(str(pop['size']))
        assert actual==expected,loc['id']
        total=sum(actual.values())
        tribal=sum(v for (k,_,_),v in actual.items() if k=='tribesmen')
        assert Decimal('.25')<=tribal/total<Decimal('.2501'),loc['id']
        if loc['id'] in additions:
            # 0.6.7 adds new Cinderstep towns, outside the 0.6.2 policy.
            assert Decimal(str(loc['pop']))==additions[loc['id']] and loc['id'] not in policy['locations']
            assert actual==expected and loc['pop_classes']['laborers']>=3,loc['id']
            continue
        if loc['id'] in settled:
            taken, laborers = settled[loc['id']]
            arrived = dict(taken, laborers=laborers, peasants=taken['peasants']-laborers)
            assert arrived=={k:Decimal(str(v)) for k,v in loc['pop_classes'].items()},loc['id']
            assert loc['id'] not in policy['locations']
            continue
        classes = {k:Decimal(str(v))+departed.get(loc['id'],{}).get(k,Decimal(0)) for k,v in loc['pop_classes'].items()}
        pop = Decimal(str(loc['pop']))+sum(departed.get(loc['id'],{}).values())
        prior=policy['locations'][loc['id']]
        changes={k:Decimal(str(v)) for k,v in prior['class_changes'].items()}
        assert 'slaves' not in changes
        assert all(classes[k]-v>=0 for k,v in changes.items())
        assert all(v>0 for k,v in changes.items() if k!='peasants')
        assert classes['peasants']>=Decimal(str(prior['minimum_peasants']))
        assert Decimal(str(loc['pop']))/total>=Decimal('.70'),loc['id']
        assert pop-sum(changes.values())==Decimal(str(prior['population_before']))
        previous_totals[loc['country']]+=Decimal(str(prior['population_before']))*1000
    assert previous_totals==policy['prior_country_population_targets']
    names=(out/'main_menu/localization/english/goblin_estates_l_english.yml').read_text(encoding='utf-8-sig')
    for key in ['crown_estate','nobles_estate','tribes_estate']:
        assert f'ga_{key}: "{goblin_estates.NAMES[key]}"' in names
    assert 'Boss Clan' not in names
    audit=economy.audit(b,game)
    assert not audit['staffing_shortfalls']
    assert {tag:c['population'] for tag,c in audit['countries'].items()}==policy['total_country_targets']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=b.ROOT/'build/economy-check')
    args = parser.parse_args()
    result = verify(args.game, args.out)
    print(json.dumps({'checks': result['checks'], 'rgo_bonus': result['rgo_expansion_total'],
                      'runtime_balance_verified': False}, indent=2))
