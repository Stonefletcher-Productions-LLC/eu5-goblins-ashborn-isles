# Goblins 0.6.4.1 release in progress

Branch `release/v0.6.4.1` from `main` (0.6.4). Remote: Bitbucket `stonefletcher/goblins-ashborn-isles` (remote name `bitbucket`, SSH). GitHub is retired (account suspended); `tools/publish_release.py` and `.github/workflows` no longer run.

Changes: hair modifiers in `tools/build_goblin_outfits.py` (male by name, female/child by native list range slice; fixes 15 "Both value and accessory" + 9 "Can't find accessory" log lines), checks in `verify_goblin_portraits.py`; `ports.csv` normalized to native LF/no trailing row (fixes `map.cpp` empty location key), generator in `archipelago.py`, shipped as overlay `mod/in_game/map_data/ports.csv` (after any full map rebuild, copy the generated file there), bundle check in `verify_prepared_bundle.py`; installer accepts four-part versions. Workshop description images now Steam-hosted (gallery uploads, SHA-1 verified), GitHub links removed, missing-mod warning added. Plan: `RELEASE_PLAN_0.6.4.1.md`.

Not mod bugs: `te_ashborn_cindermaw.dds` "not found" (valid file; only the player's flag fails, before mod graphics mount); `shatterfin.txt` BOM (already fixed in 0.6.4). The 2026-10-12 reload crashes were a goblin save loaded with the mod inactive (empty "Goblins" playset).

Pending: build/verify/clean-install gate, active install, Workshop upload, Bitbucket push, then in-game checks in TESTING.md (hair styles, log lines, ports).
