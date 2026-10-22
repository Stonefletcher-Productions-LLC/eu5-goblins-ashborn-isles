"""Authored 0.5.7 religion generator. Standalone output is a partial staging tree."""
from pathlib import Path
import argparse
import json
import covenant_stories

LORE_SECTION = '## The Ashen Covenant\n\nThe Ashborn call their shared faith the Ashen Covenant. Beneath the islands sleeps\nthe Hunger Below, whose fire makes land and whose appetite may consume it. Some\nsay the first goblins were born from that fire; others remember passages that\nclosed behind them. No common account settles the mystery.\n\n"What keeps you living must be fed." Fire, water, roots and the remembered dead\nlend their gifts, and every gift creates an obligation. A chief owes protection\nand provisions to the households that supply his crews. A rescued sailor owes\nlabor to the beacon keepers. A woodcutter owes care to the grove that shelters the\nnext generation. Offerings are useful things: food, rope, charcoal and finished\ncraftwork, with animal sacrifice at some feasts.\n\nThe Returning Mother receives the household cords of Shatterfin. Brackmaw\'s Reed\nListener witnesses agreements beside water. Reefhook tends lamps for the Lantern\nDead, including strangers whose names are lost. Sootwake\'s Rootkeeper shelters\nburial trees and seed groves. Chainhaven\'s merchants swear their measures before\nthe Silent Scale, which weighs every debt. At the Storm Teeth, crews honor the\nTooth in the Gale. These powers belong to the shared faith; migrating households carry their\nobservances between islands rather than changing religion at a border.\n\nOathkeepers preserve names, witness agreements, heal and interpret omens. They\nmay be women or men; inheritance, apprenticeship and public recognition vary by\nshrine. Their authority can restrain a chief, but gifts and family loyalties can\nalso purchase a convenient interpretation. The island crowns have no common\nreligious head at the beginning of the campaign.\n\nThe sacred places are young: fissures, pools, cairns, ropes and living groves on\nrecently emerged islands. Carried relics and remembered chants hint at an older\npast without proving where the Ashborn came from. The covenant can welcome an\noutsider adopted into a household, yet its promise of reciprocal duties also\nraises difficult questions about those held in slavery.\n\n'

ROOT = Path(__file__).resolve().parents[1]
RELIGION = 'cm_hunger_below'  # Stable save/setup identity; only the display name changes.
DESCRIPTION = ('The Ashborn live by bargains with fire, water, roots and the remembered dead. '
    'Beneath the islands sleeps the Hunger Below: its fire creates land, yet its appetite can consume it. '
    'Oathkeepers tend local shrines and witness the duties of chiefs to their households. '
    'The Returning Mother, Reed Listener, Lantern Dead, Rootkeeper, Silent Scale and Tooth in the Gale receive their own offerings. '
    'No single priest speaks for every island. A chief may bind up to four households to his hearth through marriage, '
    'so a crowned goblin keeps several wives. What keeps you living must be fed.')
ASPECTS = {
    'common_hearth': ('Feed the Common Hearth', 'The first share sustains the households. Chiefs must answer for empty stores.', 'global_monthly_food_modifier', .05),
    'offering_smoke': ('Smoke Is an Offering', 'Useful work feeds the fire below. Forge crews dedicate their first finished piece.', 'global_production_efficiency', .05),
    'crew_home': ('Bring the Crew Home', 'The Lantern Dead guide those who keep the rescue lights burning. Reckon the cargo after the living.', 'naval_morale_modifier', .05),
    'remembered_dead': ('The Dead Keep Their Names', 'Funeral keepers recite the names and obligations carried by each household.', 'stability_cost_efficiency', .10),
    'cutting_oath': ('No Axe Without an Oath', 'Root-wardens guard seed groves, firebreaks and the wooded paths that shelter our people.', 'global_defensive', .10),
    'shore_spirits': ('Every Shore Has Spirits', 'An unfamiliar shore has powers of its own. Its inhabitants may teach us how to honor them.', 'tolerance_heathen', 1),
    'first_share': ('The First Share Goes Below', 'The Hunger receives the first offering after battle; the bereaved must also receive their due.', 'land_morale_modifier', .05),
    'many_hearths': ('Many Hearths, One Covenant', 'Each shrine keeps its own witnesses. A common faith need not silence its many voices.', 'clergy_estate_target_satisfaction', .05),
}
STARTING = {'CDM': ('offering_smoke', 'first_share'), 'QBR': ('common_hearth', 'many_hearths'),
            'RHK': ('crew_home', 'shore_spirits'), 'SFK': ('crew_home', 'remembered_dead'),
            'SWK': ('cutting_oath', 'remembered_dead'), 'GTF': ('common_hearth', 'first_share')}
