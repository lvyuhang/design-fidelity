#!/usr/bin/env python3
"""Generate a deterministic Flutter scene from Lanhu evidence.

Every visual parameter comes from the saved MCP source nodes and the prepare
plan; nothing is inferred from screenshots or chosen by a model. The output is
a first implementation that already uses the verified `lanhu_fidelity`
primitives, a token class, stable `sourceKey(node_id)` keys, and override /
tap hooks so page code can replace groups without editing the generated file.

The report lists, per visible node, how it was rendered (draft
`node_decisions`), what was not supported, system chrome regions and font or
asset gaps. It never grants visual acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
from pathlib import Path
from typing import Any

from fidelity_contract import inventory, read_json
from system_chrome import detect_system_chrome
from visual_fidelity_gate import _load_nodes, _validate_evidence

GENERATOR_VERSION = 1
PRIMITIVES_IMPORT = 'package:lanhu_fidelity/lanhu_fidelity.dart'
LINE_WIDTH = 80
# Designers place odd-width items on whole pixels: 172 + 32 + 171 is centred.
CENTER_TOLERANCE = 1.0

# Sketch/AppKit NSTextAlignment. Lanhu's derived `align` string mislabels 2.
TEXT_ALIGN = {0: 'TextAlign.left', 1: 'TextAlign.right', 2: 'TextAlign.center',
              3: 'TextAlign.justify', 4: 'TextAlign.left'}
BORDER_POSITION = {'内边框': 'inside', 'inside': 'inside', '中心边框': 'center',
                   'center': 'center', '外边框': 'outside', 'outside': 'outside'}
STROKE_CAP = {0: 'StrokeCap.butt', 1: 'StrokeCap.round', 2: 'StrokeCap.square'}
STROKE_JOIN = {0: 'StrokeJoin.miter', 1: 'StrokeJoin.round', 2: 'StrokeJoin.bevel'}
CONST_CTORS = {
    'SourceBox', 'SourceFill.color', 'SourceFill.linear', 'SourceLinearGradient',
    'SourceGradientStop', 'SourceBorder', 'SourceShadow', 'SourceRectShape',
    'SourceRectShape.all', 'SourceOvalShape', 'SourcePathShape', 'SourcePathPoint',
    'Offset', 'Color', 'Rect.fromLTWH', 'SizedBox', 'Positioned', 'Positioned.fill',
    'Stack', 'SourceAsset', 'SourcePlaceholder', 'Opacity', 'ClipPath',
    'SourceShapeClipper', 'SourceBackdropBlur', 'SourceLayerBlur', 'Align', 'Center',
    'SystemChromeSlot', 'SourceTextRun',
}


# --------------------------------------------------------------------------
# Minimal Dart expression tree with const propagation and line wrapping.

class Raw:
    def __init__(self, code: str, const: bool = False):
        self.code, self.const = code, const


class Call:
    def __init__(self, ctor: str, *args: Any, **named: Any):
        self.ctor = ctor
        self.args = [a for a in args if a is not None]
        self.named = [(k, v) for k, v in named.items() if v is not None]
        self.const = ctor in CONST_CTORS and all(_is_const(v) for v in self.values())

    def values(self):
        return [*self.args, *(v for _, v in self.named)]


class Lambda:
    """`() => body`, rendered at the surrounding indentation."""
    const = False

    def __init__(self, body: Any):
        self.body = body


class DList:
    def __init__(self, items: list[Any], type_arg: str | None = None):
        self.items, self.type_arg = items, type_arg
        self.const = all(_is_const(v) for v in items)


def _is_const(value: Any) -> bool:
    if isinstance(value, (Raw, Call, DList, Lambda)):
        return value.const
    return isinstance(value, (int, float, str, bool))


def num(value: float) -> str:
    """Compact, stable decimal literal (no binary noise, no lost precision)."""
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Non-finite source number')
    text = f'{value:.4f}'.rstrip('0').rstrip('.')
    return '0' if text in ('-0', '') else text


def dart_string(value: str) -> str:
    escaped = (value.replace('\\', '\\\\').replace("'", "\\'").replace('$', '\\$')
               .replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t'))
    return f"'{escaped}'"


def render(value: Any, indent: int = 0, in_const: bool = False) -> str:
    if isinstance(value, Raw):
        return value.code
    if isinstance(value, Lambda):
        return '() => ' + render(value.body, indent, False)
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        return num(value)
    if isinstance(value, str):
        return dart_string(value)
    prefix = 'const ' if getattr(value, 'const', False) and not in_const else ''
    child_const = in_const or bool(prefix)
    pad, inner = ' ' * indent, ' ' * (indent + 2)
    if isinstance(value, DList):
        type_arg = f'<{value.type_arg}>' if value.type_arg else ''
        parts = [render(v, indent + 2, child_const) for v in value.items]
        flat = f'{prefix}{type_arg}[{", ".join(parts)}]'
        if '\n' not in flat and len(flat) + indent <= LINE_WIDTH:
            return flat
        body = ''.join(f'{inner}{render(v, indent + 2, child_const)},\n' for v in value.items)
        return f'{prefix}{type_arg}[\n{body}{pad}]'
    if isinstance(value, Call):
        def parts(ind):
            out = [render(v, ind, child_const) for v in value.args]
            out += [f'{k}: {render(v, ind, child_const)}' for k, v in value.named]
            return out
        flat = f'{prefix}{value.ctor}({", ".join(parts(indent))})'
        if '\n' not in flat and len(flat) + indent <= LINE_WIDTH:
            return flat
        body = ''.join(f'{inner}{p},\n' for p in parts(indent + 2))
        return f'{prefix}{value.ctor}(\n{body}{pad})'
    raise TypeError(f'Cannot render {type(value)!r}')


# --------------------------------------------------------------------------
# Source value parsing.

def parse_color(value: Any) -> tuple[int, int, int, float] | None:
    """Prefer the `value` string: real exports carry zeroed r/g/b beside it."""
    if isinstance(value, dict):
        parsed = parse_color(value.get('value'))
        if parsed:
            return parsed
        if all(k in value for k in 'rgba'):
            return (round(value['r']), round(value['g']), round(value['b']), float(value['a']))
        return None
    if not isinstance(value, str):
        return None
    text = value.strip()
    match = re.fullmatch(r'rgba?\(([^)]*)\)', text)
    if match:
        parts = [p.strip() for p in match.group(1).split(',')]
        if len(parts) in (3, 4):
            r, g, b = (round(float(p)) for p in parts[:3])
            a = float(parts[3]) if len(parts) == 4 else 1.0
            return (r, g, b, a)
    match = re.fullmatch(r'#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?', text)
    if match:
        rgb = int(match.group(1), 16)
        a = int(match.group(2), 16) / 255 if match.group(2) else 1.0
        return (rgb >> 16 & 255, rgb >> 8 & 255, rgb & 255, a)
    return None


def argb_hex(color: tuple[int, int, int, float]) -> str:
    r, g, b, a = color
    alpha = max(0, min(255, round(a * 255)))
    return f'{alpha:02X}{r:02X}{g:02X}{b:02X}'


def enabled(items: Any) -> list[dict]:
    return [i for i in (items or []) if isinstance(i, dict) and i.get('isEnabled', True) is not False]


def is_truthy_mask(raw: dict) -> bool:
    return bool(raw.get('hasClippingMask')) and raw.get('hasClippingMask') not in (0, '0', False)


def font_weight(value: Any) -> int:
    names = {'thin': 100, 'ultralight': 200, 'extralight': 200, 'light': 300,
             'regular': 400, 'normal': 400, 'medium': 500, 'semibold': 600,
             'demibold': 600, 'bold': 700, 'heavy': 800, 'extrabold': 800, 'black': 900}
    if isinstance(value, str):
        key = value.strip().lower().replace('-', '').replace(' ', '')
        if key in names:
            return names[key]
        try:
            value = float(value)
        except ValueError:
            return 400
    if isinstance(value, (int, float)) and math.isfinite(value):
        return int(min(900, max(100, round(value / 100) * 100)))
    return 400


# --------------------------------------------------------------------------

class Generator:
    def __init__(self, nodes: dict, documents: list[dict], plan: dict | None,
                 font_map: dict, class_name: str, app_root: Path | None,
                 asset_dir: str | None, implementation_path: str):
        self.nodes, self.documents, self.plan = nodes, documents, plan or {}
        self.class_name, self.app_root, self.asset_dir = class_name, app_root, asset_dir
        self.implementation_path = implementation_path
        first = documents[0]
        self.canvas = (float(first['canvas']['width']), float(first['canvas']['height']))
        self.visible = inventory(nodes)
        self.children: dict[Any, list[str]] = {}
        for key, node in nodes.items():
            parent = node.get('parent_id') if node.get('parent_id') in nodes else None
            self.children.setdefault(parent, []).append(key)
        for keys in self.children.values():
            keys.sort(key=lambda k: (nodes[k].get('source_order', 0), k))
        self.colors: dict[str, str] = {}
        self.text_styles: dict[str, tuple[str, Call]] = {}
        self.assets: dict[str, dict] = {}
        self.asset_constants: dict[str, str] = {}
        self.records: dict[str, dict] = {}
        self.unsupported: list[dict] = []
        self.chrome: list[dict] = []
        self.issues: list[dict] = []
        self.methods: list[tuple[str, str, Any]] = []
        self.short_ids = self._short_ids()
        self.chrome_owners = {e['node_id']: e for e in detect_system_chrome(nodes, self.canvas)}
        self._fonts = self._font_lookup(font_map)
        self._index_assets()

    # ---- inputs -----------------------------------------------------------
    def _short_ids(self) -> dict[str, str]:
        result = {}
        for key in self.nodes:
            clean = re.sub(r'[^0-9A-Za-z]', '', key) or 'node'
            length = 8
            while any(v == clean[:length] for v in result.values()) and length < len(clean):
                length += 4
            result[key] = clean[:length]
        return result

    def _font_lookup(self, font_map: dict) -> dict[str, str]:
        lookup = {}
        for label, entry in (font_map.get('fonts') or {}).items():
            if entry.get('runtime_family'):
                lookup[label] = entry['runtime_family']
        for entry in self.plan.get('fonts', []):
            if entry.get('runtime_family'):
                lookup[f"{entry.get('source_family')}@{entry.get('weight')}"] = entry['runtime_family']
        return lookup

    def _index_assets(self) -> None:
        for item in self.plan.get('assets', []):
            if item.get('kind') == 'render_fallback' or not item.get('path') or not item.get('export_rect'):
                continue
            self.assets[item['node_id']] = item

    # ---- tokens -----------------------------------------------------------
    def color(self, color: tuple[int, int, int, float]) -> Raw:
        code = argb_hex(color)
        name = f'c{code}'
        self.colors[name] = code
        return Raw(f'{self.class_name}Tokens.{name}', const=True)

    def text_style(self, run: dict, node_id: str) -> Raw:
        family_src = run.get('font_family')
        weight = font_weight(run.get('font_weight'))
        label = f'{family_src}@{run.get("font_weight")}'
        family = self._fonts.get(label)
        if family is None:
            family = family_src or 'sans-serif'
            self.issues.append({'kind': 'font_mapping_missing', 'node_id': node_id, 'font': label})
        size = float(run.get('font_size') or 14)
        line = run.get('line_height')
        line = float(line) if isinstance(line, (int, float)) and line > 0 else None
        if line is None:
            self.unsupported.append({'node_id': node_id, 'feature': 'natural_line_height',
                                     'detail': 'Sketch auto line height differs from Flutter metrics; verify visually'})
        spacing = float(run.get('letter_spacing') or 0)
        color = parse_color(run.get('color')) or (0, 0, 0, 1.0)
        decoration = {'underline': 'TextDecoration.underline',
                      'line-through': 'TextDecoration.lineThrough',
                      'strikethrough': 'TextDecoration.lineThrough'}.get(
            str(run.get('decoration_line') or 'none').lower())
        name = (f't{num(size)}w{weight}h{num(line) if line else "n"}'
                f'c{argb_hex(color)}').replace('.', '_').replace('-', 'm')
        if spacing:
            name += f'k{num(spacing)}'.replace('.', '_').replace('-', 'm')
        if decoration:
            name += 'u' if 'underline' in decoration else 's'
        signature_family = re.sub(r'[^0-9A-Za-z]', '', family)
        key = f'{name}|{family}'
        if key not in self.text_styles:
            existing = {n for n, _ in self.text_styles.values()}
            if name in existing:
                name = f'{name}{signature_family[:6]}'
            call = Call('sourceTextStyle', fontFamily=family, fontSize=size,
                        fontWeight=Raw(f'FontWeight.w{weight}', True),
                        lineHeight=line, letterSpacing=spacing if spacing else None,
                        color=self.color(color),
                        decoration=Raw(decoration, True) if decoration else None)
            self.text_styles[key] = (name, call)
        return Raw(f'{self.class_name}Tokens.{self.text_styles[key][0]}')

    # ---- classification ---------------------------------------------------
    def record(self, key: str, mode: str, **extra: Any) -> None:
        node = self.nodes[key]
        entry = {'node_id': key, 'name': node.get('name'), 'node_type': node.get('node_type'),
                 'mode': mode, **extra}
        if key in self.records:
            return
        self.records[key] = entry

    def descendants(self, key: str) -> list[str]:
        out, stack = [], list(self.children.get(key, []))
        while stack:
            item = stack.pop()
            out.append(item)
            stack.extend(self.children.get(item, []))
        return out

    def chrome_kind(self, key: str) -> str | None:
        entry = self.chrome_owners.get(key)
        return entry['kind'] if entry else None

    def shape_of(self, key: str) -> tuple[Any, str]:
        raw = self.nodes[key].get('raw_style') or {}
        points = raw.get('points') or []
        radius = raw.get('radius')

        def pt(p):
            return (round(float(p.get('x', 0)), 6), round(float(p.get('y', 0)), 6))

        corners = [pt(p.get('point', {})) for p in points]
        curved = any(p.get('hasCurveFrom') or p.get('hasCurveTo') for p in points)
        if len(points) == 4 and not curved and corners == [(0, 0), (1, 0), (1, 1), (0, 1)]:
            radii = [float(p.get('cornerRadius') or 0) for p in points]
            if not any(radii) and isinstance(radius, list) and radius:
                radii = [float(r) for r in (radius * 4 if len(radius) == 1 else radius)[:4]]
            if not any(radii):
                return Call('SourceRectShape'), 'rect'
            if len(set(radii)) == 1:
                return Call('SourceRectShape.all', radii[0]), 'rect'
            return Call('SourceRectShape', radii=DList(radii, 'double')), 'rect'
        if (len(points) == 4 and all(p.get('hasCurveFrom') and p.get('hasCurveTo') for p in points)
                and sorted(corners) == sorted([(0.5, 0), (1, 0.5), (0.5, 1), (0, 0.5)])):
            return Call('SourceOvalShape'), 'oval'
        if points:
            if any(float(p.get('cornerRadius') or 0) > 0 for p in points):
                self.unsupported.append({'node_id': key, 'feature': 'path_corner_radius',
                                         'detail': 'per-vertex corner radius on a free path is drawn sharp'})
            items = []
            for p in points:
                point = pt(p.get('point', {}))
                named = {}
                if p.get('hasCurveFrom'):
                    named['curveFrom'] = Call('Offset', *pt(p.get('curveFrom', {})))
                if p.get('hasCurveTo'):
                    named['curveTo'] = Call('Offset', *pt(p.get('curveTo', {})))
                items.append(Call('SourcePathPoint', Call('Offset', *point), **named))
            closed = bool(raw.get('isClosed', True))
            return Call('SourcePathShape', points=DList(items),
                        closed=None if closed else False,
                        evenOdd=True if raw.get('windingRule') == 1 else None), 'path'
        if isinstance(radius, list) and radius:
            radii = [float(r) for r in (radius * 4 if len(radius) == 1 else radius)[:4]]
            return (Call('SourceRectShape.all', radii[0]) if len(set(radii)) == 1
                    else Call('SourceRectShape', radii=DList(radii, 'double'))), 'rect'
        return None, 'unknown'

    def fill_of(self, fill: dict, key: str) -> Call | None:
        opacity = float(fill.get('opacity', 1) if fill.get('opacity') is not None else 1)
        gradient = fill.get('gradient')
        if fill.get('type') == 'gradient' or isinstance(gradient, dict):
            if not isinstance(gradient, dict) or gradient.get('type', 'linear') != 'linear' \
                    or gradient.get('gradientType', 0) not in (0, None):
                self.unsupported.append({'node_id': key, 'feature': 'non_linear_gradient',
                                         'detail': json.dumps(gradient, ensure_ascii=False)[:200]})
                return None
            stops = []
            for stop in gradient.get('colorStops', []):
                color = parse_color(stop.get('color'))
                if color is None:
                    continue
                stops.append(Call('SourceGradientStop', float(stop.get('position', 0)), self.color(color)))
            start, end = gradient.get('from', {}), gradient.get('to', {})
            return Call('SourceFill.linear', Call('SourceLinearGradient',
                        **{'from': Call('Offset', float(start.get('x', 0)), float(start.get('y', 0))),
                           'to': Call('Offset', float(end.get('x', 1)), float(end.get('y', 0))),
                           'stops': DList(stops)}),
                        opacity=opacity if opacity < 1 else None)
        if fill.get('type') not in (None, 'color') or fill.get('fillType') not in (None, 0):
            self.unsupported.append({'node_id': key, 'feature': 'pattern_or_image_fill',
                                     'detail': f"type={fill.get('type')} fillType={fill.get('fillType')}"})
            return None
        color = parse_color(fill.get('color'))
        if color is None:
            return None
        return Call('SourceFill.color', self.color(color), opacity=opacity if opacity < 1 else None)

    def paint_of(self, key: str) -> dict[str, Any]:
        raw = self.nodes[key].get('raw_style') or {}
        if raw.get('blendMode') not in (None, 0):
            self.unsupported.append({'node_id': key, 'feature': 'blend_mode',
                                     'detail': f"blendMode={raw.get('blendMode')}"})
        fills = [f for f in (self.fill_of(f, key) for f in enabled(raw.get('fills'))) if f]
        options = raw.get('borderOptions') or {}
        dash = [float(v) for v in options.get('dashPattern') or [] if isinstance(v, (int, float))]
        borders = []
        for border in enabled(raw.get('borders')):
            fill = self.fill_of(border, key)
            if fill is None or float(border.get('thickness') or 0) <= 0:
                continue
            position = BORDER_POSITION.get(border.get('position'), 'center')
            borders.append(Call(
                'SourceBorder', thickness=float(border['thickness']), fill=fill,
                position=None if position == 'center' else Raw(f'SourceBorderPosition.{position}', True),
                cap=None if options.get('lineCapStyle', 0) in (0, None)
                else Raw(STROKE_CAP.get(options.get('lineCapStyle'), 'StrokeCap.butt'), True),
                join=None if options.get('lineJoinStyle', 0) in (0, None)
                else Raw(STROKE_JOIN.get(options.get('lineJoinStyle'), 'StrokeJoin.miter'), True),
                dash=DList(dash, 'double') if dash else None))
        shadows = []
        for kind, items in (('shadow', raw.get('shadow')), ('innerShadow', raw.get('innerShadows') or raw.get('innerShadow'))):
            for shadow in enabled(items):
                color = parse_color(shadow.get('color'))
                if color is None:
                    continue
                inner = kind == 'innerShadow' or shadow.get('type') in ('内阴影', 'inner', 'innerShadow')
                dx, dy = float(shadow.get('offsetX') or 0), float(shadow.get('offsetY') or 0)
                spread = float(shadow.get('spread') or 0)
                if spread < 0:
                    self.unsupported.append({'node_id': key, 'feature': 'negative_shadow_spread',
                                             'detail': 'exact only for rect/oval shapes'})
                shadows.append(Call('SourceShadow', color=self.color(color),
                                    offset=Call('Offset', dx, dy) if dx or dy else None,
                                    blurRadius=float(shadow.get('blurRadius') or 0) or None,
                                    spread=spread or None, inner=True if inner else None))
        opacity = raw.get('opacity')
        opacity = float(opacity) / 100 if isinstance(opacity, (int, float)) else 1.0
        return {'fills': fills, 'borders': borders, 'shadows': shadows,
                'opacity': max(0.0, min(1.0, opacity))}

    # ---- emission ---------------------------------------------------------
    def frame(self, key: str) -> tuple[float, float, float, float]:
        b = self.nodes[key]['bounds']
        return (float(b['x']), float(b['y']), float(b['width']), float(b['height']))

    def leaf(self, key: str) -> tuple[Any, dict]:
        """Returns (widget expression, placement hints) for a non-container node."""
        node = self.nodes[key]
        raw = node.get('raw_style') or {}
        hints: dict[str, Any] = {}
        if key in self.assets:
            asset = self.assets[key]
            x, y, _, _ = self.frame(key)
            ex, ey, ew, eh = asset['export_rect']
            const_name = self.asset_constant(key, asset)
            export = Call('Rect.fromLTWH', ex - x, ey - y, ew, eh)
            if [ex, ey, ew, eh] == list(self.frame(key)):
                export = None
            for child in self.descendants(key):
                self.record(child, 'covered_by_asset', owner=key)
            self.record(key, 'original_asset', asset=asset.get('path'),
                        export_rect=asset['export_rect'])
            return Call('SourceAsset', Raw(f'{self.class_name}Assets.{const_name}', True),
                        exportRect=export), hints
        if node.get('text'):
            return self.text(key), {'text': True, 'raw': raw}
        if node.get('node_type') == 'bitmap':
            self.record(key, 'missing_asset_placeholder', reason='bitmap without exported original')
            return self.placeholder(key), hints
        shape, kind = self.shape_of(key)
        paint = self.paint_of(key)
        if shape is None:
            if node.get('asset_ids'):
                self.record(key, 'missing_asset_placeholder', reason='asset not exported/installed')
                self.issues.append({'kind': 'asset_not_installed', 'node_id': key})
            else:
                self.record(key, 'missing_asset_placeholder', reason='no complete source geometry')
            return self.placeholder(key), hints
        if not (paint['fills'] or paint['borders'] or paint['shadows']):
            self.record(key, 'no_visible_paint')
            return None, hints
        box = Call('SourceBox', shape=shape if kind != 'rect' or shape.args or shape.named else None,
                   fills=DList(paint['fills']) if paint['fills'] else None,
                   borders=DList(paint['borders']) if paint['borders'] else None,
                   shadows=DList(paint['shadows']) if paint['shadows'] else None,
                   opacity=paint['opacity'] if paint['opacity'] < 1 else None)
        widget = self.effects(key, box, shape)
        self.record(key, 'native_exact', primitive='SourceBox', shape=kind)
        return widget, hints

    def placeholder(self, key: str) -> Any:
        """Missing content only: borders, shadows, opacity and blur stay."""
        paint = self.paint_of(key)
        widget: Any = Call('SourcePlaceholder', nodeId=key)
        if paint['borders'] or paint['shadows']:
            box = Call('SourceBox', borders=DList(paint['borders']) if paint['borders'] else None,
                       shadows=DList(paint['shadows']) if paint['shadows'] else None)
            widget = Call('Stack', children=DList([Call('Positioned.fill', child=box),
                                                   Call('Positioned.fill', child=widget)], 'Widget'))
        if paint['opacity'] < 1:
            widget = Call('Opacity', opacity=paint['opacity'], child=widget)
        return self.effects(key, widget, None)

    def effects(self, key: str, widget: Any, shape: Any) -> Any:
        raw = self.nodes[key].get('raw_style') or {}
        blur = raw.get('blur')
        if isinstance(blur, dict) and blur.get('isEnabled', True) and float(blur.get('radius') or 0) > 0:
            if blur.get('blurType') == 3:
                saturation = blur.get('saturation', 1)
                widget = Call('SourceBackdropBlur', radius=float(blur['radius']),
                              shape=shape if shape is not None and (shape.args or shape.named or shape.ctor != 'SourceRectShape') else None,
                              saturation=float(saturation) if isinstance(saturation, (int, float)) and saturation != 1 else None,
                              child=widget)
            elif blur.get('blurType') in (0, None):
                widget = Call('SourceLayerBlur', radius=float(blur['radius']), child=widget)
            else:
                self.unsupported.append({'node_id': key, 'feature': 'motion_or_zoom_blur',
                                         'detail': f"blurType={blur.get('blurType')}"})
        if raw.get('rotation'):
            self.unsupported.append({'node_id': key, 'feature': 'rotation',
                                     'detail': f"rotation={raw.get('rotation')}; not applied"})
        if raw.get('isFlippedHorizontal') or raw.get('isFlippedVertical'):
            widget = Call('Transform.flip', flipX=bool(raw.get('isFlippedHorizontal')) or None,
                          flipY=bool(raw.get('isFlippedVertical')) or None, child=widget)
        return widget

    def text(self, key: str) -> Any:
        node = self.nodes[key]
        raw = node.get('raw_style') or {}
        font = raw.get('font') or {}
        spec = node.get('text_spec') or {}
        runs = [r for r in spec.get('text_runs', []) if isinstance(r.get('text'), str)]
        base = runs[0] if runs else (spec.get('base_style') or {})
        if not runs or ''.join(r['text'] for r in runs) != node['text']:
            self.issues.append({'kind': 'text_run_coverage', 'node_id': key})
            runs = [dict(base, text=node['text'])]
        code = font.get('textAlignment')
        if code is None and font.get('styles'):
            code = font['styles'][0].get('alignment')
        align = TEXT_ALIGN.get(code if isinstance(code, int) else 0, 'TextAlign.left')
        wrap = raw.get('textBehaviour', 0) not in (0, None)
        style = self.text_style(base, key)
        named = {'style': style,
                 'textAlign': None if align == 'TextAlign.left' else Raw(align, True),
                 'softWrap': True if wrap else None}
        if len(runs) == 1:
            widget = Call('SourceText', node['text'], **named)
        else:
            widget = Call('SourceText.rich', DList([Call('SourceTextRun', r['text'], self.text_style(r, key))
                                                   for r in runs]), **named)
        opacity = raw.get('opacity')
        if isinstance(opacity, (int, float)) and opacity < 100:
            widget = Call('Opacity', opacity=float(opacity) / 100, child=widget)
        self.record(key, 'native_exact', primitive='SourceText', align=align, wrap=wrap)
        return self.effects(key, widget, None)

    def asset_constant(self, key: str, asset: dict) -> str:
        if key in self.asset_constants:
            return self.asset_constants[key]
        source = Path(asset['path'])
        name = re.sub(r'[^0-9A-Za-z]+', ' ', source.stem).strip().split() or ['asset']
        ident = name[0].lower() + ''.join(p.capitalize() for p in name[1:])
        if not ident[0].isalpha():
            ident = 'a' + ident
        while ident in self.asset_constants.values():
            ident += self.short_ids[key][:4]
        self.asset_constants[key] = ident
        flutter_key = f'{self.asset_dir.rstrip("/")}/{source.name}' if self.asset_dir else source.name
        self.asset_keys = getattr(self, 'asset_keys', {})
        self.asset_keys[ident] = {'flutter_asset': flutter_key, 'source': str(source),
                                  'sha256': asset.get('sha256'), 'node_id': key}
        return ident

    def placement(self, key: str, parent_rect: tuple, stretch: bool, widget: Any,
                  hints: dict, at_root: bool) -> Call:
        x, y, w, h = self.frame(key)
        px, py, pw, ph = parent_rect
        left, top = x - px, y - py
        right = (px + pw) - (x + w)
        bottom = (py + ph) - (y + h)
        is_text = hints.get('text')
        auto_text = is_text and (hints['raw'].get('textBehaviour', 0) in (0, None))
        align_code = ((hints.get('raw') or {}).get('font') or {}).get('textAlignment')
        left_aligned_text = auto_text and align_code in (0, 4, None)
        if at_root and (x, y, w, h) == (px, py, pw, ph) and not is_text:
            return Call('Positioned.fill', child=widget)
        vertical: dict[str, Any] = {'top': top}
        if not is_text:
            vertical['height'] = h
        if at_root and stretch and bottom <= 1 and top > ph / 2:
            vertical = {'bottom': bottom} if is_text else {'bottom': bottom, 'height': h}
        if stretch:
            if abs(left - right) <= CENTER_TOLERANCE and left <= 32 and w >= pw / 2:
                if is_text:
                    self._anchor(key, 'stretch')
                return Call('Positioned', left=left, right=right, **vertical, child=widget)
            if abs(left - right) <= CENTER_TOLERANCE:
                if left_aligned_text:
                    self._anchor(key, 'center')
                inner = widget if left_aligned_text else Call('SizedBox', width=w, child=widget)
                return Call('Positioned', left=0, right=0, **vertical,
                            child=Call('Align', alignment=Raw('Alignment.topCenter', True), child=inner))
            if right < left:
                # Auto-width text keeps its intrinsic width and grows leftwards.
                width = None if left_aligned_text else w
                if left_aligned_text:
                    self._anchor(key, 'right')
                return Call('Positioned', right=right, **vertical, width=width, child=widget)
        if left_aligned_text:
            return Call('Positioned', left=left, **vertical, child=widget)
        return Call('Positioned', left=left, **vertical, width=w, child=widget)

    def _anchor(self, key: str, edge: str) -> None:
        """Record which edge a text box is laid out from, so the geometry probe
        compares that edge instead of turning advance-width noise into offsets."""
        if key in self.records:
            self.records[key]['anchor'] = edge

    def container(self, key: str | None, rect: tuple, stretch: bool, at_root: bool = False) -> list[Any]:
        """Children of a group as Positioned widgets in paint order."""
        result: list[Any] = []
        siblings = self.children.get(key, [])
        index = 0
        while index < len(siblings):
            child = siblings[index]
            raw = self.nodes[child].get('raw_style') or {}
            if is_truthy_mask(raw) and child not in self.assets:
                masked = []
                index += 1
                while index < len(siblings):
                    nxt = self.nodes[siblings[index]].get('raw_style') or {}
                    if nxt.get('shouldBreakMaskChain'):
                        break
                    masked.append(siblings[index])
                    index += 1
                placed = self.place(child, rect, stretch, at_root)
                if placed is not None:
                    result.append(placed)
                result.extend(self.masked_group(child, masked, rect))
                continue
            placed = self.place(child, rect, stretch, at_root)
            if placed is not None:
                result.append(placed)
            index += 1
        return result

    def masked_group(self, mask: str, members: list[str], parent_rect: tuple) -> list[Any]:
        if not members:
            return []
        shape, kind = self.shape_of(mask)
        mx, my, mw, mh = self.frame(mask)
        inner = []
        for member in members:
            placed = self.place(member, (mx, my, mw, mh), False, False)
            if placed is not None:
                inner.append(placed)
        if not inner:
            return []
        if shape is None:
            self.unsupported.append({'node_id': mask, 'feature': 'mask_without_geometry',
                                     'detail': 'masked layers drawn unclipped'})
            clipped = Call('Stack', clipBehavior=Raw('Clip.none', True), children=DList(inner, 'Widget'))
        else:
            clipped = Call('ClipPath', clipper=Call('SourceShapeClipper', shape),
                           child=Call('Stack', clipBehavior=Raw('Clip.none', True),
                                      children=DList(inner, 'Widget')))
        if mask in self.records:
            self.records[mask]['masks'] = members
        else:
            self.record(mask, 'native_exact', primitive='mask', shape=kind, masks=members)
        px, py, _, _ = parent_rect
        return [Call('Positioned', left=mx - px, top=my - py, width=mw, height=mh, child=clipped)]

    def place(self, key: str, parent_rect: tuple, stretch: bool, at_root: bool) -> Call | None:
        node = self.nodes[key]
        if node.get('effective_source_visible', node.get('source_visible')) is False:
            self.record(key, 'hidden')
            for child in self.descendants(key):
                self.record(child, 'hidden')
            return None
        b = node.get('bounds') or {}
        if b.get('width', 0) <= 0 or b.get('height', 0) <= 0:
            self.record(key, 'zero_size')
            return None
        kind = self.chrome_kind(key)
        if kind:
            rect = list(self.frame(key))
            if not any(c['rect'] == rect and c['kind'] == kind for c in self.chrome):
                self.chrome.append({'node_id': key, 'kind': kind, 'rect': rect})
            self.record(key, 'system_chrome', kind=kind)
            for child in self.descendants(key):
                self.record(child, 'system_chrome', kind=kind, owner=key)
            return None
        is_group = bool(self.children.get(key)) and key not in self.assets
        if is_group:
            return self.group(key, parent_rect, stretch, at_root)
        widget, hints = self.leaf(key)
        if widget is None:
            return None
        widget = Call('_node', Raw('context'), key, Lambda(widget))
        return self.placement(key, parent_rect, stretch, widget, hints, at_root)

    def group(self, key: str, parent_rect: tuple, stretch: bool, at_root: bool) -> Call | None:
        rect = self.frame(key)
        px, py, pw, ph = parent_rect
        x, y, w, h = rect
        left, right = x - px, (px + pw) - (x + w)
        child_stretch = stretch and abs(left - right) <= CENTER_TOLERANCE and left <= 32 and w >= pw / 2
        raw = self.nodes[key].get('raw_style') or {}
        children = self.container(key, rect, child_stretch)
        paint = self.paint_of(key)
        if paint['shadows'] or paint['borders']:
            self.unsupported.append({'node_id': key, 'feature': 'group_shadow_or_border',
                                     'detail': 'group-level shadows/borders are not applied'})
        if paint['fills'] and self.nodes[key].get('node_type') != 'artboard-group':
            children.insert(0, Call('Positioned.fill', child=Call('SourceBox', fills=DList(paint['fills']))))
        if not children:
            self.record(key, 'empty_group')
            return None
        method = f'_g{self.short_ids[key]}'
        body: Any = Call('Stack', clipBehavior=Raw('Clip.none', True), children=DList(children, 'Widget'))
        if paint['opacity'] < 1:
            body = Call('Opacity', opacity=paint['opacity'], child=body)
        body = self.effects(key, body, None)
        name = str(self.nodes[key].get('name') or '')
        self.methods.append((method, name, body))
        self.record(key, 'container', symbol=f'{self.class_name}Scene.{method}')
        call = Call('_node', Raw('context'), key, Raw(f'() => {method}(context)'))
        hints = {}
        if child_stretch:
            vertical = {'top': y - py, 'height': h}
            if at_root and stretch and (py + ph) - (y + h) <= 1 and y - py > ph / 2:
                vertical = {'bottom': (py + ph) - (y + h), 'height': h}
            return Call('Positioned', left=left, right=right, **vertical, child=call)
        return self.placement(key, parent_rect, stretch, call, hints, at_root)

    # ---- output -----------------------------------------------------------
    def generate(self) -> tuple[str, dict]:
        width, height = self.canvas
        roots = self.children.get(None, [])
        canvas_rect = (0.0, 0.0, width, height)
        artboards = [r for r in roots if self.nodes[r].get('node_type') == 'artboard-group'
                     and self.frame(r) == canvas_rect]
        background = None
        if len(artboards) == 1:
            root_key = artboards[0]
            raw = self.nodes[root_key].get('raw_style') or {}
            if raw.get('hasBackgroundColor'):
                fills = [f for f in (self.fill_of(f, root_key) for f in enabled(raw.get('fills'))) if f]
                if fills:
                    background = Call('Positioned.fill', child=Call('SourceBox', fills=DList(fills)))
            self.record(root_key, 'container', symbol=f'{self.class_name}Scene.build')
            children = self.container(root_key, canvas_rect, True, at_root=True)
        else:
            children = self.container(None, canvas_rect, True, at_root=True)
        if background is not None:
            children.insert(0, background)
        for key in self.visible:
            if key not in self.records:
                self.record(key, 'not_emitted')
                self.issues.append({'kind': 'node_not_emitted', 'node_id': key})
        dart = self.dart(children)
        return dart, self.report()

    def dart(self, children: list[Any]) -> str:
        width, height = self.canvas
        first = self.documents[0]
        lines = [
            '// GENERATED by lanhu-design-fidelity/scripts/generate_flutter.py; do not edit.',
            f'// Source: {first.get("design_name") or ""} snapshot {first.get("snapshot_id")}',
            f'// version {first.get("resolved_version")}, canvas {num(width)}x{num(height)}.',
            '// Replace groups through `overrides` / wire actions through `onTap`.',
            '// ignore_for_file: prefer_const_constructors, unused_element',
            '',
            "import 'package:flutter/widgets.dart';",
            f"import '{PRIMITIVES_IMPORT}';",
            '',
            f'abstract final class {self.class_name}Tokens {{',
        ]
        for name, code in sorted(self.colors.items()):
            lines.append(f'  static const Color {name} = Color(0x{code});')
        for name, call in sorted(self.text_styles.values(), key=lambda item: item[0]):
            lines.append(f'  static final TextStyle {name} = {render(call, 4)};')
        lines += ['}', '', f'abstract final class {self.class_name}Assets {{']
        keys = getattr(self, 'asset_keys', {})
        for ident, entry in sorted(keys.items()):
            lines.append(f"  static const String {ident} = {dart_string(entry['flutter_asset'])};")
        lines.append('  static const List<String> all = <String>[' +
                     ', '.join(sorted(keys)) + '];')
        lines += ['}', '']
        stack = Call('Stack', clipBehavior=Raw('Clip.hardEdge', True), children=DList(children, 'Widget'))
        lines += [
            f'class {self.class_name}Scene extends StatelessWidget {{',
            f'  const {self.class_name}Scene({{',
            '    super.key,',
            '    this.overrides = const <String, WidgetBuilder>{},',
            '    this.onTap = const <String, VoidCallback>{},',
            '    this.fillHeight = false,',
            '  });',
            '',
            f'  static const Size designSize = Size({num(width)}, {num(height)});',
            '',
            '  /// Replacement widgets keyed by source node id; placed in the node frame.',
            '  final Map<String, WidgetBuilder> overrides;',
            '',
            '  /// Tap handlers keyed by source node id.',
            '  final Map<String, VoidCallback> onTap;',
            '',
            '  /// Expand to the parent height (bottom-anchored nodes follow it).',
            '  final bool fillHeight;',
            '',
            '  Widget _node(BuildContext context, String id, Widget Function() build) {',
            '    final override = overrides[id];',
            '    var child = override != null ? override(context) : build();',
            '    final tap = onTap[id];',
            '    if (tap != null) {',
            '      child = GestureDetector(',
            '          behavior: HitTestBehavior.opaque, onTap: tap, child: child);',
            '    }',
            '    return SourceNode(nodeId: id, child: child);',
            '  }',
            '',
            '  @override',
            '  Widget build(BuildContext context) {',
            '    return SizedBox(',
            f'      height: fillHeight ? double.infinity : {num(height)},',
            f'      child: {render(stack, 6)},',
            '    );',
            '  }',
        ]
        for method, name, body in self.methods:
            lines += ['', f'  /// {name}'.rstrip(),
                      f'  Widget {method}(BuildContext context) => {render(body, 4)};']
        lines += ['}', '']
        return '\n'.join(lines)

    def report(self) -> dict:
        first = self.documents[0]
        decisions = {}
        mode_map = {'native_exact': 'native_exact', 'original_asset': 'original_asset',
                    'missing_asset_placeholder': 'missing_asset_placeholder',
                    'container': 'native_exact', 'no_visible_paint': 'native_exact',
                    'covered_by_asset': 'original_asset'}
        asset_keys = getattr(self, 'asset_keys', {})
        for key, entry in self.records.items():
            if key not in self.visible:
                continue
            if entry['mode'] == 'system_chrome':
                owner = entry.get('owner', key)
                rect = next((c['rect'] for c in self.chrome if c['node_id'] == owner), None)
                decisions[key] = {'mode': 'excluded_with_reason',
                                  'reason': f"OS-drawn {entry['kind']} in the design mock-up",
                                  'exclusion': {'kind': 'system_chrome', 'chrome': entry['kind'],
                                                'rect': rect}}
                continue
            mode = mode_map.get(entry['mode'])
            if mode is None:
                continue
            decision = {'mode': mode, 'implementation': self.implementation_path,
                        'symbol': f'{self.class_name}Scene#{key}'}
            if mode == 'original_asset':
                owner = entry.get('owner', key)
                ident = self.asset_constants.get(owner)
                decision['asset'] = (asset_keys.get(ident) or {}).get('flutter_asset')
                if owner != key:
                    decision['covered_by'] = owner
            if mode == 'missing_asset_placeholder':
                decision['shape'] = 'rect'
            if entry.get('anchor'):
                decision['anchor'] = entry['anchor']
            decisions[key] = decision
        counts: dict[str, int] = {}
        for entry in self.records.values():
            counts[entry['mode']] = counts.get(entry['mode'], 0) + 1
        return {
            'generator': 'generate_flutter.py', 'generator_version': GENERATOR_VERSION,
            'status': 'GENERATED_FOR_REVIEW',
            'scope': 'deterministic first implementation; not visual acceptance',
            'snapshot_id': first.get('snapshot_id'), 'resolved_version': first.get('resolved_version'),
            'canvas': list(self.canvas), 'class_name': self.class_name,
            'mode_counts': dict(sorted(counts.items())),
            'nodes': list(self.records.values()),
            'system_chrome': self.chrome,
            'unsupported': self.unsupported,
            'issues': self.issues,
            'assets': [dict(identifier=k, **v) for k, v in sorted(getattr(self, 'asset_keys', {}).items())],
            'draft_node_decisions': decisions,
        }


HARNESS = Path(__file__).resolve().parents[1] / 'assets' / 'flutter_render_harness.dart'


def write_render_test(path: Path, app_root: Path | None, output: Path, class_name: str,
                      scale: float, output_env: str) -> dict:
    """Create the page render test once (it is project code, never overwritten)."""
    from scene_test_codegen import page_import
    result = {'path': str(path), 'created': False}
    harness = path.parent / 'support' / 'fidelity_render_harness.dart'
    if not harness.exists():
        harness.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HARNESS, harness)
        result['harness_installed'] = str(harness)
    if path.exists():
        return result
    page = page_import(app_root, output, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"""import 'package:flutter_test/flutter_test.dart';

