# Development (main) — goblin soldiers on the native unit rig

Not yet released or tested in game. Applies through the main installer overlay.

- **Goblin infantry now use EU5's own soldier rig.** They wear the same native clothes, armour, helmets, weapons, shields and backpacks as human infantry, and play the same animations. Their gear changes with age and unit type exactly as it does for human armies. The old standalone body is retired: it had 2,476 triangles, flat single-colour textures, no gear and its own animation set.
- **A goblin head for each clan.** The heads are sculpted from the existing CC0 goblin source, with long ears, a hooked nose, tusks and a dark-eyed face. Each clan's skin has its own colour and baked shading (256 px DXT5 with mipmaps). The head is bound to the native head joint and includes a neck that covers the native torso's neck. Goblins have no hair or beards.
- **Shorter soldiers.** Goblin infantry use a copy of the native soldier graph with only its name and world scale changed (0.0625 instead of 0.08, 78% of human height).
- No native meshes or textures are copied. They are referenced by name, and the native skeleton and soldier graph are read from the installed game at build time.

Known gaps: hands come from the native torsos and take the game's human skin tone. Cavalry riders get goblin heads at human scale. Heavy helmets can clip the larger goblin skull and ears. Static checks pass (`tools/verify_goblin_models.py`); in-game look, ground contact, formation spacing and logs still need a test.

# Goblins of the Ashborn Isles 0.6.5

**0.6.5 — Buildable timber in Blackwood and Giltfang.**

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

# 0.6.1

## 0.6.2 — Workers and Wildfang Clans

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

# 0.6.0 - Giltfang and the Quiet Road

Flag repair: all six crowns explicitly select their authored coat of arms at
creation. A one-time monthly migration corrects saved procedural placeholders,
including Giltfang's blue circle on yellow. Install with EU5 closed, restart,
load an existing 0.6.0 save and advance to the next month. This repair alone
does not require a new campaign; in-game rendering still needs confirmation.

Giltfang joins the Ashborn as the sixth crown. Its northern main island and
Tolltooth companion have a combined land area of 89.97% of Brackmaw, with nine
new coastal sea tiles connected to the existing Atlantic network. Chainhaven
starts with its own market; Hooktooth keeps the southern market. Every goblin
crown begins knowing all Ashborn land and surrounding coastal tiles.

Vrekk the Brass-Tooth leads the Cinderweight from the Crown of Weights and
Chains. Giltfang has 22 districts, its own court, flag, portraits, opening story
and three projects, plus sacred sites at Chainhaven and Tolltooth. All six
crowns participate in the Gathering, Eastern Hunger, Harbor Bargains,
Compact talks, Covenant stories and the separate Ashborn Voyages situation.

Harbor descriptions now wrap into short lines. Project buttons use short
labels and show highlighted native costs and rewards on hover. Requirements
use readable conditions, broken punctuation is repaired, and both parties
receive signing receipts listing the actual payment, benefit, burden and term.
Earlier portrait, wardrobe, hair, Drogg and holy-site fixes are retained.

Starting projects now cost **25 gold**, a quarter of the 100-gold opening
treasury; the AI keeps a 20-gold reserve. Food rewards explicitly raise
the **province food storage limit**, with tooltip guidance to the native
stockpile display and its modifier breakdown. They do not create food
or increase monthly production.

Lantern Cay is a new three-district Cindermaw outpost beside an ordinary
coastal passage between the northern and southern islands. The lower
eastern impassable strip is open, and parts of three nearby current
tiles become coastal water. The route does not require fast-current
tiles. The Isles now contain nine islands, 97 districts and 28 coastal
sea tiles; Cindermaw gains 18,000 people on the new cay.

Use a NEW campaign: the world map, country roster and markets have changed.
Install with EU5 closed. Static checks cover geography, native definitions,
all-six-crown event scenarios, terrain reconstruction and package hashes.
In-game sailing, market trade, UI layout and rendering remain playtest checks.
This is local 0.6.0 staging work, separate from GitHub releases and Workshop.



