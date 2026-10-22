"""Validate the source-download installer bundle without a local build or EU5."""
import base64, hashlib, io, json, re, zipfile
from decimal import Decimal
from datetime import date
from pathlib import Path

def verify(root):
    root=Path(root)
    source=(root/'data/island.json').read_text(encoding='utf-8')
    config=json.loads(source)
    release=json.loads((root/'.release/manifest.json').read_text())
    overlay=json.loads((root/'data/main_overlay.json').read_text())
    version=config['version']
    assert version==release['version']==overlay['base_release'],'Source, bundle and overlay versions differ'
    digest=lambda b:hashlib.sha256(b).hexdigest()
    assert digest(source.encode())==release['source_config_sha256'],'Stale source configuration hash'
    asset=next(a for a in release['assets'] if a['name']==f'Goblins_Ashborn_Isles_{version}.zip')
    chunks=[]
    for path in asset['chunks']:
        assert re.fullmatch(r'assets/[A-Za-z0-9_.-]+',path),path
        chunks.append(base64.b64decode((root/'.release'/path).read_bytes(),validate=True))
    raw=b''.join(chunks)
    assert len(raw)==asset['size'] and digest(raw)==asset['sha256'],'Corrupt archive transport'
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert len(z.namelist())==len(set(z.namelist())),'Duplicate archive members'
        assert z.testzip() is None,'ZIP CRC failure'
        if tuple(map(int, version.split('.'))) >= (0, 5, 9):
            allowed = {'README.md','RELEASE_NOTES.md','TESTING.md','LORE.md','Install-Goblins.ps1','Install-Goblins.cmd','reports/validation.json'}
            assert all(n.startswith(('goblins_ashborn_isles/', 'terrain_patch/')) or n in allowed for n in z.namelist()), 'Development content in player archive'
        metadata=json.loads(z.read('goblins_ashborn_isles/.metadata/metadata.json'))
        terrain=json.loads(z.read('terrain_patch/manifest.json'))
        report=json.loads(z.read('reports/validation.json'))
        assert version==metadata['version']==terrain['version']==report['version'],'Stale packaged metadata or terrain'
        assert metadata['id']=='alex.goblins_ashborn_isles'
        assert z.read('Install-Goblins.ps1').decode('utf-8-sig').replace('\r\n','\n')==(root/'Install-Goblins.ps1').read_text(encoding='utf-8-sig'),'Stale embedded installer'
        assert len(terrain['files'])==3
        for item in terrain['files']:
            assert item['final_size']>item['source_size']
            assert len(z.read('terrain_patch/'+item['delta']))==item['final_size']-item['source_size']
            assert z.read('goblins_ashborn_isles/'+str(Path(item['path']).with_suffix('.info')).replace('\\','/'))
        for name in ['10_countries.txt','06_pops.txt','07_cities_and_buildings.txt','03_markets.txt']:
            assert z.read('goblins_ashborn_isles/main_menu/setup/start/'+name)
        if tuple(map(int, version.split('.'))) >= (0, 6, 4, 1):
            # An empty trailing row logged "Unknown reference to location! Key: ''".
            ports=z.read('goblins_ashborn_isles/in_game/map_data/ports.csv')
            assert b'\r' not in ports and not ports.endswith(b'\n'),'ports.csv must match native LF/no-trailing-newline format'
            assert all(row and len(row.split(b';'))==5 for row in ports.split(b'\n')),'Empty or malformed ports.csv row'
        if tuple(map(int, version.split('.'))) >= (0, 6, 5):
            # 'tar' has no raw-material RGO in EU5 1.3.11; such locations could not be built up.
            templates=z.read('goblins_ashborn_isles/in_game/map_data/location_templates.txt').decode('utf-8-sig')
            assert 'raw_material = tar' not in templates,'A location uses tar as its raw material'
            for island in config['islands']:
                for location in island['locations']:
                    row=re.search(r'(?m)^'+re.escape(location['id'])+r' = \{[^\n]*\braw_material = (\w+)\b',templates)
                    assert row and row[1]==location['good'],f'Stale packaged raw material: {location["id"]}'
            # Fish needs water: Netjaw (inland) produced fish until 0.6.6. Every goblin
            # location that touches sea has a ports.csv row (archipelago.build_map).
            coastal={row.split(b';')[0].decode() for row in z.read('goblins_ashborn_isles/in_game/map_data/ports.csv').split(b'\n')}
            for island in config['islands']:
                for location in island['locations']:
                    assert location['good']!='fish' or location['id'] in coastal,f'Inland location produces fish: {location["id"]}'
        if tuple(map(int, version.split('.'))) >= (0, 6, 6):
            # Provinces share food; a lone non-food location (Silver Shard) starved.
            definitions=z.read('goblins_ashborn_isles/in_game/map_data/definitions.txt').decode('utf-8-sig')
            provinces={}
            for island in config['islands']:
                for location in island['locations']:
                    provinces.setdefault(location['province'],set()).add(location['id'])
            for province,members in provinces.items():
                row=re.search(r'(?m)^'+re.escape(province)+r' = \{([^}\n]*)\}',definitions)
                assert row and set(row[1].split())==members,f'Stale packaged province: {province}'
            # Goblin unique units (Obsidian Fletchers) ship from 0.6.6.
            from verify_goblin_units import verify as verify_units
            verify_units(lambda p:z.read('goblins_ashborn_isles/'+p).decode('utf-8-sig'))
        # Configuration binding alone cannot catch a stale generated treasury.
        country_setup=z.read('goblins_ashborn_isles/main_menu/setup/start/10_countries.txt').decode('utf-8-sig')
        starting_gold={}
        for country in config['countries']:
            tag=country['tag']
            match=re.search(r'(?m)^\s*'+re.escape(tag)+r'\s*=\s*\{',country_setup)
            assert match,tag
            depth=1;end=match.end()
            while depth:
                depth+=(country_setup[end]=='{')-(country_setup[end]=='}');end+=1
            body=country_setup[match.end():end]
            currency=re.search(r'\bcurrency_data\s*=\s*\{([^{}]*)\}',body)
            assert currency,tag
            amount=re.search(r'\bgold\s*=\s*(-?[\d.]+)',currency[1])
            assert amount and Decimal(amount[1])==Decimal(str(country['gold'])),f'Stale starting gold: {tag}'
            starting_gold[tag]=country['gold']
        assert report['economy']['starting_gold']==starting_gold,'Stale treasury validation report'
        if tuple(map(int, version.split('.'))) >= (0, 5, 7):
            # Verify new features in delivered bytes, not only their source files.
            events=z.read('goblins_ashborn_isles/in_game/events/goblins_gathering.txt').decode('utf-8-sig')
            dispatches=events+z.read('goblins_ashborn_isles/in_game/common/generic_actions/goblins_gathering.txt').decode('utf-8-sig')
            for number in [17, 18, 20, 21, 22, 23, 24, 25, 30, 31, 32, 33, 34, 35]:
                assert f'trigger_event_non_silently = ga_gathering.{number}' in dispatches
            ai=z.read('goblins_ashborn_isles/in_game/common/generic_action_ai_lists/goblins_gathering.txt').decode('utf-8-sig')
            if tuple(map(int, version.split('.'))) >= (0, 5, 9):
                from verify_script_registration import verify as verify_scripts
                verify_scripts(lambda p:z.read('goblins_ashborn_isles/'+p).decode('utf-8-sig'))
                from verify_ashborn_intro import verify as verify_intro
                verify_intro(lambda p:z.read('goblins_ashborn_isles/'+p).decode('utf-8-sig'))
                from verify_divorce import verify as verify_divorce
                verify_divorce(lambda p:z.read('goblins_ashborn_isles/'+p).decode('utf-8-sig'))
                # The Old World Reacts first ships in 0.6.7; earlier bundles carry only part of it.
                if tuple(map(int, version.split('.'))) >= (0, 6, 7):
                    from verify_old_world import verify as verify_old_world
                    verify_old_world(lambda p:z.read('goblins_ashborn_isles/'+p).decode('utf-8-sig'))
                from verify_harbor_bargains import verify as verify_bargains
                verify_bargains(lambda p:z.read('goblins_ashborn_isles/'+p).decode('utf-8-sig'))
                from verify_compact_talks import verify as verify_compact
                verify_compact(lambda p:z.read('goblins_ashborn_isles/'+p).decode('utf-8-sig'))
                from verify_situation_progress import verify as verify_progress
                verify_progress(lambda p:z.read('goblins_ashborn_isles/'+p).decode('utf-8-sig'))
                from verify_early_projects import verify as verify_projects
                verify_projects(lambda p:z.read('goblins_ashborn_isles/'+p).decode('utf-8-sig'))
                from verify_covenant_stories import verify as verify_stories
                verify_stories(lambda p:z.read('goblins_ashborn_isles/'+p).decode('utf-8-sig'))
                from verify_exploration_progress import verify as verify_voyages
                verify_voyages(lambda p:z.read('goblins_ashborn_isles/'+p).decode('utf-8-sig'))
                from verify_combined_candidate import verify as verify_combined
                verify_combined(lambda p:z.read('goblins_ashborn_isles/'+p).decode('utf-8-sig'))
            else:
                assert 'ga_offer_harbor_pact' not in ai
            assert z.read('goblins_ashborn_isles/in_game/events/ashen_covenant.txt')
            estates=z.read('goblins_ashborn_isles/in_game/common/customizable_localization/estates.txt').decode('utf-8-sig')
            assert 'localization_key = ga_crown_estate' in estates
        if 'country_population_targets' in config:
            # Check the delivered setup, not merely the manifest's claimed config hash.
            pops=z.read('goblins_ashborn_isles/main_menu/setup/start/06_pops.txt').decode('utf-8-sig')
            import mixed_populations
            actual={tag:0 for tag in config['country_population_targets']}
            expected=dict(config['country_population_targets'])
            for island in config['islands']:
                for location in island['locations']:
                    start=re.search(r'(?m)^\s*'+re.escape(location['id'])+r'\s*=\s*\{',pops)
                    assert start,location['id']
                    depth=1;end=start.end()
                    while depth:
                        depth+=(pops[end]=='{')-(pops[end]=='}');end+=1
                    n=sum(Decimal(v) for v in re.findall(r'\bsize\s*=\s*([\d.]+)',pops[start.end():end]))
                    assert n==Decimal(str(location['pop']))+mixed_populations.extra(location['id']),f'Stale packaged population: {location["id"]}'
                    actual[island['country']]+=int(n*1000)
                    expected[island['country']]+=int(mixed_populations.extra(location['id'])*1000)
            assert actual==expected==report['economy']['country_populations']
            assert sum(actual.values())==sum(expected.values())
            assert report['economy']['longevity']['goblin_character_life_expectancy_bonus_years']==15
            assert report['economy']['longevity']['starting_ruler_ages']==config['starting_ruler_ages']
            chars=z.read('goblins_ashborn_isles/main_menu/setup/start/05_characters.txt').decode('utf-8-sig')
            now=date(1337,11,11)
            for tag,expected in config['starting_ruler_ages'].items():
                ident='cm_sfk_maarka' if tag=='SFK' else 'cm_'+tag.lower()+'_ruler'
                row=re.search(r'(?m)^\s*'+ident+r'\s*=\s*\{[^\r\n]+',chars)
                assert row,ident
                born=date(*map(int,re.search(r'birth_date = ([\d.]+)',row[0])[1].split('.')))
                age=now.year-born.year-((now.month,now.day)<(born.month,born.day))
                assert age==expected,f'Stale packaged ruler age: {tag}'
        for item in overlay['files']:
            path=item['path']
            assert re.fullmatch(r'[A-Za-z0-9_./-]+',path) and '..' not in Path(path).parts and not path.startswith('/')
            authored=(root/'mod'/path).read_bytes()
            assert digest(authored)==item['sha256'],f'Overlay checksum mismatch: {path}'
            assert z.read('goblins_ashborn_isles/'+path)==authored,f'Stale bundled art: {path}'
        if (root/'data/prototype_055_files.json').is_file():
            prototype=json.loads((root/'data/prototype_055_files.json').read_text())
            for item in prototype['files']:
                path=item['path']
                assert z.read('goblins_ashborn_isles/'+path)==(root/'mod'/path).read_bytes(),f'Stale or missing Gathering content: {path}'
            for name in ['README.md','RELEASE_NOTES.md','TESTING.md','LORE.md']:
                packed=z.read(name);authored=(root/('PLAYER_README.md' if name == 'README.md' and tuple(map(int, version.split('.'))) >= (0, 5, 9) else name)).read_bytes()
                if name.endswith(('.md','.txt')):
                    packed=packed.decode('utf-8-sig').replace('\r\n','\n')
                    authored=authored.decode('utf-8-sig').replace('\r\n','\n')
                assert packed==authored,f'Stale packaged guide: {name}'
    return {'version':version,'overlay_files':len(overlay['files']),'archive_bytes':len(raw),'status':'prepared bundle verified'}

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);args=ap.parse_args()
    print(json.dumps(verify(args.root),indent=2))
