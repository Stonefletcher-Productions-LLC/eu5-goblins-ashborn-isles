"""The Goblin Shore: goblin settlement on the European mainland and the backlash it draws.

The Eastern Hunger ends with a first European harbor. This chain picks up from there for
every goblin crown that holds mainland land, unifier or not, since crowns may also grab
land in their own wars. Native systems carry it: a situation with paid actions, pops moved
with native add_pop/split_pop, a native conquest casus belli for European neighbours, the
Goblin Horde for mutual aid, and the Old World debate for courts that have not met us yet.

Native reference (EU5 1.3): situations/readme.txt, casus_belli/push_back_colonizers.txt and
readme.txt, scripted_effects/location_effects.txt (transfer_pop, add_pop, split_pop).
"""
from ashborn_roster import TAGS
from event_art import image
from goblin_horde import IO, picker as horde_picker

NAMESPACE = 'ga_mainland'
SITUATION = 'ga_goblin_shore'
SETTLED_GOAL = 5          # goblin-majority mainland locations one crown needs to end the situation
SETTLERS = 3              # pop size moved by Send Settlers Across (thousands)
KIN_SETTLERS = 2          # pop size shipped by a Horde kin
ALARM_YEARS = 10          # a European neighbour reacts again after this long
GOBLIN = 'culture = { has_culture_group = culture_group:cm_goblin_group }'
HUNGER = 'religion = religion:cm_hunger_below'

PRICES = {
    'ga_ms_settlers_price': (20, 'Send Settlers Across'),
    'ga_ms_tongue_price': (15, 'Teach Them Our Tongue'),
    'ga_ms_shrine_price': (15, 'Raise a Hunger Shrine'),
    'ga_ms_kin_price': (10, 'Ship Kin to the Shore'),
}

# key: (opinion value, months, name)
BIASES = {
    'ga_ms_goblin_menace': (-25, 120, 'Goblins on Our Border'),
    'ga_ms_shore_trade': (20, 120, 'Shore Trade'),
    'ga_ms_friars_welcomed': (15, 120, 'Friars Welcomed'),
    'ga_ms_paid_off': (25, 60, 'Bought Peace'),
    'ga_ms_kin_answered': (30, 120, 'Answered Our Call'),
    'ga_ms_kin_ignored': (-20, 120, 'Ignored Our Call'),
    'ga_ms_townsfolk_charter': (15, 120, 'Chartered the Townsfolk'),
    'ga_ms_townsfolk_driven': (-20, 120, 'Drove Out the Townsfolk'),
}

# key: (modifier body, name, description)
MODIFIERS = {
    'ga_ms_first_landing': ('global_population_growth = 0.001', 'Settler Fever',
        'Every crowded hearth in the homeland has a cousin who wants a berth on the next ship east.'),
    'ga_ms_mixed_market': ('global_production_efficiency = 0.03', 'Mixed Markets',
        'Mainland traders haggle at our stockade gates. They still count their fingers after every handshake.'),
    'ga_ms_hold_the_shore': ('global_defensive = 0.10', 'Hold the Shore',
        'Every goblin on the mainland sleeps with a blade in reach.'),
    'ga_ms_let_them_come': ('land_morale_modifier = 0.05', 'Let Them Come',
        'Our captains have heard the church bells, and answered with war drums.'),
    'ga_ms_shore_kingdom': ('diplomatic_reputation = 1 global_production_efficiency = 0.05', 'The Goblin Shore',
        'Goblin towns stand on the mainland, and the mainland has stopped pretending they will go away.'),
    'ga_ms_back_to_sea': ('land_morale_modifier = 0.05 naval_morale_modifier = 0.05', 'Driven Back to the Sea',
        'The mainland pushed us off its shore. Every crew remembers the names of the towns we lost.'),
    'ga_ms_bells_rung': ('global_defensive = 0.10', 'The Bells Rung',
        'Watchmen on every tower, militia in every square: the goblins will not take another street.'),
    'ga_ms_shore_market': ('global_production_efficiency = 0.02', 'Goblin Goods',
        'Obsidian, ash-salt and strange dyes come over the border, and our merchants ask no questions.'),
    'ga_ms_friars_sent': ('diplomatic_reputation = 0.5', 'Friars Among the Goblins',
        'Our friars preach in the goblin stockades. Few listen, but the goblins have stopped throwing things.'),
}
LOCATION_MODIFIERS = {
    'ga_ms_stockade': ('local_defensive = 0.1', 'Goblin Stockade',
        'Sharpened stakes, ash-black banners and a watch that never sleeps.'),
    'ga_ms_resentment': ('local_unrest = 0.05', 'Old Townsfolk Resentment',
        'The old families of the town remember when the market spoke their tongue.'),
}

# Each: (num, art, title, desc, options); option: (letter, name, trigger, effect, ai factor)
EVENTS = []


