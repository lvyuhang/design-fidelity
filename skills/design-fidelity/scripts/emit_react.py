"""React emitter: scene model -> TSX built on `@design-fidelity/react`."""
from __future__ import annotations

import copy
import json
import os
import shutil
from pathlib import Path
from typing import Any

from scene_model import Expr, N, SceneModel, argb_hex, num

GENERATOR_VERSION = 1
PACKAGE = '@design-fidelity/react'
HARNESS = Path(__file__).resolve().parents[1] / 'assets' / 'web' / 'fidelity_render_harness.cjs'
LINE_WIDTH = 100
TEXT_KINDS = {'text', 'rich'}
WRAPPERS = {'opacity', 'flip', 'layer_blur'}


class Raw:
    """A JS expression emitted verbatim."""

    def __init__(self, code: str):
        self.code = code


class El:
    """A JSX element; tag None is a fragment."""

    def __init__(self, tag: str | None, props: dict[str, Any] | None = None, children: list | None = None):
        self.tag = tag
        self.props = [(k, v) for k, v in (props or {}).items() if v is not None and v is not False]
        self.children = [c for c in (children or []) if c is not None]


def js(value: Any) -> str:
    if isinstance(value, Raw):
        return value.code
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        return num(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        return '[' + ', '.join(js(v) for v in value) + ']'
    if isinstance(value, dict):
        items = []
        for k, v in value.items():
            if v is None:
                continue
            key = k if k.isidentifier() else json.dumps(k)
            items.append(f'{key}: {js(v)}')
        return '{ ' + ', '.join(items) + ' }' if items else '{}'
    if value is None:
        return 'undefined'
    raise TypeError(f'Cannot emit {type(value)!r}')


def jsx(node: Any, indent: int = 0) -> str:
    pad = ' ' * indent
    if isinstance(node, Raw):
        return pad + '{' + node.code + '}'
    if isinstance(node, str):
        return pad + '{' + json.dumps(node, ensure_ascii=False) + '}'
    if node.tag is None:
        open_tag, close_tag = '<>', '</>'
        props = ''
    else:
        parts = []
        for k, v in node.props:
            if v is True:
                parts.append(k)
            elif isinstance(v, str) and '"' not in v and '\\' not in v and '{' not in v and '\n' not in v:
                parts.append(f'{k}="{v}"')
            else:
                parts.append(f'{k}={{{js(v)}}}')
        props = (' ' + ' '.join(parts)) if parts else ''
        if len(pad + props) + len(node.tag) + 4 > LINE_WIDTH and len(parts) > 1:
            props = ''.join(f'\n{pad}  {p}' for p in parts) + f'\n{pad}'
        open_tag, close_tag = f'<{node.tag}{props}>', f'</{node.tag}>'
    if not node.children:
        if node.tag is None:
            return pad + '<></>'
        return pad + (open_tag[:-1] + ' />' if not open_tag.endswith('\n' + pad + '>') else open_tag[:-1] + '/>')
    body = '\n'.join(jsx(c, indent + 2) for c in node.children)
    return f'{pad}{open_tag}\n{body}\n{pad}{close_tag}'


class ReactEmitter:
    def __init__(self, model: SceneModel):
        self.m = model
        self.cls = model.class_name
        self.size: tuple[float, float] | None = None
        self.approximations: list[dict] = []
        self.current: str | None = None

    # values
    def color(self, c: N) -> Raw:
        return Raw(f'{self.cls}Tokens.{c["name"]}')

    def shape(self, s: N | None) -> dict | None:
        if s is None:
            return None
        if s.kind == 'rect':
            radii = s['radii']
            if radii is None:
                return {'kind': 'rect'}
            if isinstance(radii, tuple) and radii[0] == 'all':
                return {'kind': 'rect', 'radii': radii[1]}
            return {'kind': 'rect', 'radii': list(radii)}
        if s.kind == 'oval':
            return {'kind': 'oval'}
        points = []
        for p in s['points']:
            item = {'point': list(p['point'])}
            if p['curve_from'] is not None:
                item['curveFrom'] = list(p['curve_from'])
            if p['curve_to'] is not None:
                item['curveTo'] = list(p['curve_to'])
            points.append(item)
        return {'kind': 'path', 'points': points, 'closed': None if s['closed'] else False,
                'evenOdd': True if s['even_odd'] else None}

    def fill(self, f: N) -> dict:
        if f.kind == 'linear':
            return {'linear': {'from': list(f['start']), 'to': list(f['end']),
                               'stops': [[pos, self.color(c)] for pos, c in f['stops']]},
                    'opacity': f['opacity']}
        return {'color': self.color(f['color']), 'opacity': f['opacity']}

    def border(self, b: N) -> dict:
        return {'thickness': b['thickness'], 'fill': self.fill(b['fill']),
                'position': None if b['position'] == 'center' else b['position'],
                'cap': b['cap'], 'join': b['join'], 'dash': b['dash']}

    def shadow(self, s: N) -> dict:
        return {'color': self.color(s['color']), 'offset': list(s['offset']) if s['offset'] else None,
                'blur': s['blur'], 'spread': s['spread'], 'inner': True if s['inner'] else None}

    def value(self, v: Any) -> Any:
        if isinstance(v, Expr):
            return Raw(f"{'dy' if v.var == 'dy' else 'dyBottom'}({num(v.value)})")
        return v

    def note(self, feature: str, detail: str) -> None:
        self.approximations.append({'node_id': self.current, 'feature': feature, 'detail': detail})

    @staticmethod
    def is_text(n: N) -> bool:
        while n.kind in WRAPPERS:
            n = n['child']
        return n.kind in TEXT_KINDS

    # elements
    def element(self, n: N, fill: bool = True) -> Any:
        k = n.kind
        if k == 'box':
            shape = self.shape(n['shape'])
            if shape and shape['kind'] == 'path':
                if any(not s['inner'] for s in n['shadows']):
                    self.note('path_shadow_approximation', 'drop-shadow: no spread, not knocked out')
                if any(s['inner'] for s in n['shadows']):
                    self.note('path_inner_shadow', 'inner shadows on free paths are not drawn on the web')
            if any(b['dash'] and b['fill'].kind == 'linear' for b in n['borders']):
                self.note('dashed_gradient_border', 'drawn with the first gradient stop')
            diagonal = any(f.kind == 'linear' and f['start'][0] != f['end'][0] and f['start'][1] != f['end'][1]
                           for f in n['fills'])
            return El('SourceBox', {
                'shape': shape,
                'fills': [self.fill(f) for f in n['fills']] or None,
                'borders': [self.border(b) for b in n['borders']] or None,
                'shadows': [self.shadow(s) for s in n['shadows']] or None,
                'opacity': n['opacity'],
                'size': list(self.size) if diagonal and self.size else None})
        if k == 'text':
            return El('SourceText', {'text': n['text'], 'style': Raw(f'{self.cls}Tokens.{n["style"]["name"]}'),
                                     'align': None if n['align'] == 'left' else n['align'],
                                     'wrap': True if n['wrap'] else None})
        if k == 'rich':
            runs = Raw('[' + ', '.join(f'[{json.dumps(t, ensure_ascii=False)}, {self.cls}Tokens.{s["name"]}]'
                                       for t, s in n['runs']) + ']')
            return El('SourceText', {'runs': runs, 'style': Raw(f'{self.cls}Tokens.{n["style"]["name"]}'),
                                     'align': None if n['align'] == 'left' else n['align'],
                                     'wrap': True if n['wrap'] else None})
        if k == 'asset':
            return El('SourceAsset', {'src': Raw(f'{self.cls}Assets.{n["ident"]}'),
                                      'exportRect': list(n['export_rect']) if n['export_rect'] else None})
        if k == 'placeholder':
            return El('SourcePlaceholder', {'nodeId': n['node_id']})
        if k == 'overlay':
            return El('Fill', {}, [self.element(c, True) for c in n['children']])
        if k == 'stack':
            return El(None, {}, [self.element(c, True) for c in n['children']])
        if k == 'fill':
            return El('Fill', {}, [self.element(n['child'], True)])
        if k == 'placed':
            props = {name: self.value(v) for name, v in n['args']}
            return El('Placed', props, [self.element(n['child'], True)])
        if k == 'align_top_center':
            return El('AlignTopCenter', {}, [self.element(n['child'], True)])
        if k == 'sized':
            return El('Sized', {'width': n['width']}, [self.element(n['child'], True)])
        if k == 'opacity':
            return El('SourceOpacity', {'value': n['value'], 'fill': fill}, [self.element(n['child'], fill)])
        if k == 'backdrop':
            return El('SourceBackdropBlur', {'radius': n['radius'], 'shape': self.shape(n['shape']),
                                             'saturation': n['saturation']}, [self.element(n['child'], True)])
        if k == 'layer_blur':
            return El('SourceLayerBlur', {'radius': n['radius'], 'fill': fill}, [self.element(n['child'], fill)])
        if k == 'flip':
            return El('SourceFlip', {'x': n['x'] or None, 'y': n['y'] or None, 'fill': fill},
                      [self.element(n['child'], fill)])
        if k == 'clip':
            return El('SourceClip', {'shape': self.shape(n['shape'])}, [self.element(n['child'], True)])
        if k == 'node':
            child = n['child']
            previous, self.current, self.size = (self.current, self.size), n['id'], tuple(n['size'])
            try:
                if child.kind == 'group_ref':
                    return El('SourceNode', {'id': n['id'], 'fill': True}, [Raw(f'{child["method"]}()')])
                fill_node = not self.is_text(child)
                return El('SourceNode', {'id': n['id'], 'fill': fill_node}, [self.element(child, fill_node)])
            finally:
                self.current, self.size = previous
        raise TypeError(f'Unknown model node {k}')

    def text_spec(self, spec: dict) -> str:
        platforms = {k: v for k, v in spec['platforms'].items()}
        value = {'family': spec['family'], 'platforms': platforms or None, 'size': spec['size'],
                 'weight': spec['weight'], 'lineHeight': spec['line_height'],
                 'letterSpacing': spec['letter_spacing'] or None,
                 'color': Raw(f'{self.cls}Tokens.{spec["color"]["name"]}'),
                 'decoration': spec['decoration']}
        if platforms:
            value['platforms'] = Raw('{ ' + ', '.join(f'{k}: {js(v) if v is not None else "null"}'
                                                     for k, v in sorted(platforms.items())) + ' }')
        return js(value)

    def tsx(self, children: list[N], asset_imports: dict[str, str]) -> str:
        m = self.m
        width, height = m.canvas
        first = m.documents[0]
        cls = self.cls
        body = [self.element(c) for c in children if not c.footer]
        footer = [self.element(c) for c in children if c.footer]
        groups = [(method, name, self.element(node)) for method, name, node in m.methods]
        names = sorted({'SourceScene', 'SourceNode', 'Placed', 'Fill', 'dy', 'dyBottom', 'assetUrl',
                        *self._used(body + footer + [g for _, _, g in groups])})
        lines = [
            '// GENERATED by design-fidelity/scripts/generate.py --target react; do not edit.',
            f'// Source: {first.get("design_name") or ""} snapshot {first.get("snapshot_id")}',
            f'// version {first.get("resolved_version")}, canvas {num(width)}x{num(height)}.',
            '// Replace layers through `overrides` / wire actions through `onTap`.',
            '/* eslint-disable */',
            "import type { SceneOverrides, TextSpec } from '" + PACKAGE + "';",
            'import {',
            *(f'  {n},' for n in names),
            f"}} from '{PACKAGE}';",
        ]
        for var, path in sorted(asset_imports.items()):
            lines.append(f"import {var} from {json.dumps(path)};")
        lines += ['', f'export const {cls}Tokens = {{']
        for name, code in sorted(m.colors.items()):
            lines.append(f"  {name}: '#{code[2:]}{code[:2]}',")
        for name, spec in sorted(m.text_styles.values(), key=lambda item: item[0]):
            lines.append(f'  get {name}(): TextSpec {{ return {self.text_spec(spec)}; }},')
        lines += ['} as const;', '', f'export const {cls}Assets = {{']
        for ident, entry in sorted(m.asset_keys.items()):
            lines.append(f'  {ident}: assetUrl({self.asset_var(ident)}),')
        lines.append('  get all(): string[] { return [' + ', '.join(f'this.{i}' for i in sorted(m.asset_keys)) + ']; },')
        lines += ['};', '',
                  f'export interface {cls}SceneProps extends SceneOverrides {{',
                  '  /** Follow the device safe area (default). The scene is a full-screen page:',
                  '   *  give it a full-height parent and no extra safe-area padding. */',
                  '  adaptSafeArea?: boolean;',
                  '}', '',
                  f'export function {cls}Scene({{ overrides, onTap, adaptSafeArea = true }}: {cls}SceneProps) {{',
                  '  return (']
        scene = El('SourceScene', {'designSize': Raw(f'{cls}Scene.designSize'),
                                   'designPadding': Raw(f'{cls}Scene.designPadding'),
                                   'adaptSafeArea': Raw('adaptSafeArea'), 'overrides': Raw('overrides'),
                                   'onTap': Raw('onTap'),
                                   'footer': Raw('\n' + jsx(El(None, {}, footer), 6) + '\n    ') if footer else None},
                   body)
        lines += [jsx(scene, 4), '  );', '}', '',
                  f'{cls}Scene.designSize = [{num(width)}, {num(height)}] as const;',
                  '/** Safe-area insets drawn in the design (status bar / home indicator). */',
                  f'{cls}Scene.designPadding = {{ top: {num(m.design_top)}, bottom: {num(m.design_bottom)} }} as const;']
        for method, name, element in groups:
            label = name.replace('*/', '* /').strip()
            lines += ['', *([f'/** {label} */'] if label else []), f'function {method}() {{',
                      '  return (', jsx(element, 4), '  );', '}']
        lines.append('')
        return '\n'.join(lines)

    def asset_var(self, ident: str) -> str:
        return f'{ident}Asset'

    def _used(self, elements: list) -> set[str]:
        found: set[str] = set()

        def walk(e: Any) -> None:
            if isinstance(e, El):
                if e.tag and e.tag[0].isupper():
                    found.add(e.tag)
                for _, v in e.props:
                    if isinstance(v, El):
                        walk(v)
                for c in e.children:
                    walk(c)
        for e in elements:
            walk(e)
        return found

    def report(self) -> dict:
        report = self.m.report('generate.py --target react', GENERATOR_VERSION, asset_field='app_asset')
        nodes = copy.deepcopy(report['nodes'])
        names = {'box': 'SourceBox', 'text': 'SourceText'}
        for entry in nodes:
            if 'primitive' in entry:
                entry['primitive'] = names.get(entry['primitive'], entry['primitive'])
        report['nodes'] = nodes
        report['unsupported'] = report['unsupported'] + self.approximations
        return report


def relative_import(output: Path, target: Path) -> str:
    rel = os.path.relpath(target.resolve(), output.resolve().parent).replace(os.sep, '/')
    return rel if rel.startswith('.') else './' + rel


def write_render_test(path: Path, app_root: Path | None, output: Path, class_name: str,
                      scale: float, font_map: Path | None) -> dict:
    """Create the page render entry once (project code); keep the harness in sync."""
    result = {'path': str(path), 'created': False}
    harness = path.parent / 'support' / HARNESS.name
    if not harness.exists() or harness.read_bytes() != HARNESS.read_bytes():
        harness.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HARNESS, harness)
        result['harness_installed'] = str(harness)
    if path.exists():
        return result
    module = relative_import(path, output)
    module = module[:-4] if module.endswith('.tsx') else module
    fonts = 'null'
    if font_map is not None:
        try:
            fonts = json.dumps(font_map.resolve().relative_to(app_root.resolve()).as_posix()) if app_root else json.dumps(str(font_map))
        except ValueError:
            fonts = json.dumps(str(font_map.resolve()))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"""// Fidelity render entry (project code). Render the production page: replace
// the scene with the page component that composes it (overrides / onTap).
import {{ {class_name}Assets, {class_name}Scene }} from '{module}';

export default function Page() {{
  return <{class_name}Scene />;
}}

export const fidelity = {{
  designSize: {class_name}Scene.designSize,
  designPadding: {class_name}Scene.designPadding,
  scale: {num(scale)},
  assets: {class_name}Assets.all,
  // Design fonts are loaded from disk for fidelity renders only, never bundled.
  fontMap: {fonts},
}};
""", encoding='utf-8')
    result['created'] = True
    return result


