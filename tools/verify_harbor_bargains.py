from ashborn_roster import TAGS
"""Execute the generated negotiation subset against adversarial country scenarios.

This is a script-level regression harness, not an EU5 engine emulator/playtest.
Unknown operations fail rather than silently succeeding.
"""
from copy import deepcopy
import re
from verify_055 import parse, flatten


class World:
    def __init__(self, definitions):
        self.defs = definitions
        self.day = 0
        self.countries = {tag: dict(gold=50., vars={}, modifiers={}, exists=True,
                                   at_war=False, is_subject=False, is_junior_partner=False,
                                   is_ai=False, rivals=set(), enemies=set(), wars=set())
                          for tag in TAGS}
        self.opinion = 50
        self.queue = []
        for country in self.countries.values():
            country.update(allies=set(), country_rank_level=2, relative_strength=0.5, subject_type=None)
            country.update(religion='religion:cm_hunger_below', religious_influence=50, owned=set(), aspects=set())

    def variable(self, country, key):
        value, expiry = self.countries[country]['vars'].get(key, (None, None))
        return value if expiry is None or self.day < expiry else None

    def value(self, value, country, scopes):
        if value == 'this': return country
        if value.startswith('scope:'):
            if value.endswith('.country_rank_level'):
                target = scopes.get(value[6:].split('.')[0])
                return self.countries[target]['country_rank_level'] if target in self.countries else None
            return scopes.get(value[6:])
        if value.startswith('c:'): return value[2:]
        if value == 'country_rank_level': return self.countries[country]['country_rank_level']
        if value.startswith('var:'):
            return self.variable(country, value[4:])
        if value in ['yes', 'no']:
            return value == 'yes'
        try:
            return float(value)
        except ValueError:
            return value

    def condition(self, rows, country, scopes):
        def check(k, op, v):
            if k == 'custom_tooltip':
                return self.condition([row for row in v if row[0] != 'text'], country, scopes)
            if k in ['AND', 'OR', 'NOT']:
                answers = [check(*row) for row in v]
                return any(answers) if k == 'OR' else not all(answers) if k == 'NOT' else all(answers)
            if isinstance(v, list) and k.startswith(('scope:', 'var:', 'c:')):
                target = self.value(k, country, scopes)
                return target in self.countries and self.countries[target]['exists'] and self.condition(v, target, scopes)
            if k in self.defs:
                return self.condition(self.defs[k], country, scopes) == (v == 'yes')
            data = self.countries[country]
            if k == 'is_allied_with':
                target = next(value for key, _, value in v if key == 'target')
                return self.value(target, country, scopes) in data['allies']
            if k == 'relative_strength':
                threshold = next(value for key, _, value in v if key == 'value')
                return data['relative_strength'] <= float(threshold)
            right = self.value(v, country, scopes)
            if k == 'has_variable': return self.variable(country, v) is not None
            if k == 'exists': return self.countries[right]['exists'] if right in self.countries else right is not None
            if k == 'country_exists': return right in self.countries and self.countries[right]['exists']
            if k == 'tag': left = country
            elif k == 'this': left = country
            elif k in ['gold', 'at_war', 'is_subject', 'is_junior_partner', 'is_ai', 'religion', 'religious_influence']: left = data[k]
            elif k == 'owns': return right in data['owned']
            elif k == 'has_religious_aspect': return right in data['aspects']
            elif k == 'is_rival_of': return right in data['rivals']
            elif k == 'is_enemy_of': return right in data['enemies']
            elif k == 'is_at_war_with': return right in data['wars']
            elif k == 'is_subject_type': return right == data['subject_type']
            elif k.startswith('"opinion('): left = self.opinion
            elif k.startswith(('var:', 'scope:')): left = self.value(k, country, scopes)
            else: raise AssertionError(('Unknown condition', k, op, v))
            if left is None: return False
            if op == '=': return left == right
            if op == '!=': return left != right
            if op == '>=': return left >= right
            if op == '<=': return left <= right
            raise AssertionError(('Unknown comparison', op))
        return all(check(*row) for row in rows)

    def effects(self, rows, country, scopes):
        for k, op, v in rows:
            data = self.countries[country]
            if k == 'show_as_tooltip':
                continue  # Native effect preview; never executes gameplay effects.
            elif k == 'hidden_effect':
                self.effects(v, country, scopes)
            elif k == 'custom_tooltip':
                assert isinstance(v, str)
            elif k == 'if':
                limits = next(value for key, _, value in v if key == 'limit')
                if self.condition(limits, country, scopes):
                    self.effects([row for row in v if row[0] != 'limit'], country, scopes)
            elif k.startswith(('scope:', 'var:', 'c:')):
                target = self.value(k, country, scopes)
                if target in self.countries and self.countries[target]['exists']:
                    self.effects(v, target, scopes)
                elif op != '?=': raise AssertionError(('Missing effect scope', k))
            elif k == 'save_scope_as': scopes[v] = country
            elif k == 'save_scope_value_as':
                fields = {key: value for key, _, value in v}
                scopes[fields['name']] = self.value(fields['value'], country, scopes)
            elif k in ['set_variable', 'change_variable', 'add_country_modifier']:
                fields = {key: value for key, _, value in v}
                if k == 'change_variable':
                    data['vars'][fields['name']] = (self.variable(country, fields['name']) + float(fields['add']), None)
                else:
                    days = float(fields.get('days', 0)) + 365 * float(fields.get('years', 0))
                    expiry = self.day + days if days else None
                    if k == 'set_variable': data['vars'][fields['name']] = (self.value(fields['value'], country, scopes), expiry)
                    else: data['modifiers'][fields['modifier']] = expiry
            elif k == 'remove_variable': data['vars'].pop(v, None)
            elif k == 'remove_country_modifier': data['modifiers'].pop(v, None)
            elif k == 'add_gold': data['gold'] += float(v)
            elif k == 'add_opinion':
                fields = {key: value for key, _, value in v}
                data.setdefault('opinions', []).append((self.value(fields['target'], country, scopes), fields['modifier']))
            elif k == 'add_religious_influence': data['religious_influence'] = max(0, min(100, data['religious_influence'] + float(v)))
            elif k == 'make_subject_of':
                fields = {key: value for key, _, value in v}
                assert not data['is_subject'], 'Repeated subject grant'
                data['is_subject'] = True
                data['subject_type'] = fields['type'].split(':')[1]
                data['overlord'] = self.value(fields['target'], country, scopes)
            elif k == 'trigger_event_non_silently': self.queue.append((v, country, deepcopy(scopes)))
            else: raise AssertionError(('Unknown effect', k, op, v))

    def offer(self, actor='CDM', target='QBR', action='ga_offer_harbor_pact'):
        scopes = dict(actor=actor, target=target)
        fields = {k: v for k, _, v in self.defs[action] if k != 'select_trigger'}
        assert self.condition(fields['allow'], actor, scopes)
        selectors = [v for k, _, v in self.defs[action] if k == 'select_trigger']
        target_selector = next(s for s in selectors if ('looking_for_a', '=', 'country') in s)
        assert self.condition(next(v for k, _, v in target_selector if k == 'visible'), target, scopes)
        assert self.condition(next((v for k, _, v in target_selector if k == 'enabled'), []), target, scopes)
        self.effects(fields['effect'], actor, scopes)
        return self.queue.pop(0)

    def choose(self, popup, index, force=False):
        name, country, scopes = popup
        options = [v for k, _, v in self.defs[name] if k == 'option']
        option = options[index]
        trigger = next(v for k, _, v in option if k == 'trigger')
        if not force and not self.condition(trigger, country, scopes): return False
        context = deepcopy(scopes)
        self.effects([row for row in option if row[0] not in ['name', 'trigger', 'ai_chance']], country, context)
        after = next((v for k, _, v in self.defs[name] if k == 'after'), [])
        self.effects(after, country, context)
        return True


