# Goblins 0.6.5 release in progress

Working copy `E:\Codex_EU5_Modding\goblins-ashborn-isles`. Branch `release/v0.6.5` from `main` (0.6.4.1, pushed after the October 13 history cleanup; the local `v0.6.4.1` tag still points at the pre-cleanup commit, so it is not pushed). Remote: Bitbucket `stonefletcher/goblins-ashborn-isles` (remote name `bitbucket`, SSH). GitHub is retired (account suspended).

Change: `cm_ironbark`, `cm_pitchfang`, `cm_emberhollow` raw material tar -> lumber in `data/island.json`. Tar has no raw-material RGO in EU5 1.3.11 (players could not build them up; error.log showed `rgo_workers:tar`/`raw_resource:tar`). The corrected `location_templates.txt` ships as an overlay `mod/in_game/map_data/location_templates.txt` over the reused 0.6.4.1 map/terrain base (`archipelago.build_map` emits the same lines; after any full map rebuild, copy it there). `tools/refresh_overlay_bundle.py` accepts exactly these corrections (`RGO_FIXES`) during version promotion; `tools/economy.py` no longer exempts tar; `tools/verify_prepared_bundle.py` checks every packaged goblin raw material against `island.json`. `baseline_locations` in island.json is a historical record and still says tar for Ironbark.

Players need a new 1337 campaign for the fix; older saves keep loading.

Pending: build/verify/clean-install gate, active install, Workshop upload, Bitbucket push, then the in-game checks at the top of TESTING.md.

Multiplayer note (2026-10-13): a client's simulation stalled silently twice mid-session (no error, crash or OOS on either side); a later session from the same save ran 8 years cleanly before this fix. Cause unconfirmed; if it recurs, collect the client's logs before relaunch.
