"""Execute the delivered Ashen Kinship hook and check the Goblin Horde IO; not an EU5 engine playtest."""
from verify_harbor_bargains import World, parse, flatten


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
            else:
                if k == 'trigger_event_non_silently' and v == 'ga_gathering.42': self.joined.append(country)
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
    # Membership is native IO state; stand it in with a flag the harness can read.
    assert definitions['ga_in_horde'] == [('exists', '=', 'international_organization:goblin_horde'),
        ('is_member_of_international_organization', '=', 'international_organization:goblin_horde')]
    definitions['ga_in_horde'] = [('has_variable', '=', 'horde_member')]
    assert not any(k == 'join_war_as_defender' for k, _, _ in flatten(fields['effect'])), 'the Horde IO joins wars natively'
    scenarios = []

    def declare(attacker, defender, setup=None):
        w = WarWorld(definitions)
        w.countries['POR'] = dict(w.countries['CDM'], vars={}, modifiers={}, rivals=set(), enemies=set(), wars=set(), allies=set())
        for tag in w.countries:
            if tag != 'POR': w.countries[tag]['vars']['horde_member'] = (True, None)
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
    scenarios.append('an outsider declaring on one Horde crown calls the other five, once')
    w = declare('CDM', 'QBR')
    assert not w.joined and not w.queue
    scenarios.append('goblin infighting never triggers kinship')
    w = declare('POR', 'QBR', lambda w: w.countries['RHK']['wars'].add('QBR'))
    assert 'RHK' not in w.joined and len(w.joined) == 4
    scenarios.append('a crown already at war with the victim stays out')
    w = declare('POR', 'QBR', lambda w: w.countries['QBR']['vars'].pop('horde_member'))
    assert not w.joined and not w.queue
    scenarios.append('a crown outside the Horde gets no kinship call')
    horde = {k: v for k, _, v in parse(read('in_game/common/international_organizations/goblins_horde.txt'))}['goblin_horde']
    io = {k: v for k, _, v in horde}
    assert io['unique'] == io['has_leader_country'] == 'yes'
    for key in ['expel_members_who_are_targets_of_other_members', 'expel_members_who_target_the_leader',
                'expel_members_who_are_attackers_at_war_with_other_members', 'expel_members_who_are_defenders_at_war_with_other_members']:
        assert io[key] == 'no', key
    assert 'can_declare_war' not in io, 'members must stay free to fight each other'
    assert ('NOT', '=', [('is_member_of_international_organization', '=', 'root')]) in flatten(io['join_defensive_wars_always'])
    assert io['can_leave_trigger'] == io['auto_disband_trigger'] == [('always', '=', 'no')]
    assert any(k == 'add_country_to_international_organization' for k, _, _ in flatten(io['monthly_effect']))
    scenarios.append('Horde IO: unique, permanent, no expulsions or war ban, defends only against non-members')
    actions = {k: v for k, _, v in parse(read('in_game/common/generic_actions/goblins_horde.txt'))}
    localization = read('main_menu/localization/english/goblins_gathering_l_english.yml')
    for key, body in actions.items():
        fields = {k: v for k, _, v in body if k != 'select_trigger'}
        assert fields['type'] == 'internationalorganization'
        picker = next(v for k, _, v in body if k == 'select_trigger')
        assert ('looking_for_a', '=', 'international_organization') in picker and ('target_flag', '=', 'recipient') in picker
        for loc in [key, key + '_desc']: assert f' {loc}: "' in localization, loc
    for loc in ['goblin_horde', 'goblin_horde_desc', 'GOBLIN_HORDE_LEADER', 'goblin_horde_defense_tt']:
        assert f' {loc}: "' in localization, loc
    assert sorted(actions) == ['ga_horde_appeal_feud', 'ga_horde_ask_calm', 'ga_horde_ask_gold', 'ga_horde_levy', 'ga_horde_muster',
                               'ga_horde_settle_feud', 'ga_horde_tribute', 'ga_horde_war_horns']
    effects = {key: flatten(dict((k, v) for k, _, v in body)['effect']) for key, body in actions.items()}
    second = lambda key: [v for k, _, v in actions[key] if k == 'select_trigger'][1]
    assert ('looking_for_a', '=', 'war') in second('ga_horde_muster') and any(k == 'join_war_as_attacker' for k, _, _ in effects['ga_horde_muster'])
    assert ('looking_for_a', '=', 'country') in second('ga_horde_settle_feud')
    assert ('white_peace', '=', 'scope:ga_horde_feud_war') in effects['ga_horde_settle_feud']
    assert sum(k == 'add_manpower' for k, _, _ in effects['ga_horde_levy']) == 2
    for key in ['ga_horde_muster', 'ga_horde_settle_feud', 'ga_horde_levy', 'ga_horde_war_horns']:
        assert ('is_leader_of_international_organization', '=', 'international_organization:goblin_horde') in flatten(dict((k, v) for k, _, v in actions[key])['allow']), key
    # Petitions: only non-Warchief crowns, each sends a grant/refuse request to the Warchief.
    for key, num in [('ga_horde_ask_gold', 43), ('ga_horde_ask_calm', 44), ('ga_horde_appeal_feud', 45)]:
        allow = flatten(dict((k, v) for k, _, v in actions[key])['allow'])
        assert ('NOT', '=', [('is_leader_of_international_organization', '=', 'international_organization:goblin_horde')]) in allow, key
        assert ('trigger_event_non_silently', '=', f'ga_gathering.{num}') in effects[key], key
        options = [o for k, _, o in definitions[f'ga_gathering.{num}'] if k == 'option']
        replies = [('trigger_event_non_silently', '=', 'ga_gathering.46'), ('trigger_event_non_silently', '=', 'ga_gathering.47')]
        assert len(options) == 2 and [r in flatten(options[i]) for i, r in enumerate(replies)] == [True, True], num
    assert ('white_peace', '=', 'scope:ga_horde_feud_war') in flatten(definitions['ga_gathering.45'])
    for loc in ['ga_horde_aid_given', 'ga_horde_aid_refused']: assert f' {loc}: "' in localization, loc
    scenarios.append('3 petitions for smaller crowns reach the Warchief as grant/refuse events and answer back')
    scenarios.append(f'{len(actions)} Horde panel actions registered and localized; Muster, Feud and Levy use native war, peace and manpower effects')
    return {'scenarios': scenarios, 'static_script_simulation_passed': True, 'engine_tested': False}


if __name__ == '__main__':
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / 'mod'
    for row in verify(lambda p: (root / p).read_text(encoding='utf-8-sig'))['scenarios']:
        print(row)
