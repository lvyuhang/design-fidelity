"""Source-only preparation and compiler invariants, not wording snapshots."""
import copy
import json
from pathlib import Path
import unittest

import test_fidelity as fixtures
from compile_contract import compile_spec
from fidelity_contract import sha256
from prepare_page import prepare


class PreparationTests(unittest.TestCase):
    def setUp(self):
        f = self.fixture = fixtures.GateTests()
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.root = f.root
        self.e = copy.deepcopy(f.e)
        self.e['total'] = 3
        self.e['nodes'][2]['raw_style'] = {'fills':[], 'ddsOriginFrame': {
            'x':100,'y':200,'width':100,'height':100}}
        self.e['nodes'][1]['text_spec'] = {'base_style': {
            'font_family':'Fixture','font_size':12,'line_height':16,'color':'#000000'},
            'text_runs':[{'text':'A','font_family':'Fixture','font_weight':400}]}
        self.e['assets'] = [{'asset_id':'icon-asset','node_id':'icon',
            'source_point':{'x':109,'y':209},'source_size':{'width':12,'height':12}}]
        from PIL import Image, ImageDraw
        im = Image.new('RGBA',(48,48)); ImageDraw.Draw(im).rectangle((4,4,43,43),fill='red')
        im.save(self.root/'icon.png')
        self.manifest = {'snapshot_id':'test-snapshot','resolved_version':'test-version',
            'assets':[{'asset_id':'icon-asset','relative_path':'icon.png',
                       'bytes':(self.root/'icon.png').stat().st_size,
                       'sha256':sha256(self.root/'icon.png'),
                       'actual_pixel_size':{'width':48,'height':48}}]}
        (self.root/'fonts.json').write_text(json.dumps({'fonts':{
            'Fixture@400':{'path':'font.ttf','runtime_family':'Fixture'}}}))

    def run_prepare(self):
        (self.root/'source.json').write_text(json.dumps(self.e))
        (self.root/'manifest.json').write_text(json.dumps(self.manifest))
        return prepare([self.root/'source.json'], self.root/'reference.png',
                       self.root/'manifest.json', self.root/'fonts.json')

    def test_export_frame_preserves_padding_not_node_size(self):
        r = self.run_prepare()
        self.assertEqual(r['status'], 'PREPARED_FOR_REVIEW')
        a = r['assets'][0]
        self.assertEqual(a['layout_rect'], [10,10,10,10])
        self.assertEqual(a['export_rect'], [9,9,12,12])
        self.assertEqual(a['alpha_ink_rect'], [10,10,10,10])
        self.assertTrue(a['layout_differs_from_export'])

    def test_missing_glyph_detected_without_code_or_contract(self):
        self.e['nodes'][1]['text'] = '中'
        self.e['nodes'][1]['text_spec']['text_runs'][0]['text'] = '中'
        r = self.run_prepare()
        self.assertEqual(r['status'], 'NEEDS_INPUT_FIXES')
        self.assertEqual([i['characters'] for i in r['issues'] if i['kind']=='missing_glyphs'], ['中'])

    def test_mixed_run_font_requires_its_own_mapping(self):
        n = self.e['nodes'][1]; n['text'] = 'AA'
        n['text_spec']['text_runs'].append({'text':'A','font_family':'Fixture','font_weight':600})
        r = self.run_prepare()
        self.assertEqual([i['font'] for i in r['issues'] if i['kind']=='font_mapping_missing'], ['Fixture@600'])

    def test_no_origin_does_not_guess_from_node_bounds(self):
        self.e['nodes'][2].pop('raw_style')
        r = self.run_prepare()
        self.assertNotIn('export_rect', r['assets'][0])
        self.assertIn('export_frame_unresolved', [i['kind'] for i in r['issues']])

    def test_incomplete_pagination_rejected(self):
        self.e['total'] = 4
        with self.assertRaisesRegex(ValueError,'inventory'):
            self.run_prepare()

    def test_mismatched_asset_snapshot_rejected(self):
        self.manifest['snapshot_id'] = 'another'
        with self.assertRaisesRegex(ValueError,'snapshot'):
            self.run_prepare()

    def test_asset_corruption_rejected(self):
        self.manifest['assets'][0]['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError,'hash'):
            self.run_prepare()

    def test_node_asset_without_source_metadata_is_reported(self):
        self.e['assets'] = []
        r = self.run_prepare()
        self.assertEqual(r['status'], 'NEEDS_INPUT_FIXES')
        self.assertIn('asset_spec_missing', [i['kind'] for i in r['issues']])

    def test_parent_asset_is_proposal_only_and_effects_survive(self):
        self.e['nodes'][1]['parent_id'] = 'icon'
        self.e['nodes'][0]['raw_style'] = {'shadow':[{'isEnabled':True,'blurRadius':3}]}
        r = self.run_prepare()
        text = next(n for n in r['nodes'] if n['node_id']=='text')
        self.assertEqual(text['proposal'], 'ancestor_asset_candidate')
        self.assertIn('text',[i['node_id'] for i in r['review_queue']])
        self.assertEqual(r['effect_candidates'][0]['effect_fields'], ['shadow'])
        self.assertNotIn('coverage', r)


class ContractCompilerTests(unittest.TestCase):
    def setUp(self):
        f = self.fixture = fixtures.GateTests()
        f.setUp(); self.addCleanup(f.doCleanups)
        self.spec = copy.deepcopy(f.c)
        for k in ('coverage','pinned_files','status'):
            self.spec.pop(k)
        self.spec['excluded_nodes'] = {}

    def test_derives_same_coverage_without_changing_checks(self):
        c = compile_spec(self.spec, self.fixture.root)
        for group in ('features','regions','relations','color_samples'):
            self.assertEqual(c[group], self.fixture.c[group])
        for key in self.fixture.c['coverage']:
            self.assertEqual(c['coverage'][key]['checks'],self.fixture.c['coverage'][key]['checks'])

    def test_unreviewed_node_does_not_get_blanket_coverage(self):
        self.spec['features'].pop('icon')
        self.spec['relations'] = {}
        self.spec['not_applicable'] = {'relations':'fixture intentionally omits relation'}
        with self.assertRaisesRegex(ValueError,'Unreviewed'):
            compile_spec(self.spec,self.fixture.root)

    def test_unknown_exclusion_rejected(self):
        self.spec['excluded_nodes']['wrong-id'] = 'missing asset'
        with self.assertRaisesRegex(ValueError,'unknown'):
            compile_spec(self.spec,self.fixture.root)

    def test_exclusion_cannot_override_blocking_check(self):
        self.spec['excluded_nodes']['icon'] = 'missing asset'
        with self.assertRaisesRegex(ValueError,'both checked and excluded'):
            compile_spec(self.spec,self.fixture.root)

    def test_missing_font_still_rejected(self):
        e = self.fixture.e; e['nodes'][1]['text'] = '中'
        (self.fixture.root/'source.json').write_text(json.dumps(e))
        with self.assertRaisesRegex(ValueError,'missing glyphs'):
            compile_spec(self.spec,self.fixture.root)
