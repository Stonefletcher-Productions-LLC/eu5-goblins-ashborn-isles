# 0.6.7 noble houses acceptance

New 1337 campaign. In each goblin crown: the cabinet picker lists several Highfang nobles, Oathkeepers and guild masters; the court/marriage view shows unmarried noble sons and daughters; noble heads appear in their dynasty trees (e.g. Ashjaw, Ironbite in Cindermaw). No `05_characters.txt` errors in `error.log`.

# Development: goblin soldiers on the native unit rig

1. Install from main and restart EU5. Start a new 1337 campaign as any goblin clan.
2. Recruit light and heavy infantry for at least two clans. Check that you see native clothing, armour, weapons and animations with a green goblin head in the clan colour. The head should be large, with long ears and no hair or beard. Some soldiers wear goblin leather or iron caps (no native helmets). The whole soldier should be about 62% the size of a human soldier standing next to it.
3. Zoom in on idle, march, combat and retreat. Look for heads floating off the neck, the neck gaps, caps clipping the skull or ears, weapons or shields clipping the larger head, and units sinking into or floating above the ground.
4. Check one human country's infantry for regressions.
5. Search a fresh `error.log` for `cm_goblin_`, `Invalid entity graph`, `texture variation` and `Could not find`. Send a screenshot if anything looks off.

# 0.6.6 royal families acceptance

New 1337 campaign, fresh `logs/error.log`.

- Each captain crown's ruler shows three wives and five or six sons; brothers, an uncle and cousins appear in the dynasty tree. Shatterfin shows Jaimzha's sister, daughters and granddaughters.
- The heir is unchanged: the eldest son in Cindermaw, Brackmaw and Giltfang, the ruler's brother Krizzek/Zhor in Reefhook/Sootwake, Skritcha in Shatterfin.
- The marriage law tooltip or ruler panel allows four wives under the Ashen Covenant; arrange a fourth marriage for a goblin ruler.
- No `05_characters.txt` or `04_dynasties.txt` errors in the log. Observe 30+ years: the ruling dynasty survives at least one succession.

# 0.6.6 acceptance: Obsidian Fletchers

- As any goblin crown, open levies in a goblin-majority location: **Obsidian Fletchers** are offered, with the name and description shown, not raw keys.
- As Portugal or Castile, they are not offered in their own lands. Whoever owns a goblin-majority location can raise them there (by design, like vanilla Schiltrons).
- Raise one and check the unit panel: initiative and damage bonuses, hills and mountains combat bonus, goblin infantry card art and goblin 3D soldiers.
- After the Renaissance age starts, they upgrade to **Blackglass Crossbows**.
- Fresh `logs/error.log`: no lines mentioning `a_ga_obsidian_fletchers`, `a_ga_blackglass_crossbows` or `ga_obsidian_fletchers_location_trigger`.
- Load a 0.6.5 save: it loads and the levy appears there too.

# Goblin city buildings acceptance

- Start a new 1337 campaign and zoom into Hooktooth (city) and a few goblin towns and villages. Houses should be goblin shacks, stacked shanty towers and the chieftain's hall, not European half-timbered houses.
- Check scale against a neighbouring vanilla town: shacks should read as slightly smaller and messier, not as tiny specks or giants.
- Check that buildings sit on the ground on hills (no floating or buried shacks) and that textures are not pink, black or missing.
- Build a stockade or fort in a goblin location: it should show the stake palisade with gate towers.
- error.log: no lines mentioning `cm_goblin_`, `ashborn_goblins` or `cm_ashborn_goblins.txt`.

# 0.6.5 acceptance

Restart EU5 with only one Goblins copy enabled and start a **new 1337 campaign**.

- Ironbark, Pitchfang and Emberhollow show **lumber** as their raw material, and their RGO can be expanded.
- Fresh `logs/error.log`: no `Could not find NamedIndex 'rgo_workers:tar'`, `'raw_resource:tar'` or `'is_under_construction:tar'` lines.
- Load a 0.6.4.1 save after restarting: it loads; those three locations still show tar there (expected).
- Multiplayer: host and client both on 0.6.5 (same checksum in the lobby).

# 0.6.4.1 acceptance

Restart EU5 with only one Goblins copy enabled. Confirm the applied playset and fresh logs before judging results.

- Fresh `logs/error.log`: no `Both value and accessory are set` or `Can't find accessory` lines for `zzz_ashborn_outfits.txt`, and no `map.cpp` line `Unknown reference to location! Key: '`.
- Portraits: compare adult goblin women and girls/boys across several clans with the curated lists in `tools/build_goblin_outfits.py`: women syrian braid, german braid, iroquois parted, aztec horn braid, short afro; girls long basic or short afro; boys short, bob or curly. Men keep their named styles. Check a human control.
- Ports: dock and embark at Hooktooth, Chainhaven and Lantern Cay; confirm the port count is unchanged.
- Load a 0.6.4 save after restarting. Separately, load a goblin save with the mod disabled and confirm EU5 shows the missing-mod warning (cancel, do not continue).

# Goblin dynamic music acceptance

On October 11, 2026, the user confirmed automatic **Ashen Harbors at peace → Black Sails, Ashen Teeth at war → Ashen Harbors after peace** in the isolated Cindermaw test using the custom local audio state. Earlier candidates relying on native PlayerAtWar audio state are superseded: that value remained at war after the campaign returned to peace.

