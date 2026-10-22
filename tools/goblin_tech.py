"""Goblin starting technology and unique ships.

EU5 gates the age-1 galley (and the cog after it), Iron Working and the Feudalism
advance behind an embraced Feudalism institution. Native setup seeds institutions
per location in main_menu/setup/start/08_institutions.txt; goblin locations had no
row, so the crowns started with canoes, no iron and no feudal tree despite
starting_technology_level = 3.

Goblins sit between tribes (no institutions) and Europe (Feudalism + Legalism):
every homeland location starts with Feudalism only. Legalism has to spread in.

Two goblin-only ships use the native unique-ship pattern (n_long_fada,
n_genoese_galley: copy_from an age template plus deltas, unlocked by a
culture-gated advance in the ship_building tree):
- Ash-Oar Galley: start unit (starting_technology_level 2, like the native galley).
- Wreck-Hulk: an age-1 heavy ship researched after the cog; upgrades to the early carrack.

Writes the 08_institutions overlay (native rows byte-for-byte unchanged, goblin rows
appended), the advances, the ship types, their location trigger and localization.
"""
import argparse, json, re
from pathlib import Path
import build as b
from verify_055 import parse

ROOT = Path(__file__).resolve().parents[1]
INSTITUTIONS = 'main_menu/setup/start/08_institutions.txt'
ADVANCES = 'in_game/common/advances/goblins_ships.txt'
UNITS = 'in_game/common/unit_types/goblins_ships.txt'
TRIGGERS = 'in_game/common/scripted_triggers/goblins_ships.txt'
LOCALIZATION = 'main_menu/localization/english/goblins_ships_l_english.yml'
START_INSTITUTIONS = ('feudalism',)
GALLEY, HULK = 'n_ga_ashoar_galley', 'n_ga_wreck_hulk'
GOBLIN_CULTURE = 'culture = { has_culture_group = culture_group:cm_goblin_group }'

ADVANCE_TEXT = f'''# Goblin unique ships. Patterned on vanilla unlock_long_fada / genoese_galley.
ga_ashoar_galley_advance = {{
	age = age_1_traditions
	icon = ship_building_advance

	potential = {{
		{GOBLIN_CULTURE}
	}}
	requires = ship_building_advance
	starting_technology_level = 2

	unlock_unit = {GALLEY}
}}

ga_wreck_hulk_advance = {{
	age = age_1_traditions
	icon = ship_building_advance

	potential = {{
		{GOBLIN_CULTURE}
	}}
	requires = unlock_cog_advance

	unlock_unit = {HULK}

	ai_preference_tags = {{
		exploration
	}}
}}
'''

UNIT_TEXT = f'''# Goblin unique ships. Values after copy_from are deltas on the age template,
# as in vanilla n_long_fada.

# Long, low and packed with rowers: the isles have more hands than timber.
{GALLEY} = {{
	is_special = yes
	category = navy_galley
	copy_from = n_age_1_traditions_galley
	upgrades_to = n_mediterrannean_galley
	age = "age_1_traditions"

	movement_speed = 1
	cannons = -2
	crew_size = 0.010
	transport_capacity = 0.020

	maintenance_demand = galley_1_maintenance
	construction_demand = galley_1_construction

	location_potential = {{
		ga_goblin_shipyard_location_trigger = yes
	}}
}}

# Salvaged hulls lashed together and armed with whatever the wrecks carried.
{HULK} = {{
	is_special = yes
	category = navy_heavy_ship
	copy_from = n_age_1_traditions_heavy_ship
	upgrades_to = n_early_carrack
	age = "age_1_traditions"

	hull_size = 3
	cannons = -6
	movement_speed = -1
	crew_size = 0.020

	maintenance_demand = heavy_ship_1_maintenance
	construction_demand = heavy_ship_1_construction

	location_potential = {{
		ga_goblin_shipyard_location_trigger = yes
	}}
}}
'''

TRIGGER_TEXT = '''# location scope; goblin-majority ports, including settled or conquered ones.
ga_goblin_shipyard_location_trigger = {
	dominant_culture ?= { has_culture_group = culture_group:cm_goblin_group }
}
'''

