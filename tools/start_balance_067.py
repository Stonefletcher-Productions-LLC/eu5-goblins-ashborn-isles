"""Apply the 0.6.7 start-game balance to data/island.json, once.

Alex's direction (2026-10-22): there are tons of goblins, but they are bad at
economics and catch up later; there must be enough food, and the markets must
trade. Shatterfin is meant to conquer Giltfang, so it starts larger.

- Every location becomes 40% tribesmen. Tribesmen eat no food, pay little tax
  and promote to peasants over time, which is the native catch-up.
- Shatterfin, Reefhook and Sootwake also gain peasants and laborers.
- Glass, paper, jewelry and mason guilds are trimmed to a minimum.
- Food villages and food RGO work go where the static food estimate is short;
  new fishers and farmers settle to staff villages that lack peasants.
- One tar kiln per market supplies naval supplies.

The applied changes are recorded in `start_balance_067` so verify_economy can
check older population policies against the population before this pass.
Trade routes live in economy.STARTING_TRADES.
"""
import collections
import json
import sys
from decimal import Decimal as D, ROUND_CEILING, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Q = D('0.001')
TRIBAL = D('0.40')
# Home plus mixed people each crown reaches before food settlers.
TOTALS = {'SFK': 500000, 'RHK': 260000, 'SWK': 240000}
# Native food value (goods) and per-class consumption (pop_types), 1.3.11.
FOOD = {'fish': 5, 'wheat': 8, 'livestock': 8}
EAT = {'nobles': 20, 'clergy': 5, 'burghers': 4, 'laborers': 1, 'soldiers': 5, 'peasants': 1, 'tribesmen': 0, 'slaves': 1}
VILLAGE_FOOD = {'fishing_village': 2.5, 'farming_village': 4, 'forest_village': 0.7}
VILLAGES = {'market_village', 'fishing_village', 'farming_village', 'forest_village'}
PROVINCE_FLOOR, CROWN_FLOOR = 0.2, 0.5
# Rural building cap at setup is about 2 levels per building type.
VILLAGE_CAP = 2
SMALL_CROWN_RGO = {'cm_sootwake': 5, 'cm_sootgrain': 3, 'cm_coralpasture': 3, 'cm_tidegrain': 2}
TAR_KILNS = ['cm_ember_key', 'cm_emberhollow', 'cm_knifeback']


