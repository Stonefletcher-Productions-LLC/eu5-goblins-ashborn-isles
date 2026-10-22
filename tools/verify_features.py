"""Integration checks for geography, scenery, reciprocal contact and startup economy."""
import copy, re
import numpy as np
from PIL import Image
import archipelago, landscape


def verify(b,out,mapstats):
    cfg=b.CFG
    coastal={port['land'] for port in mapstats['ports']}
    capital_ranks={c['capital']:c['rank'] for c in cfg['countries']}
    for loc in cfg['locations']:
        rank=loc.get('rank',capital_ranks.get(loc['id'],'rural_settlement'))
        if rank in {'town','city','megalopolis'} and loc['id'] in coastal:
            assert loc['buildings'].get('wharf')==1,loc['id']
        if 'wharf' in loc['buildings']:
            assert loc['id'] in coastal,('inland wharf',loc['id'])
    counts={c['tag']:sum(l['country']==c['tag'] for l in cfg['locations']) for c in cfg['countries']}
    assert counts=={'CDM':33,'QBR':24,'RHK':8,'SFK':15,'SWK':4,'GTF':22},counts
    ratios={}
    for island in cfg['islands']:
        expected=np.pi*np.prod(cfg['radius'])*cfg['island_size_multiplier']*island['area_ratio']
        ratio=mapstats['island_pixels'][island['id']]/expected
        assert abs(ratio-1)<.015,(island['id'],'incorrect normalized area',ratio)
        ratios[island['id']]=round(ratio,4)
    from verify_geography import verify_geography
    geography=verify_geography(cfg)
    # Province seed/tag changes must leave the visual terrain unchanged.
    altered=copy.deepcopy(cfg);altered.pop('_landscape',None)
    for isl in altered['islands']:
        for loc in isl['locations']:loc['seed']=[100,100];loc['topography']='flatland';loc['vegetation']='desert'
    x,y=np.meshgrid(np.linspace(-280,230,75),np.linspace(-125,350,80))
    assert np.array_equal(landscape.heights(cfg,x,y),landscape.heights(altered,x,y))
    assert np.array_equal(landscape.material_indices(cfg,x,y),landscape.material_indices(altered,x,y))
    rivers=Image.open(out/'in_game/map_data/rivers.png');river_count=0
    for data in landscape.prepare(cfg):
        for path in data['rivers']:
            points=[(x+data['x0'],y+data['y0']) for y,x in path]
            assert rivers.getpixel(points[0])==0
            assert all(rivers.getpixel(p) in (3,4) for p in points[1:])
            assert all(abs(a[0]-c[0])+abs(a[1]-c[1])==1 for a,c in zip(points,points[1:]))
            assert len(points)>=9
            river_count+=1
    scenery_count=0
    for path in (out/'in_game/gfx/map/map_objects').glob('cm_ashborn_*.bin'):
        a=np.fromfile(path,dtype='<f4').reshape(-1,10)
        assert np.isfinite(a).all() and np.all(a[:,7:]>0)
        assert np.allclose(np.linalg.norm(a[:,3:7],axis=1),1,atol=1e-6)
        x=a[:,0]-cfg['center'][0];y=8192-a[:,2]-cfg['center'][1]
        assert np.all(archipelago.surface(cfg,x,y)>0),'Scenery placed outside land'
        scenery_count+=len(a)
    from exploration import ROUTES
    events=(out/'in_game/events/goblins_exploration.txt').read_text(encoding='utf-8-sig')
    for route in ROUTES.values():
        a,z=b.block_span(events,f'goblins_exploration.{route["event"]}')
        section=events[a:z]
        for location in route['locations']:
            la,lz=b.block_span(section,'location:'+location);contact=section[la:lz]
            assert 'exists = owner' in contact and 'owner = {' in contact
            assert 'discover_area = area:cm_cindermaw_area' in contact
            assert 'discover_area = area:cm_ashborn_seas_area' in contact
            assert 'NOT = { has_variable = ga_received_goblin_first_contact }' in contact
            assert 'NOT = { OR = {' in contact
            flag='set_variable = { name = ga_received_goblin_first_contact value = yes }'
            dispatch='trigger_event_non_silently = { id = goblins_exploration.6 }'
            assert flag in contact and dispatch in contact
            assert contact.index(flag)<contact.index(dispatch)
    economy=(out/'in_game/common/on_action/goblins_economy.txt').read_text(encoding='utf-8-sig')
    assert 'NOT = { has_variable = ga_economy_initialized }' in economy
    assert economy.count('change_max_raw_material_workers =')==len(cfg['locations'])
    assert sum(round(l['pop']*1000) for l in cfg['locations'])==cfg['population_target']
    return {'area_ratios_vs_target':ratios,'geography':geography,'location_counts':counts,'administrative_terrain_independence':True,
            'rivers':river_count,'validated_scenery_transforms':scenery_count,
            'reciprocal_routes_checked':list(ROUTES),'rgo_initialization_guard':True,
            'engine_tested':False}
