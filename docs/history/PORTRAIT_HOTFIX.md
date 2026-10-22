# Human portrait regression hotfix — 0.5.3

Cause: custom skin and attachment genes were ordinary DNA genes with no neutral template; the skin decal remained opaque at zero strength. Culture-scoped modifiers did not stop ordinary DNA defaults from rendering.

Fix: use native `special_genes` for opt-in skin and attachments; remove special visual genes from ethnicity DNA. Keep culture-scoped portrait modifiers and ethnicity facial proportions. The 0.5.3 rough clothing gene also uses `special_genes` and an additive scoped modifier.

Validation: native rig/texture/reference checks passed for all five cultures and seven portrait types. Regression check rejects the original ordinary-DNA structure. Overlay checksums refreshed. No engine validation yet.

Installed game: 0.5.2; EU5 was running, so installed files were not changed. The 0.5.2 branch provides Apply-Portrait-Hotfix.cmd with checksum checks and backup/rollback. It patches only genes and ethnicity definitions after EU5 closes. Saves are untouched. Check both an existing save and a new campaign; existing DNA recovery is not yet established.

Next: restart with the patched local mod; verify human rulers in England, Castile and a non-European nation retain native skin/ears, while all five goblin cultures retain goblin visuals, including women and children. No GitHub or Workshop publish performed by this fix; existing prepared archives have not been rebuilt.
