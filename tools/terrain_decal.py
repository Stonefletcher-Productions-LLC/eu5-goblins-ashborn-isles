"""Island terrain as a native EU5 1.4 terrain decal.

EU5 1.4 dropped the baked terrain_cache that 0.6.x patched. Terrain is now the
sum of decals listed in terrain_cache/ingame_decals.json; each decal stores
LZAV-compressed 132x132 tiles (128 px plus a 2 px border) for every mip, tile
rows Y-up. The islands are one extra decal blended with "max", the mode the
vanilla canal decals use, so it can only raise the ocean floor: away from the
islands it holds the ocean-floor minimum and leaves vanilla terrain untouched.
Its material layer holds visual-biome slots on land and 255 (empty, as on
vanilla ocean) elsewhere, so the "min" material blend keeps vanilla materials
off the islands. No vanilla decal is modified.
"""
import json
import re

import numpy as np

import landscape
import lzav

NAME = 'ga_ashborn_isles'
ROOT = 'in_game/gfx/terrain2'
DECALS = ROOT + '/decals'
INSTANCES = ROOT + '/terrain_cache/ingame_decals.json'
DEFINITIONS = DECALS + '/decal_definitions.txt'
SIZE = 2048          # decal pixels per side
SCALE = 2            # terrain units per decal pixel; 4 terrain units per map pixel
TERRAIN_H = 32768    # terrain units; map PNG is 16384 x 8192
FLOOR = 2234         # landscape.heights fill value: below every vanilla sea floor we raise
EMPTY = 255          # vanilla "no material" value
LAYER = '1XaVf7fVmQl'  # vanilla layer of the world heightmap decals
INSTANCE_ID = 'gaAshbornIs'


def placement(cfg):
    """Decal centre in terrain units (Y-up), covering every island.

    On a 4-unit grid, so decal mip 1 pixels coincide with location-map pixels.
    """
    xs = [v for i in cfg['islands'] for v in (i['center'][0] - i['radius'][0] * 2, i['center'][0] + i['radius'][0] * 2)]
    ys = [v for i in cfg['islands'] for v in (i['center'][1] - i['radius'][1] * 2, i['center'][1] + i['radius'][1] * 2)]
    cx = int(round((min(xs) + max(xs)) / 2)) * 4
    cy = TERRAIN_H - int(round((min(ys) + max(ys)) / 2)) * 4
    half = SIZE * SCALE / 2
    assert cx - half <= min(xs) * 4 and max(xs) * 4 <= cx + half, 'islands wider than the terrain decal'
    assert cy - half <= TERRAIN_H - max(ys) * 4 and TERRAIN_H - min(ys) * 4 <= cy + half, 'islands taller than the terrain decal'
    return cx, cy


def fields(cfg, center):
    """North-up height and material images at decal resolution."""
    cx, cy = center
    rows, cols = np.mgrid[0:SIZE, 0:SIZE]
    tx = cx + (cols - SIZE / 2 + .5) * SCALE
    ty = cy + (SIZE / 2 - rows - .5) * SCALE
    # Map-pixel coordinates relative to the archipelago centre, as landscape expects.
    x = tx / 4 - cfg['center'][0]
    y = (TERRAIN_H - ty) / 4 - cfg['center'][1]
    height = landscape.heights(cfg, x, y)
    slots = landscape.material_indices(cfg, x, y)
    land = height > landscape.SEA
    material = np.where(land, slots, EMPTY).astype(np.uint8)
    return height, material


