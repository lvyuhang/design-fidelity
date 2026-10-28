import unittest
import test_fidelity as fixtures
import numpy as np
from exclusion_masks import build_keep_mask
from fidelity_contract import validate_contract

class MaskTests(unittest.TestCase):
    def test_contract_rejects_fully_masked_blocking_region(self):
        f=fixtures.GateTests(); f.setUp()
        try:
            f.c['exclude_rects']=[{'rect':[70,70,10,10],'reason':'missing photo'}]
            f.c['regions']['photo']={'label':'photo','rect':[70,70,10,10],
                                     'max_mae':1,'max_p95':2}
            with self.assertRaisesRegex(ValueError, 'regions.photo: completely excluded'):
                validate_contract(f.c, {n['node_id']:n for n in f.e['nodes']})
            f.c['protect_regions']=[{'rect':[72,72,4,4],'reason':'foreground badge'}]
            validate_contract(f.c, {n['node_id']:n for n in f.e['nodes']})
        finally:f.doCleanups()

    def test_shape_preserves_corners_and_protection_wins_union(self):
        masks=[{'shape':'ellipse','rect':[10,10,40,40],'inset':1,'reason':'missing photo'}]
        keep=build_keep_mask([64,64],1,masks)
        self.assertTrue(keep[10,10]); self.assertFalse(keep[30,30])
        masks.append({'rect':[40,40,10,10],'reason':'overlapping content'})
        keep=build_keep_mask([64,64],1,masks,[{'rect':[40,40,8,8],'reason':'foreground status'}])
        self.assertTrue(keep[44,44])
        self.assertTrue(keep[10,30])

    def test_polygon_and_invalid_input(self):
        keep=build_keep_mask([64,64],1,[{'shape':'polygon','points':[[10,10],[30,10],[10,30]],'reason':'source clip'}])
        self.assertFalse(keep[15,15]);self.assertTrue(keep[29,29])
        for spec in [{'shape':'wrong','reason':'x'}, {'rect':[-1,0,3,3],'reason':'x'}, {'rect':[0,0,3,3]}]:
            with self.assertRaises(ValueError):build_keep_mask([64,64],1,[spec])

    def test_real_gate_detects_protected_corruption(self):
        f=fixtures.GateTests(); f.setUp()
        try:
            f.c['regions']['whole']['max_mae']=0
            f.c['exclude_shapes']=[{'shape':'ellipse','rect':[65,65,20,20],'reason':'missing content'}]
            f.assert_gate(0,'PASS_WITH_EXCLUSIONS','photo')
            f.c['protect_regions']=[{'rect':[72,72,4,4],'reason':'foreground badge'}]
            f.assert_gate(1,'FAIL','photo')
        finally:f.doCleanups()
