import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from renderer_capabilities import audit

class RendererCapabilityTests(unittest.TestCase):
    def node(self):
        return {'node_id':'badge','raw_style':{'fills':[{'color':{'a':.3},'opacity':.5}], 'borders':[{'gradient':{'type':'linear'}}], 'blur':{'isEnabled':True,'blurType':3}}}
    def test_each_effect_is_independent(self):
        r=audit([self.node()],{})
        self.assertEqual(set(r['unhandled']),{'fills.color','fills.opacity','borders.gradient.linear','borders.position.unknown','borders.gradient.coordinates','blur.3','blur.radius_mapping'})
    def test_partial_declaration_cannot_pass(self):
        r=audit([self.node()],{'supported':{'borders.gradient.linear':{'implementation':'paint','test':'test_gradient'}}})
        self.assertEqual(r['status'],'UNHANDLED_FEATURES')
        self.assertNotIn('borders.gradient.linear',r['unhandled'])
    def test_no_test_is_unhandled(self):
        r=audit([self.node()],{'supported':{'borders.gradient.linear':{'implementation':'paint'}}})
        self.assertIn('borders.gradient.linear',r['unhandled'])
    def test_disabled_not_required(self):
        n=self.node();n['raw_style']['borders'][0]['isEnabled']=False
        self.assertNotIn('borders.gradient.linear',audit([n],{})['requirements'])
    def test_outer_stroke_not_satisfied_by_color_support(self):
        n={'node_id':'dot','raw_style':{'borders':[{'color':{'a':1},'position':'外边框'}]}}
        r=audit([n],{'supported':{'borders.color':{'implementation':'paint','test':'test'}}})
        self.assertIn('borders.position.外边框',r['unhandled'])
    def test_export_frame_required_for_assets(self):
        n={'node_id':'icon','asset_ids':['export'],'raw_style':{}}
        self.assertIn('asset.export_frame',audit([n],{})['unhandled'])
    def test_composition_and_units_are_independent(self):
        n={'node_id':'card','raw_style':{'fills':[{'gradient':{'type':'linear','colorStops':[{'color':{'a':.65}}]}}], 'shadow':[{'type':'外阴影'}], 'blur':{'isEnabled':True,'blurType':3,'saturation':2},'radius':[3.4e38]}}
        r=audit([n],{})['requirements']
        for key in ['fills.gradient.background_dependency','fills.gradient.coordinates','shadow.kernel_and_extent','blur.radius_mapping','blur.saturation','geometry.extreme_radius']:
            self.assertIn(key,r)
if __name__=='__main__':unittest.main()
