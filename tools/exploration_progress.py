"""Bounded exploration state, immutable replies and player-facing voyage reports."""
import event_art

FILES = [
    'in_game/common/on_action/goblins_exploration.txt',
    'in_game/events/goblins_exploration.txt',
    'in_game/common/generic_actions/goblins_exploration.txt',
    'in_game/common/customizable_localization/goblins_exploration.txt',
    'in_game/common/situations/goblins_voyages.txt',
    'main_menu/localization/english/goblins_exploration_l_english.yml',
]
COMPLETE = 'has_variable = ga_charted_east has_variable = ga_charted_north has_variable = ga_charted_south'
MODERN = 'exists = scope:ga_exp_token var:ga_exp_serial = scope:ga_exp_token'
# Old saves used pending for both an open offer and a paid voyage. Do not clear it
# on a monthly pulse or infer an arrival date. A legacy reply can settle it once.
LEGACY = 'NOT = { has_variable = ga_exp_serial } NOT = { exists = scope:ga_exp_token }'
SESSION = f'has_variable = ga_exploration_pending OR = {{ AND = {{ {MODERN} }} AND = {{ {LEGACY} }} }}'
FREE = f'has_variable = ga_exploration_initialized NOT = {{ has_variable = ga_exploration_cooldown }} NOT = {{ has_variable = ga_exploration_pending }} NOT = {{ has_variable = ga_exp_route }} NOT = {{ AND = {{ {COMPLETE} }} }}'


def serial():
    return '''if = { limit = { NOT = { has_variable = ga_exp_serial } }
        set_variable = { name = ga_exp_serial value = 0 } }
        change_variable = { name = ga_exp_serial add = 1 }
        save_scope_value_as = { name = ga_exp_token value = var:ga_exp_serial }'''


def dispatch():
    # Two mutually exclusive branches avoid repeated evaluation or a world scan.
    return f'''{serial()}
        set_variable = {{ name = ga_exploration_pending value = yes }}
        if = {{ limit = {{ NOT = {{ has_variable = ga_charted_east }} }}
            trigger_event_non_silently = {{ id = goblins_exploration.1 }} }}
        if = {{ limit = {{ has_variable = ga_charted_east }}
            trigger_event_non_silently = {{ id = goblins_exploration.3 }} }}'''


def panel():
    # Own-country action preserves existing voyage eligibility and saved progress.
    # EU5 1.4 removed action_button_default; generic actions use scripted_action_tooltip.
    return '''text_multi = {
            layoutpolicy_horizontal = expanding max_width = 400 autoresize = yes
            text = "ga_exp_panel_status"
        }
        targetted_button_regular = {
            size = { 400 40 }
            text = "ga_commission_voyage"
            scripted_action_tooltip = {
                click_type = left
                click_mode = single
                action_name = "ga_commission_voyage"
                actor = "[GetPlayer]"
            }
        }
        '''


