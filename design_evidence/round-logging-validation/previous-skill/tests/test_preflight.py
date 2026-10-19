"""Regression checks for early rejection, compact evidence, and shared runner."""
import json
import os
import subprocess
import sys
import unittest
import test_fidelity as fixtures
SCRIPTS = fixtures.SCRIPTS
from fidelity_contract import sha256
from preflight import check, style_gaps


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.GateTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.save()
        self.path = self.fixture.root/'contract.json'

    def test_valid_existing_inputs_with_explicit_style_gap(self):
        result = check(self.path)
        self.assertEqual(result['status'], 'READY_FOR_RENDER')
        self.assertEqual(result['style_gaps'][0]['node_id'], 'text')

    def test_index_only_is_rejected_for_new_implementation(self):
        with self.assertRaisesRegex(ValueError, 'lack source styles'):
            check(self.path, require_style_evidence=True)

    def test_complete_style_is_recognized(self):
        nodes = {'text': {'text': 'A', 'raw_style': {'font': {
            'font': 'Fixture', 'size': 12, 'line': 16, 'color': {'r':0,'g':0,'b':0}}}}}
        self.assertEqual(style_gaps(nodes), [])
        del nodes['text']['raw_style']['font']['line']
        self.assertEqual(style_gaps(nodes)[0]['missing'], ['line_height'])

    def test_zero_values_are_not_absent(self):
        n = {'text': 'A', 'text_spec': {'base_style': {
            'font_family':'Fixture', 'font_size':12, 'line_height':0, 'color':0}}}
        self.assertEqual(style_gaps({'text':n}), [])

    def test_missing_glyph_rejected_before_any_render(self):
        f = self.fixture
        f.e['nodes'][1]['text'] = '中'
        (f.root/'source.json').write_text(json.dumps(f.e))
        f.c['pinned_files']['source.json'] = sha256(f.root/'source.json')
        f.save()
        with self.assertRaisesRegex(ValueError, 'missing glyphs'):
            check(self.path)
        self.assertFalse((f.root/'candidate.png').exists())

    def test_stale_evidence_rejected(self):
        (self.fixture.root/'source.json').write_text(json.dumps(self.fixture.e)+' ')
        with self.assertRaisesRegex(ValueError, 'Pinned file changed'):
            check(self.path)

    def test_draft_is_not_render_ready(self):
        self.fixture.c['status'] = 'draft'
        self.fixture.save()
        with self.assertRaises(ValueError):
            check(self.path)

    def test_failure_writes_compact_report_and_returns_two(self):
        output = self.fixture.root/'preflight.json'
        run = subprocess.run([sys.executable, str(SCRIPTS/'preflight.py'), '--contract',
            str(self.path), '--output', str(output), '--require-style-evidence'], capture_output=True,text=True)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(json.loads(output.read_text())['status'], 'NOT_EVALUATED')
        self.assertLess(len(run.stdout), 700)

    def run_pipeline(self, mode='normal', strict=False):
        root = self.fixture.root
        binary = root/'bin'
        binary.mkdir()
        # A deterministic renderer substitute tests orchestration without a Flutter SDK.
        shim = binary/'flutter'
        shim.write_text(f'#!{sys.executable}\nimport os,subprocess,sys\n'
                        f'sys.exit(subprocess.call([sys.executable,{str(root/"render.py")!r},'
                        'os.environ["FIXTURE_OUTPUT"],sys.argv[-1]]))\n')
        shim.chmod(0o755)
        output = root/'pipeline'
        run = subprocess.run([sys.executable,str(SCRIPTS/'run_flutter.py'),
            '--contract',str(self.path),'--app',str(root),'--test',mode,
            '--output-env','FIXTURE_OUTPUT','--output',str(output),
            *(['--require-style-evidence'] if strict else [])],
            env={**os.environ,'PATH':str(binary)+os.pathsep+os.environ.get('PATH','')},
            capture_output=True,text=True)
        return run, json.loads((output/'run.json').read_text())

    def test_runner_success_preserves_original_gate(self):
        run, report = self.run_pipeline()
        self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
        self.assertEqual(report['gate_status'], 'PASS')
        self.assertEqual([s['name'] for s in report['stages']], ['preflight','render','gate'])

    def test_runner_visual_failure_exposes_only_failed_checks(self):
        run, report = self.run_pipeline('missing')
        self.assertEqual(run.returncode, 1)
        self.assertEqual(report['gate_status'], 'FAIL')
        self.assertIn('features.icon', [x['check'] for x in report['failures']])
        self.assertNotIn('features.text', [x['check'] for x in report['failures']])
        self.assertLess(len(run.stdout), 2500)

    def test_runner_strict_mode_stops_before_render(self):
        run, report = self.run_pipeline(strict=True)
        self.assertEqual(run.returncode, 1)
        self.assertEqual(report['stages'], [])
        self.assertFalse((self.fixture.root/'pipeline/render.png').exists())


if __name__ == '__main__':
    unittest.main()
