"""Append checksum-verified overlay changes to an existing prepared release."""
import base64, hashlib, io, json, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    release=ROOT/'.release'
    manifest=json.loads((release/'manifest.json').read_text())
    asset=manifest['assets'][0]
    raw=b''.join(base64.b64decode((release/p).read_bytes(),validate=True) for p in asset['chunks'])
    digest=lambda b:hashlib.sha256(b).hexdigest()
    assert len(raw)==asset['size'] and digest(raw)==asset['sha256']
    overlay=json.loads((ROOT/'data/main_overlay.json').read_text())
    assert overlay['base_release']==manifest['version']
    changed={}
    player_roots={'README.md','RELEASE_NOTES.md','TESTING.md','LORE.md',
                  'Install-Goblins.ps1','Install-Goblins.cmd','reports/validation.json'}
    with zipfile.ZipFile(io.BytesIO(raw)) as old:
        removed={n for n in old.namelist() if not n.startswith(('goblins_ashborn_isles/','terrain_patch/')) and n not in player_roots}
        for item in overlay['files']:
            data=(ROOT/'mod'/item['path']).read_bytes()
            assert digest(data)==item['sha256'],item['path']
            name='goblins_ashborn_isles/'+item['path']
            if name not in old.namelist() or old.read(name)!=data: changed[name]=data
        for name in ['Install-Goblins.ps1','README.md','RELEASE_NOTES.md','TESTING.md','LORE.md']:
            data=(ROOT/('PLAYER_README.md' if name == 'README.md' else name)).read_bytes()
            if name not in old.namelist() or old.read(name)!=data: changed[name]=data
    if not changed and not removed:
        print('Prepared bundle already matches overlay.');return
    buffer=io.BytesIO(raw)
    with zipfile.ZipFile(buffer,'a',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.start_dir=len(raw)
        z._didModify=True  # Re-emit the directory even for removal-only updates.
        z.filelist=[i for i in z.filelist if i.filename not in changed and i.filename not in removed]
        z.NameToInfo={i.filename:i for i in z.filelist}
        for name,data in changed.items(): z.writestr(name,data)
    full=buffer.getvalue();assert full[:len(raw)]==raw
    suffix=full[len(raw):]
    prefix=digest(suffix)[:12]
    for index,offset in enumerate(range(0,len(suffix),512*1024)):
        name=f'assets/overlay-{prefix}-{index:04d}.b64'
        (release/name).write_bytes(base64.b64encode(suffix[offset:offset+512*1024]))
        asset['chunks'].append(name)
    asset['size']=len(full);asset['sha256']=digest(full)
    (release/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (ROOT/'dist').mkdir(exist_ok=True)
    (ROOT/'dist'/asset['name']).write_bytes(full)
    print(json.dumps({'updated_entries':len(changed),'archive_bytes':len(full)}))

if __name__=='__main__':main()