SITES = [
    ('first_mouth', 'The First Mouth', 'cm_cinder_crown', 'cindermaw', 'local_production_efficiency', .05,
     'A warm fissure beneath Cinder Crown. Ember-speakers listen through hollow stone tubes while forge crews surrender their first work. No one agrees whether the first goblins were born here or escaped through it.'),
    ('listening_pool', 'The Listening Pool', 'cm_reedmouth', 'brackmaw', 'local_monthly_food_modifier', .05,
     'A spring-fed pool beside the tidal channels. Carved stakes record repair oaths, and old flood marks remind the marsh houses what neglect can cost.'),
    ('lantern_steps', 'The Lantern Steps', 'cm_tidefang', 'reefhook', 'local_monthly_prosperity', .001,
     'Steps descend to the landing where the drowned are brought ashore. Lamps burn beside name stones; strangers receive a stone even when no name survives.'),
    ('mothers_basin', "The Mothers' Basin", 'cm_shatterfin', 'shatterfin', 'local_unrest', -.05,
     'Maternal households wash heirloom cords in a rain-fed basin above the harbor. Each knot recalls a dependent, a promise or a return from sea.'),
    ('storm_teeth', 'The Storm Teeth', 'cm_knifeback', 'knifeback', 'local_defensive', .10,
     'Basalt pinnacles carry ropes left by returning crews. Pilgrims climb with a stone for someone who never returned, seeking the courage of the Tooth in the Gale.'),
    ('emberroot', 'The Emberroot Hollow', 'cm_ember_key', 'sootwake', 'local_defensive', .10,
     'A charred stump marks the first sheltered hearth. Funeral ash is laid beneath young trees, and Root-wardens keep the surrounding seed grove from the charcoal axes.'),
]
# Importance is spiritual reach, not settlement size or an upgrade level.
# Native holy-site location modifiers are multiplied by this importance.
SITE_IMPORTANCE = {
    'first_mouth': 5, 'listening_pool': 3, 'lantern_steps': 2,
    'mothers_basin': 4, 'storm_teeth': 1, 'emberroot': 2,
    'blackwood_oathstones': 2, 'ashfield_hearth': 1, 'miregrove_witness': 1,
    'first_weight': 3, 'last_lamp': 1, 'three_watchfires': 1,
    'gull_cairn': 1, 'kiln_stair': 1,
}
SITES.extend([
    ('three_watchfires', 'The Three Watchfires', 'cm_emberwatch', 'lantern_cay', 'local_monthly_prosperity', .001,
     'Three fires mark the Quiet Road below Emberwatch. Passing crews leave fuel before counting their cargo, honoring the Lantern Dead and the Cindermaw households who keep the channel lit.'),
    ('first_weight', 'The First Weight', 'cm_chainhaven', 'giltfang', 'local_production_efficiency', .025,
     'A copper weight hangs above the sea fissure beneath Chainhaven. Merchants surrender the first measured share of each cargo; false scales are broken before the Oathkeepers.'),
    ('last_lamp', 'The Last Lamp', 'cm_lastlight', 'tolltooth', 'local_monthly_prosperity', .001,
     'Tolltooth households keep a lamp for crews still beyond the horizon. Its flame is tended before any toll is counted, for a lost crew can repay no debt.'),
    ('blackwood_oathstones', 'The Blackwood Oathstones', 'cm_blackwood', 'cindermaw', 'local_defensive', .025,
     'Woodcutters bind charcoal-black cords around stones on the old forest path. Each cord promises a firebreak kept or a household sheltered; broken oaths are recited before the next cutting.'),
    ('ashfield_hearth', 'The Ashfield Hearth', 'cm_ashfields', 'cindermaw', 'local_monthly_food_modifier', .025,
     'Field households carry a pinch of the first grain to a low hearth built from cooling lava. Its keepers feed hungry neighbors before burning the offering. Few pilgrims come from beyond the nearby farms.'),
    ('miregrove_witness', 'The Miregrove Witness', 'cm_miregrove', 'brackmaw', 'local_unrest', -.025,
     'A crooked grove above the floodwater shelters the oath stakes of neighboring marsh houses. Disputes over channels are spoken before its roots, where witnesses remember promises longer than chiefs do.'),
    ('gull_cairn', 'The Gull Cairn', 'cm_gullwatch', 'maw_rock', 'local_monthly_food_modifier', .025,
     'A cairn of wave-worn stones stands above the Shatter Strait. Fishers add a stone for each crew that came home and leave the first gull-picked catch of the season beneath it.'),
    ('kiln_stair', 'The Kiln Stair', 'cm_kilnwatch', 'cinderstep', 'local_production_efficiency', .025,
     'Steps cut into a cooled lava flow climb to an old charcoal kiln above the Cinderstep Passage. Smelters carry up the first bloom of each season, and crews bound for Shatter Maw leave a coal for a safe crossing.'),
])
RITES = {
    'returning_ash': ('Feast of Returning Ash', 'Fund a communal feast and name the dead.', 'stability_cost_efficiency', .10),
    'water_lanterns': ('Lanterns Upon the Water', 'Provision beacon keepers and the households of missing crews.', 'naval_morale_modifier', .10),
    'first_oath': ('Renewal of the First Oath', 'Reconcile the crown with the Oathkeepers and renew communal duties.', 'clergy_estate_target_satisfaction', .10),
}

