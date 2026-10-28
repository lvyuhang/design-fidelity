"""Deterministic codegen: source fields become primitive calls, never guesses."""
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from generate_flutter import generate, parse_color, num  # noqa: E402
from dart_tools import dart_syntax_errors  # noqa: E402

RECT = [{'point': {'x': x, 'y': y}, 'curveFrom': {'x': x, 'y': y}, 'curveTo': {'x': x, 'y': y},
         'hasCurveFrom': False, 'hasCurveTo': False, 'cornerRadius': 12}
        for x, y in ((0, 0), (1, 0), (1, 1), (0, 1))]
OVAL = [{'point': p, 'curveFrom': p, 'curveTo': p, 'hasCurveFrom': True, 'hasCurveTo': True,
         'cornerRadius': 0} for p in ({'x': .5, 'y': 0}, {'x': 1, 'y': .5},
                                      {'x': .5, 'y': 1}, {'x': 0, 'y': .5})]
TRIANGLE = [{'point': {'x': 0, 'y': 1}, 'hasCurveFrom': False, 'hasCurveTo': False},
            {'point': {'x': .5, 'y': 0}, 'hasCurveFrom': False, 'hasCurveTo': False},
            {'point': {'x': 1, 'y': 1}, 'hasCurveFrom': False, 'hasCurveTo': False}]


def color(value):
    return {'r': 0, 'g': 0, 'b': 0, 'a': 0, 'value': value}


def node(key, kind, bounds, parent='ART', order=0, name=None, text=None, raw=None, **extra):
    x, y, w, h = bounds
    result = {'node_id': key, 'parent_id': parent, 'source_order': order, 'name': name or key,
              'node_type': kind, 'bounds': {'x': x, 'y': y, 'width': w, 'height': h},
              'text': text, 'raw_style': raw or {}, 'asset_ids': []}
    result.update(extra)
    return result


def text_node(key, bounds, text, order, align=4, behaviour=0, runs=None, weight=400):
    family = 'PingFangSC-Semibold' if weight == 600 else 'PingFangSC-Regular'
    runs = runs or [{'text': text, 'font_family': family, 'font_weight': weight,
                     'font_size': 14, 'line_height': 20, 'letter_spacing': 0,
                     'color': 'rgba(34,36,42,1)'}]
    return node(key, 'text', bounds, order=order, text=text,
                raw={'textBehaviour': behaviour, 'opacity': 100,
                     'font': {'textAlignment': align, 'styles': [{'alignment': align}]}},
                text_spec={'text_runs': runs, 'base_style': runs[0]})


