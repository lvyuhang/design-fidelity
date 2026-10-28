"""Developer installer: minimal footprint, idempotent, never clobbers edits."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from install_app import (add_asset_dir, add_dependency, create_page, init_app,  # noqa: E402
                         install_fonts, install_skill)
import install_app  # noqa: E402

PUBSPEC = """name: demo_app
environment:
  sdk: '>=3.4.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  intl: ^0.19.0

dev_dependencies:
  flutter_test:
    sdk: flutter

flutter:
  uses-material-design: true
  assets:
    - assets/images/
  fonts:
    - family: AppSans
      fonts:
        - asset: assets/fonts/a.ttf
"""


class InstallAppTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.app = self.root / 'app'
        self.app.mkdir()
        (self.app / 'pubspec.yaml').write_text(PUBSPEC)

    def test_skill_copy_excludes_maintainer_material(self):
        result = install_skill(self.root / 'skills', force=False)
        installed = Path(result['path'])
        self.assertTrue((installed / 'SKILL.md').is_file())
        self.assertTrue((installed / 'scripts/page_session.py').is_file())
        self.assertTrue((installed / 'assets/flutter/design_fidelity/lib/design_fidelity.dart').is_file())
        self.assertFalse((installed / 'tests').exists())
        self.assertFalse(list(installed.rglob('__pycache__')))
        self.assertEqual(install_skill(self.root / 'skills', force=False)['status'], 'UP_TO_DATE')
        (installed / '.installed-version').write_text('0.0.1\n')
        self.assertEqual(install_skill(self.root / 'skills', force=False)['status'], 'INSTALLED')
        self.assertTrue((self.root / 'skills/design-fidelity.backup-0.0.1').is_dir())

    def test_pubspec_edits_are_minimal_and_idempotent(self):
        pubspec = self.app / 'pubspec.yaml'
        self.assertEqual(add_dependency(pubspec), 'added')
        self.assertEqual(add_dependency(pubspec), 'present')
        self.assertEqual(add_asset_dir(pubspec, 'assets/design/withdraw'), 'added')
        self.assertEqual(add_asset_dir(pubspec, 'assets/design/withdraw'), 'present')
        text = pubspec.read_text()
        self.assertIn('  intl: ^0.19.0\n  design_fidelity:\n    path: packages/design_fidelity\n\ndev_dependencies', text)
        self.assertIn('    - assets/images/\n    - assets/design/withdraw/\n  fonts:', text)
        self.assertEqual(text.count('flutter:\n  uses-material-design'), 1)

    def test_assets_section_is_created_when_missing(self):
        pubspec = self.app / 'pubspec.yaml'
        pubspec.write_text('name: x\ndependencies:\n  flutter:\n    sdk: flutter\nflutter:\n  uses-material-design: true')
        add_asset_dir(pubspec, 'assets/design/a')
        self.assertIn('flutter:\n  assets:\n    - assets/design/a/\n  uses-material-design: true', pubspec.read_text())
        pubspec.write_text('name: x\n')
        add_asset_dir(pubspec, 'assets/design/a')
        self.assertTrue(pubspec.read_text().endswith('flutter:\n  assets:\n    - assets/design/a/\n'))

    def test_init_and_page_create_a_ready_workspace(self):
        result = init_app(self.app, sys.executable, force=False)
        self.assertEqual(result['package'], 'installed')
        self.assertTrue((self.app / 'packages/design_fidelity/pubspec.yaml').is_file())
        self.assertIn('.local.env', (self.app / 'fidelity/.gitignore').read_text())
        self.assertEqual(init_app(self.app, sys.executable, force=False)['package'], 'unchanged')
        (self.app / 'packages/design_fidelity/lib/design_fidelity.dart').write_text('// edited\n')
        with self.assertRaisesRegex(ValueError, '--force'):
            init_app(self.app, sys.executable, force=False)
        init_app(self.app, sys.executable, force=True)

        page = create_page(self.app, 'order_detail', None, '订单详情')
        self.assertEqual(page['class_name'], 'OrderDetail')
        config = json.loads(Path(page['config']).read_text())
        self.assertEqual(config['generated'], '../../lib/fidelity/order_detail.g.dart')
        self.assertEqual(config['font_map'], '../font-map.json')
        self.assertIn('    - assets/design/order_detail/', (self.app / 'pubspec.yaml').read_text())
        self.assertEqual(create_page(self.app, 'order_detail', None, None)['status'], 'EXISTS')
        with self.assertRaisesRegex(ValueError, 'snake_case'):
            create_page(self.app, 'Order-Detail', None, None)

    def test_wrapper_runs_page_session(self):
        init_app(self.app, sys.executable, force=False)
        create_page(self.app, 'withdraw', None, None)
        run = subprocess.run([str(self.app / 'fidelity/page'), 'withdraw', 'start'],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)['status'], 'RUNNING')
        self.assertTrue((self.app / 'fidelity/withdraw/run/session.json').is_file())


def synthetic_pingfang(path):
    """A two-face TTC named like the system PingFang collection."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTCollection
    fonts = []
    for face in ('Regular', 'Semibold'):
        builder = FontBuilder(1000, isTTF=True)
        builder.setupGlyphOrder(['.notdef', 'uni63D0'])
        builder.setupCharacterMap({0x63D0: 'uni63D0'})
        glyph = TTGlyphPen(None).glyph()
        builder.setupGlyf({'.notdef': glyph, 'uni63D0': glyph})
        builder.setupHorizontalMetrics({'.notdef': (500, 0), 'uni63D0': (1000, 0)})
        builder.setupHorizontalHeader(ascent=800, descent=-200)
        builder.setupNameTable({'familyName': 'PingFang SC', 'styleName': face,
                                'psName': f'PingFangSC-{face}'})
        builder.setupOS2()
        builder.setupPost()
        fonts.append(builder.font)
    collection = TTCollection()
    collection.fonts = fonts
    collection.save(str(path))


class InstallFontsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.app = self.root / 'app'
        self.app.mkdir()
        (self.app / 'pubspec.yaml').write_text(PUBSPEC)
        init_app(self.app, sys.executable, force=False)
        synthetic_pingfang(self.root / 'PingFang.ttc')
        self.addCleanup(setattr, install_app, 'FONT_HOME', install_app.FONT_HOME)
        install_app.FONT_HOME = str(self.root / 'home-fonts')

    def test_faces_are_extracted_outside_the_app_and_mapped_per_platform(self):
        result = install_fonts(self.app, self.root / 'PingFang.ttc', 'NotoSansSC')
        self.assertEqual(sorted(result['extracted']), ['PingFangSC-Regular.otf', 'PingFangSC-Semibold.otf'])
        fonts = json.loads((self.app / 'fidelity/font-map.json').read_text())['fonts']
        self.assertEqual(set(fonts), {'PingFangSC-Regular@400', 'PingFangSC-Semibold@600'})
        entry = fonts['PingFangSC-Semibold@600']
        self.assertIsNone(entry['ios'])
        self.assertEqual(entry['android'], 'NotoSansSC')
        self.assertTrue(Path(entry['path']).is_file())
        self.assertFalse(list(self.app.rglob('*.otf')), 'design fonts never enter the app')

    def test_existing_entries_are_kept(self):
        path = self.app / 'fidelity/font-map.json'
        path.write_text(json.dumps({'fonts': {'PingFangSC-Regular@400': {'path': 'mine.otf',
                                                                         'runtime_family': 'Mine'}}}))
        result = install_fonts(self.app, self.root / 'PingFang.ttc', None)
        self.assertEqual(result['added_to_font_map'], ['PingFangSC-Semibold@600'])
        self.assertEqual(json.loads(path.read_text())['fonts']['PingFangSC-Regular@400']['path'], 'mine.otf')

    def test_missing_collection_is_reported(self):
        with self.assertRaisesRegex(ValueError, 'PingFang.ttc not found'):
            install_fonts(self.app, self.root / 'none.ttc', None)


if __name__ == '__main__':
    unittest.main()
