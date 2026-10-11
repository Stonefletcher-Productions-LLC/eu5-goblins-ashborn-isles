"""Check the authored divorce action's scope guards and native-effect contract."""
from verify_055 import parse
from ashborn_roster import TAGS


def verify(read):
    fields = lambda rows: {k: v for k, _, v in rows}
    action = fields(fields(parse(read('in_game/common/generic_actions/goblins_divorce.txt')))['ga_divorce_ruler'])
    price = fields(fields(parse(read('in_game/common/prices/goblins_divorce.txt')))['ga_divorce_price'])
    assert price == {'gold': '10', 'ignore_inflation': 'yes'}
    assert action['price'] == 'price:ga_divorce_price'
    assert action['type'] == 'owncountry'
    assert action['ai_tick'] == action['automation_tick'] == 'never'
    assert action['effect'] == parse('custom_tooltip = ga_divorce_effect_tt scope:actor = { ruler ?= { divorce_character = scope:target } }')
    selector = fields(action['select_trigger'])
    assert selector['target_flag'] == 'target' and selector['looking_for_a'] == 'character'
    assert selector['interaction_source_list'] == parse('scope:actor.ruler ?= { every_spouse = { limit = { is_alive = yes } add_to_list = source } }')
    goblin = fields(parse(read('in_game/common/scripted_triggers/goblins_gathering.txt')))['ga_is_goblin']

    def evaluate(rows, state):
        results = []
        for key, op, value in rows:
            if key == 'scope:actor': result = evaluate(value, state)
            elif key == 'ruler': result = not state['ruler'] or evaluate(value, state)
            elif key == 'scope:target': result = state['target'] and evaluate(value, state)
            elif key == 'ga_is_goblin': result = evaluate(goblin, state)
            elif key == 'OR': result = any(evaluate([row], state) for row in value)
            elif key == 'tag': result = state['tag'] == value
            elif key == 'has_ruler': result = state['ruler']
            elif key == 'is_junior_partner': result = state['junior'] == (value == 'yes')
            elif key == 'num_of_spouses':
                assert op == '>' and value == '0'
                result = state['spouses'] > 0
            elif key == 'exists':
                assert value == 'scope:target'
                result = state['target']
            elif key == 'is_alive': result = state['alive']
            elif key == 'is_spouse_of':
                assert value == 'scope:actor.ruler'
                result = state['married_to_current_ruler']
            elif key == 'trigger_if':
                guard = fields(value)['limit']
                result = not evaluate(guard, state) or evaluate([row for row in value if row[0] != 'limit'], state)
            else: raise AssertionError(key)
            results.append(bool(result))
        return all(results)

    for tag in TAGS:
        state = dict(tag=tag, ruler=True, junior=False, spouses=1, target=True, alive=True, married_to_current_ruler=True)
        assert evaluate(action['potential'], state) and evaluate(action['allow'], state)
        assert evaluate(selector['enabled'], state) and evaluate(selector['visible'], state)
        for change in [dict(ruler=False), dict(junior=True), dict(spouses=0), dict(alive=False), dict(married_to_current_ruler=False)]:
            assert not evaluate(action['allow'], state | change), (tag, change)
        assert not evaluate(action['potential'], state | dict(tag='POR'))
        assert evaluate(action['allow'], state | dict(target=False)), 'Must allow opening the spouse picker'
    localization = read('main_menu/localization/english/goblins_divorce_l_english.yml')
    for key in ['ga_divorce_ruler', 'ga_divorce_ruler_desc', 'ga_divorce_effect_tt', 'ga_divorce_price',
                'MODIFIER_TYPE_NAME_ga_divorce_price_cost_modifier', 'MODIFIER_TYPE_DESC_ga_divorce_price_cost_modifier']:
        assert ' ' + key + ': "' in localization, key
    definition = fields(parse(read('main_menu/common/modifier_type_definitions/goblins_divorce.txt')))
    assert 'ga_divorce_price_cost_modifier' in definition
    return {'six_crowns': True, 'stale_spouse_and_ruler_guards': True, 'junior_union_guard': True,
            'base_gold_cost': 10, 'native_divorce_only': True, 'automation_disabled': True, 'gameplay_tested': False}
