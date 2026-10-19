#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'design_evidence/message-backup-36'
CONTRACT = CASE / 'visual-contract.json'
SNAPSHOT = CASE / 'source/snapshot.json'
EXPORT = CASE / 'source/asset-export.json'
APP = ROOT / 'flutter_ui_components'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    if path.is_relative_to(CASE):
        return str(path.relative_to(CASE))
    return str(Path('../..') / path.relative_to(ROOT))


def text_rgb(reference: Image.Image, node: dict) -> list[int]:
    font = (node.get('raw_style') or {}).get('font') or {}
    color = font.get('color') or {}
    if all(key in color for key in ('r', 'g', 'b')):
        return [color['r'], color['g'], color['b']]
    return asset_rgb(reference, node)


def asset_rgb(reference: Image.Image, node: dict) -> list[int]:
    bounds = node['bounds']
    crop = reference.crop((
        round(bounds['x'] * 2), round(bounds['y'] * 2),
        round((bounds['x'] + bounds['width']) * 2),
        round((bounds['y'] + bounds['height']) * 2),
    )).convert('RGB')
    pixels = []
    for rgb in crop.getdata():
        if not all(channel > 242 for channel in rgb):
            pixels.append(tuple((channel // 16) * 16 + 8 for channel in rgb))
    if not pixels:
        return [34, 36, 42]
    return list(Counter(pixels).most_common(1)[0][0])


def build_fold_evidence(snapshot: dict) -> Path:
    ids = {
        'A22A1CD3-4A07-4A0C-B1AC-2D4D2F78CB84',
        '5FB6266F-941F-42E9-8E1A-AC46207C0726',
        '6D712D6D-7EC4-40D6-A4D6-B6DBF7B42763',
        'CA21BB0E-3177-455D-BF3C-01A8DE80CCE6',
        '26021B27-EE2A-465A-9389-E336B2D44395',
        'FB7B8225-D25C-485C-993F-C77602F6DA28',
        '60FB67EE-888B-48F6-9371-D5AAD5142C2A',
        '39267A01-AA6C-4FFE-91D4-E2B0D0DC35C1',
        '03E16F01-50B6-4D85-98C8-227018EA45EF',
    }
    path = CASE / 'source/fold-region.json'
    payload = {
        'snapshot_id': snapshot['snapshot_id'],
        'design_id': snapshot['design_id'],
        'resolved_version': snapshot['resolved_version'],
        'source_region': [0, 691, 375, 44],
        'coordinate_mapping': {'verified': True, 'strategy': 'identity'},
        'nodes': [node for node in snapshot['nodes'] if node['node_id'] in ids],
        'implementation_decision': {
            'collapse_arrow': 'original exported asset',
            'list_icon': 'six complete source vector strokes',
            'separator': 'independent 1px decoration',
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    return path


def main() -> None:
    contract = json.loads(CONTRACT.read_text())
    snapshot = json.loads(SNAPSHOT.read_text())
    nodes = {node['node_id']: node for node in snapshot['nodes']}
    reference = Image.open(CASE / contract['reference'])
    fold_evidence = build_fold_evidence(snapshot)

    contract.update({
        'status': 'ready',
        'source_documents': ['source/snapshot.json'],
        'regions': {
            'whole': {'label': '完整消息页', 'rect': [0, 0, 375, 812], 'max_mae': 10, 'max_p95': 40},
            'header': {'label': '状态栏、标题与通知条', 'rect': [0, 0, 375, 142], 'max_mae': 12, 'max_p95': 48},
            'filters': {'label': '消息筛选', 'rect': [0, 142, 375, 40], 'max_mae': 6, 'max_p95': 24},
            'list': {'label': '消息列表', 'rect': [0, 182, 375, 509], 'max_mae': 9, 'max_p95': 42},
            'fold': {'label': '折叠置顶会话', 'rect': [0, 691, 375, 44], 'max_mae': 6, 'max_p95': 30},
            'bottom': {'label': '底部导航', 'rect': [0, 735, 375, 77], 'max_mae': 9, 'max_p95': 36},
        },
        'features': {},
        'relations': {},
        'exclude_rects': [
            {'rect': [17, 194, 43, 43], 'reason': '阿珍头像原图未提供切图；保留圆形缺图占位'},
            {'rect': [17, 260, 43, 43], 'reason': '旎旎马克头像原图未提供切图；保留圆形缺图占位'},
            {'rect': [17, 326, 43, 43], 'reason': '晚风头像原图未提供切图；保留圆形缺图占位'},
            {'rect': [17, 391, 43, 43], 'reason': '花花头像原图未提供切图；保留圆形缺图占位'},
            {'rect': [17, 456, 43, 43], 'reason': '物简则明头像原图未提供切图；保留圆形缺图占位'},
            {'rect': [17, 522, 43, 43], 'reason': '跳舞机宝贝头像原图未提供切图；保留圆形缺图占位'},
        ],
        'max_excluded_fraction': 0.045,
        'not_applicable': {},
        'color_samples': {
            'page_warm': {'label': '页面暖白背景', 'rect': [362, 400, 6, 20], 'max_channel_delta': 5},
            'filter_surface': {'label': '筛选条底色', 'rect': [70, 146, 8, 6], 'max_channel_delta': 8},
            'fold_surface': {'label': '折叠栏底色', 'rect': [180, 700, 8, 8], 'max_channel_delta': 6},
            'nav_surface': {'label': '导航面板底色', 'rect': [20, 760, 8, 8], 'max_channel_delta': 10},
        },
        'environment': {
            'renderer': 'flutter-test-skia',
            'renderer_version': 'Flutter 3.47.7 / engine deb287481e',
            'platform': 'macOS widget-test 375x812 @2x',
            'locale': 'zh_CN',
            'state': 'message-backup-36-folded-list',
            'text_scale': 1,
        },
    })

    whole_ids = list(contract['coverage'])
    contract['regions']['whole']['node_ids'] = whole_ids
    for node_id in whole_ids:
        contract['coverage'][node_id] = {
            'status': 'covered', 'checks': ['regions.whole'], 'reason': ''
        }

    feature_by_node: dict[str, str] = {}
    fold_lines = {
        '6D712D6D-7EC4-40D6-A4D6-B6DBF7B42763',
        'CA21BB0E-3177-455D-BF3C-01A8DE80CCE6',
        '26021B27-EE2A-465A-9389-E336B2D44395',
        'FB7B8225-D25C-485C-993F-C77602F6DA28',
        '60FB67EE-888B-48F6-9371-D5AAD5142C2A',
        '39267A01-AA6C-4FFE-91D4-E2B0D0DC35C1',
        '03E16F01-50B6-4D85-98C8-227018EA45EF',
    }
    for node_id in whole_ids:
        node = nodes[node_id]
        is_asset = bool(node.get('asset_ids'))
        is_text = bool(node.get('text'))
        is_fold_line = node_id in fold_lines
        if not (is_asset or is_text or is_fold_line):
            continue
        bounds = node.get('bounds') or {}
        small = is_fold_line or (is_asset and bounds.get('width', 0) <= 24 and bounds.get('height', 0) <= 24)
        kind = 'asset' if is_asset else ('text' if is_text else 'vector')
        feature_id = f'{kind}_{node_id[:8].lower()}'
        if is_asset:
            rgb = asset_rgb(reference, node)
        elif is_fold_line:
            rgb = [166, 170, 181] if node_id != '03E16F01-50B6-4D85-98C8-227018EA45EF' else [240, 238, 233]
        else:
            rgb = text_rgb(reference, node)
        limits = {'max_center_delta': 1.25, 'max_size_delta': 1.5}
        if small:
            limits.update({'max_edge_delta': 1.25, 'max_ink_ratio_delta': .32, 'max_mask_iou_loss': .32})
        contract['features'][feature_id] = {
            'label': node.get('text') or node.get('name') or feature_id,
            'node_ids': [node_id],
            'padding': [2, 2, 2, 2],
            'detector': {
                'kind': 'color_distance', 'rgb': rgb,
                'max_distance': 76 if is_asset else 70,
                'min_pixels': 2 if is_fold_line else (4 if small else 8),
            },
            'limits': limits,
            **({'profile': 'small_visual'} if small else {}),
        }
        feature_by_node[node_id] = feature_id
        contract['coverage'][node_id] = {
            'status': 'covered', 'checks': [f'features.{feature_id}'], 'reason': ''
        }

    def relation(relation_id: str, first: str, second: str, metric: str, delta: float = 1.0) -> None:
        if first in feature_by_node and second in feature_by_node:
            contract['relations'][relation_id] = {
                'label': relation_id.replace('_', ' '),
                'features': [feature_by_node[first], feature_by_node[second]],
                'metric': metric,
                'max_delta': delta,
            }

    relation('title_tab_center', '60E096F3-B05B-462C-9930-AFD796E3A0FC', '8B9F016C-B7F7-4091-87F2-924ABE1BBC84', 'center_y')
    relation('first_name_detail_left', 'EFFEB311-801C-4291-90CA-5D09774B24E5', 'FE1D62F4-9919-427E-80CD-50D88551CD4F', 'left')
    relation('system_titles_left', '8B99809F-C198-48F0-96D7-6FD820ED6779', 'FBBCE9F1-5C00-4E45-B418-F9489AB39F2C', 'left')
    relation('fold_icon_text_center', '60FB67EE-888B-48F6-9371-D5AAD5142C2A', '5FB6266F-941F-42E9-8E1A-AC46207C0726', 'center_y', 1.25)
    relation('fold_text_arrow_center', '5FB6266F-941F-42E9-8E1A-AC46207C0726', 'A22A1CD3-4A07-4A0C-B1AC-2D4D2F78CB84', 'center_y', 1.25)

    assets = sorted((APP / 'assets/lanhu/message_backup_34/assets').glob('*.png'))
    assets += [
        APP / 'assets/lanhu/message_backup_36/assets/4942c8d9ffd41a52012b311e9a260d39b13004fcce7e952ea8b915267eb40240.png',
        APP / 'assets/lanhu/message_backup_36/assets/878bf0142fd15e2b935fff1f2a2bc871630338b10f3622c5a593b0db99179f9f.png',
    ]
    source_assets = sorted((APP / 'assets/lanhu/message_backup_36/assets').glob('*.png'))
    fonts = [APP / f'assets/fonts/PingFangSC-{weight}.otf' for weight in ('Regular', 'Medium', 'Semibold')]
    inputs = [
        APP / 'lib/experiments/message_backup_34_page.dart',
        APP / 'lib/experiments/message_backup_36_page.dart',
        APP / 'test/message_backup_36_render_test.dart',
        APP / 'pubspec.yaml', APP / 'pubspec.lock',
    ]
    contract['assets'] = [relative(path) for path in assets]
    text_nodes = [node for node in nodes.values() if node.get('text')]
    regular = [node['node_id'] for node in text_nodes if 'Semibold' not in str((node.get('raw_style') or {}).get('font'))]
    semibold = [node['node_id'] for node in text_nodes if 'Semibold' in str((node.get('raw_style') or {}).get('font'))]
    contract['fonts'] = [
        {'path': relative(fonts[0]), 'node_ids': regular},
        {'path': relative(fonts[1]), 'node_ids': []},
        {'path': relative(fonts[2]), 'node_ids': semibold},
    ]
    contract['implementation_inputs'] = [relative(path) for path in inputs]
    pinned = [
        CASE / contract['reference'], SNAPSHOT, EXPORT, fold_evidence,
        *source_assets, *assets, *fonts, *inputs,
    ]
    contract['pinned_files'] = {relative(path): digest(path) for path in dict.fromkeys(pinned)}
    CONTRACT.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + '\n')
    print(f'Updated {CONTRACT}: {len(contract["coverage"])} accountable nodes, '
          f'{len(contract["features"])} features, {len(assets)} runtime assets')


if __name__ == '__main__':
    main()