def ev(num, art, title, desc, options, trigger, immediate=''):
    EVENTS.append((num, art, title, desc, options, trigger, immediate))


def random_shore(effect):
    """Run effect in one of root's goblin-held mainland locations."""
    return f'random_owned_location = {{ limit = {{ ga_mainland_location = yes }} {effect} }}'


def take_from_homeland(country, size):
    """Shrink the largest goblin pop in country's capital, so settlers leave the homeland."""
    return f'''{country}.capital ?= {{
            ordered_pop = {{
                limit = {{ {GOBLIN} pop_size > {size * 3} }}
                order_by = pop_size
                max = 1
                add_pop_size = -{size}
            }}
        }}'''


def settle(country, size):
    """Location scope: add a goblin peasant pop of country's culture and religion."""
    return f'add_pop = {{ culture = {country}.culture religion = {country}.religion type = pop_type:peasants size = {size} }}'


def teach(country, fraction):
    """Location scope: part of every non-goblin pop takes up country's culture."""
    return f'every_pop = {{ limit = {{ NOT = {{ {GOBLIN} }} }} split_pop = {{ fraction = {fraction} culture = {country}.culture }} }}'


HOLDER = 'ga_is_goblin = yes ga_holds_mainland = yes'
FOREIGN = 'ga_is_goblin = no'
ACCUSER = "[SCOPE.sCountry('ga_ms_accuser').GetName]"
KIN = "[SCOPE.sCountry('ga_ms_kin').GetName]"
EVERY_NEIGHBOUR = 'every_country = { limit = { ga_is_goblin = no is_neighbor_of = root } '

ev(1, 'eastern_harbor', 'A Goblin Shore',
   "Our banners fly over mainland streets. The old townsfolk watch from their shutters while our crews pace out "
   "plots for longhouses, smoke-pits and a shrine to the Hunger Below. Back home, every crowded hearth wants a berth on "
   "the next ship. The mainland courts will not leave us here in peace for long.\n\n"
   "#bold The Goblin Shore#! - Send settlers, teach the locals our tongue and raise shrines from the situation panel. "
   f"A crown that turns {SETTLED_GOAL} mainland locations goblin-majority makes the shore ours. European neighbours "
   "may take a casus belli to drive us out, and the Goblin Horde answers any outsider who attacks.", [
    ('a', 'Fill the ships. The shore needs hands.', '',
     f'add_country_modifier = {{ modifier = ga_ms_first_landing years = 10 mode = replace }}\n        '
     f'{random_shore(settle("root", SETTLERS))}\n        {take_from_homeland("root", SETTLERS)}', 3),
    ('b', 'Build the stockade first.', '',
     f'add_prestige = 10\n        {random_shore("add_location_modifier = { modifier = ga_ms_stockade years = 20 mode = replace }")}', 2),
], HOLDER, immediate='set_variable = { name = ga_ms_landed value = yes }')

ev(2, 'iberia', 'Market Day at the Stockade',
   "Mainland traders have started setting up stalls outside our stockade gates. They sell salt fish, wool and "
   "wine, and they buy obsidian and ash-salt at twice what Lisbon pays. Some of our young crews have started "
   "trading words as well as goods, and the old captains do not like it.", [
    ('a', 'Open the gates. Coin is coin.', '',
     'add_country_modifier = { modifier = ga_ms_mixed_market years = 10 mode = replace }', 2),
    ('b', 'Let them learn our tongue, not we theirs.', '',
     f'{random_shore(teach("root", 0.1) + " add_location_modifier = { modifier = ga_ms_resentment years = 10 mode = replace }")}', 2),
    ('c', 'Keep the gates shut and the stakes sharp.', '',
     f'add_prestige = 5\n        {random_shore("add_location_modifier = { modifier = ga_ms_stockade years = 20 mode = replace }")}', 1),
], HOLDER)

ev(3, 'old_world_tavern', 'The Old Townsfolk',
   "The families who held our mainland towns before us are still here. They keep their own church, their own "
   "guild hall and their own grudges. Some have started leaving for their kin across the border, taking stories "
   "of goblin cruelty with them. The rest wait to see what kind of masters we are.", [
    ('a', 'Let them go. More room for our own.', '',
     f'{random_shore("every_pop = { limit = { NOT = { " + GOBLIN + " } } add_pop_size = { value = pop_size multiply = -0.15 } } " + settle("root", 1))}\n        '
     f'custom_tooltip = {NAMESPACE}.3.a_tt\n        hidden_effect = {{ {EVERY_NEIGHBOUR}add_opinion = {{ target = root modifier = ga_ms_townsfolk_driven }} }} }}', 2),
    ('b', 'Grant them a charter. They keep their guilds; we keep the keys.', 'trigger = { gold >= 15 }',
     f'add_gold = -15\n        custom_tooltip = {NAMESPACE}.3.b_tt\n        hidden_effect = {{ {EVERY_NEIGHBOUR}add_opinion = {{ target = root modifier = ga_ms_townsfolk_charter }} }} }}', 2),
    ('c', 'Garrison the town and let them grumble.', 'trigger = { gold >= 10 }',
     f'add_gold = -10\n        {random_shore("add_location_modifier = { modifier = ga_ms_stockade years = 20 mode = replace } add_location_modifier = { modifier = ga_ms_resentment years = 10 mode = replace }")}', 1),
], HOLDER)

