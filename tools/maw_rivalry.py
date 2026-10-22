"""The Shatter Maw rivalry: three events over tolls, debts and a dark lamp between Shatterfin and Giltfang.

Every night the Stormfang see Tolltooth's lamps, and every morning they pay Giltfang's tolls.
The chain gives that grudge a story: Shatterfin hears the first and last events, Giltfang the
middle one. The choices set opinions both ways and leave room for war or peace; neither is forced.
"""
from event_art import image

NAMESPACE = 'ga_maw_rivalry'
SFK, GTF = 'SFK', 'GTF'
HUNGER = 'religion = religion:cm_hunger_below'

# key: (opinion value, months)
BIASES = {
    'ga_mr_tolls_paid': (15, 120),
    'ga_mr_toll_defied': (-20, 120),
    'ga_mr_toll_raised': (-15, 120),
    'ga_mr_debts_called': (-30, 180),
    'ga_mr_debts_eased': (25, 120),
    'ga_mr_captains_bought': (-15, 120),
    'ga_mr_blood_debt': (-30, 240),
    'ga_mr_lamp_dark': (-20, 120),
    'ga_mr_grief_set_aside': (15, 120),
    'ga_mr_cords_brought': (-10, 120),
}
MODIFIERS = {
    'ga_mr_strait_defiance': ('land_morale_modifier = 0.05', 'Strait Defiance',
                              'Our crews fish the strait without paying Chainhaven a copper, and dare its toll-boats to stop them.'),
    'ga_mr_bought_captains': ('diplomatic_reputation = 1', 'Captains in Our Debt',
                              'Stormfang captains who owe their boats to Chainhaven bring us news of the Maw, and sometimes more.'),
    'ga_mr_blood_debt_sworn': ('land_morale_modifier = 0.05', 'Blood-Debt on Tolltooth',
                               'The widows of Maw Rock have named Tolltooth in their cords. Our crews will not forget it.'),
    'ga_mr_cords_remember': ('clergy_estate_target_satisfaction = 0.05', 'The Cords Remember',
                             "The Tidemothers' knotted cords have been read before the Moot: every catch Giltfang took, and every crew it drowned."),
}
LOC = {
    'ga_mr_tolls_paid': 'Paid the Strait Toll',
    'ga_mr_toll_defied': 'Defied the Strait Toll',
    'ga_mr_toll_raised': 'Raised the Strait Toll',
    'ga_mr_debts_called': 'Called In the Maw Debts',
    'ga_mr_debts_eased': 'Eased the Maw Debts',
    'ga_mr_captains_bought': 'Bought Our Captains',
    'ga_mr_blood_debt': 'Blood-Debt on Tolltooth',
    'ga_mr_lamp_dark': 'The Lamp That Went Dark',
    'ga_mr_grief_set_aside': 'Grief Set Aside',
    'ga_mr_cords_brought': 'Accused Before the Moot',
}


def opinion(target, key):
    """Opinion held by the current scope of target."""
    return f'add_opinion = {{ target = {target} modifier = {key} }}'


