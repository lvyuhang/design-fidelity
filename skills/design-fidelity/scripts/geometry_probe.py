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
    # Text is compared on its laid-out paragraph when the harness recorded it,
    # so an override that shifts text inside the node frame is still caught.
    paragraphs = geometry.get('text_nodes', {})
    checks, failures = [], []
    for key, decision in sorted(decisions.items()):
        if decision.get('mode') not in CHECKED_MODES or key not in nodes \
                or decision.get('geometry') is False:
            continue
        node = nodes[key]
        label = f"{key} '{node.get('name') or ''}'"
        if key not in measured:
            failures.append({'node_id': key, 'label': label,
                             'failures': ['no widget with sourceKey(node_id) in the tree']})
            continue
        sx, sy, sw, sh = _rect(node)
        rect = paragraphs.get(key) if node.get('text') and key in paragraphs else measured[key]
        ax, ay, aw, ah = (float(v) for v in rect)
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


DEFAULT_DEVICES = ('iphone_se', 'iphone_15', 'iphone_15_pro_max', 'android_compact', 'android_large')
DEFAULT_BLOCKING = ('exceptions', 'horizontal_overflow', 'vertical_clip',
                    'under_status_bar', 'under_home_indicator')
RESPONSIVE_KINDS = (*DEFAULT_BLOCKING, 'text_overlap')


def _variant_name(variant: dict) -> str:
    base = variant.get('device') or f"{variant['width']:g}w"
    return f"{base}@{variant['text_scale']:g}x"


def responsive_report(nodes: dict, variants: dict, design_width: float,
                      blocking=DEFAULT_BLOCKING, decisions: dict | None = None,
                      devices=None) -> dict:
    """Layout on other screens, safe areas and text scales.

    * exceptions / horizontal_overflow: the layout breaks or leaves the screen;
    * vertical_clip: a node ends below the screen while nothing scrolls;
    * under_status_bar: text drawn inside the top safe area;
    * under_home_indicator: a pinned footer reaches into the bottom safe area;
    * text_overlap (observation by default): texts that did not overlap in the
      design now do, e.g. at 1.3x text.
    """
    decisions = decisions or {}
    findings = []
    texts = [k for k, n in nodes.items() if n.get('text')]
    footers = {k for k, d in decisions.items() if d.get('vertical_anchor') == 'bottom'}
    # Footers the design itself draws into the home-indicator area (tab bar
    # backgrounds) may reach the screen edge, but not beyond it.
    bleeding = {k for k, d in decisions.items() if d.get('bleed') == 'bottom'}
    listed = variants.get('variants', [])
    if devices:
        recorded = {v.get('device') for v in listed}
        for device in devices:
            if device not in recorded:
                findings.append({'variant': device, 'kind': 'missing',
                                 'message': f'no variant for device {device}; call '
                                            'captureResponsiveVariants with the default devices'})
    for variant in listed:
        name = _variant_name(variant)
        width, height = variant['width'], variant.get('height')
        padding = variant.get('padding') or {}
        top_inset, bottom_inset = padding.get('top', 0), padding.get('bottom', 0)
        if variant.get('exception'):
            findings.append({'variant': name, 'kind': 'exceptions',
                             'message': variant['exception'].splitlines()[0][:300]})
        measured = variant.get('nodes', {})
        paragraphs = variant.get('text_nodes', {})

        def label(key):
            node = nodes.get(key) or {}
            return f"{key} '{node.get('text') or node.get('name') or ''}'"

        for key, rect in measured.items():
            if rect[0] < -0.5 or rect[0] + rect[2] > width + 0.5:
                findings.append({'variant': name, 'kind': 'horizontal_overflow', 'node_id': key,
                                 'message': f"{label(key)} spans {rect[0]:.1f}..{rect[0] + rect[2]:.1f} "
                                            f"outside 0..{width:g}"})
            if height and not variant.get('scrollable') and rect[1] + rect[3] > height + 0.5 \
                    and rect[3] < height:
                findings.append({'variant': name, 'kind': 'vertical_clip', 'node_id': key,
                                 'message': f"{label(key)} ends at {rect[1] + rect[3]:.1f} below the "
                                            f"{height:g} screen and the page does not scroll"})
            limit = height if key in bleeding else height - bottom_inset
            if key in footers and height and rect[1] + rect[3] > limit + 0.5:
                findings.append({'variant': name, 'kind': 'under_home_indicator', 'node_id': key,
                                 'message': f"{label(key)} reaches {rect[1] + rect[3]:.1f}, inside the "
                                            f"bottom safe area ({height - bottom_inset:g}..{height:g})"})
        for key in texts:
            rect = paragraphs.get(key) or measured.get(key)
            if rect and top_inset and rect[1] < top_inset - 0.5 and rect[1] + rect[3] > 0:
                findings.append({'variant': name, 'kind': 'under_status_bar', 'node_id': key,
                                 'message': f"{label(key)} starts at {rect[1]:.1f}, inside the "
                                            f"{top_inset:g}px status bar"})
        for i, first in enumerate(texts):
            for second in texts[i + 1:]:
                if first not in measured or second not in measured:
                    continue
                if _overlap(_rect(nodes[first]), _rect(nodes[second])):
                    continue  # Overlapping in the design already (e.g. duplicates).
                if _overlap(paragraphs.get(first) or measured[first],
                            paragraphs.get(second) or measured[second]):
                    findings.append({'variant': name, 'kind': 'text_overlap',
                                     'node_id': first, 'other_node_id': second,
                                     'message': f"'{nodes[first].get('text')}' overlaps "
                                                f"'{nodes[second].get('text')}'"})
    blocked = [f for f in findings if f['kind'] in blocking or f['kind'] == 'missing']
    counts = {}
    for item in findings:
        counts[item['kind']] = counts.get(item['kind'], 0) + 1
    return {'variants': len(listed), 'design_width': design_width,
            'blocking': list(blocking), 'counts': counts, 'findings': findings,
            'passed': not blocked}


def load(path: Path):
    return json.loads(path.read_text())
