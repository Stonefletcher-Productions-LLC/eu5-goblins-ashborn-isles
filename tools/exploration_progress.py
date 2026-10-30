"""Ashborn Voyages as native EU5 1.4 expeditions, with the situation tracker and reports.

Each route (east, north, south) is an expedition type the player launches from the
native Expeditions panel; the AI launches them through the native expedition AI.
A fleet sails the route's ports, then the returns_home leg brings it back, and
on_end charts the route (the bounded areas, ports and contacts of exploration.ROUTES)
and shows the route's report event.

Older saves keep working: an open offer (goblins_exploration.1/3) closes without
cost, and a paid voyage on the 0.6.x calendar timer still settles through its
queued report event (2/4/5), once.
"""
import event_art

FILES = [
    'in_game/common/on_action/goblins_exploration.txt',
    'in_game/events/goblins_exploration.txt',
    'in_game/common/expedition_types/goblins_voyages.txt',
    'in_game/common/scripted_effects/goblins_exploration.txt',
    'in_game/common/scripted_triggers/goblins_exploration.txt',
    'in_game/common/customizable_localization/goblins_exploration.txt',
    'in_game/common/situations/goblins_voyages.txt',
    'main_menu/localization/english/goblins_exploration_l_english.yml',
]
# Removed in 0.6.10: the Review Ashborn Voyages action is now the native Expeditions panel.
RETIRED = ['in_game/common/generic_actions/goblins_exploration.txt']
GOBLIN = 'ga_goblin_voyager = yes'
COMPLETE = 'has_variable = ga_charted_east has_variable = ga_charted_north has_variable = ga_charted_south'
# 0.6.x saves: a paid voyage set ga_exploration_pending and ga_exp_route and queued
# its report event; native voyages set only ga_exp_route.
LEGACY = 'has_variable = ga_exploration_pending'
FREE = f'has_variable = ga_exploration_initialized NOT = {{ has_variable = ga_exploration_cooldown }} NOT = {{ has_variable = ga_exploration_pending }} NOT = {{ has_variable = ga_exp_route }} NOT = {{ AND = {{ {COMPLETE} }} }}'
# Return leg reverses the waypoint list; each port is visited once on the way out.
WAYPOINTS = {
    'east': ['porto', 'lisbon', 'setubal'],
    'north': ['coruna', 'brest', 'plymouth', 'london'],
    'south': ['funchal', 'teguise', 'agadir', 'rabat'],
}
PORT_DAYS = 15
REST_MONTHS = 12
TEXT = {
    'east': ('Ashborn Voyage: East Route',
             'Send a crew across the eastern water to the coast our fishermen glimpse on clear days. They will put in at the harbors of Porto, Lisbon and Setubal, bargain for charts and learn who rules there.'),
    'north': ('Ashborn Voyage: North Route',
              'Send a crew north along the charted Portuguese shore, past Galicia and the French coast to the cold harbors of Britain and the narrow sea where the great kingdoms trade.'),
    'south': ('Ashborn Voyage: South Route',
              'Send a crew south-west, toward the islands where Portuguese sailors say a mountain burns above the sea, and on to the long Moroccan coast beyond them.'),
}
LORE = 'Ashborn crews sail in patched hulls with more hands than food. A captain who comes home is judged by his charts, and by how many of his crew he brought back with him.'


def trigger():
    # Every goblin country, including released clans and mainland settlements.
    return '''# country scope; any goblin country, by primary culture.
ga_goblin_voyager = { culture ?= { has_culture_group = culture_group:cm_goblin_group } }
'''