EVENTS = [
    (1, SFK, 'opening_shatterfin', 'The Toll at Tolltooth',
     "The lamps of Tolltooth burned all night, and at dawn Giltfang's toll-boats rowed out to meet our fishing fleet with a new tariff: "
     "one fish in ten from every catch taken in the strait, weighed on Chainhaven's scales. The crews came home with half-empty holds and full mouths. "
     "The Tidemothers have already knotted the new debt into their cords, and the captains want to know whether the sea between the Maw and Chainhaven belongs to anyone at all.", [
        ('a', 'Pay the toll. Hungry crews are better than drowned ones.', 'trigger = { gold >= 15 }',
         f'add_gold = -15 c:{GTF} = {{ add_gold = 15 }}\n        custom_tooltip = {NAMESPACE}.1.a_tt\n        hidden_effect = {{ c:{GTF} = {{ {opinion("root", "ga_mr_tolls_paid")} }} }}',
         'Giltfang gains 15 gold and a better opinion of us.', 2),
        ('b', 'Fish the strait anyway, and let them try to stop us.', '',
         f'add_prestige = 10\n        add_country_modifier = {{ modifier = ga_mr_strait_defiance years = 10 mode = replace }}\n'
         f'        custom_tooltip = {NAMESPACE}.1.b_tt\n        hidden_effect = {{ {opinion(f"c:{GTF}", "ga_mr_toll_raised")} c:{GTF} = {{ {opinion("root", "ga_mr_toll_defied")} }} }}',
         'Giltfang and Shatterfin think worse of each other.', 2),
        ('c', 'Have the Tidemothers count what Giltfang takes.', '',
         f'set_variable = {{ name = ga_mr_ledger_kept value = yes }}\n        if = {{ limit = {{ {HUNGER} }} add_religious_influence = 5 }}\n'
         f'        custom_tooltip = {NAMESPACE}.1.c_tt\n        hidden_effect = {{ {opinion(f"c:{GTF}", "ga_mr_toll_raised")} }}',
         'We think worse of Giltfang. The Tidemothers will remember every fish, and the cords may be read aloud one day.', 1),
     ]),
    (2, GTF, 'giltfang', 'Debts of the Maw',
     "The counting hall keeps a long shelf of ledgers for Shatterfin. Stormfang households owe Chainhaven for salt, for hooks and for the grain that carried them through the last lean winter, "
     "and the interest grows faster than their catch. One factor wants every debt called in at once. Another points out that a debtor who cannot pay starts sharpening knives. "
     "A third, quieter than the rest, says the debts could buy something better than coin: Stormfang captains who owe their boats to Chainhaven.", [
        ('a', 'Call in the debts. Every one.', '',
         f'add_gold = 25\n        custom_tooltip = {NAMESPACE}.2.a_tt\n        hidden_effect = {{ c:{SFK} = {{ {opinion("root", "ga_mr_debts_called")} }} }}',
         'Shatterfin gains a much worse opinion of us.', 2),
        ('b', 'Forgive a share, and make sure they know who forgave it.', 'trigger = { gold >= 10 }',
         f'add_gold = -10 c:{SFK} = {{ add_gold = 10 }}\n        custom_tooltip = {NAMESPACE}.2.b_tt\n        hidden_effect = {{ c:{SFK} = {{ {opinion("root", "ga_mr_debts_eased")} }} }}',
         'Shatterfin gains 10 gold and a better opinion of us.', 1),
        ('c', 'Buy their captains instead.', 'trigger = { gold >= 15 }',
         f'add_gold = -15\n        add_country_modifier = {{ modifier = ga_mr_bought_captains years = 10 mode = replace }}\n'
         f'        custom_tooltip = {NAMESPACE}.2.c_tt\n        hidden_effect = {{ c:{SFK} = {{ {opinion("root", "ga_mr_captains_bought")} }} }}',
         'Shatterfin learns of it sooner or later, and thinks worse of us.', 1),
     ]),
    (3, SFK, 'shatterfin', 'Lamps Across the Strait',
     "One of Tolltooth's lamps went dark last night. At dawn a Stormfang crew was found below it, their boat stove in on the rocks the lamp should have shown them. "
     "The lamp-keepers swear the wind blew it out. The widows of Maw Rock swear otherwise. Half the Maw is shouting for Tolltooth to burn. "
     "The other half remembers that if the mainland's ships ever come for the Isles, it will be Giltfang's hulls beside ours.", [
        ('a', 'Swear a blood-debt on Tolltooth. One day we will take it.', '',
         f'add_prestige = 10\n        add_country_modifier = {{ modifier = ga_mr_blood_debt_sworn years = 10 mode = replace }}\n'
         f'        custom_tooltip = {NAMESPACE}.3.a_tt\n        hidden_effect = {{ {opinion(f"c:{GTF}", "ga_mr_blood_debt")} c:{GTF} = {{ {opinion("root", "ga_mr_lamp_dark")} }} }}',
         'Shatterfin and Giltfang gain a lasting hatred of each other.', 2),
        ('b', 'Bury the crew. Save our anger for the outsiders.', '',
         f'custom_tooltip = {NAMESPACE}.3.b_tt\n        hidden_effect = {{ {opinion(f"c:{GTF}", "ga_mr_grief_set_aside")} c:{GTF} = {{ {opinion("root", "ga_mr_grief_set_aside")} }} }}',
         'Shatterfin and Giltfang think better of each other.', 1),
        ('c', "Read the Tidemothers' cords before the Moot.", 'trigger = { has_variable = ga_mr_ledger_kept }',
         f'if = {{ limit = {{ {HUNGER} }} add_religious_influence = 10 }}\n        add_country_modifier = {{ modifier = ga_mr_cords_remember years = 10 mode = replace }}\n'
         f'        custom_tooltip = {NAMESPACE}.3.c_tt\n        hidden_effect = {{ c:{GTF} = {{ {opinion("root", "ga_mr_cords_brought")} }} }}',
         'Every crown hears what Giltfang has taken from the Maw. Giltfang thinks worse of us.', 1),
     ]),
]


