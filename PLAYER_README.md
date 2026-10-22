# Goblins of the Ashborn Isles 0.6.8

**0.6.8 — Galleys, Warchiefs and sculpted goblin soldiers.**

- **Starting tech and ships:** goblin crowns start with Feudalism, so they get galleys, iron working and feudal advances from day one instead of only canoes. Two unique goblin ships join the fleet.
- **Sculpted goblin soldiers:** infantry use their own goblin body (big skull, long ears, tusks, clawed hands) with clan outfits and caps, still on EU5's native skeleton, animations and weapons.
- **Kingdom openings:** each crown gets its own opening event and painting after the shared Ashborn introduction.
- **Goblin Horde actions:** the Warchief can Call the Muster, Settle a Feud and Raise the Warchief's Levy. Smaller crowns can petition the Warchief for plunder, calm clans or a peace.
- **Shatterfin out-builds Giltfang** at the start, so it is set up to conquer it.
- **More lore:** a southern voyage, reactions from Muslim courts, a Shatterfin–Giltfang rivalry, renamed estates, new name pools and country names.
- **New art:** Covenant story paintings, redone event paintings and goblin art for cavalry, artillery and auxiliary unit cards.

Built for **EU5 1.3.11**. Restart before playing. Start a **new 1337 campaign** for the starting tech and Shatterfin changes. In multiplayer, every player needs the same version. Not yet tested in game. All 0.6.7 changes remain included.

## 0.6.7 — Shatter Maw moves, the goblin realms band together

- **Shatter Maw** moves north-west into the open water west of Giltfang and grows into the largest goblin realm: a much bigger main island, a larger Knifeback, the new Maw Rock and 23 locations, so Shatterfin can take on Giltfang. Cindermaw gains **Cinderstep**, a small volcanic island with fish, iron and stone. The map now has 11 islands, 43 provinces and 117 locations, with rugged coastlines, new rivers and new sea zones.
- **Start-game balance:** many more goblins (2.75M, mostly tribesmen who promote over time), a thinner early economy, enough food in every crown and four more starting trade routes.
- **The Goblin Horde:** every goblin crown joins one international organization with an elected Warchief. Goblins may fight each other, but when an outsider attacks one crown, the others join the defence (**Ashen Kinship**).
- **Pact Ladder:** peaceful unification is a visible three-step path, Harbor Bargain, Sworn Pact, then Compact.
- **Covenant rites:** the Ashen Covenant's rites appear in the Religion panel, with four shared rites, one clan rite per culture and a standing Moot.
- **The Old World Reacts:** Portugal and the Catholic courts respond to goblin first contact with five new events.
- **Lore pass:** event and localisation text reviewed and rewritten.
- **Bigger courts:** five noble houses, three Oathkeepers and three guild masters per crown, about 40 more characters each.

Built for **EU5 1.3.11**. Restart before playing. This version needs a **new 1337 campaign**: the map changed. In multiplayer, every player needs the same version. Not yet tested in game. All 0.6.6 changes remain included.

## 0.6.6 — Royal households, goblin soldiers and goblin towns

- **Royal families:** every goblin crown starts with a large household: brothers, uncles, cousins, three wives for the ruler and five or six sons, so Rule of the Strongest no longer runs out of heirs. The Ashen Covenant allows up to four wives. 153 authored goblin characters (was 51).
- **Obsidian Fletchers:** a goblin unique archer levy, raised from peasants in goblin-majority locations. It upgrades to Blackglass Crossbows in Age 2.
- **Goblin towns:** goblin cultures get their own city set of shacks, shanty towers, a chieftain's hall and palisades. Ports, later forts and workshops use the native wooden set.
- **Goblin infantry** now use EU5's own soldier rig, gear and animations, with a goblin head for each clan, goblin caps instead of human helmets and about 62% human height. Cavalry, artillery and ships still use human models, and hands keep the human skin tone.
- **Silver Shard** joins Shatterfin province, so it shares food and stops starving.
- **Netjaw** produces livestock instead of fish. It is inland and has no water to fish in.

Built for **EU5 1.3.11**. Restart before playing. The royal families, Silver Shard and Netjaw changes need a **new 1337 campaign**; existing 0.6.5 saves keep loading. In multiplayer, every player needs the same version. Engine-untested: the multi-wife setup, the soldier models and city set in game and AI marriage behaviour. All 0.6.5 fixes remain included.

## 0.6.5 — Buildable timber in Blackwood and Giltfang

