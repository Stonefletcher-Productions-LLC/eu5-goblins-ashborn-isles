"""Bounded bilateral requests; no alliances, subjects, land or free money."""
from ashborn_roster import TAGS
import food_storage
TERMS = {
    'provisions': ('Provisions', 'province food storage limit', '10%', '5%', 'global_food_capacity_modifier', '0.10', '-0.05', 'QBR'),
    'pilots': ('Pilots', 'naval morale recovery', '5%', '2.5%', 'naval_morale_recovery', '0.05', '-0.025', 'RHK'),
}


def free():
    return '''custom_tooltip = { text = ga_ui_independent_tt ga_independent_goblin = yes }
    custom_tooltip = { text = ga_ui_peace_tt at_war = no }
    custom_tooltip = { text = ga_ui_harbor_free_tt NOT = { has_variable = ga_hb_pending } }
    custom_tooltip = { text = ga_hb_contract_free_tt NOT = { has_variable = ga_hb_committed } }
    custom_tooltip = { text = ga_hb_quiet_tt NOT = { has_variable = ga_hb_recent_offer } }
    custom_tooltip = { text = ga_ui_legacy_free_tt NOT = { has_variable = ga_offer_pending } }
    custom_tooltip = { text = ga_ui_compact_free_tt NOT = { has_variable = ga_cp_pending } }'''


def lock_check(actor='scope:actor'):
    return '\n'.join(f'NOT = {{ AND = {{ {actor} = {{ tag = {tag} }} has_variable = ga_hb_lock_{tag} }} }}' for tag in TAGS)


def lock_pair():
    return '\n'.join(f'''scope:ga_hb_requester = {{
        if = {{ limit = {{ scope:ga_hb_provider = {{ tag = {tag} }} }}
            set_variable = {{ name = ga_hb_lock_{tag} value = yes years = 5 }} }}
    }}
    scope:ga_hb_provider = {{
        if = {{ limit = {{ scope:ga_hb_requester = {{ tag = {tag} }} }}
            set_variable = {{ name = ga_hb_lock_{tag} value = yes years = 5 }} }}
    }}''' for tag in TAGS)


def triggers():
    return '''
ga_hb_free = { ''' + free() + ''' }
# Snapshotted scopes and serial prevent an expired popup using a later request.
ga_hb_session_matches = {
    country_exists = scope:ga_hb_requester
    country_exists = scope:ga_hb_provider
    scope:ga_hb_requester = {
        has_variable = ga_hb_pending has_variable = ga_hb_is_requester
        var:ga_hb_nonce = scope:ga_hb_token
        var:ga_hb_partner = scope:ga_hb_provider
    }
    scope:ga_hb_provider = {
        has_variable = ga_hb_pending NOT = { has_variable = ga_hb_is_requester }
        var:ga_hb_nonce = scope:ga_hb_token
        var:ga_hb_partner = scope:ga_hb_requester
    }
}
ga_hb_valid = {
    ga_hb_session_matches = yes
    scope:ga_hb_requester = {
        ga_independent_goblin = yes at_war = no
        NOT = { has_variable = ga_hb_committed }
        NOT = { is_rival_of = scope:ga_hb_provider }
        NOT = { is_enemy_of = scope:ga_hb_provider }
        "opinion(scope:ga_hb_provider)" >= 25
    }
    scope:ga_hb_provider = {
        ga_independent_goblin = yes at_war = no
        NOT = { has_variable = ga_hb_committed }
        NOT = { is_rival_of = scope:ga_hb_requester }
        NOT = { is_enemy_of = scope:ga_hb_requester }
        "opinion(scope:ga_hb_requester)" >= 25
    }
}
ga_hb_offer_valid = {
    ga_hb_valid = yes
    scope:ga_hb_requester = { NOT = { has_variable = ga_hb_countered } }
}
ga_hb_counter_valid = {
    ga_hb_valid = yes
    scope:ga_hb_requester = { has_variable = ga_hb_countered }
}
'''


