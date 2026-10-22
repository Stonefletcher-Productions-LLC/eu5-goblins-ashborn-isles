"""0.6.1 setup regressions, using native building checks and actual map borders."""
import json,re
from pathlib import Path
import build as b
from audit_061 import graph,components

def verify(out,game):
    locs={l['id']:l for l in b.CFG['locations']}
    edges=graph(out/'in_game/map_data/locations.png')
    provinces={l['province'] for l in locs.values()}
    definitions=(out/'in_game/map_data/definitions.txt').read_text(encoding='utf-8-sig')
    for province in provinces:
        members=[n for n,l in locs.items() if l['province']==province]
        assert len(components(members,edges))==1,(province,components(members,edges))
        a,z=b.block_span(definitions,province)
        assert set(re.findall(r'\bcm_\w+\b',definitions[a:z]))==set(members),province
    assert locs['cm_smokehorn']['province']!='cm_hooktooth_province'
    assert locs['cm_scorchbrook']['province']!='cm_saltjaw_province'
    read=lambda p:(out/p).read_text(encoding='utf-8-sig')
    countries=read('main_menu/setup/start/10_countries.txt')
    for c in b.CFG['countries']:
        a,z=b.block_span(countries,c['tag']); body=countries[a:z]
        assert 'stability = 50 government_power = 75 prestige = 25' in body,c['tag']
        assert 'flag = "unlocked_policy_state_piracy_policy" data = { type = boolean identity = 1 }' in body
    for template in ['cm_captains','cm_tidemothers']:
        assert 'piracy_law = state_piracy_policy' in read(f'main_menu/setup/templates/{template}.txt')
    native=(game/'in_game/common/scripted_triggers/country_triggers.txt').read_text(encoding='utf-8-sig')
    assert 'has_variable = unlocked_policy_$type$' in native
    templates=read('in_game/common/town_setups/goblins_ashborn_isles.txt')
    for n,l in locs.items():
        a,z=b.block_span(templates,n+'_settlement')
        assert dict((k,int(v)) for k,v in re.findall(r'(\w+)\s*=\s*(\d+)',templates[a:z]))==l['buildings'],n
    for cap,sand,stone in [('cm_hooktooth','cm_clayjaw','cm_obsidian_cut'),('cm_chainhaven','cm_lockshore','cm_coinfall')]:
        # 0.6.7 trims every crown to one glass guild and half its masons.
        assert locs[cap]['buildings']['glass_guild']>=1
        assert locs[cap]['buildings']['tools_guild']>=2
        assert locs[cap]['buildings']['paper_guild']>=1
        assert locs[cap]['buildings']['jewelry_guild']>=1
        assert locs[sand]['good']=='sand'
        assert locs[stone]['good']=='stone' and locs[stone]['buildings']['mason']>=1
    reform=read('in_game/common/government_reforms/goblins_ashborn_isles.txt')
    assert 'global_manpower_modifier = 0.50' in reform
    assert 'max_manpower' not in reform
    for capital in ['cm_hooktooth','cm_brackhaven']:
        assert locs[capital]['buildings']['sergeantry']==1
        assert locs[capital]['pop_classes']['soldiers']>=1
    cities=read('main_menu/setup/start/07_cities_and_buildings.txt')
    a,z=b.block_span(cities,'cm_lantern_haven');assert 'rank = town' in cities[a:z]
    assert locs['cm_lantern_haven']['buildings']=={'marketplace':1,'wharf':1,'granary':1}
    for name in ['cm_copperfang','cm_netjaw','cm_rustpeak','cm_bracknet','cm_knifeback','cm_tolltooth']:
        a,z=b.block_span(cities,name);assert 'rank = town' in cities[a:z],name
    for name in ['cm_shatterfin','cm_chainhaven','cm_brackhaven']:
        a,z=b.block_span(cities,name);assert 'rank = city' in cities[a:z],name
    trade=read('in_game/common/scripted_effects/goblins_starting_trades.txt')
    hooks=read('in_game/common/on_action/goblins_starting_trades.txt')
    from economy import STARTING_TRADES, trade_effect
    from verify_055 import parse
    parse(trade);parse(hooks)
    assert 'on_game_start = { on_actions = { ga_starting_trade_setup } }' in hooks
    assert 'current_date < 1338.12.1' in hooks
    assert 'NOT = { has_variable = ga_starting_trade_061 }' in hooks
    for tag,source,target,good in STARTING_TRADES:
        a,z=b.block_span(trade,trade_effect(tag,good));body=trade[a:z]
        assert source!=target
        assert f'from = location:{source}.market to = location:{target}.market' in body
        assert f'merchant = location:{target}.market goods = goods:{good}' in body
        assert 'desired = 1 locked = yes' in body
        assert 'can_find_trade_route' in body and 'available_merchant_capacity' in body
        assert body.index('create_trade =')<body.index('set_variable =')
        assert body.count('any_trade =')==2
    from decimal import Decimal
    migrations=b.CFG['urbanization_061']['locations']
    deltas={c['tag']:Decimal(0) for c in b.CFG['countries']}
    for name,row in migrations.items():
        assert b.CFG.get('population_062',{}).get('locations',{}).get(name,{}).get('population_before',locs[name]['pop'])==row['population_after']
        deltas[locs[name]['country']]+=Decimal(str(row['population_after']))-Decimal(str(row['population_before']))
    assert all(v==0 for v in deltas.values()),deltas
    for situation in ['ga_gathering_of_five','ga_eastern_hunger']:
        assert 'text = "ac_favor_current"' in read(f'in_game/gui/panels/situation/{situation}.gui')
    assert "GetPlayer.GetCurrencyValue('religious_influence')" in read('main_menu/localization/english/ashen_covenant_l_english.yml')
    profiles=read('main_menu/gfx/portraits/portrait_modifiers/zz_ashborn_male_variation.txt')
    assert profiles.count('is_female = no age_in_years >= 18')==4
    assert 'weighted_random priority = 135' in profiles
    assert len(set(re.findall(r'gene_jaw_width template = template_1 range = \{ ([\d.]+) ([\d.]+)',profiles)))>=3
    return {'version':'0.6.1','connected_provinces':len(provinces),'locations':len(locs),
            'starting_stats':[50,75,25],'piracy_policy':'unlocked and selected',
            'production_centers':['cm_hooktooth','cm_chainhaven'],'male_profiles':4,'engine_tested':False}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--game',type=Path,required=True);a=p.parse_args()
    print(json.dumps(verify(a.out,a.game),indent=2))