LOC = {
    GALLEY: 'Ash-Oar Galley',
    GALLEY + '_desc': 'Goblin yards have more hands than good timber, so the Ash-Oar Galley is long, low and crammed with rowers. It runs down slower ships and carries raiders ashore, but mounts fewer guns than a southern galley.',
    HULK: 'Wreck-Hulk',
    HULK + '_desc': 'Two or three salvaged hulls lashed and pegged into one, armed with whatever guns the wrecks gave up. The Wreck-Hulk is slow and ugly, but it takes a beating, and no one else in the age of oars puts a ship this big to sea.',
    'ga_ashoar_galley_advance': '$' + GALLEY + '$',
    'ga_ashoar_galley_advance_desc': '$' + GALLEY + '_desc$',
    'ga_wreck_hulk_advance': '$' + HULK + '$',
    'ga_wreck_hulk_advance_desc': '$' + HULK + '_desc$',
}


def institution_rows(locations):
    return ''.join(f'{l} = {{\n' + ''.join(f'\t{i} = yes\n' for i in START_INSTITUTIONS) + '}\n' for l in locations)


def institutions(native, locations):
    """Append goblin rows inside the top-level locations block, leaving native rows untouched."""
    assert native.startswith('locations={'), 'Unexpected 08_institutions layout'
    present = set(re.findall(r'(?m)^(\w+) = \{', native))
    assert not present & set(locations), sorted(present & set(locations))
    end = native.rstrip().rfind('}')
    assert end > 0 and native[end:].strip() == '}'
    return native[:end] + institution_rows(locations) + native[end:]


def build(game, root=ROOT):
    out = root / 'mod'
    locations = [l['id'] for l in b.CFG['locations']]
    native = (game / INSTITUTIONS).read_bytes().decode('utf-8')
    (out / INSTITUTIONS).parent.mkdir(parents=True, exist_ok=True)
    (out / INSTITUTIONS).write_bytes(institutions(native, locations).encode('utf-8'))
    b.write(out, ADVANCES, ADVANCE_TEXT)
    b.write(out, UNITS, UNIT_TEXT)
    b.write(out, TRIGGERS, TRIGGER_TEXT)
    b.write(out, LOCALIZATION, 'l_english:\n' + ''.join(f' {k}: "{v}"\n' for k, v in LOC.items()))
    return verify(root, game)


def verify(root=ROOT, game=None):
    out = root / 'mod'
    read = lambda rel: (out / rel).read_text(encoding='utf-8-sig')
    fields = lambda rows: {k: v for k, _, v in rows}
    locations = [l['id'] for l in b.CFG['locations']]
    text = (out / INSTITUTIONS).read_bytes().decode('utf-8')
    assert text.endswith(institution_rows(locations) + '}\n'), 'Goblin institution rows missing'
    if game:
        native = (game / INSTITUTIONS).read_bytes().decode('utf-8')
        assert text == institutions(native, locations), 'Native institution rows changed'
    rows = fields(parse(text))['locations']
    seeded = {k: fields(v) for k, _, v in rows if k in locations}
    assert set(seeded) == set(locations) and all(v == {'feudalism': 'yes'} for v in seeded.values())
    advances = {k: fields(v) for k, v in fields(parse(read(ADVANCES))).items()}
    assert advances['ga_ashoar_galley_advance']['unlock_unit'] == GALLEY
    assert advances['ga_ashoar_galley_advance']['starting_technology_level'] == '2'
    assert advances['ga_wreck_hulk_advance']['unlock_unit'] == HULK
    assert advances['ga_wreck_hulk_advance']['requires'] == 'unlock_cog_advance'
    assert 'starting_technology_level' not in advances['ga_wreck_hulk_advance']
    for adv in advances.values():
        assert adv['potential'] == parse(GOBLIN_CULTURE)
    units = {k: fields(v) for k, v in fields(parse(read(UNITS))).items()}
    assert units[GALLEY]['upgrades_to'] == 'n_mediterrannean_galley' and units[HULK]['upgrades_to'] == 'n_early_carrack'
    for unit in units.values():
        assert unit['is_special'] == 'yes' and unit['location_potential'] == parse('ga_goblin_shipyard_location_trigger = yes')
    assert 'ga_goblin_shipyard_location_trigger' in fields(parse(read(TRIGGERS)))
    loc = read(LOCALIZATION)
    for key in LOC:
        assert re.search(r'^ ' + re.escape(key) + r': "[^"\n]+"', loc, re.M), key
    return {'feudal_locations': len(seeded), 'advances': sorted(advances), 'ships': sorted(units)}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', type=Path, help='EU5 game directory; rebuilds the overlay when given')
    args = ap.parse_args()
    print(json.dumps(build(args.game) if args.game else verify(), indent=2))
