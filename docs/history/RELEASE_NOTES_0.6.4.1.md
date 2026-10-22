# Goblins of the Ashborn Isles 0.6.4.1

## Load-error fixes and restored Workshop art

- **Goblin hairstyles:** women and children now pick their curated styles from the game's own per-portrait hair lists. 0.6.4 logged 15 "Both value and accessory are set" warnings and 9 "Can't find accessory" errors at startup from these modifiers. Men keep their named styles. Women's and children's styles still need an in-game portrait check.
- **Ports:** `ports.csv` now matches the game's native format. The 0.6.4 file ended with an empty row that EU5 logged as an unknown location with an empty name. All 75 goblin ports are unchanged.
- **Missing-mod crash:** loading a goblin save while this mod is not enabled crashes EU5. If the game warns that **Goblins of the Ashborn Isles** is missing when you load a save, cancel, enable the mod in your playset and restart. Enable only one Goblins copy.
- **Workshop page:** description artwork is now hosted on Steam; the old GitHub links are retired.
- The installer accepts four-part version numbers.

Built for **EU5 1.3.11**. Restart before playing. Existing 0.6.4 saves can continue: no starting-world changes. All 0.6.4 music, divorce and event changes remain included.
