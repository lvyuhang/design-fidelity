#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CASE = ROOT / 'design_evidence/message-backup-34'
CASE = SOURCE_CASE / 'optimized-v1'
APP = ROOT / 'flutter_ui_components'
SNAPSHOT = SOURCE_CASE / 'source/snapshot.json'
REFERENCE = APP / 'design_evidence/message-backup-34/reference-mcp.png'
CONTRACT = CASE / 'visual-contract.json'
PREFLIGHT = CASE / 'preflight.json'

ASSET_FILES = {
    '16F0957E-9372-4BDD-8A38-74F925C77F4A': '133aceb46ccc07583e92c605bc539afd2e22fd2c024af2f90025e03941ab4544.png',
    '46973292-5A6D-42BF-9A6F-25D9168D09E8': '711bc34d080a29cb67efeb89cd437f9d2d85882884085eb93a584d436983bfba.png',
    '7A7E5242-D597-4010-ACA3-D9FB4A6A55F0': 'cc123c6bf5380b980ceb60f97f87b37e3118b855f479282363ec453729369e98.png',
    'AE344697-D0D3-4867-B3BC-AA722DBF1288': 'ba6ad713213694bd6d892e33d0effb4a9384c7002553201e6aad73e35f56276f.png',
    '1357B849-5FC7-4570-9A0A-EE53EAC3ED50': 'a25881b7d5ce15dcdb2811888680942ed9ce92f2384e935c5e9eb672bcc64457.png',
    '4C5886B0-AB45-4341-AF01-363FE0A5090B': '1cc08b902b88aba143242c42b1b3f8f2b3427a06f64b9c66746997c46790c075.png',
    '001D3A26-E9F7-4A8D-B848-BDBD5D64AEE9': 'a3109e049196a732525f8c4d7b65981c9d4b943e1da00cdad33c576bf2b1d0e9.png',
    'ED7DC567-6137-467A-B368-F2F41B9230A9': 'c5b435df1b9694e954a0f7039592d6b377caf13f87a26314173e862966065822.png',
    '09D2352B-F303-4358-838E-3EEAA4F2FE77': '3d9c1507231ab4216545fd4d47fc4e0016d132646d95dee832583047252607ef.png',
    '2105E345-1E59-4004-B9B2-11B3E6B1A221': '58ae7275356d68146c2e4d681bb589158c06ac2106b49b6365258198825ddb9c.png',
    '5355B69B-C35E-4D62-AF9D-59C52351451C': '7770bd50d14ae591e54a1b0b3df11747bb86d312886b8476d748cb4be6e485db.png',
    '7A0E367B-A662-48BB-BDCB-782745125976': '302d40e3cddc0c5dc27b8fca1058f2e9e4266b93ce88e0e3bbdc9dd8d49189dd.png',
    'F5203DE6-E6BA-4BEA-A600-9111889E746E': 'f905dce5939b9af6544739ee7933e79aef295cd8228323f52ddea84e9bfcc124.png',
}
OFFICIAL_ARTWORK_NODES = {
    '25D9025F-B947-469D-98F5-838C23F9566B',
    '15621591-9263-49EE-AF51-96E07BD315AF',
    'DD79DCD8-ED07-4519-9C0C-399D4F30F08C',
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(CASE)) if path.is_relative_to(CASE) else str(Path('../../..') / path.relative_to(ROOT))


def run_preflight() -> dict:
    snapshot = json.loads(SNAPSHOT.read_text())
    failures: list[str] = []
    checks: dict[str, object] = {}
    canvas = snapshot.get('canvas') or {}
    with Image.open(REFERENCE) as image:
        reference_size = list(image.size)
    expected_size = [int(canvas.get('width', 0) * 2), int(canvas.get('height', 0) * 2)]
    checks['reference'] = {'actual': reference_size, 'expected': expected_size, 'native_scale': 2}
    if reference_size != expected_size:
        failures.append('reference image is not the native 2x design export')
    if snapshot.get('total_nodes') != len(snapshot.get('nodes', [])):
        failures.append('snapshot pagination is incomplete')
    mapping = snapshot.get('coordinate_mapping') or {}
    if snapshot.get('coordinate_space') != 'source_canvas' or not mapping.get('verified'):
        failures.append('source coordinate mapping is not verified')
    expected_asset_ids = {
        asset['node_id'] for asset in snapshot.get('assets', [])
    }
    if expected_asset_ids != set(ASSET_FILES):
        failures.append('asset map does not match the 13 exported source nodes')
    asset_root = APP / 'assets/lanhu/message_backup_34/assets'
    asset_records = []
    for node_id, filename in ASSET_FILES.items():
        path = asset_root / filename
        if not path.exists():
            failures.append(f'missing exported asset for {node_id}')
            continue
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                size = list(image.size)
        except Exception as exc:
            failures.append(f'asset decode failed for {node_id}: {exc}')
            continue
        asset_records.append({'node_id': node_id, 'file': rel(path), 'size': size, 'sha256': digest(path)})
    page_chars = set(''.join(str(node.get('text') or '') for node in snapshot.get('nodes', [])))
    font_records = []
    for weight in ('Regular', 'Medium', 'Semibold'):
        path = APP / f'assets/fonts/PingFangSC-{weight}.otf'
        font = TTFont(path)
        cmap = set()
        for table in font['cmap'].tables:
            cmap.update(table.cmap)
        missing = ''.join(sorted(char for char in page_chars if ord(char) not in cmap))
        if missing:
            failures.append(f'{weight} font misses: {missing}')
        font_records.append({'weight': weight, 'file': rel(path), 'sha256': digest(path), 'missing': missing})
    source = (APP / 'lib/experiments/message_backup_34_page.dart').read_text()
    if 'official-notification-missing-asset' not in source:
        failures.append('official artwork without an export is not represented by a traceable placeholder')
    checks.update({
        'snapshot': {
            'snapshot_id': snapshot.get('snapshot_id'),
            'version': snapshot.get('resolved_version'),
            'nodes': len(snapshot.get('nodes', [])),
            'expected_nodes': snapshot.get('total_nodes'),
            'coordinate_mapping_verified': bool(mapping.get('verified')),
        },
        'assets': asset_records,
        'fonts': font_records,
        'missing_custom_artwork': {
            'name': '官方通知图标',
            'node_ids': sorted(OFFICIAL_ARTWORK_NODES),
            'policy': '45x45 circular marked placeholder; exact interior excluded from source pixel comparison',
        },
    })
    return {'status': 'PASS' if not failures else 'FAIL', 'failures': failures, 'checks': checks}


