"""Ashen Kinship: goblin crowns may fight each other, but every crown defends
against an outside invader.

Native reference (EU5 _hardcoded.txt): on_war_declared fires once per country with
root = country, scope:actor = attacker, scope:recipient = defender, scope:war.
join_war_as_defender is the forced join vanilla uses for the War of Religions.
"""

HOOK = 'ga_kin_defense'
RALLY = {'damage_done_versus_heathens_modifier': '0.10', 'global_defensive': '0.10'}


def on_action():
    # Guard on root = recipient so the call runs once, not once per country.
    return f'''
on_war_declared = {{ on_actions = {{ {HOOK} }} }}
{HOOK} = {{
    trigger = {{
        this = scope:recipient
        ga_is_goblin = yes
        scope:actor = {{ NOT = {{ ga_is_goblin = yes }} }}
    }}
    effect = {{
        save_scope_as = ga_kin_victim
        scope:actor = {{ save_scope_as = ga_kin_invader }}
        add_country_modifier = {{ modifier = ga_kin_rally years = 5 mode = replace }}
        every_country = {{
            limit = {{
                ga_independent_goblin = yes
                this != scope:ga_kin_victim
                NOT = {{ is_at_war_with = scope:ga_kin_victim }}
                NOT = {{ is_at_war_with = scope:ga_kin_invader }}
            }}
            save_scope_as = ga_kin_ally
            join_war_as_defender = {{ war = scope:war call_in_subjects = yes }}
            add_country_modifier = {{ modifier = ga_kin_rally years = 5 mode = replace }}
            scope:ga_kin_victim = {{ add_opinion = {{ target = scope:ga_kin_ally modifier = ga_kin_answered }} }}
            trigger_event_non_silently = ga_gathering.42
        }}
        trigger_event_non_silently = ga_gathering.41
    }}
}}
'''


def events(event, option, loc):
    return [
        event(41, 'The Isles Answer',
            "[SCOPE.sCountry('ga_kin_invader').GetName] has dared to make war on Ashborn shores. Whatever blood lies between the Six, no outsider may take what belongs to the Hunger Below. Every free crown that is not at war with us now sails to our defense.\n\n"
            "#bold Ashen Kinship#! - Goblin crowns may fight one another, but a war declared on any goblin crown by an outsider draws in every independent goblin crown that is not already its enemy.",
            option(41, 'a', 'Let them come. They will find six crowns, not one.')),
        event(42, 'Kin Under Attack',
            "[SCOPE.sCountry('ga_kin_invader').GetName] has declared war on [SCOPE.sCountry('ga_kin_victim').GetName]. We may quarrel with our kin over every harbor and hill, but we will not watch an outsider take Ashborn soil. Our crown has joined the war as a defender.\n\n"
            "#bold Ashen Kinship#! - We joined automatically. Wars between goblin crowns never trigger this; only an outsider's declaration does.",
            option(42, 'a', 'To the shore. Kin first, quarrels later.')),
    ]


def modifiers(loc):
    loc('STATIC_MODIFIER_NAME_ga_kin_rally', 'Ashen Kinship')
    loc('STATIC_MODIFIER_DESC_ga_kin_rally', 'The goblin crowns stand together against an outside invader. Our troops fight harder against those outside our faith, and our fortifications hold longer.')
    loc('ga_kin_answered', 'Answered Our Call')
    return 'ga_kin_rally = { ' + ' '.join(f'{k} = {v}' for k, v in RALLY.items()) + ' }'


def biases():
    return 'ga_kin_answered = { value = 30 months = 120 }\n'
