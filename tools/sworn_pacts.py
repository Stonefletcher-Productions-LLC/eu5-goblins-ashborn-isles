"""Sworn Pacts: the middle rung of the pact ladder (Bargain -> Sworn Pact -> Compact).

A pact is a mutual oath between two independent crowns. It never creates a subject
or an alliance; it records trust that eases Compact talks and shows in the panel.
"""
from ashborn_roster import TAGS

OPINION = 50          # mutual opinion needed to swear
OATH_BONUS = 40       # native opinion bias, shown in the diplomacy view
OATH_MONTHS = 120


def sworn(other):
    """True when the current crown holds a Sworn Pact with `other`."""
    return 'OR = { ' + ' '.join(f'AND = {{ {other} = {{ tag = {tag} }} has_variable = ga_sp_sworn_{tag} }}' for tag in TAGS) + ' }'


def foundation(other):
    honored = ' '.join(f'AND = {{ {other} = {{ tag = {tag} }} has_variable = ga_cp_honored_{tag} }}' for tag in TAGS)
    return f'OR = {{ is_allied_with = {{ target = {other} }} {honored} }}'


def eligible(actor, target, explain=False):
    def check(key, body):
        return f'custom_tooltip = {{ text = ga_ui_{key}_tt {body} }}' if explain else body
    def side(me, other):
        return f'''scope:{me} = {{
        {check('independent', 'ga_independent_goblin = yes')}
        {check('peace', 'at_war = no')}
        {check('pact_free', 'NOT = { has_variable = ga_sp_pending }')}
        {check('harbor_free', 'NOT = { has_variable = ga_hb_pending }')}
        {check('friendly', f'NOT = {{ is_rival_of = scope:{other} }} NOT = {{ is_enemy_of = scope:{other} }}')}
        {check('pact_opinion', f'"opinion(scope:{other})" >= {OPINION}')}
    }}'''
    return f'''{side(actor, target)}
    {side(target, actor)}
    scope:{actor} = {{
        {check('pact_foundation', foundation('scope:' + target))}
        {check('not_sworn', 'NOT = { ' + sworn('scope:' + target) + ' }')}
    }}'''


def triggers():
    # Saved scopes plus partner variables reject stale or crossed replies.
    return '''
ga_sp_session_matches = {
    country_exists = scope:ga_sp_requester
    country_exists = scope:ga_sp_provider
    scope:ga_sp_requester = { has_variable = ga_sp_pending var:ga_sp_partner = scope:ga_sp_provider }
    scope:ga_sp_provider = { has_variable = ga_sp_pending var:ga_sp_offer_from = scope:ga_sp_requester }
}
ga_sp_valid = {
    ga_sp_session_matches = yes
    scope:ga_sp_requester = {
        ga_independent_goblin = yes at_war = no
        NOT = { is_rival_of = scope:ga_sp_provider } NOT = { is_enemy_of = scope:ga_sp_provider }
        NOT = { ''' + sworn('scope:ga_sp_provider') + ''' }
    }
    scope:ga_sp_provider = {
        ga_independent_goblin = yes at_war = no
        NOT = { is_rival_of = scope:ga_sp_requester } NOT = { is_enemy_of = scope:ga_sp_requester }
    }
}
'''


def mark(other):
    return '\n'.join(f'if = {{ limit = {{ scope:{other} = {{ tag = {tag} }} }} set_variable = {{ name = ga_sp_sworn_{tag} value = yes }} }}' for tag in TAGS)


def cleanup():
    return '''scope:ga_sp_requester ?= {
        if = { limit = { has_variable = ga_sp_partner var:ga_sp_partner = scope:ga_sp_provider } remove_variable = ga_sp_pending remove_variable = ga_sp_partner }
    }
    scope:ga_sp_provider ?= {
        if = { limit = { has_variable = ga_sp_offer_from var:ga_sp_offer_from = scope:ga_sp_requester } remove_variable = ga_sp_pending remove_variable = ga_sp_offer_from }
    }'''