- **Ironbark, Pitchfang and Emberhollow** now produce **lumber**. They were set to tar, which has no raw-material production in EU5 1.3.11, so their RGOs could not be built up and the game logged missing `rgo_workers:tar` and `raw_resource:tar` entries. All three are wooded hills; their populations, buildings and charcoal makers are unchanged.
- The build checks no longer accept tar as a raw material, and the release check now confirms every goblin location's packaged raw material.

Built for **EU5 1.3.11**. Restart before playing. The fix applies to a **new 1337 campaign**: existing 0.6.4 and 0.6.4.1 saves keep loading, but those three locations stay on tar there. In multiplayer, every player needs the same version. All 0.6.4.1 fixes remain included.

## 0.6.4.1 — Load-error fixes and restored Workshop art

- **Goblin hairstyles:** women and children now pick their curated styles from the game's own per-portrait hair lists. 0.6.4 logged 15 "Both value and accessory are set" warnings and 9 "Can't find accessory" errors at startup from these modifiers. Men keep their named styles. Women's and children's styles still need an in-game portrait check.
- **Ports:** `ports.csv` now matches the game's native format. The 0.6.4 file ended with an empty row that EU5 logged as an unknown location with an empty name. All 75 goblin ports are unchanged.
- **Missing-mod crash:** loading a goblin save while this mod is not enabled crashes EU5. If the game warns that **Goblins of the Ashborn Isles** is missing when you load a save, cancel, enable the mod in your playset and restart. Enable only one Goblins copy.
- **Workshop page:** description artwork is now hosted on Steam; the old GitHub links are retired.
- The installer accepts four-part version numbers.

Built for **EU5 1.3.11**. Restart before playing. Existing 0.6.4 saves can continue: no starting-world changes. All 0.6.4 music, divorce and event changes remain included.

## 0.6.4 — Goblin music, royal divorce and clearer events

Two peace tracks and three war tracks now rotate for all six goblin primary cultures. Peace: **Ashen Harbors** and **Six Clans, One Fire**. War: **Black Sails, Ashen Teeth**, **Hooks and Gold**, and **Drums Beneath the Volcano**. The local player's diplomacy state controls switching; native music routes are preserved for non-goblin cultures. Automatic peace → war → peace was confirmed in Cindermaw with the original two tracks. The expanded rotation, non-goblin listening, music controls and multiplayer remain unverified. Other music drafts are excluded and generation is paused.

**Dissolve a Royal Marriage** lets a goblin ruler divorce a living spouse for a base **10 gold**, unaffected by inflation, with no stability penalty. Junior union partners cannot divorce their shared ruler; AI and player automation do not initiate this action.

Every goblin kingdom receives the Ashborn introduction once, including existing saves catching up. Cindermaw retains its exclusive starting units and does not repeat its old introduction. Covenant unification rewards and major rites display proper modifier names. Hovering “Charts, provisions, then a harbor.” explains the informational event and the paid exploration/foothold steps; it grants no immediate reward or land.

Built for **EU5 1.3.11**. Restart before playing. Existing 0.6.3 saves can use these additions; earlier starting-world changes still require a new 1337 campaign. Other mods replacing the native music bank, Init bank or in-game topbar may conflict. [Music details](art/music/README.md).

## 0.6.3 — Construction economy and Jaimzha

Shatterfin's ruler is now **Jaimzha, the Mare-Mother**. Character IDs, family and succession stay intact.

Every crown now starts with masonry, glass, tools, cloth, leather, paper, pottery and naval-supply production. Masons increase from six to thirty levels: Cindermaw 8, Brackmaw 6, Shatterfin 5, Reefhook 3, Sootwake 3 and Giltfang 5. Glass guilds increase from five to thirteen levels, with at least one in every crown. Portugal's native start (1.18 million people, eight mason levels) provides a scale reference; the Isles' two-market geography and six independent builders require a larger construction buffer.

Reedfish and Tidefang supply sand; northern sand and selected stone districts receive more planned RGO capacity. Giltfang gains fiber farms, charcoal and a weapon guild to close missing workshop input chains. Surplus home-culture peasants fill added jobs, retaining each district's total population, minority/slave households, farming reserve and roughly 25% tribesmen. The Isles remain at 1,895,000 people.

The native base-recipe scenario leaves 9.3 masonry for southern construction and 1.9 in the north after modeled building upkeep, before population demand, construction, modifiers and actual hiring. These are planning quantities, not measured market balances. Every crown has positive modeled output after building inputs for essential manufactured goods; smaller crowns still use the shared market for raw materials. Actual market membership, supply, food, employment and profitability require playtesting.

**Start a new 1337 campaign. Version 0.6.3 includes the construction economy fixes and Jaimzha rename.**

## Previous 0.6.2 — Workers and Wildfang Clans

