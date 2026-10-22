"""Check actual event coverage, native-size DDS decoding, and shipped art hashes."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from PIL import Image
from event_art import ROOT, ART, EVENTS, SITUATIONS, image, runtime_paths
from verify_055 import parse


def verify(out, check_manifest=True):
    found = {}
    for path in sorted((out / 'in_game/events').glob('*.txt')):
        if not (path.name.startswith('goblins_') or path.name == 'ashen_covenant.txt'):
            continue
        assert path.read_bytes().startswith(b'\xef\xbb\xbf'), path
        for key, _, fields in parse(path.read_text(encoding='utf-8-sig')):
            if key == 'namespace':
                continue
            assert key not in found, f'Duplicate event: {key}'
            found[key] = fields
    assert set(found) == set(EVENTS), f'Uncovered or obsolete events: {set(found) ^ set(EVENTS)}'
    for key, fields in found.items():
        refs = [value.strip('"') for field, _, value in fields if field == 'image']
        assert refs == [image(key)], f'Missing or wrong explicit art: {key}'
        assert not any(field == 'illustration_tags' for field, _, _ in fields), key
    situations = parse((out / 'in_game/common/situations/goblins_gathering.txt').read_text(encoding='utf-8-sig'))
    situations += parse((out / 'in_game/common/situations/goblins_voyages.txt').read_text(encoding='utf-8-sig'))
    situations += parse((out / 'in_game/common/situations/goblins_mainland.txt').read_text(encoding='utf-8-sig'))
    assert {key for key, _, _ in situations} == set(SITUATIONS), 'Situation art coverage differs'
    for rel in runtime_paths():
        path = out / rel
        raw = path.read_bytes()
        assert raw[:4] == b'DDS ' and raw[84:88] == b'DXT1', path
        height, width = struct.unpack_from('<II', raw, 12)
        expected = (128, 128) if '/icons/' in rel else (1080, 440)
        assert (width, height) == expected, path
        levels = struct.unpack_from('<I', raw, 28)[0]
        assert levels == max(width, height).bit_length(), f'Incomplete mip chain: {path}'
        size = 128
        for _ in range(levels):
            size += ((width + 3) // 4) * ((height + 3) // 4) * 8
            width, height = max(1, width // 2), max(1, height // 2)
        assert len(raw) == size, f'Truncated DDS: {path}'
        with Image.open(path) as decoded:
            decoded.load()
            assert decoded.size == expected
    prompts = json.loads((ROOT / 'art/events/prompts.json').read_text(encoding='utf-8'))
    assert set(prompts['paintings']) == set(ART), 'Missing generation provenance'
    for name in ART:
        source = ROOT / 'art/events/sources' / (name + '.png')
        row = prompts['paintings'][name]
        assert row['prompt'] and row['sha256'] == hashlib.sha256(source.read_bytes()).hexdigest(), name
    export = json.loads((ROOT / 'art/events/exports.json').read_text(encoding='utf-8'))
    assert {row['path'] for row in export['files']} == set(runtime_paths())
    for row in export['files']:
        assert row['sha256'] == hashlib.sha256((out / row['path']).read_bytes()).hexdigest(), row['path']
    if check_manifest:
        manifest = json.loads((ROOT / 'data/prototype_055_files.json').read_text(encoding='utf-8'))
        shipped = {row['path']: row['sha256'] for row in manifest['files']}
        required = runtime_paths() + ['in_game/events/goblins_gathering.txt',
            'in_game/events/goblins_exploration.txt', 'in_game/events/goblins_ashborn_isles.txt']
        for rel in required:
            assert shipped.get(rel) == hashlib.sha256((out / rel).read_bytes()).hexdigest(), f'Unshipped art/script: {rel}'
    return {'events_with_explicit_custom_art': len(found), 'situations_with_custom_art_and_icons': len(SITUATIONS),
            'original_paintings': len(ART), 'decoded_dds_textures': len(runtime_paths()),
            'prototype_manifest_checked': check_manifest, 'engine_render_tested': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT / 'mod')
    args = parser.parse_args()
    print(json.dumps(verify(args.out), indent=2))
