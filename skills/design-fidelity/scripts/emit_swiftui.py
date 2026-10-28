"""SwiftUI emitter: scene model -> Swift on the DesignFidelity package (preview)."""
from __future__ import annotations

import copy
import os
import re
from pathlib import Path
from typing import Any

from scene_model import Expr, N, SceneModel, num

GENERATOR_VERSION = 1
HARNESS = Path(__file__).resolve().parents[1] / 'assets' / 'swiftui' / 'FidelityHarness.swift'
TEXT_KINDS = {'text', 'rich'}
WRAPPERS = {'opacity', 'flip', 'layer_blur'}
ALIGN = {'left': '.leading', 'right': '.trailing', 'center': '.center', 'justify': '.leading'}


def sw_string(value: str) -> str:
    escaped = (value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
               .replace('\r', '\\r').replace('\t', '\\t'))
    return f'"{escaped}"'


def n(value: float) -> str:
    return num(value)


def asset_runtime_path(app_asset: str, root_marker: str = 'DesignAssets') -> str:
    """`App/DesignAssets/withdraw_2/x.png` -> `withdraw_2/x.png` (bundle folder reference)."""
    parts = Path(app_asset).parts
    return '/'.join(parts[parts.index(root_marker) + 1:]) if root_marker in parts else Path(app_asset).name


class Block:
    def __init__(self, head: str, children: list | None = None, suffix: str = ''):
        self.head, self.children, self.suffix = head, children, suffix