def pyramid(image, kind):
    levels = [image]
    while levels[-1].shape[0] > 128:
        a = levels[-1]; h, w = a.shape
        q = a.reshape(h // 2, 2, w // 2, 2)
        if kind == 'height':
            # Area average; FLOOR stays FLOOR, so coarse mips never lower vanilla.
            levels.append(((q.astype(np.uint32).sum(axis=(1, 3)) + 2) // 4).astype(np.uint16))
        else:
            # Smallest slot wins, so a land pixel survives against empty ocean.
            levels.append(q.min(axis=(1, 3)).astype(np.uint8))
    return levels


def encode(image, kind):
    """Tiles for every mip, mip-major, rows Y-up; returns (bin bytes, info text)."""
    dtype = '<u2' if kind == 'height' else 'u1'
    blob = bytearray(); infos = []
    for level in pyramid(image, kind):
        flipped = np.pad(level[::-1], 2, mode='edge')
        n = level.shape[0] // 128
        for ty in range(n):
            for tx in range(n):
                tile = np.ascontiguousarray(flipped[ty * 128:ty * 128 + 132, tx * 128:tx * 128 + 132]).astype(dtype)
                data = lzav.compress(tile.tobytes())
                infos.append((len(blob), len(data)))
                blob += data
    entries = ' '.join(f'{{\n\t\toffset={o}\n\t\tsize={s}\n\t}}' for o, s in infos)
    info = (f'source_resolution={{ {SIZE} {SIZE} }}\nnum_channels=1\nbytes_per_channel={2 if kind == "height" else 1}\n'
            f'empty_value={{ 0 0 0 0 }}\nlzav=yes\ntile_infos={{ {entries} }}\n')
    return bytes(blob), info


def verify_tiles(blob, info, image, kind):
    """Decode mip 0 from the written stream and compare with the source image."""
    entries = [tuple(map(int, m)) for m in re.findall(r'offset=(\d+)\s+size=(\d+)', info)]
    n = SIZE // 128
    assert len(entries) == sum((n >> m) ** 2 for m in range(n.bit_length()))
    bpc = 2 if kind == 'height' else 1
    rebuilt = np.zeros_like(image)
    for ty in range(n):
        for tx in range(n):
            o, s = entries[ty * n + tx]
            tile = np.frombuffer(lzav.decompress(blob[o:o + s], 132 * 132 * bpc), '<u2' if bpc == 2 else 'u1').reshape(132, 132)
            rebuilt[ty * 128:(ty + 1) * 128, tx * 128:(tx + 1) * 128] = tile[2:130, 2:130]
    assert np.array_equal(rebuilt[::-1], image), f'{kind} tiles do not round-trip'


def instance_json(center, priority):
    return ('{\n\t\t"decal_name":\t"%s",\n\t\t"decal_tags":\t[],\n\t\t"decal_transform":\t{\n\t\t\t"position":\t{\n'
            '\t\t\t\t"x":\t%d,\n\t\t\t\t"y":\t%d\n\t\t\t},\n\t\t\t"rotation":\t0,\n\t\t\t"scale":\t{\n\t\t\t\t"x":\t%d,\n'
            '\t\t\t\t"y":\t%d\n\t\t\t}\n\t\t},\n\t\t"decal_params":\t{\n\t\t\t"strength":\t1,\n\t\t\t"fade_margin":\t0,\n'
            '\t\t\t"heightblendmode":\t"max",\n\t\t\t"materialblendmode":\t"min",\n\t\t\t"curvatureblendmode":\t"addsub",\n'
            '\t\t\t"curvature_strength":\t1,\n\t\t\t"depth_priority":\t%d,\n\t\t\t"groundlevel":\t0\n\t\t},\n'
            '\t\t"decal_size":\t{\n\t\t\t"x":\t%d,\n\t\t\t"y":\t%d\n\t\t}\n\t}'
            % (NAME, center[0], center[1], SCALE, SCALE, priority, SIZE, SIZE))


def build(b, game, out):
    cfg = b.CFG
    center = placement(cfg)
    height, material = fields(cfg, center)
    assert (height > landscape.SEA).sum() > 0 and np.all(height >= FLOOR)
    folder = f'{DECALS}/{NAME}'
    (out / folder / 'instances').mkdir(parents=True, exist_ok=True)
    report = {'decal': NAME, 'center_terrain_units': list(center), 'size': SIZE, 'scale': SCALE,
              'land_pixels': int((height > landscape.SEA).sum())}
    for kind, image in (('height', height), ('materials', material)):
        blob, info = encode(image, kind)
        verify_tiles(blob, info, image, kind)
        (out / folder / f'{NAME}_{kind}.bin').write_bytes(blob)
        (out / folder / f'{NAME}_{kind}.info').write_text(info, encoding='utf-8', newline='\n')
        report[f'{kind}_bytes'] = len(blob)
    presets = b.source(game, f'{DECALS}/panama_canal/presets.json').read_bytes()
    (out / folder / 'presets.json').write_bytes(presets)

    # The runtime list of decal instances: vanilla's, plus ours drawn last.
    text = b.read(game, INSTANCES)
    native = json.loads(text)
    assert all(d['decal_name'] != NAME for d in native)
    priority = max(d['decal_params']['depth_priority'] for d in native) + 1
    body = text.rstrip()
    assert body.endswith(']')
    combined = body[:-1] + ', ' + instance_json(center, priority) + ']'
    added = json.loads(combined)
    assert added[:-1] == native and added[-1]['decal_name'] == NAME
    (out / INSTANCES).parent.mkdir(parents=True, exist_ok=True)
    (out / INSTANCES).write_bytes(b'\xef\xbb\xbf' + combined.encode('utf-8'))
    (out / folder / 'instances' / f'{INSTANCE_ID}.json').write_bytes(b'\xef\xbb\xbf' + json.dumps({
        'layer_id': LAYER, 'tags': [], 'strength': 1, 'ground_level': 0, 'height_blend_mode': 0,
        'materialblendmode': 'min', 'curvatureblendmode': 'addsub', 'rotation': 0, 'fade_margin': 0,
        'position.x': center[0], 'position.y': center[1], 'scale.x': SCALE, 'scale.y': SCALE,
        'depth_priority': priority, 'locked': True, 'disabled': False}, indent='\t').encode('utf-8'))

    definitions = b.read(game, DEFINITIONS)
    assert f'name = {NAME}' not in definitions
    definitions = definitions.rstrip() + (f'\n{{\n    name = {NAME}\n    layer_textures = {{\n'
        f'        heightmap = "{NAME}_height.info"\n        materials = "{NAME}_materials.info"\n    }}\n'
        f'    additional_textures = {{\n    }}\n}}\n')
    (out / DEFINITIONS).write_text(definitions, encoding='utf-8', newline='\n')
    report['depth_priority'] = priority
    report['method'] = 'native terrain decal, max height blend, min material blend'
    report['runtime_verified'] = False
    return report
