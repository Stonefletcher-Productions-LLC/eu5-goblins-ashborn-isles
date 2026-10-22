# Goblins 0.6.5 release in progress

Working copy `E:\Codex_EU5_Modding\goblins-ashborn-isles`. Branch `release/v0.6.5` from `main` (0.6.4.1, pushed after the October 13 history cleanup; the local `v0.6.4.1` tag still points at the pre-cleanup commit, so it is not pushed). Remote: Bitbucket `stonefletcher/goblins-ashborn-isles` (remote name `bitbucket`, SSH). GitHub is retired (account suspended).

Change: `cm_ironbark`, `cm_pitchfang`, `cm_emberhollow` raw material tar -> lumber in `data/island.json`. Tar has no raw-material RGO in EU5 1.3.11 (players could not build them up; error.log showed `rgo_workers:tar`/`raw_resource:tar`). The corrected `location_templates.txt` ships as an overlay `mod/in_game/map_data/location_templates.txt` over the reused 0.6.4.1 map/terrain base (`archipelago.build_map` emits the same lines; after any full map rebuild, copy it there). `tools/refresh_overlay_bundle.py` accepts exactly these corrections (`RGO_FIXES`) during version promotion; `tools/economy.py` no longer exempts tar; `tools/verify_prepared_bundle.py` checks every packaged goblin raw material against `island.json`. `baseline_locations` in island.json is a historical record and still says tar for Ironbark.

Players need a new 1337 campaign for the fix; older saves keep loading.

Pending: build/verify/clean-install gate, active install, Workshop upload, Bitbucket push, then the in-game checks at the top of TESTING.md.

Multiplayer note (2026-10-13): a client's simulation stalled silently twice mid-session (no error, crash or OOS on either side); a later session from the same save ran 8 years cleanly before this fix. Cause unconfirmed; if it recurs, collect the client's logs before relaunch.

## Next release (0.6.6) pending: Silver Shard starvation

Silver Shard was the only location in `cm_shatterfin_outer_province`. Provinces share food, and a lone silver mine has none, so it starved permanently. It now belongs to `cm_shatterfin_province` (it borders Shatterfin and Shardpoint), and Shatterfin Outer is gone (39 provinces). The corrected `definitions.txt` ships as an overlay `mod/in_game/map_data/definitions.txt` over the reused map base, like the 0.6.5 `location_templates.txt` fix. `tools/refresh_overlay_bundle.py` accepts it via `PROVINCE_FIXES['0.6.6']` when promoting; `tools/verify_prepared_bundle.py` checks packaged province membership from 0.6.6. Bump the version to 0.6.6 and repackage before release. Needs a new 1337 campaign.

## Next release (0.6.6) pending: royal families and multiple wives

Cindermaw's dynasty died out within 20 years in a playtest. Rule of the Strongest only crowns adult men of the ruler's own dynasty, and each captain crown started with one or two such men. Every crown now starts with a large household (`ashborn_names.FAMILY_ROLES`): a dead father, an uncle and adult cousin, two brothers with wives and children, three wives for the ruler and five or six sons. Cindermaw, Brackmaw and Giltfang also have a married eldest son with an infant grandson. Shatterfin gains a sister for Jaimzha, more daughters and granddaughters (`shatterfin.FAMILY`). Existing heirs stay the strongest adult candidates; all new kin have lower Military. 153 authored goblin characters (was 51).

The Ashen Covenant adds `female_spouses = 3` to its `definition_modifier`, which stacks on Monogamous Marriage's 1 for four wives, the same cap as native Polygyny (whose `is_country_religion_pagan` whitelist excludes our religion group). Starting rulers use repeated `spouse =` lines, as native Gediminas does.

`04_dynasties.txt` and `05_characters.txt` ship as overlays over the reused bundle. `tools/goblin_families.py` swaps only the goblin rows in the bundled files and verifies dates, parentage, marriages and heirs; `prepare_main_overlay.py` runs it. Needs a new 1337 campaign. Engine-untested: the multi-wife setup, the spouse cap stacking and AI marriage behaviour.

## Next release (0.6.6) pending: Obsidian Fletchers unique unit

Goblins get a unique archer levy, `a_ga_obsidian_fletchers` (Age 1, from `a_age_1_traditions_light_infantry`: initiative +2, strength damage done and taken +10%, hills +0.15, mountains +0.10), upgrading to `a_ga_blackglass_crossbows` (Age 2) and then vanilla `a_early_arquebusiers`. Both are `levy = yes`, raised from peasants in any location whose dominant culture is in `cm_goblin_group` (`ga_obsidian_fletchers_location_trigger`), patterned on vanilla Longbowmen. Files: `mod/in_game/common/unit_types/goblins_units.txt`, `mod/in_game/common/scripted_triggers/goblins_units.txt`, `mod/main_menu/localization/english/goblins_units_l_english.yml`, all registered in `data/main_overlay.json`. `tools/verify_goblin_units.py` runs in the build (resolving vanilla upgrade targets) and in the bundle check from 0.6.6. The unit card uses the culture-wide goblin infantry painting fallback and the existing goblin 3D infantry; no dedicated art yet. Should load in existing saves; no new campaign needed for this part.
