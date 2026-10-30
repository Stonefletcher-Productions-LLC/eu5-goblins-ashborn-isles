"""Execute delivered Compact scripts; this is not an EU5 engine playtest."""
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
    # Sworn Pacts (0.6.7) lowered the Compact opinion bar; released bundles keep 150.
    threshold = 100 if 'ga_swear_pact' in definitions else 150
    def pulse(w, hook, country):
        fields = dict((k, v) for k, _, v in definitions[hook])
        if w.condition(fields['trigger'], country, {}):
            w.effects(fields['effect'], country, {})
    def alliance(w, yes=True):
        for a, b in [('CDM', 'QBR'), ('QBR', 'CDM')]:
            getattr(w.countries[a]['allies'], 'add' if yes else 'discard')(b)
    def ready():
        w = World(definitions); alliance(w); w.opinion = 150
        for a, b in [('CDM', 'QBR'), ('QBR', 'CDM')]:
            w.countries[a]['vars'].update({f'ga_cp_honored_{b}': (True, None),
                                           f'ga_cp_allied_ready_{b}': (True, None)})
        return w
    def blocked(w):
        try: w.offer(action='ga_offer_compact')
        except AssertionError: return
        raise AssertionError('Ineligible Compact offer accepted')
    def start(w): return w.offer(action='ga_offer_compact')
    def advance(w, event, option):
        assert w.choose(event, option), event
        return w.queue.pop(0)
    # Exercise the real route, without injecting eligibility history.
    for kind in [0, 1]:
        w = World(definitions); alliance(w); w.opinion = 150
        for c in ['CDM', 'QBR']: pulse(w, 'ga_cp_history_pulse', c)
        offer = w.offer(); w.choose(offer, 0); w.queue.clear()
        w.day = 3 * 365 - 1
        pulse(w, 'ga_cp_history_pulse', 'CDM')
        assert not w.variable('CDM', 'ga_cp_allied_ready_QBR')
        w.day += 1
        for c in ['CDM', 'QBR']: pulse(w, 'ga_cp_history_pulse', c)
        blocked(w)
        w.day = 5 * 365 - 1; pulse(w, 'ga_hb_contract_pulse', 'CDM'); blocked(w)
        w.day += 1; pulse(w, 'ga_hb_contract_pulse', 'CDM')
        assert w.variable('CDM', 'ga_cp_honored_QBR') and w.variable('QBR', 'ga_cp_honored_CDM')
        invitation = start(w)
        draft = advance(w, invitation, kind)
        assert not w.countries['QBR']['is_subject']
        ratification = advance(w, draft, 0)
        assert not w.countries['QBR']['is_subject']
        snapshot = deepcopy(w)
        assert snapshot.choose(ratification, kind)
        assert snapshot.countries['QBR']['subject_type'] == ['ga_compact_autonomy', 'ga_compact_protection'][kind]
        assert snapshot.variable('QBR', 'has_locked_subject_type')
        before = deepcopy(snapshot.countries)
        snapshot.choose(ratification, kind, force=True)
        assert snapshot.countries == before
        assert sum(c['gold'] for c in snapshot.countries.values()) == 50 * len(snapshot.countries)
        scenarios.append(['autonomy', 'protection'][kind] + ': five-year bargain, overlapping three-year alliance, two consents, ratification, repeat protection')
    for change in ['war', 'reverse_rival', 'annexed', 'legacy', 'mismatched_partner']:
        w = World(definitions); offer = w.offer(); w.choose(offer, 0)
        if change == 'war': w.countries['CDM']['wars'].add('QBR')
        elif change == 'reverse_rival': w.countries['QBR']['rivals'].add('CDM')
        elif change == 'annexed': w.countries['QBR']['exists'] = False
        elif change == 'legacy':
            for c in w.countries.values(): c['vars'].pop('ga_hb_tracks_term', None)
        else: w.countries['QBR']['vars']['ga_hb_contract_partner'] = ('RHK', None)
        w.day = 5 * 365
        pulse(w, 'ga_hb_contract_pulse', 'CDM')
        assert not w.variable('CDM', 'ga_cp_honored_QBR')
        assert not w.variable('QBR', 'ga_cp_honored_CDM')
        scenarios.append(change + ': no unearned contract history')
    w = ready(); pulse(w, 'ga_cp_history_pulse', 'CDM'); alliance(w, False)
    pulse(w, 'ga_cp_history_pulse', 'CDM')
    assert not w.variable('CDM', 'ga_cp_allied_ready_QBR')
    alliance(w); pulse(w, 'ga_cp_history_pulse', 'CDM'); blocked(w)
    assert w.variable('CDM', 'ga_cp_allied_timer_QBR')
    scenarios.append('observed alliance break resets the full three-year timer')
    for change in ['opinion', 'strength', 'rank', 'war', 'subject', 'alliance', 'history', 'wrong_pair', 'harbor_pending']:
        w = ready()
        if change == 'opinion': w.opinion = threshold - .01
        elif change == 'strength': w.countries['QBR']['relative_strength'] = .6501
        elif change == 'rank': w.countries['QBR']['country_rank_level'] = 3
        elif change == 'war': w.countries['CDM']['at_war'] = True
        elif change == 'subject': w.countries['QBR']['is_subject'] = True
        elif change == 'alliance': alliance(w, False)
        elif change in ['history', 'wrong_pair']:
            w.countries['QBR']['vars'].pop('ga_cp_honored_CDM')
            if change == 'wrong_pair': w.countries['QBR']['vars']['ga_cp_honored_RHK'] = (True, None)
        else: w.countries['QBR']['vars']['ga_hb_pending'] = (True, None)
        blocked(w); scenarios.append(change + ': entry blocked')
    w = ready(); w.opinion = threshold; w.countries['QBR']['relative_strength'] = .65; start(w)
    scenarios.append(f'{threshold} opinion and exactly 65 percent strength are eligible')
    for stage in [1, 2, 3]:
        for invalid in [False, True]:
            w = ready(); event = start(w)
            if stage >= 2: event = advance(w, event, 0)
            if stage >= 3: event = advance(w, event, 0)
            if invalid:
                alliance(w, False); before = deepcopy(w.countries)
                w.choose(event, 0, force=True)
                assert w.countries == before
            assert w.choose(event, 1 if stage == 2 else 2)
            assert not w.countries['QBR']['is_subject']
            assert sum(c['gold'] for c in w.countries.values()) == 50 * len(w.countries)
            assert not w.variable('CDM', 'ga_cp_pending')
            assert not w.variable('QBR', 'ga_cp_pending')
            w.day = 3 * 365; blocked(w)
            scenarios.append(f'stage {stage}: {"invalidated" if invalid else "voluntary"} refusal is free and locks pair')
    w = ready(); stale = start(w)
    try: w.offer('RHK', 'QBR')
    except AssertionError: pass
    else: raise AssertionError('Harbor negotiation overlapped Compact')
    w.day = 180; before = deepcopy(w.countries); w.choose(stale, 0, force=True)
    assert w.countries == before
    w.day = 5 * 365 + 1; fresh = start(w); before = deepcopy(w.countries)
    w.choose(stale, 2); w.choose(stale, 0, force=True)
    assert w.countries == before and w.choose(fresh, 1)
    scenarios.append('expiry, concurrent Harbor talks and stale replies cannot overwrite new talks')
    w = World(definitions)
    w.countries['QBR']['vars'].update(ga_offer_pending=(True, None), ga_offer_sender=('CDM', None))
    legacy = ('ga_gathering.3', 'QBR', {})
    w.choose(legacy, 0); w.choose(legacy, 0)
    assert w.countries['CDM']['gold'] == 60 and not w.countries['QBR']['is_subject']
    scenarios.append('legacy pending Compact refunds ten gold once without submission')
    w = ready(); w.countries['QBR']['vars'].update(has_locked_subject_type=(True, None), ga_cp_owns_type_lock=(True, None))
    pulse(w, 'ga_cp_history_pulse', 'QBR')
    assert not w.variable('QBR', 'has_locked_subject_type')
    scenarios.append('release removes only a Compact-owned subject type lock')
    types = {k: dict((key, value) for key, _, value in v) for k, _, v in parse(read('in_game/common/subject_types/goblins_gathering.txt'))}
    auto, prot = [types['ga_compact_'+k] for k in ['autonomy', 'protection']]
    assert (auto['annexation_speed'], auto['annexation_min_years_before']) == ('0.5', '20')
    assert (prot['annexation_speed'], prot['annexation_min_years_before']) == ('1', '10')
    assert auto['subject_pays'] == 'ga_compact_autonomy_tribute' and prot['subject_pays'] == 'subject_pays_vassal'
    assert ('scaled_gold', '=', '0.1') in dict((k, v) for k, _, v in parse(read('in_game/common/prices/goblins_gathering.txt')))['ga_compact_autonomy_tribute']
    assert prot['join_offensive_wars_always'] == prot['join_offensive_wars_can_call'] == [('always', '=', 'no')]
    # EU5 1.4 removed overlord_protects_external/_other_subjects; defensive calls carry protection.
    assert not any(k.startswith('overlord_protects') for t in types.values() for k in t)
    assert prot['join_defensive_wars_always'] == [('always', '=', 'yes')]
    assert ('army_maintenance_efficiency', '=', '-0.05') in prot['overlord_modifier']
    assert ('global_defensive', '=', '0.10') in prot['subject_modifier']
    assert all(t['has_overlords_ruler'] == 'no' for t in types.values())
    scenarios.append('charter costs, military obligations and integration restrictions registered')
    return {'scenarios': scenarios, 'static_script_simulation_passed': True, 'engine_tested': False,
            'history_sampling': 'monthly; short alliance or hostility changes between samples can be missed'}
