"""Check country flags, transparent emblem exports and delivery hashes."""
from pathlib import Path
import argparse, hashlib, json, re, struct
from PIL import Image
from build_clan_flags import ROOT, FLAGS, COATS, TEXTURES, runtime_paths
from verify_055 import parse


def verify(out, game=None):
    text = (out / COATS).read_text(encoding='utf-8-sig')
    # The existing script parser does not consume typed RGB literals.
    coats = parse(re.sub(r'=\s*rgb\s*\{', '= {', text))
    assert len(coats) == len(FLAGS) and {key for key, _, _ in coats} == set(FLAGS), 'Missing/duplicate country arms'
    manifest = json.loads((ROOT / 'data/prototype_055_files.json').read_text(encoding='utf-8'))
    shipped = {row['path']: row['sha256'] for row in manifest['files']}
    for tag, _, fields in coats:
        fields = {key: value for key, _, value in fields}
        assert fields['pattern'] == '"pattern_solid.dds"'
        assert [int(key) for key, _, _ in fields['color1']] == FLAGS[tag]['field']
        emblem = {key: value for key, _, value in fields['textured_emblem']}
        texture = 'te_ashborn_' + FLAGS[tag]['source'] + '.dds'
        assert emblem['texture'] == '"' + texture + '"'
        path = out / TEXTURES / texture
        raw = path.read_bytes()
        assert raw[:4] == b'DDS ' and raw[84:88] == b'DXT5'
        assert struct.unpack_from('<II', raw, 12) == (256, 384)
        assert struct.unpack_from('<I', raw, 28)[0] == 9
        width, height, size = 384, 256, 128
        for _ in range(9):
            size += ((width + 3) // 4) * ((height + 3) // 4) * 16
            width, height = max(1, width // 2), max(1, height // 2)
        assert len(raw) == size, 'Truncated emblem mip chain'
        with Image.open(path) as im:
            im.load()
            assert im.mode == 'RGBA' and im.size == (384, 256)
            hist = im.getchannel('A').histogram()
            assert hist[0] > 384 * 256 * .5 and hist[255] > 384 * 256 * .03, 'Lost transparency or emblem'
        assert (ROOT / 'art/flags/sources' / (FLAGS[tag]['source'] + '.svg')).is_file()
    for rel in runtime_paths():
        assert shipped.get(rel) == hashlib.sha256((out / rel).read_bytes()).hexdigest(), 'Stale flag manifest: ' + rel
    # Valid textures alone do not bind a country's flag: the old setup omitted
    # these assignments and the engine displayed procedural flags instead.
    setup_path = out / 'main_menu/setup/1337/10_countries.txt'
    if setup_path.exists():
        from build import block_span
        setup = setup_path.read_text(encoding='utf-8-sig')
        for tag in FLAGS:
            left, right = block_span(setup, tag)
            assert re.search(r'(?m)^\s*flag\s*=\s*"'+tag+r'"\s*$', setup[left:right]), 'Unbound starting flag: '+tag
    actions = dict((key, value) for key, _, value in parse((out / 'in_game/common/on_action/goblins_gathering.txt').read_text(encoding='utf-8-sig')))
    pulse = dict((key, value) for key, _, value in actions['monthly_country_pulse'])
    assert ('ga_clan_flags_060_pulse', None, None) in pulse['on_actions']
    repair = dict((key, value) for key, _, value in actions['ga_clan_flags_060_pulse'])
    assert repair['trigger'] == [('OR', '=', [('tag', '=', tag) for tag in FLAGS]),
                                 ('NOT', '=', [('has_variable', '=', 'ga_clan_flags_060_applied')])]
    assert repair['effect'] == [('if', '=', [('limit', '=', [('tag', '=', tag)]), ('change_country_flag', '=', tag)]) for tag in FLAGS] + [
        ('set_variable', '=', [('name', '=', 'ga_clan_flags_060_applied'), ('value', '=', 'yes')])]
    if game:
        assert (game / 'main_menu/gfx/coat_of_arms/patterns/pattern_solid.dds').is_file()
        native = (game / 'main_menu/common/coat_of_arms/coat_of_arms/pre_scripted_countries.txt').read_text(encoding='utf-8-sig')
        assert 'textured_emblem = {' in native and 'color1 = rgb {' in native
        native_setup = (game / 'main_menu/setup/1337/10_countries.txt').read_text(encoding='utf-8-sig')
        assert 'flag = "ASK"' in native_setup
        native_effects = (game / 'in_game/events/situations/fall_of_delhi.txt').read_text(encoding='utf-8-sig')
        assert 'change_country_flag = BAH' in native_effects
    return {'clan_flags': len(FLAGS), 'custom_alpha_emblems': len(FLAGS), 'full_mip_chains': True,
            'explicit_starting_flags': setup_path.exists(), 'saved_flag_repair_once': True,
            'prototype_hashes_checked': True, 'native_schema_checked': bool(game),
            'engine_render_tested': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT / 'mod')
    parser.add_argument('--game', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.out, args.game), indent=2))
