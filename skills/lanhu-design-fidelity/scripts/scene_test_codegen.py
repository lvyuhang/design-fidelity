"""Generate the Flutter scene-obligation test for a generated page.

Every source scene requirement (stroke, paint stack, clip, backdrop, boundary
overlay, placeholder effect) becomes executable checks against the production
scene widget:

* binding - the node renders through the verified `lanhu_fidelity` primitive
  with the source parameters (read from the live widget tree, not constants);
* pixels  - strokes are rendered with and without the border to prove the band
  sits inside/centred/outside the edge and leaks nowhere else; coincident fill
  stacks are sampled in the full scene against the source composite.

Primitive mechanisms themselves are proven by the package's own pixel tests.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from scene_requirements import scene_requirements

GRAY = (128, 128, 128)


def _num(value: float) -> str:
    text = f'{float(value):.4f}'.rstrip('0').rstrip('.')
    return '0' if text in ('-0', '') else text


def _dart_string(value: str) -> str:
    return "'" + value.replace('\\', '\\\\').replace("'", "\\'").replace('$', '\\$') + "'"


def page_import(app: Path | None, output: Path, test_file: Path) -> str:
    if app is not None:
        pubspec = app / 'pubspec.yaml'
        lib = (app / 'lib').resolve()
        if pubspec.is_file() and lib in output.resolve().parents:
            match = re.search(r'^name:\s*([A-Za-z_][\w]*)\s*$', pubspec.read_text(), re.M)
            if match:
                return f'package:{match.group(1)}/{output.resolve().relative_to(lib).as_posix()}'
    return os.path.relpath(output.resolve(), test_file.resolve().parent).replace(os.sep, '/')


def _over(base, color, alpha):
    return tuple(c * alpha + b * (1 - alpha) for b, c in zip(base, color))


def _distance(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


class SceneTestWriter:
    def __init__(self, generator, class_name: str, import_path: str):
        self.g = generator
        self.class_name = class_name
        self.import_path = import_path
        self.tests: list[str] = []
        self.obligations: list[dict] = []

    # ---- source facts -------------------------------------------------------
    def borders(self, key):
        from scene_model import BORDER_POSITION, enabled, parse_color
        raw = self.g.nodes[key].get('raw_style') or {}
        result = []
        for border in enabled(raw.get('borders')):
            if float(border.get('thickness') or 0) <= 0:
                continue
            color = parse_color(border.get('color')) if border.get('type', 'color') == 'color' else None
            if border.get('type', 'color') == 'color' and color is None:
                continue
            result.append({'thickness': float(border['thickness']),
                           'position': BORDER_POSITION.get(border.get('position'), 'center'),
                           'color': color})
        return result

    def solid_fills(self, key):
        from scene_model import enabled, parse_color
        raw = self.g.nodes[key].get('raw_style') or {}
        fills = []
        for fill in enabled(raw.get('fills')):
            if fill.get('type', 'color') != 'color':
                return None
            color = parse_color(fill.get('color'))
            if color is None:
                return None
            fills.append((color[:3], color[3] * float(fill.get('opacity', 1) or 1)))
        return fills

    def owner_mode(self, key):
        record = self.g.records.get(key) or {}
        return record.get('mode'), record.get('owner')

    # ---- obligations --------------------------------------------------------
    def add(self, requirement):
        ident, kind = requirement['id'], requirement['kind']
        keys = requirement['node_ids']
        modes = {k: self.owner_mode(k) for k in keys}
        if all(m[0] in ('system_chrome', 'hidden') for m in modes.values()):
            return
        body, status = None, 'bound'
        covered = [k for k, (mode, _) in modes.items() if mode == 'covered_by_asset']
        if covered and len(covered) == len(keys):
            owners = sorted({modes[k][1] for k in covered})
            body = '\n'.join(f"    _bound<SourceAsset>({_dart_string(o)});" for o in owners)
            note = 'covered by exported asset'
        elif kind == 'stroke':
            body, note = self.stroke(keys[0])
        elif kind == 'paint_stack':
            body, note = self.paint_stack(keys)
        elif kind == 'backdrop':
            body, note = self.backdrop(keys[0])
        elif kind == 'clip':
            body, note = self.clip(keys[0])
        elif kind == 'boundary_overlay':
            body, note = self.boundary(keys[0])
        elif kind == 'placeholder_effect':
            body, note = self.placeholder_effect(keys[0], ident.rsplit('/', 1)[-1])
        else:
            note = f'unknown obligation kind {kind}'
        if body is None:
            status = 'unsupported'
        else:
            name = _dart_string(f'{kind}: {ident} ({note})')
            self.tests.append(f"  testWidgets({name}, (tester) async {{\n"
                              f"    final scene = GlobalKey();\n"
                              f"    await _pumpScene(tester, scene);\n{body}\n  }});")
        self.obligations.append({'id': ident, 'kind': kind, 'node_ids': keys,
                                 'status': status, 'note': note})

    def stroke(self, key):
        mode, _ = self.owner_mode(key)
        if mode != 'native_exact':
            return None, f'node rendered as {mode}'
        borders = self.borders(key)
        if not borders:
            return None, 'no renderable border'
        expected = ', '.join(f"[{_num(b['thickness'])}, SourceBorderPosition.{b['position']}]"
                             for b in borders)
        lines = [f"    final box = _bound<SourceBox>({_dart_string(key)});",
                 "    expect([for (final b in box.borders) [b.thickness, b.position]],",
                 f"        [{expected}]);"]
        _, shape_kind = self.g.shape_of(key)
        first = borders[0]
        x, y, w, h = self.g.frame(key)
        fills = self.solid_fills(key) or []
        fill_rgb = GRAY
        for rgb, alpha in fills:
            fill_rgb = _over(fill_rgb, rgb, alpha)
        border_rgb = None
        if first['color']:
            border_rgb = _over(fill_rgb if first['position'] == 'inside' else GRAY,
                               first['color'][:3], first['color'][3])
        contrast = border_rgb is not None and _distance(border_rgb, fill_rgb if first['position'] == 'inside' else GRAY) >= 8
        if shape_kind in ('rect', 'oval') and len(borders) == 1 and contrast:
            lines.append(f"    await _expectBorderBand(tester, box, const Size({_num(w)}, {_num(h)}), "
                         f"{_num(first['thickness'])}, SourceBorderPosition.{first['position']});")
            return '\n'.join(lines), 'binding + rendered edge band'
        return '\n'.join(lines), 'binding (band pixels not distinguishable for this shape/colour)'

    def paint_stack(self, keys):
        lines = []
        for key in keys:
            mode, _ = self.owner_mode(key)
            if mode != 'native_exact':
                continue
            fills = (self.g.nodes[key].get('raw_style') or {}).get('fills') or []
            count = sum(1 for f in fills if isinstance(f, dict) and f.get('isEnabled', True) is not False)
            lines.append(f"    expect(_bound<SourceBox>({_dart_string(key)}).fills.length, {count});")
        if not lines:
            return None, 'no natively rendered layer'
        sample = self.stack_sample(keys)
        if sample:
            (px, py), rgb = sample
            lines.append("    final image = await _capture(tester, scene, 1);")
            lines.append(f"    expect(_diff(image.rgb({px}, {py}), [{', '.join(str(round(c)) for c in rgb)}]), "
                         "lessThanOrEqualTo(3),")
            lines.append(f"        reason: 'composited source fills at ({px}, {py})');")
            return '\n'.join(lines), 'binding + composited pixel'
        return '\n'.join(lines), 'binding (no unobstructed sample point)'

    def stack_sample(self, keys):
        layers = []
        base = None
        roots = [k for k, n in self.g.nodes.items() if n.get('parent_id') not in self.g.nodes]
        for root in roots:
            raw = self.g.nodes[root].get('raw_style') or {}
            if raw.get('hasBackgroundColor') and root not in keys:
                fills = self.solid_fills(root)
                if fills:
                    base = (0, 0, 0)
                    alpha = 0.0
                    for rgb, a in fills:
                        base = _over(base, rgb, a)
                        alpha = alpha + a * (1 - alpha)
                    if alpha < 0.999:
                        base = None
        for key in sorted(keys, key=lambda k: self.g.nodes[k].get('source_order', 0)):
            raw = self.g.nodes[key].get('raw_style') or {}
            if key in roots and not raw.get('hasBackgroundColor'):
                continue  # Sketch does not paint artboard fills without a background.
            fills = self.solid_fills(key)
            if fills is None:
                return None
            opacity = float(raw.get('opacity', 100) or 100) / 100
            layers.extend((rgb, a * opacity) for rgb, a in fills)
        color, alpha = base, 1.0 if base is not None else 0.0
        color = color or (0, 0, 0)
        for rgb, a in layers:
            color = _over(color, rgb, a) if alpha > 0 else tuple(rgb)
            alpha = alpha + a * (1 - alpha) if alpha > 0 else a
        if alpha < 0.999:
            return None
        x, y, w, h = self.g.frame(keys[0])
        others = []
        stack = set(keys)
        for key, node in self.g.visible.items():
            if key in stack or self.owner_mode(key)[0] in ('system_chrome', 'hidden', None):
                continue
            bx, by, bw, bh = self.g.frame(key)
            if bw >= self.g.canvas[0] - 1 and bh >= self.g.canvas[1] - 1:
                continue
            others.append((bx - 24, by - 24, bx + bw + 24, by + bh + 24))
        step = 8
        for sy in range(int(y) + 4, int(y + h) - 4, step):
            for sx in range(int(x) + 4, int(x + w) - 4, step):
                if all(not (l <= sx <= r and t <= sy <= b) for l, t, r, b in others):
                    return (sx, sy), color
        return None

    def backdrop(self, key):
        mode, _ = self.owner_mode(key)
        if mode != 'native_exact':
            return None, f'node rendered as {mode}'
        blur = (self.g.nodes[key].get('raw_style') or {}).get('blur') or {}
        saturation = blur.get('saturation', 1)
        lines = [f"    final blur = _bound<SourceBackdropBlur>({_dart_string(key)});",
                 f"    expect(blur.radius, {_num(float(blur.get('radius') or 0))});"]
        if isinstance(saturation, (int, float)):
            lines.append(f"    expect(blur.saturation, {_num(saturation)});")
        return '\n'.join(lines), 'binding of radius/saturation'

    def clip(self, key):
        members = (self.g.records.get(key) or {}).get('masks') or []
        members = [m for m in members if self.owner_mode(m)[0] in ('native_exact', 'original_asset',
                                                                   'missing_asset_placeholder')]
        if not members:
            return None, 'no rendered masked member'
        checks = '\n'.join(
            f"    expect(find.ancestor(of: find.byKey(sourceKey({_dart_string(m)})), matching: "
            "find.byWidgetPredicate((w) => w is ClipPath && w.clipper is SourceShapeClipper)), "
            "findsWidgets);" for m in members)
        return checks, 'masked members clipped by source shape'

    def boundary(self, key):
        asset = self.g.assets.get(key)
        if not asset:
            return None, 'asset not installed'
        x, y, _, _ = self.g.frame(key)
        ex, ey, ew, eh = asset['export_rect']
        rect = (f'const Rect.fromLTWH({_num(ex - x)}, {_num(ey - y)}, {_num(ew)}, {_num(eh)})'
                if [ex, ey, ew, eh] != list(self.g.frame(key)) else 'null')
        return (f"    expect(_bound<SourceAsset>({_dart_string(key)}).exportRect, {rect});",
                'export frame binding')

    def placeholder_effect(self, key, effect_key):
        mode, _ = self.owner_mode(key)
        if mode != 'missing_asset_placeholder':
            return None, f'node rendered as {mode}'
        raw = self.g.nodes[key].get('raw_style') or {}
        field = effect_key.split(':')[0]
        head = f"    _bound<SourcePlaceholder>({_dart_string(key)});"
        if field in ('shadow', 'shadows', 'innerShadows'):
            count = sum(1 for f in ('shadow', 'innerShadows', 'innerShadow') for s in raw.get(f) or []
                        if isinstance(s, dict) and s.get('isEnabled', True) is not False)
            return (head + f"\n    expect(_bound<SourceBox>({_dart_string(key)}).shadows.length, {count});",
                    'placeholder keeps source shadows')
        if field == 'borders' and not effect_key.endswith(':gradient'):
            count = sum(1 for b in raw.get('borders') or [] if isinstance(b, dict) and b.get('isEnabled', True) is not False)
            return (head + f"\n    expect(_bound<SourceBox>({_dart_string(key)}).borders.length, {count});",
                    'placeholder keeps source borders')
        if effect_key == 'opacity':
            return (head + f"\n    expect(find.ancestor(of: find.byType(SourcePlaceholder), matching: "
                    f"find.byWidgetPredicate((w) => w is Opacity && (w.opacity - {_num(float(raw['opacity']) / 100)}).abs() < 1e-6)), findsWidgets);",
                    'placeholder keeps layer opacity')
        if field == 'blur':
            blur = raw.get('blur') or {}
            widget = 'SourceBackdropBlur' if blur.get('blurType') == 3 else 'SourceLayerBlur'
            return (head + f"\n    expect(_bound<{widget}>({_dart_string(key)}).radius, {_num(float(blur.get('radius') or 0))});",
                    'placeholder keeps blur')
        return None, f'effect {effect_key} not representable on a placeholder'

    # ---- output -------------------------------------------------------------
    def dart(self) -> str:
        width, height = self.g.canvas
        header = f"""// GENERATED by lanhu-design-fidelity/scripts/generate_flutter.py; do not edit.
