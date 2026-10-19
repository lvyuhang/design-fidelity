import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ai_review import annotations, selection, speed_selection, review, _review_single, combine_parts, detail_crops, prepare_images, apply_verdict, environment_context, prepare_verdict_images, header_boundary_images
import tempfile, json
from PIL import Image
from unittest.mock import patch
def candidate(description,y=.2):
    return dict(description=description,x=.5,y=y,confidence=.95,state_relation='equivalent',
                evidence=dict(component=description,reference='原稿组件证据',actual='截图组件证据',comparability='同一职责同一状态',alternative='未见'))

def verdict_for(candidates,kinds=None):
    return {'same_screen':True,'summary':'已复核','decisions':[
        dict(candidate_id=c['candidate_id'],verdict=kind,reason='复核两侧证据及环境',description=c['description'],confidence=.95,
             verify_condition='切换到相同筛选条件' if kind=='state_check' else '',duplicate_of='')
        for c,kind in zip(candidates,kinds or ['style']*len(candidates))]}

class VisualTests(unittest.TestCase):
    def test_selection_validates_model_and_effort(self):
        with patch('ai_review.models',return_value=[{'id':'gpt-5.6-sol','efforts':['low','high'],'default_effort':'low'}]):
            self.assertEqual(selection('gpt-5.6-sol','high'),('gpt-5.6-sol','high'))
            with self.assertRaises(ValueError):selection('unknown','low')
            with self.assertRaises(ValueError):selection('gpt-5.6-sol','ultra')

    def test_progress_follows_process_events(self):
        stages=[]
        class Process:
            returncode=0
            def __init__(self,cmd,**kw): self.answer=Path(cmd[cmd.index('--output-last-message')+1])
            def communicate(self,prompt,timeout):
                self.answer.write_text(json.dumps({'same_screen':True,'summary':'ok','issues':[]}))
        with tempfile.TemporaryDirectory() as tmp:
            image=Path(tmp)/'image.png';Image.new('RGB',(100,200),'white').save(image)
            with patch('ai_review.codex_path',return_value='codex'),patch('ai_review.subprocess.Popen',Process):
                result=_review_single(image,image,{},progress=stages.append)
        self.assertEqual(stages,['preparing','comparing','validating'])
        self.assertEqual(result['issues'],[])

    def test_crops_preserve_pixels_and_coordinate_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.png'
            Image.new('RGB',(100,200),'red').save(source)
            images,regions=detail_crops(source,source,root)
            self.assertEqual(len(images),10)
            with Image.open(images[0]) as image:self.assertEqual(image.size,(100,48))
            with Image.open(images[3]) as image:self.assertEqual(image.size,(100,44))
            self.assertEqual(regions[1]['images'][1]['y0'],.78)

    def test_local_request_only_contains_paired_crops_and_maps_coordinates(self):
        sent={}
        class Process:
            returncode=0
            def __init__(self,cmd,**kw):
                self.answer=Path(cmd[cmd.index('--output-last-message')+1])
                images=[Path(cmd[i+1]) for i,k in enumerate(cmd) if k=='--image']
                sent['sizes']=[Image.open(p).size for p in images];sent['cmd']=cmd
            def communicate(self,prompt,timeout):
                sent['prompt']=prompt.decode()
                self.answer.write_text(json.dumps({'same_screen':True,'summary':'ok','issues':[dict(description='间距偏大',x=.5,y=.5,confidence=.9,state_relation='equivalent')]}))
        with tempfile.TemporaryDirectory() as tmp:
            image=Path(tmp)/'image.png';Image.new('RGB',(1000,2000),'white').save(image)
            region=dict(x=.2,y=.3,width=.4,height=.2);context=dict(analysis_region=region,reference_region=region)
            metrics={}
            with patch('ai_review.codex_path',return_value='codex'),patch('ai_review.subprocess.Popen',Process):
                result=_review_single(image,image,context,metrics=metrics)
        self.assertEqual(sent['sizes'],[(400,400),(400,400)])
        self.assertNotIn('第3/4张',sent['prompt'])
        self.assertAlmostEqual(result['issues'][0]['x'],.4)
        self.assertAlmostEqual(result['issues'][0]['y'],.4)
        self.assertIn('model_providers.review_https.supports_websockets=false',sent['cmd'])
        self.assertIn('features.plugins=false',sent['cmd'])
        self.assertIn('skills.max_context_tokens=1',sent['cmd'])
        self.assertEqual(metrics['image_count'],2)

    def test_full_request_keeps_native_detail_and_small_context_overviews(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.png';Image.new('RGB',(1000,2000),'red').save(source)
            images,mapping=prepare_images(source,source,root)
            self.assertEqual(len(images),8)
            self.assertEqual(len(mapping),3)
            with Image.open(images[0]) as image:self.assertEqual(image.size,(480,960))
            for path in images[2:]:
                with Image.open(path) as image:self.assertEqual(image.width,1000)

    def test_verdict_keeps_native_candidate_detail_not_only_full_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.png';Image.new('RGB',(1000,4000),'red').save(source)
            images,mapping=prepare_verdict_images(source,source,root,[candidate('底栏内部留白',y=.95)])
            self.assertEqual(len(images),4)
            self.assertEqual([m['region'] for m in mapping],['navigation'])
            with Image.open(images[0]) as image:self.assertEqual(image.size,(300,1200))
            with Image.open(images[2]) as image:self.assertEqual(image.size,(1000,720))

    def test_header_review_has_additional_native_boundary_detail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.png';Image.new('RGB',(1000,4000),'red').save(source)
            detail,mapping=header_boundary_images(source,source,root)
            with Image.open(detail[0]) as image:self.assertEqual(image.size,(1000,260))
            self.assertEqual(mapping['images'][1]['y0'],.065)
            images,mapping=prepare_verdict_images(source,source,root,[candidate('顶部阴影',y=.1)])
            self.assertEqual(len(images),6)
            self.assertEqual(mapping[-1]['region'],'header-boundary-detail')

    def test_long_page_retains_native_detail_tiles_and_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.png';Image.new('RGB',(1000,4000),'red').save(source)
            images,mapping=prepare_images(source,source,root)
            self.assertEqual(len(images),8)
            with Image.open(images[0]) as image:self.assertEqual(image.size,(300,1200))
            with Image.open(images[2]) as image:self.assertEqual(image.size,(1000,1440))
            self.assertEqual(mapping[0]['images'][0]['y0'],0)
            self.assertEqual(mapping[-1]['images'][0]['y1'],1)
            for previous,current in zip(mapping,mapping[1:]):self.assertLess(current['images'][0]['y0'],previous['images'][0]['y1'])

    def test_parallel_review_covers_all_regions_and_merges_duplicate_findings(self):
        from copy import deepcopy
        calls=[]
        coverage={key:{'status':'partial','note':key} for key in ('layout','header','content','navigation','overlays')}
        common=candidate('底部导航背景透明度与原稿不符',y=.9)
        def single(reference,screenshot,context,model,effort,progress,metrics,adjudication=None):
            if adjudication is not None:
                self.assertEqual(len(context['comparison_basis']['components']),3)
                self.assertIn('内容区未知',context['comparison_basis']['environment'])
                return verdict_for(adjudication)
            calls.append(context)
            basis={'environment':'字体缩放已知；内容区未知','components':[dict(component=context['component_family'],match='same_variant',
                state_basis='共同组件可比',adaptation_basis='按相对布局核对',checked='轮廓及留白',limitations='单份设计稿') ]}
            return {'same_screen':True,'summary':'已查','issues':[deepcopy(common)],'state_differences':['动态照片不同'],'coverage':coverage,'comparison_basis':basis}
        with patch('ai_review._review_single',side_effect=single):
            result=review('ref','shot',{})
        self.assertEqual(len(calls),3)
        ranges=sorted((c['analysis_region']['y'],c['analysis_region']['y']+c['analysis_region']['height']) for c in calls)
        self.assertEqual(ranges[0][0],0)
        self.assertEqual(ranges[-1][1],1)
        for previous,current in zip(ranges,ranges[1:]):self.assertLess(current[0],previous[1])
        self.assertEqual(len(result['issues']),1)
        self.assertEqual(result['state_differences'],['动态照片不同'])
        self.assertEqual(set(result['coverage']),set(coverage))
        self.assertEqual({c['component'] for c in result['comparison_basis']['components']},{'header','content','navigation'})

    def test_region_candidates_wait_for_shared_semantic_verdict(self):
        import time
        metrics={};updates=[];calls=[]
        def single(reference,screenshot,context,model,effort,progress,part_metrics,adjudication=None):
            if adjudication is not None:
                calls.extend(adjudication)
                self.assertNotIn('partial_result',metrics)
                return verdict_for(adjudication,['style','business','environment'])
            y=context['analysis_region']['y'];time.sleep(.01+y*.05)
            return {'same_screen':True,'summary':str(y),'issues':[candidate('区域'+str(y)+'差异',y=y+.05)],'coverage':{}}
        def progress(stage):updates.append((stage,len(metrics.get('completed_regions',[])),'partial_result' in metrics))
        with patch('ai_review._review_single',side_effect=single):result=review('ref','shot',{},progress=progress,metrics=metrics)
        self.assertEqual(len(calls),3)
        self.assertTrue(any(n==1 for stage,n,partial in updates))
        self.assertTrue(any(stage=='adjudicating' and n==3 for stage,n,partial in updates))
        self.assertFalse(any(partial for stage,n,partial in updates))
        self.assertEqual(len(result['issues']),1)
        self.assertEqual(metrics['suppressed_count'],2)
        self.assertEqual(metrics['request_count'],4)

    def test_verdict_suppresses_business_environment_and_ungrounded_candidates(self):
        candidates=[dict(candidate('候选'+str(n)),candidate_id='c'+str(n)) for n in range(5)]
        candidates[-1].pop('evidence')
        verdict=verdict_for(candidates,['style','business','environment','unsupported','style'])
        result=apply_verdict({'same_screen':True},candidates,verdict)
        self.assertEqual(len(result['issues']),1)
        self.assertEqual(result['issues'][0]['state_relation'],'equivalent')
        self.assertEqual(sum(a['accepted'] for a in result['review_audit']),1)

    def test_state_checks_require_action_without_arbitrary_count_cutoff(self):
        candidates=[dict(candidate('候选'+str(n),y=n/10),candidate_id='c'+str(n)) for n in range(4)]
        verdict=verdict_for(candidates,['state_check']*4)
        verdict['decisions'][0]['verify_condition']=''
        result=apply_verdict({},candidates,verdict)
        self.assertEqual(len(result['issues']),3)
        self.assertTrue(all(i['state_relation']=='uncertain' for i in result['issues']))
        self.assertTrue(all('切换到相同筛选条件' in i['description'] for i in result['issues']))

    def test_incomplete_or_invented_verdict_fails_without_leaking_candidates(self):
        candidates=[dict(candidate('标题'),candidate_id='c1')]
        verdict=verdict_for(candidates)
        verdict['decisions'][0]['candidate_id']='invented'
        with self.assertRaises(ValueError):apply_verdict({},candidates,verdict)
        verdict['decisions']=[]
        with self.assertRaises(ValueError):apply_verdict({},candidates,verdict)

    def test_physical_capture_environment_uses_effective_density_without_identifiers(self):
        capture={'android_version':'15','display_size':'Physical size: 1440x3200\nOverride size: 1080x2412','display_density':'Physical density: 480\nOverride density: 432',
                 'font_scale':'1.15','package':'private.package','device':{'id':'serial'}}
        display=environment_context(capture,[540,1206])
        self.assertEqual(display['screen_width_dp'],400)
        self.assertEqual(display['density_dpi'],432)
        self.assertEqual(display['font_scale'],1.15)
        self.assertEqual(display['android_version'],'15')
        self.assertEqual(display['content_bounds'],'unknown')
        self.assertNotIn('serial',json.dumps(display));self.assertNotIn('private.package',json.dumps(display))

    def test_missing_environment_is_unknown_and_emulator_runtime_wins(self):
        unknown=environment_context({},[1080,2412])
        self.assertIsNone(unknown['screen_width_dp']);self.assertIsNone(unknown['font_scale'])
        capture={'display_density':'Physical density: 480','font_scale':'1.0',
                 'review_context':{'runtime':{'width_dp':432,'density':400,'font_scale':1.3,'navigation':'gesture','cutout':'center'}}}
        display=environment_context(capture,[1080,2400])
        self.assertEqual(display['screen_width_dp'],432)
        self.assertEqual(display['font_scale'],1.3)
        self.assertEqual(display['navigation'],'gesture')

    def test_reviewed_local_evidence_retains_original_anchor_and_selected_model(self):
        sent=[]
        class Process:
            returncode=0
            def __init__(self,cmd,**kw):
                self.answer=Path(cmd[cmd.index('--output-last-message')+1])
                self.schema=json.loads(Path(cmd[cmd.index('--output-schema')+1]).read_text())
                sent.append({'cmd':cmd,'images':[Image.open(cmd[i+1]).size for i,k in enumerate(cmd) if k=='--image']})
            def communicate(self,prompt,timeout):
                if 'decisions' in self.schema['properties']:
                    result=verdict_for([dict(candidate('按钮留白差异'),candidate_id='c1')])
                else:result={'same_screen':True,'summary':'ok','issues':[candidate('按钮留白差异',y=.5)]}
                self.answer.write_text(json.dumps(result))
        with tempfile.TemporaryDirectory() as tmp:
            image=Path(tmp)/'image.png';Image.new('RGB',(1000,2000),'white').save(image)
            region=dict(x=.2,y=.3,width=.4,height=.2);metrics={}
            with patch('ai_review.codex_path',return_value='codex'),patch('ai_review.subprocess.Popen',Process),patch('ai_review.selection',return_value=('chosen-model','high')):
                result=review(image,image,dict(analysis_region=region,reference_region=region,speed='standard'),'chosen-model','high',metrics=metrics)
        self.assertEqual(len(sent),2)
        self.assertTrue(all('chosen-model' in c['cmd'] for c in sent))
        self.assertEqual(sent[0]['images'],[(400,400)]*2)
        self.assertEqual(sent[1]['images'][:2],[(400,400)]*2)
        self.assertEqual(len(sent[1]['images']),4)
        self.assertAlmostEqual(result['issues'][0]['x'],.4)
        self.assertAlmostEqual(result['issues'][0]['y'],.4)
        self.assertEqual(metrics['request_count'],2)

    def test_unknown_filter_state_is_retained_as_hint_not_definite_defect(self):
        item=dict(candidate('筛选图标原稿红色填充、截图黑色空心'),candidate_id='filter')
        item['evidence'].update(component='筛选按钮',comparability='相同功能控件，激活状态未知',alternative='未见额外状态证据')
        verdict=verdict_for([item],['state_check'])
        result=apply_verdict({},[item],verdict)
        marks=annotations(result,[1080,2412],'filter-state')
        self.assertEqual(len(marks),1)
        self.assertEqual(marks[0]['review_kind'],'state_hint')
        self.assertIn('切换到相同筛选条件',marks[0]['note'])

    def test_semantic_duplicate_and_low_certainty_do_not_become_issues(self):
        candidates=[dict(candidate('候选'+str(n)),candidate_id='c'+str(n)) for n in range(3)]
        verdict=verdict_for(candidates,['style','duplicate','style'])
        verdict['decisions'][1]['duplicate_of']='c0'
        verdict['decisions'][2]['confidence']=.84
        result=apply_verdict({},candidates,verdict)
        self.assertEqual(len(result['issues']),1)
        self.assertEqual(result['issues'][0]['description'],'候选0')

    def test_speed_tier_requires_advertised_support(self):
        with patch('ai_review.models',return_value=[{'id':'fast-model','speeds':['standard','fast']},{'id':'plain','speeds':['standard']}]):
            self.assertEqual(speed_selection('fast-model','fast'),'fast')
            self.assertEqual(speed_selection('fast-model',None),'fast')
            self.assertEqual(speed_selection('plain',None),'standard')
            with self.assertRaises(ValueError):speed_selection('plain','fast')
            with self.assertRaises(ValueError):speed_selection('plain','unknown')

    def result(self,**kw):return {'same_screen':True,'issues':[dict(description='弹窗底部留白明显偏大',x=.5,y=.8,confidence=.9,state_relation='equivalent',**kw)]}
    def test_maps_to_original_image_and_stable_editable_id(self):
        a=annotations(self.result(),[1220,2656],'hash');b=annotations(self.result(),[1220,2656],'hash')
        self.assertEqual(a,b);self.assertEqual(a[0]['rect']['x'],610)
        self.assertEqual(a[0]['rect']['y'],2124.8);self.assertEqual(a[0]['status'],'待确认')
        self.assertEqual(a[0]['annotation_type'],'point')
    def test_different_page_never_marks(self):
        r=self.result();r['same_screen']=False;self.assertEqual(annotations(r,[100,100],'a'),[])
    def test_state_changes_do_not_become_pins(self):
        r=self.result()
        for relation in ['state_dependent',None]:
            r['issues'][0]['state_relation']=relation
            self.assertEqual(annotations(r,[100,100],'a'),[])

    def test_uncertain_state_becomes_hint_not_issue(self):
        r=self.result();r['issues'][0].update(state_relation='uncertain',confidence=.6)
        output=annotations(r,[100,100],'a')
        self.assertEqual(len(output),1)
        self.assertEqual(output[0]['review_kind'],'state_hint')
        self.assertEqual(output[0]['status'],'待确认')

    def test_same_page_different_state_keeps_comparable_regions(self):
        r=self.result();r['state_differences']=['键盘展开']
        r['issues'].append(dict(description='底部按钮上移',x=.5,y=.9,confidence=.99,state_relation='state_dependent'))
        output=annotations(r,[100,100],'a')
        self.assertEqual(len(output),1)
        self.assertEqual(output[0]['note'],'弹窗底部留白明显偏大')

    def test_low_confidence_filtered(self):
        r=self.result();r['issues'][0]['confidence']=.6;self.assertEqual(annotations(r,[100,100],'a'),[])
    def test_bad_coordinates_reject_entire_response(self):
        for value in [float('nan'),True,1.1,-.1,'0.2']:
            r=self.result();r['issues'][0]['x']=value
            with self.assertRaises(ValueError):annotations(r,[100,100],'a')
    def test_edge_anchor_stays_in_image(self):
        r=self.result();r['issues'][0]['x']=1;self.assertEqual(annotations(r,[100,100],'a')[0]['rect']['x'],99)
if __name__=='__main__':unittest.main()
