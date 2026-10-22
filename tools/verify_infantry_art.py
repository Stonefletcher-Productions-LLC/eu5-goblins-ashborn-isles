"""Check coverage, culture isolation and DDS contracts without claiming an engine pass."""
import hashlib, json, struct
from pathlib import Path
from PIL import Image
import build_infantry_art as art

def verify(game):
    root=art.ROOT
    report=json.loads((root/'art/infantry/validation.json').read_text())
    assert report['unit_types']==art.infantry_types(game)
    assert {'a_footmen','a_archers','a_villagers'} <= set(report['unit_types'])
    for name, (categories, source) in art.CATEGORIES.items():
        built=report['categories'].get(name)
        assert (built is None)==(name in report['pending_art']),name
        if built:
            assert built['unit_types']==art.unit_types(game,categories),name
            assert built['source_sha256']==hashlib.sha256((root/source).read_bytes()).hexdigest(),name
    assert len(report['culture_tags'])==len(__import__('ashborn_roster').TAGS)
    files=set(report['files'])
    assert files=={p.relative_to(root/'mod').as_posix() for p in (root/'mod'/art.REL).rglob('*.dds')}
    for name in files:
        assert any(Path(name).stem.endswith('_'+tag) for tag in report['culture_tags'])
        assert any(Path(name).stem.startswith(f'army_{c}_') for c in report['categories'])
        raw=(root/'mod'/name).read_bytes()
        mask='/masks/' in name
        assert raw[:4]==b'DDS '
        assert raw[84:88]==(b'DXT5' if mask else b'DXT1')
        assert struct.unpack_from('<I',raw,28)[0]==(6 if mask else 11)
        with Image.open(root/'mod'/name) as image:
            assert image.size==((32,32) if mask else (1080,440))
            if mask: assert image.getextrema()==((0,0),)*4
        if not mask: assert len(raw)==317512
    overlay=json.loads((root/'data/main_overlay.json').read_text())
    assert files <= {item['path'] for item in overlay['files']}
    for item in overlay['files']:
        assert hashlib.sha256((root/'mod'/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    return {'unit_types':{k:len(v['unit_types']) for k,v in report['categories'].items()},'pending_art':report['pending_art'],'cultures':len(report['culture_tags']),'textures':len(files),'engine_tested':False,'status':'static checks passed'}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--game',type=Path,required=True)
    print(json.dumps(verify(parser.parse_args().game),indent=2))
