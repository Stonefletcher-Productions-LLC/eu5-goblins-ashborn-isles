"""Pair-specific trust history and three-stage voluntary Compact charters."""
import harbor_bargains as hb
import sworn_pacts as sp

OPINION = 100

TYPES = {'autonomy': ('Autonomy Charter', '0.5', '20', 'ga_compact_autonomy_tribute'),
         'protection': ('Protection Charter', '1', '10', 'subject_pays_vassal')}
DESCRIPTIONS = {
    'autonomy': 'Half the normal base vassal tribute; no annexation for 20 years, then half normal integration speed. The ruling house and succession customs remain. Normal vassal military obligations apply.',
    'protection': 'Normal vassal tribute and integration rules; exemption from offensive wars, protection against external attackers and fellow subjects, and +10% defensiveness. The protector takes -5% army maintenance efficiency while this charter lasts. The ruling house and succession customs remain.'}


def history(other, fields=('honored', 'allied_ready')):
    return 'OR = { ' + ' '.join(f'AND = {{ {other} = {{ tag = {tag} }} ' + ' '.join(f'has_variable = ga_cp_{field}_{tag}' for field in fields) + ' }' for tag in hb.TAGS) + ' }'


def eligible(actor, target, explain=False):
    def check(key, body):
        return f'custom_tooltip = {{ text = ga_ui_{key}_tt {body} }}' if explain else body
    def bound(other):
        # Ladder route: a Sworn Pact. Original route: alliance, honored bargain and alliance age.
        allied = f'is_allied_with = {{ target = {other} }} ' + history(other)
        return check('bound', f'OR = {{ {sp.sworn(other)} AND = {{ {allied} }} }}')
    def side(me, other):
        return f'''{check('independent', 'ga_independent_goblin = yes')}
        {check('peace', 'at_war = no')}
        {check('harbor_free', 'NOT = { has_variable = ga_hb_pending }')}
        {check('friendly', f'NOT = {{ is_rival_of = scope:{other} }} NOT = {{ is_enemy_of = scope:{other} }}')}
        {bound('scope:' + other)}'''
    return f'''scope:{actor} = {{
        {side(actor, target)}
    }}
    scope:{target} = {{
        {side(target, actor)}
        {check('opinion', f'"opinion(scope:{actor})" >= {OPINION}')}
        {check('strength', f'OR = {{ {sp.sworn('scope:' + actor)} relative_strength = {{ target = scope:{actor} value <= 0.65 }} }}')}
        {check('rank', f'scope:{actor}.country_rank_level >= country_rank_level')}
    }}'''


def triggers():
    session = hb.triggers().split('ga_hb_session_matches = {', 1)[1].split('\nga_hb_valid =', 1)[0]
    return ('\nga_cp_session_matches = {' + session).replace('ga_hb_', 'ga_cp_') + '''
ga_cp_free = {
    custom_tooltip = { text = ga_ui_independent_tt ga_independent_goblin = yes }
    custom_tooltip = { text = ga_ui_peace_tt at_war = no }
    custom_tooltip = { text = ga_ui_compact_free_tt NOT = { has_variable = ga_cp_pending } }
    custom_tooltip = { text = ga_ui_harbor_free_tt NOT = { has_variable = ga_hb_pending } }
    custom_tooltip = { text = ga_ui_legacy_free_tt NOT = { has_variable = ga_offer_pending } }
    custom_tooltip = { text = ga_ui_quiet_tt NOT = { has_variable = ga_cp_recent_offer } }
}
ga_cp_valid = {
    ga_cp_session_matches = yes
    ''' + eligible('ga_cp_requester', 'ga_cp_provider') + '\n}\n'


def stage(n):
    return f'ga_cp_valid = yes scope:ga_cp_requester = {{ var:ga_cp_stage = {n} }}'


def cleanup():
    return hb.cleanup().replace('ga_hb_', 'ga_cp_').replace('remove_variable = ga_cp_countered', 'remove_variable = ga_cp_countered remove_variable = ga_cp_stage')


def close(other):
    return hb.decline(other.replace('ga_cp_', 'ga_hb_')).replace('ga_hb_', 'ga_cp_').replace('ga_gathering.25', 'ga_gathering.35')


