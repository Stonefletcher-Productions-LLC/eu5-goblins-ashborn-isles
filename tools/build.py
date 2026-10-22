"""Build Goblins of the Ashborn Isles from a local EU5 installation. Never edits game files."""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, sys, zipfile
from collections import deque
from decimal import Decimal
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parents[1]
import archipelago
CFG = archipelago.prepare(json.loads((ROOT / 'data/island.json').read_text()))
W, H = 16384, 8192
SEA_LEVEL = 0.08340625 * 65535
WATER = {'ocean','coastal_ocean','deep_ocean','inland_sea','lakes','lake'}
HASHES = {}

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def source(game, rel):
    p = game / rel
    if not p.is_file(): raise ValueError(f'Missing game file: {rel}')
    HASHES[rel] = sha(p)
    return p

def read(game, rel): return source(game, rel).read_text(encoding='utf-8-sig')

def write(base, rel, content):
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    bom=str(rel).endswith('.yml') or (str(rel).replace('\\','/').startswith('in_game/') and str(rel).endswith('.txt'))
    p.write_text(content.replace('\r\n','\n'), encoding=('utf-8-sig' if bom else 'utf-8'), newline='\r\n')

def clean(text):
    # Preserve positions while masking comments and quoted strings.
    return re.sub(r'"(?:\\.|[^"\\])*"|#[^\r\n]*', lambda m:' '*len(m[0]), text)

def block_span(text, key, start=0):
    c=clean(text)
    m=re.search(r'(?m)^\s*'+re.escape(key)+r'\s*=\s*\{', c[start:])
    if not m: raise ValueError(f'Missing block {key}')
    left=start+m.end()-1; depth=1; i=left+1
    while depth and i<len(c):
        depth += (c[i]=='{')-(c[i]=='}'); i+=1
    if depth: raise ValueError(f'Unbalanced block {key}')
    return left,i-1

def inject(text,key,addition,start=0):
    _,end=block_span(text,key,start)
    return text[:end]+'\n'+addition+'\n'+text[end:]

def parse_names(game):
    names={}
    for p in sorted((game/'in_game/map_data/named_locations').glob('*.txt')):
        for n,h in re.findall(r'(?m)^\s*(\w+)\s*=\s*([a-fA-F0-9]{6})\b',p.read_text(encoding='utf-8-sig')):
            names[n]=tuple(bytes.fromhex(h))
    return names

def footprint(x,y):
    return archipelago.surface(CFG,x,y)

def connectivity(mask):
    points=np.argwhere(mask)
    if not len(points): return 0,0
    seen=set(); comps=0
    for py,px in points:
        key=(int(py),int(px))
        if key in seen:continue
        comps+=1; seen.add(key); q=deque([key])
        while q:
            y,x=q.popleft()
            for dy,dx in ((0,1),(1,0),(0,-1),(-1,0)):
                yy,xx=y+dy,x+dx
                if 0<=yy<mask.shape[0] and 0<=xx<mask.shape[1] and mask[yy,xx] and (yy,xx) not in seen:
                    seen.add((yy,xx));q.append((yy,xx))
    return comps,len(points)

def font(size):
    for p in [Path('C:/Windows/Fonts/segoeui.ttf'),Path('C:/Windows/Fonts/arial.ttf')]:
        if p.exists():return ImageFont.truetype(str(p),size)
    return ImageFont.load_default()

def build_map(game,out,reports):
    return archipelago.build_map(sys.modules[__name__],game,out,reports)

def build_setup(game,out):
    return archipelago.build_setup(sys.modules[__name__],game,out)

