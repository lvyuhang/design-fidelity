import json
from pathlib import Path
import tempfile
import unittest

from graphic_source_audit import audit


class GraphicSourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.code = self.root / 'page.dart'
        self.evidence = self.root / 'source.json'
        self.evidence.write_text(json.dumps({'nodes': [{
            'node_id': 'VECTOR', 'raw_style': {'points': [[0, 0], [1, 1]]}
        }]}))

    def audit_case(self, bindings=None):
        return audit([self.code], self.root, {'bindings': bindings or {}}, [self.evidence])

    def test_unbound_custom_painter_is_rejected(self):
        self.code.write_text('CustomPaint(painter: TrashPainter())')
        self.assertEqual(self.audit_case()['status'], 'FAIL')

    def test_verified_source_vector_passes(self):
        self.code.write_text('CustomPaint(painter: SourcePainter())')
        key = 'page.dart::custom_paint::SourcePainter'
        binding = {key: {'mode': 'source_vector', 'source_nodes': [
            {'node_id': 'VECTOR', 'pointer': '/raw_style/points'}]}}
        self.assertEqual(self.audit_case(binding)['status'], 'PASS')

    def test_system_chrome_requires_reason(self):
        self.code.write_text('CustomPaint(painter: StatusPainter())')
        key = 'page.dart::custom_paint::StatusPainter'
        self.assertEqual(self.audit_case({key: {'mode': 'system_chrome'}})['status'], 'FAIL')
        self.assertEqual(self.audit_case({key: {'mode': 'system_chrome',
            'reason': 'platform status area'}})['status'], 'PASS')

    def test_framework_icon_without_binding_is_rejected(self):
        self.code.write_text('const Icon(Icons.delete_outline)')
        report = self.audit_case()
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['findings'][0]['symbol'], 'Icons.delete_outline')