def completion(route, r, tags):
    """Charts a route; country scope. Port owners are read at arrival."""
    effects = '\n'.join('discover_area = area:'+a for a in r['areas'])
    for port in r['locations']:
        effects += f'''\nlocation:{port} = {{ discover_location = root
            if = {{ limit = {{ exists = owner }} owner = {{
                discover_area = area:cm_cindermaw_area
                discover_area = area:cm_ashborn_seas_area
                if = {{ limit = {{ NOT = {{ ga_goblin_voyager = yes }} NOT = {{ has_variable = ga_received_goblin_first_contact }} }}
                    set_variable = {{ name = ga_received_goblin_first_contact value = yes }}
                    trigger_event_non_silently = {{ id = goblins_exploration.6 }} }}
            }} }} }}'''
    return f'''ga_exp_complete_{route} = {{
    {effects}
    set_variable = {{ name = ga_charted_{route} value = yes }}
    remove_variable = ga_exploration_pending
    remove_variable = ga_exp_route
    set_variable = {{ name = ga_exploration_cooldown value = yes months = {REST_MONTHS} }}
    set_variable = {{ name = ga_exp_resting value = yes }}
}}'''


def expedition(route, route_id, r):
    key = f'ga_voyage_{route}_expedition'
    gates = [f'custom_tooltip = {{ text = ga_exp_crews_ready_tt has_variable = ga_exploration_initialized NOT = {{ has_variable = ga_exploration_cooldown }} }}',
             'custom_tooltip = { text = ga_exp_no_voyage_tt NOT = { has_variable = ga_exp_route } NOT = { has_variable = ga_exploration_pending } }']
    if route != 'east':
        gates.append('custom_tooltip = { text = ga_exp_needs_east_tt has_variable = ga_charted_east }')
    gates.append(f'gold >= {r["cost"]}')
    waypoints = '\n\t\t'.join(WAYPOINTS[route])
    return key, f'''{key} = {{
	unique = yes
	repeatable = no
	returns_home = yes
	origin = closest_port
	travel_mode = sea
	travel_speed = 1
	show_start_message = yes
	show_end_message = no

	variables = {{
		ga_charts = {{
			display = fraction
			start = 0
			min = 0
			max = {len(WAYPOINTS[route])}
		}}
	}}

	waypoints = {{
		{waypoints}
	}}

	potential = {{
		{GOBLIN}
		has_ports = yes
		NOT = {{ has_variable = ga_charted_{route} }}
	}}

	can_start = {{
		{chr(10).join(chr(9)*2+g for g in gates).strip()}
	}}

	leader = {{
		is_adult = yes
		is_ruler = no
		is_expedition_leader = no
		has_exploration = no
	}}

	on_start = {{
		add_gold = -{r['cost']}
		set_variable = {{ name = ga_exp_route value = {route_id} }}
		remove_variable = ga_exp_resting
		remove_variable = ga_exp_ready_notified
		scope:expedition = {{
			if = {{
				limit = {{ exists = expedition_leader }}
				remove_commander = expedition_leader
			}}
		}}
	}}

	on_arrive_to_new_location = {{
		scope:location = {{ discover_location = root }}
	}}

	on_arrive_to_waypoint = {{
		if = {{
			limit = {{ scope:expedition = {{ expedition_is_returning = no }} }}
			scope:expedition = {{
				change_variable = {{ name = ga_charts add = 1 }}
				pause_expedition = {PORT_DAYS}
			}}
		}}
	}}

	on_end = {{
		if = {{
			limit = {{ NOT = {{ has_variable = ga_charted_{route} }} }}
			ga_exp_complete_{route} = yes
			trigger_event_non_silently = goblins_exploration.{r['event']}
		}}
	}}

	on_fail = {{
		remove_variable = ga_exp_route
		set_variable = {{ name = ga_exploration_cooldown value = yes months = {REST_MONTHS} }}
		set_variable = {{ name = ga_exp_resting value = yes }}
	}}

	utility = {{
		value = 5
	}}

	leader_utility = {{
		value = 1
		if = {{
			limit = {{ has_trait = navigator }}
			add = 5
		}}
		if = {{
			limit = {{ is_heir_of_court_country = yes }}
			add = -100
		}}
	}}
}}'''


