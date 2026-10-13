"""Append checksum-verified overlay changes to an existing prepared release."""
import argparse, base64, hashlib, io, json, subprocess, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--promote-version',action='store_true',help='Promote unchanged world configuration, retaining verified terrain')
    args=ap.parse_args()
    release=ROOT/'.release'
    manifest=json.loads((release/'manifest.json').read_text())
    asset=manifest['assets'][0]
    raw=b''.join(base64.b64decode((release/p).read_bytes(),validate=True) for p in asset['chunks'])
    digest=lambda b:hashlib.sha256(b).hexdigest()
    assert len(raw)==asset['size'] and digest(raw)==asset['sha256']
    overlay=json.loads((ROOT/'data/main_overlay.json').read_text())
    config_text=(ROOT/'data/island.json').read_text(encoding='utf-8')
    config=json.loads(config_text)
    assert overlay['base_release']==config['version']
    promotion=config['version']!=manifest['version']
    if promotion:
        assert args.promote_version, 'Version promotion requires --promote-version'
        try:
            prior=json.loads(subprocess.check_output(['git','show',manifest['source_commit']+':data/island.json'],cwd=ROOT,text=True))
        except subprocess.CalledProcessError:
            prior=None
        if prior is not None:
            assert prior['version']==manifest['version']
            prior['version']=config['version']
            assert prior==config, 'World configuration changed; regenerate and validate terrain/setup before packaging'
        else:
            # The source commit is unavailable (history re-created when moving
            # to Bitbucket). The manifest's recorded config hash is the same
            # binding: the current config with the old version must match it.
            old_version=json.dumps(manifest['version'])
            restored=config_text.replace('"version": '+json.dumps(config['version']),'"version": '+old_version,1)
            assert hashlib.sha256(restored.encode('utf-8')).hexdigest()==manifest['source_config_sha256'], 'World configuration changed; regenerate and validate terrain/setup before packaging'
    changed={}
    player_roots={'README.md','RELEASE_NOTES.md','TESTING.md','LORE.md',
                  'Install-Goblins.ps1','Install-Goblins.cmd','reports/validation.json'}
    with zipfile.ZipFile(io.BytesIO(raw)) as old:
        metadata=json.loads((ROOT/'mod/.metadata/metadata.json').read_text(encoding='utf-8'))
        assert metadata['version']==config['version']
        name='goblins_ashborn_isles/.metadata/metadata.json'
        if old.read(name)!=(ROOT/'mod/.metadata/metadata.json').read_bytes():
            changed[name]=(ROOT/'mod/.metadata/metadata.json').read_bytes()
        if promotion:
            for name in ('terrain_patch/manifest.json','reports/validation.json'):
                document=json.loads(old.read(name))
                assert document['version']==manifest['version']
                document['version']=config['version']
                if name.startswith('reports/'):
                    document['terrain_reuse']={'previous_version':manifest['version'],
                        'world_configuration_unchanged_except_version':True,
                        'note':'Inherited world checks; current authored overlay and native terrain hashes checked separately by package/install validation.'}
                changed[name]=(json.dumps(document,indent=2)+'\n').encode('utf-8')
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
    if promotion:
        manifest['version']=config['version']
        manifest['source_config_sha256']=digest(config_text.encode('utf-8'))
        asset['name']=f"Goblins_Ashborn_Isles_{config['version']}.zip"
    (release/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (ROOT/'dist').mkdir(exist_ok=True)
    (ROOT/'dist'/asset['name']).write_bytes(full)
    print(json.dumps({'updated_entries':len(changed),'archive_bytes':len(full)}))

if __name__=='__main__':main()
