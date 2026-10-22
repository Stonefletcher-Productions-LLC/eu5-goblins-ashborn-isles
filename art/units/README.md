# Ashborn army illustrations

EU5 shows a 1080x440 painting on recruitment and army cards, cropped into three
360x440 frames. Each army illustration category gets one goblin painting in the
style of `art/infantry/ashborn_infantry.png`:

| Category  | Native unit categories                  | Unit types | Source painting                       |
|-----------|-----------------------------------------|-----------:|---------------------------------------|
| infantry  | army_light_infantry, army_heavy_infantry | 137 | `art/infantry/ashborn_infantry.png`   |
| cavalry   | army_light_cavalry, army_heavy_cavalry   |  73 | `art/cavalry/ashborn_cavalry.png`     |
| artillery | army_artillery                           |  16 | `art/artillery/ashborn_artillery.png` |
| auxiliary | army_auxiliary                           |  16 | `art/auxiliary/ashborn_auxiliary.png` |

`prompts.json` holds the generation prompt for each new painting. Every prompt asks
for exactly three subjects, one per frame, so each crop shows a whole goblin.
Fill in each painting's `sha256` once its PNG is committed.

`tools/build_infantry_art.py` writes `army_<category>_<unit_type>_<culture_tag>.dds`
for every unit type in the category plus an `army_<category>_<culture_tag>.dds`
fallback, for each Ashborn culture, with zeroed masks, exactly like infantry. A
category whose painting is missing is listed under `pending_art` in
`art/infantry/validation.json` and keeps native art. Navy illustrations are not
covered.

Rebuild and verify as described in `art/infantry/README.md`.