def start(event_id):
    return '''scope:actor = {
        save_scope_as = ga_hb_requester
        if = { limit = { NOT = { has_variable = ga_hb_serial } }
            set_variable = { name = ga_hb_serial value = 0 } }
        change_variable = { name = ga_hb_serial add = 1 }
        save_scope_value_as = { name = ga_hb_token value = var:ga_hb_serial }
        set_variable = { name = ga_hb_pending value = yes days = 180 }
        set_variable = { name = ga_hb_is_requester value = yes days = 180 }
        set_variable = { name = ga_hb_nonce value = scope:ga_hb_token days = 180 }
        set_variable = { name = ga_hb_partner value = scope:target days = 180 }
        set_variable = { name = ga_hb_recent_offer value = yes years = 2 }
        remove_variable = ga_hb_countered
    }
    scope:target = {
        save_scope_as = ga_hb_provider
        set_variable = { name = ga_hb_pending value = yes days = 180 }
        set_variable = { name = ga_hb_nonce value = scope:ga_hb_token days = 180 }
        set_variable = { name = ga_hb_partner value = scope:actor days = 180 }
        set_variable = { name = ga_hb_recent_offer value = yes years = 2 }
        remove_variable = ga_hb_is_requester
        remove_variable = ga_hb_countered
    }
    ''' + lock_pair() + f'\n scope:target = {{ trigger_event_non_silently = ga_gathering.{event_id} }}'


def actions(action, picker):
    result = []
    for kind, key, number in [('provisions', 'ga_offer_harbor_pact', 20), ('pilots', 'ga_seek_pilot_bargain', 21)]:
        title, metric, gain, burden, _, _, _, preferred = TERMS[kind]
        description = ('Step 1 of 3 on the road to one crown: Bargain, Sworn Pact, Compact.\n'
                       f'Buy {kind} from an independent Ashborn crown.\n'
                       f'Price: 10 gold, paid only when signed. Duration: 5 years.\n'
                       f'You gain: +{gain} {metric}.\n'
                       f'Supplier commits: {burden} of its {metric}.\n'
                       'One counteroffer: the other service for 15 gold.\n\n'
                       'Requires: mutual opinion of 25+ and a free contract slot.\n'
                       'A completed five-year bargain lets the pair swear a Sworn Pact.\n'
                       'One contract per crown; no alliance or vassalage.\n'
                       'Talks expire in 180 days. Crown cooldown: 2 years.\n'
                       'The same pair must wait 5 years between approaches.\n'
                       'War, rivalry or a vanished partner ends the contract '
                       'at the next monthly check. No refund.')
        if kind == 'provisions':
            description += '\nInspect storage in the province food stockpile tooltip.'
        conditions = '''ga_hb_free = yes this != scope:actor
            "opinion(scope:actor)" >= 25
            NOT = { is_rival_of = scope:actor } NOT = { is_enemy_of = scope:actor }
            scope:actor = {
                "opinion(scope:target)" >= 25
                NOT = { is_rival_of = scope:target } NOT = { is_enemy_of = scope:target }
                ''' + lock_check('scope:target') + '\n }\n' + lock_check()
        selector = picker(conditions)
        ai = f'''add = -1000
            if = {{ limit = {{ scope:actor = {{ gold >= 30 }} exists = scope:target }}
                add = 1005
                if = {{ limit = {{ scope:target = {{ tag = {preferred} }} }} add = 10 }}
            }}'''
        result.append(action(key, 'Seek ' + title + ' for Our Harbors', description,
                             'hidden_effect = { if = { limit = { scope:actor = { ga_hb_free = yes gold >= 10 } scope:target = { '
                             + conditions + ' } } ' + start(number) + ' } }', selector,
                             allow='ga_hb_free = yes gold >= 10', ai=ai, years=2))
    return result


def clear_local():
    return '\n'.join('remove_variable = ' + key for key in
                     ['ga_hb_pending', 'ga_hb_partner', 'ga_hb_nonce', 'ga_hb_is_requester', 'ga_hb_countered'])


def cleanup():
    # Each side is independently checked, including when the other no longer exists.
    return '\n'.join(f'''scope:{who} ?= {{
        if = {{ limit = {{ has_variable = ga_hb_pending var:ga_hb_nonce = scope:ga_hb_token
            var:ga_hb_partner = scope:{other} {role} }}
            {clear_local()}
        }}
    }}''' for who, other, role in [('ga_hb_requester', 'ga_hb_provider', 'has_variable = ga_hb_is_requester'),
                                  ('ga_hb_provider', 'ga_hb_requester', 'NOT = { has_variable = ga_hb_is_requester }')])


