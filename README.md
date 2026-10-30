# Goblins of the Ashborn Isles

Working copy: `E:\Codex_EU5_Modding\goblins-ashborn-isles`. Repository: [GitHub](https://github.com/Stonefletcher-Productions-LLC/eu5-goblins-ashborn-isles) (Bitbucket was a temporary home from October 12 to 22; its history was rebuilt onto GitHub in PR #13).

**0.6.9 — Ready for EU5 1.4.**

- **Updated for EU5 1.4 (Across the Pillars).** The mod is rebuilt against EU5 1.4.6: the 1337 start setup, the map, the city and port positions and the institutions all follow the 1.4 files.
- **New island terrain method:** the Ashborn Isles are now a native 1.4 terrain layer added on top of the world. The installer no longer rewrites EU5's own terrain files.
- **Fixes the 0.6.8 breakage on 1.4:** the title screen no longer hangs, game sound works again, and the goblin nations load.
- **Goblin music rebuilt** for the 1.4 sound banks.
- **Goblin unit cards for 1.4's new unit types**, such as camelry, order knights, jinetes and ghulams.
- The mod is now listed as **[1.4] - Goblins of the Ashborn Isles**.

Built for **EU5 1.4**. It does not work on 1.3. Restart before playing and start a **new 1337 campaign**; 0.6.8 saves do not carry over. In multiplayer, every player needs the same version. Not yet tested in game. All 0.6.8 changes remain included.

**0.6.8 — Galleys, Warchiefs and sculpted goblin soldiers.**

- **Starting tech and ships:** goblin crowns start with Feudalism, so they get galleys, iron working and feudal advances from day one instead of only canoes. Two unique goblin ships join the fleet.
- **Sculpted goblin soldiers:** infantry use their own goblin body (big skull, long ears, tusks, clawed hands) with clan outfits, trousers, spaulders, belt knives and caps, still on EU5's native skeleton, animations and weapons.
- **Kingdom openings:** each crown gets its own opening event and painting after the shared Ashborn introduction.
- **Goblin Horde actions:** the Warchief can Call the Muster, Settle a Feud and Raise the Warchief's Levy. Smaller crowns can petition the Warchief for plunder, calm clans or a peace.
- **Shatterfin out-builds Giltfang** at the start, so it is set up to conquer it.
- **The Goblin Shore:** goblin crowns can settle on the mainland, and Europe pushes back.
- **More lore:** a southern voyage, reactions from Muslim courts, a Shatterfin–Giltfang rivalry, renamed estates, new name pools and country names.
- **Fixes from the 0.6.7 error log:** the Goblin Horde definition loads, a vanilla Venice event has its text back, Shatterfin buildings start within their max level, and fleets and battles sit inside the reshaped Atlantic sea zones.
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

![Goblins of the Ashborn Isles banner](art/workshop/0.6.0/banner.jpg)

[0.6.9 release notes](RELEASE_NOTES_0.6.9.md) | [Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3814944518)

Fire rose from the Atlantic. When the smoke cleared, goblin kingdoms stood among the new volcanic islands between the Azores and Portugal. Captains claimed sheltered harbors, smiths built their forges beneath black ridges, and rival houses began arguing over who should lead them.

**Goblins of the Ashborn Isles** adds a fantasy homeland to Europa Universalis V. Choose a crown, develop its economy, bargain with neighboring rulers, and decide whether the Isles will unite through conquest, submission or dynastic union. Beyond the familiar shoals lie foreign ports and the promise of an eastern foothold.

## Previous 0.6.3 — Construction economy and Jaimzha

Shatterfin's ruler is now **Jaimzha, the Mare-Mother**. Character IDs, family and succession stay intact.

Every crown now starts with masonry, glass, tools, cloth, leather, paper, pottery and naval-supply production. Masons increase from six to thirty levels: Cindermaw 8, Brackmaw 6, Shatterfin 5, Reefhook 3, Sootwake 3 and Giltfang 5. Glass guilds increase from five to thirteen levels, with at least one in every crown. Portugal's native start (1.18 million people, eight mason levels) provides a scale reference; the Isles' two-market geography and six independent builders require a larger construction buffer.

Reedfish and Tidefang supply sand; northern sand and selected stone districts receive more planned RGO capacity. Giltfang gains fiber farms, charcoal and a weapon guild to close missing workshop input chains. Surplus home-culture peasants fill added jobs, retaining each district's total population, minority/slave households, farming reserve and roughly 25% tribesmen. The Isles remain at 1,895,000 people.

The native base-recipe scenario leaves 9.3 masonry for southern construction and 1.9 in the north after modeled building upkeep, before population demand, construction, modifiers and actual hiring. These are planning quantities, not measured market balances. Every crown has positive modeled output after building inputs for essential manufactured goods; smaller crowns still use the shared market for raw materials. Actual market membership, supply, food, employment and profitability require playtesting.

**Start a new 1337 campaign. Version 0.6.3 includes the construction economy fixes and Jaimzha rename.**

## Previous 0.6.2 — Workers and Wildfang Clans

All six goblin kingdoms now start with the appropriate classes for their existing buildings. Each district has at least 125% of native building employment demand, plus a separate laborer reserve of 2,000 people and 1,000 per planned RGO expansion level. This reserve is a planning allowance; actual RGO capacity, hiring, goods access and profitability still require a fresh-campaign test.

Tribesmen make up approximately 25% of every district, including the cities. The total population is 1,895,000, slightly below 0.6.1's 1,923,313. Cindermaw falls from 730,688 to 620,000; Brackmaw rises to 420,000, Shatterfin to 280,000, Reefhook to 140,000, Sootwake to 130,000 and Giltfang to 305,000. Existing slave and minority households remain intact. Home-culture peasants are rebalanced into workers and tribesmen, with a separate farming/subsistence reserve and at least 70% home culture in every district. The tribal estate is **Wildfang Clans**, nobles are **Highfangs**, and the crown is **Ironfang Crown**, replacing Boss Clan.

A **new 1337 campaign is required**. Existing saves retain their populations. Population availability does not itself prove full employment or sufficient masonry output in game.

## Previous 0.6.1 — Starting economy, connected provinces and distinct goblins

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

## Previous release: 0.6.0

- **Giltfang, the sixth crown:** a northern realm with its own market, court, culture, lore, flag and opening artwork.
- **Lantern Cay and the Quiet Road:** a Cindermaw outpost and ordinary coastal passage connecting the northern and southern islands.
- **Two markets and mutual discovery:** Chainhaven joins Hooktooth as a market center; every goblin crown begins knowing the homeland and surrounding waters.
- **Clearer events:** shorter prompts, highlighted hover rewards, readable requirements and signed bargains explaining both partners' commitments.
- **A separate Ashborn Voyages situation**, 25-gold starting projects, clearer food-storage descriptions and corrected clan-flag assignments.

## An Atlantic homeland

![The nine Ashborn islands and their Atlantic placement](art/workshop/0.6.0/ashborn-map.png)

*Map diagram generated from the mod's geography, not an in-game screenshot.*

The Isles contain **117 locations in 43 provinces across 11 islands, with 91 ports** and about 2,750,000 people at the start, most of them tribesmen who settle into peasant life over the centuries. Volcanic highlands, marshes, woodland and fisheries give each crown a different base of resources and settlements.

Giltfang and its smaller companion, Tolltooth, lie north of Cindermaw. Together they are about 10% smaller than Brackmaw. Between north and south, Cindermaw's new **Lantern Cay** adds Lantern Haven, Wickwood and Emberwatch. The Quiet Road provides a connected route through ordinary coastal water, with the lower eastern approach opened and selected current tiles reworked.

## Choose your crown

Every crown has its own culture, ruling household, introduction and three starting projects. All six participate in shared diplomacy, religion, exploration and unification.

**Cindermaw — Emberblood.** Drogg, the Stone Fletcher, rules the largest realm from Hooktooth. Forges, muster yards and volcanic defenses support his ambition to lead the Isles.

**Brackmaw — Brineward.** Murgash, the Sluice-King, builds influence through provisions, waterways and remembered debts. Marsh engineers and harbor workshops sustain Brackhaven's rival crown.

**Reefhook — Reefstrider.** Skrezz, the Wreck-Taker, rules among pilots, fishing households and pearl divers. Rescue obligations, salvage claims and foreign friendships all compete for his attention.

**Shatterfin — Stormfang.** Jaimzha, the Mare-Mother, leads the Tidemothers from Shatter Maw, the largest goblin realm, spread across Shatterfin, Knifeback and Maw Rock. Her court bargains for security while preserving its maternal royal house and succession.

**Sootwake — Ashveil.** Snikh, the Blackbough, guards the woodland paths and charcoal hearths that sustain his smaller realm. Independence rests on the groves as much as the crown.

![Vrekk the Brass-Tooth and the Giltfang court](art/workshop/0.6.0/giltfang.jpg)

**Giltfang — Cinderweight.** Vrekk, the Brass-Tooth, turned salvage disputes and trusted copper weights into harbor fees, armed crews and a crown. Copper workings and salt pans supply Chainhaven's market, while Tolltooth's lamps guard the approach. His projects support honest weights, harbor envoys or a supplied watch.

The clans share an Ashborn identity, with distinct names, dynasties, courts and original artwork. Read the [lore and royal-family stories](LORE.md) for their origins and rivalries.

## Gather the crowns

![Six envoys meet at the Gathering](art/workshop/0.6.0/gathering.jpg)

The Gathering turns the homeland into a shared contest for leadership. Build alliances, offer paid aid, negotiate submission and Compact charters, or press your claims through normal EU5 warfare. Other crowns can refuse; an offer is not a guaranteed treaty.

Unification requires all **117 homeland locations** within your realm through direct ownership, qualifying vassals or senior unions. Alliances and temporary wartime occupation do not unite the Isles. The situation panel shows the founding crowns and progress toward that goal.

## Harbors, provisions and promises

![A Harbor Bargain signed between goblin rulers](art/workshop/0.6.0/harbor-bargain.jpg)

Harbor Bargains let independent crowns negotiate provisions or pilot services for five years. Payment happens when the agreement is signed. A counteroffer can change the service and price, and each partner receives a receipt explaining the benefit, burden and duration.

Hooktooth, Chainhaven and Shatter Maw begin as three separate markets, linked by seeded trade routes in fish, grain, livestock, salt, silver and lumber. Fisheries, mines, woodland crafts and urban workshops give the islands different economic foundations; actual trade and profitability depend on EU5's market systems and the course of your campaign.

Each crown starts with **100 gold**. Its three opening projects cost **25 gold** each. Food bonuses raise the **province food storage limit**, not monthly production: hover the province food display and then the stockpile total to inspect capacity and its modifiers.

## Chart the foreign shores

![Ashborn captains examine charts before a voyage](art/workshop/0.6.0/voyages.jpg)

The separate **Ashborn Voyages** situation tracks preparation, a route at sea, returning crews, rest and completed charts. Fund expeditions toward Iberia, northern waters or northwest Africa. The first offer follows 36 months of preparation; voyages cost gold and take time.

You can request a later reminder or commission available routes manually. Returning crews reveal limited coastal destinations, and reciprocal contact lets the countries they visit learn about the Isles. Foreign land is not all revealed at the start.

## The Eastern Hunger and the Ashen Covenant

![Goblin captains look toward the eastern coast](art/workshop/0.6.0/eastern-hunger.jpg)

Once the homeland is united, the **Eastern Hunger** turns attention toward a European coastal foothold. Prepare your fleet and select an eligible objective, then pursue it through normal declarations of war and peace settlements. You must build the forces and win the land yourself.

At home, the **Ashen Covenant** provides twelve sacred sites, traditions, rites, Favor and religious stories. Its choices sit alongside clan politics and the demands of the ruling household. Earlier portrait, skin, hairstyle, Drogg, wardrobe and holy-site fixes remain included.

## Install and continue

Built for **EU5 1.4**. Start a **new 1337 campaign**; saves from 0.6.8 and EU5 1.3 do not carry over.

- Subscribe through the Workshop, or download **Goblins_Ashborn_Isles_0.6.9.zip** from the release above, extract it and run **Install-Goblins.cmd** with EU5 closed.
- Enable only one Goblins copy and disable the old Gathering Prototype add-on. Restart before playing.
- Existing 0.6.0 saves can receive the clan-flag repair after restart and the next monthly pulse; that repair alone needs no new campaign.
- Other map, terrain and starting-world mods may conflict. Keep separate saves.

## Checks and feedback

The five-track candidate passed native audio-route preservation, playlist/media checks and clean-source installer verification. The 0.6.4 release package receives its own clean install check; see the [release receipt](reports/release-064-install.json). Economy checks from 0.6.3 remain applicable to the unchanged world configuration. Actual employment, trade and profitability still require gameplay checks.

Development packaging creates the player installer by default. Use `python tools/package.py --source` only when a separate source ZIP is needed; GitHub already supplies source downloads. Reuse verified build stages and keep one current clean-test workspace.

The complete 0.6.1 static build, economy, connected-province, portrait asset and voyage script checks have passed. The city/wharf/seeded-trade follow-up passed full static validation, clean-source reconstruction and isolated installation; all 1,977 delivered files matched the build. These checks are separate from in-game confirmation of production, trade, UI rendering, portraits and save behavior. Multiplayer and achievements are unverified; dedicated foreign invasion ambitions and fear mechanics are not included.

[Report a problem](https://steamcommunity.com/sharedfiles/filedetails/?id=3814944518) in the Workshop comments with your version, clan, enabled mods and steps to reproduce it. Screenshots and relevant saves help. See the [release history](RELEASE_NOTES.md) and [playtest checklist](TESTING.md) for more detail.

## Credits

Original setting and development by Stonefletcher. Base goblin infantry model: Quaternius, Ultimate Animated Character Pack (CC0). Music was generated with ElevenLabs Music v2 and local ACE-Step 1.5 (MIT). Paintings, banner and thumbnail use AI-generated artwork; map diagrams use the mod's generated geography. Europa Universalis V and its original assets belong to Paradox Interactive. This is an unofficial mod.
