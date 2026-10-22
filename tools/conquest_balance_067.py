"""Give Shatterfin the economic edge over Giltfang, once (Alex, 2026-10-22).

Shatterfin is meant to conquer Giltfang. After start_balance_067 it already
had more people, but Giltfang still had more building levels. This trims
Giltfang's market villages and duplicate industry (keeping its food villages)
and gives Shatterfin fishing villages and more town industry. Changes are
recorded in start_balance_067.shatterfin_over_giltfang.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGES = {
    # Giltfang: fewer market villages, marketplaces, tools guilds and smelters.
    'cm_chainhaven': {'tools_guild': -2, 'marketplace': -1},
    'cm_tolltooth': {'marketplace': -1},
    'cm_cinderfurrow': {'fiber_crops_farm': -1, 'market_village': -1},
    'cm_coppercut': {'local_smelters': -1},
    'cm_blackmeasure': {'local_smelters': -1},
    'cm_chainwood': {'market_village': -1},
    'cm_watchfang': {'market_village': -1},
    'cm_netreach': {'market_village': -1},
    'cm_lockshore': {'market_village': -1},
    'cm_lastlight': {'market_village': -1},
    # Shatterfin: fishing and farming villages where peasants can staff them,
    # and a stronger capital and naval town.
    'cm_gullwatch': {'fishing_village': 2},
    'cm_edgewater': {'fishing_village': 2},
    'cm_silver_shard': {'fishing_village': 2},
    'cm_gullscar': {'fishing_village': 1},
    'cm_stormpasture': {'farming_village': 1},
    # A second wharf (Shatterfin) and smelter (Stormcrag) exceeded the max level 1
    # in game (error.log, 2026-10-22) and were dropped.
    'cm_shatterfin': {'marketplace': 1, 'weapon_guild': 1},
    'cm_knifeback': {'marketplace': 1},
}


def apply(d):
    balance = d['start_balance_067']
    if 'shatterfin_over_giltfang' in balance:
        sys.exit('shatterfin_over_giltfang is already applied')
    byid = {l['id']: l for i in d['islands'] for l in i['locations']}
    for ident, changes in CHANGES.items():
        b = byid[ident]['buildings']
        for key, n in changes.items():
            b[key] = b.get(key, 0)+n
            assert b[key] >= 0, (ident, key)
            if not b[key]:
                del b[key]
    balance['shatterfin_over_giltfang'] = CHANGES


def main():
    path = ROOT/'data/island.json'
    d = json.loads(path.read_text(encoding='utf-8'))
    apply(d)
    path.write_text(json.dumps(d, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
