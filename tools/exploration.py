"""Known Atlantic waters; foreign land is discovered by completed voyages."""
import re
import event_art

FIRST_OFFER_MONTHS = 36
STARTING_REGIONS = []
STARTING_SEA_AREAS = ['iberian_west_coast_area', 'bay_of_biscay_area',
                      'english_channel_area', 'nw_africa_coast_area', 'azores_sea_area']
# Known sea beside undiscovered land is the intended coastal-silhouette state.
# Never reveal mainland provinces/regions merely to expose their shorelines.
STARTING_PROVINCES = []


def starting_knowledge():
    return f"discovered_areas = {{ cm_cindermaw_area cm_ashborn_seas_area {' '.join(STARTING_SEA_AREAS)} }}"

# Bounded coastal pockets plus their nearby market centers. Revealing only a
# handful of ports leaves most useful coastline and foreign markets unknown.
ROUTES = {
    'east': {'cost':5,'months':4,'event':2,
             'areas':['iberian_west_coast_area'],
             'locations':['lisbon','porto','setubal','torres_vedras','alcacer_do_sal','viana_do_castelo'],
             'summary':'the Portuguese coast around Porto, Lisbon and Setubal, and its Atlantic approaches'},
    'north': {'cost':10,'months':6,'event':4,
              'areas':['iberian_west_coast_area','bay_of_biscay_area','english_channel_area','nw_africa_coast_area'],
              'locations':['brest','la_rochelle','bordeaux','plymouth','exeter','southampton','portsmouth','wight','dover','london',
                           'coruna','ferrol','cadiz','algeciras','gibraltar','tarifa','sevilla',
                           'tangier','ceuta','asilah','tetouan','larache','fez'],
              'summary':'pockets of southern Britain, the French Atlantic coast, Galicia and the Spanish straits, and northern Morocco; the markets at London, Bordeaux, Seville and Fez and the seas between these shores'},
    'south': {'cost':10,'months':6,'event':5,
              'areas':['nw_africa_coast_area','iberian_west_coast_area'],
              'locations':['cadiz','algeciras','gibraltar','tarifa','huelva','sevilla','tangier','ceuta','asilah','tetouan','larache','sale','fez','strait_of_gibraltar'],
              'summary':'the Spanish and Moroccan shores of the straits, the coast toward Huelva and Sale, the Seville and Fez markets, and their sea approaches'},
}


TEXT = {
    'goblins_exploration.6.title':'Strange Visitors on Our Shores',
    'goblins_exploration.6.desc':'Fishermen report that a strange little vessel put ashore along our coast. Its crew were unlike any people they had seen: short, ugly creatures with long pointed ears, sharp teeth and restless eyes. They picked through the shallows and argued in a rasping tongue, but the moment they realized they had been spotted, they scrambled aboard and fled out to sea.\n\nA scout ship followed at a cautious distance, keeping their patched sails just within sight. Beyond our familiar waters, the pursuit led to a cluster of smoke-wreathed islands, their coves crowded with crooked docks and more of the same vessels. Our scouts have returned with a chart of the crossing. Whatever these creatures may be, we now know where they live.',
    'goblins_exploration.6.a':'Mark the islands on our charts. Keep watch on the sea.',
    'goblins_exploration.1.title':'The Captains Look East',
    'goblins_exploration.1.desc':'Our rough charts trace the nearby waters, but the mainland beyond them remains unknown. After years of gathering provisions and seaworthy hulls, the crews are ready. A small expedition could cross the eastern waters, chart its harbors and learn who lives beyond them.',
    'goblins_exploration.1.east':'Provision a voyage east. The crew returns in four months.',
    'goblins_exploration.1.wait':'We need these provisions at home. Ask again in six months.',
    'goblins_exploration.2.title':'A Coast Beyond Counting',
    'goblins_exploration.2.desc':'Salt-stained charts cover the council table. Our crews have followed the Portuguese shore from fishing coves to the busy quays of Porto and Lisbon. Beyond the breakers they found people eager to bargain, and watchmen eager to send them away. A foreign sail followed the expedition home; our islands are no longer a secret.',
    'goblins_exploration.2.a':'Keep the charts dry. There will be more voyages.',
    'goblins_exploration.3.title':'The Captains Unroll Their Charts',
    'goblins_exploration.3.desc':'We have charted the first eastern harbors, but the shores farther north and south remain unexplored. Some crews favor the northern waters, others the warmer southern coast. Provisions for another expedition will cost ten gold, and the voyage will take six months.',
    'goblins_exploration.3.north':'Chart the northern coasts and the narrow sea beyond.',
    'goblins_exploration.3.south':'Follow the coast south toward the straits.',
    'goblins_exploration.3.wait':'Let the crews rest. Reconsider in six months.',
    'goblins_exploration.4.title':'Cold Seas and Foreign Harbors',
    'goblins_exploration.4.desc':'The returning ships wear a crust of salt and carry a hold full of stories. Our captains have sounded the cold harbors of Britain and followed the crowded French shore. In foreign taverns they bartered for charts of Spanish coves and the sunlit ports of Morocco. Dock by dock, the distant world takes shape on the council table. Ships can now seek those shores, and their rulers have heard of the Ashborn Isles.',
    'goblins_exploration.4.a':'Another stretch of the world has a name.',
    'goblins_exploration.5.title':'The Southern Straits',
    'goblins_exploration.5.desc':'Warm winds bring the southern expedition home. The crews speak of white walls above the straits, markets crowded with unfamiliar wares and watchtowers following every sail. Their charts trace the Spanish and Moroccan shores, opening new places to bargain and new waters to fear. The rulers they encountered now know where our islands lie.',
    'goblins_exploration.5.a':'The sea is wider than our old stories claimed.',
}

def build(b,game,out,validate_setup=True):
    # Runtime state and presentation live together; starting knowledge stays here.
    from exploration_progress import build_runtime
    names=b.parse_names(game);defs=b.read(game,'in_game/map_data/definitions.txt')
    for key in STARTING_REGIONS + STARTING_SEA_AREAS + STARTING_PROVINCES:
        b.block_span(defs,key)
    for route in ROUTES.values():
        for area in route['areas']:b.block_span(defs,area)
        for name in route['locations']:assert name in names,name
    tags=' '.join('tag = '+c['tag'] for c in b.CFG['countries'])
    build_runtime(b, out, tags, ROUTES, TEXT, FIRST_OFFER_MONTHS)
    # Runtime-only installer overlays do not contain generated starting setup.
    # Full builds always retain these starting-knowledge checks.
    if validate_setup:
        setup=(out/'main_menu/setup/start/10_countries.txt').read_text(encoding='utf-8-sig')
        for c in b.CFG['countries']:
            a,z=b.block_span(setup,c['tag']);country=setup[a:z]
            assert 'expl_western_europe' not in country
            assert starting_knowledge() in country
    # Mutual contact is limited to the owners of this voyage's named ports.
    return {'starting_knowledge':{'regions':STARTING_REGIONS,'sea_areas':STARTING_SEA_AREAS,
                                'coastal_provinces':STARTING_PROVINCES,'fog_of_war':'normal'},
            'countries':[c['tag'] for c in b.CFG['countries']],
            'first_offer_after_months':FIRST_OFFER_MONTHS,'routes':ROUTES,'reciprocal_discovery':True,
            'recipients':'current owners of visited locations; unowned sea locations skipped','runtime_verified':False}
