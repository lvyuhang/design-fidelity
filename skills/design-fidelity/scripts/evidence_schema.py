#!/usr/bin/env python3
"""Validate a design evidence document against the canonical schema.

Every design source (Lanhu MCP, Figma REST, ...) is converted into this one
format before `prepare`; the scene model, contracts and gates only read it.
The schema is described in references/evidence-schema.md. This validator checks
the fields those consumers depend on, so an adapter bug is reported here as a
pointer into the document instead of as a wrong render three steps later.

    python3 evidence_schema.py evidence/source.json [more.json ...]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
NODE_TYPES = {'artboard-group', 'layer-group', 'symbol', 'shape', 'text', 'bitmap'}
BORDER_POSITIONS = {'内边框', '中心边框', '外边框', 'inside', 'center', 'outside'}
SHADOW_TYPES = {None, '外阴影', '内阴影', 'outer', 'inner', 'innerShadow', 'dropShadow'}
BLUR_TYPES = {0, 1, 2, 3}
TEXT_ALIGN_CODES = {0, 1, 2, 3, 4}


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _color(value: Any) -> bool:
    if isinstance(value, str):
        return value.startswith(('#', 'rgb'))
    return isinstance(value, dict) and (isinstance(value.get('value'), str)
                                        or all(_number(value.get(k)) for k in 'rgba'))


class Checker:
    def __init__(self, known_ids: set | None = None) -> None:
        self.issues: list[dict] = []
        self.known_ids = known_ids or set()

    def fail(self, pointer: str, message: str, severity: str = 'error') -> None:
        self.issues.append({'pointer': pointer, 'message': message, 'severity': severity})

    def warn(self, pointer: str, message: str) -> None:
        self.fail(pointer, message, 'warning')

    def rect(self, value: Any, pointer: str, positive: bool = False) -> None:
        if not isinstance(value, dict) or not all(_number(value.get(k)) for k in ('x', 'y', 'width', 'height')):
            self.fail(pointer, 'expected {x, y, width, height} numbers')
        elif positive and (value['width'] < 0 or value['height'] < 0):
            self.fail(pointer, 'negative size')

    def paint(self, fill: Any, pointer: str) -> None:
        if not isinstance(fill, dict):
            return self.fail(pointer, 'expected an object')
        gradient = fill.get('gradient')
        if fill.get('type') == 'gradient' or isinstance(gradient, dict):
            if not isinstance(gradient, dict):
                return self.fail(pointer + '/gradient', 'gradient fill without gradient object')
            for i, stop in enumerate(gradient.get('colorStops') or []):
                if not _color(stop.get('color')) or not _number(stop.get('position')):
                    self.fail(f'{pointer}/gradient/colorStops/{i}', 'stop needs color and numeric position 0..1')
            for end in ('from', 'to'):
                point = gradient.get(end)
                if point is not None and not (isinstance(point, dict) and _number(point.get('x')) and _number(point.get('y'))):
                    self.fail(f'{pointer}/gradient/{end}', 'expected unit {x, y}')
        elif fill.get('type') in (None, 'color') and fill.get('fillType') in (None, 0):
            if not _color(fill.get('color')):
                self.fail(pointer + '/color', 'solid fill without a parsable color')
        if fill.get('opacity') is not None and not _number(fill.get('opacity')):
            self.fail(pointer + '/opacity', 'fill opacity is a 0..1 number')

    def raw_style(self, raw: Any, pointer: str, node: dict) -> None:
        if raw is None:
            return self.warn(pointer, 'no raw_style; the node renders without fills, borders or effects')
        if not isinstance(raw, dict):
            return self.fail(pointer, 'raw_style must be an object')
        for key in ('fills', 'borders', 'shadow', 'innerShadow', 'innerShadows', 'points'):
            if key in raw and raw[key] is not None and not isinstance(raw[key], list):
                self.fail(f'{pointer}/{key}', 'expected a list')
        for i, fill in enumerate(raw.get('fills') or []):
            self.paint(fill, f'{pointer}/fills/{i}')
        for i, border in enumerate(raw.get('borders') or []):
            self.paint(border, f'{pointer}/borders/{i}')
            if isinstance(border, dict):
                if border.get('position') not in BORDER_POSITIONS:
                    self.fail(f'{pointer}/borders/{i}/position', f'one of {sorted(BORDER_POSITIONS)}')
                if not _number(border.get('thickness')):
                    self.fail(f'{pointer}/borders/{i}/thickness', 'numeric stroke width')
        for key in ('shadow', 'innerShadow', 'innerShadows'):
            for i, shadow in enumerate(raw.get(key) or []):
                p = f'{pointer}/{key}/{i}'
                if not isinstance(shadow, dict) or not _color(shadow.get('color')):
                    self.fail(p, 'shadow needs a color')
                    continue
                for field in ('offsetX', 'offsetY', 'blurRadius', 'spread'):
                    if shadow.get(field) is not None and not _number(shadow[field]):
                        self.fail(f'{p}/{field}', 'number')
                if shadow.get('type') not in SHADOW_TYPES:
                    self.fail(f'{p}/type', f'one of {sorted(t for t in SHADOW_TYPES if t)}')
        blur = raw.get('blur')
        if blur is not None:
            if not isinstance(blur, dict) or not _number(blur.get('radius')) or blur.get('blurType', 0) not in BLUR_TYPES:
                self.fail(pointer + '/blur', 'expected {radius, blurType: 0 layer | 3 background}')
        for i, point in enumerate(raw.get('points') or []):
            p = f'{pointer}/points/{i}'
            main = point.get('point') if isinstance(point, dict) else None
            if not (isinstance(main, dict) and _number(main.get('x')) and _number(main.get('y'))):
                self.fail(p + '/point', 'unit-space {x, y} required')
                continue
            for flag, field in (('hasCurveFrom', 'curveFrom'), ('hasCurveTo', 'curveTo')):
                if point.get(flag) and not (isinstance(point.get(field), dict) and _number(point[field].get('x'))):
                    self.fail(f'{p}/{field}', f'{flag} set without control point')
        if raw.get('opacity') is not None and not (_number(raw['opacity']) and 0 <= raw['opacity'] <= 100):
            self.fail(pointer + '/opacity', 'layer opacity is a 0..100 percentage')
        if node.get('text'):
            font = raw.get('font') or {}
            code = font.get('textAlignment')
            if code is not None and code not in TEXT_ALIGN_CODES:
                self.fail(pointer + '/font/textAlignment', 'NSTextAlignment code 0 left, 1 right, 2 center, 3 justify')

    def text_spec(self, node: dict, pointer: str) -> None:
        spec = node.get('text_spec')
        if not isinstance(spec, dict):
            return self.fail(pointer, 'text node needs text_spec')
        runs = spec.get('text_runs')
        if not isinstance(runs, list) or not runs:
            return self.fail(pointer + '/text_runs', 'at least one run')
        if ''.join(r.get('text', '') for r in runs if isinstance(r, dict)) != node['text']:
            self.fail(pointer + '/text_runs', 'runs must concatenate to node.text')
        base = spec.get('base_style') if isinstance(spec.get('base_style'), dict) else {}
        for i, run in enumerate(runs):
            p = f'{pointer}/text_runs/{i}'
            run = {**base, **{k: v for k, v in run.items() if v is not None}}
            if not isinstance(run.get('font_family'), str) or not run['font_family']:
                self.fail(p + '/font_family', 'source font family (PostScript or family name)')
            if not _number(run.get('font_size')):
                self.warn(p + '/font_size', 'missing font size (run or base_style)')
            if run.get('line_height') is not None and not _number(run['line_height']):
                self.fail(p + '/line_height', 'absolute line height in canvas units, or null for auto')
            if run.get('color') is not None and not _color(run['color']):
                self.fail(p + '/color', 'run color (omit only when the source has none; renders black)')

    def document(self, doc: Any) -> None:
        if not isinstance(doc, dict):
            return self.fail('', 'evidence must be a JSON object')
        for key in ('snapshot_id', 'resolved_version'):
            if not isinstance(doc.get(key), str) or not doc[key]:
                self.fail(f'/{key}', 'pinned source version is required; never invent one')
        if doc.get('coordinate_space') != 'source_canvas':
            self.fail('/coordinate_space', 'must be "source_canvas"')
        if not (doc.get('coordinate_mapping') or {}).get('verified'):
            self.fail('/coordinate_mapping/verified', 'mapping between source and canvas must be verified')
        canvas = doc.get('canvas') or {}
        if not (_number(canvas.get('width')) and _number(canvas.get('height'))):
            self.fail('/canvas', 'expected {width, height}')
        nodes = doc.get('nodes')
        if not isinstance(nodes, list) or not nodes:
            return self.fail('/nodes', 'non-empty list')
        ids = {n.get('node_id') for n in nodes if isinstance(n, dict)}
        ids |= {a.get('node_id') for a in doc.get('ancestors') or [] if isinstance(a, dict)}
        ids |= self.known_ids
        seen = set()
        for i, node in enumerate(nodes):
            p = f'/nodes/{i}'
            if not isinstance(node, dict):
                self.fail(p, 'expected an object')
                continue
            key = node.get('node_id')
            if not isinstance(key, str) or not key:
                self.fail(p + '/node_id', 'stable string id')
            elif key in seen:
                self.fail(p + '/node_id', f'duplicate id {key}')
            seen.add(key)
            if node.get('parent_id') is not None and node['parent_id'] not in ids:
                self.fail(p + '/parent_id', f'unknown parent {node["parent_id"]}')
            if not _number(node.get('source_order')):
                self.warn(p + '/source_order', 'paint order among siblings (0 = back); siblings fall back to id order')
            if node.get('node_type') not in NODE_TYPES:
                self.warn(p + '/node_type', f'one of {sorted(NODE_TYPES)}')
            self.rect(node.get('bounds'), p + '/bounds', positive=True)
            if not isinstance(node.get('asset_ids', []), list):
                self.fail(p + '/asset_ids', 'list')
            self.raw_style(node.get('raw_style'), p + '/raw_style', node)
            if node.get('text'):
                self.text_spec(node, p + '/text_spec')
        node_ids = set(ids)
        for i, asset in enumerate(doc.get('assets') or []):
            p = f'/assets/{i}'
            if not isinstance(asset, dict) or asset.get('node_id') not in node_ids:
                self.fail(p + '/node_id', 'asset must belong to a node in this document')
                continue
            if not asset.get('asset_id'):
                self.fail(p + '/asset_id', 'required')
            if asset.get('render_bounds') is not None:
                self.rect(asset['render_bounds'], p + '/render_bounds', positive=True)


def validate(doc: Any, known_ids: set | None = None) -> list[dict]:
    """Issues for one document; `known_ids` are nodes/ancestors of sibling pages."""
    checker = Checker(known_ids)
    checker.document(doc)
    return checker.issues


def _ids(doc: Any, field: str) -> set:
    return {n.get('node_id') for n in (doc.get(field) or []) if isinstance(n, dict)} if isinstance(doc, dict) else set()


def validate_set(docs: list[Any]) -> dict:
    """Pages of one query (or regions of one design) are validated together:
    parents may live in a sibling page and pagination must be complete overall."""
    known = set().union(*(_ids(d, 'nodes') | _ids(d, 'ancestors') for d in docs)) if docs else set()
    per_doc = [validate(doc, known) for doc in docs]
    overall = []
    unique = set().union(*(_ids(d, 'nodes') for d in docs)) if docs else set()
    declared = [d.get(k) for d in docs if isinstance(d, dict) for k in ('total_nodes', 'total') if _number(d.get(k))]
    if declared and len(unique) < max(declared):
        overall.append({'pointer': '', 'severity': 'error',
                        'message': f'{len(unique)} unique nodes, source declares {max(declared)}; '
                        'fetch every page/region before prepare'})
    return {'documents': per_doc, 'overall': overall}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('evidence', type=Path, nargs='+')
    args = parser.parse_args()
    result = validate_set([json.loads(path.read_text()) for path in args.evidence])
    report = {str(path): issues for path, issues in zip(args.evidence, result['documents'])}
    failed = sum(i['severity'] == 'error' for v in report.values() for i in v) + len(result['overall'])
    print(json.dumps({'status': 'FAIL' if failed else 'PASS', 'schema_version': SCHEMA_VERSION,
                      'issues': report, 'overall': result['overall']}, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
