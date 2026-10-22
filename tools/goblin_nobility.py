"""Noble houses, oathkeepers and guild masters for every goblin crown.

The royal households (ashborn_names, shatterfin) left each crown with few
courtiers, so cabinets and marriage choices were thin. Each crown now starts
with five Highfang noble households (head, wife, grown and young children),
three Oathkeepers of the Ashen Covenant and three guild masters. Rows are
reproducible: every value comes from a per-crown seeded generator.

None of these characters can inherit a crown: Rule of the Strongest and the
Tidemother seniority only consider the ruling dynasty, and no row here uses it.
"""
import random
from ashborn_names import POOLS, key, house_key

# (household index, noble house index). House 0 rules; houses 1-3 also hold the
# authored courtiers and 4-5 the royal wives' kin, so every house gets a seat.
NOBLE_HOUSES = (1, 2, 3, 4, 5)
CLERGY = 3
GUILD = 3


def _date(rng, year):
    return f'{year}.{rng.randint(1, 12)}.{rng.randint(1, 28)}'


def _stats(rng, focus=None):
    """Ordinary courtiers sit in the 35-70 band; one stat may be a strength."""
    stats = [rng.randint(35, 70) for _ in range(3)]
    if focus is not None:
        stats[focus] = rng.randint(72, 88)
    return stats


def rows(countries):
    characters = []
    for country in countries:
        tag = country['tag']
        _, culture, males, females, _, lowborn = POOLS[tag]
        males, females, lowborn = males.split(), females.split(), lowborn.split()
        # Leave the ruler's, consort's and heirs' names to the royal family.
        males, females = males[3:], females[2:]
        capital = country['capital']
        prefix = 'cm_' + tag.lower()
        rng = random.Random('goblin-nobility-' + tag)

        def person(ident, name, born, female=False, dynasty=None, last=None, estate='nobles_estate',
                   stats=None, extra=''):
            adm, dip, mil = stats or _stats(rng)
            fields = [f'first_name = {{ name = {key(name)} }}']
            if last:
                fields.append(f'last_name = {{ name = {key(last)} }}')
            fields += [f'culture = {culture}', 'religion = cm_hunger_below']
            if dynasty:
                fields.append(f'dynasty = {dynasty}')
            fields += [f'estate = {estate}', f'tag = {tag}', f'birth = {capital}', f'birth_date = {born}',
                       f'adm = {adm}', f'dip = {dip}', f'mil = {mil}']
            if female:
                fields.append('female = yes')
            characters.append(f'{ident} = {{ ' + ' '.join(fields) + (' ' + extra if extra else '') + ' }')

        for n, house in enumerate(NOBLE_HOUSES):
            dynasty = house_key(tag, house)
            ident = f'{prefix}_noble_{house}'
            # Heads span 1278-1296 so some houses have grown grandchildren-age heirs.
            head_year = 1278 + n * 4 + rng.randint(0, 2)
            wife_year = head_year + rng.randint(2, 7)
            head_name, wife_name = rng.choice(males), rng.choice(females)
            # The wife comes from the next noble house along, tying the houses together.
            wife_house = house_key(tag, NOBLE_HOUSES[(n + 1) % len(NOBLE_HOUSES)])
            person(ident + '_head', head_name, _date(rng, head_year), dynasty=dynasty, stats=_stats(rng, n % 3),
                   extra=f'spouse = {ident}_wife')
            person(ident + '_wife', wife_name, _date(rng, wife_year), True, wife_house, stats=_stats(rng, (n + 1) % 3),
                   extra=f'spouse = {ident}_head')
            # Two unmarried grown sons, two unmarried grown daughters and a child:
            # the marriage pool and future cabinet candidates.
            first = wife_year + rng.randint(18, 21)
            children = [('son', False, first), ('daughter', True, first + 2), ('son_2', False, first + 4),
                        ('daughter_2', True, first + 6), ('child', rng.random() < .5, 1330 + rng.randint(0, 6))]
            used = {head_name, wife_name}
            for role, female, year in children:
                pool = [x for x in (females if female else males) if x not in used]
                name = rng.choice(pool)
                used.add(name)
                focus = rng.choice((0, 1, 2, None)) if year <= 1319 else None
                person(f'{ident}_{role}', name, _date(rng, min(year, 1336)), female, dynasty,
                       stats=_stats(rng, focus), extra=f'father = {ident}_head mother = {ident}_wife')
        # Oathkeepers and guild masters are lowborn: a byname instead of a dynasty.
        bynames = rng.sample(lowborn, CLERGY + GUILD)
        for i in range(CLERGY):
            female = i == 1
            person(f'{prefix}_clergy_{i}', rng.choice(females if female else males), _date(rng, rng.randint(1288, 1312)),
                   female, last=bynames[i], estate='clergy_estate', stats=_stats(rng, (0, 1, 0)[i]))
        for i in range(GUILD):
            female = i == 2
            person(f'{prefix}_guild_{i}', rng.choice(females if female else males), _date(rng, rng.randint(1290, 1314)),
                   female, last=bynames[CLERGY + i], estate='burghers_estate', stats=_stats(rng, (0, 1, 0)[i]))
    return characters
