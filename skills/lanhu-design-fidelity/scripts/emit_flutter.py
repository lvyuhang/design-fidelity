"""Flutter emitter: scene model -> Dart built on the `lanhu_fidelity` primitives."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

from scene_model import Expr, N, SceneModel, num

GENERATOR_VERSION = 1
PRIMITIVES_IMPORT = 'package:lanhu_fidelity/lanhu_fidelity.dart'
LINE_WIDTH = 80
HARNESS = Path(__file__).resolve().parents[1] / 'assets' / 'flutter_render_harness.dart'
CONST_CTORS = {
    'SourceBox', 'SourceFill.color', 'SourceFill.linear', 'SourceLinearGradient',
    'SourceGradientStop', 'SourceBorder', 'SourceShadow', 'SourceRectShape',
    'SourceRectShape.all', 'SourceOvalShape', 'SourcePathShape', 'SourcePathPoint',
    'Offset', 'Color', 'Rect.fromLTWH', 'SizedBox', 'Positioned', 'Positioned.fill',
    'Stack', 'SourceAsset', 'SourcePlaceholder', 'Opacity', 'ClipPath',
    'SourceShapeClipper', 'SourceBackdropBlur', 'SourceLayerBlur', 'Align', 'Center',
    'SystemChromeSlot', 'SourceTextRun',
}
TEXT_ALIGN = {'left': 'TextAlign.left', 'right': 'TextAlign.right',
              'center': 'TextAlign.center', 'justify': 'TextAlign.justify'}
PRIMITIVE_NAMES = {'box': 'SourceBox', 'text': 'SourceText'}


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

class FlutterEmitter:
    def __init__(self, model: SceneModel):
        self.m = model
        self.cls = model.class_name

    # values
    def color(self, c: N) -> Raw:
        return Raw(f'{self.cls}Tokens.{c["name"]}', const=True)

    def tstyle(self, s: N) -> Raw:
        return Raw(f'{self.cls}Tokens.{s["name"]}')

    def shape(self, s: N | None) -> Call | None:
        if s is None:
            return None
        if s.kind == 'rect':
            radii = s['radii']
            if radii is None:
                return Call('SourceRectShape')
            if isinstance(radii, tuple) and radii[0] == 'all':
                return Call('SourceRectShape.all', radii[1])
            return Call('SourceRectShape', radii=DList(list(radii), 'double'))
        if s.kind == 'oval':
            return Call('SourceOvalShape')
        if s.kind == 'path':
            items = []
            for p in s['points']:
                named = {}
                if p['curve_from'] is not None:
                    named['curveFrom'] = Call('Offset', *p['curve_from'])
                if p['curve_to'] is not None:
                    named['curveTo'] = Call('Offset', *p['curve_to'])
                items.append(Call('SourcePathPoint', Call('Offset', *p['point']), **named))
            return Call('SourcePathShape', points=DList(items),
                        closed=None if s['closed'] else False,
                        evenOdd=True if s['even_odd'] else None)
        raise TypeError(s.kind)

    def fill(self, f: N) -> Call:
        if f.kind == 'linear':
            return Call('SourceFill.linear', Call('SourceLinearGradient', **{
                'from': Call('Offset', *f['start']), 'to': Call('Offset', *f['end']),
                'stops': DList([Call('SourceGradientStop', pos, self.color(c))
                                for pos, c in f['stops']])}), opacity=f['opacity'])
        return Call('SourceFill.color', self.color(f['color']), opacity=f['opacity'])

    def border(self, b: N) -> Call:
        caps = {'butt': 'StrokeCap.butt', 'round': 'StrokeCap.round', 'square': 'StrokeCap.square'}
        joins = {'miter': 'StrokeJoin.miter', 'round': 'StrokeJoin.round', 'bevel': 'StrokeJoin.bevel'}
        return Call('SourceBorder', thickness=b['thickness'], fill=self.fill(b['fill']),
                    position=None if b['position'] == 'center'
                    else Raw(f'SourceBorderPosition.{b["position"]}', True),
                    cap=Raw(caps[b['cap']], True) if b['cap'] else None,
                    join=Raw(joins[b['join']], True) if b['join'] else None,
                    dash=DList(b['dash'], 'double') if b['dash'] else None)

    def shadow(self, s: N) -> Call:
        return Call('SourceShadow', color=self.color(s['color']),
                    offset=Call('Offset', *s['offset']) if s['offset'] else None,
                    blurRadius=s['blur'], spread=s['spread'], inner=True if s['inner'] else None)

    def value(self, v: Any) -> Any:
        if isinstance(v, Expr):
            return Raw(f'{v.var} + {num(v.value)}')
        return v

    # widgets
    def widget(self, n: N) -> Any:
        k = n.kind
        if k == 'box':
            return Call('SourceBox', shape=self.shape(n['shape']),
                        fills=DList([self.fill(f) for f in n['fills']]) if n['fills'] else None,
                        borders=DList([self.border(b) for b in n['borders']]) if n['borders'] else None,
                        shadows=DList([self.shadow(s) for s in n['shadows']]) if n['shadows'] else None,
                        opacity=n['opacity'])
        if k in ('text', 'rich'):
            named = {'style': self.tstyle(n['style']),
                     'textAlign': None if n['align'] == 'left' else Raw(TEXT_ALIGN[n['align']], True),
                     'softWrap': True if n['wrap'] else None}
            if k == 'text':
                return Call('SourceText', n['text'], **named)
            return Call('SourceText.rich', DList([Call('SourceTextRun', t, self.tstyle(s))
                                                 for t, s in n['runs']]), **named)
        if k == 'asset':
            export = n['export_rect']
            return Call('SourceAsset', Raw(f'{self.cls}Assets.{n["ident"]}', True),
                        exportRect=Call('Rect.fromLTWH', *export) if export else None)
        if k == 'placeholder':
            return Call('SourcePlaceholder', nodeId=n['node_id'])
        if k == 'overlay':
            return Call('Stack', children=DList([self.widget(c) for c in n['children']], 'Widget'))
        if k == 'stack':
            return Call('Stack', clipBehavior=Raw('Clip.none', True),
                        children=DList([self.widget(c) for c in n['children']], 'Widget'))
        if k == 'fill':
            return Call('Positioned.fill', child=self.widget(n['child']))
        if k == 'placed':
            args = {name: self.value(v) for name, v in n['args']}
            return Call('Positioned', **args, child=self.widget(n['child']))
        if k == 'align_top_center':
            return Call('Align', alignment=Raw('Alignment.topCenter', True), child=self.widget(n['child']))
        if k == 'sized':
            return Call('SizedBox', width=n['width'], child=self.widget(n['child']))
        if k == 'opacity':
            return Call('Opacity', opacity=n['value'], child=self.widget(n['child']))
        if k == 'backdrop':
            return Call('SourceBackdropBlur', radius=n['radius'], shape=self.shape(n['shape']),
                        saturation=n['saturation'], child=self.widget(n['child']))
        if k == 'layer_blur':
            return Call('SourceLayerBlur', radius=n['radius'], child=self.widget(n['child']))
        if k == 'flip':
            return Call('Transform.flip', flipX=n['x'] or None, flipY=n['y'] or None,
                        child=self.widget(n['child']))
        if k == 'clip':
            return Call('ClipPath', clipper=Call('SourceShapeClipper', self.shape(n['shape'])),
                        child=self.widget(n['child']))
        if k == 'node':
            child = n['child']
            if child.kind == 'group_ref':
                return Call('_node', Raw('context'), n['id'], Raw(f'() => {child["method"]}(context)'))
            return Call('_node', Raw('context'), n['id'], Lambda(self.widget(child)))
        raise TypeError(f'Unknown model node {k}')

    def text_style_call(self, spec: dict) -> Call:
        family: Any = spec['family']
        if spec['platforms']:
            args = ''.join(f", {k}: {'SourceFonts.system' if v is None else dart_string(v)}"
                           for k, v in sorted(spec['platforms'].items()))
            family = Raw(f'sourceFontFamily({dart_string(spec["family"])}{args})')
        decoration = {'underline': 'TextDecoration.underline',
                      'lineThrough': 'TextDecoration.lineThrough'}.get(spec['decoration'])
        return Call('sourceTextStyle', fontFamily=family, fontSize=spec['size'],
                    fontWeight=Raw(f'FontWeight.w{spec["weight"]}', True),
                    lineHeight=spec['line_height'],
                    letterSpacing=spec['letter_spacing'] if spec['letter_spacing'] else None,
                    color=self.color(spec['color']),
                    decoration=Raw(decoration, True) if decoration else None)

    def dart(self, children: list[N]) -> str:
        m = self.m
        width, height = m.canvas
        first = m.documents[0]
        lines = [
            '// GENERATED by lanhu-design-fidelity/scripts/generate_flutter.py; do not edit.',
            f'// Source: {first.get("design_name") or ""} snapshot {first.get("snapshot_id")}',
            f'// version {first.get("resolved_version")}, canvas {num(width)}x{num(height)}.',
            '// Replace groups through `overrides` / wire actions through `onTap`.',
            '// ignore_for_file: prefer_const_constructors, unused_element, unused_local_variable',
            '',
            "import 'package:flutter/widgets.dart';",
            f"import '{PRIMITIVES_IMPORT}';",
            '',
            f'abstract final class {self.cls}Tokens {{',
        ]
        for name, code in sorted(m.colors.items()):
            lines.append(f'  static const Color {name} = Color(0x{code});')
        for name, spec in sorted(m.text_styles.values(), key=lambda item: item[0]):
            lines.append(f'  static final TextStyle {name} = {render(self.text_style_call(spec), 4)};')
        lines += ['}', '', f'abstract final class {self.cls}Assets {{']
        for ident, entry in sorted(m.asset_keys.items()):
            lines.append(f"  static const String {ident} = {dart_string(entry['app_asset'])};")
        lines.append('  static const List<String> all = <String>[' +
                     ', '.join(sorted(m.asset_keys)) + '];')
        lines += ['}', '']
        body_children = [self.widget(c) for c in children if not c.footer]
        footer_children = [self.widget(c) for c in children if c.footer]
        body = Call('Stack', clipBehavior=Raw('Clip.none', True), children=DList(body_children, 'Widget'))
        footer = ''.join(f'            {render(c, 12)},\n' for c in footer_children)
        lines += [
            f'class {self.cls}Scene extends StatelessWidget {{',
            f'  const {self.cls}Scene({{',
            '    super.key,',
            '    this.overrides = const <String, WidgetBuilder>{},',
            '    this.onTap = const <String, VoidCallback>{},',
            '    this.adaptSafeArea = true,',
            '  });',
            '',
            f'  static const Size designSize = Size({num(width)}, {num(height)});',
            '',
            '  /// Safe-area insets drawn in the design (status bar / home indicator).',
            '  /// The fidelity harness renders with exactly these insets.',
            f'  static const EdgeInsets designPadding = EdgeInsets.only(top: {num(m.design_top)}, '
            f'bottom: {num(m.design_bottom)});',
            '',
            '  /// Replacement widgets keyed by source node id; placed in the node frame.',
            '  final Map<String, WidgetBuilder> overrides;',
            '',
            '  /// Tap handlers keyed by source node id.',
            '  final Map<String, VoidCallback> onTap;',
            '',
            '  /// Follow the device safe area (default). The scene is a full-screen',
            '  /// page: do not wrap it in SafeArea or put an AppBar above it.',
            '  final bool adaptSafeArea;',
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
            '    final padding = adaptSafeArea',
            '        ? MediaQuery.maybePaddingOf(context) ?? designPadding',
            '        : designPadding;',
            '    // Root layers keep their distance to the top / bottom safe area.',
            '    final dy = padding.top - designPadding.top;',
            '    final dyBottom = padding.bottom - designPadding.bottom;',
            '    final natural = designSize.height + dy + dyBottom;',
            '    return LayoutBuilder(builder: (context, constraints) {',
            '      final height =',
            '          constraints.hasBoundedHeight ? constraints.maxHeight : natural;',
            '      // Shorter screens scroll the body; footers stay pinned.',
            '      final scrolls = height < natural - 0.5;',
            '      final body = SizedBox(',
            '        height: scrolls ? natural : height,',
            f'        child: {render(body, 8)},',
            '      );',
            '      return SizedBox(',
            '        height: height,',
            '        child: Stack(',
            '          clipBehavior: Clip.hardEdge,',
            '          children: <Widget>[',
            '            Positioned.fill(',
            '              child: scrolls ? SingleChildScrollView(child: body) : body,',
            '            ),',
            *([footer.rstrip('\n')] if footer_children else []),
            '          ],',
            '        ),',
            '      );',
            '    });',
            '  }',
        ]
        for method, name, node in m.methods:
            lines += ['', f'  /// {name}'.rstrip(),
                      f'  Widget {method}(BuildContext context) => {render(self.widget(node), 4)};']
        lines += ['}', '']
        return '\n'.join(lines)

    def report(self) -> dict:
        report = self.m.report('generate_flutter.py', GENERATOR_VERSION, asset_field='flutter_asset')
        # Keep Flutter vocabulary in the per-node records (stable report format).
        nodes = copy.deepcopy(report['nodes'])
        for entry in nodes:
            if 'primitive' in entry:
                entry['primitive'] = PRIMITIVE_NAMES.get(entry['primitive'], entry['primitive'])
            if 'align' in entry:
                entry['align'] = TEXT_ALIGN[entry['align']]
        report['nodes'] = nodes
        return report


def write_render_test(path: Path, app_root: Path | None, output: Path, class_name: str,
                      scale: float, output_env: str, font_map: Path | None = None) -> dict:
    """Create the page render test once (it is project code, never overwritten)."""
    from scene_test_codegen import page_import
    result = {'path': str(path), 'created': False}
    harness = path.parent / 'support' / 'fidelity_render_harness.dart'
    if not harness.exists() or harness.read_bytes() != HARNESS.read_bytes():
        # The harness is tool code: keep it in sync with the Skill version.
        harness.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HARNESS, harness)
        result['harness_installed'] = str(harness)
    if path.exists():
        text = path.read_text()
        if 'designPadding' not in text or 'height:' in text.split('captureResponsiveVariants', 1)[-1][:200]:
            result['outdated'] = ('render test predates safe-area support: pass padding: '
                                  f'{class_name}Scene.designPadding to captureFidelityPage and drop '
                                  'height: from captureResponsiveVariants')
        return result
    page = page_import(app_root, output, path)
    fonts = ''
    if font_map is not None:
        try:
            relative = font_map.resolve().relative_to(app_root.resolve()) if app_root else font_map
        except ValueError:
            relative = font_map.resolve()
        fonts = f"\n    // Design fonts are loaded from disk for fidelity renders only, never bundled.\n" \
                f"    await loadSourceFontMap({dart_string(Path(relative).as_posix())});"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"""import 'package:flutter_test/flutter_test.dart';

