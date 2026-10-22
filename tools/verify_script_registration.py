"""Regression checks for registrations reported missing by EU5 1.3.11."""
import re
from verify_055 import parse


def verify(read):
    def entries(path):
        # The script parser handles blocks, not EU5's typed color literals.
        script = re.sub(r'\bcolor\s*=\s*rgb\s*\{[^}]*\}', '', read(path))
        return {k: v for k, _, v in parse(script)}
    localization = '\n'.join(read('main_menu/localization/english/' + name + '_l_english.yml')
                             for name in ['goblins_gathering', 'ashen_covenant', 'goblins_ashborn_isles'])
    prices = {}
    definitions = {}
    for name in ['goblins_gathering', 'ashen_covenant']:
        prices.update(entries('in_game/common/prices/' + name + '.txt'))
        definitions.update(entries('main_menu/common/modifier_type_definitions/' + name + '.txt'))
    # The released bundle can predate newer rites, so require the 0.5.9 set and check each price below.
    assert len(prices) >= 8
    for price in prices:
        modifier = price + '_cost_modifier'
        assert definitions[modifier] == [('color', '=', 'bad'), ('percent', '=', 'yes'),
                                         ('game_data', '=', [('category', '=', 'country')])]
        for key in [price, 'MODIFIER_TYPE_NAME_' + modifier, 'MODIFIER_TYPE_DESC_' + modifier]:
            assert re.search(r'^ ' + re.escape(key) + r': "[^"\n]+"', localization, re.M), key
    ai = entries('in_game/common/generic_action_ai_lists/goblins_gathering.txt')
    matches = []
    for name, body in ai.items():
        fields = {k: v for k, _, v in body}
        if any(k == 'ga_offer_harbor_pact' for k, _, _ in fields['actions']):
            matches.append(name)
            assert ('ga_hb_free', '=', 'yes') in fields['potential']
            assert ('gold', '>=', '30') in fields['potential']
            assert fields['actions'] == [('ga_offer_harbor_pact', None, None), ('ga_seek_pilot_bargain', None, None)]
    assert len(matches) == 1, 'Harbor offers must register once in the bounded AI list'
    biases = entries('in_game/common/biases/goblins_gathering.txt')
    for name, value, months in [('ga_harbor_pact_opinion', '35', '120'),
                                ('ga_received_supplies', '30', '60'), ('ga_oath_honored', '25', '120')]:
        assert biases[name] == [('value', '=', value), ('months', '=', months)]
    for key in ['ga_no_kingdom_available', 'ga_no_eastern_target']:
        assert re.search(r'^ ' + key + r': "@trigger_no! ', localization, re.M), key
    assert ' AUTO_MODIFIER_NAME_ga_goblin_longevity: "Goblin Longevity"' in localization
    language = entries('in_game/common/languages/goblins_ashborn_isles.txt')['cm_cinder_tongue']
    language = {k: v for k, _, v in language}
    dialects = {k for k, _, _ in language['dialects']}
    religion = entries('in_game/common/religions/goblins_ashborn_isles.txt')['cm_hunger_below']
    assert next(v for k, _, v in religion if k == 'language') in dialects
    for pool in ['male_names', 'female_names', 'dynasty_names']:
        names = [k for k, _, _ in language[pool]]
        assert len(names) == len(set(names)), pool
    return {'registered_prices': len(prices), 'harbor_ai_guarded': True,
            'opinion_durations_months': [120, 60, 120], 'religion_dialect_resolved': True,
            'selector_icons_and_longevity_text': True, 'unique_root_names': True}
