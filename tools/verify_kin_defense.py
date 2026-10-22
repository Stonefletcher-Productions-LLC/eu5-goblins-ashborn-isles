"""Execute the delivered Ashen Kinship hook; this is not an EU5 engine playtest."""
from verify_harbor_bargains import World, parse


class WarWorld(World):
    def __init__(self, definitions):
        super().__init__(definitions)
        self.joined = []

    def effects(self, rows, country, scopes):
        rest = []
        for row in rows:
            k, _, v = row
            if k == 'every_country':
                limit = next(value for key, _, value in v if key == 'limit')
                body = [r for r in v if r[0] != 'limit']
                for tag in self.countries:
                    if self.countries[tag]['exists'] and self.condition(limit, tag, scopes):
                        self.effects(body, tag, scopes)
            elif k == 'join_war_as_defender':
                fields = {key: value for key, _, value in v}
                assert fields['war'] == 'scope:war'
                self.joined.append(country)
                self.countries[country]['wars'].add(scopes['actor'])
            else:
                self.effects_base([row], country, scopes)

    def effects_base(self, rows, country, scopes):
        World.effects(self, rows, country, scopes)


def verify(read):
    definitions = {}
    for path in ['in_game/common/scripted_triggers/goblins_gathering.txt',
                 'in_game/common/on_action/goblins_gathering.txt',
                 'in_game/events/goblins_gathering.txt']:
        definitions.update({k: v for k, _, v in parse(read(path)) if k != 'namespace'})
    hooks = [v for k, _, v in parse(read('in_game/common/on_action/goblins_gathering.txt')) if k == 'on_war_declared']
    assert hooks == [[('on_actions', '=', [('ga_kin_defense', None, None)])]]
    fields = dict((k, v) for k, _, v in definitions['ga_kin_defense'])
    scenarios = []

    def declare(attacker, defender, setup=None):
        w = WarWorld(definitions)
        w.countries['POR'] = dict(w.countries['CDM'], vars={}, modifiers={}, rivals=set(), enemies=set(), wars=set(), allies=set())
        if setup: setup(w)
        scopes = dict(actor=attacker, recipient=defender)
        # The engine fires the hook for every country; only the defender's run acts.
        for root in list(w.countries):
            if w.condition(fields['trigger'], root, dict(scopes)):
                w.effects(fields['effect'], root, dict(scopes))
        return w

    # The roster check (ga_is_goblin) uses tags; POR stands in for a European crown.
    w = declare('POR', 'QBR')
    assert sorted(w.joined) == ['CDM', 'GTF', 'RHK', 'SFK', 'SWK']
    assert [e[0] for e in w.queue].count('ga_gathering.42') == 5
    assert [e[0] for e in w.queue].count('ga_gathering.41') == 1
    assert all('ga_kin_rally' in c['modifiers'] for t, c in w.countries.items() if t != 'POR')
    assert len(w.countries['QBR']['opinions']) == 5
    scenarios.append('an outsider declaring on one crown draws in the other five, once')
    w = declare('CDM', 'QBR')
    assert not w.joined and not w.queue
    scenarios.append('goblin infighting never triggers kinship')
    w = declare('POR', 'QBR', lambda w: w.countries['RHK']['wars'].add('QBR'))
    assert 'RHK' not in w.joined and len(w.joined) == 4
    scenarios.append('a crown already at war with the victim stays out')
    w = declare('POR', 'QBR', lambda w: w.countries['SFK'].update(is_subject=True))
    assert 'SFK' not in w.joined
    scenarios.append('subject crowns follow their overlord, not kinship')
    w = declare('POR', 'QBR', lambda w: w.countries['GTF']['wars'].add('POR'))
    assert 'GTF' not in w.joined
    scenarios.append('a crown already fighting the invader is not re-added')
    return {'scenarios': scenarios, 'static_script_simulation_passed': True, 'engine_tested': False}


if __name__ == '__main__':
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / 'mod'
    for row in verify(lambda p: (root / p).read_text(encoding='utf-8-sig'))['scenarios']:
        print(row)