Loading cleanup: register all seven action prices and their cost labels; resolve
the Covenant language to the existing Cindermaw dialect; register the
Harbor Bargains AI actions with eligibility and reserve checks; repair unavailable-target icons and longevity text;
deduplicate shared character names. Opinion bonuses now use their stated
fixed durations (supplies five years, pacts/oaths ten) without conflicting
annual decay. Legacy opinion modifiers remain available for existing saves.

All six Ashborn clans now start with 100 gold in new campaigns, replacing
Cindermaw's 50, Brackmaw's 35 and the other clans' 20. This uses the explicit
100-gold setup of small vanilla countries such as Oneida, Onondaga and Cayuga as
a benchmark; it is not a claim that every vanilla country starts with 100.
Opening projects now cost 25 gold. AI reserves, recurring income and war actions are unchanged.
Existing saves retain their current treasury; start a new campaign for this change.

Exploration now shows preparation, pending decisions, the route at sea with a
remaining-time range, crew rest and completed charts in the separate Ashborn
Voyages situation. Review Ashborn Voyages reopens available routes there. Offers show the price, duration, destinations and reciprocal discovery
before payment. Choose a six-month reminder or stop reminders and commission
manually. Stops persist across voyages; choosing a six-month reminder restores
automatic offers. Arrival reports record the current owners of visited ports.
Discovery and the 12-month rest now begin on arrival, without waiting for the
report to be dismissed. Prices (5/10/10 gold), travel (4/6/6 months), first offer
(36 months) and limited coastal discovery remain unchanged. Duplicate and stale
replies cannot charge again or alter a later voyage. Older paid voyages still
complete; an already-open older return message settles when acknowledged.
Generated-script regression checks pass; GUI and real save/reload playtests remain.

Covenant stories now offer two competing approaches and a neutral defer option.
Each story has specific costs and effects instead of the repeated gold/Favor/prestige
template. Funded approaches cost 5 gold; AI retains 20. Practical alternatives may
cost Favor or carry temporary estate, tolerance or military drawbacks. Effects last
three years and replace earlier story consequences. There are no story prestige
rewards. Defer changes no resources or modifiers and schedules no follow-up; the
existing three-year cooldown and event frequency remain. Major rites, religious
traditions and the Moot settlement are unchanged. Old pending popups without a new
session token can only be deferred safely. In-game balance and save/reload need testing.

All six clans now receive three mutually exclusive projects plus a free keep-the-gold
option in their existing introduction. Every project costs 25 gold and lasts five
years; AI buyers keep 20 gold. Cindermaw chooses army morale, diplomacy or army
upkeep. Brackmaw chooses storage, production or fort defense. Reefhook chooses
naval recovery, fleet upkeep or diplomacy. Shatterfin chooses monthly sailors,
naval morale or diplomacy. Sootwake chooses fort defense, production or storage.
Benefits are shown on each choice. Existing project rewards and already-seen
introductions remain unchanged; choosing one project blocks the other two.

Situation progress: both panels now show your qualifying realm's live homeland
location count out of 97, using the same ownership rules as unification. The
Gathering explains the Compact route. Its partner selector keeps existing crowns
visible when they fail requirements and explains bargain history, alliance age,
opinion, strength, rank, peace, pending offers and cooldowns. Annexed crowns and
your own crown are excluded. This changes presentation, not eligibility or balance.
History checks show whether the full term has been recorded; they are not an exact
days-remaining countdown. UI layout and responsiveness still need an engine test.

