# Playtest fixes and divorce action ready

Branch: staging/ashborn-intro. Current combined payload beac163; divorce source 1820b4f. Main/tag/Workshop and active installation remain released 0.6.3 without these pending changes.

Pending: once-per-country introduction for all six goblin kingdoms; proper Moot/rite modifier labels; Eastern Hunger announcement hover help; Dissolve a Royal Marriage action. Divorce uses the native divorce_character effect, selects a living current spouse, costs base 10 gold unaffected by inflation (normal action-cost modifiers apply), and adds no stability penalty. Junior union partners are excluded. No AI or player automation. Eligibility is by goblin crown, not religion or ruler sex.

Passed prior regressions, divorce eligibility/selector/effect/price/localization checks, prepared-bundle validation and stale-source rejection. Clean committed export PrepareOnly and isolated installation passed; all 1,981 installed files match, including reconstructed terrain.

Receipt: reports/ashborn-intro-candidate.json. Current clean source: E:/CodexScratch/goblins-divorce-review/source. Isolated target: E:/CodexScratch/goblins-divorce-review/user. Old horizon workspace was already absent when this task resumed; bundle transport was reused from the checkout. Reuse this gate for doc-only follow-ups.

No blocker. No active deployment or publication performed. Next: deploy/release when requested and verify action visibility, payment, selected-spouse divorce and tooltip rendering in game. These script/display changes should work in existing saves after restart; gameplay acceptance remains pending.
