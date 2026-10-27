"""Compare laid-out widget rects (from `sourceKey`) with source node bounds.

Pixel segmentation answers "does it look the same"; this answers "which node
is where", with messages a model can act on directly ("top +2.00px"). Text
compares the alignment edge and line box, and reports width separately
because glyph advances legitimately differ by a fraction of a pixel.
"""
from __future__ import annotations

import json
from pathlib import Path

BOX_TOLERANCE = 0.5
TEXT_EDGE_TOLERANCE = 1.0
TEXT_WIDTH_TOLERANCE = 3.0
CHECKED_MODES = ('native_exact', 'original_asset', 'render_fallback', 'missing_asset_placeholder')
ALIGN_EDGE = {1: 'right', 2: 'center'}


def geometry_path(candidate: Path, suffix: str = 'geometry') -> Path:
    return candidate.with_name(candidate.name + f'.{suffix}.json')


def _rect(node):
    b = node['bounds']
    return [float(b['x']), float(b['y']), float(b['width']), float(b['height'])]


def _text_edge(node):
    font = (node.get('raw_style') or {}).get('font') or {}
    code = font.get('textAlignment')
    if code is None and font.get('styles'):
        code = font['styles'][0].get('alignment')
    return ALIGN_EDGE.get(code, 'left')


def _fmt(value):
    return f'{value:+.2f}px'


def compare_geometry(nodes: dict, decisions: dict, geometry: dict) -> dict:
    measured = geometry.get('nodes', {})
    checks, failures = [], []
    for key, decision in sorted(decisions.items()):
        if decision.get('mode') not in CHECKED_MODES or key not in nodes:
            continue
        node = nodes[key]
        label = f"{key} '{node.get('name') or ''}'"
        if key not in measured:
            failures.append({'node_id': key, 'label': label,
                             'failures': ['no widget with sourceKey(node_id) in the tree']})
            continue
        sx, sy, sw, sh = _rect(node)
        ax, ay, aw, ah = (float(v) for v in measured[key])
        problems, deltas = [], {}
        if node.get('text'):
            # The generator records the edge it anchored auto-width text to;
            # otherwise the source alignment edge is the stable one.
            anchor = decision.get('anchor')
            edge = anchor if anchor in ('left', 'center', 'right') else _text_edge(node)
            source_edge = {'left': sx, 'center': sx + sw / 2, 'right': sx + sw}[edge]
            actual_edge = {'left': ax, 'center': ax + aw / 2, 'right': ax + aw}[edge]
            deltas = {f'{edge}': actual_edge - source_edge, 'top': ay - sy,
                      'height': ah - sh, 'width': aw - sw}
            if anchor == 'stretch':
                deltas.pop('width')
            if abs(deltas[edge]) > TEXT_EDGE_TOLERANCE:
                problems.append(f'{edge} edge {_fmt(deltas[edge])}')
            if abs(deltas['top']) > BOX_TOLERANCE:
                problems.append(f"top {_fmt(deltas['top'])}")
            if abs(deltas['height']) > BOX_TOLERANCE:
                problems.append(f"line box height {_fmt(deltas['height'])} "
                                '(line height, wrapping or strut)')
            if anchor != 'stretch' and abs(deltas['width']) > TEXT_WIDTH_TOLERANCE:
                problems.append(f"width {_fmt(deltas['width'])} (font file/weight/letter spacing)")
        else:
            deltas = {'left': ax - sx, 'top': ay - sy, 'width': aw - sw, 'height': ah - sh}
            problems = [f'{k} {_fmt(v)}' for k, v in deltas.items() if abs(v) > BOX_TOLERANCE]
        entry = {'node_id': key, 'label': label, 'deltas': {k: round(v, 3) for k, v in deltas.items()},
                 'source': [sx, sy, sw, sh], 'actual': [ax, ay, aw, ah],
                 'passed': not problems, 'failures': problems}
        checks.append(entry)
        if problems:
            failures.append({'node_id': key, 'label': label, 'failures': problems})
    return {'checked': len(checks), 'failures': failures, 'checks': checks,
            'passed': not failures}


def _overlap(a, b, slack=0.5):
    return (a[0] + slack < b[0] + b[2] and b[0] + slack < a[0] + a[2] and
            a[1] + slack < b[1] + b[3] and b[1] + slack < a[1] + a[3])


def responsive_report(nodes: dict, variants: dict, design_width: float,
                      blocking=('exceptions', 'horizontal_overflow')) -> dict:
    """Layout at other widths/text scales: exceptions, overflow, new text overlaps."""
    findings = []
    texts = [k for k, n in nodes.items() if n.get('text')]
    for variant in variants.get('variants', []):
        name = f"{variant['width']:g}w@{variant['text_scale']:g}x"
        if variant.get('exception'):
            findings.append({'variant': name, 'kind': 'exceptions',
                             'message': variant['exception'].splitlines()[0][:300]})
        measured = variant.get('nodes', {})
        for key, rect in measured.items():
            if rect[0] < -0.5 or rect[0] + rect[2] > variant['width'] + 0.5:
                findings.append({'variant': name, 'kind': 'horizontal_overflow', 'node_id': key,
                                 'message': f"{key} '{(nodes.get(key) or {}).get('name', '')}' "
                                            f"spans {rect[0]:.1f}..{rect[0] + rect[2]:.1f} "
                                            f"outside 0..{variant['width']:g}"})
        for i, first in enumerate(texts):
            for second in texts[i + 1:]:
                if first not in measured or second not in measured:
                    continue
                if _overlap(_rect(nodes[first]), _rect(nodes[second])):
                    continue  # Overlapping in the design already (e.g. duplicates).
                if _overlap(measured[first], measured[second]):
                    findings.append({'variant': name, 'kind': 'text_overlap',
                                     'node_id': first, 'other_node_id': second,
                                     'message': f"'{nodes[first].get('text')}' overlaps "
                                                f"'{nodes[second].get('text')}'"})
    blocked = [f for f in findings if f['kind'] in blocking or f['kind'] == 'missing']
    counts = {}
    for item in findings:
        counts[item['kind']] = counts.get(item['kind'], 0) + 1
    return {'variants': len(variants.get('variants', [])), 'design_width': design_width,
            'blocking': list(blocking), 'counts': counts, 'findings': findings,
            'passed': not blocked}


def load(path: Path):
    return json.loads(path.read_text())
