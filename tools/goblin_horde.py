"""The Goblin Horde: a native international organization of every goblin crown.

Members may war on each other (no expulsions, no war ban), but the Horde joins
every defensive war against a non-member. Membership is automatic and permanent
for goblin crowns. The strongest homeland holder leads as Warchief.

Native reference (EU5 international_organizations/readme.txt, religious_leagues.txt,
japanese_shogunate.txt, generic_actions/unlockable_io_actions.txt).
"""
from PIL import Image, ImageDraw, ImageOps

KEY = 'goblin_horde'
IO = f'international_organization:{KEY}'
TRIBUTE_GOLD = 10
HORNS_GOLD = 25
MUSTER_GOLD = 50
FEUD_GOLD = 25
LEVY_MONTHS = 2
AID_GOLD = 30
CALM_PRESTIGE = 10


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
    subject_limited = no
    expel_members_who_are_targets_of_other_members = no
    expel_members_who_target_the_leader = no
    expel_members_who_are_attackers_at_war_with_other_members = no
    expel_members_who_are_defenders_at_war_with_other_members = no

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
    show_message = no
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
    show_message = no
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
    return tribute + horns + muster(loc) + feud(loc) + levy(loc) + petitions(loc)


def warchief_only():
    return f'scope:actor = {{ is_leader_of_international_organization = {IO} }}'


def muster(loc):
    # Native call-to-war shape (vanilla crusade.txt, hussite_wars_actions.txt): the second
    # target is one of the Warchief's own offensive wars against an outsider.
    loc('ga_horde_muster', 'Call the Muster')
    loc('ga_horde_muster_desc', f'Warchief only. Spend {MUSTER_GOLD} gold to call every crown of the Horde into one of our offensive wars against an outsider. Crowns already at war with us stay out. Once every ten years.')
    loc('ga_horde_muster_choose', 'Choose the war')
    loc('ga_horde_muster_none', '@trigger_no! We lead no offensive war against an outsider.')
    return f'''ga_horde_muster = {{
    type = internationalorganization
    show_message = no
    ai_tick = monthly
    ai_tick_frequency = 6
    automation_tick = never
    force_click_and_confirm_or_hold = yes
    potential = {{ scope:actor = {{ ga_in_horde = yes }} }}
    allow = {{ {warchief_only()} scope:actor = {{ gold >= {MUSTER_GOLD} }} }}
    cooldown = {{ type = ga_horde_muster years = 10 }}
    {picker()}
    select_trigger = {{
        looking_for_a = war
        source = actor
        target_flag = target
        name = "ga_horde_muster_choose"
        none_available_msg_key = "ga_horde_muster_none"
        column = {{ data = name }}
        visible = {{
            attacker_leader = scope:actor
            defender_leader = {{ NOT = {{ is_member_of_international_organization = {IO} }} }}
        }}
    }}
    effect = {{
        if = {{
            limit = {{ exists = scope:target }}
            scope:actor = {{ add_gold = -{MUSTER_GOLD} }}
            {IO} = {{
                every_international_organization_member = {{
                    limit = {{
                        this != scope:actor
                        NOT = {{ is_at_war_with = scope:actor }}
                    }}
                    join_war_as_attacker = {{ war = scope:target call_in_subjects = yes }}
                    add_country_modifier = {{ modifier = ga_horde_war_horns years = 2 mode = replace }}
                }}
            }}
        }}
        else = {{ custom_tooltip = ga_horde_muster_choose }}
    }}
    ai_will_do = {{ add = 50 }}
}}
'''


