"""Fault injection for tiny visuals; synthetic source, fresh render receipts."""
import subprocess
import sys
import unittest
import json
import numpy as np

import test_fidelity as fixture_support
from visual_fidelity_gate import _mask

DRAW = '''from PIL import Image, ImageDraw
import sys
mode=sys.argv[2]
im=Image.new('RGB',(100,100),'white'); d=ImageDraw.Draw(im)
d.rectangle((30,10,39,19),fill='black')
if mode in ('normal','wrong_shape'):
 for i in range(10): d.point((10+i,10+i if mode=='normal' else 19-i),fill='red')
elif mode in ('circle','rectangle'):
 getattr(d,'ellipse' if mode=='circle' else 'rectangle')((10,10,19,19),fill='red')
else: d.line((10,10,19,19),fill='red')
if mode!='no_underline': d.rectangle((60,30,79,31),fill=(255,225,180))
if mode!='no_shadow':
 d.rectangle((60,50,79,50),fill=(245,224,185))
 d.rectangle((60,51,79,51),fill=(252,244,225))
im.save(sys.argv[1])
'''


class SmallVisualTests(unittest.TestCase):
    setUp = fixture_support.GateTests.setUp
    save = fixture_support.GateTests.save
    render = fixture_support.GateTests.render
    gate = fixture_support.GateTests.gate
    assert_gate = fixture_support.GateTests.assert_gate

    def test_relative_dark_detector_is_background_independent(self):
        light=np.full((12,24,3),240,dtype=np.uint8); light[3:9,4:20]=120
        dark=np.full((12,24,3),150,dtype=np.uint8); dark[3:9,4:20]=60
        detector={'kind':'relative_dark','percentile':80,'delta':20}
        self.assertTrue(np.array_equal(_mask(light,detector),_mask(dark,detector)))

    def fixture(self, reference_mode='normal'):
        (self.root/'render.py').write_text(DRAW)
        subprocess.run([sys.executable,str(self.root/'render.py'),str(self.root/'reference.png'),reference_mode],check=True)
        self.c['pinned_files']['reference.png']=fixture_support.sha256(self.root/'reference.png')
        icon=self.c['features']['icon']
        icon['profile']='small_visual'
        icon['limits'].update(max_edge_delta=0.5,max_ink_ratio_delta=0.1,max_mask_iou_loss=0.2)
        self.c['color_samples'].update({
            'underline':{'label':'underline','rect':[60,30,20,2],'max_channel_delta':6},
            'shadow_edge':{'label':'shadow edge','rect':[60,50,20,1],'max_channel_delta':6},
            'shadow_fade':{'label':'shadow fade','rect':[60,51,20,1],'max_channel_delta':6},
        })

    def test_correct_shape_passes(self):
        self.fixture(); self.assert_gate(0,'PASS')

    def test_wrong_shape_same_bbox_center_and_ink_is_rejected(self):
        self.fixture(); report=self.assert_gate(1,'FAIL','wrong_shape')
        candidate=report['candidates']['test']
        self.assertTrue(candidate['regions']['whole']['passed'])
        feature=candidate['features']['icon']
        self.assertEqual(feature['metrics']['ink_ratio'],1)
        self.assertEqual(feature['metrics']['max_edge_delta'],0)
        self.assertEqual(len(feature['failures']),1)
        self.assertIn('mask_iou_loss',feature['failures'][0])

    def test_small_visual_cannot_omit_shape_check(self):
        self.fixture(); del self.c['features']['icon']['limits']['max_mask_iou_loss']
        self.assert_gate(2,'NOT_EVALUATED')

    def test_small_visual_cannot_cover_whole_row(self):
        self.fixture(); self.c['features']['icon']['node_ids'].append('text')
        self.assert_gate(2,'NOT_EVALUATED')

    def test_shape_limit_out_of_range_rejected(self):
        self.fixture(); self.c['features']['icon']['limits']['max_mask_iou_loss']=1.1
        self.assert_gate(2,'NOT_EVALUATED')

    def test_missing_underline_rejected_despite_whole_region_pass(self):
        self.fixture(); report=self.assert_gate(1,'FAIL','no_underline')
        self.assertTrue(report['candidates']['test']['regions']['whole']['passed'])
        self.assertFalse(report['candidates']['test']['colors']['underline']['passed'])

    def test_missing_shadow_rejected_despite_whole_region_pass(self):
        self.fixture(); report=self.assert_gate(1,'FAIL','no_shadow')
        self.assertTrue(report['candidates']['test']['regions']['whole']['passed'])
        self.assertFalse(report['candidates']['test']['colors']['shadow_edge']['passed'])
        self.assertFalse(report['candidates']['test']['colors']['shadow_fade']['passed'])

    def test_circle_placeholder_accepts_expected_shape(self):
        self.fixture('circle'); self.assert_gate(0,'PASS','circle')

    def test_circle_placeholder_rejects_rectangle(self):
        # Separate synthetic placeholder contract, never compare the pink block to a photo.
        self.fixture('circle'); report=self.assert_gate(1,'FAIL','rectangle')
        self.assertEqual(report['candidates']['test']['features']['icon']['metrics']['max_edge_delta'],0)

    def test_initializer_discovers_parent_effect_and_vector_hint(self):
        self.e['nodes'][0]['parent_id']='surface'
        self.e['nodes'][0]['raw_style']={'points':[{'point':{'x':0,'y':0}}]}
        self.e['nodes'][2]['raw_style']={'shadows':[{'isEnabled':True}]}
        (self.root/'source.json').write_text(json.dumps(self.e))
        result=subprocess.run([sys.executable,str(fixture_support.SCRIPTS/'init_visual_contract.py'),
            '--evidence',str(self.root/'source.json'),'--reference',str(self.root/'reference.png'),
            '--output',str(self.root/'draft.json'),'--name','effects'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        hints=json.loads((self.root/'draft.suggestions.json').read_text())
        self.assertEqual(hints['effect_candidates'][0]['node_id'],'surface')
        icon=next(n for n in hints['nodes'] if n['node_id']=='icon')
        self.assertTrue(icon['evidence_hints']['vector_data_present'])
        self.assertEqual(icon['implementation'],'pending')

    def test_disabled_effect_not_suggested(self):
        from init_visual_contract import visual_hints
        self.assertEqual(visual_hints({'raw_style':{'shadows':[{'isEnabled':False}]}})['effect_fields'],[])


if __name__ == '__main__': unittest.main()