def action(make, picker):
    locks = hb.lock_check().replace('ga_hb_', 'ga_cp_')
    reverse = hb.lock_check('scope:target').replace('ga_hb_', 'ga_cp_')
    conditions = f'''ga_cp_free = yes custom_tooltip = {{ text = ga_ui_pair_wait_tt {locks} }}
        scope:actor = {{ ga_cp_free = yes custom_tooltip = {{ text = ga_ui_pair_wait_tt {reverse} }} }}
        {eligible('actor', 'target', explain=True)}'''
    begin = hb.start(30).replace('ga_hb_', 'ga_cp_')
    # The stage is set before dispatching the invitation.
    begin = begin.replace('scope:target = { trigger_event_non_silently',
                          'scope:actor = { set_variable = { name = ga_cp_stage value = 1 days = 180 } }\n scope:target = { trigger_event_non_silently')
    effect = f'hidden_effect = {{ if = {{ limit = {{ scope:target = {{ {conditions} }} }} {begin} }} }}'
    # Keep existing crowns visible; the native disabled-target tooltip explains each unmet rule.
    selector = '''select_trigger = {
        looking_for_a = country
        interaction_source_list = { ''' + ' '.join(f'c:{tag} ?= {{ add_to_list = source }}' for tag in hb.TAGS) + ''' }
        target_flag = target name = ga_choose_kingdom none_available_msg_key = ga_ui_no_crown
        column = { data = name }
        show_why_not_enabled = yes
        visible = { ga_is_goblin = yes this != scope:actor country_exists = this }
        enabled = { ''' + conditions + ''' }
    }'''
    return make('ga_offer_compact', 'Open Compact Talks',
        'Step 3 of 3 on the road to one crown.\n'
        'Invite a sworn or long-allied crown to become your subject under a charter.\n\n'
        'Requires one of:\n'
        '- a Sworn Pact between the two crowns, or\n'
        '- a completed Harbor Bargain plus three observed years of alliance.\n'
        f'The smaller crown needs {OPINION}+ opinion of you and no higher rank.\n'
        'Without a Sworn Pact it must also have at most 65% of your strength.\n\n'
        'It chooses autonomy or protection terms, you accept or refuse, and it\n'
        'ratifies or withdraws. No fee. Talks expire after 180 days, with a\n'
        'two-year quiet period and a five-year wait for the same pair.',
        effect, selector, allow='ga_cp_free = yes', ai='add = 10', years=2)