Harbor Bargains replace the cheap alliance offer with paid provisions or pilots.
A supplier can accept 10 gold, counter once with the other service for 15,
or refuse. Signed five-year contracts grant the buyer +10% food storage or
+5% naval morale recovery, while committing 5% storage or 2.5% recovery
from the supplier. Payment transfers only at signing. Both crowns need
25 mutual opinion and one free contract slot. AI retains 20 gold.
Talks expire after 180 days; pairs wait five years between approaches,
with a two-year quiet period for each crown. Hostilities, rivalry or a
vanished partner end the contract on the next monthly check, without refund.
No alliance is created; existing alliances remain. Saved old pact offers
close with their five-gold fee returned.

Compact talks now require a completed five-year Harbor Bargain with that crown
and three years of an alliance observed by the monthly check. These can overlap.
Both crowns must be independent and at peace; the prospective subject needs
150 opinion, no higher rank, and no more than 65% of the patron's strength.
In the Gathering situation, select Open Compact Talks and the eligible crown.
The smaller crown chooses its charter, the patron accepts or refuses, and the
smaller crown explicitly ratifies or withdraws. There is no negotiation fee,
instant prestige or loyalty reward. Ordinary alliance remains a valid alternative.

- Autonomy Charter: half normal base tribute, a 20-year minimum before annexation,
  then half normal integration speed. Normal offensive military obligations.
- Protection Charter: normal tribute and 10-year annexation minimum; exemption
  from offensive wars, +10% defensiveness, and protection against external attacks
  and fellow subjects. The patron bears -5% army maintenance efficiency.

Both charters retain the ruling house and succession customs, count toward
unification, and lock normal subject-type switching to preserve their terms.
They still impose limited diplomacy and the normal -20% subject cabinet efficiency.
Talks expire 180 days after invitation. Both crowns have a two-year quiet period;
the pair waits five years between approaches, restarted on a live refusal.
All eligibility conditions are rechecked before each agreement and ratification.

Existing alliances remain, but their three-year observation starts with this update.
Only new bargains carrying the full tracking record can earn completion credit;
older contracts are not credited retroactively. Monthly sampling can miss a brief
alliance break or hostility that begins and ends between checks. Old pending
Compact requests close with their ten-gold fee returned once, without submission.
Script and installation checks are separate from pending in-game acceptance.


Reefhook can restore its rescue beacons in its existing introduction: pay
25 gold for +5% naval morale recovery for five years, or keep the money.
The paid choice requires at least 25 gold. Already-seen introductions do
not replay, and no additional popup is added.

Brackmaw can now repair its sluices in its existing introductory event: pay
25 gold for +10% province food storage limit for five years, or keep the money.
The paid choice requires at least 25 gold. No additional popup is added.
Campaigns that already received the introduction will not receive it again.

The six goblin infantry bodies now register with EU5's native fixed-texture
attachment list. This addresses the missing texture-variation registration reported
by the engine. Geometry, palettes, animations and the shared-pose attachment route
are unchanged. Static checks pass; a fresh engine test must confirm the errors stop.

Approved opening-choice update: leadership grants +5% army morale, cooperation
+0.5 diplomatic reputation, and independence +10% defensiveness. Each lasts five
years and grants +5 prestige. Existing saves keep already-granted legacy modifiers
until expiry; the new benefits apply when choosing the opening event.

- Restrict recurring Gathering introduction scans to five native country scopes.
- Skip completed Covenant Moot ownership work; stop repeated conversion cleanup.
- Compact Eastern-action ownership tooltips; remove the repeated Crossing check.
- Validate all 49 event illustrations, including the 13 Covenant events.
- Retain the 0.5.8 portraits, hide/leather wardrobe and working infantry renderer.
- Remove source art, proposals, previews and publishing guides from the player ZIP.
- Rebuild compact prepared transport without old archive data or obsolete chunks.

Static checks do not prove in-game performance or visual acceptance.

# Goblins of the Ashborn Isles 0.5.8 — Portrait art pass

Staging candidate, incorporating the completed 0.5.7 release at b4940c7.
Not a Steam release and not installed into the active game profile.

## Portrait changes

- Replace the flat ear fans with closed, cupped ears: recessed bowls, raised rims,
  smooth normals, swept tips and subtle left/right differences. Retain native
  skeleton bindings and the working shared-pose attachment route.