def emit(model: SceneModel, ctx: dict) -> dict:
    output: Path = ctx['output']
    app_root: Path | None = ctx.get('app_root')
    children = model.build()
    emitter = ReactEmitter(model)
    imports = {}
    for ident, entry in model.asset_keys.items():
        target = (app_root / entry['app_asset']) if app_root is not None else Path(entry['source'])
        imports[emitter.asset_var(ident)] = relative_import(output, target)
    code = emitter.tsx(children, imports)
    report = emitter.report()
    render_test = ctx.get('render_test')
    scene_spec = ctx.get('scene_test') or (render_test.parent / 'scene.g.json' if render_test else None)
    report['scene_test'] = None
    if scene_spec is not None:
        from scene_test_codegen import write_web_scene_spec
        report['scene_test'] = write_web_scene_spec(model, model.class_name,
                                                    relative_import(scene_spec, output), scene_spec)
    if render_test is not None:
        report['render_test'] = write_render_test(render_test, app_root, output, model.class_name,
                                                  float(model.plan.get('render_scale') or 4),
                                                  ctx.get('font_map'))
    return {'code': code, 'report': report, 'asset_field': 'app_asset'}


def default_report_path(output: Path) -> Path:
    name = output.name
    for suffix in ('.g.tsx', '.tsx'):
        if name.endswith(suffix):
            return output.with_name(name[:-len(suffix)] + '.codegen.json')
    return output.with_suffix('.codegen.json')


__all__ = ['emit', 'default_report_path', 'write_render_test', 'HARNESS', 'jsx', 'js', 'El', 'Raw']
_ = argb_hex
