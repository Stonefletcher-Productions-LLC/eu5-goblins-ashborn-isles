# Ashborn infantry illustrations

Original AI-generated artwork, created for this mod on 2026-10-06. Art direction:
short, wiry, ugly goblins, long pointed ears and hooked noses, scavenged iron,
patchwork cloth and leather, painted volcanic island shoreline. No native art
is redistributed by this generator.

`ashborn_infantry.png` is the authored source. `tools/build_infantry_art.py`
exports native-size 1080x440 BC1/DXT1 sheets with 11 mip levels and zeroed BC3
country-color masks. EU5 crops this sheet into three 360x440 UI frames.

Native reference: `main_menu/gfx/interface/illustrations/units/00_naming_convention.info`.
Exact `army_infantry_<unit_type>_<culture_tag>.dds` names have highest priority.
All 137 installed light/heavy infantry definitions (including templates and
levies) receive mappings for every Ashborn culture tag. No vanilla
filenames, unit definitions, unlocks, stats or recruitment rules are replaced.

Cavalry, artillery and auxiliary use the same builder; see `art/units/README.md`.

This first pass intentionally shares one medieval illustration across infantry
types and ages. Equipment-specific archer and gunpowder paintings are future work.
2D illustrations do not repair invisible 3D map units or character portraits.

Rebuild: `python tools/build_infantry_art.py --game <game> --update-overlay`
Then: `python tools/refresh_overlay_bundle.py`
Then: `python tools/verify_prepared_bundle.py`

Engine acceptance is pending: check recruitable infantry, levies, army detail,
and England/Castile as negative controls after completely restarting EU5.
