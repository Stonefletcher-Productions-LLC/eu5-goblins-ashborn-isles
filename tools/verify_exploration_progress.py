"""Execute the generated Ashborn Voyages: native expedition hooks, reports and old saves.

This bounded harness runs the expedition types' can_start/on_start/arrival/on_end
blocks the way the engine calls them, with 30-day test months. Pathfinding, travel
time, the Expeditions panel and engine saves still need an in-game playtest.
"""
from copy import deepcopy
from verify_harbor_bargains import World
from verify_055 import parse, flatten
from exploration_progress import FILES, WAYPOINTS, RETIRED
from exploration import ROUTES

EXPEDITION = 'EXPEDITION'


class Voyages(World):
    def __init__(self, definitions):
        super().__init__(definitions)
        for tag in ['POR','FRA','ENG','MOR']:
            self.countries[tag]=deepcopy(self.countries['CDM'])
        self.goblins={tag for tag in self.countries if tag not in ['POR','FRA','ENG','MOR']}
        self.locations={}
        for route,r in ROUTES.items():
            for port in r['locations']:
                loc='location:'+port
                self.countries[loc]=deepcopy(self.countries['CDM'])
                self.locations[loc]='POR'
        for data in self.countries.values():data.update(areas=set(),locations=set())
        self.active=None

    def value(self, value, country, scopes):
        if value=='owner':return self.locations.get(country)
        if value=='root':return scopes.get('root',country)
        return super().value(value,country,scopes)

    def condition(self, rows, country, scopes):
        plain=[]
        for k,op,v in rows:
            if k=='ga_goblin_voyager':
                if (country in self.goblins)!=(v=='yes'):return False
            elif k=='has_ports':
                if v!='yes':return False
            elif k=='expedition_is_returning':
                if self.active['returning']!=(v=='yes'):return False
            elif k=='NOT':
                if self.condition(v,country,scopes):return False
            elif k in ['OR','AND','custom_tooltip']:
                inner=[r for r in v if r[0]!='text']
                if k=='OR':
                    if not any(self.condition([r],country,scopes) for r in inner):return False
                elif not self.condition(inner,country,scopes):return False
            else:plain.append((k,op,v))
        return super().condition(plain,country,scopes)

    def effects(self, rows, country, scopes):
        for k,op,v in rows:
            if k.startswith('location:'):self.effects(v,k,scopes)
            elif k=='owner':
                owner=self.locations[country]
                if owner is not None:self.effects(v,owner,scopes)
            elif k=='if':
                limits=next(value for key,_,value in v if key=='limit')
                if self.condition(limits,country,scopes):
                    self.effects([row for row in v if row[0]!='limit'],country,scopes)
            elif k=='scope:expedition':self.effects(v,EXPEDITION,scopes)
            elif k in ['remove_commander','pause_expedition']:self.active.setdefault(k,[]).append(v)
            elif k=='discover_area':self.countries[country]['areas'].add(v)
            elif k=='discover_location':self.countries[self.value(v,country,scopes)]['locations'].add(country)
            elif k in self.defs and v=='yes':self.effects(self.defs[k],country,scopes)
            elif k=='set_variable' and any(key=='months' for key,_,_ in v):
                data=dict((key,value) for key,_,value in v)
                data['days']=str(float(data.pop('months'))*30)
                super().effects([(k,op,[(key,'=',value) for key,value in data.items()])],country,scopes)
            elif k=='trigger_event_non_silently':
                fields=dict((key,value) for key,_,value in v) if isinstance(v,list) else {'id':v}
                context=deepcopy(scopes);context['root']=country
                context['due']=self.day+30*float(fields.get('months',0))
                self.queue.append((fields['id'],country,context))
            else:super().effects([(k,op,v)],country,scopes)

    def monthly(self, country='CDM'):
        self.effects(dict((k,v) for k,_,v in self.defs['ga_exploration_monthly'])['effect'],country,{'root':country})

    def deliver(self, event=None):
        i=next(i for i,p in enumerate(self.queue) if p[2]['due']<=self.day and (event is None or p[0]==event))
        popup=self.queue.pop(i);name,country,scopes=popup
        fields=dict((k,v) for k,_,v in self.defs[name])
        if not self.countries[country]['exists'] or not self.condition(fields['trigger'],country,scopes):return None
        self.effects(fields.get('immediate',[]),country,scopes)
        return popup

    def answer(self, popup, index):
        name,country,scopes=popup
        option=[v for k,_,v in self.defs[name] if k=='option'][index]
        self.effects([row for row in option if row[0] not in ['name','trigger','ai_chance']],country,deepcopy(scopes))

    # Native expedition lifecycle -------------------------------------------------
    def type(self, route):
        return dict((k,v) for k,_,v in self.defs[f'ga_voyage_{route}_expedition'])

    def visible(self, route, country='CDM'):
        return self.condition(self.type(route)['potential'],country,{'root':country})

    def can_start(self, route, country='CDM'):
        return self.visible(route,country) and self.condition(self.type(route)['can_start'],country,{'root':country})

    def hook(self, route, name, country='CDM', location=None):
        scopes={'root':country,'expedition':EXPEDITION}
        if location:scopes['location']=location
        self.effects(self.type(route).get(name,[]),country,scopes)

    def launch(self, route, country='CDM'):
        if not self.can_start(route,country):return False
        variables=self.type(route)['variables']
        self.countries[EXPEDITION]=deepcopy(self.countries['CDM'])
        self.countries[EXPEDITION]['vars']={k:(float(dict((a,c) for a,_,c in v)['start']),None) for k,_,v in variables}
        self.active={'route':route,'country':country,'returning':False}
        self.hook(route,'on_start',country)
        return True

    def sail(self):
        route,country=self.active['route'],self.active['country']
        stops=[k for k,_,_ in self.type(route)['waypoints']]
        for stop in stops:self.hook(route,'on_arrive_to_waypoint',country,'location:'+stop)
        self.active['returning']=True
        for stop in reversed(stops):self.hook(route,'on_arrive_to_waypoint',country,'location:'+stop)
        charts=self.variable(EXPEDITION,'ga_charts')
        self.hook(route,'on_end',country)
        self.active=None
        return charts


