"""Package generated output and authored sources; do not install or publish."""
from pathlib import Path
import argparse,json,zipfile
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source",action="store_true",help="Also create a standalone source ZIP (Git downloads already provide source).")
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1]
version=json.loads((ROOT/'data/island.json').read_text())['version']
report=ROOT/'build/reports/validation.json'
if not report.is_file():raise SystemExit('Run build.py successfully first.')
checks=json.loads(report.read_text())
if checks['version']!=version:raise SystemExit('Rebuild before packaging this version.')
output=ROOT/'build/goblins_ashborn_isles'
metadata=json.loads((output/'.metadata/metadata.json').read_text())
if metadata['id']!='alex.goblins_ashborn_isles' or metadata['version']!=version:
    raise SystemExit('Metadata version mismatch: rebuild first.')
decal=output/'in_game/gfx/terrain2/decals/ga_ashborn_isles'
if not all((decal/f'ga_ashborn_isles_{n}').is_file() for n in ['height.bin','height.info','materials.bin','materials.info']):
    raise SystemExit('Incomplete terrain build.')
if (output/'in_game/gfx/terrain2/terrain_cache/heightmap.bin').exists():
    raise SystemExit('Stale pre-1.4 terrain cache in build output.')
for filename in ['10_countries.txt','06_pops.txt','07_cities_and_buildings.txt','03_markets.txt']:
    if not (output/'main_menu/setup/1337'/filename).is_file():raise SystemExit('Incomplete campaign setup.')
dist=ROOT/'dist';dist.mkdir(exist_ok=True)
docs=['README.md','RELEASE_NOTES.md','TESTING.md','LORE.md','Install-Goblins.ps1','Install-Goblins.cmd']
with zipfile.ZipFile(dist/f'Goblins_Ashborn_Isles_{version}.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted((ROOT/'build/goblins_ashborn_isles').rglob('*')):
        if p.is_file():z.write(p,'goblins_ashborn_isles/'+p.relative_to(ROOT/'build/goblins_ashborn_isles').as_posix())
    for name in docs:z.write(ROOT/('PLAYER_README.md' if name == 'README.md' else name),name)
    # Only the machine-readable validation receipt accompanies the runtime.
    z.write(report, 'reports/validation.json')
if args.source:
    with zipfile.ZipFile(dist/f'Goblins_Ashborn_Isles_Source_{version}.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in docs+['PLAYER_README.md','requirements.txt','.gitignore','.gitattributes']:z.write(ROOT/name,'goblins-ashborn-isles-source/'+name)
        for folder in ['data','mod','tools','art','.github']:
            for p in sorted((ROOT/folder).rglob('*')):
                if p.is_file() and '__pycache__' not in p.parts:z.write(p,'goblins-ashborn-isles-source/'+p.relative_to(ROOT).as_posix())
for p in dist.iterdir():print(f'{p.name}: {p.stat().st_size:,} bytes')