def action(make):
    conditions = eligible('actor', 'target', explain=True)
    effect = f'''hidden_effect = {{ if = {{ limit = {{ {eligible('actor', 'target')} }}
        scope:actor = {{
            save_scope_as = ga_sp_requester
            set_variable = {{ name = ga_sp_pending value = yes days = 180 }}
            set_variable = {{ name = ga_sp_partner value = scope:target days = 180 }}
        }}
        scope:target = {{
            save_scope_as = ga_sp_provider
            set_variable = {{ name = ga_sp_pending value = yes days = 180 }}
            set_variable = {{ name = ga_sp_offer_from value = scope:actor days = 180 }}
            trigger_event_non_silently = ga_gathering.36
        }}
    }} }}'''
    selector = '''select_trigger = {
        looking_for_a = country
        interaction_source_list = { ''' + ' '.join(f'c:{tag} ?= {{ add_to_list = source }}' for tag in TAGS) + ''' }
        target_flag = target name = ga_choose_kingdom none_available_msg_key = ga_ui_no_crown
        column = { data = name }
        show_why_not_enabled = yes
        visible = { ga_is_goblin = yes this != scope:actor country_exists = this }
        enabled = { ''' + conditions + ''' }
    }'''
    ai = '''add = 10
        if = { limit = { exists = scope:target }
            add = { value = "scope:actor.opinion(scope:target)" multiply = 0.2 desc = ga_relations }
        }'''
    return make('ga_swear_pact', 'Swear a Sworn Pact',
        'Step 2 of 3 on the road to one crown.\n'
        'Bind another independent Ashborn crown by oath. No gold, no subjects.\n\n'
        f'Requires: an alliance or a completed Harbor Bargain with them, and {OPINION}+ opinion both ways.\n'
        f'Both crowns gain +{OATH_BONUS} opinion of each other for ten years.\n\n'
        'A Sworn Pact eases Compact talks: no strength check, and either crown can '
        'later open talks without an alliance. War or rivalry between the two '
        'crowns breaks the pact. Offers expire after 180 days.',
        effect, selector, allow='ga_sp_free = yes', ai=ai, years=2)


def events(event, option, loc):
    loc('ga_sp_ready_tt', 'This offer is still open and both crowns remain independent, at peace and friendly.')
    guard = 'custom_tooltip = { text = ga_sp_ready_tt ga_sp_valid = yes }'
    terms = loc('ga_sp_terms_tt', f'Both crowns record a #Y Sworn Pact#!. Each gains #G +{OATH_BONUS}#! opinion of the other for ten years.\nCompact talks between us no longer check relative strength or need an alliance.\nWar or rivalry between us breaks the pact.')
    swear = f'''if = {{ limit = {{ ga_sp_valid = yes }}
        scope:ga_sp_requester = {{
            {mark('ga_sp_provider')}
            add_opinion = {{ target = scope:ga_sp_provider modifier = ga_sworn_pact }}
        }}
        scope:ga_sp_provider = {{
            {mark('ga_sp_requester')}
            add_opinion = {{ target = scope:ga_sp_requester modifier = ga_sworn_pact }}
        }}
        {cleanup()}
        scope:ga_sp_requester = {{ trigger_event_non_silently = ga_gathering.37 }}
        scope:ga_sp_provider = {{ trigger_event_non_silently = ga_gathering.37 }}
    }}'''
    refuse = f'''if = {{ limit = {{ ga_sp_session_matches = yes }}
        scope:ga_sp_requester = {{ trigger_event_non_silently = ga_gathering.38 }}
    }}
    {cleanup()}'''
    result = [event(36, 'An Oath Across the Water',
        "[SCOPE.sCountry('ga_sp_requester').GetName] asks our crown to swear a Sworn Pact. Envoys would carry embers from each royal hearth to the other, and our captains would name each other kin before the Hunger Below.\n\n"
        "A pact is not submission. We keep our crown, our laws and our alliances. But a sworn crown is a trusted crown: if either of us later opens Compact talks, no one will weigh which of us is stronger.",
        option(36, 'a', 'Carry the embers. We swear.', 'custom_tooltip = ' + terms + '\nhidden_effect = { ' + swear + ' }', guard,
               'factor = 3 modifier = { factor = 0.5 relative_strength = { target = scope:ga_sp_requester value <= 0.5 } }') + '\n' +
        option(36, 'b', 'Our hearth burns alone.', 'hidden_effect = { ' + refuse + ' }', ai='factor = 1'))]
    result.append(event(37, 'The Pact Is Sworn',
        "Embers from [SCOPE.sCountry('ga_sp_requester').GetName] and [SCOPE.sCountry('ga_sp_provider').GetName] now burn in each other's hearths. The two crowns are bound by a Sworn Pact.\n\n"
        "#bold The next step#! - When one crown holds 100 opinion of the other and is of equal or lower rank, the other may open Compact talks to take it under a charter. Relative strength no longer matters between sworn crowns.",
        option(37, 'a', 'May the embers never cool.')))
    result.append(event(38, 'The Oath Refused',
        "[SCOPE.sCountry('ga_sp_provider').GetName] has refused our Sworn Pact. Its envoys returned our embers unlit. Nothing was lost but time; we may ask again, or seek other partners among the Six.",
        option(38, 'a', 'Their loss.')))
    result.append(event(39, 'A Sworn Pact Broken',
        "War, rivalry or open hostility has broken our Sworn Pact with [SCOPE.sCountry('ga_sp_broken_partner').GetName]. The oath no longer eases Compact talks between us, and the opinion it granted is cancelled.",
        option(39, 'a', 'Let the embers go out.')))
    return result