All six goblin kingdoms now start with the appropriate classes for their existing buildings. Each district has at least 125% of native building employment demand, plus a separate laborer reserve of 2,000 people and 1,000 per planned RGO expansion level. This reserve is a planning allowance; actual RGO capacity, hiring, goods access and profitability still require a fresh-campaign test.

Tribesmen make up approximately 25% of every district, including the cities. The total population is 1,895,000, slightly below 0.6.1's 1,923,313. Cindermaw falls from 730,688 to 620,000; Brackmaw rises to 420,000, Shatterfin to 280,000, Reefhook to 140,000, Sootwake to 130,000 and Giltfang to 305,000. Existing slave and minority households remain intact. Home-culture peasants are rebalanced into workers and tribesmen, with a separate farming/subsistence reserve and at least 70% home culture in every district. The tribal estate is **Wildfang Clans**, nobles are **Highfangs**, and the crown is **Ironfang Crown**, replacing Boss Clan.

A **new 1337 campaign is required**. Existing saves retain their populations. Population availability does not itself prove full employment or sufficient masonry output in game.


## 0.6.1 — Starting economy, connected provinces and distinct goblins

- All six crowns start with State Piracy selected and permanently unlocked through the native policy-unlock flag. The policy remains changeable; no later-age advance is granted.
- Starting stability is 50, legitimacy is 75 and prestige is 25.
- Hooktooth and Brackhaven start with a staffed sergeantry. Ironfang Monarchy grants +50% Manpower, increasing monthly manpower gain through the native `global_manpower_modifier`.
- Hooktooth and Chainhaven each receive two glass guilds, local sand supplies and two nearby mason levels. Supporting tools, leather, paper, jewelry and northern cloth production supply the workshops and marketplaces. Chainhaven gains a wharf and northern tar/silver resources support its production chains.
- Province assignments follow real shared land borders across all nine islands, including Smokehorn, Scorchbrook, the disconnected outer provinces and Giltfang. District shapes and country ownership are unchanged.
- Lantern Haven becomes a town with a marketplace, wharf and granary, keeping its fish resource and existing population.
- All ten coastal goblin towns/cities have one wharf. Netjaw is inland, so its invalid wharf is removed; Copperfang and Rustpeak also remain inland. Brackhaven is promoted to a city.
- Starting trade is explicitly seeded: Cindermaw imports silver from Chainhaven into Hooktooth; Giltfang imports lumber from Hooktooth into Chainhaven. Each requests one merchant-capacity unit and is locked against automatic cancellation, while remaining player-editable. Startup checks require a merchant, available capacity and a route; a bounded monthly retry covers initialization delays through November 1338. Completed routes are never recreated after cancellation.
- Additional towns: Copperfang and Netjaw (Cindermaw), Rustpeak and Bracknet (Brackmaw), Knifeback on Shatterfin's smaller island, and Tolltooth. Brackhaven, Shatterfin and Chainhaven become cities. Nearby rural households relocate into the expanded settlements; urban class mixes and production buildings change while each kingdom's total population stays constant.
- Covenant Favor is shown as a live value in the Gathering and Eastern Hunger panels, with an explanation of its religious-influence resource and rite costs. The native Religion panel retains the detailed resource tooltip.
- Adult male goblins draw from four distinct facial profiles, in addition to their existing hair choices. Drogg has a heavier brow, stronger jaw, leaner cheeks, prominent battle scar and a dedicated bear-hunter outfit.
- Cold Seas and Foreign Harbors uses story prose followed by a clear discovery summary. Voyages reveal bounded coastal pockets and market centers; the northern return charts southern Britain, Atlantic France, parts of Spain and northern Morocco, including London, Bordeaux, Seville and Fez. Most inland territory stays unknown.

**New 1337 campaign required** for the starting stats, policy, production, town and province assignments. Existing saves retain their saved starting world. Portrait/UI rendering, actual market membership, production ramp-up and profitable trades require in-game acceptance.

Goods move within a market through market access; this does not create an inter-market trade route. Between Hooktooth and Chainhaven, native country/burgher trade still depends on access, demand, prices, transport cost and available merchant capacity. The setup supplies production, merchant infrastructure and the two seeded routes. Goods inside Hooktooth are allocated by market access; a same-market trade route is rejected by the native trade action. Profitability, actual market membership and route activity must be checked in game.

## Installation

Built for EU5 1.3.11. Extract the entire package, close EU5, and run Install-Goblins.cmd. Enable only one Goblins copy. Start a new 1337 campaign.

If EU5 says **Goblins of the Ashborn Isles** is missing when you load a save, cancel the load. Enable the mod in your playset and restart EU5 first; continuing without it crashes the game.