def events(event, option, loc):
    loc('ga_cp_ready_tt', f'These talks remain valid: both crowns are still independent, at peace and bound by a Sworn Pact or a proven alliance, with {OPINION} opinion and the required rank and strength.')
    result = []
    def choice(n, suffix, name, effects, condition='', ai='factor = 1', tip=None):
        if tip:
            key = loc(f'ga_cp_{n}_{suffix}_terms_tt', tip)
            prefix = 'custom_tooltip = ' + key
        else: prefix = ''
        guard = 'custom_tooltip = { text = ga_cp_ready_tt ' + condition + ' }' if condition else ''
        return option(n, suffix, name, (prefix + '\n' if prefix else '') + 'hidden_effect = { ' + effects + ' }', guard, ai)
    choices = []
    for i, kind in enumerate(TYPES, 1):
        effects = f'''if = {{ limit = {{ {stage(1)} }}
            save_scope_value_as = {{ name = ga_cp_charter value = {i} }}
            scope:ga_cp_requester = {{
                set_variable = {{ name = ga_cp_stage value = 2 days = 180 }}
                trigger_event_non_silently = ga_gathering.{30+i}
            }}
        }}'''
        ai = 'factor = 3 modifier = { factor = 2 tag = SFK }' if kind == 'autonomy' else 'factor = 3'
        choices.append(choice(30, kind, 'Ask for the '+TYPES[kind][0]+'.', effects, stage(1), ai, DESCRIPTIONS[kind]))
    choices.append(choice(30, 'refuse', 'Our alliance is enough. Keep our independence.', close('ga_cp_requester'), ai='factor = 2'))
    result.append(event(30, 'A Seat Beneath Another Crown?',
        "[SCOPE.sCountry('ga_cp_requester').GetName] invites us into the Compact. Years of cooperation make this worth discussing, but friendship does not purchase our crown. Choose the guarantees we require, or remain independent. Selecting terms is not submission.", '\n'.join(choices)))
    for i, kind in enumerate(TYPES, 1):
        effects = f'''if = {{ limit = {{ {stage(2)} scope:ga_cp_charter = {i} }}
            scope:ga_cp_requester = {{ set_variable = {{ name = ga_cp_stage value = 3 days = 180 }} }}
            scope:ga_cp_provider = {{ trigger_event_non_silently = ga_gathering.33 }}
        }}'''
        result.append(event(30+i, 'The Smaller Crown Names Its Price',
            "[SCOPE.sCountry('ga_cp_provider').GetName] asks for the " + TYPES[kind][0] + '. ' + DESCRIPTIONS[kind] +
            ' These obligations are part of the subject relationship, not a temporary loyalty reward. Accept the draft or walk away. The smaller crown must still ratify it.',
            choice(30+i, 'a', 'Accept these obligations; send the charter for ratification.', effects,
                   stage(2) + f' scope:ga_cp_charter = {i}', 'factor = 3', DESCRIPTIONS[kind]) + '\n' +
            choice(30+i, 'b', 'Those concessions cost too much. End the talks.', close('ga_cp_provider'))))
    grants = []
    for i, kind in enumerate(TYPES, 1):
        grants.append(f'''if = {{ limit = {{ scope:ga_cp_charter = {i} }}
            make_subject_of = {{ target = scope:ga_cp_requester type = subject_type:ga_compact_{kind} }}
        }}''')
    final = f'''if = {{ limit = {{ {stage(3)} OR = {{ scope:ga_cp_charter = 1 scope:ga_cp_charter = 2 }} }}
        {' '.join(grants)}
        set_variable = {{ name = has_locked_subject_type value = yes }}
        set_variable = {{ name = ga_cp_owns_type_lock value = yes }}
        {cleanup()}
        scope:ga_cp_requester = {{ trigger_event_non_silently = ga_gathering.34 }}
    }}'''
    result.append(event(33, 'The Charter Awaits Our Seal',
        "[SCOPE.sCountry('ga_cp_requester').GetName] has accepted our chosen charter. We now decide whether to ratify it. Our ruling house and succession customs remain, but we become a subject. The chosen tribute, military obligations and integration limits will govern this relationship. We may still withdraw without paying a fee.",
        '\n'.join(choice(33, kind, 'Ratify the '+TYPES[kind][0]+'.', final,
                           stage(3)+f' scope:ga_cp_charter = {i}', 'factor = 10', DESCRIPTIONS[kind])
                  for i, kind in enumerate(TYPES, 1)) + '\n' +
        choice(33, 'withdraw', 'We will remain an independent ally.', close('ga_cp_requester'))))
    result.append(event(34, 'Two Seals, One Compact',
        "[SCOPE.sCountry('ga_cp_provider').GetName] has ratified its charter beneath [SCOPE.sCountry('ga_cp_requester').GetName]. The relationship now carries the negotiated obligations. Its territory counts toward Ashborn unification; its house and customs endure. No bonus prestige or loyalty is awarded.", option(34, 'a', 'Honor the charter.', 'hidden_effect = { }')))
    result.append(event(35, 'Compact Talks End',
        'The proposed charter was refused or the conditions changed. No submission or payment took place. Existing alliances remain. A live refusal protects the pair from another approach for five years.', option(35, 'a', 'Respect the other crown.', 'hidden_effect = { }')))
    return result


