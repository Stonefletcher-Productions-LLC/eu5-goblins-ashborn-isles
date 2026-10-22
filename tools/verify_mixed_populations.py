"""Verify native classes, additive demographics, and prepared population overrides."""
from collections import Counter
from decimal import Decimal
from pathlib import Path
import argparse
import json
import re
import mixed_populations as mixed

def verify(base, out, game):
    # Use the existing script parser to compare every original population entry.
    from verify_055 import parse
    cfg=json.loads((mixed.ROOT/'data/island.json').read_text())
    additions=mixed.additions()
    manifest=json.loads((mixed.ROOT/'data/prototype_055_files.json').read_text())
    old_bytes=base.read_bytes(); new_bytes=out.read_bytes()
    assert old_bytes.startswith(b'\xef\xbb\xbf')==new_bytes.startswith(b'\xef\xbb\xbf')
    before=parse(old_bytes.decode('utf-8-sig')); after=parse(new_bytes.decode('utf-8-sig'))
    def locations(ast):
        return next(v for k,op,v in ast if k=='locations')
    old=locations(before); new=locations(after)
    assert [(k,op) for k,op,v in old]==[(k,op) for k,op,v in new]
    native=(game/'main_menu/setup/start/06_pops.txt').read_text(encoding='utf-8-sig')
    native_classes=set(re.findall(r'\btype\s*=\s*(\w+)',native))
    cultures={c['culture'] for c in cfg['countries']}; summary={}
    expected={l['id']:(island['country'],cultures,next(c['culture'] for c in cfg['countries'] if c['tag']==island['country'])) for island in cfg['islands'] for l in island['locations']}
    assert set(additions)==set(expected)
    for (ident,_,prior),(_,_,current) in zip(old,new):
        if ident not in additions:
            assert prior==current,ident
            continue
        assert current[:len(prior)]==prior,ident
        expected_rows=parse('\n'.join(mixed.rows(ident)))
        assert current[len(prior):]==expected_rows,ident
        assert manifest['population_additions'][ident]=='\n'.join(mixed.rows(ident))
        tag,_,home=expected[ident]; stats=summary.setdefault(tag,Counter())
        foreign=set()
        for p in additions[ident]:
            assert p['culture'] in cultures and p['culture']!=home
            assert p['type'] in native_classes
            size=Decimal(str(p['size']))*1000
            assert size>0 and size==int(size)
            foreign.add(p['culture']);stats['added']+=int(size)
            if p['type']=='slaves':stats['slaves']+=int(size)
        assert len(foreign)==4
        # Every district remains overwhelmingly its home clan despite the uplift.
        homeland = sum(Decimal(dict((k, v) for k, op, v in row)['size'])
                       for kind, op, row in prior if kind == 'define_pop')
        assert homeland / (homeland + mixed.extra(ident)) >= Decimal('.70'), ident
    assert summary['CDM']['slaves']>sum(v['slaves'] for k,v in summary.items() if k!='CDM')
    assert len({v['added'] for v in summary.values()})==5
    for tag, stats in summary.items():
        # Measured against the crowns the minorities were generated for, before 0.6.7 grew them.
        home = cfg.get('start_balance_067', {}).get('prior_country_population_targets', cfg['country_population_targets'])[tag]
        minority_share = stats['added'] / (home + stats['added'])
        assert .15 <= minority_share <= .25, (tag, minority_share)
    return {'population':cfg['population_target']+sum(v['added'] for v in summary.values()),'countries':summary,'original_entries_preserved':True,'native_classes_checked':True,'engine_tested':False}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--game',type=Path,required=True)
    args=ap.parse_args();print(json.dumps(verify(args.base,args.out,args.game),indent=2))
