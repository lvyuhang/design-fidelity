"""Compose emitter: scene model -> Kotlin on the `design.fidelity` Compose primitives (preview)."""
from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path
from typing import Any

from scene_model import Expr, N, SceneModel, num

GENERATOR_VERSION = 1
HARNESS = Path(__file__).resolve().parents[1] / 'assets' / 'compose' / 'FidelityHarness.kt'
TEXT_KINDS = {'text', 'rich'}
WRAPPERS = {'opacity', 'flip', 'layer_blur'}
ALIGN = {'left': 'TextAlign.Left', 'right': 'TextAlign.Right', 'center': 'TextAlign.Center',
         'justify': 'TextAlign.Justify'}
CAPS = {'butt': 'StrokeCap.Butt', 'round': 'StrokeCap.Round', 'square': 'StrokeCap.Square'}
JOINS = {'miter': 'StrokeJoin.Miter', 'round': 'StrokeJoin.Round', 'bevel': 'StrokeJoin.Bevel'}
DENSITY_QUALIFIER = {1: 'mdpi', 2: 'xhdpi', 3: 'xxhdpi', 4: 'xxxhdpi'}


def kt_string(value: str) -> str:
    escaped = (value.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$')
               .replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t'))
    return f'"{escaped}"'


def f(value: float) -> str:
    return f'{num(value)}f'


def kotlin_package(path: Path) -> str:
    parts = path.resolve().parent.parts
    for marker in ('kotlin', 'java'):
        if marker in parts:
            index = len(parts) - 1 - parts[::-1].index(marker)
            package = parts[index + 1:]
            if package and all(re.fullmatch(r'[A-Za-z_]\w*', p) for p in package):
                return '.'.join(package)
    return 'fidelity.generated'


def asset_runtime_path(app_asset: str) -> str:
    """`app/src/main/assets/design/x.png` -> `design/x.png` (AssetManager path)."""
    marker = '/assets/'
    text = '/' + app_asset.replace(os.sep, '/')
    return text.split(marker, 1)[1] if marker in text else app_asset


class Block:
    """A Kotlin call with optional named args and a trailing lambda of children."""

    def __init__(self, head: str, children: list | None = None, param: str | None = None):
        self.head, self.children, self.param = head, children, param


class ComposeEmitter:
    def __init__(self, model: SceneModel):
        self.m = model
        self.cls = model.class_name
        self.uses_max = False
        self.approximations: list[dict] = []
        self.current: str | None = None

    def note(self, feature: str, detail: str) -> None:
        self.approximations.append({'node_id': self.current, 'feature': feature, 'detail': detail})

    # values
    def color(self, c: N) -> str:
        return f'{self.cls}Tokens.{c["name"]}'

    def offset(self, point) -> str:
        return f'Offset({f(point[0])}, {f(point[1])})'

    def shape(self, s: N | None) -> str | None:
        if s is None:
            return None
        if s.kind == 'rect':
            radii = s['radii']
            if radii is None:
                return 'SourceRectShape()'
            if isinstance(radii, tuple) and radii[0] == 'all':
                return f'SourceRectShape({f(radii[1])})'
            return 'SourceRectShape(listOf(' + ', '.join(f(r) for r in radii) + '))'
        if s.kind == 'oval':
            return 'SourceOvalShape'
        points = []
        for p in s['points']:
            extra = ''
            if p['curve_from'] is not None:
                extra += f', curveFrom = {self.offset(p["curve_from"])}'
            if p['curve_to'] is not None:
                extra += f', curveTo = {self.offset(p["curve_to"])}'
            points.append(f'SourcePathPoint({self.offset(p["point"])}{extra})')
        args = ['points = listOf(' + ', '.join(points) + ')']
        if not s['closed']:
            args.append('closed = false')
        if s['even_odd']:
            args.append('evenOdd = true')
        return 'SourcePathShape(' + ', '.join(args) + ')'

    def fill(self, fl: N) -> str:
        opacity = f', opacity = {f(fl["opacity"])}' if fl['opacity'] is not None else ''
        if fl.kind == 'linear':
            stops = ', '.join(f'SourceGradientStop({f(pos)}, {self.color(c)})' for pos, c in fl['stops'])
            return (f'SourceFill.Linear(SourceLinearGradient({self.offset(fl["start"])}, {self.offset(fl["end"])}, '
                    f'listOf({stops})){opacity})')
        return f'SourceFill.Solid({self.color(fl["color"])}{opacity})'

    def border(self, b: N) -> str:
        args = [f'thickness = {f(b["thickness"])}', f'fill = {self.fill(b["fill"])}']
        if b['position'] != 'center':
            args.append(f'position = SourceBorderPosition.{b["position"].capitalize()}')
        if b['cap']:
            args.append(f'cap = {CAPS[b["cap"]]}')
        if b['join']:
            args.append(f'join = {JOINS[b["join"]]}')
        if b['dash']:
            args.append('dash = listOf(' + ', '.join(f(v) for v in b['dash']) + ')')
        return 'SourceBorder(' + ', '.join(args) + ')'

    def shadow(self, s: N) -> str:
        args = [f'color = {self.color(s["color"])}']
        if s['offset']:
            args.append(f'offset = {self.offset(s["offset"])}')
        if s['blur']:
            args.append(f'blurRadius = {f(s["blur"])}')
        if s['spread']:
            args.append(f'spread = {f(s["spread"])}')
        if s['inner']:
            args.append('inner = true')
        return 'SourceShadow(' + ', '.join(args) + ')'

    def value(self, v: Any) -> str:
        if isinstance(v, Expr):
            expr = f'insets.{v.var} + {f(v.value)}'
            if v.floor is not None:
                self.uses_max = True
                return f'max({f(v.floor)}, {expr})'
            return expr
        return f(v)

    @staticmethod
    def is_text(n: N) -> bool:
        while n.kind in WRAPPERS:
            n = n['child']
        return n.kind in TEXT_KINDS

    # elements -> Blocks
    def element(self, n: N, fill: bool = True) -> Block:
        k = n.kind
        if k == 'box':
            shape = self.shape(n['shape'])
            args = []
            if shape:
                args.append(f'shape = {shape}')
            if n['fills']:
                args.append('fills = listOf(' + ', '.join(self.fill(x) for x in n['fills']) + ')')
            if n['borders']:
                args.append('borders = listOf(' + ', '.join(self.border(x) for x in n['borders']) + ')')
            if n['shadows']:
                args.append('shadows = listOf(' + ', '.join(self.shadow(x) for x in n['shadows']) + ')')
            if n['opacity'] is not None:
                args.append(f'opacity = {f(n["opacity"])}')
            if shape and n['shape'].kind == 'path' and any(s['spread'] and s['spread'] < 0 for s in n['shadows']):
                self.note('negative_spread_on_path', 'drawn without spread')
            return Block('SourceBox(' + ', '.join(args) + ')')
        if k in TEXT_KINDS:
            named = [f'style = {self.cls}Tokens.{n["style"]["name"]}']
            if n['align'] != 'left':
                named.append(f'align = {ALIGN[n["align"]]}')
            if n['wrap']:
                named.append('wrap = true')
            if k == 'text':
                return Block(f'SourceText({kt_string(n["text"])}, ' + ', '.join(named) + ')')
            runs = ', '.join(f'{kt_string(t)} to {self.cls}Tokens.{s["name"]}' for t, s in n['runs'])
            return Block(f'SourceText(runs = listOf({runs}), ' + ', '.join(named) + ')')
        if k == 'asset':
            rect = n['export_rect']
            extra = f', exportRect = SourceRect({", ".join(f(v) for v in rect)})' if rect else ''
            return Block(f'SourceAsset({self.cls}Assets.{n["ident"]}{extra})')
        if k == 'placeholder':
            return Block(f'SourcePlaceholder({kt_string(n["node_id"])})')
        if k in ('overlay', 'stack'):
            return Block('Box(Modifier.fillMaxSize())', [self.element(c, True) for c in n['children']])
        if k == 'fill':
            return Block('Box(Modifier.fillMaxSize())', [self.element(n['child'], True)])
        if k == 'placed':
            args = ', '.join(f'{name} = {self.value(v)}' for name, v in n['args'] if v is not None)
            return Block(f'Box(Modifier.sourcePlaced({args}))', [self.element(n['child'], True)])
        if k == 'align_top_center':
            return Block('Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter)',
                         [self.element(n['child'], True)])
        if k == 'sized':
            return Block(f'Box(Modifier.width({num(n["width"])}.dp))', [self.element(n['child'], True)])
        if k == 'opacity':
            return Block(f'SourceOpacity({f(n["value"])}{"" if fill else ", fill = false"})',
                         [self.element(n['child'], fill)])
        if k == 'backdrop':
            self.note('backdrop_blur', 'Compose cannot sample content behind a node; the blur is not drawn')
            shape = self.shape(n['shape'])
            args = [f'radius = {f(n["radius"])}']
            if shape:
                args.append(f'shape = {shape}')
            return Block('SourceBackdropBlur(' + ', '.join(args) + ')', [self.element(n['child'], True)])
        if k == 'layer_blur':
            return Block(f'SourceLayerBlur({f(n["radius"])}{"" if fill else ", fill = false"})',
                         [self.element(n['child'], fill)])
        if k == 'flip':
            args = [*(['x = true'] if n['x'] else []), *(['y = true'] if n['y'] else []),
                    *([] if fill else ['fill = false'])]
            return Block('SourceFlip(' + ', '.join(args) + ')', [self.element(n['child'], fill)])
        if k == 'clip':
            return Block(f'SourceClip({self.shape(n["shape"])})', [self.element(n['child'], True)])
        if k == 'node':
            child = n['child']
            previous, self.current = self.current, n['id']
            try:
                if child.kind == 'group_ref':
                    return Block(f'SourceNode({kt_string(n["id"])})', [Block(f'{child["method"]}()')])
                fill_node = not self.is_text(child)
                head = f'SourceNode({kt_string(n["id"])}{"" if fill_node else ", fill = false"})'
                return Block(head, [self.element(child, fill_node)])
            finally:
                self.current = previous
        raise TypeError(f'Unknown model node {k}')

    def render(self, block: Block, indent: int) -> list[str]:
        pad = ' ' * indent
        if block.children is None:
            return [pad + block.head]
        param = f' {block.param} ->' if block.param else ''
        lines = [f'{pad}{block.head} {{{param}']
        for child in block.children:
            lines += self.render(child, indent + 4)
        lines.append(pad + '}')
        return lines

    def text_spec(self, spec: dict) -> str:
        args = [f'family = {kt_string(spec["family"])}']
        if spec['platforms']:
            pairs = ', '.join(f'{kt_string(k)} to {"null" if v is None else kt_string(v)}'
                              for k, v in sorted(spec['platforms'].items()))
            args.append(f'platforms = mapOf({pairs})')
        args += [f'size = {f(spec["size"])}', f'weight = {spec["weight"]}']
        if spec['line_height']:
            args.append(f'lineHeight = {f(spec["line_height"])}')
        if spec['letter_spacing']:
            args.append(f'letterSpacing = {f(spec["letter_spacing"])}')
        args.append(f'color = {spec["color"]["name"]}')
        if spec['decoration']:
            args.append('decoration = TextDecoration.' + {'underline': 'Underline', 'lineThrough': 'LineThrough'}[spec['decoration']])
        return 'SourceTextSpec(' + ', '.join(args) + ')'

    def kotlin(self, children: list[N], package: str) -> str:
        m = self.m
        cls = self.cls
        width, height = m.canvas
        first = m.documents[0]
        body = [self.element(c) for c in children if not c.footer]
        footer = [self.element(c) for c in children if c.footer]
        groups = [(method, name, self.element(node)) for method, name, node in m.methods]
        lines = [
            '// GENERATED by design-fidelity/scripts/generate.py --target compose; do not edit.',
            f'// Source: {first.get("design_name") or ""} snapshot {first.get("snapshot_id")}',
            f'// version {first.get("resolved_version")}, canvas {num(width)}x{num(height)}.',
            '// Replace layers through `overrides` / wire actions through `onTap`.',
            '@file:Suppress("UNUSED_ANONYMOUS_PARAMETER", "FunctionName", "ObjectPropertyName")',
            '',
            f'package {package}',
            '',
            'import androidx.compose.foundation.layout.Box',
            'import androidx.compose.foundation.layout.fillMaxSize',
            'import androidx.compose.foundation.layout.fillMaxWidth',
            'import androidx.compose.foundation.layout.width',
            'import androidx.compose.runtime.Composable',
            'import androidx.compose.ui.Alignment',
            'import androidx.compose.ui.Modifier',
            'import androidx.compose.ui.geometry.Offset',
            'import androidx.compose.ui.graphics.Color',
            'import androidx.compose.ui.graphics.StrokeCap',
            'import androidx.compose.ui.graphics.StrokeJoin',
            'import androidx.compose.ui.text.style.TextAlign',
            'import androidx.compose.ui.text.style.TextDecoration',
            'import androidx.compose.ui.unit.dp',
            'import design.fidelity.*',
            *(['import kotlin.math.max'] if self.uses_max else []),
            '',
            f'object {cls}Tokens {{',
        ]
        for name, code in sorted(m.colors.items()):
            lines.append(f'    val {name} = Color(0x{code})')
        for name, spec in sorted(m.text_styles.values(), key=lambda item: item[0]):
            lines.append(f'    val {name} = {self.text_spec(spec)}')
        lines += ['}', '', f'object {cls}Assets {{']
        for ident, entry in sorted(m.asset_keys.items()):
            lines.append(f'    const val {ident} = {kt_string(asset_runtime_path(entry["app_asset"]))}')
        lines.append('    val all = listOf(' + ', '.join(sorted(m.asset_keys)) + ')')
        lines += ['}', '',
                  f'object {cls}Design {{',
                  f'    const val WIDTH = {f(width)}',
                  f'    const val HEIGHT = {f(height)}',
                  '    /** Safe-area insets drawn in the design (status bar / home indicator). */',
                  f'    const val TOP = {f(m.design_top)}',
                  f'    const val BOTTOM = {f(m.design_bottom)}',
                  '}', '',
                  '/** Full-screen page: give it the whole window and no extra system-bar padding. */',
                  '@Composable',
                  f'fun {cls}Scene(',
                  '    overrides: Map<String, @Composable () -> Unit> = emptyMap(),',
                  '    onTap: Map<String, () -> Unit> = emptyMap(),',
                  '    adaptSafeArea: Boolean = true,',
                  ') {',
                  '    SourceScene(',
                  f'        designWidth = {cls}Design.WIDTH,',
                  f'        designHeight = {cls}Design.HEIGHT,',
                  f'        designTop = {cls}Design.TOP,',
                  f'        designBottom = {cls}Design.BOTTOM,',
                  '        adaptSafeArea = adaptSafeArea,',
                  '        overrides = overrides,',
                  '        onTap = onTap,']
        if footer:
            lines.append('        footer = { insets ->')
            for block in footer:
                lines += self.render(block, 12)
            lines.append('        },')
        lines.append('    ) { insets ->')
        for block in body:
            lines += self.render(block, 8)
        lines += ['    }', '}']
        for method, name, element in groups:
            lines += ['', f'/** {name.replace("*/", "* /")} */' if name else '/** group */', '@Composable',
                      f'private fun {method}() {{']
            lines += self.render(element, 4)
            lines.append('}')
        lines.append('')
        return '\n'.join(lines)

    def report(self) -> dict:
        report = self.m.report('generate.py --target compose', GENERATOR_VERSION, asset_field='app_asset')
        nodes = copy.deepcopy(report['nodes'])
        for entry in nodes:
            if 'primitive' in entry:
                entry['primitive'] = {'box': 'SourceBox', 'text': 'SourceText'}.get(entry['primitive'], entry['primitive'])
        report['nodes'] = nodes
        report['unsupported'] = report['unsupported'] + self.approximations
        return report


def gradle_target(test: Path, app_root: Path | None) -> tuple[str, str]:
    """(':module', 'TestClass') for a test file under <module>/src/test/..."""
    rel = test.resolve()
    if app_root is not None:
        try:
            rel = test.resolve().relative_to(app_root.resolve())
        except ValueError:
            pass
    parts = rel.parts
    module = ':' + ':'.join(parts[:parts.index('src')]) if 'src' in parts and parts.index('src') > 0 else ':app'
    return module, test.stem


def module_dir(test: Path) -> Path:
    parts = test.resolve().parts
    return Path(*parts[:parts.index('src')]) if 'src' in parts else test.resolve().parent


def write_render_test(path: Path, app_root: Path | None, package: str, class_name: str, scale: float,
                      font_map: Path | None, scene_spec: Path | None) -> dict:
    """Create the render and scene tests once (project code); keep the harness in sync."""
    result = {'path': str(path), 'created': False}
    test_package = kotlin_package(path)
    harness = path.parent / 'support' / HARNESS.name
    # Tool code, kept in sync; its package follows the test directory.
    source = HARNESS.read_text(encoding='utf-8').replace('package fidelity.support',
                                                         f'package {test_package}.support', 1)
    if not harness.exists() or harness.read_text(encoding='utf-8') != source:
        harness.parent.mkdir(parents=True, exist_ok=True)
        harness.write_text(source, encoding='utf-8')
        result['harness_installed'] = str(harness)
    module = module_dir(path)
    fonts = ''
    if font_map is not None:
        relative = os.path.relpath(font_map.resolve(), module).replace(os.sep, '/')
        fonts = f'\n        FidelityHarness.loadSourceFontMap({kt_string(relative)})'
    qualifier = DENSITY_QUALIFIER.get(round(scale), 'xxxhdpi')
    header = f"""package {test_package}

import androidx.compose.runtime.Composable
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import {test_package}.support.FidelityHarness
import {package}.{class_name}Design
import {package}.{class_name}Scene
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode
"""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(header + f"""
// Fidelity render test (project code). Render the production screen: replace the
// scene with the composable that composes it (overrides / onTap) and fixed data.
@RunWith(AndroidJUnit4::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = [34], qualifiers = "w430dp-h932dp-{qualifier}")
class {path.stem} {{
    @get:Rule val compose = createComposeRule()

    @Test fun sourceCanvas() {{{fonts}
        val output = FidelityHarness.outputPath("PAGE_RENDER_OUTPUT")
        val page: @Composable () -> Unit = {{ {class_name}Scene() }}
        FidelityHarness.capturePage(
            compose, output, {class_name}Design.WIDTH, {class_name}Design.HEIGHT,
            {class_name}Design.TOP, {class_name}Design.BOTTOM, page,
        )
        // iPhone SE / 15 / 15 Pro Max and two Android sizes, at 1.0x and 1.3x text.
        FidelityHarness.captureVariants(compose, output, page = page)
    }}
}}
""", encoding='utf-8')
        result['created'] = True
    if scene_spec is not None:
        scene_test = path.with_name(path.stem.replace('FidelityTest', '') + 'FidelitySceneTest.kt')
        spec_rel = os.path.relpath(scene_spec.resolve(), module).replace(os.sep, '/')
        scene_test.write_text(f"""// GENERATED by design-fidelity/scripts/generate.py --target compose; do not edit.
{header}
@RunWith(AndroidJUnit4::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = [34], qualifiers = "w430dp-h932dp-{qualifier}")
class {scene_test.stem} {{
    @get:Rule val compose = createComposeRule()

    @Test fun sceneObligations() {{{fonts}
        FidelityHarness.checkScene(
            compose, {kt_string(spec_rel)}, {class_name}Design.TOP, {class_name}Design.BOTTOM,
        ) {{ {class_name}Scene() }}
    }}
}}
""", encoding='utf-8')
        result['scene_test'] = str(scene_test)
    return result


def emit(model: SceneModel, ctx: dict) -> dict:
    output: Path = ctx['output']
    app_root: Path | None = ctx.get('app_root')
    package = (ctx.get('options') or {}).get('package') or kotlin_package(output)
    children = model.build()
    emitter = ComposeEmitter(model)
    code = emitter.kotlin(children, package)
    report = emitter.report()
    report['kotlin_package'] = package
    render_test = ctx.get('render_test')
    report['scene_test'] = None
    scene_spec = None
    if render_test is not None:
        scene_spec = ctx.get('scene_test') or render_test.parent / f'{model.class_name}.scene.g.json'
        from scene_test_codegen import write_native_scene_spec
        report['scene_test'] = write_native_scene_spec(model, model.class_name, scene_spec, backdrop=False)
        report['render_test'] = write_render_test(render_test, app_root, package, model.class_name,
                                                  float(model.plan.get('render_scale') or 4), ctx.get('font_map'),
                                                  scene_spec)
        report['scene_test']['runner'] = report['render_test'].get('scene_test')
    return {'code': code, 'report': report, 'asset_field': 'app_asset'}


def default_report_path(output: Path) -> Path:
    name = output.name
    for suffix in ('.g.kt', '.kt'):
        if name.endswith(suffix):
            return output.with_name(name[:-len(suffix)] + '.codegen.json')
    return output.with_suffix('.codegen.json')


_ = json