import '{page}';
import 'support/fidelity_render_harness.dart';

void main() {{
  FidelityTestBinding();
  setUpAll(() async {{
    await loadDeclaredFidelityFonts();{fonts}
  }});

  testWidgets('{class_name} source canvas', (tester) async {{
    // Render the production page: replace the scene with the page widget that
    // composes it (overrides/onTap) and pass appBuilder: your real app root.
    const page = {class_name}Scene();
    final output = fidelityOutputPath('{output_env}');
    await captureFidelityPage(
      tester,
      page: page,
      size: {class_name}Scene.designSize,
      padding: {class_name}Scene.designPadding,
      scale: {num(scale)},
      imageAssets: {class_name}Assets.all,
      output: output,
    );
    // iPhone SE / 15 / 15 Pro Max and two Android sizes, at 1.0x and 1.3x text.
    await captureResponsiveVariants(tester, page: page, output: output);
  }});
}}
""", encoding='utf-8')
    result['created'] = True
    return result


def emit(model: SceneModel, ctx: dict) -> dict:
    """Write the Dart scene, scene test and render test; returns the report."""
    output: Path = ctx['output']
    app_root: Path | None = ctx.get('app_root')
    children = model.build()
    emitter = FlutterEmitter(model)
    dart = emitter.dart(children)
    report = emitter.report()
    scene_test = ctx.get('scene_test')
    if scene_test is None and app_root is not None:
        stem = output.name[:-len('.g.dart')] if output.name.endswith('.g.dart') else output.stem
        scene_test = app_root / 'test' / f'{stem}_scene_test.g.dart'
    if scene_test is not None:
        from scene_test_codegen import write_scene_test
        report['scene_test'] = write_scene_test(model, model.class_name, app_root, output, scene_test)
    render_test = ctx.get('render_test')
    if render_test is not None:
        report['render_test'] = write_render_test(render_test, app_root, output, model.class_name,
                                                  float(model.plan.get('render_scale') or 4),
                                                  ctx.get('output_env') or 'PAGE_RENDER_OUTPUT',
                                                  ctx.get('font_map'))
        if report['render_test'].get('outdated'):
            report['issues'].append({'kind': 'render_test_outdated', 'path': str(render_test),
                                     'message': report['render_test']['outdated']})
    return {'code': dart, 'report': report, 'asset_field': 'flutter_asset'}


def default_report_path(output: Path) -> Path:
    return output.with_suffix('').with_suffix('.codegen.json')


__all__ = ['emit', 'render', 'Call', 'Raw', 'DList', 'Lambda', 'dart_string',
           'write_render_test', 'default_report_path', 'HARNESS']
_ = (hashlib, json, re)
