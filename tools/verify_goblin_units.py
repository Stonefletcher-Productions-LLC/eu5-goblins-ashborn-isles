"""Check the goblin unique unit line: stats, culture gate, upgrade chain and localization."""
import re
from verify_055 import parse

UNITS = {
    'a_ga_obsidian_fletchers': {'copy_from': 'a_age_1_traditions_light_infantry', 'upgrades_to': 'a_ga_blackglass_crossbows'},
    'a_ga_blackglass_crossbows': {'copy_from': 'a_age_2_renaissance_light_infantry', 'upgrades_to': 'a_early_arquebusiers'},
}


def verify(read, native_units=None):
    """read(rel) returns a packaged file; native_units, when given, holds the installed unit type keys."""
    fields = lambda rows: {k: v for k, _, v in rows}
    units = fields(parse(read('in_game/common/unit_types/goblins_units.txt')))
    assert set(units) == set(UNITS), sorted(units)
    trigger = fields(parse(read('in_game/common/scripted_triggers/goblins_units.txt')))
    assert trigger['ga_obsidian_fletchers_location_trigger'] == parse(
        'dominant_culture ?= { has_culture_group = culture_group:cm_goblin_group }')
    group = fields(parse(read('in_game/common/culture_groups/goblins_ashborn_isles.txt')))
    assert 'cm_goblin_group' in group
    localization = read('main_menu/localization/english/goblins_units_l_english.yml')
    for key, expected in UNITS.items():
        unit = fields(units[key])
        assert unit['copy_from'] == expected['copy_from'], key
        assert unit['upgrades_to'] == expected['upgrades_to'], key
        assert unit['is_special'] == unit['levy'] == 'yes' and unit['buildable'] == 'no', key
        assert unit['location_potential'] == parse('ga_obsidian_fletchers_location_trigger = yes'), key
        assert unit['maintenance_demand'] == 'archer_infantry_maintenance', key
        for loc in [key, key + '_desc']:
            assert re.search(r'^ ' + re.escape(loc) + r': "[^"\n]+"', localization, re.M), loc
        if native_units is not None:
            for ref in [unit['copy_from'], unit['upgrades_to']]:
                assert ref in native_units or ref in units, f'{key} references missing unit {ref}'
    fletchers = fields(units['a_ga_obsidian_fletchers'])
    assert fletchers['initiative'] == '2'
    assert fletchers['strength_damage_done'] == fletchers['strength_damage_taken'] == '0.10'
    assert fields(fletchers['combat']) == {'hills': '0.15', 'mountains': '0.10'}
    return {'unit_types': sorted(units), 'gate': 'goblin-majority location', 'upgrade_chain_resolved': native_units is not None}


if __name__ == '__main__':
    import argparse, json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / 'mod'
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', type=Path, help='EU5 game directory, to resolve vanilla upgrade targets')
    args = ap.parse_args()
    native = None
    if args.game:
        from build_infantry_art import blocks
        native = set()
        for p in sorted((args.game / 'in_game/common/unit_types').glob('*.txt')):
            native.update(blocks(p.read_text(encoding='utf-8-sig')))
    print(json.dumps(verify(lambda p: (root / p).read_text(encoding='utf-8-sig'), native)))
