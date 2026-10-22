# Goblins of the Ashborn Isles 0.6.4.1 — release plan

Status: implemented 2026-10-12; release via build/release-0641 scripts. See HANDOFF.md for outcome. Base: 0.6.4 (Workshop item 3814944518, EU5 1.3.11).
All changes below ship as **0.6.4.1**. Patch release: no starting-world changes, so
existing 0.6.4 saves must keep loading.

## 1. Workshop page art is broken (GitHub account suspended)

All seven description images and the README link point to
`raw.githubusercontent.com/stonefletcher/eu5-goblins-ashborn-isles` / `github.com/...`,
which no longer resolve. The Workshop preview gallery (steamusercontent) is unaffected.

Broken references in `STEAM_DESCRIPTION.txt`:

| Line | Asset (repo path `art/workshop/0.6.0/`) | Bytes |
|---|---|---|
| 5  | banner.jpg         | 1,126,433 |
| 24 | ashborn-map.png    |   207,951 |
| 46 | giltfang.jpg       | 1,061,296 |
| 54 | gathering.jpg      | 1,260,229 |
| 62 | harbor-bargain.jpg | 1,190,923 |
| 72 | voyages.jpg        | 1,182,363 |
| 80 | eastern-hunger.jpg | 1,167,411 |
| 91 | "GitHub installer ZIP" install route | — |
| 99 | `[url=https://github.com/.../README.md]` | — |

Bitbucket (`stonefletcher/goblins-ashborn-isles`) is **private**, so its raw URLs only
work for a signed-in owner and are not a valid replacement.

Plan:
- [x] Host the seven images on Steam: add them to item 3814944518's own image
      gallery (Workshop page → Add/edit images & videos), then copy each image's
      `images.steamusercontent.com/ugc/...` URL. Steam-hosted URLs do not depend on
      any code host.
- [x] Replace the seven `[img]` URLs in `STEAM_DESCRIPTION.txt` with those URLs.
- [x] Line 91: drop the GitHub installer route (Workshop subscription only), unless a
      public download host is chosen.
- [x] Line 99: remove the GitHub README link; point feedback to the Workshop
      discussions/comments instead.
- [x] Record the new URLs and SHA-256 hashes in `build/release-0641/release-art-0641.json`
      (replaces `build/release-art-063.json`, which lists the dead GitHub URLs).
- [ ] After publishing, load the Workshop page signed **out** and confirm all seven
      images render.

Open decision: whether the Bitbucket repo should become public (would allow raw
image links and a README link). Default for this release: no — Steam-hosted art only.

## 2. Release tooling still targets GitHub

- `tools/publish_release.py` requires `GITHUB_REF_NAME`.
- `.github/workflows/` (installer, event/art, publication) no longer run.
- `.local/publish_github_061.py` publishes to GitHub.
- [ ] Publish 0.6.4.1 to Steam with the existing uploader (`goblins-config.json`, as in
      `build/steam-release-064.log`); skip the GitHub publication steps.
- [ ] Note in `HANDOFF.md` that GitHub publication is retired.

## 3. Crash-on-reload findings (from the 2026-10-12 crash reports)

The crash came from loading a goblin save without the mod active ("Missing mods:
Goblins of the Ashborn Isles" → continue → access violation). That is not a mod bug,
but players need to be told about it, and the logs show these mod-side errors:

- [x] Workshop description, "Install and continue": add "If EU5 warns that
      Goblins of the Ashborn Isles is missing when loading a save, cancel and
      enable the mod in your playset; continuing will crash."
- [x] `te_ashborn_cindermaw.dds` "not found": not a mod bug. The file ships and is a valid
      DXT5 like the other five; only the player country's flag fails, before mod graphics mount.
- [x] `shatterfin.txt` BOM: already fixed in 0.6.4 (warning came from an older build).
- [x] `gfx/portraits/portrait_modifiers/zzz_ashborn_outfits.txt`: hair accessories
      not found in gene template `all_hair` (`female_ashanti_hair_short_afro`,
      `female_syrian_braided_back_hair`, `female_iroquois_straight_parted_hair`,
      `female_hair_long_basic`, `female_german_braid_hair_behind`,
      `female_aztec_horn_braid_hair`, `boy_short_hair_a`, `boy_german_hair_bob_short`)
      and "Both value and accessory are set" (15×).
- [x] `map.cpp: Unknown reference to location! Key: ''`: likely the trailing empty row in
      `ports.csv` (CRLF + final newline; native file is LF without one). Normalized; confirm
      the log line is gone in game.
- [ ] Still needed: a crash folder from a player who crashes **with** the mod enabled.

## 4. Version bump

- [ ] `.metadata/metadata.json` → `"version": "0.6.4.1"`.
- [ ] `STEAM_DESCRIPTION.txt` header and `README.md` → 0.6.4.1.
- [ ] `RELEASE_NOTES_0.6.4.1.md`, `STEAM_CHANGELOG.txt` entry, Steam change notes.

## Developer setup note

The local test machine loads both the `Documents/.../mod/goblins_ashborn_isles` copy and
the Workshop copy (same id `alex.goblins_ashborn_isles`), and the "Goblins" playset is
empty. Test 0.6.4.1 with exactly one copy enabled.
