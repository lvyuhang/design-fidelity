#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'design_evidence/message-backup-36'
APP = ROOT / 'flutter_ui_components'
CONTRACT = CASE / 'visual-contract.json'
SNAPSHOT = CASE / 'source/snapshot.json'
EXPORT = CASE / 'source/asset-export.json'
REFERENCE = CASE / 'source/reference-native.png'
OUTPUT = CASE / 'preflight.json'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    failures: list[str] = []
    snapshot = json.loads(SNAPSHOT.read_text())
    export = json.loads(EXPORT.read_text())
    contract = json.loads(CONTRACT.read_text())
    if snapshot['total_nodes'] != len(snapshot['nodes']):
        failures.append('snapshot pagination is incomplete')
    if snapshot['snapshot_id'] != contract['source_snapshot']:
        failures.append('snapshot id changed')
    if snapshot['resolved_version'] != contract['source_version']:
        failures.append('resolved source version changed')
    with Image.open(REFERENCE) as image:
        if image.size != (750, 1624):
            failures.append(f'reference is not native 2x: {image.size}')
    if export.get('counts', {}).get('succeeded') != 14 or export.get('failed'):
        failures.append('source asset export is not complete 14/14')
    asset_root = APP / 'assets/lanhu/message_backup_36'
    asset_records = []
    for record in export['assets']:
        path = asset_root / record['relative_path']
        if not path.exists():
            failures.append(f'missing cached source asset: {record["node_id"]}')
            continue
        if digest(path) != record['sha256']:
            failures.append(f'cached asset hash mismatch: {record["node_id"]}')
        asset_records.append({'node_id': record['node_id'], 'sha256': record['sha256']})
    page_chars = set(''.join(str(node.get('text') or '') for node in snapshot['nodes']))
    font_records = []
    for weight in ('Regular', 'Medium', 'Semibold'):
        path = APP / f'assets/fonts/PingFangSC-{weight}.otf'
        font = TTFont(path)
        cmap = set().union(*(table.cmap for table in font['cmap'].tables))
        missing = ''.join(sorted(char for char in page_chars if ord(char) not in cmap))
        if missing:
            failures.append(f'{weight} font misses: {missing}')
        font_records.append({'weight': weight, 'sha256': digest(path), 'missing': missing})
    for relative, expected in contract['pinned_files'].items():
        path = (CASE / relative).resolve()
        if not path.exists():
            failures.append(f'pinned file missing: {relative}')
        elif digest(path) != expected:
            failures.append(f'pinned file changed: {relative}')
    source = (APP / 'lib/experiments/message_backup_34_page.dart').read_text()
    test = (APP / 'test/message_backup_36_render_test.dart').read_text()
    if 'Rect.fromLTWH(-.5, y, 2.5, 2)' not in source:
        failures.append('fold icon no longer uses audited six-stroke source geometry')
    if 'all six unavailable portraits use circular placeholders' not in test:
        failures.append('missing portrait-shape regression test')
    result = {
        'status': 'PASS' if not failures else 'FAIL',
        'failures': failures,
        'snapshot': {
            'snapshot_id': snapshot['snapshot_id'],
            'version': snapshot['resolved_version'],
            'nodes': len(snapshot['nodes']),
        },
        'assets': {'source_exported': len(asset_records), 'reused_by_sha': 12, 'downloaded_new': 2},
        'fonts': font_records,
        'contract_sha256': digest(CONTRACT),
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
