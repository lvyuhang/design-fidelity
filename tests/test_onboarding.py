"""Behavior checks for clone setup, configuration isolation and offline evidence."""
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import project


class OnboardingTests(unittest.TestCase):
    def test_changed_source_and_replaced_build_are_not_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);app=root/'app';local=root/'local'
            (app/'lib').mkdir(parents=True);(app/'build/web').mkdir(parents=True)
            for name in ('pubspec.yaml','pubspec.lock'):(app/name).write_text('fixture')
            source=app/'lib/main.dart';source.write_text('first source')
            binary=app/'build/web/main.dart.js';binary.write_text('first build')
            with patch.object(project,'APP',app),patch.object(project,'LOCAL',local):
                project.record_build();self.assertTrue(project.build_current())
                source.write_text('second source');self.assertFalse(project.build_current())
                project.record_build();binary.write_text('replaced build');self.assertFalse(project.build_current())

    def test_local_configuration_is_literal_and_preserves_existing_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            marker=root/'must-not-exist'
            (root/'.env.local').write_text('REVIEW_DATA_DIR="'+str(root/'my data')+'"\nLANHU_MCP_LAUNCHER=$(touch '+str(marker)+')\nGH_TOKEN=not-used\n')
            with patch.object(project,'ROOT',root),patch.dict(os.environ,{'REVIEW_DATA_DIR':'existing-user-data'}):
                env=project.environment({})
                self.assertEqual(env['REVIEW_DATA_DIR'],'existing-user-data')
                self.assertTrue(env['LANHU_MCP_LAUNCHER'].startswith('$(touch'))
                self.assertFalse(marker.exists())

    def test_occupied_port_is_rejected_without_killing_owner(self):
        with socket.socket() as owner:
            owner.bind(('127.0.0.1',0));owner.listen()
            with self.assertRaisesRegex(ValueError,'已占用'):
                project.port_available(owner.getsockname()[1])
            self.assertGreater(owner.fileno(),-1)

    def test_offline_evidence_is_complete_and_hash_pinned(self):
        base=ROOT/'examples/withdraw-2';manifest=json.loads((base/'manifest.json').read_text())
        for name,digest in manifest['sha256'].items():
            self.assertEqual(hashlib.sha256((base/name).read_bytes()).hexdigest(),digest,name)
        source=json.loads((base/'source.json').read_text())
        self.assertEqual(len(source['nodes']),source['total'])
        self.assertEqual(len({n['node_id'] for n in source['nodes']}),51)

    def test_partial_font_directory_is_not_accepted(self):
        from tools.prepare_fonts import prepare
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);(base/'source').mkdir()
            with self.assertRaisesRegex(ValueError,'字体目录缺少'):
                prepare(base/'output',font_dir=base/'source')

    def test_bootstrap_critical_paths_do_not_depend_on_original_username(self):
        for name in ['project.py','tools/prepare_fonts.py','tools/fetch_lanhu_page.py',
                     'android-design-review/server.py','android-design-review/lanhu_bridge.py']:
            self.assertNotIn('/Users/tan', (ROOT/name).read_text(),name)


if __name__=='__main__':unittest.main()