def verify(read):
    defs={}
    for p in FILES[:-1]:defs.update({k:v for k,_,v in parse(read(p)) if k!='namespace'})
    scenarios=[]
    def passed(name):scenarios.append(name)
    def status(w,key='ga_exp_status'):
        for k,_,v in defs[key]:
            if k!='text':continue
            row=dict((k,v) for k,_,v in v)
            if w.condition(row.get('trigger',[]),'CDM',{}):return row['localization_key']
        raise AssertionError('Missing fallback')

    w=Voyages(defs);w.monthly();assert not w.queue
    assert status(w)=='ga_exp_preparing' and w.visible('east') and not w.can_start('east')
    w.day=36*30-1;w.monthly();assert not w.queue and not w.can_start('east')
    w.day+=1;w.monthly();assert [p[0] for p in w.queue]==['goblins_exploration.1']
    w.monthly();assert len(w.queue)==1
    assert status(w)=='ga_exp_status_default' and w.countries['CDM']['gold']==50
    passed('36-month preparation; one free readiness notice; monthly pulses never charge or duplicate')

    for funds,allowed in [(4.99,False),(5,True)]:
        t=deepcopy(w);t.countries['CDM']['gold']=funds
        assert t.launch('east')==allowed
        if allowed:assert t.countries['CDM']['gold']==0
    for route in ['north','south']:assert w.visible(route) and not w.can_start(route)
    passed('exact affordability; north and south shown but locked until the East Route is charted')

    notice=w.deliver();w.answer(notice,0)
    assert w.launch('east') and w.countries['CDM']['gold']==45
    assert status(w)=='ga_exp_at_sea_east' and status(w,'ga_exp_remaining')=='ga_exp_remaining_default'
    assert w.active['remove_commander']
    for route in ROUTES:assert not w.can_start(route)
    w.day+=36*30;w.monthly();assert not w.queue
    passed('one debit per launch; no second voyage or notice while a fleet is at sea')

    # Conquer a port while the fleet is out; contact follows the owner at return.
    w.locations['location:lisbon']='FRA';w.locations['location:setubal']=None
    charts=w.sail();assert charts==len(WAYPOINTS['east'])
    assert w.active is None and w.variable('CDM','ga_charted_east') is True
    assert w.countries['CDM']['locations']>={'location:'+n for n in ROUTES['east']['locations']}
    assert {'area:'+a for a in ROUTES['east']['areas']}<=w.countries['CDM']['areas']
    assert w.countries['FRA']['areas']=={'area:cm_cindermaw_area','area:cm_ashborn_seas_area'}
    assert w.countries['ENG']['areas']==set()
    queued=[p[0] for p in w.queue]
    assert queued.count('goblins_exploration.6')==2 and queued[-1]=='goblins_exploration.2'
    report=w.deliver('goblins_exploration.2');before=deepcopy(w.countries)
    w.effects(dict((k,v) for k,_,v in defs['goblins_exploration.2'])['immediate'],'CDM',report[2])
    assert w.countries==before and not w.visible('east')
    assert status(w)=='ga_exp_resting_status' and w.countries['CDM']['gold']==45
    passed('ports counted once outbound; return charts listed coasts for us and current port owners; report and first contact fire once')

    w.queue=[];start=w.day
    w.day=start+REST-1;w.monthly();assert not w.queue and not w.can_start('north')
    w.day=start+REST;w.monthly();assert [p[0] for p in w.queue]==['goblins_exploration.3']
    passed('exactly 12-month rest, then one notice for the next routes')
    for order in [('north','south'),('south','north')]:
        t=deepcopy(w);t.queue=[]
        for route in order:
            t.countries['CDM']['gold']=9.99;assert not t.launch(route)
            t.countries['CDM']['gold']=10;assert t.launch(route) and t.countries['CDM']['gold']==0
            assert not t.can_start(order[1] if route==order[0] else order[0])
            t.sail()
            assert {'location:'+n for n in ROUTES[route]['locations']}<=t.countries['CDM']['locations']
            t.queue=[];t.day+=REST
        assert status(t)=='ga_exp_completed' and not any(t.visible(r) for r in ROUTES)
        t.monthly();assert not t.queue
    passed('both remaining-route orders; 10-gold boundaries; completed routes leave the Expeditions panel')

    t=deepcopy(w);t.queue=[];t.launch('north');t.hook('north','on_fail')
    assert status(t)=='ga_exp_resting_status' and t.variable('CDM','ga_charted_north') is None
    t.day+=REST;assert t.can_start('north')
    passed('a failed voyage frees the route after the crews rest')

    t=Voyages(defs);t.monthly();t.day=36*30;t.monthly();t.answer(t.deliver(),1)
    assert t.variable('CDM','ga_exp_paused') is True and t.launch('east')
    t.sail();t.queue=[];t.day+=REST;t.monthly();assert not t.queue
    passed('stopped notices stay off; voyages remain available in the panel')

    t=Voyages(defs);t.countries['CDM']['is_ai']=True;t.monthly();t.day=36*30;t.monthly()
    assert not t.queue and t.can_start('east')
    assert float(dict((k,v) for k,_,v in t.type('east')['utility'])['value'])>0
    passed('AI crowns get no notices and launch voyages through native expedition utility')

    for num in [1,3]:
        for choice in [0,1]:
            old=Voyages(defs);c=old.countries['CDM']['vars']
            c.update(ga_exploration_initialized=(True,None),ga_exploration_pending=(True,None))
            if num==3:c['ga_charted_east']=(True,None)
            old.answer((f'goblins_exploration.{num}','CDM',{'root':'CDM'}),choice)
            assert old.variable('CDM','ga_exploration_pending') is None and old.countries['CDM']['gold']==50
            assert old.can_start('east' if num==1 else 'north')
    passed('older open offers close without cost and unlock the native voyages')
    for route_id,(route,r) in enumerate(ROUTES.items(),1):
        old=Voyages(defs);c=old.countries['CDM']['vars']
        c.update(ga_exploration_initialized=(True,None),ga_exploration_pending=(True,None),ga_exp_route=(float(route_id),None),
                 ga_exp_remaining_1=(True,None))
        if route!='east':c['ga_charted_east']=(True,None)
        for k in range(2):old.answer((f'goblins_exploration.{1 if route=="east" else 3}','CDM',{'root':'CDM'}),k)
        assert old.variable('CDM','ga_exploration_pending') is True
        assert status(old)=='ga_exp_at_sea_'+route and status(old,'ga_exp_remaining')=='ga_exp_remaining_1_text'
        for other in ROUTES:assert not old.can_start(other)
        old.queue.append((f'goblins_exploration.{r["event"]}','CDM',{'root':'CDM','due':0}))
        assert old.deliver()
        assert old.variable('CDM','ga_charted_'+route) is True and old.countries['CDM']['gold']==50
        assert {'location:'+n for n in r['locations']}<=old.countries['CDM']['locations']
        before=deepcopy(old.countries)
        old.queue=[(f'goblins_exploration.{r["event"]}','CDM',{'root':'CDM','due':0})];old.deliver()
        assert old.countries==before
    passed('0.6.x calendar voyages already at sea settle once, without another fee')

    for route,r in ROUTES.items():
        fields=dict((k,v) for k,_,v in defs[f'ga_voyage_{route}_expedition'])
        stops=[k for k,_,_ in fields['waypoints']]
        assert stops==WAYPOINTS[route] and set(stops)<=set(r['locations'])
        assert ('add_gold','=',str(-r['cost'])) in fields['on_start']
        assert dict((k,v) for k,_,v in fields['leader'])['is_ruler']=='no'
        for key in ['unique','repeatable','returns_home','travel_mode','show_end_message']:
            assert key in fields,key
    gui=read('in_game/gui/panels/situation/ga_ashborn_voyages.gui')
    assert 'action_button' not in gui and 'ga_commission_voyage' not in gui
    for route in ROUTES: assert 'ga_exp_chart_'+route+'_row' in gui
    for sit in ['ga_gathering_of_five','ga_eastern_hunger']:
        assert 'ga_exp_panel_status' not in read(f'in_game/gui/panels/situation/{sit}.gui')
    localization=read(FILES[-1])
    keys=set()
    for rows in defs.values():
        for key,_,value in flatten(rows):
            if key in ['localization_key','text','title','desc','custom_tooltip'] and isinstance(value,str):keys.add(value)
            if key=='option':keys.add(dict((k,v) for k,_,v in value)['name'])
    for route in ROUTES:
        base=f'ga_voyage_{route}_expedition'
        keys|={base,base+'_desc',base+'_historical_info',base+'_outcome_overview'}
    keys|={'ga_charts','ga_charts_desc','ga_exp_panel_status','ga_exp_route_heading','ga_ashborn_voyages','ga_ashborn_voyages_desc'}
    for key in keys:assert '\n '+key+':' in localization,key
    assert 'Newly charted:' in localization and 'Review Ashborn Voyages' not in localization
    passed('expedition types, situation panel and all their text registered; Review Ashborn Voyages button retired')
    return {'scenario_groups':len(scenarios),'scenarios':scenarios,'retired':RETIRED,'engine_playtested':False}


REST=12*30

if __name__=='__main__':
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    print(json.dumps(verify(lambda p:(root/'mod'/p).read_text(encoding='utf-8-sig')),indent=2))