The accepted design reads the local player's actual diplomacy state through invisible in-game GUI widgets and posts custom audio-state events. Only goblin bank routes consume the custom state; no synchronized campaign variable or host-only pulse drives music. This is a multiplayer-compatible design intention, not completed multiplayer acceptance. The 0.6.4 library has two peace tracks and three war tracks, totaling 7 minutes 30 seconds. Verify complete rotation within each mood, then a second cycle; the original listening confirmation does not cover the expanded playlists.

Before accepting a packaged candidate, confirm its applied playset and installed bank/GUI hashes. A saved playset or successful launch command alone does not prove the mod loaded. Use listening confirmation; a native track title or advancing music UI is not evidence of the intended audio.

Remaining runtime checks:

- Repeat peace → war → peace across the six goblin primary cultures, including formed goblin countries. End every simultaneous war before expecting peace music; verify subsequent wars switch again.
- Start or load a campaign already at war, and load a peaceful save. Confirm correct initial music without manual track selection, including when the game remains paused. Repeat save/reload after a transition.
- Test Portugal or another non-goblin control at peace and war. It must retain native music. Switch the local country between goblin and non-goblin countries and verify correct routing without leftover custom music.
- Run two actual multiplayer clients with different local countries and war states: goblin at peace versus goblin at war, then goblin versus non-goblin. Each must hear its own appropriate music. Test a joining/rejoining client and save/reload; do not infer success from static route combinations.
- Verify music off remains silent, restore music, and exercise pause/resume, next track, volume and manual selection. Check returning to the menu and entering another campaign.
- Inspect fresh logs for missing audio events, unknown custom states, GUI binding errors or bank-load errors. Confirm the installer carries the matching music bank, Init registration, catalogue, culture definitions and topbar watcher.

# 0.6.2 construction economy playtest

Start fresh campaigns for all six crowns. Record at pause, months 1, 3 and 12:

- Verify Jaimzha in Shatterfin's court, events and ruler tooltip; Skritcha remains the initial successor.
- Check each capital's masons, glass, tools, paper, leather, cloth and pottery guilds. Record employment, production method, input shortages and profit. Native startup ramping may delay output even when workers exist.
- Inspect Hooktooth and Chainhaven membership and access. In each crown, queue one guild (0.5 native masonry demand) and check progress without a persistent construction shortage. Verify Shatterfin has five mason levels across its capital and Shardpoint.
- Check sand from Clayjaw, Reedfish, Tidefang and Lockshore, stone supply and first-month RGO investment. Check Giltfang's fiber farms and charcoal supply, and its wool/silver production methods.
- Record treasury balance, building subsidies, province food balance, unrest and migration before and after a year. Keep populations at the documented totals and Wildfang Clans near 25%; do not mistake a static recipe surplus for proven profitability.

Static checks use full staffing and one explicitly listed native base recipe per building. They exclude population consumption, RGO quantities, construction, prices, modifiers, startup ramp and trade. Actual market membership is not forced. The candidate has not been run in EU5.

# 0.6.1 gameplay acceptance

## 0.6.2 — Workers and Wildfang Clans

All six goblin kingdoms now start with the appropriate classes for their existing buildings. Each district has at least 125% of native building employment demand, plus a separate laborer reserve of 2,000 people and 1,000 per planned RGO expansion level. This reserve is a planning allowance; actual RGO capacity, hiring, goods access and profitability still require a fresh-campaign test.

Tribesmen make up approximately 25% of every district, including the cities. The total population is 1,895,000, slightly below 0.6.1's 1,923,313. Cindermaw falls from 730,688 to 620,000; Brackmaw rises to 420,000, Shatterfin to 280,000, Reefhook to 140,000, Sootwake to 130,000 and Giltfang to 305,000. Existing slave and minority households remain intact. Home-culture peasants are rebalanced into workers and tribesmen, with a separate farming/subsistence reserve and at least 70% home culture in every district. The tribal estate is **Wildfang Clans**, nobles are **Highfangs**, and the crown is **Ironfang Crown**, replacing Boss Clan.

A **new 1337 campaign is required**. Existing saves retain their populations. Population availability does not itself prove full employment or sufficient masonry output in game.


Start a NEW 1337 campaign after restarting with only this Goblins copy enabled.

1. Check each crown: stability 50, legitimacy 75, prestige 25, State Piracy selected and available to reselect after changing policy.
2. Inspect province mode: every province is connected by land within its island. Check Smokehorn, Scorchbrook, Blackwood Outer, Crown Outer, Brinewood Outer, Rustpeak Outer, Brackhaven and Giltfang.
3. Confirm Lantern Haven, Copperfang, Netjaw, Rustpeak, Bracknet, Knifeback and Tolltooth are towns; Brackhaven, Shatterfin and Chainhaven are cities. Inspect their population classes and staffed buildings. Country population totals should remain unchanged.
4. Inspect both markets at start and after monthly production updates: sand, glass, masonry, tools and marketplace input supply; check actual market membership, staffing and production methods.
5. Inspect starting silver imports into Hooktooth (Cindermaw) and lumber imports into Chainhaven (Giltfang): one merchant-capacity unit requested each, locked. If initialization delays creation, check the first monthly update. Cancel a seeded route, save/reload and advance a month: it must stay cancelled. Verify all ten coastal urban locations have one wharf and Netjaw has none; no invalid-wharf errors should appear. Inspect market access and local goods allocation inside Hooktooth; these do not create same-market route entries. Burgher activity and profitable volume remain engine checks.
6. Open the Gathering and Eastern Hunger panels: Covenant Favor displays the current religious-influence value; spending on a rite changes it. Check the Religion panel tooltip.
7. Compare several adult males and Drogg, plus human and child controls. Check clothing, scar, hair, facial animation and save/reload stability.