ev(4, 'departure', 'Berths to the East',
   "Word of free land on the mainland has run through every homeland harbor. Families sleep on the quays "
   "waiting for a ship, and the clan elders complain that the fields are emptying. The quartermasters ask "
   "whether to give the berths away or keep the hands at home.", [
    ('a', 'Give them the berths.', '',
     f'{random_shore(settle("root", SETTLERS))}\n        {take_from_homeland("root", SETTLERS)}', 2),
    ('b', 'The homeland needs its hands.', '', 'add_stability = stability_mild_bonus', 1),
], HOLDER)

ev(5, 'old_world_demons', 'Goblins on Our Border',
   "Goblins hold a town on our border. Pilgrims swear they have seen the creatures' smoke-shrines from the road, "
   "and merchants swear that goblin obsidian is the best they have ever sold. The bishops want the bells rung and "
   "the goblins driven into the sea. The merchants would rather keep the road open.\n\n"
   "Whatever we choose, any war on a goblin crown brings the whole Goblin Horde against us.", [
    ('a', 'Ring the bells. Drive them into the sea.', '',
     f'add_country_modifier = {{ modifier = ga_ms_bells_rung years = 10 mode = replace }}\n        '
     f'custom_tooltip = {NAMESPACE}.5.a_tt\n        save_scope_as = ga_ms_accuser\n        '
     'every_country = { limit = { ga_holds_mainland = yes is_neighbor_of = root }\n'
     '            save_scope_as = ga_ms_holder\n'
     '            root = { add_casus_belli = { type = casus_belli:ga_cb_drive_out_goblins target = scope:ga_ms_holder years = 10 } }\n'
     '            hidden_effect = { root = { add_opinion = { target = scope:ga_ms_holder modifier = ga_ms_goblin_menace } } }\n'
     f'            trigger_event_non_silently = {NAMESPACE}.6\n        }}',
     'factor = 2 modifier = { add = 3 has_variable = ga_owr_demons }'),
    ('b', 'Keep the road open, and a sword by the door.', '',
     f'add_country_modifier = {{ modifier = ga_ms_shore_market years = 10 mode = replace }}\n        '
     f'custom_tooltip = {NAMESPACE}.5.b_tt\n        hidden_effect = {{ every_country = {{ limit = {{ ga_holds_mainland = yes is_neighbor_of = root }}\n'
     '            add_opinion = { target = root modifier = ga_ms_shore_trade }\n'
     '            save_scope_as = ga_ms_holder\n'
     '            root = { add_opinion = { target = scope:ga_ms_holder modifier = ga_ms_shore_trade } }\n        } }',
     'factor = 2 modifier = { add = 2 has_variable = ga_owr_souls }'),
    ('c', 'Send friars across the border.', 'trigger = { has_variable = ga_owr_souls }',
     f'add_country_modifier = {{ modifier = ga_ms_friars_sent years = 10 mode = replace }}\n        '
     f'custom_tooltip = {NAMESPACE}.5.c_tt\n        hidden_effect = {{ every_country = {{ limit = {{ ga_holds_mainland = yes is_neighbor_of = root }}\n'
     '            add_opinion = { target = root modifier = ga_ms_friars_welcomed }\n        } }', 2),
], FOREIGN)

ev(6, 'foreign_sails', 'The Bells Ring Against Us',
   f"The church bells of {ACCUSER} have rung for three days. Its preachers call us spawn of the pit, and its "
   "captains have sworn to drive every goblin on the mainland into the sea. They are counting on fighting one "
   "crown alone. They have forgotten the Horde.", [
    ('a', 'Call the Horde. Every crown answers.', 'trigger = { ga_in_horde = yes }',
     'add_country_modifier = { modifier = ga_ms_hold_the_shore years = 5 mode = replace }\n        '
     f'custom_tooltip = {NAMESPACE}.6.a_tt\n        save_scope_as = ga_ms_kin\n        '
     f'{IO} ?= {{ every_international_organization_member = {{ limit = {{ NOT = {{ this = root }} }} trigger_event_non_silently = {NAMESPACE}.7 }} }}', 3),
    ('b', 'Buy them off with gold.', 'trigger = { gold >= 25 }',
     f'add_gold = -25\n        scope:ga_ms_accuser = {{ add_gold = 25 add_opinion = {{ target = root modifier = ga_ms_paid_off }} }}', 1),
    ('c', 'Let them come.', '',
     'add_prestige = 10\n        add_country_modifier = { modifier = ga_ms_let_them_come years = 5 mode = replace }', 1),
], HOLDER)

