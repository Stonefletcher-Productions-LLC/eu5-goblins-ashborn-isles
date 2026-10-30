"""Read installed starting economies; no game-derived files are written to source."""
import re
from collections import Counter
from decimal import Decimal


def blocks(text):
    """Immediate child blocks, ignoring comments and quoted braces."""
    import build
    clean = build.clean(text)
    pos = 0
    while match := re.search(r'(\w+)\s*=\s*\{', clean[pos:]):
        start = pos + match.end()
        end = start
        depth = 1
        while depth:
            depth += (clean[end] == '{') - (clean[end] == '}')
            end += 1
        yield match[1], text[start:end-1]
        pos = end


def compare(b, game):
    countries = dict(blocks(dict(blocks(b.read(game, 'main_menu/setup/1337/10_countries.txt')))['countries']))
    countries = dict(blocks(countries['countries']))
    pops = dict(blocks(dict(blocks(b.read(game, 'main_menu/setup/1337/06_pops.txt')))['locations']))
    city_file = dict(blocks(b.read(game, 'main_menu/setup/1337/07_cities_and_buildings.txt')))
    settlements = dict(blocks(city_file['locations']))
    templates = {}
    for path in (game / 'in_game/common/town_setups').glob('*.txt'):
        templates.update(blocks(path.read_text(encoding='utf-8-sig')))
    result = {}
    for tag in ['POR', 'SER', 'SCO', 'BRI', 'NAV', 'CYP', 'NAX', 'KNI']:
        owned = set(' '.join(re.findall(r'\bown_control_\w+\s*=\s*\{([^}]+)', b.clean(countries[tag]))).split())
        population = sum((Decimal(n) for loc in owned for n in re.findall(r'\bsize\s*=\s*([\d.]+)', pops.get(loc, ''))), Decimal(0))
        buildings = Counter()
        towns = {}
        for loc in sorted(owned):
            setup = settlements.get(loc, '')
            template = re.search(r'\btown_setup\s*=\s*(\w+)', setup)
            if template:
                towns[loc] = template[1]
                buildings.update({key: int(value) for key, value in re.findall(r'(\w+)\s*=\s*(\d+)\b', templates[template[1]])})
        explicit = Counter()
        for key, entry in blocks(city_file['building_manager']):
            owner = re.search(r'\btag\s*=\s*(\w+)', entry)
            location = re.search(r'\blocation\s*=\s*(\w+)', entry)
            level = re.search(r'\blevel\s*=\s*(\d+)', entry)
            if owner and owner[1] == tag and location and location[1] in owned and level:
                explicit[key] += int(level[1])
        result[tag] = {'population': int(population*1000), 'locations': len(owned),
                       'town_templates': towns, 'template_building_levels': dict(buildings),
                       'template_levels_total': sum(buildings.values()),
                       'explicit_building_levels': dict(explicit),
                       'levels_total': sum(buildings.values()) + sum(explicit.values())}
    return result


if __name__ == '__main__':
    import argparse, json, build
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', type=Path, required=True)
    print(json.dumps(compare(build, parser.parse_args().game), indent=2))