def feud(loc):
    # Native forced peace (vanilla hre.txt Enforce Landfriede): white_peace takes a war.
    loc('ga_horde_settle_feud', 'Settle a Feud')
    loc('ga_horde_settle_feud_desc', f'Warchief only. Spend {FEUD_GOLD} gold to end one war between two crowns of the Horde with a white peace. The Warchief cannot settle a feud it is fighting itself. Once every five years.')
    loc('ga_horde_settle_feud_choose', 'Choose the crown that started the feud')
    loc('ga_horde_settle_feud_none', '@trigger_no! No two crowns of the Horde are at war.')
    feud_war = f'''attacker_leader = root
                defender_leader = {{ is_member_of_international_organization = {IO} }}
                NOT = {{ defender_leader = scope:actor }}'''
    return f'''ga_horde_settle_feud = {{
    type = internationalorganization
    show_message = no
    ai_tick = monthly
    ai_tick_frequency = 12
    automation_tick = never
    potential = {{ scope:actor = {{ ga_in_horde = yes }} }}
    allow = {{ {warchief_only()} scope:actor = {{ gold >= {FEUD_GOLD} }} }}
    cooldown = {{ type = ga_horde_settle_feud years = 5 }}
    {picker()}
    select_trigger = {{
        looking_for_a = country
        source = recipient
        target_flag = target
        name = "ga_horde_settle_feud_choose"
        none_available_msg_key = "ga_horde_settle_feud_none"
        column = {{ data = name }}
        visible = {{
            root != scope:actor
            any_current_war = {{
                {feud_war}
            }}
        }}
    }}
    effect = {{
        if = {{
            limit = {{ exists = scope:target }}
            scope:actor = {{ add_gold = -{FEUD_GOLD} add_prestige = 5 }}
            scope:target = {{
                random_current_war = {{
                    limit = {{
                        attacker_leader = scope:target
                        defender_leader = {{ is_member_of_international_organization = {IO} }}
                        NOT = {{ defender_leader = scope:actor }}
                    }}
                    save_scope_as = ga_horde_feud_war
                }}
                white_peace = scope:ga_horde_feud_war
            }}
        }}
        else = {{ custom_tooltip = ga_horde_settle_feud_choose }}
    }}
    ai_will_do = {{ add = -20 if = {{ limit = {{ scope:actor = {{ at_war = no }} }} add = 30 }} }}
}}
'''


def levy(loc):
    # add_manpower block form from vanilla appanage_request_levies.txt.
    loc('ga_horde_levy', 'Raise the Warchief\'s Levy')
    loc('ga_horde_levy_desc', f'Warchief only. Every other crown of the Horde sends us {LEVY_MONTHS} months of its manpower. Each crown resents it: -15 opinion of the Warchief for five years. Once every ten years.')
    loc('ga_horde_levy_taken', 'Took Our Levy')
    return f'''ga_horde_levy = {{
    type = internationalorganization
    show_message = no
    ai_tick = monthly
    ai_tick_frequency = 12
    automation_tick = never
    potential = {{ scope:actor = {{ ga_in_horde = yes }} }}
    allow = {{ {warchief_only()} }}
    cooldown = {{ type = ga_horde_levy years = 10 }}
    {picker()}
    effect = {{
        {IO} = {{
            every_international_organization_member = {{
                limit = {{ this != scope:actor }}
                save_scope_as = ga_horde_levy_payer
                scope:actor = {{ add_manpower = {{ value = scope:ga_horde_levy_payer.monthly_manpower multiply = {LEVY_MONTHS} }} }}
                add_manpower = {{ value = monthly_manpower multiply = -{LEVY_MONTHS} }}
                add_opinion = {{ target = scope:actor modifier = ga_horde_levy_taken }}
            }}
        }}
    }}
    ai_will_do = {{ add = -20 if = {{ limit = {{ scope:actor = {{ at_war = yes }} }} add = 40 }} }}
}}
'''


# Petitions: the smaller crowns ask the Warchief for help. Each fires a request event
# (ga_gathering.43-45) to the Warchief, who grants or refuses; the answer comes back
# to the petitioner as .46 (granted) or .47 (refused).
FEUD_AGAINST_US = f'''defender_leader = scope:actor
                attacker_leader = {{ is_member_of_international_organization = {IO} NOT = {{ is_leader_of_international_organization = {IO} }} }}'''
PETITIONS = [
    ('ga_horde_ask_gold', 43, 'Plead for Plunder',
     f'Ask the Warchief for {AID_GOLD} gold from the Horde\'s plunder. The Warchief may grant it or refuse; a refusal costs the Warchief our goodwill. Once every five years.', ''),
    ('ga_horde_ask_calm', 44, 'Ask the Warchief to Calm Our Clans',
     'Ask the Warchief to lend its name to quiet our feuding clans. If granted, we gain stability and the Warchief spends prestige. Once every five years.', ''),
    ('ga_horde_appeal_feud', 45, 'Appeal to the Warchief',
     'Another crown of the Horde has attacked us. Ask the Warchief to end that war with a white peace. Once every five years.',
     f'''scope:actor = {{
            any_current_war = {{
                {FEUD_AGAINST_US}
            }}
        }}'''),
]


