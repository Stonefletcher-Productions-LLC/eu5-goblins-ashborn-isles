# Earlier 0.5.5 prototype — The Gathering of the Five

**Archived add-on instructions:** the full 0.5.5 release includes this content.
Install it with `Install-Goblins.cmd` and disable the separate prototype. The
installation steps below apply only to the earlier add-on with 0.5.4. Gameplay
rules and test cases remain useful.

Built on `staging/0.5.4` for EU5 1.3.11. **Static checks passed; engine parsing,
UI behavior, AI use and gameplay balance have not been tested.**

## Install the small prototype add-on

1. Keep the installed, working Goblins **0.5.4** base mod.
2. Download this branch with GitHub **Code → Download ZIP**, and extract it.
3. Close EU5 and run **Install-Prototype-055.cmd**.
4. Enable **both** the base Goblins mod and **Goblins 0.5.5 - Gathering Prototype**.
5. Restart EU5 and start a **new 1337 campaign**. The Gathering becomes eligible in July 1337.

This installs a separate, small add-on. It does not replace the base mod, alter
playsets or rebuild terrain. Disable the add-on to return to 0.5.4; use a base-only
save rather than continuing a prototype save with missing scripted definitions.
Do not enable this add-on alongside a full future 0.5.5 build: those scripts would
be duplicated. The regular installer still contains the previous release bundle;
**use the prototype installer for this branch**. This is not a Workshop release.

For preparation without installation:

```powershell
.\Install-Prototype-055.ps1 -PrepareOnly
```

## Implemented

- Mixed island populations: 323,941 additional goblins, including 231,332 slaves.
  Every district has all four foreign Ashborn cultures. Capital ports draw
  more newcomers and some free merchants; mining districts favor captive labor.
  Minorities comprise about 16–22% of each nation (20% across the isles),
  leaving home clans at 78–84%. These represent settled migrants, captives and
  their descendants accumulated over the islands' history.
  The distribution uses seed 1337055 and stays fixed between installs. Existing
  home-culture populations, classes, religions and district majorities remain.
  All additions follow the Hunger Below. No humans are added.

| Kingdom | Added goblins | Of those, slaves | New total population |
|---|---:|---:|---:|
| Cindermaw | 159,949 | 133,351 | 712,688 |
| Brackmaw | 73,355 | 50,012 | 391,818 |
| Reefhook | 21,955 | 10,414 | 130,392 |
| Shatterfin | 49,120 | 28,543 | 262,607 |
| Sootwake | 19,562 | 9,012 | 121,191 |

The prototype installer now creates a population setup override from the
installed 0.5.4 base, appending these entries without editing that base. Enable
the prototype after the base in load order so its `06_pops.txt` takes precedence.
Re-running the installer starts from the base again and does not stack additions.
`tools/generate_mixed_populations.py` regenerates the authored distribution;
`tools/prepare_prototype_055.py` refreshes its installer manifest. The full source
builder uses the same distribution. The regular prepared release remains 0.5.4.

- Cindermaw's **Drogg, the Stone Fletcher** (78/80/96) leads a militaristic Emberblood realm of muster yards, forge captains and ridge defenses. Expanded lore explains his nickname, House Cindermaw's **One fire, many blades** saying, Grakka's concern for provisions, Grask's ambition for command and Kragga's attention to court alliances. Its influence rests on weapons, patronage and protection, while its claims to leadership meet resistance from the other crowns. The introduction is **One Fire, Many Blades**. These institutions and relationships are narrative flavor; ruler abilities are the balance change.

- Brackmaw's Murgash is **the Sluice-King**, an exacting marsh engineer and provision broker (ADM 84, DIP 78, MIL 90). His nickname recalls sacrificing his hall's embankment to save Brackhaven's granaries in the Blackwater Flood. Expanded Brineward culture text and **The Sluice-King's Bargain** introduction connect the marsh houses, tidal gates, coastal workshops and supply oaths to his rivalry with Cindermaw. These are character setup and flavor changes; situation actions and their costs remain unchanged.
- Reefhook's **Skrezz, the Wreck-Taker** (62/88/90) combines rescue obligations, shoal pilotage, pearl trade and risky foreign friendships. House Reefhook's rescue-beacon tradition, brother Krizzek's fishing-household interests and consort Zikka's Shoalcut ties shape its court. Its introduction is **The Wreck-Taker's Share**.
- Sootwake's **Snikh, the Blackbough** (80/54/90) protects woodland settlements through firebreaks, guarded paths and cutting oaths. House Sootwake's rootwood-table tradition, brother Zhor's wardens and consort Zheska's charcoal households give its court competing claims. Its introduction is **Beneath the Blackbough**.
- Shatterfin’s **Jaima, the Mare-Mother** retains her existing 66/58/52 abilities and maternal seniority. The expanded **The Tidemother’s Terms** introduction (`ga_gathering.13`) brings her own terms to the Gathering. It schedules **The Maternal House Endures** (`ga_gathering.15`) 30 days later, a Shatterfin-only, once-only family council involving Skritcha, Morzha, Rikkra and Vrosh. These two narrative events alter no stats, heir, succession law or diplomatic relationship. Their authored source is `data/shatterfin.json`; all five kingdoms have lore in `LORE.md`.
- The prototype installer derives character and localization overrides from the installed 0.5.4 base. It changes these four rulers' abilities, adds the three new nicknames and updates their culture descriptions. Drogg's existing Stone Fletcher nickname is preserved exactly once. Other characters and text are preserved, including house names, family relationships and succession. Shared authored sources are `data/cindermaw.json`, `data/brackmaw.json`, `data/reefhook.json` and `data/sootwake.json`; full lore is in `LORE.md`. The court roles, house sayings, customs and rescue/fire stories are narrative flavor, without additional economic or succession mechanics.

