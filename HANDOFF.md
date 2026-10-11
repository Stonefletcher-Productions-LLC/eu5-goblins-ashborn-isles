# Goblin music staging

Branch staging/ashborn-intro. Published main/Workshop remain0.6.3. Earlier introduction, localization, Horizon help and divorce fixes retained.

Accepted implementation reads local Player.GetDiplomacy.IsAtWar via complementary GUI _show callbacks and custom SetState-only events. Dedicated group inInit avoids EU5 native audio flag latchingTrue. Audit:reports/goblin-music-engine-audit.md. User confirms Cindermaw automatic peace-war-peace on2026-10-11. Non-goblin listening question pending; multiplayer and wartime-entry remain unverified.

Authored default outputs exactly match testedbank120a2507380663b967c1767e3ffc9f37a2c61177d30abe7be52f643f66086ccf,Init61d89a0f473a1fef4f2206911699d14ef30e7a42def727280e9d341974837ff5,GUI7131dc63ca27f8959946daeded237183ddc496ddc1a6ae03ffda022481a29e6e. Failed diagnosticflags removed. Builder requires native music+InitXML; skills updated. 224MODE+5376root+24independentstatecases+6latchedroundtrips pass;1975nativeobjects and nativeInit/GUI preserved except additions.

Fresh bundle verified302124916bytes,1936overlayfiles. Commit,cleanexportPrepareOnly/freshisolatedinstall,receipt andstagingpush pending. Do not claim release or multiplayer acceptance. Currentusergame isolatedPID2840/userpathE:/CodexScratch/goblins-divorce-review/user. User ownscontrols; noaudio capture. Testsourceexport atE:/CodexScratch/goblins-divorce-review/source is reproducible and may be replaced afterpathchecks; preserve user/saves. Launch game visibly only.
