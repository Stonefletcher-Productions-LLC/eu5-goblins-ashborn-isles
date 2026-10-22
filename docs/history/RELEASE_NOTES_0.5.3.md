# 0.5.3 - Rough-Clad Goblins

Demo release for **Europa Universalis V 1.3.11 (Pavia)**. Fully restart the game and start a **new 1337 campaign**.

- Revised goblin features, subdued clan skin colours, compact adult proportions and plain clothing for all five Ashborn cultures; human appearance remains isolated.
- Repaired custom infantry through native shared-pose mesh attachments. User confirmed visibility and no recurrence of the reported crash on October 6, 2026. Further visual refinement is tracked in issue #4.
- Added original culture-scoped goblin infantry recruitment and army-card paintings without changing native unit statistics.
- Added **Strange Visitors on Our Shores** for owners of visited ports when expeditions establish reciprocal contact. The event is guarded once per non-Ashborn country.
- Consolidated the matching prepared installer and Workshop staging tools, full terrain caches, thumbnail and Steam BBCode description.

The five kingdoms, 36 land locations, six islands, thirteen sea zones, exploration routes, Ironfang succession and Shatterfin maternal seniority are included. The 0.5.4 economy, population, lifespan and younger-ruler work, and the 0.5.5 expansion chain, are not part of this release.

**Install:** download `Goblins_Ashborn_Isles_0.5.3.zip`, extract it into a new writable folder, close EU5 and run `Install-Goblins.cmd`. The compact installer reconstructs and verifies terrain using your matching game installation. Source downloads at this tag also include the matching prepared bundle.

**Steam upload:** use the separately prepared `Goblins_Ashborn_Isles_0.5.3_Workshop.zip`. Run its staging script, then update the existing Workshop item from the full `goblins_ashborn_isles` folder under the EU5 user-data `mod` directory. See `WORKSHOP_UPLOAD.md`. Publishing the GitHub release does not upload the Steam item.

**Remaining checks:** portrait/clothing appearance, recruitment illustrations, first-contact event behavior, succession edge cases, movement/combat/save-reload coverage, long-term balance and multiplayer. Static/package validation is separate from these checks.