import '{page}';
import 'support/fidelity_render_harness.dart';

void main() {{
  FidelityTestBinding();
  setUpAll(loadDeclaredFidelityFonts);

  testWidgets('{class_name} source canvas', (tester) async {{
    // Render the production page. Replace the scene with the page widget that
    // composes it (overrides/onTap) and pass appBuilder: your real app root.
    const page = {class_name}Scene();
    final output = fidelityOutputPath('{output_env}');
    await captureFidelityPage(
      tester,
      page: page,
      size: {class_name}Scene.designSize,
      scale: {num(scale)},
      imageAssets: {class_name}Assets.all,
      output: output,
    );
    await captureResponsiveVariants(
      tester,
      page: page,
      height: {class_name}Scene.designSize.height,
      output: output,
    );
  }});
}}
""", encoding='utf-8')
    result['created'] = True
    return result


def generate(evidence: list[Path], plan_path: Path | None, font_map_path: Path | None,
             class_name: str, output: Path, report_path: Path | None = None,
             app_root: Path | None = None, asset_dir: str | None = None,
             scene_test: Path | None = None, render_test: Path | None = None,
             output_env: str | None = None) -> dict:
    if not re.fullmatch(r'[A-Z][A-Za-z0-9]*', class_name):
        raise ValueError('class name must be UpperCamelCase')
    documents = [read_json(p) for p in evidence]
    first = documents[0]
    canvas = [first['canvas']['width'], first['canvas']['height']]
    _validate_evidence(evidence, {'canvas': canvas})
    nodes = _load_nodes(evidence)
    plan = read_json(plan_path) if plan_path else None
    if plan:
        for field in ('snapshot_id', 'resolved_version'):
            if plan.get(field) != first.get(field):
                raise ValueError(f'Plan {field} differs from evidence; re-run prepare')
    font_map = read_json(font_map_path) if font_map_path else {}
    implementation = output.name
    if app_root is not None:
        try:
            implementation = str(output.resolve().relative_to(app_root.resolve()))
        except ValueError:
            implementation = str(output)
    generator = Generator(nodes, documents, plan, font_map, class_name, app_root,
                          asset_dir, implementation)
    dart, report = generator.generate()
    if scene_test is None and app_root is not None:
        stem = output.name[:-len('.g.dart')] if output.name.endswith('.g.dart') else output.stem
        scene_test = app_root / 'test' / f'{stem}_scene_test.g.dart'
    if scene_test is not None:
        from scene_test_codegen import write_scene_test
        report['scene_test'] = write_scene_test(generator, class_name, app_root, output, scene_test)
    if render_test is not None:
        report['render_test'] = write_render_test(render_test, app_root, output, class_name,
                                                  float((plan or {}).get('render_scale') or 4),
                                                  output_env or 'PAGE_RENDER_OUTPUT')
    if app_root is not None and asset_dir:
        for entry in report['assets']:
            target = (app_root / entry['flutter_asset']).resolve()
            if app_root.resolve() not in target.parents:
                raise ValueError('Asset target escapes app root')
            target.parent.mkdir(parents=True, exist_ok=True)
            source = Path(entry['source'])
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if entry.get('sha256') and digest != entry['sha256']:
                raise ValueError(f'Asset hash changed since prepare: {source}')
            if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                shutil.copyfile(source, target)
            entry['installed'] = str(target)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(dart, encoding='utf-8')
    report['output'] = str(output)
    report['output_sha256'] = hashlib.sha256(dart.encode('utf-8')).hexdigest()
    report_path = report_path or output.with_suffix('').with_suffix('.codegen.json')
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    report['report'] = str(report_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--evidence', type=Path, action='append', required=True)
    parser.add_argument('--plan', type=Path, help='page-plan.json from prepare (assets, fonts)')
    parser.add_argument('--font-map', type=Path)
    parser.add_argument('--class-name', required=True, help='UpperCamelCase page name, e.g. Withdraw2')
    parser.add_argument('--output', type=Path, required=True, help='Dart file, e.g. lib/pages/withdraw_2.g.dart')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--app-root', type=Path, help='Flutter app root; enables asset install')
    parser.add_argument('--asset-dir', help='Asset directory relative to app root, e.g. assets/lanhu/withdraw_2')
    parser.add_argument('--scene-test', type=Path, help='Scene obligation test (default app/test/<page>_scene_test.g.dart)')
    parser.add_argument('--render-test', type=Path, help='Create this render test if missing (project-owned)')
    parser.add_argument('--output-env', help='Environment variable the render test writes the PNG to')
    args = parser.parse_args()
    report = generate(args.evidence, args.plan, args.font_map, args.class_name, args.output,
                      args.report, args.app_root, args.asset_dir, args.scene_test,
                      args.render_test, args.output_env)
    summary = {k: report[k] for k in ('status', 'mode_counts', 'output', 'report')}
    summary['unsupported'] = len(report['unsupported'])
    summary['issues'] = len(report['issues'])
    summary['system_chrome'] = [c['kind'] for c in report['system_chrome']]
    if report.get('scene_test'):
        obligations = report['scene_test']['obligations']
        summary['scene_obligations'] = {'bound': sum(o['status'] == 'bound' for o in obligations),
                                        'unsupported': [o['id'] for o in obligations if o['status'] != 'bound']}
    if report['assets'] and not args.asset_dir:
        summary['next_action'] = 'pass --app-root/--asset-dir to install assets and declare them in pubspec.yaml'
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
