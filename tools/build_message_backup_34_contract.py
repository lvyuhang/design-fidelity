#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'design_evidence/message-backup-34'
CONTRACT = CASE / 'visual-contract.json'
SNAPSHOT = CASE / 'source/snapshot.json'
APP = ROOT / 'flutter_ui_components'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def node_rgb(node: dict) -> list[int]:
    raw = node.get('raw_style') or {}
    font = raw.get('font') or {}
    color = font.get('color')
    if color:
        return [color['r'], color['g'], color['b']]
    text = node.get('text') or ''
    if text == '2':
        return [255, 255, 255]
    if text in {'全部', '去开启', '消息'} and (text != '消息' or (node.get('bounds') or {}).get('y', 0) > 700):
        return [178, 122, 49]
    if text == '生人':
        return [201, 135, 113]
    if text == '熟人' and (node.get('bounds') or {}).get('y', 0) > 200:
        return [149, 84, 104]
    if text == '未接':
        return [217, 68, 58]
    if text in {'已取消', '熟人', '深夜聊的...', '我关注的'}:
        return [166, 170, 181]
    if text in {'通话记录', '你在干嘛呀？'} or text.startswith('[') or text.startswith('XX') or text.startswith('XXXX'):
        return [145, 145, 155]
    if text == '15:33':
        return [172, 175, 183]
    if text in {'首页', '关系', '任务', '我的'}:
        return [123, 121, 128]
    return [34, 36, 42]


ASSET_RGB = {
    '16F0957E-9372-4BDD-8A38-74F925C77F4A': [34, 36, 42],
    '46973292-5A6D-42BF-9A6F-25D9168D09E8': [230, 181, 94],
    '7A7E5242-D597-4010-ACA3-D9FB4A6A55F0': [247, 233, 217],
    'AE344697-D0D3-4867-B3BC-AA722DBF1288': [198, 200, 208],
    '1357B849-5FC7-4570-9A0A-EE53EAC3ED50': [188, 145, 74],
    '4C5886B0-AB45-4341-AF01-363FE0A5090B': [24, 24, 27],
    '001D3A26-E9F7-4A8D-B848-BDBD5D64AEE9': [24, 24, 27],
    'ED7DC567-6137-467A-B368-F2F41B9230A9': [24, 24, 27],
    '09D2352B-F303-4358-838E-3EEAA4F2FE77': [24, 24, 27],
    '2105E345-1E59-4004-B9B2-11B3E6B1A221': [24, 24, 27],
    '5355B69B-C35E-4D62-AF9D-59C52351451C': [230, 181, 94],
    '7A0E367B-A662-48BB-BDCB-782745125976': [217, 68, 58],
    'F5203DE6-E6BA-4BEA-A600-9111889E746E': [166, 170, 181],
}

KEY_TEXT = {
    'EC6EE647', 'B21589D4', '33E0B12A', '53EBEC3C',
    '783F2F13', '95DE9DE3', '481A3981', 'F3D18C28',
    '41BE3DCA', '83542956', '84005589',
}


