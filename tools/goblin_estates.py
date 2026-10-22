"""Goblin estate names, inserted ahead of native country-name alternatives."""
import re

NAMES = {
    'crown_estate': 'Ironfang Crown',
    'nobles_estate': 'Highfangs',
    'clergy_estate': 'Oathkeepers',
    'burghers_estate': 'Coinclutchers',
    'peasants_estate': 'Muckgrubs',
    'tribes_estate': 'Wildfang Clans',
    'dhimmi_estate': 'Outsiders',
    'cossacks_estate': 'Freebooters',
}
PATH = 'in_game/common/customizable_localization/estates.txt'

def build(b, game, out):
    native = b.read(game, PATH)
    result = native
    cultures = ' '.join('culture = culture:' + c['culture'] for c in b.CFG['countries'])
    insertions = []
    for estate in NAMES:
        start, end = b.block_span(result, estate)
        body = result[start:end]
        match = re.search(r'\btype\s*=\s*country\b', body)
        assert match, f'Native estate localization scope changed: {estate}'
        insertion = ('\n\ttext = {\n\t\tlocalization_key = ga_' + estate +
                     '\n\t\ttrigger = { OR = { ' + cultures + ' } }\n\t}\n')
        position = start + match.end()
        result = result[:position] + insertion + result[position:]
        insertions.append(insertion)
    # Stripping only our conditional alternatives must recover every native byte.
    restored = result
    for insertion in insertions:
        restored = restored.replace(insertion, '', 1)
    assert restored == native, 'Unrelated native estate localization changed'
    b.write(out, PATH, result)
    b.write(out, 'main_menu/localization/english/goblin_estates_l_english.yml',
            'l_english:\n' + ''.join(f' ga_{key}: "{value}"\n' for key, value in NAMES.items()))
    return {'names': NAMES, 'scope': 'country primary culture is one of the five Ashborn cultures',
            'native_alternatives_preserved': True, 'estate_mechanics_changed': False,
            'engine_tested': False}