8. Check Hooktooth and Brackhaven: one sergeantry each with soldier staffing. Hover Manpower and confirm Ironfang Monarchy contributes +50% to monthly gain. Removing the reform should remove its contribution.

9. Complete all three voyages, including Cold Seas and Foreign Harbors. Read the flavor and discovery summary, then inspect revealed coastal pockets in Britain, Spain and Morocco and the London, Bordeaux, Seville and Fez markets. Confirm sea approaches, reciprocal contact, no extra fee and no repeated voyage reward after save/reload. Check trade availability and profitability separately.

Static validation and installer verification do not substitute for these gameplay checks.

# 0.6.0 acceptance

- Clan flag repair: start as Giltfang and confirm a brass fang with chain links on dark blue instead of the yellow/blue procedural flag. Check all six authored clan emblems. Load a pre-fix 0.6.0 save, advance to the next monthly pulse, and confirm the same repair occurs once. Later intentional flag changes must not be reset by subsequent pulses. This visual check is still pending.

- Quiet Road: sail from Chainhaven to Cindermaw using only ordinary coastal tiles, with a stop at Lantern Haven. Check both sides of the new island and the lower eastern gate. Confirm all three Lantern Cay districts start owned, controlled and cored by Cindermaw, share starting discovery, and count toward unification. Verify the three trimmed current tiles remain connected and navigable.
- Northern world: start a NEW campaign as Giltfang and each older crown. Confirm mutual discovery of all 97 districts and coastal sea tiles, separate Chainhaven and Hooktooth markets, and 100 gold. Sail and transport between Chainhaven, Tolltooth, every older island and native coastal waters. Inspect coastlines, ports, rivers and sea-zone borders at several zoom levels.
- Trade: advance the two markets through several monthly updates. Inspect market membership, goods shortages/surpluses, merchant capacity and actual import/export routes. Static registration and connected seas do not prove profitable or automatic trade.
- UI cleanup: hover provisions/pilots target selections and all eighteen project options. Confirm bounded descriptions, highlighted native cost/reward previews, short buttons, readable disabled requirements and intact punctuation. Sign both services at 10 gold and counteroffers at 15; inspect both signatories' receipt terms.
- Combined-candidate regression: compare ear/face colour across all clans, both sexes and children; check Drogg, hair and clothing. Confirm twelve holy sites with varied importance, six founding-crown standings (including annexation/restoration and both Compact types), and a separate Ashborn Voyages situation. Recheck all newer diplomacy/story/project features. Engine visual acceptance remains pending.
- Food rewards: Brackmaw sluices, Sootwake stores, provisions bargains and food-related Covenant choices must explain province storage. Open a location, hover the province food display, then hover its stockpile total: confirm the capacity modifier breakdown reflects the active reward. Food currently stored and monthly production receive no direct grant.
- Starting treasury: start a fresh campaign as each of the six clans and confirm 100 gold before purchases or time advances. Opening projects cost 25 gold, AI retains 20, and exploration still costs 5/10/10. Existing saves should receive no treasury grant.
- Exploration: check the dedicated Ashborn Voyages situation, Review Ashborn Voyages, every status and remaining-time range; six-month reminders, stopped reminders/manual reopening, 36-month first offer and 12-month rest. Verify 5/10/10-gold boundaries, 4/6/6-month voyages, no overlapping purchases, unchanged coastal-only discovery, arrival-owner reports after conquest and one contact notice per foreign country. Test real save/reload at offer, departure and arrival; upgrade older pending offers, queued voyages and already-open returns. Confirm report dismissal adds no reward and no monthly progress popups occur.
- Covenant stories: exercise both approaches and neutral defer in all twelve stories. Verify five-gold and three-Favor boundaries, AI twenty-gold reserve, three-year effects, replacement of prior story consequences, no prestige and no penalty for defer. Test conversion, loss of site/aspect eligibility, duplicate/stale replies, existing pending events and save/reload. Confirm three-year cooldown, unchanged frequency and untouched major rites/Moot. Inspect option tooltips, estate effects and fresh logs.
- Early clan projects: test all eighteen project choices across the six clans. Every introduction must show three project alternatives and one free decline when funds allow. Check exact 25-gold affordability, five-year modifiers, free decline, no repeat purchase and the AI 20-gold reserve. Verify Shatterfin succession and its existing follow-up remain unchanged. Already-seen introductions must not replay; existing accounts bonuses must keep their original strength and expiry. Check save/reload and UI wording in the game.
- Situation progress: inspect both panels at normal and enlarged UI scales. Check the live homeland count after annexation, loss/release of subjects, Compact ratification and save/reload. It must reach 97 exactly when the player meets unification requirements. In Open Compact Talks, inspect independent, dependent and at-war crowns; unmet requirements must be readable while the crowns remain disabled. Verify annexed/self entries are absent, AI still rejects ineligible targets, and event/panel opening frame times remain acceptable. No engine layout or timing claim is made by static checks.
- Compact talks: complete a newly tracked five-year bargain and a three-year alliance (overlap allowed), then open talks in the Gathering. Test both charters through client terms, patron agreement and final client ratification. Refuse at each stage; invalidate with war, rivalry, alliance loss, strength, rank or opinion changes. Test expiry, duplicate/stale replies and save/reload at every stage. Verify autonomy tribute/integration, protection war-call exclusion/defence/upkeep, own ruling house, native subject-type switch lock, release cleanup and unification credit. Verify AI frequency and charter choice. Existing-save tracking starts now; inspect monthly boundary behavior. Engine playtesting remains pending.