def affordability(price):
    return f'''scope:ga_hb_requester = {{ gold >= {price}
        OR = {{ is_ai = no gold >= {price + 20} }} }}'''


def sign(kind, price, stage):
    # Repeat all guards in the effects, not only in the option visibility.
    return f'''if = {{ limit = {{ ga_hb_{stage}_valid = yes {affordability(price)} }}
        save_scope_value_as = {{ name = ga_hb_signed_service value = {1 if kind == 'provisions' else 2} }}
        save_scope_value_as = {{ name = ga_hb_signed_price value = {price} }}
        scope:ga_hb_requester = {{
            add_gold = -{price}
            add_country_modifier = {{ modifier = ga_hb_{kind}_received years = 5 mode = replace }}
            set_variable = {{ name = ga_hb_committed value = yes }}
            set_variable = {{ name = ga_hb_tracks_term value = yes }}
            set_variable = {{ name = ga_hb_term_running value = yes years = 5 }}
            set_variable = {{ name = ga_hb_contract_partner value = scope:ga_hb_provider }}
        }}
        scope:ga_hb_provider = {{
            add_gold = {price}
            add_country_modifier = {{ modifier = ga_hb_{kind}_supplied years = 5 mode = replace }}
            set_variable = {{ name = ga_hb_committed value = yes }}
            set_variable = {{ name = ga_hb_tracks_term value = yes }}
            set_variable = {{ name = ga_hb_term_running value = yes years = 5 }}
            set_variable = {{ name = ga_hb_contract_partner value = scope:ga_hb_requester }}
        }}
        {cleanup()}
        scope:ga_hb_requester = {{
            trigger_event_non_silently = ga_gathering.24 }}
        scope:ga_hb_provider = {{
            trigger_event_non_silently = ga_gathering.24 }}
    }}'''


def decline(other):
    return f'''if = {{ limit = {{ ga_hb_session_matches = yes }}
        {lock_pair()}
        scope:ga_hb_requester = {{ set_variable = {{ name = ga_hb_recent_offer value = yes years = 2 }} }}
        scope:ga_hb_provider = {{ set_variable = {{ name = ga_hb_recent_offer value = yes years = 2 }} }}
        scope:{other} = {{ trigger_event_non_silently = ga_gathering.25 }}
    }}
    {cleanup()}'''