# Covenant rites beyond the three major rites. Each entry:
# name, description, extra potential, extra allow, price, cooldown years, modifier years,
# modifiers, immediate effect. Shared rites serve every Covenant crown; each clan rite
# follows the country's primary culture, so all six Ashborn cultures receive one.
CLAN_CULTURES = {'cindermaw': 'cm_cinderkin', 'brackmaw': 'cm_brinekin', 'reefhook': 'cm_reefkin',
                 'shatterfin': 'cm_shatterkin', 'sootwake': 'cm_sootkin', 'giltfang': 'cm_giltkin'}
PRICES = {'ac_offering': 'scaled_gold = 1', 'ac_minor_rite': 'religious_influence = 10',
          'ac_clan_rite': 'religious_influence = 15', 'ac_moot_convening': 'scaled_gold = 1 religious_influence = 25'}
COVENANT_RITES = {
    'feed_mouth': ('Feed the Mouth', 'Carry a month of the crown\'s income to the nearest fissure shrine. The Oathkeepers count the offering aloud.',
        '', '', 'ac_offering', 2, 0, {}, 'add_religious_influence = 10'),
    'witness_oath': ('Witness an Oath', 'Oathkeepers hear the chiefs swear their duties to the crown and to their households.',
        '', '', 'ac_minor_rite', 1, 0, {},
        'add_estate_satisfaction = { type = estate_type:nobles_estate value = 0.05 } add_estate_satisfaction = { type = estate_type:clergy_estate value = 0.025 }'),
    'name_dead': ('Name the Dead', 'Recite the names of the fallen before the muster, so that no household is forgotten in the reckoning.',
        '', 'at_war = yes', 'ac_minor_rite', 2, 2, {'land_morale_recovery': .05, 'global_manpower_modifier': .05}, ''),
    'bless_hulls': ('Bless the Hulls', 'Smoke every keel in the harbor and hang a lantern for each crew still at sea.',
        '', '', 'ac_minor_rite', 3, 3, {'naval_morale_recovery': .05, 'navy_maintenance_efficiency': .05}, ''),
    'clan_cindermaw': ('Smoke from the First Mouth', 'Ember-speakers carry coals from the First Mouth to every new foundation. Emberblood work goes faster under that smoke.',
        'culture = culture:cm_cinderkin', '', 'ac_clan_rite', 5, 3, {'global_construction_speed': .10}, ''),
    'clan_brackmaw': ('Listening at the Pool', 'Reed-witnesses read the Listening Pool and bless the marsh households that will raise the next generation.',
        'culture = culture:cm_brinekin', '', 'ac_clan_rite', 5, 3, {'global_population_growth': .001}, ''),
    'clan_reefhook': ('Lantern for the Lost', 'Reefstriders light the Lantern Steps for crews that never returned. Their kin answer by signing onto the next voyage.',
        'culture = culture:cm_reefkin', '', 'ac_clan_rite', 5, 3, {'global_sailors_modifier': .10}, ''),
    'clan_shatterfin': ("The Tidemothers' Cord", "Tidemothers tie a new knot at the Mothers' Basin for every household bound to us abroad. Foreign courts learn that a Stormfang cord is not cut lightly.",
        'culture = culture:cm_shatterkin', '', 'ac_clan_rite', 5, 3, {'diplomatic_reputation': 1}, ''),
    'clan_sootwake': ('Oath of the Axe', 'Root-wardens let each young Ashveil swear by Emberroot Hollow before taking up an axe for the crown.',
        'culture = culture:cm_sootkin', '', 'ac_clan_rite', 5, 3, {'global_manpower_modifier': .10}, ''),
    'clan_giltfang': ('Weighing of the First Gold', 'Merchants hang their scales beside the First Weight and swear them true. Cinderweight traders are trusted wherever their oath is known.',
        'culture = culture:cm_giltkin', '', 'ac_clan_rite', 5, 3, {'global_merchant_power': .10}, ''),
    # The standing Moot of Six Fires, for a crown that has held the Moot.
    'convene_moot': ('Convene the Moot of Six Fires', 'Call the Oathkeepers of every island to the six fires. Disputes between chiefs are heard and settled before the crown.',
        'has_variable = ac_moot_held', '', 'ac_moot_convening', 5, 0, {},
        'add_stability = stability_mild_bonus add_all_estate_satisfaction = { value = estate_satisfaction_mild_bonus }'),
    'hear_shrines': ('Hear the Local Shrines', 'Under the Local Covenants each shrine keeps its own witnesses. The crown travels to hear them in turn.',
        'has_variable = ac_moot_held has_variable = ac_local_covenants', '', 'ac_clan_rite', 5, 5,
        {'clergy_estate_target_satisfaction': .05, 'tolerance_heathen': .5}, ''),
    'oathkeeper_writ': ("The First Oathkeeper's Writ", 'The First Oathkeeper sends sealed writs to every island. Chiefs who ignore them answer to the Moot.',
        'has_variable = ac_moot_held has_variable = ac_first_oathkeeper', '', 'ac_clan_rite', 5, 5,
        {'global_monthly_control': .0025, 'stability_cost_efficiency': .05}, ''),
}