def apply(d, mixed, ports):
    locs = [l for i in d['islands'] for l in i['locations']]
    country = {l['id']: l.get('country') or i['country'] for i in d['islands'] for l in i['locations']}
    caps = {c['tag']: c['capital'] for c in d['countries']}
    original = {l['id']: json.loads(json.dumps(l)) for l in locs}

    def mix(l):
        return sum((D(str(p['size'])) for p in mixed.get(l['id'], [])), D(0))

    def nontribal(l):
        return sum((D(str(v)) for k, v in l['pop_classes'].items() if k != 'tribesmen'), D(0)) + mix(l)

    def add(l, cls, amount):
        l['pop_classes'][cls] = float((D(str(l['pop_classes'].get(cls, 0))) + amount).quantize(Q))

    # 1. Smaller crowns gain working people: 70% peasants, 30% laborers.
    for tag, total in TOTALS.items():
        mine = [l for l in locs if country[l['id']] == tag]
        need = D(total)/1000*(1-TRIBAL) - sum(nontribal(l) for l in mine)
        assert need > 0, tag
        base = {l['id']: D(str(l['pop_classes'].get('peasants', 0)))+D(str(l['pop_classes'].get('laborers', 0))) for l in mine}
        for l in mine:
            share = need*base[l['id']]/sum(base.values())
            add(l, 'peasants', (share*D('0.7')).quantize(Q, ROUND_HALF_UP))
            add(l, 'laborers', (share*D('0.3')).quantize(Q, ROUND_HALF_UP))

    # 2. Thin luxury industry, keeping construction goods in every crown.
    def trim(tag, key, keep):
        mine = [l for l in locs if country[l['id']] == tag and key in l['buildings']]
        excess = sum(l['buildings'][key] for l in mine) - keep
        # Quarries keep their masons longest, then capitals keep their guilds.
        mine.sort(key=lambda l: (key == 'mason' and l['good'] == 'stone', l['id'] == caps[tag], -l['buildings'][key]))
        while excess > 0:
            l = next(l for l in mine if l['buildings'].get(key, 0) > 0)
            l['buildings'][key] -= 1; excess -= 1
            if not l['buildings'][key]:
                del l['buildings'][key]
    for c in d['countries']:
        tag = c['tag']
        # Cindermaw's own guilds use more paper than one guild makes.
        for key, keep in [('glass_guild', 1), ('paper_guild', 2 if tag == 'CDM' else 1), ('jewelry_guild', 1)]:
            trim(tag, key, keep)
        masons = sum(l['buildings'].get('mason', 0) for l in locs if country[l['id']] == tag)
        trim(tag, 'mason', masons - masons//2)

    # 3. Naval supplies need tar, which has no RGO: one wooded kiln per market.
    for l in locs:
        if l['id'] in TAR_KILNS:
            l['buildings']['tar_kiln'] = 1
        if l['id'] == 'cm_emberhollow':
            add(l, 'laborers', D('0.5'))  # tar burners to staff the kiln

    # 4. Food.
    def classes(l):
        c = collections.Counter({k: float(v) for k, v in l['pop_classes'].items()})
        for p in mixed.get(l['id'], []):
            c[p['type']] += p['size']
        return c

    def eat(l):
        return sum(EAT[k]*v for k, v in classes(l).items())

    def food(l):
        workers = min(classes(l)['laborers'], 2+l['rgo_expansion'])
        return workers*FOOD.get(l['good'], 0) + sum(VILLAGE_FOOD.get(k, 0)*n for k, n in l['buildings'].items())

    def option(l):
        if l['id'] in caps.values() or l.get('rank', 'rural_settlement') != 'rural_settlement':
            return None
        if l['good'] in ('wheat', 'livestock', 'wool'):
            return 'farming_village'
        return 'fishing_village' if l['id'] in ports else None

    def headroom(l):
        used = sum(n for k, n in l['buildings'].items() if k in VILLAGES)
        return classes(l)['peasants'] - 1.25*(used+1)

    def cover(members):
        return sum(map(food, members))/sum(map(eat, members))

    for l in locs:
        if l['id'] in SMALL_CROWN_RGO:
            l['rgo_expansion'] = SMALL_CROWN_RGO[l['id']]
    # Giltfang turns eight market villages into food villages.
    giltfang = sorted((l for l in locs if country[l['id']] == 'GTF' and l['buildings'].get('market_village')
                       and option(l) and l['buildings'].get(option(l), 0) < VILLAGE_CAP), key=lambda l: food(l)/eat(l))
    assert len(giltfang) >= 8
    for l in giltfang[:8]:
        l['buildings']['market_village'] -= 1
        if not l['buildings']['market_village']:
            del l['buildings']['market_village']
        l['buildings'][option(l)] = l['buildings'].get(option(l), 0)+1
    provinces = collections.defaultdict(list)
    for l in locs:
        provinces[l['province']].append(l)
    crowns = {c['tag']: [l for l in locs if country[l['id']] == c['tag']] for c in d['countries']}
    skip = set()
    while True:
        short = [(cover(m), p) for p, m in provinces.items() if cover(m) < PROVINCE_FLOOR and p not in skip]
        hungry = [(cover(m), t) for t, m in crowns.items() if cover(m) < CROWN_FLOOR and t not in skip]
        if not short and not hungry:
            break
        target = min(short)[1] if short else min(hungry)[1]
        pool = provinces[target] if short else crowns[target]
        pool = [l for l in pool if option(l) and l['buildings'].get(option(l), 0) < VILLAGE_CAP]
        if not pool:
            skip.add(target)
            continue
        l = max(pool, key=lambda l: (VILLAGE_FOOD[option(l)], headroom(l) >= 0, headroom(l)))
        l['buildings'][option(l)] = l['buildings'].get(option(l), 0)+1
        if headroom(l) < 0:
            # New fishers and farmers settle to staff the village (1.25k per level).
            add(l, 'peasants', D(str(-headroom(l))).quantize(Q, ROUND_CEILING))
    # Crowns still short work their food RGOs harder where laborers allow it.
    for tag, members in crowns.items():
        while cover(members) < CROWN_FLOOR:
            pool = [l for l in members if l['good'] in FOOD and l['rgo_expansion'] < 6
                    and classes(l)['laborers'] >= 4+l['rgo_expansion']]
            if not pool:
                break
            max(pool, key=lambda l: classes(l)['laborers']-l['rgo_expansion'])['rgo_expansion'] += 1

    # 5. Tribesmen are 40% of every location, home and mixed people included.
    record = {}
    for l in locs:
        l['pop_classes']['tribesmen'] = float((nontribal(l)*TRIBAL/(1-TRIBAL)).quantize(Q, ROUND_CEILING))
        l['pop'] = float(sum((D(str(v)) for v in l['pop_classes'].values()), D(0)))
        o = original[l['id']]
        entry = {}
        changes = {k: float(D(str(v))-D(str(o['pop_classes'].get(k, 0)))) for k, v in l['pop_classes'].items()
                   if D(str(v)) != D(str(o['pop_classes'].get(k, 0)))}
        buildings = {k: l['buildings'].get(k, 0)-o['buildings'].get(k, 0) for k in sorted(set(l['buildings']) | set(o['buildings']))
                     if l['buildings'].get(k, 0) != o['buildings'].get(k, 0)}
        if changes:
            entry['class_changes'] = changes
        if buildings:
            entry['building_changes'] = buildings
        if l['rgo_expansion'] != o['rgo_expansion']:
            entry['rgo_expansion_before'] = o['rgo_expansion']
        if entry:
            record[l['id']] = entry
    home, total = collections.Counter(), collections.Counter()
    for l in locs:
        home[country[l['id']]] += round(D(str(l['pop']))*1000)
        total[country[l['id']]] += int((D(str(l['pop']))+mix(l))*1000)
    d['start_balance_067'] = {
        'note': '0.6.7 start-game balance: many more goblins, mostly tribesmen (40% of every location), who eat no food, pay little tax and settle into peasants over time; thinner luxury industry; a food source in every province; seeded trade between the three markets. Applied by tools/start_balance_067.py.',
        'tribal_share': float(TRIBAL),
        'small_crown_totals': TOTALS,
        'prior_population_target': d['population_target'],
        'prior_country_population_targets': d['country_population_targets'],
        'total_country_targets': dict(total),
        'locations': record}
    d['country_population_targets'] = {k: int(v) for k, v in home.items()}
    d['population_target'] = int(sum(home.values()))
    return dict(total)


def main():
    path = ROOT/'data/island.json'
    d = json.loads(path.read_text(encoding='utf-8'))
    if 'start_balance_067' in d:
        sys.exit('start_balance_067 is already applied')
    mixed = json.loads((ROOT/'data/mixed_populations.json').read_text(encoding='utf-8'))['locations']
    ports = {line.split(';')[0] for line in (ROOT/'mod/in_game/map_data/ports.csv').read_text(encoding='utf-8-sig').splitlines()
             if line.startswith('cm_')}
    totals = apply(d, mixed, ports)
    path.write_text(json.dumps(d, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps(totals))


if __name__ == '__main__':
    main()
