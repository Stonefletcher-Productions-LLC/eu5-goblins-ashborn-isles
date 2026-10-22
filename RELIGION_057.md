# 0.5.7 — Oaths of Ash and Salt

Release branch: `release/v0.5.7`, including the published 0.5.6 repairs.
This first religion implementation is included in the complete 0.5.7 installer.
The limitations below remain; static checks do not establish gameplay acceptance.

## Implemented

`tools/ashen_covenant.py` generates eleven religion files into a supplied staging
directory. The normal full build calls it after Gathering generation and runs its
focused validator. `tools/build.py` supplies the new display name and description.
The stable `cm_hunger_below` religion ID, group and all population references remain.

- Six holy sites, one per island, each with a distinct local effect and lore.
- Eight native religious aspects; two slots, with five clan-specific initial pairs.
- Initial pairs are assigned on the first eligible monthly pulse only when a crown
  has zero aspects. A persistent flag prevents replenishing removed aspects.
- Covenant Favor uses native religious influence: base monthly gain 0.2 and a
  maximum-influence modifier of 100. These are modifiers, not a claim that the
  displayed final gain/cap ignores other game modifiers.
- Three own-country religious actions cost two scaled months of income plus 20
  Favor. Their bonuses last five years; a shared five-year variable blocks stacking.
  An AI action list exposes all three rites to native AI evaluation.
- Twelve eligible random stories, initially delayed one year, then a 5% monthly
  chance while eligible and a three-year cooldown after an event fires.
- The once-only Moot requires the existing Gathering unifier flag and homeland
  control. Local Covenants gives +1 heathen tolerance; First Oathkeeper gives
  +10% stability cost efficiency. Both are permanent until conversion away.
- Religion-specific country bonuses are removed on the next monthly pulse after
  conversion away. Initialization and Moot history remain, preventing repeat grants.

## Goblin estate names

The full build runs `tools/goblin_estates.py` to insert Ashborn-specific names
before the native estate-name alternatives. The condition checks the country's
primary culture against all five Ashborn cultures, so other countries keep their
existing names and goblin countries retain these labels if their religion changes.

| Native estate | Goblin name |
|---|---|
| Crown | Boss Clan |
| Nobility | Bigfangs |
| Clergy | Shamans |
| Burghers | Quay-Guilds |
| Commoners | Ashfolk |
| Tribes, if enabled | Warbands |
| Dhimmi, if enabled | Outsiders |
| Cossacks, if enabled | Freebooters |

These are estate display names only; population classes, privileges, estate IDs
and mechanics are unchanged. The generator preserves every native alternative
and fallback, and validates that removing its insertions restores the original
file. The generated native-file override remains in ignored build output.
Static parsing and priority checks passed; the estate panel still needs an
in-game check. Oathkeeper remains a religious office within the Shaman estate.

## Holy sites

| Site | District / island | Local effect |
|---|---|---|
| First Mouth | Cinder Crown / Cindermaw | +5% production efficiency |
| Listening Pool | Reedmouth / Brackmaw | +5% monthly food modifier |
| Lantern Steps | Tidefang / Reefhook | +0.001 monthly prosperity |
| Mothers' Basin | Shatterfin / Shatterfin | -0.05 unrest |
| Storm Teeth | Knifeback / Knifeback | +10% defensiveness |
| Emberroot Hollow | Ember Key / Sootwake | +10% defensiveness |

All sites have importance 3 and no country modifier. Shatterfin owns two different
local benefits, not two passive national religious bonuses. Native ownership,
control, religion and holy-site behavior require engine verification.

## Traditions and rites

| Tradition | National effect |
|---|---|
| Feed the Common Hearth | +5% monthly food modifier |
| Smoke Is an Offering | +5% production efficiency |
| Bring the Crew Home | +5% naval morale |
| The Dead Keep Their Names | +10% stability cost efficiency |
| No Axe Without an Oath | +10% defensiveness |
| Every Shore Has Spirits | +1 heathen tolerance |
| The First Share Goes Below | +5% land morale |
| Many Hearths, One Covenant | +5 percentage points clergy target satisfaction |

Cindermaw starts with Smoke / First Share; Brackmaw Hearth / Many Hearths;
Reefhook Crew / Shore Spirits; Shatterfin Crew / Dead; Sootwake Axe / Dead.

Feast of Returning Ash gives +10% stability cost efficiency; Lanterns Upon the
Water gives +10% naval morale; Renewal of the First Oath gives +10 percentage
points clergy target satisfaction. Each lasts five years.

## Deliberate first-pass limits

Tradition changes currently use native add/change/remove actions and their native
prices. A custom council cost/cooldown is not implemented. Adding a parallel
custom button alone would leave a native bypass, so this needs a separate pass.

The twelve stories currently share a simple economic choice: spend 5 gold for
5 Favor and 2 prestige, or take the unpaid option and lose 3 Favor. The paid choice
is hidden below 5 gold; the unpaid option always remains. Text concerning rescue,
burial or repairs describes that transaction: it does not create population,
emancipation, mining, disaster or building effects. Differentiated local outcomes,
scaled event costs and additional event art remain to be developed.

Holy-site restoration states, negotiated pilgrimage access, suppression rules,
custom religion/shrine artwork, and deeper reform opposition are not implemented.
Renewal of the First Oath presently reconciles clergy; it does not repair a
damaged-site state. Existing native graphics and the mod's event paintings are
used as staging art. No new mechanic is gated on a DLC.

## Validation

Run with a Python environment containing the existing build dependencies:

```text
python tools/verify_ashen_covenant.py --game "<EU5>/game"
python tools/verify_exploration.py --game "<EU5>/game"
python tools/verify_economy.py --game "<EU5>/game"
```

The religion check validates unique island placement, existing modifier keys,
starting pairs, encoding/braces, event localization/art references, routing,
initialization guards, Moot dispatch order, scaled prices and shared cooldowns.
It is not an engine parser or simulation. Output under `build/religion-check` is
a partial staging tree and must not be installed as a complete mod.

## Fresh-campaign acceptance before release

1. Check all five countries: religion name, Favor, two aspects after the first
   month, native aspect selection and no extra grants after save/reload.
2. Inspect all six holy sites and their local effects, including both Shatterfin
   islands. Check conquest, occupation and ownership by a foreign religion.
3. Use each rite in separate tests. Verify actual prices, affordability, shared
   cooldown, five-year expiry and persistence after save/reload.
4. Confirm AI can use rites without excessive treasury depletion.
5. Trigger all twelve stories, test below 5 gold and check appropriate eligibility.
6. Complete Gathering; inspect the Moot's two outcomes and verify no repeat on
   reload. Convert away and check cleanup after one month.
7. Recheck 0.5.7 sea-only starting charts and undiscovered foreign land, voyage
   timing, mixed populations and economy. See TESTING.md for screenshot acceptance.
8. Review the fresh game error log; package only after resolving new errors and
   completing the project's clean-download release gate.
