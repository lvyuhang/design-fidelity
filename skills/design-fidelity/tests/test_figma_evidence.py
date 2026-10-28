"""Figma REST -> canonical evidence, then the unchanged prepare/generate path."""
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[0] / 'scripts'
sys.path[:0] = [str(SCRIPTS), str(HERE)]
import figma_evidence as fe  # noqa: E402
import figma_fixture  # noqa: E402
from evidence_schema import validate  # noqa: E402
from dart_tools import dart_syntax_errors  # noqa: E402


def png(width, height, color=(0, 120, 255, 255)):
    from PIL import Image
    buffer = io.BytesIO()
    Image.new('RGBA', (width, height), color).save(buffer, 'PNG')
    return buffer.getvalue()


class PathTests(unittest.TestCase):
    def test_url(self):
        self.assertEqual(fe.parse_url('https://www.figma.com/design/AbC123/Name?node-id=12-34&t=x'),
                         ('AbC123', '12:34'))
        with self.assertRaises(ValueError):
            fe.parse_url('https://www.figma.com/design/AbC123/Name')

    def test_svg_path_to_unit_points(self):
        sub = fe.parse_path('M0 0L10 0C10 5 5 10 0 10L0 0Z')
        self.assertEqual(len(sub), 1)
        points, closed = fe.points_from_path(sub[0], 10, 10)
        self.assertTrue(closed)
        self.assertEqual(len(points), 3)  # duplicate closing point dropped
        self.assertEqual(points[1]['curveFrom'], {'x': 1.0, 'y': 0.5})
        self.assertEqual(points[2]['curveTo'], {'x': 0.5, 'y': 1.0})
        self.assertTrue(points[1]['hasCurveFrom'] and points[2]['hasCurveTo'])
        quad, _ = fe.points_from_path(fe.parse_path('M0 0Q10 0 10 10')[0], 10, 10)
        self.assertAlmostEqual(quad[0]['curveFrom']['x'], 2 / 3)
        self.assertEqual(len(fe.parse_path('M0 0L1 1ZM2 2L3 3Z')), 2)
        hv, _ = fe.points_from_path(fe.parse_path('M0 0H10V10')[0], 10, 10)
        self.assertEqual([p['point'] for p in hv], [{'x': 0, 'y': 0}, {'x': 1, 'y': 0}, {'x': 1, 'y': 1}])


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.doc = fe.convert(figma_fixture.response(), 'KEY', '1:2')
        self.by_id = {n['node_id']: n for n in self.doc['nodes']}

    def raw(self, key):
        return self.by_id[key]['raw_style']

    def test_identity_version_and_schema(self):
        self.assertEqual(self.doc['snapshot_id'], 'figma:KEY:1:2@4242')
        self.assertEqual(self.doc['resolved_version'], '4242')
        self.assertEqual(self.doc['canvas'], {'width': 375.0, 'height': 812.0})
        self.assertEqual(validate(self.doc), [])
        self.assertEqual(self.doc['total_nodes'], len(self.doc['nodes']))

    def test_coordinates_are_frame_relative(self):
        self.assertEqual(self.by_id['1:2']['bounds'], {'x': 0.0, 'y': 0.0, 'width': 375.0, 'height': 812.0})
        self.assertEqual(self.by_id['1:30']['bounds'], {'x': 32.0, 'y': 515.0, 'width': 6.0, 'height': 6.0})
        self.assertTrue(self.raw('1:2')['hasBackgroundColor'])

    def test_styled_clipping_frame_becomes_shadow_background_mask_and_group(self):
        group, bg, shadow = self.by_id['1:20'], self.by_id['1:20#bg'], self.by_id['1:20#shadow']
        self.assertEqual(group['node_type'], 'layer-group')
        self.assertNotIn('fills', group['raw_style'])
        self.assertEqual(bg['parent_id'], '1:20')
        self.assertEqual(bg['raw_style']['hasClippingMask'], 1)
        self.assertEqual(bg['raw_style']['radius'], [12.0])
        self.assertEqual(bg['raw_style']['borders'][0]['position'], 'inside')
        self.assertNotIn('shadow', bg['raw_style'])
        self.assertEqual(shadow['raw_style']['shadow'][0]['blurRadius'], 10.0)
        self.assertNotIn('fills', shadow['raw_style'])
        self.assertLess(shadow['source_order'], bg['source_order'])
        children = [n['source_order'] for n in self.doc['nodes'] if n['parent_id'] == '1:20' and '#' not in n['node_id']]
        self.assertGreater(min(children), bg['source_order'])
        self.assertEqual(group['figma_layout']['layoutMode'], 'VERTICAL')

    def test_paints_effects_and_geometry(self):
        fill = self.raw('1:90')['fills'][0]
        self.assertEqual(fill['gradient']['from'], {'x': 0, 'y': 0.5})
        self.assertEqual(fill['gradient']['colorStops'][1]['color']['value'], 'rgba(214,164,74,1)')
        self.assertEqual(self.raw('1:70')['blur'], {'isEnabled': True, 'radius': 20.0, 'blurType': 3, 'saturation': 1})
        self.assertTrue(self.raw('1:30')['points'][0]['hasCurveFrom'])  # ellipse
        self.assertEqual(len(self.raw('1:31')['points']), 3)
        self.assertTrue(self.raw('1:31')['isClosed'])
        line = self.by_id['1:60']
        self.assertEqual(line['bounds'], {'x': 16.0, 'y': 599.5, 'width': 343.0, 'height': 1.0})
        self.assertEqual(line['raw_style']['fills'][0]['color']['value'], 'rgba(241,237,225,1)')

    def test_text_runs_alignment_and_behaviour(self):
        amount = self.by_id['1:22']
        self.assertEqual(amount['text'], '¥280')
        runs = amount['text_spec']['text_runs']
        self.assertEqual([(r['text'], r['font_size']) for r in runs], [('¥', 14.0), ('280', 20.0)])
        self.assertEqual(amount['text_spec']['base_style']['font_size'], 20.0)
        self.assertEqual(runs[1]['font_family'], 'PingFangSC-Semibold')
        self.assertEqual(runs[0]['color'], 'rgba(34,36,42,1)')
        self.assertEqual(amount['raw_style']['textBehaviour'], 0)
        self.assertEqual(self.raw('1:21')['font']['textAlignment'], 0)

    def test_exports_visibility_and_chrome(self):
        reasons = {a['node_id']: a['reason'] for a in self.doc['assets']}
        self.assertEqual(reasons, {'1:40': 'vector icon', '1:50': 'image fill'})
        icon = next(a for a in self.doc['assets'] if a['node_id'] == '1:40')
        self.assertEqual(icon['render_bounds'], icon['source_size'] | {'x': 331.0, 'y': 128.0})
        self.assertEqual(self.by_id['1:50']['node_type'], 'bitmap')
        self.assertFalse(self.by_id['1:80']['effective_source_visible'])
        from system_chrome import detect_system_chrome
        nodes = {n['node_id']: n for n in self.doc['nodes']}
        kinds = {c['node_id']: c['kind'] for c in detect_system_chrome(nodes, (375, 812))}
        self.assertEqual(kinds, {'1:10': 'statusBar', '1:99': 'homeIndicator'})

    def test_unrepresentable_styles_are_reported(self):
        response = figma_fixture.response()
        frame = response['nodes']['1:2']['document']
        frame['children'][2]['fills'][0]['blendMode'] = 'MULTIPLY'
        frame['children'][7]['effects'].append({'type': 'LAYER_BLUR', 'radius': 4, 'visible': True})
        frame['children'][1]['children'][0]['style']['textAlignVertical'] = 'CENTER'
        codes = {g['code'] for g in fe.convert(response, 'KEY', '1:2')['source_gaps']}
        self.assertEqual(codes, {'paint_blend_mode', 'multiple_blurs', 'text_vertical_alignment'})


class OfflineCliTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / 'nodes.json').write_text(json.dumps(figma_fixture.response()))
        images = self.root / 'images'
        images.mkdir()
        (images / '1-2.png').write_bytes(png(1500, 3248, (255, 254, 250, 255)))
        (images / '1-40.png').write_bytes(png(64, 64))
        (images / '1-50.png').write_bytes(png(192, 192))
        self.app = self.root / 'app'
        (self.app / 'fidelity').mkdir(parents=True)
        (self.app / 'fidelity' / '.local.env').write_text('FIGMA_TOKEN="figd_secret_value"\n')
        self.out = self.app / 'fidelity' / 'withdraw' / 'evidence'

    def run_cli(self):
        return subprocess.run([sys.executable, str(SCRIPTS / 'figma_evidence.py'),
                               '--url', 'https://www.figma.com/design/KEY/F?node-id=1-2', '--out', str(self.out),
                               '--nodes-json', str(self.root / 'nodes.json'), '--images-dir', str(self.root / 'images')],
                              capture_output=True, text=True)

    def test_outputs_feed_prepare_and_both_generators(self):
        run = self.run_cli()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result['status'], 'OK')
        manifest = json.loads((self.out / 'manifest.json').read_text())
        self.assertEqual({a['asset_id'] for a in manifest['assets']}, {'1:40:image', '1:50:image'})
        for path in self.out.rglob('*'):
            if path.is_file() and path.suffix in ('.json', '.txt'):
                self.assertNotIn('figd_secret_value', path.read_text())
        from prepare_page import prepare
        (self.root / 'fonts.json').write_text(json.dumps({'fonts': {}}))
        plan = prepare([self.out / 'source.json'], self.out / 'reference.png', self.out / 'manifest.json')
        self.assertEqual(plan['source_nodes'], len(json.loads((self.out / 'source.json').read_text())['nodes']))
        self.assertEqual(plan['evidence_schema_warnings']['count'], 0)
        self.assertFalse([i for i in plan['issues'] if i['kind'] not in ('font_mapping_missing', 'source_styles_missing')],
                         plan['issues'])
        (self.root / 'plan.json').write_text(json.dumps(plan))
        from generate import generate
        react = generate([self.out / 'source.json'], self.root / 'plan.json', None, 'Withdraw',
                         self.app / 'src/fidelity/withdraw.g.tsx', app_root=self.app,
                         asset_dir='src/assets/design/withdraw', target='react')
        modes = {n['node_id']: n['mode'] for n in react['nodes']}
        self.assertEqual(modes['1:40'], 'original_asset')
        self.assertEqual(modes['1:41'], 'covered_by_asset')
        self.assertEqual(modes['1:20#bg'], 'native_exact')
        self.assertEqual(react['issues'], [i for i in react['issues'] if i['kind'] == 'font_mapping_missing'])
        tsx = (self.app / 'src/fidelity/withdraw.g.tsx').read_text()
        self.assertIn('<SourceClip shape={{ kind: "rect", radii: 12 }}>', tsx)
        self.assertIn('id="1:20#shadow"', tsx)
        flutter = self.app / 'lib/withdraw.g.dart'
        generate([self.out / 'source.json'], self.root / 'plan.json', None, 'Withdraw', flutter,
                 app_root=self.app, asset_dir='assets/design/withdraw', target='flutter')
        errors = dart_syntax_errors(flutter)
        if errors is not None:
            self.assertEqual(errors, '', errors)

    def test_token_lookup_never_needs_a_file_in_the_repo(self):
        old = os.environ.pop('FIGMA_TOKEN', None)
        try:
            self.assertEqual(fe.token_from(self.out), 'figd_secret_value')
            (self.app / 'fidelity' / '.local.env').write_text('DESIGN_FIDELITY_SKILL=/x\n')
            with self.assertRaises(ValueError):
                fe.token_from(self.out)
            os.environ['FIGMA_TOKEN'] = 'from-env'
            self.assertEqual(fe.token_from(self.out), 'from-env')
        finally:
            os.environ.pop('FIGMA_TOKEN', None)
            if old is not None:
                os.environ['FIGMA_TOKEN'] = old