# Event-specific eligibility is checked by native random_events before selection.
# Each story has two distinct approaches and a neutral defer option.
STORIES = [
    (1, 'The Mountain Answers', 'A tremor opens a narrow cavity beneath the First Mouth. Miners want to follow the warm draft; the Ember-speakers demand that the listening fissure be made safe first.', 'owns = location:cm_cinder_crown', 'covenant_mountain', 'Secure the fissure and hear the witnesses.', 'Let the miners follow the draft.'),
    (2, 'The Flood Remembers', 'The stakes at the Listening Pool name a wealthy house that promised labor after the last flood. Its heirs now deny the debt. The Reed-witnesses bring the old flood marks before the crown.', 'owns = location:cm_reedmouth', 'covenant_flood', 'Fund the repairs and uphold the oath.', 'Accept the heirs\' objection.'),
    (3, 'A Stranger Beneath Our Lantern', 'A foreign sailor has washed ashore at the Lantern Steps. Some households refuse a stranger a place among their dead; the keepers answer that the sea did not ask his birthplace.', 'owns = location:cm_tidefang', 'covenant_lantern', 'Give the stranger a lamp and a stone.', 'Leave the burial to the harbor households.'),
    (4, 'A Cord Without a Name', 'A dependent branch of the maternal house presents an unmarked cord at the Mothers\' Basin. Recognizing it would make old promises public and give its households a voice at future observances.', 'owns = location:cm_shatterfin', 'covenant_cord', 'Provide the gifts and witness their names.', 'Let the senior households settle it.'),
    (5, 'The Path to the Storm Teeth', 'Loose stone has made the pilgrimage climb dangerous. Returning captains demand a repaired path, while younger crews call the danger a fitting test of the storm spirit.', 'owns = location:cm_knifeback', 'covenant_storm_teeth', 'Repair the path before another climb.', 'Leave the climb to those who dare.'),
    (6, 'The Forbidden Felling', 'Charcoal burners have marked trees inside Emberroot Hollow. The navy needs timber and the forges need fuel, but Root-wardens insist that a seed grove cannot be bought back once it is gone.', 'owns = location:cm_ember_key', 'covenant_grove', 'Pay for supplies from outside the grove.', 'Permit a limited cutting.'),
    (7, 'The Unnamed Crew', 'A captain has omitted missing sailors from his account of a voyage. Naming them would oblige his patrons to support their households. The Lantern-keepers have brought their families to court.', 'has_religious_aspect = religious_aspect:ac_crew_home', 'covenant_unnamed_crew', 'Compensate the households and record the names.', 'Accept the captain\'s account.'),
    (8, 'The Hungry Preacher', 'A wandering speaker claims that charcoal and food no longer satisfy the Hunger Below. The local Oathkeepers accuse the preacher of making the mountain an excuse for ambition.', '', 'covenant_preacher', 'Sponsor a public feast under the Oathkeepers.', 'Let the shrines answer without the crown.'),
    (9, 'The Captive\'s Hearth', 'An enslaved household asks to name its dead beside those of its owners. Its speaker asks whether sharing a hearth creates duties even toward captives. Several chiefs fear the precedent.', '', 'covenant_captives_hearth', 'Pay for their memorial and acknowledge the duty.', 'Leave the matter to the household\'s owners.'),
    (10, 'A Spirit Beyond the Sea', 'Our overseas crews return with accounts of a sacred place tended by people beyond the Isles. Some wish to offer useful gifts there; others fear acknowledging powers whose names we barely know.', 'has_variable = ga_charted_east', 'covenant_spirit_beyond', 'Send gifts and learn the local observances.', 'Keep our offerings for the island shrines.'),
    (11, 'The Empty Feast', 'Common-hearth keepers report that some households cannot bring even a small offering to the seasonal feast. A chief\'s full table has become an accusation against him.', 'has_religious_aspect = religious_aspect:ac_common_hearth', 'covenant_empty_feast', 'Feed the households from the crown\'s stores.', 'Require each household to provide its share.'),
    (12, 'The First Finished Blade', 'Forge crews disagree over an unusually fine blade set aside for the First Mouth. A captain wants it for the muster; the smith who made it insists that an offering is an oath already spoken.', 'has_religious_aspect = religious_aspect:ac_offering_smoke', 'covenant_finished_blade', 'Pay the smith and honor the offering.', 'Send the blade to the muster.'),
    (13, 'The Light Weight', 'An Oathkeeper has found a copper weight shaved thin in a Chainhaven counting house. The house that owns it is rich, well connected and owed money by half the harbor. The First Weight still hangs above the fissure, and every merchant is watching to learn what it is worth.', 'owns = location:cm_chainhaven', 'covenant_light_weight', 'Break the false weight beneath the First Weight.', 'Fine the house quietly and keep its trade.'),
]

