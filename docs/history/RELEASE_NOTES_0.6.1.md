# Goblins of the Ashborn Isles 0.6.1

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

Validation: complete static build, economy, geography, portrait assets and voyage scenarios passed. The city/wharf/seeded-trade follow-up passed clean-source reconstruction and isolated installation, with all 1,977 files matching the build. Gameplay acceptance pending.