class SwiftUIEmitter:
    def __init__(self, model: SceneModel):
        self.m = model
        self.cls = model.class_name
        self.approximations: list[dict] = []
        self.current: str | None = None

    def note(self, feature: str, detail: str) -> None:
        self.approximations.append({'node_id': self.current, 'feature': feature, 'detail': detail})

    def color(self, c: N) -> str:
        return f'{self.cls}Tokens.{c["name"]}'

    @staticmethod
    def point(p) -> str:
        return f'CGPoint(x: {n(p[0])}, y: {n(p[1])})'

    def shape(self, s: N | None) -> str | None:
        if s is None:
            return None
        if s.kind == 'rect':
            radii = s['radii']
            if radii is None:
                return '.rect()'
            if isinstance(radii, tuple) and radii[0] == 'all':
                return f'.rect({n(radii[1])})'
            return '.rect(radii: [' + ', '.join(n(r) for r in radii) + '])'
        if s.kind == 'oval':
            return '.oval'
        points = []
        for p in s['points']:
            extra = ''
            if p['curve_from'] is not None:
                extra += f', curveFrom: {self.point(p["curve_from"])}'
            if p['curve_to'] is not None:
                extra += f', curveTo: {self.point(p["curve_to"])}'
            points.append(f'SourcePathPoint({self.point(p["point"])}{extra})')
        return (f'.path(points: [{", ".join(points)}], closed: {"true" if s["closed"] else "false"}, '
                f'evenOdd: {"true" if s["even_odd"] else "false"})')

    def fill(self, fl: N) -> str:
        opacity = f', opacity: {n(fl["opacity"])}' if fl['opacity'] is not None else ''
        if fl.kind == 'linear':
            stops = ', '.join(f'SourceGradientStop({n(pos)}, {self.color(c)})' for pos, c in fl['stops'])
            return (f'.linear(SourceLinearGradient(from: {self.point(fl["start"])}, to: {self.point(fl["end"])}, '
                    f'stops: [{stops}]){opacity})')
        return f'.solid({self.color(fl["color"])}{opacity})'

    def border(self, b: N) -> str:
        args = [f'thickness: {n(b["thickness"])}', f'fill: {self.fill(b["fill"])}']
        if b['position'] != 'center':
            args.append(f'position: .{b["position"]}')
        if b['cap']:
            args.append(f'cap: .{b["cap"]}')
        if b['join']:
            args.append(f'join: .{b["join"]}')
        if b['dash']:
            args.append('dash: [' + ', '.join(n(v) for v in b['dash']) + ']')
        return 'SourceBorder(' + ', '.join(args) + ')'

    def shadow(self, s: N) -> str:
        args = [f'color: {self.color(s["color"])}']
        if s['offset']:
            args.append(f'offset: CGSize(width: {n(s["offset"][0])}, height: {n(s["offset"][1])})')
        if s['blur']:
            args.append(f'blurRadius: {n(s["blur"])}')
        if s['spread']:
            args.append(f'spread: {n(s["spread"])}')
        if s['inner']:
            args.append('inner: true')
        return 'SourceShadow(' + ', '.join(args) + ')'

    def value(self, v: Any) -> str:
        if isinstance(v, Expr):
            expr = f'insets.{v.var} + {n(v.value)}'
            return f'max({n(v.floor)}, {expr})' if v.floor is not None else expr
        return n(v)

    @staticmethod
    def is_text(node: N) -> bool:
        while node.kind in WRAPPERS:
            node = node['child']
        return node.kind in TEXT_KINDS

    def element(self, e: N, fill: bool = True) -> Block:
        k = e.kind
        if k == 'box':
            args = []
            shape = self.shape(e['shape'])
            if shape:
                args.append(f'shape: {shape}')
            if e['fills']:
                args.append('fills: [' + ', '.join(self.fill(x) for x in e['fills']) + ']')
            if e['borders']:
                args.append('borders: [' + ', '.join(self.border(x) for x in e['borders']) + ']')
            if e['shadows']:
                args.append('shadows: [' + ', '.join(self.shadow(x) for x in e['shadows']) + ']')
            if e['opacity'] is not None:
                args.append(f'opacity: {n(e["opacity"])}')
            return Block('SourceBox(' + ', '.join(args) + ')')
        if k in TEXT_KINDS:
            named = [f'style: {self.cls}Tokens.{e["style"]["name"]}']
            if e['align'] != 'left':
                named.append(f'align: {ALIGN[e["align"]]}')
                if e['align'] == 'justify':
                    self.note('justified_text', 'SwiftUI has no justified alignment; drawn leading')
            if e['wrap']:
                named.append('wrap: true')
            if k == 'text':
                return Block(f'SourceText({sw_string(e["text"])}, ' + ', '.join(named) + ')')
            runs = ', '.join(f'({sw_string(t)}, {self.cls}Tokens.{s["name"]})' for t, s in e['runs'])
            return Block(f'SourceText(runs: [{runs}], ' + ', '.join(named) + ')')
        if k == 'asset':
            rect = e['export_rect']
            extra = (f', exportRect: CGRect(x: {n(rect[0])}, y: {n(rect[1])}, width: {n(rect[2])}, height: {n(rect[3])})'
                     if rect else '')
            return Block(f'SourceAsset({self.cls}Assets.{e["ident"]}{extra})')
        if k == 'placeholder':
            return Block(f'SourcePlaceholder(nodeId: {sw_string(e["node_id"])})')
        if k in ('overlay', 'stack'):
            return Block('ZStack(alignment: .topLeading)', [self.element(c, True) for c in e['children']])
        if k == 'fill':
            return Block('SourcePlaced(left: 0, top: 0, right: 0, bottom: 0)', [self.element(e['child'], True)])
        if k == 'placed':
            args = ', '.join(f'{name}: {self.value(v)}' for name, v in sorted(
                [a for a in e['args'] if a[1] is not None],
                key=lambda a: ('left', 'top', 'right', 'bottom', 'width', 'height').index(a[0])))
            return Block(f'SourcePlaced({args})', [self.element(e['child'], True)])
        if k == 'align_top_center':
            return Block('ZStack(alignment: .top)', [self.element(e['child'], True)],
                         '.frame(maxWidth: .infinity, alignment: .top)')
        if k == 'sized':
            return Block('ZStack(alignment: .topLeading)', [self.element(e['child'], True)],
                         f'.frame(width: {n(e["width"])})')
        if k == 'opacity':
            return Block(f'SourceOpacity({n(e["value"])}{"" if fill else ", fill: false"})', [self.element(e['child'], fill)])
        if k == 'backdrop':
            self.note('backdrop_blur', 'SwiftUI materials have no calibrated radius; the blur is not drawn')
            return Block(f'SourceBackdropBlur(radius: {n(e["radius"])})', [self.element(e['child'], True)])
        if k == 'layer_blur':
            return Block(f'SourceLayerBlur({n(e["radius"])}{"" if fill else ", fill: false"})', [self.element(e['child'], fill)])
        if k == 'flip':
            args = [*(['x: true'] if e['x'] else []), *(['y: true'] if e['y'] else []),
                    *([] if fill else ['fill: false'])]
            return Block('SourceFlip(' + ', '.join(args) + ')', [self.element(e['child'], fill)])
        if k == 'clip':
            return Block(f'SourceClip({self.shape(e["shape"])})', [self.element(e['child'], True)])
        if k == 'node':
            child = e['child']
            previous, self.current = self.current, e['id']
            try:
                if child.kind == 'group_ref':
                    return Block(f'SourceNode({sw_string(e["id"])})', [Block(child['method'])])
                fill_node = not self.is_text(child)
                return Block(f'SourceNode({sw_string(e["id"])}{"" if fill_node else ", fill: false"})',
                             [self.element(child, fill_node)])
            finally:
                self.current = previous
        raise TypeError(f'Unknown model node {k}')

    @staticmethod
    def chunked(children: list) -> list:
        """ViewBuilder closures take at most 10 children on older SDKs: group the rest."""
        while len(children) > 10:
            children = [Block('Group', children[i:i + 10]) for i in range(0, len(children), 10)]
        return children

    def render(self, block: Block, indent: int) -> list[str]:
        pad = ' ' * indent
        if block.children is None:
            return [pad + block.head + block.suffix]
        lines = [f'{pad}{block.head} {{']
        for child in self.chunked(block.children):
            lines += self.render(child, indent + 4)
        lines.append(pad + '}' + block.suffix)
        return lines

    def text_spec(self, spec: dict) -> str:
        args = [f'family: {sw_string(spec["family"])}']
        if spec['platforms']:
            pairs = ', '.join(f'{sw_string(k)}: {"nil" if v is None else sw_string(v)}'
                              for k, v in sorted(spec['platforms'].items()))
            args.append(f'platforms: [{pairs}]')
        args += [f'size: {n(spec["size"])}', f'weight: {spec["weight"]}']
        if spec['line_height']:
            args.append(f'lineHeight: {n(spec["line_height"])}')
        if spec['letter_spacing']:
            args.append(f'letterSpacing: {n(spec["letter_spacing"])}')
        args.append(f'color: {spec["color"]["name"]}')
        if spec['decoration'] == 'underline':
            args.append('underline: true')
        if spec['decoration'] == 'lineThrough':
            args.append('strikethrough: true')
        return 'SourceTextSpec(' + ', '.join(args) + ')'

    def swift(self, children: list[N]) -> str:
        m = self.m
        cls = self.cls
        width, height = m.canvas
        first = m.documents[0]
        body = [self.element(c) for c in children if not c.footer]
        footer = [self.element(c) for c in children if c.footer]
        groups = [(method, name, self.element(node)) for method, name, node in m.methods]
        lines = [
            '// GENERATED by design-fidelity/scripts/generate.py --target swiftui; do not edit.',
            f'// Source: {first.get("design_name") or ""} snapshot {first.get("snapshot_id")}',
            f'// version {first.get("resolved_version")}, canvas {n(width)}x{n(height)}.',
            '// Replace layers through `overrides` / wire actions through `onTap`.',
            'import DesignFidelity',
            'import SwiftUI',
            '',
            f'public enum {cls}Tokens {{',
        ]
        for name, code in sorted(m.colors.items()):
            a, r, g, b = (int(code[i:i + 2], 16) for i in range(0, 8, 2))
            lines.append(f'    public static let {name} = Color(.sRGB, red: {r} / 255.0, green: {g} / 255.0, '
                         f'blue: {b} / 255.0, opacity: {a} / 255.0)')
        for name, spec in sorted(m.text_styles.values(), key=lambda item: item[0]):
            lines.append(f'    public static let {name} = {self.text_spec(spec)}')
        lines += ['}', '', f'public enum {cls}Assets {{']
        for ident, entry in sorted(m.asset_keys.items()):
            lines.append(f'    public static let {ident} = {sw_string(asset_runtime_path(entry["app_asset"]))}')
        lines.append('    public static let all = [' + ', '.join(sorted(m.asset_keys)) + ']')
        lines += ['}', '',
                  f'public enum {cls}Design {{',
                  f'    public static let size = CGSize(width: {n(width)}, height: {n(height)})',
                  '    /// Safe-area insets drawn in the design (status bar / home indicator).',
                  f'    public static let top: CGFloat = {n(m.design_top)}',
                  f'    public static let bottom: CGFloat = {n(m.design_bottom)}',
                  '}', '',
                  '/// Full-screen page: use it as the whole screen, without extra safe-area padding.',
                  f'public struct {cls}Scene: View {{',
                  '    public var overrides: [String: () -> AnyView]',
                  '    public var onTap: [String: () -> Void]',
                  '    public var adaptSafeArea: Bool',
                  '',
                  '    public init(overrides: [String: () -> AnyView] = [:], onTap: [String: () -> Void] = [:],',
                  '                adaptSafeArea: Bool = true) {',
                  '        self.overrides = overrides',
                  '        self.onTap = onTap',
                  '        self.adaptSafeArea = adaptSafeArea',
                  '    }',
                  '',
                  '    public var body: some View {',
                  f'        SourceScene(designSize: {cls}Design.size, designTop: {cls}Design.top, designBottom: {cls}Design.bottom,',
                  '                    adaptSafeArea: adaptSafeArea,',
                  '                    overrides: SceneOverrides(overrides: overrides, onTap: onTap)) { insets in']
        if footer:
            for block in self.chunked(footer):
                lines += self.render(block, 12)
        else:
            lines.append('            EmptyView()')
        lines.append('        } content: { insets in')
        for block in self.chunked(body):
            lines += self.render(block, 12)
        lines += ['        }', '    }', '}']
        if groups:
            lines += ['', f'private extension {cls}Scene {{']
            for method, name, element in groups:
                lines += ['', f'    /// {name}' if name else '    /// group', f'    var {method}: some View {{']
                lines += self.render(element, 8)
                lines.append('    }')
            lines.append('}')
        lines.append('')
        return '\n'.join(lines)

    def report(self) -> dict:
        report = self.m.report('generate.py --target swiftui', GENERATOR_VERSION, asset_field='app_asset')
        nodes = copy.deepcopy(report['nodes'])
        for entry in nodes:
            if 'primitive' in entry:
                entry['primitive'] = {'box': 'SourceBox', 'text': 'SourceText'}.get(entry['primitive'], entry['primitive'])
        report['nodes'] = nodes
        report['unsupported'] = report['unsupported'] + self.approximations
        return report


