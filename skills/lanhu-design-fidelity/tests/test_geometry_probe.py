"""Node geometry and multi-size checks: precise, actionable, and fail-closed."""
import json
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from geometry_probe import compare_geometry, responsive_report  # noqa: E402
import test_fidelity as fixtures  # noqa: E402


def nodes():
    return {
        'BOX': {'node_id': 'BOX', 'name': '卡片', 'bounds': {'x': 16, 'y': 100, 'width': 343, 'height': 50}},
        'LEFT': {'node_id': 'LEFT', 'name': '标签', 'text': '提现金额',
                 'bounds': {'x': 32, 'y': 120, 'width': 56, 'height': 20},
                 'raw_style': {'font': {'textAlignment': 4}}},
        'MID': {'node_id': 'MID', 'name': '标题', 'text': '提现',
                'bounds': {'x': 172, 'y': 55, 'width': 32, 'height': 22},
                'raw_style': {'font': {'textAlignment': 2}}},
        'NEXT': {'node_id': 'NEXT', 'name': '说明', 'text': '到账时间',
                 'bounds': {'x': 32, 'y': 142, 'width': 60, 'height': 17},
                 'raw_style': {'font': {'textAlignment': 4}}},
    }


DECISIONS = {k: {'mode': 'native_exact'} for k in ('BOX', 'LEFT', 'MID', 'NEXT')}


def measured(**overrides):
    rects = {'BOX': [16, 100, 343, 50], 'LEFT': [32, 120, 55.4, 20],
             'MID': [171.6, 55, 32.8, 22], 'NEXT': [32, 142, 59.2, 17]}
    rects.update(overrides)
    return {'nodes': rects}


class GeometryProbeTests(unittest.TestCase):
    def test_exact_layout_passes_with_text_advance_noise(self):
        result = compare_geometry(nodes(), DECISIONS, measured())
        self.assertTrue(result['passed'], result['failures'])
        self.assertEqual(result['checked'], 4)

    def test_box_shift_names_node_and_delta(self):
        result = compare_geometry(nodes(), DECISIONS, measured(BOX=[16, 102, 343, 50]))
        self.assertEqual(result['failures'], [{'node_id': 'BOX', 'label': "BOX '卡片'",
                                               'failures': ['top +2.00px']}])

    def test_text_uses_alignment_edge_and_line_box(self):
        moved = compare_geometry(nodes(), DECISIONS, measured(MID=[168, 55, 32, 22]))
        self.assertIn('center edge -4.00px', moved['failures'][0]['failures'])
        taller = compare_geometry(nodes(), DECISIONS, measured(LEFT=[32, 120, 56, 24]))
        self.assertTrue(taller['failures'][0]['failures'][0].startswith('line box height +4.00px'))
        wider = compare_geometry(nodes(), DECISIONS, measured(LEFT=[32, 120, 63, 20]))
        self.assertIn('width +7.00px', wider['failures'][0]['failures'][0])

    def test_anchor_edge_absorbs_advance_width_noise(self):
        # Auto-width text anchored at the right grows leftwards: comparing its
        # left edge would report the 1.6px advance difference as an offset.
        n = nodes()
        n['EDIT'] = {'node_id': 'EDIT', 'name': '修改', 'text': '修改',
                     'bounds': {'x': 301, 'y': 120, 'width': 24, 'height': 17},
                     'raw_style': {'font': {'textAlignment': 4}}}
        geometry = measured(EDIT=[299.4, 120, 25.6, 17])
        left = dict(DECISIONS, EDIT={'mode': 'native_exact'})
        self.assertFalse(compare_geometry(n, left, geometry)['passed'])
        right = dict(DECISIONS, EDIT={'mode': 'native_exact', 'anchor': 'right'})
        self.assertTrue(compare_geometry(n, right, geometry)['passed'])
        shifted = measured(EDIT=[297.4, 120, 25.6, 17])
        self.assertIn('right edge -2.00px',
                      compare_geometry(n, right, shifted)['failures'][0]['failures'])

    def test_text_inside_an_override_frame_is_measured(self):
        # The override fills the frame (unchanged) but pads the text down 3px.
        geometry = measured()
        geometry['text_nodes'] = {'LEFT': [32, 123, 55.4, 20]}
        result = compare_geometry(nodes(), DECISIONS, geometry)
        self.assertEqual(result['failures'][0]['failures'], ['top +3.00px'])

    def test_missing_source_key_fails_closed(self):
        geometry = measured()
        del geometry['nodes']['MID']
        result = compare_geometry(nodes(), DECISIONS, geometry)
        self.assertFalse(result['passed'])
        self.assertIn('sourceKey', result['failures'][0]['failures'][0])

    def test_excluded_nodes_are_not_probed(self):
        decisions = dict(DECISIONS, MID={'mode': 'excluded_with_reason'})
        geometry = measured()
        del geometry['nodes']['MID']
        self.assertTrue(compare_geometry(nodes(), decisions, geometry)['passed'])

    def test_responsive_findings(self):
        variants = {'variants': [
            {'width': 360, 'height': 812, 'text_scale': 1.0, 'exception': None,
             'nodes': measured()['nodes']},
            {'width': 360, 'height': 812, 'text_scale': 1.3, 'exception':
                'A RenderFlex overflowed by 12 pixels on the right.\nmore',
             'nodes': measured(NEXT=[32, 135, 80, 22], BOX=[16, 100, 350, 50])['nodes']},
        ]}
        report = responsive_report(nodes(), variants, 375)
        kinds = {f['kind'] for f in report['findings']}
        self.assertEqual(kinds, {'exceptions', 'horizontal_overflow', 'text_overlap'})
        self.assertFalse(report['passed'])
        self.assertEqual(report['findings'][0]['message'],
                         'A RenderFlex overflowed by 12 pixels on the right.')
        clean = responsive_report(nodes(), {'variants': variants['variants'][:1]}, 375)
        self.assertTrue(clean['passed'])
        overlap_only = {'variants': [dict(variants['variants'][1], exception=None,
                                          nodes=measured(NEXT=[32, 135, 80, 22])['nodes'])]}
        self.assertTrue(responsive_report(nodes(), overlap_only, 375)['passed'],
                        'text_overlap is reported but not blocking by default')
        self.assertFalse(responsive_report(nodes(), overlap_only, 375,
                                           blocking=('text_overlap',))['passed'])


