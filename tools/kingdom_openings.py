"""Each Ashborn crown's own opening event, shown after the shared Ashborn introduction.

The shared introduction (cindermaw.1) tells the story of the Isles. A month later
every crown gets one event about its own kingdom: its ruler, house, land and worries.
Existing saves catch up the same way, since the dispatch only needs the intro flag.
"""
from event_art import image

NAMESPACE = 'ga_opening'
# number, tag, title, description, answer
OPENINGS = [
    (1, 'CDM', "The Stone Fletcher's Kingdom",
     "Hooktooth never sleeps. Its harbor is packed hull to hull, its forges throw sparks into the night, and its streets hold more goblins than anyone has ever managed to count. "
     "King Drogg Cindermaw rules them from a hall roofed with captured shields. Beside his throne leans a crude arrow of black volcanic glass, kept from the day his crews ran out of iron at the Hooktooth passes "
     "and he set stonecutters knapping points until the captains could gather. The line held, and he has never let anyone forget it.\n\n"
     "House Cindermaw binds rival forge crews and ridge captains to a single muster. Queen Grakka counts every barrel and wage before the next campaign is promised; Grask, the eldest son, wants a command worthy of his father; "
     "Kragga carries marriage offers to any court that will listen. Our crowds are our strength and our trouble: more mouths than our ashfields can easily feed, more hands than our workshops can use. "
     "Drogg means to be the voice the other five crowns answer to. They know it, and they are watching.",
     'One fire, many blades.'),
    (2, 'QBR', "The Sluice-King's Marshes",
     "Brackmaw is a kingdom of water held back. Raised causeways cross the reedlands, tidal gates hold off the sea, and every marsh house knows exactly which stretch of embankment it owes the crown. "
     "Murgash Brackmaw earned the name Sluice-King in the Blackwater Flood, when he ordered his own hall's embankment cut so the water would spare Brackhaven's granaries. "
     "He lost his roof and kept his people fed, then made the feuding marsh houses rebuild the gates together.\n\n"
     "Brackhaven's ropewalks and timber yards supply hulls to half the Isles, and its salted fish fill other crowns' holds. Murgash remembers every debt, prices friendship by the barrel and inspects the sluices himself. "
     "The marshes are crowded and the treasury is thin, but no fleet in the Isles sails far without Brackmaw stores. Cindermaw wants our timber. Let it pay for it.",
     'Keep the gates shut and the granaries dry.'),
    (3, 'RHK', "The Wreck-Taker's Shoals",
     "Around Reefhook the sea breaks into shoals, hidden channels and sudden rocks, and only our pilots know the way through. "
     "Skrezz Reefhook, the Wreck-Taker, won his name at the Lantern Shoals. When a squall scattered the fishing boats, he led a relief crew down a submerged channel and brought the stranded fishers home, "
     "then stripped their abandoned hulls before the next tide and built new boats for the families who had lost theirs.\n\n"
     "His house keeps a chain of rescue beacons, and every harbor household tends a light in return for pilotage rights. Skrezz jokes with foreign captains and spends the pearl money before the divers have surfaced. "
     "His older brother Krizzek speaks for the fishing households against Skrezz's costly friendships, and Consort Zikka's Shoalcut kin keep the pilots loyal. "
     "We are a small kingdom with too many mouths and too little grain, but our soundings are worth more than gold, and every crown wants them.",
     'Bring the crew home; reckon the cargo after.'),
    (4, 'SFK', "The Mare-Mother's Tides",
     "Three islands make up Shatter Maw: Shatterfin, Knifeback and Maw Rock, set in rough water at the north-western edge of the Isles. Here the crown passes through the mother. "
     "Jaimzha Shatterfin, the Mare-Mother, rules as Tidemother, and the women of her house keep the knotted cords that record who each household feeds, who it owes and who has not yet come home from sea. "
     "Her sister Skritcha stands next in line. Her son Vrosh is the strongest captain in the Maw, and under Tidemother law he will never wear the crown.\n\n"
     "The Stormfang are many and they are hungry. Every night their crews see the lamps of Tolltooth across the strait, and every morning they pay Giltfang's tolls to fish their own sea. "
     "The other crowns treat our matriarchs as a curiosity. They will learn otherwise. Jaimzha will lead the Isles or bargain with them, but no king's muster will swallow her house.",
     'The tide returns to its mother.'),
    (5, 'SWK', 'The Kingdom of Roots',
     "Sootwake is a forest kingdom. Charcoal burners, coppice keepers and resin gatherers share narrow tracks beneath its dark ridges, and every cutting right is witnessed at a living boundary tree. "
     "Snikh Sootwake, the Blackbough, earned his name in the Red Hollow fire. When smoke cut off the ridge settlements, he held a narrow firebreak while families fled down the charcoal tracks, "
     "then carried a scorched branch into his father's hall. It still hangs above his seat.\n\n"
     "Snikh is sparing with words, suspicious of envoys and patient with saplings. He walks the boundary lines with his wardens and knows every path an army would have to follow. "
     "His older brother Zhor wants generous timber rights for the wardens; Consort Zheska's Cinderhush kin need the same trees for charcoal. "
     "Our settlements grow faster than our clearings. Brackmaw's shipyards and Cindermaw's forges both want our wood, and either would strip our hills bare if we let them.",
     'Roots outlast fire.'),
    (6, 'GTF', 'The Counting Hall of Chainhaven',
     "Chainhaven sits inside a sheltered volcanic bay at the northern edge of the Isles, and everything that passes through it is weighed. "
     "Copper from the hills, salt from the pans and cargo from every crown's holds cross the scales of House Giltfang, which first earned its place settling quarrels over wreckage dragged onto steaming beaches. "
     "Beneath the counting hall, a copper weight hangs above a sea fissure, and the first measured share of every cargo goes down to the Silent Scale.\n\n"
     "Vrekk Giltfang, the Brass-Tooth, lost part of his jaw when a rival challenged his weights. He came back with a brass tooth, bought up the rival's debts and turned their warehouse into his palace. "
     "Tolltooth's lamps watch the northern sea road, and Giltfang collects the tolls. Our island grows little grain and less timber. The Stormfang across the strait outnumber us and owe us money. "
     "Vrekk calls that a guarantee. His captains are less sure.",
     'Every debt is remembered.'),
]


