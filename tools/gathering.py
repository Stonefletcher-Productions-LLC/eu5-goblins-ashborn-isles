"""Generate the 0.5.5 Gathering/Eastern Hunger prototype; no game files are edited.

Native reference: EU5 1.3.11 situations, generic_actions, biases and conquest CB.
The prototype deliberately leaves wars, peace, unions and succession to native EU5.
"""
from pathlib import Path
import argparse
import json
import textwrap
from clan_identity import PROFILES, SHATTERFIN
from event_art import image
import harbor_bargains
import compact_talks
import sworn_pacts
import kin_defense
import situation_progress
import early_projects

ROOT = Path(__file__).resolve().parents[1]
from ashborn_roster import TAGS
TEXT = {}

def loc(key, value):
    TEXT[key] = value
    return key

def write(out, path, content):
    p = out / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.strip() + '\n', encoding='utf-8-sig', newline='\r\n')

def event(num, title, desc, body, trigger='ga_is_goblin = yes', immediate='', after=''):
    key = f'ga_gathering.{num}'
    loc(key + '.title', title)
    loc(key + '.desc', desc)
    return f'''{key} = {{
    type = country_event
    category = situation_event
    outcome = neutral
    title = {key}.title
    desc = {key}.desc
    trigger = {{ {trigger} }}
    image = "{image(key)}"
    immediate = {{ {immediate} }}
    {body}
    after = {{ {after} }}
}}
'''

def option(num, suffix, name, effects='', trigger='', ai='factor = 1'):
    key = loc(f'ga_gathering.{num}.{suffix}', name)
    return f'''option = {{
        name = {key}
        trigger = {{ {trigger} }}
        ai_chance = {{ {ai} }}
        {effects}
    }}'''

def situation_picker(situation):
    return f'''select_trigger = {{
        looking_for_a = situation
        interaction_source_list = {{ situation:{situation} = {{ add_to_list = source }} }}
        target_flag = recipient
        name = choose_situation
        column = {{ data = name }}
        visible = {{ this = situation:{situation} situation_is_active = yes }}
    }}'''

def country_picker(conditions):
    return f'''select_trigger = {{
        looking_for_a = country
        source_global_list = ga_five_kingdoms
        target_flag = target
        name = ga_choose_kingdom
        none_available_msg_key = ga_no_kingdom_available
        column = {{ data = name }}
        visible = {{
            ga_is_goblin = yes
            this != scope:actor
            is_subject = no
            is_junior_partner = no
            at_war = no
            {conditions}
        }}
    }}'''

def action(key, name, desc, effect, selector='', allow='', ai='add = 10',
           years=3, price=None, eastern=False):
    loc(key, name)
    # Country-selection tooltips do not wrap these descriptions themselves.
    # Keep explicit paragraphs and serialize native localization line breaks.
    loc(key + '_desc', '\n'.join(textwrap.fill(paragraph, width=68,
        break_long_words=False, break_on_hyphens=False)
        for paragraph in desc.split('\n')))
    sit = 'ga_eastern_hunger' if eastern else 'ga_gathering_of_five'
    extra = 'has_variable = ga_unifier custom_tooltip = { text = ga_gathering_complete_tt ga_controls_homeland = yes }' if eastern else ''
    if selector:
        effect = 'if = { limit = { exists = scope:target } ' + effect + ' }'
    price_line = f'    price = price:{price}\n' if price else ''
    # Harbor/Compact eligibility already supplies the readable peace check.
    peace = '' if allow.startswith(('ga_hb_free', 'ga_cp_free', 'ga_sp_free')) else 'at_war = no'
    return f'''{key} = {{
    type = situation
    show_message = no
    potential = {{ scope:actor = {{ ga_is_goblin = yes is_subject = no is_junior_partner = no {extra} }} }}
    allow = {{ scope:actor = {{ {peace} {allow} }} }}
    automation_tick = never
    ai_tick = monthly
    ai_tick_frequency = 6
    cooldown = {{ type = {key} years = {years} }}
{price_line}    {situation_picker(sit)}
    {selector}
    effect = {{ {effect} }}
    ai_will_do = {{ {ai} }}
}}
'''

