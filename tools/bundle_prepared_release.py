"""Bundle a verified install ZIP, reusing unchanged archive transport chunks.

The resulting ZIP has one active directory and no duplicate entry names. Its
prefix is the previous ZIP; appended records and a new central directory replace
changed members. Both Python and the Windows installer must verify extraction.
"""
import argparse, base64, hashlib, json, shutil, zipfile
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base-root',type=Path,required=True)
    ap.add_argument('--prepared-root',type=Path,required=True)
    ap.add_argument('--source-commit',required=True)
    args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    config=json.loads((root/'data/island.json').read_text(encoding='utf-8'))
    version=config['version']
    assert config==json.loads((args.prepared_root/'data/island.json').read_text(encoding='utf-8'))
    report=json.loads((args.prepared_root/'build/reports/validation.json').read_text(encoding='utf-8'))
    assert report['version']==version and 'STATIC VALIDATION PASSED' in report['status']
    previous=json.loads((args.base_root/'.release/manifest.json').read_text())
    base=next(a for a in previous['assets'] if 'Source' not in a['name'])
    base_bytes=b''.join(base64.b64decode((args.base_root/'.release'/p).read_bytes(),validate=True) for p in base['chunks'])
    assert len(base_bytes)==base['size'] and sha(base_bytes)==base['sha256']
    name=f'Goblins_Ashborn_Isles_{version}.zip'
    candidate=args.prepared_root/'dist'/name
    with zipfile.ZipFile(candidate) as z:
        assert z.testzip() is None
        desired={i.filename:z.read(i) for i in z.infolist()}
    overlay=json.loads((root/'data/main_overlay.json').read_text())
    assert overlay['base_release']==version
    for item in overlay['files']:
        raw=(root/'mod'/item['path']).read_bytes()
        assert sha(raw)==item['sha256'],item['path']
        assert desired['goblins_ashborn_isles/'+item['path']]==raw, 'Stale candidate: '+item['path']
    assert desired['goblins_ashborn_isles/.metadata/metadata.json']==(root/'mod/.metadata/metadata.json').read_bytes()
    # The canonical packager defines the player payload. Do not replace its
    # player guide with the development README or inject development reports.
    for doc in ['README.md','RELEASE_NOTES.md','TESTING.md','LORE.md','Install-Goblins.ps1','Install-Goblins.cmd']:
        source=root/('PLAYER_README.md' if doc=='README.md' else doc)
        assert desired[doc].decode('utf-8-sig').replace('\r\n','\n')==source.read_text(encoding='utf-8-sig'), 'Stale guide: '+doc
    assert json.loads(desired['reports/validation.json'])==report
    assert not any(n.startswith('terrain_patch/') for n in desired), 'EU5 1.4 builds carry no terrain patch'
    destination=root/'dist'/name
    destination.parent.mkdir(exist_ok=True)
    destination.write_bytes(base_bytes)
    with zipfile.ZipFile(destination,'a',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        changed={n:b for n,b in desired.items() if n not in z.NameToInfo or z.read(n)!=b}
        # Retain all previous bytes, including its inactive central directory.
        z.start_dir=len(base_bytes)
        z.filelist=[i for i in z.filelist if i.filename in desired and i.filename not in changed]
        z.NameToInfo={i.filename:i for i in z.filelist}
        for n,b in changed.items():z.writestr(n,b)
    complete=destination.read_bytes()
    assert complete[:len(base_bytes)]==base_bytes
    with zipfile.ZipFile(destination) as z:
        assert len(z.namelist())==len(set(z.namelist()))==len(desired)
        assert z.testzip() is None
        for n,b in desired.items():assert z.read(n)==b,n
    release=root/'.release';(release/'assets').mkdir(parents=True,exist_ok=True)
    chunks=list(base['chunks'])
    for p in chunks:
        source=args.base_root/'.release'/p
        if source.resolve() != (release/p).resolve():
            shutil.copyfile(source,release/p)
    suffix=complete[len(base_bytes):]
    for i,offset in enumerate(range(0,len(suffix),512*1024)):
        rel=f'assets/{name}.update.{sha(suffix)[:12]}.{i:04d}.b64'
        (release/rel).write_bytes(base64.b64encode(suffix[offset:offset+512*1024]))
        chunks.append(rel)
    manifest={'version':version,'source_commit':args.source_commit,
              'source_config_sha256':sha((root/'data/island.json').read_text(encoding='utf-8').encode()),
              'assets':[{'name':name,'size':len(complete),'sha256':sha(complete),'chunks':chunks}]}
    (release/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'version':version,'archive_bytes':len(complete),'new_transport_bytes':len(suffix),'replaced_entries':len(changed),'entries':len(desired)},indent=2))

if __name__=='__main__':main()