- Replace oversized eyes and broad mouths with smaller, recessed, hooded eyes,
  stronger brows, lean cheeks and restrained mouths. Keep hooked noses without
  combining maximum nose length, maximum projection and minimum jaw size.
- Preserve more native skin colour detail: reduce the constant skin replacement
  from 88% to 60%. Normal-map detail, native ageing and clan colours remain.
- Shorter necks; compact torso strength 0.32 to 0.42 and stoop 0.18 to 0.24.
  These are rig parameters, not measured height in metres. Female height poses
  remain unsupported, so no disabled height attribute is introduced.
- Smaller jaw-bound teeth; remove native beards to expose goblin facial anatomy.
- Replace the mixed adult cloth wardrobe entirely with inspected native hide
  tunics, fringed leather overcoats and fur-trimmed hunter garments. No Chinese,
  German jacket, Aztec wrap or Syrian scarf-dress entries remain in the adult
  selection. Children retain fitted plain garments and infants retain swaddling.
  Custom torn-leather geometry remains future work.
- Apply by goblin culture to court members, nobles, relatives and generated
  characters, preserving human appearance and unrelated individual DNA.
- Keep infant skin/ears separate from adult teeth and compact-body treatment;
  native child ageing still controls the adult facial morphs.

## Validation and visual acceptance

Static checks cover all five cultures and seven portrait age/sex types, native
rig transforms and clothing references, DDS array compatibility, finite mesh
data, normalized normals/weights and closed consistently wound ear shells.
Full build and clean-source installer checks are recorded in HANDOFF.md.

No in-game visual acceptance is claimed. Review the court, noble/estate and
character views at their normal small size and in close-up: men, women,
children, adolescents, infants and elders from all five cultures; an existing
save and newly generated characters; a human ruler as a negative control.
Check blink/talk/idle poses, ear roots and lighting, teeth/lip clipping, neck
and hand colour seams, hair overlap, clothing fit and portrait framing.

The reference is art/events/sources/gathering.png. Judge whether the faces read
as weathered, ugly goblins with short adult proportions. A technical mesh
preview is not a screenshot of the engine result.

## Inherited 0.5.7 changes

Retains the Ashen Covenant religion and goblin estate names, homeland-only
starting land discovery, delayed voyages, Harbor Pact response notifications,
Ashen Compact refusal notifications and removal of AI custom Harbor Pact spam.
New campaigns are required for inherited starting-world/discovery changes.
Portrait modifiers should also affect existing culture-matched characters;
verify this in a saved game rather than assuming the engine refreshes every view.

---

# Goblins of the Ashborn Isles 0.5.6

## Changes

- Specialized starting economies for all five kingdoms, scaled to population and local resources.
- Opening exploration delayed to 36 months, with nearby Atlantic starting charts.
- Added missing Gathering and Eastern Hunger situation panels.
- Replaced expensive completion-tooltip expansion with concise descriptions while preserving unification rules.
- Corrected unnamed Gathering modifiers.
- One Fire, Many Blades offers three five-year rewards: +5% army morale, +0.5 diplomatic reputation, or +10% army maintenance efficiency.
- Rebuilt the complete installer against the current configuration, fixing the stale terrain configuration error.

## Installation

Download Goblins_Ashborn_Isles_0.5.6.zip, extract into a new folder, close EU5 and run Install-Goblins.cmd. No earlier package is required. Enable only this mod and start a new 1337 campaign. Targets EU5 1.3.11.

## Validation

Full build and static checks passed. Clean-source preparation and isolated installation passed; all 1,644 installed files matched. Gameplay, balance, panel rendering and performance still need in-game acceptance. Crash resolution has not been confirmed.


# 0.5.6 installer repair candidate

Combines the staging economy and exploration pacing with situation layouts, concise completion tooltips, named modifiers and three Cindermaw council rewards. Rebuilds the complete installer payload against the current source configuration. New campaign required. Runtime testing pending.

