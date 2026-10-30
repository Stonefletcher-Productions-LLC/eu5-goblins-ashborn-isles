"""Focused setup/contact checks against installed EU5; no terrain or install."""
import argparse
import json
import re
from pathlib import Path
import build as b
import exploration as e


def verify(game, out, rebuild=True):
    if rebuild:
        b.build_setup(game, out)
        e.build(b, game, out)
    report = {"runtime_verified":False}
    definitions = b.read(game, 'in_game/map_data/definitions.txt')
    known = set()
    for key in e.STARTING_REGIONS + e.STARTING_SEA_AREAS + e.STARTING_PROVINCES:
        start, end = b.block_span(definitions, key)
        known.update(re.findall(r'\b\w+\b', b.clean(definitions[start:end])))
    # Every foreign location granted by the starting sea areas must really be sea.
    names = set(b.parse_names(game))
    defaults = b.read(game, 'in_game/map_data/default.map')
    start, end = b.block_span(defaults, 'sea_zones')
    seas = set(re.findall(r'\b\w+\b', b.clean(defaults[start:end])))
    assert known & names, 'Starting sea areas contain no locations'
    assert (known & names) <= seas, f'Foreign land revealed at start: {(known & names) - seas}'
    land_ports = {loc for route in e.ROUTES.values() for loc in route['locations']} - seas
    assert not land_ports & known, 'Voyage destinations already discovered'
    assert not e.STARTING_REGIONS and not e.STARTING_PROVINCES
    setup = (out/'main_menu/setup/1337/10_countries.txt').read_text(encoding='utf-8-sig')
    for country in b.CFG['countries']:
        start, end = b.block_span(setup, country['tag'])
        block = setup[start:end]
        assert 'discovered_regions' not in block and 'discovered_provinces' not in block
        assert 'discovered_locations' not in block and 'discover_location' not in block
    assert not {'paris', 'london', 'fez_region', 'beijing'} & known
    actions = (out/'in_game/common/on_action/goblins_exploration.txt').read_text(encoding='utf-8-sig')
    assert 'name = ga_exploration_cooldown value = yes months = 36' in actions
    assert 'NOT = { has_variable = ga_exploration_initialized }' in actions
    assert 'NOT = { has_variable = ga_exploration_pending }' in actions
    events = (out/'in_game/events/goblins_exploration.txt').read_text(encoding='utf-8-sig')
    for num in (1, 3):
        start, end = b.block_span(events, f'goblins_exploration.{num}')
        notice = events[start:end]
        assert 'discover_area' not in notice and 'discover_location' not in notice and 'add_gold' not in notice
        assert 'remove_variable = ga_exploration_pending' in notice
    effects = (out/'in_game/common/scripted_effects/goblins_exploration.txt').read_text(encoding='utf-8-sig')
    voyages = (out/'in_game/common/expedition_types/goblins_voyages.txt').read_text(encoding='utf-8-sig')
    from exploration_progress import WAYPOINTS
    ports = {line.split(';')[0] for line in b.read(game, 'in_game/map_data/ports.csv').splitlines()[1:]}
    for route, config in e.ROUTES.items():
        assert not set(WAYPOINTS[route]) - ports, set(WAYPOINTS[route]) - ports
        start, end = b.block_span(voyages, f'ga_voyage_{route}_expedition')
        assert f'ga_exp_complete_{route} = yes' in voyages[start:end]
        assert f"trigger_event_non_silently = goblins_exploration.{config['event']}" in voyages[start:end]
        start, end = b.block_span(effects, f'ga_exp_complete_{route}')
        arrival = effects[start:end]
        for location in config['locations']:
            left, right = b.block_span(arrival, 'location:' + location)
            assert 'discover_location = root' in arrival[left:right]
        assert arrival.count('limit = { exists = owner }') == len(config['locations'])
        assert arrival.count('NOT = { has_variable = ga_received_goblin_first_contact }') == len(config['locations'])
        assert f'name = ga_charted_{route} value = yes' in arrival
        assert 'name = ga_exploration_cooldown value = yes months = 12' in arrival
        assert f"goblins_exploration.{config['event']} = {{" in events
    assert 'lift_fog_of_war' not in actions + events + effects + voyages
    report['checks'] = ['native map references', 'starting knowledge for all six crowns',
                        'sea-only foreign starting knowledge', 'undiscovered ports revealed on voyage completion', 'three-year initial cooldown',
                        'pending/retry guards', 'delayed owner-scoped first contact', 'voyage waypoints are native ports']
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=b.ROOT/'build/exploration-check')
    args = parser.parse_args()
    print(json.dumps(verify(args.game, args.out), indent=2))