// Scene obligations of {self.class_name}Scene: each source effect is bound to the
// verified lanhu_fidelity primitive in the production scene, with pixel probes.
// ignore_for_file: prefer_const_constructors
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/rendering.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lanhu_fidelity/lanhu_fidelity.dart';

import '{self.import_path}';

const Size _canvas = Size({_num(width)}, {_num(height)});

Future<void> _pumpScene(WidgetTester tester, GlobalKey boundary) async {{
  tester.view.physicalSize = _canvas;
  tester.view.devicePixelRatio = 1;
  // The design's own safe area keeps every node at its source coordinates.
  const inset = {self.class_name}Scene.designPadding;
  final padding = FakeViewPadding(top: inset.top, bottom: inset.bottom);
  tester.view.padding = padding;
  tester.view.viewPadding = padding;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  addTearDown(tester.view.resetPadding);
  addTearDown(tester.view.resetViewPadding);
  await tester.pumpWidget(Directionality(
    textDirection: TextDirection.ltr,
    child: RepaintBoundary(key: boundary, child: const {self.class_name}Scene()),
  ));
}}

T _bound<T extends Widget>(String nodeId) {{
  final finder = find.descendant(
      of: find.byKey(sourceKey(nodeId)), matching: find.byType(T));
  expect(finder, findsWidgets, reason: '$nodeId must render through $T');
  return finder.evaluate().first.widget as T;
}}

