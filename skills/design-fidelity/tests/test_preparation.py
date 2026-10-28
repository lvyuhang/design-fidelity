"""Source-only preparation and compiler invariants, not wording snapshots."""
import copy
import json
from pathlib import Path
import unittest

import test_fidelity as fixtures
from compile_contract import compile_spec, check_raster_scope, freeze_or_verify
from fidelity_contract import sha256
from prepare_page import implementation_brief, prepare


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

    def test_unused_fallback_bytes_are_optional_but_metadata_remains(self):
        self.e['assets'][0]['kind'] = 'render_fallback'
        self.manifest['assets'] = []
        result = self.run_prepare()
        self.assertFalse(any(i['kind'] == 'asset_not_exported' for i in result['issues']))
        self.assertEqual(result['assets'][0]['download_state'], 'deferred')
        self.assertNotIn('path', result['assets'][0])
        self.assertFalse(result['assets'][0]['usable_for_implementation'])

    def test_missing_original_asset_still_blocks(self):
        self.e['assets'][0]['kind'] = 'exported_asset'
        self.manifest['assets'] = []
        result = self.run_prepare()
        self.assertTrue(any(i['kind'] == 'asset_not_exported' for i in result['issues']))

    def test_export_frame_preserves_padding_not_node_size(self):
        r = self.run_prepare()
        self.assertEqual(r['status'], 'PREPARED_FOR_REVIEW')
        a = r['assets'][0]
        self.assertEqual(a['layout_rect'], [10,10,10,10])
        self.assertEqual(a['export_rect'], [9,9,12,12])
        self.assertEqual(a['alpha_ink_rect'], [10,10,10,10])
        self.assertTrue(a['layout_differs_from_export'])

    def test_node_local_origin_preserves_transparent_export_padding_without_canvas_anchor(self):
        self.e['nodes'][2].pop('raw_style')
        self.e['nodes'][0]['raw_style']['ddsOriginFrame'] = {
            'x':110,'y':210,'width':10,'height':10}
        a = self.run_prepare()['assets'][0]
        self.assertEqual(a['export_rect'], [9,9,12,12])
        self.assertEqual(a['export_frame_source'], 'source_point_relative_to_node_origin')
        self.assertEqual(a['export_density'], 4)

    def test_asset_not_downloaded_is_not_reported_as_missing_bitmap(self):
        self.e['nodes'][0]['node_type'] = 'bitmap'
        self.manifest['assets'] = []
        result = self.run_prepare()
        node = next(n for n in result['nodes'] if n['node_id'] == 'icon')
        self.assertEqual(result['status'], 'NEEDS_INPUT_FIXES')
        self.assertEqual(node['proposal'], 'review_asset_export')
        self.assertEqual(node['source_disposition']['state'], 'asset_candidate')
        self.assertEqual(implementation_brief(result, {n['node_id']:n for n in self.e['nodes']})['missing_bitmaps'], [])

    def test_influence_fallback_requires_matching_source_size(self):
        self.e['assets'][0].pop('source_point')
        self.e['nodes'][0]['raw_style'].update(
            ddsOriginFrame={'x':100,'y':200}, influenceLeft=99, influenceTop=199,
            influenceWidth=12, influenceHeight=12)
        self.e['assets'][0]['source_point'] = {'x':900,'y':900}
        a = self.run_prepare()['assets'][0]
        self.assertEqual(a['export_rect'], [9,9,12,12])
        self.assertEqual(a['export_density'], 4)
        self.e['assets'][0].pop('source_point')
        self.e['assets'][0]['source_size']['width'] = 11
        r = self.run_prepare()
        self.assertNotIn('export_rect', r['assets'][0])
        self.assertTrue(any(i['kind']=='export_frame_unresolved' for i in r['issues']))

    def test_nonuniform_density_is_not_silently_stretched(self):
        self.e['assets'][0]['source_size']['width'] = 11
        r = self.run_prepare()
        self.assertNotIn('export_rect', r['assets'][0])
        self.assertTrue(any(i['kind']=='export_density_mismatch' for i in r['issues']))

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

    def test_verified_canvas_frame_does_not_double_translate_document_point(self):
        self.e.update(coordinate_space='source_canvas',coordinate_mapping={'verified':True})
        self.e['assets'][0]['render_bounds']={'x':9,'y':9,'width':12,'height':12}
        # Conflicting legacy origin is superseded only by verified normalized evidence.
        self.e['assets'][0]['source_point']={'x':999,'y':-999}
        r=self.run_prepare()
        self.assertEqual(r['assets'][0]['export_rect'],[9,9,12,12])
        self.assertEqual(r['assets'][0]['export_frame_source'],'verified_render_bounds')

    def test_unverified_bounds_do_not_authorize_normalization(self):
        self.e['nodes'][2].pop('raw_style')
        self.e['assets'][0]['render_bounds']={'x':9,'y':9,'width':12,'height':12}
        self.e.update(coordinate_space='source_canvas',coordinate_mapping={'verified':False})
        with self.assertRaisesRegex(ValueError,'Unverified'):
            self.run_prepare()

    def test_render_fallback_not_promoted_to_original_by_download(self):
        self.e['assets'][0]['kind']='render_fallback'
        r=self.run_prepare()
        self.assertNotEqual(next(n['proposal'] for n in r['nodes'] if n['node_id']=='icon'),'original_asset')
        brief=implementation_brief(r,{n['node_id']:n for n in self.e['nodes']})
        self.assertEqual(brief['assets'][0]['kind'],'render_fallback')

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

    def test_review_groups_do_not_remove_instances_or_effects(self):
        r = self.run_prepare()
        grouped = [key for group in r['review_groups'] for key in group['node_ids']]
        self.assertEqual(sorted(grouped), sorted(n['node_id'] for n in r['nodes']))
        self.assertEqual(len(grouped), len(set(grouped)))

    def test_implementation_brief_keeps_instances_but_deduplicates_styles(self):
        r = self.run_prepare()
        nodes = {n['node_id']: n for n in self.e['nodes']}
        brief = implementation_brief(r, nodes)
        instances = [item for group in brief['text_style_groups']
                     for item in group['instances']]
        self.assertEqual([item['node_id'] for item in instances], ['text'])
        self.assertEqual(instances[0]['rect'], [30, 10, 10, 10])
        self.assertEqual(brief['assets'][0]['node_id'], 'icon')
        self.assertEqual(brief['source']['snapshot_id'], 'test-snapshot')

    def test_small_fills_borders_and_parent_survive_brief_compression(self):
        nodes = {n['node_id']: n for n in self.e['nodes']}
        nodes['badge'] = {'node_type':'shape', 'parent_id':'surface',
            'bounds':{'x':85,'y':280,'width':34,'height':14},
            'raw_style':{'opacity':20,'radius':[7.2],
                         'fills':[{'type':'color','color':{'r':0,'g':0,'b':0,'a':1}}]}}
        nodes['badge2'] = copy.deepcopy(nodes['badge'])
        nodes['badge2']['bounds']['y'] = 512
        nodes['dot'] = {'node_type':'shape','parent_id':'badge',
            'bounds':{'x':63,'y':100,'width':8,'height':8},
            'raw_style':{'opacity':100,'fills':[],
                'borders':[{'position':'外边框','thickness':1}],
                'ddsOriginFrame':{'x':63,'y':100},
                'influenceLeft':62,'influenceTop':99,'influenceWidth':10,'influenceHeight':10}}
        result = self.run_prepare()
        brief = implementation_brief(result, nodes)
        groups = brief['visual_style_groups']
        group = next(g for g in groups if g['style'].get('opacity') == 20)
        self.assertEqual([v['node_id'] for v in group['instances']], ['badge','badge2'])
        self.assertEqual(group['style']['fills'][0]['color']['a'], 1)
        self.assertEqual([i['rect'][1] for i in group['instances']], [280,512])
        self.assertEqual(group['instances'][0]['parent_id'], 'surface')
        dot = next(g for g in groups if 'borders' in g['style'])
        self.assertEqual(dot['style']['borders'][0]['position'], '外边框')
        self.assertEqual(dot['instances'][0]['rect'], [63,100,8,8])
        self.assertEqual(dot['instances'][0]['paint_rect'], [62,99,10,10])
        self.assertEqual(brief['inventory_count'], 5)  # Empty parent is not a painted node.

    def test_painted_parent_cannot_disappear_from_inventory(self):
        from fidelity_contract import inventory
        nodes = {'parent':{'bounds':{'x':0,'y':0,'width':34,'height':14},
            'raw_style':{'fills':[{'type':'color'}]}},
            'child':{'parent_id':'parent','bounds':{'x':1,'y':1,'width':2,'height':2}}}
        self.assertEqual(set(inventory(nodes)), {'parent','child'})

    def test_scene_relationships_and_paint_order_survive_compact_brief(self):
        result = self.run_prepare()
        nodes = {n['node_id']:n for n in self.e['nodes']}
        nodes['surface']['raw_style']['hasClippingMask'] = True
        nodes['surface']['source_order'] = 1
        nodes['icon'].update(source_order=2, parent_id='page')
        nodes['icon']['bounds'] = {'x':95,'y':95,'width':10,'height':10}
        brief = implementation_brief(result,nodes)
        instances = [i for g in brief['scene_requirements'] for i in g['instances']]
        self.assertEqual({i['id'] for i in instances}, {'surface/clip','icon/boundary/surface'})
        icon = next(i for g in brief['visual_style_groups'] for i in g['instances'] if i['node_id']=='icon')
        self.assertEqual((icon['parent_id'],icon['source_order']),('page',2))


