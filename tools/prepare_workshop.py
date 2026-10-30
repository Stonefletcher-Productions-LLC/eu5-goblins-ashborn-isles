"""Stage the FULL built mod for Workshop. Does not install or publish anything."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def main():
    source = ROOT / 'build/goblins_ashborn_isles'
    reports = ROOT / 'build/reports'
    require((reports / 'validation.json').is_file(), 'Run tools/build.py successfully first.')
    config = read(ROOT / 'data/island.json')
    version = config['version']
    validation = read(reports / 'validation.json')
    metadata = read(source / '.metadata/metadata.json')
    require(version == validation['version'] == metadata['version'],
            'Source/build/metadata versions differ. Rebuild before staging.')
    require(metadata['id'] == 'alex.goblins_ashborn_isles' and metadata['game_id'] == 'eu5',
            'Unexpected mod identity.')
    require(metadata['supported_game_version'] == validation['target_game_version'],
            'Supported game version differs from validated build.')
    require('STATIC VALIDATION PASSED' in validation['status'], 'Static build validation did not pass.')
    for name in ('feature_verification.json', 'terrain_verification.json',
                 'portrait_verification.json', 'model_verification.json'):
        require((reports / name).is_file(), f'Missing build report: {name}')
    # Source changes after the successful validation require another full build.
    built_at = (reports / 'validation.json').stat().st_mtime_ns
    for folder in ('mod', 'data', 'tools', 'art/models/goblins'):
        for path in (ROOT / folder).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.name != 'prepare_workshop.py':
                require(path.stat().st_mtime_ns <= built_at, f'Source changed after build: {path}. Rebuild.')
    thumbnail = source / '.metadata/thumbnail.png'
    with Image.open(thumbnail) as image:
        require(image.format == 'PNG' and image.size == (512, 512), 'Expected a 512 x 512 PNG thumbnail.')
        image.verify()
    require(sha(thumbnail) == sha(ROOT / 'mod/.metadata/thumbnail.png'), 'Thumbnail differs from source.')
    decal = source / 'in_game/gfx/terrain2/decals/ga_ashborn_isles'
    for name in ('height.bin', 'height.info', 'materials.bin', 'materials.info'):
        require((decal / f'ga_ashborn_isles_{name}').is_file(), f'Missing island terrain decal: {name}')
    require(not (source / 'in_game/gfx/terrain2/terrain_cache/heightmap.bin').exists(),
            'Stale pre-1.4 terrain cache in build output. Rebuild.')
    for name in ('10_countries.txt', '06_pops.txt', '07_cities_and_buildings.txt', '03_markets.txt'):
        require((source / 'main_menu/setup/1337' / name).is_file(), f'Missing generated setup: {name}')
    require((source / 'in_game/map_data/locations.png').is_file(), 'Missing generated map.')
    # Fresh output only: never silently replace a previously reviewed candidate.
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    package = ROOT / 'dist' / f'Workshop_{version}_{stamp}'
    target = package / 'goblins_ashborn_isles'
    shutil.copytree(source, target)
    files = []
    for path in sorted(source.rglob('*')):
        if path.is_file():
            rel = path.relative_to(source)
            digest = sha(path)
            require(digest == sha(target / rel), f'Copy verification failed: {rel}')
            files.append({'path': rel.as_posix(), 'bytes': path.stat().st_size, 'sha256': digest})
    shutil.copy2(ROOT / 'STEAM_DESCRIPTION.txt', package / 'STEAM_DESCRIPTION.txt')
    shutil.copy2(ROOT / 'WORKSHOP_UPLOAD.md', package / 'WORKSHOP_UPLOAD.md')
    shutil.copytree(reports, package / 'reports')
    result = {'version': version, 'game_version': metadata['supported_game_version'],
              'status': 'UPLOAD STRUCTURE VERIFIED; IN-GAME ACCEPTANCE PENDING',
              'runtime_tested': validation.get('runtime_tested', False),
              'upload_folder': str(target), 'thumbnail': '.metadata/thumbnail.png',
              'file_count': len(files), 'total_bytes': sum(f['bytes'] for f in files), 'files': files}
    (package / 'workshop_manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))


if __name__ == '__main__':
    main()