class _Pixels {{
  _Pixels(this.width, this.data);

  final int width;
  final ByteData data;

  List<int> rgb(int x, int y) {{
    final offset = (y * width + x) * 4;
    return <int>[
      data.getUint8(offset),
      data.getUint8(offset + 1),
      data.getUint8(offset + 2),
    ];
  }}
}}

Future<_Pixels> _capture(
    WidgetTester tester, GlobalKey key, double ratio) async {{
  final boundary =
      key.currentContext!.findRenderObject()! as RenderRepaintBoundary;
  final pixels = await tester.runAsync(() async {{
    final image = await boundary.toImage(pixelRatio: ratio);
    try {{
      final data = await image.toByteData(format: ui.ImageByteFormat.rawRgba);
      return _Pixels(image.width, data!);
    }} finally {{
      image.dispose();
    }}
  }});
  return pixels!;
}}

int _diff(List<int> a, List<int> b) {{
  var result = 0;
  for (var i = 0; i < 3; i++) {{
    final delta = (a[i] - b[i]).abs();
    if (delta > result) result = delta;
  }}
  return result;
}}

/// Renders the node's own shape/fills with and without its border on mid-grey
/// and checks the band position plus the absence of leaks on the other side.
Future<void> _expectBorderBand(WidgetTester tester, SourceBox box, Size size,
    double thickness, SourceBorderPosition position) async {{
  const ratio = 4.0;
  final margin = thickness * 2 + 4;
  Future<_Pixels> render(SourceBox variant) async {{
    final key = GlobalKey();
    await tester.pumpWidget(Directionality(
      textDirection: TextDirection.ltr,
      child: Align(
        alignment: Alignment.topLeft,
        child: RepaintBoundary(
          key: key,
          child: ColoredBox(
            color: const Color(0xFF808080),
            child: Padding(
              padding: EdgeInsets.all(margin),
              child: SizedBox.fromSize(size: size, child: variant),
            ),
          ),
        ),
      ),
    ));
    return _capture(tester, key, ratio);
  }}

  final bordered = await render(SourceBox(
      shape: box.shape, fills: box.fills, borders: box.borders, opacity: box.opacity));
  final plain = await render(
      SourceBox(shape: box.shape, fills: box.fills, opacity: box.opacity));
  final y = ((margin + size.height / 2) * ratio).floor();
  int px(double x) => (x * ratio).floor();
  final band = switch (position) {{
    SourceBorderPosition.inside => margin + thickness / 2,
    SourceBorderPosition.center => margin,
    SourceBorderPosition.outside => margin - thickness / 2,
  }};
  expect(_diff(bordered.rgb(px(band), y), plain.rgb(px(band), y)),
      greaterThan(2), reason: 'border band must be painted at $band');
  final outsideEdge = switch (position) {{
    SourceBorderPosition.inside => margin - 1.5,
    SourceBorderPosition.center => margin - thickness / 2 - 1.5,
    SourceBorderPosition.outside => margin - thickness - 1.5,
  }};
  final insideEdge = switch (position) {{
    SourceBorderPosition.inside => margin + thickness + 1.5,
    SourceBorderPosition.center => margin + thickness / 2 + 1.5,
    SourceBorderPosition.outside => margin + 1.5,
  }};
  for (final x in <double>[outsideEdge, insideEdge]) {{
    expect(_diff(bordered.rgb(px(x), y), plain.rgb(px(x), y)),
        lessThanOrEqualTo(2), reason: 'border must not leak to $x');
  }}
}}
"""
        if not self.tests:
            body = "  test('no scene obligations', () {});"
        else:
            body = '\n\n'.join(self.tests)
        return header + '\nvoid main() {\n' + body + '\n}\n'


def write_scene_test(generator, class_name: str, app: Path | None, output: Path,
                     test_file: Path) -> dict:
    writer = SceneTestWriter(generator, class_name, page_import(app, output, test_file))
    for requirement in scene_requirements(generator.nodes):
        writer.add(requirement)
    from source_requirements import effects
    for key, record in generator.records.items():
        if record['mode'] == 'missing_asset_placeholder' and key in generator.visible:
            for effect_key in effects(generator.nodes[key]):
                writer.add({'id': f'{key}/placeholder_effect/{effect_key}', 'kind': 'placeholder_effect',
                            'node_ids': [key]})
    text = writer.dart()
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(text, encoding='utf-8')
    return {'test_file': str(test_file), 'obligations': writer.obligations}
