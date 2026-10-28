#!/usr/bin/env python3
"""Figma frame -> canonical design evidence (references/evidence-schema.md).

    export FIGMA_TOKEN=<personal access token>        # or FIGMA_TOKEN=... in fidelity/.local.env
    python3 figma_evidence.py --url 'https://www.figma.com/design/<key>/<name>?node-id=12-34' \\
        --out fidelity/<page>/evidence [--version <file version id>]

Uses the Figma REST API (not the Dev Mode MCP server, which returns generated
code instead of source styles):
  GET /v1/files/:key/nodes?ids=<frame>&geometry=paths   node tree with raw paint, effects, text
  GET /v1/images/:key?ids=...&scale=4&format=png       reference render and asset exports

Writes source.json (canonical evidence), reference.png (4x), manifest.json and
assets/*.png. The file version returned by the first call is pinned for every
image request and recorded as resolved_version. The token is read from the
environment and is never written to any output; signed image URLs are not
stored either.

Assets are exported for nodes the designer marked for export (exportSettings),
nodes with image fills, and vector icons whose geometry is not a single path.
Everything else is translated into the canonical (Sketch-vocabulary) styles
so the generators render it natively. Anything the canonical format cannot
express is listed in source_gaps rather than dropped.

Offline (tests, or a saved response): --nodes-json response.json --images-dir dir
where dir holds <node id with ':' -> '-'>.png renders at the chosen scale.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = 'https://api.figma.com'
SCALE = 4
ICON_MAX = 64
VECTOR_TYPES = {'VECTOR', 'STAR', 'REGULAR_POLYGON', 'BOOLEAN_OPERATION', 'LINE'}
GROUP_TYPES = {'FRAME', 'GROUP', 'COMPONENT', 'COMPONENT_SET', 'INSTANCE', 'SECTION'}
ALIGN = {'LEFT': 0, 'RIGHT': 1, 'CENTER': 2, 'JUSTIFIED': 3}
STROKE_POSITION = {'INSIDE': 'inside', 'CENTER': 'center', 'OUTSIDE': 'outside'}
CAP = {'NONE': 0, 'ROUND': 1, 'SQUARE': 2, 'LINE_ARROW': 0, 'TRIANGLE_ARROW': 0}
JOIN = {'MITER': 0, 'ROUND': 1, 'BEVEL': 2}
GRADIENT_KIND = {'GRADIENT_LINEAR': 0, 'GRADIENT_RADIAL': 1, 'GRADIENT_ANGULAR': 2, 'GRADIENT_DIAMOND': 3}
RECT = [(0, 0), (1, 0), (1, 1), (0, 1)]


def parse_url(url: str) -> tuple[str, str]:
    """(file key, node id) from a Figma design/file URL."""
    parsed = urllib.parse.urlparse(url)
    match = re.search(r'/(?:design|file|proto)/([A-Za-z0-9]+)', parsed.path)
    if not match:
        raise ValueError('Not a Figma file URL (expected /design/<key>/...)')
    node = urllib.parse.parse_qs(parsed.query).get('node-id', [None])[0]
    if not node:
        raise ValueError('The URL has no node-id; copy the link to the frame (right click > Copy link)')
    return match.group(1), node.replace('-', ':')


def safe_id(node_id: str) -> str:
    return re.sub(r'[^0-9A-Za-z]+', '-', node_id).strip('-')


# ---------------------------------------------------------------------------
# paints, strokes, effects

def rgba(color: dict, alpha: float = 1.0) -> str:
    r, g, b = (round(float(color.get(k, 0)) * 255) for k in 'rgb')
    a = float(color.get('a', 1)) * alpha
    return f'rgba({r},{g},{b},{round(a, 4):g})'


def paint(p: dict, gaps: list, node_id: str, field: str) -> dict | None:
    kind = p.get('type')
    enabled = p.get('visible', True) is not False
    opacity = float(p.get('opacity', 1))
    if p.get('blendMode') not in (None, 'NORMAL', 'PASS_THROUGH'):
        gaps.append(gap('paint_blend_mode', node_id, f'{field} blendMode {p.get("blendMode")}'))
    if kind == 'SOLID':
        return {'type': 'color', 'fillType': 0, 'isEnabled': enabled, 'opacity': opacity,
                'color': {'value': rgba(p['color'])}}
    if kind in GRADIENT_KIND:
        handles = p.get('gradientHandlePositions') or [{'x': 0, 'y': .5}, {'x': 1, 'y': .5}]
        stops = [{'position': float(s.get('position', 0)), 'color': {'value': rgba(s['color'])}}
                 for s in p.get('gradientStops', [])]
        return {'type': 'gradient', 'fillType': 1, 'isEnabled': enabled, 'opacity': opacity,
                'gradient': {'type': 'linear' if kind == 'GRADIENT_LINEAR' else kind.split('_', 1)[1].lower(),
                             'gradientType': GRADIENT_KIND[kind],
                             'from': {'x': handles[0]['x'], 'y': handles[0]['y']},
                             'to': {'x': handles[1]['x'], 'y': handles[1]['y']},
                             'colorStops': stops}}
    if kind in ('IMAGE', 'VIDEO', 'EMOJI'):
        return {'type': 'pattern', 'fillType': 1, 'isEnabled': enabled, 'opacity': opacity,
                'figma_image': True}
    gaps.append(gap('unknown_paint', node_id, f'{field} type {kind}'))
    return None


def gap(code: str, node_id: str, message: str) -> dict:
    return {'code': code, 'node_id': node_id, 'message': message}


def strokes(n: dict, gaps: list) -> tuple[list, dict]:
    weight = n.get('strokeWeight', 0) or 0
    individual = n.get('individualStrokeWeights')
    if individual:
        values = {individual.get(k, weight) for k in ('top', 'right', 'bottom', 'left')}
        if len(values) > 1:
            gaps.append(gap('individual_stroke_weights', n['id'], f'per-side strokes {individual}; max used'))
        weight = max(values)
    borders = []
    for p in n.get('strokes') or []:
        item = paint(p, gaps, n['id'], 'stroke')
        if item is None:
            continue
        item.update(thickness=float(weight), position=STROKE_POSITION.get(n.get('strokeAlign', 'CENTER'), 'center'))
        borders.append(item)
    options = {'lineCapStyle': CAP.get(n.get('strokeCap', 'NONE'), 0),
               'lineJoinStyle': JOIN.get(n.get('strokeJoin', 'MITER'), 0),
               'dashPattern': [float(v) for v in n.get('strokeDashes') or []]}
    return borders, options


def effects(n: dict, gaps: list, raw: dict) -> None:
    shadows, inner = [], []
    for e in n.get('effects') or []:
        enabled = e.get('visible', True) is not False
        kind = e.get('type')
        if kind in ('DROP_SHADOW', 'INNER_SHADOW'):
            offset = e.get('offset') or {}
            item = {'isEnabled': enabled, 'color': {'value': rgba(e['color'])},
                    'offsetX': float(offset.get('x', 0)), 'offsetY': float(offset.get('y', 0)),
                    'blurRadius': float(e.get('radius', 0)), 'spread': float(e.get('spread', 0) or 0),
                    'type': 'outer' if kind == 'DROP_SHADOW' else 'inner'}
            if kind == 'DROP_SHADOW' and e.get('showShadowBehindNode'):
                gaps.append(gap('shadow_behind_node', n['id'], 'shadow shows through translucent fills; '
                                'renderers knock it out under the shape'))
            (shadows if kind == 'DROP_SHADOW' else inner).append(item)
        elif kind in ('LAYER_BLUR', 'BACKGROUND_BLUR'):
            if raw.get('blur'):
                gaps.append(gap('multiple_blurs', n['id'], 'only the first blur is kept'))
                continue
            if e.get('blurType') == 'PROGRESSIVE':
                gaps.append(gap('progressive_blur', n['id'], 'drawn as a uniform blur'))
            raw['blur'] = {'isEnabled': enabled, 'radius': float(e.get('radius', 0)),
                           'blurType': 0 if kind == 'LAYER_BLUR' else 3, 'saturation': 1}
        else:
            gaps.append(gap('unknown_effect', n['id'], f'effect {kind}'))
    if shadows:
        raw['shadow'] = shadows
    if inner:
        raw['innerShadow'] = inner


# ---------------------------------------------------------------------------
# geometry

PATH_TOKEN = re.compile(r'[MLCQZHVmlcqzhv]|-?\d*\.?\d+(?:e[-+]?\d+)?')


def parse_path(d: str) -> list[list[tuple[str, list[float]]]]:
    """Absolute SVG path (Figma geometry) -> subpaths of (command, coords)."""
    tokens = PATH_TOKEN.findall(d)
    subpaths, current, i, cmd = [], None, 0, None
    pos = (0.0, 0.0)
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in 'Zz':
                if current is not None:
                    current.append(('Z', []))
                continue
        if cmd is None:
            raise ValueError('path starts with a number')
        count = {'M': 2, 'L': 2, 'C': 6, 'Q': 4, 'H': 1, 'V': 1}[cmd.upper()]
        if cmd.islower():
            raise ValueError('relative path commands are not produced by Figma; unsupported')
        values = [float(v) for v in tokens[i:i + count]]
        i += count
        if cmd == 'M':
            current = [('M', values)]
            subpaths.append(current)
            cmd = 'L'
        elif cmd == 'H':
            current.append(('L', [values[0], pos[1]]))
        elif cmd == 'V':
            current.append(('L', [pos[0], values[0]]))
        else:
            current.append((cmd, values))
        last = current[-1][1]
        if last:
            pos = (last[-2], last[-1])
    return subpaths


def points_from_path(sub: list, w: float, h: float) -> tuple[list[dict], bool]:
    """One subpath -> Sketch-style unit points (point, curveFrom, curveTo)."""
    def unit(x, y):
        return {'x': x / w if w else 0.0, 'y': y / h if h else 0.0}
    points: list[dict] = []
    closed = False
    for cmd, v in sub:
        if cmd == 'M':
            points.append({'point': unit(v[0], v[1]), 'hasCurveFrom': False, 'hasCurveTo': False})
        elif cmd == 'L':
            points.append({'point': unit(v[0], v[1]), 'hasCurveFrom': False, 'hasCurveTo': False})
        elif cmd in ('C', 'Q'):
            if cmd == 'Q':  # quadratic -> cubic
                start = points[-1]['point']
                sx, sy = start['x'] * w, start['y'] * h
                qx, qy, ex, ey = v
                v = [sx + 2 / 3 * (qx - sx), sy + 2 / 3 * (qy - sy),
                     ex + 2 / 3 * (qx - ex), ey + 2 / 3 * (qy - ey), ex, ey]
            points[-1]['curveFrom'] = unit(v[0], v[1])
            points[-1]['hasCurveFrom'] = True
            points.append({'point': unit(v[4], v[5]), 'curveTo': unit(v[2], v[3]),
                           'hasCurveFrom': False, 'hasCurveTo': True})
        elif cmd == 'Z':
            closed = True
    if closed and len(points) > 1 and _same(points[0]['point'], points[-1]['point']):
        last = points.pop()
        if last.get('hasCurveTo'):
            points[0]['curveTo'] = last['curveTo']
            points[0]['hasCurveTo'] = True
    for p in points:
        p.setdefault('curveFrom', p['point'])
        p.setdefault('curveTo', p['point'])
        p.setdefault('cornerRadius', 0)
    return points, closed


def _same(a: dict, b: dict) -> bool:
    return abs(a['x'] - b['x']) < 1e-6 and abs(a['y'] - b['y']) < 1e-6


def rect_points(radius: float = 0) -> list[dict]:
    return [{'point': {'x': x, 'y': y}, 'curveFrom': {'x': x, 'y': y}, 'curveTo': {'x': x, 'y': y},
             'hasCurveFrom': False, 'hasCurveTo': False, 'cornerRadius': radius} for x, y in RECT]


def oval_points() -> list[dict]:
    k = 0.5 * 0.5522847498
    pts = [((.5, 0), (.5 - k, 0), (.5 + k, 0)), ((1, .5), (1, .5 - k), (1, .5 + k)),
           ((.5, 1), (.5 + k, 1), (.5 - k, 1)), ((0, .5), (0, .5 + k), (0, .5 - k))]
    return [{'point': {'x': p[0], 'y': p[1]}, 'curveTo': {'x': t[0], 'y': t[1]},
             'curveFrom': {'x': f[0], 'y': f[1]}, 'hasCurveTo': True, 'hasCurveFrom': True,
             'cornerRadius': 0} for p, t, f in pts]


def radii(n: dict) -> list[float]:
    if n.get('rectangleCornerRadii'):
        return [float(v) for v in n['rectangleCornerRadii']]
    return [float(n.get('cornerRadius', 0) or 0)] * 4


# ---------------------------------------------------------------------------
# text

def text_style(style: dict, fills: list, gaps: list, node_id: str) -> dict:
    family = style.get('fontPostScriptName') or style.get('fontFamily')
    run = {'font_family': family, 'font_size': float(style.get('fontSize', 14)),
           'font_weight': style.get('fontWeight', 400),
           'line_height': float(style['lineHeightPx']) if style.get('lineHeightPx') else None,
           'letter_spacing': float(style.get('letterSpacing', 0) or 0),
           'decoration_line': {'UNDERLINE': 'underline', 'STRIKETHROUGH': 'line-through'}.get(
               style.get('textDecoration'), 'none')}
    solid = [f for f in fills if f.get('type') == 'SOLID' and f.get('visible', True) is not False]
    if solid:
        top = solid[-1]
        run['color'] = rgba(top['color'], float(top.get('opacity', 1)))
    elif fills:
        gaps.append(gap('text_non_solid_fill', node_id, 'gradient/image text fill'))
    if style.get('textCase') not in (None, 'ORIGINAL'):
        gaps.append(gap('text_case', node_id, f"textCase {style['textCase']} (characters are not transformed)"))
    if style.get('paragraphSpacing'):
        gaps.append(gap('paragraph_spacing', node_id, f"paragraphSpacing {style['paragraphSpacing']}"))
    return run


def text_runs(n: dict, gaps: list) -> list[dict]:
    text = n.get('characters', '')
    base_style = n.get('style') or {}
    base = text_style(base_style, n.get('fills') or [], gaps, n['id'])
    overrides = n.get('characterStyleOverrides') or []
    table = n.get('styleOverrideTable') or {}
    units = text.encode('utf-16-le')
    length = len(units) // 2
    ids = [overrides[i] if i < len(overrides) else 0 for i in range(length)]
    runs, start = [], 0
    for i in range(1, length + 1):
        if i == length or ids[i] != ids[start]:
            chunk = units[start * 2:i * 2].decode('utf-16-le')
            key = str(ids[start])
            if ids[start] and key in table:
                o = table[key]
                style = {**base_style, **{k: v for k, v in o.items() if k != 'fills'}}
                run = text_style(style, o.get('fills') or n.get('fills') or [], gaps, n['id'])
            else:
                run = dict(base)
            run.update(text=chunk, start=start, length=i - start, offset_unit='utf16')
            runs.append(run)
            start = i
    return runs or [dict(base, text=text)]


# ---------------------------------------------------------------------------
# tree

class Converter:
    def __init__(self, frame: dict, file_key: str, version: str, file_name: str = ''):
        self.frame = frame
        self.file_key, self.version, self.file_name = file_key, version, file_name
        box = frame['absoluteBoundingBox']
        self.ox, self.oy = float(box['x']), float(box['y'])
        self.nodes: list[dict] = []
        self.gaps: list[dict] = []
        self.exports: dict[str, dict] = {}   # node id -> asset spec
        self.order = 0

    def bounds(self, n: dict, field: str = 'absoluteBoundingBox') -> dict | None:
        box = n.get(field)
        if not box:
            return None
        return {'x': round(float(box['x']) - self.ox, 4), 'y': round(float(box['y']) - self.oy, 4),
                'width': round(float(box['width']), 4), 'height': round(float(box['height']), 4)}

    def wants_export(self, n: dict) -> str | None:
        if n.get('exportSettings'):
            return 'designer export'
        if any(p.get('type') in ('IMAGE', 'VIDEO') and p.get('visible', True) is not False
               for p in n.get('fills') or []):
            return 'image fill'
        if n.get('type') in VECTOR_TYPES and n.get('type') != 'LINE':
            geometry = n.get('fillGeometry') or []
            if not geometry:
                return 'stroked vector (centre line not in the REST geometry)'
            if len(geometry) != 1 or len(parse_path(geometry[0].get('path', ''))) != 1:
                return 'vector with compound geometry'
        box = n.get('absoluteBoundingBox') or {}
        if (n.get('type') in GROUP_TYPES and n is not self.frame and self._vector_only(n)
                and box.get('width', 999) <= ICON_MAX and box.get('height', 999) <= ICON_MAX):
            return 'vector icon'
        return None

    def _vector_only(self, n: dict) -> bool:
        children = [c for c in n.get('children') or [] if c.get('visible', True) is not False]
        if not children:
            return False
        return all(c.get('type') in VECTOR_TYPES | {'ELLIPSE', 'RECTANGLE'} or
                   (c.get('type') in GROUP_TYPES and self._vector_only(c)) for c in children)

    def base(self, n: dict, parent: str | None, node_type: str, visible: bool, bounds: dict) -> dict:
        raw: dict[str, Any] = {'opacity': round(float(n.get('opacity', 1)) * 100, 4)}
        if n.get('blendMode') not in (None, 'PASS_THROUGH', 'NORMAL'):
            raw['blendMode'] = n['blendMode']
        rotation = n.get('rotation')
        if rotation and abs(float(rotation)) > 1e-6:
            # Bounds are the axis-aligned box; the generators report rotation as unsupported.
            raw['rotation'] = float(rotation)
        if n.get('isMask'):
            raw['hasClippingMask'] = 1
            if n.get('maskType') not in (None, 'ALPHA', 'VECTOR'):
                self.gaps.append(gap('luminance_mask', n['id'], 'luminance masks are drawn as alpha masks'))
        node = {'node_id': n['id'], 'source_id': n['id'], 'identity_source': 'figma_node_id',
                'parent_id': parent, 'source_order': self.order, 'name': n.get('name'),
                'node_type': node_type, 'bounds': bounds, 'source_visible': visible,
                'effective_source_visible': visible, 'text': None, 'raw_style': raw, 'asset_ids': [],
                'source_pointer': f'figma:{n["id"]}'}
        layout = {k: n[k] for k in ('layoutMode', 'primaryAxisAlignItems', 'counterAxisAlignItems',
                                    'paddingLeft', 'paddingRight', 'paddingTop', 'paddingBottom',
                                    'itemSpacing', 'layoutAlign', 'layoutGrow', 'layoutPositioning',
                                    'layoutSizingHorizontal', 'layoutSizingVertical', 'constraints',
                                    'clipsContent') if k in n}
        if layout:
            node['figma_layout'] = layout
        if n.get('componentId'):
            node['figma_component'] = n['componentId']
        self.order += 1
        return node

    def paint_style(self, n: dict, raw: dict) -> None:
        fills = [p for p in (paint(f, self.gaps, n['id'], 'fill') for f in n.get('fills') or []) if p]
        if fills:
            raw['fills'] = fills
        borders, options = strokes(n, self.gaps)
        if borders:
            raw['borders'] = borders
            raw['borderOptions'] = options
        effects(n, self.gaps, raw)

    def visit(self, n: dict, parent: str | None, visible: bool, root: bool = False,
              covered: bool = False) -> None:
        visible = visible and n.get('visible', True) is not False
        kind = n.get('type')
        bounds = self.bounds(n) if not root else {'x': 0.0, 'y': 0.0,
                                                    'width': float(n['absoluteBoundingBox']['width']),
                                                    'height': float(n['absoluteBoundingBox']['height'])}
        if bounds is None:
            self.gaps.append(gap('no_bounds', n['id'], f'{kind} without absoluteBoundingBox skipped'))
            return
        reason = None if root or covered else self.wants_export(n)
        if kind == 'TEXT' and not reason:
            node = self.base(n, parent, 'text', visible, bounds)
            raw = node['raw_style']
            style = n.get('style') or {}
            raw['font'] = {'textAlignment': ALIGN.get(style.get('textAlignHorizontal', 'LEFT'), 0)}
            raw['textBehaviour'] = 0 if n.get('style', {}).get('textAutoResize') == 'WIDTH_AND_HEIGHT' \
                or n.get('textAutoResize') == 'WIDTH_AND_HEIGHT' else 1
            if style.get('textAlignVertical') not in (None, 'TOP'):
                self.gaps.append(gap('text_vertical_alignment', n['id'],
                                     f"textAlignVertical {style['textAlignVertical']}: text drawn from the top"))
            borders, _ = strokes(n, self.gaps)
            if borders:
                self.gaps.append(gap('text_stroke', n['id'], 'text outline strokes are not drawn'))
            effects(n, self.gaps, raw)
            node['text'] = n.get('characters', '')
            runs = text_runs(n, self.gaps)
            base = text_style(style, n.get('fills') or [], [], n['id'])
            node['text_spec'] = {'base_style': base, 'text_runs': runs}
            self.nodes.append(node)
            return
        if root or (kind in GROUP_TYPES and not reason):
            node = self.base(n, parent, 'artboard-group' if root else 'layer-group', visible, bounds)
            self.nodes.append(node)
            styled = bool(n.get('fills') or n.get('strokes') or n.get('effects'))
            if root:
                fills = [p for p in (paint(f, self.gaps, n['id'], 'fill') for f in n.get('fills') or []) if p]
                if fills:
                    node['raw_style'].update(hasBackgroundColor=True, fills=fills)
                if n.get('strokes') or n.get('effects'):
                    self.gaps.append(gap('artboard_stroke_or_effect', n['id'], 'frame-level strokes/effects of the page frame are not drawn'))
            elif kind != 'GROUP' and (styled or n.get('clipsContent')):
                # A styled frame becomes a background layer plus an unstyled group, so
                # radius, strokes and shadows render like any shape. clipsContent
                # makes that layer the mask of the frame's children.
                self._frame_background(n, node, visible, bool(n.get('clipsContent')))
            for child in n.get('children') or []:
                self.visit(child, n['id'], visible, covered=covered)
            return
        node = self.base(n, parent, 'bitmap' if reason == 'image fill' else 'shape', visible, bounds)
        raw = node['raw_style']
        if reason:
            render = self.bounds(n, 'absoluteRenderBounds') or bounds
            asset_id = f'{n["id"]}:image'
            node['asset_ids'] = [asset_id]
            self.exports[n['id']] = {'asset_id': asset_id, 'node_id': n['id'], 'kind': 'exported_asset',
                                     'reason': reason, 'render_bounds': render,
                                     'source_size': {'width': render['width'], 'height': render['height']},
                                     'source_point': {'x': render['x'], 'y': render['y']},
                                     'source_field': 'figma_images_api', 'format_hint': 'png'}
            self.nodes.append(node)
            # Children of an exported node are covered by the bitmap.
            for child in n.get('children') or []:
                self.visit(child, n['id'], visible, covered=True)
            return
        self.paint_style(n, raw)
        w, h = bounds['width'], bounds['height']
        if kind == 'RECTANGLE':
            r = radii(n)
            raw['points'] = rect_points()
            for p, value in zip(raw['points'], r):
                p['cornerRadius'] = value
            raw['radius'] = r if len(set(r)) > 1 else [r[0]]
        elif kind == 'ELLIPSE':
            arc = n.get('arcData') or {}
            if arc and (abs(arc.get('endingAngle', 2 * math.pi) - arc.get('startingAngle', 0) - 2 * math.pi) > 1e-3
                        or arc.get('innerRadius')):
                self.gaps.append(gap('ellipse_arc', n['id'], 'arc/donut ellipse drawn as a full oval'))
            raw['points'] = oval_points()
        elif kind == 'LINE':
            weight = float(n.get('strokeWeight', 1) or 1)
            stroke = raw.pop('borders', [])
            raw.pop('borderOptions', None)
            if h < 1e-6 or w < 1e-6:
                horizontal = h < 1e-6
                node['bounds'] = dict(bounds, **({'height': weight, 'y': bounds['y'] - weight / 2} if horizontal
                                                 else {'width': weight, 'x': bounds['x'] - weight / 2}))
                raw['points'] = rect_points()
                raw['fills'] = [dict(s, type=s.get('type', 'color')) for s in stroke]
                for f in raw['fills']:
                    f.pop('thickness', None)
                    f.pop('position', None)
            else:
                self.gaps.append(gap('diagonal_line', n['id'], 'diagonal line not representable'))
        elif kind in VECTOR_TYPES:
            geometry = n.get('fillGeometry') or []
            subpaths = parse_path(geometry[0]['path']) if geometry else []
            if len(subpaths) == 1:
                raw['points'], raw['isClosed'] = points_from_path(subpaths[0], w, h)
                raw['windingRule'] = 1 if geometry[0].get('windingRule') == 'EVENODD' else 0
            elif not covered:
                self.gaps.append(gap('vector_geometry', n['id'], 'no single fill path; drawn as its bounds'))
                raw['points'] = rect_points()
        else:
            self.gaps.append(gap('unsupported_node_type', n['id'], f'{kind} drawn from its bounds only'))
            raw['points'] = rect_points()
        self.nodes.append(node)

    def _frame_background(self, n: dict, group: dict, visible: bool, clip: bool) -> None:
        bg = self.base({**n, 'id': n['id'] + '#bg', 'name': f"{n.get('name', '')} (frame)",
                        'opacity': 1, 'blendMode': None, 'rotation': 0, 'isMask': clip},
                       n['id'], 'shape', visible, dict(group['bounds']))
        raw = bg['raw_style']
        self.paint_style(n, raw)
        if not raw.get('fills') and clip:
            # A clip without paint still masks the children; give it a clear fill.
            raw['fills'] = [{'type': 'color', 'fillType': 0, 'isEnabled': True, 'opacity': 1,
                             'color': {'value': 'rgba(0,0,0,0)'}}]
        r = radii(n)
        raw['points'] = rect_points()
        for p, value in zip(raw['points'], r):
            p['cornerRadius'] = value
        raw['radius'] = r if len(set(r)) > 1 else [r[0]]
        if clip and raw.get('shadow'):
            # Sketch masks clip the mask's own shadow too; keep the shadow on a
            # separate unclipped layer below the mask.
            shadow = self.base({**n, 'id': n['id'] + '#shadow', 'name': f"{n.get('name', '')} (shadow)",
                                'opacity': 1, 'blendMode': None, 'rotation': 0, 'isMask': False},
                               n['id'], 'shape', visible, dict(group['bounds']))
            # Shadow only: the fill is drawn once, by the clipping layer above.
            shadow['raw_style'].update(points=raw['points'], radius=raw['radius'], shadow=raw.pop('shadow'))
            shadow['source_order'], bg['source_order'] = bg['source_order'], shadow['source_order']
            self.nodes.append(shadow)
        self.nodes.append(bg)

    def document(self) -> dict:
        self.visit(self.frame, None, True, root=True)
        # Hidden ancestors hide descendants.
        hidden = {n['node_id'] for n in self.nodes if n['source_visible'] is False}
        by_id = {n['node_id']: n for n in self.nodes}
        for n in self.nodes:
            parent = n['parent_id']
            while parent:
                if parent in hidden:
                    n['effective_source_visible'] = False
                    break
                parent = by_id.get(parent, {}).get('parent_id')
        box = self.frame['absoluteBoundingBox']
        canvas = {'width': float(box['width']), 'height': float(box['height'])}
        fonts: dict[str, dict] = {}
        for n in self.nodes:
            for run in (n.get('text_spec') or {}).get('text_runs', []):
                entry = fonts.setdefault(run['font_family'], {'family': run['font_family'], 'weights': set(),
                                                              'node_count': 0, 'source': 'design'})
                entry['weights'].add(run['font_weight'])
                entry['node_count'] += 1
        return {
            'status': 'complete', 'source': 'figma',
            'snapshot_id': f'figma:{self.file_key}:{self.frame["id"]}@{self.version}',
            'resolved_version': str(self.version),
            'design_name': self.frame.get('name'), 'file_name': self.file_name,
            'coordinate_space': 'source_canvas',
            'coordinate_mapping': {'verified': True, 'strategy': 'frame_absolute_origin',
                                   'source_origin': {'x': self.ox, 'y': self.oy}},
            'canvas': canvas, 'image_size': None, 'scale': {'x': SCALE, 'y': SCALE},
            'font_requirements': [dict(v, weights=sorted(v['weights'], key=str)) for v in fonts.values()],
            'source_gaps': self.gaps, 'gaps': self.gaps,
            'nodes': self.nodes, 'total_nodes': len(self.nodes), 'returned': len(self.nodes),
            'truncated': False, 'next_offset': None,
            'assets': list(self.exports.values()),
        }


def convert(response: dict, file_key: str, node_id: str) -> dict:
    entry = (response.get('nodes') or {}).get(node_id)
    if not entry or not entry.get('document'):
        raise ValueError(f'node {node_id} not in the response (wrong node-id or no access)')
    frame = entry['document']
    if frame.get('type') not in GROUP_TYPES:
        raise ValueError(f'node {node_id} is a {frame.get("type")}; link a frame or component')
    return Converter(frame, file_key, response.get('version') or response.get('lastModified') or 'unknown',
                     response.get('name', '')).document()


# ---------------------------------------------------------------------------
# I/O

def token_from(out: Path) -> str:
    token = os.environ.get('FIGMA_TOKEN')
    if token:
        return token.strip()
    for folder in [out.resolve(), *out.resolve().parents]:
        env = folder / '.local.env' if folder.name == 'fidelity' else folder / 'fidelity' / '.local.env'
        if env.is_file():
            match = re.search(r'^\s*(?:export\s+)?FIGMA_TOKEN\s*=\s*"?([^"\n]+)"?', env.read_text(), re.M)
            if match:
                return match.group(1).strip()
    raise ValueError('Set FIGMA_TOKEN (a Figma personal access token with file read access) in the '
                     'environment or as FIGMA_TOKEN=... in fidelity/.local.env (git-ignored)')


def get_json(path: str, token: str, params: dict) -> dict:
    url = f'{API}{path}?{urllib.parse.urlencode(params)}'
    request = urllib.request.Request(url, headers={'X-Figma-Token': token})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        hint = {403: 'token lacks access to this file', 404: 'file or node not found',
                429: 'rate limited; retry later'}.get(exc.code, '')
        raise ValueError(f'Figma API {exc.code} for {path}: {hint}') from None


def download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=300) as response:
        return response.read()


def render_images(file_key: str, ids: list[str], token: str, version: str) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for start in range(0, len(ids), 50):
        batch = ids[start:start + 50]
        data = get_json(f'/v1/images/{file_key}', token,
                        {'ids': ','.join(batch), 'scale': SCALE, 'format': 'png', 'version': version})
        if data.get('err'):
            raise ValueError(f"Figma image render failed: {data['err']}")
        for node_id, url in (data.get('images') or {}).items():
            if not url:
                raise ValueError(f'Figma could not render node {node_id} (empty or invisible)')
            result[node_id] = download(url)
    return result


def write_outputs(doc: dict, images: dict[str, bytes], out: Path, frame_id: str, raw: dict | None) -> dict:
    from PIL import Image
    import io
    out.mkdir(parents=True, exist_ok=True)
    (out / 'assets').mkdir(exist_ok=True)
    reference = images.get(frame_id)
    if reference is None:
        raise ValueError('reference render of the frame is missing')
    (out / 'reference.png').write_bytes(reference)
    with Image.open(io.BytesIO(reference)) as im:
        doc['image_size'] = {'width': im.width, 'height': im.height}
        doc['original_reference_size'] = dict(doc['image_size'])
        doc['visual_source'] = 'figma_images_api'
    manifest_assets = []
    for asset in doc['assets']:
        data = images.get(asset['node_id'])
        if data is None:
            raise ValueError(f"asset render missing for {asset['node_id']}")
        name = f"{safe_id(asset['node_id'])}.png"
        (out / 'assets' / name).write_bytes(data)
        with Image.open(io.BytesIO(data)) as im:
            size = {'width': im.width, 'height': im.height}
        asset['pixel_dimensions'] = size
        asset['pixel_dimensions_status'] = 'downloaded'
        manifest_assets.append({'asset_id': asset['asset_id'], 'node_id': asset['node_id'],
                                'relative_path': f'assets/{name}', 'bytes': len(data),
                                'sha256': hashlib.sha256(data).hexdigest(), 'actual_pixel_size': size,
                                'format': 'png', 'scale': SCALE})
    manifest = {'snapshot_id': doc['snapshot_id'], 'resolved_version': doc['resolved_version'],
                'canvas': [doc['canvas']['width'], doc['canvas']['height']],
                'reference': {'path': 'reference.png', 'sha256': hashlib.sha256(reference).hexdigest()},
                'assets': manifest_assets}
    (out / 'source.json').write_text(json.dumps(doc, ensure_ascii=False, indent=1) + '\n')
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n')
    if raw is not None:
        (out / 'figma-nodes.json').write_text(json.dumps(raw, ensure_ascii=False) + '\n')
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--url', required=True, help='Figma link to the frame (contains node-id)')
    parser.add_argument('--out', type=Path, required=True, help='Evidence directory, e.g. fidelity/<page>/evidence')
    parser.add_argument('--version', help='Pin a file version id (default: current version, then pinned)')
    parser.add_argument('--nodes-json', type=Path, help='Offline: saved /v1/files/:key/nodes response')
    parser.add_argument('--images-dir', type=Path, help='Offline: <node-id>.png renders at scale 4')
    args = parser.parse_args()
    try:
        file_key, node_id = parse_url(args.url)
        if args.nodes_json:
            raw = json.loads(args.nodes_json.read_text())
        else:
            token = token_from(args.out)
            params = {'ids': node_id, 'geometry': 'paths'}
            if args.version:
                params['version'] = args.version
            raw = get_json(f'/v1/files/{file_key}/nodes', token, params)
        doc = convert(raw, file_key, node_id)
        ids = [node_id, *(a['node_id'] for a in doc['assets'])]
        if args.images_dir:
            images = {i: (args.images_dir / f'{safe_id(i)}.png').read_bytes() for i in ids
                      if (args.images_dir / f'{safe_id(i)}.png').is_file()}
        else:
            images = render_images(file_key, ids, token, doc['resolved_version'])
        manifest = write_outputs(doc, images, args.out, node_id, raw)
        from evidence_schema import validate
        issues = [i for i in validate(doc) if i['severity'] == 'error']
        print(json.dumps({'status': 'FAIL' if issues else 'OK', 'evidence': str(args.out / 'source.json'),
                          'snapshot_id': doc['snapshot_id'], 'nodes': len(doc['nodes']),
                          'assets': len(manifest['assets']), 'source_gaps': len(doc['source_gaps']),
                          'schema_errors': issues[:10],
                          'next_action': 'prepare' if not issues else 'fix the adapter output'},
                         ensure_ascii=False))
        return 1 if issues else 0
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({'status': 'ERROR', 'error': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