- Harbor Bargains: test both direct agreements, both counteroffers, free refusal and insufficient money at signing. Verify buyer debit equals supplier credit, both modifiers and five-year expiry, one contract per crown, 180-day talk expiry, two-year quiet period and five-year pair lock. Test stale replies, simultaneous approaches, save/reload, war/rivalry/annexation, and an old pending pact refund. Inspect AI offer frequency and ensure it retains 20 gold. Watch event-open frame times and tooltip readability. Native engine acceptance is still pending.

- Reefhook beacons: below 25 gold, the paid choice must be unavailable; at exactly 25 gold, it leaves 0 and grants +5% naval morale recovery for five years. Decline changes no gold or modifiers. Check expiry, save/reload and no repeated introduction.

- Brackmaw sluices: at 24 gold the paid choice must be unavailable; at exactly 25 gold it must leave 0 gold and grant +10% province food storage limit for five years. Declining leaves gold and modifiers unchanged. Check expiry and save/reload, and confirm an already-seen introduction is not repeated.

- Loading cleanup: check fresh logs for the eight custom price registrations, Covenant language, Harbor Pact AI-list registration, duplicate names, selector icons and opinion expiry warnings. Verify action cost labels, bounded AI Harbor Bargain offers, and five-/ten-year opinion expiry. Existing-save behavior also needs an engine check.

- Mesh registration: use a fresh EU5 process with only this candidate enabled. Inspect light/heavy infantry for all six clans, movement/combat and save/reload; compare with human infantry. Check fresh logs for `attachment without a texture variation assigned`, `has not assigned a texture variation` and `Could not find NamedIndex` referencing `cm_goblin_*_mesh`. Compare against the retained pre-fix package if appearance regresses. Passing static checks is not engine acceptance.

- In separate new campaigns, choose each Gathering response. Each grants exactly +5 prestige and its one distinct five-year benefit. Check the modifier name, effect, expiry and option tooltip. No follow-up popup or permanent restriction is added.
- Load a save with the older Claimant or Defiant benefit: its original effect and remaining duration must be preserved.

- Compare identical saves, speed and graphics settings against 0.5.8. Record frame-time spikes for A Seat Among the Five, clan introductions, diplomatic replies and Covenant stories. Compare first and repeated opens.
- Run monthly ticks with the Gathering open; each living crown receives its introduction once. Check annexed crowns and save/reload.
- Check direct, vassal and union unification. Foreign/unowned districts must still block completion. Verify Eastern action eligibility and tooltips.
- After the Moot, confirm no repeat popup. Convert away: modifiers clear. Convert back: initialization resumes without duplicate starting aspects.
- Review all seven portrait age/sex types, clothing fit, skin seams and expressions, plus human portraits. Check infantry idle, walking, combat, retreat and death.
- Review situation panels, flags and images at multiple UI scales, then inspect the fresh error log.

# 0.5.8 portrait acceptance

Follow the age/sex, culture, existing-save and human-control checks in
RELEASE_NOTES_0.5.8.md. Compare to the Gathering artwork. Confirm adult court and noble portraits select
hide/leather/fur outfits, with no cloth robe or jacket from the old mixed pool. In-game acceptance is
pending; static geometry and packaging checks do not establish visual quality.

## 0.5.7 exploration correction acceptance (pending full build)

Run `python tools/verify_exploration.py --game <EU5 game directory>` for a focused
setup build, native map-reference checks, initial cooldown and voyage/contact
guards. `tools/verify_economy.py` checks the shared setup generator's economy.
These partial build folders are not installable mods.

After packaging 0.5.7, start a new 1337 campaign as each crown. Confirm the Ashborn
homeland and nearby Atlantic waters are discovered, while Iberia and all English,
French and Moroccan land remain terra incognita. Compare known-water/unknown-land
edges to the user's coastal-silhouette screenshot: no pre-revealed political
colors, country labels or inspectable port details. Check distant interiors such
as Paris and London remain hidden unless revealed by normal gameplay. Existing
saves retain previous discoveries and are not valid acceptance tests for setup.

Confirm no exploration offer before the 36-month initial cooldown expires
(counted from the first monthly pulse, around 1340). Save/reload before expiry.
Check unaffordable voyages and six-month postponement; then pay for the eastward
voyage and confirm arrival after four months. Confirm Porto, Lisbon and Setubal
are newly discovered only on return, and north/south land ports remain hidden.
Verify the owners of visited ports
learn of the Isles on arrival and receive at most one first-contact notice each.
After twelve months, test each six-month north/south voyage, including a port
changing owner before arrival. Complete both routes and check offers stop.
Other native sources of discovery may independently reveal the Isles earlier.

## 0.5.5 art acceptance

Check all five country shields and land/naval flags against the Gathering banner
reference: Cindermaw black volcano/rust orange; Brackmaw ivory reeds/olive;
Reefhook ivory curling wave/teal; Shatterfin ivory shark and three waves/slate
blue; Sootwake ivory spiked helmet/charcoal. Check diplomacy and country headers,
small situation participants, map armies and ships. Confirm transparent emblem
surrounds, no skull-and-swords fallback and no duplicate Cindermaw arms. Restart
fully after installing to refresh flag art; check a new campaign and save/reload.
Native flag shape and lighting can change the appearance from the flat preview.