def build(out):
    text = {'religious_influence_cm_hunger_below': 'Covenant Favor',
            'ac_favor_current': "Covenant Favor: [GetPlayer.GetCurrencyValue('religious_influence')|1]",
            'ac_favor_explanation': 'Covenant Favor is your religious influence. The Ashen Covenant grants 0.2 Favor per month and adds 100 to its maximum. Stories can raise or spend Favor. Major rites cost 20 Favor plus gold. See the Religion panel for the current gain and maximum modifiers.'}
    paths = []
    def loc(key, value):
        text[key] = value
        return key
    def write(path, content):
        p = out / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content.strip() + '\n', encoding='utf-8-sig', newline='\r\n')
        paths.append(path)
    # female_spouses stacks on the marriage law: Monogamous Marriage (1) + 3 = four wives,
    # the same limit as native Polygyny, which the Ashen Covenant cannot select.
    write('in_game/common/religions/goblins_ashborn_isles.txt', f'''{RELIGION} = {{
 color = rgb {{ 160 56 36 }}
 group = cm_ashen_faiths
 language = cm_cinderkin_dialect
 tags = {{ folk_african_gfx pagan_gfx }}
 religious_aspects = 2
 has_religious_influence = yes
 definition_modifier = {{ monthly_religious_influence = 0.2 maximum_religious_influence = 100 female_spouses = 3 }}
 opinions = {{ }}
}}''')
    aspects = []
    for key, (name, desc, modifier, value) in ASPECTS.items():
        loc('ac_' + key, name); loc('ac_' + key + '_desc', desc)
        aspects.append(f'ac_{key} = {{ religion = {RELIGION} icon = religious_aspect_folk_green modifier = {{ {modifier} = {value} }} }}')
    write('in_game/common/religious_aspects/ashen_covenant.txt', '\n'.join(aspects))
    sites, types = [], []
    for key, name, location, island, modifier, value, desc in SITES:
        loc('ac_' + key, name); loc('ac_' + key + '_desc', desc)
        loc('ac_' + key + '_site', name)
        sites.append(f'ac_{key} = {{ location = {location} type = ac_{key}_site importance = {SITE_IMPORTANCE[key]} religions = {{ {RELIGION} }} }}')
        types.append(f'ac_{key}_site = {{ location_modifier = {{ {modifier} = {value} }} }}')
    write('in_game/common/holy_sites/ashen_covenant.txt', '\n'.join(sites))
    write('in_game/common/holy_site_types/ashen_covenant.txt', '\n'.join(types))
    write('in_game/common/prices/ashen_covenant.txt', 'ac_major_rite = { scaled_gold = 2 religious_influence = 20 }\n'
          + '\n'.join(f'{key} = {{ {body} }}' for key, body in PRICES.items()))
    # EU5 1.3.11 logs a missing <price>_cost_modifier for every price without one.
    price_labels = [('ac_major_rite', 'Major Covenant Rite', 'a major Covenant rite'), ('ac_offering', 'Covenant Offering', 'a Covenant offering'),
                    ('ac_minor_rite', 'Covenant Rite', 'a Covenant rite'), ('ac_clan_rite', 'Clan Rite', 'a clan or Moot rite'),
                    ('ac_moot_convening', 'Convening the Moot', 'the Moot of Six Fires')]
    write('main_menu/common/modifier_type_definitions/ashen_covenant.txt', '\n'.join(
          f'{key}_cost_modifier = {{ color = bad percent = yes game_data = {{ category = country }} }}' for key, _, _ in price_labels))
    for key, label, what in price_labels:
        loc(key, label)
        loc(f'MODIFIER_TYPE_NAME_{key}_cost_modifier', label + ' Cost')
        loc(f'MODIFIER_TYPE_DESC_{key}_cost_modifier', f'Changes the cost of performing {what}.')
    mods, actions = [], []
    for key, (name, desc, modifier, value) in RITES.items():
        loc('ac_' + key, name)
        loc('ac_' + key + '_desc', desc + ' Costs two months of scaled income and 20 Covenant Favor. The blessing lasts five years; all major rites share a five-year cooldown.')
        loc('STATIC_MODIFIER_NAME_ac_' + key, name)
        loc('STATIC_MODIFIER_DESC_ac_' + key, desc + ' The blessing lasts five years.')
        mods.append(f'ac_{key} = {{ {modifier} = {value} }}')
        actions.append(f'''ac_{key} = {{
 # Religious actions are listed in the Religion panel's actions card, beside Covenant Favor.
 type = religious
 sound = UI_action_religion_generic
 show_message = no
 automation_tick = never
 ai_tick = monthly
 ai_tick_frequency = 12
 potential = {{ scope:actor = {{ religion = religion:{RELIGION} }} }}
 allow = {{ scope:actor = {{ NOT = {{ has_variable = ac_rite_cooldown }} }} }}
 price = price:ac_major_rite
 cooldown = {{ type = ac_{key} years = 5 }}
 select_trigger = {{ looking_for_a = religion source = actor target_flag = recipient name = "choose_religion" column = {{ data = name }} }}
 effect = {{ scope:actor = {{
   set_variable = {{ name = ac_rite_cooldown years = 5 }}
   add_country_modifier = {{ modifier = ac_{key} years = 5 mode = replace }}
 }} }}
 ai_will_do = {{ add = 5 }}
}}''')
    for key, (name, desc, potential, allow, price, cooldown, years, modifiers, immediate) in COVENANT_RITES.items():
        terms = []
        if modifiers:
            terms.append(f'The blessing lasts {years} years.')
        terms.append(f'Can be performed again after {cooldown} year{"s" if cooldown > 1 else ""}.')
        loc('ac_' + key, name)
        loc('ac_' + key + '_desc', desc + ' ' + ' '.join(terms))
        effect = immediate
        if modifiers:
            loc('STATIC_MODIFIER_NAME_ac_' + key, name)
            loc('STATIC_MODIFIER_DESC_ac_' + key, desc)
            mods.append(f'ac_{key} = {{ ' + ' '.join(f'{m} = {v}' for m, v in modifiers.items()) + ' }')
            effect = (effect + f' add_country_modifier = {{ modifier = ac_{key} years = {years} mode = replace }}').strip()
        actions.append(f"""ac_{key} = {{
 type = religious
 sound = UI_action_religion_generic
 show_message = no
 automation_tick = never
 ai_tick = monthly
 ai_tick_frequency = 6
 potential = {{ scope:actor = {{ religion = religion:{RELIGION} {potential} }} }}
 allow = {{ scope:actor = {{ has_ruler = yes {allow} }} }}
 price = price:{price}
 cooldown = {{ type = ac_{key} years = {cooldown} }}
 select_trigger = {{ looking_for_a = religion source = actor target_flag = recipient name = "choose_religion" column = {{ data = name }} }}
 effect = {{ scope:actor = {{ {effect} }} }}
 ai_will_do = {{ add = 5 }}
}}""")
    for key, name, modifier, value in [('local_covenants', 'The Local Covenants', 'tolerance_heathen', 1), ('first_oathkeeper', 'The First Oathkeeper', 'stability_cost_efficiency', .10)]:
        loc('ac_' + key, name); loc('ac_' + key + '_desc', 'The settlement agreed at the Moot of Six Fires.')
        loc('STATIC_MODIFIER_NAME_ac_' + key, name)
        loc('STATIC_MODIFIER_DESC_ac_' + key, 'The permanent settlement agreed at the Moot of Six Fires.')
        mods.append(f'ac_{key} = {{ {modifier} = {value} }}')
    write('in_game/common/generic_actions/ashen_covenant.txt', '\n'.join(actions))
    write('in_game/common/generic_action_ai_lists/ashen_covenant.txt',
          f'ac_rites_ai = {{ potential = {{ religion = religion:{RELIGION} }} actions = {{ ' + ' '.join('ac_' + k for k in list(RITES) + list(COVENANT_RITES)) + ' } }')
    write('main_menu/common/static_modifiers/ashen_covenant.txt', '\n'.join(mods) + '\n' + covenant_stories.modifiers(loc))
    events = ['namespace = ashen_covenant']
    events.extend(covenant_stories.event(row, loc) for row in STORIES)
    prefix = 'ashen_covenant.20'
    loc(prefix + '.title', 'The Moot of Six Fires')
    loc(prefix + '.desc', 'The islands answer to a common realm, but their Oathkeepers speak with many voices. Ember-speakers ask who will witness the crown\'s promises. Tidemothers insist that no common authority erase their household cords. The gathered custodians await a settlement: renew the local covenants, or appoint a First Oathkeeper to serve the united realm?')
    loc(prefix + '.a', 'Renew the local covenants. Each shrine keeps its witnesses.')
    loc(prefix + '.b', 'Appoint a First Oathkeeper to the common realm.')
    events.append(f'''{prefix} = {{
 type = country_event category = situation_event outcome = neutral
 title = {prefix}.title desc = {prefix}.desc
 image = "gfx/interface/illustrations/event/ashborn/covenant_moot.dds"
 trigger = {{ religion = religion:{RELIGION} has_variable = ga_unifier ga_controls_homeland = yes }}
 option = {{ name = {prefix}.a ai_chance = {{ factor = 1 }} set_variable = {{ name = ac_local_covenants value = yes }} add_country_modifier = {{ modifier = ac_local_covenants years = -1 mode = replace }} }}
 option = {{ name = {prefix}.b ai_chance = {{ factor = 1 }} set_variable = {{ name = ac_first_oathkeeper value = yes }} add_country_modifier = {{ modifier = ac_first_oathkeeper years = -1 mode = replace }} }}
}}''')
    write('in_game/events/ashen_covenant.txt', '\n'.join(events))
    starts = []
    for tag, pair in STARTING.items():
        starts.append(f'if = {{ limit = {{ tag = {tag} num_of_religious_aspects = 0 }} ' + ' '.join(f'add_religious_aspect = religious_aspect:ac_{key}' for key in pair) + ' }')
    timed = [key for key, row in COVENANT_RITES.items() if row[7]]
    cleanup = ' '.join(f'remove_country_modifier = ac_{key}' for key in list(RITES) + ['local_covenants', 'first_oathkeeper'] + timed)
    cleanup += ' ' + covenant_stories.cleanup() + ' remove_variable = ac_story_open'
    write('in_game/common/on_action/ashen_covenant.txt', f'''monthly_country_pulse = {{ on_actions = {{ ac_covenant_monthly ac_covenant_stories }} }}
ac_covenant_monthly = {{
 trigger = {{ OR = {{ religion = religion:{RELIGION} has_variable = ac_initialized }} }}
 effect = {{
  if = {{ limit = {{ religion = religion:{RELIGION} }}
   if = {{ limit = {{ NOT = {{ has_variable = ac_initialized }} }}
    set_variable = {{ name = ac_initialized value = yes }}
    set_variable = {{ name = ac_story_cooldown years = 1 }}
    {' '.join(starts)}
   }}
   if = {{ limit = {{ has_variable = ga_unifier NOT = {{ has_variable = ac_moot_held }} ga_controls_homeland = yes }}
    set_variable = {{ name = ac_moot_held value = yes }}
    trigger_event_non_silently = {{ id = ashen_covenant.20 }}
   }}
  }}
  else = {{ {cleanup} remove_variable = ac_initialized }}
 }}
}}
ac_covenant_stories = {{
 trigger = {{ religion = religion:{RELIGION} has_variable = ac_initialized NOT = {{ has_variable = ac_story_cooldown }} }}
 random_events = {{ chance_to_happen = 5 {' '.join(f'10 = ashen_covenant.{s[0]}' for s in STORIES)} }}
}}''')
    write('main_menu/localization/english/ashen_covenant_l_english.yml', 'l_english:\n' + '\n'.join(' ' + k + ': "' + v.replace('"', '\\"') + '"' for k, v in text.items()))
    return {'version': '0.5.7', 'sites': len(SITES), 'site_importance': SITE_IMPORTANCE, 'aspects': len(ASPECTS), 'rites': len(RITES), 'covenant_rites': len(COVENANT_RITES), 'events': len(STORIES) + 1, 'files': paths, 'engine_tested': False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'build/religion-check')
    args = parser.parse_args()
    print(json.dumps(build(args.out), indent=2))