class EdgeBleedTests(unittest.TestCase):
    """Backgrounds drawn under the status bar / home indicator stay at the screen edge."""

    def model(self, extra):
        import test_generate_flutter as base
        from scene_model import SceneModel
        doc = base.fixture()
        doc['nodes'].extend(extra)
        nodes = {n['node_id']: n for n in doc['nodes']}
        model = SceneModel(nodes, [doc], None, {}, 'Fixture', None, 'x.g.dart')
        return model, model.build()

    def test_leaf_and_group_bleeds(self):
        import test_generate_flutter as base
        rect = [dict(p, cornerRadius=0) for p in base.RECT]
        fill = [{'type': 'color', 'isEnabled': True, 'color': base.color('#EEEEEE')}]
        model, _ = self.model([
            base.node('NAVBG', 'shape', (0, 0, 375, 88), order=30, raw={'points': rect, 'fills': fill}),
            base.node('DOCK', 'layer-group', (0, 790, 375, 22), order=31),
            base.node('DOCKBG', 'shape', (0, 790, 375, 22), parent='DOCK', order=32,
                      raw={'points': rect, 'fills': fill}),
        ])
        report = model.report('t', 1)
        decisions = report['draft_node_decisions']
        self.assertEqual(decisions['NAVBG'].get('bleed'), 'top')
        self.assertEqual(decisions['TABBAR'].get('bleed'), 'bottom')
        self.assertEqual(model.records['DOCK'].get('bleed'), 'bottom')
        from emit_flutter import FlutterEmitter
        dart = FlutterEmitter(model).dart(model.children_of_root)
        self.assertIn("import 'dart:math' as math;", dart)
        self.assertIn('bottom: math.max(0, dyBottom + 0)', dart)
        self.assertIn('height: dy + 88', dart)
        from emit_react import ReactEmitter
        tsx = ReactEmitter(model).tsx(model.children_of_root, {})
        self.assertIn('bottom={dyBottom(0, 0)}', tsx)
        self.assertIn('height={dy(88)}', tsx)


if __name__ == '__main__':
    unittest.main()