# 0.5.5 — The Gathering of the Six

Complete release candidate for EU5 1.3.11. Start a new 1337 campaign. Disable the
earlier Gathering Prototype add-on: this full mod includes its content and
installs without a 0.5.4 prerequisite.

- Unite the 97 homeland districts through conquest, vassalage or senior unions
  in the Gathering of the Five, then pursue a European coastal foothold through
  Eastern Hunger.
- Seven situation actions support alliances, paid aid, voluntary submission,
  war goals and fleet preparation. Offers can be refused; conquests follow
  normal EU5 declarations, warfare and peace rules.
- Five clan introductions, expanded royal-family stories, revised ruler
  abilities and Shatterfin's maternal-house follow-up. Existing family
  relationships and succession laws are preserved.
- 323,941 additional minority-culture goblins bring the Isles to 1,618,696 people.
  All five Ashborn cultures live in every district.
- Seventeen original paintings cover all 21 authored events. Both situations
  have custom headers and icons; all five clans have matching custom flags.
- One regular installer and a matching 0.5.5 terrain/package bundle replace the
  separate prototype installation. The README is now a player guide.

In-game acceptance of the new situations, art, AI behavior and balance remains
pending. Automated checks and package verification do not establish gameplay
readiness. Earlier release notes follow.

## 0.5.5 Jaima Gathering update

Shatterfin is included in the ruler table at Jaima’s unchanged 66/58/52 ADM/DIP/MIL. Expanded The Tidemother’s Terms and new The Maternal House Endures give her two Shatterfin-only narrative events. The follow-up is scheduled 30 days after the introduction and guarded against repeats. All six kingdoms retain their introductions; total events rise from 13 to 14. Maternal seniority, family setup, situation costs and population additions are preserved. README, prototype guide and generated lore now cover her role. Static and packaging checks are separate from pending gameplay acceptance.

## 0.5.4 demographic revision

- Starting populations: Cindermaw 552,739; Brackmaw 318,463; Reefhook 108,437; Shatterfin 213,487; Sootwake 101,629. Total 1,294,755. All clans gain at least another 50% over the first 0.5.4 pass; Shatterfin is the largest smaller clan.
- Rulers start at varied ages of 27-39, with varied consort/court birthdays; their family dates preserve plausible parent ages, adult dynastic heirs, younger rulers with minor children and adult brothers, and Shatterfin maternal seniority.
- Native character auto modifier grants Ashborn goblins +15 years of life expectancy by culture, independent of country, dynasty and employment. Conditional application avoids stacking and excludes humans. Mortality remains probabilistic; combat, illness and scripted deaths remain possible.
- Starting RGO expansion scales with the additional population, reaching 387 levels. Geography, resources and buildings retain the previous 0.5.4 layout.
- Static and installer checks are separate from pending engine acceptance. Starting-population and birth-date edits require a new campaign.

The earlier 0.5.4 entries below describe the initial pass.

# 0.5.4 — Districts and Dynasties

Built on tested staging/0.5.3. EU5 1.3.11; a new 1337 campaign is required.

- 682,694 goblins, up from 593,647 (+15%, rounded to whole people). Each original population is split between two districts, with all starting population classes expanded.
- 36 → 72 inhabited locations and 15 → 30 provinces. Every original location and province is subdivided. Stable country tags, original location IDs, capitals, coastlines and thirteen sea zones remain.
- Starting building levels rise from 47 to 114: stronger capital markets, five granaries, tools/cloth/pottery guilds, rural villages, wheat windmills and smelters on iron/copper RGOs.
- Once-only, ownership-checked first-month RGO expansion rises from 70 to 160 levels across the larger map.
- New RGOs: 2 gold, 3 silver, 2 dyes, 2 saffron, 1 silk, 1 pearls and 2 alum. New food/timber/material districts support basic demand; original districts retain their resources. Native gold ID: goods_gold.
- Ironfang: strongest eligible adult Ashborn man within the ruling dynasty inherits. Military ability decides, with Administration and age breaking ties. Unrelated courtiers cannot inherit through this law; no eligible dynasty member means no eligible heir.
- Native country naming follows the reigning house after a takeover or dynasty reassignment; succession hooks and monthly reconciliation cover changes. Regents do not rename the country. Shatterfin keeps maternal seniority.
- Retains 0.5.3 human portrait isolation, working shared-pose infantry, recruitment art and first-contact events.

