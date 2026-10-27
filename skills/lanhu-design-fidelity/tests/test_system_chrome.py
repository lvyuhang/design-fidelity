"""OS chrome is reserved and disclosed, never faked or allowed to block a page."""
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from source_requirements import source_gaps, validate_exclusion  # noqa: E402
from system_chrome import (chrome_exclusion_shapes, chrome_members,  # noqa: E402
                           detect_system_chrome)
from test_generate_flutter import fixture, node, text_node  # noqa: E402


def nodes_of(evidence):
    return {n['node_id']: n for n in evidence['nodes']}


class SystemChromeTests(unittest.TestCase):
    def setUp(self):
        self.nodes = nodes_of(fixture())

    def test_detects_named_status_bar_and_home_indicator(self):
        found = {e['kind']: e for e in detect_system_chrome(self.nodes)}
        self.assertEqual(found['statusBar']['node_id'], 'STATUS')
        self.assertEqual(set(found['statusBar']['members']), {'TIME', 'WIFI'})
        self.assertEqual(found['homeIndicator']['rect'], [121, 778, 134, 34])

    def test_detects_unnamed_status_bar_by_geometry_and_clock(self):
        evidence = fixture()
        for item in evidence['nodes']:
            if item['node_id'] == 'STATUS':
                item['name'] = '编组 3'
        found = detect_system_chrome(nodes_of(evidence))
        self.assertIn('STATUS', [e['node_id'] for e in found])

    def test_ignores_page_content_that_merely_sits_on_top(self):
        evidence = fixture()
        evidence['nodes'].append(node('NAV', 'layer-group', (0, 0, 375, 44), order=30, name='导航'))
        evidence['nodes'].append(dict(text_node('NAVTITLE', (150, 10, 60, 20), '标题', 31),
                                      parent_id='NAV'))
        self.assertNotIn('NAV', chrome_members(nodes_of(evidence)))
        evidence['nodes'].append(node('LOW', 'layer-group', (0, 300, 375, 44), order=32,
                                      name='Status Bar copy'))
        self.assertNotIn('LOW', chrome_members(nodes_of(evidence)),
                         'a status-bar name away from the top is not chrome')

    def test_missing_chrome_geometry_does_not_block_preparation(self):
        gaps = {g['node_id'] for g in source_gaps(self.nodes)}
        self.assertNotIn('WIFI', gaps)
        self.nodes['WIFI']['parent_id'] = 'ART'  # same shape outside chrome still blocks
        self.nodes['WIFI']['raw_style'] = {'fills': [{'isEnabled': True, 'type': 'color'}]}
        self.assertIn('WIFI', {g['node_id'] for g in source_gaps(self.nodes)})

    def test_exclusion_is_verified_against_source(self):
        decision = {'mode': 'excluded_with_reason', 'reason': 'OS chrome',
                    'exclusion': {'kind': 'system_chrome'}}
        validate_exclusion('TIME', decision, self.nodes, (375, 812))
        with self.assertRaisesRegex(ValueError, 'system_chrome'):
            validate_exclusion('LABEL', decision, self.nodes, (375, 812))

    def test_gate_masks_are_source_rects_with_reasons(self):
        shapes = chrome_exclusion_shapes(self.nodes)
        self.assertEqual([s['rect'] for s in shapes], [[0, 0, 375, 44], [121, 778, 134, 34]])
        self.assertTrue(all(s['reason'].startswith('system_chrome:') for s in shapes))


if __name__ == '__main__':
    unittest.main()