def write_render_test(path: Path, class_name: str, scale: float, font_map: Path | None,
                      scene_spec: Path | None, module: str) -> dict:
    """Create the render test once (project code), the scene test and the harness (tool code)."""
    result = {'path': str(path), 'created': False}
    harness = path.parent / 'Support' / HARNESS.name
    if not harness.exists() or harness.read_bytes() != HARNESS.read_bytes():
        harness.parent.mkdir(parents=True, exist_ok=True)
        harness.write_bytes(HARNESS.read_bytes())
        result['harness_installed'] = str(harness)

    def relative(target: Path) -> str:
        return os.path.relpath(target.resolve(), path.parent.resolve()).replace(os.sep, '/')

    here = 'URL(fileURLWithPath: #filePath).deletingLastPathComponent()'
    fonts = (f'\n        try FidelityHarness.loadSourceFontMap({here}.appendingPathComponent({sw_string(relative(font_map))}).path)'
             if font_map is not None else '')
    imports = f"""import DesignFidelity
import SwiftUI
import XCTest
@testable import {module}
"""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(imports + f"""
// Fidelity render test (project code). Render the production screen: replace the
// scene with the view that composes it (overrides / onTap) and fixed data.
@MainActor
final class {path.stem}: XCTestCase {{
    func testSourceCanvas() throws {{{fonts}
        let output = FidelityHarness.outputPath("PAGE_RENDER_OUTPUT")
        let page = {class_name}Scene()
        try FidelityHarness.capturePage(output: output, width: {class_name}Design.size.width,
                                        height: {class_name}Design.size.height, top: {class_name}Design.top,
                                        bottom: {class_name}Design.bottom, scale: {n(scale)}, page: page)
        // iPhone SE / 15 / 15 Pro Max and two Android sizes, at 1.0x and ~1.3x text.
        try FidelityHarness.captureVariants(output: output, page: page)
    }}
}}
""", encoding='utf-8')
        result['created'] = True
    if scene_spec is not None:
        scene_test = path.with_name(re.sub(r'FidelityTests?$', '', path.stem) + 'FidelitySceneTests.swift')
        scene_test.write_text('// GENERATED by design-fidelity/scripts/generate.py --target swiftui; do not edit.\n'
                              + imports + f"""
@MainActor
final class {scene_test.stem}: XCTestCase {{
    func testSceneObligations() throws {{{fonts}
        let spec = {here}.appendingPathComponent({sw_string(relative(scene_spec))}).path
        try FidelityHarness.checkScene(specPath: spec, top: {class_name}Design.top, bottom: {class_name}Design.bottom,
                                       scene: {class_name}Scene())
    }}
}}
""", encoding='utf-8')
        result['scene_test'] = str(scene_test)
    return result


def emit(model: SceneModel, ctx: dict) -> dict:
    children = model.build()
    emitter = SwiftUIEmitter(model)
    code = emitter.swift(children)
    report = emitter.report()
    render_test = ctx.get('render_test')
    report['scene_test'] = None
    if render_test is not None:
        scene_spec = ctx.get('scene_test') or render_test.parent / f'{model.class_name}.scene.g.json'
        from scene_test_codegen import write_native_scene_spec
        report['scene_test'] = write_native_scene_spec(model, model.class_name, scene_spec, backdrop=False)
        module = (ctx.get('options') or {}).get('module') or 'App'
        report['render_test'] = write_render_test(render_test, model.class_name,
                                                  float(model.plan.get('render_scale') or 4), ctx.get('font_map'),
                                                  scene_spec, module)
        report['scene_test']['runner'] = report['render_test'].get('scene_test')
    return {'code': code, 'report': report, 'asset_field': 'app_asset'}


def default_report_path(output: Path) -> Path:
    name = output.name
    for suffix in ('.g.swift', '.swift'):
        if name.endswith(suffix):
            return output.with_name(name[:-len(suffix)] + '.codegen.json')
    return output.with_suffix('.codegen.json')