def build_contract(preflight: dict) -> dict:
    base = json.loads((SOURCE_CASE / 'visual-contract.json').read_text())
    snapshot = json.loads(SNAPSHOT.read_text())
    base['name'] = '1备份 34 — optimized replay v1'
    base['status'] = 'ready'
    base['render_scale'] = 2.0
    base['reference'] = rel(REFERENCE)
    base['source_documents'] = [rel(SNAPSHOT)]
    base['environment'] = {
        **base['environment'],
        'platform': 'macOS widget-test 375x812 @2x',
        'state': 'message-backup-34 optimized replay',
    }
    official_exclusion = {
        'rect': [17, 585, 44, 44],
        'reason': '官方通知定制图标没有可导出素材；实现使用45×45圆形未切图占位，排除内部像素，外部位置与占位形状由Widget测试验证',
    }
    base['exclude_rects'] = [
        item for item in base.get('exclude_rects', [])
        if item.get('rect') != official_exclusion['rect']
    ] + [official_exclusion]
    for node_id in OFFICIAL_ARTWORK_NODES:
        if node_id in base.get('coverage', {}):
            base['coverage'][node_id] = {
                'status': 'excluded',
                'checks': [],
                'reason': official_exclusion['reason'],
            }
    for feature in base.get('features', {}).values():
        detector = feature.get('detector') or {}
        if 'min_pixels' in detector:
            detector['min_pixels'] = max(2, round(detector['min_pixels'] / 4))
    assets = [APP / 'assets/lanhu/message_backup_34/assets' / name for name in ASSET_FILES.values()]
    fonts = [APP / f'assets/fonts/PingFangSC-{weight}.otf' for weight in ('Regular', 'Medium', 'Semibold')]
    inputs = [
        APP / 'lib/experiments/message_backup_34_page.dart',
        APP / 'test/message_backup_34_render_test.dart',
        APP / 'pubspec.yaml',
        APP / 'pubspec.lock',
    ]
    text_node_ids = [node['node_id'] for node in snapshot['nodes'] if node.get('text')]
    base['assets'] = [rel(path) for path in assets]
    base['fonts'] = [{'path': rel(path), 'node_ids': text_node_ids} for path in fonts]
    base['implementation_inputs'] = [rel(path) for path in inputs]
    pinned = [REFERENCE, SNAPSHOT, *assets, *fonts, *inputs]
    base['pinned_files'] = {rel(path): digest(path) for path in pinned}
    base['revision'] = {
        'id': 'optimized-v1',
        'based_on': '../visual-contract.json',
        'reason': 'Use native 2x reference, preflight assets/fonts, and explicitly classify missing official artwork before rendering.',
        'preflight_sha256': digest(PREFLIGHT),
    }
    return base


def verify_frozen_contract() -> list[str]:
    if not CONTRACT.exists():
        return ['optimized contract has not been prepared']
    contract = json.loads(CONTRACT.read_text())
    failures = []
    for relative, expected in contract.get('pinned_files', {}).items():
        path = (CASE / relative).resolve()
        if not path.exists():
            failures.append(f'pinned file missing: {relative}')
        elif digest(path) != expected:
            failures.append(f'pinned file changed after freeze: {relative}')
    current = run_preflight()
    failures.extend(current['failures'])
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.verify_only:
        failures = verify_frozen_contract()
        print(json.dumps({'status': 'PASS' if not failures else 'FAIL', 'failures': failures}, ensure_ascii=False))
        return 0 if not failures else 1
    CASE.mkdir(parents=True, exist_ok=True)
    preflight = run_preflight()
    PREFLIGHT.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + '\n')
    if preflight['status'] != 'PASS':
        print(json.dumps(preflight, ensure_ascii=False, indent=2))
        return 1
    contract = build_contract(preflight)
    CONTRACT.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'contract': str(CONTRACT), 'contract_sha256': digest(CONTRACT), 'preflight': str(PREFLIGHT)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
