import unittest
import test_fidelity as fixtures
from source_disposition import source_disposition, placeholder_issue, disposition_groups
from source_requirements import validate_obligations


def shape(**extra):
    return {'node_id': 'icon', 'node_type': 'shapePath',
            'bounds': {'x': 0, 'y': 0, 'width': 12, 'height': 12},
            'raw_style': {'fills': []}, **extra}


class DispositionTests(unittest.TestCase):
    def check(self, node, allowed):
        issue = placeholder_issue('icon', {'icon': node})
        self.assertEqual(issue is None, allowed)
        return issue

    def test_unread_geometry_is_not_missing(self):
        self.assertEqual(self.check(shape(), False)['next_action'],
                         'inspect_complete_node_and_children')

    def test_readable_path_cannot_be_waived_as_missing(self):
        for raw in ({'points': [{'point': {'x': 0, 'y': 0}}]}, {'path': 'M0,0L1,1'}):
            with self.subTest(raw=raw):
                self.assertEqual(self.check(shape(raw_style=raw), False)['source_state'],
                                 'vector_candidate')

    def test_asset_id_requires_inspection_even_if_download_failed(self):
        self.assertEqual(self.check(shape(asset_ids=['asset']), False)['source_state'],
                         'asset_candidate')

    def test_ancestor_asset_is_candidate_not_blanket_permission(self):
        nodes = {'icon': shape(parent_id='parent'), 'parent': {'asset_ids': ['group']}}
        self.assertEqual(placeholder_issue('icon', nodes)['source_state'],
                         'ancestor_asset_candidate')

    def test_confirmed_empty_leaf_geometry_remains_eligible(self):
        self.check(shape(raw_style={'fills': [], 'points': []}), True)

    def test_uninspected_children_prevent_missing_claim(self):
        nodes = {'icon': shape(raw_style={'fills': [], 'points': []}),
                 'child': shape(parent_id='icon')}
        self.assertIsNotNone(placeholder_issue('icon', nodes))

    def test_photo_mask_path_does_not_mean_image_content_available(self):
        self.check(shape(node_type='bitmap', raw_style={'points': [{'point': [0, 0]}]}), True)

    def test_unavailable_photo_and_unknown_style_are_distinct(self):
        self.check(shape(node_type='bitmap'), True)
        self.check(shape(node_type='bitmap', raw_style={}), False)

    def test_business_text_needs_font_repair(self):
        self.check(shape(text='设置'), False)

    def test_grouping_retains_all_instances_without_repeating_instructions(self):
        nodes = {'a': shape(), 'b': shape()}
        groups = disposition_groups(nodes, nodes)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['node_ids'], ['a', 'b'])

    def test_obligation_gate_rejects_self_declared_missing(self):
        n = shape(raw_style={'points': [{'point': [0, 0]}], 'fills': []})
        c = {'workflow_version': 1, 'canvas': [375, 812],
             'node_decisions': {'icon': {'mode': 'missing_asset_placeholder',
                  'shape': 'rect', 'reason': 'not exported', 'implementation': 'page.dart',
                  'symbol': 'placeholder'}}, 'implementation_inputs': ['page.dart'],
             'coverage': {'icon': {'status': 'excluded', 'checks': []}}}
        with self.assertRaisesRegex(ValueError, 'MISSING_SOURCE_NOT_ESTABLISHED'):
            validate_obligations(c, {'icon': n}, {'icon': n})
        n['node_type'] = 'bitmap'
        self.assertEqual(validate_obligations(c, {'icon': n}, {'icon': n})['unaccounted_visible_nodes'], 0)


class GateIntegrationTests(unittest.TestCase):
    setUp = fixtures.GateTests.setUp
    save = fixtures.GateTests.save
    render = fixtures.GateTests.render
    gate = fixtures.GateTests.gate
    assert_gate = fixtures.GateTests.assert_gate

    def test_false_missing_is_rejected_by_real_visual_gate(self):
        self.c['coverage']['icon'] = {'status': 'excluded', 'checks': [], 'reason': 'not exported'}
        self.c['node_decisions']['icon'].update(mode='missing_asset_placeholder', shape='rect', reason='not exported')
        self.c['features'].pop('icon')
        self.c['relations'] = {}
        self.c['not_applicable'] = {'relations': 'single text fixture'}
        report = self.assert_gate(2, 'NOT_EVALUATED')
        self.assertIn('MISSING_SOURCE_NOT_ESTABLISHED', report['reason'])


if __name__ == '__main__':
    unittest.main()
