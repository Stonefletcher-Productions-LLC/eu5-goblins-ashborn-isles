# Goblins of the Ashborn Isles 0.6.5

## Buildable timber in Blackwood and Giltfang

- **Ironbark, Pitchfang and Emberhollow** now produce **lumber**. They were set to tar, which has no raw-material production in EU5 1.3.11, so their RGOs could not be built up and the game logged missing `rgo_workers:tar` and `raw_resource:tar` entries. All three are wooded hills; their populations, buildings and charcoal makers are unchanged.
- The build checks no longer accept tar as a raw material, and the release check now confirms every goblin location's packaged raw material.

Built for **EU5 1.3.11**. Restart before playing. The fix applies to a **new 1337 campaign**: existing 0.6.4 and 0.6.4.1 saves keep loading, but those three locations stay on tar there. In multiplayer, every player needs the same version. All 0.6.4.1 fixes remain included.