Install the full 0.5.5 release with Install-Goblins.cmd and disable the separate
Gathering Prototype add-on. Start a new 1337 campaign. Inspect both situation
headers and their 128 x 128 icons in the situation list, panel and notifications.
Check the Gathering council and Eastern Hunger fleet appear without missing
textures or generic fallback art. Inspect at normal UI scale and one larger scale.

Read all five clan introductions: stone arrow and forge for Cindermaw, tidal gate
and stores for Brackmaw, split shell and rescue harbor for Reefhook, female ruler
and maternal household for Shatterfin, scorched branch and woodland for Sootwake.
Check the harbor pact, oath, unification, eastern preparation and first-harbor
events. Oath offer/acceptance and both unification perspectives intentionally
share their corresponding painting. Faces and props must remain readable under
the native frame, with intact choices and no foreground character overlay.

Complete east, north and south exploration voyages and inspect departure, charts,
Iberia, Biscay and African coast art. From a contacted foreign country, inspect
the human scout following goblin sails in Strange Visitors on Our Shores. Check
the initial Cindermaw lore event uses its forge illustration. Save/reload and reopen
the active situation. Inspect the error log for missing DDS or image-path errors.
Static art validation does not establish these engine/UI results.

# 0.5.5 Jaima Gathering acceptance

Start a new 1337 campaign as Shatterfin with the prototype after the 0.5.4 base. Check Jaima, the Mare-Mother, at 66/58/52 and Skritcha as initial eligible successor. When the Gathering starts, read The Tidemother’s Terms; 30 days after its introduction, read The Maternal House Endures. Save/reload during the delay and continue for several months to verify one delivery. Check all buttons and family names. Neither event changes stats, heirs, laws or relationships. Repeat as each other kingdom: its own introduction must fire and neither Shatterfin event should appear. Check voluntary Shatterfin vassalage preserves the maternal house and law. In-game delivery and layout remain unverified by static checks.

## 0.5.5 clan identity acceptance

Cindermaw: check Drogg, The Stone Fletcher, at 78/80/96 ADM/DIP/MIL, with exactly one nickname. Read the expanded Emberblood culture description and the **One Fire, Many Blades** Gathering introduction. Verify Grakka, Grask and Kragga retain their original family links and dates. Military institutions and influence described in the text are flavor; no free forces, imposed allegiance or new diplomatic mechanics are granted.

Enable the 0.5.4 base and the prepared 0.5.5 add-on, then start a new 1337 campaign. Check Murgash Brackmaw, The Sluice-King (84/78/90 ADM/DIP/MIL), Skrezz Reefhook, The Wreck-Taker (62/88/90), and Snikh Sootwake, The Blackbough (80/54/90). Their culture descriptions should show the expanded Brineward, Reefstrider and Ashveil customs. House names, parents, spouses, children, birthdays and strongest-dynasty succession should match the base. Krizzek and Zhor remain the adult dynastic successors at start.

Run each kingdom to the Gathering introduction. Check The Sluice-King's Bargain, The Wreck-Taker's Share and Beneath the Blackbough for readable text, correct family names and intact buttons. These are narrative changes: rescue shares, cutting rights, house sayings and court interests do not add new actions or economic bonuses. Disable the add-on and start a separate base-only campaign to confirm the base's original names, abilities and descriptions return. In-game display, override precedence and event layout remain unverified by static tests.

## 0.5.4 demographic revision acceptance

Start a new 1337 campaign. Check total populations: CDM 552,739; QBR 318,463; RHK 108,437; SFK 213,487; SWK 101,629. Verify ruler ages are CDM 38, QBR 36, RHK 27, SFK 39 and SWK 29, eligible heirs remain adults and Jaima retains maternal seniority.

Check Goblin Longevity in character life-expectancy modifiers: +15 years for each Ashborn culture, both sexes, children and newly generated characters. Test a goblin employed in a human country and a human in a goblin country. Save/reload and change character culture; the conditional bonus must follow culture and never stack. Compare otherwise identical goblin/human characters rather than asserting a fixed death age.

Inspect food prices, employment, RGO capacity, tax receipts and budgets after the first monthly initialization and after 1, 5 and 10 years. More people and capacity have passed static checks, but economic viability needs gameplay evidence. Check the three smaller clans especially.

Earlier population figures below refer to the initial 0.5.4 pass.

# 0.5.4 acceptance checklist

Use a NEW 1337 campaign, only the intended 0.5.4 copy active.

1. Confirm 72 land locations and 30 provinces, with complete borders, settlements, ports and navigable channels.
2. Starting population before simulation: CDM 368,134; QBR 210,677; RHK 35,067; SFK 35,442; SWK 33,374. Total 682,694. Check burgher/laborer employment alongside peasants.
3. All five capitals: marketplace level 2, granary level 1 and tools/cloth/pottery guilds. Check wheat windmills and iron/copper smelters have usable production methods.
4. First monthly pulse grants RGO investment once. Save/reload and advance another year to check for repeated grants.
5. Inspect Goldscar/Goldvein, Silverfang/Silverneedle/Silver Shard, Saffron Hollow/Vale, Dyer's Marsh/Fen, Silkworm Grove, Pearlshore and Alumcrag/Alum Key. Original resource districts remain beside them.
6. Run all clans for 1, 5 and 10 years; record treasury balance, tax/trade income, building profitability, employment, market access and provincial food. Check luxury production does not starve basic industry of workers.
7. Each Ironfang dynastic son (MIL 82) initially qualifies ahead of unrelated courtier MIL 86. In a disposable save, raise another eligible dynastic adult man's MIL and check he leads. Minors, women, foreign rulers and blocked candidates remain excluded.
8. With no eligible adult men in the dynasty, no unrelated courtier may become eligible under this law. Test the native crisis/alternative-law path separately.
9. Force a new dynasty or successful pretender takeover in a disposable save: displayed country name/adjective should follow the new house, with tag, territory, relations and events intact. Directly reassign a ruler's dynasty, advance a month and check reconciliation. A regent must not rename the country.
10. Shatterfin retains Jaima, the Mare-Mother, and maternal seniority: Skritcha is the initial eligible successor; stronger men cannot inherit. A new maternal house also updates the country name.
11. Regression: human portraits, goblin courts, visible infantry, recruitment art, voyages and reciprocal first contact.