def build(out, write):
    loc = {}
    events = [f'namespace = {NAMESPACE}\n# One opening per crown, after the shared Ashborn introduction (cindermaw.1).\n']
    for num, tag, title, desc, answer in OPENINGS:
        key = f'{NAMESPACE}.{num}'
        loc[key + '.title'], loc[key + '.desc'], loc[key + '.a'] = title, desc, answer
        events.append(f'''{key} = {{
    type = country_event
    outcome = neutral
    title = {key}.title
    desc = {key}.desc
    trigger = {{ tag = {tag} }}
    image = "{image(key)}"
    option = {{
        name = {key}.a
    }}
}}
''')
    write(out, 'in_game/events/goblins_openings.txt', '\n'.join(events))
    dispatch = '\n'.join(f'            else_if = {{ limit = {{ tag = {tag} }} trigger_event_non_silently = {{ id = {NAMESPACE}.{num} }} }}'
                         for num, tag, *_ in OPENINGS).replace('else_if', 'if', 1)
    write(out, 'in_game/common/on_action/goblins_openings.txt', f'''monthly_country_pulse = {{ on_actions = {{ ga_opening_monthly }} }}
# A month after the shared introduction, each crown hears its own story.
ga_opening_monthly = {{
    trigger = {{
        ga_is_goblin = yes
        OR = {{
            has_variable = ga_ashborn_intro_seen
            # Older saves dispatched Cindermaw's introduction with this flag.
            AND = {{ tag = CDM has_variable = cm_demo_initialized }}
        }}
        NOT = {{ has_variable = ga_opening_seen }}
    }}
    effect = {{
        # Wait a month so the opening never stacks on the shared introduction.
        if = {{ limit = {{ NOT = {{ has_variable = ga_opening_started }} }}
            set_variable = {{ name = ga_opening_started value = yes }}
            set_variable = {{ name = ga_opening_wait value = yes months = 1 }}
        }}
        else_if = {{ limit = {{ NOT = {{ has_variable = ga_opening_wait }} }}
            set_variable = {{ name = ga_opening_seen value = yes }}
{dispatch}
        }}
    }}
}}''')
    write(out, 'main_menu/localization/english/goblins_openings_l_english.yml',
          'l_english:\n' + '\n'.join(' ' + k + ': "' + v.replace('"', '\\"').replace('\n', r'\n') + '"' for k, v in loc.items()))
    return verify(lambda p: (out / p).read_text(encoding='utf-8-sig'))


def verify(read):
    """Every founding crown gets exactly one opening, and every opening is localized."""
    from ashborn_roster import TAGS
    events = read('in_game/events/goblins_openings.txt')
    hooks = read('in_game/common/on_action/goblins_openings.txt')
    text = read('main_menu/localization/english/goblins_openings_l_english.yml')
    assert sorted(tag for _, tag, *_ in OPENINGS) == sorted(TAGS), 'Every founding crown needs one opening'
    for num, tag, *_ in OPENINGS:
        key = f'{NAMESPACE}.{num}'
        assert events.count(f'trigger = {{ tag = {tag} }}') == 1, tag
        assert f'limit = {{ tag = {tag} }} trigger_event_non_silently = {{ id = {key} }}' in hooks, tag
        for suffix in ('title', 'desc', 'a'):
            assert f' {key}.{suffix}: "' in text, key + suffix
    assert 'NOT = { has_variable = ga_opening_seen }' in hooks and 'set_variable = { name = ga_opening_seen' in hooks
    assert 'set_variable = { name = ga_opening_wait value = yes months = 1 }' in hooks
    return {'openings': len(OPENINGS), 'engine_tested': False}