ev(7, 'kinship', 'Kin Across the Water',
   f"{KIN} holds a goblin shore on the mainland, and the mainland means to take it back. Its envoy reminds us "
   "that whatever blood lies between the crowns, the Horde does not leave kin to the outsiders. The Horde will "
   "fight in any war the mainland starts. What else will we send?", [
    ('a', 'Send gold for their walls.', 'trigger = { gold >= 20 }',
     f'add_gold = -20\n        scope:ga_ms_kin = {{ add_gold = 20 add_opinion = {{ target = root modifier = ga_ms_kin_answered }} }}', 2),
    ('b', 'Send settlers to fill their streets.', '',
     f'custom_tooltip = {NAMESPACE}.7.b_tt\n        scope:ga_ms_kin = {{ {random_shore(settle("root", KIN_SETTLERS))} add_opinion = {{ target = root modifier = ga_ms_kin_answered }} }}\n'
     f'        {take_from_homeland("root", KIN_SETTLERS)}', 2),
    ('c', 'Their shore, their problem.', '',
     'scope:ga_ms_kin = { add_opinion = { target = root modifier = ga_ms_kin_ignored } }', 1),
], 'ga_is_goblin = yes exists = scope:ga_ms_kin')

ev(8, 'pact_broken', 'Driven Back to the Sea',
   "The last of our mainland towns has fallen. Our crews rowed home through smoke, and the mainland bells rang "
   "the whole night. The shore is lost, but the charts are not, and every captain knows the way back.", [
    ('a', 'We will return.', '', 'add_country_modifier = { modifier = ga_ms_back_to_sea years = 10 mode = replace }', 1),
], 'ga_is_goblin = yes')

ev(9, 'unification', 'The Shore Is Ours',
   "Goblin towns now stand on the mainland, goblin-majority and goblin-built. The old townsfolk have learned our "
   "tongue or moved on, our shrines smoke beside their churches, and the mainland courts have stopped calling it a "
   "raid and started calling it a border. The Hunger Below has a second home.", [
    ('a', 'Let the mainland get used to us.', '',
     'add_prestige = 25\n        add_country_modifier = { modifier = ga_ms_shore_kingdom years = 25 mode = replace }', 1),
], 'ga_is_goblin = yes')

ev(10, 'kinship', 'A Goblin Shore Stands',
   "Another crown has made the mainland shore goblin. Whatever we think of its rulers, the mainland now has "
   "goblin towns, and every goblin captain walks a little taller in foreign ports.", [
    ('a', 'Kin is kin.', '', 'add_prestige = 10', 1),
], 'ga_is_goblin = yes')

OPTION_TOOLTIPS = {
    '3.a': 'Our European neighbours think worse of us.',
    '3.b': 'Our European neighbours think better of us.',
    '5.a': 'We gain a 10-year Drive Out the Goblins casus belli on every goblin crown that holds land on our border, and think worse of them.',
    '5.b': 'We and the goblin crowns on our border think better of each other.',
    '5.c': 'The goblin crowns on our border think better of us.',
    '6.a': 'Every other crown of the Goblin Horde hears our call. Whatever they send, the Horde already joins any war an outsider declares on us.',
    '7.b': f'Settlers from our homeland join their mainland towns.',
}


def situation_picker():
    return f'''select_trigger = {{
        looking_for_a = situation
        interaction_source_list = {{ situation:{SITUATION} = {{ add_to_list = source }} }}
        target_flag = recipient
        name = choose_situation
        column = {{ data = name }}
        visible = {{ this = situation:{SITUATION} situation_is_active = yes }}
    }}'''


def shore_picker(extra=''):
    return f'''select_trigger = {{
        looking_for_a = province
        target_flag = target
        name = ga_ms_choose_shore
        none_available_msg_key = ga_ms_no_shore
        column = {{ data = name }}
        visible = {{
            any_location_in_province = {{ owner = scope:actor ga_mainland_location = yes {extra} }}
        }}
    }}'''


def in_target(effect, extra=''):
    return f'scope:target = {{ random_location_in_province = {{ limit = {{ owner = scope:actor ga_mainland_location = yes {extra} }} {effect} }} }}'