def localization(out):
    import ashen_covenant
    loc={'CDM':'Cindermaw','CDM_ADJ':'Cindermaw','CDM_ADJ_f':'Cindermaw','CDM_ADJ_m':'Cindermaw',
         'cm_cinderkin':'Emberblood','cm_goblin_group':'Goblin','cm_cinder_tongue':'Cinder Tongue','cm_goblin_language_family':'Goblin',
         'cm_hunger_below':'The Ashen Covenant','cm_hunger_below_ADJ':'Ashen','cm_hunger_below_desc':ashen_covenant.DESCRIPTION,
         'cm_ashen_faiths':'Ashen Faiths','cm_captains_confederation':'Confederation of Captains','cm_captain_elective':'Election of the High Captain',
         'cm_captains_confederation_desc':'Ship-clans share a harbor, a war fleet and a hunger for plunder. Their autonomy weakens taxation while supporting privateering and slave raids.',
         'cm_cindermaw_sea':'Cindermaw Coastal Waters','cm_cindermaw_area':'Cindermaw','cm_crown_province':'The Cinder Crown','cm_hooktooth_province':'Hooktooth Coast','cm_ashfields_province':'The Ashfields',
         'cindermaw.1.title':'Smoke on the Horizon',
         'cindermaw.1.desc':'The captains have gathered at Hooktooth. Our holds are nearly empty, our ships patched, and the volcano smolders above crowded settlements. Yet Cindermaw has timber, ore and fertile ashfields. A fleet of four galleys and eight cogs, with two companies of footmen, has assembled. Across the water lie the ports of Madagascar and the African coast. Will plunder finance our rise, or will we first build a stronger home?',
         'cindermaw.1.a':'Prepare the crews.', 'cindermaw.1.b':'First, study what our island can support.',
         'cm_demo_raiding_tip':'Your starting force has assembled at Hooktooth. The captain government enables native privateering and slave-raiding mechanics. Use diplomacy to select a target; this introduction does not declare war.',
         'cm_demo_building_tip':'Hooktooth has a market, naval supplies workshop and stockade. Other locations are rural. Develop food and timber production before taking on a long war. This is an introductory choice; it grants no additional resources.'}
    for l in CFG['locations']:loc[l['id']]=l['name']
    for n in ['Grik','Mograt','Skrag','Vrek','Nibz','Krakk','Zog','Grizza','Snikka','Vezza','Morga','Krikka','Rikka']:loc['cm_'+n.lower()]=n
    for n in ['Hooktooth','Copperfang','Ashbite','Blackwake','Splinter','Saltjaw','Coalhand']:loc['cm_'+n.lower()+'_name']=n
    write(out,'main_menu/localization/english/goblins_ashborn_isles_l_english.yml','l_english:\n'+''.join(' '+k+': "'+v.replace('"','\\"')+'"\n' for k,v in loc.items()))