def fixture():
    nodes = [
        node('ART', 'artboard-group', (0, 0, 375, 812), parent=None,
             raw={'hasBackgroundColor': True, 'fills': [{'type': 'color', 'fillType': 0,
                  'opacity': 1, 'isEnabled': True, 'color': color('rgba(255,254,250,1)')}]}),
        node('BG', 'shape', (0, 0, 375, 812), order=1, raw={'points': RECT[:0] or [
            dict(p, cornerRadius=0) for p in RECT], 'fills': [{'type': 'color', 'fillType': 0,
            'opacity': 1, 'isEnabled': True, 'color': color('rgba(255,255,255,1)')}], 'opacity': 100}),
        node('CARD', 'shape', (16, 100, 343, 146), order=2, raw={
            'points': RECT, 'opacity': 100,
            'fills': [{'type': 'color', 'fillType': 0, 'opacity': 1, 'isEnabled': True,
                       'color': color('rgba(255,253,249,0.85)')}],
            'borders': [{'position': '内边框', 'thickness': 1, 'isEnabled': True, 'type': 'color',
                         'fillType': 0, 'opacity': 1, 'color': color('rgba(238,220,196,1)')}],
            'shadow': [{'type': '外阴影', 'blurRadius': 10, 'offsetX': 0, 'offsetY': 1, 'spread': 0,
                        'isEnabled': True, 'color': color('rgba(216,155,71,0.08)')}]}),
        text_node('LABEL', (32, 120, 56, 20), '提现金额', 3),
        text_node('TITLE', (172, 55, 32, 22), '提现', 4, align=2, weight=600),
        text_node('MIXED', (32, 150, 120, 20), '共 3 件', 5, runs=[
            {'text': '共 ', 'font_family': 'PingFangSC-Regular', 'font_weight': 400, 'font_size': 14,
             'line_height': 20, 'color': 'rgba(34,36,42,1)'},
            {'text': '3', 'font_family': 'PingFangSC-Semibold', 'font_weight': 600, 'font_size': 16,
             'line_height': 20, 'color': 'rgba(188,145,74,1)'},
            {'text': ' 件', 'font_family': 'PingFangSC-Regular', 'font_weight': 400, 'font_size': 14,
             'line_height': 20, 'color': 'rgba(34,36,42,1)'}]),
        text_node('EDIT', (301, 120, 24, 17), '修改', 6),
        node('DOT', 'shape', (32, 515, 5, 5), order=7, raw={'points': OVAL, 'fills': [{
            'type': 'color', 'fillType': 0, 'opacity': 1, 'isEnabled': True,
            'color': color('#DAC8A3')}]}),
        node('ARROW', 'shape', (16, 61, 6, 12), order=8, raw={'points': TRIANGLE, 'isClosed': False,
             'borders': [{'position': '中心边框', 'thickness': 1.5, 'isEnabled': True,
                          'type': 'color', 'fillType': 0, 'color': color('rgba(0,0,0,1)')}],
             'borderOptions': {'lineCapStyle': 1, 'lineJoinStyle': 1, 'dashPattern': []},
             'isFlippedHorizontal': True}),
        node('PHOTO', 'layer-group', (189, 97, 170, 140), order=9),
        node('MASK', 'shape', (189, 97, 170, 140), parent='PHOTO', order=10,
             raw={'points': RECT, 'hasClippingMask': 1, 'fills': []}),
        node('IMG', 'bitmap', (189, 104, 170, 133), parent='PHOTO', order=11, raw={'opacity': 50}),
        node('ICON', 'shape', (35, 261, 22, 22), order=12, raw={'points': RECT}, asset_ids=['ICON:image']),
        node('GLASS', 'shape', (14, 735, 347, 56), order=13, raw={
            'points': RECT, 'fills': [{'type': 'color', 'fillType': 0, 'opacity': 1, 'isEnabled': True,
                                       'color': color('rgba(255,255,255,0.7)')}],
            'blur': {'blurType': 3, 'radius': 20, 'saturation': 1, 'isEnabled': True}}),
        node('TILT', 'shape', (100, 600, 20, 20), order=14, raw={
            'points': RECT, 'rotation': 15, 'fills': [{'type': 'color', 'fillType': 0, 'opacity': 1,
                                                     'isEnabled': True, 'color': color('#000000')}]}),
        node('GHOST', 'shape', (0, 300, 10, 10), order=15, effective_source_visible=False,
             raw={'points': RECT, 'fills': [{'type': 'color', 'isEnabled': True, 'color': color('#FF0000')}]}),
        node('STATUS', 'layer-group', (0, 0, 375, 44), order=16, name='Bars/Status Bars/iPhone/Light'),
        text_node('TIME', (21, 14, 54, 18), '9:41', 17),
        node('WIFI', 'shape', (316, 17, 15, 11), parent='STATUS', order=18, raw={}),
        node('HOME', 'layer-group', (121, 778, 134, 34), order=19, name='Bars/Home Indicators/iPhone'),
        node('BAR', 'shape', (121, 799, 134, 5), parent='HOME', order=20, raw={'points': RECT,
             'fills': [{'type': 'color', 'isEnabled': True, 'color': color('#000000')}]}),
        node('BUTTON', 'shape', (28, 706, 320, 50), order=21, raw={
            'points': [dict(p, cornerRadius=25) for p in RECT],
            'fills': [{'type': 'gradient', 'fillType': 1, 'opacity': 1, 'isEnabled': True,
                       'gradient': {'type': 'linear', 'gradientType': 0, 'from': {'x': 0, 'y': .5},
                                    'to': {'x': 1, 'y': .5}, 'colorStops': [
                                        {'position': 0, 'color': color('rgba(230,181,94,1)')},
                                        {'position': 1, 'color': color('rgba(214,164,74,1)')}]}}]}),
        node('TABBAR', 'shape', (0, 762, 375, 50), order=22, raw={'points': RECT, 'fills': [
            {'type': 'color', 'isEnabled': True, 'color': color('#FFFFFF')}]}),
    ]
    nodes[17]['parent_id'] = 'STATUS'
    return {
        'snapshot_id': 'snap', 'resolved_version': 'ver', 'design_name': 'Fixture',
        'coordinate_space': 'source_canvas', 'coordinate_mapping': {'verified': True},
        'canvas': {'width': 375, 'height': 812}, 'total_nodes': len(nodes), 'nodes': nodes,
        'assets': [{'asset_id': 'ICON:image', 'node_id': 'ICON', 'kind': 'exported_asset'}],
    }


class GenerateFlutterTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / 'source.json').write_text(json.dumps(fixture(), ensure_ascii=False))
        from PIL import Image
        Image.new('RGBA', (96, 96), (0, 120, 255, 255)).save(self.root / 'icon.png')
        plan = {'snapshot_id': 'snap', 'resolved_version': 'ver',
                'assets': [{'asset_id': 'ICON:image', 'node_id': 'ICON', 'kind': 'exported_asset',
                            'path': str(self.root / 'icon.png'),
                            'export_rect': [34, 260, 24, 24], 'layout_rect': [35, 261, 22, 22]}],
                'fonts': [{'source_family': 'PingFangSC-Regular', 'weight': 400,
                           'runtime_family': 'SourcePingFang'},
                          {'source_family': 'PingFangSC-Semibold', 'weight': 600,
                           'runtime_family': 'SourcePingFang'}]}
        (self.root / 'plan.json').write_text(json.dumps(plan))
        self.app = self.root / 'app'
        self.report = self.run_generate()
        self.dart = (self.app / 'lib/fixture.g.dart').read_text()
        self.by_id = {n['node_id']: n for n in self.report['nodes']}

    def run_generate(self, output='lib/fixture.g.dart'):
        return generate([self.root / 'source.json'], self.root / 'plan.json', None, 'Fixture',
                        self.app / output, app_root=self.app, asset_dir='assets/lanhu/fixture',
                        render_test=self.app / 'test' / (Path(output).name.split('.')[0] + '_test.dart'))

    def test_every_visible_node_has_a_disposition(self):
        modes = {k: n['mode'] for k, n in self.by_id.items()}
        self.assertNotIn('not_emitted', modes.values())
        self.assertEqual(modes['GHOST'], 'hidden')
        self.assertEqual(modes['IMG'], 'missing_asset_placeholder')
        self.assertEqual(modes['ICON'], 'original_asset')
        self.assertEqual(modes['CARD'], 'native_exact')
        self.assertEqual(self.report['issues'], [])
        self.assertNotIn('GHOST', self.dart)

    def test_system_chrome_is_reserved_not_painted(self):
        kinds = {c['kind']: c for c in self.report['system_chrome']}
        self.assertEqual(set(kinds), {'statusBar', 'homeIndicator'})
        self.assertEqual(kinds['statusBar']['rect'], [0, 0, 375, 44])
        for key in ('STATUS', 'TIME', 'WIFI', 'HOME', 'BAR'):
            self.assertEqual(self.by_id[key]['mode'], 'system_chrome')
            self.assertNotIn(f"'{key}'", self.dart)
        decision = self.report['draft_node_decisions']['TIME']
        self.assertEqual(decision['mode'], 'excluded_with_reason')
        self.assertEqual(decision['exclusion']['kind'], 'system_chrome')

    def test_source_effects_use_primitives(self):
        card = self.section('CARD')
        self.assertIn('SourceRectShape.all(12)', card)
        self.assertIn('position: SourceBorderPosition.inside', card)
        self.assertIn('blurRadius: 10', card)
        self.assertIn('offset: Offset(0, 1)', card)
        self.assertIn('FixtureTokens.cD9FFFDF9', card)  # alpha from rgba value, not zero r/g/b
        self.assertIn('SourceOvalShape()', self.section('DOT'))
        arrow = self.section('ARROW')
        self.assertIn('closed: false', arrow)
        self.assertIn('cap: StrokeCap.round', arrow)
        self.assertIn('Transform.flip', arrow)
        glass = self.section('GLASS')
        self.assertIn('SourceBackdropBlur(', glass)
        self.assertIn('radius: 20', glass)
        self.assertIn('SourceFill.linear(', self.section('BUTTON'))
        self.assertEqual([u['feature'] for u in self.report['unsupported']], ['rotation'])

    def test_text_alignment_uses_appkit_codes_and_fonts_map(self):
        title = self.section('TITLE')
        self.assertIn('textAlign: TextAlign.center', title)
        self.assertIn("fontFamily: 'SourcePingFang'", self.dart)
        mixed = self.section('MIXED')
        self.assertIn('SourceText.rich(', mixed)
        self.assertEqual(mixed.count('SourceTextRun('), 3)

    def test_assets_are_placed_by_export_frame_and_installed(self):
        icon = self.section('ICON')
        self.assertIn('FixtureAssets.icon', icon)
        self.assertIn('exportRect: Rect.fromLTWH(-1, -1, 24, 24)', icon)
        self.assertTrue((self.app / 'assets/lanhu/fixture/icon.png').exists())
        self.assertIn("'assets/lanhu/fixture/icon.png'", self.dart)

    def test_masked_members_are_clipped_to_the_mask_shape(self):
        photo = self.method_body('PHOTO')
        self.assertIn('ClipPath(', photo)
        self.assertIn('SourceShapeClipper(', photo)
        self.assertIn("'IMG'", photo)

    def test_responsive_placement(self):
        self.assertRegex(self.positioned('CARD'), r'left: 16,\s*right: 16')
        self.assertRegex(self.positioned('TITLE'), r'Alignment.topCenter')
        self.assertRegex(self.positioned('EDIT'), r'right: 50')
        self.assertRegex(self.positioned('LABEL'), r'left: 32,\s*top: dy \+ 120,\s*child')
        self.assertRegex(self.positioned('BUTTON'), r'left: 28,\s*right: 27,\s*bottom: dyBottom \+ 56')
        self.assertRegex(self.positioned('TABBAR'),
                         r'left: 0,\s*right: 0,\s*bottom: dyBottom \+ 0,\s*height: 50')
        self.assertIn('Positioned.fill(', self.positioned('BG'))
        decisions = self.report['draft_node_decisions']
        self.assertEqual(decisions['EDIT']['anchor'], 'right',
                         'right-anchored auto text is probed on its right edge')
        self.assertNotIn('anchor', decisions['LABEL'])

    def test_safe_area_and_screen_height_adaptation(self):
        self.assertIn('static const EdgeInsets designPadding = EdgeInsets.only(top: 44, bottom: 34);',
                      self.dart)
        self.assertIn('MediaQuery.maybePaddingOf(context) ?? designPadding', self.dart)
        self.assertIn('final dy = padding.top - designPadding.top;', self.dart)
        self.assertIn('scrolls ? SingleChildScrollView(child: body) : body', self.dart)
        layout = self.report['layout']
        self.assertEqual(layout['design_padding'], {'top': 44, 'bottom': 34})
        self.assertEqual(set(layout['footer']), {'BUTTON', 'GLASS', 'TABBAR'}, 'floating nav bar included')
        decisions = self.report['draft_node_decisions']
        self.assertEqual(decisions['BUTTON']['vertical_anchor'], 'bottom')
        self.assertNotIn('vertical_anchor', decisions['CARD'])
        # Footers are painted outside the scrolling body, after it.
        body_end = self.dart.index('child: scrolls ? SingleChildScrollView')
        self.assertGreater(self.dart.index("'BUTTON'"), body_end)
        self.assertLess(self.dart.index("'CARD'"), body_end)
        self.assertNotIn('fillHeight', self.dart)

    def test_design_without_chrome_starts_below_the_device_status_bar(self):
        evidence = fixture()
        evidence['nodes'] = [n for n in evidence['nodes']
                             if n['node_id'] not in ('STATUS', 'TIME', 'WIFI', 'HOME', 'BAR')]
        evidence['total_nodes'] = len(evidence['nodes'])
        (self.root / 'source.json').write_text(json.dumps(evidence, ensure_ascii=False))
        report = self.run_generate('lib/plain.g.dart')
        text = (self.app / 'lib/plain.g.dart').read_text()
        self.assertIn('designPadding = EdgeInsets.only(top: 0, bottom: 0)', text)
        self.assertEqual(set(report['layout']['footer']), {'GLASS', 'TABBAR'}, 'BUTTON is 56px up: body')

    def test_platform_fonts_come_from_the_font_map(self):
        (self.root / 'fonts.json').write_text(json.dumps({'fonts': {
            'PingFangSC-Regular@400': {'path': 'a.otf', 'runtime_family': 'SourcePingFang',
                                       'ios': None, 'android': 'NotoSansSC'},
            'PingFangSC-Semibold@600': {'path': 'b.otf', 'runtime_family': 'SourcePingFang'}}}))
        generate([self.root / 'source.json'], self.root / 'plan.json', self.root / 'fonts.json',
                 'Fixture', self.app / 'lib/fonts.g.dart', app_root=self.app)
        text = (self.app / 'lib/fonts.g.dart').read_text()
        self.assertIn("fontFamily: sourceFontFamily('SourcePingFang', android: 'NotoSansSC', "
                      "ios: SourceFonts.system)", text)
        self.assertIn("fontFamily: 'SourcePingFang',", text, 'unmapped platforms keep the family')
        errors = dart_syntax_errors(self.app / 'lib/fonts.g.dart')
        if errors is not None:
            self.assertEqual(errors, '')

    def test_render_test_uses_design_padding_and_flags_old_tests(self):
        test = (self.app / 'test/fixture_test.dart').read_text()
        self.assertIn('padding: FixtureScene.designPadding', test)
        self.assertIn('captureResponsiveVariants(tester, page: page, output: output)', test)
        (self.app / 'test/fixture_test.dart').write_text('captureFidelityPage(); captureResponsiveVariants(height: 1)')
        report = generate([self.root / 'source.json'], self.root / 'plan.json', None, 'Fixture',
                          self.app / 'lib/fixture.g.dart', app_root=self.app,
                          render_test=self.app / 'test/fixture_test.dart')
        self.assertIn('render_test_outdated', {i['kind'] for i in report['issues']})

    def test_tokens_hold_every_color_literal(self):
        body = self.dart.split('abstract final class FixtureAssets')[1]
        self.assertNotRegex(body, r'Color\(0x')
        self.assertIn('static const Color cFFFFFEFA', self.dart)

    def test_output_is_deterministic(self):
        again = self.run_generate('lib/again.g.dart')
        self.assertEqual(again['output_sha256'], self.report['output_sha256'])

    def test_generated_dart_parses(self):
        errors = dart_syntax_errors(self.app / 'lib/fixture.g.dart')
        if errors is None:
            self.skipTest('no Dart syntax checker (set FIDELITY_DART_SYNTAX or install dart)')
        self.assertEqual(errors, '')

    def test_rejects_plan_from_another_snapshot(self):
        plan = json.loads((self.root / 'plan.json').read_text())
        plan['snapshot_id'] = 'other'
        (self.root / 'plan.json').write_text(json.dumps(plan))
        with self.assertRaisesRegex(ValueError, 'snapshot_id'):
            self.run_generate('lib/x.g.dart')

    def test_value_helpers(self):
        self.assertEqual(parse_color('rgba(34,36,42,1.000000)'), (34, 36, 42, 1.0))
        self.assertEqual(parse_color({'r': 0, 'g': 0, 'b': 0, 'a': 0, 'value': '#BC914A'}),
                         (188, 145, 74, 1.0))
        self.assertEqual(num(21.9999170683794), '21.9999')
        self.assertEqual(num(-0.0), '0')

    # helpers -----------------------------------------------------------------
    def section(self, key):
        start = self.dart.index(f"'{key}'")
        end = self.dart.find('_node(', start + 1)
        return self.dart[start:end if end > 0 else None]

    def positioned(self, key):
        index = self.dart.index(f"'{key}'")
        start = self.dart.rfind('Positioned', 0, index)
        return self.dart[start:index]

    def method_body(self, key):
        short = re.sub(r'[^0-9A-Za-z]', '', key)[:8]
        start = self.dart.index(f'Widget _g{short}(')
        end = self.dart.find('\n  Widget ', start + 1)
        return self.dart[start:end if end > 0 else None]


if __name__ == '__main__':
    unittest.main()
