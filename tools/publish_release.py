"""Publish the exact validated installer without rewriting its contents."""
from pathlib import Path
import base64, hashlib, json, os, re, subprocess
from verify_prepared_bundle import verify

def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / '.release/manifest.json').read_text())
    version = manifest['version']
    assert re.fullmatch(r'\d+\.\d+\.\d+', version)
    branch = 'release/v' + version
    assert os.environ['GITHUB_REF_NAME'] == branch
    tag = 'v' + version
    existing = subprocess.run(['gh', 'release', 'view', tag], capture_output=True)
    if existing.returncode == 0:
        raise SystemExit('Release already exists; inspect it before changing assets.')
    print(json.dumps(verify(root), indent=2), flush=True)
    assert len(manifest['assets']) == 1
    item = manifest['assets'][0]
    assert item['name'] == f'Goblins_Ashborn_Isles_{version}.zip'
    raw = b''.join(base64.b64decode((root / '.release' / chunk).read_bytes(), validate=True)
                   for chunk in item['chunks'])
    assert len(raw) == item['size'] and hashlib.sha256(raw).hexdigest() == item['sha256']
    destination = root / 'dist'
    destination.mkdir(exist_ok=True)
    archive = destination / item['name']
    archive.write_bytes(raw)
    checksum = destination / 'SHA256SUMS.txt'
    checksum.write_text(f"{item['sha256']}  {item['name']}\n", encoding='utf-8')
    target = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    assert not subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], text=True).strip()
    subprocess.run(['gh', 'release', 'create', tag, str(archive), str(checksum),
                    '--target', target, '--title', f'[1.4] - Goblins of the Ashborn Isles {version}',
                    '--notes-file', str(root / f'RELEASE_NOTES_{version}.md'), '--latest'], check=True)

if __name__ == '__main__':
    main()
