"""Shared v2 preflight: incomplete evidence must never become a visual PASS."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path


def read_json(path):
    def reject(value):
        raise ValueError(f'Non-finite JSON number: {value}')
    data = json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=reject)
    def finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError('Non-finite JSON number')
        if isinstance(value, dict):
            for item in value.values(): finite(item)
        if isinstance(value, list):
            for item in value: finite(item)
    finite(data)
    return data


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(nodes):
    parents = {n.get('parent_id') for n in nodes.values()}
    result = {}
    for key, node in nodes.items():
        b = node.get('bounds', {})
        if node.get('effective_source_visible', node.get('source_visible')) is False:
            continue
        if not b or b.get('width', 0) <= 0 or b.get('height', 0) <= 0:
            continue
        raw = node.get('raw_style') or {}
        effect_fields = ('shadow', 'shadows', 'innerShadows', 'blur', 'effects')
        has_effect = any(_enabled_effect(raw.get(field, node.get(field)))
                         for field in effect_fields)
        has_effect = has_effect or bool(raw.get('hasClippingMask'))
        has_effect = has_effect or raw.get('opacity') not in (None, 100, 1)
        has_effect = has_effect or any(
            item.get('isEnabled', True)
            for field in ('fills', 'borders')
            for item in (raw.get(field) or [])
            if isinstance(item, dict) and
            (item.get('type') == 'gradient' or field == 'borders')
        )
        if node.get('text') or node.get('asset_ids') or key not in parents or has_effect:
            result[key] = node
    return result


def _enabled_effect(value):
    values = value if isinstance(value, list) else [value] if isinstance(value, dict) else []
    return any(item.get('isEnabled', item.get('enabled', True))
               for item in values if isinstance(item, dict))


def _number(value, label, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{label}: finite number required')
    if value < 0 or (positive and value == 0):
        raise ValueError(f'{label}: invalid nonpositive value')


def validate_contract(c, nodes):
    if c.get('schema_version') != 2:
        raise ValueError('Use schema_version 2; migrate legacy contracts before acceptance')
    if c.get('status') != 'ready':
        raise ValueError('Contract is DRAFT / 未验收; review suggestions and coverage first')
    for key in ('source_snapshot', 'source_version'):
        if not isinstance(c.get(key), str) or not c[key].strip() or 'REPLACE' in c[key]:
            raise ValueError(f'{key}: pinned identity required')
    if len(c.get('canvas', [])) != 2:
        raise ValueError('canvas: two dimensions required')
    for value in c['canvas']:
        _number(value, 'canvas', True)
    _number(c.get('render_scale'), 'render_scale', True)
    if not c.get('source_documents'):
        raise ValueError('source_documents required')
    scope = c.get('source_scope', {})
    if scope.get('kind') == 'page':
        expected = scope.get('expected_node_count')
        if isinstance(expected, bool) or not isinstance(expected, int) or expected <= 0 or len(nodes) < expected:
            raise ValueError('Incomplete source pagination / invalid expected_node_count')
    elif scope.get('kind') != 'provided_nodes' or not scope.get('reason', '').strip():
        raise ValueError('Declare page scope and node count, or provided_nodes with a reason')
    exceptions = []
    if scope['kind'] == 'provided_nodes':
        exceptions.append('Partial source scope: ' + scope['reason'])
    categories = ('regions', 'features', 'relations', 'color_samples')
    for category in categories:
        checks = c.get(category)
        if not isinstance(checks, dict):
            raise ValueError(f'{category}: object required')
        blocking = {k: v for k, v in checks.items() if v.get('blocking', True)}
        if not blocking:
            reason = c.get('not_applicable', {}).get(category, '').strip()
            if category in ('regions', 'features') or not reason:
                raise ValueError(f'{category}: blocking checks required')
            exceptions.append(f'{category}: {reason}')
        for key, spec in checks.items():
            if not spec.get('label'):
                raise ValueError(f'{category}.{key}: label required')
            if 'blocking' in spec and not isinstance(spec['blocking'], bool):
                raise ValueError(f'{key}: blocking must be boolean')
            if not spec.get('blocking', True):
                if not spec.get('reason', '').strip():
                    raise ValueError(f'{key}: nonblocking check needs reason')
                exceptions.append(f'{category}.{key}: {spec["reason"]}')
            for node_id in spec.get('node_ids', []):
                if node_id not in nodes:
                    raise ValueError(f'{key}: unknown node {node_id}')
            if category == 'relations':
                pair = spec.get('features', [])
                if len(pair) != 2 or pair[0] == pair[1] or any(x not in c['features'] for x in pair):
                    raise ValueError(f'{key}: two distinct existing features required')
                if spec.get('metric') not in ('center_x', 'center_y', 'left', 'right', 'top', 'bottom'):
                    raise ValueError(f'{key}: unsupported relation metric')
                _number(spec.get('max_delta'), key)
            elif category == 'features':
                if not spec.get('node_ids'):
                    raise ValueError(f'{key}: source node IDs required')
                limits = spec.get('limits', {})
                if not {'max_center_delta', 'max_size_delta'} <= limits.keys():
                    raise ValueError(f'{key}: center and size limits required')
                allowed = {'max_center_delta', 'max_size_delta', 'max_edge_delta', 'max_ink_ratio_delta', 'max_mask_iou_loss'}
                if set(limits) - allowed:
                    raise ValueError(f'{key}: unknown limit')
                for field, value in limits.items():
                    _number(value, f'{key}.{field}')
                if limits.get('max_mask_iou_loss', 0) > 1:
                    raise ValueError(f'{key}: max_mask_iou_loss must be in [0, 1]')
                profile = spec.get('profile')
                if profile not in (None, 'small_visual'):
                    raise ValueError(f'{key}: unknown feature profile')
                if profile == 'small_visual':
                    required_limits = {'max_edge_delta', 'max_ink_ratio_delta', 'max_mask_iou_loss'}
                    if not required_limits <= limits.keys() or len(spec['node_ids']) != 1:
                        raise ValueError(f'{key}: small_visual requires one node and edge, ink and mask limits')
                det = spec.get('detector', {})
                if det.get('kind') not in ('dark', 'light', 'gold', 'color_distance', 'channel_range'):
                    raise ValueError(f'{key}: unsupported detector')
                _number(det.get('min_pixels', 8), key, True)
                pad = spec.get('padding', [0]*4)
                if len(pad) != 4:
                    raise ValueError(f'{key}: padding must have four values')
                for value in pad:
                    _number(value, key)
            elif category == 'regions':
                _number(spec.get('max_mae'), key)
                if 'max_p95' in spec:
                    _number(spec['max_p95'], key)
            else:
                _number(spec.get('max_channel_delta'), key)
            if category in ('regions', 'color_samples') and not (spec.get('node_ids') or spec.get('rect')):
                raise ValueError(f'{key}: rect or node_ids required')
            if 'rect' in spec:
                rect = spec['rect']
                if len(rect) != 4 or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in rect):
                    raise ValueError(f'{key}: invalid rect')
                x, y, w, h = rect
                if x < 0 or y < 0 or w <= 0 or h <= 0 or x+w > c['canvas'][0] or y+h > c['canvas'][1]:
                    raise ValueError(f'{key}: rect outside canvas')
    coverage = c.get('coverage', {})
    required = inventory(nodes)
    if not required:
        raise ValueError('No visible source nodes to evaluate')
    for key, node in required.items():
        decision = coverage.get(key, {})
        if decision.get('status') == 'excluded' and decision.get('reason', '').strip():
            exceptions.append(f'node {key}: {decision["reason"]}')
            continue
        if decision.get('status') != 'covered' or not decision.get('checks'):
            raise ValueError(f'Unreviewed source node: {key}')
        for check in decision['checks']:
            category, _, check_id = check.partition('.')
            spec = c.get(category, {}).get(check_id)
            if category not in categories or not spec or not spec.get('blocking', True) or key not in spec.get('node_ids', []):
                raise ValueError(f'{key}: coverage must reference a blocking check containing this node')
            if (node.get('text') or node.get('asset_ids')) and category != 'features':
                raise ValueError(f'{key}: text/asset needs visible feature coverage')
    if set(coverage) - set(required):
        raise ValueError('Coverage includes unknown or non-inventory nodes')
    return {'nodes': len(required), 'covered': sum(v.get('status') == 'covered' for v in coverage.values()), 'exceptions': exceptions}


def verify_files(c, directory):
    pins = c.get('pinned_files', {})
    required = {c['reference'], *c['source_documents'], *c.get('assets', [])}
    required.update(f['path'] for f in c.get('fonts', []))
    if not required <= pins.keys():
        raise ValueError('Missing pinned hashes for reference, evidence, assets or fonts')
    for path, expected in pins.items():
        if sha256(directory / path) != expected:
            raise ValueError(f'Pinned file changed: {path}')
    if not c.get('implementation_inputs'):
        raise ValueError('implementation_inputs must include code, configuration and lockfiles')
    for path in c['implementation_inputs']:
        if not (directory / path).is_file():
            raise ValueError(f'Missing implementation input: {path}')
    env = c.get('environment', {})
    for key in ('renderer', 'renderer_version', 'platform', 'locale', 'state'):
        if not isinstance(env.get(key), str) or not env[key].strip():
            raise ValueError(f'environment.{key} required')
    _number(env.get('text_scale'), 'text_scale', True)


def verify_fonts(c, nodes, directory):
    texts = {key: str(node['text']) for key, node in inventory(nodes).items()
             if node.get('text') and c['coverage'][key].get('status') != 'excluded'}
    checked = set()
    for spec in c.get('fonts', []):
        from fontTools.ttLib import TTFont
        font = TTFont(directory / spec['path'], fontNumber=spec.get('font_number', 0))
        try:
            cmap = font.getBestCmap() or {}
            for key in spec.get('node_ids', []):
                if key not in texts:
                    raise ValueError(f'Font references non-covered text node: {key}')
                missing = sorted({ch for ch in texts[key] if not ch.isspace() and ord(ch) not in cmap})
                if missing:
                    raise ValueError(f'Font missing glyphs for {key}: {"".join(missing)}')
                checked.add(key)
        finally:
            font.close()
    if set(texts) - checked:
        raise ValueError(f'No verified font for text nodes: {sorted(set(texts)-checked)}')
    return {'text_nodes_checked': len(checked)}


def input_hashes(c, directory):
    paths = set(c['implementation_inputs']) | set(c['pinned_files'])
    return {p: sha256(directory / p) for p in sorted(paths)}


def verify_receipt(path, candidate, contract_path, c):
    receipt = read_json(path)
    if receipt.get('contract_sha256') != sha256(contract_path):
        raise ValueError('Render receipt uses another contract')
    if receipt.get('candidate_sha256') != sha256(candidate):
        raise ValueError('Screenshot does not match render receipt')
    if receipt.get('environment') != c['environment']:
        raise ValueError('Render environment mismatch')
    if receipt.get('inputs') != input_hashes(c, contract_path.parent):
        raise ValueError('Inputs changed since screenshot; re-render required')
    if not receipt.get('command') or receipt.get('exit_code') != 0:
        raise ValueError('Receipt must record a successful render command')
    return receipt