def petitions(loc):
    out = ''
    for key, num, name, desc, allow in PETITIONS:
        loc(key, name)
        loc(key + '_desc', desc)
        save_war = '' if key != 'ga_horde_appeal_feud' else f'''scope:actor = {{
            random_current_war = {{
                limit = {{
                    {FEUD_AGAINST_US}
                }}
                save_scope_as = ga_horde_feud_war
            }}
        }}'''
        out += f'''{key} = {{
    type = internationalorganization
    show_message = no
    ai_tick = monthly
    ai_tick_frequency = 12
    automation_tick = never
    potential = {{ scope:actor = {{ ga_in_horde = yes }} }}
    allow = {{
        scope:actor = {{ NOT = {{ is_leader_of_international_organization = {IO} }} }}
        exists = {IO}.leader_country
        {allow}
    }}
    cooldown = {{ type = {key} years = 5 }}
    {picker()}
    effect = {{
        scope:actor = {{ save_scope_as = ga_horde_petitioner }}
        {save_war}
        {IO}.leader_country = {{
            save_scope_as = ga_horde_warchief
            trigger_event_non_silently = ga_gathering.{num}
        }}
    }}
    ai_will_do = {{ add = 10 }}
}}
'''
    return out


def events(event, option, loc):
    petitioner = "[SCOPE.sCountry('ga_horde_petitioner').GetName]"
    warchief = "[SCOPE.sCountry('ga_horde_warchief').GetName]"
    answer = lambda granted: f'scope:ga_horde_petitioner = {{ add_opinion = {{ target = scope:ga_horde_warchief modifier = {"ga_horde_aid_given" if granted else "ga_horde_aid_refused"} }} trigger_event_non_silently = ga_gathering.{46 if granted else 47} }}'
    refuse = lambda num: option(num, 'b', 'Refuse. The Horde owes the weak nothing.', answer(False), ai='factor = 1')
    rule = '\n\n#bold Goblin Horde#! - Smaller crowns may petition the Warchief. Granting earns their goodwill (+25 opinion); refusing costs it (-20).'
    return [
        event(43, 'A Plea for Plunder',
            f"Envoys from {petitioner} kneel at our fire. Their coffers are empty and they ask the Warchief for a share of the Horde's plunder: {AID_GOLD} gold.{rule}",
            option(43, 'a', f'Give them {AID_GOLD} gold. A fed crown fights for us.',
                f'add_gold = -{AID_GOLD} scope:ga_horde_petitioner = {{ add_gold = {AID_GOLD} }} ' + answer(True),
                trigger=f'gold >= {AID_GOLD}', ai='factor = 2') + refuse(43)),
        event(44, 'Clans in Uproar',
            f"The clans of {petitioner} quarrel over every hearth and harbor. Their ruler asks the Warchief to speak and remind them whose Horde they belong to.{rule}",
            option(44, 'a', 'Speak for them. The clans will listen to the Warchief.',
                f'add_prestige = -{CALM_PRESTIGE} scope:ga_horde_petitioner = {{ add_stability = stability_mild_bonus }} ' + answer(True),
                ai='factor = 2') + refuse(44)),
        event(45, 'An Appeal Against Kin',
            f"{petitioner} has been attacked by another crown of the Horde and begs the Warchief to end the war. Goblins may fight goblins, but the Warchief may also say when enough blood has been spilled.{rule}",
            option(45, 'a', 'Enough. This feud ends now.',
                'scope:ga_horde_petitioner = { white_peace = scope:ga_horde_feud_war } ' + answer(True),
                trigger='exists = scope:ga_horde_feud_war', ai='factor = 2') + refuse(45)),
        event(46, 'The Warchief Answers',
            f"{warchief} has granted our petition. Whatever grudges lie between the crowns, the Warchief has stood by us.",
            option(46, 'a', 'The Warchief remembers its kin.')),
        event(47, 'The Warchief Refuses',
            f"{warchief} has refused our petition. We will remember who stood by us, and who did not.",
            option(47, 'a', 'We will not forget this.')),
    ]


def modifiers(loc):
    loc('STATIC_MODIFIER_NAME_ga_horde_war_horns', 'Horde War Horns')
    loc('STATIC_MODIFIER_DESC_ga_horde_war_horns', 'The Warchief has sounded the war horns across the Ashborn Isles.')
    return 'ga_horde_war_horns = { land_morale_modifier = 0.05 }'


