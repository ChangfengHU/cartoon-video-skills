#!/usr/bin/env python3
"""Copy command templates to an explicit directory; never overwrite different files."""
import argparse
from pathlib import Path


def install(client, target, apply=False):
    source = Path(__file__).resolve().parent / client
    if client not in ('pi', 'claude', 'codex-legacy'):
        raise ValueError('Unsupported client')
    target = Path(target).expanduser().resolve()
    files = sorted(source.glob('*.md'))
    import json
    expected = {c['name'] + '.md' for c in json.loads((source.parent / 'catalog.json').read_text())['commands']}
    if {f.name for f in files} != expected:
        raise ValueError('Incomplete command bundle')
    # Preflight the whole set before any write. Symlinks are not install targets.
    for item in files:
        dest = target / item.name
        if dest.is_symlink() or (dest.exists() and
            (not dest.is_file() or dest.read_bytes() != item.read_bytes())):
            raise FileExistsError(f'Existing command differs; no files written: {dest}')
    if apply:
        target.mkdir(parents=True, exist_ok=True)
        for item in files:
            dest = target / item.name
            if not dest.exists():
                with dest.open('xb') as handle:
                    handle.write(item.read_bytes())
    return {'client': client, 'target': str(target), 'files': [p.name for p in files],
            'applied': apply, 'runtime_verified': False}


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', required=True, choices=['pi', 'claude', 'codex-legacy'])
    parser.add_argument('--target-dir', required=True,
                        help='Explicit command directory, e.g. PROJECT/.pi/prompts')
    parser.add_argument('--apply', action='store_true', help='Write files; otherwise dry-run')
    args = parser.parse_args()
    print(json.dumps(install(args.client, args.target_dir, args.apply), ensure_ascii=False))
