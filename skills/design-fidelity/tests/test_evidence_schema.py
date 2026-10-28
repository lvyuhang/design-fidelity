"""Canonical evidence schema: adapters are judged here, before prepare."""
import copy
import json
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from evidence_schema import validate, validate_set  # noqa: E402


def minimal():
    return {'snapshot_id': 's1', 'resolved_version': 'v1', 'coordinate_space': 'source_canvas',
            'coordinate_mapping': {'verified': True}, 'canvas': {'width': 100, 'height': 200},
            'total_nodes': 2, 'nodes': [
                {'node_id': 'root', 'parent_id': None, 'source_order': 0, 'node_type': 'artboard-group',
                 'bounds': {'x': 0, 'y': 0, 'width': 100, 'height': 200}, 'raw_style': {}, 'text': None,
                 'asset_ids': []},
                {'node_id': 't', 'parent_id': 'root', 'source_order': 0, 'node_type': 'text',
                 'bounds': {'x': 10, 'y': 10, 'width': 40, 'height': 20}, 'text': 'Hi', 'asset_ids': [],
                 'raw_style': {'font': {'textAlignment': 2}},
                 'text_spec': {'base_style': {'font_family': 'Inter', 'font_size': 14, 'color': '#111111'},
                               'text_runs': [{'text': 'H'}, {'text': 'i', 'font_weight': 700}]}}]}


def errors(issues):
    return [i for i in issues if i['severity'] == 'error']


class EvidenceSchemaTests(unittest.TestCase):
    def test_minimal_document_and_runs_inheriting_base_style(self):
        self.assertEqual(validate(minimal()), [])

    def test_lanhu_example_passes(self):
        example = Path(__file__).resolve().parents[3] / 'examples/withdraw-2/source.json'
        if not example.exists():
            self.skipTest('sparse checkout without examples')
        self.assertEqual(errors(validate(json.loads(example.read_text()))), [])

    def test_style_vocabulary_errors_point_into_the_document(self):
        doc = minimal()
        doc['nodes'][0]['raw_style'] = {
            'fills': [{'type': 'color', 'color': 'red'}],
            'borders': [{'color': '#000000', 'thickness': 1, 'position': 'middle'}],
            'shadow': [{'color': '#00000033', 'blurRadius': 'x'}],
            'blur': {'radius': 4, 'blurType': 9}, 'opacity': 0.5 * 300}
        pointers = {i['pointer'] for i in validate(doc)}
        self.assertEqual(pointers, {'/nodes/0/raw_style/fills/0/color', '/nodes/0/raw_style/borders/0/position',
                                    '/nodes/0/raw_style/shadow/0/blurRadius', '/nodes/0/raw_style/blur',
                                    '/nodes/0/raw_style/opacity'})

    def test_identity_version_and_text_coverage_are_errors(self):
        doc = minimal()
        doc['resolved_version'] = ''
        doc['nodes'][1]['text'] = 'Hello'
        doc['nodes'].append(copy.deepcopy(doc['nodes'][1]))
        doc['nodes'][2]['parent_id'] = 'ghost'
        found = {i['pointer']: i['message'] for i in errors(validate(doc))}
        self.assertIn('/resolved_version', found)
        self.assertIn('/nodes/1/text_spec/text_runs', found)
        self.assertIn('duplicate', found['/nodes/2/node_id'])
        self.assertIn('/nodes/2/parent_id', found)

    def test_missing_order_and_type_are_warnings_only(self):
        doc = minimal()
        del doc['nodes'][1]['source_order']
        doc['nodes'][1]['node_type'] = 'frame'
        issues = validate(doc)
        self.assertEqual(errors(issues), [])
        self.assertEqual(len(issues), 2)

    def test_paginated_set_resolves_parents_and_requires_every_page(self):
        first, second = minimal(), minimal()
        first.update(total=3, nodes=first['nodes'][:1], truncated=True, next_offset=1)
        second.update(total=3, nodes=second['nodes'][1:])
        del first['total_nodes'], second['total_nodes']
        result = validate_set([first, second])
        self.assertEqual(result['documents'], [[], []])
        self.assertEqual(len(result['overall']), 1)
        self.assertIn('2 unique nodes, source declares 3', result['overall'][0]['message'])
        second['nodes'].append({**second['nodes'][0], 'node_id': 't2', 'text': 'Hi'})
        self.assertEqual(validate_set([first, second])['overall'], [])


if __name__ == '__main__':
    unittest.main()
