"""End-to-end: a real Lanhu snapshot reaches a frozen contract with no hand edits.

Uses the repository's offline example (examples/withdraw-2) when present; the
skill alone ships without it, so the test skips instead of passing vacuously.
Rendering needs Flutter and is outside this test.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / 'scripts'
EXAMPLE = SKILL.parents[1] / 'examples' / 'withdraw-2'
sys.path.insert(0, str(SCRIPTS))
from dart_tools import dart_syntax_errors  # noqa: E402


def synthetic_font(path, evidence):
    """Covers the page's characters; licensed fonts are never bundled."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    chars, families = set(), set()
    for node in evidence['nodes']:
        for run in (node.get('text_spec') or {}).get('text_runs', []):
            chars |= set(run.get('text') or '')
            families.add(f"{run['font_family']}@{run['font_weight']}")
    names = ['.notdef'] + [f'u{ord(c):04X}' for c in sorted(chars)]
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(names)
    builder.setupCharacterMap({ord(c): f'u{ord(c):04X}' for c in chars})
    glyph = TTGlyphPen(None).glyph()
    builder.setupGlyf({n: glyph for n in names})
    builder.setupHorizontalMetrics({n: (500, 0) for n in names})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({'familyName': 'Fixture', 'styleName': 'Regular'})
    builder.setupOS2()
    builder.setupPost()
    builder.save(path)
    return families


@unittest.skipUnless((EXAMPLE / 'source.json').is_file(), 'repository example not available')
class PipelineEndToEndTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        page, app = self.root / 'page', self.root / 'app'
        page.mkdir()
        app.mkdir()
        for name in ('source.json', 'reference.png', 'asset-manifest.json'):
            shutil.copy(EXAMPLE / name, page / name)
        shutil.copytree(EXAMPLE / 'assets', page / 'assets')
        families = synthetic_font(page / 'fixture.ttf', json.loads((page / 'source.json').read_text()))
        (page / 'font-map.json').write_text(json.dumps({'fonts': {
            f: {'path': 'fixture.ttf', 'runtime_family': 'SourcePingFang'} for f in families}}))
        (app / 'pubspec.yaml').write_text('name: demo_app\n')
        self.config = page / 'page.json'
        self.config.write_text(json.dumps({
            'name': 'withdraw-2', 'run_dir': 'run', 'scope': 'page', 'evidence': ['source.json'],
            'reference': 'reference.png', 'manifest': 'asset-manifest.json',
            'font_map': 'font-map.json', 'spec': 'reviewed-spec.json',
            'contract': 'visual-contract.json', 'app': '../app',
            'generated': '../app/lib/pages/withdraw_2.g.dart', 'class_name': 'Withdraw2',
            'asset_dir': 'assets/lanhu/withdraw_2', 'test': 'test/withdraw_2_test.dart',
            'output_env': 'PAGE_RENDER_OUTPUT', 'renderer_version': '3.47.7',
            'platform': 'test'}))
        self.page, self.app = page, app

    def step(self, action):
        run = subprocess.run([sys.executable, str(SCRIPTS / 'page_session.py'), '--config',
                              str(self.config), action], capture_output=True, text=True)
        result = json.loads(run.stdout)
        return run.returncode, result

    def test_snapshot_to_frozen_contract_without_hand_edits(self):
        expected = {'start': None, 'prepare': 'GENERATE', 'generate': 'IMPLEMENT_SEMANTICS',
                    'spec': 'ACCEPT', 'compile': 'VALIDATE'}
        for action, next_code in expected.items():
            code, result = self.step(action)
            self.assertEqual(code, 0, f'{action}: {result}')
            if next_code:
                self.assertEqual(result['next_action']['code'], next_code, action)
        contract = json.loads((self.page / 'visual-contract.json').read_text())
        statuses = {v['status'] for v in contract['coverage'].values()}
        self.assertEqual(statuses, {'covered', 'excluded'})
        reasons = {s['reason'].split(' ')[0] for s in contract['exclude_shapes']}
        self.assertEqual(reasons, {'system_chrome:statusBar', 'system_chrome:homeIndicator'})
        self.assertEqual(contract['dart_lint'], 'v1')
        self.assertEqual(contract['geometry_probe'], 'v1')
        self.assertIn('generated_scene', contract['scene_checks'])
        generated = [self.app / 'lib/pages/withdraw_2.g.dart',
                     self.app / 'test/withdraw_2_scene_test.g.dart',
                     self.app / 'test/withdraw_2_test.dart']
        for path in generated:
            self.assertTrue(path.is_file(), path)
        lint = subprocess.run([sys.executable, str(SCRIPTS / 'dart_fidelity_lint.py'), '--contract',
                               str(self.page / 'visual-contract.json')], capture_output=True, text=True)
        self.assertEqual(lint.returncode, 0, lint.stdout)
        errors = dart_syntax_errors(*generated)
        if errors is not None:
            self.assertEqual(errors, '')

    def test_reviewed_spec_is_never_overwritten(self):
        for action in ('start', 'prepare', 'generate', 'spec'):
            self.assertEqual(self.step(action)[0], 0, action)
        spec = self.page / 'reviewed-spec.json'
        spec.write_text(spec.read_text().replace('"max_mae": 6.0', '"max_mae": 5.0', 1))
        code, result = self.step('spec')
        self.assertNotEqual(code, 0)
        self.assertIn('5.0', spec.read_text())


if __name__ == '__main__':
    unittest.main()