ACTIONS = [
    ('ga_ms_send_settlers', 'Send Settlers Across',
     f'Pay {PRICES["ga_ms_settlers_price"][0]} gold to ship goblin peasants from our capital to one of our mainland locations. '
     'The location gets a stockade for ten years. Once every two years.', 'ga_ms_settlers_price', 2, '',
     in_target(settle('scope:actor', SETTLERS) + ' add_location_modifier = { modifier = ga_ms_stockade years = 10 mode = replace }')
     + '\n        ' + take_from_homeland('scope:actor', SETTLERS),
     'add = 40'),
    ('ga_ms_teach_tongue', 'Teach Them Our Tongue',
     f'Pay {PRICES["ga_ms_tongue_price"][0]} gold to bring our tongue and customs to the old townsfolk of one mainland location. '
     'A tenth of every non-goblin pop there adopts our culture; the rest resent it for ten years. Once every three years.',
     'ga_ms_tongue_price', 3, '',
     in_target(teach('scope:actor', 0.1) + ' add_location_modifier = { modifier = ga_ms_resentment years = 10 mode = replace }'),
     'add = 25'),
    ('ga_ms_raise_shrine', 'Raise a Hunger Shrine',
     f'Pay {PRICES["ga_ms_shrine_price"][0]} gold to raise a smoke-shrine to the Hunger Below in one mainland location. '
     'A tenth of every pop there of another faith converts. Ashen Covenant crowns only. Once every three years.',
     'ga_ms_shrine_price', 3, HUNGER,
     in_target('every_pop = { limit = { NOT = { religion = scope:actor.religion } } split_pop = { fraction = 0.1 religion = scope:actor.religion } }'),
     'add = 20'),
]


def actions(loc):
    out = []
    for key, name, desc, price, years, allow, effect, ai in ACTIONS:
        loc(key, name)
        loc(key + '_desc', desc)
        out.append(f'''{key} = {{
    type = situation
    show_message = no
    potential = {{ scope:actor = {{ ga_is_goblin = yes is_subject = no ga_holds_mainland = yes }} }}
    allow = {{ scope:actor = {{ {allow} }} }}
    automation_tick = never
    ai_tick = monthly
    ai_tick_frequency = 6
    cooldown = {{ type = {key} years = {years} }}
    price = price:{price}
    {situation_picker()}
    {shore_picker()}
    effect = {{ if = {{ limit = {{ exists = scope:target }}
        {effect}
    }} }}
    ai_will_do = {{ {ai} }}
}}
''')
    # The Horde button: any member ships settlers to a kin crown that holds a mainland shore.
    loc('ga_horde_ship_kin', 'Ship Kin to the Shore')
    loc('ga_horde_ship_kin_desc', f'Pay {PRICES["ga_ms_kin_price"][0]} gold to ship settlers from our capital to the mainland towns of another '
        'Horde crown. It gains +30 opinion of us for ten years. Once every five years.')
    kin_exists = f'{IO} = {{ any_international_organization_member = {{ ga_holds_mainland = yes NOT = {{ this = scope:actor }} }} }}'
    out.append(f'''ga_horde_ship_kin = {{
    type = internationalorganization
    ai_tick = monthly
    ai_tick_frequency = 12
    automation_tick = never
    potential = {{ scope:actor = {{ ga_in_horde = yes }} }}
    allow = {{
        custom_tooltip = {{ text = ga_ms_kin_shore_tt {kin_exists} }}
    }}
    cooldown = {{ type = ga_horde_ship_kin years = 5 }}
    show_message = no
    price = price:ga_ms_kin_price
    {horde_picker()}
    effect = {{
        {IO} = {{
            random_international_organization_member = {{
                limit = {{ ga_holds_mainland = yes NOT = {{ this = scope:actor }} }}
                {random_shore(settle("scope:actor", KIN_SETTLERS))}
                add_opinion = {{ target = scope:actor modifier = ga_ms_kin_answered }}
            }}
        }}
        {take_from_homeland("scope:actor", KIN_SETTLERS)}
    }}
    ai_will_do = {{ add = 15 }}
}}
''')
    return '\n'.join(out)


def events(loc):
    out = [f'namespace = {NAMESPACE}\n# The Goblin Shore: mainland settlement and European backlash, paced by goblins_mainland on_actions.\n']
    for num, art, title, desc, options, trigger, immediate in EVENTS:
        key = f'{NAMESPACE}.{num}'
        loc(key + '.title', title)
        loc(key + '.desc', desc)
        body = []
        for letter, name, opt_trigger, effect, chance in options:
            loc(f'{key}.{letter}', name)
            if f'{num}.{letter}' in OPTION_TOOLTIPS:
                loc(f'{key}.{letter}_tt', OPTION_TOOLTIPS[f'{num}.{letter}'])
            ai = chance if isinstance(chance, str) else f'factor = {chance}'
            lines = [f'    option = {{ name = {key}.{letter} ai_chance = {{ {ai} }}']
            lines += ['        ' + part for part in (opt_trigger, effect) if part]
            body.append('\n'.join(lines) + '\n    }')
        imm = f'\n    immediate = {{ {immediate} }}' if immediate else ''
        out.append(f'''{key} = {{
    type = country_event
    outcome = neutral
    title = {key}.title
    desc = {key}.desc
    trigger = {{ {trigger} }}
    image = "{image(key)}"{imm}
{chr(10).join(body)}
}}
''')
    return '\n'.join(out)