Static checks do not establish gameplay acceptance. Earlier-version notes follow.

## 0.5.3 infantry attachment repair — user tested

Native fallback infantry were visible and did not reproduce the crash in the user's test. Custom goblin infantry are now re-enabled through the native attachment workflow: the base graph supplies the skeleton, transform and animation machine; a named shared_pose_entity attachment supplies the visible mesh. The direct root MeshType is removed.

The user confirmed on October 6, 2026 that the repaired infantry no longer crashes and appears properly. The precise engine fault is not proven, and exhaustive state coverage is not claimed. Visual refinement is deferred in issue #4: make the units less goofy while preserving this working attachment route. Continue regression checks for movement, combat and save/reload.

## 0.5.3 appearance acceptance - pending

- Inspect all six clans: rulers, family, cabinet, other courtiers, both sexes and every age. Clothing and skin must follow culture, not employer.
- Check ears and small teeth during idle and jaw movement; check female outfit fit, child coverage and single infant swaddling.
- Verify crowns/court finery are absent on Ashborn and unchanged elsewhere.
- Compare infantry height with native units; exercise idle, movement, attack and retreat.
- Inspect fresh logs for missing accessories, gene errors and texture-array failures.
- Compare compact torso proportions and mild stoop on adult men and women. Check head/hand/clothing alignment, portrait crop and preserved child growth. Exact full-body height is not certified.
- Verify the repaired graph no longer logs Invalid entity graph for any of the six clans, and that infantry are visible before accepting the fix.

# Goblins of the Ashborn Isles 0.5.3 verification

## Build checks

- Require a fresh 0.5.3 validation report against EU5 1.3.11.
- Check 36 connected land footprints, six islands and preserved vanilla geography.
- Verify thirteen registered sea zones, connected to each other and native Atlantic lanes.
- Verify 36 settlement anchors within their own land, fleet/combat anchors and coastal ports.
- Check population totals, capital ranks, braces, law/policy IDs and monarchy succession registration.
- Validate native terrain caches and compact-package reconstruction checksums.
- Probe all six island centres from 32 directions at radius 0.0001 map units. Height spread must be at most two uint16 units (quantization); the 0.4.0 formula had jumps of 244-1596 units.
- Decode the final height cache independently at mip 2. Check above-water coverage of each location, a Cindermaw peak above 12 world units, smaller mountain-island peaks above 7, and Reefhook above 4. Peaks follow geology rather than requiring one in every administrative location.
- Inspect `Goblins_Cache_Relief.png`; this is a diagnostic of encoded terrain, not a substitute for an engine screenshot.
- Check the renamed metadata, installer, packages and 512 x 512 thumbnail.

## New-campaign playtest

Fully restart EU5. Enable only **Goblins of the Ashborn Isles** and start a new 1337 campaign; do not use an earlier save.

1. Find five goblin countries between the Azores and Portugal. Check six physical islands: Reefhook has four playable tiles, Sootwake two, and Shatterfin three across two islands.
2. Check populations: Cindermaw 320,117; Brackmaw 183,197; Reefhook 30,492; Shatterfin 30,819; Sootwake 29,022. Hooktooth is a city with 63,973 people; other capitals are towns.
3. Zoom into every island. Inspect coasts, mountains, craters, less-green materials, visible settlements and cache seams. Check armies and docks.

   Specifically repeat the 0.4.0 screenshots at Hooktooth/Cinder Crown and the two Shatterfin islands, at close and medium zoom. Check that the larger relief appears in geometry and not merely in texture shading. Compare with mainland mountains in the same session. If the islands still look unchanged, the rendering path remains unresolved; do not mark this build terrain-verified based on the numerical report. Verify that Graphics > Disable 3D Terrain is unchecked and compare in a terrain map mode.
4. Advance one month as Cindermaw: its opening force and introduction should appear once. Advance another month and save/reload to check they do not repeat.
5. Sail around Cindermaw through its distinct north, west and east waters and the southern channel. After exploration, sail out into the Atlantic. Dock at each island and test embarkation and landing. No sailing through land or invisible bridges.
6. Move armies over internal borders. Inspect combat terrain, buildings, construction, workers, food and market membership.
7. Test Ironfang succession, ordinary monarchy law changes, raiding and budgets for at least a year. Highest Military ability must win among eligible adult male Ashborn; administration then age break ties. Save/reload with the rule changed and verify it stays changed.
8. Review fresh logs for invalid sea targets, mixed sea/land areas, election mismatches, missing advances, parser errors and locator errors. Compare unrelated errors against vanilla. An empty religion-modifier warning remains a known content limitation.
9. Confirm the renamed mod appears once and the previous installation is backed up outside the mod scan directory.
10. Switch to vanilla and start an unmodded campaign to confirm normal geography.

## Exploration acceptance

