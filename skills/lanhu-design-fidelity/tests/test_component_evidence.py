import copy
import json
from pathlib import Path
import unittest

import test_fidelity as fixtures
import test_preparation as preparation
from component_evidence import (closure,component_packet,expand_brief,factor_styles,
    map_references,node_aliases,packed,unpack_packet,write_component)
from prepare_page import implementation_brief


class ComponentEvidenceTests(unittest.TestCase):
    def test_defaults_preserve_absence_boolean_and_precision(self):
        groups=[{'style':{'opacity':100,'border':True,'x':1.123456789},'instances':[]},
                {'style':{'opacity':100,'border':1,'x':1.123456789},'instances':[]},
                {'style':{'opacity':100,'x':1.123456789},'instances':[]}]
        defaults,rows=factor_styles(groups)
        rebuilt=[{'style':{**defaults,**r['overrides']},'instances':r['instances']} for r in rows]
        self.assertEqual(json.dumps(groups,sort_keys=True),json.dumps(rebuilt,sort_keys=True))
        self.assertNotIn('border',defaults)
        groups=[{'style':{'border':v,'metadata':'long common value '*10},'instances':[]} for v in [True,1,True]]
        defaults,rows=factor_styles(groups)
        rebuilt=[{'style':{**defaults,**r['overrides']},'instances':r['instances']} for r in rows]
        self.assertEqual(json.dumps(groups,sort_keys=True),json.dumps(rebuilt,sort_keys=True))

    def test_aliases_leave_business_text_untouched_and_roundtrip_scene_ids(self):
        nodes={'source-uuid':{'parent_id':'@n1'},'mask-uuid':{}}
        mapping=node_aliases(nodes)
        original={'node_id':'source-uuid','text':'source-uuid',
                  'id':'source-uuid/boundary/mask-uuid',
                  'samples':{'source-uuid':[{'role':'peak','rect':[1,2,3,4]}]},
                  'node_ids':['source-uuid','mask-uuid']}
        encoded=map_references(original,mapping)
        self.assertEqual(encoded['text'],'source-uuid')
        self.assertNotEqual(mapping['source-uuid'],'@n1')
        self.assertEqual(map_references(encoded,{v:k for k,v in mapping.items()}),original)

    def scene(self):
        def n(parent,x,y,w,h,order,raw=None):
            return {'parent_id':parent,'bounds':{'x':x,'y':y,'width':w,'height':h},
                    'source_order':order,'raw_style':raw or {}}
        return {'page':n(None,0,0,375,812,0),
                'background':n('page',0,0,375,812,1),
                'group':n('page',10,700,350,70,3),
                'blur':n('group',10,700,350,70,4,{'blur':{'type':'background','radius':20}}),
                'label':n('group',30,710,30,20,5),
                'unrelated':n('page',10,100,30,20,2)}

    def test_component_includes_ancestor_backdrop_and_cross_boundary_effect(self):
        nodes=self.scene()
        nodes['mask']={'parent_id':'page','bounds':{'x':10,'y':700,'width':350,'height':60},'source_order':2}
        scenes=[{'kind':'boundary_overlay','node_ids':['label','mask']}]
        selected,included,reasons=closure(nodes,['group'],scenes)
        self.assertEqual(selected,{'group','blur','label'})
        self.assertTrue({'page','background','mask'}<=included)
        self.assertNotIn('unrelated',included)
        self.assertIn('backdrop_overlap_candidate',reasons['background'])

    def test_mask_chain_includes_nested_sibling_content(self):
        nodes=self.scene();nodes['blur']['raw_style']={'hasClippingMask':True}
        nodes['child']={'parent_id':'label','bounds':{'x':30,'y':710,'width':10,'height':10}}
        _,included,_=closure(nodes,['blur'],[])
        self.assertIn('child',included)

    def test_unknown_root_rejected(self):
        with self.assertRaises(ValueError):closure(self.scene(),['absent'],[])

    def test_whole_page_packet_preserves_every_brief_fact_and_asset_kind(self):
        f=preparation.PreparationTests();f.setUp();self.addCleanup(f.doCleanups)
        f.e['assets'][0]['kind']='render_fallback'
        plan=f.run_prepare();nodes={n['node_id']:n for n in f.e['nodes']}
        brief=implementation_brief(plan,nodes)
        packet=component_packet(brief,nodes,plan,['all'])
        self.assertEqual(expand_brief(packet),brief)
        self.assertEqual(packet['selection']['unselected_page_inventory'],0)
        self.assertEqual(expand_brief(packet)['assets'][0]['kind'],'render_fallback')
        self.assertEqual(unpack_packet(packet)['source_pins'],plan['pinned_inputs'])
        groups=unpack_packet(packet)['source_decision_groups']
        self.assertEqual({k for g in groups for k in g['node_ids']},
                         {n['node_id'] for n in plan['nodes']})
        self.assertTrue(all(g.get('state') and g.get('action') for g in groups))

    def test_component_query_rejects_changed_source(self):
        f=preparation.PreparationTests();f.setUp();self.addCleanup(f.doCleanups)
        plan=f.run_prepare();nodes={n['node_id']:n for n in f.e['nodes']}
        folder=f.root/'prepared';folder.mkdir()
        (folder/'page-plan.json').write_text(json.dumps(plan))
        (folder/'implementation-brief.json').write_text(json.dumps(implementation_brief(plan,nodes)))
        write_component(folder,[f.root/'source.json'],['all'])
        (f.root/'source.json').write_text(json.dumps({**f.e,'changed':True}))
        with self.assertRaisesRegex(ValueError,'changed'):
            write_component(folder,[f.root/'source.json'],['all'])


if __name__=='__main__':unittest.main()