def main() -> None:
    contract = json.loads(CONTRACT.read_text())
    snapshot = json.loads(SNAPSHOT.read_text())
    nodes = {n['node_id']: n for n in snapshot['nodes']}

    contract.update({
        'status': 'ready',
        'regions': {
            'whole': {'label': '完整消息页', 'rect': [0, 0, 375, 812], 'max_mae': 10, 'max_p95': 40},
            'header': {'label': '状态栏、标题与通知条', 'rect': [0, 0, 375, 142], 'max_mae': 12, 'max_p95': 48},
            'filters': {'label': '消息筛选', 'rect': [0, 142, 375, 40], 'max_mae': 5, 'max_p95': 20},
            'list': {'label': '消息列表', 'rect': [0, 182, 375, 530], 'max_mae': 8, 'max_p95': 40},
            'bottom': {'label': '底部导航', 'rect': [0, 712, 375, 100], 'max_mae': 8, 'max_p95': 32},
        },
        'features': {},
        'relations': {},
        'exclude_rects': [
            {'rect': [17, 194, 43, 43], 'reason': '阿珍头像原图未提供切图；保留圆形缺图占位'},
            {'rect': [17, 260, 43, 43], 'reason': '旎旎马克头像原图未提供切图；保留圆形缺图占位'},
            {'rect': [17, 391, 43, 43], 'reason': '花花头像原图未提供切图；保留圆形缺图占位'},
            {'rect': [17, 456, 43, 43], 'reason': '物简则明头像原图未提供切图；保留圆形缺图占位'},
            {'rect': [17, 522, 43, 43], 'reason': '跳舞机宝贝头像原图未提供切图；保留圆形缺图占位'},
        ],
        'max_excluded_fraction': 0.04,
        'not_applicable': {},
        'color_samples': {
            'page_white': {'label': '页面白色背景', 'rect': [362, 400, 6, 20], 'max_channel_delta': 5},
            'filter_surface': {'label': '筛选条底色', 'rect': [70, 146, 8, 6], 'max_channel_delta': 8},
            'nav_surface': {'label': '导航面板底色', 'rect': [20, 760, 8, 8], 'max_channel_delta': 10},
        },
        'environment': {
            'renderer': 'flutter-test-skia',
            'renderer_version': 'Flutter 3.47.7 / engine deb287481e',
            'platform': 'macOS widget-test 375x812 @4x',
            'locale': 'zh_CN',
            'state': 'message-backup-34',
            'text_scale': 1,
        },
    })

    # Every inventoried source node remains accountable to the complete-page
    # and sectional checks. Salient text and every exported asset add an
    # independent position/shape gate.
    whole_ids = list(contract['coverage'])
    contract['regions']['whole']['node_ids'] = whole_ids
    for node_id in whole_ids:
        contract['coverage'][node_id] = {
            'status': 'covered', 'checks': ['regions.whole'], 'reason': ''
        }

    feature_by_node = {}
    for node_id, node in nodes.items():
        if node_id not in contract['coverage']:
            continue
        is_asset = bool(node.get('asset_ids'))
        if not node.get('text') and not is_asset:
            continue
        b = node.get('bounds') or {}
        small = is_asset and b.get('width', 0) <= 24 and b.get('height', 0) <= 24
        fid = ('asset_' if is_asset else 'text_') + node_id[:8].lower()
        rgb = ASSET_RGB.get(node_id, node_rgb(node))
        limits = {'max_center_delta': 1.25, 'max_size_delta': 1.5}
        if small:
            limits.update({'max_edge_delta': 1.25, 'max_ink_ratio_delta': .30, 'max_mask_iou_loss': .30})
        contract['features'][fid] = {
            'label': node.get('text') or node.get('name') or fid,
            'node_ids': [node_id],
            'padding': [2, 2, 2, 2],
            'detector': {'kind': 'color_distance', 'rgb': rgb,
                         'max_distance': 70 if is_asset else 74,
                         'min_pixels': 4 if small else 8},
            'limits': limits,
            **({'profile': 'small_visual'} if small else {}),
        }
        feature_by_node[node_id] = fid
        contract['coverage'][node_id] = {
            'status': 'covered',
            'checks': [f'features.{fid}'],
            'reason': '',
        }

    by_prefix = {node_id[:8]: node_id for node_id in nodes}
    relation_specs = [
        ('title_tab_center', 'EC6EE647', 'B21589D4', 'center_y'),
        ('first_name_detail_left', '783F2F13', '95DE9DE3', 'left'),
        ('system_titles_left', '41BE3DCA', '83542956', 'left'),
    ]
    for rid, first_prefix, second_prefix, metric in relation_specs:
        first = by_prefix.get(first_prefix, '')
        second = by_prefix.get(second_prefix, '')
        if first in feature_by_node and second in feature_by_node:
            contract['relations'][rid] = {
                'label': rid.replace('_', ' '),
                'features': [feature_by_node[first], feature_by_node[second]],
                'metric': metric,
                'max_delta': 1.0,
            }

    assets = sorted((APP / 'assets/lanhu/message_backup_34/assets').glob('*.png'))
    fonts = [APP / f'assets/fonts/PingFangSC-{w}.otf' for w in ('Regular', 'Medium', 'Semibold')]
    inputs = [
        APP / 'lib/experiments/message_backup_34_page.dart',
        APP / 'lib/experiments/two_page_fidelity_lab.dart',
        APP / 'test/message_backup_34_render_test.dart',
        APP / 'pubspec.yaml', APP / 'pubspec.lock',
    ]
    relative = lambda p: str(p.relative_to(CASE)) if p.is_relative_to(CASE) else str(Path('../..') / p.relative_to(ROOT))
    contract['assets'] = [relative(p) for p in assets]
    text_nodes = [n for n in nodes.values() if n.get('text')]
    regular = [n['node_id'] for n in text_nodes if 'Semibold' not in str((n.get('raw_style') or {}).get('font'))]
    semibold = [n['node_id'] for n in text_nodes if 'Semibold' in str((n.get('raw_style') or {}).get('font'))]
    contract['fonts'] = [
        {'path': relative(fonts[0]), 'node_ids': regular},
        {'path': relative(fonts[1]), 'node_ids': []},
        {'path': relative(fonts[2]), 'node_ids': semibold},
    ]
    contract['implementation_inputs'] = [relative(p) for p in inputs]
    pinned = [CASE / contract['reference'], SNAPSHOT, *assets, *fonts, *inputs]
    contract['pinned_files'] = {relative(p): digest(p) for p in pinned}
    CONTRACT.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + '\n')
    print(f'Updated {CONTRACT}: {len(contract["coverage"])} source nodes, '
          f'{len(contract["features"])} features, {len(assets)} assets')


if __name__ == '__main__':
    main()