def events(event, option, loc):
    emit_option = option
    loc('ga_hb_eligibility_tt', 'These talks are still valid, both crowns remain eligible, and the buyer can afford the terms.')
    # Keep internal serials, bilateral lock branches and rechecks out of hover trees.
    def option(number, suffix, name, effects='', trigger='', ai='factor = 1'):
        tip = ''
        if number in [20, 21, 22, 23]:
            key = f'ga_hb_{number}_{suffix}_result_tt'
            if suffix == 'a':
                kind = 'provisions' if number in [20, 22] else 'pilots'
                _, metric, gain, burden, *_ = TERMS[kind]
                price = 10 if number in [20, 21] else 15
                text = f'The buyer pays the supplier {price} gold and gains {gain} {metric}; the supplier commits {burden} of its own {metric}. Both commitments last five years. Hostilities, rivalry or a vanished partner end the contract at the next monthly check, without a refund.'
            elif suffix == 'b' and number in [20, 21]:
                text = 'Send one final counteroffer for the other service at 15 gold. No payment is taken unless the buyer accepts.'
            else:
                text = 'End these talks without payment or commitments. Neither crown will approach the other for five years.'
            if suffix == 'a' and number in (20, 22):
                text += '\n\n' + food_storage.REFERENCE
            loc(key, text)
            tip = f'custom_tooltip = {key}\n'
        condition = 'custom_tooltip = { text = ga_hb_eligibility_tt ' + trigger + ' }' if trigger else ''
        return emit_option(number, suffix, name, tip + 'hidden_effect = { ' + effects + ' }', condition, ai)
    result = []
    for kind, number, counter_number in [('provisions', 20, 23), ('pilots', 21, 22)]:
        title, metric, gain, burden, _, _, _, preferred = TERMS[kind]
        other = 'pilots' if kind == 'provisions' else 'provisions'
        alternative = TERMS[other]
        common = (f'We receive 10 gold and commit {burden} of our {metric} for five years; '
                  f'the buyer gains {gain} {metric}. We can instead offer {other} for 15 gold: '
                  f'we commit {alternative[3]} {alternative[1]}, and the buyer gains {alternative[2]} {alternative[1]}, for five years. '
                  'Only one counteroffer is allowed. These are paid services, not an alliance or a promise to become a subject. '
                  'No money changes hands unless a bargain is signed. Each crown can hold only one contract at a time.')
        accept_ai = f'''factor = 2
            modifier = {{ factor = 3 tag = {preferred} }}'''
        counter_ai = f'''factor = 1
            modifier = {{ factor = 4 tag = {alternative[7]} }}'''
        counter = f'''if = {{ limit = {{ ga_hb_offer_valid = yes }}
            scope:ga_hb_requester = {{
                set_variable = {{ name = ga_hb_countered value = yes days = 180 }}
                trigger_event_non_silently = ga_gathering.{counter_number}
            }}
        }}'''
        result.append(event(number, title + ' at a Price',
            "[SCOPE.sCountry('ga_hb_requester').GetName] seeks our " + kind + '. ' + common,
            option(number, 'a', 'Accept the 10-gold contract.', sign(kind, 10, 'offer'),
                   'ga_hb_offer_valid = yes ' + affordability(10), accept_ai) + '\n' +
            option(number, 'b', f'Offer our {other} instead, for 15 gold.', counter,
                   'ga_hb_offer_valid = yes', counter_ai) + '\n' +
            option(number, 'c', 'Decline, or close talks if the terms are no longer valid.', decline('ga_hb_requester'), ai='factor = 2')))
    for kind, number in [('provisions', 22), ('pilots', 23)]:
        title, metric, gain, burden, *_ = TERMS[kind]
        result.append(event(number, 'A Counteroffer from the Harbors',
            "[SCOPE.sCountry('ga_hb_provider').GetName] offers " + kind +
            f' instead. Pay it 15 gold for {gain} more {metric} for five years. '
            f'It commits {burden} of its own {metric} for that period. '
            'Accept these final terms or walk away without payment. No further counteroffer is possible.',
            option(number, 'a', 'Pay 15 gold and sign these terms.', sign(kind, 15, 'counter'),
                   'ga_hb_counter_valid = yes ' + affordability(15), 'factor = 2') + '\n' +
            option(number, 'b', 'Keep our money; end the talks.', decline('ga_hb_provider'), ai='factor = 2')))
    result.append(event(24, 'A Harbor Bargain Signed',
        "[ROOT.GetCountry.Custom('ga_hb_signed_recap')]",
        option(24, 'a', 'Let both harbors honor the bargain.')))
    result.append(event(25, 'Harbor Talks Closed',
        'The proposed bargain was declined or its conditions changed. No contract was signed and no payment was taken. These two crowns will not reopen negotiations for five years.',
        option(25, 'a', 'Our crown keeps its freedom to choose.')))
    return result


def signed_recap(loc):
    rows = ['ga_hb_signed_recap = { type = country']
    for service, (kind, terms) in enumerate(TERMS.items(), 1):
        title, metric, gain, burden, *_ = terms
        for price in (10, 15):
            key = f'ga_hb_signed_{kind}_{price}'
            loc(key, f'#bold {title} bargain signed#!\\n\\n'
                + "[SCOPE.sCountry('ga_hb_requester').GetName] (buyer):\\n"
                + f'Paid #R {price} gold#!. Gains #G +{gain} {metric}#!.\\n\\n'
                + "[SCOPE.sCountry('ga_hb_provider').GetName] (supplier):\\n"
                + f'Received #G {price} gold#!. Commits #R -{burden} {metric}#!.\\n\\n'
                + 'Both modifiers last #Y five years#! from signing. Payment and effects have already been applied.\\n'
                + 'War, rivalry or a vanished partner ends the contract at the next monthly check, without a refund.'
                + ('\\n\\n' + food_storage.REFERENCE if kind == 'provisions' else ''))
            rows.append(f'text = {{ trigger = {{ exists = scope:ga_hb_signed_service exists = scope:ga_hb_signed_price scope:ga_hb_signed_service = {service} scope:ga_hb_signed_price = {price} }} localization_key = {key} }}')
    loc('ga_hb_signed_legacy', 'This earlier bargain was signed before detailed receipts were recorded. Its payment and five-year commitments were already applied; consult the active country modifiers for its service.')
    rows.append('text = { fallback = yes localization_key = ga_hb_signed_legacy } }')
    return '\n'.join(rows)


