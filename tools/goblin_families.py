"""Regenerate the goblin royal families in the starting-setup overlays.

0.6.6 ships 04_dynasties.txt and 05_characters.txt as overlays over the reused
prepared bundle, like the map_data fixes. This reads both files from the bundle
in .release, removes every authored goblin row, and injects the rows that
ashborn_names.court_rows and shatterfin.family_rows generate now. Native rows
are left byte-for-byte unchanged. No game installation is needed; a full build
(archipelago.build_setup) emits the same goblin rows.
"""
import argparse, base64, hashlib, io, json, re, zipfile
from datetime import date
from pathlib import Path
import ashborn_names, goblin_nobility, shatterfin

ROOT = Path(__file__).resolve().parents[1]
TAGS = ('cdm', 'qbr', 'rhk', 'sfk', 'swk', 'gtf')
GOBLIN_ROW = re.compile(r'^(?:cm_(?:' + '|'.join(TAGS) + r')_\w+|cm_shatterfin_dynasty) = \{.*\}\s*$')
COURT = re.compile(r'_(?:court|noble|clergy|guild)_')
LOWBORN = re.compile(r'_(?:clergy|guild)_')
FILES = {'main_menu/setup/start/04_dynasties.txt': 'dynasty_manager',
         'main_menu/setup/start/05_characters.txt': 'character_db'}


def bundle(root=ROOT):
    manifest = json.loads((root / '.release/manifest.json').read_text())
    asset = manifest['assets'][0]
    raw = b''.join(base64.b64decode((root / '.release' / p).read_bytes(), validate=True) for p in asset['chunks'])
    assert len(raw) == asset['size'] and hashlib.sha256(raw).hexdigest() == asset['sha256']
    return zipfile.ZipFile(io.BytesIO(raw))


def replace_rows(text, rows):
    """Swap the contiguous run of goblin rows for new ones, keeping native rows and CRLF."""
    lines = text.split('\r\n')
    hits = [i for i, line in enumerate(lines) if GOBLIN_ROW.match(line)]
    assert hits, 'No authored goblin rows found'
    first = hits[0]
    # Authored rows sit together at the end of the block, at most separated by blank lines.
    assert all(GOBLIN_ROW.match(l) or not l.strip() for l in lines[first:hits[-1] + 1]), 'Goblin rows are not contiguous'
    kept = lines[:first] + [l for l in lines[first:hits[-1] + 1] if not GOBLIN_ROW.match(l) and l.strip()] + lines[hits[-1] + 1:]
    return '\r\n'.join(kept[:first] + rows + kept[first:])


def generated(config):
    dynasties, characters = ashborn_names.court_rows(config['countries'])
    return {'main_menu/setup/start/04_dynasties.txt': [shatterfin.dynasty_row()] + dynasties,
            'main_menu/setup/start/05_characters.txt': shatterfin.family_rows() + characters
            + goblin_nobility.rows(config['countries'])}


def build(root=ROOT):
    config = json.loads((root / 'data/island.json').read_text(encoding='utf-8'))
    rows = generated(config)
    with bundle(root) as z:
        for rel in FILES:
            text = z.read('goblins_ashborn_isles/' + rel).decode('utf-8')
            out = root / 'mod' / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(replace_rows(text, rows[rel]).encode('utf-8'))
    return verify(root)