def situation():
    bounded = ''.join(f'''        c:{tag} ?= {{
            if = {{
                limit = {{ ga_holds_mainland = yes NOT = {{ has_variable = ga_ms_landed }} }}
                trigger_event_non_silently = {NAMESPACE}.1
            }}
        }}
''' for tag in TAGS)
    return f'''{SITUATION} = {{
    monthly_spawn_chance = monthly_spawn_chance_unique
    can_start = {{ custom_tooltip = {{
        text = ga_ms_start_tt
        any_country = {{ ga_independent_goblin = yes ga_holds_mainland = yes }}
    }} }}
    can_end = {{ custom_tooltip = {{
        text = ga_ms_end_tt
        any_country = {{ ga_shore_settled = yes }}
    }} }}
    visible = {{ OR = {{ ga_is_goblin = yes has_variable = ga_ms_alarmed }} }}
    # Only the six crowns can land; avoid a global scan every month.
    on_monthly = {{
{bounded}    }}
    on_ending = {{
        every_country = {{
            limit = {{ ga_shore_settled = yes }}
            set_variable = {{ name = ga_ms_settled value = yes }}
            trigger_event_non_silently = {NAMESPACE}.9
        }}
        every_country = {{
            limit = {{ ga_is_goblin = yes NOT = {{ has_variable = ga_ms_settled }} }}
            trigger_event_non_silently = {NAMESPACE}.10
        }}
    }}
}}
'''


def on_actions():
    return f'''monthly_country_pulse = {{ on_actions = {{ ga_ms_goblin_monthly ga_ms_foreign_monthly }} }}
# Each goblin crown that has landed gets the settlement events in order, two years apart,
# and hears it when it loses its last mainland town.
ga_ms_goblin_monthly = {{
    trigger = {{
        ga_is_goblin = yes
        has_variable = ga_ms_landed
        NOT = {{ has_variable = ga_ms_cooldown }}
    }}
    effect = {{
        if = {{ limit = {{ ga_holds_mainland = no }}
            if = {{ limit = {{ NOT = {{ has_variable = ga_ms_driven_out }} }}
                set_variable = {{ name = ga_ms_driven_out value = yes }}
                trigger_event_non_silently = {{ id = {NAMESPACE}.8 }}
            }}
        }}
        else = {{
            remove_variable = ga_ms_driven_out
            if = {{ limit = {{ NOT = {{ has_variable = ga_ms_started }} }}
                set_variable = {{ name = ga_ms_started value = yes }}
                set_variable = {{ name = ga_ms_cooldown value = yes years = 2 }}
            }}
            else_if = {{ limit = {{ NOT = {{ has_variable = ga_ms_2_done }} }}
                set_variable = {{ name = ga_ms_2_done value = yes }}
                set_variable = {{ name = ga_ms_cooldown value = yes years = 2 }}
                trigger_event_non_silently = {{ id = {NAMESPACE}.2 }}
            }}
            else_if = {{ limit = {{ NOT = {{ has_variable = ga_ms_3_done }} }}
                set_variable = {{ name = ga_ms_3_done value = yes }}
                set_variable = {{ name = ga_ms_cooldown value = yes years = 2 }}
                trigger_event_non_silently = {{ id = {NAMESPACE}.3 }}
            }}
            else_if = {{ limit = {{ NOT = {{ has_variable = ga_ms_4_done }} }}
                set_variable = {{ name = ga_ms_4_done value = yes }}
                set_variable = {{ name = ga_ms_cooldown value = yes years = 2 }}
                trigger_event_non_silently = {{ id = {NAMESPACE}.4 }}
            }}
        }}
    }}
}}
# A European court bordering a goblin shore reacts, and again every {ALARM_YEARS} years.
# A court that never met the goblins is marked for the Old World debate first
# (ga_owr_foreign_monthly fires ga_old_world.1 or .6 six months later).
ga_ms_foreign_monthly = {{
    trigger = {{
        ga_is_goblin = no
        NOT = {{ has_variable = ga_ms_alarm_cooldown }}
        any_owned_location = {{ ga_mainland_location = yes }}
        ga_shore_neighbour = yes
    }}
    effect = {{
        if = {{ limit = {{ NOT = {{ has_variable = ga_received_goblin_first_contact }} }}
            set_variable = {{ name = ga_received_goblin_first_contact value = yes }}
            set_variable = {{ name = ga_ms_alarm_cooldown value = yes months = 9 }}
        }}
        else = {{
            set_variable = {{ name = ga_ms_alarmed value = yes }}
            set_variable = {{ name = ga_ms_alarm_cooldown value = yes years = {ALARM_YEARS} }}
            trigger_event_non_silently = {{ id = {NAMESPACE}.5 }}
        }}
    }}
}}
'''