def pulse():
    checks = []
    for tag in TAGS:
        # A one-sided break (rivalry, or the partner's own pulse) clears the mirror next month.
        mirror = ' '.join(f'AND = {{ tag = {me} c:{tag} = {{ NOT = {{ has_variable = ga_sp_sworn_{me} }} }} }}' for me in TAGS if me != tag)
        hostile = f'OR = {{ is_at_war_with = c:{tag} is_rival_of = c:{tag} is_enemy_of = c:{tag} {mirror} }}'
        checks.append(f'''if = {{ limit = {{ has_variable = ga_sp_sworn_{tag} }}
            if = {{ limit = {{ country_exists = c:{tag} {hostile} }}
                remove_variable = ga_sp_sworn_{tag}
                c:{tag} = {{ save_scope_as = ga_sp_broken_partner }}
                add_opinion = {{ target = scope:ga_sp_broken_partner modifier = ga_sworn_pact_broken }}
                trigger_event_non_silently = ga_gathering.39
            }}
            if = {{ limit = {{ NOT = {{ country_exists = c:{tag} }} }} remove_variable = ga_sp_sworn_{tag} }}
        }}''')
    # Each crown checks its own side; the partner's pulse clears the mirror flag.
    return '''
ga_sp_pact_pulse = {
    trigger = { ga_is_goblin = yes }
    effect = {
        ''' + '\n'.join(checks) + '''
    }
}
'''


def biases():
    return f'ga_sworn_pact = {{ value = {OATH_BONUS} months = {OATH_MONTHS} }}\nga_sworn_pact_broken = {{ value = -{OATH_BONUS} months = {OATH_MONTHS} }}\n'


def free_trigger():
    return '''
ga_sp_free = {
    custom_tooltip = { text = ga_ui_independent_tt ga_independent_goblin = yes }
    custom_tooltip = { text = ga_ui_peace_tt at_war = no }
    custom_tooltip = { text = ga_ui_pact_free_tt NOT = { has_variable = ga_sp_pending } }
    custom_tooltip = { text = ga_ui_harbor_free_tt NOT = { has_variable = ga_hb_pending } }
}
'''


def localization(loc):
    loc('ga_sworn_pact', 'Sworn Pact')
    loc('ga_sworn_pact_broken', 'Sworn Pact Broken')


def step_values():
    """Per-crown ladder step, evaluated on the viewing player's country."""
    rows = []
    for tag in TAGS:
        rows.append(f'''ga_pact_step_{tag} = {{
    value = 0
    if = {{ limit = {{ tag = {tag} }} value = 4 }}
    else_if = {{ limit = {{ c:{tag} ?= {{ is_subject = yes any_overlord_or_above = {{ this = root }} }} }} value = 3 }}
    else_if = {{ limit = {{ has_variable = ga_sp_sworn_{tag} }} value = 2 }}
    else_if = {{ limit = {{ OR = {{ has_variable = ga_cp_honored_{tag} c:{tag} ?= {{ is_allied_with = {{ target = root }} }} }} }} value = 1 }}
}}''')
    return '\n'.join(rows) + '\n'


STEPS = [
    ('strangers', 'Strangers', 'No alliance and no completed Harbor Bargain yet. Form an alliance through normal diplomacy, or complete a five-year Harbor Bargain, to start the pact ladder.'),
    ('trusted', 'Trusted', f'An alliance or a completed Harbor Bargain links our crowns. Next: once both crowns hold {OPINION}+ opinion of each other, use #Y Swear a Sworn Pact#! in this situation.'),
    ('sworn', 'Sworn Pact', 'Our crowns are bound by oath. Next: when they hold 100+ opinion of us and their rank is no higher than ours, use #Y Open Compact Talks#!. Relative strength is not checked between sworn crowns.'),
    ('bound', 'Bound to us', 'This crown is our subject. Its homeland locations count toward our unification.'),
]