def verify(root=ROOT):
    chars = (root / 'mod/main_menu/setup/start/05_characters.txt').read_bytes().decode('utf-8')
    dyn = (root / 'mod/main_menu/setup/start/04_dynasties.txt').read_bytes().decode('utf-8')
    people = {}
    for line in chars.split('\r\n'):
        if GOBLIN_ROW.match(line):
            ident = line.split(' ', 1)[0]
            assert ident not in people, 'Duplicate character ' + ident
            people[ident] = line
    houses = set(re.findall(r'(?m)^(cm_\w+_house_\d+|cm_shatterfin_dynasty) = ', dyn))
    seen = set()
    now = date(1337, 11, 11)
    born = lambda row: date(*map(int, re.search(r'birth_date = ([\d.]+)', row)[1].split('.')))
    summary = {}
    for ident, row in people.items():
        dynasty = re.search(r'dynasty = (\w+)', row)
        assert (dynasty[1] in houses) if dynasty else ('last_name = ' in row and LOWBORN.search(ident)), ident
        assert born(row) <= now, ident
        for parent in re.findall(r'\b(?:mother|father) = (cm_\w+)', row):
            assert parent in seen, 'Parents must precede children: ' + ident
            assert (born(row) - born(people[parent])).days >= 16 * 365.25, ident
        for spouse in re.findall(r'\bspouse = (cm_\w+)', row):
            assert ident in re.findall(r'\bspouse = (cm_\w+)', people[spouse]), 'One-sided marriage: ' + ident
        seen.add(ident)
    for tag in TAGS:
        if tag == 'sfk':
            continue
        prefix = 'cm_' + tag + '_'
        family = {i: r for i, r in people.items() if i.startswith(prefix) and not COURT.search(i)}
        alive = {i: r for i, r in family.items() if 'death_date' not in r}
        men = [i for i, r in alive.items() if 'female = yes' not in r and i != prefix + 'ruler']
        adults = [i for i in men if (now - born(alive[i])).days >= 18 * 365.25]
        wives = re.findall(r'\bspouse = (cm_\w+)', people[prefix + 'ruler'])
        sons = [i for i, r in alive.items() if 'father = ' + prefix + 'ruler' in r and 'female = yes' not in r]
        assert len(wives) == 3 and len(sons) >= 3 and len(men) >= 8 and len(adults) >= 2, tag
        # The established heir stays the strongest adult man of the ruling house.
        heir = prefix + ('brother' if tag in {'rhk', 'swk'} else 'son')
        mil = lambda i: int(re.search(r'\bmil = (\d+)', alive[i])[1])
        assert max(adults, key=mil) == heir and all(mil(i) < mil(heir) for i in adults if i != heir), tag
        summary[tag.upper()] = {'living_family': len(alive), 'wives': len(wives), 'sons': len(sons),
                                'men_of_the_house': len(men), 'adult_men': len(adults)}
    women = [i for i, r in people.items() if i.startswith('cm_sfk_') and not COURT.search(i) and 'death_date' not in r
             and 'female = yes' in r and 'mother = ' in r and (now - born(r)).days >= 18 * 365.25]
    summary['SFK'] = {'eligible_adult_women': len(women)}
    # Courtiers: enough adults of each estate for cabinets, and unmarried adults to marry.
    courts = {}
    for tag in TAGS:
        prefix = 'cm_' + tag + '_'
        court = {i: r for i, r in people.items() if i.startswith(prefix) and COURT.search(i)}
        adults = {i: r for i, r in court.items() if (now - born(r)).days >= 18 * 365.25}
        estates = {e: sum('estate = ' + e in r for r in adults.values()) for e in ('nobles_estate', 'clergy_estate', 'burghers_estate')}
        single = [i for i, r in adults.items() if 'spouse = ' not in r]
        assert estates['nobles_estate'] >= 20 and estates['clergy_estate'] >= 3 and estates['burghers_estate'] >= 3, tag
        assert sum('female = yes' in adults[i] for i in single) >= 6 and sum('female = yes' not in adults[i] for i in single) >= 6, tag
        # Courtiers never share the ruling dynasty, so succession is untouched.
        ruling = 'cm_shatterfin_dynasty' if tag == 'sfk' else prefix + 'house_0'
        assert all('dynasty = ' + ruling + ' ' not in r for r in court.values()), tag
        courts[tag.upper()] = {'courtiers': len(court), 'adults': len(adults), 'unmarried_adults': len(single), **estates}
    summary['courts'] = courts
    return {'goblin_characters': len(people), 'families': summary, 'engine_tested': False}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify-only', action='store_true')
    args = ap.parse_args()
    print(json.dumps(verify() if args.verify_only else build(), indent=2))
