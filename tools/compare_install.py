"""Compare an isolated install with the packaged archive for the current version; write a receipt.

Usage: compare_install.py <repo> <gate> <receipt.json>
"""
import hashlib, json, sys, zipfile
from pathlib import Path

repo, gate, receipt = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
version = json.loads((repo/'data/island.json').read_text(encoding='utf-8'))['version']
inst = gate/'user/mod/goblins_ashborn_isles'
archive = repo/f'dist/Goblins_Ashborn_Isles_{version}.zip'
z = zipfile.ZipFile(archive)
terrain = json.loads(z.read('terrain_patch/manifest.json'))
want = {n[len('goblins_ashborn_isles/'):]: n for n in z.namelist() if n.startswith('goblins_ashborn_isles/') and not n.endswith('/')}
have = {p.relative_to(inst).as_posix() for p in inst.rglob('*') if p.is_file()}
reconstructed = {f['path'].replace('\\', '/') for f in terrain['files']}
missing = sorted(set(want)-have); extra = sorted(have-set(want)-reconstructed)
changed = sorted(r for r in set(want) & have if (inst/r).read_bytes() != z.read(want[r]))
for f in terrain['files']:
    assert hashlib.sha256((inst/f['path']).read_bytes()).hexdigest() == f['final_sha256'], f['path']
meta = json.loads((inst/'.metadata/metadata.json').read_text(encoding='utf-8-sig'))
r = {'version': meta['version'], 'files': len(have), 'missing': missing, 'extra': extra, 'changed': changed,
     'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'archive_bytes': archive.stat().st_size}
print(json.dumps(r, indent=2))
assert r['version'] == version and not (missing or extra or changed)
receipt.write_text(json.dumps(r, indent=2), encoding='utf-8')
