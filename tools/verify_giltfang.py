"""Independent new-world checks against delivered rasters, setup and event scripts."""
import json, math, re
from collections import defaultdict, deque
from pathlib import Path
import numpy as np
from PIL import Image
import build as b
from ashborn_roster import TAGS
from verify_055 import parse, flatten
from verify_harbor_bargains import World
from verify_exploration_progress import Voyages
from exploration_progress import FILES


def verify(out,game):
    read=lambda p:(out/p).read_text(encoding='utf-8-sig')
    cfg=b.CFG
    assert len(TAGS)==6 and 'GTF' in TAGS
    new=[l for l in cfg['locations'] if l['country']=='GTF']
    assert len(new)==22 and {l['island'] for l in new}=={'giltfang','tolltooth'}
    countries=read('main_menu/setup/start/10_countries.txt')
    defs=read('in_game/map_data/definitions.txt')
    a,z=b.block_span(defs,'cm_cindermaw_area');homeland=defs[a:z]
    a,z=b.block_span(defs,'cm_ashborn_seas_area');waters=defs[a:z]
    for l in cfg['locations']:assert len(re.findall(r'\b'+l['id']+r'\b',homeland))==1,l['id']
    for sea in cfg['coastal_sea']['zones']:assert sea['id'] in waters
    for tag in TAGS:
        a,z=b.block_span(countries,tag);country=countries[a:z]
        a,z=b.block_span(country,'discovered_areas');known=country[a:z]
        assert 'cm_cindermaw_area' in known and 'cm_ashborn_seas_area' in known,tag
        from exploration import STARTING_SEA_AREAS
        assert set(STARTING_SEA_AREAS)<=set(re.findall(r'\b\w+\b',known)),tag
    a,z=b.block_span(countries,'GTF');assert 'capital = cm_chainhaven' in countries[a:z]
    markets=read('main_menu/setup/start/03_markets.txt')
    for cap in ['cm_chainhaven','cm_hooktooth']:assert markets.count('add_market = '+cap)==1
    # Direct raster adjacency, without the builder's graph or wrapping array edges.
    box=(6000,1650,7900,3100)
    with Image.open(out/'in_game/map_data/locations.png') as im:actual=np.asarray(im.crop(box)).astype(np.uint32)
    with Image.open(game/'in_game/map_data/locations.png') as im:native=np.asarray(im.crop(box)).astype(np.uint32)
    code=lambda rgb:(rgb[...,0]<<16)|(rgb[...,1]<<8)|rgb[...,2]
    actual,native=code(actual),code(native)
    names=b.parse_names(game)
    names.update({x['id']:tuple(bytes.fromhex(x['color'])) for x in cfg['locations']+cfg['coastal_sea']['zones']})
    ids={n:int(code(np.array(c,dtype=np.uint32))) for n,c in names.items()}
    reworked=cfg['coastal_sea'].get('reworked_navigable_sources',[])
    allowed=[ids[n] for n in ['celtic_sea','azores_biscay_ridge']+reworked]
    assert np.isin(native[actual!=native],allowed).all(),'Changed native land or an unapproved sea lane'
    yy,xx=np.mgrid[box[1]:box[3],box[0]:box[2]]
    for source in reworked:
        permitted=np.zeros(actual.shape,bool)
        for region in cfg['coastal_sea']['extra_basins']:
            if region['source_water']==source:
                # Trimmed edges are warped by at most edge_warp[0] pixels.
                m=math.ceil(cfg['coastal_sea'].get('edge_warp',[0])[0]);x0,y0,x1,y1=region['bounds']
                permitted|=(xx>=x0-m)&(xx<x1+m)&(yy>=y0-m)&(yy<y1+m)
        assert not np.any((native==ids[source])&(actual!=native)&~permitted)
        assert b.connectivity(actual==ids[source])[0]==1,source
    pixels={i['id']:sum(int(np.sum(actual==ids[l['id']])) for l in i['locations']) for i in cfg['islands']}
    ratio=(pixels['giltfang']+pixels['tolltooth'])/pixels['brackmaw']
    assert .895<=ratio<=.905,ratio
    default=read('in_game/map_data/default.map')
    a,z=b.block_span(default,'sea_zones');sea=set(re.findall(r'\b\w+\b',b.clean(default[a:z])))
    a,z=b.block_span(default,'impassable_mountains');sea-=set(re.findall(r'\b\w+\b',b.clean(default[a:z])))
    sea_codes={ids[n] for n in sea if n in ids}
    from exploration import STARTING_SEA_AREAS
    known_seas={s['id'] for s in cfg['coastal_sea']['zones']}
    for area in STARTING_SEA_AREAS:
        a,z=b.block_span(defs,area);known_seas.update(re.findall(r'\b\w+\b',b.clean(defs[a:z])))
    # A physical route must also be charted at campaign start to support trade.
    sea_codes &= {ids[n] for n in known_seas if n in ids}
    graph=defaultdict(set)
    for left,right in [(actual[:,:-1],actual[:,1:]),(actual[:-1,:],actual[1:,:])]:
        mask=(left!=right)&np.isin(left,list(sea_codes))&np.isin(right,list(sea_codes))
        for x,y in np.unique(np.stack([left[mask],right[mask]],axis=1),axis=0):
            graph[int(x)].add(int(y));graph[int(y)].add(int(x))
    start=ids['cm_chainhaven_roads'];seen={start};q=deque([start])
    while q:
        for x in graph[q.popleft()]-seen:seen.add(x);q.append(x)
    assert all(ids[s['id']] in seen for s in cfg['coastal_sea']['zones']),'Northern and southern sea networks are disconnected'
    # User requirement: sail between all custom waters without entering a native
    # fast-current tile. Ordinary coastal definitions must carry no assistance.
    ordinary={ids[s['id']] for s in cfg['coastal_sea']['zones']}
    coastal_seen={start};q=deque([start]);parent={}
    while q:
        here=q.popleft()
        for x in (graph[here]&ordinary)-coastal_seen:
            coastal_seen.add(x);parent[x]=here;q.append(x)
    assert ordinary<=coastal_seen,'Route still depends on a fast-current tile'
    route=[ids['cm_cindermaw_north']]
    while route[-1]!=start:route.append(parent[route[-1]])
    reverse={code:name for name,code in ids.items()}
    route=[reverse[code] for code in reversed(route)]
    templates=read('in_game/map_data/location_templates.txt')
    for zone in cfg['coastal_sea']['zones']:
        a,z=b.block_span(templates,zone['id']);body=templates[a:z]
        assert 'topography = coastal_ocean' in body and 'movement_assistance' not in body
    outpost=next(i for i in cfg['islands'] if i['id']=='lantern_cay')
    assert outpost['country']=='CDM' and len(outpost['locations'])==3
    a,z=b.block_span(countries,'CDM');owned=countries[a:z]
    assert all(loc['id'] in owned for loc in outpost['locations'])
    ports=read('in_game/map_data/ports.csv')
    assert 'cm_chainhaven;' in ports
    # Every directed pair can sign both services, receive receipts and earn history.
    scripts={}
    for path in ['scripted_triggers','generic_actions','on_action']:
        scripts.update({k:v for k,_,v in parse(read('in_game/common/'+path+'/goblins_gathering.txt'))})
    scripts.update({k:v for k,_,v in parse(read('in_game/events/goblins_gathering.txt')) if k!='namespace'})
    pairs=0
    for actor in TAGS:
        for target in TAGS:
            if actor==target:continue
            for action in ['ga_offer_harbor_pact','ga_seek_pilot_bargain']:
                w=World(scripts);p=w.offer(actor,target,action);assert w.choose(p,0)
                assert (w.countries[actor]['gold'],w.countries[target]['gold'])==(40,60)
                assert {p[1] for p in w.queue if p[0]=='ga_gathering.24'}=={actor,target}
                w.day=5*365
                hook=dict((k,v) for k,_,v in scripts['ga_hb_contract_pulse'])
                w.effects(hook['effect'],actor,{})
                assert w.variable(actor,'ga_cp_honored_'+target) and w.variable(target,'ga_cp_honored_'+actor)
                pairs+=1
    compacts=0
    for actor,target in [('GTF','CDM'),('CDM','GTF')]:
        for kind in [0,1]:
            w=World(scripts);w.opinion=150
            for a,t in [(actor,target),(target,actor)]:
                w.countries[a]['allies'].add(t)
                w.countries[a]['vars'].update({f'ga_cp_honored_{t}':(True,None),f'ga_cp_allied_ready_{t}':(True,None)})
            p=w.offer(actor,target,'ga_offer_compact')
            for choice in [kind,0]:
                assert w.choose(p,choice);p=w.queue.pop(0)
            assert w.choose(p,kind)
            assert w.countries[target]['subject_type']==['ga_compact_autonomy','ga_compact_protection'][kind]
            assert w.countries[target]['overlord']==actor
            compacts+=1
    voyage={}
    for path in FILES[:-1]:voyage.update({k:v for k,_,v in parse(read(path)) if k!='namespace'})
    for tag in TAGS:
        w=Voyages(voyage);w.monthly(tag);w.day=36*30;w.monthly(tag)
        p=w.deliver('goblins_exploration.1');assert p[1]==tag and w.choose(p,0)
        w.day+=4*30;p=w.deliver('goblins_exploration.2');assert p[1]==tag
        assert 'location:lisbon' in w.countries[tag]['locations']
    return {'land_ratio_to_brackmaw':ratio,'land_pixels':pixels,'new_locations':22,
            'new_sea_tiles':sum(s.get('basin')=='giltfang' for s in cfg['coastal_sea']['zones']),
            'all_seas_connected_to_known_native_network':True,'ordinary_coastal_route':route,
            'coastal_tiles_without_movement_assistance':len(ordinary),'native_land_preserved':True,
            'reworked_current_tiles_with_connected_remnants':reworked,'other_native_sea_lanes_preserved':True,
            'cindermaw_outpost':'Lantern Cay',
            'mutual_starting_homeland_discovery':list(TAGS),'markets':['cm_hooktooth','cm_chainhaven'],
            'directed_harbor_service_cases':pairs,'giltfang_compact_roles':compacts,'successful_voyages':len(TAGS),'engine_tested':False}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--game',type=Path,required=True);a=p.parse_args()
    result=verify(a.out,a.game);print(json.dumps(result,indent=2))
    (b.ROOT/'build/reports/giltfang.json').write_text(json.dumps(result,indent=2)+'\n')