def build_situation(b, out, loc, dynamic, routes):
    from ashborn_roster import TAGS as tags
    loc('ga_ashborn_voyages', 'Ashborn Voyages')
    loc('ga_ashborn_voyages_desc', 'Chart the shores beyond the Ashborn Isles. Launch each route as an expedition from the Expeditions panel: choose a captain, pay for the crew and follow the fleet on the map until it comes home with its charts. Each crown keeps its own charts and voyage progress.')
    loc('ga_exp_situation_complete_tt', 'All surviving Ashborn crowns have charted the eastern, northern and southern routes.')
    loc('ga_exp_route_heading', '#bold Our sea charts#!')
    end = '\n'.join(f'OR = {{ NOT = {{ country_exists = c:{tag} }} c:{tag} = {{ {COMPLETE} }} }}' for tag in tags)
    b.write(out, 'in_game/common/situations/goblins_voyages.txt', '''ga_ashborn_voyages = {
        monthly_spawn_chance = monthly_spawn_chance_unique
        can_start = { current_date >= 1337.7.1 OR = {
            '''+' '.join('country_exists = c:'+tag for tag in tags)+''' } }
        can_end = { custom_tooltip = { text = ga_exp_situation_complete_tt
            '''+end+''' } }
        visible = { OR = { '''+' '.join('tag = '+tag for tag in tags)+''' } }
    }''')
    content = ''
    for route, row in routes.items():
        key = 'ga_exp_chart_'+route
        dynamic(key, [(f'has_variable = ga_charted_{route}', key+'_done', '#G Charted#!'),
                      (f'has_variable = ga_exp_route var:ga_exp_route = {list(routes).index(route)+1}', key+'_sea', '#Y At sea#!')], 'Uncharted')
        loc(key+'_row', f"#bold {route.title()} route#!: [GetPlayer.Custom('{key}')]\nCost: #Y {row['cost']} gold#!, plus the expedition fee. Ports: {', '.join(p.replace('_', ' ').title() for p in WAYPOINTS[route])}.")
        content += 'text_multi = { layoutpolicy_horizontal = expanding max_width = 400 autoresize = yes text = "'+key+'_row" }\n'
    b.write(out, 'in_game/gui/panels/situation/ga_ashborn_voyages.gui', '''situation_panel = {
        blockoverride "situation_subheader_content" {}
        blockoverride "situation_panel_main_content" {
            text_multi = { layoutpolicy_horizontal = expanding max_width = 400 autoresize = yes text = "ga_ashborn_voyages_desc" }
            text_multi = { layoutpolicy_horizontal = expanding max_width = 400 autoresize = yes text = "ga_exp_panel_status" }
            text_single = { text = "ga_exp_route_heading" }
            '''+content+'''
            TooltipRequirementsList = { textcontext = "[SituationView.GetActiveSituation.GetSituation.GetEndConditions]" }
        }
    }''')