def verify(read):
    definitions = {}
    for path in ['in_game/common/scripted_triggers/goblins_gathering.txt',
                 'in_game/common/generic_actions/goblins_gathering.txt',
                 'in_game/common/on_action/goblins_gathering.txt',
                 'in_game/events/goblins_gathering.txt']:
        definitions.update({k: v for k, _, v in parse(read(path)) if k != 'namespace'})
    scenarios = []
    def passed(name): scenarios.append(name)
    for action, kind in [('ga_offer_harbor_pact', 'provisions'), ('ga_seek_pilot_bargain', 'pilots')]:
        w = World(definitions); popup = w.offer(action=action)
        assert sum(c['gold'] for c in w.countries.values()) == 50 * len(w.countries)
        assert w.choose(popup, 0)
        assert (w.countries['CDM']['gold'], w.countries['QBR']['gold']) == (40, 60)
        for tag, suffix in [('CDM', 'received'), ('QBR', 'supplied')]:
            assert w.countries[tag]['modifiers'] == {f'ga_hb_{kind}_{suffix}': 5 * 365}
            assert w.variable(tag, 'ga_hb_pending') is None
            assert w.variable(tag, 'ga_hb_committed') is True
        before = deepcopy(w.countries)
        w.choose(popup, 0, force=True)
        assert w.countries == before, 'Repeated acceptance applied twice'
        passed(kind + ': conserved gold, five-year reciprocal effects, no double acceptance')
    for action, other in [('ga_offer_harbor_pact', 'pilots'), ('ga_seek_pilot_bargain', 'provisions')]:
        w = World(definitions); original = w.offer(action=action)
        assert w.choose(original, 1)
        assert not w.choose(original, 1), 'Second counteroffer allowed'
        counter = w.queue.pop(0)
        assert w.choose(counter, 0)
        assert (w.countries['CDM']['gold'], w.countries['QBR']['gold']) == (35, 65)
        assert f'ga_hb_{other}_received' in w.countries['CDM']['modifiers']
        passed(other + ': counter changes service once and transfers 15 gold')
    for stage in ['offer', 'counter']:
        w = World(definitions); popup = w.offer()
        if stage == 'counter': w.choose(popup, 1); popup = w.queue.pop(0)
        w.choose(popup, 2 if stage == 'offer' else 1)
        assert all(c['gold'] == 50 and not c['modifiers'] for c in w.countries.values())
        assert w.variable('CDM', 'ga_hb_pending') is None
        assert w.variable('QBR', 'ga_hb_pending') is None
        assert w.variable('CDM', 'ga_hb_lock_QBR') is True
        assert w.variable('QBR', 'ga_hb_lock_CDM') is True
        passed(stage + ': free refusal, both locks released, five-year pair protection')
    # Affordability is rechecked when an offer is answered, including AI reserves.
    for ai, funds, allowed in [(False, 9.99, False), (False, 10, True), (True, 29.99, False), (True, 30, True)]:
        w = World(definitions); popup = w.offer()
        w.countries['CDM'].update(gold=funds, is_ai=ai)
        assert w.choose(popup, 0) == allowed
        assert w.countries['CDM']['gold'] >= 0
    passed('acceptance checks exact funds and retains AI treasury reserve')
    for ai, funds, allowed in [(False, 14.99, False), (False, 15, True), (True, 34.99, False), (True, 35, True)]:
        w = World(definitions); popup = w.offer(); w.choose(popup, 1); popup = w.queue.pop(0)
        w.countries['CDM'].update(gold=funds, is_ai=ai)
        assert w.choose(popup, 0) == allowed
        assert w.countries['CDM']['gold'] >= 0
    passed('counteroffer checks its higher price and AI reserve at signing')
    for change in ['war', 'subject', 'rival', 'opinion', 'annexed', 'expired']:
        w = World(definitions); popup = w.offer()
        if change == 'war': w.countries['CDM']['at_war'] = True
        elif change == 'subject': w.countries['CDM']['is_subject'] = True
        elif change == 'rival': w.countries['QBR']['rivals'].add('CDM')
        elif change == 'opinion': w.opinion = 24
        elif change == 'annexed': w.countries['CDM']['exists'] = False
        else: w.day = 180
        assert not w.choose(popup, 0)
        before = deepcopy(w.countries)
        w.choose(popup, 0, force=True)
        assert w.countries == before, change
        w.choose(popup, 2)
        assert w.variable('QBR', 'ga_hb_pending') is None
        passed('invalidated ' + change + ': no debit or rewards; reply closes safely')
    w = World(definitions); stale = w.offer()
    try: w.offer('RHK', 'QBR')
    except AssertionError: pass
    else: raise AssertionError('Simultaneous incoming request accepted')
    try: w.offer('QBR', 'RHK')
    except AssertionError: pass
    else: raise AssertionError('Incoming recipient could start another negotiation')
    raw_effect = next(v for k, _, v in definitions['ga_seek_pilot_bargain'] if k == 'effect')
    before = deepcopy(w.countries)
    w.effects(raw_effect, 'RHK', dict(actor='RHK', target='QBR'))
    assert w.countries == before and not w.queue, 'Stale selector overwrote a pending request'
    w.day = 5 * 365 + 1
    fresh = w.offer()
    before = deepcopy(w.countries)
    w.choose(stale, 2)
    assert w.countries == before, 'Old refusal cleared a newer session'
    w.choose(stale, 0, force=True)
    assert w.countries == before, 'Old acceptance altered a newer session'
    saved = deepcopy(w)
    assert saved.choose(fresh, 0)
    passed('simultaneous, reverse-role, expired and save-state reply isolation')
    # Refusal and one-active-contract constraints are read from the actual selectors.
    w = World(definitions); popup = w.offer(); w.choose(popup, 2); w.day = 3 * 365
    try: w.offer()
    except AssertionError: pass
    else: raise AssertionError('Refusal pair cooldown bypassed')
    w = World(definitions); popup = w.offer(); w.choose(popup, 0); w.day = 3 * 365
    try: w.offer('RHK', 'QBR')
    except AssertionError: pass
    else: raise AssertionError('Second concurrent contract accepted')
    passed('pair refusal lock and one active contract per crown')
    w = World(definitions)
    w.countries['QBR']['vars'].update(ga_offer_pending=(True, None), ga_offer_sender=('CDM', None))
    legacy = ('ga_gathering.2', 'QBR', {})
    w.choose(legacy, 0)
    assert w.countries['CDM']['gold'] == 55 and not w.countries['QBR']['vars']
    w.choose(legacy, 0)
    assert w.countries['CDM']['gold'] == 55, 'Legacy fee refunded twice'
    passed('legacy alliance request closes with one fee refund and no new relation')
    # Maintenance does not depend on the Gathering still being active.
    for reason in ['war', 'annexation', 'rivalry']:
        w = World(definitions); popup = w.offer(); w.choose(popup, 0)
        if reason == 'war': w.countries['CDM']['wars'].add('QBR')
        elif reason == 'annexation': w.countries['QBR']['exists'] = False
        else: w.countries['CDM']['rivals'].add('QBR')
        hook = {k: v for k, _, v in definitions['ga_hb_contract_pulse']}
        assert w.condition(hook['trigger'], 'CDM', {})
        w.effects(hook['effect'], 'CDM', {})
        assert not w.countries['CDM']['modifiers']
        if reason != 'annexation': assert not w.countries['QBR']['modifiers']
        assert (w.countries['CDM']['gold'], w.countries['QBR']['gold']) == (40, 60)
        passed(reason + ': contract ends on monthly hook without refund or popup')
    subset = [definitions['ga_offer_harbor_pact'], definitions['ga_seek_pilot_bargain']]
    subset += [definitions[f'ga_gathering.{n}'] for n in [2, 20, 21, 22, 23, 24, 25]]
    forbidden = {'create_relation', 'make_subject_of', 'every_country', 'any_country', 'create_sub_unit'}
    assert not any(k in forbidden for body in subset for k, _, _ in flatten(body))
    for n in [22, 23]:
        assert not any(k == 'trigger_event_non_silently' and v in ['ga_gathering.20', 'ga_gathering.21', 'ga_gathering.22', 'ga_gathering.23']
                       for k, _, v in flatten(definitions[f'ga_gathering.{n}']))
    passed('no forced relations, units, global scans or counteroffer loops')
    localization = read('main_menu/localization/english/goblins_gathering_l_english.yml')
    for body in subset:
        for key, _, value in flatten(body):
            if key in {'custom_tooltip', 'text'} and isinstance(value, str) and value.startswith('ga_hb_'):
                assert re.search(r'^ ' + re.escape(value) + ':', localization, re.M), value
    passed('compact negotiation and effect tooltips all resolve to player text')
    return {'scenarios': scenarios, 'static_script_simulation_passed': True, 'engine_tested': False}
