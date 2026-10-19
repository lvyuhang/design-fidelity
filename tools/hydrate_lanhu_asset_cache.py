#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description='Materialize exported Lanhu assets from verified local SHA-256 cache hits.')
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--cache-root', required=True, action='append', type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    cache: dict[str, Path] = {}
    for root in args.cache_root:
        for path in root.rglob('*'):
            if path.is_file() and path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.svg'}:
                cache.setdefault(digest(path), path)
    copied = []
    existing = []
    misses = []
    for asset in manifest.get('assets', []):
        target = args.output / asset['relative_path']
        expected = asset['sha256']
        if target.exists() and digest(target) == expected:
            existing.append(asset['node_id'])
            continue
        source = cache.get(expected)
        if source is None:
            misses.append({'node_id': asset['node_id'], 'sha256': expected, 'relative_path': asset['relative_path']})
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied.append({'node_id': asset['node_id'], 'from': str(source), 'to': str(target)})
    result = {'status': 'PASS' if not misses else 'PARTIAL', 'copied': copied, 'existing': existing, 'misses': misses}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'cache-hydration.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'copied': len(copied), 'existing': len(existing), 'misses': len(misses)}, ensure_ascii=False))
    return 0 if not misses else 1


if __name__ == '__main__':
    raise SystemExit(main())
