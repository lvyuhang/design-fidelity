"""Adversarial end-to-end checks for the gaps found in the 2.8 audit."""
import json
import subprocess
import sys
import unittest
import numpy as np
from PIL import Image, ImageDraw
from unittest.mock import patch
import test_fidelity as fixtures
from source_requirements import (add_sample_drafts, effects, requirements, source_gaps,
    validate_exclusion, validate_visual_exclusion, is_small_visual)
from fidelity_contract import inventory, sha256
from visual_fidelity_gate import _vector_effect_metric

DRAW = '''from PIL import Image, ImageDraw
import sys
mode=sys.argv[2]
im=Image.new('RGB',(100,100),'white');d=ImageDraw.Draw(im)
d.rectangle((10,10,19,19),fill='red');d.rectangle((30,10,39,19),fill='black')
if mode!='no_shadow':
 for y,color in [(70,(225,210,170)),(74,(235,220,185)),(82,(250,246,230))]:d.line((10,y,89,y),fill=color)
if mode!='no_gradient':
 for y,color in [(10,(250,245,235)),(50,(230,220,190)),(90,(200,180,150))]:d.line((45,y,55,y),fill=color)
im.save(sys.argv[1])
'''

class SourceObligationTests(unittest.TestCase):
    setUp=fixtures.GateTests.setUp
    save=fixtures.GateTests.save
    render=fixtures.GateTests.render
    gate=fixtures.GateTests.gate
    assert_gate=fixtures.GateTests.assert_gate

    def test_unchanged_source_cannot_exempt_unverified_implementation(self):
        nodes = {'badge':{'bounds':{'x':10,'y':10,'width':34,'height':14}}}
        for proof in ({}, {'kind':'source_unchanged'}, {'kind':'reuse'}):
            with self.subTest(proof=proof), self.assertRaisesRegex(ValueError,'not an exemption'):
                validate_exclusion('badge', {'exclusion':proof,'reason':'same source and assets'}, nodes, [100,100])

    def test_nonvisibility_exclusions_require_source_geometry(self):
        nodes = {'badge':{'node_id':'badge','source_order':1,
            'bounds':{'x':10,'y':10,'width':34,'height':14}},
            'cover':{'node_id':'cover','source_order':2,
                'bounds':{'x':0,'y':0,'width':100,'height':100},
                'raw_style':{'opacity':100,'radius':[4],
                    'points':[{'point':{'x':x,'y':y}} for x,y in [(0,0),(1,0),(1,1),(0,1)]],
                    'fills':[{'type':'color','color':{'a':1}}]}}}
        proof={'exclusion':{'kind':'fully_occluded','by':'cover'}}
        validate_exclusion('badge',proof,nodes,[100,100])
        nodes['cover']['raw_style']['opacity']=20
        with self.assertRaisesRegex(ValueError,'opaque'):
            validate_exclusion('badge',proof,nodes,[100,100])
        with self.assertRaisesRegex(ValueError,'intersects'):
            validate_exclusion('badge',{'exclusion':{'kind':'outside_canvas'}},nodes,[100,100])
        nodes['badge']['bounds']['x']=100
        validate_exclusion('badge',{'exclusion':{'kind':'outside_canvas'}},nodes,[100,100])

    def test_clipping_mask_is_not_an_independent_small_visual(self):
        node={'node_type':'shape','bounds':{'x':0,'y':0,'width':20,'height':20},
              'raw_style':{'hasClippingMask':1}}
        self.assertFalse(is_small_visual(node))

    @patch('source_requirements.pending_allowed', return_value=True)
    def test_missing_backdrop_visual_exclusion_requires_executable_verification(self, _):
        nodes={'photo':{'bounds':{'x':0,'y':0,'width':20,'height':20},'source_order':1},
               'badge':{'bounds':{'x':5,'y':5,'width':8,'height':8},'source_order':2}}
        contract={'implementation_inputs':['scene_test.dart'],
                  'node_decisions':{'photo':{'mode':'missing_asset_placeholder'}}}
        decision={'visual_exclusion':{'kind':'missing_backdrop','by':'photo',
                  'verification':'scene_test.dart','assertion':'exact frame and asset binding'}}
        validate_visual_exclusion('badge',decision,nodes,contract)
        decision['visual_exclusion'].pop('assertion')
        with self.assertRaisesRegex(ValueError,'verification and assertion'):
            validate_visual_exclusion('badge',decision,nodes,contract)

    def test_gradient_sample_moves_along_same_band_when_center_is_covered(self):
        surface={'node_id':'surface','source_order':1,'node_type':'shape',
                 'bounds':{'x':0,'y':0,'width':100,'height':100},
                 'raw_style':{'fills':[{'type':'gradient','isEnabled':True,'gradient':{
                     'type':'linear','from':{'x':.5,'y':0},'to':{'x':.5,'y':1}}}]}}
        cover={'node_id':'cover','source_order':2,'node_type':'bitmap',
               'bounds':{'x':40,'y':40,'width':20,'height':20},'raw_style':{}}
        req=next(r for r in requirements({'surface':surface,'cover':cover},[100,100])
                 if r['node_id']=='surface')
        middle=next(s for s in req['samples'] if s['role']=='middle')
        self.assertEqual(middle['rect'][1],50)
        self.assertNotEqual(middle['rect'][0],50)
        self.assertIn('same gradient band',middle['review_reason'])

    def sync(self):
        (self.root/'source.json').write_text(json.dumps(self.e))
        self.c['pinned_files']['source.json']=sha256(self.root/'source.json')

    def effect_fixture(self, kind):
        (self.root/'render.py').write_text(DRAW)
        subprocess.run([sys.executable,str(self.root/'render.py'),str(self.root/'reference.png'),'normal'],check=True)
        self.c['pinned_files']['reference.png']=sha256(self.root/'reference.png')
        n=self.e['nodes'][2]
        if kind=='shadow':
            n['bounds']['height']=70
            n['raw_style']={'shadow':[{'isEnabled':True,'offsetY':4,'blurRadius':8}]}
        else:
            n['raw_style']={'fills':[{'type':'gradient','isEnabled':True,'gradient':{
                'type':'linear','from':{'x':.5,'y':0},'to':{'x':.5,'y':1}}}]}
        self.e['nodes'][0]['parent_id']='surface';self.e['nodes'][1]['parent_id']='surface'
        self.sync()

    def add_samples(self):
        nodes={n['node_id']:n for n in self.e['nodes']}
        add_sample_drafts(self.c,nodes,4)
        for key,s in self.c['color_samples'].items():
            if s.get('effect'):self.c['coverage']['surface']['checks'].append('color_samples.'+key)

    def test_old_contract_needs_explicit_migration(self):
        self.c.pop('workflow_version');self.assert_gate(2,'NOT_EVALUATED')

    def test_missing_implementation_decision_is_not_accepted(self):
        self.c['node_decisions'].pop('surface');self.assert_gate(2,'NOT_EVALUATED')

    def test_unknown_visual_evidence_is_not_assumed_plain(self):
        self.e['nodes'][2]['raw_style']={'ddsOriginFrame':{'x':0,'y':0,'width':100,'height':100}}
        self.sync();self.assert_gate(2,'NOT_EVALUATED')

    def test_painted_shape_without_geometry_or_asset_is_input_gap(self):
        node={'node_id':'wifi','node_type':'shape','source_visible':True,
              'bounds':{'x':10,'y':10,'width':17,'height':11},
              'raw_style':{'fills':[{'isEnabled':True,'color':{'a':1}}]}}
        self.assertEqual(source_gaps({'wifi':node})[0]['kind'],'geometry_source_unknown')
        node['asset_ids']=['wifi-original']
        self.assertEqual(source_gaps({'wifi':node}),[])

    def test_geometry_gap_respects_asset_ancestry_but_requires_final_disposition(self):
        child={'node_type':'shape','parent_id':'group',
               'bounds':{'x':1,'y':1,'width':10,'height':10},
               'raw_style':{'fills':[{'color':{'a':1}}]}}
        nodes={'child':child,'group':{'asset_ids':['original']}}
        self.assertEqual(source_gaps(nodes),[])
        self.assertTrue(source_gaps(nodes,decisions={'child':{'mode':'native_exact'}}))
        d={'child':{'mode':'original_asset','asset':'group.png'}}
        self.assertTrue(source_gaps(nodes,decisions=d,assets=[]))
        self.assertEqual(source_gaps(nodes,decisions=d,assets=['group.png']),[])
        d['child']={'mode':'missing_asset_placeholder','shape':'circle'}
        self.assertEqual(source_gaps(nodes,decisions=d),[])
        d['child']={'mode':'render_fallback','asset':'source.png'}
        self.assertEqual(source_gaps(nodes,decisions=d,assets=['source.png']),[])

    def test_disabled_paint_does_not_require_missing_geometry(self):
        n={'node_type':'shape','bounds':{'x':0,'y':0,'width':10,'height':10},
           'raw_style':{'fills':[{'isEnabled':False,'color':{'a':1}}]}}
        self.assertEqual(source_gaps({'node':n}),[])

    def test_grouped_small_decoration_cannot_use_whole_page_coverage(self):
        n={'node_id':'quote','node_type':'shape','bounds':{'x':80,'y':20,'width':4,'height':3},'raw_style':{'fills':[]}}
        self.e['nodes'].append(n);self.c['source_scope']['expected_node_count']=4
        self.c['node_decisions']['quote']={'mode':'native_exact','implementation':'render.py','symbol':'quote'}
        self.c['regions']['whole']['node_ids']=['surface','quote']
        self.c['coverage']['quote']={'status':'covered','checks':['regions.whole']}
        self.sync();report=self.assert_gate(2,'NOT_EVALUATED')
        self.assertIn('independent small_visual',report['reason'])

    def test_parent_shadow_cannot_use_center_sample(self):
        self.effect_fixture('shadow');report=self.assert_gate(2,'NOT_EVALUATED')
        self.assertIn('missing effect sample',report['reason'])

    def test_generated_shadow_checks_accept_correct_and_reject_missing(self):
        self.effect_fixture('shadow');self.add_samples();self.assert_gate(0,'PASS')
        report=self.assert_gate(1,'FAIL','no_shadow')
        self.assertTrue(report['candidates']['test']['regions']['whole']['passed'])
        failures=[s for s in report['candidates']['test']['colors'].values() if not s['passed']]
        self.assertEqual(len(failures),3)

    def test_asset_can_have_visible_feature_and_independent_effect_checks(self):
        self.effect_fixture('shadow');self.add_samples()
        self.e['nodes'][2]['asset_ids']=['panel-asset'];self.sync()
        self.c['features']['panel']={'label':'panel','node_ids':['surface'],
            'detector':{'kind':'light','luma_min':250,'min_pixels':4},
            'limits':{'max_center_delta':1,'max_size_delta':1}}
        self.c['coverage']['surface']['checks'].append('features.panel')
        self.assert_gate(0,'PASS')

    def test_gradient_cannot_omit_middle_check(self):
        self.effect_fixture('gradient');self.add_samples()
        name=next(k for k,s in self.c['color_samples'].items() if s.get('effect',{}).get('role')=='middle')
        self.c['color_samples'].pop(name);self.c['coverage']['surface']['checks'].remove('color_samples.'+name)
        self.assert_gate(2,'NOT_EVALUATED')

    def test_generated_gradient_checks_accept_correct_and_reject_missing(self):
        self.effect_fixture('gradient');self.add_samples();self.assert_gate(0,'PASS')
        report=self.assert_gate(1,'FAIL','no_gradient')
        self.assertTrue(report['candidates']['test']['regions']['whole']['passed'])
        self.assertTrue(any(not s['passed'] for s in report['candidates']['test']['colors'].values()))

    def test_samples_cannot_be_relabelled_same_center(self):
        self.effect_fixture('shadow');self.add_samples()
        for s in self.c['color_samples'].values():
            if s.get('effect'): s['rect']=[49.5,73.5,1,1]
        self.assert_gate(2,'NOT_EVALUATED')

    def test_reviewed_exposed_gradient_sample_catches_middle_drift(self):
        self.effect_fixture('gradient')
        draw=DRAW.replace('d.line((45,y,55,y),fill=color)', 'd.line((10,y,89,y),fill=color)')
        draw=draw.replace("im.save(sys.argv[1])", "if mode=='middle_drift':d.line((10,50,89,50),fill='white')\nd.rectangle((30,40,70,60),fill='white')\nim.save(sys.argv[1])")
        (self.root/'render.py').write_text(draw)
        subprocess.run([sys.executable,str(self.root/'render.py'),str(self.root/'reference.png'),'normal'],check=True)
        self.c['pinned_files']['reference.png']=sha256(self.root/'reference.png')
        self.add_samples()
        for s in self.c['color_samples'].values():
            if s.get('effect',{}).get('role')=='middle':
                s['rect']=[20,50,1,1]
                s['review_reason']='White child covers center; inspect confirms exposed left strip at same gradient band.'
        self.assert_gate(0,'PASS')
        report=self.assert_gate(1,'FAIL','middle_drift')
        self.assertTrue(report['candidates']['test']['regions']['whole']['passed'])

    def test_review_reason_cannot_move_gradient_check_to_wrong_band(self):
        self.effect_fixture('gradient');self.add_samples()
        for s in self.c['color_samples'].values():
            if s.get('effect',{}).get('role')=='middle':
                s.update(rect=[20,10,1,1],review_reason='claimed exposed point')
        self.assert_gate(2,'NOT_EVALUATED')

    def test_effect_samples_cannot_target_sibling(self):
        self.effect_fixture('shadow');self.add_samples()
        for s in self.c['color_samples'].values():
            if s.get('effect'):s['node_ids']=['text','surface']
        self.assert_gate(2,'NOT_EVALUATED')

    def test_unsupported_gradient_is_review_work_not_auto_pass(self):
        self.effect_fixture('gradient')
        self.e['nodes'][2]['raw_style']['fills'][0]['gradient']['type']='radial'
        self.sync();self.add_samples();r=self.assert_gate(2,'NOT_EVALUATED')
        self.assertIn('automatic samples unavailable',r['reason'])

    def test_vector_effect_profile_accepts_rasterizer_noise_but_rejects_border_regressions(self):
        reference=Image.new('RGB',(128,128),'white')
        candidate=Image.new('RGB',(128,128),'white')
        missing=Image.new('RGB',(128,128),'white')
        shifted=Image.new('RGB',(128,128),'white')
        thinner=Image.new('RGB',(128,128),'white')
        # Equivalent 4x vector rasterizations may differ by one physical pixel.
        ImageDraw.Draw(reference).rounded_rectangle((16,16,111,111),radius=16,outline=(235,209,166),width=2)
        ImageDraw.Draw(candidate).rounded_rectangle((17,16,112,111),radius=16,outline=(235,209,166),width=2)
        # These are real final-scale regressions: 1 logical px displacement and
        # a 50% loss of the already-thin source stroke.
        ImageDraw.Draw(shifted).rounded_rectangle((20,16,115,111),radius=16,outline=(235,209,166),width=2)
        ImageDraw.Draw(thinner).rounded_rectangle((16,16,111,111),radius=16,outline=(235,209,166),width=1)
        rect=[4,4,24,24]
        close=_vector_effect_metric(np.asarray(reference),np.asarray(candidate),rect,4)
        self.assertLessEqual(close['p95_max_channel'],12)
        for label, image in [('missing',missing),('shifted',shifted),('thinner',thinner)]:
            with self.subTest(label=label):
                regression=_vector_effect_metric(np.asarray(reference),np.asarray(image),rect,4)
                self.assertGreater(regression['p95_max_channel'],12)

    def test_disabled_effect_and_one_percent_opacity_are_distinguished(self):
        n={'bounds':{'x':0,'y':0,'width':20,'height':20},'raw_style':{
            'opacity':1,'shadow':[{'isEnabled':True,'enabled':False}]}}
        self.assertEqual(set(effects(n)),{'opacity'})
        nodes={'parent':n,'child':{'parent_id':'parent','bounds':{'x':0,'y':0,'width':2,'height':2}}}
        self.assertIn('parent',inventory(nodes))

    def test_sample_generation_does_not_mark_ready_or_remove_review(self):
        self.effect_fixture('gradient');self.c['status']='draft';self.add_samples()
        self.assertEqual(self.c['status'],'draft')
        self.assertTrue(requirements({n['node_id']:n for n in self.e['nodes']},[100,100])[0]['needs_review'])

if __name__=='__main__': unittest.main()
