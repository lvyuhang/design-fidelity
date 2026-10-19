"""Portable behavioral regressions; all data and generated fonts are synthetic."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from fidelity_contract import sha256

RENDER = '''from PIL import Image, ImageDraw
import sys
mode=sys.argv[2]
im=Image.new('RGB',(100,100),'white');d=ImageDraw.Draw(im)
if mode!='missing':
 y=14 if mode=='shift' else 10
 d.rectangle((10,y,19,y+9),fill='blue' if mode=='color' else 'red')
if mode!='missing_text':d.rectangle((30,10,39,19),fill='black')
if mode=='photo':d.rectangle((70,70,79,79),fill='blue')
im.save(sys.argv[1])
'''


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'render.py').write_text(RENDER)
        # Minimal valid font with A only; no licensed font data in the test bundle.
        from fontTools.fontBuilder import FontBuilder
        from fontTools.pens.ttGlyphPen import TTGlyphPen
        fb = FontBuilder(1000, isTTF=True)
        fb.setupGlyphOrder(['.notdef','A'])
        glyphs = {}
        for key in ['.notdef','A']:
            pen = TTGlyphPen(None);pen.moveTo((0,0));pen.lineTo((0,500));pen.lineTo((400,500));pen.lineTo((400,0));pen.closePath();glyphs[key]=pen.glyph()
        fb.setupCharacterMap({65:'A'});fb.setupGlyf(glyphs)
        fb.setupHorizontalMetrics({k:(500,0) for k in glyphs});fb.setupHorizontalHeader(ascent=800,descent=-200)
        fb.setupNameTable({'familyName':'Fixture','styleName':'Regular','uniqueFontIdentifier':'Fixture','fullName':'Fixture Regular','psName':'Fixture-Regular'})
        fb.setupOS2();fb.setupPost();fb.setupMaxp();fb.save(self.root/'font.ttf')
        nodes=[{'node_id':'icon','asset_ids':['icon-asset'],'bounds':{'x':10,'y':10,'width':10,'height':10}},
               {'node_id':'text','text':'A','bounds':{'x':30,'y':10,'width':10,'height':10}},
               {'node_id':'surface','bounds':{'x':0,'y':0,'width':100,'height':100}}]
        self.e={'snapshot_id':'test-snapshot','resolved_version':'test-version','canvas':{'width':100,'height':100},'coordinate_space':'source_canvas','coordinate_mapping':{'verified':True},'nodes':nodes}
        (self.root/'source.json').write_text(json.dumps(self.e))
        subprocess.run([sys.executable,str(self.root/'render.py'),str(self.root/'reference.png'),'normal'],check=True)
        self.c={'schema_version':2,'source_scope':{'kind':'page','expected_node_count':3},'status':'ready','source_snapshot':'test-snapshot','source_version':'test-version','canvas':[100,100],'render_scale':1,
                'reference':'reference.png','source_documents':['source.json'],
                'regions':{'whole':{'label':'whole','rect':[0,0,100,100],'max_mae':6,'max_p95':32}},
                'features':{},'relations':{'row':{'label':'row','features':['icon','text'],'metric':'center_y','max_delta':0.75}},
                'color_samples':{'surface':{'label':'surface','node_ids':['surface'],'anchor':[0.5,0.5],'size':[4,4],'max_channel_delta':4}},
                'coverage':{'icon':{'status':'covered','checks':['features.icon']},'text':{'status':'covered','checks':['features.text']},'surface':{'status':'covered','checks':['color_samples.surface']}},
                'implementation_inputs':['render.py'], 'assets':[], 'fonts':[{'path':'font.ttf','node_ids':['text']}],
                'environment':{'renderer':'Pillow-fixture','renderer_version':'1','platform':'test','locale':'en','state':'static','text_scale':1},
                'pinned_files':{p:sha256(self.root/p) for p in ['source.json','reference.png','font.ttf']}}
        for key,det in [('icon',{'kind':'color_distance','rgb':[255,0,0],'max_distance':10,'min_pixels':4}),('text',{'kind':'dark','luma_max':10,'min_pixels':4})]:
            self.c['features'][key]={'label':key,'node_ids':[key],'padding':[5]*4,'detector':det,'limits':{'max_center_delta':1,'max_size_delta':1.5}}

    def save(self):
        (self.root/'contract.json').write_text(json.dumps(self.c,allow_nan=False))

    def render(self,mode='normal',command=None):
        self.save()
        cmd=command or [sys.executable,str(self.root/'render.py'),str(self.root/'candidate.png'),mode]
        return subprocess.run([sys.executable,str(SCRIPTS/'render_with_receipt.py'),'--contract',str(self.root/'contract.json'),'--candidate',str(self.root/'candidate.png'),'--receipt',str(self.root/'receipt.json'),'--cwd',str(self.root),'--',*cmd],capture_output=True,text=True)

    def gate(self,diagnostic=False):
        result=subprocess.run([sys.executable,str(SCRIPTS/'visual_fidelity_gate.py'),'--contract',str(self.root/'contract.json'),'--candidate','test='+str(self.root/'candidate.png'),'--receipt','test='+str(self.root/'receipt.json'),'--output-dir',str(self.root/'report'),*(['--diagnostic'] if diagnostic else [])],capture_output=True,text=True)
        report=json.loads((self.root/'report/visual-gate-report.json').read_text(),parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
        return result,report

    def assert_gate(self,code,status,mode='normal'):
        render=self.render(mode);self.assertEqual(render.returncode,0,render.stderr)
        result,report=self.gate();self.assertEqual(result.returncode,code,result.stderr);self.assertEqual(report['status'],status)
        return report

    def test_valid_pass(self): self.assert_gate(0,'PASS')
    def test_missing_icon(self): self.assert_gate(1,'FAIL','missing')
    def test_shift(self): self.assert_gate(1,'FAIL','shift')
    def test_wrong_color(self): self.assert_gate(1,'FAIL','color')
    def test_missing_text_finite_json(self):
        report=self.assert_gate(1,'FAIL','missing_text');self.assertIsNone(report['candidates']['test']['relations']['row']['error'])
    def test_empty_checks(self):
        for key in ['regions','features','relations','color_samples']:self.c[key]={}
        self.assert_gate(2,'NOT_EVALUATED')
    def test_draft(self):
        self.c['status']='draft';self.assert_gate(2,'NOT_EVALUATED')
    def test_missing_coverage(self):
        del self.c['coverage']['icon'];self.assert_gate(2,'NOT_EVALUATED')
    def test_invented_coverage(self):
        self.c['coverage']['icon']['checks']=['regions.whole'];self.assert_gate(2,'NOT_EVALUATED')
    def test_all_nonblocking(self):
        for spec in self.c['features'].values():spec.update(blocking=False,reason='test')
        self.assert_gate(2,'NOT_EVALUATED')
    def test_empty_feature_limits(self):
        self.c['features']['icon']['limits']={};self.assert_gate(2,'NOT_EVALUATED')
    def test_missing_glyph(self):
        self.e['nodes'][1]['text']='中';(self.root/'source.json').write_text(json.dumps(self.e));self.c['pinned_files']['source.json']=sha256(self.root/'source.json');self.assert_gate(2,'NOT_EVALUATED')
    def test_missing_font_mapping(self):
        self.c['fonts']=[];self.assert_gate(2,'NOT_EVALUATED')
    def test_inputs_changed(self):
        self.assertEqual(self.render().returncode,0)
        (self.root/'render.py').write_text(RENDER+'\n# changed')
        result,report=self.gate();self.assertEqual(result.returncode,2);self.assertIn('Inputs changed',report['reason'])
    def test_reference_changed(self):
        self.assertEqual(self.render().returncode,0)
        with (self.root/'reference.png').open('ab') as f:f.write(b'x')
        result,report=self.gate();self.assertEqual(result.returncode,2);self.assertIn('Pinned file changed',report['reason'])
    def test_candidate_changed(self):
        self.assertEqual(self.render().returncode,0)
        with (self.root/'candidate.png').open('ab') as f:f.write(b'x')
        result,report=self.gate();self.assertEqual(result.returncode,2);self.assertIn('Screenshot',report['reason'])
    def test_missing_receipt(self):
        self.assertEqual(self.render().returncode,0);(self.root/'receipt.json').unlink()
        self.assertEqual(self.gate()[0].returncode,2)
    def test_environment_mismatch(self):
        self.assertEqual(self.render().returncode,0)
        r=json.loads((self.root/'receipt.json').read_text());r['environment']['renderer']='other';(self.root/'receipt.json').write_text(json.dumps(r))
        result,report=self.gate();self.assertEqual(result.returncode,2);self.assertIn('environment mismatch',report['reason'])
    def test_stale_render_rejected(self):
        self.assertEqual(self.render().returncode,0)
        result=self.render(command=[sys.executable,'-c','pass']);self.assertEqual(result.returncode,2);self.assertIn('stale',result.stderr)
    def test_diagnostic_never_passes(self):
        self.assertEqual(self.render().returncode,0)
        result,report=self.gate(True);self.assertEqual(result.returncode,2);self.assertFalse(report['passed']);self.assertTrue(report['metrics_passed'])
    def test_actual_exclusion_mask(self):
        self.c['regions']['whole']['max_mae']=0
        self.c['exclude_rects']=[{'rect':[70,70,10,10],'reason':'fixed dynamic content area'}]
        report=self.assert_gate(0,'PASS_WITH_EXCLUSIONS','photo');self.assertEqual(report['candidates']['test']['regions']['whole']['metrics']['compared_pixels'],9900)
    def test_mask_cannot_hide_icon(self):
        self.c['exclude_rects']=[{'rect':[10,10,10,10],'reason':'test'}];self.assert_gate(1,'FAIL','missing')
    def test_oversized_mask(self):
        self.c['exclude_rects']=[{'rect':[0,0,100,100],'reason':'test'}];self.assert_gate(2,'NOT_EVALUATED')
    def test_invalid_roi(self):
        self.c['regions']['whole']['rect']=[1000,0,1,1];self.assert_gate(2,'NOT_EVALUATED')
    def test_initializer_is_draft_with_suggestions(self):
        result=subprocess.run([sys.executable,str(SCRIPTS/'init_visual_contract.py'),'--evidence',str(self.root/'source.json'),'--reference',str(self.root/'reference.png'),'--output',str(self.root/'draft.json'),'--name','fixture'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        draft=json.loads((self.root/'draft.json').read_text());self.assertEqual(draft['status'],'draft');self.assertEqual(set(draft['coverage']),{'icon','text','surface'})
        hints=json.loads((self.root/'draft.suggestions.json').read_text());self.assertEqual(len(hints['nodes']),3);self.assertEqual(len(hints['relation_candidates']),1)
    def test_nonfinite_json_rejected(self):
        self.assertEqual(self.render().returncode,0)
        p=self.root/'contract.json';p.write_text(p.read_text().replace('"max_mae": 6','"max_mae": NaN'))
        result,report=self.gate();self.assertEqual(result.returncode,2);self.assertIn('Non-finite',report['reason'])
    def test_incomplete_pagination(self):
        self.c['source_scope']['expected_node_count']=4;self.assert_gate(2,'NOT_EVALUATED')
    def test_failed_rerender_invalidates_receipt(self):
        self.assertEqual(self.render().returncode,0)
        result=self.render(command=[sys.executable,'-c','raise SystemExit(1)'])
        self.assertEqual(result.returncode,2);self.assertEqual(self.gate()[0].returncode,2)
    def test_overflow_number_rejected(self):
        self.assertEqual(self.render().returncode,0)
        p=self.root/'contract.json';p.write_text(p.read_text().replace('"max_mae": 6','"max_mae": 1e309'))
        result,report=self.gate();self.assertEqual(result.returncode,2);self.assertIn('Non-finite',report['reason'])
    def test_output_cannot_overwrite_reference(self):
        self.assertEqual(self.render().returncode,0)
        before=sha256(self.root/'reference.png')
        result=subprocess.run([sys.executable,str(SCRIPTS/'visual_fidelity_gate.py'),'--contract',str(self.root/'contract.json'),'--candidate','test='+str(self.root/'candidate.png'),'--receipt','test='+str(self.root/'receipt.json'),'--output-dir',str(self.root)],capture_output=True,text=True)
        self.assertEqual(result.returncode,2);self.assertEqual(sha256(self.root/'reference.png'),before)
    def test_snapshot_mismatch(self):
        self.c['source_snapshot']='wrong';self.assert_gate(2,'NOT_EVALUATED')


if __name__ == '__main__':unittest.main()