class GateGeometryTests(unittest.TestCase):
    """The gate fails closed when geometry_probe is enabled."""

    def setUp(self):
        f = self.f = fixtures.GateTests()
        f.setUp()
        self.addCleanup(f.doCleanups)
        f.c['geometry_probe'] = 'v1'

    def render_with_geometry(self, icon):
        """Renderer writes the PNG and its geometry sidecar in the same run."""
        geometry = {'nodes': {'icon': icon, 'text': [30, 10, 10, 10], 'surface': [0, 0, 100, 100]}}
        script = self.f.root / 'render_geo.py'
        script.write_text(
            'import json, subprocess, sys\n'
            f'subprocess.run([sys.executable, {str(self.f.root / "render.py")!r}, sys.argv[1], "normal"], check=True)\n'
            f'open(sys.argv[1] + ".geometry.json", "w").write({json.dumps(json.dumps(geometry))})\n')
        run = self.f.render(command=[sys.executable, str(script), str(self.f.root / 'candidate.png')])
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_valid_pass(self):
        self.render_with_geometry([10, 10, 10, 10])
        result, report = self.f.gate()
        self.assertEqual(report['status'], 'PASS', result.stdout + result.stderr)
        self.assertEqual(report['candidates']['test']['geometry']['checked'], 3)

    def test_missing_geometry_file_fails(self):
        self.f.render()
        _, report = self.f.gate()
        self.assertEqual(report['status'], 'FAIL')

    def test_shifted_node_fails_with_message(self):
        self.render_with_geometry([10, 13, 10, 10])
        _, report = self.f.gate()
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['candidates']['test']['geometry']['failures'][0]['failures'],
                         ['top +3.00px'])

    def test_geometry_written_after_render_is_rejected(self):
        self.render_with_geometry([10, 13, 10, 10])
        (self.f.root / 'candidate.png.geometry.json').write_text(json.dumps(
            {'nodes': {'icon': [10, 10, 10, 10], 'text': [30, 10, 10, 10], 'surface': [0, 0, 100, 100]}}))
        _, report = self.f.gate()
        self.assertEqual(report['status'], 'NOT_EVALUATED')


if __name__ == '__main__':
    unittest.main()