class ContractCompilerTests(unittest.TestCase):
    def setUp(self):
        f = self.fixture = fixtures.GateTests()
        f.setUp(); self.addCleanup(f.doCleanups)
        self.spec = copy.deepcopy(f.c)
        for k in ('coverage','pinned_files','status'):
            self.spec.pop(k)
        self.spec['excluded_nodes'] = {}

    def test_frozen_reuse_requires_identical_inputs_and_checks(self):
        spec = self.fixture.root/'reviewed.json'
        output = self.fixture.root/'frozen.json'
        spec.write_text(json.dumps(self.spec))
        self.assertEqual(freeze_or_verify(spec, output)[1], 'CONTRACT_COMPILED')
        before = output.read_bytes()
        self.assertEqual(freeze_or_verify(spec, output)[1], 'CONTRACT_REUSED')
        self.spec['features']['icon']['label'] = 'changed'
        spec.write_text(json.dumps(self.spec))
        with self.assertRaisesRegex(ValueError, 'differs'):
            freeze_or_verify(spec, output)
        self.assertEqual(output.read_bytes(), before)

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

    def test_groups_expand_to_independent_unchanged_checks(self):
        expected = copy.deepcopy(self.spec['features']['icon'])
        self.spec['feature_groups'] = {'group':self.spec['features'].pop('icon')}
        self.spec['relations']['row']['features'][0] = 'group__icon'
        original = self.spec['node_decisions'].pop('icon')
        self.spec['decision_groups'] = {'icons':{'node_ids':['icon'],'decision':original}}
        result = compile_spec(self.spec, self.fixture.root)
        self.assertEqual(result['features']['group__icon'], expected)
        self.assertEqual(result['node_decisions']['icon'], original)
        self.assertNotIn('feature_groups', result)
        self.assertEqual(result['coverage']['icon']['checks'], ['features.group__icon'])

    def test_group_cannot_overwrite_explicit_decision(self):
        self.spec['decision_groups'] = {'icons':{'node_ids':['icon'],
            'decision':self.spec['node_decisions']['icon']}}
        with self.assertRaisesRegex(ValueError,'duplicate binding'):
            compile_spec(self.spec,self.fixture.root)

    def test_empty_reference_detector_rejected_before_any_candidate(self):
        self.spec['features']['icon']['detector']['rgb'] = [0,255,0]
        with self.assertRaisesRegex(ValueError,'no ink'):
            compile_spec(self.spec,self.fixture.root)
        self.assertFalse((self.fixture.root/'candidate.png').exists())

    def test_rasterized_text_and_text_parent_are_not_component_implementation(self):
        nodes = {'text':{'text':'Reply','parent_id':'card'}, 'card':{}}
        for key in ('text','card'):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError,'contains text/UI'):
                check_raster_scope({'node_decisions':{key:{'mode':'render_fallback'}}},nodes)
        check_raster_scope({'node_decisions':{'photo':{'mode':'render_fallback'}}},
                           {'photo':{'node_type':'bitmap'}})

    def test_text_detector_uses_only_single_opaque_source_color(self):
        from init_visual_contract import source_text_detector
        self.assertEqual(source_text_detector({'text_spec':{'base_style':{'color':'#102030'}}})['rgb'],[16,32,48])
        self.assertIsNone(source_text_detector({'text_spec':{'text_runs':[{'color':'rgba(1,2,3,0.5)'}]}}))
        self.assertIsNone(source_text_detector({'text_spec':{'text_runs':[{'color':'#000000'},{'color':'#ff0000'}]}}))
