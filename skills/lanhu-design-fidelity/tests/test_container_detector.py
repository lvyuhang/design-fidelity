"""Container geometry must ignore enclosed content, not boundary defects."""
import unittest
import test_fidelity
import numpy as np
from PIL import Image, ImageDraw
from visual_fidelity_gate import _mask, _measure_feature, _feature_comparison
from fidelity_contract import validate_contract


class ContainerDetectorTests(unittest.TestCase):
    detector = {'kind':'enclosed_container', 'foreground':{'kind':'light','luma_min':220}}

    def sample(self, dx=0, width=4, missing=False, content=False):
        im = Image.new('RGB', (100,60), (70,70,70))
        d = ImageDraw.Draw(im)
        if not missing:
            d.rounded_rectangle((10+dx,10,89+dx,49), radius=8, outline='white', width=width)
            if content:
                d.rectangle((25+dx,20,60+dx,35), fill='white')
        return np.asarray(im)

    def test_internal_content_does_not_move_container(self):
        self.assertTrue(np.array_equal(_mask(self.sample(),self.detector),
                                       _mask(self.sample(content=True),self.detector)))

    def test_shift_and_missing_remain_detectable(self):
        roi=[0,0,100,60]
        ref=_measure_feature(self.sample(),roi,1,self.detector)
        moved=_measure_feature(self.sample(dx=4),roi,1,self.detector)
        self.assertEqual(_feature_comparison(ref,moved)['center_x_delta'],4)
        self.assertIsNone(_measure_feature(self.sample(missing=True),roi,1,self.detector))

    def test_stroke_needs_separate_unfilled_measurement(self):
        # Filling holes intentionally erases stroke thickness. Never use it as
        # the sole paint check: retain the foreground stroke/effect check.
        normal=self.sample(); thin=self.sample(width=2)
        self.assertTrue(np.array_equal(_mask(normal,self.detector),_mask(thin,self.detector)))
        foreground=self.detector['foreground']
        self.assertLess(_mask(thin,foreground).sum(),_mask(normal,foreground).sum()*.65)

    def test_contract_rejects_container_without_paint_check(self):
        f=test_fidelity.GateTests(); f.setUp(); self.addCleanup(f.doCleanups)
        f.c['features']['icon']['detector']=self.detector
        with self.assertRaisesRegex(ValueError,'paint_region'):
            validate_contract(f.c, {n['node_id']:n for n in f.e['nodes']})