Installed Europe reference medians: 520 map pixels/location, 2,626 pixels/province and 5 locations/province. The new districts use this spatial scale as a reference while preserving the islands' smaller political units.

Volcanic/hydrothermal seams explain gold, silver and alum; reeds/lichens supply dyes; drained sheltered volcanic plots grow saffron. Knifeback has a small cultivated silk grove and Reefhook has pearl-diving grounds. These are fictional resources appropriate to the setting.

Extra production capacity is not guaranteed profitability. Food, employment, balance and succession require gameplay acceptance. Use only a verified matching 0.5.4 installer; older instructions below refer to earlier releases.

## 0.5.3 companion first-contact event

Owners of ports visited by an Ashborn expedition now receive Strange Visitors on Our Shores when reciprocal discovery occurs. Strange creatures flee the shore and a scout ship follows them to the islands. Each non-Ashborn nation receives the event once across all clans and voyage routes. Already-completed voyages are not replayed. Static checks only; in-game testing pending.

## 0.5.3 infantry attachment repair — user tested

Native fallback infantry were visible and did not reproduce the crash in the user's test. Custom goblin infantry are now re-enabled through the native attachment workflow: the base graph supplies the skeleton, transform and animation machine; a named shared_pose_entity attachment supplies the visible mesh. The direct root MeshType is removed.

The user confirmed on October 6, 2026 that the repaired infantry no longer crashes and appears properly. The precise engine fault is not proven, and exhaustive state coverage is not claimed. Visual refinement is deferred in issue #4: make the units less goofy while preserving this working attachment route. Continue regression checks for movement, combat and save/reload.

## 0.5.3 development: rough-clad goblins

Portrait refinement: ears now extend 9 cm from their base (previously 5.8), with longer hooked noses, smaller jaws/chins, prominent cheeks, wider mouths and smaller teeth. A culture-only special gene applies compact torso proportions and a mild stoop to adult males and females, fading out during childhood. Human cultures remain outside these modifiers. Exact stature, portrait framing and clothing fit await engine review.

Infantry repair candidate: connect the missing translation input explicitly, consume the native CustomAnimationMachineName parameter, and write graphics scripts with a UTF-8 BOM. Typed graph-link checks now complement mesh/animation validation. The prior graph was rejected in the game log; the subsequent shared-pose attachment repair has now passed the user's visibility/crash test.

First art pass on a separate branch based on 0.5.2. Infantry stature is reduced from 1.12 m to 0.92 m, jaws are narrower and teeth smaller. Clan skin palettes are muted olive, marsh, lichen, slate and soot greens. Portrait recoloring retains 12% of underlying albedo detail.

Portraits select native plain harnesses, wraps, jackets and overcoats for both sexes and all Ashborn cultures, including rulers and courts. Crowns, normal court clothes, capes and neck ornaments are overridden. Children retain basic clothes and infants retain a single native swaddle.

Static model, animation, texture, rig and clothing-reference checks pass. In-game appearance remains unverified. Exact full-body stature and custom torn/patchwork leather-and-rag art remain pending. This branch includes a prepared 0.5.3 installer. Download a fresh branch ZIP, extract it into a new folder and run Install-Goblins.cmd with EU5 closed. In-game art acceptance and Workshop publication remain separate.

## 0.5.2 portrait fix integration