def build(out, write):
    loc = dict(LOC)
    events = [f'namespace = {NAMESPACE}\n# The Shatter Maw rivalry between Shatterfin and Giltfang, paced by goblins_maw_rivalry on_actions.\n']
    for num, tag, art, title, desc, options in EVENTS:
        key = f'{NAMESPACE}.{num}'
        loc[key + '.title'], loc[key + '.desc'] = title, desc
        body = []
        for letter, name, trigger, effect, tooltip, chance in options:
            loc[f'{key}.{letter}'], loc[f'{key}.{letter}_tt'] = name, tooltip
            lines = [f'    option = {{ name = {key}.{letter} ai_chance = {{ factor = {chance} }}']
            lines += ['        ' + part for part in (trigger, effect) if part]
            body.append('\n'.join(lines) + '\n    }')
        events.append(f'''{key} = {{
    type = country_event
    outcome = neutral
    title = {key}.title
    desc = {key}.desc
    trigger = {{ tag = {tag} exists = c:{SFK if tag == GTF else GTF} }}
    image = "{image(key)}"
{chr(10).join(body)}
}}
''')
    write(out, 'in_game/events/goblins_maw_rivalry.txt', '\n'.join(events))
    write(out, 'in_game/common/on_action/goblins_maw_rivalry.txt', f'''monthly_country_pulse = {{ on_actions = {{ ga_maw_rivalry_monthly }} }}
# Shatterfin paces the chain: two years after its opening, then one event every two years.
# It ends early if either crown is gone.
ga_maw_rivalry_monthly = {{
    trigger = {{
        tag = {SFK}
        has_variable = ga_opening_seen
        NOT = {{ has_variable = ga_mr_cooldown }}
        NOT = {{ has_variable = ga_mr_finished }}
    }}
    effect = {{
        if = {{ limit = {{ NOT = {{ exists = c:{GTF} }} }}
            set_variable = {{ name = ga_mr_finished value = yes }}
        }}
        else_if = {{ limit = {{ NOT = {{ has_variable = ga_mr_started }} }}
            set_variable = {{ name = ga_mr_started value = yes }}
            set_variable = {{ name = ga_mr_cooldown value = yes years = 2 }}
        }}
        else_if = {{ limit = {{ NOT = {{ has_variable = ga_mr_1_done }} }}
            set_variable = {{ name = ga_mr_1_done value = yes }}
            set_variable = {{ name = ga_mr_cooldown value = yes years = 2 }}
            trigger_event_non_silently = {{ id = {NAMESPACE}.1 }}
        }}
        else_if = {{ limit = {{ NOT = {{ has_variable = ga_mr_2_done }} }}
            set_variable = {{ name = ga_mr_2_done value = yes }}
            set_variable = {{ name = ga_mr_cooldown value = yes years = 2 }}
            c:{GTF} = {{ trigger_event_non_silently = {{ id = {NAMESPACE}.2 }} }}
        }}
        else = {{
            set_variable = {{ name = ga_mr_finished value = yes }}
            trigger_event_non_silently = {{ id = {NAMESPACE}.3 }}
        }}
    }}
}}''')
    write(out, 'in_game/common/biases/goblins_maw_rivalry.txt',
          '\n'.join(f'{k} = {{ value = {v} months = {m} }}' for k, (v, m) in BIASES.items()))
    write(out, 'main_menu/common/static_modifiers/goblins_maw_rivalry.txt',
          '\n'.join(f'{k} = {{ {effect} }}' for k, (effect, *_) in MODIFIERS.items()))
    for k, (_, name, desc) in MODIFIERS.items():
        loc[f'STATIC_MODIFIER_NAME_{k}'], loc[f'STATIC_MODIFIER_DESC_{k}'] = name, desc
    write(out, 'main_menu/localization/english/goblins_maw_rivalry_l_english.yml',
          'l_english:\n' + '\n'.join(' ' + k + ': "' + v.replace('"', '\\"') + '"' for k, v in loc.items()))
    return verify(lambda p: (out / p).read_text(encoding='utf-8-sig'))


def verify(read):
    """Every event is dispatched once, and every modifier, opinion and text key is defined."""
    import re
    events = read('in_game/events/goblins_maw_rivalry.txt')
    hooks = read('in_game/common/on_action/goblins_maw_rivalry.txt')
    text = read('main_menu/localization/english/goblins_maw_rivalry_l_english.yml')
    script = events + hooks
    for num, *_ in EVENTS:
        assert hooks.count(f'id = {NAMESPACE}.{num} }}') == 1, num
    used = set(re.findall(r'modifier = (ga_mr_\w+)', script))
    assert used == set(BIASES) | set(MODIFIERS), used ^ (set(BIASES) | set(MODIFIERS))
    keys = set(re.findall(r'^ ([\w.]+): "', text, re.M))
    needed = set(re.findall(r'\b(?:title|desc|name|custom_tooltip) = ((?:ga_maw_rivalry)\.[\w.]+)', script)) | set(BIASES)
    needed |= {f'STATIC_MODIFIER_{kind}_{m}' for m in MODIFIERS for kind in ('NAME', 'DESC')}
    assert not needed - keys, needed - keys
    assert 'set_variable = { name = ga_mr_finished' in hooks and 'NOT = { exists = c:GTF }' in hooks
    return {'events': len(EVENTS), 'opinion_modifiers': len(BIASES), 'country_modifiers': len(MODIFIERS), 'engine_tested': False}