def modifiers(loc):
    loc('ga_hb_contract_free_tt', 'No active Harbor Bargain. Each crown may hold #Y one contract#! for #Y five years#!.')
    loc('ga_hb_quiet_tt', 'The #Y two-year#! waiting period since our last harbor approach has ended.')
    rows = []
    for kind, (title, metric, gain, burden, key, benefit, cost, _) in TERMS.items():
        for suffix, value, text in [('received', benefit, f'Purchased {kind} increase {metric} by {gain} for five years.'),
                                    ('supplied', cost, f'Committed {kind} reduce our {metric} by {burden} for five years. We received payment when the bargain was signed.')]:
            name = f'ga_hb_{kind}_{suffix}'
            rows.append(f'{name} = {{ {key} = {value} }}')
            loc('STATIC_MODIFIER_NAME_' + name, title + (' Purchased' if suffix == 'received' else ' Committed'))
            if kind == 'provisions':
                text += '\n\n' + food_storage.REFERENCE
            loc('STATIC_MODIFIER_DESC_' + name, text)
    return '\n'.join(rows)


def maintenance():
    remove = '\n'.join(f'remove_country_modifier = ga_hb_{kind}_{suffix}' for kind in TERMS for suffix in ['received', 'supplied'])
    clear = remove + '\nremove_variable = ga_hb_committed\nremove_variable = ga_hb_contract_partner\nremove_variable = ga_hb_tracks_term\nremove_variable = ga_hb_term_running'
    honored = '\n'.join(f'if = {{ limit = {{ var:ga_hb_contract_partner = {{ tag = {tag} }} }} set_variable = {{ name = ga_cp_honored_{tag} value = yes }} }}' for tag in TAGS)
    finish = f'''if = {{ limit = {{ has_variable = ga_hb_tracks_term NOT = {{ has_variable = ga_hb_term_running }} country_exists = var:ga_hb_contract_partner }}
        save_scope_as = ga_hb_finished_partner
        if = {{ limit = {{ var:ga_hb_contract_partner = {{ var:ga_hb_contract_partner = scope:ga_hb_finished_partner has_variable = ga_hb_tracks_term NOT = {{ has_variable = ga_hb_term_running }} }} }}
            {{HONORED}}
            var:ga_hb_contract_partner = {{ {{HONORED}} {{CLEAR}} }}
        }}
        {{CLEAR}}
    }}'''.replace('{HONORED}', honored).replace('{CLEAR}', clear)
    # Hook is a cheap flag test; partner checks run only for active contracts.
    return '''monthly_country_pulse = { on_actions = { ga_hb_contract_pulse } }
ga_hb_contract_pulse = {
    trigger = { has_variable = ga_hb_committed }
    effect = {
        if = { limit = { NOT = { country_exists = var:ga_hb_contract_partner } }
            ''' + clear + '''
        }
        if = { limit = { country_exists = var:ga_hb_contract_partner }
        save_scope_as = ga_hb_checked_partner
        if = { limit = { OR = {
            is_at_war_with = var:ga_hb_contract_partner
            is_rival_of = var:ga_hb_contract_partner
            is_enemy_of = var:ga_hb_contract_partner
            var:ga_hb_contract_partner = { OR = {
                is_at_war_with = scope:ga_hb_checked_partner
                is_rival_of = scope:ga_hb_checked_partner
                is_enemy_of = scope:ga_hb_checked_partner
            } }
        } }
            save_scope_as = ga_hb_broken_partner
            var:ga_hb_contract_partner ?= {
                if = { limit = { var:ga_hb_contract_partner = scope:ga_hb_broken_partner }
                    ''' + clear + '''
                }
            }
            ''' + clear + '''
        }
        }
        ''' + finish + '''
    }
}
'''
