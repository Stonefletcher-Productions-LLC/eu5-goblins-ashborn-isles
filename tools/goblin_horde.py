"""The Goblin Horde: a native international organization of every goblin crown.

Members may war on each other (no expulsions, no war ban), but the Horde joins
every defensive war against a non-member. Membership is automatic and permanent
for goblin crowns. The strongest homeland holder leads as Warchief.

Native reference (EU5 international_organizations/readme.txt, religious_leagues.txt,
japanese_shogunate.txt, generic_actions/unlockable_io_actions.txt).
"""
from PIL import Image, ImageOps

KEY = 'goblin_horde'
IO = f'international_organization:{KEY}'
TRIBUTE_GOLD = 10
HORNS_GOLD = 25


def definition():
    return f'''{KEY} = {{
    has_target = no
    unique = yes
    has_leader_country = yes
    leader_type = country
    leader_title_key = "GOBLIN_HORDE_LEADER"
    disband_if_no_leader = no
    leader_change_trigger_type = timed
    leader_change_method = score
    months_between_leader_changes = 60
    show_on_diplomatic_map = yes
    show_leave_message = no
    use_laws_as_join_reason = no
    can_invite_countries = no
    subject_limited = no
    expel_members_who_are_targets_of_other_members = no
    expel_members_who_target_the_leader = no
    expel_members_who_are_attackers_at_war_with_other_members = no
    expel_members_who_are_defenders_at_war_with_other_members = no
    opinion_bonus = 10

    create_visible_trigger = {{ always = no }}
    invite_visible_trigger = {{ always = no }}
    join_visible_trigger = {{ always = no }}

    can_join_trigger = {{ ga_is_goblin = yes is_rebel_country = no }}
    can_leave_trigger = {{ always = no }}
    auto_leave_trigger = {{ NOT = {{ ga_is_goblin = yes }} }}
    auto_disband_trigger = {{ always = no }}
    can_lead_trigger = {{ ga_independent_goblin = yes }}
    # The crown holding most of the homeland leads.
    leader_score = {{ value = ga_ui_homeland_count }}

    # Kin against outsiders: every member defends against a non-member attacker.
    # Wars between members never call the Horde.
    join_defensive_wars_always = {{
        custom_tooltip = {{
            text = goblin_horde_defense_tt
            scope:target ?= {{ NOT = {{ is_member_of_international_organization = root }} }}
        }}
    }}

    modifier = {{ global_defensive = 0.05 }}
    leader_modifier = {{ monthly_prestige = 0.05 diplomatic_reputation = 1 }}

    monthly_effect = {{
        every_country = {{
            limit = {{
                ga_is_goblin = yes
                NOT = {{ is_member_of_international_organization = root }}
                country_can_join_international_organization = root
            }}
            root = {{ add_country_to_international_organization = prev }}
        }}
        update_leader_country = yes
    }}

    ai_desire_to_join = {{ add = {{ desc = "GOBLIN_HORDE_KIN" value = 100 }} }}
    ai_desire_to_allow_new_member = {{ add = {{ desc = "GOBLIN_HORDE_KIN" value = 100 }} }}
}}
'''


def triggers():
    return f'''
ga_in_horde = {{
    exists = {IO}
    is_member_of_international_organization = {IO}
}}
'''


def founding():
    # Registered on monthly_country_pulse in gathering.py. The first goblin crown to tick
    # founds the Horde; its monthly effect gathers the rest.
    return f'''
ga_horde_founding = {{
    trigger = {{ ga_is_goblin = yes is_rebel_country = no NOT = {{ exists = {IO} }} }}
    effect = {{
        create_international_organization = {{
            type = international_organization_type:{KEY}
            add_country_to_international_organization = prev
            set_leader_country = prev
        }}
    }}
}}
'''


def picker():
    return f'''select_trigger = {{
        looking_for_a = international_organization
        source = actor
        target_flag = recipient
        name = "choose_international_organization"
        column = {{ data = name }}
        visible = {{ international_organization_type = international_organization_type:{KEY} }}
    }}'''