def build(out, cfg=None):
    TEXT.clear()
    if cfg is None:
        import archipelago
        cfg = archipelago.prepare(json.loads((ROOT / 'data/island.json').read_text(encoding='utf-8-sig')))
    # These are fixed starting homeland locations, not current cultural population.
    homeland = [x['id'] for x in cfg['locations']]
    tags = ' '.join(f'tag = {tag}' for tag in TAGS)
    ownership = '\n'.join(f'        location:{x} = {{ exists = owner owner = {{ ga_owner_in_claimant_realm = yes }} }}' for x in homeland)
    triggers = f'''
ga_is_goblin = {{ OR = {{ {tags} }} }}

# country scope; unions are IOs in EU5, not a subject_type.
ga_independent_goblin = {{ ga_is_goblin = yes is_subject = no is_junior_partner = no }}

# Claimant scope is explicitly captured by ga_controls_homeland before owner scopes.
# Check the native overlord iterator without recursive scripted triggers.
# Every intervening subject must be a vassal; tributary chains never count.
ga_owner_in_claimant_realm = {{
    OR = {{
        this = scope:ga_claimant
        AND = {{
            is_subject_type = vassal
            any_overlord_or_above = {{
                OR = {{ this = scope:ga_claimant junior_union_with = {{ target = scope:ga_claimant }} }}
            }}
            any_overlord_or_above = {{
                OR = {{
                    this = scope:ga_claimant
                    is_subject_type = vassal
                    junior_union_with = {{ target = scope:ga_claimant }}
                }}
                count = all
            }}
        }}
        AND = {{ junior_union_with = {{ target = scope:ga_claimant }} }}
    }}
}}

ga_controls_homeland = {{
    ga_independent_goblin = yes
    save_temporary_scope_as = ga_claimant
    AND = {{
{ownership}
    }}
}}

ga_owns_entire_homeland = {{
    ga_independent_goblin = yes
    AND = {{
{chr(10).join(f'        owns = location:{x}' for x in homeland)}
    }}
}}

# Evaluated in the recipient country. Repeat at acceptance to cover delayed popups.
ga_valid_pact_offer = {{
    ga_independent_goblin = yes
    at_war = no
    country_exists = var:ga_offer_sender
    var:ga_offer_sender = {{ ga_independent_goblin = yes at_war = no }}
    NOT = {{ is_rival_of = var:ga_offer_sender }}
    NOT = {{ is_enemy_of = var:ga_offer_sender }}
    NOT = {{ is_allied_with = {{ target = var:ga_offer_sender }} }}
}}

ga_valid_submission_offer = {{
    ga_independent_goblin = yes
    at_war = no
    country_exists = var:ga_offer_sender
    var:ga_offer_sender = {{ ga_independent_goblin = yes at_war = no }}
    is_allied_with = {{ target = var:ga_offer_sender }}
    relative_strength = {{ target = var:ga_offer_sender value <= 0.65 }}
    "opinion(var:ga_offer_sender)" >= 125
    var:ga_offer_sender.country_rank_level >= country_rank_level
}}

ga_has_european_foothold = {{
    ga_controls_homeland = yes
    any_country = {{
        ga_owner_in_claimant_realm = yes
        any_owned_location = {{
            continent = continent:europe
            is_coastal = yes
            NOT = {{ area = area:cm_cindermaw_area }}
        }}
    }}
}}
'''
    write(out, 'in_game/common/scripted_triggers/goblins_gathering.txt', triggers + harbor_bargains.triggers() + compact_talks.triggers() + sworn_pacts.triggers() + sworn_pacts.free_trigger())
    from build_clan_flags import recovery_on_action
    write(out, 'in_game/common/on_action/goblins_gathering.txt', harbor_bargains.maintenance().replace("on_actions = { ga_hb_contract_pulse }", "on_actions = { ga_hb_contract_pulse ga_cp_history_pulse ga_sp_pact_pulse ga_clan_flags_060_pulse }") + compact_talks.pulse() + sworn_pacts.pulse() + kin_defense.on_action() + recovery_on_action())

    # Use native monthly situation evaluation; no external global pulse override.
    situations = '''
ga_gathering_of_five = {
    monthly_spawn_chance = monthly_spawn_chance_unique
    can_start = {
        current_date >= 1337.7.1
        any_country = { ga_independent_goblin = yes }
    }
    # Keep the full test, but do not expand 72 ownership trees in the UI.
    can_end = { custom_tooltip = {
        text = ga_gathering_complete_tt
        any_country = { ga_controls_homeland = yes }
    } }
    visible = { ga_is_goblin = yes }
    on_start = {
        every_country = {
            limit = { ga_is_goblin = yes }
            add_to_global_variable_list = { name = ga_five_kingdoms target = this }
            trigger_event_non_silently = { id = ga_gathering.1 days = 1 }
        }
    }
    on_monthly = {
        every_country = {
            limit = { ga_is_goblin = yes }
            if = {
                limit = { NOT = { has_variable = ga_signature_seen } }
                set_variable = { name = ga_signature_seen value = yes }
                if = { limit = { tag = CDM } trigger_event_non_silently = ga_gathering.10 }
                if = { limit = { tag = QBR } trigger_event_non_silently = ga_gathering.11 }
                if = { limit = { tag = RHK } trigger_event_non_silently = ga_gathering.12 }
                if = { limit = { tag = SFK } trigger_event_non_silently = ga_gathering.13 }
                if = { limit = { tag = SWK } trigger_event_non_silently = ga_gathering.14 }
                if = { limit = { tag = GTF } trigger_event_non_silently = ga_gathering.40 }
            }
        }
    }
    on_ending = {
        every_country = {
            limit = { ga_controls_homeland = yes }
            set_variable = { name = ga_unifier value = yes }
            trigger_event_non_silently = ga_gathering.5
            every_subject = {
                limit = { ga_is_goblin = yes is_subject_type = vassal }
                trigger_event_non_silently = ga_gathering.7
            }
            union ?= {
                every_international_organization_member = {
                    limit = { ga_is_goblin = yes is_junior_partner = yes }
                    trigger_event_non_silently = ga_gathering.7
                }
            }
        }
    }
}

ga_eastern_hunger = {
    monthly_spawn_chance = monthly_spawn_chance_unique
    can_start = { custom_tooltip = {
        text = ga_eastern_start_tt
        any_country = { has_variable = ga_unifier ga_controls_homeland = yes }
    } }
    can_end = { custom_tooltip = {
        text = ga_eastern_complete_tt
        any_country = { has_variable = ga_unifier ga_has_european_foothold = yes }
    } }
    visible = { ga_is_goblin = yes }
    on_start = {
        every_country = {
            limit = { has_variable = ga_unifier ga_controls_homeland = yes }
            trigger_event_non_silently = ga_gathering.6
        }
    }
    on_ending = {
        every_country = {
            limit = { has_variable = ga_unifier ga_has_european_foothold = yes }
            trigger_event_non_silently = ga_gathering.8
        }
    }
}
'''
    # Only these five tags are eligible; avoid a global scan every month.
    monthly_start = situations.index('    on_monthly = {')
    monthly_end = situations.index('    on_ending = {', monthly_start)
    monthly = situations[monthly_start:monthly_end]
    body = monthly[monthly.index('            if = {'):monthly.rindex('        }')]
    bounded = '    on_monthly = {\n' + ''.join(
        '        c:' + tag + ' ?= {\n' + body + '        }\n' for tag in TAGS) + '    }\n'
    situations = situations[:monthly_start] + bounded + situations[monthly_end:]
    write(out, 'in_game/common/situations/goblins_gathering.txt', situations)
    # Native panels are resolved by situation ID; definitions alone render no UI.
    # Inherit the game's illustration, start date, scrolling and action list.
    for situation_id in ('ga_gathering_of_five', 'ga_eastern_hunger'):
        panel = '''
situation_panel = {
    blockoverride "situation_subheader_content" {}
    blockoverride "situation_panel_main_content" {
        text_multi = {
            layoutpolicy_horizontal = expanding
            max_width = 400
            autoresize = yes
            text = "SITUATION_DESCRIPTION_KEY"
        }
        text_single = {
            layoutpolicy_horizontal = expanding
            text = "END_REQUIREMENTS"
        }
        TooltipRequirementsList = {
            textcontext = "[SituationView.GetActiveSituation.GetSituation.GetEndConditions]"
        }
    }
}
'''.replace('SITUATION_DESCRIPTION_KEY', situation_id + '_desc')
        write(out, f'in_game/gui/panels/situation/{situation_id}.gui', panel)

    # Persist sender in the recipient, so event responses survive save/reload and
    # do not depend on the generic action's transient actor scope.
    request = '''scope:target = {
        set_variable = { name = ga_offer_sender value = scope:actor }
        set_variable = { name = ga_offer_pending value = yes }
        trigger_event_non_silently = ga_gathering.EVENT
    }'''
    choices = '''NOT = { has_variable = ga_offer_pending }
            NOT = { is_rival_of = scope:actor }
            NOT = { is_enemy_of = scope:actor }'''
    ai_friendly = '''add = 5
        if = { limit = { exists = scope:target }
            add = { value = "scope:actor.opinion(scope:target)" multiply = 0.2 desc = ga_relations }
            if = { limit = { scope:actor = { is_allied_with = { target = scope:target } } } add = 15 }
        }'''
    actions = []
    actions.extend(harbor_bargains.actions(action, country_picker))
    actions.append(action('ga_send_supplies', 'Send Grain and Iron',
        'Pay 10 gold to send supplies to another independent Ashborn kingdom. The recipient gains 10 gold and improved opinion of you for five years.',
        '''scope:target = {
            add_gold = 10
            add_opinion = { target = scope:actor modifier = ga_received_supplies }
        }''', country_picker(choices), ai=ai_friendly, years=5, price='ga_gathering_aid_price'))
    actions.append(sworn_pacts.action(action))
    actions.append(compact_talks.action(action, country_picker))
    war_ai = '''add = -100
        if = { limit = { exists = scope:target scope:actor = { wants_to_attack = scope:target } } add = 140 }
        if = { limit = { scope:actor = { manpower_percentage < 0.5 } } subtract = 1000 }'''
    war_selector = country_picker('''
            NOT = { is_allied_with = { target = scope:actor } }
            scope:actor = { can_declare_war_on = scope:target NOT = { has_truce_with = scope:target } }''')
    actions.append(action('ga_challenge_crown', 'Challenge a Rival Crown',
        'Gain a five-year native subjugation casus belli against an independent goblin rival. You must declare and win a normal war; this action grants no subjects.',
        '''scope:actor = { add_casus_belli = { type = casus_belli:cb_subjugation target = scope:target years = 5 } }''',
        war_selector, allow='manpower_percentage >= 0.25', ai=war_ai, years=5, price='ga_gathering_claim_price'))
    actions.append(action('ga_claim_homeland', 'Claim a Rival Harbor',
        'Gain a five-year native province conquest casus belli for a rival goblin capital province. Normal declarations, peace costs and territorial transfers apply.',
        '''scope:actor = { add_casus_belli = {
            type = casus_belli:cb_conquer_province target = scope:target province = scope:target.capital.province years = 5
        } }''', war_selector, allow='manpower_percentage >= 0.25', ai=war_ai, years=5, price='ga_gathering_claim_price'))
    actions.append(action('ga_prepare_crossing', 'Prepare the Eastern Crossing',
        'Pay 20 gold for five years of 15% lower transport construction cost and 5% higher naval morale. Ships, armies and land must still be obtained through normal gameplay. Available once every ten years.',
        '''scope:actor = { add_country_modifier = { modifier = ga_crossing_preparations years = 5 mode = replace } }''',
        ai='add = 20', years=10, price='ga_gathering_crossing_price', eastern=True))
    coastal = '''select_trigger = {
        looking_for_a = province
        target_flag = target
        name = ga_choose_eastern_province
        none_available_msg_key = ga_no_eastern_target
        column = { data = name }
        pre_evaluation_sort_value = { add = { value = "border_distance_to(scope:actor)" multiply = -1 } }
        pre_evaluation_number_to_evaluate_fully = 8
        visible = {
            exists = owner
            any_location_in_province = {
                continent = continent:europe
                is_coastal = yes
                is_discovered_by = scope:actor
                NOT = { area = area:cm_cindermaw_area }
                owner = root.owner
            }
            NOT = { owner = { ga_is_goblin = yes } }
        }
        enabled = {
            scope:actor = {
                can_declare_war_on = root.owner
                NOT = { has_truce_with = root.owner }
                NOT = { is_allied_with = { target = root.owner } }
            }
        }
    }'''
    east_ai = '''add = -100
        if = {
            limit = { exists = scope:target scope:actor = {
                wants_to_attack = scope:target.owner
                manpower_percentage >= 0.5
                navy_size > 0
            } }
            add = 160
        }'''
    actions.append(action('ga_plan_eastern_foothold', 'Plan an Eastern Foothold',
        'Pay 10 gold and select a discovered European coastal province. Gain a five-year conquest casus belli against its current owner. Selecting another province replaces the permitted eastern objective. No war is declared and no land is granted.',
        '''scope:actor = {
            set_variable = { name = ga_eastern_target value = scope:target years = 5 }
            add_casus_belli = { type = casus_belli:ga_cb_eastern_foothold target = scope:target.owner province = scope:target years = 5 }
        }''', coastal, ai=east_ai, years=3, price='ga_gathering_target_price', eastern=True))
    write(out, 'in_game/common/generic_actions/goblins_gathering.txt', '\n'.join(actions))
    write(out, 'in_game/common/generic_action_ai_lists/goblins_gathering.txt', '''
ga_gathering_ai_list = {
    potential = { ga_independent_goblin = yes can_see_situation = situation:ga_gathering_of_five }
    actions = { ga_send_supplies ga_swear_pact ga_offer_compact ga_challenge_crown ga_claim_homeland }
}
ga_eastern_ai_list = {
    potential = { has_variable = ga_unifier ga_controls_homeland = yes can_see_situation = situation:ga_eastern_hunger }
    actions = { ga_prepare_crossing ga_plan_eastern_foothold }
}
# Both parties reserve their sole negotiation slot; AI also retains 20 gold.
ga_harbor_bargains_ai_list = {
    potential = { ga_hb_free = yes gold >= 30 can_see_situation = situation:ga_gathering_of_five }
    actions = { ga_offer_harbor_pact ga_seek_pilot_bargain }
}
''')
    write(out, 'in_game/common/prices/goblins_gathering.txt', '''
ga_gathering_pact_price = { gold = 5 }
ga_gathering_aid_price = { gold = 10 }
ga_gathering_compact_price = { gold = 10 }
ga_gathering_claim_price = { prestige = 5 }
ga_gathering_crossing_price = { gold = 20 }
ga_gathering_target_price = { gold = 10 }
''')
    price_types = []
    for suffix, label in [('pact', 'Harbor Pact'), ('aid', 'Send Supplies'),
                          ('compact', 'Offer Compact'), ('claim', 'Claim the Homeland'),
                          ('crossing', 'Prepare the Crossing'), ('target', 'Plan an Eastern Foothold')]:
        price = 'ga_gathering_' + suffix + '_price'
        modifier = price + '_cost_modifier'
        loc(price, label)
        loc('MODIFIER_TYPE_NAME_' + modifier, label + ' Cost')
        loc('MODIFIER_TYPE_DESC_' + modifier, 'Changes the cost of this action.')
        price_types.append(f'{modifier} = {{ color = bad percent = yes game_data = {{ category = country }} }}')
    write(out, 'main_menu/common/modifier_type_definitions/goblins_gathering.txt', '\n'.join(price_types))
    write(out, 'in_game/common/biases/goblins_gathering.txt', '''
ga_harbor_pact_opinion = { value = 35 months = 120 }
ga_received_supplies = { value = 30 months = 60 }
ga_oath_honored = { value = 25 months = 120 }
''' + sworn_pacts.biases() + kin_defense.biases())
    for key, text in [('ga_harbor_pact_opinion', 'The Harbor Pact'), ('ga_received_supplies', 'Grain and Iron Received'), ('ga_oath_honored', 'The Ashen Oath')]:
        loc(key, text)
    write(out, 'main_menu/common/static_modifiers/goblins_gathering.txt', '''
ga_cindermaw_drilled_captains = { land_morale_modifier = 0.05 }
ga_cindermaw_court_envoys = { diplomatic_reputation = 0.5 }
ga_cindermaw_counted_stores = { army_maintenance_efficiency = 0.10 }
ga_brackmaw_repaired_sluices = { global_food_capacity_modifier = 0.10 }
ga_reefhook_restored_beacons = { naval_morale_recovery = 0.05 }
ga_gathering_claimant = { diplomatic_reputation = 0.5 }
ga_gathering_defiant = { naval_morale_modifier = 0.05 }
ga_gathering_leadership = { land_morale_modifier = 0.05 }
ga_gathering_cooperation = { diplomatic_reputation = 0.5 }
ga_gathering_independence = { global_defensive = 0.10 }
ga_compact_guarantees = { subject_loyalty = 10 }
ga_unification_recovery = { global_monthly_control = 0.002 }
ga_crossing_preparations = { navy_transport_build_cost_modifier = -0.15 naval_morale_modifier = 0.05 }
ga_first_eastern_harbor = { naval_morale_recovery = 0.05 }
''' + harbor_bargains.modifiers(loc) + '\n' + early_projects.modifiers(loc) + '\n' + kin_defense.modifiers(loc))
    for key, text in [('ga_gathering_claimant', 'Claimant Among the Six'), ('ga_gathering_defiant', 'Our Shores, Our Crown'), ('ga_compact_guarantees', 'Guarantees of the Ashen Compact'), ('ga_unification_recovery', 'Six Crowns, One Hunger'), ('ga_crossing_preparations', 'The Eastern Crossing'), ('ga_first_eastern_harbor', 'The First Eastern Harbor')]:
        loc('STATIC_MODIFIER_NAME_' + key, text)
        loc('STATIC_MODIFIER_DESC_' + key, text + '. A temporary benefit from the Ashborn situation.')
    for key, name, description in [
        ('ga_gathering_leadership', 'Lead the Six', 'Our captains prepare to lead the Ashborn. Army morale increases by 5% for five years.'),
        ('ga_gathering_cooperation', 'Stand Together', 'Our envoys seek partners among the crowns. Diplomatic reputation increases by 0.5 for five years.'),
        ('ga_gathering_independence', 'Guard Our Shores', 'Our households prepare to defend their independence. Defensiveness increases by 10% for five years.'),
        ('ga_cindermaw_drilled_captains', 'One Fire, Many Blades', 'Grask drills the rival captains to hold their companies together beneath Cindermaw banners.'),
        ('ga_cindermaw_court_envoys', 'A Place at the Forge', 'Kragga carries offers of patronage and protection to the other Ashborn courts.'),
        ('ga_cindermaw_counted_stores', "Grakka's Muster Accounts", 'Grakka counts stores and wages before the captains promise another campaign.'),
        ('ga_brackmaw_repaired_sluices', 'Dry Granaries, Sound Gates', 'Repaired tidal gates protect the granaries. Province food storage limit increases by 10% for five years.\n\n$ga_province_food_storage_tt$'),
        ('ga_reefhook_restored_beacons', 'Lights Along the Shoals', 'Restored rescue beacons give returning crews confidence. Naval morale recovery increases by 5% for five years.'),
    ]:
        loc('STATIC_MODIFIER_NAME_' + key, name)
        loc('STATIC_MODIFIER_DESC_' + key, description)
    # Native conquest goal and peace costs; only the paid, selected target is valid.
    write(out, 'in_game/common/casus_belli/goblins_gathering.txt', '''
ga_cb_eastern_foothold = {
    years = 5
    create_visible = { always = no }
    create_enabled = { always = no }
    declare_enabled = {
        has_variable = ga_unifier
        has_variable = ga_eastern_target
        ga_controls_homeland = yes
        scope:target = { this = root.var:ga_eastern_target.owner }
    }
    province = { this = scope:actor.var:ga_eastern_target }
    war_goal_type = conquer_province
}
''')
    loc('ga_cb_eastern_foothold', 'Eastern Foothold')
    loc('ga_cb_eastern_foothold_desc', 'Secure the selected coastal province through a normal conquest war. No territory is awarded by the event chain.')

    def reply(num):
        # Event-local saved scope keeps simultaneous replies from overwriting names.
        return f'''save_scope_as = ga_offer_respondent
            var:ga_offer_sender ?= {{ trigger_event_non_silently = ga_gathering.{num} }}'''

    cleanup = 'remove_variable = ga_offer_sender remove_variable = ga_offer_pending'
    events = ['namespace = ga_gathering\n']
    events.append(event(1, 'A Seat Among the Six',
        'The mountains have shaken and the six crowns send their captains to the gathering. The Hunger Below binds us, but no crown commands all our shores. Shall we claim leadership, seek partners, or guard our independence? Use the Gathering of the Six situation to bargain for provisions or pilots, send aid, offer voluntary vassalage or obtain war justifications. Harbor Bargains purchase services, not alliances. Every homeland location must fall under one authority before the eastward ambition begins.',
        '\n'.join([
            option(1, 'a', 'Our crown shall lead them.', 'add_prestige = 5 add_country_modifier = { modifier = ga_gathering_leadership years = 5 mode = replace }', ai='factor = 3'),
            option(1, 'b', 'Find those worth standing beside.', 'add_prestige = 5 add_country_modifier = { modifier = ga_gathering_cooperation years = 5 mode = replace }', ai='factor = 3'),
            option(1, 'c', 'Our shores answer to us alone.', 'add_prestige = 5 add_country_modifier = { modifier = ga_gathering_independence years = 5 mode = replace }', ai='factor = 2')
        ])))
    # Keep the old event ID so a saved pending request closes without granting an alliance.
    events.append(event(2, 'An Earlier Harbor Offer',
        'This offer predates the new Harbor Bargains. It cannot create an alliance. Close it to return the old five-gold offer fee to its sender; new talks use the situation actions.',
        option(2, 'b', 'Return the fee and close the old offer.', '''if = { limit = { has_variable = ga_offer_pending has_variable = ga_offer_sender }
                var:ga_offer_sender ?= { add_gold = 5 }
            }
''' + reply(17)),
        after=cleanup))
    events.append(event(3, 'An Earlier Compact Offer',
        'This offer predates charter negotiations. Close it to return the ten-gold fee to its sender. It cannot create a subject; new Compact talks require proven cooperation and two seals.',
        option(3, 'b', 'Return the fee and close the old offer.',
               'if = { limit = { has_variable = ga_offer_pending has_variable = ga_offer_sender } var:ga_offer_sender ?= { add_gold = 10 } } ' + reply(18)),
        after=cleanup))
    events.append(event(4, 'An Oath Accepted',
        '[SCOPE.sCountry(\'ga_offer_respondent\').GetName] has accepted our protection under the Compact. Its dynasty and customs endure beneath our authority. Remaining independent kingdoms may still resist; the gathering ends only when every homeland location is held by us, our vassals, or our junior union partners.',
        option(4, 'a', 'Honor the oath.', 'add_prestige = 3')))
    for num, title, desc in [
        (16, 'Harbor Pact Accepted', "[SCOPE.sCountry('ga_offer_respondent').GetName] has accepted our Harbor Pact. Our kingdoms are now allied, with the usual obligations of an alliance."),
        (17, 'Harbor Pact Refused', "[SCOPE.sCountry('ga_offer_respondent').GetName] has declined our Harbor Pact. No alliance has been formed."),
        (18, 'Ashen Compact Refused', "[SCOPE.sCountry('ga_offer_respondent').GetName] has declined our offer to join the Ashen Compact. Its crown remains independent."),
    ]:
        events.append(event(num, title, desc, option(num, 'a', 'The answer is received.')))
    events.append(event(5, 'Six Crowns, One Hunger',
        'Every shore of the Ashborn homeland now answers to one authority. Some crowns may have fallen; others endure through oaths or a union. Our dynasty keeps its name. Beyond the smoke, the eastern coasts await. Unification grants no foreign territory.',
        option(5, 'a', 'Let the captains look east.', 'add_prestige = 10 add_country_modifier = { modifier = ga_unification_recovery years = 5 mode = replace }')))
    loc('ga_eastern_horizon_acknowledge_tt',
        'Acknowledge the start of The Eastern Hunger. This option has no immediate cost or reward.\n\n'
        'Next steps: use Ashborn Voyages to chart the European coast. In The Eastern Hunger situation, Prepare the Eastern Crossing buys a temporary fleet-preparation bonus, and Plan an Eastern Foothold buys a temporary casus belli for an eligible coastal province. These are separate paid actions.\n\n'
        'Your goal is to secure a European coastal foothold while keeping the Ashborn homeland united. You must obtain ships, troops and territory through normal gameplay; this event does not provide them or declare war.')
    events.append(event(6, 'Beyond the Ashen Horizon',
        'The homeland is united, but Europe must be approached by sea. Complete the existing exploration voyages to chart its coast. The Eastern Hunger situation offers paid fleet preparation and a temporary casus belli for a chosen coastal province. Build your ships, choose your enemy and win your war; neither land nor troops are provided.',
        option(6, 'a', 'Charts, provisions, then a harbor.', 'custom_tooltip = ga_eastern_horizon_acknowledge_tt')))
    events.append(event(7, 'One Hunger Beyond the Isles',
        'The island struggle is settled under a common authority. Our crown still stands and our succession customs remain. Our people may now share in an eastern expedition through the normal obligations of our vassalage or union.',
        option(7, 'a', 'Our house endures.')))
    events.append(event(8, 'The First Eastern Harbor',
        'Our realm has secured a European coastal foothold while the homeland remains united. It was acquired through the ordinary rules of diplomacy and war. The situation rewards the achievement with prestige and a temporary naval recovery benefit. No further territory is bestowed.',
        option(8, 'a', 'The eastern horizon is open.', 'add_prestige = 10 add_country_modifier = { modifier = ga_first_eastern_harbor years = 5 mode = replace }')))
    signatures = [
        (10, 'CDM', *(PROFILES['CDM'][k] for k in ('event_title','event_description','event_answer'))),
        (11, 'QBR', *(PROFILES['QBR'][k] for k in ('event_title','event_description','event_answer'))),
        (12, 'RHK', *(PROFILES['RHK'][k] for k in ('event_title','event_description','event_answer'))),
        (13, 'SFK', *(SHATTERFIN[k] for k in ('event_title','event_description','event_answer'))),
        (14, 'SWK', *(PROFILES['SWK'][k] for k in ('event_title','event_description','event_answer'))),
        (40, 'GTF', *(PROFILES['GTF'][k] for k in ('event_title','event_description','event_answer')))
    ]
    for num, tag, title, desc, answer in signatures:
        after = 'trigger_event_non_silently = { id = ga_gathering.15 days = 30 }' if tag == 'SFK' else ''
        choices = option(num, 'a', answer)
        if tag in early_projects.PROJECTS:
            choices, project_text = early_projects.choices(tag, option)
            # Project costs and rewards are shown by native option tooltips.
        events.append(event(num, title, desc, choices, trigger=f'tag = {tag}', after=after))
    events.append(event(15, SHATTERFIN['followup_title'], SHATTERFIN['followup_description'],
        option(15, 'a', SHATTERFIN['followup_answer']),
        trigger='tag = SFK NOT = { has_variable = ga_tidemother_council_seen }',
        immediate='set_variable = { name = ga_tidemother_council_seen value = yes }'))
    events.extend(harbor_bargains.events(event, option, loc))
    write(out, 'in_game/common/customizable_localization/goblins_harbor_receipts.txt', harbor_bargains.signed_recap(loc))
    events.extend(compact_talks.events(event, option, loc))
    events.extend(sworn_pacts.events(event, option, loc))
    events.extend(kin_defense.events(event, option, loc))
    sworn_pacts.localization(loc)
    write(out, 'in_game/events/goblins_gathering.txt', '\n'.join(events))

    for key, text in [
        ('ga_gathering_of_five', 'The Gathering of the Six'),
        ('ga_gathering_of_five_desc', 'The six Ashborn kingdoms compete to unite their homeland through conquest, vassalage or unions. Alliances help cooperation but do not complete the struggle. Every starting goblin location must be held within one realm.'),
        ('ga_eastern_hunger', 'The Eastern Hunger'),
        ('ga_eastern_hunger_desc', 'The united Ashborn look toward Europe. Chart a coast, pay for preparations and obtain a temporary conquest casus belli. A European coastal foothold completes this ambition; wars and peace deals follow the normal rules.'),
        ('ga_gathering_complete_tt', 'One independent Ashborn crown holds every homeland location through direct ownership, vassalage or junior union partners. Alliances and tributaries do not count.'),
        ('ga_eastern_start_tt', 'A recognized Ashborn unifier still holds the entire homeland within its realm.'),
        ('ga_eastern_complete_tt', 'A recognized Ashborn unifier holds the homeland and a coastal European foothold within its realm.'),
        ('ga_choose_kingdom', 'Choose an Ashborn Kingdom'),
        ('ga_no_kingdom_available', '@trigger_no! No eligible independent Ashborn kingdom is available.'),
        ('ga_choose_eastern_province', 'Choose a European Coastal Province'),
        ('ga_no_eastern_target', '@trigger_no! No eligible discovered European coastal province. Explore first, and check alliances, truces and diplomatic restrictions.'),
        ('ga_relations', 'Relations with the other kingdom')
    ]:
        loc(key, text)
    compact_talks.extra(out, write, loc)
    import gathering_panel
    gathering_panel.build(write, loc, out, homeland, TAGS)
    situation_progress.build(out, homeland, write, loc)
    localization = 'l_english:\n' + '\n'.join(' ' + k + ': "' + v.replace('"', '\\"').replace('\n', r'\n') + '"' for k, v in TEXT.items())
    write(out, 'main_menu/localization/english/goblins_gathering_l_english.yml', localization)
    return {'version': '0.5.5', 'homeland_locations': len(homeland), 'kingdoms': TAGS,
            'situations': 2, 'actions': len(actions), 'events': len(events) - 1,
            'free_foreign_land': False, 'automatic_war_declaration': False,
            'union_creation': 'native mechanics; recognized by completion',
            'engine_tested': False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT / 'mod')
    args = parser.parse_args()
    print(json.dumps(build(args.out), indent=2))