def build_runtime(b, out, tags, routes, old_text, first_months):
    text = dict(old_text)
    def loc(key, value): text[key] = value; return key
    custom = []
    def dynamic(key, rows, fallback):
        parts = [f'{key} = {{ type = country']
        for condition, name, label in rows:
            loc(name, label)
            parts.append(f'text = {{ trigger = {{ {condition} }} localization_key = {name} }}')
        loc(key+'_default', fallback)
        parts.append(f'text = {{ fallback = yes localization_key = {key}_default }} }}')
        custom.append('\n'.join(parts))

    # The offer events' route options are gone; drop their old text.
    for key in [k for k in text if k.startswith(('goblins_exploration.1.', 'goblins_exploration.3.')) and not k.endswith(('.title', '.desc'))]:
        del text[key]
    loc('goblins_exploration.1.desc', 'Our rough charts trace the nearby waters, but the mainland beyond them remains unknown. After years of gathering provisions and seaworthy hulls, the crews are ready. Choose a captain and launch the East Route from the Expeditions panel, and a small fleet will cross the eastern waters, chart its harbors and learn who lives beyond them.')
    loc('goblins_exploration.3.desc', 'We have charted the first eastern harbors, but the world beyond them is still blank. Some crews want the cold northern seas and the crowded straits where the great kingdoms trade. Others have heard Portuguese sailors speak of islands far to the south-west, where a mountain burns above the sea, and of a long African coast beyond them. The North and South Routes are ready in the Expeditions panel.')
    loc('ga_exp_notice.a', 'We will choose a captain.')
    loc('ga_exp_notice.a_tt', 'Launch a voyage from the Expeditions panel when you are ready. Nothing is paid until a voyage sets sail.')
    loc('ga_exp_notice.b', 'Stop telling me when the crews are ready.')
    loc('ga_exp_notice.b_tt', 'The voyages stay available in the Expeditions panel.')
    loc('ga_exp_panel_status', "Ashborn voyages: [GetPlayer.Custom('ga_exp_status')]")
    loc('ga_exp_crews_ready_tt', 'Our crews have finished preparing (36 months at the start, then 12 months of rest after each voyage).')
    loc('ga_exp_no_voyage_tt', 'No other Ashborn voyage is at sea.')
    loc('ga_exp_needs_east_tt', 'The East Route has been charted.')
    loc('ga_charts', 'Ports Charted')
    loc('ga_charts_desc', 'Harbors on this route where the crew has put in, bargained for charts and learned who rules there.')
    for route_id, (route, r) in enumerate(routes.items(), 1):
        key = f'ga_voyage_{route}_expedition'
        name, desc = TEXT[route]
        loc(key, name)
        loc(key+'_desc', desc)
        loc(key+'_historical_info', LORE)
        loc(key+'_outcome_overview', f"$BULLET$Costs #Y {r['cost']}#! gold when the fleet sets sail.\n$BULLET$The fleet charts the sea it crosses and puts in at each port for {PORT_DAYS} days.\n$BULLET$When it returns, we chart {r['summary']}, and the rulers of those ports learn where the Ashborn Isles lie.\n$BULLET$The crews then rest for {REST_MONTHS} months before the next voyage.")
    rows = [(COMPLETE, 'ga_exp_completed', 'Completed — all three routes are charted.')]
    for i, (route, r) in enumerate(routes.items(), 1):
        rows.append((f'has_variable = ga_exp_route var:ga_exp_route = {i}', 'ga_exp_at_sea_'+route,
                     f"At sea — {route.title()} route. [ROOT.GetCountry.Custom('ga_exp_remaining')]"))
    rows += [
        ('has_variable = ga_exploration_pending', 'ga_exp_legacy',
         'Awaiting an earlier offer from this older save. Close it, then launch voyages from the Expeditions panel.'),
        ('has_variable = ga_exp_resting has_variable = ga_exploration_cooldown', 'ga_exp_resting_status', 'Resting crews — 12 months from the last return.'),
        ('has_variable = ga_exploration_cooldown', 'ga_exp_preparing', 'Preparing — the crews are ready after 36 months.'),
        ('NOT = { has_variable = ga_exploration_initialized }', 'ga_exp_not_started', 'Preparing — 36-month preparation begins at the first monthly check.'),
    ]
    dynamic('ga_exp_status', rows, 'Ready — choose a captain and launch a voyage from the Expeditions panel.')
    # Only 0.6.x calendar voyages carry these expiring flags; native fleets show on the map.
    dynamic('ga_exp_remaining', [(f'has_variable = ga_exp_remaining_{n}', f'ga_exp_remaining_{n}_text',
             'Expected return within one month.' if n == 1 else f'Expected return in {n-1}–{n} months.')
             for n in range(6, 0, -1)], 'Follow the fleet on the map or in the Expeditions panel.')

    notice = 'ga_exp_ready_notified'
    b.write(out, FILES[0], f'''ga_exploration_monthly = {{
        trigger = {{ {GOBLIN} }}
        effect = {{
            if = {{ limit = {{ NOT = {{ has_variable = ga_exploration_initialized }} }}
                set_variable = {{ name = ga_exploration_initialized value = yes }}
                set_variable = {{ name = ga_exploration_cooldown value = yes months = {first_months} }} }}
            if = {{ limit = {{ {FREE} is_ai = no NOT = {{ has_variable = ga_exp_paused }} NOT = {{ has_variable = {notice} }} }}
                set_variable = {{ name = {notice} value = yes }}
                if = {{ limit = {{ NOT = {{ has_variable = ga_charted_east }} }}
                    trigger_event_non_silently = {{ id = goblins_exploration.1 }} }}
                if = {{ limit = {{ has_variable = ga_charted_east }}
                    trigger_event_non_silently = {{ id = goblins_exploration.3 }} }} }}
        }}
    }}''')

    voyages = []
    for route_id, (route, r) in enumerate(routes.items(), 1):
        voyages.append(expedition(route, route_id, r)[1])
    b.write(out, FILES[2], '# Ashborn Voyages: goblin-only native expeditions (EU5 1.4).\n' + '\n\n'.join(voyages) + '\n')
    b.write(out, FILES[3], '\n'.join(completion(route, r, tags) for route, r in routes.items()) + '\n')
    b.write(out, FILES[4], trigger())
    build_situation(b, out, loc, dynamic, routes)

    events = ['namespace = goblins_exploration']
    for num in (1, 3):
        prefix = f'goblins_exploration.{num}'
        # An older save may hold this event open as an unpaid offer (pending, no
        # route); either answer settles it at no cost.
        settle = 'if = { limit = { NOT = { has_variable = ga_exp_route } } remove_variable = ga_exploration_pending }'
        events.append(f'''{prefix} = {{ type = country_event outcome = neutral
            title = {prefix}.title desc = {prefix}.desc
            trigger = {{ {GOBLIN} }} image = "{event_art.image(prefix)}"
            option = {{ name = ga_exp_notice.a ai_chance = {{ factor = 1 }} custom_tooltip = ga_exp_notice.a_tt
                hidden_effect = {{ {settle} }} }}
            option = {{ name = ga_exp_notice.b ai_chance = {{ factor = 0 }} custom_tooltip = ga_exp_notice.b_tt
                hidden_effect = {{ {settle} set_variable = {{ name = ga_exp_paused value = yes }} }} }}
        }}''')
    for route_id, (route, r) in enumerate(routes.items(), 1):
        num = r['event']; prefix = f'goblins_exploration.{num}'
        # A 0.6.x calendar voyage settles here once; a native voyage has already
        # charted the route in on_end before showing this report.
        legacy = f'{LEGACY} has_variable = ga_exp_route var:ga_exp_route = {route_id} NOT = {{ has_variable = ga_charted_{route} }}'
        loc(prefix+'.desc', old_text[prefix+'.desc'].split('\n\n#bold Newly charted:')[0]+'\n\n#bold Newly charted:#! '+r['summary'][0].upper()+r['summary'][1:]+'.')
        events.append(f'''{prefix} = {{ type = country_event outcome = neutral
            title = {prefix}.title desc = {prefix}.desc
            trigger = {{ {GOBLIN} OR = {{ has_variable = ga_charted_{route} AND = {{ {legacy} }} }} }}
            image = "{event_art.image(prefix)}"
            immediate = {{ if = {{ limit = {{ {legacy} }} ga_exp_complete_{route} = yes }} }}
            option = {{ name = {prefix}.a }}
        }}''')
    events.append(f'''goblins_exploration.6 = {{ type = country_event outcome = neutral
        title = goblins_exploration.6.title desc = goblins_exploration.6.desc
        trigger = {{ NOT = {{ {GOBLIN} }} }}
        image = "{event_art.image('goblins_exploration.6')}"
        option = {{ name = goblins_exploration.6.a trigger = {{ }} }}
    }}''')
    b.write(out, FILES[1], '\n'.join(events))
    b.write(out, FILES[5], '\n'.join(custom))
    for rel in RETIRED:
        (out / rel).unlink(missing_ok=True)
    b.write(out, FILES[-1], 'l_english:\n'+'\n'.join(' '+k+': "'+v.replace('\n',r'\n')+'"' for k,v in text.items())+'\n')
