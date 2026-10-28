import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from background_bias import measure
class BiasTests(unittest.TestCase):
 def test_one_channel_drift_fails(self):
  a=np.full((8,8,3),255,dtype=np.uint8);b=a.copy();b[:,:,1]=254
  self.assertEqual(measure(a,b,{'center':[0,0,8,8]})['status'],'LOCAL_FAIL')
 def test_equal_passes(self):
  a=np.full((8,8,3),255,dtype=np.uint8)
  self.assertEqual(measure(a,a,{'center':[0,0,8,8]})['status'],'LOCAL_PASS')
 def test_regions_do_not_cancel_each_other(self):
  a=np.full((8,8,3),128,dtype=np.uint8);b=a.copy();b[:4,:,1]=127;b[4:,:,1]=129
  self.assertEqual(measure(a,b,{'top':[0,0,8,4],'bottom':[0,4,8,8]})['status'],'LOCAL_FAIL')