def build_situation(b, out, loc, dynamic, routes):
    from ashborn_roster import TAGS as tags
    loc('ga_ashborn_voyages', 'Ashborn Voyages')
    loc('ga_ashborn_voyages_desc', 'Chart the shores beyond the Ashborn Isles. Choose a route, fund its crew and await their report. Each crown keeps its own charts and voyage progress.')
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
        loc(key+'_row', f"#bold {route.title()} route#!: [GetPlayer.Custom('{key}')]\nCost: #Y {row['cost']} gold#!. Travel: #Y {row['months']} months#!.")
        content += 'text_multi = { layoutpolicy_horizontal = expanding max_width = 400 autoresize = yes text = "'+key+'_row" }\n'
    b.write(out, 'in_game/gui/panels/situation/ga_ashborn_voyages.gui', '''situation_panel = {
        blockoverride "situation_subheader_content" {}
        blockoverride "situation_panel_main_content" {
            text_multi = { layoutpolicy_horizontal = expanding max_width = 400 autoresize = yes text = "ga_ashborn_voyages_desc" }
            '''+panel()+'''
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

    loc('ga_commission_voyage', 'Review Ashborn Voyages')
    loc('ga_commission_voyage_desc', "[SCOPE.sCountry('actor').Custom('ga_exp_status')]\n\nOpen the available routes without paying. Payment happens only when you commission a voyage. Reminders remain stopped unless you choose to be reminded in six months. The first offer requires 36 months of preparation; crews rest for 12 months after returning.")
    loc('ga_exp_ready_tt', 'Preparation or the current waiting period has finished, no offer or voyage is pending, and at least one route remains uncharted.')
    loc('ga_exp_offer_tt', 'This is the current offer, no expedition is at sea, this route remains uncharted, and its price is available.')
    loc('ga_exp_panel_status', "Ashborn voyages: [GetPlayer.Custom('ga_exp_status')]\nUse Review Ashborn Voyages to reopen available routes. Routes and expedition reports are managed here, independently of unification.")
    loc('ga_exp_stale', 'Close this old message.')
    loc('ga_exp_stale_tt', 'This message is no longer current. Closing it changes nothing.')
    rows = [(COMPLETE, 'ga_exp_completed', 'Completed — all three routes are charted.')]
    for i, (route, r) in enumerate(routes.items(), 1):
        rows.append((f'has_variable = ga_exp_route var:ga_exp_route = {i}', 'ga_exp_at_sea_'+route,
                     f"At sea — {route.title()}. [ROOT.GetCountry.Custom('ga_exp_remaining')]"))
    rows += [
        (f'has_variable = ga_exploration_pending {LEGACY.replace(" NOT = { exists = scope:ga_exp_token }", "")}', 'ga_exp_legacy',
         'Awaiting an earlier offer or voyage — this older save has no route timer. Answer its existing offer or wait for its paid expedition to return.'),
        ('has_variable = ga_exploration_pending', 'ga_exp_decision', 'Awaiting decision — answer the open voyage offer.'),
        ('has_variable = ga_exp_postponed', 'ga_exp_postponed_status', 'Awaiting decision — reminder postponed for six months from your reply.'),
        ('has_variable = ga_exp_resting has_variable = ga_exploration_cooldown', 'ga_exp_resting_status', 'Resting crews — 12 months from the last arrival.'),
        ('has_variable = ga_exploration_cooldown', 'ga_exp_preparing', 'Preparing — first offer after 36 months of preparation.'),
        ('NOT = { has_variable = ga_exploration_initialized }', 'ga_exp_not_started', 'Preparing — 36-month preparation begins at the first monthly check.'),
        ('has_variable = ga_exp_paused', 'ga_exp_paused_status', 'Awaiting decision — reminders stopped. Review Ashborn Voyages when ready.'),
    ]
    dynamic('ga_exp_status', rows, 'Awaiting decision — the captains are ready. Review Ashborn Voyages or await the next monthly offer.')
    # Six expiring flags per voyage at most. They tick in native save data, with no
    # progress events or monthly counter. Route lengths remain calendar months.
    dynamic('ga_exp_remaining', [(f'has_variable = ga_exp_remaining_{n}', f'ga_exp_remaining_{n}_text',
             'Expected return within one month.' if n == 1 else f'Expected return in {n-1}–{n} months.')
             for n in range(6, 0, -1)], 'The expedition is due to return.')

    b.write(out, FILES[0], f'''ga_exploration_monthly = {{
        trigger = {{ OR = {{ {tags} }} }}
        effect = {{
            if = {{ limit = {{ NOT = {{ has_variable = ga_exploration_initialized }} }}
                set_variable = {{ name = ga_exploration_initialized value = yes }}
                set_variable = {{ name = ga_exploration_cooldown value = yes months = {first_months} }} }}
            if = {{ limit = {{ {FREE} NOT = {{ has_variable = ga_exp_paused }} }}
                {dispatch()} }}
        }}
    }}''')
    b.write(out, FILES[2], f'''ga_commission_voyage = {{
        type = owncountry show_message = no ai_tick = never automation_tick = never
        potential = {{ scope:actor = {{ OR = {{ {tags} }} }} }}
        allow = {{ scope:actor = {{ custom_tooltip = {{ text = ga_exp_ready_tt {FREE} }} }} }}
        effect = {{ scope:actor = {{ if = {{ limit = {{ OR = {{ {tags} }} {FREE} }} {dispatch()} }} }} }}
    }}''')

    build_situation(b, out, loc, dynamic, routes)

    events = ['namespace = goblins_exploration']
    for num, keys in [(1, ['east']), (3, ['north', 'south'])]:
        prefix = f'goblins_exploration.{num}'
        options = []
        for route in keys:
            r = routes[route]; route_id = list(routes).index(route)+1
            ports = r['summary']
            loc(prefix+'.'+route, f"Sail {route}: {r['cost']} gold; return in {r['months']} months.")
            loc(prefix+'.'+route+'_terms', f"Pay {r['cost']} gold once. Chart {ports}. Most inland territory remains unknown. Travel takes {r['months']} months. When the crew arrives, the current owners of these ports learn the Ashborn homeland and its surrounding waters. Crews then rest for 12 months.")
            gate = f'OR = {{ {tags} }} {SESSION} NOT = {{ has_variable = ga_exp_route }} NOT = {{ has_variable = ga_charted_{route} }} gold >= {r["cost"]}'
            if route != 'east': gate += ' has_variable = ga_charted_east'
            timers = ' '.join(f'set_variable = {{ name = ga_exp_remaining_{n} value = yes months = {r["months"]-n+1} }}' for n in range(1,r['months']+1))
            options.append(f'''option = {{ name = {prefix}.{route}
                trigger = {{ custom_tooltip = {{ text = ga_exp_offer_tt {gate} }} }}
                ai_chance = {{ factor = 10 }} custom_tooltip = {prefix}.{route}_terms
                hidden_effect = {{ if = {{ limit = {{ {gate} }}
                    {serial()}
                    add_gold = -{r['cost']}
                    set_variable = {{ name = ga_exp_route value = {route_id} }}
                    remove_variable = ga_exp_resting
                    {timers}
                    trigger_event_non_silently = {{ id = goblins_exploration.{r['event']} months = {r['months']} }}
                }} }}
            }}''')
        session = f'{SESSION} NOT = {{ has_variable = ga_exp_route }}'
        for key, label, effects, chance in [
            ('wait', 'Remind me in six months.', 'remove_variable = ga_exp_paused set_variable = { name = ga_exploration_cooldown value = yes months = 6 } set_variable = { name = ga_exp_postponed value = yes months = 6 }', 1),
            ('pause', "Stop reminders; I will commission a voyage myself.", 'set_variable = { name = ga_exp_paused value = yes }', 0),
        ]:
            loc(prefix+'.'+key, label)
            loc(prefix+'.'+key+'_terms', 'No payment. '+('Review Ashborn Voyages in the Ashborn Voyages situation to reopen an available route. Reminders stay off after manual voyages.' if key == 'pause' else 'The next automatic offer is six months away. This also restores reminders if they were stopped.'))
            options.append(f'''option = {{ name = {prefix}.{key} trigger = {{ {session} }}
                ai_chance = {{ factor = {chance} }} custom_tooltip = {prefix}.{key}_terms
                hidden_effect = {{ if = {{ limit = {{ {session} }}
                    {serial()} remove_variable = ga_exploration_pending {effects}
                }} }} }}''')
        options.append(f'''option = {{ name = ga_exp_stale trigger = {{ NOT = {{ {session} }} }}
            ai_chance = {{ factor = 1 }} custom_tooltip = ga_exp_stale_tt }}''')
        events.append(f'''{prefix} = {{ type = country_event outcome = neutral
            title = {prefix}.title desc = {prefix}.desc
            trigger = {{ OR = {{ {tags} }} }} image = "{event_art.image(prefix)}"
            {chr(10).join(options)}
        }}''')

    for route_id, (route,r) in enumerate(routes.items(), 1):
        num=r['event']; prefix=f'goblins_exploration.{num}'
        gate=f'OR = {{ {tags} }} has_variable = ga_exploration_pending NOT = {{ has_variable = ga_charted_{route} }} OR = {{ AND = {{ {MODERN} var:ga_exp_route = {route_id} }} AND = {{ {LEGACY} }} }}'
        effects='\n'.join('discover_area = area:'+a for a in r['areas'])
        for port in r['locations']:
            # Port owners are captured at arrival, before the report is displayed.
            effects+=f'''\nlocation:{port} = {{ discover_location = root
                if = {{ limit = {{ exists = owner }} owner = {{
                    save_scope_as = ga_exp_contact_{port}
                    discover_area = area:cm_cindermaw_area
                    discover_area = area:cm_ashborn_seas_area
                    if = {{ limit = {{ NOT = {{ OR = {{ {tags} }} }} NOT = {{ has_variable = ga_received_goblin_first_contact }} }}
                        set_variable = {{ name = ga_received_goblin_first_contact value = yes }}
                        trigger_event_non_silently = {{ id = goblins_exploration.6 }} }}
                }} }} }}'''
        # Arrival prose is deliberately static: no saved-token diagnostics or
        # missing-scope fallbacks should appear in a player's story event.
        loc(prefix+'.desc', old_text[prefix+'.desc']+'\n\n#bold Newly charted:#! '+r['summary'][0].upper()+r['summary'][1:]+'.')
        completion=f'''{effects}
                {serial()}
                set_variable = {{ name = ga_charted_{route} value = yes }}
                remove_variable = ga_exploration_pending remove_variable = ga_exp_route
                set_variable = {{ name = ga_exploration_cooldown value = yes months = 12 }}
                set_variable = {{ name = ga_exp_resting value = yes }}'''
        events.append(f'''{prefix} = {{ type = country_event outcome = neutral
            title = {prefix}.title desc = {prefix}.desc
            trigger = {{ {gate} }} image = "{event_art.image(prefix)}"
            immediate = {{ if = {{ limit = {{ {gate} }}
                {completion}
                save_scope_value_as = {{ name = ga_exp_report_ready value = 1 }}
            }} }}
            option = {{ name = {prefix}.a trigger = {{ }}
                hidden_effect = {{ if = {{ limit = {{ {gate} {LEGACY} }} {completion} }} }}
            }}
        }}''')
    events.append(f'''goblins_exploration.6 = {{ type = country_event outcome = neutral
        title = goblins_exploration.6.title desc = goblins_exploration.6.desc
        trigger = {{ NOT = {{ OR = {{ {tags} }} }} }}
        image = "{event_art.image('goblins_exploration.6')}"
        option = {{ name = goblins_exploration.6.a trigger = {{ }} }}
    }}''')
    b.write(out, FILES[1], '\n'.join(events))
    b.write(out, FILES[3], '\n'.join(custom))
    b.write(out, FILES[-1], 'l_english:\n'+'\n'.join(' '+k+': "'+v.replace('\n',r'\n')+'"' for k,v in text.items())+'\n')