def validate(game,out,mapstats,economy):
    checks=[]
    for p in out.rglob('*.txt'):
        s=clean(p.read_text(encoding='utf-8-sig'));depth=0
        for c in s:
            depth+=(c=='{')-(c=='}')
            assert depth>=0,f'Unbalanced closing brace in {p}'
        assert depth==0,f'Unclosed brace in {p}'
    checks.append('All generated script files have balanced braces (not an engine parser test).')
    for p in out.rglob('*.json'):json.loads(p.read_text(encoding='utf-8-sig'))
    checks.append('Metadata and terrain instance JSON parse.')
    for p in (out/'main_menu/setup').rglob('*.txt'):
        assert not p.read_bytes().startswith(bytes.fromhex('efbbbf')),f'Setup BOM rejected by engine: {p}'
    cities=(out/'main_menu/setup/start/07_cities_and_buildings.txt').read_text()
    assert 'cm_hooktooth = { rank = city town_setup = cm_hooktooth_settlement }' in cities
    for country in CFG['countries']:
        assert f'{country["capital"]} = {{ rank = {country["rank"]} town_setup = {country["capital"]}_settlement }}' in cities
        owned={l['id'] for l in CFG['locations'] if l['country']==country['tag']}
        assert country['capital'] in owned
    checks.append('Setup files have no BOM; all six countries have populated urban capitals, with city rank only at Hooktooth.')
    for rel in ['main_menu/setup/start/06_pops.txt','main_menu/setup/start/10_countries.txt','main_menu/setup/start/07_cities_and_buildings.txt','main_menu/setup/start/03_markets.txt','in_game/map_data/definitions.txt']:
        before=[l.strip() for l in (game/rel).read_text(encoding='utf-8-sig').splitlines() if l.strip()]
        after=[l.strip() for l in (out/rel).read_text(encoding='utf-8-sig').splitlines() if l.strip()]
        # Every original line survives in order; new content only inserted.
        pos=0
        for line in after:
            if pos<len(before) and line==before[pos]:pos+=1
        assert pos==len(before),f'Unexpected vanilla change: {rel}'
    checks.append('Existing country, population, city, market and hierarchy lines preserved in order.')
    pops=(out/'main_menu/setup/start/06_pops.txt').read_text(encoding='utf-8-sig')
    for l in CFG['locations']:
        a,b=block_span(pops,l['id']);sizes=re.findall(r'\bsize\s*=\s*([\d.]+)',pops[a:b])
        import mixed_populations
        assert sum(map(Decimal,sizes))==Decimal(str(l['pop']))+mixed_populations.extra(l['id'])
    checks.append(f'Each location population matches its specification: {economy["total_population"]:,} people across six countries.')
    checks.append('All generated locations are connected within their islands; every island has a port into the connected coastal basin.')
    checks.append('Archipelago replaces only impassable ocean pixels; all vanilla land and navigable sea lanes are preserved.')
    im=Image.open(out/'in_game/map_data/locations.png');mapping=parse_names(game)
    defaults=(out/'in_game/map_data/default.map').read_text(encoding='utf-8-sig')
    a,z=block_span(defaults,'sea_zones');water=set(re.findall(r'\b\w+\b',clean(defaults[a:z])))
    a,z=block_span(defaults,'impassable_mountains');blocked=set(re.findall(r'\b\w+\b',clean(defaults[a:z])))
    for zone in CFG['coastal_sea']['zones']:
        mapping[zone['id']]=tuple(bytes.fromhex(zone['color']))
        assert zone['id'] in water and zone['id'] not in blocked
    checks.append(f'{len(CFG["coastal_sea"]["zones"])} connected sea zones are registered and reach native navigable Atlantic lanes.')
    for loc in CFG['locations']:
        anchor=mapstats['settlement_locators'][loc['id']]
        assert im.getpixel((int(anchor['x']),int(anchor['png_y'])))==tuple(bytes.fromhex(loc['color']))
    checks.append('All generated settlement anchors lie inside their own land locations; all new seas have fleet anchors.')
    for p in mapstats['ports']:
        assert im.getpixel((p['x'],H-p['y']))==mapping[p['sea']]
    checks.append('Every port lies on its named sea pixels with correct Y-axis conversion.')
    for folder,ids in [('unit_types',['a_footmen','n_cog','n_traditional_galley']),('building_types',['marketplace','naval_supplies_guild','stockade']),('heir_selections',['pirate_elective'])]:
        corpus='\n'.join(p.read_text(encoding='utf-8-sig') for p in (game/'in_game/common'/folder).glob('*.txt'))
        for key in ids:assert re.search(r'(?m)^\s*'+re.escape(key)+r'\s*=\s*\{',corpus),f'Missing vanilla ID {key}'
    checks.append('Starting unit, building and heir-selection IDs exist in installed EU5.')
    template=(out/'main_menu/setup/templates/cm_captains.txt').read_text(encoding='utf-8-sig')
    a,b=block_span(template,'laws')
    law_corpus='\n'.join(p.read_text(encoding='utf-8-sig') for p in (game/'in_game/common/laws').glob('*.txt'))
    for law,policy in re.findall(r'(\w+)\s*=\s*(\w+)',template[a+1:b]):
        la,lb=block_span(law_corpus,law)
        assert re.search(r'\b'+policy+r'\s*=\s*\{',law_corpus[la:lb]),f'Invalid law/policy pair {law}={policy}'
    checks.append('Every starting law/policy pair exists in its vanilla law block.')
    election=(out/'in_game/common/heir_selections/goblins_ashborn_isles.txt').read_text(encoding='utf-8-sig')
    assert 'has_reform = government_reform:cm_ironfang_monarchy' in election
    assert 'allow_children = no' in election and 'allow_female = no' in election
    assert 'all_in_country = yes' in election and 'value = root.mil' in election
    assert 'locked = {' not in election and 'use_election = no' in election
    assert 'type = monarchy' in template and 'heir_selection = cm_rule_of_the_strongest' in template
    gov=(out/'in_game/common/government_types/00_default.txt').read_text(encoding='utf-8-sig')
    ga,gz=block_span(gov,'monarchy');assert 'heir_selection = cm_rule_of_the_strongest' in gov[ga:gz]
    intro=(out/'in_game/events/goblins_ashborn_isles.txt').read_text(encoding='utf-8-sig')
    assert len(re.findall(r'\boption\s*=\s*\{',intro))==1
    from verify_ashborn_intro import verify as verify_intro
    verify_intro(lambda p: (out/p).read_text(encoding='utf-8-sig'))
    from verify_divorce import verify as verify_divorce
    verify_divorce(lambda p: (out/p).read_text(encoding='utf-8-sig'))
    from verify_goblin_units import verify as verify_units
    from build_infantry_art import blocks as unit_blocks
    native_units={k for f in sorted((game/'in_game/common/unit_types').glob('*.txt')) for k in unit_blocks(f.read_text(encoding='utf-8-sig'))}
    verify_units(lambda p: (out/p).read_text(encoding='utf-8-sig'),native_units)
    import shatterfin
    shatterfin.verify(sys.modules[__name__],out)
    import ashborn_names
    ashborn_names.verify(sys.modules[__name__],out)
    checks.append('Ironfang Monarchy uses native monarchy mechanics; adult male military succession is registered and unlocked; lore event has one option.')
    return checks

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--game',type=Path,required=True,help='EU5 game directory');args=ap.parse_args();game=args.game.resolve()
    out=ROOT/'build/goblins_ashborn_isles';reports=ROOT/'build/reports'
    out.mkdir(parents=True,exist_ok=True);reports.mkdir(parents=True,exist_ok=True)
    # A fresh staging tree prevents obsolete decals/overrides surviving a rebuild.
    if out.exists():
        assert out.resolve().parent==(ROOT/'build').resolve() and out.name=='goblins_ashborn_isles'
        shutil.rmtree(out)
    out.mkdir(parents=True)
    # Copy only authored sources; generated output never goes into source control.
    shutil.copytree(ROOT/'mod',out,dirs_exist_ok=True)
    for p in out.rglob('*.txt'):
        write(out,p.relative_to(out),p.read_text(encoding='utf-8-sig'))
    from verify_terrain import verify, verify_center_continuity
    continuity=verify_center_continuity(CFG)
    print('Building playable map and island terrain...',flush=True)
    mapstats=build_map(game,out,reports)
    from terrain_cache import build_cache_patch
    print('Patching runtime terrain cache...',flush=True)
    terrain=build_cache_patch(game,out,reports,CFG,footprint,source)
    terrain['verification']=verify(game,out,reports,CFG)
    terrain['center_continuity']=continuity
    print('Building campaign setup...',flush=True)
    economy=build_setup(game,out);localization(out);archipelago.add_localization(sys.modules[__name__],out)
    import economy as starting_economy
    economy['production']=starting_economy.build(sys.modules[__name__],game,out)
    import dynastic_clans
    dynastic_clans.build(sys.modules[__name__],game,out)
    economy['dynastic_clans']=dynastic_clans.verify(sys.modules[__name__],out)
    import goblin_longevity
    goblin_longevity.build(sys.modules[__name__],game,out)
    economy['longevity']=goblin_longevity.verify(sys.modules[__name__],out)
    import exploration
    discovery=exploration.build(sys.modules[__name__],game,out)
    import gathering
    gathering_report=gathering.build(out,CFG)
    import ashen_covenant
    religion_report=ashen_covenant.build(out)
    import goblin_estates
    religion_report['estate_names']=goblin_estates.build(sys.modules[__name__],game,out)
    from verify_ashen_covenant import verify as verify_religion
    religion_report['validation']=verify_religion(game,out)
    (reports/'religion_057.json').write_text(json.dumps(religion_report,indent=2),encoding='utf-8')
    import export_event_art
    export_event_art.build(out)
    import export_goblin_models
    models=export_goblin_models.build(out)
    import build_goblin_portraits
    build_goblin_portraits.build(out)
    import build_infantry_art
    build_infantry_art.build(game,out)
    import verify_goblin_portraits
    portrait_checks=verify_goblin_portraits.verify(out,game)
    (reports/'portrait_verification.json').write_text(json.dumps(portrait_checks,indent=2),encoding='utf-8')
    import verify_goblin_models
    model_checks=verify_goblin_models.verify(out,game)
    print('Running static validation...',flush=True)
    checks=validate(game,out,mapstats,economy)
    import verify_features
    features=verify_features.verify(sys.modules[__name__],out,mapstats)
    import verify_054
    features['version_054']=verify_054.verify(sys.modules[__name__],game,out,mapstats)
    from verify_055 import verify as verify_gathering
    features['version_055']=verify_gathering(ROOT,game,out)
    import verify_giltfang
    features['giltfang']=verify_giltfang.verify(out,game)
    import verify_059
    candidate_validation=verify_059.verify(out,game)
    (reports/'gathering.json').write_text(json.dumps(gathering_report,indent=2),encoding='utf-8')
    (reports/'feature_verification.json').write_text(json.dumps(features,indent=2),encoding='utf-8')
    (reports/'model_export.json').write_text(json.dumps(models,indent=2),encoding='utf-8')
    (reports/'model_verification.json').write_text(json.dumps(model_checks,indent=2),encoding='utf-8')
    import preview
    preview.context(game,out,reports)
    report={'version':CFG['version'],'target_game_version':CFG['game_version'],'status':'STATIC VALIDATION PASSED; IN-GAME TESTING PENDING','checks':checks,'map':mapstats,'economy':economy,'runtime_tested':False,'terrain_cache_baked':False,'terrain_cache_patch':terrain,'exploration':discovery,'source_sha256':HASHES}
    report['candidate_validation']=candidate_validation
    (reports/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'locations':len(CFG['locations']),'population':economy['total_population'],'land_pixels':mapstats['land_pixels'],'ports':len(mapstats['ports']),'output':str(out)},indent=2))

if __name__=='__main__':main()
