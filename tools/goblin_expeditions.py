"""Open vanilla EU5 1.4 expeditions that goblins are kept out of only by geography.

The Ashborn Isles sit in Macaronesia (continent africa, sub-continent north_africa),
so two vanilla expedition types never show for goblins although nothing else about
them is European:
- western_ocean_voyage_expedition (the Atlantic crossing) asks for a capital in
  western_europe;
- grand_tour_expedition (an heir's tour of Italy) asks for a capital in Europe.

Each file is copied from the installed game with only its potential widened by
`ga_goblin_voyager = yes`; every other condition (open_sea_exploration, the age,
institutions, gold, the heir) still applies. The copies are regenerated from the
game on every build, so they follow vanilla changes.

Already open to goblins without changes: the holy site pilgrimage (the Ashen
Covenant has holy sites), the highland prospecting survey and, once they research
Explorer Commissions, the coastal survey.
"""
import argparse
from pathlib import Path
import build as b

PATCHES = {
    'in_game/common/expedition_types/western_ocean_voyage.txt': (
        '\t\tOR = {\n\t\t\tcapital = { sub_continent = sub_continent:western_europe }\n',
        '\t\tOR = {\n\t\t\tcapital = { sub_continent = sub_continent:western_europe }\n\t\t\tga_goblin_voyager = yes\n'),
    'in_game/common/expedition_types/grand_tour.txt': (
        '\t\tcapital = {\n\t\t\tcontinent = continent:europe\n\t\t\tNOT = { region = region:italy_region }\n\t\t}\n',
        '\t\tOR = {\n\t\t\tcapital = {\n\t\t\t\tcontinent = continent:europe\n\t\t\t\tNOT = { region = region:italy_region }\n\t\t\t}\n\t\t\tga_goblin_voyager = yes\n\t\t}\n'),
}
FILES = list(PATCHES)


def patch(native, old, new):
    text = native.replace('\r\n', '\n')
    assert text.count(old) == 1, 'Vanilla expedition potential changed; update goblin_expeditions.PATCHES'
    return text.replace(old, new)


def build(game, out=b.ROOT / 'mod'):
    for rel, (old, new) in PATCHES.items():
        b.write(out, rel, patch(b.read(game, rel), old, new))
    return FILES


def verify(read):
    for rel, (old, new) in PATCHES.items():
        text = read(rel)
        assert text.count('ga_goblin_voyager = yes') == 1, rel
        assert new in text.replace('\r\n', '\n'), rel
    triggers = read('in_game/common/scripted_triggers/goblins_exploration.txt')
    assert 'ga_goblin_voyager = {' in triggers
    return {'patched_vanilla_expeditions': FILES}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--game', type=Path, required=True)
    args = ap.parse_args()
    build(args.game)
    print(verify(lambda p: (b.ROOT / 'mod' / p).read_text(encoding='utf-8-sig')))
