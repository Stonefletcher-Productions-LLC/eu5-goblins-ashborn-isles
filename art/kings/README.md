# Crown ruler portraits

In-game ruler portraits are EU5's 3D character models, not images. Each 1337
crown ruler's look is set in `tools/build_goblin_portraits.py` (`KINGS`, plus
per-culture face offsets in `CLAN_FACE`) and `tools/build_goblin_outfits.py`
(`KING_CLOTHING`). Rebuild with `python tools/build_goblin_portraits.py` and
check with `python tools/verify_goblin_portraits.py --game <EU5>/game`.

| Ruler | Character | Build and face | Hair | Dress and regalia |
|---|---|---|---|---|
| Drogg, Cindermaw | `cm_cdm_ruler` | heavy warlord, square jaw, jutting brow, battle scar | brushed crest | bear-hunter hide coat, leather crown, black gorget |
| Murgash, Brackmaw | `cm_qbr_ruler` | stoutest, broad flat jowly face, short neck | receding | hooded wading cloak, cloth scarf |
| Skrezz, Reefhook | `cm_rhk_ruler` | lean, youngest, sharp chin and nose, wide eyes, grin | crest | sea-scarf, shell headband, coral beads |
| Snikh, Sootwake | `cm_swk_ruler` | gaunt, long narrow face, deep-set eyes | long | hide-and-fringe mantle, headband |
| Vrekk, Giltfang | `cm_gtf_ruler` | well-fed, long nose, small chin, jaw scar | balding | merchant kaftan, fur cap, chains of office |
| Jaimzha, Shatterfin | `cm_sfk_maarka` | long face, high cheekbones, strong jaw | horned braids | noble overcoat, pearl circlet, coral collar |

`codex_prompt.txt` asks Codex for six matching reference paintings, saved under
`sources/`. They are art direction and store-page art; the game does not read
them.