- In a NEW 1337 campaign, each goblin country sees only the archipelago and its thirteen waters; Portugal, France and Britain begin as terra incognita. Old saves retain old discoveries.
- At approximately the fourth monthly pulse, the first voyage offer appears. Postpone: no cost or reveal; the offer returns six months later.
- Fund the eastern voyage for 5 gold: no immediate reveal, no duplicate offer while pending. After four months the result reveals only the western Iberian route and Porto/Lisbon/Setubal.
- After twelve more months, fund a northern or southern voyage for 10 gold. Six months later, verify only the chosen coast is revealed. The other voyage remains available after the next cooldown.
- Save/reload during a voyage: it still returns once. Insufficient gold disables funding but always permits postponement. Test a smaller clan too.
- Each completed route reveals the Ashborn land and waters to the current owners of its visited ports. Confirm Portugal on the eastern route, the current northern port owners on the northern route, and Iberian/Maghrebi owners on the southern route. Unrelated countries should not be revealed by the event. Conquered ports must use their new owners. Discovery alone does not guarantee an AI invasion.

## Main development: models and culture names

- Use a fresh download of `main`, extract it and run Install-Goblins.cmd after closing EU5. This includes development model files; the published 0.5.0 ZIP does not. Current running tests are not modified automatically.
- Verify the culture group is Ashborn. Cultures should display Emberblood (Cindermaw), Brineward (Brackmaw), Reefstrider (Reefhook), Stormfang (Shatterfin) and Ashveil (Sootwake), including succession descriptions and lore.
- Inspect light and heavy infantry from each clan. Confirm short goblin anatomy and the five skin palettes, correct ground contact, sensible scale against a vanilla infantry unit, shadows, selection highlights and normal lighting.
- Check idle, walking, attack, retreat and charge. Confirm animation progresses instead of restarting each frame. Save/reload and retest movement. The death clip is exported but its game trigger remains pending; report actual casualty behavior.
- Confirm vanilla countries still use their original infantry. Cavalry and artillery crews are not converted. Portraits have a separate development pass described below. Inspect fresh logs for mesh, shader, skeleton, schematic, unit-constructor or state-machine errors.
- Rebuild art with Node, then run `python tools/prepare_main_overlay.py --game "PATH/TO/EU5/game"`. This checks native asset round trips, skinning against 51 source poses and all five palettes, and refreshes the install manifest. A normal full build also exports and verifies the models.

## Runtime limits

Static checks do not prove in-game rendering, pathfinding, construction or balance. Terrain uses a native cache patch, not an engine-editor export. This version awaits user playtesting. Dedicated foreign desire/fear mechanics are not implemented. Goblin portraits now have an unverified development pass. No Steam Workshop upload has been performed.

## Version 0.5.0 integration acceptance

- Confirm Cindermaw has 15 locations, Brackmaw 12, Reefhook four, Shatterfin three and Sootwake two; province groupings are retained. Population totals remain unchanged.
- Compare `feature_verification.json`: every island matches its normalized area target within 1.5%; land is 12% smaller than 0.5.0. Both crowded channels must exceed 24 map pixels; all other island pairs must exceed 10. Reefhook is about 1.2x either small rival clan.
- In terrain mode, inspect Cindermaw across province borders: continuous rocky spine and foothills, not province-shaped surface swatches. Zoom close enough for native vegetation layers; inspect trees, rocky outcrops, shorelines and streams on every island.
- Compare native Madeira/Sao Miguel in the same session. Confirm no native island's materials changed. Review shader/parser logs for the added biome.
- Open each capital and rural location: verify appropriate village types, one/two capital guilds, wharves, and actual workers. Confirm no unsupported building IDs or missing production methods.
- Record RGO capacity before and after the first monthly pulse; it should receive the configured one-time expansion. Advance another month and save/reload: it must not be granted again.
- At months 3, 6 and 12, record income, expenses, treasury, food, prices, employment, control and market membership for all six clans. The production setup is not evidence of a positive budget by itself. Check naval-supply inputs (lumber, fiber, tar, cloth) and tools/pottery inputs before raising industry further.
- Confirm the starting force is 1 footmen unit, 2 galleys and 3 cogs after the first pulse. No repeated grants. The introduction has one option and grants nothing independently.
- Ironfang reform must be removable and Rule of the Strongest changeable. Compare eligible candidates' Military ability, exclude children/women/foreign rulers, and test an actual succession. Ordinary monarchy alternatives must remain available after the change.

## 0.5.1 terrain integration acceptance

- Run `python tools/verify_geography.py` for district connectivity and minimum channel clearance.
- Inspect crater rims, dark lava aprons, rocky lee slopes and reduced woodland at close and middle zoom. Check moist valleys remain distinct from bare volcanic uplands.
- Sail through both widened channels and inspect the Shatterfin approach for intact vanilla sea routes.
- The source integration retains the 0.5.0 package number until the next prepared release; do not overwrite the published 0.5.0 archive. Build from source for the new terrain.


## Culture-based portrait test pass (main only)

All five Ashborn cultures now select their own portrait ethnicity and deterministic
appearance modifier. The rules follow the character's culture, not their employer,
country, sex, or office. This targets ruling families, cabinet members, other
characters and culture-generated population portraits. Existing character DNA gets
the visible modifiers without a save-edit migration. Newly generated DNA also uses
the culture's ethnicity. Human cultures receive none of these modifiers.

