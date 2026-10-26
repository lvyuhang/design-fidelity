"""Source-derived obligations survive compacting and cannot be omitted."""
import unittest
from scene_requirements import scene_requirements, validate_scene_checks
from prepare_page import compact_scene_requirements
from source_requirements import source_gaps

class PaintConsumptionTests(unittest.TestCase):
    def nodes(self):
        return {k:dict(node_type='rectangle', bounds=dict(x=0,y=0,width=40,height=16),
                       source_order=i, raw_style=style) for i,(k,style) in enumerate([
            ('dark',dict(fills=[{'color':'black','alpha':.4}])),
            ('light',dict(fills=[{'color':'white','alpha':.2}])),
            ('border',dict(borders=[{'thickness':2,'position':'内边框'}],opacity=50))])}

    def test_exact_paint_parameters_survive_brief(self):
        requirements=scene_requirements(self.nodes())
        groups={g['kind']:g for g in compact_scene_requirements(requirements)}
        self.assertEqual(groups['stroke']['instances'][0]['expected']['opacity'],50)
        self.assertEqual(groups['stroke']['instances'][0]['expected']['borders'][0]['thickness'],2)
        self.assertEqual(groups['paint_stack']['instances'][0]['node_ids'],['dark','light'])

    def test_no_scene_test_blocks_acceptance(self):
        with self.assertRaisesRegex(ValueError,'Unverified scene dependencies'):
            validate_scene_checks({},self.nodes())

    def test_no_background_is_evidence_only_for_artboard(self):
        nodes={'root':dict(node_type='artboard-group',bounds=dict(x=0,y=0,width=375,height=812),raw_style={'hasBackgroundColor':False})}
        self.assertFalse(source_gaps(nodes))
        nodes['root']['node_type']='group'
        self.assertTrue(source_gaps(nodes))