- Two native situations: Gathering of the Five, followed by Eastern Hunger.
- All five starting kingdoms participate; kingdom names may change with dynasty.
- Opening choice and one introductory event for each kingdom, a Shatterfin
  follow-up, plus response and completion events: 14 events total.
- Seven situation actions: offer an alliance, transfer paid aid, negotiate
  voluntary vassalage, obtain subjugation or province conquest CBs, prepare the
  eastern fleet and choose an eastern conquest objective.
- Offers persist their sender in the recipient and recheck eligibility when
  answered. Pending offers cannot overwrite one another. AI may refuse.
- Submission needs an alliance, recipient opinion of at least 125, recipient
  strength at most 65% of the proposer, and adequate proposer country rank.
  Normal vassal obligations apply. The recipient receives ten years of +10
  subject loyalty. No dynasty, ruler or succession law is changed.
- Every one of the 72 starting homeland locations must be owned by the claimant,
  a qualifying vassal chain, or a junior partner under that claimant's senior
  union authority. Vassals beneath junior partners also count. Alliances,
  tributaries, occupations and foreign-held or unowned districts do not count.
- Unions are obtained through native EU5 mechanics. This prototype recognizes
  senior/junior unions; it does not script union creation or Shatterfin succession
  changes. A loose federal union without a senior crown is not the winning realm.
- Eastern preparation costs 20 gold and gives five years of -15% transport
  construction cost and +5% naval morale, with a ten-year cooldown.
- Selecting a discovered European coastal province costs 10 gold and gives a
  five-year CB using the native province conquest war goal and peace rules.
  Re-selecting changes the permitted objective. Truces and allies are excluded.
  Loss of homeland unity blocks further eastern actions and use of this CB.
- A European coastal foothold held within the qualifying realm ends the eastern situation, granting
  10 prestige and five years of +5% naval morale recovery. A pre-existing,
  legitimately acquired foothold qualifies too.
- **No free foreign land, troops, ships, foreign subjects or automatic declarations.**
- AI action lists and weights favor friendly negotiations, and gate CB planning
  on native attack desire; eastern AI planning also requires manpower and a navy.
  Normal EU5 AI decides whether to declare and conduct a war. Successful naval
  invasion behavior is not yet established.

## Deferred from the larger proposal

Ascendancy scoring, a formal Council organization, anti-hegemon defensive blocs,
repeatable harbor crises, bespoke union bargaining and negotiated tribute
discounts are not in this first prototype. Kingdom-specific events currently
provide flavor and guidance, rather than unique contribution mechanics.

## First test pass

Check a new campaign for the population totals above, foreign Ashborn minorities
and their slave/free classes. Cindermaw's existing home-culture slaves remain in
addition to its 133,351 new foreign-culture slaves. Check load order if the world
still has 1,294,755 goblins. Gameplay and economic balance remain untested.

1. Start as each kingdom in turn; confirm the Gathering panel appears and the
   opening and correct kingdom event fire. As Shatterfin, check The Tidemother’s Terms and The Maternal House Endures 30 days later; save/reload before the follow-up and advance further to confirm it does not repeat. Other kingdoms must not receive these two events. Check localization and available actions.
2. Offer a Harbor Pact; test acceptance and refusal. Confirm acceptance creates
   an alliance and does not complete the situation or create a subject.
3. Send supplies: the sender loses 10 gold, the recipient receives 10, and opinion
   improves. Verify cooldowns and affordability.
4. Build an eligible alliance and offer the Compact. Test refusal, acceptance,
   and a save/reload with a pending offer. Change war status before responding;
   an invalid acceptance should disappear while refusal remains available.
5. Vassalize Shatterfin; verify its house, Tidemother reform and heir law survive.
6. Test conquest and subjugation CBs, using normal declarations and peace deals.
7. Unify through direct ownership, vassals, and a senior/junior union. Leave one
   district outside the realm and confirm the situation remains active.
8. Confirm Eastern Hunger follows completion. Explore Europe, pay for preparation
   and select a coast. No land, units or ships should appear from these actions.
9. Check the eastern CB province and owner, expiry, changed ownership, and lost
   homeland unity. Win a foothold normally and inspect the completion reward.
10. Observe an AI-only run: pacts, aid, CB planning, spending and naval readiness.

After a failure, inspect the EU5 `logs/error.log` for `ga_gathering`,
`goblins_gathering` or `ga_cb_eastern_foothold`, and record the date and country.
Custom trigger scopes, situation selectors and AI choices particularly need
in-engine acceptance. No claim of engine compatibility follows from static checks.

## Rebuild and verify scripts

Seventeen original paintings cover all fourteen new events, both situations and
the seven existing introduction/exploration events. Events use explicit native
`image` paths; situation headers and icons resolve by situation ID. Original PNGs
and complete generation prompts are in `art/events/`. The prototype manifest
carries every texture and all three event files. The regular installer is still
the prior 0.5.4 package; these changes ship through the prototype add-on.

```powershell
python tools/gathering.py
python tools/export_event_art.py
python tools/verify_055.py --game "E:\SteamLibrary\steamapps\common\Europa Universalis V\game"
```

The generator is integrated into the full build and receives its prepared map
configuration. Regenerate the prototype checksum manifest after script changes:

```powershell
python tools/prepare_prototype_055.py
python tools/verify_event_art.py
```

Static checks parse script structure, resolve declared native CB/relation/price
and modifier references, check localization, and evaluate the generated homeland
ownership predicates over 14 regression scenarios. They also reject scripted
land/unit grants and automatic declarations. They do not execute EU5.
