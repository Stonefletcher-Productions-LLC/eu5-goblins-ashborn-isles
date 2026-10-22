"""Execute actual generated decisions; not an EU5 engine emulator."""
from copy import deepcopy
import re
from verify_harbor_bargains import World,parse,flatten
from covenant_stories import CHOICES


def verify(read):
    defs={k:v for k,_,v in parse(read('in_game/events/ashen_covenant.txt')) if k!='namespace'}
    hooks=read('in_game/common/on_action/ashen_covenant.txt')
    localization=read('main_menu/localization/english/ashen_covenant_l_english.yml')
    # Native modifier tooltips resolve prefixed keys, not action/option titles.
    localized = dict(re.findall(r'^ (\S+): "(.+)"\r?$', localization, re.M))
    for modifier, _, _ in parse(read('main_menu/common/static_modifiers/ashen_covenant.txt')):
        for prefix in ('STATIC_MODIFIER_NAME_', 'STATIC_MODIFIER_DESC_'):
            assert localized.get(prefix + modifier), 'Missing modifier text: ' + prefix + modifier
    assert 'chance_to_happen = 5' in hooks
    scenarios=[]
    # Story 13 first ships in 0.6.7; older bundles stop at 12.
    stories=[n for n in sorted(CHOICES) if n<=12 or f'ashen_covenant.{n}' in defs]
    def setup(n):
        w=World(defs);data=w.countries['CDM']
        data['owned']={v for k,_,v in flatten(defs[f'ashen_covenant.{n}']) if k=='owns'}
        data['aspects']={v for k,_,v in flatten(defs[f'ashen_covenant.{n}']) if k=='has_religious_aspect'}
        data['vars']['ga_charted_east']=(True,None)
        return w
    def start(w,n):
        scopes={};event=f'ashen_covenant.{n}'
        w.effects(next(v for k,_,v in defs[event] if k=='immediate'),'CDM',scopes)
        return (event,'CDM',scopes)
    for n in stories:
        event=f'ashen_covenant.{n}';body=defs[event]
        options=[v for k,_,v in body if k=='option'];assert len(options)==3
        for key,_,value in flatten(body):
            if key in ['custom_tooltip','text'] and isinstance(value,str):
                assert ' '+value+':' in localization,value
        assert not any(k=='add_prestige' for k,_,_ in flatten(body))
        assert ('name','=','ac_story_cooldown') in list(flatten(body))
        for i in [0,1]:
            for gold,favor,ai in [(50,50,False),(4.99,50,False),(5,50,False),(24.99,50,True),(25,50,True),(50,2.99,False),(50,3,False)]:
                w=setup(n);popup=start(w,n);data=w.countries['CDM'];data.update(gold=gold,religious_influence=favor,is_ai=ai)
                rows=list(flatten(options[i]));cost=-sum(float(v) for k,_,v in rows if k=='add_gold');change=sum(float(v) for k,_,v in rows if k=='add_religious_influence')
                allowed=gold>=cost and (not ai or not cost or gold>=cost+20) and favor>=max(0,-change)
                assert w.choose(popup,i)==allowed,(n,i,gold,favor,ai)
                assert data['gold']==gold-(cost if allowed else 0)
                assert data['religious_influence']==favor+(change if allowed else 0)
                if allowed:
                    assert all(expiry==1095 for expiry in data['modifiers'].values())
                else: assert not data['modifiers']
                before=deepcopy(w.countries);w.choose(popup,i,force=True);assert w.countries==before
            scenarios.append(f'{n}.{i}: price, Favor, AI reserve and repeat boundaries')
        w=setup(n);popup=start(w,n);data=w.countries['CDM'];data.update(gold=0,religious_influence=0)
        data['modifiers']['existing_reward']=1000
        before=(data['gold'],data['religious_influence'],deepcopy(data['modifiers']))
        assert w.choose(popup,2)
        assert before==(data['gold'],data['religious_influence'],data['modifiers'])
        assert w.variable('CDM','ac_story_cooldown') is True
        scenarios.append(f'{n}: neutral defer retains existing effects and cooldown')
        w=setup(n);old=start(w,n);fresh=start(w,n);before=deepcopy(w.countries)
        w.choose(old,0,force=True);w.choose(old,2);assert w.countries==before
        assert deepcopy(w).choose(fresh,0)
        scenarios.append(f'{n}: stale reply cannot affect newer or copied save state')
        legacy=(event,'CDM',{})
        assert not w.choose(legacy,0) and not w.choose(legacy,1)
        before=deepcopy(w.countries);assert w.choose(legacy,2);assert w.countries==before
        scenarios.append(f'{n}: legacy popup can close without changing the current session')
        for reason in ['conversion','eligibility']:
            w=setup(n);popup=start(w,n);data=w.countries['CDM']
            if reason=='conversion': data['religion']='religion:catholic'
            else:
                data['owned'].clear();data['aspects'].clear();data['vars'].pop('ga_charted_east')
                if n in [8,9]: continue # intentionally no additional eligibility
            before=deepcopy(w.countries);w.choose(popup,0,force=True);assert w.countries==before
        scenarios.append(f'{n}: changed faith or story eligibility blocks rewards')
    w=setup(1);w.choose(start(w,1),0);assert 'ac_story_1_0' in w.countries['CDM']['modifiers']
    w.countries['CDM']['owned'].add('location:cm_reedmouth');w.choose(start(w,2),0)
    assert set(w.countries['CDM']['modifiers'])=={'ac_story_2_0'}
    for n in stories:
        for i in [0,1]:
            key=f'ac_story_{n}_{i}'
            if key in read('main_menu/common/static_modifiers/ashen_covenant.txt'):
                assert 'remove_country_modifier = '+key in hooks
    scenarios.append('new story consequences replace old ones and are included in conversion cleanup')
    hook_defs={k:v for k,_,v in parse(hooks)}
    effect=next(v for k,_,v in hook_defs['ac_covenant_monthly'] if k=='effect')
    cleanup=next(v for k,_,v in effect if k=='else')
    w.effects(cleanup,'CDM',{})
    assert not w.countries['CDM']['modifiers'] and not w.variable('CDM','ac_story_open')
    scenarios.append('actual conversion cleanup removes story effects and pending state')
    return {'scenario_groups':len(scenarios),'stories':12,'options_per_story':3,'effect_years':3,
            'neutral_defer':True,'unchanged_frequency':True,'no_prestige_rewards':True,'engine_tested':False}