The pass uses the native animated portrait faces and clothing, with custom rigged
pointed ears, jaw-bound tusks, goblin facial proportions, and matching head/body skin
colour. It does not reuse the infantry's whole-body mesh as a portrait. Adult male,
adult female, boy, girl, both adolescent types and infant are configured; infants
have smaller ears without tusks. Clan colours match the infantry art palette.

**Status: static checks passed; in-game appearance has not been verified.** Native
rig bindings, skin weights, geometry, asset references, all seven portrait types,
and all five culture routes are checked by `tools/verify_goblin_portraits.py`.
Clothing fit, expressions, child scaling and population portrait selection still
need a game test. Restart EU5 after installing a fresh main download; the published
0.5.0 ZIP does not contain this pass. Compare a ruler, relative, cabinet member,
woman, child and infant from each culture, plus a human character as a control.
Check skin on neck/hands, eyes, ear placement, tusks during animation, save/reload,
and a newly generated character. Send a screenshot and fresh error.log if wrong.

The separate infantry integration currently fails in-game with `Invalid entity
graph [cm_goblin_cindermaw_schematic]`, producing invisible infantry. The 0.5.3 repair candidate supplies explicit translation and the native animation-machine parameter; it requires an engine retest.


## 0.5.2 succession acceptance

- Confirm installer and mod metadata say 0.5.2; begin a new 1337 campaign.
- In SFK, inspect Tidemother Monarchy and Seniority of the Tidemothers. Jaima
  should rule and Skritcha should lead the candidate list ahead of the daughters.
- Trigger a succession in a disposable test save. Skritcha should inherit, followed
  by Morzha after a second succession if all eligible candidates remain alive.
- Test women of equal displayed age but different birthdays; the older wins.
- Exclude a high-Military male, under-18 girl, unrelated older woman, a woman
  related only through her father, a foreign ruler and a character barred from rule.
- Test a newborn of a ruling-house mother and a differently named father: the
  child should keep the mother's dynasty. Recheck her eligibility as an adult.
- Change the law and confirm the custom birth action stops; remove the reform
  and confirm the fallback law. Confirm CDM/QBR/RHK/SWK retain strongest-male law.
- Test exhausted candidates, regency and save/reload. Report the actual game
  behavior: these paths have not been certified by static tests.

All five Ashborn cultures have 16 male and 16 female name entries, six house names and six lowborn names each. Four additional royal families and 15 adult courtiers are authored. Drogg Cindermaw bears the nickname "the Stone Fletcher"; Jaima Shatterfin bears "the Mare-Mother". Cabinet appointments remain native, drawing on culture-specific names and the available court.

## 0.5.2 portrait crash-fix gate

- All five skin decals must match native 1024 x 1024 BC3/DXT5 arrays with 11 mip levels.
- Run `tools/verify_goblin_portraits.py` against the prepared 0.5.2 output and installed game. The report must pass before packaging.
- Verify the bundled archive and development overlay include the same corrected textures.
- Static validation is not an engine playtest; confirm campaign startup and portrait rendering in EU5. The reported missing land in 0.5.1 also requires a separate terrain acceptance pass.

## Companion first contact

- As Portugal, let an Ashborn eastern expedition return: confirm the islands reveal and Strange Visitors on Our Shores appears once, despite owning multiple visited ports.
- Let another clan visit Portugal: no duplicate popup. Test northern/southern routes for other current port owners, including conquered ports.
- Confirm Ashborn owners and unowned sea locations do not receive the foreign-contact event.
- Existing saves: completed voyages do not replay; a future voyage may trigger the first notification.
# Integrated 0.5.3 infantry artwork

- Fully restart after installation. Inspect infantry recruitment, levies and army cards
  for each of the five Ashborn cultures; confirm readable goblin illustrations.
- Check England and Castile retain human unit art and recruitment/stats are unchanged.
- Verify map infantry spawning and movement separately; the latest shared-pose
  attachment candidate is included and still needs engine acceptance.
- Test Portugal's companion event on the next eastern voyage return.
- Later-age infantry sharing medieval equipment artwork is expected in this first pass.

### 0.5.7 diplomatic replies
- Historical 0.5.7 response checks are superseded by the Harbor Bargain and staged Compact checks above.
- Leave an offer pending, save/reload, then answer it. Repeat with offers involving different kingdoms; confirm names do not cross between result popups.
- Make acceptance invalid while an offer is pending (war or subject status), then decline and check notification and pending-state cleanup.
- Observe bounded AI Harbor Bargain and Compact offers under their current eligibility and cooldown rules; ordinary native alliance diplomacy remains possible.

## 0.5.6 Gathering popup regression

After a full 0.5.6 build, compare the same campaign date and graphics settings with 0.5.5. Open A Seat Among Five, hover all three options, and open the Gathering situation completion tooltip. Confirm responsive input and readable names: Claimant Among the Five for the first two choices, Our Shores, Our Crown for the third. Confirm the unchanged five-year bonuses. Reopen the situation tooltip repeatedly and check that new logs no longer accumulate scope-description warnings at its completion condition. Test Eastern Hunger start/completion descriptions as well. Validate unification through direct ownership, vassals and junior unions; one foreign-held homeland district must still prevent completion. Static checks do not establish frame-time improvement or crash freedom.

Test all three One Fire, Many Blades options from the same pre-event save. Each must award exactly its selected five-year modifier. Verify this introduction appears for any earlier Gathering choice and does not repeat monthly.

Open both custom situations in the full 0.5.6 build. Verify title, artwork, start date, description, completion requirement, scrolling and eligible action buttons appear. Check ended-state display, GUI error logs and repeated panel opening responsiveness.
