"""Target-neutral scene model built from canonical design evidence.

Every decision that does not depend on the output platform lives here: node
classification (asset / text / shape / placeholder / container / chrome),
paint parsing, text runs and tokens, masks, effects, responsive anchoring,
safe-area footers, the per-node report and draft node decisions.

Emitters (`emit_flutter.py`, `emit_react.py`, `emit_compose.py`,
`emit_swiftui.py`) turn the resulting tree of `N` nodes into source code and
must not re-derive any of these decisions.

The input is the canonical evidence format documented in
`references/evidence-schema.md` (Lanhu MCP output; Figma via
`integrations/figma`).
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from fidelity_contract import inventory
from system_chrome import detect_system_chrome

MODEL_VERSION = 1
# Designers place odd-width items on whole pixels: 172 + 32 + 171 is centred.
CENTER_TOLERANCE = 1.0
# A root layer whose bottom sits within this distance above the design's home
# indicator (or the canvas bottom), in the lower part of the canvas, is a
# footer: it stays pinned above the bottom safe area on every screen height.
FOOTER_SLACK = 48.0
FOOTER_MIN_TOP_RATIO = 0.6

# Sketch/AppKit NSTextAlignment (Lanhu's derived `align` string mislabels 2);
# adapters for other sources emit the same codes.
TEXT_ALIGN = {0: 'left', 1: 'right', 2: 'center', 3: 'justify', 4: 'left'}
BORDER_POSITION = {'内边框': 'inside', 'inside': 'inside', '中心边框': 'center',
                   'center': 'center', '外边框': 'outside', 'outside': 'outside'}
STROKE_CAP = {0: 'butt', 1: 'round', 2: 'square'}
STROKE_JOIN = {0: 'miter', 1: 'round', 2: 'bevel'}


class N:
    """A model node: `kind` plus ordered fields. Emitters dispatch on kind."""

    __slots__ = ('kind', 'fields', 'footer')

    def __init__(self, kind: str, **fields: Any):
        self.kind = kind
        self.fields = fields
        self.footer = False

    def __getitem__(self, key: str) -> Any:
        return self.fields[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.fields.get(key, default)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f'N({self.kind}, {self.fields})'


class Expr:
    """`<var> + value`, evaluated by the target at run time (`dy`, `dyBottom`)."""

    __slots__ = ('var', 'value')

    def __init__(self, var: str, value: float):
        self.var, self.value = var, value


def num(value: float) -> str:
    """Compact, stable decimal literal (no binary noise, no lost precision)."""
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Non-finite source number')
    text = f'{value:.4f}'.rstrip('0').rstrip('.')
    return '0' if text in ('-0', '') else text


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


def font_lookup(plan: dict, font_map: dict, platforms=('ios', 'android', 'web')) -> dict[str, dict]:
    """label -> {'family': fidelity family, <platform>: production family}.

    A platform value of null means the platform's system font; an absent key
    means the fidelity family is also used in production.
    """
    lookup: dict[str, dict] = {}
    for entry in plan.get('fonts', []):
        if entry.get('runtime_family'):
            lookup[f"{entry.get('source_family')}@{entry.get('weight')}"] = {
                'family': entry['runtime_family']}
    for label, entry in (font_map.get('fonts') or {}).items():
        if not entry.get('runtime_family'):
            continue
        item = {'family': entry['runtime_family']}
        for platform in platforms:
            if platform in entry:
                value = entry[platform]
                if value is not None and not isinstance(value, str):
                    raise ValueError(f'font map {label}.{platform} must be a family name or null')
                item[platform] = value
        lookup[label] = item
    return lookup


class SceneModel:
    """Builds the neutral tree. `class_name` is used for symbols in decisions."""

    def __init__(self, nodes: dict, documents: list[dict], plan: dict | None,
                 font_map: dict, class_name: str, asset_dir: str | None,
                 implementation_path: str, font_platforms=('ios', 'android')):
        self.nodes, self.documents, self.plan = nodes, documents, plan or {}
        self.class_name, self.asset_dir = class_name, asset_dir
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
        self.text_styles: dict[str, tuple[str, dict]] = {}
        self.assets: dict[str, dict] = {}
        self.asset_constants: dict[str, str] = {}
        self.asset_keys: dict[str, dict] = {}
        self.records: dict[str, dict] = {}
        self.unsupported: list[dict] = []
        self.chrome: list[dict] = []
        self.issues: list[dict] = []
        self.methods: list[tuple[str, str, Any]] = []
        self.short_ids = self._short_ids()
        self.chrome_owners = {e['node_id']: e for e in detect_system_chrome(nodes, self.canvas)}
        self.design_top, self.design_bottom = 0.0, 0.0
        for entry in self.chrome_owners.values():
            x, y, w, h = entry['rect']
            if entry['kind'] == 'statusBar':
                self.design_top = max(self.design_top, y + h)
            else:
                self.design_bottom = max(self.design_bottom, self.canvas[1] - y)
        self.footer: list[str] = []
        self._fonts = font_lookup(self.plan, font_map, font_platforms)
        self.font_platforms = font_platforms
        self._index_assets()
        self.children_of_root: list[Any] = []

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

    def _index_assets(self) -> None:
        for item in self.plan.get('assets', []):
            if item.get('kind') == 'render_fallback' or not item.get('path') or not item.get('export_rect'):
                continue
            self.assets[item['node_id']] = item

    # ---- tokens -----------------------------------------------------------
    def color(self, color: tuple[int, int, int, float]) -> N:
        code = argb_hex(color)
        name = f'c{code}'
        self.colors[name] = code
        return N('color', name=name, hex=code, rgba=color)

    def text_style(self, run: dict, node_id: str) -> N:
        family_src = run.get('font_family')
        weight = font_weight(run.get('font_weight'))
        label = f'{family_src}@{run.get("font_weight")}'
        mapping = self._fonts.get(label)
        if mapping is None:
            mapping = {'family': family_src or 'sans-serif'}
            self.issues.append({'kind': 'font_mapping_missing', 'node_id': node_id, 'font': label})
        family = mapping['family']
        size = float(run.get('font_size') or 14)
        line = run.get('line_height')
        line = float(line) if isinstance(line, (int, float)) and line > 0 else None
        if line is None:
            self.unsupported.append({'node_id': node_id, 'feature': 'natural_line_height',
                                     'detail': 'Sketch auto line height differs from Flutter metrics; verify visually'})
        spacing = float(run.get('letter_spacing') or 0)
        color = parse_color(run.get('color')) or (0, 0, 0, 1.0)
        decoration = {'underline': 'underline', 'line-through': 'lineThrough',
                      'strikethrough': 'lineThrough'}.get(str(run.get('decoration_line') or 'none').lower())
        name = (f't{num(size)}w{weight}h{num(line) if line else "n"}'
                f'c{argb_hex(color)}').replace('.', '_').replace('-', 'm')
        if spacing:
            name += f'k{num(spacing)}'.replace('.', '_').replace('-', 'm')
        if decoration:
            name += 'u' if decoration == 'underline' else 's'
        signature_family = re.sub(r'[^0-9A-Za-z]', '', family)
        platforms = {k: mapping[k] for k in self.font_platforms if k in mapping}
        key = f'{name}|{family}|{json.dumps(platforms, sort_keys=True)}'
        if key not in self.text_styles:
            existing = {n for n, _ in self.text_styles.values()}
            if name in existing:
                name = f'{name}{signature_family[:6]}'
            spec = {'family': family, 'platforms': platforms, 'size': size, 'weight': weight,
                    'line_height': line, 'letter_spacing': spacing, 'color': self.color(color),
                    'decoration': decoration}
            self.text_styles[key] = (name, spec)
        return N('tstyle', name=self.text_styles[key][0])

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

    def shape_of(self, key: str) -> tuple[N | None, str]:
        """(shape, kind). A plain rectangle without radii is N('rect', radii=None)."""
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
                return N('rect', radii=None), 'rect'
            if len(set(radii)) == 1:
                return N('rect', radii=('all', radii[0])), 'rect'
            return N('rect', radii=radii), 'rect'
        if (len(points) == 4 and all(p.get('hasCurveFrom') and p.get('hasCurveTo') for p in points)
                and sorted(corners) == sorted([(0.5, 0), (1, 0.5), (0.5, 1), (0, 0.5)])):
            return N('oval'), 'oval'
        if points:
            if any(float(p.get('cornerRadius') or 0) > 0 for p in points):
                self.unsupported.append({'node_id': key, 'feature': 'path_corner_radius',
                                         'detail': 'per-vertex corner radius on a free path is drawn sharp'})
            items = []
            for p in points:
                items.append({'point': pt(p.get('point', {})),
                              'curve_from': pt(p.get('curveFrom', {})) if p.get('hasCurveFrom') else None,
                              'curve_to': pt(p.get('curveTo', {})) if p.get('hasCurveTo') else None})
            closed = bool(raw.get('isClosed', True))
            return N('path', points=items, closed=closed, even_odd=raw.get('windingRule') == 1), 'path'
        if isinstance(radius, list) and radius:
            radii = [float(r) for r in (radius * 4 if len(radius) == 1 else radius)[:4]]
            return (N('rect', radii=('all', radii[0])) if len(set(radii)) == 1
                    else N('rect', radii=radii)), 'rect'
        return None, 'unknown'

    @staticmethod
    def explicit_shape(shape: N | None) -> N | None:
        """None for a plain rectangle (the primitives' default shape)."""
        if shape is None or (shape.kind == 'rect' and shape['radii'] is None):
            return None
        return shape

    def fill_of(self, fill: dict, key: str) -> N | None:
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
                stops.append((float(stop.get('position', 0)), self.color(color)))
            start, end = gradient.get('from', {}), gradient.get('to', {})
            return N('linear', start=(float(start.get('x', 0)), float(start.get('y', 0))),
                     end=(float(end.get('x', 1)), float(end.get('y', 0))), stops=stops,
                     opacity=opacity if opacity < 1 else None)
        if fill.get('type') not in (None, 'color') or fill.get('fillType') not in (None, 0):
            self.unsupported.append({'node_id': key, 'feature': 'pattern_or_image_fill',
                                     'detail': f"type={fill.get('type')} fillType={fill.get('fillType')}"})
            return None
        color = parse_color(fill.get('color'))
        if color is None:
            return None
        return N('solid', color=self.color(color), opacity=opacity if opacity < 1 else None)

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
            cap_code, join_code = options.get('lineCapStyle', 0), options.get('lineJoinStyle', 0)
            borders.append(N(
                'border', thickness=float(border['thickness']), fill=fill,
                position=BORDER_POSITION.get(border.get('position'), 'center'),
                cap=None if cap_code in (0, None) else STROKE_CAP.get(cap_code, 'butt'),
                join=None if join_code in (0, None) else STROKE_JOIN.get(join_code, 'miter'),
                dash=dash or None))
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
                shadows.append(N('shadow', color=self.color(color),
                                 offset=(dx, dy) if dx or dy else None,
                                 blur=float(shadow.get('blurRadius') or 0) or None,
                                 spread=spread or None, inner=inner))
        opacity = raw.get('opacity')
        opacity = float(opacity) / 100 if isinstance(opacity, (int, float)) else 1.0
        return {'fills': fills, 'borders': borders, 'shadows': shadows,
                'opacity': max(0.0, min(1.0, opacity))}

    # ---- tree ---------------------------------------------------------------
    def frame(self, key: str) -> tuple[float, float, float, float]:
        b = self.nodes[key]['bounds']
        return (float(b['x']), float(b['y']), float(b['width']), float(b['height']))

    def leaf(self, key: str) -> tuple[N | None, dict]:
        node = self.nodes[key]
        raw = node.get('raw_style') or {}
        hints: dict[str, Any] = {}
        if key in self.assets:
            asset = self.assets[key]
            x, y, _, _ = self.frame(key)
            ex, ey, ew, eh = asset['export_rect']
            ident = self.asset_constant(key, asset)
            export = (ex - x, ey - y, ew, eh)
            if [ex, ey, ew, eh] == list(self.frame(key)):
                export = None
            for child in self.descendants(key):
                self.record(child, 'covered_by_asset', owner=key)
            self.record(key, 'original_asset', asset=asset.get('path'),
                        export_rect=asset['export_rect'])
            return N('asset', ident=ident, export_rect=export, size=self.frame(key)[2:]), hints
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
        box = N('box', shape=self.explicit_shape(shape), fills=paint['fills'],
                borders=paint['borders'], shadows=paint['shadows'],
                opacity=paint['opacity'] if paint['opacity'] < 1 else None)
        widget = self.effects(key, box, shape)
        self.record(key, 'native_exact', primitive='box', shape=kind)
        return widget, hints

    def placeholder(self, key: str) -> N:
        """Missing content only: borders, shadows, opacity and blur stay."""
        paint = self.paint_of(key)
        widget: N = N('placeholder', node_id=key)
        if paint['borders'] or paint['shadows']:
            box = N('box', shape=None, fills=[], borders=paint['borders'],
                    shadows=paint['shadows'], opacity=None)
            widget = N('overlay', children=[N('fill', child=box), N('fill', child=widget)])
        if paint['opacity'] < 1:
            widget = N('opacity', value=paint['opacity'], child=widget)
        return self.effects(key, widget, None)

    def effects(self, key: str, widget: N, shape: N | None) -> N:
        raw = self.nodes[key].get('raw_style') or {}
        blur = raw.get('blur')
        if isinstance(blur, dict) and blur.get('isEnabled', True) and float(blur.get('radius') or 0) > 0:
            if blur.get('blurType') == 3:
                saturation = blur.get('saturation', 1)
                widget = N('backdrop', radius=float(blur['radius']),
                           shape=self.explicit_shape(shape),
                           saturation=float(saturation) if isinstance(saturation, (int, float)) and saturation != 1 else None,
                           child=widget)
            elif blur.get('blurType') in (0, None):
                widget = N('layer_blur', radius=float(blur['radius']), child=widget)
            else:
                self.unsupported.append({'node_id': key, 'feature': 'motion_or_zoom_blur',
                                         'detail': f"blurType={blur.get('blurType')}"})
        if raw.get('rotation'):
            self.unsupported.append({'node_id': key, 'feature': 'rotation',
                                     'detail': f"rotation={raw.get('rotation')}; not applied"})
        if raw.get('isFlippedHorizontal') or raw.get('isFlippedVertical'):
            widget = N('flip', x=bool(raw.get('isFlippedHorizontal')),
                       y=bool(raw.get('isFlippedVertical')), child=widget)
        return widget

    def text(self, key: str) -> N:
        node = self.nodes[key]
        raw = node.get('raw_style') or {}
        font = raw.get('font') or {}
        spec = node.get('text_spec') or {}
        inherited = spec.get('base_style') if isinstance(spec.get('base_style'), dict) else {}
        runs = [{**inherited, **{k: v for k, v in r.items() if v is not None}}
                for r in spec.get('text_runs', []) if isinstance(r.get('text'), str)]
        base = runs[0] if runs else inherited
        if not runs or ''.join(r['text'] for r in runs) != node['text']:
            self.issues.append({'kind': 'text_run_coverage', 'node_id': key})
            runs = [dict(base, text=node['text'])]
        code = font.get('textAlignment')
        if code is None and font.get('styles'):
            code = font['styles'][0].get('alignment')
        align = TEXT_ALIGN.get(code if isinstance(code, int) else 0, 'left')
        wrap = raw.get('textBehaviour', 0) not in (0, None)
        style = self.text_style(base, key)
        if len(runs) == 1:
            widget = N('text', text=node['text'], style=style, align=align, wrap=wrap)
        else:
            widget = N('rich', runs=[(r['text'], self.text_style(r, key)) for r in runs],
                       style=style, align=align, wrap=wrap)
        opacity = raw.get('opacity')
        if isinstance(opacity, (int, float)) and opacity < 100:
            widget = N('opacity', value=float(opacity) / 100, child=widget)
        self.record(key, 'native_exact', primitive='text', align=align, wrap=wrap)
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
        app_asset = f'{self.asset_dir.rstrip("/")}/{source.name}' if self.asset_dir else source.name
        self.asset_keys[ident] = {'app_asset': app_asset, 'source': str(source),
                                  'sha256': asset.get('sha256'), 'node_id': key}
        return ident

    def placement(self, key: str, parent_rect: tuple, stretch: bool, widget: N,
                  hints: dict, at_root: bool) -> N:
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
            return N('fill', child=widget)
        vertical = self.vertical(key, top, bottom, h, bool(is_text), at_root)
        if stretch:
            if abs(left - right) <= CENTER_TOLERANCE and left <= 32 and w >= pw / 2:
                if is_text:
                    self._anchor(key, 'stretch')
                return N('placed', args=[('left', left), ('right', right), *vertical], child=widget)
            if abs(left - right) <= CENTER_TOLERANCE:
                if left_aligned_text:
                    self._anchor(key, 'center')
                inner = widget if left_aligned_text else N('sized', width=w, child=widget)
                return N('placed', args=[('left', 0), ('right', 0), *vertical],
                         child=N('align_top_center', child=inner))
            if right < left:
                # Auto-width text keeps its intrinsic width and grows leftwards.
                width = None if left_aligned_text else w
                if left_aligned_text:
                    self._anchor(key, 'right')
                return N('placed', args=[('right', right), *vertical, ('width', width)], child=widget)
        if left_aligned_text:
            return N('placed', args=[('left', left), *vertical], child=widget)
        return N('placed', args=[('left', left), *vertical, ('width', w)], child=widget)

    def is_footer(self, key: str) -> bool:
        x, y, w, h = self.frame(key)
        height = self.canvas[1]
        if h >= height - 1:
            return False
        return (y >= height * FOOTER_MIN_TOP_RATIO
                and height - (y + h) <= self.design_bottom + FOOTER_SLACK)

    def vertical(self, key: str, top: float, bottom: float, h: float, is_text: bool,
                 at_root: bool) -> list[tuple[str, Any]]:
        """Vertical placement. Root layers follow the device safe area at run
        time: footers keep their distance to the bottom inset, everything else
        to the top inset."""
        if not at_root:
            result: list[tuple[str, Any]] = [('top', top)]
        elif self.is_footer(key):
            if key not in self.footer:
                self.footer.append(key)
            if key in self.records:
                self.records[key]['vertical_anchor'] = 'bottom'
            result = [('bottom', Expr('dyBottom', bottom))]
        else:
            result = [('top', Expr('dy', top))]
        if not is_text:
            result.append(('height', h))
        return result

    def _anchor(self, key: str, edge: str) -> None:
        """Record which edge a text box is laid out from, so the geometry probe
        compares that edge instead of turning advance-width noise into offsets."""
        if key in self.records:
            self.records[key]['anchor'] = edge

    def container(self, key: str | None, rect: tuple, stretch: bool, at_root: bool = False) -> list[N]:
        """Children of a group as placed nodes in paint order."""
        result: list[N] = []
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
                    result.append(self._tag(placed, child, at_root))
                result.extend(self._tag(p, child, at_root)
                              for p in self.masked_group(child, masked, rect, at_root))
                continue
            placed = self.place(child, rect, stretch, at_root)
            if placed is not None:
                result.append(self._tag(placed, child, at_root))
            index += 1
        return result

    def _tag(self, placed: N, key: str, at_root: bool) -> N:
        placed.footer = at_root and key in self.footer
        return placed

    def masked_group(self, mask: str, members: list[str], parent_rect: tuple,
                     at_root: bool = False) -> list[N]:
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
            clipped = N('stack', children=inner)
        else:
            clipped = N('clip', shape=shape, child=N('stack', children=inner))
        if mask in self.records:
            self.records[mask]['masks'] = members
        else:
            self.record(mask, 'native_exact', primitive='mask', shape=kind, masks=members)
        px, py, pw, ph = parent_rect
        vertical = self.vertical(mask, my - py, (py + ph) - (my + mh), mh, False, at_root)
        return [N('placed', args=[('left', mx - px), *vertical, ('width', mw)], child=clipped)]

    def place(self, key: str, parent_rect: tuple, stretch: bool, at_root: bool) -> N | None:
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
        widget = N('node', id=key, child=widget, size=self.frame(key)[2:])
        return self.placement(key, parent_rect, stretch, widget, hints, at_root)

    def group(self, key: str, parent_rect: tuple, stretch: bool, at_root: bool) -> N | None:
        rect = self.frame(key)
        px, py, pw, ph = parent_rect
        x, y, w, h = rect
        left, right = x - px, (px + pw) - (x + w)
        child_stretch = stretch and abs(left - right) <= CENTER_TOLERANCE and left <= 32 and w >= pw / 2
        children = self.container(key, rect, child_stretch)
        paint = self.paint_of(key)
        if paint['shadows'] or paint['borders']:
            self.unsupported.append({'node_id': key, 'feature': 'group_shadow_or_border',
                                     'detail': 'group-level shadows/borders are not applied'})
        if paint['fills'] and self.nodes[key].get('node_type') != 'artboard-group':
            children.insert(0, N('fill', child=N('box', shape=None, fills=paint['fills'], borders=[],
                                                  shadows=[], opacity=None)))
        if not children:
            self.record(key, 'empty_group')
            return None
        method = f'_g{self.short_ids[key]}'
        body: N = N('stack', children=children)
        if paint['opacity'] < 1:
            body = N('opacity', value=paint['opacity'], child=body)
        body = self.effects(key, body, None)
        name = str(self.nodes[key].get('name') or '')
        self.methods.append((method, name, body))
        self.record(key, 'container', symbol=f'{self.class_name}Scene.{method}')
        call = N('node', id=key, child=N('group_ref', method=method), size=(w, h))
        if child_stretch:
            vertical = self.vertical(key, y - py, (py + ph) - (y + h), h, False, at_root)
            return N('placed', args=[('left', left), ('right', right), *vertical], child=call)
        return self.placement(key, parent_rect, stretch, call, {}, at_root)

    def build(self) -> list[N]:
        """Root children (background first); footers carry `.footer = True`."""
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
                    background = N('fill', child=N('box', shape=None, fills=fills, borders=[],
                                                    shadows=[], opacity=None))
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
        self.children_of_root = children
        return children

    # ---- report -------------------------------------------------------------
    def report(self, generator: str, generator_version: int, asset_field: str = 'app_asset') -> dict:
        first = self.documents[0]
        decisions = {}
        mode_map = {'native_exact': 'native_exact', 'original_asset': 'original_asset',
                    'missing_asset_placeholder': 'missing_asset_placeholder',
                    'container': 'native_exact', 'no_visible_paint': 'native_exact',
                    'covered_by_asset': 'original_asset'}
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
                decision['asset'] = (self.asset_keys.get(ident) or {}).get('app_asset')
                if owner != key:
                    decision['covered_by'] = owner
            if mode == 'missing_asset_placeholder':
                decision['shape'] = 'rect'
            if entry.get('anchor'):
                decision['anchor'] = entry['anchor']
            if entry.get('vertical_anchor'):
                decision['vertical_anchor'] = entry['vertical_anchor']
            decisions[key] = decision
        counts: dict[str, int] = {}
        for entry in self.records.values():
            counts[entry['mode']] = counts.get(entry['mode'], 0) + 1
        assets = []
        for ident, entry in sorted(self.asset_keys.items()):
            item = dict(entry)
            item[asset_field] = item.pop('app_asset')
            assets.append(dict(identifier=ident, **{k: item[k] for k in
                                                    (asset_field, 'source', 'sha256', 'node_id')}))
        return {
            'generator': generator, 'generator_version': generator_version,
            'status': 'GENERATED_FOR_REVIEW',
            'scope': 'deterministic first implementation; not visual acceptance',
            'snapshot_id': first.get('snapshot_id'), 'resolved_version': first.get('resolved_version'),
            'canvas': list(self.canvas), 'class_name': self.class_name,
            'mode_counts': dict(sorted(counts.items())),
            'nodes': list(self.records.values()),
            'system_chrome': self.chrome,
            'layout': {'design_padding': {'top': self.design_top, 'bottom': self.design_bottom},
                       'footer': list(self.footer),
                       'note': 'Root layers follow the device safe area; footers stay pinned above '
                               'the bottom inset; shorter screens scroll the body.'},
            'unsupported': self.unsupported,
            'issues': self.issues,
            'assets': assets,
            'draft_node_decisions': decisions,
        }
