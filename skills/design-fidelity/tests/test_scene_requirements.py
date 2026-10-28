"""Portable fail-closed scene checks; source IDs/names are arbitrary fixtures."""
import json
import sys
import unittest
import test_fidelity as fixtures
from scene_requirements import scene_requirements, validate_scene_checks
from fidelity_contract import sha256


class SceneTests(unittest.TestCase):
    setUp = fixtures.GateTests.setUp
    save = fixtures.GateTests.save
    render = fixtures.GateTests.render
    gate = fixtures.GateTests.gate
    assert_gate = fixtures.GateTests.assert_gate

    def panel(self):
        self.e['nodes'][2]['raw_style']['blur'] = {'isEnabled':True,'blurType':3,'radius':2}
        (self.root/'source.json').write_text(json.dumps(self.e))
        self.c['pinned_files']['source.json'] = sha256(self.root/'source.json')

    def test_flat_pixel_match_does_not_prove_backdrop(self):
        self.panel()
        report = self.assert_gate(2,'NOT_EVALUATED')
        self.assertIn('surface/backdrop',report['reason'])

    def checks(self):
        self.panel()
        # The project test exercises its rendering operation on patterned AND
        # uniform backgrounds. A flat reference alone cannot detect blur loss.
        (self.root/'panel.py').write_text('''from PIL import Image,ImageFilter
import json
def render(bg):
 cfg=json.load(open('panel.json'))
 if not cfg['no_blur']:bg=bg.filter(ImageFilter.GaussianBlur(2))
 return Image.blend(bg,Image.new('RGB',bg.size,'white'),1 if cfg['opaque'] else .9)
''')
        (self.root/'probe.py').write_text('''from PIL import Image,ImageFilter,ImageChops
from panel import render
for mode in ['black','white','stripes']:
 bg=Image.new('RGB',(48,48),'white' if mode=='white' else 'black')
 if mode=='stripes':
  for x in range(48):
   for y in range(48):bg.putpixel((x,y),(255,255,255) if x%8<4 else (0,0,0))
 expected=Image.blend(bg.filter(ImageFilter.GaussianBlur(2)),Image.new('RGB',bg.size,'white'),.9)
 assert ImageChops.difference(render(bg),expected).getbbox() is None,mode
''')
        self.c['implementation_inputs'] += ['panel.py','panel.json','probe.py']
        self.c['scene_checks'] = {'panel':{'obligations':['surface/backdrop'],
            'command':[sys.executable,'probe.py'], 'test_file':'probe.py',
            'assertions':'Render actual panel with source radius/alpha on black, white and stripe backgrounds.'}}
        self.state()

    def state(self):
        (self.root/'panel.json').write_text(json.dumps(dict(no_blur=False,opaque=False)))

    def test_executable_checks_reject_blur_and_transparency_mutations(self):
        self.checks()
        self.assert_gate(0,'PASS')
        for mutation in ['no_blur','opaque']:
            (self.root/'panel.json').write_text(json.dumps({'no_blur':mutation=='no_blur','opaque':mutation=='opaque'}))
            result = self.render()
            self.assertEqual(result.returncode,2)
            self.assertIn('Scene check panel failed', result.stderr)
            self.assertEqual(json.loads((self.root/'receipt.json').read_text())['status'],'NOT_EVALUATED')

    def test_scene_receipt_required_and_test_file_changes_invalidate_it(self):
        self.checks();self.assert_gate(0,'PASS')
        r=json.loads((self.root/'receipt.json').read_text());r.pop('scene_checks')
        (self.root/'receipt.json').write_text(json.dumps(r))
        self.assertIn('scene-check',self.gate()[1]['reason'])
        self.render()
        with (self.root/'probe.py').open('a') as f:f.write('\n# changed test\n')
        self.assertIn('Inputs changed',self.gate()[1]['reason'])

    def test_missing_content_cannot_exempt_effect(self):
        nodes={'photo':{'bounds':{'x':0,'y':0,'width':100,'height':100},
            'raw_style':{'opacity':50}}}
        c={'node_decisions':{'photo':{'mode':'missing_asset_placeholder'}}}
        with self.assertRaisesRegex(ValueError,'placeholder_effect/opacity'):
            validate_scene_checks(c,nodes)

    def test_source_order_boundary_crossing_survives_missing_photo(self):
        nodes={
            'mask':{'parent_id':'card','source_order':1,'bounds':{'x':10,'y':10,'width':70,'height':70},'raw_style':{'hasClippingMask':True}},
            'photo':{'parent_id':'card','source_order':2,'bounds':{'x':10,'y':10,'width':70,'height':70},'raw_style':{}},
            'rim':{'parent_id':'page','source_order':3,'asset_ids':['rim-asset'],'bounds':{'x':60,'y':60,'width':24,'height':24},'raw_style':{}}}
        req=scene_requirements(nodes)
        self.assertEqual({r['id'] for r in req},{'mask/clip','rim/boundary/mask'})
        self.assertEqual(req[-1]['node_ids'],['rim','mask'])
        c={'node_decisions':{'photo':{'mode':'missing_asset_placeholder'}}}
        with self.assertRaisesRegex(ValueError,'rim/boundary/mask'):validate_scene_checks(c,nodes)
        nodes['rim']['source_order']=0
        self.assertEqual(len(scene_requirements(nodes)),1)

    def test_unknown_or_unhashed_tests_cannot_satisfy_check(self):
        self.checks();nodes={n['node_id']:n for n in self.e['nodes']}
        self.c['scene_checks']['panel']['test_file']='unhashed.py'
        with self.assertRaisesRegex(ValueError,'hashed'):validate_scene_checks(self.c,nodes)
        self.c['scene_checks']['panel']['obligations']=['invented']
        with self.assertRaisesRegex(ValueError,'unknown'):validate_scene_checks(self.c,nodes)

    def test_test_cwd_is_honored_and_receipt_bound(self):
        self.checks()
        app = self.root/'app';app.mkdir()
        for name in ['panel.py','panel.json','probe.py']:
            (self.root/name).rename(app/name)
        self.c['implementation_inputs'] = ['render.py','app/panel.py','app/panel.json','app/probe.py']
        self.c['scene_checks']['panel'].update(cwd='app',test_file='app/probe.py')
        self.assert_gate(0,'PASS')
        r=json.loads((self.root/'receipt.json').read_text())
        r['scene_checks']['panel']['cwd']='elsewhere'
        (self.root/'receipt.json').write_text(json.dumps(r))
        self.assertIn('did not succeed',self.gate()[1]['reason'])

    def test_disabled_backdrop_is_not_work(self):
        self.panel();nodes={n['node_id']:n for n in self.e['nodes']}
        nodes['surface']['raw_style']['blur']['isEnabled']=False
        self.assertEqual(scene_requirements(nodes),[])


if __name__ == '__main__': unittest.main()