def pulse():
    checks = []
    for tag in hb.TAGS:
        allied = f'country_exists = c:{tag} NOT = {{ tag = {tag} }} is_allied_with = {{ target = c:{tag} }}'
        tracked, timer, ready = (f'ga_cp_allied_{s}_{tag}' for s in ['tracking', 'timer', 'ready'])
        checks.append(f'''if = {{ limit = {{ {allied} }}
            if = {{ limit = {{ NOT = {{ has_variable = {tracked} }} }}
                set_variable = {{ name = {tracked} value = yes }}
                set_variable = {{ name = {timer} value = yes years = 3 }} }}
            if = {{ limit = {{ NOT = {{ has_variable = {timer} }} }}
                set_variable = {{ name = {ready} value = yes }} }}
        }}
        if = {{ limit = {{ NOT = {{ {allied} }} }}
            remove_variable = {tracked} remove_variable = {timer} remove_variable = {ready}
        }}''')
    return '''
ga_cp_history_pulse = {
    trigger = { ga_is_goblin = yes }
    effect = {
        ''' + '\n'.join(checks) + '''
        if = { limit = { has_variable = ga_cp_owns_type_lock
            NOT = { OR = { is_subject_type = ga_compact_autonomy is_subject_type = ga_compact_protection } } }
            remove_variable = has_locked_subject_type remove_variable = ga_cp_owns_type_lock
        }
    }
}
'''


def extra(out, write, loc):
    def append(path, text):
        write(out, path, (out/path).read_text(encoding='utf-8-sig') + '\n' + text)
    for path in ['in_game/common/scripted_triggers/goblins_gathering.txt', 'in_game/common/situations/goblins_gathering.txt']:
        text = (out/path).read_text(encoding='utf-8-sig')
        write(out, path, text.replace('is_subject_type = vassal',
            'OR = { is_subject_type = vassal is_subject_type = ga_compact_autonomy is_subject_type = ga_compact_protection }'))
    rows = []
    for kind, (name, speed, years, price) in TYPES.items():
        rows.append(f'''ga_compact_{kind} = {{
            color = subject_vassal level = 2 subject_pays = {price}
            visible = {{ always = no }} creation_visible = {{ always = no }}
            visible_through_diplomacy = {{ always = no }} visible_through_treaty = {{ always = no }}
            has_overlords_ruler = no has_limited_diplomacy = yes
            can_change_heir_selection = yes can_change_rank = no
            overlord_can_cancel = yes will_join_independence_wars = yes
            overlord_protects_external = yes overlord_protects_other_subjects = yes
            join_defensive_wars_always = {{ always = yes }}
            join_offensive_wars_always = {{ always = {'yes' if kind == 'autonomy' else 'no'} }}
            join_offensive_wars_can_call = {{ always = no }}
            allow_declaring_wars = {{ always = no }}
            annexation_speed = {speed} annexation_min_years_before = {years}
            annexation_min_opinion = 150 annexation_stall_opinion = 125
            diplomatic_capacity_cost_scale = 1.0 strength_vs_overlord = -0.5
            fleet_basing_rights = yes food_access = yes great_power_score_transfer = 0.25
            can_overlord_build_roads = yes can_overlord_build_buildings = yes can_overlord_build_rgos = yes
            subject_modifier = {{ country_cabinet_efficiency = -0.20 {'global_defensive = 0.10' if kind == 'protection' else ''} }}
            {'overlord_modifier = { army_maintenance_efficiency = -0.05 }' if kind == 'protection' else ''}
        }}''')
        loc('ga_compact_'+kind, name)
        loc('ga_compact_'+kind+'_desc', DESCRIPTIONS[kind])
    write(out, 'in_game/common/subject_types/goblins_gathering.txt', '\n'.join(rows))
    append('in_game/common/prices/goblins_gathering.txt', 'ga_compact_autonomy_tribute = { scaled_gold = 0.1 ignore_inflation = yes }')
    append('main_menu/common/modifier_type_definitions/goblins_gathering.txt', 'ga_compact_autonomy_tribute_cost_modifier = { color = bad percent = yes game_data = { category = country } }')
    loc('ga_compact_autonomy_tribute', 'Autonomy Charter Tribute')
    loc('MODIFIER_TYPE_NAME_ga_compact_autonomy_tribute_cost_modifier', 'Autonomy Charter Tribute Cost')
    loc('MODIFIER_TYPE_DESC_ga_compact_autonomy_tribute_cost_modifier', 'Changes the tribute paid under an Autonomy Charter.')
