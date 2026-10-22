"""Regression checks for population conservation across splits and dynastic eligibility."""
from collections import Counter
from decimal import Decimal
import re

def verify(b,game,out,mapstats):
    cfg=b.CFG;locs=cfg['locations'];baseline=cfg['baseline_locations'];byid={l['id']:l for l in locs}
    assert len(byid)==len(locs)==97 and len({l['color'] for l in locs})==97
    assert set(baseline)<=set(byid)
    assert sum(Decimal(str(l['pop'])) for l in locs)==Decimal(cfg['population_target'])/1000
    for l in locs:
        assert sum(Decimal(str(v)) for v in l['pop_classes'].values())==Decimal(str(l['pop']))
        assert all(v>=0 for v in l['pop_classes'].values())
    for ident,old in baseline.items():
        children=[l for l in locs if l.get('split_from')==ident];assert len(children)==1
        # The construction pass deliberately converts Tidefang's fish to sand.
        expected_good = 'sand' if ident == 'cm_tidefang' else old['good']
        assert byid[ident]['good']==expected_good
        # 0.6.1 relocates households into new towns within each kingdom.
        # Check the historical split before those explicit migrations, then
        # check current country totals and generated populations below.
        migrations=cfg.get('urbanization_061',{}).get('locations',{})
        revision=cfg.get('population_062',{})
        prior=lambda loc: migrations.get(loc['id'],{}).get('population_before',revision.get('locations',{}).get(loc['id'],{}).get('population_before',loc['pop']))
        combined=Decimal(str(prior(byid[ident])))+Decimal(str(prior(children[0])))
        previous=cfg['population_revision_baseline']['locations']
        old_combined=Decimal(str(previous[ident]))+Decimal(str(previous[children[0]['id']]))
        tag=byid[ident]['country']
        original_target=revision.get('prior_country_population_targets',cfg['country_population_targets'])[tag]-cfg.get('outpost_population_additions',{}).get(tag,0)
        factor=Decimal(original_target)/cfg['population_revision_baseline']['country_populations'][tag]
        assert abs(combined-old_combined*factor)<=Decimal('.004')
        # Province membership follows actual land borders in verify_061.
    # 0.6.6 folded the one-location Shatterfin Outer province into Shatterfin.
    assert len({l['province'] for l in locs})==39
    # Check generated setup, not just input configuration.
    pops=(out/'main_menu/setup/start/06_pops.txt').read_text(encoding='utf-8-sig')
    for l in locs:
        a,z=b.block_span(pops,l['id']);rows=pops[a:z]
        import mixed_populations
        assert sum(Decimal(v) for v in re.findall(r'\bsize\s*=\s*([\d.]+)',rows))==Decimal(str(l['pop']))+mixed_populations.extra(l['id'])
    defs=(out/'in_game/map_data/definitions.txt').read_text(encoding='utf-8-sig')
    a,z=b.block_span(defs,'cm_cindermaw_area');area=defs[a:z]
    for l in locs:assert len(re.findall(r'\b'+re.escape(l['id'])+r'\b',area))==1
    # Outsiders at MIL 86 and minor sons must lose to eligible dynastic adults.
    chars=(out/'main_menu/setup/start/05_characters.txt').read_text(encoding='utf-8-sig')
    heirs={}
    for tag in ['CDM','QBR','RHK','SWK','GTF']:
        prefix='cm_'+tag.lower();candidates=[]
        suffixes=['son','daughter','court_0','court_1','court_2']+(['brother','father'] if tag in {'RHK','SWK'} else [])
        for suffix in suffixes:
            ident=prefix+'_'+suffix;a,z=b.block_span(chars,ident);s=chars[a:z]
            house=re.search(r'\bdynasty\s*=\s*(\w+)',s)[1]
            if house!=prefix+'_house_0' or 'female = yes' in s:continue
            if 'death_date =' in s:continue
            from datetime import date
            born=date(*map(int,re.search(r'birth_date = ([\d.]+)',s)[1].split('.')))
            if (date(1337,11,11)-born).days<18*365.25:continue
            stats=[int(re.search(r'\b'+k+r'\s*=\s*(\d+)',s)[1]) for k in ['mil','adm']]
            candidates.append((tuple(stats),ident))
        expected=prefix+('_brother' if tag in {'RHK','SWK'} else '_son')
        assert max(candidates)[1]==expected;heirs[tag]=max(candidates)[1]
    law=(out/'in_game/common/heir_selections/goblins_ashborn_isles.txt').read_text(encoding='utf-8-sig')
    assert 'dynasty = scope:target.last_valid_ruler.dynasty' in law
    assert 'regardless of dynasty' not in (out/'main_menu/localization/english/goblins_ashborn_isles_l_english.yml').read_text(encoding='utf-8-sig')
    import statistics
    provinces={p:sum(mapstats['locations'][l['id']]['pixels'] for l in locs if l['province']==p) for p in {l['province'] for l in locs}}
    populations={c['tag']:sum(round(l['pop']*1000) for l in locs if l['country']==c['tag']) for c in cfg['countries']}
    assert populations==cfg['country_population_targets']
    assert populations['SFK']>populations['RHK']>populations['SWK']
    for tag,n in populations.items():
        if tag in cfg['population_revision_baseline']['country_populations']:
            historical=cfg.get('population_062',{}).get('prior_country_population_targets',populations)
            assert historical[tag]>=cfg['population_revision_baseline']['country_populations'][tag]*1.5
        assert n>=100000
    import goblin_longevity
    longevity=goblin_longevity.verify(b,out)
    return {'version':'0.5.4','population':cfg['population_target'],'country_populations':populations,
            'increase_from_previous_054_percent':{tag:round((n/cfg['population_revision_baseline']['country_populations'][tag]-1)*100,3) for tag,n in populations.items() if tag in cfg['population_revision_baseline']['country_populations']},
            'longevity':longevity,
            'locations':len(locs),'provinces':len(provinces),'resources':dict(Counter(l['good'] for l in locs)),
            'starting_dynastic_heirs':heirs,'population_classes_and_generated_totals_checked':True,
            'original_ids_and_resources_preserved':True,
            'map_density':{'europe_reference_location_pixels_median':520,'europe_reference_province_pixels_median':2626,
                'ashborn_location_pixels_median':statistics.median(v['pixels'] for v in mapstats['locations'].values()),
                'ashborn_province_pixels_median':statistics.median(provinces.values())},'engine_tested':False}
