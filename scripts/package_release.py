"""Archive a committed release candidate, Git replay history and built frontend."""
import argparse, hashlib, json, subprocess, tarfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--tag', default='v1.0.0-rc.1')
p.add_argument('--output', type=Path, default=root / '.release-archives')
a = p.parse_args()
revision = subprocess.check_output(['git', 'rev-parse', a.tag + '^{commit}'], cwd=root, text=True).strip()
a.output.mkdir(parents=True, exist_ok=True)
bundle = a.output / ('deva-' + a.tag + '.bundle')
source = a.output / ('deva-' + a.tag + '-source.tar.gz')
frontend = a.output / ('deva-' + a.tag + '-frontend.tar.gz')
subprocess.run(['git', 'bundle', 'create', str(bundle), '--all'], cwd=root, check=True)
subprocess.run(['git', 'bundle', 'verify', str(bundle)], cwd=root, check=True)
subprocess.run(['git', 'archive', '--format=tar.gz', '-o', str(source), a.tag], cwd=root, check=True)
with tarfile.open(frontend, 'w:gz') as archive:
    archive.add(root / 'apps/command/dist', arcname='frontend-dist')
manifest = {'version': a.tag, 'git_commit': revision, 'canonical_url': None,
            'deployment_status': 'PENDING', 'reconstruction': 'Clone the bundle; checkout the tag; install pinned requirements and npm ci; use REPLAY_MANIFEST.json.',
            'files': {f.name: {'sha256': hashlib.sha256(f.read_bytes()).hexdigest(), 'bytes': f.stat().st_size} for f in [bundle, source, frontend]}}
(a.output / ('deva-' + a.tag + '-archive-manifest.json')).write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