def triggers():
    return f'''# location scope: European mainland, outside the Ashborn homeland.
ga_mainland_location = {{
    continent = continent:europe
    NOT = {{ area = area:cm_cindermaw_area }}
}}

# location scope: a goblin-majority mainland location.
ga_settled_mainland_location = {{
    ga_mainland_location = yes
    dominant_culture ?= {{ has_culture_group = culture_group:cm_goblin_group }}
}}

# country scope
ga_holds_mainland = {{
    ga_is_goblin = yes
    any_owned_location = {{ ga_mainland_location = yes }}
}}

ga_shore_settled = {{
    ga_independent_goblin = yes
    any_owned_location = {{ ga_settled_mainland_location = yes count >= {SETTLED_GOAL} }}
}}

# A non-goblin country that borders a goblin crown holding mainland land.
ga_shore_neighbour = {{
    ga_is_goblin = no
    save_temporary_scope_as = ga_ms_self
    any_country = {{ ga_holds_mainland = yes is_neighbor_of = scope:ga_ms_self }}
}}
'''


def casus_belli():
    # Native conquest goal, like cb_push_back_colonizers: any court can fabricate it
    # against a goblin crown on its border; event 5 grants it at once.
    return '''ga_cb_drive_out_goblins = {
    years = 10
    create_visible = { ga_is_goblin = no }
    create_enabled = {
        ga_is_goblin = no
        scope:target = { ga_holds_mainland = yes is_neighbor_of = root }
    }
    declare_enabled = {
        ga_is_goblin = no
        scope:target = { ga_holds_mainland = yes }
    }
    #scopes are actor/recipient for countries, while root = province checked.
    province = {
        any_location_in_province = { owner = scope:recipient ga_mainland_location = yes }
    }
    additional_war_enthusiasm_attacker = 0.25
    war_goal_type = conquer_province
}
'''


PANEL = '''
situation_panel = {
    blockoverride "situation_subheader_content" {}
    blockoverride "situation_panel_main_content" {
        text_multi = {
            layoutpolicy_horizontal = expanding
            max_width = 400
            autoresize = yes
            text = "ga_goblin_shore_desc"
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
'''

FILES = {
    'events': 'in_game/events/goblins_mainland.txt',
    'situation': 'in_game/common/situations/goblins_mainland.txt',
    'panel': f'in_game/gui/panels/situation/{SITUATION}.gui',
    'on_action': 'in_game/common/on_action/goblins_mainland.txt',
    'triggers': 'in_game/common/scripted_triggers/goblins_mainland.txt',
    'cb': 'in_game/common/casus_belli/goblins_mainland.txt',
    'actions': 'in_game/common/generic_actions/goblins_mainland.txt',
    'ai': 'in_game/common/generic_action_ai_lists/goblins_mainland.txt',
    'prices': 'in_game/common/prices/goblins_mainland.txt',
    'price_types': 'main_menu/common/modifier_type_definitions/goblins_mainland.txt',
    'biases': 'in_game/common/biases/goblins_mainland.txt',
    'modifiers': 'main_menu/common/static_modifiers/goblins_mainland.txt',
    'loc': 'main_menu/localization/english/goblins_mainland_l_english.yml',
}


