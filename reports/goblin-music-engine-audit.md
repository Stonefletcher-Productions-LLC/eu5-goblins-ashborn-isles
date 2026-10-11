# EU5 1.3.11 audio war-state audit

Observed 2026-10-11 in the isolated test profile. Automatic peace and war entry work; return to peace fails on both nested and flattened music-switch candidates. A forced False state also fails while paused.

Static executable audit (preferred image base 0x140000000):
- Country audio collector at 0x140e98da0 checks country war-list count at +0x3dac. A nonempty list writes 1 at 0x140e98f76; the empty branch skips this write without clearing the flag.
- Global audio PlayerAtWar byte: RVA 0x75cb79d.
- Audio update at 0x140e99459 reads the flag and dispatches literal True or False.
- The other direct write at 0x140e9a75e copies the bulk audio snapshot byte at +0x3d. Located zero-snapshot callers are invalid-country/no-game paths, not normal valid-country updates.
- Exported Wwise SetState(string,string) at 0x1457ca310 lowercases and FNV1 hashes both strings. Case spelling is not the cause.

Read-only live corroboration: while the user was at peace and paused on 2 May 1341, process12064 loaded base0x7ff718b50000. Reading exactly one byte at base+0x75cb79d returned1. No process memory was written. The game console visibly contained two audio.set_state PlayerAtWar False calls.

Conclusion: the engine audio snapshot remains latched at war in this session and repeatedly supplies that value. This is strong evidence for bypassing PlayerAtWar, not for changing playlist loop duration or more bank transition experiments. It is specific to this inspected version and does not establish every native music implementation is affected identically.

Proposed workaround: complementary local GUI visibility callbacks use the current player's actual diplomacy IsAtWar and post two SetState-only events. A dedicated ga_music_war_state controls only goblin routes. Register its group explicitly in Init; preserve all existing groups and non-goblin routes. No synchronized gameplay effect or memory patch. Multiplayer and live reverse-transition acceptance remain required.