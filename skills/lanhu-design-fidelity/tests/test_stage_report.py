"""Run summaries separate blockers from observations and keep node detail."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from stage_report import build, markdown  # noqa: E402


class StageReportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = self.root = Path(temp.name)
        run = root / 'run' / '005-accept'
        (run / 'gate').mkdir(parents=True)
        (run / 'gate' / 'visual-gate-report.json').write_text(json.dumps({
            'excluded_fraction': 0.06,
            'candidates': {'flutter': {
                'regions': {'whole': {'label': '整页', 'passed': True}},
                'features': {'t': {'label': '提现', 'passed': False, 'failures': ['center_x_delta=1.2px']}},
                'relations': {}, 'colors': {},
                'geometry': {'passed': False, 'checked': 30, 'failures': [
                    {'node_id': 'A', 'label': "A '修改'", 'failures': ['left edge -1.60px']}]},
                'responsive': {'passed': False, 'blocking': ['exceptions', 'horizontal_overflow'],
                               'findings': [
                                   {'variant': '360w@1.3x', 'kind': 'horizontal_overflow', 'message': 'x'},
                                   *[{'variant': '360w@1.3x', 'kind': 'text_overlap', 'message': 'o'}] * 12]},
            }}}))
        (run / 'run.json').write_text(json.dumps({'gate_status': 'FAIL', 'failed_stage': 'gate',
            'preflight': {'dart_fidelity_lint': {'status': 'PASS', 'findings': [], 'suppressed': []}}}))
        (root / 'run' / 'session.json').write_text(json.dumps({
            'status': 'RUNNING', 'summary': {'elapsed_seconds': 70.2, 'tokens': None,
                                             'rounds': {'rounds': 1, 'validation_attempts': 1}},
            'events': [{'action': 'accept', 'status': 'FAILED', 'report': str(run / 'run.json')}]}))
        (root / 'page.json').write_text(json.dumps({'name': 'demo', 'run_dir': 'run',
                                                    'contract': 'missing.json'}))

    def test_blockers_and_observations_are_separate(self):
        report = build(self.root / 'page.json')
        self.assertEqual(report['blocking'], {'features': 1, 'geometry': 1,
                                              'responsive.horizontal_overflow': 1})
        self.assertEqual(report['blocking_total'], 3)
        self.assertEqual(report['observations'], {'responsive.text_overlap': 12})
        self.assertEqual(report['geometry_failures'][0]['failures'], ['left edge -1.60px'])
        self.assertIsNone(report['tokens'])
        text = markdown(report)
        self.assertIn('| 阻断项合计 | 3 |', text)
        self.assertIn("A '修改'", text)

    def test_missing_artifacts_stay_null(self):
        (self.root / 'run' / 'session.json').write_text(json.dumps({'events': []}))
        report = build(self.root / 'page.json')
        self.assertIsNone(report['gate_status'])
        self.assertEqual(report['blocking_total'], 0)

    def test_cli_writes_markdown(self):
        out = self.root / 'report.md'
        run = subprocess.run([sys.executable, str(SCRIPTS / 'stage_report.py'), '--config',
                              str(self.root / 'page.json'), '--output', str(out)],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(out.read_text().startswith('# demo'))


if __name__ == '__main__':
    unittest.main()