- Includes the 0.5.1 portrait decal correction: 1024 x 1024 BC3 textures with all 11 mip levels, matching native portrait arrays.
- Validates texture dimensions, format, mip count, payload size and native headers during the build.
- Rejects a bundled installer whose version or terrain configuration does not match the source.
- In-game succession, portrait rendering and terrain acceptance remain pending.

## 0.5.2 â€” Shatterfin Tidemothers (feature branch)

Shatterfin alone starts with **Tidemother Monarchy** and **Seniority of the
Tidemothers**. Normal monarchy institutions and the existing naval modifiers
remain. The oldest eligible adult Stormfang woman of the ruling dynasty inherits;
her mother must belong to that same dynasty. Age is measured to the day, with no
Military or administrative score. Men, minors, foreign rulers and blocked
characters are excluded. This is maternal dynastic seniority, not daughter-first
primogeniture or an election. The law can be changed through normal monarchy
controls; removing the reform falls back to absolute cognatic primogeniture.

**Jaima Shatterfin, the Mare-Mother** begins as Tidemother. Her younger sister **Skritcha** is the
oldest eligible successor, followed by Morzha, Rikkra and Krishka. Vrosh is excluded
because he is male despite his high Military ability; Zrikka is too young. The
family is authored parent-before-child, with a deceased maternal founder, Zhavra.
Children born in Shatterfin to women of the ruling house inherit their mother's
dynasty while the law is active. The birth action is restricted to Shatterfin and
this law. Other clans retain Ironfang Monarchy and Rule of the Strongest.

If no eligible adult woman survives, the rule does not silently admit a man or
an unrelated woman. The engine's handling of an exhausted candidate list needs
in-game testing. Existing campaigns are not forcibly migrated: use a new 1337
campaign for the authored dynasty and government setup.

This branch includes the 0.5.1 terrain source and the portrait test pass. Its
prepared installer and metadata are **0.5.2**. The branch remains separate from
main; the published 0.5.0 release is unchanged. Static setup and build checks do
not certify in-game succession, maternal inheritance or portrait rendering.

# 0.5.1 terrain development (source integration)

- Wider CindermawÃ¢â‚¬â€œBrackmaw and BrackmawÃ¢â‚¬â€œSootwake channels; land area reduced 12%.
- Individual coast profiles with broad bays, headlands and restrained coastal erosion.
- 15 Cindermaw, 12 Brackmaw, four Reefhook, three Shatterfin and two Sootwake playable tiles. Province groupings remain unchanged.
- National populations and total starting RGO expansion are preserved when subdividing locations.
- Wider crater bowls and raised rims; dark lava aprons, exposed rock and reduced woodland on dry volcanic ground.
- New raster checks enforce channel clearance, island continuity and playable tile size.
- Static validation passed: 36 connected land tiles, 31 coastal ports, all settlement anchors, navigable sea graph, population totals, rivers and scenery; terrain cache shared-border error is zero. Final shoreline gaps are 40.79 pixels (CindermawÃ¢â‚¬â€œBrackmaw) and 26.93 pixels (BrackmawÃ¢â‚¬â€œSootwake), up from 5.00 and 5.39.
- Full game rendering and navigation acceptance require a new campaign. Published archives and existing installations are unchanged; build from source to test this terrain pass.

---
# Development on main after 0.5.0

- Merged the release and goblin-model art branches into main. Code > Download ZIP now reconstructs the prepared release and applies checked development files.
- Added five native goblin infantry variants, materials, clan graphics selection and 17 animation exports. Idle, movement, attack, retreat and charge are wired; engine rendering and death-event integration remain pending. Cavalry and equipment fitting need separate work. The portrait test pass is documented below.
- Renamed the shared culture group to Ashborn, with Emberblood, Brineward, Reefstrider, Stormfang and Ashveil cultures. Technical IDs are preserved.
- Native checks cover 51 source/engine pose comparisons, palettes, graphics references and exact native asset round trips. The main-download installer preparation path was tested.
- The published 0.5.0 archives and currently installed games are unchanged. Use a fresh main download to test the development additions.