def actions(loc):
    loc('ga_horde_tribute', 'Send Tribute to the Warchief')
    loc('ga_horde_tribute_desc', f'Send {TRIBUTE_GOLD} gold to the Warchief of the Goblin Horde. The Warchief gains +25 opinion of us for ten years. Once every five years.')
    loc('ga_horde_war_horns', 'Sound the War Horns')
    loc('ga_horde_war_horns_desc', f'Warchief only. Spend {HORNS_GOLD} gold to rouse every crown of the Horde: +5% land morale for all members for two years. Once every ten years.')
    tribute = f'''ga_horde_tribute = {{
    type = internationalorganization
    ai_tick = monthly
    ai_tick_frequency = 12
    automation_tick = never
    potential = {{ scope:actor = {{ ga_in_horde = yes }} }}
    allow = {{
        scope:actor = {{ gold >= {TRIBUTE_GOLD} NOT = {{ is_leader_of_international_organization = {IO} }} }}
        exists = {IO}.leader_country
    }}
    cooldown = {{ type = ga_horde_tribute years = 5 }}
    {picker()}
    effect = {{
        scope:actor = {{ add_gold = -{TRIBUTE_GOLD} }}
        {IO}.leader_country = {{
            add_gold = {TRIBUTE_GOLD}
            add_opinion = {{ target = scope:actor modifier = ga_horde_tribute_paid }}
        }}
    }}
    ai_will_do = {{ add = -20 if = {{ limit = {{ scope:actor = {{ gold >= 100 }} }} add = 30 }} }}
}}
'''
    horns = f'''ga_horde_war_horns = {{
    type = internationalorganization
    ai_tick = monthly
    ai_tick_frequency = 12
    automation_tick = never
    potential = {{ scope:actor = {{ ga_in_horde = yes }} }}
    allow = {{ scope:actor = {{ gold >= {HORNS_GOLD} is_leader_of_international_organization = {IO} }} }}
    cooldown = {{ type = ga_horde_war_horns years = 10 }}
    {picker()}
    effect = {{
        scope:actor = {{ add_gold = -{HORNS_GOLD} }}
        {IO} = {{
            every_international_organization_member = {{
                add_country_modifier = {{ modifier = ga_horde_war_horns years = 2 mode = replace }}
            }}
        }}
    }}
    ai_will_do = {{ add = -20 if = {{ limit = {{ scope:actor = {{ at_war = yes gold >= 75 }} }} add = 40 }} }}
}}
'''
    return tribute + horns


def modifiers(loc):
    loc('STATIC_MODIFIER_NAME_ga_horde_war_horns', 'Horde War Horns')
    loc('STATIC_MODIFIER_DESC_ga_horde_war_horns', 'The Warchief has sounded the war horns across the Ashborn Isles.')
    return 'ga_horde_war_horns = { land_morale_modifier = 0.05 }'


def biases(loc):
    loc('ga_horde_tribute_paid', 'Tribute to the Warchief')
    return 'ga_horde_tribute_paid = { value = 25 months = 120 }\n'


def localization(loc):
    loc(KEY, 'Goblin Horde')
    loc(KEY + '_desc', 'Every goblin crown of the Ashborn Isles belongs to the Horde. Its crowns raid, rival and conquer one another freely, but when an outsider declares war on any of them, the whole Horde answers. The crown holding most of the homeland leads as Warchief.')
    loc('GOBLIN_HORDE_LEADER', 'Warchief')
    loc('GOBLIN_HORDE_KIN', 'Goblin kin')
    loc('goblin_horde_defense_tt', 'The attacker is not a member of the Goblin Horde. Wars between goblin crowns do not call the Horde.')


ICON = 'main_menu/gfx/interface/icons/international_organizations/goblin_horde.dds'
ILLUSTRATION = 'main_menu/gfx/interface/illustrations/international_organization_types/goblin_horde.dds'


def art(root, out, write_bytes):
    from build_infantry_art import dds
    with Image.open(root / 'art/horde/goblin_horde.png') as source:
        write_bytes(out / ILLUSTRATION, dds(ImageOps.fit(source.convert('RGB'), (1920, 826), method=Image.Resampling.LANCZOS), 'DXT1'))
    with Image.open(root / 'art/horde/goblin_horde_icon.png') as source:
        write_bytes(out / ICON, dds(ImageOps.fit(source.convert('RGB'), (128, 128), method=Image.Resampling.LANCZOS), 'DXT1'))
