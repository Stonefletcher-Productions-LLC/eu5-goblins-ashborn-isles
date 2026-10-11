# Goblins of the Ashborn Isles 0.6.3

This staging build adds **Ashen Harbors** at peace and **Black Sails, Ashen Teeth** at war for all six goblin cultures. Automatic peace → war → peace is confirmed in Cindermaw. These are two short demo tracks; live multiplayer, non-goblin and music-off checks remain pending. The music change works with an existing save after restarting. It requires EU5 1.3.11's matching native music/Init banks and topbar GUI, checked by the installer; mods replacing those files may conflict. The published 0.6.3 release and Workshop have not been updated with this prototype.

Pending tooltip fix: the Moot of Six Fires rewards now display “The Local Covenants” and “The First Oathkeeper”. The three major Covenant rites also have proper modifier names and descriptions. Effects and saved modifier IDs are unchanged.

Pending introduction patch: all six goblin kingdoms receive the Ashborn introduction once on their monthly country pulse. Existing saves catch up; Cindermaw does not repeat its old introduction or starting units. This candidate is not the published 0.6.3 release.

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