# Goblins of the Ashborn Isles 0.5.0 - Ironfang Isles

For **Europa Universalis V 1.3.11 (Pavia)**. **Close the game, install, and start a NEW 1337 campaign.** Earlier saves are incompatible with the expanded location map.

- Every island gains approximately 25% land area. Reefhook gains extra land and is about 20% larger than either smaller rival clan. Native land and navigable sea lanes are preserved.
- Cindermaw now has 12 locations in 6 provinces; Brackmaw has 8 in 4. The smaller clans retain two locations each. National population totals remain unchanged.
- Terrain follows continuous island geology: Cindermaw's mountain spine, irregular foothills, craters, eroded valleys, beaches, woodland, exposed rock and short rivers. Ground materials no longer change at administrative borders. Native tree and rock meshes add visible scenery to all six islands.
- All six clans use **Ironfang Monarchy**, a unique reform with native monarchy mechanics. **Rule of the Strongest** selects an eligible adult male Goblinkin by Military ability, with administration and age breaking ties. The rule can be changed; removing the reform restores ordinary succession if necessary.
- Voyages now reveal the Ashborn Isles to the current owners of the ports the goblins visit. Unrelated countries receive no scripted reveal.
- Every clan starts with modest capital industry and developed rural settlements: 27 village levels, two fiber-crop farms, and seven capital guilds. New clay, tar, fiber and wool sites supply production. A one-time first-month initialization adds 70 RGO capacity levels.
- The old 15% tax-income penalty is removed. Cindermaw's first-month force is reduced to 1 footmen unit, 2 galleys and 3 cogs. Starting treasuries and development receive modest increases; unnecessary stockades in minor capitals are removed.
- The introductory lore event now has one **The Ashborn rise.** button. Its former two options had identical gameplay results.

## Installation

Download **Goblins_Ashborn_Isles_0.5.0.zip**, extract it, close EU5 and run **Install-Goblins.cmd**. Enable only this mod for the first test and start a new campaign. The installer checks the game version through terrain hashes and backs up the prior mod outside the mod scan folder. Steam's game files are not edited.

The source package contains authored code and assets. Building requires a local EU5 installation, Python, NumPy and Pillow. See README.md and TESTING.md.

## Verification and remaining tests

The release includes static build, map, terrain and feature reports. Checks cover map connectivity, ports, untouched native geography, population totals, script references, terrain tile seams, height coverage, area ratios, river paths, scenery placement, province-independent terrain, reciprocal discovery and guarded RGO initialization. ZIP integrity and terrain reconstruction hashes are checked before publication.

**This is a test release.** The new visual biome must still be checked in the engine. Succession, reciprocal discovery and actual monthly budgets require playtesting; increased production is not a claim of a measured positive balance. Other terrain shaders or map/startup mods can conflict. See TESTING.md for focused acceptance steps.

No Steam Workshop publication is included.


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
graph [cm_goblin_cindermaw_schematic]`, producing invisible infantry. Its repair is
deferred while portraits are prioritised; this portrait pass does not claim to fix it.


All five Ashborn cultures have 16 male and 16 female name entries, six house names and six lowborn names each. Four additional royal families and 15 adult courtiers are authored. Drogg Cindermaw bears the nickname "the Stone Fletcher"; Jaima Shatterfin bears "the Mare-Mother". Cabinet appointments remain native, drawing on culture-specific names and the available court.
# 0.5.3 integrated infantry illustrations

- Original goblin regiment artwork for all five Ashborn cultures, including levies.
- Preserves native recruitment, stats and human artwork; no custom regiments required.
- Includes the latest shared-pose infantry attachment repair and companion contact event.
- One medieval painting is shared across infantry types and ages in this first pass.
- Prepared installer updated and checksum-verified; in-game acceptance pending.
