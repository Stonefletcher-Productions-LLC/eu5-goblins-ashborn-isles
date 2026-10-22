"""Check the Old World Reacts events: every goblin crown is eligible, every key is registered."""
import re
from verify_055 import parse
from ashborn_roster import TAGS

EVENTS = [f'ga_old_world.{n}' for n in range(1, 7)]
GOBLIN_EVENTS = EVENTS[1:5]


def verify(read):
    fields = lambda rows: {k: v for k, _, v in rows}
    events = fields(parse(read('in_game/events/goblins_old_world.txt')))
    assert events.pop('namespace') == 'ga_old_world'
    assert sorted(events) == EVENTS, sorted(events)
    script = read('in_game/events/goblins_old_world.txt') + read('in_game/common/on_action/goblins_old_world.txt')
    # No crown-specific gating: the chain is for every Ashborn crown, not one tag or ruler.
    assert not re.search(r'\btag\s*=|c:(?:' + '|'.join(TAGS) + r')\b', script), 'Old World events must not single out a crown'
    goblin = fields(parse(read('in_game/common/scripted_triggers/goblins_gathering.txt')))['ga_is_goblin']
    assert {v for k, _, v in goblin[0][2]} == set(TAGS) and goblin[0][0] == 'OR'
    for key in GOBLIN_EVENTS:
        assert fields(fields(events[key])['trigger']).get('ga_is_goblin') == 'yes', key
    for key in ('ga_old_world.1', 'ga_old_world.6'):
        assert fields(fields(events[key])['trigger'])['ga_is_goblin'] == 'no', key

    pulses = fields(parse(read('in_game/common/on_action/goblins_old_world.txt')))
    registered = {k for k, _, _ in fields(pulses['monthly_country_pulse'])['on_actions']}
    assert registered == {'ga_owr_foreign_monthly', 'ga_owr_goblin_monthly'}
    fired = set(re.findall(r'trigger_event_non_silently = \{ id = (ga_old_world\.\d+) \}',
                           read('in_game/common/on_action/goblins_old_world.txt')))
    assert fired == set(EVENTS), fired

    biases = fields(parse(read('in_game/common/biases/goblins_old_world.txt')))
    modifiers = fields(parse(read('main_menu/common/static_modifiers/goblins_old_world.txt')))
    used_biases = set(re.findall(r'modifier = (ga_owr_\w+) \}', script)) - set(modifiers)
    used_modifiers = set(re.findall(r'add_country_modifier = \{ modifier = (ga_owr_\w+)', script))
    assert used_biases == set(biases), used_biases ^ set(biases)
    assert used_modifiers == set(modifiers), used_modifiers ^ set(modifiers)

    localization = read('main_menu/localization/english/goblins_old_world_l_english.yml')
    assert localization.startswith('l_english:')
    keys = set(re.findall(r'^ ([\w.]+): "[^"\n]+"$', localization, re.M))
    needed = set(biases) | {f'STATIC_MODIFIER_{kind}_{m}' for m in modifiers for kind in ('NAME', 'DESC')}
    needed |= set(re.findall(r'\b(?:title|desc|name|custom_tooltip) = (ga_old_world\.[\w.]+)', script))
    missing = needed - keys
    assert not missing, missing
    return {'events': len(EVENTS), 'goblin_crowns': len(TAGS), 'opinion_modifiers': len(biases),
            'country_modifiers': len(modifiers), 'crown_specific_gates': 0, 'gameplay_tested': False}


if __name__ == '__main__':
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / 'mod'
    print(json.dumps(verify(lambda p: (root / p).read_text(encoding='utf-8-sig')), indent=2))