def biases(loc):
    loc('ga_horde_tribute_paid', 'Tribute to the Warchief')
    loc('ga_horde_aid_given', 'Answered Our Petition')
    loc('ga_horde_aid_refused', 'Refused Our Petition')
    # EU5 asks every IO type for an io_opinion_<key> bias: members' standing opinion of each other.
    return 'io_opinion_goblin_horde = { value = 10 }\nga_horde_tribute_paid = { value = 25 months = 120 }\nga_horde_levy_taken = { value = -15 months = 60 }\nga_horde_aid_given = { value = 25 months = 120 }\nga_horde_aid_refused = { value = -20 months = 60 }\n'


ACTIONS = ('ga_horde_tribute', 'ga_horde_war_horns', 'ga_horde_muster', 'ga_horde_settle_feud',
           'ga_horde_levy', 'ga_horde_ask_gold', 'ga_horde_ask_calm', 'ga_horde_appeal_feud')


def ai_list():
    # Native AI lists keep the AI from scanning every action every tick.
    return f'''ga_horde_ai_list = {{
    potential = {{ ga_in_horde = yes }}
    actions = {{ {' '.join(ACTIONS)} ga_horde_ship_kin }}
}}
'''


def localization(loc):
    loc(KEY, 'Goblin Horde')
    loc(KEY + '_desc', 'Every goblin crown of the Ashborn Isles belongs to the Horde. Its crowns raid, rival and conquer one another freely, but when an outsider declares war on any of them, the whole Horde answers. The crown holding most of the homeland leads as Warchief.')
    loc('io_opinion_goblin_horde', 'Goblin Horde kin')
    loc('GOBLIN_HORDE_LEADER', 'Warchief')
    loc('GOBLIN_HORDE_KIN', 'Goblin kin')
    loc('diplomatic_status_goblin_horde_name', 'Goblin Horde')
    loc('diplomatic_status_goblin_horde_tooltip', '#T Goblin Horde#!\nThis country belongs to the Goblin Horde. If an outsider attacks it, every other crown of the Horde is called to arms.')
    loc('goblin_horde_list_who_tt', '$WHO$ is in the Goblin Horde with $LIST$. They defend each other against anyone outside the Horde')
    loc('goblin_horde_defense_tt', 'The attacker is not a member of the Goblin Horde. Wars between goblin crowns do not call the Horde.')


ICON = 'main_menu/gfx/interface/icons/international_organizations/goblin_horde.dds'
ILLUSTRATION = 'main_menu/gfx/interface/illustrations/international_organization_types/goblin_horde.dds'


def art(root, out, write_bytes):
    from build_infantry_art import dds
    with Image.open(root / 'art/horde/goblin_horde.png') as source:
        write_bytes(out / ILLUSTRATION, dds(ImageOps.fit(source.convert('RGB'), (1920, 826), method=Image.Resampling.LANCZOS), 'DXT1'))
    with Image.open(root / 'art/horde/goblin_horde_icon.png') as source:
        write_bytes(out / ICON, dds_rgba(emblem(source)))


def emblem(source):
    """The volcano medallion at the centre of the clan ring, on transparency like vanilla IO icons.

    The full ring of six clan banners reads as a busy square at the 32 px top-bar size.
    """
    cx, cy, r = 512 * source.width // 1024, 488 * source.height // 1024, 212 * source.width // 1024
    image = source.convert('RGBA').crop((cx - r, cy - r, cx + r, cy + r)).resize((512, 512), Image.Resampling.LANCZOS)
    mask = Image.new('L', (2048, 2048), 0)
    ImageDraw.Draw(mask).ellipse((8, 8, 2040, 2040), fill=255)
    image.putalpha(mask.resize((512, 512), Image.Resampling.LANCZOS))
    return image.resize((128, 128), Image.Resampling.LANCZOS)


def dds_rgba(image):
    """DXT5 with real alpha and a full mip chain, like vanilla IO icons (Pillow encodes each level)."""
    import io, struct
    levels = []
    while True:
        buffer = io.BytesIO()
        image.save(buffer, 'DDS', pixel_format='DXT5')
        levels.append(buffer.getvalue()[128:])
        if image.size == (1, 1):
            break
        image = image.resize((max(1, image.width // 2), max(1, image.height // 2)), Image.Resampling.LANCZOS)
    width = height = 128
    header = [124, 0xA1007, height, width, len(levels[0]), 0, len(levels)] + [0] * 11
    header += [32, 4, int.from_bytes(b'DXT5', 'little'), 0, 0, 0, 0, 0]
    header += [0x401008, 0, 0, 0, 0]
    return b'DDS ' + struct.pack('<31I', *header) + b''.join(levels)