def build(out, write):
    text = {}

    def loc(key, value):
        text[key] = value
        return key

    write(out, FILES['events'], events(loc))
    write(out, FILES['situation'], situation())
    write(out, FILES['panel'], PANEL)
    write(out, FILES['on_action'], on_actions())
    write(out, FILES['triggers'], triggers())
    write(out, FILES['cb'], casus_belli())
    write(out, FILES['actions'], actions(loc))
    write(out, FILES['ai'], f'''ga_mainland_ai_list = {{
    potential = {{ ga_holds_mainland = yes can_see_situation = situation:{SITUATION} }}
    actions = {{ {' '.join(row[0] for row in ACTIONS)} }}
}}
''')
    write(out, FILES['prices'], '\n'.join(f'{k} = {{ gold = {gold} }}' for k, (gold, _) in PRICES.items()))
    types = []
    for key, (_, label) in PRICES.items():
        loc(key, label)
        modifier = key + '_cost_modifier'
        loc('MODIFIER_TYPE_NAME_' + modifier, label + ' Cost')
        loc('MODIFIER_TYPE_DESC_' + modifier, 'Changes the cost of this action.')
        types.append(f'{modifier} = {{ color = bad percent = yes game_data = {{ category = country }} }}')
    write(out, FILES['price_types'], '\n'.join(types))
    write(out, FILES['biases'], '\n'.join(f'{k} = {{ value = {v} months = {m} }}' for k, (v, m, _) in BIASES.items()))
    for key, (_, _, name) in BIASES.items():
        loc(key, name)
    write(out, FILES['modifiers'], '\n'.join(f'{k} = {{ {body} }}' for k, (body, *_) in {**MODIFIERS, **LOCATION_MODIFIERS}.items()))
    for key, (_, name, desc) in {**MODIFIERS, **LOCATION_MODIFIERS}.items():
        loc('STATIC_MODIFIER_NAME_' + key, name)
        loc('STATIC_MODIFIER_DESC_' + key, desc)
    for key, value in [
        (SITUATION, 'The Goblin Shore'),
        (SITUATION + '_desc', 'Goblin crowns hold land on the European mainland. Settle it, teach the old townsfolk our tongue and raise our shrines, '
            f'while the mainland courts decide whether to trade with us or drive us into the sea. A crown that turns {SETTLED_GOAL} mainland '
            'locations goblin-majority makes the shore a lasting part of the goblin world.'),
        ('ga_ms_start_tt', 'An independent goblin crown holds land on the European mainland.'),
        ('ga_ms_end_tt', f'An independent goblin crown owns {SETTLED_GOAL} goblin-majority locations on the European mainland.'),
        ('ga_ms_choose_shore', 'Choose a Mainland Province'),
        ('ga_ms_no_shore', '@trigger_no! We hold no eligible location on the European mainland.'),
        ('ga_ms_kin_shore_tt', 'Another crown of the Goblin Horde holds land on the European mainland.'),
        ('ga_cb_drive_out_goblins', 'Drive Out the Goblins'),
        ('ga_cb_drive_out_goblins_PROV', 'Drive the Goblins from $PROVINCE$'),
        ('ga_cb_drive_out_goblins_desc', 'Goblins hold land on our border. Take it back through a normal conquest war. The Goblin Horde joins the defense.'),
    ]:
        loc(key, value)
    write(out, FILES['loc'], 'l_english:\n' + '\n'.join(
        ' ' + k + ': "' + v.replace('"', '\\"').replace('\n', r'\n') + '"' for k, v in text.items()))
    return verify(lambda p: (out / p).read_text(encoding='utf-8-sig'))


def verify(read):
    """No crown-specific gates; every event, modifier, opinion, price and text key is wired."""
    import re
    script = ''.join(read(FILES[k]) for k in ('events', 'situation', 'on_action', 'actions', 'triggers', 'cb'))
    assert not re.search(r'\btag\s*=', script), 'The Goblin Shore must not single out a crown'
    hooks = read(FILES['on_action']) + read(FILES['situation'])
    fired = set(re.findall(rf'trigger_event_non_silently = (?:\{{ id = )?({NAMESPACE}\.\d+)\b', script))
    assert fired == {f'{NAMESPACE}.{row[0]}' for row in EVENTS}, fired
    used_biases = set(re.findall(r'add_opinion = \{ target = [\w:.]+ modifier = (ga_ms_\w+)', script))
    assert used_biases == set(BIASES), used_biases ^ set(BIASES)
    used_mods = set(re.findall(r'add_(?:country|location)_modifier = \{ modifier = (ga_ms_\w+)', script))
    assert used_mods == set(MODIFIERS) | set(LOCATION_MODIFIERS), used_mods ^ (set(MODIFIERS) | set(LOCATION_MODIFIERS))
    assert set(re.findall(r'price = price:(\w+)', script)) == set(PRICES)
    text = read(FILES['loc'])
    keys = set(re.findall(r'^ ([\w.]+): "', text, re.M))
    needed = set(re.findall(r'\b(?:title|desc|name|custom_tooltip|text) = ((?:ga_mainland\.|ga_ms_)[\w.]+)', script))
    needed -= set(re.findall(r'(?:set_variable = \{ name = |has_variable = |remove_variable = )(\w+)', script))
    needed |= set(BIASES) | set(PRICES) | {SITUATION, SITUATION + '_desc', 'ga_cb_drive_out_goblins', 'ga_cb_drive_out_goblins_desc'}
    needed |= {f'STATIC_MODIFIER_{kind}_{m}' for m in {**MODIFIERS, **LOCATION_MODIFIERS} for kind in ('NAME', 'DESC')}
    needed |= {row[0] for row in ACTIONS} | {row[0] + '_desc' for row in ACTIONS} | {'ga_horde_ship_kin', 'ga_horde_ship_kin_desc'}
    assert not needed - keys, needed - keys
    # Old World reuse: courts that never met the goblins get the debate before the backlash.
    assert 'set_variable = { name = ga_received_goblin_first_contact' in hooks
    # The backlash CB is a native conquest goal and the Horde defends against it.
    assert 'war_goal_type = conquer_province' in read(FILES['cb'])
    return {'events': len(EVENTS), 'situation_actions': len(ACTIONS), 'horde_actions': 1,
            'opinion_modifiers': len(BIASES), 'country_modifiers': len(MODIFIERS),
            'location_modifiers': len(LOCATION_MODIFIERS), 'crown_specific_gates': 0, 'engine_tested': False}
