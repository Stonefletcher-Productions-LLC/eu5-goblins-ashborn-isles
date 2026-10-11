# Goblin music prototype

Two original 60-second ElevenLabs Music v2 demos, generated for this mod:

* Ashen Harbors: peace, instrumental. Session 5plOnLee0Eon2NXBrOnN, generation 1DOikKiC9zOJJKu9uD7G.
* Black Sails, Ashen Teeth: war, goblin crew vocals. Approved revision; session kEZh2geoTyTfuyhNpuA4, generation oL95uDsIfrtBUbRdq3d6.

The user confirmed automatic peace → war → peace playback in the isolated Cindermaw test on October 11, 2026. This establishes that sequence for the tested local-state candidate; it does not establish multiplayer, every kingdom, wartime campaign entry or all music controls. Two short looping demos remain a prototype library, not a complete soundtrack. More and longer arrangements would reduce repetition.

MP3s are original generated masters. WEM derivatives use uncompressed 16-bit PCM, normalized to -20 LUFS / -2 dBTP, 48 kHz stereo. Rebuild them with FFmpeg through the bank builder's `--ffmpeg <executable>` option. Previous Vorbis derivatives decoded offline but were silent in EU5; their precise incompatibility remains unresolved.

## Routing and local war state

`tools/build_goblin_music.py` reads installed EU5 1.3.11 music and Init banks and their wwiser XML dumps. It rejects unrecognized native bank and topbar hashes. The complete native sound catalogue is preserved, with registrations for the custom media, state and events. Children are serialized before music containers, matching native load order. The two tracks are embedded in the music bank and play through looping playlists.

The music root sends goblin campaign-introduction requests through the mode selector, avoiding the native culture-introduction branch that has no goblin match. Native cultures keep their original introduction routes. The mode selector's PlayerCulturePrimary condition routes six goblin audio categories to the custom playlists; wildcard branches preserve native destinations and the no-music branch remains intact.

The tested engine's PlayerAtWar audio value remained at war after the player's wars ended. The working candidate therefore uses a separate `ga_music_war_state`, registered in Init, without changing the native state. Two invisible widgets in the existing in-game topbar read the local player's actual `Player.GetDiplomacy.IsAtWar` value. Their visibility transitions post `ga_music_peace` or `ga_music_war` on the native music manager. These audio events update only the custom state. They are not gameplay events and change no synchronized variables, diplomacy or campaign data.

Only goblin music routes consume that custom state. A non-goblin client's native routes do not use it. This provides a local-client design for multiplayer, but independent clients with different war states still need a live test.

The six categories match goblin graphical culture tags at priority 200, above native continental categories. Eligibility follows **primary culture**, including formed goblin countries that retain it. A country adopting a non-goblin primary culture follows native routing. Eligibility does not depend on ownership of goblin land or the other players.

## Rebuilding and acceptance

Build with `--game <EU5 installation> --xml <native music XML> --init-xml <native Init XML>`. The local audio-state routing is the default; the native Init XML is required. Add `--ffmpeg <executable>` to regenerate WEMs from the MP3 masters. Dump the resulting banks with wwiser and run `tools/verify_goblin_music.py` with the corresponding native and built XML inputs. Rebuild after game audio or topbar updates. Do not combine with another mod replacing the same music bank, Init bank or in-game topbar.

The runtime payload includes the music bank, Init state registration, native catalogue additions, culture definitions and topbar watcher together. Packaging and installation must keep those files in sync; an older music-only installer is not this tested candidate. Refer to `reports/goblin-music.json` for candidate-specific checks and `TESTING.md` for outstanding acceptance. Static routing checks cannot certify multiplayer or replace listening tests.
