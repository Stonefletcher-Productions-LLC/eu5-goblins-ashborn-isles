"""Execute delivered Sworn Pact scripts; this is not an EU5 engine playtest."""
from copy import deepcopy
from verify_harbor_bargains import World, parse, flatten


def verify(read):
    definitions = {}
    for path in ['in_game/common/scripted_triggers/goblins_gathering.txt',
                 'in_game/common/generic_actions/goblins_gathering.txt',
                 'in_game/common/on_action/goblins_gathering.txt',
                 'in_game/events/goblins_gathering.txt']:
        definitions.update({k: v for k, _, v in parse(read(path)) if k != 'namespace'})
    scenarios = []

    def world(allied=True, honored=False, opinion=50):
        w = World(definitions); w.opinion = opinion
        for a, b in [('CDM', 'QBR'), ('QBR', 'CDM')]:
            if allied: w.countries[a]['allies'].add(b)
            if honored: w.countries[a]['vars'][f'ga_cp_honored_{b}'] = (True, None)
        return w

    def blocked(w, action='ga_swear_pact'):
        try: w.offer(action=action)
        except AssertionError: return
        raise AssertionError('Ineligible ' + action + ' accepted')

    def sworn(w):
        return w.variable('CDM', 'ga_sp_sworn_QBR') and w.variable('QBR', 'ga_sp_sworn_CDM')

    def pulse(w, country):
        fields = dict((k, v) for k, _, v in definitions['ga_sp_pact_pulse'])
        if w.condition(fields['trigger'], country, {}):
            w.effects(fields['effect'], country, {})

    def swear(w):
        popup = w.offer(action='ga_swear_pact')
        assert popup[0] == 'ga_gathering.36'
        assert w.choose(popup, 0)
        return popup

    for route in ['alliance', 'bargain']:
        w = world(allied=route == 'alliance', honored=route == 'bargain'); swear(w)
        assert sworn(w)
        assert [e[0] for e in w.queue] == ['ga_gathering.37', 'ga_gathering.37']
        assert ('QBR', 'ga_sworn_pact') in w.countries['CDM']['opinions']
        assert ('CDM', 'ga_sworn_pact') in w.countries['QBR']['opinions']
        for tag in ['CDM', 'QBR']:
            assert not w.variable(tag, 'ga_sp_pending')
        assert sum(c['gold'] for c in w.countries.values()) == 50 * len(w.countries)
        scenarios.append(route + ': both consents record a mirrored pact and native opinion, no gold moves')
    for change in ['strangers', 'opinion', 'rival', 'war', 'subject', 'already_sworn', 'harbor_pending']:
        w = world()
        if change == 'strangers': w = world(allied=False)
        elif change == 'opinion': w.opinion = 49.99
        elif change == 'rival': w.countries['QBR']['rivals'].add('CDM')
        elif change == 'war': w.countries['QBR']['at_war'] = True
        elif change == 'subject': w.countries['QBR']['is_subject'] = True
        elif change == 'already_sworn':
            w.countries['CDM']['vars']['ga_sp_sworn_QBR'] = (True, None)
        else: w.countries['QBR']['vars']['ga_hb_pending'] = (True, None)
        blocked(w); scenarios.append(change + ': oath blocked')
    w = world(); popup = w.offer(action='ga_swear_pact')
    assert w.choose(popup, 1) and not sworn(w)
    assert [e[0] for e in w.queue] == ['ga_gathering.38']
    assert not w.variable('CDM', 'ga_sp_pending') and not w.variable('QBR', 'ga_sp_pending')
    before = deepcopy(w.countries); w.choose(popup, 0, force=True)
    assert w.countries == before
    scenarios.append('refusal notifies the requester, frees both crowns and a stale accept does nothing')
    w = world(); popup = w.offer(action='ga_swear_pact')
    w.countries['CDM']['rivals'].add('QBR')
    assert not w.choose(popup, 0)
    before = deepcopy(w.countries); w.choose(popup, 0, force=True)
    assert w.countries == before
    scenarios.append('rivalry after the offer voids acceptance')
    w = world(); popup = w.offer(action='ga_swear_pact'); w.day = 181
    before = deepcopy(w.countries); w.choose(popup, 0, force=True)
    assert w.countries == before
    scenarios.append('expired offer cannot be accepted')
    # A pact replaces both the alliance requirement and the strength cap.
    w = world(); swear(w); w.queue.clear()
    for c in w.countries.values(): c['allies'].clear()
    w.countries['QBR']['relative_strength'] = 0.95
    w.opinion = 99.99; blocked(w, 'ga_offer_compact')
    w.opinion = 100
    invitation = w.offer(action='ga_offer_compact')
    assert w.choose(invitation, 1); draft = w.queue.pop(0)
    assert w.choose(draft, 0); ratification = w.queue.pop(0)
    assert w.choose(ratification, 1)
    assert w.countries['QBR']['subject_type'] == 'ga_compact_protection'
    scenarios.append('sworn crowns reach a Compact at 100 opinion without alliance or strength cap')
    w = world(); w.countries['QBR']['relative_strength'] = 0.95; w.opinion = 150
    for a, b in [('CDM', 'QBR'), ('QBR', 'CDM')]:
        w.countries[a]['vars'].update({f'ga_cp_honored_{b}': (True, None), f'ga_cp_allied_ready_{b}': (True, None)})
    blocked(w, 'ga_offer_compact')
    scenarios.append('without a pact the 65 percent strength cap still applies')
    for breach in ['war', 'rival', 'enemy']:
        w = world(); swear(w); w.queue.clear()
        if breach == 'war': w.countries['CDM']['wars'].add('QBR')
        elif breach == 'rival': w.countries['CDM']['rivals'].add('QBR')
        else: w.countries['CDM']['enemies'].add('QBR')
        pulse(w, 'CDM'); pulse(w, 'QBR')
        assert not w.variable('CDM', 'ga_sp_sworn_QBR') and not w.variable('QBR', 'ga_sp_sworn_CDM')
        assert [e[1] for e in w.queue if e[0] == 'ga_gathering.39'] == ['CDM', 'QBR']
        assert ('QBR', 'ga_sworn_pact_broken') in w.countries['CDM']['opinions']
        assert ('CDM', 'ga_sworn_pact_broken') in w.countries['QBR']['opinions']
        scenarios.append(breach + ': both crowns lose the pact, are told why and lose its opinion')
    w = world(); swear(w); w.queue.clear(); w.countries['QBR']['exists'] = False
    pulse(w, 'CDM')
    assert not w.variable('CDM', 'ga_sp_sworn_QBR') and not w.queue
    scenarios.append('a vanished partner clears the pact silently')
    w = world(); swear(w); w.queue.clear(); before = deepcopy(w.countries)
    pulse(w, 'CDM'); pulse(w, 'QBR')
    assert w.countries == before and not w.queue
    scenarios.append('a kept pact is untouched by the monthly check')
    return {'scenarios': scenarios, 'static_script_simulation_passed': True, 'engine_tested': False}


if __name__ == '__main__':
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / 'mod'
    for row in verify(lambda p: (root / p).read_text(encoding='utf-8-sig'))['scenarios']:
        print(row)
